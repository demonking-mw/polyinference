"""P0 incident regressions: local boundaries, provider limits and retained evidence."""

from __future__ import annotations

import asyncio
import json
import sys
from copy import deepcopy

import httpx
import pytest
from test_model_retries import setup

from polyinference.agent.architecture import validate_local_tasks
from polyinference.agent.local_provider import sync_local_provider
from polyinference.agent.routing import allocate
from polyinference.domain import Assignment, SeniorProposal
from polyinference.os_config import OSTuning
from polyinference.primitives import canonical, digest
from polyinference.runtime.inference import CompletedBudgetExceeded, HTTPInference
from polyinference.runtime.kernel import KernelRuntime
from polyinference.runtime.storage import Records
from polyinference.system_settings import Endpoint, RuntimeConfig
from polyinference.ui_os import inspection_connection


def local_task(**changes):
    return Assignment.model_validate({
        "task_id": "one_file", "objective": "Parse one request into a result", "write_paths": ["src/parser.py"],
        "checks": ["parser"], "behavior": "Reject malformed input without mutation", "focused_check": "parser",
        "acceptance_criteria": ["Valid inputs round trip and invalid ones produce ParseError"],
        "local_contract": {"implementation_path": "src/parser.py", "inputs": "parse(raw: bytes)",
            "outputs": "Result(name: str, count: int)", "provided_symbols": ["parse(bytes) -> Result"],
            "state_ownership": "Caller owns input; result is new", "side_effects": "None",
            "errors": "ParseError on invalid UTF-8 or missing fields"}, **changes})


def runtime_config(tmp_path, **changes):
    return RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
        local={"model": "fixture"}, cloud={"model": "fixture"}, role_bindings={"worker": "local", "specialist": "cloud"},
        **changes)


def test_effective_local_plan_rejects_missing_contract_or_second_production_file(config):
    for task in [local_task(local_contract=None), local_task(behavior=None, focused_check=None),
                 local_task(write_paths=["src/parser.py", "index.html"]),
                 local_task(write_paths=["src/parser.py", "src/other.py"])]:
        with pytest.raises(ValueError, match="Local task"):
            validate_local_tasks(SeniorProposal(goal="small", tasks=[task]), config)
    task = local_task(write_paths=["src/parser.py", "tests/test_parser.py", "README.md"])
    validate_local_tasks(SeniorProposal(goal="small", tasks=[task]), config)


def test_irreducible_cloud_task_survives_zero_fraction_without_changing_grants(config):
    task = local_task(role="specialist", local_contract=None, write_paths=["src/parser.py", "src/api.py"],
                      cloud_only_reason="The transactional API transition cannot be published in separate steps")
    effective = allocate([task], [], 0)
    assert effective == [task]
    validate_local_tasks(SeniorProposal(goal="coupled", tasks=effective), config)
    with pytest.raises(ValueError, match="Cloud-only"):
        validate_local_tasks(SeniorProposal(goal="wrong binding", tasks=effective),
                             config.model_copy(update={"role_bindings": {**config.role_bindings, "specialist": "local"}}))


def test_resolved_tuning_has_no_mutable_alias_and_round_trips(tmp_path):
    config = runtime_config(tmp_path)
    original = digest(canonical(config))
    with pytest.raises(TypeError):
        config.system.tuning.tool_environment["HOME"] = "/bad"
    with pytest.raises((AttributeError, TypeError)):
        config.tuning.workspace_ignored_names.append("src")
    assert digest(canonical(config)) == original
    assert deepcopy(config.tuning) == OSTuning.model_validate_json(config.tuning.model_dump_json())


def test_one_pair_overrides_legacy_projections_and_survives_restart(tmp_path):
    from polyinference.agent.system_settings import ui_system_settings
    from polyinference.config import AgentConfig
    from polyinference.os_config import LocalTokenLimits

    ui = AgentConfig.model_validate({"system": ui_system_settings(tmp_path), "objective": "Inspect fixture"})
    assert ui.local_token_limits == LocalTokenLimits() == runtime_config(tmp_path).local_token_limits
    config = runtime_config(tmp_path, local_token_limits={"input_tokens": 49152, "output_tokens": 16384})
    restarted = RuntimeConfig.model_validate_json(config.model_dump_json())
    assert restarted.local_token_limits == config.local_token_limits
    assert restarted.local.max_context_tokens == 65536
    assert restarted.local.reserved_context_tokens == 65536 * restarted.local.max_inflight
    assert restarted.limits.max_input_tokens_per_call == 49152
    assert restarted.limits.max_output_tokens_per_call == 16384
    assert restarted.token_limits("specialist") is None
    assert "max_context_tokens" not in restarted.cloud.model_dump()
    assert "reserved_context_tokens" not in restarted.cloud.model_dump()
    changed = RuntimeConfig.model_validate({**config.model_dump(),
        "local_token_limits": {"input_tokens": 12000, "output_tokens": 2000}})
    assert changed.local.max_context_tokens == 14000 and changed.limits.max_output_tokens_per_call == 2000


@pytest.mark.parametrize("name", ["local", "cloud"])
async def test_cli_readiness_uses_the_same_pair_or_provider_owned_cloud_limits(tmp_path, monkeypatch, name):
    import polyinference.runtime.inference as module
    from polyinference.cli import probe_endpoint

    config = runtime_config(tmp_path, local_token_limits={"input_tokens": 12000, "output_tokens": 2345})
    calls = []
    async def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"model": "fixture", "usage": {"completion_tokens": 2, "total_tokens": 12},
            "choices": [{"finish_reason": "stop", "message": {"content": "ready"}}]})
    client = HTTPInference(getattr(config, name), httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(module, "HTTPInference", lambda *args, **kwargs: client)
    assert (await probe_endpoint(config, name))["reply"] == "ready"
    assert calls[0].get("max_tokens") == (2345 if name == "local" else None)


async def test_cli_readiness_does_not_bypass_the_local_input_cap(tmp_path, monkeypatch):
    import polyinference.runtime.inference as module
    from polyinference.cli import probe_endpoint

    config = runtime_config(tmp_path, local_token_limits={"input_tokens": 1, "output_tokens": 100})
    calls = []
    async def handler(request):
        calls.append(request)
        raise AssertionError("Oversized readiness input must not reach the provider")
    client = HTTPInference(config.local, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(module, "HTTPInference", lambda *args, **kwargs: client)
    with pytest.raises(ValueError, match="input token cap"):
        await probe_endpoint(config, "local")
    assert not calls


@pytest.mark.parametrize("protocol,key", [("chat", "max_tokens"), ("anthropic", "max_tokens"),
                                         ("responses", "max_output_tokens"), ("gemini", "maxOutputTokens")])
async def test_provider_wire_uses_same_local_output_cap_and_omits_cloud_cap(tmp_path, protocol, key):
    config = runtime_config(tmp_path, local_token_limits={"input_tokens": 12000, "output_tokens": 2345})
    client = HTTPInference(Endpoint(protocol=protocol, model="fixture"), httpx.AsyncClient())
    try:
        for role in ("worker", "specialist"):
            pair = config.token_limits(role)
            wire = client.prepare([{"role": "user", "content": "task"}], pair.output_tokens if pair else None)
            payload = wire["payload"].get("generationConfig", wire["payload"])
            assert payload.get(key) == (2345 if pair else None)
            assert (key in payload) == bool(pair)
    finally:
        await client.close()


@pytest.mark.parametrize("inline", [False, True])
def test_strata_startup_sync_changes_only_context_and_is_idempotent(tmp_path, inline):
    config = runtime_config(tmp_path, local_token_limits={"input_tokens": 49152, "output_tokens": 16384})
    path = tmp_path / "strata.json"
    context = ["--max-context=32000"] if inline else ["--max-context", "32000"]
    before = {"args": ["--pack", "fixture", *context], "parallel": 1, "sampling": {"temperature": 0}}
    path.write_text(json.dumps(before))
    facts = sync_local_provider(config.model_copy(update={"local_strata_config": str(path)}))
    assert facts["restart_required"]
    expected = deepcopy(before)
    expected["args"][-1] = "--max-context=65536" if inline else "65536"
    assert json.loads(path.read_text()) == expected
    assert json.loads(path.with_name(path.name + ".before-polyinference").read_text()) == before
    assert not sync_local_provider(config.model_copy(update={"local_strata_config": str(path)}))["restart_required"]


@pytest.mark.parametrize("args", [
    ["--max-context", "1000", "--max-context=2000"],
    ["--max-context=1000", "--max-context=2000"],
    ["--max-context"], ["--max-context", "--parallel", "1"],
    ["--max-context=0"], ["--max-context=invalid"],
])
def test_strata_ambiguous_or_invalid_context_leaves_launch_file_untouched(tmp_path, args):
    config = runtime_config(tmp_path)
    path = tmp_path / "strata.json"
    raw = json.dumps({"args": args})
    path.write_text(raw)
    with pytest.raises(ValueError, match="--max-context"):
        sync_local_provider(config, path)
    assert path.read_text() == raw
    assert not path.with_name(path.name + ".before-polyinference").exists()


def test_independent_inspection_uses_saved_sqlite_timeout(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    tuning = OSTuning(sqlite_timeout_seconds=0.125)
    records = Records(state / "records.sqlite", tuning=tuning)
    records.put_once("runtime/os-tuning", tuning.model_dump(mode="json"))
    records.db.close()
    with inspection_connection(state / "records.sqlite") as db:
        assert db.execute("PRAGMA busy_timeout").fetchone()[0] == 125


async def test_environment_proxy_setting_changes_actual_request_route(monkeypatch):
    paths = []
    async def serve(reader, writer):
        request = await reader.readuntil(b"\r\n\r\n")
        paths.append(request.split(b"\r\n", 1)[0].decode())
        body = b'{"model":"fixture","choices":[{"finish_reason":"stop","message":{"content":"ok"}}]}'
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                     + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.setenv(name, f"http://127.0.0.1:{port}")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setenv("no_proxy", "")
    try:
        for trust in (True, False):
            endpoint = Endpoint(model="fixture", base_url=f"http://127.0.0.1:{port}/v1")
            client = HTTPInference(endpoint, tuning=OSTuning(http_trust_environment=trust))
            try:
                assert (await client.generate([{"role": "user", "content": "hello"}], 64))["text"] == "ok"
            finally:
                await client.close()
        assert paths[0].startswith("POST http://127.0.0.1:")
        assert paths[1] == "POST /v1/chat/completions HTTP/1.1"
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.parametrize("binding,location,capped", [("local", "local", True), ("cloud", "cloud", False),
                                                   ("local", "cloud", False)])
async def test_native_complete_usage_is_not_truncation_and_cloud_has_no_cap(tmp_path, binding, location, capped):
    script = tmp_path / "native.py"
    script.write_text('''import json,sys
def send(v): print(json.dumps(v),flush=True)
for line in sys.stdin:
 m=json.loads(line); method=m.get('method')
 if method=='initialize': send({'id':m['id'],'result':{}})
 elif method=='thread/start': send({'id':m['id'],'result':{'thread':{'id':'thread'},'sandbox':{'type':'readOnly'},'approvalPolicy':'never'}})
 elif method=='turn/start':
  send({'id':m['id'],'result':{'turn':{'id':'turn'}}})
  send({'method':'item/completed','params':{'item':{'type':'agentMessage','text':'{}'}}})
  send({'method':'thread/tokenUsage/updated','params':{'threadId':'thread','turnId':'turn','tokenUsage':{'total':{'totalTokens':20200,'outputTokens':20189}}}})
  send({'method':'turn/completed','params':{'turn':{'id':'turn','status':'completed','error':None}}})
''')
    rt, request = await setup(tmp_path, protocol="codex_app_server", binding=binding,
                              endpoint_options={"command": [sys.executable, str(script)], "inference_location": location})
    config = rt.config
    try:
        result = await rt.execute(request)
        assert result.state == ("failed" if capped else "succeeded"), result
        output = json.loads(rt.artifacts.read(result.output_refs[0]))
        assert output["text"] == "{}" and output["completion"]["provider_status"] == "completed"
        assert not output.get("incomplete")
        if capped:
            assert result.error.code == CompletedBudgetExceeded.__name__
            assert result.extensions["runtime/completed-budget-exceeded"]["usage_scope"] == "native_thread_total"
        else:
            assert result.extensions["runtime/context-receipt"]["input_allowance"] is None
            assert rt.admission[binding].token_limit is None
        assert not rt.records.scan("output-retry/") and not rt.records.scan("model-retry/")
        assert rt.records.get("budget/run")[1]["reserved_or_used"] == 20200
    finally:
        await rt.close()
    reopened = await KernelRuntime(config).open()
    try:
        assert await reopened.execute(request) == result
        assert reopened.records.get("budget/run")[1]["reserved_or_used"] == 20200
    finally:
        await reopened.close()
