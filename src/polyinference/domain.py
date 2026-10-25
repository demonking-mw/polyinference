"""Application schemas; live services never belong in these records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Limits, PhaseReserve, Wire
from .workspace_contracts import RelativePath

PROGRAM_VERSION = "agent-5-progress-monitoring"
STATE_VERSION = "2.4"


def now():
    return datetime.now(timezone.utc)


def canonical(value) -> bytes:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def operation_fingerprint(request):
    data = request.model_dump(mode="json")
    keys = (
        "payload",
        "extensions",
        "grant_ref",
        "owner_generation",
        "expected_process_revision",
        "expected_binding_generation",
        "schedule_ref",
        "budget_account_ref",
        "limits",
        "resources",
        "conflict_keys",
        "safe_boundary",
        "replay_policy",
        "required_features",
    )
    return digest(canonical({key: data[key] for key in keys}))


def default_limits() -> Limits:
    return Limits(
        max_steps=2048,
        max_model_calls=512,
        max_repairs=2,
        max_input_tokens_per_call=24000,
        max_output_tokens_per_call=4000,
        max_total_tokens=16000000,
        max_output_bytes=262144,
        max_wall_time_ms=3600000,
        max_api_spend_microusd=0,
        cost_guarantee="estimate",
        final_phase_reserve=PhaseReserve(
            reconciliation_model_calls=2, assessment_model_calls=2, publication_steps=2, cleanup_steps=1
        ),
    )


class Check(Wire):
    name: str
    argv: Annotated[list[str], Field(min_length=1)]
    timeout_seconds: Annotated[float, Field(gt=0, le=600)] = 60


InterfaceRef = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,80}@[1-9][0-9]*$")]
ContractText = Annotated[str, Field(min_length=1, max_length=3000)]


class InterfaceContract(Wire):
    interface_id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
    version: Annotated[int, Field(ge=1)]
    description: ContractText
    inputs: ContractText
    outputs: ContractText
    invariants: Annotated[list[ContractText], Field(min_length=1, max_length=12)]
    verification: Annotated[list[ContractText], Field(min_length=1, max_length=12)]
    change_reason: Annotated[str, Field(max_length=3000)] = ""

    @property
    def reference(self):
        return f"{self.interface_id}@{self.version}"

    @model_validator(mode="after")
    def revision_reason(self):
        if self.version > 1 and not self.change_reason.strip():
            raise ValueError("Interface revisions require a change_reason and compatibility impact")
        return self


class Assignment(Wire):
    task_id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
    objective: Annotated[str, Field(min_length=1, max_length=16000)]
    write_paths: Annotated[list[RelativePath], Field(min_length=1)]
    read_paths: list[RelativePath] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    role: Literal["worker", "specialist"] = "worker"
    checks: Annotated[list[str], Field(min_length=1)]
    acceptance_criteria: list[ContractText] = Field(default_factory=list, max_length=12)
    non_goals: list[ContractText] = Field(default_factory=list, max_length=12)
    provides: list[InterfaceRef] = Field(default_factory=list, max_length=16)
    consumes: list[InterfaceRef] = Field(default_factory=list, max_length=16)
    resume_from: str | None = None

    @model_validator(mode="after")
    def unique(self):
        for values in (
            self.write_paths,
            self.read_paths,
            self.dependencies,
            self.checks,
            self.provides,
            self.consumes,
        ):
            if len(values) != len(set(values)):
                raise ValueError("Assignment lists must contain unique entries")
        if self.task_id in self.dependencies:
            raise ValueError("Task cannot depend on itself")
        if (self.provides or self.consumes) and not self.acceptance_criteria:
            raise ValueError("Module assignments require observable acceptance_criteria")
        return self


class Disposition(Wire):
    report_ref: str
    action: Literal["keep", "revert", "retry", "defer"]
    reason: Annotated[str, Field(min_length=1, max_length=8000)]


class ExceptionDisposition(Wire):
    exception_ref: str
    action: Literal["retry", "defer", "stop"]
    reason: Annotated[str, Field(min_length=1, max_length=4000)]
    changed_condition: Annotated[str, Field(max_length=4000)] = ""
    replacement_task_id: str | None = None

    @model_validator(mode="after")
    def linked_retry(self):
        if self.action == "retry":
            if not self.replacement_task_id or not self.changed_condition.strip():
                raise ValueError("Recovery needs a new assignment and a specific changed condition")
        elif self.replacement_task_id is not None:
            raise ValueError("Only retry may name a replacement")
        return self


class ReviewRead(Wire):
    path: RelativePath
    offset: Annotated[int, Field(ge=0)] = 0
    max_bytes: Annotated[int, Field(ge=1, le=4000)] = 2000


class CriterionAssessment(Wire):
    criterion_id: str
    verdict: Literal["met", "unmet", "uncertain"]
    rationale: Annotated[str, Field(min_length=1, max_length=2000)]
    evidence_refs: list[str] = Field(default_factory=list)


class CompletionAssessment(Wire):
    reviewed_tree_digest: str
    criteria: list[CriterionAssessment]


class SeniorProposal(Wire):
    goal: str
    tasks: list[Assignment] = Field(default_factory=list)
    dispositions: list[Disposition] = Field(default_factory=list)
    complete: bool = False
    memory_update: str | None = None
    cancel_pending_task_ids: list[str] = Field(default_factory=list)
    read_requests: list[ReviewRead] = Field(default_factory=list, max_length=8)
    completion_assessment: CompletionAssessment | None = None
    interface_contracts: list[InterfaceContract] = Field(default_factory=list, max_length=16)
    exception_dispositions: list[ExceptionDisposition] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def validate_dag(self):
        tasks = {t.task_id: t for t in self.tasks}
        if len(tasks) != len(self.tasks):
            raise ValueError("Task IDs must be unique")
        refs = [c.reference for c in self.interface_contracts]
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate interface contract version")
        visiting, done = set(), set()

        def visit(key):
            if key in visiting:
                raise ValueError("Task dependency cycle")
            if key in done or key not in tasks:
                return
            visiting.add(key)
            for dep in tasks[key].dependencies:
                visit(dep)
            visiting.remove(key)
            done.add(key)

        for key in tasks:
            visit(key)
        if len(self.cancel_pending_task_ids) != len(set(self.cancel_pending_task_ids)):
            raise ValueError("Duplicate pending cancellation")
        if set(self.cancel_pending_task_ids) & set(tasks):
            raise ValueError("Cannot cancel and create the same task ID")
        refs = [d.report_ref for d in self.dispositions]
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate report disposition")
        if self.complete and self.tasks:
            raise ValueError("Completion cannot create tasks")
        if self.complete and self.read_requests:
            raise ValueError("Read requested evidence before proposing completion")
        return self


class Action(Wire):
    kind: Literal["action"]
    tool: Literal[
        "files.list",
        "files.read",
        "files.write",
        "files.delete",
        "checks.run",
        "shell.run",
        "repository.select_branch",
    ]
    arguments: dict


class Candidate(Wire):
    kind: Literal["candidate"]
    summary: str


class Assessment(Wire):
    kind: Literal["assessment"]
    verdict: Literal["fail", "uncertain", "successful"]
    summary: Annotated[str, Field(min_length=1)]
    repair: bool = False


class NeedsReview(Wire):
    kind: Literal["needs_review"]
    reason: Annotated[str, Field(min_length=1)]


WorkerReply = Annotated[Action | Candidate | Assessment | NeedsReview, Field(discriminator="kind")]
