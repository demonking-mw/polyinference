"""Real HTTP test runner, checkpoint history and artifact-backed node inspection."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import signal
import threading

import httpx
import pytest
from conftest import ScriptedAgent, fixture_completion, fixture_review_reply

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.os_config import LocalTokenLimits
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.runtime.storage import Records
from polyinference.snapshots import run_summary
from polyinference.ui import TestUI, make_server, read_artifact, read_records


def test_machine_ui_defaults_preserve_project_selection_and_explicit_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "preferences"))
    monkeypatch.delenv("POLYINFERENCE_LOCAL_BATCH_SIZE", raising=False)
    directory = tmp_path / "preferences" / "polyinference"
    directory.mkdir(parents=True)
    manager = TestUI(tmp_path / "ui")
    original = manager.configuration()
    assert original.local_token_limits == LocalTokenLimits(input_tokens=96000, output_tokens=32000)
    assert original.local.max_context_tokens == original.local.reserved_context_tokens == 128000
    preferences = {
        "local": {"protocol": "anthropic", "base_url": "http://127.0.0.1:8080/v1",
                  "model": "qwen3.8-flash-next-coder-iq1_m", "api_key_env": None,
                  "inference_location": "local", "max_inflight": 1},
        "local_token_limits": {"input_tokens": 114688, "output_tokens": 16384},
        "max_workers": 1, "local_strata_config": "strata.json", "local_strata_profile": "ui-local",
    }
    path = directory / "ui-defaults.json"
    path.write_text(json.dumps(preferences))
    effective = manager.configuration()
    assert effective.local.model == preferences["local"]["model"]
    assert effective.local.api_key_env is None
    assert effective.local.max_context_tokens == effective.local.reserved_context_tokens == 131072
    assert effective.local_token_limits.input_tokens == 114688
    assert effective.limits.max_output_tokens_per_call == 16384
    assert effective.local.max_inflight == effective.max_workers == 1
    assert effective.local_strata_config == str(directory / "strata.json")
    assert effective.local_strata_profile == "ui-local"
    assert effective.cloud == original.cloud
    project = tmp_path / "other-project"
    project.mkdir()
    (project / "app.py").write_text("print('ready')\n")
    selected = manager.configure_run(str(project))
    assert selected.write_scope == "project" and selected.repository == str(project)
    assert selected.local == effective.local
    explicit = tmp_path / "explicit.json"
    explicit.write_text(original.model_dump_json())
    assert TestUI(tmp_path / "explicit-ui", config_path=explicit).configuration().local == original.local
    simulated = TestUI(tmp_path / "simulation-ui", sim_batch=2).configuration()
    assert simulated.local.inference_location == "cloud" and simulated.local.api_key_env == "ANTHROPIC_API_KEY"
    assert simulated.local.max_inflight == simulated.max_workers == 2
    assert simulated.local_token_limits == original.local_token_limits
    assert simulated.local.reserved_context_tokens == 256000
    path.write_text('{"repository": "/unexpected"}')
    with pytest.raises(ValueError, match="expected only"):
        manager.configuration()
    path.write_text('{"local": {"model": "qwen", "max_inflight": 0}}')
    with pytest.raises(ValueError):
        manager.configuration()


@pytest.mark.parametrize("initial", ["stopped", "ready", "starting", "failed", "mismatch", "start-failed"])
def test_ui_strata_autostart_reuses_and_checks_runtime(config, monkeypatch, initial):
    from polyinference.agent.local_provider import ensure_ui_local_provider

    config = config.model_copy(update={"local_strata_profile": "ui-local", "local": config.local.model_copy(
        update={"base_url": "http://127.0.0.1:8080/v1", "inference_location": "local"})})
    calls = []
    ready = {"ok": True, "state": "ready", "generation_ready": True,
             "owner_id": "a" * 32, "instance_id": "b" * 32}

    def run(argv, **kwargs):
        from subprocess import CompletedProcess

        calls.append(argv[2])
        state = initial if len(calls) == 1 else "ready"
        state = "stopped" if state == "start-failed" else state
        result = ready if state in {"ready", "mismatch"} else {"state": state}
        if argv[2] == "start" and initial == "start-failed":
            return CompletedProcess(argv, 6, json.dumps({**ready, "state": "failed", "error": "load failed"}))
        if argv[2] == "start":
            assert argv[argv.index("--die-with-pid") + 1] == str(os.getpid())
            assert argv[argv.index("--shutdown-timeout") + 1] == "10"
        if argv[2] == "stop":
            assert argv[argv.index("--if-owner-id") + 1] == ready["owner_id"]
            assert argv[argv.index("--if-instance-id") + 1] == ready["instance_id"]
            result = {"ok": True, "state": "stopped"}
        return CompletedProcess(argv, 0, json.dumps(result))

    telemetry = {"model": {"id": config.local.model, "loaded": True,
                           "context": config.local_token_limits.context_tokens},
                 "work": {"slots_effective": config.local.max_inflight}}
    if initial == "mismatch":
        telemetry["model"]["context"] += 1
    real_client = httpx.Client
    monkeypatch.setattr("polyinference.agent.local_provider.shutil.which", lambda name: "/bin/strata")
    monkeypatch.setattr("polyinference.agent.local_provider.subprocess.run", run)
    monkeypatch.setattr("polyinference.agent.local_provider.time.sleep", lambda seconds: None)
    monkeypatch.setattr("polyinference.agent.local_provider.httpx.Client", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(lambda request: httpx.Response(200, json=telemetry))))
    if initial in {"failed", "mismatch", "start-failed"}:
        with pytest.raises(ValueError):
            ensure_ui_local_provider(config)
    else:
        owned = ensure_ui_local_provider(config)
        if initial == "stopped":
            assert owned is not None
            owned.close()
            owned.close()
        else:
            assert owned is None
    assert calls == (["status", "start", "stop"] if initial in {"stopped", "start-failed"}
                     else ["status", "status"] if initial == "starting" else ["status"])
    # Remote simulation and configurations without explicit opt-in never touch Strata.
    calls.clear()
    ensure_ui_local_provider(config.model_copy(update={"local_strata_profile": None}))
    ensure_ui_local_provider(config.model_copy(update={"local": config.local.model_copy(
        update={"inference_location": "cloud"})}))
    assert not calls


@pytest.mark.parametrize("sim_batch", [None, 2])
def test_ui_prepares_provider_before_restoring_runs(config, monkeypatch, sim_batch):
    from types import SimpleNamespace

    from polyinference.ui import serve

    events = []
    monkeypatch.setattr("polyinference.ui.greeting_config", lambda root: config)
    monkeypatch.setattr("polyinference.agent.local_provider.ensure_ui_local_provider",
                        lambda selected: events.append(("provider", selected.local.model)))
    monkeypatch.setattr("polyinference.ui.TestUI", lambda *args, **kwargs: events.append(("manager", None)) or
                        SimpleNamespace(configuration=lambda: config, simulation_label=lambda c: "simulation"))
    def interrupt():
        raise KeyboardInterrupt
    monkeypatch.setattr("polyinference.ui.make_server", lambda *args: SimpleNamespace(
        server_port=8765, serve_forever=interrupt, server_close=lambda: None))
    serve(sim_batch=sim_batch)
    assert events == [("provider", config.local.model if sim_batch is None else "claude-haiku-5-5"),
                      ("manager", None)]


@pytest.mark.parametrize("ending", ["return", "interrupt", "term", "hup", "restore-failed", "bind-failed"])
def test_ui_cleans_owned_provider_on_exit_and_startup_errors(config, monkeypatch, ending):
    from types import SimpleNamespace

    from polyinference.ui import serve

    events = []
    if ending == "hup" and not hasattr(signal, "SIGHUP"):
        pytest.skip("SIGHUP is unavailable on this platform")
    signals = [signal.SIGTERM] + ([signal.SIGHUP] if hasattr(signal, "SIGHUP") else [])
    previous = {sig: signal.getsignal(sig) for sig in signals}
    monkeypatch.setattr("polyinference.ui.greeting_config", lambda root: config)
    monkeypatch.setattr("polyinference.agent.local_provider.ensure_ui_local_provider",
                        lambda config: SimpleNamespace(close=lambda: events.append("provider-close")))

    def manager(*args, **kwargs):
        if ending == "restore-failed":
            raise ValueError("restore failed")
        return object()

    def run():
        if ending == "interrupt":
            raise KeyboardInterrupt
        if ending in {"term", "hup"}:
            signum = signal.SIGTERM if ending == "term" else signal.SIGHUP
            signal.getsignal(signum)(signum, None)

    def server(*args):
        if ending == "bind-failed":
            raise OSError("port occupied")
        return SimpleNamespace(server_port=8765, serve_forever=run,
                               server_close=lambda: events.append("server-close"))

    monkeypatch.setattr("polyinference.ui.TestUI", manager)
    monkeypatch.setattr("polyinference.ui.make_server", server)
    if ending in {"restore-failed", "bind-failed"}:
        with pytest.raises((ValueError, OSError), match="failed|occupied"):
            serve()
    elif ending in {"term", "hup"}:
        with pytest.raises(SystemExit) as error:
            serve()
        assert error.value.code == 128 + (signal.SIGTERM if ending == "term" else signal.SIGHUP)
    else:
        serve()
    assert events == (["provider-close"] if ending in {"restore-failed", "bind-failed"}
                      else ["server-close", "provider-close"])
    assert all(signal.getsignal(sig) == handler for sig, handler in previous.items())


@pytest.mark.parametrize("failure", ["telemetry", "not-ready", "racing-start", "replaced-owner",
                                    "replaced-instance", "interrupt"])
def test_ui_provider_failed_start_only_cleans_captured_owner(config, monkeypatch, failure):
    from subprocess import CompletedProcess

    from polyinference.agent.local_provider import ensure_ui_local_provider

    config = config.model_copy(update={"local_strata_profile": "ui-local", "local": config.local.model_copy(
        update={"base_url": "http://127.0.0.1:8080/v1", "inference_location": "local"})})
    owner = "a" * 32
    instance = "b" * 32
    calls = []

    def run(argv, **kwargs):
        action = argv[2]
        calls.append(action)
        result = {"ok": True, "state": "stopped"}
        if action == "start":
            result = {"ok": True, "state": "ready", "generation_ready": True,
                      "owner_id": owner, "instance_id": instance}
            if failure == "racing-start":
                return CompletedProcess(argv, 6, json.dumps({"ok": False, "error": "profile already live"}))
            if failure == "not-ready":
                result["generation_ready"] = False
            if failure in {"replaced-owner", "replaced-instance", "interrupt"}:
                result["state"] = "starting"
        elif action == "status" and len(calls) > 1:
            result = {"ok": True, "state": "ready", "generation_ready": True,
                      "owner_id": owner if failure == "replaced-instance" else "c" * 32,
                      "instance_id": "d" * 32}
        elif action == "stop":
            assert argv[argv.index("--if-owner-id") + 1] == owner
            assert argv[argv.index("--if-instance-id") + 1] == instance
        return CompletedProcess(argv, 0, json.dumps(result))

    def sleep(seconds):
        if failure == "interrupt":
            raise KeyboardInterrupt

    real_client = httpx.Client
    monkeypatch.setattr("polyinference.agent.local_provider.shutil.which", lambda name: "/bin/strata")
    monkeypatch.setattr("polyinference.agent.local_provider.subprocess.run", run)
    monkeypatch.setattr("polyinference.agent.local_provider.time.sleep", sleep)
    monkeypatch.setattr("polyinference.agent.local_provider.httpx.Client", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(lambda request: httpx.Response(503))))
    with pytest.raises(KeyboardInterrupt if failure == "interrupt" else ValueError):
        ensure_ui_local_provider(config)
    assert ("stop" in calls) == (failure != "racing-start")


def test_ui_provider_cleanup_failure_is_reported_without_unguarded_retry(monkeypatch, capsys):
    from subprocess import CompletedProcess

    from polyinference.agent.local_provider import OwnedStrataRuntime

    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        return CompletedProcess(argv, 6, '{"ok":false,"error":"owner_changed"}')

    monkeypatch.setattr("polyinference.agent.local_provider.subprocess.run", run)
    owned = OwnedStrataRuntime("strata", "ui-local", "a" * 32, "b" * 32)
    owned.close()
    owned.close()
    assert len(calls) == 1
    assert "owner_changed" in capsys.readouterr().err


@pytest.mark.parametrize("termination", ["SIGINT", "SIGTERM", "SIGHUP"])
def test_ui_process_signal_closes_its_provider(tmp_path, termination):
    import subprocess
    import sys
    import time

    if not hasattr(signal, termination):
        pytest.skip(f"{termination} is unavailable on this platform")
    if sys.platform == "win32":
        pytest.skip("POSIX process signals; handler/cleanup cases run on all platforms")
    script = '''
import sys
from pathlib import Path
from types import SimpleNamespace
from polyinference import ui
from polyinference.agent import local_provider

root = Path(sys.argv[1])
ui.greeting_config = lambda root: SimpleNamespace()
local_provider.ensure_ui_local_provider = lambda config: SimpleNamespace(
    close=lambda: (root / "closed").write_text("owned provider closed"))
ui.TestUI = lambda *args, **kwargs: object()

def run():
    import time
    (root / "ready").write_text("serving")
    while True:
        time.sleep(0.05)

ui.make_server = lambda *args: SimpleNamespace(
    server_port=0, serve_forever=run, server_close=lambda: None)
ui.serve()
'''
    with (tmp_path / "process.log").open("w") as log:
        proc = subprocess.Popen([sys.executable, "-c", script, str(tmp_path)], cwd=tmp_path,
                                stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 15
            while not (tmp_path / "ready").exists() and proc.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            assert (tmp_path / "ready").exists(), (tmp_path / "process.log").read_text()
            proc.send_signal(getattr(signal, termination))
            expected = 0 if termination == "SIGINT" else 128 + getattr(signal, termination)
            assert proc.wait(timeout=15) == expected, (tmp_path / "process.log").read_text()
            assert (tmp_path / "closed").read_text() == "owned provider closed"
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=15)


async def fixture_runner(config):
    # Setup has its own broker/branch tests; this fixture covers the UI development history.
    config = config.model_copy(update={"prepare_repository": False})

    class ConfiguredScript(ScriptedAgent):
        async def generate(self, *args, **kwargs):
            result = await super().generate(*args, **kwargs)
            reply = json.loads(result["text"])
            for task in reply.get("tasks", []):
                task["checks"] = [config.checks[0].name]
                task["focused_check"] = config.checks[0].name
            result["text"] = json.dumps(reply)
            return result

    runtime = await StandaloneRuntime(config).open()
    try:
        for name in runtime.clients:
            await runtime.clients[name].close()
            runtime.clients[name] = ConfiguredScript(two=False)
        return await ProjectAgent(AgentServices(runtime, config)).run()
    finally:
        await runtime.close()


async def finished(client, run_id):
    deadline = asyncio.get_running_loop().time() + 60
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get("/api/run", params={"id": run_id})
        assert response.status_code == 200, response.text
        value = response.json()
        if value["status"] != "running":
            return value
        await asyncio.sleep(0.05)
    pytest.fail("UI fixture did not finish within 60 seconds: " + str(value))


@pytest.mark.parametrize("pause_kind", ["controller", "worker"])
@pytest.mark.parametrize("text", ["", "Keep the public signature."])
@pytest.mark.parametrize("repository_mode", ["isolated", "in_place"])
async def test_resume_run_over_http_preserves_run_and_private_work(
    config, tmp_path, monkeypatch, pause_kind, text, repository_mode
):
    config = config.model_copy(update={"repository_mode": repository_mode, "git_policy": {}})
    from polyinference.cli import apply_resume
    from polyinference.runtime.inference import ProviderError

    scripted = ScriptedAgent(two=False)
    failed = False
    release = threading.Event()
    received_configs = []

    class Provider:
        async def generate(self, messages, max_output):
            nonlocal failed
            data = json.loads(next(m["content"] for m in messages if "Pinned application inputs:" in m["content"])
                              .split("Pinned application inputs:\n", 1)[1])
            if pause_kind == "worker" and data.get("phase") == "reconciliation" and not failed:
                failed = True
                raise ProviderError("fixture invalid request", category="invalid_request", status=400)
            return await scripted.generate(messages, max_output)

        async def close(self):
            pass

    async def runner(selected, *, resume_request_ref=None):
        received_configs.append(selected.model_dump(mode="json"))
        if resume_request_ref:
            await asyncio.to_thread(release.wait)
        runtime = await StandaloneRuntime(selected).open()
        try:
            for name in runtime.clients:
                await runtime.clients[name].close()
                runtime.clients[name] = Provider()
            app = AgentServices(runtime, selected)
            engine = ProjectAgent(app)
            if resume_request_ref:
                await engine.initialize()
                await apply_resume(engine, resume_request_ref)
                with pytest.raises(ValueError, match="already been handled"):
                    await apply_resume(engine, resume_request_ref)
            elif pause_kind == "controller":
                await engine.initialize()
                app.update("app/run", {**app.get("app/run"), "status": "paused", "blocker": "User review"})
                runtime.processes.finish("controller", state="paused")
                return {"outcome": "paused"}
            return await engine.run()
        finally:
            await runtime.close()

    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=runner)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            run_id = (await client.post("/api/run", json={})).json()["id"]
            paused = await finished(client, run_id)
            assert paused["status"] == "paused", paused
            pid = "controller" if pause_kind == "controller" else "worker-1-a"
            assert paused["resume"]["allowed"] and pid in paused["resume"]["process_ids"]
            records_before = read_records(manager.runs[run_id]["state"])
            saved_config = (__import__("pathlib").Path(manager.runs[run_id]["state"]).parent / "config.json").read_bytes()
            assert (await client.post("/api/resume", json={"id": run_id, "process_id": "missing"})).status_code == 400
            assert (await client.post("/api/resume", json={"id": run_id, "process_id": pid, "text": "x" * 16001})).status_code == 400
            assert (await client.post("/api/resume", json={"id": run_id, "process_id": pid},
                                      headers={"Origin": "https://unrelated.test"})).status_code == 403
            # New-launch settings and environment must not change an old run's pin.
            manager.sim_batch = 3
            monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", "1")
            reply = await client.post("/api/resume", json={"id": run_id, "text": text, "request_id": "one-click"})
            assert reply.status_code == 202, reply.text
            request_ref = reply.json()["request_ref"]
            assert reply.json()["id"] == run_id and reply.json()["process_id"] is None
            duplicate = await client.post("/api/resume", json={"id": run_id, "text": text, "request_id": "one-click"})
            assert duplicate.status_code == 202 and duplicate.json()["request_ref"] == request_ref
            conflicting = await client.post("/api/resume", json={"id": run_id, "request_id": "another-click"})
            assert conflicting.status_code == 400 and "active run" in conflicting.json()["error"]
            release.set()
            completed = await finished(client, run_id)
            assert completed["status"] == "completed", completed
            assert len(manager.runs) == 1 and received_configs[0] == received_configs[1]
            state = __import__("pathlib").Path(manager.runs[run_id]["state"])
            assert (state.parent / "config.json").read_bytes() == saved_config
            records = read_records(state)
            assert records[request_ref]["text"] == text
            assert records["resume-outcome/" + request_ref]["state"] == "applied"
            assert records["app/run"]["steering_received"] == records["app/run"]["steering_applied"] == bool(text)
            result_path = config.repo_path / "a.py" if repository_mode == "in_place" else state / "result/a.py"
            assert result_path.read_text() == "VALUE = 2\n"
            writes = [v for k, v in records.items() if k.startswith("effect/")
                      and v["request"]["payload"].get("capability_id") == "files.write"]
            assert len(writes) == 1, "Resume must not repeat the completed private edit"
            for key, value in records_before.items():
                if key.startswith("effect/") and value["state"] == "failed":
                    assert records[key] == value
            assert (await client.post("/api/resume", json={"id": run_id, "process_id": pid})).status_code == 400
    finally:
        release.set()
        for _ in range(200):
            if not manager.active:
                break
            await asyncio.sleep(0.02)
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("failure", ["unknown", "pin", "thread"])
async def test_ui_resume_preserves_unknown_effects_and_exposes_rejection(config, tmp_path, monkeypatch, failure):
    runtime = await StandaloneRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        await ProjectAgent(app).initialize()
        run = app.get("app/run")
        program = {**run["program"], "program_version": "incompatible-fixture"} if failure == "pin" else run["program"]
        app.update("app/run", {**run, "status": "paused", "program": program})
        runtime.processes.finish("controller", state="paused")
        if failure == "unknown":
            from polyinference.contracts import ModelQuery

            payload = ModelQuery(role="senior", phase="review", prompt_template_ref="prompt/1",
                                 context=app.context("Review", {}, [], "controller", {}),
                                 response_schema_ref="senior/1", capability_requirements=[], temperature=0, session_ref=None)
            unknown = app.ensure_request("controller", "unknown", payload)
            runtime.records.put_once("effect/" + unknown.operation_id,
                                     {"state": "uncertain", "result": None, "request": unknown.model_dump(mode="json")})
    finally:
        await runtime.close()
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, state=config.state_path)
    run_id = next(iter(manager.runs))
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    if failure == "thread":
        original = threading.Thread.start

        def fail_start(selected):
            if selected.name == "polyinference-test":
                raise RuntimeError("fixture thread launch failed")
            return original(selected)

        monkeypatch.setattr(threading.Thread, "start", fail_start)
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            response = await client.post("/api/resume", json={"id": run_id, "process_id": "controller",
                                                             "text": "Preserve the source."})
            if failure == "unknown":
                assert response.status_code == 202
                view = await finished(client, run_id)
                assert "does not support automatic recovery" in view["resume"]["error"]
                records = read_records(config.state_path)
                assert records["effect/" + unknown.operation_id]["state"] == "uncertain"
                assert records["effect/" + unknown.operation_id]["result"] is None
                assert records["resume-progress/" + response.json()["request_ref"]]["state"] == "failed"
            elif failure == "pin":
                assert response.status_code == 202, response.text
                view = await finished(client, run_id)
                assert view["status"] == "paused"
                assert "pinned implementation" in view["resume"]["error"]
                request_ref = response.json()["request_ref"]
                records = read_records(config.state_path)
                assert records["resume-outcome/" + request_ref]["state"] == "rejected"
                assert records["app/run"]["steering_received"] == 0
                assert (tmp_path / "ui/runs" / run_id / "ui-run.json").is_file()
            else:
                assert response.status_code == 400 and "thread launch failed" in response.json()["error"]
                assert manager.active is None
                records = read_records(config.state_path)
                key = manager.runs[run_id]["last_resume_request"]
                assert records["resume-outcome/" + key]["state"] == "rejected"
                assert records["app/run"]["status"] == "paused"
                assert records["app/run"]["steering_received"] == 0
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("logging_failure", [False, True])
@pytest.mark.parametrize("runner_failure", [False, True])
async def test_terminal_reporting_never_replaces_runner_result(config, monkeypatch, logging_failure, runner_failure):
    from polyinference.ui import run_with_terminal_events

    captured, warnings = [], []

    def emit(run_id, message):
        captured.append(message)
        if logging_failure:
            raise BrokenPipeError("closed terminal")

    monkeypatch.setattr("polyinference.ui.terminal_event", emit)

    async def runner(selected):
        records = Records(selected.state_path / "records.sqlite")
        try:
            records.put_once("effect/operation-id", {
                "state": "uncertain", "result": None,
                "diagnostic": "original native execution failure",
            })
        finally:
            records.db.close()
        await asyncio.sleep(0.01)
        if runner_failure:
            raise RuntimeError("original execution exception")
        return {"outcome": "paused"}

    if runner_failure:
        with pytest.raises(RuntimeError, match="original execution exception"):
            await run_with_terminal_events(runner, config, "fixture", warnings)
    else:
        assert await run_with_terminal_events(runner, config, "fixture", warnings) == {"outcome": "paused"}
    assert any("original native execution failure" in message for message in captured)
    assert bool(warnings) == logging_failure


def test_summary_preserves_durable_pause_and_resolves_original_blocker():
    records = {
        "app/run": {"status": "paused", "blocker": "operation-id"},
        "effect/operation-id": {"state": "uncertain", "result": None,
                                "diagnostic": "original native execution failure"},
    }
    summary = run_summary({"error": "secondary reporter error"}, records, {}, cost={})
    assert summary["status"] == "paused"
    assert summary["error"] == summary["blocker_detail"] == "original native execution failure"
    assert summary["blocker"] == "operation-id"
    assert run_summary({"error": "startup failed"}, {}, {}, cost={})["status"] == "failed"


async def test_ui_exports_original_failure_and_separate_reporting_errors(config, tmp_path, monkeypatch):
    from polyinference.runtime.adapter import UncertainEffect

    def broken_terminal(*args):
        raise BrokenPipeError("closed terminal")

    monkeypatch.setattr("polyinference.ui.terminal_event", broken_terminal)

    async def runner(selected):
        records = Records(selected.state_path / "records.sqlite")
        try:
            records.compare_and_publish({"app/run": 0, "effect/operation-id": 0}, {
                "app/run": {"status": "paused", "blocker": "operation-id"},
                "effect/operation-id": {
                    "state": "uncertain", "result": None, "diagnostic": "original native execution failure",
                    "native_diagnostics": {"received_events": 2200, "received_bytes": 100000},
                    "request": {"operation_id": "operation-id", "payload": {"kind": "agent_job"}},
                },
            })
        finally:
            records.db.close()
        raise UncertainEffect("operation-id")

    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=runner)
    run_id = manager.start()
    for _ in range(200):
        if not manager.active:
            break
        await asyncio.sleep(0.02)
    assert manager.active is None
    view = await manager.view(run_id)
    assert view["status"] == "paused"
    assert view["error"] == "original native execution failure"
    assert view["reporting_errors"] == ["BrokenPipeError: closed terminal"]
    document = await manager.export(run_id)
    assert document["run"]["error"] == view["error"]
    assert document["run"]["reporting_errors"] == view["reporting_errors"]
    assert document["effects"][0]["native_diagnostics"]["received_events"] == 2200


async def test_ui_runs_real_agent_and_inspects_actual_nodes_over_http(config, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=fixture_runner)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            page = await client.get("/")
            assert page.status_code == 200 and "Start run" in page.text
            assert "innerHTML" not in page.text  # Prompt/code content is always rendered as text.
            assert (await client.get("/api/runs")).json()["objective"] == config.objective
            response = await client.post("/api/run", json={"objective": "Update a.py"})
            assert response.status_code == 202
            run_id = response.json()["id"]
            view = await finished(client, run_id)
            assert view["status"] == "completed", view
            history = list((tmp_path / "history").glob("*.json"))
            assert len(history) == 1
            archived = json.loads(history[0].read_text())
            downloaded = (await client.get("/api/export", params={"id": run_id})).json()
            for document in (archived, downloaded):
                document.pop("exported_at")
                document["capture"].pop("records_captured_at")
                document["os"].pop("captured_at")
            assert archived == downloaded
            assert {p["role"] for p in view["processes"]} == {"controller", "senior", "worker"}
            worker = next(p for p in view["processes"] if p["role"] == "worker")
            names = [n["name"] for n in worker["nodes"]]
            assert names[0] == "load" and names[-1] == "release"
            assert names.index("integrate") < names.index("checks") < names.index("publish")
            assert all(node["status"] == "completed" for node in worker["nodes"])
            model = next(n for n in worker["nodes"] if n["name"] == "model")
            data = (await client.get("/api/node", params={"run": run_id, "id": model["id"]})).json()
            operation = data["operations"][0]
            assert operation["prompt"][0]["role"] == "system"
            assert "Pinned application inputs:" in operation["prompt"][1]["content"]
            assert json.loads(operation["response"]["text"])["tool"] == "files.read"
            tool = next(n for n in worker["nodes"] if n["name"] == "tool")
            result = (await client.get("/api/node", params={"run": run_id, "id": tool["id"]})).json()
            assert not result["model_call"]
            assert result["operations"][0]["tool"] == "files.read"
            assert "VALUE = 1" in result["operations"][0]["response"]["content"]
            assert (await client.get("/api/node", params={"run": run_id, "id": "missing"})).status_code == 404

            # A second button press creates new run state; it never replays the completed test.
            second = (await client.post("/api/run", json={})).json()["id"]
            second_view = await finished(client, second)
            assert second != run_id and second_view["state"] != view["state"]
            assert second_view["status"] == "completed"
            assert len(list((tmp_path / "history").glob("*.json"))) == 2
            assert len((await client.get("/api/runs")).json()["runs"]) == 2
            reloaded = TestUI(tmp_path / "ui", config_path=path)
            assert (await reloaded.view(run_id))["processes"] == view["processes"]
            # All node history is read from persisted records/checkpoints, not UI instrumentation.
            external = TestUI(tmp_path / "external", state=view["state"])
            saved = await external.view(next(iter(external.runs)))
            assert saved["processes"] == view["processes"]
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_ui_rejects_cross_origin_starts_and_unrecognized_hosts(config, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=fixture_runner)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin) as client:
            assert (await client.post("/api/run", json={})).status_code == 403
            assert (
                await client.post("/api/run", json={}, headers={"Origin": "http://unrelated.test"})
            ).status_code == 403
            assert (await client.get("/", headers={"Host": "unrelated.test"})).status_code == 403
            assert (
                await client.post("/api/run", content="{}", headers={"Origin": origin})
            ).status_code == 400
            assert not manager.runs
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_ui_busy_and_failed_runs_remain_inspectable(config, tmp_path):
    release = threading.Event()

    async def failure(_config):
        await asyncio.to_thread(release.wait)
        raise RuntimeError("Fixture provider failed")

    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=failure)
    run_id = manager.start()
    try:
        with pytest.raises(ValueError, match="already running"):
            manager.start()
    finally:
        release.set()
    for _ in range(100):
        if not manager.active:
            break
        await asyncio.sleep(0.02)
    view = await manager.view(run_id)
    assert view["status"] == "failed" and view["error"] == "Fixture provider failed"
    history = list((tmp_path / "history").glob("*.json"))
    assert len(history) == 1
    archived = json.loads(history[0].read_text())
    assert archived["run"]["status"] == "failed"
    assert archived["run"]["error"] == "Fixture provider failed"
    assert view["processes"] == []
    reloaded = TestUI(tmp_path / "ui", config_path=path)
    assert (await reloaded.view(run_id))["error"] == "Fixture provider failed"


@pytest.mark.parametrize("failure", ["validation", "thread", "runner"])
async def test_failed_start_has_ids_exact_diagnostics_and_a_saveable_snapshot(config, tmp_path, monkeypatch, failure):
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    message = "Provider could not initialize: " + "detail " * 700 if failure == "runner" else "Thread launch failed"

    async def runner(_config):
        raise RuntimeError(message)

    manager = TestUI(tmp_path / "ui", config_path=path, runner=runner)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    if failure == "thread":
        original = threading.Thread.start

        def start(selected):
            if selected.name == "polyinference-test":
                raise RuntimeError(message)
            return original(selected)

        monkeypatch.setattr(threading.Thread, "start", start)
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            request = {"objective": "", "check_command": ""} if failure == "validation" else {}
            response = await client.post("/api/run", json=request)
            assert response.status_code == (202 if failure == "runner" else 400), response.text
            run_id = response.json()["id"]
            selected = await finished(client, run_id)
            expected = "Enter a test objective of 1–16000 characters" if failure == "validation" else message
            assert selected["error"] == expected
            assert selected["status"] == "failed" and selected["failure_stage"] == "startup"
            process_id = selected["process_id"]
            assert process_id and any(row["process_id"] == process_id for row in selected["os"]["processes"])
            downloaded = await client.get("/api/export", params={"id": run_id})
            assert downloaded.status_code == 200
            document = downloaded.json()
            assert document["run"]["error"] == expected
            assert document["records"]["process/" + process_id]["error"] == expected
            assert document["run"]["launch_request"] == {
                "objective": request.get("objective"), "repository": None,
                "check_command": request.get("check_command"), "base_branch": None,
            }
            assert manager.active is None
            reloaded = TestUI(tmp_path / "ui", config_path=path)
            assert (await reloaded.view(run_id))["error"] == expected
            snapshots = list((tmp_path / "history").glob("*.json"))
            assert len(snapshots) == 1
            assert json.loads(snapshots[0].read_text())["run"]["error"] == expected
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


def test_ui_reads_only_real_state_and_valid_content_addressed_artifacts(tmp_path):
    assert read_records(tmp_path / "absent") == {}
    assert not (tmp_path / "absent").exists()
    with pytest.raises(ValueError, match="records.sqlite"):
        TestUI(tmp_path / "ui", state=tmp_path)
    with pytest.raises(ValueError, match="Invalid artifact"):
        read_artifact(tmp_path, {"digest": "../../secret"})


async def test_ui_selects_another_repository_and_exports_complete_json(config, tmp_path):
    import shlex
    import subprocess
    from pathlib import Path

    source = tmp_path / "other"
    source.mkdir()
    (source / "a.py").write_text("VALUE = 1\n")
    (source / "b.py").write_text("VALUE = 1\n")
    subprocess.run(["git", "-C", str(source), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@localhost",
            "commit",
            "-qm",
            "other",
        ],
        check=True,
    )

    # No external task config: switching away from the greeting fixture grants the
    # committed files in this chosen root and uses its own configured check.
    manager = TestUI(tmp_path / "ui", runner=fixture_runner)
    base = manager.configuration()
    # Substitute fixture transports while preserving the UI's context/output envelope.
    base = base.model_copy(update={
        name: getattr(config, name).model_copy(update={
            "max_context_tokens": getattr(base, name).max_context_tokens,
            "reserved_context_tokens": getattr(base, name).reserved_context_tokens,
        }) for name in ("local", "cloud")
    })
    manager.configuration = lambda: base
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            listing = (await client.get("/api/directories", params={"path": str(tmp_path)})).json()
            assert any(entry["path"] == str(source) for entry in listing["directories"])
            chosen = (await client.get("/api/repository", params={"path": str(source)})).json()
            assert chosen["repository"] == str(source) and chosen["file_count"] == 2
            assert chosen["clear_objective"]
            response = await client.post(
                "/api/run",
                json={
                    "objective": "Update a.py",
                    "repository": str(source),
                    "check_command": shlex.join(config.checks[0].argv),
                },
            )
            assert response.status_code == 202, response.text
            run_id = response.json()["id"]
            view = await finished(client, run_id)
            assert view["status"] == "completed", view
            assert view["repository"] == str(source)
            saved = json.loads((Path(view["state"]).parent / "config.json").read_text())
            assert saved["repository"] == str(source)
            assert saved["allowed_write_paths"] == ["a.py", "b.py"]
            exported = await client.get("/api/export", params={"id": run_id})
            assert exported.status_code == 200
            assert "attachment" in exported.headers["content-disposition"]
            document = exported.json()
            assert document["schema_version"] == 2 and document["run"]["repository"] == str(source)
            assert document["configuration"]["repository"] == str(source)
            assert document["reports"][0]["verdict"] == "successful"
            assert document["worker_progress"] and isinstance(document["progress_events"], dict)
            assert any(process.get("progress") for process in document["processes"])
            model_nodes = [
                node for process in document["processes"] for node in process["nodes"] if node["model_call"]
            ]
            assert model_nodes and model_nodes[0]["operations"][0]["prompt"]
            assert model_nodes[0]["operations"][0]["response"]["text"]
            assert document["effects"] and document["effects"][0]["request"]["operation_id"]
            assert document["inference_attempts"] and document["inference_attempts"][0]["context_parts"]
            semantic = document["run_record"]["semantic_completion"]
            assert document["completion_reviews"][semantic["review_ref"]] == semantic
            assert document["review_artifacts"]
            assert "cost" in document["run"]
            from polyinference.os_config import KERNEL_VERSION
            assert document["records"]["runtime/kernel"]["version"] == KERNEL_VERSION
            assert document["record_revisions"]["app/run"] > 1
            assert document["checkpoints"] and document["artifacts"] and document["events"]
            assert document["capture"]["artifact_errors"] == 0
            for artifact in document["artifacts"]:
                content = base64.b64decode(artifact["data"])
                assert "sha256:" + hashlib.sha256(content).hexdigest() == artifact["digest"]
                assert len(content) == artifact["size_bytes"]
            permit_states = [
                change["value"]["process_id"]
                for event in document["events"] for key, change in event["changes"].items()
                if key == "permit/verification/project"
            ]
            assert any(permit_states) and permit_states[-1] is None
            assert document["os"]["journal"]["count"] == len(document["events"])
            record = await client.get("/api/record", params={"run": run_id, "key": "runtime/kernel"})
            assert record.json()["value"] == document["records"]["runtime/kernel"]
            assert (await client.get("/api/record", params={"run": "missing", "key": "app/run"})).status_code == 404
            script = await client.get("/ui-monitor.js")
            assert script.status_code == 200 and script.headers["content-type"].startswith("text/javascript")
            assert "projectTasks" in script.text
            explanation = document["reports"][0]["assessment_summary"]
            artifact = await client.get("/api/artifact", params={"run": run_id, "digest": explanation["digest"]})
            assert artifact.json()["text"] == read_artifact(view["state"], explanation)
            assert (await client.get("/api/artifact", params={
                "run": run_id, "digest": "../config.json",
            })).status_code == 400
            assert (await client.get("/api/artifact", params={
                "run": "missing", "digest": explanation["digest"],
            })).status_code == 404
            assert document["agents"]["records"]["task/a"]["execution"] == "completed"
            assert explanation["digest"] in document["agents"]["texts"]
            latest = (await client.get("/api/activity", params={"run": run_id})).json()
            assert latest["last_sequence"] == document["events"][-1]["sequence"]
            if latest["has_older"]:
                older = (await client.get("/api/activity", params={
                    "run": run_id, "before": latest["first_sequence"],
                })).json()
                assert older["last_sequence"] < latest["first_sequence"]
            assert (source / "a.py").read_text() == "VALUE = 2\n"
            assert document["repository_setup"]["isolated"] is False
            assert document["repository_summary"]["head"]
            assert not subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"]).strip()
            (source / "a.py").write_text("VALUE = 99\n")
            refused = await client.post(
                "/api/run",
                json={"objective": "another", "repository": str(source), "check_command": "python -m pytest"},
            )
            assert refused.status_code == 400 and "Commit or stash" in refused.json()["error"]
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_ui_steering_uses_the_same_atomic_capture_as_cli(config, tmp_path):
    from polyinference.cli import record_steering
    from polyinference.runtime.storage import Records

    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    initialized, release = threading.Event(), threading.Event()

    async def waiting(selected):
        runtime = await StandaloneRuntime(selected).open()
        try:
            app = AgentServices(runtime, selected)
            await ProjectAgent(app).initialize()
            run = app.get("app/run")
            app.update("app/run", {**run, "active_workers": ["worker-waiting"], "starts_closed": False})
            initialized.set()
            await asyncio.to_thread(release.wait)
        finally:
            await runtime.close()

    manager = TestUI(tmp_path / "ui", config_path=path, runner=waiting)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            run_id = (await client.post("/api/run", json={})).json()["id"]
            assert await asyncio.to_thread(initialized.wait, 5)
            reply = await client.post("/api/steer", json={"id": run_id, "text": "Keep the public signature."})
            assert reply.status_code == 202 and reply.json()["sequence"] == 1
            state = manager.runs[run_id]["state"]
            records = read_records(state)
            assert records["app/run"]["starts_closed"]
            assert records["app/run"]["captured_workers"] == ["worker-waiting"]
            assert records["steering/00000001"]["text"] == "Keep the public signature."
            assert record_steering(state, "Also update comments.") == 2
            exported = (await client.get("/api/export", params={"id": run_id})).json()
            assert [item["sequence"] for item in exported["steering"]] == [1, 2]
            view = (await client.get("/api/run", params={"id": run_id})).json()
            assert view["steering_received"] == 2 and view["steering_applied"] == 0
            assert (await client.post("/api/steer", json={"id": run_id, "text": "  "})).status_code == 400
            assert (
                await client.post(
                    "/api/steer",
                    json={"id": run_id, "text": "x"},
                    headers={"Origin": "http://unrelated.test"},
                )
            ).status_code == 403
            db = Records(__import__("pathlib").Path(state) / "records.sqlite")
            try:
                rev, run = db.get("app/run")
                db.compare_and_publish({"app/run": rev}, {"app/run": {**run, "status": "completed"}})
            finally:
                db.db.close()
            assert (
                await client.post("/api/steer", json={"id": run_id, "text": "too late"})
            ).status_code == 400
    finally:
        release.set()
        for _ in range(100):
            if not manager.active:
                break
            await asyncio.sleep(0.02)
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


def test_repository_picker_rejects_subdirectories_and_non_repositories(config, tmp_path):
    from polyinference.ui_repository import repository

    with pytest.raises(ValueError, match="Git repository"):
        repository(str(tmp_path))
    subdir = __import__("pathlib").Path(config.repository) / "nested"
    subdir.mkdir()
    with pytest.raises(ValueError, match="repository root"):
        repository(str(subdir))


@pytest.mark.parametrize("output_target", [32000, 12000])
async def test_default_ui_routes_workers_to_haiku_and_finishes_after_former_sprint_cap(
    config, tmp_path, monkeypatch
, output_target):
    import shlex
    from pathlib import Path

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-key")
    worker_requests, senior_requests, setup_requests, policy_requests = [], [], [], []
    worker = ScriptedAgent(two=True)

    class CodexSenior:
        async def generate_job(self, messages, snapshot, schema, callback=None):
            assert Path(snapshot).is_dir()
            data = json.loads(
                next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
                    "Pinned application inputs:\n", 1
                )[1]
            )
            if "repository_observation" in data:
                policy_requests.append(data)
                return {"model": "gpt-6.1-sol", "text": json.dumps({"mode": "new", "task_branches": True}),
                        "usage": {"inputTokens": 100, "outputTokens": 20, "total_tokens": 120}, "events": []}
            if "assignment" in data:
                assert callback is not None
                assert data["assignment"]["task_id"] == "project_setup"
                setup_requests.append(data)
                reply = (
                    {"kind": "assessment", "verdict": "successful", "summary": "Setup inspected"}
                    if data["phase"] == "assessment"
                    else {"kind": "candidate", "summary": "Setup complete"}
                )
                return {
                    "model": "gpt-6.1-sol",
                    "text": json.dumps(fixture_review_reply(reply, data)),
                    "usage": {"inputTokens": 100, "outputTokens": 20, "total_tokens": 120},
                    "events": [],
                }
            assert "tasks" in schema["properties"]
            senior_requests.append(data)
            reply = {
                "goal": "Update both files, then conduct a final review",
                "dispositions": [
                    {"report_ref": report["record_id"], "action": "keep", "reason": "Reviewed"}
                    for report in data["reports"]
                ],
                "memory_update": "Review " + str(len(senior_requests)),
            }
            if "a" not in data["all_task_ids"]:
                reply["tasks"] = [
                    {
                        "task_id": name,
                        "objective": "Update " + name + ".py",
                        "write_paths": [name + ".py"],
                        "read_paths": [name + ".py"],
                        "dependencies": [] if name == "a" else ["a"],
                        "checks": ["tests"],
                    }
                    for name in ["a", "b"]
                ]
            else:
                reply["complete"] = not data["reports"] and not data["pending_tasks"]
                if reply["complete"]:
                    reply["completion_assessment"] = fixture_completion(data)
            return {
                "model": "gpt-6.1-sol",
                "text": json.dumps(fixture_review_reply(reply, data)),
                "usage": {"inputTokens": 100, "outputTokens": 20, "total_tokens": 120},
                "events": [],
            }

        async def close(self):
            pass

    async def haiku(request):
        assert str(request.url) == "https://api.anthropic.com/v1/messages"
        assert request.headers["x-api-key"] == "fixture-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        body = json.loads(request.content)
        assert body["model"] == "claude-haiku-5-5"
        assert body["max_tokens"] == output_target
        assert body["stream"] is True
        messages = [{"role": "system", "content": body["system"]}, *body["messages"]]
        assert '"assignment"' in messages[1]["content"]
        worker_requests.append(body)
        result = await worker.generate(messages, body["max_tokens"])
        # Both the small fresh-UI target and an explicit >8k response remain valid.
        frames = [
            {"type": "message_start", "message": {"id": "fixture-" + str(len(worker_requests)),
                "model": "claude-haiku-5-5", "usage": {"input_tokens": 100}}},
            {"type": "content_block_start", "index": 0,
                "content_block": {"type": "text", "text": result["text"]}},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn"},
                "usage": {"output_tokens": min(9000, output_target - 100)}},
            {"type": "message_stop"},
        ]
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
            content="".join("data: " + json.dumps(frame) + "\n\n" for frame in frames))


    async def mixed_run(selected):
        runtime = await StandaloneRuntime(selected).open()
        try:
            # Keep the real Anthropic adapter and constructed authentication headers.
            client = runtime.clients["local"]
            headers = client.client.headers
            await client.client.aclose()
            client.client = httpx.AsyncClient(headers=headers, transport=httpx.MockTransport(haiku))
            await runtime.clients["cloud"].close()
            runtime.clients["cloud"] = CodexSenior()
            return await ProjectAgent(AgentServices(runtime, selected)).run()
        finally:
            await runtime.close()

    manager = TestUI(tmp_path / "ui", runner=mixed_run)
    if output_target != 32000:
        default_configuration = manager.configuration
        def configuration_with_local_pair():
            selected = default_configuration()
            return type(selected).model_validate({**selected.model_dump(), "local_token_limits": {
                "input_tokens": selected.local_token_limits.input_tokens, "output_tokens": output_target}})
        manager.configuration = configuration_with_local_pair
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            settings = (await client.get("/api/runs")).json()
            assert "claude-haiku-5-5 workers (cloud)" in settings["configuration"]
            assert "27 sprints" in settings["configuration"]
            reply = await client.post(
                "/api/run",
                json={
                    "repository": config.repository,
                    "objective": "Update both values",
                    "check_command": shlex.join(config.checks[0].argv),
                },
            )
            assert reply.status_code == 202, reply.text
            run_id = reply.json()["id"]
            view = await finished(client, run_id)
            assert view["status"] == "completed", view
            document = (await client.get("/api/export", params={"id": run_id})).json()
            assert document["configuration"]["max_sprints"] == 27
            assert document["configuration"]["limits"]["max_output_tokens_per_call"] == output_target
            assert document["run_record"]["sprint"] == len(senior_requests) == 4
            assert worker_requests
            effects = document["effects"]
            models = [e for e in effects if e["request"]["payload"]["kind"] == "model_query"]
            assert len(models) == len(worker_requests)
            assert all(e["result"]["actual_backend"]["model_version"] == "claude-haiku-5-5" for e in models)
            assert all(e["request"]["payload"]["role"] == "worker" for e in models)
            assert all(e["request"]["limits"]["max_output_tokens_per_call"] == output_target for e in models)
            jobs = [e for e in effects if e["request"]["payload"]["kind"] == "agent_job"]
            assert len(jobs) == len(senior_requests) + len(setup_requests) + len(policy_requests)
            assert {e["request"]["payload"]["role"] for e in jobs} == {"senior", "specialist"}
            assert all(e["result"]["actual_backend"]["model_version"] == "gpt-6.1-sol" for e in jobs)
            assert view["cost"]["by_provider"]["haiku"]["estimated_usd"] > 0
            assert view["cost"]["by_provider"]["haiku"]["calls"] == len(worker_requests)
            assert view["cost"]["by_provider"]["codex"]["calls"] == (
                len(senior_requests) + len(setup_requests) + len(policy_requests))
            assert (Path(config.repository) / "a.py").read_text() == "VALUE = 2\n"
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_endpoint_probe_is_explicit_serialized_and_retained(config, tmp_path, monkeypatch):
    from polyinference.runtime.kernel import UncertainEffect
    from polyinference.ui import RunStartError
    path = tmp_path / "agent.json"
    path.write_text(config.model_dump_json())
    calls = []
    release = threading.Event()
    async def probe(selected, state):
        calls.append(selected.local.lifecycle)
        await asyncio.to_thread(release.wait)
        return {"status": "succeeded", "error": None}
    monkeypatch.setattr("polyinference.agent.endpoint_probe.probe_endpoint", probe)
    manager = TestUI(tmp_path / "ui", path)
    assert manager.probe_view() is None and calls == []
    manager.test_endpoint("local-inference")
    with pytest.raises(ValueError, match="active work"):
        manager.test_endpoint()
    with pytest.raises(RunStartError, match="endpoint probe"):
        manager.start()
    release.set()
    for _ in range(100):
        if manager.probe_view()["status"] != "running":
            break
        await asyncio.sleep(.01)
    assert manager.probe_view()["status"] == "succeeded"
    assert len(calls) == 1 and calls[0].first_output_seconds == 900
    async def unknown(selected, state):
        from pathlib import Path
        Path(state).mkdir(parents=True, exist_ok=True)
        records = Records(Path(state) / "records.sqlite")
        try:
            records.put_once("effect/probe", {"state": "uncertain"})
        finally:
            records.db.close()
        raise UncertainEffect("probe")
    monkeypatch.setattr("polyinference.agent.endpoint_probe.probe_endpoint", unknown)
    manager.test_endpoint()
    for _ in range(100):
        if manager.probe_view()["status"] != "running":
            break
        await asyncio.sleep(.01)
    assert manager.probe_view()["status"] == "uncertain"
    restored = TestUI(tmp_path / "ui", path)
    assert restored.probe_view()["status"] == "uncertain"
    with pytest.raises(ValueError, match="uncertain endpoint probe"):
        restored.test_endpoint()
