from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import Limits, Wire
from .domain import Check, default_limits
from .workspace_contracts import RelativePath


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
    timeout_seconds: Annotated[float, Field(gt=0, le=1800)] = 180
    estimated_microusd_per_token: Annotated[float, Field(ge=0)] | None = None

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


class AgentConfig(Wire):
    repository: str
    state_directory: str = ".polyinference"
    objective: Annotated[str, Field(min_length=1)]
    allowed_write_paths: Annotated[list[RelativePath], Field(min_length=1)]
    closure_paths: list[RelativePath] = Field(default_factory=list)
    checks: Annotated[list[Check], Field(min_length=1)]
    local: Endpoint
    cloud: Endpoint
    role_bindings: dict[str, Literal["local", "cloud"]] = Field(
        default_factory=lambda: {"senior": "cloud", "worker": "local", "specialist": "cloud"}
    )
    prepare_repository: bool = False
    base_branch: str | None = None
    write_scope: Literal["explicit", "project"] = "explicit"
    shell_execution: Literal["disabled", "trusted", "bubblewrap"] = "disabled"
    senior_development_fraction: Annotated[float, Field(ge=0, le=1)] = 0.1
    max_workers: Annotated[int, Field(gt=0, le=16)] = 2
    max_sprints: Annotated[int, Field(gt=0, le=100)] = 8
    max_senior_corrections: Annotated[int, Field(ge=0, le=3)] = 1
    limits: Limits = Field(default_factory=default_limits)
    run_token_budget: Annotated[int, Field(gt=0)] = 64000000
    review_token_reserve: Annotated[int, Field(ge=0)] = 32000
    run_spend_budget_microusd: Annotated[int, Field(gt=0)] | None = None
    max_artifact_bytes: Annotated[int, Field(gt=0)] = 128 * 1024 * 1024
    max_workspace_bytes: Annotated[int, Field(gt=0)] = 64 * 1024 * 1024
    max_workspace_total_bytes: Annotated[int, Field(gt=0)] = 1024 * 1024 * 1024
    max_queued_operations: Annotated[int, Field(gt=0, le=4096)] = 128
    max_command_seconds: Annotated[float, Field(gt=0, le=3600)] = 300
    max_model_response_bytes: Annotated[int, Field(gt=0)] = 4 * 1024 * 1024
    check_execution: Literal["disabled", "trusted", "bubblewrap"] = "disabled"

    @model_validator(mode="before")
    @classmethod
    def environment_capacity(cls, value):
        if isinstance(value, dict) and "POLYINFERENCE_LOCAL_BATCH_SIZE" in os.environ:
            value = dict(value)
            local = value.get("local")
            local = local.model_dump() if isinstance(local, Endpoint) else dict(local or {})
            local["max_inflight"] = os.environ["POLYINFERENCE_LOCAL_BATCH_SIZE"]
            value["local"] = local
        return value

    @model_validator(mode="after")
    def feasible(self):
        if set(self.role_bindings) != {"senior", "worker", "specialist"}:
            raise ValueError("Pin all three role bindings")
        for role in ("worker", "specialist"):
            backend = getattr(self, self.role_bindings[role])
            if backend.protocol not in {"chat", "responses", "gemini", "anthropic"} and not (
                backend.protocol == "codex_app_server" and backend.brokered_tools
            ):
                raise ValueError("Opaque native coding jobs cannot enforce the worker protocol")
        for endpoint in (self.local, self.cloud):
            if endpoint.reserved_context_tokens < endpoint.max_context_tokens:
                raise ValueError("One maximum-size context must fit")
        names = [c.name for c in self.checks]
        if len(names) != len(set(names)):
            raise ValueError("Check names must be unique")
        if self.review_token_reserve >= self.run_token_budget:
            raise ValueError("Review reserve must be smaller than the run token budget")
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
