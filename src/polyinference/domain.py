"""Application schemas; live services never belong in these records."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Limits, PhaseReserve, Wire
from .execution_contracts import Check as Check
from .primitives import canonical as canonical
from .primitives import digest as digest
from .primitives import now as now
from .primitives import operation_fingerprint as operation_fingerprint
from .workspace_contracts import RelativePath

PROGRAM_VERSION = "agent-5-in-place-repository"
STATE_VERSION = "2.3"


class GitPolicy(Wire):
    mode: Literal["new", "existing", "current"] = "new"
    branch: str | None = None
    task_branches: bool = True
    reason: str = "Git policy selected by the coding agent"
    blocker: str | None = None
    change_requested: bool = False

    @model_validator(mode="after")
    def coherent(self):
        if self.mode == "existing" and not self.branch:
            raise ValueError("An existing branch must be named")
        if self.mode == "current" and self.branch:
            raise ValueError("Current-branch policy cannot name another branch")
        return self


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


class Assignment(Wire):
    task_id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
    objective: Annotated[str, Field(min_length=1, max_length=16000)]
    write_paths: Annotated[list[RelativePath], Field(min_length=1)]
    read_paths: list[RelativePath] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    resume_from: str | None = None
    role: Literal["worker", "specialist"] = "worker"
    checks: Annotated[list[str], Field(min_length=1)]

    @model_validator(mode="after")
    def unique(self):
        for values in (self.write_paths, self.read_paths, self.dependencies, self.checks):
            if len(values) != len(set(values)):
                raise ValueError("Assignment lists must contain unique entries")
        if self.task_id in self.dependencies:
            raise ValueError("Task cannot depend on itself")
        return self


class Disposition(Wire):
    report_ref: str
    action: Literal["keep", "revert", "retry", "defer"]
    reason: Annotated[str, Field(min_length=1, max_length=8000)]


class CheckPreparation(Wire):
    check_name: str
    task_id: str


class SeniorProposal(Wire):
    goal: str
    user_brief: Annotated[str, Field(min_length=1, max_length=8000)] | None = None
    tasks: list[Assignment] = Field(default_factory=list)
    dispositions: list[Disposition] = Field(default_factory=list)
    complete: bool = False
    memory_update: str | None = None
    cancel_pending_task_ids: list[str] = Field(default_factory=list)
    check_preparations: list[CheckPreparation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dag(self):
        tasks = {t.task_id: t for t in self.tasks}
        if len(tasks) != len(self.tasks):
            raise ValueError("Task IDs must be unique")
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
        return self


class Action(Wire):
    kind: Literal["action"]
    tool: Literal[
        "files.list",
        "files.read",
        "files.search",
        "files.patch",
        "files.write",
        "files.delete",
        "checks.run",
        "checks.configure",
        "shell.run",
        "repository.select_branch",
        "user.notify",
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
