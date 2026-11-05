"""Agent-owned test assignments need observations, not writable/result files."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest
from conftest import fixture_completion, git
from pydantic import ValidationError

from polyinference.agent.architecture import validate_local_tasks
from polyinference.agent.controller import ProjectAgent
from polyinference.agent.reports import TestReport as ResultReport
from polyinference.agent.services import AgentServices
from polyinference.agent.worker import publish
from polyinference.domain import Assignment, Disposition, GitPolicy, SeniorProposal
from polyinference.runtime.adapter import StandaloneRuntime


def make_test_assignment(**changes):
    return Assignment.model_validate({
        "kind": "test", "task_id": "verify", "objective": "Verify existing Python modules parse",
        "read_paths": ["a.py", "b.py"], "checks": ["syntax"], **changes,
    })


def test_test_assignment_needs_no_implementation_or_result_path(config):
    task = make_test_assignment()
    assert task.write_paths == [] and task.local_contract is None
    validate_local_tasks(SeniorProposal(goal="Verify", tasks=[task]), config)
    assert "result_path" not in Assignment.model_json_schema()["properties"]
    assert Assignment.model_validate_json(task.model_dump_json()) == task
    with pytest.raises(ValidationError, match="Edit assignments require write_paths"):
        make_test_assignment(kind="edit")


@pytest.mark.parametrize("changes", [
    {"write_paths": ["a.py"]}, {"resume_from": "old-source"}, {"provides": ["api@1"]},
])
def test_testing_does_not_bypass_edit_authority(changes):
    with pytest.raises(ValidationError, match="Test assignments run existing tests"):
        make_test_assignment(**changes)


class ScriptedTester:
    def __init__(self):
        self.inputs = []
        self.prompts = []

    async def close(self):
        pass

    async def generate(self, messages, max_output, response_schema=None, **kwargs):
        data = json.loads(next(m["content"] for m in messages if "Pinned application inputs:" in m["content"])
                          .split("Pinned application inputs:\n", 1)[1])
        self.inputs.append(data)
        self.prompts.append(messages[0]["content"])
        if "assignment" in data:
            if data["phase"] == "assessment":
                # Deliberately optimistic: the host must preserve actual failures.
                reply = {"kind": "assessment", "verdict": "successful",
                         "summary": "Expected modules to parse; inspected the supplied check receipts"}
            else:
                reply = {"kind": "candidate", "summary": "Ready to verify existing modules"}
        elif not data["all_task_ids"]:
            reply = {"goal": "Verify modules", "tasks": [make_test_assignment().model_dump(mode="json")]}
        else:
            failed = any(r["verdict"] != "successful" for r in data["reports"])
            reply = {"goal": "Reviewed test observations", "complete": not failed,
                     "dispositions": [{"report_ref": r["record_id"], "action": "revert" if failed else "keep",
                                       "reason": "Reviewed the actual test evidence"} for r in data["reports"]]}
            if not failed:
                reply["completion_assessment"] = fixture_completion(data)
        return {"text": json.dumps(reply), "usage": {"total_tokens": 50}, "model": "fixture", "events": []}


@pytest.mark.parametrize("mode,failure,branches", [("isolated", False, False), ("in_place", False, True), ("in_place", True, False)])
async def test_test_task_reports_without_source_commit_or_result_file(config, mode, failure, branches):
    checks = config.checks
    if failure:
        checks = [checks[0].model_copy(update={"argv": [sys.executable, "-c", "raise SystemExit(1)"]})]
    config = config.model_copy(update={
        "repository_mode": mode, "objective": "Verify existing modules without editing source",
        "git_policy": GitPolicy(mode="current", task_branches=branches).model_dump(mode="json"), "checks": checks,
    })
    original = git(config.repo_path, "rev-parse", "HEAD")
    runtime = await StandaloneRuntime(config).open()
    scripted = ScriptedTester()
    for client in runtime.clients.values():
        await client.close()
    runtime.clients = {"local": scripted, "cloud": scripted}
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        result = await engine.run()
        assert result["outcome"] == ("paused" if failure else "completed"), app.get("app/run")
        reports = [ResultReport.model_validate(v) for _, _, v in runtime.records.scan("report/")]
        assert len(reports) == 1
        report = reports[0]
        assert report.verdict == ("fail" if failure else "successful")
        assert report.evidence[0].status == ("failed" if failure else "passed")
        assert report.tested_code == app.task_attempt(app.get("attempt/" + report.attempt_id)).original_base
        assert app.get("head/provisional")["code"] == report.tested_code.model_dump(mode="json")
        assert not runtime.records.scan("commit-info/")
        assert not runtime.records.scan("receipt/")
        assert not runtime.records.scan("diagnosis/")
        assert git(config.repo_path, "rev-parse", "HEAD") == original
        assert git(config.repo_path, "status", "--porcelain") == ""
        assert not app.get("app/run")["active_workers"]
        assert app.get("process/" + report.process_id)["state"] == "completed"
        assert app.get("process-status/" + report.process_id)["cleanup_state"] == "complete"
        spec = app.get(report.task_spec_ref)
        assert spec["allowed_change_scope"] == [] and spec["report_schema_ref"] == "test-report/1"
        assert not {"files.write", "files.patch", "files.delete"} & set(spec["allowed_capabilities"])
        assert not {"workspace.commit", "coding.commit", "coding.publish", "records.publish"} & set(
            app.get("process/" + report.process_id)["capabilities"])
        workers = [d for d in scripted.inputs if "assignment" in d]
        assert {d["phase"] for d in workers} == {"development", "reconciliation", "assessment"}
        assert all(d["available_tools"] == spec["allowed_capabilities"] for d in workers)
        review = next(d["reports"][0] for d in scripted.inputs if d.get("reports"))
        assert review["result_kind"] == "test" and review["changed_paths"] == []
        assert "candidate_commit_id" not in review
        assert "result path" in scripted.prompts[0]
        # Replaying publication observes the durable result before inspecting a retired workspace.
        saved = await engine.worker.aget_state({"configurable": {"thread_id": report.process_id}})
        assert await publish(saved.values, SimpleNamespace(context=engine.context)) == {"report_ref": report.record_id}
        if failure:
            with pytest.raises(ValueError, match="Only successful test results"):
                await engine.resolve("review", 99, 0, Disposition(report_ref=report.record_id,
                                    action="keep", reason="Must not release dependents"))
    finally:
        await runtime.close()
