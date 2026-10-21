"""OS inference recovery preserves budgets, replay, authority and effect certainty."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest

from polyinference.config import Endpoint, RuntimeConfig
from polyinference.contracts import (
    AgentJob,
    ArtifactRef,
    ContextPart,
    ContextView,
    ModelQuery,
    OperationRequest,
    ProcessSpec,
)
from polyinference.primitives import digest, now, operation_fingerprint
from polyinference.runtime.codex import NativeJobStopped
from polyinference.runtime.inference import HTTPInference
from polyinference.runtime.kernel import KernelRuntime, UncertainEffect


async def setup(tmp_path, protocol="anthropic", binding="local", endpoint_options=None, **options):
    endpoint = Endpoint(model="fixture", protocol=protocol, brokered_tools=True, **(endpoint_options or {}))
    config = RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
                           local=endpoint, cloud=endpoint, role_bindings={"researcher": binding},
                           model_retry_delay_ms=0, **options)
    rt = await KernelRuntime(config).open()
    scope = rt.scope.model_copy(update={"process_id": "research"})
    prompt = rt.artifacts.put(b"Summarize facts", scope)
    examples = json.loads((Path(__file__).parents[1] / "design-docs/langgraph-agent/examples.json").read_text())
    template = next(r for r in examples["records"] if r["kind"] == "process_spec")
    spec = ProcessSpec.model_validate({
        **template, "record_id": "process-spec/research", "scope": scope.model_dump(mode="json"),
        "created_at": now(), "required_features": [], "extensions": {}, "process_id": "research",
        "parent_process_id": None, "role": "researcher", "entry_point": "summary", "task_spec_ref": None,
        "attempt_id": None, "workspace_id": None, "input_refs": [prompt], "limits": config.limits,
        "output_schema_ref": "summary/1", "grant_ref": "grant/run", "budget_account_ref": "budget/run",
        "program": {**template["program"], "program_id": "research", "program_version": "1"},
    })
    rt.processes.register(spec, binding, capabilities=["user.notify"])
    context = ContextView(
        view_id="facts", digest=digest(b"facts"), parts=[ContextPart(
            part_id="facts", content=prompt, part_kind="data", trust="user", source_ref="user", required=True)],
        memory_snapshot_refs=[], tool_catalog_digest=digest(b"none"), maximum_input_tokens=24000, omitted_refs=[],
    )
    if protocol == "codex_app_server":
        rt.register_agent_protocol("research/1", {"type": "object", "properties": {}},
                                   workspace="none", brokered=True)
        payload = AgentJob(role="researcher", objective=prompt, context=context, workspace_id="unused",
                           allowed_capabilities=["user.notify"], required_phase_protocol="research/1",
                           required_guarantees=[], response_schema_ref="summary/1", session_ref=None)
    else:
        payload = ModelQuery(role="researcher", phase="summary", prompt_template_ref="summary/1", context=context,
                             response_schema_ref="summary/1", capability_requirements=[], temperature=0, session_ref=None)
    request = OperationRequest(
        record_id="request/research/summary", scope=scope, created_at=now(), revision=1, operation_id="summary",
        logical_step_id="summary", intent_digest=digest(b"pending"), causal_parent_ref=None, trace_id="run",
        grant_ref="grant/run", owner_generation=1, expected_process_revision=1, expected_binding_generation=1,
        schedule_ref="summary/1", budget_account_ref="budget/run", deadline=now() + timedelta(seconds=30),
        limits=config.limits, resources=[], conflict_keys=[], safe_boundary="settled_operation",
        replay_policy="reconcile_before_retry", payload=payload,
    )
    return rt, request.model_copy(update={"intent_digest": operation_fingerprint(request)})


def body(protocol, text):
    result = {"id": "fixture-id", "model": "fixture", "usage": {"total_tokens": 11}}
    if protocol == "anthropic":
        result.update(stop_reason="end_turn", content=[{"type": "text", "text": text}],
                      usage={"input_tokens": 4, "output_tokens": 7})
    elif protocol == "gemini":
        result.update(candidates=[{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}],
                      usageMetadata={"totalTokenCount": 11})
    elif protocol == "responses":
        result.update(status="completed", output=[{"type": "message", "content": [{"type": "output_text", "text": text}]}])
    else:
        result.update(choices=[{"finish_reason": "stop", "message": {"content": text}}])
    return result


async def install(rt, request, handler):
    binding = rt.config.role_bindings[request.payload.role]
    await rt.clients[binding].close()
    rt.clients[binding] = HTTPInference(getattr(rt.config, binding),
                                        httpx.AsyncClient(transport=httpx.MockTransport(handler)))


@pytest.mark.parametrize("binding", ["local", "cloud"])
@pytest.mark.parametrize("protocol", ["anthropic", "chat", "responses", "gemini"])
async def test_empty_response_retries_and_retains_usage_and_immutable_failure(tmp_path, protocol, binding):
    rt, request = await setup(tmp_path, protocol, binding)
    calls = []

    async def handler(http_request):
        calls.append(json.loads(http_request.content))
        return httpx.Response(200, headers={"request-id": "req-fixture"},
                              json=body(protocol, "" if len(calls) == 1 else "valid answer"))

    await install(rt, request, handler)
    try:
        first, concurrent = await asyncio.gather(rt.execute(request), rt.execute(request))
        assert first == concurrent and first.state == "succeeded"
        assert len(calls) == 2 and calls[0] == calls[1]
        failed = rt.records.get("effect/summary")[1]["result"]
        diagnostic = failed["extensions"]["polyinference/model-output-error"]
        assert diagnostic["reason"] == "empty_text" and diagnostic["request_id"] == "req-fixture"
        assert failed["usage"][0]["value"] == 11
        assert failed["actual_backend"]["backend_id"] == binding
        assert rt.records.get("budget/process/research")[1]["reserved_or_used"] == 22
        rt.processes.finish("research")
        assert await rt.execute(request) == first
        assert len(calls) == 2
        assert rt.records.get("effect/summary")[1]["result"] == failed
        assert rt.admission[binding].active == 0 and not rt.uncertain()
        assert not rt.records.scan("task/") and not rt.config.repo_path.exists()
    finally:
        await rt.close()


@pytest.mark.parametrize("binding", ["local", "cloud"])
@pytest.mark.parametrize("answer", ["A short plain-text answer.", '{"answer":"short"}'])
async def test_output_recovery_preserves_plain_text_and_structured_grammars(tmp_path, binding, answer):
    rt, request = await setup(tmp_path, binding=binding)
    calls = []

    async def handler(http_request):
        wire = json.loads(http_request.content)
        calls.append(wire)
        if len(calls) == 1:
            partial = body("anthropic", "unusable partial answer")
            partial["stop_reason"] = "max_tokens"
            return httpx.Response(200, json=partial)
        feedback = wire["messages"][-1]["content"]
        assert "UTF-8 bytes" in feedback and "same declared protocol" in feedback
        assert "JSON" not in feedback
        return httpx.Response(200, json=body("anthropic", answer))

    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded"
        assert json.loads(rt.artifacts.read(result.output_refs[0]))["text"] == answer
        assert (await rt.execute(request)) == result and len(calls) == 2
        assert rt.records.get("effect/summary")[1]["result"]["state"] == "failed"
        assert rt.admission[binding].active == 0 and not rt.uncertain()
        assert not rt.records.scan("task/") and not rt.config.repo_path.exists()
    finally:
        await rt.close()


@pytest.mark.parametrize("failure", ["thinking_only", "invalid_json", "invalid_shape", "unexpected_content"])
async def test_unusable_response_facts_survive_and_thinking_is_not_exported(tmp_path, failure):
    rt, request = await setup(tmp_path)
    calls = 0

    async def handler(_):
        nonlocal calls
        calls += 1
        if calls > 1:
            return httpx.Response(200, json=body("anthropic", "recovered"))
        if failure == "invalid_json":
            return httpx.Response(200, content=b"invalid JSON")
        if failure == "invalid_shape":
            return httpx.Response(200, json={"content": None, "stop_reason": "end_turn"})
        result = body("anthropic", "")
        result["content"] = [{"type": "thinking", "thinking": "PRIVATE REASONING"}]
        if failure == "unexpected_content":
            result["content"].append({"type": "tool_use", "name": "never_execute", "input": {}})
        return httpx.Response(200, json=result)

    await install(rt, request, handler)
    try:
        assert (await rt.execute(request)).state == "succeeded"
        assert calls == 2
        failed = rt.records.get("effect/summary")[1]["result"]
        assert "PRIVATE REASONING" not in json.dumps(failed)
        retained = json.loads(rt.artifacts.read(ArtifactRef.model_validate(failed["output_refs"][0])))
        assert "PRIVATE REASONING" not in json.dumps(retained)
        assert retained["text"] == "" and "error" in retained
        assert not any(e[2]["request"]["payload"]["kind"] == "capability_call" for e in rt.records.scan("effect/"))
    finally:
        await rt.close()


async def test_exhaustion_and_restart_replay_never_resubmit(tmp_path):
    rt, request = await setup(tmp_path)
    config = rt.config
    calls = 0

    async def handler(_):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=body("anthropic", ""))

    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "failed" and calls == 2
        assert (await rt.execute(request)) == result and calls == 2
    finally:
        await rt.close()
    rt = await KernelRuntime(config).open()
    await install(rt, request, handler)
    try:
        assert await rt.execute(request) == result
        assert calls == 2 and len(rt.records.scan("model-retry/")) == 1
    finally:
        await rt.close()


@pytest.mark.parametrize("failure", [429, 503, "connect", "disconnect", 400, 401, 403])
async def test_transport_retry_classification_and_backoff(tmp_path, monkeypatch, failure):
    rt, request = await setup(tmp_path)
    calls, waits = [], []

    async def wait_until(value):
        waits.append((datetime.fromisoformat(value) - now()).total_seconds())

    monkeypatch.setattr(rt.model_retries, "wait_until", wait_until)

    async def handler(_):
        calls.append(1)
        if len(calls) > 1:
            return httpx.Response(200, json=body("anthropic", "ok"))
        if failure == "connect":
            raise httpx.ConnectError("fixture")
        if failure == "disconnect":
            raise httpx.ReadError("fixture")
        return httpx.Response(failure, headers={"retry-after": "2"}, json={"error": {"type": "fixture"}})

    await install(rt, request, handler)
    try:
        if failure == "disconnect":
            with pytest.raises(UncertainEffect):
                await rt.execute(request)
            assert rt.uncertain() and len(calls) == 1 and not waits
            return
        result = await rt.execute(request)
        if failure in {429, 503, "connect"}:
            assert result.state == "succeeded" and len(calls) == 2
            if failure in {429, 503}:
                assert 1.5 < waits[0] <= 2
            else:
                assert rt.records.get("effect/summary")[1]["result"]["extensions"][
                    "polyinference/attempted-backend"]["submitted"] is False
                assert rt.records.get("budget/process/research")[1]["reserved_or_used"] == 11
        else:
            assert result.state == "failed" and len(calls) == 1 and not waits
    finally:
        await rt.close()


@pytest.mark.parametrize("stop", ["cancel", "deadline", "allowance", "retry_after", "shutdown"])
async def test_backoff_obeys_cancellation_deadlines_allowances_and_shutdown(tmp_path, monkeypatch, stop):
    rt, request = await setup(tmp_path)
    if stop == "deadline":
        request = request.model_copy(update={"deadline": now() + timedelta(milliseconds=100)})
    if stop == "allowance":
        request = request.model_copy(update={"limits": request.limits.model_copy(update={"max_model_calls": 1})})
        rt.config = rt.config.model_copy(update={"limits": request.limits})
        request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
    calls = 0

    async def handler(_):
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"retry-after": "120" if stop == "retry_after" else "2"},
                              json={"error": {"type": "rate_limit"}})

    async def wait_until(_):
        if stop == "cancel":
            rt.processes.cancel("research", "Cancelled during backoff")
        if stop == "shutdown":
            rt.closing = True

    monkeypatch.setattr(rt.model_retries, "wait_until", wait_until)
    await install(rt, request, handler)
    try:
        assert (await rt.execute(request)).state == "failed"
        assert calls == 1 and rt.admission["local"].active == 0
    finally:
        rt.closing = False
        await rt.close()


@pytest.mark.parametrize("mode", ["safe", "callback", "unbrokered", "policy"])
async def test_native_retries_only_before_any_brokered_effect(tmp_path, mode):
    rt, request = await setup(tmp_path, "codex_app_server")

    class Provider:
        calls = 0

        async def generate_job(self, messages, snapshot, schema, callback):
            self.calls += 1
            if self.calls == 1:
                if mode == "callback":
                    await callback("notification", {"tool": "user.notify", "arguments": {"text": "once"}})
                if mode == "unbrokered":
                    (snapshot / "unauthorized.txt").write_text("unbrokered mutation")
                if mode == "policy":
                    raise NativeJobStopped("Permission policy mismatch", retryable=False)
                raise NativeJobStopped("Fixture terminal failure")
            return {"text": "{}", "model": "fixture", "usage": {"total_tokens": 11}}

        async def close(self):
            pass

    await rt.clients["local"].close()
    provider = rt.clients["local"] = Provider()
    try:
        result = await rt.execute(request)
        assert result.state == ("succeeded" if mode == "safe" else "failed")
        assert provider.calls == (2 if mode == "safe" else 1)
        assert len(rt.records.scan("user-message/")) == int(mode == "callback")
        assert rt.admission["local"].active == 0
    finally:
        await rt.close()


async def test_invalid_input_circuit_does_not_block_a_different_context(tmp_path):
    rt, request = await setup(tmp_path)
    calls = 0

    async def handler(_):
        nonlocal calls
        calls += 1
        return httpx.Response(400, json={"error": {"type": "invalid_request"}}) if calls <= 2 else httpx.Response(
            200, json=body("anthropic", "healthy input"))

    await install(rt, request, handler)
    try:
        for step in ("bad-1", "bad-2", "blocked"):
            result = await rt.execute(request.model_copy(update={"operation_id": step, "logical_step_id": step}))
            assert result.state == "failed"
        assert calls == 2
        prompt = rt.artifacts.put(b"Different valid facts", request.scope)
        context = request.payload.context.model_copy(update={"parts": [request.payload.context.parts[0].model_copy(
            update={"content": prompt})]})
        changed = request.model_copy(update={"operation_id": "healthy", "logical_step_id": "healthy",
                                             "payload": request.payload.model_copy(update={"context": context})})
        changed = changed.model_copy(update={"intent_digest": operation_fingerprint(changed)})
        assert (await rt.execute(changed)).state == "succeeded" and calls == 3
    finally:
        await rt.close()


async def test_restart_during_backoff_resumes_the_same_durable_retry_intent(tmp_path, monkeypatch):
    rt, request = await setup(tmp_path)
    config, calls = rt.config, []

    async def handler(_):
        calls.append(1)
        return httpx.Response(200, json=body("anthropic", "" if len(calls) == 1 else "ok"))

    async def interrupted_wait(_):
        raise RuntimeError("simulated coordinator stop before retry submission")

    monkeypatch.setattr(rt.model_retries, "wait_until", interrupted_wait)
    await install(rt, request, handler)
    try:
        with pytest.raises(RuntimeError, match="coordinator stop"):
            await rt.execute(request)
        retained = rt.records.scan("model-retry/")[0][2]
        assert len(calls) == 1 and not rt.records.get("effect/" + retained["request"]["operation_id"])
    finally:
        await rt.close()
    rt = await KernelRuntime(config).open()
    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded" and len(calls) == 2
        assert rt.records.scan("model-retry/")[0][2] == retained
        assert rt.records.get("model-retry-outcome/summary")[1]["reason"] == "recovered"
    finally:
        await rt.close()


@pytest.mark.parametrize("resource", ["tokens", "spend"])
async def test_retry_cannot_exceed_aggregate_token_or_spend_budget(tmp_path, resource):
    options = ({"run_token_budget": 4500} if resource == "tokens" else {
        "run_spend_budget_microusd": 4500, "endpoint_options": {"estimated_microusd_per_token": 1},
    })
    rt, request = await setup(tmp_path, **options)
    calls = []

    async def handler(_):
        calls.append(1)
        return httpx.Response(503, json={"error": {"type": "temporary"}})

    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "failed" and "budget exhausted" in result.error.message
        assert len(calls) == 1 and rt.admission["local"].active == 0
        assert rt.records.get("budget/run")[1]["reserved_or_used"] <= 4500
        if resource == "spend":
            assert rt.records.get("spend/run")[1]["estimated_microusd"] <= 4500
    finally:
        await rt.close()


async def test_os_retry_followed_by_output_limit_uses_os_adaptation(config):
    from test_output_limits import runtime_fixture, truncated_response

    calls = []

    async def handler(http_request):
        calls.append(json.loads(http_request.content))
        if len(calls) == 1:
            return httpx.Response(200, json=body("anthropic", ""))
        if len(calls) == 2:
            return truncated_response()
        assert "substantially smaller" in calls[-1]["messages"][-1]["content"]
        return httpx.Response(200, json=body("anthropic", '{"kind":"candidate","summary":"small reply"}'))

    rt, app, state = await runtime_fixture(config, handler)
    try:
        assert (await app.model(state))["kind"] == "candidate"
        assert (await app.model(state))["kind"] == "candidate" and len(calls) == 3
        retry = rt.records.scan("model-retry/")[0][2]
        recovery = rt.records.scan("output-retry/")[0][2]["extensions"]["runtime/output-retry"]
        assert recovery["previous_operation_id"] == retry["request"]["operation_id"]
        assert recovery["root_operation_id"] == retry["previous_operation_id"]
        assert not rt.records.scan("recovery/")
    finally:
        await rt.close()


async def test_one_off_full_admission_queue_retries_before_provider_submission(tmp_path, monkeypatch):
    rt, request = await setup(tmp_path, max_queued_operations=1)
    queue = rt.admission["local"].queues[0]
    ticket = object()
    queue.append(ticket)
    calls = []

    async def handler(_):
        calls.append(1)
        return httpx.Response(200, json=body("anthropic", "ok"))

    async def wait_until(_):
        assert queue.pop() is ticket

    monkeypatch.setattr(rt.model_retries, "wait_until", wait_until)
    await install(rt, request, handler)
    try:
        assert (await rt.execute(request)).state == "succeeded"
        assert len(calls) == 1
        failed = rt.records.get("effect/summary")[1]["result"]
        assert failed["extensions"]["polyinference/provider-error"]["category"] == "admission"
        assert failed["extensions"]["polyinference/attempted-backend"]["submitted"] is False
        assert rt.records.get("budget/run")[1]["reserved_or_used"] == 11
    finally:
        await rt.close()


async def test_os_retry_preserves_the_callers_finishing_reserve(config):
    from test_output_limits import runtime_fixture

    from polyinference.agent.services import ModelOperationFailure

    config = config.model_copy(update={"limits": config.limits.model_copy(update={"max_model_calls": 5})})
    calls = []

    async def handler(_):
        calls.append(1)
        return httpx.Response(200, json=body("anthropic", ""))

    rt, app, state = await runtime_fixture(config, handler)
    try:
        with pytest.raises(ModelOperationFailure):
            await app.model(state)
        assert len(calls) == 1 and not rt.records.scan("model-retry/")
        outcome = rt.records.scan("model-retry-outcome/")[0][2]
        assert outcome["reason"] == "model-call allowance or finishing reserve reached"
    finally:
        await rt.close()


@pytest.mark.parametrize("recoveries", [1, 2])
async def test_os_retry_of_adaptive_recovery_does_not_consume_caller_allowance(config, recoveries):
    from test_output_limits import runtime_fixture, truncated_response

    config = config.model_copy(update={"max_model_recoveries": recoveries})
    calls = []

    async def handler(http_request):
        calls.append(json.loads(http_request.content))
        if len(calls) == 1:
            return truncated_response()
        assert "substantially smaller" in calls[-1]["messages"][-1]["content"]
        if len(calls) == 2:
            return httpx.Response(503, json={"error": {"type": "temporary"}})
        return httpx.Response(200, json=body("anthropic", '{"kind":"candidate","summary":"recovered"}'))

    rt, app, state = await runtime_fixture(config, handler)
    try:
        assert (await app.model(state))["kind"] == "candidate"
        assert len(calls) == 3 and calls[1] == calls[2]
        assert len(rt.records.scan("output-retry/")) == 1
        assert not rt.records.scan("recovery/")
        retry = rt.records.scan("model-retry/")[0][2]
        parent = rt.records.get("effect/" + retry["previous_operation_id"])[1]
        assert parent["request"]["extensions"].get("runtime/output-retry")
        assert (await app.model(state))["kind"] == "candidate"
        assert len(calls) == 3 and len(rt.records.scan("output-retry/")) == 1
    finally:
        await rt.close()


async def test_unissued_os_retry_cannot_bypass_caller_recovery_authorization(tmp_path):
    rt, request = await setup(tmp_path, max_model_recoveries=0)
    calls = []

    async def handler(_):
        calls.append(1)
        return httpx.Response(200, json=body("anthropic", "" if len(calls) == 1 else "ok"))

    await install(rt, request, handler)
    try:
        assert (await rt.execute(request)).state == "succeeded" and len(calls) == 2
        forged = request.model_copy(update={
            "operation_id": "unissued", "logical_step_id": "unissued",
            "extensions": {"polyinference/recovery-of": request.operation_id,
                           "polyinference/recovery-reason": "Not authorized",
                           "runtime/model-retry": {"root_operation_id": request.operation_id,
                                                   "previous_operation_id": request.operation_id, "attempt": 1}},
        })
        forged = forged.model_copy(update={"intent_digest": operation_fingerprint(forged)})
        with pytest.raises(ValueError, match="durable OS-issued intent"):
            await rt.execute(forged)
        assert len(calls) == 2 and not rt.records.scan("recovery/")
    finally:
        await rt.close()
