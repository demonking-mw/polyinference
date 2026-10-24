"""All coding-agent choices of OS defaults live together here.

The complete OS schema and generic defaults are in polyinference.system_settings.
JSON callers can override these in one adjacent `system` object. No shared agent
library is required; this module belongs to the coding application.
"""

import sys

from ..domain import Check, default_limits
from ..system_settings import ContextPolicy, Endpoint, InferenceLifecycle


def coding_system_defaults():
    return {
        "limits": default_limits(),
        "model_call_retries": 2,
        "control_token_reserve": 32000,
        "role_bindings": {"senior": "cloud", "worker": "local", "specialist": "cloud"},
        "prepare_repository": True,
        "shell_fail_fast": True,
        # Packing is deterministic. Lossy compaction requires an explicit opt-in.
        "context_policy": ContextPolicy(auto_deal_context=True),
    }


def haiku_endpoint():
    """Complete remote stand-in, shared by the ordinary UI and launch overlay."""
    return Endpoint(protocol="anthropic", base_url="https://api.anthropic.com/v1",
                    model="claude-haiku-5-5", api_key_env="ANTHROPIC_API_KEY",
                    max_context_tokens=128000, reserved_context_tokens=256000,
                    max_inflight=1, timeout_seconds=180, inference_location="cloud",
                    lifecycle=InferenceLifecycle())


def simulation_config(config, slots):
    """Pure invocation policy; the OS receives ordinary fully validated settings."""
    if type(slots) is not int or not 1 <= slots <= 16:
        raise ValueError("--sim-batch requires an integer from 1 to 16")
    endpoint = config.local if config.local.protocol == "anthropic" else haiku_endpoint()
    local = {**endpoint.model_dump(), "max_inflight": slots,
             "reserved_context_tokens": max(endpoint.reserved_context_tokens, slots * endpoint.max_context_tokens)}
    return type(config).model_validate({**config.model_dump(), "local": local, "max_workers": slots,
        "role_bindings": {**config.role_bindings, "worker": "local"}},
        context={"resolve_environment_capacity": False})


def ui_system_settings(source):
    """The UI coding agent's complete OS preferences, configured together."""
    endpoint = Endpoint(
        protocol="codex_app_server",
        model="gpt-6.1-sol",
        command=["codex", "app-server", "-c", 'model_reasoning_effort="low"'],
        max_context_tokens=128000,
        reserved_context_tokens=256000,
        max_inflight=1,
        timeout_seconds=180,
        inference_location="cloud",
    )
    return {**coding_system_defaults(), **dict(
        shell_execution="trusted",
        repository=str(source),
        allowed_write_paths=["greeting.py"],
        closure_paths=["greeting.py", "test_greeting.py"],
        checks=[Check(name="greeting", argv=[sys.executable, "-m", "unittest", "-q"])],
        check_execution="trusted",
        local=haiku_endpoint(),
        cloud=endpoint.model_copy(update={"brokered_tools": True}),
        max_workers=1,
        limits=default_limits().model_copy(
            update={"max_input_tokens_per_call": 96000, "max_output_tokens_per_call": 32000}
        ),
    )}


def endpoint_profile(config, profile=None):
    """Testing application's explicit deployment choice, never inferred from URL."""
    if profile in {None, "configured"}:
        return config
    if profile not in {"small-cloud", "local-inference", "buffered"}:
        raise ValueError("Unknown endpoint profile")
    if config.local.protocol not in {"chat", "responses", "anthropic", "gemini"}:
        raise ValueError("Endpoint profiles require a raw generation endpoint on the local lane")
    values = ({"first_output_seconds": 900, "idle_seconds": 300, "total_seconds": 1800}
              if profile == "local-inference" else {})
    if profile == "buffered":
        values["transport"] = "buffered"
    if config.local.protocol == "gemini" and profile != "buffered":
        raise ValueError("Gemini currently requires the explicit buffered profile")
    return config.model_copy(update={
        "local": config.local.model_copy(update={"lifecycle": InferenceLifecycle(**values)}),
    })
