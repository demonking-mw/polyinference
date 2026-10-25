from __future__ import annotations

import json
from copy import deepcopy

import pytest
from conftest import ScriptedAgent, fixture_completion
from langgraph.runtime import Runtime
from test_runtime import setup

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.review import (
    brief_ref,
    contract,
    evidence_catalog,
    fit_snapshot,
    retrieve,
    validate_completion,
)
from polyinference.agent.senior import validate
from polyinference.agent.services import AgentServices
from polyinference.agent.worker import AppContext
from polyinference.config import AcceptanceCriterion
from polyinference.domain import ReviewRead, SeniorProposal
from polyinference.runtime.adapter import StandaloneRuntime


def pinned(messages):
    return json.loads(
        next(m["content"] for m in messages if "Pinned application inputs:\n" in m["content"]).split(
            "Pinned application inputs:\n", 1
        )[1]
    )


async def packet(app, engine):
    head = app.get("head/provisional")["code"]
    app.process("senior-fixture", "senior")
    evidence = await engine.review_checks("senior-fixture", 41, head)
    result = {
        "head": head,
        "acceptance_contract": contract(app, head),
        "reports": [],
        "repository_context": await app.repository_context(head),
        "independent_review_evidence": evidence,
    }
    result["review_evidence_catalog"] = evidence_catalog(result)
    return result


@pytest.mark.parametrize(
    "problem", ["missing", "unmet", "uncertain", "stale", "worker_claim", "omitted_criterion", "checks_only"]
)
async def test_technical_pass_does_not_override_semantic_contract(config, problem):
    config = config.model_copy(
        update={
            "acceptance_criteria": [
                AcceptanceCriterion(
                    criterion_id="ui",
                    description="Menus and save/load work through the UI",
                    required_checks=["syntax"],
                )
            ]
        }
    )
    runtime, app, engine = await setup(config)
    try:
        data = await packet(app, engine)
        assert all(e["status"] == "passed" for e in data["independent_review_evidence"])
        proposal = {
            "goal": "Claimed done",
            "complete": True,
            "completion_assessment": fixture_completion(data),
        }
        assessment = proposal["completion_assessment"]
        if problem == "missing":
            proposal.pop("completion_assessment")
        elif problem in {"unmet", "uncertain"}:
            assessment["criteria"][1]["verdict"] = problem
        elif problem == "stale":
            assessment["reviewed_tree_digest"] = "another-tree"
        elif problem == "worker_claim":
            assessment["criteria"][0]["evidence_refs"] = ["worker-said-all-done"]
        elif problem == "omitted_criterion":
            assessment["criteria"].pop()
        elif problem == "checks_only":
            for item in assessment["criteria"]:
                item["evidence_refs"] = [
                    e["evidence_id"]
                    for e in data["review_evidence_catalog"]
                    if e["kind"] == "independent_check"
                ]
        result = await validate(
            {"reply": proposal, "input": data, "process_id": "senior-fixture", "logical_step": 0},
            Runtime(context=AppContext(app)),
        )
        assert result["error"]
        assert "proposal" not in result
        # The same failed/uncertain assessment may accompany provisional follow-up planning.
        proposal["complete"] = False
        validate_completion(SeniorProposal.model_validate(proposal), data)
    finally:
        await runtime.close()


@pytest.mark.parametrize("native", [False, True])
async def test_reviewer_requests_omitted_source_on_pinned_head_for_api_and_native(config, native):
    # Relevant behavior is deliberately beyond the automatic prefix.
    (config.repo_path / "a.py").write_text("# padding\n" * 250 + "VALUE = 1\n")
    from conftest import git

    git(config.repo_path, "add", "a.py")
    git(
        config.repo_path,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-qm",
        "long file",
    )
    config = config.model_copy(update={"objective": "Inspect baseline source"})
    if native:
        config = config.model_copy(
            update={"cloud": config.cloud.model_copy(update={"protocol": "codex_app_server"})}
        )
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)

    class Reviewer:
        calls = 0

        def reply(self, messages):
            data = pinned(messages)
            self.calls += 1
            if self.calls == 1:
                source = data["repository_context"]["contents"][0]
                assert source["truncated"] and "VALUE" not in source["content"]
                reply = {
                    "goal": "Inspect omitted source",
                    "read_requests": [{"path": "a.py", "offset": 2400, "max_bytes": 200}],
                }
            else:
                view = data["review_reads"][0]
                assert "VALUE = 1" in view["content"] and view["source_ref"]["digest"]
                reply = {
                    "goal": "Reviewed",
                    "complete": True,
                    "completion_assessment": fixture_completion(data),
                }
            return {
                "text": json.dumps(reply),
                "usage": {"total_tokens": 10},
                "model": "review-fixture",
                "events": [],
            }

        async def generate(self, messages, *args, **kwargs):
            return self.reply(messages)

        async def generate_job(self, messages, snapshot, schema, **kwargs):
            assert not kwargs.get("callback")
            return self.reply(messages)

        async def close(self):
            pass

    client = Reviewer()
    await runtime.clients["cloud"].close()
    runtime.clients["cloud"] = client
    try:
        await engine.initialize()
        await engine.review()
        assert client.calls == 2
        assert app.get("app/run")["completion_proposed"]
        assert await engine.accept()
        receipt = runtime.records.scan("acceptance-receipt/")[0][2]
        assert receipt["semantic_review"]["head"] == receipt["code"]
        assert receipt["semantic_review"]["review_ref"].startswith("completion-review/")
    finally:
        await runtime.close()


async def test_review_read_bounds_and_stale_acceptance(config):
    runtime, app, engine = await setup(config)
    try:
        data = await packet(app, engine)
        original = deepcopy(data["head"])
        app.update("head/provisional", {"code": {**original, "effective_tree_digest": "moved"}})
        views = await retrieve(app, data, [ReviewRead(path="a.py")])
        assert views[0]["source_code"]["effective_tree_digest"] == original["effective_tree_digest"]
        assert "VALUE = 1" in views[0]["content"]
        result = await validate(
            {
                "reply": {"goal": "Read too much", "read_requests": [{"path": "a.py"}]},
                "input": data,
                "process_id": "senior-fixture",
                "logical_step": 0,
                "review_reads_used": config.max_review_reads,
            },
            Runtime(context=AppContext(app)),
        )
        assert "exhausted" in result["error"]
        app.update("head/reviewed", app.get("head/provisional"))
        app.update("app/run", {**app.get("app/run"), "completion_proposed": True})
        assert not await engine.accept()
        assert not app.get("app/run")["completion_proposed"]
        assert not runtime.records.scan("acceptance-receipt/")
    finally:
        await runtime.close()


async def test_review_context_overflow_preserves_inputs_and_parks_honestly(config):
    config = config.model_copy(
        update={"limits": config.limits.model_copy(update={"max_input_tokens_per_call": 8000})}
    )
    runtime, app, engine = await setup(config)
    try:
        await engine.review()
        run = app.get("app/run")
        assert run["status"] == "paused" and "context bound" in run["blocker"]
        saved = app.read(run["review_input_ref"])
        assert saved["objective"] == config.objective
        assert not runtime.records.scan("inference-attempt/")
        assert not runtime.records.scan("acceptance-receipt/")
    finally:
        await runtime.close()


async def test_review_prioritizes_requested_source_and_preserves_scoped_provenance(config):
    runtime, app, engine = await setup(config)
    try:
        data = await packet(app, engine)
        reads = await retrieve(app, data, [ReviewRead(path="a.py")])
        data["review_reads"] = reads
        data["memory"] = {
            "senior_summary": None,
            "notes": [{"record_id": "memory-note/claim", "comment": "Optimistic claim " * 4000}],
        }
        bounded = fit_snapshot(app, data)
        assert bounded["review_reads"][0]["content"] == reads[0]["content"]
        assert "memory/memory-note/claim" in bounded["omitted_review_material"]
        assert bounded["acceptance_contract"] == data["acceptance_contract"]
        first = brief_ref(app, app.artifact("same bytes", "fixture"))
        second = brief_ref(app, app.artifact("same bytes"))
        assert first["digest"] == second["digest"] and first["record_ref"] != second["record_ref"]
        assert app.get(first["record_ref"])["scope"]["process_id"] == "fixture"
        assert app.get(second["record_ref"])["scope"]["process_id"] is None
    finally:
        await runtime.close()


async def test_review_exposes_real_diff_despite_optimistic_claim_and_keeps_partial_work(config):
    runtime = await StandaloneRuntime(config).open()

    class Reviewer(ScriptedAgent):
        def __init__(self):
            super().__init__(two=False)
            self.saw_diff = False

        async def generate(self, messages, *args, **kwargs):
            data = pinned(messages)
            if "assignment" not in data and data["all_task_ids"]:
                if data["reports"]:
                    report = data["reports"][0]
                    assert report["worker_claim"]["summary"] == "All requirements implemented"
                    assert "+VALUE = 2" in report["integrated_diff"]["preview"]
                    assert report["task_contract"]["allowed_change_scope"] == ["a.py"]
                    source = {s["path"]: s["content"] for s in data["repository_context"]["contents"]}
                    assert "VALUE = 1" in source["b.py"]
                    assert report["publication_status"].startswith("provisional")
                    self.saw_diff = True
                return {
                    "text": json.dumps(
                        {
                            "goal": "Partial: b.py is unfinished",
                            "complete": False,
                            "dispositions": [
                                {
                                    "report_ref": r["record_id"],
                                    "action": "keep",
                                    "reason": "Useful partial delta",
                                }
                                for r in data["reports"]
                            ],
                        }
                    ),
                    "usage": {},
                    "model": "fixture",
                    "events": [],
                }
            result = await super().generate(messages, *args, **kwargs)
            reply = json.loads(result["text"])
            if reply.get("kind") == "assessment":
                reply["summary"] = "All requirements implemented"
                result["text"] = json.dumps(reply)
            return result

    client = Reviewer()
    for old in runtime.clients.values():
        await old.close()
    runtime.clients = {"local": client, "cloud": client}
    app = AgentServices(runtime, config)
    try:
        await ProjectAgent(app).run()
        assert client.saw_diff
        assert app.get("app/run")["status"] != "completed"
        assert not runtime.records.scan("acceptance-receipt/")
        assert runtime.records.scan("resolution/")[0][2]["action"] == "keep"
    finally:
        await runtime.close()
