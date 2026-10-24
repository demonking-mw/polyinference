"""Opt-in inference simulation exercises real OS admission, accounting and recovery."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import timedelta

import httpx
import pytest
from conftest import ScriptedAgent
from pydantic import ValidationError

from polyinference.agent.inference_simulation import (
    PREFIX,
    SharedDecoder,
    SimulatedHTTPInference,
    SimulationAgentConfig,
    SimulationSettings,
    configure_simulation,
    install_simulation,
    simulation_view,
)
from polyinference.agent.services import AgentServices
from polyinference.cli import load_config
from polyinference.config import AgentConfig
from polyinference.contracts import ModelQuery
from polyinference.primitives import canonical, digest, now, operation_fingerprint
from polyinference.runtime.inference import HTTPInference
from polyinference.runtime.kernel import KernelRuntime, UncertainEffect
from polyinference.ui import RunStartError, TestUI, make_server


def test_cli_flag_is_ui_only_and_absence_preserves_plumbing(monkeypatch):
    import polyinference.cli as cli
    import polyinference.ui as ui

    monkeypatch.setattr(cli, "load_saved_credentials", lambda: None)
    calls = []
    monkeypatch.setattr(ui, "serve", lambda *args, **kwargs: calls.append((args, kwargs)))
    for flags in ([], ["--sim-inference"], ["--sim-inference", "--sim-batch", "3"]):
        monkeypatch.setattr(sys, "argv", ["polyinference", "ui", *flags])
        cli.main()
    assert calls == [((8765, None, None), {"sim_batch": None}),
                     ((8765, None, None), {"sim_batch": None, "sim_inference": True}),
                     ((8765, None, None), {"sim_batch": 3, "sim_inference": True})]
    monkeypatch.setattr(sys, "argv", ["polyinference", "run", "config.json", "--sim-inference"])
    with pytest.raises(SystemExit) as raised:
        cli.main()
    assert raised.value.code == 2


@pytest.mark.parametrize("options", [
    {"tps": 0}, {"tps": float("nan")}, {"tps": float("inf")}, {"tps": True},
    {"batch": 0}, {"batch": 17}, {"batch": 1.5}, {"batch": True},
    {"bug_rate": -1}, {"bug_rate": 101}, {"bug_rate": False},
    {"seed": -1}, {"seed": 2**53}, {"mode": "unknown"}, {"jitter": 1}, {"unexpected": 1},
])
def test_simulation_settings_reject_invalid_values(options):
    with pytest.raises(ValidationError):
        SimulationSettings.model_validate(options)


def test_shared_tps_is_not_multiplied_by_batch_and_refills_on_completion():
    clock = [0.0]
    decoder = SharedDecoder(30, clock=lambda: clock[0])
    decoder.add("a", 1)
    decoder.add("b", 1)
    clock[0] = 10
    assert decoder.tokens("a") == decoder.tokens("b") == 150
    decoder.remove("a")
    decoder.add("c", 1)
    clock[0] = 20
    assert decoder.tokens("b") == 300 and decoder.tokens("c") == 150
    decoder.remove("c")
    clock[0] = 30
    assert decoder.tokens("b") == 600
    decoder.remove("b")
    assert not decoder.active


def test_no_flag_and_normal_mode_keep_identical_configuration(config, tmp_path, monkeypatch):
    monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", "1")
    path = tmp_path / "base.json"
    path.write_text(config.model_dump_json())
    before = path.read_bytes()
    plain = TestUI(tmp_path / "plain", path)
    enabled = TestUI(tmp_path / "enabled", path, sim_inference=True)
    baseline = plain.configure_run()
    normal = enabled.configure_run(simulation={"mode": "normal"})
    assert type(normal) is type(baseline) is AgentConfig
    assert canonical(normal) == canonical(baseline)
    assert "inference_simulation" not in normal.model_dump()
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="--sim-inference"):
        plain.configure_run(simulation={"mode": "buggy"})
    assert plain.configure_run().model_dump() == baseline.model_dump()


def test_batch_resolution_saved_config_reload_and_launch_isolation(config, tmp_path, monkeypatch):
    monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", "1")
    path = tmp_path / "base.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", path, sim_inference=True, sim_batch=3)
    effective = manager.configure_run(simulation={"mode": "slow-buggy", "tps": 30, "batch": 2,
                                                 "bug_rate": 5, "seed": 123})
    assert isinstance(effective, SimulationAgentConfig)
    assert effective.max_workers == effective.local.max_inflight == effective.system.local.max_inflight == 2
    assert effective.cloud == config.cloud
    assert effective.local.protocol == "anthropic"
    assert effective.local.reserved_context_tokens >= 2 * effective.local.max_context_tokens
    saved = tmp_path / "effective.json"
    saved.write_text(effective.model_dump_json())
    assert canonical(load_config(saved)) == canonical(effective)
    assert canonical(load_config(path)) == canonical(TestUI(tmp_path / "plain", path).configuration())
    assert "inference_simulation" not in TestUI(tmp_path / "later", path).configure_run().model_dump()
    assert configure_simulation(effective, {"mode": "normal"}).__class__ is AgentConfig
    assert manager.configure_run(simulation={"mode": "normal"}).local.max_inflight == 3


async def setup(config, tmp_path, *, mode="buggy", **settings):
    options = SimulationSettings(mode=mode, bug_rate=0, batch=2, seed=1, **settings)
    # Keep real provider framing without using credentials or a remote service.
    base = config.model_copy(update={"local": config.local.model_copy(update={"protocol": "anthropic"}),
                                     "model_retry_delay_ms": 0})
    effective = SimulationAgentConfig.model_validate(
        {**base.model_dump(), "inference_simulation": options.model_dump()},
        context={"resolve_environment_capacity": False})
    rt = await KernelRuntime(effective).open()
    await install_simulation(rt, options)
    app = AgentServices(rt, effective)
    return rt, app


def request_for(app, name="worker", step="summary"):
    app.process(name, "worker")
    payload = ModelQuery(role="worker", phase="development", prompt_template_ref="text/1",
        context=app.context("Return plain text", {"identity": name}, [], name, {}), response_schema_ref="text/1",
        capability_requirements=[], temperature=0, session_ref=None)
    return app.ensure_request(name, step, payload)


async def transport(rt, handler=None, *, output_tokens=7):
    client = rt.clients["local"]
    headers = client.client.headers
    await client.client.aclose()
    calls = []

    async def respond(request):
        calls.append(json.loads(request.content))
        if handler:
            return await handler(request)
        return httpx.Response(200, json={"model": "fixture", "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "Complete real provider response"}],
            "usage": {"input_tokens": 4, "output_tokens": output_tokens}})

    client.client = httpx.AsyncClient(headers=headers, transport=httpx.MockTransport(respond))
    return calls


def force_fault(rt, request, fault):
    rt.records.put_once(PREFIX + "decision/" + request.operation_id, {
        "version": 1, "operation_id": request.operation_id, "fault": fault, "incident_started": bool(fault),
        "restart_until": None, "speed_factor": 1, "stall_seconds": 0,
    })


@pytest.mark.parametrize("fault", ["unavailable", "empty", "malformed", "cutoff"])
async def test_faults_follow_normal_outcome_paths_without_losing_real_usage(config, tmp_path, fault):
    rt, app = await setup(config, tmp_path)
    request = request_for(app)
    force_fault(rt, request, fault)
    calls = await transport(rt)
    try:
        result = await rt._execute_once(request)
        assert result.state == "failed" and result.execution_termination == "confirmed_stopped"
        assert rt.admission["local"].active == rt.admission["local"].tokens == 0
        assert not rt.uncertain()
        row = rt.records.get(PREFIX + "attempt/" + request.operation_id)[1]
        assert row["injected"] and row["phase"] == "failed"
        usage = rt.records.get("budget/process/worker")[1]["reserved_or_used"]
        if fault == "unavailable":
            assert not calls and usage == 0
            assert result.extensions["polyinference/provider-error"]["submitted"] is False
        else:
            assert len(calls) == 1 and usage == 11 and result.usage[0].value == 11
            assert rt.records.get(PREFIX + "provider/" + request.operation_id)[1]["confirmed_stopped"]
            extension = "polyinference/incomplete-generation" if fault == "cutoff" else "polyinference/model-output-error"
            assert result.extensions[extension]["simulated"] is True
    finally:
        await rt.close()


async def test_transient_fault_recovers_once_and_replay_after_restart_makes_no_calls(config, tmp_path):
    rt, app = await setup(config, tmp_path)
    effective = rt.config
    request = request_for(app)
    force_fault(rt, request, "unavailable")
    calls = await transport(rt)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded" and len(calls) == 1
        assert len(rt.records.scan(PREFIX + "decision/")) == 2
        assert rt.records.get("effect/" + request.operation_id)[1]["state"] == "failed"
        assert await rt.execute(request) == result and len(calls) == 1
        assert rt.records.get("budget/process/worker")[1]["reserved_or_used"] == 11
        assert type(rt.clients["cloud"]) is HTTPInference
    finally:
        await rt.close()
    rt = await KernelRuntime(effective).open()
    await install_simulation(rt, effective.inference_simulation)
    calls = await transport(rt)
    try:
        assert await rt.execute(request) == result and calls == []
        view = simulation_view({key: value for key, _, value in rt.records.scan(PREFIX)},
                               effective.model_dump(mode="json"))
        assert view["incidents"] == view["affected_attempts"] == 1
    finally:
        await rt.close()


@pytest.mark.parametrize("fault", ["empty", "malformed", "cutoff"])
async def test_synthetic_output_faults_use_bounded_os_recovery(config, tmp_path, fault):
    rt, app = await setup(config, tmp_path)
    request = request_for(app)
    force_fault(rt, request, fault)
    calls = await transport(rt)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded" and len(calls) == 2
        assert json.loads(rt.artifacts.read(result.output_refs[0]))["text"] == "Complete real provider response"
        assert rt.records.get("effect/" + request.operation_id)[1]["state"] == "failed"
        assert rt.records.get("budget/process/worker")[1]["reserved_or_used"] == 22
        assert len(rt.records.scan(PREFIX + "decision/")) == 2
        if fault == "cutoff":
            assert len(rt.records.scan("output-retry/")) == 1
        assert await rt.execute(request) == result and len(calls) == 2
    finally:
        await rt.close()


async def test_restart_cooldown_affects_retry_and_is_bounded(config, tmp_path, monkeypatch):
    rt, app = await setup(config, tmp_path)
    # Force incident selection only, retaining production decision/cooldown bookkeeping.
    monkeypatch.setattr("polyinference.agent.inference_simulation.random.Random.random", lambda _: 0.0)
    monkeypatch.setattr("polyinference.agent.inference_simulation.random.Random.choices", lambda *a, **k: ["restart"])
    rt.clients["local"].settings = rt.config.inference_simulation.model_copy(update={"bug_rate": 100})
    calls = await transport(rt)
    request = request_for(app)
    try:
        result = await rt.execute(request)
        assert result.state == "failed" and calls == []
        assert rt.records.get(PREFIX + "server")[1]["restart_until"] > time.time()
        decisions = [row for _, _, row in rt.records.scan(PREFIX + "decision/")]
        assert len(decisions) == 3  # initial attempt plus two native OS retries
        assert {row["fault"] for row in decisions} == {"restart", "restarting"}
        assert sum(row["incident_started"] for row in decisions) == 1
        assert rt.admission["local"].active == rt.admission["local"].tokens == 0
        assert await rt.execute(request) == result
    finally:
        await rt.close()


async def test_seeded_decisions_are_durable_and_new_attempts_have_new_identities(config, tmp_path):
    rt, app = await setup(config, tmp_path)
    client = rt.clients["local"]
    request = request_for(app)
    try:
        first = client.decision(request)
        second = client.decision(request.model_copy(update={"operation_id": "different-attempt"}))
        assert client.decision(request) == first
        assert first["operation_id"] != second["operation_id"] and first["fault"] is second["fault"] is None
        assert first["speed_factor"] != second["speed_factor"]
        assert all(0.8 <= row["speed_factor"] <= 1.2 for row in (first, second))
        assert not rt.records.scan(PREFIX + "attempt/")
    finally:
        await rt.close()


async def test_pacing_holds_admission_refills_independently_and_exceeds_network_timeout(config, tmp_path):
    config = config.model_copy(update={"local": config.local.model_copy(update={"timeout_seconds": 0.05})})
    rt, app = await setup(config, tmp_path, mode="slow-buggy", tps=200, prefill_seconds=0,
                          prefill_tps=1000000, jitter=0, stall_rate=0)
    entered = []

    async def handler(request):
        body = json.loads(request.content)
        name = "a" if '"identity": "a"' in str(body) else "b"
        # Different lengths ensure the next waiter starts before the longest finishes.
        entered.append(name)
        return httpx.Response(200, json={"model": "fixture", "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 30 if len(entered) == 1 else 90}})

    await transport(rt, handler)
    requests = [request_for(app, name) for name in ("a", "b", "c")]
    futures = [asyncio.create_task(rt._execute_once(request)) for request in requests]
    started = time.monotonic()
    try:
        await asyncio.sleep(0.15)
        assert len(entered) == rt.admission["local"].active == 2
        assert not futures[0].done() and not futures[1].done()
        while len(entered) < 3:
            await asyncio.sleep(0.01)
            assert time.monotonic() - started < 5
        assert not futures[1].done()
        results = await asyncio.gather(*futures)
        assert all(result.state == "succeeded" for result in results)
        assert time.monotonic() - started >= 0.9  # 210 output tokens / 200 shared TPS, with loose tolerance.
        assert rt.admission["local"].active == rt.admission["local"].tokens == 0
        assert not rt.clients["local"].decoder.active
        assert all(row["phase"] == "completed" for _, _, row in rt.records.scan(PREFIX + "attempt/"))
    finally:
        await asyncio.gather(*futures, return_exceptions=True)
        await rt.close()


@pytest.mark.parametrize("stop", ["cancel", "deadline", "process"])
async def test_artificial_wait_interruption_preserves_known_termination_and_actual_usage(config, tmp_path, stop):
    rt, app = await setup(config, tmp_path, mode="slow-buggy", tps=1, prefill_seconds=0,
                          prefill_tps=1000000, jitter=0, stall_rate=0)
    calls = await transport(rt)
    request = request_for(app)
    if stop == "deadline":
        request = request.model_copy(update={"deadline": now() + timedelta(seconds=0.4)})
        request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
    future = asyncio.create_task(rt._execute_once(request))
    try:
        for _ in range(100):
            if rt.records.get(PREFIX + "provider/" + request.operation_id):
                break
            await asyncio.sleep(0.01)
        else:
            pytest.fail("Provider receipt not retained before pacing")
        if stop == "cancel":
            rt.inflight[request.operation_id].cancel()
        elif stop == "process":
            rt.records.put_once("process-control/worker", {"cancel_requested": True})
        result = await asyncio.wait_for(future, 2)
        assert len(calls) == 1 and result.state == "failed"
        assert result.error.code == "SimulationInterrupted"
        assert not result.error.retryable_after_reconciliation
        assert result.execution_termination == "confirmed_stopped" and result.usage[0].value == 11
        assert not rt.uncertain() and not rt.clients["local"].decoder.active
        assert rt.admission["local"].active == rt.admission["local"].tokens == 0
    finally:
        await rt.close()


async def test_cancellation_during_real_provider_work_retains_uncertainty(config, tmp_path):
    rt, app = await setup(config, tmp_path)
    entered = asyncio.Event()

    async def handler(request):
        entered.set()
        await asyncio.Event().wait()

    await transport(rt, handler)
    request = request_for(app)
    future = asyncio.create_task(rt._execute_once(request))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        rt.inflight[request.operation_id].cancel()
        with pytest.raises(UncertainEffect):
            await future
        assert rt.uncertain() == [request.operation_id]
        assert rt.admission["local"].active == 1
        assert not rt.clients["local"].decoder.active
    finally:
        await rt.close()


async def test_cancellation_racing_with_terminal_rejection_keeps_known_provider_facts(config, tmp_path):
    rt, app = await setup(config, tmp_path, mode="slow-buggy", prefill_seconds=10)
    entered, release = asyncio.Event(), asyncio.Event()

    async def handler(request):
        entered.set()
        await release.wait()
        return httpx.Response(401, json={"error": {"message": "fixture rejection"}})

    await transport(rt, handler)
    request = request_for(app)
    future = asyncio.create_task(rt._execute_once(request))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        release.set()
        for _ in range(20):
            await asyncio.sleep(0)  # Deliver the terminal rejection while the prefill timer is still asleep.
        rt.inflight[request.operation_id].cancel()
        result = await asyncio.wait_for(future, 2)
        assert result.state == "failed" and result.error.code == "ProviderError"
        assert result.extensions["polyinference/provider-error"]["http_status"] == 401
        assert not rt.uncertain() and rt.admission["local"].active == 0
    finally:
        release.set()
        await rt.close()


def test_output_token_fallback_is_explicit_and_never_uses_input_tokens():
    assert SimulatedHTTPInference.output_tokens({"text": "12345678", "usage": {"total_tokens": 999}}) == (
        2, "estimated_utf8_bytes_div_4")
    assert SimulatedHTTPInference.output_tokens({"text": "long", "usage": {"output_tokens": 3}}) == (
        3, "provider_reported")


async def test_ui_start_persists_options_and_history_without_changing_next_launch(config, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-only")
    path = tmp_path / "base.json"
    path.write_text(config.model_dump_json())
    captured = []

    async def runner(effective):
        captured.append(effective)
        rt = await KernelRuntime(effective).open()
        await rt.close()
        return {"outcome": "finished"}

    manager = TestUI(tmp_path / "ui", path, runner=runner, sim_inference=True)
    run_id = manager.start(simulation={"mode": "slow-buggy", "tps": 30, "batch": 2, "bug_rate": 5, "seed": 7})
    for _ in range(100):
        if manager.active is None:
            break
        await asyncio.sleep(0.02)
    document = await manager.export(run_id)
    assert captured[0].inference_simulation.seed == document["configuration"]["inference_simulation"]["seed"] == 7
    assert "inference_simulation" not in TestUI(tmp_path / "later", path).configuration().model_dump()
    before = (tmp_path / "ui" / "runs" / run_id / "config.json").read_bytes()
    other = TestUI(tmp_path / "other", state=manager.runs[run_id]["state"], sim_inference=True, sim_batch=3)
    assert (await other.export(next(iter(other.runs))))["configuration"] == document["configuration"]
    assert (tmp_path / "ui" / "runs" / run_id / "config.json").read_bytes() == before
    with pytest.raises(RunStartError, match="--sim-inference"):
        TestUI(tmp_path / "plain", path).start(simulation={"mode": "buggy"})


async def test_ui_http_flag_controls_are_absent_without_flag_and_reject_unenabled_payload(config, tmp_path):
    import threading

    path = tmp_path / "base.json"
    path.write_text(config.model_dump_json())
    for enabled in (False, True):
        manager = TestUI(tmp_path / str(enabled), path, sim_inference=enabled)
        server = make_server(manager, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            async with httpx.AsyncClient(base_url=base) as client:
                listing = (await client.get("/api/runs")).json()
                assert ("inference_simulation" in listing) is enabled
                response = await client.post("/api/run", headers={"Origin": base},
                                             json={"simulation": {"mode": "invalid" if enabled else "buggy"}})
                assert response.status_code == 400
                assert ("--sim-inference" if not enabled else "mode") in response.json()["error"]
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


async def test_plain_runtime_uses_unmodified_adapter_and_configuration_pin(config):
    rt = await KernelRuntime(config).open()
    try:
        assert type(rt.clients["local"]) is HTTPInference
        assert not hasattr(rt.clients["local"], "generate_operation")
        assert rt.records.get("runtime/config")[1]["digest"] == digest(canonical(config))
        assert not rt.records.scan(PREFIX)
    finally:
        await rt.close()


async def test_real_provider_failure_is_not_relabelled_as_a_simulated_fault(config, tmp_path):
    rt, app = await setup(config, tmp_path, mode="slow-buggy", prefill_seconds=1)
    request = request_for(app)
    force_fault(rt, request, "empty")

    async def handler(request):
        return httpx.Response(401, json={"error": {"message": "fixture rejection"}})

    await transport(rt, handler)
    try:
        result = await rt._execute_once(request)
        assert result.error.code == "ProviderError"
        assert result.extensions["polyinference/provider-error"]["http_status"] == 401
        assert "simulated" not in result.extensions["polyinference/provider-error"]
        row = rt.records.get(PREFIX + "attempt/" + request.operation_id)[1]
        assert row["phase"] == "failed" and not row["injected"]
        assert rt.admission["local"].active == 0
    finally:
        await rt.close()


@pytest.mark.parametrize("enabled", [False, True])
async def test_real_coding_execute_installs_only_when_explicit_and_completes(config, monkeypatch, enabled):
    import polyinference.cli as cli

    script = ScriptedAgent()
    selected = config.model_copy(update={"local": config.local.model_copy(update={"protocol": "anthropic"})})
    if enabled:
        selected = SimulationAgentConfig.model_validate({**selected.model_dump(),
            "inference_simulation": {"mode": "buggy", "bug_rate": 0, "seed": 5}},
            context={"resolve_environment_capacity": False})
    observed = []

    async def handler(request):
        body = json.loads(request.content)
        result = await script.generate([{"role": "system", "content": body["system"]}, *body["messages"]],
                                       body["max_tokens"])
        return httpx.Response(200, json={"model": "fixture", "stop_reason": "end_turn",
            "content": [{"type": "text", "text": result["text"]}],
            "usage": {"input_tokens": 10, "output_tokens": 10}})

    class FixtureRuntime(KernelRuntime):
        async def open(self):
            await super().open()
            await self.clients["cloud"].close()
            self.clients["cloud"] = script
            observed.append(self)
            return self

        async def close(self):
            if not self.closing:
                assert isinstance(self.clients["local"], SimulatedHTTPInference) is enabled
                assert bool(self.records.scan(PREFIX)) is enabled
                assert self.records.get("app/run")[1]["status"] == "completed"
                assert len(self.records.scan("report/")) == 2
            await super().close()

    monkeypatch.setattr(cli, "KernelRuntime", FixtureRuntime)
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **kwargs: httpx.MockTransport(handler))
    outcome = await cli.execute(selected, save_history=False)
    assert outcome["status"] == "completed" and len(observed) == 1
