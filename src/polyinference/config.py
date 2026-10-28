from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import InferencePolicy, Wire
from .execution_contracts import Check
from .system_settings import Endpoint, RuntimeConfig
from .workspace_contracts import RelativePath

__all__ = ["AgentConfig", "Endpoint", "RuntimeConfig"]


class InferenceRetry(Wire):
    max_attempts: Annotated[int, Field(ge=2, le=8)] = 2
    replacement_wait_seconds: Annotated[float, Field(ge=0, le=60)] = 1


class CheckDiagnosis(Wire):
    role: Literal["worker", "specialist", "senior"] = "worker"
    max_rounds: Annotated[int, Field(ge=0, le=3)] = 1
    max_read_paths: Annotated[int, Field(ge=1, le=32)] = 16
    instructions: str = ""


class AcceptanceCriterion(Wire):
    criterion_id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]
    description: Annotated[str, Field(min_length=1, max_length=4000)]
    required_checks: list[str] = Field(default_factory=list)


class ProgressMonitor(Wire):
    mode: Literal["off", "observe", "enforce"] = "enforce"
    warn_after: Annotated[int, Field(ge=2, le=128)] = 8
    escalate_after: Annotated[int, Field(ge=3, le=256)] = 12

    @model_validator(mode="after")
    def ordered(self):
        if self.escalate_after <= self.warn_after:
            raise ValueError("Progress escalation must leave decisions after warning")
        return self


class AgentConfig(RuntimeConfig):
    """Policy of the bundled coding agent, separate from the runtime's contract."""

    inference_policy: InferencePolicy | None = Field(default=None, exclude_if=lambda value: value is None)
    model_output_target_tokens: Annotated[int, Field(gt=0)] | None = Field(
        default=None, exclude_if=lambda value: value is None)
    objective: Annotated[str, Field(min_length=1)]
    repository_mode: Literal["in_place", "isolated"] = "in_place"
    git_policy: dict | None = None
    dependency_prepare: list[str] = Field(default_factory=list)
    prerequisite_checks: list[Check] = Field(default_factory=list)
    acceptance_checks: list[Check] | None = None
    allowed_write_paths: Annotated[list[RelativePath], Field(min_length=1)]
    senior_development_fraction: Annotated[float, Field(ge=0, le=1)] = 0.1
    max_sprints: Annotated[int, Field(gt=0, le=100)] = 8
    max_senior_corrections: Annotated[int, Field(ge=0, le=3)] = 1
    inference_retry: InferenceRetry = Field(default_factory=InferenceRetry)
    check_diagnosis: CheckDiagnosis = Field(default_factory=CheckDiagnosis)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    max_review_reads: Annotated[int, Field(ge=0, le=16)] = 4
    max_worker_recoveries: Annotated[int, Field(ge=0, le=3)] = 1
    max_cloud_recoveries: Annotated[int, Field(ge=0, le=3)] = 1
    progress_monitor: ProgressMonitor = Field(default_factory=ProgressMonitor)

    max_protocol_corrections: Annotated[int, Field(ge=0, le=16)] = 3

    @model_validator(mode="before")
    @classmethod
    def coding_defaults(cls, value):
        from .agent.system_settings import coding_system_defaults
        if isinstance(value, dict):
            value = dict(value)
            system = value.pop("system", {})
            if not isinstance(system, dict) or system.keys() & value.keys():
                raise ValueError("System settings must be configured once, in system or at top level")
            value = {**coding_system_defaults(), **system, **value}
            if "review_token_reserve" in value:
                value["control_token_reserve"] = value.pop("review_token_reserve")
        return value

    @property
    def review_token_reserve(self):
        return self.control_token_reserve

    @model_validator(mode="after")
    def feasible_agent(self):
        ids = [c.criterion_id for c in self.acceptance_criteria]
        if len(ids) != len(set(ids)) or "objective" in ids:
            raise ValueError("Acceptance criterion IDs must be unique; objective is reserved")
        if any(not set(c.required_checks) <= {c.name for c in [*self.checks, *(self.acceptance_checks or [])]} for c in self.acceptance_criteria):
            raise ValueError("Acceptance criteria must use configured checks")

        if not (self.checks or self.acceptance_checks) and not self.prepare_repository:
            raise ValueError("Provide checks or enable prepare_repository to discover them")
        definitions = {}
        for check in [*self.checks, *self.prerequisite_checks, *(self.acceptance_checks or [])]:
            if check.name in definitions and definitions[check.name] != check:
                raise ValueError("A check name must have one immutable command definition across purposes")
            definitions[check.name] = check
        if set(self.role_bindings) != {"senior", "worker", "specialist"}:
            raise ValueError("Pin all three role bindings")
        for role in ("worker", "specialist"):
            backend = getattr(self, self.role_bindings[role])
            if backend.protocol not in {"chat", "responses", "gemini", "anthropic"} and not (
                backend.protocol == "codex_app_server" and backend.brokered_tools
            ):
                raise ValueError("Opaque native coding jobs cannot enforce the worker protocol")
        return self
