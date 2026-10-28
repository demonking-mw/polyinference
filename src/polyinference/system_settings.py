from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, ValidationInfo, model_serializer, model_validator

from .contracts import DataPolicy, Limits, Wire
from .execution_contracts import Check
from .primitives import runtime_limits
from .workspace_contracts import RelativePath


class ContextPolicy(Wire):
    """Caller-selected context assistance. Hard execution guards are unconditional."""

    auto_deal_context: bool = False
    auto_compaction: bool = False
    compaction_trigger: Annotated[float, Field(gt=0, le=1)] = 0.8
    compaction_target: Annotated[float, Field(gt=0, lt=1)] = 0.6
    max_compaction_calls: Annotated[int, Field(ge=0, le=32)] = 8
    compaction_output_tokens: Annotated[int, Field(gt=0)] = 1024
    compaction_summary_bytes: Annotated[int, Field(gt=0)] = 4096
    recovery_headroom: Annotated[int, Field(ge=0)] = 1024

    @model_validator(mode="after")
    def valid_target(self):
        if self.compaction_target >= self.compaction_trigger:
            raise ValueError("Compaction target must be below its trigger")
        return self


class InferenceSafety(Wire):
    """Common raw/native completion and response recovery settings."""

    output_recoveries: Annotated[int, Field(ge=0, le=3)] = 2
    smaller_response_bytes: Annotated[int, Field(gt=0)] = 4096
    require_output_token_enforcement: bool = False
    require_completion_metadata: Literal[True] = True


class InferenceLifecycle(Wire):
    """Explicit deployment timings; binding names and URLs imply no safety facts."""

    transport: Literal["sse", "buffered"] = "sse"
    connect_seconds: Annotated[float, Field(gt=0, le=1800)] = 10
    first_output_seconds: Annotated[float, Field(gt=0, le=3600)] = 180
    idle_seconds: Annotated[float, Field(gt=0, le=3600)] = 90
    total_seconds: Annotated[float, Field(gt=0, le=7200)] = 600


class RetryModel(Wire):
    """Caller-selected alternate on the same provider/protocol and authority envelope."""

    model: Annotated[str, Field(min_length=1)]
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"] = "medium"
    fallback_calls: Annotated[int, Field(ge=1, le=32)] = 7


class Endpoint(Wire):
    protocol: Literal["chat", "responses", "gemini", "anthropic", "codex_app_server", "codex_proxy"] = "chat"
    base_url: str = "http://127.0.0.1:8000/v1"
    model: str
    api_key_env: str | None = None
    command: list[str] = Field(default_factory=lambda: ["codex", "app-server"])
    max_inflight: Annotated[int, Field(gt=0, le=32)] = 2
    max_context_tokens: Annotated[int, Field(gt=0)] = 32000
    reserved_context_tokens: Annotated[int, Field(gt=0)] = 64000
    readonly_snapshot_root: str | None = None
    brokered_tools: bool = False
    inference_location: Literal["local", "cloud"] | None = None
    supports_temperature: bool = True
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"] = "medium"
    retry_model: RetryModel | None = Field(default=None, exclude_if=lambda value: value is None)
    input_token_count_path: Annotated[str, Field(pattern=r"^/(?:[A-Za-z0-9_-]+/)*(?:input_tokens|count_tokens)$")] | None = Field(
        default=None, exclude_if=lambda value: value is None)
    timeout_seconds: Annotated[float, Field(gt=0, le=1800)] = 180
    lifecycle: InferenceLifecycle | None = Field(default=None, exclude_if=lambda value: value is None)
    estimated_microusd_per_token: Annotated[float, Field(ge=0)] | None = None

    @model_serializer(mode="wrap")
    def preserve_disabled_retry(self, handler):
        data = handler(self)
        if self.retry_model is None and "retry_model" in self.model_fields_set:
            data["retry_model"] = None
        return data

    @model_validator(mode="after")
    def distinct_retry_model(self):
        if self.input_token_count_path and self.protocol in {"codex_app_server", "codex_proxy"}:
            raise ValueError("Native hidden context cannot be measured by a raw input counter")
        if self.retry_model and self.retry_model.model == self.model:
            raise ValueError("Retry model must differ from the primary model")
        if self.retry_model and self.protocol == "codex_proxy":
            raise ValueError("Model fallback requires a direct provider or app-server adapter")
        return self

    @property
    def physical_location(self):
        if self.inference_location:
            return self.inference_location
        from urllib.parse import urlparse

        return (
            "local"
            if self.protocol in {"chat", "responses"}
            and urlparse(self.base_url).hostname in {"127.0.0.1", "localhost", "::1"}
            else "cloud"
        )


class RuntimeConfig(Wire):
    """OS resources and optional file capabilities; no coding-agent requirements."""

    repository: str
    state_directory: str = ".polyinference"
    allowed_write_paths: list[RelativePath] = Field(default_factory=list)
    closure_paths: list[RelativePath] = Field(default_factory=list)
    checks: list[Check] = Field(default_factory=list)
    local: Endpoint
    cloud: Endpoint
    role_bindings: dict[str, Literal["local", "cloud"]] = Field(
        default_factory=lambda: {"default": "local"}
    )
    prepare_repository: bool = False
    data_policy: DataPolicy | None = Field(default=None, exclude_if=lambda value: value is None)
    output_directory: str | None = None
    base_branch: str | None = None
    write_scope: Literal["explicit", "project"] = "explicit"
    shell_execution: Literal["disabled", "trusted", "bubblewrap"] = "disabled"
    shell_fail_fast: bool = False
    max_workers: Annotated[int, Field(gt=0, le=16)] = 2
    limits: Limits = Field(default_factory=runtime_limits)
    run_token_budget: Annotated[int, Field(gt=0)] = 64000000
    control_token_reserve: Annotated[int, Field(ge=0)] = Field(
        default=0, validation_alias=AliasChoices("control_token_reserve", "review_token_reserve"))
    run_spend_budget_microusd: Annotated[int, Field(gt=0)] | None = None
    max_artifact_bytes: Annotated[int, Field(gt=0)] = 128 * 1024 * 1024
    max_workspace_bytes: Annotated[int, Field(gt=0)] = 64 * 1024 * 1024
    max_workspace_total_bytes: Annotated[int, Field(gt=0)] = 1024 * 1024 * 1024
    max_queued_operations: Annotated[int, Field(gt=0, le=4096)] = 128
    max_command_seconds: Annotated[float, Field(gt=0, le=3600)] = 300
    max_model_response_bytes: Annotated[int, Field(gt=0)] = 4 * 1024 * 1024
    max_model_request_bytes: Annotated[int, Field(gt=0)] | None = Field(default=None, exclude_if=lambda value: value is None)
    context_policy: ContextPolicy = Field(default_factory=ContextPolicy)
    inference_safety: InferenceSafety = Field(default_factory=InferenceSafety)
    max_repeated_model_failures: Annotated[int, Field(gt=0)] = 2
    max_model_recoveries: Annotated[int, Field(ge=0)] = 2
    model_call_retries: Annotated[int, Field(ge=0, le=3)] = 1
    model_retry_delay_ms: Annotated[int, Field(ge=0, le=60000)] = 100
    model_retry_max_delay_ms: Annotated[int, Field(ge=0, le=3600000)] = 60000
    check_execution: Literal["disabled", "trusted", "bubblewrap"] = "disabled"

    @model_validator(mode="before")
    @classmethod
    def grouped_settings(cls, value):
        if isinstance(value, dict) and "system" in value:
            value = dict(value)
            system = value.pop("system")
            if not isinstance(system, dict) or system.keys() & value.keys():
                raise ValueError("Configure each system setting once in the system block")
            value = {**system, **value}
        return value

    @property
    def system(self):
        """One validated view of the complete OS configuration, without agent policy."""
        return RuntimeConfig.model_validate({key: getattr(self, key) for key in RuntimeConfig.model_fields},
                                            context={"resolve_environment_capacity": False})

    @model_validator(mode="before")
    @classmethod
    def environment_capacity(cls, value, info: ValidationInfo):
        if info.context and info.context.get("resolve_environment_capacity") is False:
            return value
        if isinstance(value, dict) and "POLYINFERENCE_LOCAL_BATCH_SIZE" in os.environ:
            value = dict(value)
            grouped = value.get("system")
            settings = dict(grouped) if isinstance(grouped, dict) else value
            local = settings.get("local")
            local = local.model_dump() if isinstance(local, Endpoint) else dict(local or {})
            local["max_inflight"] = os.environ["POLYINFERENCE_LOCAL_BATCH_SIZE"]
            settings["local"] = local
            if isinstance(grouped, dict):
                value["system"] = settings
        return value

    @model_validator(mode="after")
    def feasible_resources(self):
        if not self.role_bindings:
            raise ValueError("Pin at least one role binding")
        for endpoint in (self.local, self.cloud):
            if endpoint.reserved_context_tokens < endpoint.max_context_tokens:
                raise ValueError("One maximum-size context must fit")
        names = [c.name for c in self.checks]
        if len(names) != len(set(names)):
            raise ValueError("Check names must be unique")
        if self.control_token_reserve >= self.run_token_budget:
            raise ValueError("Control reserve must be smaller than the run token budget")
        if self.run_spend_budget_microusd or self.limits.max_api_spend_microusd:
            for name in set(self.role_bindings.values()):
                endpoint = getattr(self, name)
                if endpoint.physical_location == "cloud" and endpoint.estimated_microusd_per_token is None:
                    raise ValueError("A spend estimate requires an explicit endpoint token price")
        if self.limits.cost_guarantee == "enforced":
            raise ValueError("No provider-enforced dollar quota; use estimate with the OS token budget")
        return self

    @property
    def repo_path(self):
        return Path(self.repository).resolve()

    @property
    def state_path(self):
        return Path(self.state_directory).resolve()

