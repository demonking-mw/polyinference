from __future__ import annotations

import json

import pytest

from polyinference.costs import combine_costs, estimate, run_cost


def test_codex_cost_counts_cached_tokens_once_and_reasoning_with_output():
    usage = {
        "inputTokens": 1000000,
        "cachedInputTokens": 200000,
        "cacheWriteInputTokens": 100000,
        "outputTokens": 10000,
        "reasoningOutputTokens": 4000,
    }
    value = estimate("gpt-6.1-sol", "codex_app_server", usage)
    # 700k fresh * $2 + 200k cached * $.10 + 100k writes * $2.50 + 10k output * $10.
    assert value["estimated_usd"] == pytest.approx(1.77)
    assert value["input_tokens"] == 1000000 and value["output_tokens"] == 10000
    raw = estimate(
        "gpt-6.1-sol",
        "responses",
        {
            "input_tokens": 1000000,
            "input_tokens_details": {"cached_tokens": 200000, "cache_write_tokens": 100000},
            "output_tokens": 10000,
        },
    )
    assert raw["estimated_usd"] == pytest.approx(3.49)


@pytest.mark.parametrize("long_prompt", [False, True])
def test_haiku_cost_prices_all_cache_categories_and_long_prompts(long_prompt):
    usage = {
        "input_tokens": 90000 if long_prompt else 1000,
        "output_tokens": 2000,
        "cache_read_input_tokens": 10000,
        "cache_creation_input_tokens": 2000,
        "cache_creation": {"ephemeral_1h_input_tokens": 500, "ephemeral_5m_input_tokens": 1500},
    }
    value = estimate("claude-haiku-5-5", "anthropic", usage)
    factor = 5 if long_prompt else 1
    expected = (
        (usage["input_tokens"] * 0.1 + 10000 * 0.01 + 1500 * 0.125 + 500 * 0.2 + 2000 * 0.5)
        * factor
        / 1000000
    )
    assert value["estimated_usd"] == pytest.approx(expected)
    assert value["input_tokens"] == usage["input_tokens"] + 12000


def test_costs_deduplicate_effects_recover_old_native_usage_and_report_unknowns():
    def effect(op_id, kind="agent_job", state="succeeded", ref=None):
        return {
            "state": state,
            "request": {"operation_id": op_id, "payload": {"kind": kind}},
            "result": {
                "actual_backend": {"model_version": "gpt-6.1-sol", "harness_version": "codex_app_server"},
                "output_refs": [{"digest": ref or op_id}],
            },
        }

    native = json.dumps(
        {
            "model": "gpt-6.1-sol",
            "usage": None,
            "events": [
                {
                    "method": "thread/tokenUsage/updated",
                    "params": {
                        "tokenUsage": {
                            "total": {"inputTokens": 100, "cachedInputTokens": 20, "outputTokens": 10}
                        }
                    },
                },
                {
                    "method": "thread/tokenUsage/updated",
                    "params": {
                        "tokenUsage": {
                            "total": {"inputTokens": 200, "cachedInputTokens": 40, "outputTokens": 20}
                        }
                    },
                },
            ],
        }
    )
    records = {
        "effect/a": effect("a"),
        "effect/duplicate-a": effect("a"),
        "effect/tool": effect("tool", kind="capability_call"),
        "effect/pending": effect("pending", state="uncertain"),
        "effect/no-usage": effect("no-usage"),
    }

    def read(ref):
        return native if ref["digest"] == "a" else "{}"

    value = run_cost(records, read)
    assert value["calls"] == 3 and value["priced_calls"] == 1
    assert value["input_tokens"] == 200 and value["output_tokens"] == 20
    assert value["pending_calls"] == 1 and value["unpriced_calls"] == 1 and value["partial"]
    assert value["estimated_usd"] == pytest.approx((160 * 2 + 40 * 0.1 + 20 * 10) / 1000000)
    assert value["by_provider"]["codex"]["calls"] == 1
    combined = combine_costs([value, value])
    assert combined["estimated_usd"] == pytest.approx(value["estimated_usd"] * 2)


def test_raw_missing_usage_estimates_tokens_but_unknown_models_stay_unpriced():
    record = {
        "state": "succeeded",
        "request": {
            "operation_id": "a",
            "payload": {"kind": "model_query", "context": {"parts": [{"content": {"size_bytes": 400}}]}},
        },
        "result": {"actual_backend": {"harness_version": "anthropic"}, "output_refs": [{"digest": "a"}]},
    }
    value = run_cost(
        {"effect/a": record}, lambda _: json.dumps({"model": "claude-haiku-5-5", "text": "x" * 40})
    )
    assert value["estimated_token_calls"] == 1 and value["priced_calls"] == 1
    assert value["input_tokens"] == 100 and value["output_tokens"] == 10
    assert estimate("unknown-model", "chat", {"input_tokens": 100, "output_tokens": 10}) is None


def test_mixed_run_totals_separate_codex_and_haiku_without_child_tool_charges():
    records, outputs = {}, {}
    for index, (kind, model, protocol, usage) in enumerate(
        [
            ("agent_job", "gpt-6.1-sol", "codex_app_server", {"inputTokens": 1000, "outputTokens": 100}),
            ("model_query", "claude-haiku-5-5", "anthropic", {"input_tokens": 2000, "output_tokens": 200}),
            (
                "capability_call",
                "gpt-6.1-sol",
                "codex_app_server",
                {"inputTokens": 9000, "outputTokens": 900},
            ),
        ]
    ):
        key = str(index)
        records["effect/" + key] = {
            "state": "succeeded",
            "request": {"operation_id": key, "payload": {"kind": kind}},
            "result": {
                "actual_backend": {"harness_version": protocol},
                "output_refs": [{"digest": key}],
            },
        }
        outputs[key] = json.dumps({"model": model, "usage": usage})
    value = run_cost(records, lambda ref: outputs[ref["digest"]])
    assert value["calls"] == value["priced_calls"] == 2
    assert value["by_provider"]["codex"]["estimated_usd"] == pytest.approx(0.003)
    assert value["by_provider"]["haiku"]["estimated_usd"] == pytest.approx(0.0003)
    assert value["estimated_usd"] == pytest.approx(0.0033)
    assert not value["partial"]
