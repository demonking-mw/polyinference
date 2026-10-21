"""Output truncation is a bounded recoverable observation, never an executable reply."""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices, ModelOperationFailure
from polyinference.agent.worker import AppContext
from polyinference.agent.worker import model as worker_model
from polyinference.contracts import CodeRevision, OperationRequest
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.runtime.inference import HTTPInference, IncompleteGeneration


@pytest.mark.parametrize("thinking_only", [False, True])
async def test_anthropic_truncation_preserves_usage_without_promoting_partial_json(thinking_only):
    partial = '{"kind":"candidate","summary":"valid JSON is still incomplete"}'

    async def handler(request):
        return httpx.Response(200, json={
            "id": "msg-cutoff", "model": "fixture", "stop_reason": "max_tokens",
            "content": [{"type": "thinking", "thinking": "private reasoning"}]
            + ([] if thinking_only else [{"type": "text", "text": partial}]),
            "usage": {"input_tokens": 10, "output_tokens": 8000, "cache_read_input_tokens": 20},
        })

    from polyinference.config import Endpoint

    adapter = HTTPInference(Endpoint(protocol="anthropic", model="fixture"),
                            httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    try:
        with pytest.raises(IncompleteGeneration) as caught:
            await adapter.generate([{"role": "user", "content": "task"}], 8000)
        failure = caught.value
        assert failure.response["text"] == ("" if thinking_only else partial)
        assert failure.response["usage"]["total_tokens"] == 8030
        assert failure.response["incomplete"] is True
        assert failure.diagnostics["category"] == "output_limit"
        assert failure.diagnostics["provider_id"] == "msg-cutoff"
        assert "private reasoning" not in json.dumps(failure.response)
    finally:
        await adapter.close()


@pytest.mark.parametrize("protocol", ["chat", "responses", "gemini"])
async def test_other_http_output_limits_are_classified(protocol):
    from polyinference.config import Endpoint

    bodies = {
        "chat": {"choices": [{"finish_reason": "length", "message": {"content": "partial"}}],
                 "usage": {"total_tokens": 12}},
        "responses": {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
                      "output": [{"type": "message", "content": [{"type": "output_text", "text": "partial"}]}],
                      "usage": {"total_tokens": 12}},
        "gemini": {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "partial"}]}}],
                   "usageMetadata": {"totalTokenCount": 12}},
    }

    async def handler(request):
        return httpx.Response(200, json=bodies[protocol])

    adapter = HTTPInference(Endpoint(protocol=protocol, model="fixture"),
                            httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    try:
        with pytest.raises(IncompleteGeneration) as caught:
            await adapter.generate([{"role": "user", "content": "task"}], 10)
        assert caught.value.response["text"] == "partial"
        assert caught.value.response["usage"]["total_tokens"] == 12
    finally:
        await adapter.close()


async def runtime_fixture(config, handler):
    endpoint = config.local.model_copy(update={"protocol": "anthropic"})
    config = config.model_copy(update={
        "local": endpoint,
        "limits": config.limits.model_copy(update={"max_output_tokens_per_call": 8000}),
    })
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    await ProjectAgent(app).initialize()
    app.process("fixture", "worker")
    base = CodeRevision.model_validate(app.get("head/provisional")["code"])
    await runtime.workspaces.create("fixture-ws", "fixture", "fixture-spec", base, ["a.py"], ["a.py"])
    app.update("fixture-task", {"assignment": {
        "task_id": "fixture", "objective": "Implement incrementally", "write_paths": ["a.py"], "checks": ["syntax"],
    }})
    await runtime.clients["local"].close()
    runtime.clients["local"] = HTTPInference(endpoint, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    state = {"process_id": "fixture", "workspace_id": "fixture-ws", "task_ledger_ref": "fixture-task",
             "phase": "development", "logical_step": 0, "calls": 0}
    return runtime, app, state


def truncated_response():
    # Even syntactically valid tool JSON must not execute after an output-limit stop.
    text = json.dumps({"kind": "action", "tool": "files.write", "arguments": {
        "path": "a.py", "content": "UNSAFE PARTIAL WRITE", "expected_digest": None,
    }})
    return httpx.Response(200, json={
        "id": "msg-cutoff", "model": "fixture", "stop_reason": "max_tokens",
        "content": [{"type": "text", "text": text}], "usage": {"input_tokens": 10, "output_tokens": 8000},
    })


@pytest.mark.parametrize("failures", [1, 2])
async def test_worker_recovers_smaller_response_and_replay_does_not_resubmit(config, failures):
    calls = []

    async def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body["max_tokens"] == 8000
        if len(calls) > 1:
            target = 4096 // (2 ** (len(calls) - 2))
            assert f"below {target} UTF-8 bytes" in body["messages"][-1]["content"]
        if len(calls) <= failures:
            return truncated_response()
        assert "substantially smaller" in body["messages"][-1]["content"]
        assert "UNSAFE PARTIAL WRITE" not in body["messages"][-1]["content"]
        return httpx.Response(200, json={
            "model": "fixture", "stop_reason": "end_turn",
            "content": [{"type": "text", "text": '{"kind":"action","tool":"files.list","arguments":{}}'}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        })

    runtime, app, state = await runtime_fixture(config, handler)
    try:
        result = await worker_model(state, SimpleNamespace(context=AppContext(app)))
        assert result["reply"]["tool"] == "files.list"
        assert result["calls"] == failures + 1
        assert (await app.model(state))["tool"] == "files.list"
        assert len(calls) == failures + 1
        effects = [e for _, _, e in runtime.records.scan("effect/")]
        assert len(effects) == failures + 1
        assert all(e["request"]["payload"]["kind"] == "model_query" for e in effects)
        assert len(runtime.records.scan("output-retry/")) == failures
        assert not runtime.records.scan("recovery/")
        original = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        assert (await runtime.execute(original)).state == "succeeded"
        failed = await runtime._execute_once(original)  # The original attempt remains immutable.
        assert failed.state == "failed" and failed.error.code == "IncompleteGeneration"
        assert failed.execution_termination == "confirmed_stopped"
        assert failed.usage[0].value == 8010 and failed.actual_backend.model_version == "fixture"
        assert app.read(failed.output_refs[0])["incomplete"] is True
        assert not runtime.records.scan("model-failures/")
        root = runtime.workspaces.root_for(runtime.workspaces.current("fixture-ws"))
        assert (root / "a.py").read_text() == "VALUE = 1\n"
        assert runtime.admission["local"].active == 0
        assert app.get("budget/process/fixture")["reserved_or_used"] == failures * 8010 + 15
    finally:
        await runtime.close()


@pytest.mark.parametrize("recoveries", [0, 1, 2])
async def test_output_limit_recovery_is_finite_and_replay_keeps_last_failure(config, recoveries):
    config = config.model_copy(update={"max_model_recoveries": recoveries})
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return truncated_response()

    runtime, app, state = await runtime_fixture(config, handler)
    try:
        operation_ids = []
        for _ in range(2):
            with pytest.raises(ModelOperationFailure) as caught:
                await app.model(state)
            operation_ids.append(caught.value.result.operation_id)
        assert calls == recoveries + 1
        assert operation_ids[0] == operation_ids[1]
        assert not runtime.uncertain()
        assert runtime.admission["local"].active == 0
        assert app.get("budget/process/fixture")["reserved_or_used"] == calls * 8010
    finally:
        await runtime.close()


async def test_output_recovery_preserves_mandatory_phase_allowance(config):
    config = config.model_copy(update={"limits": config.limits.model_copy(update={"max_model_calls": 5})})
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return truncated_response()

    runtime, app, state = await runtime_fixture(config, handler)
    try:
        with pytest.raises(ModelOperationFailure):
            await app.model(state)
        assert calls == 1
        assert not runtime.records.scan("recovery/")
    finally:
        await runtime.close()
