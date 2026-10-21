"""Shared identities, serialization and resource defaults, independent of agent policy."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .contracts import Limits


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
    keys = ("payload", "extensions", "grant_ref", "owner_generation", "expected_process_revision",
            "expected_binding_generation", "schedule_ref", "budget_account_ref", "limits", "resources",
            "conflict_keys", "safe_boundary", "replay_policy", "required_features")
    return digest(canonical({key: data[key] for key in keys}))


def runtime_limits():
    return Limits(max_steps=2048, max_model_calls=512, max_repairs=0,
                  max_input_tokens_per_call=24000, max_output_tokens_per_call=4000,
                  max_total_tokens=16000000, max_output_bytes=262144, max_wall_time_ms=3600000,
                  max_api_spend_microusd=0, cost_guarantee="estimate")
