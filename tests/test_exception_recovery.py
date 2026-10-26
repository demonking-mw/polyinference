from __future__ import annotations

import json

import pytest
from conftest import ScriptedAgent

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.exceptions import park, validate
from polyinference.agent.services import AgentServices
from polyinference.agent.tasks import make_task
from polyinference.config import CheckDiagnosis
from polyinference.contracts import ArtifactRef, CodeRevision, OperationRequest, TaskAttempt
from polyinference.domain import Assignment, SeniorProposal, digest, operation_fingerprint
from polyinference.runtime.adapter import StandaloneRuntime


def inputs(messages):
    return json.loads(
        next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
            "Pinned application inputs:\n", 1
        )[1]
    )


def output(reply):
    return {"text": json.dumps(reply), "usage": {"total_tokens": 10}, "model": "fixture", "events": []}


async def connect(config, client=None):
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    if client:
        for old in runtime.clients.values():
            await old.close()
        runtime.clients = {name: client for name in runtime.clients}
    await engine.initialize()
    return runtime, app, engine


async def seed(app, engine):
    assignment = Assignment(task_id="a", objective="Update a", write_paths=["a.py"], checks=["syntax"])
    task, specs = make_task(app, assignment, "plan/test", app.get("head/provisional")["code"], "1-a")
    task["execution"] = "in_progress"
    app.ports.records.compare_and_publish(
        {"task/a": 0, "app/run": app.ports.records.get("app/run")[0]},
        {
            "task/a": task,
            "app/run": {
                **app.get("app/run"),
                "active_workers": [task["process_id"]],
                "captured_workers": [task["process_id"]],
            },
        },
        specs,
    )
    app.process(task["process_id"], "worker", task["spec_ref"], task)
    manifest = await app.ports.workspaces.create(
        task["workspace_id"],
        task["process_id"],
        task["spec_ref"],
        CodeRevision.model_validate(task["base"]),
        ["a.py"],
        [],
    )
    (app.ports.workspaces.root_for(manifest) / "a.py").write_text("VALUE = 2\n")
    return {
        "process_id": task["process_id"],
        "task_ledger_ref": "task/a",
        "task_spec_ref": task["spec_ref"],
        "attempt_id": task["attempt_id"],
        "workspace_id": task["workspace_id"],
        "phase": "development",
        "logical_step": 2,
        "interrupted": "Need a narrower check " * 100,
        "evidence": [],
        "verification_permit_ref": None,
    }


class Recovering(ScriptedAgent):
    async def generate(self, messages, *args, **kwargs):
        data = inputs(messages)
        if data.get("exceptions"):
            packet = data["exceptions"][0]
            return output(
                {
                    "goal": "Finish retained source with a narrower inspection",
                    "exception_dispositions": [
                        {
                            "exception_ref": packet["exception_ref"],
                            "action": "retry",
                            "reason": "Keep existing source and assess it",
                            "changed_condition": "Reuse completed edit; inspect exact syntax result",
                            "replacement_task_id": "a2",
                        }
                    ],
                    "tasks": [
                        {
                            "task_id": "a2",
                            "objective": "Validate and finish the retained a.py edit",
                            "write_paths": ["a.py"],
                            "checks": ["syntax"],
                            "resume_from": packet["exception_ref"],
                        }
                    ],
                }
            )
        if "assignment" in data:
            name, phase = data["assignment"]["task_id"], data["phase"]
            if name == "a" and phase == "development":
                count = self.counts.get((name, phase), 0)
                self.counts[(name, phase)] = count + 1
                if not count:
                    return output(
                        {
                            "kind": "action",
                            "tool": "files.write",
                            "arguments": {
                                "path": "a.py",
                                "expected_digest": digest(b"VALUE = 1\n"),
                                "content": "VALUE = 2\n",
                            },
                        }
                    )
                return output({"kind": "needs_review", "reason": "Need a narrower inspection " * 50})
            if name == "a2":
                return output(
                    {"kind": "assessment", "verdict": "successful", "summary": "Checked retained exact tree"}
                    if phase == "assessment"
                    else {"kind": "candidate", "summary": "Retained edit is ready"}
                )
        return await super().generate(messages, *args, **kwargs)


async def test_clean_exception_recovers_with_source_lineage_and_shared_allowance(config):
    config = config.model_copy(update={"check_diagnosis": CheckDiagnosis(max_rounds=0)})
    runtime, app, engine = await connect(config, Recovering(two=False))
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        old, new = app.get("task/a"), app.get("task/a2")
        assert old["execution"] == "interrupted" and old["replacement_task_id"] == "a2"
        attempt = TaskAttempt.model_validate(app.get("attempt/" + old["attempt_id"]))
        assert attempt.stop_reason == "needs_review"
        assert app.get("attempt/" + new["attempt_id"])["previous_attempt_ref"] == attempt.record_id
        assert runtime.account(new["process_id"]) == old["process_id"]
        assert runtime.inference_calls_used(new["process_id"]) == 5
        assert not app.get("app/run")["active_workers"]
        assert not app.get("app/run")["captured_workers"]
        assert runtime.records.get("handoff/" + new["workspace_id"])
        head = CodeRevision.model_validate(app.get("head/provisional")["code"])
        assert (await runtime.workspaces.tree(head.commit_id))["a.py"][1] == b"VALUE = 2\n"
        await engine.consume()
        assert not engine.workers
    finally:
        await runtime.close()


async def test_parking_replays_after_fence_without_restarting_or_losing_source(config):
    runtime, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        fence = runtime.park_process

        def crash(pid):
            fence(pid)
            raise RuntimeError("crash after fence")

        runtime.park_process = crash
        with pytest.raises(RuntimeError, match="crash after fence"):
            await park(app, state)
        assert app.get("task/a")["execution"] == "in_progress"
        runtime.park_process = fence
        await park(app, state)
        await park(app, state)
        await engine.consume()
        assert not engine.workers and not app.get("app/run")["active_workers"]
        assert len(runtime.records.scan("worker-exception/")) == 1
        assert app.get("attempt/1-a")["stop_reason"] == "needs_review"
        assert app.get("process-status/" + state["process_id"])["cleanup_state"] == "complete"
        delta = app.get("private-delta/workspace-1-a")
        assert (
            runtime.artifacts.read(ArtifactRef.model_validate(delta["changes"][0]["content"]))
            == b"VALUE = 2\n"
        )
    finally:
        await runtime.close()


async def test_fence_refuses_ownership_and_unsettled_effects(config):
    runtime, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        pid = state["process_id"]
        permit = await runtime.exclusive.acquire("verification/project", pid)
        with pytest.raises(RuntimeError, match="unsettled"):
            runtime.park_process(pid)
        await runtime.exclusive.release(permit, pid)
        runtime.records.put_once(
            "effect/pending",
            {"state": "uncertain", "request": {"scope": {"process_id": pid}}, "result": None},
        )
        with pytest.raises(RuntimeError, match="unsettled"):
            runtime.park_process(pid)
        assert not runtime.records.get("process-parked/" + pid)
    finally:
        await runtime.close()


async def test_recovery_validation_rejects_renaming_exhaustion_and_unpinned_dispositions(config):
    runtime, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        await park(app, state)
        packet = app.get("worker-exception/1-a")
        raw = {
            "goal": "Retry",
            "exception_dispositions": [
                {
                    "exception_ref": packet["exception_ref"],
                    "action": "retry",
                    "reason": "Retry",
                    "changed_condition": "Try again",
                    "replacement_task_id": "a2",
                }
            ],
            "tasks": [{**app.get("task/a")["assignment"], "task_id": "a2"}],
        }
        with pytest.raises(ValueError, match="Renaming"):
            validate(app, SeniorProposal.model_validate(raw), {"exceptions": [packet]})
        raw["tasks"][0]["objective"] = "Inspect a narrower boundary"
        runtime.records.put_once(
            "budget/model-calls/" + state["process_id"], {"used": config.limits.max_model_calls}
        )
        with pytest.raises(ValueError, match="cannot refill"):
            validate(app, SeniorProposal.model_validate(raw), {"exceptions": [packet]})
        with pytest.raises(ValueError, match="pinned"):
            validate(app, SeniorProposal.model_validate(raw), {"exceptions": []})
    finally:
        await runtime.close()


async def test_recovery_charges_physical_retries_once_and_preserves_replay_and_cutoff(config):
    from test_inference_retry import READY, prepare

    runtime, app, state, client = await prepare(config, ["invalid", READY])
    try:
        assert (await app.model(state))["kind"] == "candidate"
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        assert client.calls == 2
        runtime.park_process("fixture")
        assert (await runtime.execute(request)).state == "succeeded"
        assert client.calls == 2  # Replay still precedes the generation fence.
        app.process("replacement", "worker")
        runtime.bind_recovery("replacement", "fixture")
        await runtime.workspaces.create(
            "replacement-ws",
            "replacement",
            "test",
            CodeRevision.model_validate(app.get("head/provisional")["code"]),
            ["a.py"],
            [],
        )
        child = {**state, "process_id": "replacement", "workspace_id": "replacement-ws"}
        assert (await app.model(child))["kind"] == "candidate"
        assert client.calls == runtime.inference_calls_used("replacement") == 3
        assert not runtime.records.get("budget/model-calls/replacement")
        assert app.get("budget/steps/fixture")["used"] == 2
        assert not runtime.records.get("budget/process/replacement")
        child_request = OperationRequest.model_validate(app.get("request/replacement/model-0"))
        assert child_request.deadline <= request.deadline
        changed = child_request.model_copy(
            update={
                "operation_id": "new-inflated",
                "limits": child_request.limits.model_copy(update={"max_model_calls": 1000}),
            }
        )
        changed = changed.model_copy(update={"intent_digest": operation_fingerprint(changed)})
        with pytest.raises(ValueError, match="inherited"):
            await runtime.execute(changed)
        new = request.model_copy(
            update={
                "operation_id": "new-on-parked",
                "owner_generation": app.get("process/fixture")["owner_generation"],
            }
        )
        new = new.model_copy(update={"intent_digest": operation_fingerprint(new)})
        with pytest.raises(ValueError, match="Parked"):
            await runtime.execute(new)
    finally:
        await runtime.close()


async def test_integration_exception_keeps_original_delta_separate_and_rejects_conflicting_reuse(config):
    runtime, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        pid, wid = state["process_id"], state["workspace_id"]
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        permit = await runtime.exclusive.acquire("verification/project", pid)
        integrated = await runtime.workspaces.integrate(wid, base, permit)
        (runtime.workspaces.root_for(integrated) / "a.py").write_text("VALUE = 4\n")
        await park(app, {**state, "phase": "reconciliation", "verification_permit_ref": permit})
        packet = app.get("worker-exception/1-a")
        assert (
            runtime.workspaces.snapshot_root(packet["abandoned_view_ref"]) / "a.py"
        ).read_text() == "VALUE = 4\n"
        delta = app.get(packet["source_delta_ref"])
        assert (
            runtime.artifacts.read(ArtifactRef.model_validate(delta["changes"][0]["content"]))
            == b"VALUE = 2\n"
        )
        assert not runtime.exclusive.owns(permit, "verification/project", pid)
        with pytest.raises(ValueError, match="write grant"):
            await runtime.workspaces.validate_handoff(packet["source_delta_ref"], base, ["b.py"])
        # A different current base on the same path requires explicit repair, never blind reuse.
        await runtime.workspaces.create("other", "controller", "test", base, ["a.py"], [])
        other_permit = await runtime.exclusive.acquire("verification/project", "controller")
        try:
            other = await runtime.workspaces.integrate("other", base, other_permit)
            (runtime.workspaces.root_for(other) / "a.py").write_text("VALUE = 3\n")
            new_commit = await runtime.workspaces.commit("other", base, "test-conflicting-base")
        finally:
            await runtime.exclusive.release(other_permit, "controller")
        with pytest.raises(ValueError, match="conflicts"):
            await runtime.workspaces.validate_handoff(packet["source_delta_ref"], new_commit, ["a.py"])
    finally:
        await runtime.close()


def test_replacement_requires_atomic_replanning_of_pending_dependents():
    from polyinference.agent.architecture import validate_plan

    a = Assignment(task_id="a", objective="Provide a", write_paths=["a.py"], checks=["syntax"])
    b = Assignment(
        task_id="b", objective="Use a", write_paths=["b.py"], checks=["syntax"], dependencies=["a"]
    )
    tasks = [
        {"assignment": a.model_dump(mode="json"), "execution": "interrupted", "attempt_id": "1-a"},
        {"assignment": b.model_dump(mode="json"), "execution": "pending"},
    ]
    proposal = SeniorProposal.model_validate(
        {
            "goal": "Recover",
            "tasks": [{**a.model_dump(mode="json"), "task_id": "a2"}],
            "exception_dispositions": [
                {
                    "exception_ref": "worker-exception/1-a",
                    "action": "retry",
                    "replacement_task_id": "a2",
                    "changed_condition": "Narrower inspection",
                    "reason": "Recover",
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="cancelled dependency"):
        validate_plan(proposal, tasks, {})
    fixed = proposal.model_copy(
        update={
            "cancel_pending_task_ids": ["b"],
            "tasks": [*proposal.tasks, b.model_copy(update={"task_id": "b2", "dependencies": ["a2"]})],
        }
    )
    validate_plan(fixed, tasks, {})


def test_schema_compaction_preserves_named_properties_and_literal_values():
    from polyinference.agent.schema import schema_text

    schema = {
        "title": "Display label",
        "type": "object",
        "properties": {"title": {"title": "Field label", "type": "string"}},
        "required": ["title"],
        "const": {"title": "literal"},
    }
    compact = json.loads(schema_text(schema))
    assert compact == {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "const": {"title": "literal"},
    }


async def test_restart_finishes_published_worker_cleanup_without_restarting_development(config, monkeypatch):
    from polyinference.agent import worker

    original = worker.release

    async def crash_before_release(state, runtime):
        raise RuntimeError("crash before cleanup")

    monkeypatch.setattr(worker, "release", crash_before_release)
    runtime, app, engine = await connect(config, ScriptedAgent(two=False))
    try:
        await engine.run()
        task = app.get("task/a")
        assert task["execution"] == "completed" and app.get("app/run")["status"] == "paused"
        assert runtime.records.get("permit/verification/project")[1]["process_id"] == task["process_id"]
        calls = runtime.inference_calls_used(task["process_id"])
    finally:
        await runtime.close()
    monkeypatch.setattr(worker, "release", original)
    runtime, app, engine = await connect(config, ScriptedAgent(two=False))
    try:
        engine.steer("Finish committed worker cleanup and review its existing report")
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        assert runtime.inference_calls_used(task["process_id"]) == calls
        assert len(runtime.records.scan("report/")) == len(runtime.records.scan("receipt/")) == 1
        assert runtime.records.get("permit/verification/project")[1]["process_id"] is None
        assert not app.get("app/run")["active_workers"]
        # A stale active entry for an already completed END graph is detached, not relaunched.
        app.update("app/run", {**app.get("app/run"), "active_workers": [task["process_id"]]})
        await engine.consume()
        assert not app.get("app/run")["active_workers"] and not engine.workers
        assert runtime.inference_calls_used(task["process_id"]) == calls
    finally:
        await runtime.close()
