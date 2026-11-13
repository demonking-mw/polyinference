"""All coding-agent choices of OS defaults live together here.

The complete OS schema and generic defaults are in polyinference.system_settings.
JSON callers can override these in one adjacent `system` object. No shared agent
library is required; this module belongs to the coding application.
"""

import json
import os
import sys
from pathlib import Path

from ..domain import Check, default_limits
from ..os_config import LocalTokenLimits
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
                    max_inflight=1, timeout_seconds=180, inference_location="cloud",
                    lifecycle=InferenceLifecycle())


def haiku_token_limits():
    """Application preset for fresh remote Haiku worker runs."""
    return LocalTokenLimits(input_tokens=96000, output_tokens=32000)


def simulation_config(config, slots):
    """Pure invocation policy; the OS receives ordinary fully validated settings."""
    if type(slots) is not int or not 1 <= slots <= 16:
        raise ValueError("--sim-batch requires an integer from 1 to 16")
    preserve_endpoint = (config.local.protocol == "anthropic"
                         and config.local.inference_location != "local")
    endpoint = config.local if preserve_endpoint else haiku_endpoint()
    local = {**endpoint.model_dump(), "max_inflight": slots}
    return type(config).model_validate({**config.model_dump(), "local": local, "max_workers": slots,
        "local_token_limits": config.local_token_limits if preserve_endpoint else haiku_token_limits(),
        "role_bindings": {**config.role_bindings, "worker": "local"}},
        context={"resolve_environment_capacity": False})


def ui_system_settings(source):
    """The UI coding agent's complete OS preferences, configured together."""
    endpoint = Endpoint(
        protocol="codex_app_server",
        model="gpt-6.1-sol",
        command=["codex", "app-server"],
        max_inflight=1,
        timeout_seconds=1800,
        inference_location="cloud",
    )
    settings = {**coding_system_defaults(), **dict(
        shell_execution="trusted",
        repository=str(source),
        allowed_write_paths=["greeting.py"],
        closure_paths=["greeting.py", "test_greeting.py"],
        checks=[Check(name="greeting", argv=[sys.executable, "-m", "unittest", "-q"])],
        check_execution="trusted",
        local=haiku_endpoint(),
        local_token_limits=haiku_token_limits(),
        cloud=endpoint.model_copy(update={"brokered_tools": True}),
        max_workers=1,
        limits=default_limits(),
    )}
    directory = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "polyinference"
    path = directory / "ui-defaults.json"
    if path.is_file():
        preferences = json.loads(path.read_text())
        allowed = {"local", "local_token_limits", "max_workers", "local_strata_config", "local_strata_profile"}
        if not isinstance(preferences, dict) or preferences.keys() - allowed:
            raise ValueError(f"{path}: expected only {', '.join(sorted(allowed))}")
        # Replace the whole endpoint: a local server must not inherit Haiku credentials.
        if "local" in preferences:
            preferences["local"] = Endpoint.model_validate(preferences["local"])
        if preferences.get("local_strata_config") is not None:
            preferences["local_strata_config"] = str(
                (directory / preferences["local_strata_config"]).resolve())
        settings.update(preferences)
    return settings


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
