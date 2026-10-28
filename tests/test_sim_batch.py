"""Invocation-only coding UI presets; generic admission remains provider-neutral."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys

import httpx
import pytest
from conftest import ScriptedAgent

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.config import AgentConfig
from polyinference.contracts import ModelQuery
from polyinference.runtime.kernel import KernelRuntime
from polyinference.runtime.storage import Records
from polyinference.ui import RunStartError, TestUI


@pytest.mark.parametrize("argument", [None, "1", "2", "16", "0", "-1", "17", "1.5", "bad"])
def test_cli_sim_batch_scope_and_plumbing(argument, monkeypatch):
    import polyinference.cli as cli
    import polyinference.ui as ui

    captured = []
    monkeypatch.setattr(cli, "load_saved_credentials", lambda: None)
    monkeypatch.setattr(ui, "serve", lambda *args, **kwargs: captured.append((args, kwargs)))
    arguments = ["polyinference", "ui", "--port", "8766", "--config", "settings.json", "--state", "old"]
    monkeypatch.setattr(sys, "argv", arguments + ([] if argument is None else ["--sim-batch", argument]))
    if argument in {"0", "-1", "17", "1.5", "bad"}:
        with pytest.raises(SystemExit) as raised:
            cli.main()
        assert raised.value.code == 2 and not captured
    else:
        cli.main()
        assert captured == [((8766, "settings.json", "old"), {"sim_batch": int(argument) if argument else None})]


def test_separate_cli_invocations_do_not_retain_the_flag():
    script = ("import polyinference.cli as c, polyinference.ui as u; c.load_saved_credentials=lambda:None; "
              "u.serve=lambda *a,**kw:print(kw['sim_batch']); c.main()")
    first = subprocess.check_output([sys.executable, "-c", script, "ui", "--sim-batch", "2"], text=True)
    second = subprocess.check_output([sys.executable, "-c", script, "ui"], text=True)
    assert first.strip() == "2" and second.strip() == "None"


@pytest.mark.parametrize("ambient", [None, "1", "malformed"])
@pytest.mark.parametrize("slots", [1, 2, 16])
def test_simulation_preserves_complete_endpoint_and_precedence(config, tmp_path, monkeypatch, ambient, slots):
    if ambient is None:
        monkeypatch.delenv("POLYINFERENCE_LOCAL_BATCH_SIZE", raising=False)
    else:
        monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", ambient)
    source = config.model_dump(mode="json")
    local = {**source.pop("local"), "protocol": "anthropic", "model": "custom-haiku",
             "base_url": "https://custom.example/v1", "api_key_env": "CUSTOM_ANTHROPIC",
             "timeout_seconds": 123, "estimated_microusd_per_token": 0.7,
             "max_context_tokens": 48000, "reserved_context_tokens": 500000}
    source["system"] = {"local": local, "cloud": source.pop("cloud"), "max_workers": source.pop("max_workers")}
    path = tmp_path / "grouped.json"
    text = json.dumps(source)
    path.write_text(text)
    environment = dict(os.environ)
    manager = TestUI(tmp_path / "sim", path, sim_batch=slots)
    for effective in (manager.configuration(), manager.configure_run(), manager.configuration().system):
        assert effective.max_workers == effective.local.max_inflight == slots
        assert effective.local.reserved_context_tokens == max(500000, slots * 48000)
        assert effective.local.model_dump(exclude={"max_inflight", "reserved_context_tokens"}) == {
            k: v for k, v in local.items() if k not in {"max_inflight", "reserved_context_tokens"}}
        assert effective.cloud.model_dump(mode="json") == source["system"]["cloud"]
        assert effective.limits == config.limits
    assert path.read_text() == text and dict(os.environ) == environment
    normal = TestUI(tmp_path / "normal", path)
    if ambient == "malformed":
        with pytest.raises(ValueError):
            normal.configuration()
    else:
        assert normal.configuration().max_workers == config.max_workers
        assert normal.configuration().local.max_inflight == (1 if ambient else local["max_inflight"])


def test_non_anthropic_replacement_is_complete_and_does_not_change_base(config, tmp_path):
    path = tmp_path / "base.json"
    path.write_text(config.model_dump_json())
    selected = TestUI(tmp_path / "ui", path, sim_batch=2)
    effective = selected.configuration()
    assert effective.local.protocol == "anthropic" and effective.local.model == "claude-haiku-5-5"
    assert effective.local.api_key_env == "ANTHROPIC_API_KEY"
    assert effective.local.physical_location == "cloud"
    assert effective.cloud == config.cloud and effective.role_bindings["worker"] == "local"
    assert "Remote Anthropic simulation" in selected.simulation_label(effective)
    assert TestUI(tmp_path / "other", path).configuration().local == config.local


async def test_simulation_does_not_reconfigure_imported_history(tmp_path):
    state = tmp_path / "old" / "state"
    state.mkdir(parents=True)
    records = Records(state / "records.sqlite")
    records.put_once("runtime/config", {"digest": "old-pin"})
    records.db.close()
    old = {"local": {"model": "old-model", "max_inflight": 1}, "max_workers": 1}
    path = state.parent / "config.json"
    text = json.dumps(old)
    path.write_text(text)
    manager = TestUI(tmp_path / "ui", state=state, sim_batch=2)
    document = await manager.export(next(iter(manager.runs)))
    assert document["configuration"] == old and document["records"]["runtime/config"]["digest"] == "old-pin"
    assert path.read_text() == text


@pytest.mark.parametrize("credential", [None, "", "   "])
async def test_missing_simulation_credentials_are_saved_start_failures(tmp_path, monkeypatch, credential):
    if credential is None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_API_KEY", credential)
    manager = TestUI(tmp_path / "ui", sim_batch=2)
    with pytest.raises(RunStartError, match="nonempty credential") as raised:
        manager.start()
    assert manager.active is None
    metadata = raised.value.metadata
    assert metadata["failure_stage"] == "startup"
    saved = await manager.export(metadata["id"])
    assert saved["configuration"]["max_workers"] == saved["configuration"]["local"]["max_inflight"] == 2
    assert "sim_batch" not in saved["configuration"]
    assert "nonempty credential" in saved["run"]["error"]


@pytest.mark.parametrize("slots", [1, 2])
async def test_simulated_worker_requests_overlap_to_capacity_and_refill_without_pairing(tmp_path, monkeypatch, slots):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret")
    monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", "1")
    config = TestUI(tmp_path / "ui", sim_batch=slots).configuration().model_copy(
        update={"state_directory": str(tmp_path / "runtime-state")})
    runtime = await KernelRuntime(config).open()
    app = AgentServices(runtime, config)
    entered, released = [], {name: asyncio.Event() for name in ("a", "b", "c")}
    changed = asyncio.Event()
    active = peak = 0
    client = runtime.clients["local"]
    headers = client.client.headers
    await client.client.aclose()

    async def handler(request):
        nonlocal active, peak
        body = json.loads(request.content)
        pinned = next(message["content"] for message in body["messages"] if "Pinned application inputs:" in message["content"])
        name = json.loads(pinned.split("Pinned application inputs:\n", 1)[1])["identity"]
        assert str(request.url) == "https://api.anthropic.com/v1/messages"
        assert request.headers["x-api-key"] == "fixture-secret" and request.headers["anthropic-version"] == "2023-06-01"
        assert body["model"] == "claude-haiku-5-5"
        assert body["max_tokens"] == config.model_output_target_tokens == 4096
        assert body["system"].startswith("Independent bounded task") and body["messages"][-1]["role"] == "user"
        active += 1
        peak = max(peak, active)
        entered.append(name)
        changed.set()
        await released[name].wait()
        active -= 1
        events = [
            {"type": "message_start", "message": {"id": "msg-" + name, "model": body["model"],
                                                   "usage": {"input_tokens": 20}}},
            {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
            {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": name}},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 1}},
            {"type": "message_stop"},
        ]
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
                              content=b"".join(b"data: " + json.dumps(e).encode() + b"\n\n" for e in events))

    client.client = httpx.AsyncClient(headers=headers, transport=httpx.MockTransport(handler))
    futures = []

    async def wait_count(count):
        while len(entered) < count:
            if all(future.done() for future in futures):
                raise AssertionError([str(future.exception()) if future.exception() else future.result()[1]
                                      for future in futures])
            changed.clear()
            await asyncio.wait_for(changed.wait(), 5)

    try:
        for name in ("a", "b", "c"):
            pid = "worker-" + name
            app.process(pid, "worker")
            payload = ModelQuery(role="worker", phase="development", prompt_template_ref="task/1",
                context=app.context("Independent bounded task", {"identity": name}, [], pid, {}), response_schema_ref="text/1",
                capability_requirements=[], temperature=0, session_ref=None)
            futures.append(asyncio.create_task(app.effect(pid, "independent", payload)))
            futures[-1].add_done_callback(lambda _: changed.set())
        await wait_count(slots)
        assert len(entered) == slots and runtime.admission["local"].active == slots
        # Releasing either slot must admit the next request while another remains held.
        released[entered[-1]].set()
        await wait_count(slots + 1)
        assert len(entered) == slots + 1 and peak == slots
        for event in released.values():
            event.set()
        outcomes = await asyncio.gather(*futures)
        assert all(result.state == "succeeded" for result, _ in outcomes)
        assert {output["text"] for _, output in outcomes} == {"a", "b", "c"}
        assert runtime.admission["local"].active == runtime.admission["local"].tokens == 0
        assert config.system.local.max_inflight == slots
    finally:
        for event in released.values():
            event.set()
        for future in futures:
            if not future.done():
                future.cancel()
        await asyncio.gather(*futures, return_exceptions=True)
        await runtime.close()


async def test_simulation_runs_two_real_worker_assignments_and_persists_effective_settings(config, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret")
    path = tmp_path / "base.json"
    source = config.model_copy(update={"local": config.local.model_copy(update={"protocol": "anthropic",
        "base_url": "https://api.anthropic.com/v1", "api_key_env": "ANTHROPIC_API_KEY"})})
    path.write_text(source.model_dump_json())
    scripted = ScriptedAgent()

    async def handler(request):
        body = json.loads(request.content)
        reply = await scripted.generate([{"role": "system", "content": body["system"]}, *body["messages"]], body["max_tokens"])
        return httpx.Response(200, json={"model": body["model"], "stop_reason": "end_turn",
            "content": [{"type": "text", "text": reply["text"]}], "usage": {"input_tokens": 10, "output_tokens": 10}})

    async def runner(effective):
        runtime = await KernelRuntime(effective).open()
        client = runtime.clients["local"]
        headers = client.client.headers
        await client.client.aclose()
        client.client = httpx.AsyncClient(headers=headers, transport=httpx.MockTransport(handler))
        await runtime.clients["cloud"].close()
        runtime.clients["cloud"] = scripted
        try:
            app = AgentServices(runtime, effective)
            await ProjectAgent(app).run()
            assert app.get("app/run")["status"] == "completed"
            assert len(runtime.records.scan("report/")) == 2 and scripted.peak == 2
            return app.get("app/run")
        finally:
            await runtime.close()

    manager = TestUI(tmp_path / "ui", path, runner=runner, sim_batch=2)
    run_id = manager.start()
    for _ in range(1000):
        if manager.active is None:
            break
        await asyncio.sleep(0.02)
    assert manager.active is None and manager.runs[run_id]["error"] is None
    document = await manager.export(run_id)
    assert document["run"]["status"] == "completed"
    assert document["configuration"]["max_workers"] == document["configuration"]["local"]["max_inflight"] == 2
    assert document["configuration"]["local"]["reserved_context_tokens"] >= 2 * config.local.max_context_tokens
    persisted = AgentConfig.model_validate(document["configuration"], context={"resolve_environment_capacity": False})
    assert persisted.system.local.max_inflight == 2
    assert len(document["reports"]) == 2 and scripted.peak == 2


@pytest.mark.parametrize("status", [401, 404, 429])
async def test_simulation_provider_rejections_remain_visible_and_sanitized(tmp_path, monkeypatch, status):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret")

    async def runner(config):
        from polyinference.runtime.inference import HTTPInference

        adapter = HTTPInference(config.local)
        headers = adapter.client.headers
        await adapter.client.aclose()
        adapter.client = httpx.AsyncClient(headers=headers, transport=httpx.MockTransport(
            lambda request: httpx.Response(status, json={"error": {"message": "api_key=fixture-secret"}})))
        try:
            await adapter.generate([{"role": "user", "content": "Task"}], 10)
        finally:
            await adapter.close()

    manager = TestUI(tmp_path / "ui", runner=runner, sim_batch=2)
    run_id = manager.start()
    for _ in range(500):
        if manager.active is None:
            break
        await asyncio.sleep(0.01)
    assert manager.active is None
    document = await manager.export(run_id)
    assert document["run"]["status"] == "failed"
    assert str(status) in document["run"]["error"]
    assert "fixture-secret" not in json.dumps(document)
