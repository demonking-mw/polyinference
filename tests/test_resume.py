"""Run continuation across the UI adapter, coding agent and generic OS boundary."""
from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from conftest import static_schedule

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.resume import COMPATIBLE_GRAPH
from polyinference.agent.services import AgentServices
from polyinference.config import Endpoint, RuntimeConfig
from polyinference.contracts import ContextPart, ContextView, ModelQuery, OperationRequest, ProcessSpec
from polyinference.primitives import digest, now, operation_fingerprint
from polyinference.runtime.inference import HTTPInference, UnknownExecution
from polyinference.runtime.kernel import KernelRuntime, UncertainEffect
from polyinference.runtime.processes import request_resume
from polyinference.runtime.storage import Records
from polyinference.ui import TestUI


async def research(tmp_path, protocol="chat", timeout=180):
    endpoint = Endpoint(model="fixture", protocol=protocol, base_url="http://fixture/v1", timeout_seconds=timeout)
    config = RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
                           local=endpoint, cloud=endpoint, role_bindings={"researcher": "local"})
    runtime = await KernelRuntime(config).open()
    scope = runtime.scope.model_copy(update={"process_id": "research"})
    prompt = runtime.artifacts.put(b"Summarize facts", scope)
    examples = json.loads((Path(__file__).parents[1] / "design-docs/langgraph-agent/examples.json").read_text())
    template = next(r for r in examples["records"] if r["kind"] == "process_spec")
    spec = ProcessSpec.model_validate({
        **template, "record_id": "process-spec/research", "scope": scope.model_dump(mode="json"),
        "created_at": now(), "required_features": [], "extensions": {},
        "process_id": "research", "parent_process_id": None, "role": "researcher",
        "entry_point": "summarize", "task_spec_ref": None, "attempt_id": None,
        "workspace_id": None, "input_refs": [prompt], "limits": config.limits,
        "output_schema_ref": "summary/1", "grant_ref": "grant/run", "budget_account_ref": "budget/run",
        "program": {**template["program"], "program_id": "research", "program_version": "1"},
        "schedule": static_schedule(template["schedule"], config, "researcher"),
    })
    runtime.processes.register(spec, "local")
    context = ContextView(view_id="facts", digest=digest(b"facts"),
                          parts=[ContextPart(part_id="facts", content=prompt, part_kind="data", trust="user",
                                             source_ref="user", required=True)],
                          memory_snapshot_refs=[], tool_catalog_digest=digest(b"no-tools"),
                          maximum_input_tokens=config.limits.max_input_tokens_per_call, omitted_refs=[])
    payload = ModelQuery(role="researcher", phase="summarize", prompt_template_ref="research/1", context=context,
                         response_schema_ref="summary/1", capability_requirements=[], temperature=0, session_ref=None)
    request = OperationRequest(
        record_id="request/research/summary", scope=scope, created_at=now(), revision=1,
        operation_id="research-summary", logical_step_id="summary", intent_digest=digest(b"pending"),
        causal_parent_ref=None, trace_id="run", grant_ref="grant/run", owner_generation=1,
        expected_process_revision=1, expected_binding_generation=1, schedule_ref="research/1",
        budget_account_ref="budget/run", deadline=now() + timedelta(seconds=120), limits=config.limits,
        resources=[], conflict_keys=[], safe_boundary="settled_operation", replay_policy="deduplicated", payload=payload,
    )
    return runtime, request.model_copy(update={"intent_digest": operation_fingerprint(request)})


class Disconnected:
    async def generate(self, *args, **kwargs):
        raise UnknownExecution("Connection lost after submission")

    async def close(self):
        pass


@pytest.mark.parametrize("recovery", ["receipt", "response", "failed", "unsupported", "invalid-status"])
async def test_generic_os_prepares_resume_without_git_or_coding_policy(tmp_path, recovery):
    runtime, request = await research(tmp_path, "responses" if recovery != "receipt" else "chat")
    config = runtime.config
    try:
        await runtime.clients["local"].close()
        runtime.clients["local"] = Disconnected()
        with pytest.raises(UncertainEffect):
            await runtime.execute(request)
        runtime.processes.finish("research", state="paused")
        key = "effect/" + request.operation_id
        original = runtime.records.get(key)[1]
        response = {"text": "Retained facts.", "model": "fixture", "usage": {"total_tokens": 7}}
        if recovery == "receipt":
            runtime.records.put_once("model-response/" + request.operation_id, {
                "response_ref": runtime.artifacts.put(json.dumps(response).encode(), request.scope).model_dump(mode="json")})
        else:
            runtime._update(key, {**original, "provider": {"response_id": "resp_saved"}})
        ref = request_resume(runtime.records, text="Continue", request_id="one-click")
        await runtime.close()
        runtime = await KernelRuntime(config).open()
        calls = []

        async def handler(req):
            calls.append((req.method, req.url.path))
            status = "failed" if recovery == "failed" else "unknown" if recovery == "invalid-status" else "completed"
            return httpx.Response(200, json={"id": "resp_saved", "model": "fixture", "status": status,
                                            "output": [{"type": "message", "content": [
                                                {"type": "output_text", "text": "Retained facts."}]}],
                                            "usage": {"total_tokens": 7}})

        if recovery != "unsupported":
            await runtime.clients["local"].close()
            runtime.clients["local"] = HTTPInference(config.local, httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        else:
            await runtime.clients["local"].close()
            runtime.clients["local"] = Disconnected()
        before = runtime.records.get(key)[1]
        if recovery in {"unsupported", "invalid-status"}:
            with pytest.raises(RuntimeError, match="Could not resume|final state"):
                await runtime.prepare_resume(ref)
            assert runtime.records.get(key)[1] == before
            assert runtime.uncertain() == [request.operation_id]
            assert runtime.admission["local"].active == 1
            assert runtime.records.get("resume-preparation/" + ref)[1]["state"] == "failed"
        else:
            await runtime.prepare_resume(ref)
            result = await runtime.execute(request)
            assert result.state == ("failed" if recovery == "failed" else "succeeded")
            assert result.execution_termination == "confirmed_stopped"
            assert runtime.admission["local"].active == 0
            assert runtime.records.get("resume-preparation/" + ref)[1]["state"] == "ready"
            settled = runtime.records.get(key)[1]
            await runtime.prepare_resume(ref)
            assert runtime.records.get(key)[1] == settled
            assert len(calls) == (0 if recovery == "receipt" else 1)
            assert result.usage[0].value == 7
        assert not runtime.records.scan("task/") and not runtime.records.get("app/run")
        assert not config.repo_path.exists() and not (config.state_path / "repository.git").exists()
    finally:
        await runtime.close()


async def test_resume_uses_exact_supported_program_migration_and_rejects_other_graphs(config):
    runtime = await KernelRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        await engine.initialize()
        original_manifest = app.get("program/manifest")
        old = {**app.get("app/run")["program"], "graph_digest": COMPATIBLE_GRAPH}
        app.update("app/run", {**app.get("app/run"), "program": old, "status": "paused"})
        await engine.initialize()
        assert app.get("app/run")["program"] == app.program.model_dump(mode="json")
        assert app.get("program/manifest") == original_manifest
        migration = runtime.records.scan("coding/resume-program-migration/")[0][2]
        assert migration["from"] == old and migration["to"] == app.get("app/run")["program"]
        app.update("app/run", {**app.get("app/run"), "program": {**old, "graph_digest": digest(b"unknown")}})
        with pytest.raises(RuntimeError, match="pinned implementation"):
            await engine.initialize()
    finally:
        await runtime.close()


async def test_resume_text_is_applied_once_after_interrupted_continuation(config, monkeypatch):
    runtime = await KernelRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        await engine.initialize()
        app.update("app/run", {**app.get("app/run"), "status": "paused"})
        runtime.processes.finish("controller", state="paused")
        ref = request_resume(runtime.records, text="Keep the signature", request_id="one-click")
        steer = engine.steer

        class CoordinatorLost(BaseException):
            pass

        def interrupted(*args, **kwargs):
            steer(*args, **kwargs)
            raise CoordinatorLost("Interrupted after steering commit")

        monkeypatch.setattr(engine, "steer", interrupted)
        with pytest.raises(CoordinatorLost, match="steering commit"):
            await engine.resume(ref)
        monkeypatch.setattr(engine, "steer", steer)
        await engine.resume(ref)
        await engine.resume(ref)
        assert app.get("app/run")["steering_received"] == 1
        assert len(runtime.records.scan("steering/")) == 1
        assert app.get("resume-outcome/" + ref)["state"] == "applied"
    finally:
        await runtime.close()


async def test_ui_restores_acceptance_before_metadata_save(config, tmp_path):
    runtime = await KernelRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        await ProjectAgent(app).initialize()
        app.update("app/run", {**app.get("app/run"), "status": "paused"})
        runtime.processes.finish("controller", state="paused")
    finally:
        await runtime.close()
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    original = TestUI(tmp_path / "ui", config_path=path, state=config.state_path)
    run_id = next(iter(original.runs))
    original.save(original.runs[run_id])
    records = Records(config.state_path / "records.sqlite")
    ref = request_resume(records, text="Keep work", request_id="saved-before-metadata")
    records.db.close()
    entered = asyncio.Event()
    received = []
    # Do not start a real thread: inspect what startup would dispatch, including
    # the original request identity recovered from the OS pointer alone.
    class RestoredUI(TestUI):
        def launch_driver(self, metadata, selected, runner):
            received.append((metadata["id"], metadata["last_resume_request"], selected.state_path))
            entered.set()
    restored = RestoredUI(tmp_path / "ui", config_path=path)
    assert entered.is_set() and received == [(run_id, ref, config.state_path)]
    assert restored.resume(run_id, text="Keep work", request_id="saved-before-metadata")["request_ref"] == ref
    records = Records(config.state_path / "records.sqlite")
    try:
        assert len(records.scan("resume-request/")) == 1
    finally:
        records.db.close()


async def test_resume_accounts_for_multiple_interrupted_workers_and_preserves_source(config):
    from conftest import ScriptedAgent

    from polyinference.runtime.inference import ProviderError

    runtime = await KernelRuntime(config).open()
    scripted = ScriptedAgent(two=True)
    failing = True

    class Provider:
        async def generate(self, messages, max_output):
            data = json.loads(next(m["content"] for m in messages if "Pinned application inputs:" in m["content"])
                              .split("Pinned application inputs:\n", 1)[1])
            if failing and data.get("phase") == "reconciliation":
                raise ProviderError("Stopped for fixture", category="invalid_request", status=400)
            return await scripted.generate(messages, max_output)

        async def close(self):
            pass

    try:
        for name in runtime.clients:
            await runtime.clients[name].close()
            runtime.clients[name] = Provider()
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        await engine.run()
        tasks = [task for _, _, task in runtime.records.scan("task/")]
        assert len(tasks) == 2 and all(task.get("model_failure") for task in tasks)
        before = {task["workspace_id"]: await runtime.workspaces.scan_async(
            runtime.workspaces.root_for(runtime.workspaces.current(task["workspace_id"]))) for task in tasks}
        failing = False
        ref = request_resume(runtime.records, request_id="resume-all")
        await engine.resume(ref)
        active = app.get("app/run")["active_workers"]
        assert len(active) == 1
        for task in tasks:
            manifest = runtime.workspaces.current(task["workspace_id"])
            current = await runtime.workspaces.scan_async(runtime.workspaces.root_for(manifest))
            for path in task["assignment"]["write_paths"]:
                assert current[path] == before[task["workspace_id"]][path]
            if task["process_id"] not in active:
                assert app.get("task/" + task["assignment"]["task_id"])["execution"] == "interrupted"
        await asyncio.gather(*engine.workers.values())
        await engine.consume()
        assert not app.get("app/run")["active_workers"]
        assert len([task for _, _, task in runtime.records.scan("task/") if task["execution"] == "interrupted"]) == 1
    finally:
        await runtime.close()


async def test_ui_restores_activated_request_before_first_execution(config, tmp_path):
    runtime = await KernelRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        await engine.initialize()
        app.update("app/run", {**app.get("app/run"), "status": "paused"})
        runtime.processes.finish("controller", state="paused")
    finally:
        await runtime.close()
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    original = TestUI(tmp_path / "ui", config_path=path, state=config.state_path)
    run_id = next(iter(original.runs))
    original.save(original.runs[run_id])
    records = Records(config.state_path / "records.sqlite")
    ref = request_resume(records, text="Only once", request_id="activation-crash")
    records.db.close()
    runtime = await KernelRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        await engine.initialize()
        await engine.resume(ref)
        assert app.get("app/run")["steering_received"] == 1
    finally:
        await runtime.close()
    dispatched = []

    class RestoredUI(TestUI):
        def launch_driver(self, metadata, selected, runner):
            dispatched.append(metadata["last_resume_request"])

    RestoredUI(tmp_path / "ui", config_path=path)
    assert dispatched == [ref]
    runtime = await KernelRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        await engine.initialize()
        await engine.resume(ref)
        assert app.get("app/run")["steering_received"] == 1
        assert len(runtime.records.scan("steering/")) == 1
    finally:
        await runtime.close()


async def test_generic_resume_retains_uncertainty_when_provider_lookup_times_out(tmp_path):
    # Bound lookup itself; fixture preparation must not consume the entire logical deadline.
    runtime, request = await research(tmp_path, "responses", timeout=0.05)
    try:
        await runtime.clients["local"].close()
        runtime.clients["local"] = Disconnected()
        with pytest.raises(UncertainEffect):
            await runtime.execute(request)
        runtime.processes.finish("research", state="paused")
        key = "effect/" + request.operation_id
        runtime._update(key, {**runtime.records.get(key)[1], "provider": {"response_id": "resp_waiting"}})
        before = runtime.records.get(key)[1]
        async def handler(req):
            assert req.method == "GET"
            return httpx.Response(200, json={"id": "resp_waiting", "status": "in_progress"})
        runtime.clients["local"] = HTTPInference(runtime.config.local,
                                                  httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        ref = request_resume(runtime.records, request_id="bounded-recovery")
        with pytest.raises(RuntimeError, match="has not returned"):
            await runtime.prepare_resume(ref)
        assert runtime.records.get(key)[1] == before
        assert runtime.admission["local"].active == 1
    finally:
        await runtime.close()


async def test_accepted_resume_does_not_bypass_external_coordinator_ownership(tmp_path):
    runtime, request = await research(tmp_path)
    try:
        ref = request_resume(runtime.records, request_id="queued-intent")
        with pytest.raises(RuntimeError, match="Another coordinator"):
            KernelRuntime(runtime.config)
        assert runtime.records.get(ref) and not runtime.records.scan("effect/")
    finally:
        await runtime.close()


async def test_cli_resume_records_optional_instructions_for_the_shared_service(config, monkeypatch, capsys):
    from polyinference import cli

    runtime = await KernelRuntime(config).open()
    try:
        app = AgentServices(runtime, config)
        await ProjectAgent(app).initialize()
        app.update("app/run", {**app.get("app/run"), "status": "paused"})
        runtime.processes.finish("controller", state="paused")
    finally:
        await runtime.close()
    path = config.state_path.parent / "cli-config.json"
    path.write_text(config.model_dump_json())
    seen = []

    async def execute(selected, *, resume_request_ref=None):
        records = Records(selected.state_path / "records.sqlite")
        try:
            seen.append(records.get(resume_request_ref)[1])
        finally:
            records.db.close()
        return {"status": "completed"}

    monkeypatch.setattr(cli, "execute", execute)
    monkeypatch.setattr(cli, "load_saved_credentials", lambda: None)
    monkeypatch.setattr(cli.sys, "argv", ["polyinference", "resume", str(path), "--text", "Keep all edits"])
    # main owns its event loop, just as the installed CLI does.
    await asyncio.to_thread(cli.main)
    assert len(seen) == 1 and seen[0]["process_id"] is None and seen[0]["text"] == "Keep all edits"
    assert 'completed' in capsys.readouterr().out


async def test_completed_recovery_finishes_accounting_after_settlement_crash(tmp_path, monkeypatch):
    runtime, request = await research(tmp_path)
    try:
        await runtime.clients["local"].close()
        runtime.clients["local"] = Disconnected()
        with pytest.raises(UncertainEffect):
            await runtime.execute(request)
        runtime.processes.finish("research", state="paused")
        response = {"text": "Retained facts", "model": "fixture", "usage": {"total_tokens": 7}}
        runtime.records.put_once("model-response/" + request.operation_id, {
            "response_ref": runtime.artifacts.put(json.dumps(response).encode(), request.scope).model_dump(mode="json")})
        ref = request_resume(runtime.records, request_id="settlement-crash")
        settle = runtime._settle_budget

        def interrupted(*args, **kwargs):
            raise RuntimeError("Interrupted after effect settlement")

        monkeypatch.setattr(runtime, "_settle_budget", interrupted)
        with pytest.raises(RuntimeError, match="effect settlement"):
            await runtime.prepare_resume(ref)
        assert runtime.records.get("effect/" + request.operation_id)[1]["state"] == "succeeded"
        monkeypatch.setattr(runtime, "_settle_budget", settle)
        await runtime.prepare_resume(ref)
        allocation = runtime.records.get("allocation/" + request.operation_id)[1]
        assert allocation["settled"] and allocation["amount"] == 7 and allocation["provider_reported"]
        assert runtime.admission["local"].active == 0
        assert runtime.records.get("budget/run")[1]["reserved_or_used"] == 7
    finally:
        await runtime.close()
