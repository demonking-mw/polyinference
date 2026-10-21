"""Read-only OS inspection from a single durable journal snapshot."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def read_snapshot(state):
    result = {"records": {}, "revisions": {}, "events": [], "captured_at": datetime.now(timezone.utc).isoformat()}
    path = Path(state) / "records.sqlite"
    if not path.is_file():
        return result
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        db.execute("BEGIN")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "records" in tables:
            for key, revision, body in db.execute("SELECT key,revision,body FROM records ORDER BY key"):
                result["records"][key] = json.loads(body)
                result["revisions"][key] = revision
        if "events" in tables:
            result["events"] = [
                {**json.loads(body), "sequence": sequence}
                for sequence, body in db.execute("SELECT sequence,body FROM events ORDER BY sequence")
            ]
    return result


def category(key):
    prefix = key.split("/", 1)[0]
    if prefix in {"reservation", "process", "process-status", "process-spec", "task", "attempt"}:
        return "scheduling"
    if prefix in {"permit", "ownership-wait"}:
        return "critical sections"
    if prefix in {"process-control", "steering"} or key == "app/run":
        return "control"
    if prefix in {"budget", "spend", "allocation"}:
        return "budgets"
    if prefix in {"effect", "logical"}:
        return "operations"
    return "workspace & records"


def activity(events, records):
    rows = []
    for event in events:
        for key, change in event.get("changes", {}).items():
            value = change.get("value", {})
            request = value.get("request", {})
            rows.append({
                "sequence": event["sequence"], "at": event.get("at"), "key": key,
                "category": category(key), "revision": change.get("revision"),
                "state": change.get("state"),
                "process_id": value.get("process_id") or value.get("scope", {}).get("process_id")
                              or request.get("scope", {}).get("process_id"),
                "resource": value.get("resource"), "value": value or None,
            })
        for key in event.get("immutable", []):
            value = event.get("immutable_values", {}).get(key, {})
            rows.append({
                "sequence": event["sequence"], "at": event.get("at"), "key": key,
                "category": category(key), "revision": 1, "state": "created",
                "process_id": value.get("process_id") or value.get("scope", {}).get("process_id"),
                "value": value or None,
            })
    return rows


def context_metadata(request, effect, records):
    """Small, artifact-free relationships for live and saved invocation inspection."""
    oid = request.get("operation_id")
    extensions = request.get("extensions") or {}
    attempted = ((effect.get("result") or {}).get("extensions") or {}).get(
        "polyinference/attempted-backend", effect.get("attempted_backend") or {})
    return {
        "logical_step_id": request.get("logical_step_id"),
        "model_retry": extensions.get("runtime/model-retry"),
        "output_retry": extensions.get("runtime/output-retry"),
        "context_compaction": bool(extensions.get("runtime/context-compaction")),
        "original_context_ref": request.get("payload", {}).get("context", {}).get("view_id"),
        "prepared_record": "context-prepared/" + str(oid) if "context-prepared/" + str(oid) in records else None,
        "receipt_record": "context-receipt/" + str(oid) if "context-receipt/" + str(oid) in records else None,
        "submitted": attempted.get("submitted"),
        "model_retry_outcome": records.get("model-retry-outcome/" + str(oid), {}).get("result_operation_id"),
        "output_retry_outcome": records.get("output-retry-outcome/" + str(oid), {}).get("operation_id"),
    }


def invocation_root(oid, operations, visiting=None):
    """Follow only explicit retry edges; malformed chains remain separate."""
    visiting = set() if visiting is None else visiting
    if oid in visiting:
        raise ValueError("Retry provenance cycle")
    row = operations[oid]
    visiting = visiting | {oid}
    roots = set()
    for marker in (row.get("model_retry"), row.get("output_retry")):
        if marker is None:
            continue
        if not isinstance(marker, dict) or not marker.get("root_operation_id") or not marker.get("previous_operation_id"):
            raise ValueError("Incomplete retry provenance")
        for reference in (marker["root_operation_id"], marker["previous_operation_id"]):
            parent = operations.get(reference)
            if not parent or parent["process_id"] != row["process_id"] or parent.get("context_compaction"):
                raise ValueError("Missing or cross-process retry provenance")
            roots.add(invocation_root(reference, operations, visiting))
    if len(roots) > 1:
        raise ValueError("Conflicting retry roots")
    return next(iter(roots), oid)


def runtime_view(snapshot, configuration, running=False):
    records, events = snapshot["records"], snapshot["events"]

    def group(prefix):
        return [{**value, "key": key} for key, value in records.items() if key.startswith(prefix)]

    operations = []
    for row in group("effect/"):
        request = row.get("request", {})
        payload = request.get("payload", {})
        operations.append({
            "key": row["key"], "operation_id": request.get("operation_id"), "state": row.get("state"),
            "process_id": request.get("scope", {}).get("process_id"),
            "kind": payload.get("kind"), "capability": payload.get("capability_id"),
            "created_at": request.get("created_at"), "deadline": request.get("deadline"),
            "parent_operation_id": request.get("causal_parent_ref"),
            "conflict_keys": request.get("conflict_keys", []), "diagnostic": row.get("diagnostic"),
            "native_diagnostics": row.get("native_diagnostics") or
            (row.get("result") or {}).get("extensions", {}).get("polyinference/native-diagnostics"),
            **context_metadata(request, row, records),
        })
    reservations = group("reservation/")
    lanes = []
    for name in ("local", "cloud"):
        endpoint = configuration.get(name, {})
        retained = [r for r in reservations if r["key"].startswith("reservation/" + name + "/")]
        held = [r for r in retained if r.get("state") == "held"]
        waiting = [r for r in retained if r.get("state") == "waiting"]
        lanes.append({
            "name": name, "model": endpoint.get("model"), "protocol": endpoint.get("protocol"),
            "limit": endpoint.get("max_inflight"), "token_limit": endpoint.get("reserved_context_tokens"),
            "held": len(held), "reserved_tokens": sum(r.get("tokens", 0) for r in held),
            "ordinary_waiters": sum(r.get("lane") == "ordinary" for r in waiting),
            "finishing_waiters": sum(r.get("lane") == "finishing" for r in waiting),
        })
    processes = []
    keys = set(key.split("/", 1)[1] for key in records if key.startswith(("process/", "process-status/")))
    for pid in sorted(keys):
        row = records.get("process/" + pid, {})
        status = records.get("process-status/" + pid, {})
        spec = records.get("process-spec/" + pid, {})
        processes.append({
            "key": "process-status/" + pid if status else "process/" + pid,
            "process_id": pid, "role": row.get("role", spec.get("role")),
            "state": status.get("state", row.get("state")), "status": status,
            "started_at": row.get("started_at", status.get("created_at")),
            "finished_at": row.get("finished_at") or (
                status.get("last_progress_at") if status.get("state") in {"completed", "failed", "cancelled"}
                else None
            ),
            "endpoint": configuration.get("role_bindings", {}).get(row.get("role", spec.get("role"))),
            "schedule": spec.get("schedule"), "control": records.get("process-control/" + pid),
        })
    first = events[0]["sequence"] if events else None
    return {
        "captured_at": snapshot["captured_at"], "source": "durable records",
        "coordinator_running": running, "kernel": records.get("runtime/kernel"),
        "policy": {
            "admission": "FIFO within ordinary/finishing lanes; alternate lanes when both have waiters",
            "preemption": "Cooperative cancellation; steering closes new starts and drains started workers",
            "critical_sections": "Verification/project ownership and installation-wide shell exclusion",
            "atomic_publication": "Compare-and-swap record updates commit in one SQLite transaction",
            "max_workers": configuration.get("max_workers"),
        },
        "lanes": lanes, "processes": processes, "reservations": reservations,
        "critical_sections": group("permit/"), "ownership_waits": group("ownership-wait/"),
        "operations": operations, "operation_counts": dict(Counter(row["state"] for row in operations)),
        "budgets": group("budget/") + group("spend/"),
        "workspaces": group("workspace/"), "tasks": group("task/"),
        "workspace_grants": group("workspace-grant/"),
        "limits": {key: configuration[key] for key in (
            "max_workers", "run_token_budget", "control_token_reserve", "run_spend_budget_microusd",
            "max_artifact_bytes", "max_workspace_bytes", "max_workspace_total_bytes", "max_queued_operations",
        ) if key in configuration},
        "control": records.get("app/run", {}), "cancellations": group("process-control/"),
        "steering": group("steering/"),
        "messages": sorted(group("user-message/"), key=lambda row: (row["created_at"], row["key"])),
        "record_index": [{"key": key, "revision": snapshot["revisions"][key], "category": category(key)}
                         for key in records],
        "journal": {
            "count": len(events), "first_sequence": first,
            "last_sequence": events[-1]["sequence"] if events else None,
            "pruned_events": max(0, (first or 1) - 1),
            "legacy_events": sum("at" not in event or any("value" not in change
                                 for change in event.get("changes", {}).values()) for event in events),
            "retention_limit": 10000,
        },
        "activity": activity(events[-120:], records),
    }


def artifact_references(value):
    if isinstance(value, dict):
        if value.get("artifact_id") == value.get("digest") and isinstance(value.get("digest"), str):
            if re.fullmatch(r"sha256:[0-9a-f]{64}", value["digest"]):
                yield value
        for child in value.values():
            yield from artifact_references(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from artifact_references(child)


def export_artifacts(state, references=()):
    """Include exact bytes of every retained content-addressed artifact."""
    artifacts = []
    root = Path(state) / "artifacts"
    names = {path.name for path in root.iterdir() if re.fullmatch(r"[0-9a-f]{64}", path.name)} \
        if root.is_dir() else set()
    names.update(ref["digest"][7:] for ref in references)
    for name in sorted(names):
        path = root / name
        row = {"digest": "sha256:" + path.name, "encoding": "base64"}
        try:
            if path.is_symlink() or not path.is_file():
                raise ValueError("Artifact is not a regular file")
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != path.name:
                raise ValueError("Artifact digest mismatch")
            row.update(size_bytes=len(content), data=base64.b64encode(content).decode("ascii"))
        except (ValueError, OSError) as exc:
            row["error"] = str(exc)
        artifacts.append(row)
    return artifacts
