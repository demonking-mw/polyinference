from __future__ import annotations

import pytest

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.contracts import CodeRevision, OperationRequest
from polyinference.domain import digest, operation_fingerprint
from polyinference.runtime.adapter import StandaloneRuntime, UncertainEffect
from polyinference.runtime.storage import Conflict, Records


async def setup(config):
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    await engine.initialize()
    app.process("fixture", "worker")
    base = CodeRevision.model_validate(app.get("head/provisional")["code"])
    await runtime.workspaces.create("fixture-ws", "fixture", "fixture-spec", base, ["a.py"], ["a.py"])
    return runtime, app, engine


async def test_effect_replay_before_generation_checks_and_changed_intent_denied(config):
    runtime, app, _ = await setup(config)
    try:
        state = {"process_id": "fixture", "workspace_id": "fixture-ws"}
        args = {
            "path": "a.py",
            "content": "VALUE = 9\n",
            "expected_digest": digest(b"VALUE = 1\n"),
            "generation": 1,
        }
        result, _ = await app.capability(state, "write-once", "files.write", args, "private_write")
        assert result.state == "succeeded"
        # Replayed node must use the retained request even though its original content is stale.
        repeated, _ = await app.capability(state, "write-once", "files.write", args, "private_write")
        assert repeated == result
        retained = OperationRequest.model_validate(app.get("request/fixture/write-once"))
        changed = retained.model_copy(
            update={
                "payload": retained.payload.model_copy(
                    update={"arguments": app.artifact({**args, "content": "different"})}
                )
            }
        )
        changed = changed.model_copy(update={"intent_digest": operation_fingerprint(changed)})
        with pytest.raises(ValueError, match="changed intent"):
            await runtime.execute(changed)
        # A distinct stale write is denied and recorded as an observation.
        denied, output = await app.capability(state, "stale-write", "files.write", args, "private_write")
        assert denied.state == "failed" and "current file digest" in output["error"]
    finally:
        await runtime.close()


async def test_unknown_remote_effect_is_not_retried_or_treated_as_cancelled(config):
    runtime, app, _ = await setup(config)
    from polyinference.runtime.inference import UnknownExecution

    class Disconnected:
        calls = 0

        async def generate(self, *args):
            self.calls += 1
            raise UnknownExecution("after send")

        async def close(self):
            pass

    client = Disconnected()
    await runtime.clients["local"].close()
    runtime.clients["local"] = client
    state = {
        "process_id": "fixture",
        "workspace_id": "fixture-ws",
        "task_ledger_ref": "fixture-task",
        "phase": "development",
        "logical_step": 0,
    }
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
    try:
        with pytest.raises(UncertainEffect):
            await app.model(state)
        assert len(runtime.uncertain()) == 1
        with pytest.raises(UncertainEffect):
            await app.model(state)
        assert client.calls == 1
        assert runtime.admission["local"].active == 1
        assert runtime.admission["local"].tokens > 0
        body = app.get("effect/" + runtime.uncertain()[0])
        assert body["state"] == "uncertain" and not body["result"]
    finally:
        await runtime.close()


async def test_partial_copy_missing_path_never_deletes_and_add_over_base_is_denied(config):
    runtime, app, _ = await setup(config)
    try:
        manifest = runtime.workspaces.current("fixture-ws")
        root = runtime.workspaces.root_for(manifest)
        assert not (root / "untouched.txt").exists()
        await runtime.workspaces.preserve_delta("fixture-ws")
        permit = await runtime.exclusive.acquire("verification/project", "fixture")
        head = CodeRevision.model_validate(app.get("head/provisional")["code"])
        integrated = await runtime.workspaces.integrate("fixture-ws", head, permit)
        assert (
            (runtime.workspaces.root_for(integrated) / "untouched.txt").read_text().startswith("must survive")
        )
        state = {"process_id": "fixture", "workspace_id": "fixture-ws"}
        stale, output = await app.capability(
            state, "stale-generation", "files.read", {"path": "a.py", "generation": 1}
        )
        assert stale.state == "failed" and "Stale workspace generation" in output["error"]
        await runtime.exclusive.release(permit, "fixture")
    finally:
        await runtime.close()


async def test_checks_that_modify_source_cannot_prove_success(config):
    import sys

    from polyinference.domain import Check

    modified = config.model_copy(
        update={
            "checks": [
                Check(
                    name="syntax",
                    argv=[
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('a.py').write_text('VALUE = 77\\n')",
                    ],
                )
            ]
        }
    )
    runtime, app, _ = await setup(modified)
    try:
        evidence = await runtime.tools.check("fixture-ws", "syntax")
        assert evidence["status"] == "inconclusive"
    finally:
        await runtime.close()


async def test_final_acceptance_rejects_new_steering_during_checks(config):
    runtime, app, engine = await setup(config)
    try:
        run = app.get("app/run")
        app.update("app/run", {**run, "completion_proposed": True})
        original = runtime.tools.check

        async def interrupt_check(*args):
            result = await original(*args)
            engine.steer("New requirement arrived during independent checks")
            return result

        runtime.tools.check = interrupt_check
        accepted = await engine.accept()
        assert not accepted
        assert app.get("app/run")["status"] != "completed"
        assert app.get("app/run")["steering_received"] == 1
        assert not runtime.records.scan("acceptance-receipt/")
    finally:
        await runtime.close()


def test_atomic_compare_never_exposes_half_publication(tmp_path):
    records = Records(tmp_path / "records.sqlite")
    records.compare_and_publish({"head": 0}, {"head": {"value": "old"}})
    with pytest.raises(Conflict):
        records.compare_and_publish({"head": 999}, {"head": {"value": "new"}}, {"report": {"x": 1}})
    assert records.get("head")[1]["value"] == "old"
    assert records.get("report") is None
    records.db.close()


@pytest.mark.parametrize("known_end", [True, False])
async def test_native_terminal_failure_releases_resources_but_unknown_retains_them(config, known_end):
    from polyinference.runtime.codex import NativeJobStopped
    from polyinference.runtime.inference import UnknownExecution

    endpoint = config.local.model_copy(update={"protocol": "codex_app_server", "brokered_tools": True})
    config = config.model_copy(update={"local": endpoint})
    runtime, app, _ = await setup(config)

    class NativeFailure:
        calls = 0

        async def generate_job(self, *args):
            self.calls += 1
            raise (
                NativeJobStopped("fixture terminal failure")
                if known_end
                else UnknownExecution("fixture disconnected")
            )

        async def close(self):
            pass

    client = NativeFailure()
    await runtime.clients["local"].close()
    runtime.clients["local"] = client
    state = {
        "process_id": "fixture",
        "workspace_id": "fixture-ws",
        "task_ledger_ref": "fixture-task",
        "phase": "development",
        "logical_step": 0,
    }
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
    try:
        for _ in range(2):
            with pytest.raises(RuntimeError if known_end else UncertainEffect):
                await app.model(state)
        assert client.calls == 1
        assert runtime.admission["local"].active == (0 if known_end else 1)
        permit = runtime.records.get("permit/shell/installation")[1]
        # Direct Codex reasoning never owns shell; actual broker callbacks acquire it.
        assert permit["process_id"] is None
        effect = runtime.records.scan("effect/")[0][2]
        assert effect["state"] == ("failed" if known_end else "uncertain")
        if known_end:
            assert effect["result"]["execution_termination"] == "confirmed_stopped"
            assert "fixture terminal failure" in effect["result"]["error"]["message"]
    finally:
        # This fake provider has no live remote execution. Retention was asserted
        # above; explicitly reconcile its fixture lease so later tests can run.
        for permit, (owner, _) in list(runtime.exclusive.shell_handles.items()):
            await runtime.exclusive.release(permit, owner)
        await runtime.close()
