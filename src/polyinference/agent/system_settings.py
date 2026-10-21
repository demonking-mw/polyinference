"""All coding-agent choices of OS defaults live together here.

The complete OS schema and generic defaults are in polyinference.system_settings.
JSON callers can override these in one adjacent `system` object. No shared agent
library is required; this module belongs to the coding application.
"""

import sys

from ..domain import Check, default_limits
from ..system_settings import ContextPolicy, Endpoint


def coding_system_defaults():
    return {
        "limits": default_limits(),
        "control_token_reserve": 32000,
        "role_bindings": {"senior": "cloud", "worker": "local", "specialist": "cloud"},
        "prepare_repository": True,
        "shell_fail_fast": True,
        # Packing is deterministic. Lossy compaction requires an explicit opt-in.
        "context_policy": ContextPolicy(auto_deal_context=True),
    }


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
        local=Endpoint(
            protocol="anthropic",
            base_url="https://api.anthropic.com/v1",
            model="claude-haiku-5-5",
            api_key_env="ANTHROPIC_API_KEY",
            max_context_tokens=128000,
            reserved_context_tokens=256000,
            max_inflight=1,
            timeout_seconds=180,
            inference_location="cloud",
        ),
        cloud=endpoint.model_copy(update={"brokered_tools": True}),
        max_workers=1,
        limits=default_limits().model_copy(
            update={"max_input_tokens_per_call": 96000, "max_output_tokens_per_call": 32000}
        ),
    )}
