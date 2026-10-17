from __future__ import annotations

import pytest
from conftest import ScriptedAgent, git

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.contracts import PublicationReceipt, TaskReport
from polyinference.runtime.adapter import StandaloneRuntime


@pytest.mark.parametrize("verdict", ["successful", "uncertain"])
async def test_two_workers_publish_provisional_verdicts_and_accept_exact_tree(config, verdict):
    runtime = await StandaloneRuntime(config).open()
    scripted = ScriptedAgent(verdict)
    await runtime.clients["local"].close()
    await runtime.clients["cloud"].close()
    runtime.clients = {"local": scripted, "cloud": scripted}
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        result = await engine.run()
        assert result["outcome"] == "completed", app.get("app/run")
        reports = [TaskReport.model_validate(v) for _, _, v in runtime.records.scan("report/")]
        assert len(reports) == 2
        assert {r.verdict for r in reports} == {verdict}
        assert {r.resolution for r in reports} == {"unresolved"}
        head = app.get("head/provisional")["code"]
        tree = await runtime.workspaces.tree(head["commit_id"])
        assert tree["a.py"][1] == tree["b.py"][1] == b"VALUE = 2\n"
        assert tree["untouched.txt"][1] == b"must survive partial copies\n"
        assert head == app.get("head/reviewed")["code"]
        by_commit = {r.final_code.commit_id: r for r in reports}
        newest = by_commit[head["commit_id"]]
        assert newest.captured_head.commit_id in by_commit
        assert newest.reconciliation_turn_refs and newest.assessment_turn_refs
        receipts = [PublicationReceipt.model_validate(v) for _, _, v in runtime.records.scan("receipt/")]
        assert len(receipts) == 2
        assert scripted.peak >= 2
        assert not app.get("app/run")["active_workers"]
        assert not runtime.exclusive.owns(
            newest.verification_permit_ref, "verification/project", newest.process_id
        )
        # Source checkout is never used as the agent's writable working directory.
        assert (config.repo_path / "a.py").read_text() == "VALUE = 1\n"
        assert git(config.repo_path, "status", "--porcelain") == ""
    finally:
        await runtime.close()


async def test_steering_during_workers_drains_started_and_preserves_late_input(config):
    runtime = await StandaloneRuntime(config).open()
    scripted = ScriptedAgent(two=True)
    for client in runtime.clients.values():
        await client.close()
    runtime.clients = {"local": scripted, "cloud": scripted}
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    steered = False

    async def hook(data):
        nonlocal steered
        if "assignment" in data and not steered:
            steered = True
            engine.steer("Retain the two value updates and inspect them together.")
            assert set(app.get("app/run")["captured_workers"]) == set(app.get("app/run")["active_workers"])

    scripted.hook = hook
    try:
        await engine.run()
        run = app.get("app/run")
        assert run["status"] == "completed", run
        assert run["steering_received"] == run["steering_applied"] == 1
        assert len(runtime.records.scan("report/")) == 2
        assert scripted.review_inputs[0]["steering"][0]["sequence"] == 1
    finally:
        await runtime.close()
