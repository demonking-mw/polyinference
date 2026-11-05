from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, ConfigDict, Field, ValidationInfo, model_serializer, model_validator

from .contracts import DataPolicy, Limits, Wire
from .execution_contracts import Check
from .os_config import BOUNDS, LocalTokenLimits, OSTuning, default
from .primitives import runtime_limits
from .workspace_contracts import RelativePath


class OSSettings(Wire):
    model_config = ConfigDict(validate_default=True)


class ContextPolicy(OSSettings):
    """Caller-selected context assistance. Hard execution guards are unconditional."""

    auto_deal_context: bool = default("ContextPolicy", "auto_deal_context")
    auto_compaction: bool = default("ContextPolicy", "auto_compaction")
    compaction_trigger: Annotated[float, Field(gt=0, le=1)] = default("ContextPolicy", "compaction_trigger")
    compaction_target: Annotated[float, Field(gt=0, lt=1)] = default("ContextPolicy", "compaction_target")
    max_compaction_calls: Annotated[int, Field(ge=0, le=BOUNDS["compaction_calls"])] = default("ContextPolicy", "max_compaction_calls")
    compaction_summary_bytes: Annotated[int, Field(gt=0)] = default("ContextPolicy", "compaction_summary_bytes")
    recovery_headroom: Annotated[int, Field(ge=0)] = default("ContextPolicy", "recovery_headroom")

    @model_validator(mode="before")
    @classmethod
    def retire_helper_token_cap(cls, value):
        if isinstance(value, dict) and "compaction_output_tokens" in value:
            value = dict(value)
            legacy = value.pop("compaction_output_tokens")
            if isinstance(legacy, bool) or not isinstance(legacy, int) or legacy <= 0:
                raise ValueError("Legacy compaction_output_tokens must be positive; use local_token_limits")
        return value

    @model_validator(mode="after")
    def valid_target(self):
        if self.compaction_target >= self.compaction_trigger:
            raise ValueError("Compaction target must be below its trigger")
        return self


class InferenceSafety(OSSettings):
    """Common raw/native completion and response recovery settings."""

    output_recoveries: Annotated[int, Field(ge=0, le=BOUNDS["output_recoveries"])] = default("InferenceSafety", "output_recoveries")
    smaller_response_bytes: Annotated[int, Field(gt=0)] = default("InferenceSafety", "smaller_response_bytes")
    require_output_token_enforcement: bool = default("InferenceSafety", "require_output_token_enforcement")
    require_completion_metadata: Literal[True] = default("InferenceSafety", "require_completion_metadata")


class InferenceLifecycle(OSSettings):
    """Explicit deployment timings; binding names and URLs imply no safety facts."""

    transport: Literal["sse", "buffered"] = default("InferenceLifecycle", "transport")
    connect_seconds: Annotated[float, Field(gt=0, le=BOUNDS["connect_seconds"])] = default("InferenceLifecycle", "connect_seconds")
    first_output_seconds: Annotated[float, Field(gt=0, le=BOUNDS["first_output_seconds"])] = default("InferenceLifecycle", "first_output_seconds")
    idle_seconds: Annotated[float, Field(gt=0, le=BOUNDS["idle_seconds"])] = default("InferenceLifecycle", "idle_seconds")
    total_seconds: Annotated[float, Field(gt=0, le=BOUNDS["total_seconds"])] = default("InferenceLifecycle", "total_seconds")


class RetryModel(OSSettings):
    """Caller-selected alternate on the same provider/protocol and authority envelope."""

    model: Annotated[str, Field(min_length=1)]
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"] = default("RetryModel", "reasoning_effort")
    fallback_calls: Annotated[int, Field(ge=1, le=BOUNDS["fallback_calls"])] = default("RetryModel", "fallback_calls")


class Endpoint(OSSettings):
    protocol: Literal["chat", "responses", "gemini", "anthropic", "codex_app_server", "codex_proxy"] = default("Endpoint", "protocol")
    base_url: str = default("Endpoint", "base_url")
    model: str
    api_key_env: str | None = default("Endpoint", "api_key_env")
    command: list[str] = Field(default_factory=lambda: default("Endpoint", "command"))
    max_inflight: Annotated[int, Field(gt=0, le=BOUNDS["inflight"])] = default("Endpoint", "max_inflight")
    max_context_tokens: Annotated[int, Field(gt=0)] | None = Field(
        default=default("Endpoint", "max_context_tokens"), exclude_if=lambda value: value is None)
    reserved_context_tokens: Annotated[int, Field(gt=0)] | None = Field(
        default=default("Endpoint", "reserved_context_tokens"), exclude_if=lambda value: value is None)
    readonly_snapshot_root: str | None = default("Endpoint", "readonly_snapshot_root")
    brokered_tools: bool = default("Endpoint", "brokered_tools")
    inference_location: Literal["local", "cloud"] | None = default("Endpoint", "inference_location")
    supports_temperature: bool = default("Endpoint", "supports_temperature")
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"] = default("Endpoint", "reasoning_effort")
    retry_model: RetryModel | None = Field(default=default("Endpoint", "retry_model"), exclude_if=lambda value: value is None)
    input_token_count_path: Annotated[str, Field(pattern=r"^/(?:[A-Za-z0-9_-]+/)*(?:input_tokens|count_tokens)$")] | None = Field(
        default=default("Endpoint", "input_token_count_path"), exclude_if=lambda value: value is None)
    timeout_seconds: Annotated[float, Field(gt=0, le=BOUNDS["endpoint_timeout_seconds"])] = default("Endpoint", "timeout_seconds")
    lifecycle: InferenceLifecycle | None = Field(default=default("Endpoint", "lifecycle"), exclude_if=lambda value: value is None)
    estimated_microusd_per_token: Annotated[float, Field(ge=0)] | None = default("Endpoint", "estimated_microusd_per_token")

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


class RuntimeConfig(OSSettings):
    """OS resources and optional file capabilities; no coding-agent requirements."""

    repository: str
    tuning: OSTuning = Field(default_factory=OSTuning)
    local_token_limits: LocalTokenLimits = Field(default_factory=LocalTokenLimits)
    state_directory: str = default("RuntimeConfig", "state_directory")
    allowed_write_paths: list[RelativePath] = Field(default_factory=lambda: default("RuntimeConfig", "allowed_write_paths"))
    closure_paths: list[RelativePath] = Field(default_factory=lambda: default("RuntimeConfig", "closure_paths"))
    checks: list[Check] = Field(default_factory=lambda: default("RuntimeConfig", "checks"))
    local: Endpoint
    cloud: Endpoint
    role_bindings: dict[str, Literal["local", "cloud"]] = Field(
        default_factory=lambda: default("RuntimeConfig", "role_bindings")
    )
    prepare_repository: bool = default("RuntimeConfig", "prepare_repository")
    cloud_agent_timeout_interrupt: bool = Field(
        default=default("RuntimeConfig", "cloud_agent_timeout_interrupt"), strict=True,
        description="Interrupt cloud AgentJob calls at endpoint.timeout_seconds; false logs a warning and keeps the job running. Original deadlines and explicit cancellation still apply.")
    data_policy: DataPolicy | None = Field(default=default("RuntimeConfig", "data_policy"), exclude_if=lambda value: value is None)
    output_directory: str | None = default("RuntimeConfig", "output_directory")
    base_branch: str | None = default("RuntimeConfig", "base_branch")
    write_scope: Literal["explicit", "project"] = default("RuntimeConfig", "write_scope")
    shell_execution: Literal["disabled", "trusted", "bubblewrap"] = default("RuntimeConfig", "shell_execution")
    shell_fail_fast: bool = default("RuntimeConfig", "shell_fail_fast")
    max_workers: Annotated[int, Field(gt=0, le=BOUNDS["workers"])] = default("RuntimeConfig", "max_workers")
    limits: Limits = Field(default_factory=runtime_limits)
    run_token_budget: Annotated[int, Field(gt=0)] = default("RuntimeConfig", "run_token_budget")
    control_token_reserve: Annotated[int, Field(ge=0)] = Field(
        default=default("RuntimeConfig", "control_token_reserve"), validation_alias=AliasChoices("control_token_reserve", "review_token_reserve"))
    run_spend_budget_microusd: Annotated[int, Field(gt=0)] | None = default("RuntimeConfig", "run_spend_budget_microusd")
    max_artifact_bytes: Annotated[int, Field(gt=0)] = default("RuntimeConfig", "max_artifact_bytes")
    max_workspace_bytes: Annotated[int, Field(gt=0)] = default("RuntimeConfig", "max_workspace_bytes")
    max_workspace_total_bytes: Annotated[int, Field(gt=0)] = default("RuntimeConfig", "max_workspace_total_bytes")
    max_queued_operations: Annotated[int, Field(gt=0, le=BOUNDS["queued_operations"])] = default("RuntimeConfig", "max_queued_operations")
    max_command_seconds: Annotated[float, Field(gt=0, le=BOUNDS["command_seconds"])] = default("RuntimeConfig", "max_command_seconds")
    max_model_response_bytes: Annotated[int, Field(gt=0)] = default("RuntimeConfig", "max_model_response_bytes")
    max_model_request_bytes: Annotated[int, Field(gt=0)] | None = Field(default=default("RuntimeConfig", "max_model_request_bytes"), exclude_if=lambda value: value is None)
    context_policy: ContextPolicy = Field(default_factory=ContextPolicy)
    inference_safety: InferenceSafety = Field(default_factory=InferenceSafety)
    max_repeated_model_failures: Annotated[int, Field(gt=0)] = default("RuntimeConfig", "max_repeated_model_failures")
    max_model_recoveries: Annotated[int, Field(ge=0)] = default("RuntimeConfig", "max_model_recoveries")
    model_call_retries: Annotated[int, Field(ge=0, le=BOUNDS["model_call_retries"])] = default("RuntimeConfig", "model_call_retries")
    model_retry_delay_ms: Annotated[int, Field(ge=0, le=BOUNDS["retry_delay_ms"])] = default("RuntimeConfig", "model_retry_delay_ms")
    model_retry_max_delay_ms: Annotated[int, Field(ge=0, le=BOUNDS["retry_max_delay_ms"])] = default("RuntimeConfig", "model_retry_max_delay_ms")
    check_execution: Literal["disabled", "trusted", "bubblewrap"] = default("RuntimeConfig", "check_execution")

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

    @model_validator(mode="before")
    @classmethod
    def resolve_local_tokens(cls, value):
        """Migrate legacy input once; the explicit pair overrides every projection."""
        if not isinstance(value, dict):
            return value
        value = dict(value)
        grouped = value.get("system")
        settings = dict(grouped) if isinstance(grouped, dict) else value
        legacy_target = value.pop("model_output_target_tokens", None)
        if "model_output_target_tokens" in settings:
            legacy_target = settings.pop("model_output_target_tokens")
        if "local_token_limits" not in settings:
            limits = settings.get("limits")
            limits = limits.model_dump() if hasattr(limits, "model_dump") else dict(limits or {})
            pair = LocalTokenLimits(
                input_tokens=limits.get("max_input_tokens_per_call", LocalTokenLimits().input_tokens),
                output_tokens=legacy_target or limits.get("max_output_tokens_per_call", LocalTokenLimits().output_tokens),
            )
            local = settings.get("local")
            local = local.model_dump() if hasattr(local, "model_dump") else dict(local or {})
            if local.get("max_context_tokens") is not None and int(local["max_context_tokens"]) > pair.output_tokens:
                pair = pair.model_copy(update={"input_tokens": min(pair.input_tokens,
                    int(local["max_context_tokens"]) - pair.output_tokens)})
            settings["local_token_limits"] = pair
        elif legacy_target is not None:
            pair = LocalTokenLimits.model_validate(settings["local_token_limits"])
            if legacy_target != pair.output_tokens:
                raise ValueError("Configure local output_tokens once in local_token_limits")
        if "limits" in settings:
            limits = settings["limits"]
            limits = limits.model_dump() if hasattr(limits, "model_dump") else limits
            if isinstance(limits, dict):
                pair = LocalTokenLimits.model_validate(settings["local_token_limits"])
                settings["limits"] = {**limits, "max_input_tokens_per_call": pair.input_tokens,
                                      "max_output_tokens_per_call": pair.output_tokens}
        if isinstance(grouped, dict):
            value["system"] = settings
        return value

    @model_validator(mode="after")
    def feasible_resources(self):
        if not self.role_bindings:
            raise ValueError("Pin at least one role binding")
        # Legacy fields are compatibility projections, never independent local caps.
        pair = self.local_token_limits
        object.__setattr__(self, "limits", self.limits.model_copy(update={
            "max_input_tokens_per_call": pair.input_tokens,
            "max_output_tokens_per_call": pair.output_tokens,
        }))
        local_caps = self.token_limits_for_binding("local")
        object.__setattr__(self, "local", self.local.model_copy(update={
            "max_context_tokens": pair.context_tokens if local_caps else None,
            "reserved_context_tokens": pair.context_tokens * self.local.max_inflight if local_caps else None,
        }))
        object.__setattr__(self, "cloud", self.cloud.model_copy(update={
            "max_context_tokens": None, "reserved_context_tokens": None,
        }))
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

    def token_limits(self, role):
        """Cloud inference owns its per-call token limits; campaign budgets still apply."""
        return self.token_limits_for_binding(self.role_bindings[role])

    def token_limits_for_binding(self, binding):
        endpoint = getattr(self, binding)
        native_cloud = endpoint.protocol in {"codex_app_server", "codex_proxy"} and endpoint.physical_location == "cloud"
        return self.local_token_limits if binding == "local" and not native_cloud else None

    def request_byte_limit(self):
        # Serialized bytes are an independent transport bound, not a token count.
        return self.max_model_request_bytes or default("RuntimeConfig", "max_model_request_bytes")

    @property
    def repo_path(self):
        return Path(self.repository).resolve()

    @property
    def state_path(self):
        return Path(self.state_directory).resolve()

