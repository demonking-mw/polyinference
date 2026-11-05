"""Agent-owned code reports and commit-free test results; no OS task policy."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from ..contracts import ArtifactRef, CheckEvidence, CodeRevision, Identifier, Record, TaskReport, UsageMeasure


class TestReport(Record):
    """An observation of existing code, with no candidate or publication commit."""

    kind: Literal["test_report"] = "test_report"
    task_spec_ref: Identifier
    attempt_id: Identifier
    process_id: Identifier
    plan_ref: Identifier
    execution: Literal["completed"] = "completed"
    resolution: Literal["unresolved"] = "unresolved"
    verdict: Literal["fail", "uncertain", "successful"]
    reconciliation_turn_refs: Annotated[list[Identifier], Field(min_length=1)]
    assessment_turn_refs: Annotated[list[Identifier], Field(min_length=1)]
    assessment_summary: ArtifactRef
    tested_code: CodeRevision
    evidence: list[CheckEvidence]
    usage: list[UsageMeasure]

    @model_validator(mode="after")
    def successful_evidence(self):
        if self.verdict == "successful":
            if not self.evidence or any(e.status != "passed" for e in self.evidence):
                raise ValueError("Successful testing needs passed evidence")
            fields = ("repository_id", "effective_tree_digest", "environment_digest")
            if any(any(getattr(e.checked_code, f) != getattr(self.tested_code, f) for f in fields)
                   for e in self.evidence):
                raise ValueError("Test evidence must match the tested code/environment")
        return self


async def record_test_result(app, state, current, evidence, verdict):
    """Atomically finish a test attempt; the result record is its replay boundary."""
    report_ref = "report/" + state["attempt_id"]
    if app.ports.records.get(report_ref):
        return {"report_ref": report_ref}
    if not app.ports.exclusive.owns(state["verification_permit_ref"], "verification/project", state["process_id"]):
        raise RuntimeError("Test results require current verification ownership")
    head_version, head_body = app.ports.records.get("head/provisional")
    head = CodeRevision.model_validate(state["captured_head"])
    if head_body["code"] != head.model_dump(mode="json") or any(
        getattr(current, field) != getattr(head, field)
        for field in ("repository_id", "effective_tree_digest", "environment_digest")
    ):
        raise RuntimeError("Test task changed source or lost its captured head")
    task_version, task = app.ports.records.get(state["task_ledger_ref"])
    attempt_key = "attempt/" + state["attempt_id"]
    attempt_version, attempt = app.ports.records.get(attempt_key)
    report = TestReport(
        **app.base(report_ref), task_spec_ref=state["task_spec_ref"],
        attempt_id=state["attempt_id"], process_id=state["process_id"], plan_ref=task["plan_ref"],
        verdict=verdict, tested_code=head, evidence=evidence,
        assessment_summary=app.artifact(state["reply"]["summary"], state["process_id"]),
        reconciliation_turn_refs=state["reconciliation_turn_refs"],
        assessment_turn_refs=state["assessment_turn_refs"],
        usage=[UsageMeasure.model_validate(measure)
               for _, _, operation in app.ports.records.scan("effect/")
               if operation["request"]["scope"]["process_id"] == state["process_id"] and operation.get("result")
               for measure in operation["result"]["usage"]],
    )
    expected = {"head/provisional": head_version, state["task_ledger_ref"]: task_version, attempt_key: attempt_version}
    updates = {
        state["task_ledger_ref"]: {**task, "execution": "completed", "report_ref": report_ref},
        attempt_key: app.task_attempt(attempt, update={"revision": attempt["revision"] + 1,
                                  "execution": "completed", "report_ref": report_ref}).model_dump(mode="json"),
    }
    if verdict != "successful":
        version, run = app.ports.records.get("app/run")
        expected["app/run"] = version
        updates["app/run"] = {**run, "starts_closed": True, "completion_proposed": False,
                              "review_reason": "test_" + verdict,
                              "captured_workers": sorted(set(run["captured_workers"]) | set(run["active_workers"]))}
    app.ports.records.compare_and_publish(expected, updates, {report_ref: report.model_dump(mode="json")})
    return {"report_ref": report_ref}


class PrivateTaskReport(TaskReport):
    """An assessed candidate retained without integration into the shared branch."""

    verdict: Literal["fail", "uncertain"] = "fail"
    publication_policy: Literal["retain_failed"] = "retain_failed"
    code_location: Literal["private"] = "private"


class PrivateCommitReceipt(Record):
    kind: Literal["private_commit_receipt"] = "private_commit_receipt"
    publication_operation_id: Identifier
    report_ref: Identifier
    previous_head: CodeRevision
    candidate: CodeRevision
    verification_permit_ref: Identifier
    publication_policy: Literal["retain_failed"] = "retain_failed"


def task_report(value):
    cls = PrivateTaskReport if value.get("code_location") == "private" else TaskReport
    return cls.model_validate(value)
