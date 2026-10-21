"""Endpoint clients. Raw generation and native agent jobs are distinct protocols."""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx


class EndpointError(RuntimeError):
    pass


class ProviderError(EndpointError):
    """A known rejection, with bounded diagnostics kept separately from log text."""

    def __init__(self, message, *, category, status=None, provider_code=None,
                 provider_message=None, request_id=None, retry_after_ms=None, submitted=True):
        super().__init__(message)
        self.diagnostics = {
            "category": category, "http_status": status, "provider_code": provider_code,
            "provider_message": provider_message, "request_id": request_id,
            "retry_after_ms": retry_after_ms, "submitted": submitted,
            "fault_scope": ({"invalid_request": "input", "authentication": "account", "permission": "account",
                             "rate_limit": "account", "service_unavailable": "endpoint", "connection": "endpoint",
                             "admission": "resource"}
                            .get(category, "operation")),
        }
        self.retryable = category in {"rate_limit", "service_unavailable", "connection", "admission"}


class ModelResponseError(EndpointError):
    """A received but unusable response; retain facts without hidden reasoning."""

    retryable = True

    def __init__(self, message, response, diagnostics):
        super().__init__(message)
        self.response = {**response, "error": message}
        self.diagnostics = diagnostics


class UnknownExecution(EndpointError):
    """The transport ended without proof the provider stopped."""


class IncompleteGeneration(EndpointError):
    """A confirmed output-limit stop; partial text is an observation, never an action."""

    retryable = True

    def __init__(self, response, stop_reason, max_output):
        super().__init__(f"Model output reached its {max_output}-token limit ({stop_reason}); "
                         "retry with a smaller response")
        self.response = {**response, "incomplete": True, "stop_reason": stop_reason,
                         "max_output_tokens": max_output, "error": str(self)}
        self.diagnostics = {"category": "output_limit", "stop_reason": stop_reason,
                            "max_output_tokens": max_output, "provider_id": response.get("provider_id")}


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
            if body["state"] == "waiting":
                self.records.compare_and_publish({key: revision}, {key: {**body, "state": "interrupted"}})
                continue
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

    def _record(self, operation_id, state, **fields):
        if not self.records or not operation_id:
            return
        key = "reservation/" + self.name + "/" + operation_id
        saved = self.records.get(key)
        self.records.compare_and_publish(
            {key: saved[0] if saved else 0},
            {key: {**(saved[1] if saved else {}), "operation_id": operation_id, "state": state, **fields}},
        )

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
    async def reserve(self, tokens, finishing=False, operation_id=None, timeout=None, process_id=None):
        if tokens < 0 or tokens > self.token_limit:
            raise EndpointError("Context cannot fit configured token reservation")
        ticket = object()
        lane = int(finishing)
        async with self.condition:
            if sum(map(len, self.queues)) >= self.max_queued:
                raise ProviderError("Inference admission queue is full", category="admission", submitted=False)
            self.queues[lane].append(ticket)
            try:
                self._record(
                    operation_id, "waiting", tokens=tokens, process_id=process_id,
                    lane="finishing" if finishing else "ordinary",
                    queued_at=datetime.now(timezone.utc).isoformat(),
                )
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
                self._record(operation_id, "held", admitted_at=datetime.now(timezone.utc).isoformat())
                self.condition.notify_all()
            except BaseException:
                if ticket in self.queues[lane]:
                    self.queues[lane].remove(ticket)
                    self._record(operation_id, "withdrawn", released_at=datetime.now(timezone.utc).isoformat())
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
                        self._record(operation_id, "released", released_at=datetime.now(timezone.utc).isoformat())
                    self.active -= 1
                    self.tokens -= tokens
                    self.condition.notify_all()


class HTTPInference:
    def __init__(self, endpoint, client=None):
        self.endpoint = endpoint
        self.secrets = []
        self.output_cap = 4 * 1024 * 1024
        self.require_completion_metadata = True
        headers = {"anthropic-version": "2023-06-01"} if endpoint.protocol == "anthropic" else {}
        if endpoint.api_key_env:
            key = os.environ.get(endpoint.api_key_env)
            if not key:
                raise EndpointError(f"Missing credential environment variable: {endpoint.api_key_env}")
            self.secrets.append(key)
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

    def validate_messages(self, messages):
        if self.endpoint.protocol == "anthropic":
            turns = [m for m in messages if m["role"] != "system"]
            if turns and turns[-1]["role"] != "user":
                raise ProviderError(
                    "Anthropic model queries require a final user turn; assistant prefill is not supported",
                    category="invalid_request", provider_code="assistant_prefill", submitted=False,
                )

    def sanitize(self, value):
        if not isinstance(value, str):
            return None
        for secret in self.secrets:
            value = value.replace(secret, "[redacted]")
        value = re.sub(r"(?i)(bearer\s+|sk-)[A-Za-z0-9._-]+", "[redacted]", value)
        value = re.sub(r"(?i)((?:api[_-]?key|authorization|token|password)\s*[=:]\s*)\S+", r"\1[redacted]", value)
        return " ".join(value.split())[:1024]

    async def rejected(self, response):
        chunks, size = [], 0
        async for chunk in response.aiter_bytes():
            size += len(chunk)
            if size > 16384:
                break
            chunks.append(chunk)
        try:
            body = json.loads(b"".join(chunks))
            detail = body.get("error", {}) if isinstance(body, dict) else {}
            if not isinstance(detail, dict):
                detail = {}
        except (ValueError, UnicodeError):
            detail = {}
        status = response.status_code
        detail_message = str(detail.get("message", "")).lower()
        category = ({400: "invalid_request", 401: "authentication", 403: "permission", 429: "rate_limit"}
                    .get(status, "service_unavailable" if status >= 500 else "request_rejected"))
        if status in {400, 413, 422} and any(t in detail_message for t in ("context length", "context window", "too many tokens", "prompt is too long")):
            category = "input_overflow"
        retry_after = None
        try:
            retry_after = max(0, min(int(float(response.headers.get("retry-after", "")) * 1000), 3600000))
        except (ValueError, OverflowError):
            try:
                retry_after = max(0, min(int((parsedate_to_datetime(response.headers["retry-after"])
                                             - datetime.now(timezone.utc)).total_seconds() * 1000), 3600000))
            except (KeyError, ValueError, TypeError, OverflowError):
                pass
        return ProviderError(
            f"Endpoint HTTP {status}", category=category, status=status,
            provider_code=self.sanitize(detail.get("type") or detail.get("code")),
            provider_message=self.sanitize(detail.get("message")),
            request_id=self.sanitize(response.headers.get("request-id") or response.headers.get("x-request-id")),
            retry_after_ms=retry_after,
        )

    def prepare(self, messages, max_output, response_schema=None):
        self.validate_messages(messages)
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
        return {"path": path, "payload": payload}

    async def generate(self, messages, max_output, response_schema=None, *, prepared=None):
        endpoint = self.endpoint
        wire = prepared or self.prepare(messages, max_output, response_schema)
        path, payload = wire["path"], wire["payload"]
        # Compatibility endpoints may not implement response_format. The typed grammar
        # is in the instruction; host validation is always authoritative.
        try:
            async with self.client.stream(
                "POST", endpoint.base_url.rstrip("/") + path, json=payload
            ) as response:
                if response.status_code >= 400:
                    raise await self.rejected(response)
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self.output_cap:
                        raise UnknownExecution("Endpoint response exceeded transport output cap")
                    chunks.append(chunk)
            try:
                body = json.loads(b"".join(chunks))
            except (ValueError, UnicodeError) as exc:
                raise self.response_error("Endpoint returned invalid JSON", {}, response, "invalid_json") from exc
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
            raise ProviderError("Endpoint connection failed before submission", category="connection",
                                submitted=False) from exc
        except (httpx.TransportError, asyncio.CancelledError) as exc:
            raise UnknownExecution("Endpoint disconnected; execution requires reconciliation") from exc
        if not isinstance(body, dict):
            raise self.response_error("Endpoint returned a non-object response", {}, response, "invalid_shape")
        try:
            return self.normalize(body, max_output, response)
        except (KeyError, TypeError, IndexError, AttributeError) as exc:
            raise self.response_error("Endpoint returned a malformed response", body, response, "invalid_shape") from exc

    def response_error(self, message, body, http_response, reason):
        endpoint = self.endpoint
        usage = body.get("usage")
        usage = dict(usage) if isinstance(usage, dict) else None
        if endpoint.protocol == "anthropic" and usage is not None:
            names = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
            counts = [usage.get(name, 0) for name in names]
            if all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in counts):
                usage["total_tokens"] = sum(counts)
        blocks = body.get("content", body.get("output", []))
        stop_reason = body.get("stop_reason", body.get("status"))
        if endpoint.protocol == "gemini":
            candidates = body.get("candidates")
            candidate = candidates[0] if isinstance(candidates, list) and candidates else {}
            candidate = candidate if isinstance(candidate, dict) else {}
            content = candidate.get("content") or {}
            blocks = content.get("parts", []) if isinstance(content, dict) else []
            stop_reason = candidate.get("finishReason")
            metadata = body.get("usageMetadata") or {}
            if isinstance(metadata, dict) and isinstance(metadata.get("totalTokenCount"), int):
                usage = {"total_tokens": metadata["totalTokenCount"]}
        elif endpoint.protocol == "chat":
            choices = body.get("choices")
            choice = choices[0] if isinstance(choices, list) and choices else {}
            stop_reason = choice.get("finish_reason") if isinstance(choice, dict) else None
        blocks = blocks if isinstance(blocks, list) else []
        block_types = [self.sanitize(p.get("type")) for p in blocks[:32] if isinstance(p, dict)]
        request_id = self.sanitize(http_response.headers.get("request-id")
                                   or http_response.headers.get("x-request-id"))
        response = {"text": "", "usage": usage, "provider_id": self.sanitize(body.get("id")),
                    "model": self.sanitize(body.get("model")) or endpoint.model, "events": []}
        diagnostics = {"category": "model_output", "fault_scope": "response", "reason": reason,
                       "http_status": http_response.status_code, "request_id": request_id,
                       "provider_id": response["provider_id"], "stop_reason": self.sanitize(stop_reason),
                       "content_types": block_types, "submitted": True}
        return ModelResponseError(message, response, diagnostics)

    def normalize(self, body, max_output, http_response):
        endpoint = self.endpoint
        incomplete_reason = None
        if endpoint.protocol == "gemini":
            candidate = body.get("candidates", [{}])[0]
            if candidate.get("finishReason") == "MAX_TOKENS":
                incomplete_reason = "MAX_TOKENS"
            elif candidate.get("finishReason") != "STOP":
                raise self.response_error(
                    "Gemini did not complete: "
                    + self.sanitize(str(candidate.get("finishReason", body.get("promptFeedback")))),
                    body, http_response, "stop_reason",
                )
            text = "".join(
                p.get("text", "")
                for p in candidate.get("content", {}).get("parts", [])
                if not p.get("thought")
            )
            metadata = body.get("usageMetadata")
            body["usage"] = (
                {"total_tokens": metadata["totalTokenCount"],
                 "output_tokens": metadata.get("candidatesTokenCount", 0) + metadata.get("thoughtsTokenCount", 0)}
                if metadata and "totalTokenCount" in metadata
                else None
            )
        elif endpoint.protocol == "anthropic":
            if body.get("stop_reason") == "max_tokens":
                incomplete_reason = "max_tokens"
            elif body.get("stop_reason") == "model_context_window_exceeded":
                raise ProviderError("Provider context window exceeded", category="input_overflow",
                                    provider_code="model_context_window_exceeded")
            elif body.get("stop_reason") not in {"end_turn", "stop_sequence"}:
                raise self.response_error("Anthropic did not complete: " + str(self.sanitize(body.get("stop_reason"))),
                                          body, http_response, "stop_reason")
            blocks = body.get("content", [])
            if any(p.get("type") not in {"text", "thinking", "redacted_thinking"} for p in blocks):
                raise self.response_error("Unexpected Anthropic tool/content block: use the typed action grammar",
                                          body, http_response, "unexpected_content")
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
            if (body.get("status") == "incomplete"
                    and (body.get("incomplete_details") or {}).get("reason") == "max_output_tokens"):
                incomplete_reason = "max_output_tokens"
            elif body.get("status") != "completed":
                raise self.response_error("Non-complete response: " + str(self.sanitize(body.get("status"))),
                                          body, http_response, "stop_reason")
            output = body.get("output", [])
            if any(item.get("type") in {"function_call", "custom_tool_call"} for item in output):
                raise self.response_error("Unexpected client tool calls: use the agent's typed action grammar",
                                          body, http_response, "unexpected_content")
            text = "".join(
                part.get("text", "")
                for item in output
                if item.get("type") == "message"
                for part in item.get("content", [])
                if part.get("type") == "output_text"
            )
        else:
            choice = body["choices"][0]
            if choice.get("finish_reason") == "length":
                incomplete_reason = "length"
            elif (choice.get("finish_reason") != "stop"
                  and (self.require_completion_metadata or choice.get("finish_reason") is not None)):
                raise self.response_error("Non-complete generation: " + str(self.sanitize(choice.get("finish_reason"))),
                                          body, http_response, "stop_reason")
            if choice["message"].get("tool_calls"):
                raise self.response_error("Client tool calls are not native completed jobs",
                                          body, http_response, "unexpected_content")
            text = choice["message"].get("content")
        response = {
            "text": text if isinstance(text, str) else "",
            "usage": body.get("usage"),
            "provider_id": body.get("id"),
            "model": body.get("model", endpoint.model),
            "events": [],
        }
        if incomplete_reason:
            raise IncompleteGeneration(response, incomplete_reason, max_output)
        usage = response.get("usage") or {}
        emitted = usage.get("output_tokens", usage.get("completion_tokens"))
        if isinstance(emitted, int) and emitted > max_output:
            raise IncompleteGeneration(response, "reported_output_limit_exceeded", max_output)
        if not isinstance(text, str) or not text.strip():
            raise self.response_error("Endpoint returned no text", body, http_response, "empty_text")
        return response

    async def close(self):
        await self.client.aclose()
