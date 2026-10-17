"""Endpoint clients. Raw generation and native agent jobs are distinct protocols."""

from __future__ import annotations

import asyncio
import json
import os
from collections import deque
from contextlib import asynccontextmanager

import httpx


class EndpointError(RuntimeError):
    pass


class UnknownExecution(EndpointError):
    """The transport ended without proof the provider stopped."""


class Admission:
    """Bounded requests/tokens, FIFO with alternating verifier and ordinary lanes."""

    def __init__(self, limit, token_limit, records=None, name="local", max_queued=128):
        self.limit, self.token_limit = limit, token_limit
        self.records, self.name, self.max_queued = records, name, max_queued
        self.active = self.tokens = 0
        self.queues = [deque(), deque()]
        self.next_lane = 0
        self.condition = asyncio.Condition()

    def restore(self):
        """Unknown remote work still occupies capacity after coordinator restart."""
        self.active = self.tokens = 0
        if not self.records:
            return
        for key, revision, body in self.records.scan("reservation/" + self.name + "/"):
            if body["state"] != "held":
                continue
            effect = self.records.get("effect/" + body["operation_id"])
            if effect and (effect[1].get("result") or effect[1]["state"] == "prepared"):
                self.records.compare_and_publish({key: revision}, {key: {**body, "state": "released"}})
            else:
                self.active += 1
                self.tokens += body["tokens"]

    def snapshot(self):
        return {
            "limit": self.limit,
            "active": self.active,
            "reserved_tokens": self.tokens,
            "token_limit": self.token_limit,
            "ordinary_waiters": len(self.queues[0]),
            "finishing_waiters": len(self.queues[1]),
        }

    def _front(self):
        lane = self.next_lane if self.queues[self.next_lane] else 1 - self.next_lane
        return self.queues[lane][0] if self.queues[lane] else None

    async def release_unsubmitted(self, operation_id):
        """Only the dispatcher can establish that no provider submission occurred."""
        if not self.records:
            return
        async with self.condition:
            key = "reservation/" + self.name + "/" + operation_id
            saved = self.records.get(key)
            if saved and saved[1]["state"] == "held":
                self.records.compare_and_publish({key: saved[0]}, {key: {**saved[1], "state": "released"}})
                self.active -= 1
                self.tokens -= saved[1]["tokens"]
                self.condition.notify_all()

    @asynccontextmanager
    async def reserve(self, tokens, finishing=False, operation_id=None, timeout=None):
        if tokens < 0 or tokens > self.token_limit:
            raise EndpointError("Context cannot fit configured token reservation")
        ticket = object()
        lane = int(finishing)
        async with self.condition:
            if sum(map(len, self.queues)) >= self.max_queued:
                raise EndpointError("Inference admission queue is full")
            self.queues[lane].append(ticket)
            try:
                ready = self.condition.wait_for(
                    lambda: (
                        self._front() is ticket
                        and self.active < self.limit
                        and self.tokens + tokens <= self.token_limit
                    )
                )
                try:
                    await asyncio.wait_for(ready, timeout)
                except asyncio.TimeoutError as exc:
                    raise EndpointError("Admission deadline expired before submission") from exc
                self.queues[lane].popleft()
                self.next_lane = 1 - lane
                self.active += 1
                self.tokens += tokens
                if self.records and operation_id:
                    key = "reservation/" + self.name + "/" + operation_id
                    saved = self.records.get(key)
                    self.records.compare_and_publish(
                        {key: saved[0] if saved else 0},
                        {key: {"operation_id": operation_id, "tokens": tokens, "state": "held"}},
                    )
                self.condition.notify_all()
            except BaseException:
                if ticket in self.queues[lane]:
                    self.queues[lane].remove(ticket)
                self.condition.notify_all()
                raise
        known_end = True
        try:
            yield
        except (UnknownExecution, asyncio.TimeoutError, asyncio.CancelledError):
            known_end = False
            raise
        finally:
            if known_end:
                async with self.condition:
                    if self.records and operation_id:
                        key = "reservation/" + self.name + "/" + operation_id
                        saved = self.records.get(key)
                        self.records.compare_and_publish(
                            {key: saved[0]}, {key: {**saved[1], "state": "released"}}
                        )
                    self.active -= 1
                    self.tokens -= tokens
                    self.condition.notify_all()


class HTTPInference:
    def __init__(self, endpoint, client=None):
        self.endpoint = endpoint
        self.output_cap = 4 * 1024 * 1024
        headers = {"anthropic-version": "2023-06-01"} if endpoint.protocol == "anthropic" else {}
        if endpoint.api_key_env:
            key = os.environ.get(endpoint.api_key_env)
            if not key:
                raise EndpointError(f"Missing credential environment variable: {endpoint.api_key_env}")
            if endpoint.protocol == "anthropic":
                headers["x-api-key"] = key
            elif endpoint.protocol == "gemini":
                headers["x-goog-api-key"] = key
            else:
                headers["Authorization"] = f"Bearer {key}"
        self.client = client or httpx.AsyncClient(
            timeout=endpoint.timeout_seconds,
            headers=headers,
            follow_redirects=False,
            transport=httpx.AsyncHTTPTransport(retries=0),
        )

    async def generate(self, messages, max_output, response_schema=None):
        endpoint = self.endpoint
        if endpoint.protocol == "gemini":
            path = "/models/" + endpoint.model.removeprefix("models/") + ":generateContent"
            payload = {
                "contents": [
                    {
                        "role": "model" if m["role"] == "assistant" else "user",
                        "parts": [{"text": m["content"]}],
                    }
                    for m in messages
                    if m["role"] != "system"
                ],
                "systemInstruction": {
                    "parts": [{"text": m["content"]} for m in messages if m["role"] == "system"]
                },
                "generationConfig": {"maxOutputTokens": max_output, "responseMimeType": "application/json"},
            }
            if not payload["contents"]:
                payload["contents"] = [
                    {"role": "user", "parts": [{"text": "Follow the application instructions."}]}
                ]
        elif endpoint.protocol == "anthropic":
            path = "/messages"
            payload = {
                "model": endpoint.model,
                "max_tokens": max_output,
                "system": "\n\n".join(m["content"] for m in messages if m["role"] == "system"),
                "messages": [m for m in messages if m["role"] != "system"],
                "stream": False,
            }
            if not payload["messages"]:
                payload["messages"] = [{"role": "user", "content": "Follow the application instructions."}]
        elif endpoint.protocol == "responses":
            path = "/responses"
            payload = {"model": endpoint.model, "input": messages, "max_output_tokens": max_output}
        else:
            path = "/chat/completions"
            payload = {
                "model": endpoint.model,
                "messages": messages,
                "max_tokens": max_output,
                "stream": False,
            }
        # Compatibility endpoints may not implement response_format. The typed grammar
        # is in the instruction; host validation is always authoritative.
        try:
            async with self.client.stream(
                "POST", endpoint.base_url.rstrip("/") + path, json=payload
            ) as response:
                if response.status_code >= 400:
                    raise EndpointError(f"Endpoint HTTP {response.status_code}")
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self.output_cap:
                        raise UnknownExecution("Endpoint response exceeded transport output cap")
                    chunks.append(chunk)
            body = json.loads(b"".join(chunks))
        except (httpx.TransportError, asyncio.CancelledError) as exc:
            raise UnknownExecution("Endpoint disconnected; execution requires reconciliation") from exc
        if endpoint.protocol == "gemini":
            candidate = body.get("candidates", [{}])[0]
            if candidate.get("finishReason") != "STOP":
                raise EndpointError(
                    "Gemini did not complete: "
                    + str(candidate.get("finishReason", body.get("promptFeedback")))
                )
            text = "".join(
                p.get("text", "")
                for p in candidate.get("content", {}).get("parts", [])
                if not p.get("thought")
            )
            metadata = body.get("usageMetadata")
            body["usage"] = (
                {"total_tokens": metadata["totalTokenCount"]}
                if metadata and "totalTokenCount" in metadata
                else None
            )
        elif endpoint.protocol == "anthropic":
            if body.get("stop_reason") not in {"end_turn", "stop_sequence"}:
                raise EndpointError(f"Anthropic did not complete: {body.get('stop_reason')}")
            blocks = body.get("content", [])
            if any(p.get("type") not in {"text", "thinking", "redacted_thinking"} for p in blocks):
                raise EndpointError("Unexpected Anthropic tool/content block: use the typed action grammar")
            text = "".join(p.get("text", "") for p in blocks if p.get("type") == "text")
            usage = body.get("usage")
            if usage is not None:
                # Anthropic input_tokens excludes cache creation/read tokens.
                usage["total_tokens"] = sum(
                    usage.get(name, 0)
                    for name in (
                        "input_tokens",
                        "output_tokens",
                        "cache_creation_input_tokens",
                        "cache_read_input_tokens",
                    )
                )
        elif endpoint.protocol == "responses":
            if body.get("status") != "completed":
                raise EndpointError(f"Non-complete response: {body.get('status')}")
            output = body.get("output", [])
            if any(item.get("type") in {"function_call", "custom_tool_call"} for item in output):
                raise EndpointError("Unexpected client tool calls: use the agent's typed action grammar")
            text = "".join(
                part.get("text", "")
                for item in output
                if item.get("type") == "message"
                for part in item.get("content", [])
                if part.get("type") == "output_text"
            )
        else:
            choice = body["choices"][0]
            if choice.get("finish_reason") not in {None, "stop"}:
                raise EndpointError(f"Non-complete generation: {choice.get('finish_reason')}")
            if choice["message"].get("tool_calls"):
                raise EndpointError("Client tool calls are not native completed jobs")
            text = choice["message"].get("content")
        if not isinstance(text, str) or not text.strip():
            raise EndpointError("Endpoint returned no text")
        return {
            "text": text,
            "usage": body.get("usage"),
            "provider_id": body.get("id"),
            "model": body.get("model", endpoint.model),
            "events": [],
        }

    async def close(self):
        await self.client.aclose()
