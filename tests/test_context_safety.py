"""I/O guarantees are shared by coding, non-coding, local and cloud callers."""

from __future__ import annotations

import json

import httpx
import pytest
from test_model_retries import body, install, setup

from polyinference.config import AgentConfig
from polyinference.contracts import ContextPart
from polyinference.primitives import canonical, operation_fingerprint
from polyinference.runtime.context import context_with_parts
from polyinference.runtime.inference import HTTPInference, IncompleteGeneration, ModelResponseError
from polyinference.system_settings import ContextPolicy, InferenceSafety, RuntimeConfig


def with_parts(rt, request, parts, policy=None):
    context = context_with_parts(request.payload.context, parts)
    extensions = dict(request.extensions)
    if policy is not None:
        extensions["runtime/context-policy"] = policy
    request = request.model_copy(update={"payload": request.payload.model_copy(update={"context": context}),
                                         "extensions": extensions})
    return request.model_copy(update={"intent_digest": operation_fingerprint(request)})


def part(rt, request, name, text, *, required=True, compactable=False, kind="data", call_id=None):
    return ContextPart(part_id=name, content=rt.artifacts.put(text.encode(), request.scope),
        part_kind=kind, trust="retrieved", source_ref=name, required=required,
        compactable=compactable, call_id=call_id)


@pytest.mark.parametrize("binding", ["local", "cloud"])
@pytest.mark.parametrize("automatic", [False, True])
async def test_manual_and_automatic_overflow_preserve_pins_and_complete_pairs(tmp_path, binding, automatic):
    rt, request = await setup(tmp_path, binding=binding)
    pinned = part(rt, request, "constraints", "Never discard this constraint")
    call = part(rt, request, "call", '"\\\n' * 9000, required=False, kind="tool_call", call_id="pair")
    result = part(rt, request, "result", "historical result", required=False, kind="tool_result", call_id="pair")
    current = part(rt, request, "current", "Respond now")
    request = with_parts(rt, request, [pinned, call, result, current], {"auto_deal_context": automatic})
    sent = []
    async def handler(http_request):
        payload = json.loads(http_request.content)
        sent.append(payload)
        assert "Never discard this constraint" in str(payload)
        assert "historical result" not in str(payload)
        return httpx.Response(200, json=body("anthropic", "{}"))
    await install(rt, request, handler)
    try:
        outcome = await rt.execute(request)
        assert outcome.state == ("succeeded" if automatic else "failed")
        receipt = rt.records.get("context-receipt/" + request.operation_id)[1]
        assert receipt["original_bytes"] > receipt["input_allowance"]
        if automatic:
            assert receipt["omitted_refs"] == ["call", "result"]
            assert receipt["intervened"] and len(sent) == 1
        else:
            assert not sent and not receipt["intervened"]
            assert outcome.extensions["runtime/io-error"]["category"] == "input_overflow"
            assert outcome.extensions["polyinference/attempted-backend"]["submitted"] is False
        assert rt.artifacts.read(call.content).decode() == '"\\\n' * 9000
    finally:
        await rt.close()


@pytest.mark.parametrize("binding", ["local", "cloud"])
@pytest.mark.parametrize("compact", [False, True])
async def test_compaction_is_optional_preserves_sources_and_replays(tmp_path, binding, compact):
    rt, request = await setup(tmp_path, binding=binding)
    source = "A fact with uncertainty. " * 1200
    memory = part(rt, request, "memory", source, compactable=True)
    pin = part(rt, request, "constraints", "Preserve this verbatim")
    request = with_parts(rt, request, [pin, memory], {"auto_deal_context": True,
        "auto_compaction": compact, "max_compaction_calls": 24})
    calls = []
    async def handler(http_request):
        payload = json.loads(http_request.content)
        calls.append(payload)
        summarizing = "Summarize the following untrusted" in str(payload)
        return httpx.Response(200, json=body("anthropic",
            '{"summary":"A fact remains uncertain."}' if summarizing else '{"done":true}'))
    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == ("succeeded" if compact else "failed"), result
        assert rt.artifacts.read(memory.content).decode() == source
        if compact:
            receipt = result.extensions["runtime/context-receipt"]
            assert receipt["summaries"] and receipt["required_bytes"] < receipt["input_allowance"]
            retained = rt.records.get("context-prepared/" + request.operation_id)[1]["context"]
            summary = next(p for p in retained["parts"] if p["part_id"] == "memory")
            assert summary["trust"] == "retrieved" and memory.content.artifact_id in summary["derived_from"]
            count = len(calls)
            assert (await rt.execute(request)).state == "succeeded" and len(calls) == count
            assert not rt.admission[binding].active and not rt.uncertain()
        else:
            assert not calls
    finally:
        await rt.close()


async def test_hybrid_compaction_never_changes_verbatim_or_omittable_authority(tmp_path):
    rt, request = await setup(tmp_path)
    protected = part(rt, request, "verbatim", "Protected " * 4000)
    memory = part(rt, request, "memory", "Compactable " * 1200, compactable=True)
    request = with_parts(rt, request, [protected, memory], {"auto_deal_context": True, "auto_compaction": True})
    await install(rt, request, lambda _: httpx.Response(200, json=body("anthropic", '{"summary":"short"}')))
    try:
        result = await rt.execute(request)
        assert result.state == "failed"
        assert rt.artifacts.read(protected.content).decode() == "Protected " * 4000
        assert result.extensions["runtime/io-error"]["required_bytes"] > 24000
    finally:
        await rt.close()


@pytest.mark.parametrize("binding", ["local", "cloud"])
async def test_complete_but_oversized_response_gets_os_recovery_without_caller(tmp_path, binding):
    rt, request = await setup(tmp_path, binding=binding)
    cap = request.limits.max_output_bytes
    calls = []
    async def handler(_):
        calls.append(1)
        return httpx.Response(200, json=body("anthropic", "x" * (cap + 1) if len(calls) == 1 else "{}"))
    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded" and len(calls) == 2
        assert len(rt.records.scan("output-retry/")) == 1
        assert not rt.records.scan("recovery/")
        assert rt.records.get("effect/" + request.operation_id)[1]["state"] == "failed"
    finally:
        await rt.close()


async def test_missing_completion_signal_and_reported_over_limit_are_rejected():
    from polyinference.config import Endpoint
    adapter = HTTPInference(Endpoint(model="fixture"))
    response = httpx.Response(200)
    try:
        with pytest.raises(ModelResponseError):
            adapter.normalize({"choices": [{"message": {"content": "{}"}}]}, 10, response)
        with pytest.raises(IncompleteGeneration):
            adapter.normalize({"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}],
                               "usage": {"completion_tokens": 11}}, 10, response)
    finally:
        await adapter.close()


def test_system_settings_grouping_and_coding_defaults_have_one_source(tmp_path):
    endpoint = {"model": "fixture"}
    system = {"repository": str(tmp_path), "state_directory": str(tmp_path / "state"),
              "local": endpoint, "cloud": endpoint, "context_policy": {"auto_deal_context": True}}
    config = AgentConfig.model_validate({"system": system, "objective": "inspect", "allowed_write_paths": ["a.py"]})
    assert config.system.context_policy.auto_deal_context
    assert isinstance(config.system, RuntimeConfig)
    assert "objective" not in config.system.model_dump()
    assert config.shell_fail_fast and config.control_token_reserve == 32000
    with pytest.raises(ValueError, match="once"):
        AgentConfig.model_validate({"system": system, "repository": str(tmp_path), "objective": "inspect"})
    with pytest.raises(ValueError):
        ContextPolicy(compaction_trigger=0.5, compaction_target=0.7)
    assert InferenceSafety().require_completion_metadata


async def test_native_strict_output_guarantee_is_rejected_before_submission(tmp_path):
    rt, request = await setup(tmp_path, protocol="codex_app_server",
        inference_safety=InferenceSafety(require_output_token_enforcement=True))
    try:
        result = await rt.execute(request)
        assert result.state == "failed" and "cannot enforce" in result.error.message
        assert not result.extensions["polyinference/attempted-backend"]["submitted"]
    finally:
        await rt.close()


async def test_shell_fail_fast_reports_pipeline_failure(config):
    from test_in_place_repository import app_for
    rt, app, engine, _ = await app_for(config, shell_execution="trusted")
    try:
        await engine.initialize()
        app.process("pipe", "worker")
        from polyinference.contracts import CodeRevision
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        await app.repository.create("pipe", "pipe", "opaque", base, ["a.py"], [])
        result, output = await app.capability({"process_id": "pipe", "workspace_id": "pipe"},
            "pipeline", "shell.run", {"script": "false | cat; printf misleading-success"}, "private_write")
        assert result.state == "succeeded"  # A known nonzero command outcome is an observation.
        assert output["exit_code"] != 0 and "misleading-success" not in output["stdout"]
    finally:
        await app.repository.close_run()
        await rt.close()


@pytest.mark.parametrize("config_type", [RuntimeConfig, AgentConfig])
def test_grouped_settings_validate_types_and_environment_override(tmp_path, monkeypatch, config_type):
    system = {"repository": str(tmp_path), "local": {"model": "fixture"}, "cloud": {"model": "fixture"}}
    agent = {"objective": "inspect", "allowed_write_paths": ["a.py"]} if config_type is AgentConfig else {}
    monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", "3")
    config = config_type.model_validate({"system": system, **agent})
    assert config.local.max_inflight == 3
    assert system["local"] == {"model": "fixture"}
    for invalid in (None, [], "invalid"):
        with pytest.raises(ValueError):
            config_type.model_validate({"system": invalid, **agent})


async def test_request_context_override_wins_over_process_policy(tmp_path):
    rt, request = await setup(tmp_path)
    process = rt.records.get("process/research")[1]
    spec = rt.records.get(process["spec_ref"])[1]
    rt._update(process["spec_ref"], {**spec, "extensions": {
        "runtime/context-policy": {"auto_deal_context": True, "recovery_headroom": 12}}})
    request = with_parts(rt, request, [part(rt, request, "large", "x" * 30000, required=False)],
                         {"auto_deal_context": False})
    calls = []
    await install(rt, request, lambda _: calls.append(1))
    try:
        assert rt.contexts.policy(request).recovery_headroom == 12
        result = await rt.execute(request)
        assert result.state == "failed" and not calls
        assert not result.extensions["runtime/io-error"]["policy"]["auto_deal_context"]
    finally:
        await rt.close()


@pytest.mark.parametrize("kind", ["context-compaction", "output-retry"])
async def test_unissued_os_recovery_intents_are_rejected(tmp_path, kind):
    rt, request = await setup(tmp_path)
    try:
        if kind == "context-compaction":
            rt._update("effect/parent", {"state": "prepared", "request": request.model_dump(mode="json")})
            request = request.model_copy(update={"causal_parent_ref": "parent",
                                                "extensions": {"runtime/context-compaction": True}})
        else:
            request = request.model_copy(update={"extensions": {"runtime/output-retry": {"attempt": 1}}})
        request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
        with pytest.raises(ValueError, match="OS-issued"):
            await rt.execute(request)
        assert not rt.records.get("effect/" + request.operation_id)
    finally:
        # The parent is an authorization fixture, never an active remote job.
        if kind == "context-compaction":
            rt._update("effect/parent", {"state": "failed", "request": request.model_dump(mode="json")})
        await rt.close()


@pytest.mark.parametrize("failure", ["empty", "uncertain", "cancel", "budget"])
async def test_failed_compaction_never_submits_parent_or_retries_child(tmp_path, failure):
    from polyinference.primitives import runtime_limits
    limits = runtime_limits().model_copy(update={"max_model_calls": 1}) if failure == "budget" else runtime_limits()
    rt, request = await setup(tmp_path, limits=limits)
    source = part(rt, request, "memory", "a fact " * 4500, compactable=True)
    request = with_parts(rt, request, [source], {"auto_deal_context": True, "auto_compaction": True,
                                              "max_compaction_calls": 24})
    calls = []
    async def handler(_):
        calls.append(1)
        if failure == "uncertain":
            raise httpx.ReadError("submitted compaction disconnected")
        if failure == "cancel":
            rt.processes.cancel("research", "cancel during compaction")
        return httpx.Response(200, json=body("anthropic",
            "" if failure == "empty" else '{"summary":"short"}'))
    await install(rt, request, handler)
    try:
        outcome = await rt.execute(request)
        assert outcome.state == "failed" and len(calls) <= 1
        assert not outcome.extensions["polyinference/attempted-backend"]["submitted"]
        assert rt.artifacts.read(source.content).decode() == "a fact " * 4500
        assert not rt.records.scan("model-retry/")
        if failure == "uncertain":
            assert rt.uncertain() and rt.admission["local"].active == 1
    finally:
        await rt.close()


async def test_output_recovery_remeasures_feedback_and_packs_near_full_context(tmp_path):
    rt, request = await setup(tmp_path)
    endpoint = rt.clients["local"]
    pin = part(rt, request, "pin", "Respond under the declared protocol.")
    # Fill the original wire almost exactly; the extra OS feedback cannot fit.
    cap = request.limits.max_input_tokens_per_call
    overhead = len(canonical(
        endpoint.prepare([{"role": "user", "content": "Respond under the declared protocol."},
                          {"role": "user", "content": ""}], request.limits.max_output_tokens_per_call)))
    history = part(rt, request, "history", "h" * (cap - overhead - 10), required=False)
    request = with_parts(rt, request, [pin, history], {"auto_deal_context": True, "recovery_headroom": 0})
    calls = []
    async def handler(http_request):
        calls.append(json.loads(http_request.content))
        if len(calls) == 1:
            response = body("anthropic", '{"partial":')
            response["stop_reason"] = "max_tokens"
        else:
            response = body("anthropic", "{}")
        return httpx.Response(200, json=response)
    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded" and len(calls) == 2
        receipt = result.extensions["runtime/context-receipt"]
        assert receipt["original_bytes"] > receipt["input_allowance"]
        assert receipt["omitted_refs"] == ["history"]
        assert "Recovery attempt" in str(calls[1])
        assert rt.records.get("effect/" + request.operation_id)[1]["state"] == "failed"
    finally:
        await rt.close()


async def test_compaction_restart_reuses_completed_summaries(tmp_path, monkeypatch):
    import asyncio

    from polyinference.runtime.kernel import KernelRuntime
    rt, request = await setup(tmp_path)
    request = with_parts(rt, request, [part(rt, request, "memory", "a fact " * 4500, compactable=True)],
                         {"auto_deal_context": True, "auto_compaction": True, "max_compaction_calls": 24})
    calls = []
    async def handler(_):
        calls.append(1)
        return httpx.Response(200, json=body("anthropic", '{"summary":"short"}'))
    await install(rt, request, handler)
    compact = rt.contexts._compact
    async def interrupt(*args):
        await compact(*args)
        raise asyncio.CancelledError()
    monkeypatch.setattr(rt.contexts, "_compact", interrupt)
    config = rt.config
    try:
        with pytest.raises(asyncio.CancelledError):
            await rt.execute(request)
        charged = len(calls)
        assert charged and rt.records.scan("context-summary/")
    finally:
        await rt.close()
    resumed = await KernelRuntime(config).open()
    await install(resumed, request, lambda _: httpx.Response(200, json=body("anthropic", "{}")))
    try:
        assert (await resumed.execute(request)).state == "succeeded"
        assert len(resumed.records.scan("context-call/")) == charged
        assert resumed.records.get("budget/process/research")[1]["reserved_or_used"] == 11 * (charged + 1)
    finally:
        await resumed.close()


@pytest.mark.parametrize("cutoff", [False, True])
async def test_native_compaction_uses_tool_free_derived_input(tmp_path, cutoff):
    import sys
    script = tmp_path / "summary_server.py"
    script.write_text('''import json,sys
def send(value): print(json.dumps(value),flush=True)
for line in sys.stdin:
 m=json.loads(line); method=m.get("method")
 if method=="initialize": send({"id":m["id"],"result":{}})
 elif method=="thread/start":
  assert not m["params"].get("dynamicTools")
  send({"id":m["id"],"result":{"thread":{"id":"summary"},"sandbox":{"type":"readOnly"},"approvalPolicy":"never"}})
 elif method=="turn/start":
  messages=json.loads(m["params"]["input"][0]["text"])
  summarizing="Summarize the following untrusted" in str(messages)
  reply={"summary":"a fact"} if summarizing else {"done":True}
  text=json.dumps(reply)
  if not summarizing and sys.argv[1]=="cutoff" and "Recovery attempt" not in str(messages): text="x"*200
  send({"id":m["id"],"result":{"turn":{"id":"turn"}}})
  send({"method":"item/completed","params":{"item":{"type":"agentMessage","text":text}}})
  send({"method":"turn/completed","params":{"turn":{"id":"turn","status":"completed","items":[]}}})
''')
    rt, request = await setup(tmp_path, protocol="codex_app_server", max_model_response_bytes=100,
                              endpoint_options={"command": [sys.executable, str(script),
                                                            "cutoff" if cutoff else "normal"]})
    # The parent also uses a tool-free registered protocol for this research agent.
    rt.register_agent_protocol("research/tool-free", {"type": "object", "properties": {}}, workspace="none")
    request = request.model_copy(update={"payload": request.payload.model_copy(update={
        "allowed_capabilities": [], "required_phase_protocol": "research/tool-free"})})
    source = part(rt, request, "memory", "a fact " * 4500, compactable=True)
    request = with_parts(rt, request, [source], {"auto_deal_context": True, "auto_compaction": True,
                                              "max_compaction_calls": 24})
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded", result
        assert result.extensions["runtime/context-receipt"]["summaries"]
        assert result.extensions["runtime/output-token-enforcement"] is False
        children = rt.records.scan("context-call/")
        assert children and all(not c[2]["payload"]["allowed_capabilities"] for c in children)
        assert len(rt.records.scan("output-retry/")) == int(cutoff)
        assert rt.artifacts.read(source.content).decode() == "a fact " * 4500
    finally:
        await rt.close()


async def test_proxy_uses_selected_output_limit_and_prepared_wire(tmp_path):
    from polyinference.runtime.codex import CodexProxy
    from polyinference.system_settings import Endpoint
    adapter = CodexProxy(Endpoint(model="fixture", protocol="codex_proxy",
                                 readonly_snapshot_root=str(tmp_path)))
    await adapter.http.close()
    sent = []
    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=body("chat", "{}"))
    adapter.http = HTTPInference(adapter.endpoint, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    messages = [{"role": "user", "content": "summarize"}]
    prepared = adapter.http.prepare(messages, 23)
    try:
        assert (await adapter.generate_job(messages, tmp_path, {}, max_output=23, prepared=prepared))["text"] == "{}"
        assert sent == [prepared["payload"]] and sent[0]["max_tokens"] == 23
    finally:
        await adapter.close()


@pytest.mark.parametrize("mode", ["bytes", "reported_tokens"])
async def test_native_cutoff_recovers_only_after_confirmed_terminal_reply(tmp_path, mode):
    import sys
    script = tmp_path / "cutoff_server.py"
    script.write_text('''import json,sys
def send(value): print(json.dumps(value),flush=True)
for line in sys.stdin:
 m=json.loads(line); method=m.get("method")
 if method=="initialize": send({"id":m["id"],"result":{}})
 elif method=="thread/start":
  send({"id":m["id"],"result":{"thread":{"id":"cutoff"},"sandbox":{"type":"readOnly"},"approvalPolicy":"never"}})
 elif method=="turn/start":
  retry="Recovery attempt" in str(m["params"]["input"])
  mode=sys.argv[1]
  text="{}" if retry or mode=="reported_tokens" else "x"*200
  send({"id":m["id"],"result":{"turn":{"id":"turn"}}})
  send({"method":"item/completed","params":{"item":{"type":"agentMessage","text":text}}})
  send({"method":"thread/tokenUsage/updated","params":{"threadId":"cutoff","turnId":"turn",
        "tokenUsage":{"total":{"totalTokens":5000,"outputTokens":1 if retry else 4500 if mode=="reported_tokens" else 100}}}})
  send({"method":"turn/completed","params":{"turn":{"id":"turn","status":"completed","items":[]}}})
''')
    rt, request = await setup(tmp_path, protocol="codex_app_server", max_model_response_bytes=100,
                              endpoint_options={"command": [sys.executable, str(script), mode]})
    rt.register_agent_protocol("research/tool-free", {"type": "object", "properties": {}}, workspace="none")
    request = request.model_copy(update={"payload": request.payload.model_copy(update={
        "allowed_capabilities": [], "required_phase_protocol": "research/tool-free"})})
    request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded", result
        original = rt.records.get("effect/" + request.operation_id)[1]["result"]
        assert original["extensions"]["polyinference/incomplete-generation"]["stop_reason"] == (
            "native_response_byte_limit" if mode == "bytes" else "reported_output_limit_exceeded")
        assert len(rt.records.scan("output-retry/")) == 1
        assert not rt.records.scan("model-retry/") and not rt.uncertain()
    finally:
        await rt.close()


def test_gemini_reported_generation_tokens_include_thinking():
    from polyinference.system_settings import Endpoint
    adapter = HTTPInference.__new__(HTTPInference)
    adapter.endpoint, adapter.secrets = Endpoint(model="fixture", protocol="gemini"), []
    response = body("gemini", "{}")
    response["usageMetadata"] = {"totalTokenCount": 100, "candidatesTokenCount": 8, "thoughtsTokenCount": 3}
    with pytest.raises(IncompleteGeneration):
        adapter.normalize(response, 10, httpx.Response(200))


def test_os_settings_reference_covers_every_exported_field():
    from pathlib import Path

    from polyinference.contracts import Limits, PhaseReserve
    from polyinference.execution_contracts import Check
    from polyinference.system_settings import Endpoint
    reference = (Path(__file__).parents[1] / "design-docs/simplified-os/AGENT_SETTINGS.md").read_text()
    for model in (RuntimeConfig, Endpoint, Limits, PhaseReserve, ContextPolicy, InferenceSafety, Check):
        for field in model.model_fields:
            assert "| " + field + " |" in reference, (model.__name__, field)
    from polyinference.cli import load_config
    for example in sorted((Path(__file__).parents[1] / "examples").glob("agent.*.json")):
        original = json.loads(example.read_text())
        assert "system" in original
        assert not (set(RuntimeConfig.model_fields) & original.keys())
        config = load_config(example)
        assert config.system.context_policy.auto_deal_context


async def test_valid_tool_action_resets_consecutive_protocol_errors():
    from types import SimpleNamespace

    from polyinference.agent.worker import consume
    class Records:
        def get(self, key):
            return None
    app = SimpleNamespace(ports=SimpleNamespace(records=Records()),
                          config=SimpleNamespace(max_protocol_corrections=1),
                          append_history=lambda *args: "history")
    runtime = SimpleNamespace(context=SimpleNamespace(services=app))
    state = {"process_id": "worker", "phase": "development", "logical_step": 1,
             "protocol_errors": 1, "reply": {"kind": "action", "tool": "files.list", "arguments": {}}}
    accepted = await consume(state, runtime)
    assert accepted["route"] == "tool" and accepted["protocol_errors"] == 0
    state.update(accepted)
    state["reply"] = {"invalid": True}
    correction = await consume(state, runtime)
    assert correction["route"] == "model" and correction["protocol_errors"] == 1
