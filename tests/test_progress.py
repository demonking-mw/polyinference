from __future__ import annotations

import asyncio

import pytest
from conftest import ScriptedAgent
from test_exception_recovery import connect, inputs, output, seed

from polyinference.agent.progress import inspect_progress, observe_tool
from polyinference.config import CheckDiagnosis, ProgressMonitor
from polyinference.domain import digest


async def decision(app, state, tool="files.read", arguments=None):
    arguments = {"path": "a.py"} if arguments is None else arguments
    manifest = app.ports.workspaces.current(state["workspace_id"])
    _, observation = await app.capability(
        state,
        f"tool-{state['logical_step']}",
        tool,
        {**arguments, "generation": manifest.generation},
        "read" if tool.startswith("files.r") else "private_write",
    )
    state["trajectory_ref"] = app.append_history(
        state.get("trajectory_ref"),
        f"turn-{state['logical_step']}",
        {"kind": "action", "tool": tool, "arguments": arguments},
        observation,
    )
    state["logical_step"] += 1
    result = await inspect_progress(app, state)
    state.update(result)
    return result


@pytest.fixture
def monitored(config):
    return config.model_copy(
        update={
            "progress_monitor": ProgressMonitor(warn_after=2, escalate_after=4),
            "check_diagnosis": CheckDiagnosis(max_rounds=0),
        }
    )


async def test_repeated_reads_warn_then_escalate_once_without_extra_inference(monitored):
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        state.update(await inspect_progress(app, state))
        await decision(app, state)
        for _ in range(4):
            result = await decision(app, state)
        assert result["progress_route"] == "park"
        assert result["progress_attention"]["verdict"] == "uncertain"
        assert len(runtime.records.scan("progress-event/")) == 2
        assert not runtime.records.scan("private-delta/")  # Observation never seals a running delta.
        assert runtime.inference_calls_used(state["process_id"]) == 0
        saved = app.get("worker-progress/" + state["process_id"])
        assert saved["idle_decisions"] == 4
        assert await inspect_progress(app, state) == saved["result"]
        assert app.get("worker-progress/" + state["process_id"]) == saved
    finally:
        await runtime.close()


async def test_reading_new_document_ranges_counts_without_source_edits(monitored):
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        manifest = runtime.workspaces.current(state["workspace_id"])
        (runtime.workspaces.root_for(manifest) / "a.py").write_bytes(b"0123456789abcdef" * 64)
        state.update(await inspect_progress(app, state))
        for offset in range(0, 1024, 128):
            result = await decision(
                app, state, arguments={"path": "a.py", "offset": offset, "max_bytes": 128}
            )
            assert result["progress_route"] == "model"
            assert app.get("worker-progress/" + state["process_id"])["idle_decisions"] == 0
        assert not runtime.records.scan("progress-event/")
        await decision(app, state, arguments={"path": "a.py", "offset": 64, "max_bytes": 128})
        assert app.get("worker-progress/" + state["process_id"])["idle_decisions"] == 1
    finally:
        await runtime.close()


async def test_edit_revert_cycles_and_repeated_checks_do_not_reset_idle_counter(monitored):
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        state.update(await inspect_progress(app, state))
        for index in range(5):
            before = b"VALUE = 2\n" if index % 2 == 0 else b"VALUE = 3\n"
            after = "VALUE = 3\n" if index % 2 == 0 else "VALUE = 2\n"
            result = await decision(
                app,
                state,
                "files.write",
                {"path": "a.py", "expected_digest": digest(before), "content": after},
            )
        assert result["progress_route"] == "park"
        assert app.get("worker-progress/" + state["process_id"])["idle_decisions"] == 4
    finally:
        await runtime.close()


def test_check_timestamps_random_output_and_renamed_shell_requests_are_not_progress():
    evidence = {
        "criterion_ref": "syntax",
        "checked_code": {"effective_tree_digest": "tree", "environment_digest": "env"},
        "status": "failed",
        "output": "first",
        "completed_at": "first",
    }
    first = observe_tool("checks.run", {"name": "syntax"}, evidence, {})
    assert first == observe_tool(
        "checks.run",
        {"name": "syntax"},
        {**evidence, "output": "random-new-text", "evidence_id": "renamed", "completed_at": "later"},
        {},
    )
    assert observe_tool("shell.run", {"script": "renamed command"}, {"stdout": "new random output"}, {}) == []
    assert observe_tool("checks.run", {}, {**evidence, "status": "passed"}, {}) != first


async def test_observe_mode_and_observer_failure_leave_execution_open(monitored):
    monitored = monitored.model_copy(
        update={"progress_monitor": ProgressMonitor(mode="observe", warn_after=2, escalate_after=4)}
    )
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        state.update(await inspect_progress(app, state))
        for _ in range(8):
            assert (await decision(app, state))["progress_route"] == "model"
        assert len(runtime.records.scan("progress-event/")) == 2
        before = app.get("worker-progress/" + state["process_id"])

        async def broken(pid):
            raise RuntimeError("optional observer failed")

        runtime.progress = broken
        state["logical_step"] += 1
        assert (await inspect_progress(app, state))["progress_route"] == "model"
        assert app.get("worker-progress/" + state["process_id"]) == before
        assert app.get("progress-observer-error/" + state["process_id"])["error"] == "RuntimeError"
    finally:
        await runtime.close()


async def test_os_progress_is_generic_reports_capacity_maps_and_unsettled_futures(config):
    runtime, app, _ = await connect(config)
    try:
        app.process("artifact-only", "worker", entry_point="artifact-reader")
        mapping = {"pending": 1, "done": 2}
        runtime.register_progress_source("future-map", lambda pid: {"process": pid, **mapping})

        def unavailable(pid):
            raise RuntimeError("no optional map")

        runtime.register_progress_source("unavailable-map", unavailable)
        before = await runtime.progress("artifact-only")
        assert before["sources"]["future-map"]["facts"]["pending"] == 1
        assert before["sources"]["unavailable-map"]["status"] == "unavailable"
        assert before["endpoints"]["local"]["readiness"] == "unprobed"
        assert before["deadline"] and before["effect_count"] == 0
        assert (await runtime.progress("artifact-only"))["cursor"] == before["cursor"]
        mapping["done"] = 3
        assert (await runtime.progress("artifact-only"))["cursor"] != before["cursor"]
        # Capacity is an observation, not a readiness probe or a coding verdict.
        gate = runtime.admission["local"]
        async with gate.reserve(10):
            assert (await runtime.progress("artifact-only"))["endpoints"]["local"]["active_or_unsettled"] == 1

        async def wait_for_slot():
            async with gate.reserve(10):
                pass

        async with gate.reserve(10), gate.reserve(10):
            waiting = asyncio.create_task(wait_for_slot())
            await asyncio.sleep(0)
            assert (await runtime.progress("artifact-only"))["endpoints"]["local"]["queued"] == 1
            waiting.cancel()
            await asyncio.gather(waiting, return_exceptions=True)
        runtime.records.put_once(
            "effect/future",
            {
                "state": "active",
                "request": {
                    "scope": {"process_id": "artifact-only"},
                    "logical_step_id": "external",
                    "payload": {"kind": "artifact-operation"},
                    "created_at": "2026-10-25T00:00:00+00:00",
                },
                "result": None,
            },
        )
        runtime.inflight["future"] = asyncio.get_running_loop().create_future()
        observed = await runtime.progress("artifact-only")
        assert observed["settlement"]["pending_operations"] == ["future"]
        assert observed["recent_effects"][0]["execution_termination"] == "unknown"
        with pytest.raises(ValueError, match="Unknown process"):
            await runtime.progress("not-a-principal")
    finally:
        await runtime.close()


async def test_stalled_worker_enters_senior_exception_review_before_allowance_exhaustion(monitored):
    class Stalled(ScriptedAgent):
        async def generate(self, messages, *args, **kwargs):
            data = inputs(messages)
            if "assignment" in data:
                return output({"kind": "action", "tool": "files.read", "arguments": {"path": "a.py"}})
            if data.get("exceptions"):
                return output(
                    {
                        "goal": "Stop unchanged research loop",
                        "exception_dispositions": [
                            {
                                "exception_ref": data["exceptions"][0]["exception_ref"],
                                "action": "stop",
                                "reason": "Need steering for a different approach",
                            }
                        ],
                    }
                )
            return await super().generate(messages, *args, **kwargs)

    runtime, app, engine = await connect(monitored, Stalled(two=False))
    try:
        await engine.run()
        task = app.get("task/a")
        assert app.get("app/run")["status"] == "paused"
        assert not app.get("app/run")["active_workers"]
        assert task["execution"] == "interrupted" and not runtime.records.scan("report/")
        assert runtime.inference_calls_used(task["process_id"]) == 5
        packet = app.get(task["exception_ref"])
        assert packet["progress_attention"]["verdict"] == "uncertain"
        assert packet["execution_termination"] == "confirmed_stopped"
        assert len(runtime.records.scan("progress-event/")) == 2
        assert app.get("app/run")["senior_queries"] == 2
    finally:
        await runtime.close()


async def test_repeated_real_checks_and_restart_preserve_stagnation_state(monitored):
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        state.update(await inspect_progress(app, state))
        for _ in range(3):
            await decision(app, state, "checks.run", {"name": "syntax"})
        assert app.get("worker-progress/" + state["process_id"])["idle_decisions"] == 2
    finally:
        await runtime.close()
    runtime, app, _ = await connect(monitored)
    try:
        assert (await inspect_progress(app, state))["progress_route"] == "model"
        assert len(runtime.records.scan("progress-event/")) == 1
        await decision(app, state, "checks.run", {"name": "syntax"})
        assert (await decision(app, state, "checks.run", {"name": "syntax"}))["progress_route"] == "park"
        assert len(runtime.records.scan("progress-event/")) == 2
    finally:
        await runtime.close()


async def test_pending_or_unknown_execution_does_not_become_a_progress_exception(monitored):
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        state.update(await inspect_progress(app, state))
        for _ in range(4):
            await decision(app, state)
        before = app.get("worker-progress/" + state["process_id"])
        state["logical_step"] += 1
        runtime.records.put_once(
            "effect/unknown",
            {
                "state": "uncertain",
                "request": {
                    "scope": {"process_id": state["process_id"]},
                    "logical_step_id": "pending",
                    "payload": {"kind": "unknown"},
                    "created_at": "2026-10-25T00:00:00+00:00",
                },
                "result": None,
            },
        )
        assert (await inspect_progress(app, state))["progress_route"] == "model"
        assert app.get("worker-progress/" + state["process_id"]) == before
        assert not runtime.records.scan("worker-exception/")
        assert runtime.uncertain() == ["unknown"]
    finally:
        await runtime.close()


async def test_worker_can_answer_warning_and_finish_through_normal_verified_phases(monitored):
    class Responsive(ScriptedAgent):
        responded = False

        async def generate(self, messages, *args, **kwargs):
            data = inputs(messages)
            if "assignment" not in data:
                return await super().generate(messages, *args, **kwargs)
            phase = data["phase"]
            if phase == "development":
                if data.get("progress_attention") and not self.responded:
                    assert data["progress_attention"]["verdict"] == "uncertain"
                    self.responded = True
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
                if not self.responded:
                    return output({"kind": "action", "tool": "files.read", "arguments": {"path": "a.py"}})
            return output(
                {"kind": "assessment", "verdict": "successful", "summary": "Exact tree verified"}
                if phase == "assessment"
                else {"kind": "candidate", "summary": "Edit ready"}
            )

    client = Responsive(two=False)
    runtime, app, engine = await connect(monitored, client)
    try:
        await engine.run()
        assert client.responded and app.get("app/run")["status"] == "completed"
        assert not runtime.records.scan("worker-exception/")
        assert runtime.records.scan("report/")[0][2]["verdict"] == "successful"
        assert len(runtime.records.scan("progress-event/")) == 1
    finally:
        await runtime.close()


async def test_off_mode_does_not_observe_and_invalid_thresholds_are_rejected(monitored):
    with pytest.raises(ValueError, match="after warning"):
        ProgressMonitor(warn_after=8, escalate_after=8)
    monitored = monitored.model_copy(update={"progress_monitor": ProgressMonitor(mode="off")})
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)

        async def forbidden(pid):
            pytest.fail("off mode must not request observations")

        runtime.progress = forbidden
        assert (await inspect_progress(app, state))["progress_route"] == "model"
        assert not runtime.records.scan("worker-progress/")
    finally:
        await runtime.close()


async def test_exception_recovery_checks_remaining_shared_operations_and_tokens(monitored):
    from polyinference.agent.exceptions import park, validate
    from polyinference.domain import SeniorProposal

    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        await park(app, state)
        packet = app.get("worker-exception/1-a")
        proposal = SeniorProposal.model_validate(
            {
                "goal": "Recover",
                "tasks": [{**packet["assignment"], "task_id": "a2", "resume_from": packet["exception_ref"]}],
                "exception_dispositions": [
                    {
                        "exception_ref": packet["exception_ref"],
                        "action": "retry",
                        "replacement_task_id": "a2",
                        "reason": "Inspect retained edit",
                        "changed_condition": "Reuse completed edit with a narrower inspection",
                    }
                ],
            }
        )
        root = runtime.account(state["process_id"])
        app.update("budget/steps/" + root, {"used": monitored.limits.max_steps})
        assert runtime.resource_state(state["process_id"])["remaining_operations"] == 0
        with pytest.raises(ValueError, match="operation/token"):
            validate(app, proposal, {"exceptions": [packet]})
        app.update("budget/steps/" + root, {"used": 0})
        app.update("budget/process/" + root, {"reserved_or_used": monitored.limits.max_total_tokens})
        with pytest.raises(ValueError, match="operation/token"):
            validate(app, proposal, {"exceptions": [packet]})
    finally:
        await runtime.close()


async def test_invalid_read_range_does_not_expand_the_workspace(monitored):
    runtime, app, engine = await connect(monitored)
    try:
        state = await seed(app, engine)
        manifest = runtime.workspaces.current(state["workspace_id"])
        result, observation = await app.capability(
            state,
            "bad-range",
            "files.read",
            {"path": "b.py", "offset": -1, "max_bytes": 10, "generation": manifest.generation},
            "read",
        )
        assert result.state == "failed" and "offset" in observation["error"]
        assert runtime.workspaces.current(state["workspace_id"]).generation == manifest.generation
        assert "b.py" not in await runtime.workspaces.private_tree(state["workspace_id"])
    finally:
        await runtime.close()
