from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from langgraph.runtime import Runtime
from test_runtime import setup

from polyinference.agent.diagnostics import diagnose
from polyinference.agent.worker import AppContext, diagnose_exception, tool
from polyinference.domain import Check, digest


class Checker:
    def __init__(self, plan):
        self.plan, self.calls = plan, 0

    async def generate(self, messages, *args, **kwargs):
        data = json.loads(
            next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
                "Pinned application inputs:\n", 1
            )[1]
        )
        assert data["check_diagnosis"]
        assert "b.py" in data["available_at_base"]
        assert "output_preview" in data["failure"] if data["failure"] else True
        self.calls += 1
        return {"text": json.dumps(self.plan), "model": "checker", "usage": {"total_tokens": 5}, "events": []}

    async def close(self):
        pass


async def prepared(config, plan, *, role="worker", genuine_failure=False):
    check = Check(
        name="syntax",
        argv=[
            sys.executable,
            "-c",
            "raise AssertionError('real code defect')"
            if genuine_failure
            else "from pathlib import Path; assert 'VALUE' in Path('b.py').read_text()",
        ],
    )
    config = config.model_copy(
        update={
            "checks": [check],
            "check_diagnosis": config.check_diagnosis.model_copy(update={"role": role}),
        }
    )
    runtime, app, _ = await setup(config)
    app.update(
        "fixture-task",
        {
            "assignment": {
                "task_id": "fixture",
                "objective": "bounded",
                "write_paths": ["a.py"],
                "read_paths": ["a.py"],
                "checks": ["syntax"],
            }
        },
    )
    client = Checker(plan)
    lane = config.role_bindings[role]
    await runtime.clients[lane].close()
    runtime.clients[lane] = client
    state = {
        "process_id": "fixture",
        "workspace_id": "fixture-ws",
        "task_ledger_ref": "fixture-task",
        "phase": "development",
        "logical_step": 0,
        "reply": {"kind": "action", "tool": "checks.run", "arguments": {"name": "syntax"}},
    }
    return runtime, app, state, client


async def test_failed_scoped_check_invokes_agent_expands_reads_and_rechecks(config):
    runtime, app, state, client = await prepared(
        config,
        {
            "classification": "missing_inputs",
            "read_paths": ["b.py"],
            "guidance": "The fixture is at pinned B; materialize it read-only.",
        },
    )
    try:
        result = await tool(state, Runtime(context=AppContext(app)))
        assert client.calls == 1 and result["last_check_evidence"]["status"] == "passed"
        manifest = runtime.workspaces.current("fixture-ws")
        assert manifest.generation == 2 and manifest.allowed_write_paths == ["a.py"]
        assert (runtime.workspaces.root_for(manifest) / "b.py").read_text() == "VALUE = 1\n"
        history = app.history(result["trajectory_ref"])
        assert history[0]["observation"]["status"] == "failed"  # Original observation was not rewritten.
        assert history[1]["feedback"]["check_evidence"]["status"] == "passed"
        assert len(runtime.records.scan("diagnosis/")) == 1
        # Replay does not rerun checks, invoke another checker or consume another round.
        again = await tool(state, Runtime(context=AppContext(app)))
        assert again["last_check_evidence"] == result["last_check_evidence"] and client.calls == 1
        assert (config.repo_path / "b.py").read_text() == "VALUE = 1\n"
    finally:
        await runtime.close()


@pytest.mark.parametrize("classification", ["code_failure", "uncertain", "environment"])
async def test_genuine_failure_or_uncertainty_never_becomes_passing_evidence(config, classification):
    runtime, app, state, client = await prepared(
        config,
        {
            "classification": classification,
            "guidance": "Investigate the actual failure; no input expansion proves success.",
        },
        genuine_failure=True,
    )
    try:
        result = await tool(state, Runtime(context=AppContext(app)))
        assert result["last_check_evidence"]["status"] == "failed" and client.calls == 1
        # A later failing check cannot create an unbounded diagnosis loop.
        await tool({**state, "logical_step": 1}, Runtime(context=AppContext(app)))
        assert client.calls == 1
    finally:
        await runtime.close()


async def test_checker_cannot_expand_write_authority(config):
    runtime, app, state, client = await prepared(
        config,
        {
            "classification": "missing_inputs",
            "read_paths": ["not-at-base.py"],
            "guidance": "Try a missing file",
        },
    )
    try:
        result = await tool(state, Runtime(context=AppContext(app)))
        assert result["last_check_evidence"]["status"] == "failed"
        assert runtime.workspaces.current("fixture-ws").allowed_write_paths == ["a.py"]
        assert not (config.repo_path / "not-at-base.py").exists()
        assert (
            app.history(result["trajectory_ref"])[-1]["feedback"]["check_diagnosis"]["classification"]
            == "uncertain"
        )
    finally:
        await runtime.close()


async def test_review_request_is_checked_before_parking(config):
    runtime, app, state, client = await prepared(
        config,
        {
            "classification": "code_failure",
            "guidance": "The helper and test are inside this assignment; reconcile their contradiction.",
        },
    )
    try:
        result = await diagnose_exception(
            {**state, "interrupted": "I think the fix is outside scope"}, Runtime(context=AppContext(app))
        )
        assert result["route"] == "model" and client.calls == 1
        again = await diagnose_exception(
            {**state, "logical_step": 1, "interrupted": "still blocked"}, Runtime(context=AppContext(app))
        )
        assert again["route"] == "park" and client.calls == 1
    finally:
        await runtime.close()


async def test_definition_can_route_checker_to_cloud_native_with_current_readonly_snapshot(config):
    runtime, app, state, _ = await prepared(
        config, {"classification": "uncertain", "guidance": "unused"}, role="specialist"
    )
    # Pin a native endpoint before opening the run in this separate setup.
    await runtime.close()
    cfg = config.model_copy(
        update={
            "state_directory": str(Path(config.state_directory).parent / "native-state"),
            "cloud": config.cloud.model_copy(update={"protocol": "codex_app_server", "brokered_tools": True}),
            "check_diagnosis": config.check_diagnosis.model_copy(update={"role": "specialist"}),
        }
    )
    runtime, app, _ = await setup(cfg)
    app.update(
        "fixture-task",
        {
            "assignment": {
                "task_id": "fixture",
                "objective": "bounded",
                "write_paths": ["a.py"],
                "checks": ["syntax"],
            }
        },
    )

    class Native:
        async def generate_job(self, messages, snapshot, schema, callback=None):
            assert callback is not None and "classification" in schema["properties"]
            assert (Path(snapshot) / "a.py").read_text() == "VALUE = 2\n"
            read = await callback("inspect-source", {"tool": "coding.diagnostic_read", "arguments": {"path": "a.py"}})
            assert read["state"] == "succeeded" and read["observation"]["content"] == "VALUE = 2\n"
            with pytest.raises(ValueError, match="outside grant"):
                await callback("denied-write", {"tool": "files.write", "arguments": {"path": "a.py"}})
            return {
                "text": '{"classification":"code_failure","guidance":"Repair inside the declared scope"}',
                "model": "native-checker",
                "usage": {"total_tokens": 1},
                "events": [],
            }

        async def close(self):
            pass

    await runtime.clients["cloud"].close()
    runtime.clients["cloud"] = Native()
    state = {
        "process_id": "fixture",
        "workspace_id": "fixture-ws",
        "task_ledger_ref": "fixture-task",
        "phase": "development",
        "logical_step": 0,
    }
    try:
        await app.capability(
            state,
            "write",
            "files.write",
            {
                "path": "a.py",
                "content": "VALUE = 2\n",
                "expected_digest": digest(b"VALUE = 1\n"),
                "generation": 1,
            },
            "private_write",
        )
        outcome = await diagnose(app, state, "exception", reason="inspect this change")
        assert outcome["classification"] == "code_failure"
        model = [
            v for _, _, v in runtime.records.scan("effect/") if v["request"]["payload"]["kind"] == "agent_job"
        ][0]
        assert model["request"]["payload"]["role"] == "specialist"
        assert model["request"]["payload"]["allowed_capabilities"] == ["coding.diagnostic_read"]
    finally:
        await runtime.close()
