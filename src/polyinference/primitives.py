"""Shared identities, serialization and resource defaults, independent of agent policy."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .contracts import Limits
from .os_config import DEFAULTS


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
    return Limits.model_validate(DEFAULTS["Limits"])
