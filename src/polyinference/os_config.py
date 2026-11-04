"""Canonical OS defaults and operational tuning. No agent policy or provider scheduler.

Change defaults here, or override exported RuntimeConfig fields/system.tuning in a
fresh run configuration. Existing state pins the resolved configuration. Wire tags,
resource ownership, authority and physical-termination rules are not tuning knobs.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULTS = {
    "LocalTokenLimits": {"input_tokens": 24000, "output_tokens": 4000},
    "InferencePolicy": {"additional_retries": 0, "replace_undelivered": False},
    "ContextPart": {"compactable": False, "retention_priority": 0},
    "ContextPolicy": {
        "auto_deal_context": False,
        "auto_compaction": False,
        "compaction_trigger": 0.8,
        "compaction_target": 0.6,
        "max_compaction_calls": 8,
        "compaction_summary_bytes": 4096,
        "recovery_headroom": 1024,
    },
    "InferenceSafety": {
        "output_recoveries": 2,
        "smaller_response_bytes": 4096,
        "require_output_token_enforcement": False,
        "require_completion_metadata": True,
    },
    "InferenceLifecycle": {
        "transport": "sse",
        "connect_seconds": 10,
        "first_output_seconds": 180,
        "idle_seconds": 90,
        "total_seconds": 600,
    },
    "RetryModel": {"reasoning_effort": "medium", "fallback_calls": 7},
    "Endpoint": {
        "protocol": "chat",
        "base_url": "http://127.0.0.1:8000/v1",
        "api_key_env": None,
        "command": ["codex", "app-server"],
        "max_inflight": 2,
        "max_context_tokens": None,
        "reserved_context_tokens": None,
        "readonly_snapshot_root": None,
        "brokered_tools": False,
        "inference_location": None,
        "supports_temperature": True,
        "reasoning_effort": "medium",
        "retry_model": None,
        "input_token_count_path": None,
        "timeout_seconds": 180,
        "lifecycle": None,
        "estimated_microusd_per_token": None,
    },
    "RuntimeConfig": {
        "state_directory": ".polyinference",
        "allowed_write_paths": [],
        "closure_paths": [],
        "checks": [],
        "role_bindings": {"default": "local"},
        "prepare_repository": False,
        "cloud_agent_timeout_interrupt": False,
        "data_policy": None,
        "output_directory": None,
        "base_branch": None,
        "write_scope": "explicit",
        "shell_execution": "disabled",
        "shell_fail_fast": False,
        "max_workers": 2,
        "run_token_budget": 64000000,
        "control_token_reserve": 0,
        "run_spend_budget_microusd": None,
        "max_artifact_bytes": 134217728,
        "max_workspace_bytes": 67108864,
        "max_workspace_total_bytes": 1073741824,
        "max_queued_operations": 128,
        "max_command_seconds": 300,
        "max_model_response_bytes": 4194304,
        "max_model_request_bytes": 4194304,
        "max_repeated_model_failures": 2,
        "max_model_recoveries": 2,
        "model_call_retries": 1,
        "model_retry_delay_ms": 100,
        "model_retry_max_delay_ms": 60000,
        "check_execution": "disabled",
    },
    "Limits": {
        "max_steps": 2048,
        "max_model_calls": 512,
        "max_repairs": 0,
        "max_total_tokens": 16000000,
        "max_output_bytes": 262144,
        "max_wall_time_ms": 3600000,
        "max_api_spend_microusd": 0,
        "cost_guarantee": "estimate",
        "final_phase_reserve": None,
    },
}
DEFAULTS["Limits"].update(
    max_input_tokens_per_call=DEFAULTS["LocalTokenLimits"]["input_tokens"],
    max_output_tokens_per_call=DEFAULTS["LocalTokenLimits"]["output_tokens"],
)


def default(section, name):
    """Return an independent copy, including for standalone helper defaults."""
    return deepcopy(DEFAULTS[section][name])


# Validation ceilings of existing public settings, not alternate execution values.
# Zero/one constraints, units, enum/wire versions and authority guards are invariants.
BOUNDS = {
    "additional_retries": 3,
    "compaction_calls": 32,
    "output_recoveries": 3,
    "connect_seconds": 1800,
    "first_output_seconds": 3600,
    "idle_seconds": 3600,
    "total_seconds": 7200,
    "fallback_calls": 32,
    "inflight": 32,
    "endpoint_timeout_seconds": 1800,
    "workers": 16,
    "queued_operations": 4096,
    "command_seconds": 3600,
    "model_call_retries": 3,
    "retry_delay_ms": 60000,
    "retry_max_delay_ms": 3600000,
    "check_seconds": 600,
    "shell_seconds": 600,
    "notification_chars": 16000,
    "resume_chars": 16000,
    "request_id_chars": 128,
    "error_chars": 4000,
    "retrieval_reason_chars": 1000,
}

DISTRIBUTION_WEIGHT_TOLERANCE = 1e-9
KERNEL_VERSION = "simple-os/6"
STORAGE_POLICY = {"journal_mode": "WAL", "synchronous": "FULL"}
EXCLUSIVE_FALLBACK_SECONDS = 3600
CHECK_DEFAULT_SECONDS = 60
# Stable adapter/client identities are centralized for maintenance, not user overrides.
NATIVE_CLIENT = {"name": "polyinference", "version": "0.1.0"}

Positive = Annotated[int, Field(gt=0)]
Nonnegative = Annotated[int, Field(ge=0)]
Seconds = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class FrozenEnvironment(dict):
    """String mapping with normal JSON encoding and no mutable configuration alias."""

    def _immutable(self, *args, **kwargs):
        raise TypeError("Resolved OS tuning is immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


class LocalTokenLimits(BaseModel):
    """One local-lane input/output pair, including API stand-ins for local workers."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)
    input_tokens: Positive = default("LocalTokenLimits", "input_tokens")
    output_tokens: Positive = default("LocalTokenLimits", "output_tokens")

    @property
    def context_tokens(self):
        return self.input_tokens + self.output_tokens


class OSTuning(BaseModel):
    """Generic operational settings, resolved and pinned with each runtime config."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)
    journal_retention_events: Positive | None = 10000
    events_page_size: Positive = 100
    events_page_max: Positive = 1000
    sqlite_timeout_seconds: Seconds = 5
    exclusive_wait_seconds: Seconds | None = None
    lock_poll_seconds: Seconds = 0.05
    subprocess_stream_bytes: Positive = 65536
    command_chunk_bytes: Positive = 65536
    tool_chunk_bytes: Positive = 8192
    file_list_default: Positive = 1000
    file_list_max: Positive = 1000
    search_pattern_chars: Positive = 1000
    search_line_chars: Positive = 1000
    search_matches: Positive = 100
    shell_script_chars: Positive = 16000
    shell_default_seconds: Seconds = CHECK_DEFAULT_SECONDS
    shell_max_seconds: Annotated[float, Field(gt=0, le=BOUNDS["shell_seconds"])] = BOUNDS["shell_seconds"]
    shell_command: Annotated[tuple[str, ...], Field(min_length=1)] = ("bash", "-c")
    sandbox_readonly_paths: tuple[str, ...] = ("/usr", "/bin", "/lib", "/lib64", "/etc")
    tool_environment: dict[str, str] = {
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_ADDOPTS": "-p no:cacheprovider",
    }
    native_event_limit: Positive = 2000
    native_recent_events: Positive = 24
    native_method_buckets: Positive = 32
    native_method_chars: Positive = 120
    native_line_bytes: Positive = 1048576
    native_shutdown_seconds: Seconds = 5
    native_error_chars: Positive = 1500
    diagnostic_error_chars: Annotated[int, Field(gt=0, le=BOUNDS["error_chars"])] = BOUNDS["error_chars"]
    diagnostic_preview_chars: Positive = 2000
    check_excerpt_chars: Positive = 3000
    command_error_chars: Positive = 1000
    progress_recent_effects: Positive = 32
    inspector_activity_events: Positive = 120
    progress_time_decimals: Annotated[int, Field(ge=0, le=9)] = 3
    http_max_connections: Positive | None = 100
    http_max_keepalive_connections: Nonnegative | None = 20
    http_keepalive_expiry_seconds: Seconds | None = 5
    http_trust_environment: bool = True
    http_error_chars: Positive = 1024
    http_error_body_bytes: Positive = 16384
    http_counter_body_bytes: Positive = 65536
    http_retry_after_max_ms: Positive = 3600000
    http_recovery_poll_seconds: Seconds = 0.25
    http_progress_interval_seconds: Seconds = 0.25
    http_content_type_items: Positive = 32
    anthropic_version: str = "2023-06-01"
    response_recovery_seconds: Seconds = 30
    retry_backoff_multiplier: Annotated[float, Field(ge=1, allow_inf_nan=False)] = 2
    response_shrink_divisor: Annotated[int, Field(ge=2)] = 2
    context_headroom_divisor: Positive = 10
    compaction_reserve_tokens: Nonnegative = 2000
    compaction_chunk_divisor: Positive = 8
    compaction_min_chunk_bytes: Positive = 64
    compaction_temperature: Annotated[float, Field(ge=0, le=2)] = 0
    workspace_ignored_names: tuple[str, ...] = (
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "node_modules",
        ".venv",
        ".venv-linux",
    )
    environment_directory_names: tuple[str, ...] = ("node_modules", ".venv", ".venv-linux")
    dependency_file_names: tuple[str, ...] = (
        "package.json",
        "package-lock.json",
        "npm-shrinkwrap.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "pyproject.toml",
        "uv.lock",
        "poetry.lock",
        "Pipfile.lock",
    )
    dependency_requirements_prefix: str = "requirements"
    dependency_requirements_suffix: str = ".txt"
    initial_excluded_names: tuple[str, ...] = (
        ".git",
        ".polyinference",
        "node_modules",
        ".npm",
        ".venv",
        ".venv-linux",
        "__pycache__",
    )
    initial_excluded_globs: tuple[str, ...] = ("**/.env*", "**/*.pem", "**/*.key")
    empty_baseline_gitignore: str = ".polyinference/\n.env\n.venv/\nnode_modules/\n__pycache__/\n"
    setup_git_name: str = "PolyInference"
    setup_git_email: str = "agent@localhost"
    publication_git_name: str = "PolyInference"
    publication_git_email: str = "agent@polyinference.local"
    publication_git_date: str = "2000-01-01T00:00:00+0000"

    @field_validator("tool_environment", mode="after")
    @classmethod
    def freeze_environment(cls, value):
        return FrozenEnvironment(value)

    @model_validator(mode="after")
    def coherent(self):
        if self.events_page_size > self.events_page_max or self.file_list_default > self.file_list_max:
            raise ValueError("Default page sizes must fit their maximum")
        if (
            self.http_max_connections is not None
            and self.http_max_keepalive_connections is not None
            and self.http_max_keepalive_connections > self.http_max_connections
        ):
            raise ValueError("Keepalive connection count must fit the total connection limit")
        if self.shell_default_seconds > self.shell_max_seconds:
            raise ValueError("Default shell timeout must fit its maximum")
        protected = {
            "PATH",
            "HOME",
            "XDG_CACHE_HOME",
            "XDG_CONFIG_HOME",
            "XDG_DATA_HOME",
            "XDG_STATE_HOME",
            "TMPDIR",
            "TMP",
            "TEMP",
            "npm_config_cache",
            "PIP_CACHE_DIR",
        }
        if protected & self.tool_environment.keys():
            raise ValueError("Tool environment cannot override host-issued private paths")
        from pathlib import PurePosixPath

        for name in (
            *self.workspace_ignored_names,
            *self.environment_directory_names,
            *self.dependency_file_names,
            *self.initial_excluded_names,
        ):
            if not name or name in {".", ".."} or "/" in name or "\\" in name:
                raise ValueError("Workspace classification names must be single path components")
        for path in self.sandbox_readonly_paths:
            if not PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
                raise ValueError("Sandbox system paths must be absolute without traversal")
        return self


DEFAULT_TUNING = OSTuning()
