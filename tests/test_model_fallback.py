"""Availability fallback keeps original authority, replay and physical accounting."""

import asyncio
import json
import sys
from datetime import timedelta

import httpx
import pytest
from test_model_retries import body, setup

from polyinference.config import AgentConfig
from polyinference.contracts import ProcessSpec
from polyinference.primitives import operation_fingerprint
from polyinference.runtime.inference import HTTPInference, model_unavailable
from polyinference.runtime.kernel import KernelRuntime, UncertainEffect
from polyinference.system_settings import RetryModel


def next_request(request, number):
    result = request.model_copy(
        update={
            "operation_id": f"call-{number}",
            "logical_step_id": f"call-{number}",
            "record_id": f"request/call-{number}",
        }
    )
    return result.model_copy(update={"intent_digest": operation_fingerprint(result)})


async def install(rt, handler):
    for mapping in [rt.clients, rt.fallback_clients]:
        endpoint = mapping["cloud"].endpoint
        await mapping["cloud"].close()
        mapping["cloud"] = HTTPInference(endpoint, httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def options():
    return {"retry_model": RetryModel(model="gpt-6.1-terra", reasoning_effort="high", fallback_calls=7)}


async def test_availability_retry_probe_and_seven_call_window_survive_restart(tmp_path):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    calls = []
    primary = 0

    async def handler(http_request):
        nonlocal primary
        wire = json.loads(http_request.content)
        calls.append(wire["model"])
        if wire["model"] == "fixture":
            primary += 1
            if primary <= 2:
                return httpx.Response(
                    503,
                    json={
                        "error": {
                            "code": "model_unavailable",
                            "message": "Selected model is at capacity. Please try a different model.",
                        }
                    },
                )
        value = body("chat", "complete")
        value["model"] = wire["model"]
        return httpx.Response(200, json=value)

    await install(rt, handler)
    try:
        first = await rt.execute(request)
        assert first.state == "succeeded" and first.actual_backend.model_version == "gpt-6.1-terra"
        assert calls == ["fixture", "gpt-6.1-terra"]
        assert rt.records.get("model-fallback-state/cloud")[1]["remaining"] == 7
        for number in range(1, 4):
            assert (await rt.execute(next_request(request, number))).state == "succeeded"
        config = rt.config
        await rt.close()
        rt = await KernelRuntime(config).open()
        await install(rt, handler)
        assert rt.records.get("model-fallback-state/cloud")[1]["remaining"] == 4
        for number in range(4, 8):
            assert (await rt.execute(next_request(request, number))).state == "succeeded"
        assert calls == ["fixture", "gpt-6.1-terra"] + ["gpt-6.1-terra"] * 7
        assert (await rt.execute(next_request(request, 8))).actual_backend.model_version == "gpt-6.1-terra"
        assert calls[-2:] == ["fixture", "gpt-6.1-terra"]
        assert rt.records.get("model-fallback-state/cloud")[1]["remaining"] == 7
        for number in range(9, 16):
            assert (
                await rt.execute(next_request(request, number))
            ).actual_backend.model_version == "gpt-6.1-terra"
        assert (await rt.execute(next_request(request, 16))).actual_backend.model_version == "fixture"
        state = rt.records.get("model-fallback-state/cloud")
        assert not state[1]["main_failed"] and state[1]["remaining"] == 0
        count = len(calls)
        assert await rt.execute(request) == first
        assert len(calls) == count and rt.records.get("model-fallback-state/cloud") == state
        assert rt.records.get("effect/summary")[1]["result"]["state"] == "failed"
        assert rt.inference_calls_used("research") == 19
        assert not rt.records.get("model-fallback-state/local")
        assert not rt.uncertain() and rt.admission["cloud"].active == 0
    finally:
        await rt.close()


@pytest.mark.parametrize(
    "status,message,code",
    [
        (401, "Invalid API key", "authentication_error"),
        (403, "Model permission denied", "permission_denied"),
        (429, "Model quota exhausted", "insufficient_quota"),
        (400, "Invalid request", None),
        (401, "Model unavailable", "model_unavailable"),
        (403, "Model unavailable", "model_unavailable"),
    ],
)
async def test_non_model_availability_errors_do_not_switch_models(tmp_path, status, message, code):
    rt, request = await setup(
        tmp_path, protocol="chat", binding="cloud", endpoint_options=options(), model_call_retries=0
    )
    calls = []

    async def handler(req):
        calls.append(json.loads(req.content)["model"])
        return httpx.Response(status, json={"error": {"message": message, "code": code}})

    await install(rt, handler)
    try:
        assert (await rt.execute(request)).state == "failed"
        assert calls == ["fixture"] and not rt.records.scan("model-fallback/")
    finally:
        await rt.close()


async def test_alternative_failure_is_one_attempt_and_call_limit_can_prevent_it(tmp_path):
    for limit, expected in [(4, 2), (1, 1)]:
        rt, request = await setup(
            tmp_path / str(limit),
            protocol="chat",
            binding="cloud",
            endpoint_options=options(),
            call_limit=limit,
        )
        calls = []

        async def handler(req):
            calls.append(json.loads(req.content)["model"])
            return httpx.Response(
                503, json={"error": {"code": "model_unavailable", "message": "Model unavailable"}}
            )

        await install(rt, handler)
        try:
            assert (await rt.execute(request)).state == "failed"
            assert len(calls) == expected and rt.inference_calls_used("research") == expected
        finally:
            await rt.close()


async def test_uncertain_generation_never_switches_models(tmp_path):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    calls = []

    async def handler(req):
        calls.append(json.loads(req.content)["model"])
        raise httpx.ReadTimeout("lost delivery", request=req)

    await install(rt, handler)
    try:
        with pytest.raises(UncertainEffect):
            await rt.execute(request)
        assert calls == ["fixture"] and rt.uncertain() and not rt.records.scan("model-fallback/")
    finally:
        await rt.close()


@pytest.mark.parametrize(
    "provider_error",
    [
        {"message": "Selected model is at capacity. Please try a different model."},
        {"message": "Provider busy", "codexErrorInfo": "serverOverloaded"},
    ],
)
async def test_effectful_native_fallback_resumes_thread_and_replays_old_callback_once(
    tmp_path, provider_error
):
    script = tmp_path / "native.py"
    log = tmp_path / "native-models.jsonl"
    script.write_text(
        "ERROR="
        + repr(provider_error)
        + "\nLOG="
        + repr(str(log))
        + "\n"
        + r"""
import json,sys
def send(value): print(json.dumps(value),flush=True)
def tool(call,text):
 send({"id":99,"method":"item/tool/call","params":{"threadId":"retained-thread","turnId":"turn", "callId":call,
   "tool":"polyinference_tool","arguments":{"tool":"user.notify","arguments":{"text":text}}}})
 response=json.loads(sys.stdin.readline())
 assert response["result"]["success"],response
 assert json.loads(response["result"]["contentItems"][0]["text"])["state"]=="succeeded"
for line in sys.stdin:
 msg=json.loads(line);method=msg.get('method')
 if method=='initialize': send({'id':msg['id'],'result':{}})
 elif method in ['thread/start','thread/resume']:
  model=msg['params']['model']; resumed=method=='thread/resume'
  with open(LOG,'a') as f:f.write(json.dumps({'method':method,'model':model})+'\n')
  if resumed: assert msg['params']['threadId']=='retained-thread'
  else: assert msg['params']['allowProviderModelFallback'] is False
  assert msg['params']['permissions']=='polyinference_readonly'
  send({'id':msg['id'],'result':{'thread':{'id':'retained-thread'},'sandbox':{'type':'readOnly'},'approvalPolicy':'never'}})
 elif method=='turn/start':
  send({'id':msg['id'],'result':{'turn':{'id':'turn'}}})
  tool('already-done','first effect')
  if not resumed:
   send({'method':'turn/completed','params':{'threadId':'retained-thread','turn':{'id':'turn','status':'failed',
       'error':ERROR}}})
  else:
   assert model=='gpt-6.1-terra' and msg['params']['effort']=='high'
   assert 'Continue the interrupted turn' in msg['params']['input'][0]['text']
   tool('remaining','remaining effect')
   send({'method':'item/completed','params':{'threadId':'retained-thread','turnId':'turn','item':{'type':'agentMessage','text':'{}'}}})
   send({'method':'thread/tokenUsage/updated','params':{'threadId':'retained-thread','turnId':'turn','tokenUsage':{'total':{'totalTokens':10}}}})
   send({'method':'turn/completed','params':{'threadId':'retained-thread','turn':{'id':'turn','status':'completed','items':[]}}})
"""
    )
    rt, request = await setup(
        tmp_path,
        protocol="codex_app_server",
        binding="cloud",
        endpoint_options={**options(), "command": [sys.executable, str(script)], "timeout_seconds": 5},
    )
    # A caller-provided thread reference cannot become ambient conversation access.
    request = request.model_copy(
        update={"payload": request.payload.model_copy(update={"session_ref": "not-os-issued"})}
    )
    request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded" and result.actual_backend.model_version == "gpt-6.1-terra"
        assert [json.loads(s) for s in log.read_text().splitlines()] == [
            {"method": "thread/start", "model": "fixture"},
            {"method": "thread/resume", "model": "gpt-6.1-terra"},
        ]
        assert len(rt.records.scan("user-message/")) == 2
        children = [v for _, _, v in rt.records.scan("effect/") if v["request"].get("causal_parent_ref")]
        assert len(children) == 2 and rt.inference_calls_used("research") == 2
        assert not rt.uncertain() and rt.admission["cloud"].active == 0
        before = log.read_bytes()
        assert await rt.execute(request) == result and log.read_bytes() == before
    finally:
        await rt.close()


def test_agent_retry_default_is_configurable_and_os_default_is_absent(config):
    cloud = {**config.cloud.model_dump(), "protocol": "codex_app_server", "brokered_tools": True}
    value = {**config.model_dump(), "cloud": cloud}
    value["cloud"].pop("retry_model", None)
    configured = AgentConfig.model_validate(value)
    assert configured.cloud.retry_model.model == "gpt-6.1-terra"
    assert configured.cloud.retry_model.reasoning_effort == "high"
    assert configured.cloud.retry_model.fallback_calls == RetryModel(model="os-choice").fallback_calls == 7
    custom = AgentConfig.model_validate(
        {**value, "default_retry_model": {"model": "chosen", "reasoning_effort": "low", "fallback_calls": 5}}
    )
    assert custom.cloud.retry_model.model == "chosen" and custom.cloud.retry_model.fallback_calls == 5
    disabled = AgentConfig.model_validate({**value, "default_retry_model": None})
    assert disabled.cloud.retry_model is None
    explicit = AgentConfig.model_validate({**value, "cloud": {**cloud, "retry_model": None}})
    assert explicit.cloud.retry_model is None
    assert AgentConfig.model_validate_json(explicit.model_dump_json()).cloud.retry_model is None
    assert config.cloud.retry_model is None


async def test_availability_after_transport_retry_switches_before_another_primary_attempt(tmp_path):
    rt, request = await setup(
        tmp_path, protocol="chat", binding="cloud", endpoint_options=options(), model_call_retries=2
    )
    calls = []

    async def handler(req):
        model = json.loads(req.content)["model"]
        calls.append(model)
        if len(calls) == 1:
            return httpx.Response(200, json=body("chat", ""))
        if model == "fixture":
            return httpx.Response(
                503, json={"error": {"code": "model_unavailable", "message": "Model unavailable"}}
            )
        value = body("chat", "done")
        value["model"] = model
        return httpx.Response(200, json=value)

    await install(rt, handler)
    try:
        assert (await rt.execute(request)).state == "succeeded"
        assert calls == ["fixture", "fixture", "gpt-6.1-terra"]
        assert len(rt.records.scan("model-retry/")) == 1
        assert await rt.execute(request) == await rt.execute(request)
        assert len(calls) == 3
    finally:
        await rt.close()


@pytest.mark.parametrize("stop", ["cancel", "deadline"])
async def test_availability_cannot_continue_past_cancellation_or_original_deadline(
    tmp_path, monkeypatch, stop
):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    calls = []

    async def handler(req):
        calls.append(json.loads(req.content)["model"])
        if stop == "cancel":
            rt.processes.cancel("research", "cancel after provider rejection")
        return httpx.Response(
            503, json={"error": {"code": "model_unavailable", "message": "Model unavailable"}}
        )

    await install(rt, handler)
    try:
        if stop == "deadline":
            original = rt.model_fallback.observe

            def expire(req, result, **kwargs):
                original(req, result, **kwargs)
                # Keep a real dispatched failure, then advance only the guard's clock.
                from polyinference.runtime import model_retries

                monkeypatch.setattr(model_retries, "now", lambda: request.deadline + timedelta(seconds=1))

            rt.model_fallback.observe = expire
            result = await rt.execute(request)
        else:
            result = await rt.execute(request)
        assert result.state == "failed" and calls == ["fixture"]
        assert not rt.records.scan("model-fallback/")
    finally:
        await rt.close()


async def test_unissued_fallback_cannot_authorize_model_or_recovery_change(tmp_path):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    forged = next_request(request, "forged").model_copy(
        update={
            "extensions": {
                "runtime/inference-root": request.operation_id,
                "runtime/model-fallback": {
                    "root_operation_id": request.operation_id,
                    "retry_operation_id": "forged",
                    "callback_root_operation_id": request.operation_id,
                },
            }
        }
    )
    forged = forged.model_copy(update={"intent_digest": operation_fingerprint(forged)})
    try:
        with pytest.raises(ValueError, match="durable OS-issued intent"):
            await rt.execute(forged)
        assert rt.inference_calls_used("research") == 0
    finally:
        await rt.close()


async def test_late_primary_success_does_not_erase_a_newer_availability_failure(tmp_path):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    spec = ProcessSpec.model_validate(rt.records.get("process-spec/research")[1])
    scope = request.scope.model_copy(update={"process_id": "research-later"})
    rt.processes.register(
        spec.model_copy(
            update={
                "record_id": "process-spec/research-later",
                "process_id": "research-later",
                "scope": scope,
            }
        ),
        "cloud",
        capabilities=["user.notify"],
    )
    later = next_request(request, 1).model_copy(update={"scope": scope})
    later = later.model_copy(update={"intent_digest": operation_fingerprint(later)})
    first_submitted, release_first = asyncio.Event(), asyncio.Event()
    calls = []

    async def handler(req):
        model = json.loads(req.content)["model"]
        calls.append(model)
        if len(calls) == 1:
            first_submitted.set()
            await release_first.wait()
        elif model == "fixture":
            return httpx.Response(503, json={"error": {"code": "model_unavailable"}})
        value = body("chat", "done")
        value["model"] = model
        return httpx.Response(200, json=value)

    await install(rt, handler)
    first = asyncio.create_task(rt.execute(request))
    try:
        await first_submitted.wait()
        assert (await rt.execute(later)).state == "succeeded"
        release_first.set()
        assert (await first).state == "succeeded"
        assert rt.records.get("model-fallback-state/cloud")[1]["main_failed"]
        assert (await rt.execute(next_request(request, 2))).state == "succeeded"
        assert rt.records.get("model-fallback-state/cloud")[1]["remaining"] == 6
    finally:
        release_first.set()
        await first
        await rt.close()


@pytest.mark.parametrize("status", [429, 500, 503])
async def test_provider_rejection_resends_same_request_on_alternate(tmp_path, status):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    calls = []

    async def handler(req):
        wire = json.loads(req.content)
        calls.append(wire)
        if len(calls) == 1:
            return httpx.Response(status, json={"error": {"message": "Provider temporarily unavailable"}})
        value = body("chat", "done")
        value["model"] = wire["model"]
        return httpx.Response(200, json=value)

    await install(rt, handler)
    try:
        assert (await rt.execute(request)).state == "succeeded"
        assert [c["model"] for c in calls] == ["fixture", "gpt-6.1-terra"]
        assert {k: v for k, v in calls[0].items() if k not in {"model", "reasoning_effort"}} == {
            k: v for k, v in calls[1].items() if k not in {"model", "reasoning_effort"}
        }
        assert rt.records.get("model-fallback-state/cloud")[1]["remaining"] == 7
    finally:
        await rt.close()


def test_native_provider_diagnostics_exclude_policy_limits_and_unknown_transport():
    for code in [
        "serverOverloaded",
        "flexUnavailable",
        "internalServerError",
        "rateLimitExceeded",
        {"httpConnectionFailed": {"httpStatusCode": 503}},
    ]:
        assert model_unavailable("Provider error", code)
    for code in [
        "unauthorized",
        "badRequest",
        "usageLimitExceeded",
        "contextWindowExceeded",
        "sandboxError",
        {"responseStreamDisconnected": {"httpStatusCode": None}},
    ]:
        assert not model_unavailable("Selected model unavailable", code)


async def test_caller_overrides_os_default_window_and_primary_configuration_is_restored(tmp_path):
    rt, request = await setup(
        tmp_path,
        protocol="chat",
        binding="cloud",
        endpoint_options={
            "retry_model": RetryModel(model="gpt-6.1-terra", reasoning_effort="high", fallback_calls=2),
            "reasoning_effort": "medium",
        },
    )
    calls = []

    async def handler(req):
        wire = json.loads(req.content)
        calls.append(wire["model"])
        if len(calls) == 1:
            return httpx.Response(503, json={"error": {"message": "Provider overloaded"}})
        value = body("chat", "done")
        value["model"] = wire["model"]
        return httpx.Response(200, json=value)

    await install(rt, handler)
    try:
        for number in range(4):
            assert (await rt.execute(next_request(request, number))).state == "succeeded"
        assert calls == ["fixture", "gpt-6.1-terra", "gpt-6.1-terra", "gpt-6.1-terra", "fixture"]
        selected = rt.records.get("model-selection/call-3")[1]
        assert selected["model"] == "fixture" and selected["reasoning_effort"] == "medium"
        assert rt.config.cloud.model == "fixture" and rt.config.cloud.reasoning_effort == "medium"
    finally:
        await rt.close()


async def test_native_continuation_keeps_workspace_edits_and_deduplicates_a_write(config, tmp_path):
    from polyinference.agent.controller import ProjectAgent
    from polyinference.agent.services import AgentServices
    from polyinference.contracts import CodeRevision

    script = tmp_path / "native-write.py"
    script.write_text(r"""
import json,sys,hashlib
from pathlib import Path
def send(value):print(json.dumps(value),flush=True)
def write(call,before,after):
 send({'id':99,'method':'item/tool/call','params':{'threadId':'edit-thread','turnId':'turn','callId':call,
  'tool':'polyinference_tool','arguments':{'tool':'files.write','arguments':{'path':'a.py',
   'expected_digest':'sha256:'+hashlib.sha256(before.encode()).hexdigest(),'content':after}}}})
 response=json.loads(sys.stdin.readline())
 assert response['result']['success'],response
 result=json.loads(response['result']['contentItems'][0]['text'])
 assert result['state']=='succeeded',result
for line in sys.stdin:
 msg=json.loads(line);method=msg.get('method')
 if method=='initialize':send({'id':msg['id'],'result':{}})
 elif method in ['thread/start','thread/resume']:
  resumed=method=='thread/resume'
  assert Path(msg['params']['cwd'],'a.py').read_text()==('VALUE = 2\n' if resumed else 'VALUE = 1\n')
  send({'id':msg['id'],'result':{'thread':{'id':'edit-thread'},'sandbox':{'type':'readOnly'},'approvalPolicy':'never'}})
 elif method=='turn/start':
  send({'id':msg['id'],'result':{'turn':{'id':'turn'}}})
  write('first','VALUE = 1\n','VALUE = 2\n')
  if not resumed:
   send({'method':'turn/completed','params':{'threadId':'edit-thread','turn':{'id':'turn','status':'failed',
    'error':{'message':'Selected model is at capacity'}}}})
  else:
   write('second','VALUE = 2\n','VALUE = 3\n')
   send({'method':'item/completed','params':{'threadId':'edit-thread','turnId':'turn',
    'item':{'type':'agentMessage','text':'{"reply":{"kind":"candidate","summary":"continued edits"}}'}}})
   send({'method':'thread/tokenUsage/updated','params':{'threadId':'edit-thread','turnId':'turn',
    'tokenUsage':{'total':{'totalTokens':10}}}})
   send({'method':'turn/completed','params':{'threadId':'edit-thread','turn':{'id':'turn','status':'completed','items':[]}}})
""")
    endpoint = config.local.model_copy(
        update={
            "protocol": "codex_app_server",
            "brokered_tools": True,
            "command": [sys.executable, str(script)],
            "retry_model": RetryModel(model="gpt-6.1-terra", reasoning_effort="high"),
            "timeout_seconds": 5,
        }
    )
    config = config.model_copy(update={"local": endpoint})
    rt = await KernelRuntime(config).open()
    app = AgentServices(rt, config)
    try:
        await ProjectAgent(app).initialize()
        app.process("fixture", "worker")
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        await rt.workspaces.create("fixture-ws", "fixture", "fixture-spec", base, ["a.py"], ["a.py"])
        app.update(
            "fixture-task",
            {
                "assignment": {
                    "task_id": "fixture",
                    "objective": "Increment value",
                    "write_paths": ["a.py"],
                    "checks": ["syntax"],
                }
            },
        )
        state = {
            "process_id": "fixture",
            "workspace_id": "fixture-ws",
            "task_ledger_ref": "fixture-task",
            "phase": "development",
            "logical_step": 0,
            "calls": 0,
        }
        assert (await app.model(state))["kind"] == "candidate"
        manifest = rt.workspaces.current("fixture-ws")
        root = rt.workspaces.root_for(manifest)
        assert (root / "a.py").read_text() == "VALUE = 3\n"
        writes = [
            v
            for _, _, v in rt.records.scan("effect/")
            if v["request"]["payload"].get("capability_id") == "files.write"
        ]
        assert len(writes) == 2 and all(v["result"]["state"] == "succeeded" for v in writes)
        assert rt.inference_calls_used("fixture") == 2 and not rt.uncertain()
        assert (await app.model(state))["kind"] == "candidate"
        assert (root / "a.py").read_text() == "VALUE = 3\n"
    finally:
        await rt.close()


@pytest.mark.parametrize("eventually_submitted", [False, True])
async def test_cooldown_slot_is_restored_only_if_the_whole_retry_chain_was_unsubmitted(
    tmp_path, eventually_submitted
):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    calls = []

    async def handler(req):
        model = json.loads(req.content)["model"]
        calls.append(model)
        if model == "fixture":
            return httpx.Response(503, json={"error": {"message": "Provider busy"}})
        if len(calls) == 3 or len(calls) == 4 and not eventually_submitted:
            raise httpx.ConnectError("proven unsubmitted", request=req)
        value = body("chat", "done")
        value["model"] = model
        return httpx.Response(200, json=value)

    await install(rt, handler)
    try:
        assert (await rt.execute(request)).state == "succeeded"
        result = await rt.execute(next_request(request, 1))
        assert result.state == ("succeeded" if eventually_submitted else "failed")
        assert rt.records.get("model-fallback-state/cloud")[1]["remaining"] == (
            6 if eventually_submitted else 7
        )
        before = rt.records.get("model-fallback-state/cloud")
        assert await rt.execute(next_request(request, 1)) == result
        assert rt.records.get("model-fallback-state/cloud") == before
    finally:
        await rt.close()


async def test_fallback_keeps_the_exact_output_adapted_request(tmp_path):
    rt, request = await setup(tmp_path, protocol="chat", binding="cloud", endpoint_options=options())
    calls = []

    async def handler(req):
        wire = json.loads(req.content)
        calls.append(wire)
        if len(calls) == 1:
            value = body("chat", "partial")
            value["choices"][0]["finish_reason"] = "length"
            return httpx.Response(200, json=value)
        if len(calls) == 2:
            return httpx.Response(503, json={"error": {"message": "Provider unavailable"}})
        value = body("chat", "done")
        value["model"] = wire["model"]
        return httpx.Response(200, json=value)

    await install(rt, handler)
    try:
        assert (await rt.execute(request)).state == "succeeded"
        assert [c["model"] for c in calls] == ["fixture", "fixture", "gpt-6.1-terra"]
        assert calls[1]["messages"] == calls[2]["messages"] and calls[0]["messages"] != calls[1]["messages"]
        assert "substantially smaller" in calls[2]["messages"][-1]["content"]
    finally:
        await rt.close()


async def test_fallback_keeps_the_exact_caller_response_repair(config):
    from test_output_limits import runtime_fixture

    endpoint = config.local.model_copy(
        update={"retry_model": RetryModel(model="gpt-6.1-terra", reasoning_effort="high")}
    )
    config = config.model_copy(update={"local": endpoint})
    calls = []

    async def handler(req):
        wire = json.loads(req.content)
        calls.append(wire)
        if len(calls) == 2:
            return httpx.Response(503, json={"error": {"message": "Provider unavailable"}})
        value = body(
            "anthropic", "invalid reply" if len(calls) == 1 else '{"kind":"candidate","summary":"done"}'
        )
        value["model"] = wire["model"]
        return httpx.Response(200, json=value)

    rt, app, state = await runtime_fixture(config, handler)
    endpoint = rt.fallback_clients["local"].endpoint
    await rt.fallback_clients["local"].close()
    rt.fallback_clients["local"] = HTTPInference(
        endpoint, httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    try:
        assert (await app.model(state))["kind"] == "candidate"
        assert len(calls) == 3 and calls[-1]["model"] == "gpt-6.1-terra"
        assert calls[0]["messages"] != calls[1]["messages"]
        assert calls[1]["messages"] == calls[2]["messages"]
        assert rt.inference_calls_used("fixture") == 3
    finally:
        await rt.close()
