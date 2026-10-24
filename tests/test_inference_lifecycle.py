"""Offline lifecycle faults, physical holds and independent caller/native retry policy."""
import asyncio
import json

import httpx
import pytest
from test_model_retries import install, setup

from polyinference.contracts import Feature
from polyinference.primitives import operation_fingerprint
from polyinference.runtime.inference_stream import SSEDecoder
from polyinference.runtime.kernel import UncertainEffect


def policy(request, additional=0, replace=False):
    request = request.model_copy(update={"required_features": [Feature(feature_id="runtime/inference-policy", version="1")],
        "extensions": {"runtime/inference-policy": {"additional_retries": additional, "replace_undelivered": replace}}})
    return request.model_copy(update={"intent_digest": operation_fingerprint(request)})


def events(text="answer"):
    return [
        {"type": "message_start", "message": {"id": "msg-fixture", "model": "fixture", "usage": {"input_tokens": 4}}},
        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}},
        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 7}},
        {"type": "message_stop"},
    ]


def encoded(items):
    return b"".join(b"data: " + json.dumps(e, ensure_ascii=False).encode() + b"\n\n" for e in items)


class Chunks(httpx.AsyncByteStream):
    def __init__(self, chunks, delay=0):
        self.chunks, self.delay = chunks, delay
    async def __aiter__(self):
        for chunk in self.chunks:
            if self.delay:
                await asyncio.sleep(self.delay)
            yield chunk


async def streamed(rt, request, chunks, delay=0):
    async def handler(wire):
        assert json.loads(wire.content)["stream"] is True
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Chunks(chunks, delay))
    await install(rt, request, handler)


def test_sse_split_unicode_and_multiline_data():
    decoder = SSEDecoder()
    text = chr(0x96ea)
    wire = ('data: {"text":"' + text + '"}\r\n\r\n').encode()
    result = []
    for byte in wire:
        result.extend(decoder.feed(bytes([byte])))
    assert json.loads(result[0])["text"] == text
    assert decoder.feed(b"data: one\ndata: two\n\n") == ["one\ntwo"]


@pytest.mark.parametrize("additional,expected", [(0, 3), (1, 4), (3, 6)])
async def test_os_retries_then_caller_allowance(tmp_path, additional, expected):
    rt, request = await setup(tmp_path, model_call_retries=2)
    request = policy(request, additional)
    calls = []
    async def handler(wire):
        calls.append(1)
        return httpx.Response(503, json={"error": {"type": "overloaded_error"}})
    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "failed" and len(calls) == expected
        assert rt.records.get("model-retry-outcome/summary")[1]["retry_counts"] == {"native": 2, "caller": additional}
        assert await rt.execute(request) == result and len(calls) == expected
    finally:
        await rt.close()


async def test_streamed_completion_and_progress(tmp_path):
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {}})
    text = '{"answer":"' + chr(0x96ea) + '"}'
    await streamed(rt, request, [bytes([b]) for b in encoded(events(text))])
    try:
        result = await rt.execute(request)
        output = json.loads(rt.artifacts.read(result.output_refs[0]))
        assert result.state == "succeeded" and output["text"] == text
        assert output["usage"]["total_tokens"] == 11
        progress = rt.records.get("inference-progress/summary")[1]
        assert progress["state"] == "terminal" and progress["last_output_seconds"] is not None
    finally:
        await rt.close()


@pytest.mark.parametrize("capacity,consent,replaces", [(1, True, False), (2, False, False), (2, True, True)])
async def test_unknown_generation_holds_capacity_and_requires_consent(tmp_path, capacity, consent, replaces):
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {}, "max_inflight": capacity})
    request = policy(request, replace=consent)
    calls = []
    async def handler(wire):
        calls.append(1)
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
            stream=Chunks([encoded(events() if len(calls) > 1 else events()[:-1])]))
    await install(rt, request, handler)
    try:
        if replaces:
            result = await rt.execute(request)
            assert result.state == "succeeded" and len(calls) == 2
            assert await rt.execute(request) == result and len(calls) == 2
            effect = rt.records.get("effect/summary")[1]
            assert effect["state"] == "uncertain" and not effect.get("result")
            assert effect["delivery_result"]["execution_termination"] == "unknown"
            assert rt.admission["local"].active == 1
            assert not rt.records.get("allocation/summary")[1]["settled"]
            rt.admission["local"].restore()
            assert rt.admission["local"].active == 1
            from polyinference.runtime.kernel import KernelRuntime
            await rt.close()
            rt = await KernelRuntime(rt.config).open()
            assert rt.admission["local"].active == 1
            assert await rt.execute(request) == result and len(calls) == 2
        elif consent:
            result = await rt.execute(request)
            assert result.state == "uncertain" and len(calls) == 1
            assert rt.admission["local"].active == 1 and not rt.uncertain()
            assert rt.uncertain(include_isolated=True) == ["summary"]
            assert rt.records.get("model-retry-outcome/summary")[1]["reason"] == "pending generation occupies endpoint capacity"
        else:
            with pytest.raises(UncertainEffect):
                await rt.execute(request)
            assert len(calls) == 1 and rt.uncertain() == ["summary"]
    finally:
        await rt.close()


async def test_second_unknown_blocks_without_another_overlap(tmp_path):
    rt, request = await setup(tmp_path, model_call_retries=2, endpoint_options={"lifecycle": {}, "max_inflight": 3})
    request = policy(request, additional=2, replace=True)
    await streamed(rt, request, [encoded(events()[:-1])])
    try:
        with pytest.raises(UncertainEffect):
            await rt.execute(request)
        assert len(rt.records.scan("effect/")) == 2
        assert rt.admission["local"].active == 2 and len(rt.uncertain()) == 1
    finally:
        await rt.close()


async def test_pings_do_not_extend_first_output_watchdog(tmp_path):
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {"first_output_seconds": .025}})
    await streamed(rt, request, [b'data: {"type":"ping"}\n\n'] * 50, delay=.01)
    try:
        with pytest.raises(UncertainEffect):
            await rt.execute(request)
        failure = rt.records.get("effect/summary")[1]["failure"]
        assert failure["stage"] == "first_output" and failure["cause"] == "TimeoutError"
        assert rt.admission["local"].active == 1
    finally:
        await rt.close()


async def test_total_deadline_does_not_reset(tmp_path):
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {"total_seconds": .025}}, model_call_retries=2)
    async def handler(wire):
        await asyncio.sleep(.03)
        return httpx.Response(503, json={})
    await install(rt, request, handler)
    try:
        with pytest.raises(UncertainEffect):
            await rt.execute(policy(request, additional=3, replace=True))
        assert len(rt.records.scan("effect/")) == 1
    finally:
        await rt.close()


def test_legacy_endpoint_and_public_error():
    from polyinference.config import Endpoint
    from polyinference.ports import WriteScopeError
    from polyinference.runtime.workspace_state import WriteScopeError as LegacyError
    assert "lifecycle" not in Endpoint(model="old").model_dump()
    assert WriteScopeError is LegacyError


@pytest.mark.parametrize("protocol", ["chat", "responses"])
async def test_other_streaming_protocols_require_terminal_evidence(tmp_path, protocol):
    from test_model_retries import body
    rt, request = await setup(tmp_path, protocol=protocol, endpoint_options={"lifecycle": {}})
    if protocol == "chat":
        wire = encoded([{"id": "chat-1", "choices": [{"index": 0, "delta": {"content": "ready"}, "finish_reason": None}]},
                        {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}]) + b"data: [DONE]\n\n"
    else:
        wire = encoded([{"type": "response.created", "response": {"id": "response-1"}},
                        {"type": "response.output_text.delta", "delta": "ready"},
                        {"type": "response.completed", "response": body("responses", "ready")}])
    await streamed(rt, request, [wire])
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded"
        assert json.loads(rt.artifacts.read(result.output_refs[0]))["text"] == "ready"
    finally:
        await rt.close()


async def test_idle_watchdog_and_hidden_reasoning_not_persisted(tmp_path):
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {"idle_seconds": .025}})
    thinking = events()
    thinking[1]["content_block"] = {"type": "thinking", "thinking": "private reasoning"}
    thinking[2]["delta"] = {"type": "thinking_delta", "thinking": "private reasoning"}
    await streamed(rt, request, [encoded(thinking[:3])] + [b'data: {"type":"ping"}\n\n'] * 40, delay=.01)
    try:
        with pytest.raises(UncertainEffect):
            await rt.execute(request)
        assert rt.records.get("effect/summary")[1]["failure"]["stage"] == "output_idle"
        assert "private reasoning" not in json.dumps(rt.records.scan("inference-progress/"))
    finally:
        await rt.close()


async def test_output_adaptation_does_not_reset_retry_allowance(tmp_path):
    from test_model_retries import body
    rt, request = await setup(tmp_path, model_call_retries=1)
    request = policy(request, additional=1)
    calls = []
    async def handler(wire):
        calls.append(1)
        if len(calls) == 1 or len(calls) > 2:
            return httpx.Response(503, json={})
        partial = body("anthropic", "partial")
        partial["stop_reason"] = "max_tokens"
        return httpx.Response(200, json=partial)
    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "failed" and len(calls) == 4
        # initial, native retry (cutoff), adaptation, caller retry. No new native allowance.
        assert rt.model_retries.counts(request) == {"native": 1, "caller": 1}
    finally:
        await rt.close()


async def test_endpoint_probe_is_bounded_and_has_no_git_or_tools(tmp_path, monkeypatch):
    from polyinference.agent.endpoint_probe import probe_endpoint
    from polyinference.config import Endpoint, RuntimeConfig
    from polyinference.runtime.inference import HTTPInference
    from polyinference.runtime.storage import Records
    original = HTTPInference.__init__
    calls = []
    async def handler(wire):
        calls.append(json.loads(wire.content))
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Chunks([encoded(events("ready"))]))
    def client(self, endpoint, client=None):
        original(self, endpoint, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(HTTPInference, "__init__", client)
    endpoint = Endpoint(model="fixture", protocol="anthropic", lifecycle={})
    config = RuntimeConfig(repository=str(tmp_path / "not-a-repo"), local=endpoint, cloud=endpoint)
    result = await probe_endpoint(config, tmp_path / "probe")
    assert result["status"] == "succeeded" and len(calls) == 1 and calls[0]["max_tokens"] == 64
    assert not config.repo_path.exists()
    records = Records(tmp_path / "probe" / "records.sqlite")
    try:
        assert not records.scan("workspace/") and not records.scan("task/")
        assert records.get("budget/process/probe")[1]["reserved_or_used"] == 11
    finally:
        records.db.close()


async def test_late_reconciliation_never_delivers_discarded_answer(tmp_path):
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {}, "max_inflight": 2})
    request = policy(request, replace=True)
    calls = []
    async def handler(wire):
        calls.append(1)
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
            stream=Chunks([encoded(events("chosen") if len(calls) > 1 else events("discarded")[:-1])]))
    await install(rt, request, handler)
    try:
        chosen = await rt.execute(request)
        await rt.settle_recovered_model(request, {"text": "discarded", "model": "fixture", "usage": {"total_tokens": 11}})
        assert not rt.uncertain(include_isolated=True) and rt.admission["local"].active == 0
        assert await rt.execute(request) == chosen
        assert len(calls) == 2
        assert json.loads(rt.artifacts.read(chosen.output_refs[0]))["text"] == "chosen"
    finally:
        await rt.close()


@pytest.mark.parametrize("terminal", [True, False])
async def test_loopback_http_sse_fixture(tmp_path, terminal):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    payload = encoded(events() if terminal else events()[:-1])
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            wire = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            assert wire["stream"] is True
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            for offset in range(0, len(payload), 7):
                self.wfile.write(payload[offset:offset + 7])
                self.wfile.flush()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {},
        "base_url": "http://127.0.0.1:" + str(server.server_port)})
    try:
        if terminal:
            assert (await rt.execute(request)).state == "succeeded"
        else:
            with pytest.raises(UncertainEffect):
                await rt.execute(request)
            assert rt.records.get("effect/summary")[1]["failure"]["cause"] == "missing_terminal"
    finally:
        await rt.close()
        server.shutdown()
        server.server_close()
        thread.join()


async def test_progress_observer_failure_cannot_fake_termination():
    from polyinference.config import Endpoint
    from polyinference.runtime.inference import HTTPInference, UnknownExecution
    async def handler(wire):
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
                              stream=Chunks([encoded(events()[:-1])]))
    async def observer(facts):
        raise RuntimeError("diagnostic storage unavailable")
    client = HTTPInference(Endpoint(model="fixture", protocol="anthropic", lifecycle={}),
                           httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    try:
        with pytest.raises(UnknownExecution):
            await client.generate([{"role": "user", "content": "task"}], 64, progress=observer)
    finally:
        await client.close()


async def test_tool_bearing_wire_cannot_claim_generation_only(tmp_path):
    rt, request = await setup(tmp_path, endpoint_options={"lifecycle": {}, "max_inflight": 2})
    request = policy(request, replace=True)
    await streamed(rt, request, [encoded(events()[:-1])])
    prepare = rt.clients["local"].prepare
    def tools(*args, **kwargs):
        wire = prepare(*args, **kwargs)
        wire["payload"]["tools"] = [{"name": "external-effect"}]
        return wire
    rt.clients["local"].prepare = tools
    try:
        with pytest.raises(UncertainEffect):
            await rt.execute(request)
        assert rt.uncertain() == ["summary"] and len(rt.records.scan("effect/")) == 1
    finally:
        await rt.close()
