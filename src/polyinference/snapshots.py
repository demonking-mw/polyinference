"""Shared readers and diagnostic snapshots for UI Save and rolling run history."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from .agent.routing import accounting
from .costs import run_cost
from .ui_agents import agent_snapshot
from .ui_os import (
    artifact_references,
    context_metadata,
    export_artifacts,
    invocation_root,
    read_snapshot,
    runtime_view,
)


def read_records(state):
    path = Path(state) / "records.sqlite"
    if not path.is_file():
        return {}
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='records'").fetchone():
            return {}
        return {key: json.loads(body) for key, body in db.execute("SELECT key,body FROM records")}


def read_artifact(state, ref):
    digest = ref.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Invalid artifact reference")
    root = Path(state) / "artifacts"
    path = root / digest[7:]
    if path.is_symlink():
        raise ValueError("Invalid artifact path")
    content = path.read_bytes()
    if "sha256:" + hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("Artifact digest mismatch")
    return content.decode(errors="replace")


async def checkpoints(state):
    path = Path(state) / "checkpoints.sqlite"
    if not path.is_file():
        return []
    async with aiosqlite.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        tables = await connection.execute(
            "SELECT name FROM sqlite_master WHERE name IN ('checkpoints', 'writes')"
        )
        if len(await tables.fetchall()) != 2:
            return []
        saver = AsyncSqliteSaver(connection)
        return [item async for item in saver.alist(None)]


async def node_history(state, running=False):
    """Each branch channel identifies the actual next node in these serial graphs."""
    groups = defaultdict(list)
    for item in await checkpoints(state):
        groups[item.config["configurable"]["thread_id"]].append(item)
    processes = []
    for pid, items in groups.items():
        items.sort(key=lambda item: item.checkpoint["id"])
        nodes = []
        for index, item in enumerate(items):
            if item.metadata.get("source") != "loop":
                continue
            before = item.checkpoint["channel_values"]
            following = items[index + 1] if index + 1 < len(items) else None
            writes = {name: value for _, name, value in item.pending_writes}
            for channel in before:
                if not channel.startswith("branch:to:"):
                    continue
                name = channel.removeprefix("branch:to:")
                status = (
                    "failed"
                    if "__error__" in writes
                    else "interrupted"
                    if "__interrupt__" in writes
                    else "completed"
                    if following
                    else "running"
                    if running
                    else "interrupted"
                )
                nodes.append(
                    {
                        "id": pid + ":" + item.checkpoint["id"] + ":" + name,
                        "name": name,
                        "phase": before.get("phase", before.get("mode", "")),
                        "status": status,
                        "started_at": item.checkpoint["ts"],
                        "finished_at": following.checkpoint["ts"] if following else None,
                        "logical_step": before.get("logical_step"),
                        "input": {k: v for k, v in before.items() if not k.startswith("branch:")},
                        "output": {k: v for k, v in writes.items() if not k.startswith("branch:")},
                        "model_call": name in {"model", "submit"},
                    }
                )
        if nodes:
            processes.append({"id": pid, "nodes": nodes, "started_at": items[0].checkpoint["ts"]})
    return sorted(processes, key=lambda process: process["started_at"])


def detail(state, node, records):
    effects = [
        value
        for key, value in records.items()
        if key.startswith("effect/") and value["request"]["scope"]["process_id"] == node["process_id"]
    ]
    matching = [
        effect
        for effect in effects
        if effect["request"]["created_at"] >= node["started_at"]
        and (not node["finished_at"] or effect["request"]["created_at"] < node["finished_at"])
    ]
    if node["model_call"]:
        step = "model-" + str(node["logical_step"])
        models = {effect["request"]["operation_id"]: {
            "process_id": node["process_id"], **context_metadata(effect["request"], effect, records)}
            for effect in effects if effect["request"]["payload"]["kind"] in {"model_query", "agent_job"}}
        roots = {oid for oid, row in models.items() if row["logical_step_id"] == step and not row["context_compaction"]}
        selected = set(roots)
        for oid, row in models.items():
            if row["context_compaction"]:
                continue
            try:
                if invocation_root(oid, models) in roots:
                    selected.add(oid)
            except ValueError:
                pass
        matching = [effect for effect in effects if effect["request"]["operation_id"] in selected]
    operations = []
    def text(ref):
        try:
            return read_artifact(state, ref)
        except (ValueError, OSError, TypeError) as exc:
            return "Artifact unavailable: " + str(exc)

    def messages(context):
        return [{"role": "system" if part.get("part_kind") == "instruction"
                 and part.get("trust") in {"application", "user"} else "assistant"
                 if part.get("part_kind") in {"message", "tool_call"} else "user",
                 "content": text(part.get("content", {}))} for part in context.get("parts", [])]

    matching.sort(key=lambda effect: (effect["request"]["created_at"], effect["request"]["operation_id"]))
    selected_operation = None
    if node["model_call"] and matching:
        retained = {e["request"]["operation_id"]: e for e in matching}
        outstanding = [e for e in matching if e["state"] not in {"succeeded", "failed", "cancelled"}]
        effective_id, visited = next(iter(sorted(roots)), None), set()
        outcome = None
        while effective_id in retained and effective_id not in visited:
            visited.add(effective_id)
            metadata = models[effective_id]
            target = metadata["output_retry_outcome"] or metadata["model_retry_outcome"]
            if not target or target == effective_id:
                break
            if target in visited:
                outcome = None
                break
            outcome = target if target in retained else None
            effective_id = target
        selected_operation = (outstanding[-1]["request"]["operation_id"] if outstanding else
                              outcome or matching[-1]["request"]["operation_id"])
    for effect in matching:
        request = effect["request"]
        payload = request["payload"]
        original = payload.get("context", {})
        prepared = records.get("context-prepared/" + request["operation_id"], {})
        effective = prepared.get("context")
        receipt = prepared.get("receipt", {})
        identity_ok = bool(effective and receipt.get("context_ref") == original.get("view_id")
                           and receipt.get("prepared_context_ref") == effective.get("view_id"))
        prompt = messages(effective if identity_ok else original)
        native_prompt = None
        response = None
        if effect.get("result"):
            refs = effect["result"]["output_refs"]
            if refs:
                raw = text(refs[0])
                try:
                    response = json.loads(raw)
                except ValueError:
                    response = raw
        # Codex persists the submitted application messages in its userMessage event.
        if payload["kind"] == "agent_job" and isinstance(response, dict):
            for event in response.get("events", []):
                item = event.get("params", {}).get("item", {})
                if item.get("type") != "userMessage":
                    continue
                for part in item.get("content", []):
                    try:
                        native = json.loads(part.get("text", ""))
                    except ValueError:
                        continue
                    if isinstance(native, list) and all(
                        isinstance(message, dict) and "role" in message and "content" in message
                        for message in native
                    ):
                        native_prompt = native
        arguments = text(payload["arguments"]) if payload.get("arguments") else None
        operations.append(
            {
                "id": request["operation_id"],
                "kind": payload["kind"],
                "tool": payload.get("capability_id"),
                "status": effect["state"],
                "prompt": prompt,
                "prompt_origin": "effective_prepared" if identity_ok else "original_supplied",
                "prompt_issue": "Prepared context/receipt identity mismatch" if effective and not identity_ok else None,
                "original_prompt": messages(original),
                "native_observed_prompt": native_prompt,
                "context_compaction": bool(request.get("extensions", {}).get("runtime/context-compaction")),
                "arguments": arguments,
                "response": response,
                "error": effect.get("diagnostic"),
            }
        )
    return {**node, "operations": operations, "selected_operation_id": selected_operation}


def run_summary(metadata, records, configuration, active=False, cost=None):
    # A coordinator may finish during the read. Report running until the next
    # snapshot rather than interpreting its earlier "active" record as a crash.
    run = records.get("app/run", {})
    blocker = run.get("blocker")
    operation = records.get("effect/" + str(blocker), {})
    blocker_detail = operation.get("diagnostic") or (
        ((operation.get("result") or {}).get("error") or {}).get("message")
    ) or blocker
    status = (
        "running"
        if active
        else "failed"
        if metadata.get("error") and run.get("status") != "paused"
        else run.get("status", "interrupted")
    )
    if status == "active":
        status = "interrupted"
    source = metadata.get("repository")
    if not source:
        source = configuration.get("repository")
    return {
        **metadata,
        "status": status,
        "objective": run.get("objective", metadata.get("objective", configuration.get("objective", ""))),
        "error": blocker_detail if operation else metadata.get("error"),
        "repository": source,
        "output": run.get("output"),
        "repository_setup": records.get("repository/setup"),
        "repository_summary": records.get("coding/repository-summary"),
        "blocker": blocker,
        "blocker_detail": blocker_detail,
        "cost": cost if cost is not None else run_cost(records, lambda ref: read_artifact(metadata["state"], ref)),
        "development_allocation": accounting(
            records, configuration.get("senior_development_fraction", 0.1)
        ),
        "steering_received": run.get("steering_received", 0),
        "steering_applied": run.get("steering_applied", 0),
    }


async def export_run(metadata, configuration, active=False):
    """The shared diagnostic snapshot for UI Save and automatic run history."""
    state = metadata["state"]
    snapshot = read_snapshot(state)
    records = snapshot["records"]
    view = run_summary(metadata, records, configuration, active)
    history = await node_history(state, view["status"] == "running")
    processes = []
    for process in history:
        record = records.get("process/" + process["id"], {})
        process["role"] = "controller" if process["id"] == "controller" else record.get("role", "process")
        progress = records.get("worker-progress/" + process["id"])
        if progress:
            process["progress"] = {key: progress[key] for key in ("status", "idle_decisions")}
        nodes = []
        for node in process["nodes"]:
            original = {**node, "process_id": process["id"]}
            try:
                nodes.append(detail(state, original, records))
            except (ValueError, OSError) as exc:
                nodes.append({**original, "export_error": str(exc)})
        processes.append({**process, "nodes": nodes})
    effects = []
    for key, effect in records.items():
        if not key.startswith("effect/"):
            continue
        outputs = []
        for ref in (effect.get("result") or {}).get("output_refs", []):
            try:
                text = read_artifact(state, ref)
                try:
                    output = json.loads(text)
                except ValueError:
                    output = text
                outputs.append({"ref": ref, "value": output})
            except (ValueError, OSError) as exc:
                outputs.append({"ref": ref, "error": str(exc)})
        effects.append({"record_ref": key, **effect, "outputs": outputs})
    inference_attempts = []
    for key, effect in records.items():
        if not key.startswith("inference-attempt/"):
            continue
        outputs, parts = [], []
        for ref in (effect.get("result") or {}).get("output_refs", []):
            try:
                text = read_artifact(state, ref)
                try:
                    output = json.loads(text)
                except ValueError:
                    output = text
                outputs.append({"ref": ref, "value": output})
            except (ValueError, OSError) as exc:
                outputs.append({"ref": ref, "error": str(exc)})
        for part in effect["request"]["payload"].get("context", {}).get("parts", []):
            try:
                parts.append({**part, "text": read_artifact(state, part["content"])})
            except (ValueError, OSError) as exc:
                parts.append({**part, "export_error": str(exc)})
        inference_attempts.append({"record_ref": key, **effect, "outputs": outputs, "context_parts": parts})
    os_view = runtime_view(snapshot, configuration, view["status"] == "running")
    retained_checkpoints = await checkpoints(state)
    checkpoint_records = [{
        "config": item.config, "checkpoint": item.checkpoint, "metadata": item.metadata,
        "parent_config": item.parent_config, "pending_writes": item.pending_writes,
    } for item in retained_checkpoints]
    references = artifact_references([records, snapshot["events"], checkpoint_records])
    artifacts = export_artifacts(state, references)
    return {
        "schema_version": 2,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "run": {key: value for key, value in view.items() if key not in {"processes", "os"}},
        "configuration": configuration or None,
        "os": os_view,
        "agents": agent_snapshot(records, lambda ref: read_artifact(state, ref)),
        "records": records,
        "record_revisions": snapshot["revisions"],
        "events": snapshot["events"],
        "artifacts": artifacts,
        "checkpoints": checkpoint_records,
        "capture": {
            "records_captured_at": snapshot["captured_at"],
            "journal": os_view["journal"],
            "artifact_errors": sum("error" in row for row in artifacts),
            "note": "Records and events share a read transaction. Checkpoints and artifacts are captured "
                    "separately; an active run may advance during export. Journal retention is 10,000 events; "
                    "older runs may lack timestamps, historical values and queue telemetry. "
                    "This diagnostic export does not include private Git objects or restore a runnable OS.",
        },
        "processes": processes,
        "effects": effects,
        "inference_attempts": inference_attempts,
        "retry_windows": {key: value for key, value in records.items() if key.startswith("retry/")},
        "check_diagnoses": {key: value for key, value in records.items() if key.startswith("diagnosis/")},
        "worker_exceptions": {key: value for key, value in records.items() if key.startswith("worker-exception/")},
        "exception_decisions": {key: value for key, value in records.items() if key.startswith("exception-queue/")},
        "recovery_accounts": {key: value for key, value in records.items() if key.startswith("process-account/")},
        "worker_progress": {key: value for key, value in records.items() if key.startswith("worker-progress/")},
        "progress_events": {key: value for key, value in records.items() if key.startswith("progress-event/")},
        "progress_observer_errors": {key: value for key, value in records.items() if key.startswith("progress-observer-error/")},
        "completion_reviews": {key: value for key, value in records.items() if key.startswith("completion-review/")},
        "review_artifacts": {key: value for key, value in records.items() if key.startswith("review-artifact/")},
        "interface_contracts": {key: value for key, value in records.items() if key.startswith("interface-contract/")},
        "reports": [value for key, value in records.items() if key.startswith("report/")],
        "steering": [value for key, value in sorted(records.items()) if key.startswith("steering/")],
        "run_record": records.get("app/run"),
        "repository_setup": records.get("repository/setup"),
        "repository_summary": records.get("coding/repository-summary"),
    }

