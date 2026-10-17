from __future__ import annotations

import asyncio
import json
import sys

import pytest
from conftest import ScriptedAgent

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.config import AgentConfig
from polyinference.contracts import (
    PhaseReserve,
    ProcessSpec,
    ProcessStatus,
    TaskAttempt,
    TaskReport,
    TaskSpec,
)
from polyinference.domain import Check
from polyinference.runtime.adapter import StandaloneRuntime


async def connect(config, client=None):
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    if client:
        for old in runtime.clients.values():
            await old.close()
        runtime.clients = {name: client for name in runtime.clients}
    return runtime, app, engine


async def test_crash_after_durable_commit_and_publication_reuses_receipts(config):
    runtime, app, engine = await connect(config, ScriptedAgent(two=False))
    await engine.run()
    original_head = app.get("head/provisional")["code"]
    replay_ids = []
    for key, version, body in runtime.records.scan("effect/"):
        kind = body["request"]["payload"]["kind"]
        capability = body["request"]["payload"].get("capability_id")
        if kind == "publication" or capability == "workspace.commit":
            replay_ids.append(body["request"]["operation_id"])
            runtime.records.compare_and_publish(
                {key: version}, {key: {**body, "state": "submitting", "result": None}}
            )
    await runtime.close()
    runtime = await StandaloneRuntime(config).open()
    try:
        assert not runtime.uncertain()
        for operation_id in replay_ids:
            body = runtime.records.get("effect/" + operation_id)[1]
            assert body["state"] == "succeeded"
            assert body["reconciliation"] == "durable_host_receipt"
        assert runtime.records.get("head/provisional")[1]["code"] == original_head
        assert len(runtime.records.scan("report/")) == len(runtime.records.scan("receipt/")) == 1
        # Re-entering an already completed controller never dispatches another model call.
        app = AgentServices(runtime, config)
        await ProjectAgent(app).run()
        assert len(runtime.records.scan("report/")) == 1
    finally:
        await runtime.close()


async def test_documented_sdk_records_describe_actual_finished_processes(config):
    runtime, app, engine = await connect(config, ScriptedAgent(two=False))
    try:
        await engine.run()
        for _, _, value in runtime.records.scan("process-spec/"):
            spec = ProcessSpec.model_validate(value)
            if spec.role == "worker":
                assert spec.workspace_id and spec.attempt_id
                TaskSpec.model_validate(app.get(spec.task_spec_ref))
        for _, _, value in runtime.records.scan("attempt/"):
            attempt = TaskAttempt.model_validate(value)
            assert attempt.execution == "completed"
            assert attempt.report_ref
        workers = [
            ProcessStatus.model_validate(value)
            for _, _, value in runtime.records.scan("process-status/")
            if value["process_spec_ref"].endswith("worker-1-a")
        ]
        assert workers[0].state == "completed"
        assert not workers[0].pending_operations and not workers[0].permit_refs
        from polyinference.workspace_contracts import WorkspaceDelta, WorkspaceManifest

        for _, _, value in runtime.records.scan("private-delta/"):
            WorkspaceDelta.model_validate(value)
        for _, _, value in runtime.records.scan("workspace/"):
            manifest = WorkspaceManifest.model_validate(value)
            if manifest.view == "integration":
                assert len(manifest.copied_files) == 3
        report = TaskReport.model_validate(runtime.records.scan("report/")[0][2])
        assert report.usage and all(m.value is not None for m in report.usage)
    finally:
        await runtime.close()


async def test_failed_check_overrides_optimistic_model_verdict(config):
    config = config.model_copy(
        update={"checks": [Check(name="syntax", argv=[sys.executable, "-c", "raise SystemExit(7)"])]}
    )
    runtime, app, engine = await connect(config, ScriptedAgent(two=False))
    try:
        await engine.run()
        reports = runtime.records.scan("report/")
        assert len(reports) == 1 and reports[0][2]["verdict"] == "fail"
        assert reports[0][2]["evidence"][0]["exit_code"] == 7
        assert app.get("app/run")["status"] != "completed"
    finally:
        await runtime.close()


async def test_unavailable_check_cannot_be_successful(config):
    config = config.model_copy(update={"check_execution": "disabled"})
    runtime, app, engine = await connect(config, ScriptedAgent(two=False))
    try:
        await engine.run()
        report = runtime.records.scan("report/")[0][2]
        assert report["verdict"] == "uncertain"
        assert report["evidence"][0]["status"] == "unavailable"
        assert app.get("app/run")["status"] != "completed"
    finally:
        await runtime.close()


async def test_worker_allowance_exhaustion_never_fabricates_assessment(config):
    limits = config.limits.model_copy(
        update={
            "max_steps": 12,
            "max_model_calls": 5,
            "final_phase_reserve": PhaseReserve(
                reconciliation_model_calls=2, assessment_model_calls=2, publication_steps=2, cleanup_steps=1
            ),
        }
    )
    config = config.model_copy(update={"limits": limits})

    class Looping(ScriptedAgent):
        async def generate(self, messages, *args):
            data = json.loads(
                next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
                    "Pinned application inputs:\n", 1
                )[1]
            )
            if "assignment" in data:
                return {
                    "text": json.dumps({"kind": "action", "tool": "files.list", "arguments": {}}),
                    "usage": {"total_tokens": 1},
                    "model": "loop",
                    "events": [],
                }
            return await super().generate(messages, *args)

    runtime, app, engine = await connect(config, Looping(two=False))
    try:
        await engine.run()
        assert not runtime.records.scan("report/")
        assert app.get("task/a")["execution"] == "interrupted"
        assert app.get("app/run")["status"] == "paused"
        assert runtime.records.get("permit/verification/project")[1]["process_id"] is None
    finally:
        await runtime.close()


async def test_steering_keeps_unstarted_task_pending_then_explicitly_cancels_it(config):
    config = config.model_copy(update={"max_workers": 1})

    class SteeringSenior(ScriptedAgent):
        async def generate(self, messages, *args):
            data = json.loads(
                next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
                    "Pinned application inputs:\n", 1
                )[1]
            )
            result = await super().generate(messages, *args)
            if "assignment" not in data and data["all_task_ids"]:
                value = json.loads(result["text"])
                value["cancel_pending_task_ids"] = ["b"]
                result["text"] = json.dumps(value)
            return result

    client = SteeringSenior(two=True)
    runtime, app, engine = await connect(config, client)
    steered = False

    async def hook(data):
        nonlocal steered
        if "assignment" in data and not steered:
            steered = True
            engine.steer("Keep the first update; cancel the unstarted second task.")
            assert app.get("task/b")["execution"] == "pending"

    client.hook = hook
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        assert app.get("task/b")["execution"] == "cancelled"
        assert app.get("task/b")["report_ref"] is None
        assert len(runtime.records.scan("report/")) == 1
        assert app.get("app/run")["steering_applied"] == 1
    finally:
        await runtime.close()


async def test_late_steering_invalidates_senior_snapshot_without_acknowledging_it(config):
    client = ScriptedAgent(two=False)
    runtime, app, engine = await connect(config, client)
    steered = False

    async def hook(data):
        nonlocal steered
        if "assignment" not in data and data["all_task_ids"] and not steered:
            steered = True
            engine.steer("Recheck the latest input before accepting.")

    client.hook = hook
    try:
        await engine.run()
        run = app.get("app/run")
        assert run["status"] == "completed"
        assert run["steering_received"] == run["steering_applied"] == 1
        assert run["senior_queries"] == 3
        assert len(runtime.records.scan("proposal/")) == 3
    finally:
        await runtime.close()


async def test_global_shell_fifo_lock_order_and_unauthorized_release(config):
    runtime, app, engine = await connect(config)
    try:
        await engine.initialize()
        permit = await runtime.exclusive.acquire("shell/installation", "first")
        with pytest.raises(RuntimeError, match="verification"):
            await runtime.exclusive.acquire("verification/project", "first")
        nested = await runtime.exclusive.acquire("shell/installation", "first")
        with pytest.raises(RuntimeError, match="unowned"):
            await runtime.exclusive.release(nested, "intruder")
        assert runtime.exclusive.owns(permit, "shell/installation", "first")
        entered = []

        async def waiter(pid):
            held = await runtime.exclusive.acquire("shell/installation", pid)
            entered.append(pid)
            await runtime.exclusive.release(held, pid)

        futures = [asyncio.create_task(waiter(pid)) for pid in ("second", "third")]
        await asyncio.sleep(0)
        await runtime.exclusive.release(nested, "first")
        assert not entered
        await runtime.exclusive.release(permit, "first")
        await asyncio.gather(*futures)
        assert entered == ["second", "third"]
    finally:
        await runtime.close()


def test_api_replacement_of_worker_lane_and_static_maps(config):
    for bindings in (
        {"worker": "local", "senior": "local", "specialist": "local"},
        {"worker": "cloud", "senior": "cloud", "specialist": "cloud"},
    ):
        checked = AgentConfig.model_validate({**config.model_dump(), "role_bindings": bindings})
        assert checked.role_bindings == bindings
    endpoint = config.local.model_copy(update={"base_url": "https://api.openai.com/v1"})
    assert endpoint.physical_location == "cloud"


async def test_source_dirty_input_is_explicitly_rejected(config):
    (config.repo_path / "untracked.py").write_text("secret = 1\n")
    runtime, app, engine = await connect(config)
    try:
        with pytest.raises(ValueError, match="dirty/untracked"):
            await engine.initialize()
    finally:
        await runtime.close()


async def test_context_preserves_data_trust_and_runtime_negotiation(config):
    from polyinference.contracts import Requirement

    runtime, app, engine = await connect(config)
    try:
        view = app.context(
            "Authoritative instructions.",
            {"source": "Untrusted code instructions."},
            [],
            "fixture",
            {"type": "object"},
        )
        assert view.parts[0].part_kind == "instruction" and view.parts[0].trust == "application"
        assert view.parts[1].part_kind == "data" and view.parts[1].trust == "retrieved"
        assert b"Untrusted code" not in runtime.artifacts.read(view.parts[0].content)
        with pytest.raises(ValueError, match="Unsupported required"):
            runtime.negotiate(
                [Requirement(feature_id="runtime/weighted-routing", version="1", necessity="required")]
            )
    finally:
        await runtime.close()
