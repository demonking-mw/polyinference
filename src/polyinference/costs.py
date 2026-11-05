"""Approximate debugging costs, separate from billing and admission budgets."""

from __future__ import annotations

import json
import math

PRICING_DATE = "2026-10-17"
SOURCES = [
    "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
    "https://platform.claude.com/docs/en/models/haiku-5-5/overview",
    "https://learn.chatgpt.com/docs/pricing",
]
NOTE = (
    "USD estimates at standard API rates. Codex is an API-equivalent value, "
    "not a subscription charge or remaining allowance. Excludes service-tier, "
    "regional and tool surcharges. Missing usage/prices are marked incomplete."
)


def number(value):
    return max(0, value) if isinstance(value, (int, float)) and math.isfinite(value) else 0


def estimate(model, protocol, usage):
    """Return USD from fresh, cached, cache-write and output token counts."""
    if not isinstance(usage, dict):
        return None
    if model == "claude-haiku-5-5" or model.startswith("claude-haiku-5-5-"):
        if "input_tokens" not in usage or "output_tokens" not in usage:
            return None
        fresh = number(usage["input_tokens"])
        cached = number(usage.get("cache_read_input_tokens"))
        writes = number(usage.get("cache_creation_input_tokens"))
        output = number(usage["output_tokens"])
        long = fresh + cached + writes > 100000
        rates = [0.5, 0.05, 0.625, 2.5] if long else [0.1, 0.01, 0.125, 0.5]
        one_hour = min(writes, number((usage.get("cache_creation") or {}).get("ephemeral_1h_input_tokens")))
        cost = (
            fresh * rates[0]
            + cached * rates[1]
            + (writes - one_hour) * rates[2]
            + one_hour * rates[0] * 2
            + output * rates[3]
        )
    elif model == "gpt-6.1-sol":
        inputs = usage.get("inputTokens", usage.get("input_tokens", usage.get("prompt_tokens")))
        outputs = usage.get("outputTokens", usage.get("output_tokens", usage.get("completion_tokens")))
        if inputs is None or outputs is None:
            return None
        inputs, output = number(inputs), number(outputs)
        details = usage.get("input_tokens_details", usage.get("prompt_tokens_details", {})) or {}
        cached = min(inputs, number(usage.get("cachedInputTokens", details.get("cached_tokens"))))
        writes = min(
            inputs - cached, number(usage.get("cacheWriteInputTokens", details.get("cache_write_tokens")))
        )
        fresh = max(0, inputs - cached - writes)
        # Native totals can contain many short calls. Do not apply long-context
        # premiums to that cumulative number as if it were one prompt.
        long = inputs > 272000 and not protocol.startswith("codex")
        rates = [4, 0.2, 5, 15] if long else [2, 0.1, 2.5, 10]
        cost = fresh * rates[0] + cached * rates[1] + writes * rates[2] + output * rates[3]
    else:
        return None
    return {
        "estimated_usd": cost / 1000000,
        "input_tokens": int(fresh + cached + writes),
        "output_tokens": int(output),
        "cached_input_tokens": int(cached),
        "cache_write_input_tokens": int(writes),
    }


def empty_cost():
    return {
        "currency": "USD",
        "estimated_usd": 0.0,
        "calls": 0,
        "priced_calls": 0,
        "unpriced_calls": 0,
        "pending_calls": 0,
        "estimated_token_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "partial": False,
        "by_provider": {},
        "pricing_date": PRICING_DATE,
        "sources": SOURCES,
        "note": NOTE,
    }


def combine_costs(costs):
    total = empty_cost()
    for cost in costs:
        for field in (
            "estimated_usd",
            "calls",
            "priced_calls",
            "unpriced_calls",
            "pending_calls",
            "estimated_token_calls",
            "input_tokens",
            "output_tokens",
        ):
            total[field] += cost[field]
        for family, value in cost["by_provider"].items():
            group = total["by_provider"].setdefault(family, {"estimated_usd": 0.0, "calls": 0})
            group["estimated_usd"] += value["estimated_usd"]
            group["calls"] += value["calls"]
    total["estimated_usd"] = round(total["estimated_usd"], 8)
    total["partial"] = bool(total["unpriced_calls"] or total["pending_calls"])
    return total


def run_cost(records, read):
    total = empty_cost()
    seen = set()
    effects = []
    for key, effect in records.items():
        if not key.startswith("effect/"):
            continue
        prefix = "inference-attempt/" + effect["request"]["operation_id"] + "/"
        attempts = [
            ("effect/" + v["request"]["operation_id"], v) for k, v in records.items() if k.startswith(prefix)
        ]
        effects.extend(attempts or [(key, effect)])
    for key, effect in effects:
        if not key.startswith("effect/"):
            continue
        request = effect["request"]
        payload = request["payload"]
        if payload["kind"] not in {"agent_job", "model_query"} or request["operation_id"] in seen:
            continue
        seen.add(request["operation_id"])
        total["calls"] += 1
        if effect["state"] in {"prepared", "submitting", "active", "uncertain"}:
            total["pending_calls"] += 1
            continue
        result = effect.get("result") or {}
        backend = result.get("actual_backend") or {}
        model = backend.get("model_version", "")
        protocol = backend.get("harness_version", "")
        response = {}
        try:
            refs = result.get("output_refs", [])
            if refs:
                response = json.loads(read(refs[0]))
            if not isinstance(response, dict):
                response = {}
        except (OSError, ValueError):
            response = {}
        model = response.get("model") or model
        if payload["kind"] == "agent_job" and not protocol:
            protocol = "codex_app_server"
        usage = response.get("usage")
        if not usage:
            # Older native results retained the full usage events, but no normalized usage.
            for event in response.get("events", []):
                if event.get("method") == "thread/tokenUsage/updated":
                    usage = event.get("params", {}).get("tokenUsage", {}).get("total") or usage
        estimated_tokens = False
        if not usage and payload["kind"] == "model_query" and isinstance(response.get("text"), str):
            usage = {
                "input_tokens": math.ceil(
                    sum(p["content"]["size_bytes"] for p in payload["context"]["parts"]) / 4
                ),
                "output_tokens": math.ceil(len(response["text"].encode()) / 4),
            }
            estimated_tokens = True
        value = estimate(model, protocol, usage)
        if value is None:
            total["unpriced_calls"] += 1
            continue
        family = (
            "codex"
            if protocol.startswith("codex")
            else "haiku"
            if model.startswith("claude-haiku")
            else "other"
        )
        group = total["by_provider"].setdefault(family, {"estimated_usd": 0.0, "calls": 0})
        group["calls"] += 1
        group["estimated_usd"] += value["estimated_usd"]
        total["estimated_usd"] += value["estimated_usd"]
        total["input_tokens"] += value["input_tokens"]
        total["output_tokens"] += value["output_tokens"]
        total["priced_calls"] += 1
        total["estimated_token_calls"] += estimated_tokens
    return combine_costs([total])
