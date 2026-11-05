"""Anthropic uses native Messages framing; tools remain application-owned."""

from __future__ import annotations

import json

import httpx
import pytest

from polyinference.config import Endpoint
from polyinference.runtime.inference import EndpointError, HTTPInference, ProviderError, UnknownExecution


async def test_anthropic_headers_history_blocks_and_complete_token_accounting(monkeypatch):
    monkeypatch.setenv("TEST_ANTHROPIC_KEY", "fixture-credential")
    endpoint = Endpoint(
        protocol="anthropic",
        model="claude-haiku-5-5",
        base_url="https://api.anthropic.com/v1",
        api_key_env="TEST_ANTHROPIC_KEY",
    )
    adapter = HTTPInference(endpoint)
    # Preserve the real constructed headers while replacing only the network transport.
    headers = adapter.client.headers
    await adapter.client.aclose()
    calls = []

    async def handler(request):
        calls.append(request)
        assert request.url.path == "/v1/messages"
        assert request.headers["x-api-key"] == "fixture-credential"
        assert request.headers["anthropic-version"] == "2023-06-01"
        assert "authorization" not in request.headers
        payload = json.loads(request.content)
        assert payload["system"] == "authority\n\nmore authority"
        assert payload["messages"] == [
            {"role": "user", "content": "pinned data"},
            {"role": "assistant", "content": "previous action"},
            {"role": "user", "content": "observation"},
        ]
        assert payload["model"] == "claude-haiku-5-5"
        assert payload["max_tokens"] == 50000
        assert "tools" not in payload
        return httpx.Response(
            200,
            json={
                "id": "msg-fixture",
                "model": "claude-haiku-5-5",
                "stop_reason": "end_turn",
                "content": [
                    {"type": "thinking", "thinking": "private reasoning"},
                    {"type": "redacted_thinking", "data": "private"},
                    {"type": "text", "text": '{"ok":'},
                    {"type": "text", "text": "true}"},
                ],
                "usage": {
                    "input_tokens": 5,
                    "output_tokens": 7,
                    "cache_creation_input_tokens": 11,
                    "cache_read_input_tokens": 13,
                },
            },
        )

    adapter.client = httpx.AsyncClient(headers=headers, transport=httpx.MockTransport(handler))
    try:
        result = await adapter.generate(
            [
                {"role": "system", "content": "authority"},
                {"role": "system", "content": "more authority"},
                {"role": "user", "content": "pinned data"},
                {"role": "assistant", "content": "previous action"},
                {"role": "user", "content": "observation"},
            ],
            50000,
        )
        assert result["text"] == '{"ok":true}'
        assert result["usage"]["total_tokens"] == 36
        assert result["provider_id"] == "msg-fixture"
        assert result["model"] == "claude-haiku-5-5"
        assert len(calls) == 1
    finally:
        await adapter.close()


@pytest.mark.parametrize(
    "failure",
    [
        "max_tokens",
        "pause_turn",
        "tool_use",
        "refusal",
        "model_context_window_exceeded",
        "unexpected_block",
        "empty",
        "http_401",
        "http_429",
        "disconnect",
    ],
)
async def test_anthropic_does_not_promote_incomplete_output_or_retry(failure):
    count = 0

    async def handler(request):
        nonlocal count
        count += 1
        if failure == "disconnect":
            raise httpx.ReadError("fixture disconnect")
        if failure.startswith("http_"):
            # Provider error content must not get echoed into logs.
            return httpx.Response(int(failure[5:]), json={"error": {"message": "private-provider-detail"}})
        return httpx.Response(
            200,
            json={
                "stop_reason": failure if failure not in {"unexpected_block", "empty"} else "end_turn",
                "content": []
                if failure == "empty"
                else [
                    {
                        "type": "tool_use" if failure == "unexpected_block" else "text",
                        "text": '{"kind":"candidate","summary":"partial"}',
                    }
                ],
            },
        )

    adapter = HTTPInference(
        Endpoint(protocol="anthropic", model="fixture"),
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    try:
        with pytest.raises(UnknownExecution if failure == "disconnect" else EndpointError) as error:
            await adapter.generate([{"role": "user", "content": "request"}], 10)
        assert count == 1
        assert "private-provider-detail" not in str(error.value)
    finally:
        await adapter.close()


@pytest.mark.parametrize("status,category,retryable", [
    (400, "invalid_request", False), (401, "authentication", False),
    (403, "permission", False), (429, "rate_limit", True), (503, "service_unavailable", True),
])
async def test_structured_provider_errors_are_bounded_and_credentials_are_redacted(monkeypatch, status, category, retryable):
    monkeypatch.setenv("FIXTURE_KEY", "fixture-private-key")

    async def handler(request):
        return httpx.Response(status, headers={"request-id": "req-fixture", "retry-after": "2"}, json={
            "error": {"type": "fixture_error", "message": "Bad parameter; api_key=fixture-private-key " + "x" * 3000},
        })

    adapter = HTTPInference(Endpoint(protocol="anthropic", model="fixture", api_key_env="FIXTURE_KEY"),
                            httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    try:
        with pytest.raises(ProviderError) as raised:
            await adapter.generate([{"role": "user", "content": "request"}], 20)
        error = raised.value
        assert error.diagnostics["category"] == category
        assert error.diagnostics["request_id"] == "req-fixture"
        assert error.diagnostics["retry_after_ms"] == 2000
        assert error.retryable == retryable
        assert "fixture-private-key" not in json.dumps(error.diagnostics)
        assert len(error.diagnostics["provider_message"]) <= 1024
    finally:
        await adapter.close()


async def test_invalid_assistant_prefill_is_rejected_before_submission():
    submitted = False

    async def handler(request):
        nonlocal submitted
        submitted = True
        raise AssertionError("Invalid request reached provider")

    adapter = HTTPInference(Endpoint(protocol="anthropic", model="claude-haiku-5-5"),
                            httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    try:
        with pytest.raises(ProviderError) as raised:
            await adapter.generate([{"role": "user", "content": "task"},
                                    {"role": "assistant", "content": "candidate"}], 20)
        assert raised.value.diagnostics["submitted"] is False
        assert not submitted
    finally:
        await adapter.close()
