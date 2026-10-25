from __future__ import annotations

import asyncio
import json
import sys

import httpx
import pytest

from polyinference.config import Endpoint
from polyinference.runtime.codex import CodexAppServer, CodexProxy, NativeJobStopped, strict_output_schema
from polyinference.runtime.inference import Admission, EndpointError, HTTPInference, UnknownExecution


@pytest.mark.parametrize("protocol", ["chat", "responses", "gemini"])
async def test_endpoint_request_and_usage(protocol, monkeypatch):
    monkeypatch.setenv("FIXTURE_KEY", "never-store-this")
    captured = []

    async def handler(request):
        captured.append(request)
        body = {"id": "provider-id", "model": "fixture", "usage": {"total_tokens": 17}}
        if protocol == "gemini":
            body = {
                "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '{"ok":true}'}]}}],
                "usageMetadata": {"totalTokenCount": 17},
            }
        elif protocol == "responses":
            body["output"] = [
                {"type": "message", "content": [{"type": "output_text", "text": '{"ok":true}'}]}
            ]
            body["status"] = "completed"
        else:
            body["choices"] = [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}]
        return httpx.Response(200, json=body)

    endpoint = Endpoint(protocol=protocol, model="fixture", api_key_env="FIXTURE_KEY")
    client = HTTPInference(endpoint)
    await client.client.aclose()
    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        headers={"x-goog-api-key" if protocol == "gemini" else "Authorization": "fixture"},
    )
    try:
        result = await client.generate(
            [{"role": "system", "content": "instructions"}, {"role": "user", "content": "request"}], 30
        )
        assert json.loads(result["text"]) == {"ok": True}
        assert result["usage"]["total_tokens"] == 17
        request = captured[0]
        body = json.loads(request.content)
        assert "tools" not in body
        assert "fixture" in request.url.path if protocol == "gemini" else body["model"] == "fixture"
        assert request.method == "POST"
    finally:
        await client.close()


@pytest.mark.parametrize("failure", ["length", "client_tools", "http", "disconnect"])
async def test_endpoint_never_promotes_partial_or_disconnected_output(failure):
    async def handler(request):
        if failure == "disconnect":
            raise httpx.ReadError("fixture disconnected")
        if failure == "http":
            return httpx.Response(429, json={"error": "quota"})
        message = {"content": '{"kind":"candidate"}'}
        if failure == "client_tools":
            message["tool_calls"] = [{"id": "unexecuted"}]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "length" if failure == "length" else "stop", "message": message}
                ]
            },
        )

    client = HTTPInference(
        Endpoint(model="fixture"), httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    try:
        with pytest.raises(UnknownExecution if failure == "disconnect" else EndpointError):
            await client.generate([{"role": "user", "content": "x"}], 2)
    finally:
        await client.close()


async def test_two_requests_overlap_and_finishing_lane_does_not_exclude_ordinary():
    admission = Admission(2, 200)
    entered = []
    release = asyncio.Event()

    async def call(name, finishing):
        async with admission.reserve(100, finishing):
            entered.append(name)
            await release.wait()

    first = asyncio.create_task(call("owner", True))
    second = asyncio.create_task(call("other", False))
    await asyncio.wait_for(_until(lambda: len(entered) == 2), 2)
    assert admission.active == 2 and admission.tokens == 200
    release.set()
    await asyncio.gather(first, second)
    assert admission.active == admission.tokens == 0


async def _until(predicate):
    while not predicate():
        await asyncio.sleep(0.001)


@pytest.mark.parametrize("streaming_events", [False, True])
async def test_codex_real_stdio_handshake_terminal_events_before_start_reply(tmp_path, streaming_events):
    script = tmp_path / "server.py"
    script.write_text("""import json,sys
def send(m):
 print(json.dumps(m),flush=True)
for line in sys.stdin:
 m=json.loads(line); method=m.get("method")
 if method=="initialize":
  assert "item/agentMessage/delta" in m["params"]["capabilities"]["optOutNotificationMethods"]
  send({"id":m["id"],"result":{}})
 elif method=="thread/start":
  assert m["params"]["permissions"]=="polyinference_readonly"
  assert m["params"]["approvalPolicy"]=="never"
  send({"id":m["id"],"result":{"thread":{"id":"thread-fixture"}}})
 elif method=="turn/start":
  assert "permissions" not in m["params"]
  if sys.argv[1]=="stream":
   methods=["item/agentMessage/delta","item/reasoning/textDelta","item/reasoning/summaryTextDelta"]
   for i in range(2500):
    send({"method":methods[i%len(methods)],"params":{"threadId":"thread-fixture","turnId":"turn-fixture","delta":"text"}})
  send({"method":"thread/tokenUsage/updated","params":{"threadId":"thread-fixture","turnId":"turn-fixture","tokenUsage":{"total":{"totalTokens":17}}}})
  send({"method":"item/completed","params":{"item":{"type":"agentMessage","text":"{\\"goal\\":\\"done\\",\\"complete\\":true}"}}})
  send({"method":"turn/completed","params":{"turn":{"id":"turn-fixture","status":"completed","items":[]}}})
  send({"id":m["id"],"result":{"turn":{"id":"turn-fixture"}}})
""")
    adapter = CodexAppServer(
        Endpoint(
            protocol="codex_app_server",
            model="fixture",
            command=[sys.executable, str(script), "stream" if streaming_events else "plain"],
            timeout_seconds=3,
        )
    )
    result = await adapter.generate_job(
        [{"role": "user", "content": "inspect"}], tmp_path, {"type": "object"}
    )
    assert json.loads(result["text"])["complete"]
    assert result["session_id"] == "thread-fixture"
    assert result["usage"]["total_tokens"] == 17
    assert any(e["method"] == "turn/completed" for e in result["events"])
    assert len(result["events"]) < 2000
    assert all(
        not e["method"].endswith(("/delta", "textDelta", "summaryTextDelta"))
        for e in result["events"]
    )


async def test_proxy_requires_pinned_snapshot(tmp_path):
    adapter = CodexProxy(Endpoint(protocol="codex_proxy", model="fixture"))
    try:
        with pytest.raises(EndpointError, match="snapshot"):
            await adapter.generate_job([], tmp_path, {})
    finally:
        await adapter.close()


def test_codex_strict_schema_preserves_application_types_and_wraps_phase_union():
    from pydantic import TypeAdapter

    from polyinference.domain import Assessment, Candidate, NeedsReview, SeniorProposal

    senior, wrapped = strict_output_schema(SeniorProposal.model_json_schema())
    assert not wrapped
    worker, wrapped = strict_output_schema(TypeAdapter(Candidate | Assessment | NeedsReview).json_schema())
    assert wrapped and worker["required"] == ["reply"]
    assert "anyOf" in worker["properties"]["reply"]
    assert set(worker["$defs"]) == {"Candidate", "Assessment", "NeedsReview"}

    def validate(value):
        if isinstance(value, list):
            for item in value:
                validate(item)
        elif isinstance(value, dict):
            assert "default" not in value and "discriminator" not in value and "oneOf" not in value
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) == set(value["properties"])
            for item in value.values():
                validate(item)

    validate(senior)
    validate(worker)


@pytest.mark.parametrize("failure", ["dispatch", "terminal"])
async def test_codex_confirms_dispatch_rejection_and_terminal_failure(tmp_path, failure):
    script = tmp_path / "failure.py"
    script.write_text(
        """import json,sys
def send(value): print(json.dumps(value),flush=True)
for line in sys.stdin:
 m=json.loads(line);method=m.get("method")
 if method=="initialize":send({"id":m["id"],"result":{}})
 elif method=="thread/start":
  if sys.argv[1]=="dispatch":
   send({"id":m["id"],"error":{"code":-32600,"message":"profile rejected"}})
  else:send({"id":m["id"],"result":{"thread":{"id":"fixture-thread"}}})
 elif method=="turn/start":
  send({"id":m["id"],"result":{"turn":{"id":"fixture-turn"}}})
  send({"method":"turn/completed","params":{"turn":{"id":"fixture-turn","status":"failed","error":{"message":"invalid output schema"}}}})
"""
    )
    client = CodexAppServer(
        Endpoint(
            protocol="codex_app_server",
            model="fixture",
            command=[sys.executable, str(script), failure],
            timeout_seconds=3,
        )
    )
    with pytest.raises(
        NativeJobStopped, match="profile rejected" if failure == "dispatch" else "invalid output schema"
    ):
        await client.generate_job([], tmp_path, {"type": "object"})
