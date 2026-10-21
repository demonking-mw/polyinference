from __future__ import annotations

import pytest
from conftest import ScriptedAgent

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.contracts import CodeRevision
from polyinference.domain import Disposition
from polyinference.runtime.adapter import StandaloneRuntime


async def populated(config):
    runtime = await StandaloneRuntime(config).open()
    client = ScriptedAgent(two=True)
    for old in runtime.clients.values():
        await old.close()
    runtime.clients = {"local": client, "cloud": client}
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    await engine.run()
    return runtime, app, engine


async def test_abort_uses_original_delta_and_retires_evidence(config):
    runtime, app, engine = await populated(config)
    try:
        reports = [v for _, _, v in runtime.records.scan("report/")]
        newest = next(r for r in reports if r["final_code"] == app.get("head/provisional")["code"])
        wid = next(
            task["workspace_id"]
            for _, _, task in runtime.records.scan("task/")
            if task["process_id"] == newest["process_id"]
        )
        old = runtime.workspaces.current(wid)
        assert old.view == "integration"
        await runtime.workspaces.abort(wid)
        restored = runtime.workspaces.current(wid)
        assert restored.generation > old.generation and restored.view == "development"
        original_delta = app.get(newest["preserved_private_delta_ref"])
        assert {c["path"] for c in original_delta["changes"]} == set(restored.allowed_write_paths)
        permit = await runtime.exclusive.acquire("verification/project", restored.process_id)
        try:
            fresh = await runtime.workspaces.integrate(
                wid, CodeRevision.model_validate(app.get("head/provisional")["code"]), permit
            )
            assert fresh.generation > restored.generation
            tree = runtime.workspaces.scan(runtime.workspaces.root_for(fresh))
            assert tree["a.py"][1] == tree["b.py"][1] == b"VALUE = 2\n"
            assert fresh.preserved_delta_ref == newest["preserved_private_delta_ref"]
        finally:
            await runtime.exclusive.release(permit, restored.process_id)
    finally:
        await runtime.close()


async def test_senior_revert_has_own_receipt_and_replay_creates_no_second_commit(config):
    runtime, app, engine = await populated(config)
    try:
        report = runtime.records.scan("report/")[0][2]
        app.process("senior-revert-fixture", "senior")
        disposition = Disposition(
            report_ref=report["record_id"], action="revert", reason="Conservative fixture inverse"
        )
        await engine.revert("senior-revert-fixture", 99, 0, disposition)
        head = app.get("head/provisional")["code"]
        receipt = app.get("senior-receipt/99/0")
        assert receipt["published_head"] == head
        await engine.revert("senior-revert-fixture", 99, 0, disposition)
        assert app.get("head/provisional")["code"] == head
        assert len(runtime.records.scan("report/")) == 2  # Senior never fabricates a worker report.
        tree = await runtime.workspaces.tree(head["commit_id"])
        changed_path = next(c["path"] for c in app.get(report["preserved_private_delta_ref"])["changes"])
        assert tree[changed_path][1] == b"VALUE = 1\n"
    finally:
        await runtime.close()


async def test_second_coordinator_and_changed_program_cannot_resume(config):
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        await engine.initialize()
        with pytest.raises(RuntimeError, match="coordinator"):
            StandaloneRuntime(config)
        app.program = app.program.model_copy(update={"program_version": "incompatible"})
        with pytest.raises(RuntimeError, match="version changed"):
            await engine.initialize()
    finally:
        await runtime.close()


async def test_review_crash_between_two_reverts_resumes_only_remaining_disposition(config):
    runtime, app, engine = await populated(config)
    reports = [value for _, _, value in runtime.records.scan("report/")]
    run = app.get("app/run")
    app.update("app/run", {**run, "status": "active", "starts_closed": True, "completion_proposed": False})
    run = app.get("app/run")
    pid = "senior-99"
    app.process(pid, "senior")
    batch = {
        "state": "applying",
        "pid": pid,
        "query_index": 99,
        "run": run,
        "head": app.get("head/provisional")["code"],
        "fingerprint": "fixture-two-reverts",
        "proposal": {
            "goal": "Rollback reviewed changes",
            "complete": True,
            "dispositions": [
                {"report_ref": report["record_id"], "action": "revert", "reason": "Fixture inverse"}
                for report in reports
            ],
        },
        "snapshot": {"reports": reports, "all_task_ids": ["a", "b"]},
    }
    app.update("review-batch/active", batch)
    original = engine.resolve

    async def crash_after_first(pid, query_index, index, disposition):
        await original(pid, query_index, index, disposition)
        if index == 0:
            raise RuntimeError("simulated coordinator crash")

    engine.resolve = crash_after_first
    with pytest.raises(RuntimeError, match="simulated"):
        await engine._apply_review(batch)
    first_receipt = app.get("senior-receipt/99/0")
    assert runtime.records.get("senior-receipt/99/1") is None
    await runtime.close()
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        assert app.get("senior-receipt/99/0") == first_receipt
        assert len(runtime.records.scan("senior-receipt/99/")) == 2
        assert len(runtime.records.scan("report/")) == 2
        final = app.get("head/provisional")["code"]
        tree = await runtime.workspaces.tree(final["commit_id"])
        assert tree["a.py"][1] == tree["b.py"][1] == b"VALUE = 1\n"
        count = (await runtime.workspaces.git("rev-list", "--count", final["commit_id"])).decode().strip()
        assert count == "5"
    finally:
        await runtime.close()


async def test_delivery_receipt_recovers_lost_result_and_old_acceptance_lease(config):
    runtime, app, _ = await populated(config)
    effect_key, revision, effect = next(
        item for item in runtime.records.scan("effect/")
        if item[2]["request"]["payload"].get("capability_id") == "outputs.deliver"
    )
    await runtime.exclusive.acquire("verification/project", "controller")
    app.update("app/run", {**app.get("app/run"), "status": "delivering"})
    runtime.records.compare_and_publish(
        {effect_key: revision}, {effect_key: {**effect, "state": "submitting", "result": None}}
    )
    await runtime.close()
    runtime = await StandaloneRuntime(config).open()
    try:
        assert not runtime.uncertain()
        app = AgentServices(runtime, config)
        assert (await ProjectAgent(app).run())["outcome"] == "completed"
        assert len(runtime.records.scan("output-delivery/")) == 1
        assert not runtime.records.get("permit/verification/project")[1].get("process_id")
        assert runtime.processes.status("controller")["state"] == "completed"
        assert (config.state_path / "result/a.py").read_text() == "VALUE = 2\n"
    finally:
        await runtime.close()
