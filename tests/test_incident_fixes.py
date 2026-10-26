from __future__ import annotations

import asyncio
import json

import pytest
from conftest import ScriptedAgent, fixture_review_reply

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.contracts import OperationRequest
from polyinference.runtime.inference import ProviderError
from polyinference.runtime.kernel import KernelRuntime


def pinned(messages):
    return json.loads(next(m["content"] for m in messages if m["content"].startswith("Pinned application inputs:\n")).split("\n", 1)[1])


async def install(runtime, provider):
    for client in runtime.clients.values():
        await client.close()
    runtime.clients = {name: provider for name in runtime.clients}


async def test_empty_plan_terminates_despite_changing_memory(config):
    calls = []

    class Provider:
        async def generate(self, messages, max_output):
            calls.append(messages)
            return {"text": json.dumps({"goal": "Blocked", "memory_update": "New wording " + str(len(calls))}),
                    "model": "fixture", "usage": {"total_tokens": 5}}

        async def close(self):
            pass

    runtime = await KernelRuntime(config).open()
    await install(runtime, Provider())
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        assert (await engine.run())["outcome"] == "paused"
        assert len(calls) == 1
        assert (await engine.run())["outcome"] == "paused"
        assert len(calls) == 1
        assert app.get("process-status/controller")["state"] == "paused"
        assert not app.get("app/run")["active_workers"]
        assert all(a.active == 0 for a in runtime.admission.values())
        from polyinference.cli import record_steering

        record_steering(config.state_path, "Review again with this additional information")
        assert (await engine.run())["outcome"] == "paused"
        assert len(calls) == 2
        assert app.get("app/run")["steering_applied"] == 1
    finally:
        await runtime.close()


@pytest.mark.parametrize("conflict", [False, True])
async def test_new_project_can_write_application_and_delivers_accepted_files(config, tmp_path, conflict):
    source = tmp_path / "new-game"
    config = config.model_copy(update={
        "repository": str(source), "prepare_repository": True, "write_scope": "project",
        "allowed_write_paths": ["README.md"], "closure_paths": [],
        "objective": "Build a 2D game with multiple worlds and saved player progress.",
    })
    observations = []
    written = False

    class Provider:
        async def generate(self, messages, max_output):
            nonlocal written
            data = pinned(messages)
            observations.append(data)
            assert messages[-1]["role"] == "user"
            if "assignment" in data:
                assert data["user_objective"] == config.objective
                if data["phase"] == "assessment":
                    if conflict and data["assignment"]["task_id"] == "app":
                        (source / "index.html").write_text("USER CHANGE")
                    reply = {"kind": "assessment", "verdict": "successful", "summary": "Fixture checked"}
                elif data["assignment"]["task_id"] == "app" and data["phase"] == "development" and not written:
                    written = True
                    assert not (source / "index.html").exists(), "Only accepted files may be delivered"
                    reply = {"kind": "action", "tool": "files.write", "arguments": {
                        "path": "index.html", "expected_digest": None, "content": "<canvas id='world-2d'></canvas>\n",
                    }}
                else:
                    reply = {"kind": "candidate", "summary": "Ready for the next phase"}
            else:
                assert data["write_scope"] == "project"
                assert data["write_authority"]["may_assign_new_project_paths"]
                assert data["write_authority"]["explicit_paths"] is None
                reply = {"goal": config.objective, "dispositions": [
                    {"report_ref": r["record_id"], "action": "keep", "reason": "Checked fixture"}
                    for r in data["reports"]
                ]}
                if "app" not in data["all_task_ids"]:
                    reply["tasks"] = [{"task_id": "app", "objective": config.objective,
                                       "write_paths": ["index.html"], "read_paths": data["repository_context"]["paths"],
                                       "checks": ["syntax"]}]
                else:
                    reply["complete"] = True
            return {"text": json.dumps(fixture_review_reply(reply, data)), "model": "fixture", "usage": {"total_tokens": 5}}

        async def close(self):
            pass

    runtime = await KernelRuntime(config).open()
    await install(runtime, Provider())
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        result = await engine.run()
        if conflict:
            assert result["outcome"] == "paused"
            assert (source / "index.html").read_text() == "USER CHANGE"
            (source / "index.html").unlink()
            before = len(observations)
            engine.retry_outputs("Restored the output destination to its initial state")
            assert (await engine.run())["outcome"] == "completed", app.get("app/run")
            assert len(observations) == before
        else:
            assert result["outcome"] == "completed", app.get("app/run")
        assert (source / "index.html").read_text() == "<canvas id='world-2d'></canvas>\n"
        assert app.get("app/run")["output"]["directory"] == str(source)
        assert runtime.records.scan("output-delivery/")
        before = len(observations)
        assert (await engine.run())["outcome"] == "completed"
        assert len(observations) == before
    finally:
        await runtime.close()


@pytest.mark.parametrize("uncertain", [False, True])
@pytest.mark.parametrize("crash", [False, True])
async def test_model_failure_pauses_then_explicit_recovery_preserves_private_edit(config, uncertain, crash, monkeypatch):
    scripted = ScriptedAgent(two=False)
    failed = False

    class Provider:
        async def generate(self, messages, max_output):
            nonlocal failed
            data = pinned(messages)
            if data.get("phase") == "reconciliation" and not failed:
                failed = True
                if uncertain:
                    from polyinference.runtime.inference import UnknownExecution

                    raise UnknownExecution("Provider disconnected after submission")
                raise ProviderError("Endpoint HTTP 400", category="invalid_request", status=400,
                                    provider_code="fixture_invalid_request")
            return await scripted.generate(messages, max_output)

        async def close(self):
            pass

    runtime = await KernelRuntime(config).open()
    await install(runtime, Provider())
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        assert (await engine.run())["outcome"] == "paused"
        if uncertain:
            with pytest.raises(ValueError, match="reconcile"):
                await engine.retry_worker("a", "Must not retry unknown execution")
            await runtime.reconcile_stopped(runtime.uncertain()[0], "Fixture provider and host descendants have terminated")
        task = app.get("task/a")
        failure_id = task["model_failure"]["operation_id"]
        original = OperationRequest.model_validate(app.get("effect/" + failure_id)["request"])
        assert runtime.workspaces.current(task["workspace_id"]).view == "development"
        assert not runtime.exclusive.owns("unused", "verification/project", task["process_id"])
        assert not (config.state_path / "result").exists()
        if crash:
            publish = runtime.records.compare_and_publish

            def interrupted_activation(expected, updates, immutable=None):
                if "app/run" in updates and updates.get("task/a", {}).get("execution") == "in_progress":
                    raise RuntimeError("simulated interruption after recovery checkpoint")
                return publish(expected, updates, immutable)

            monkeypatch.setattr(runtime.records, "compare_and_publish", interrupted_activation)
            with pytest.raises(RuntimeError, match="recovery checkpoint"):
                await engine.retry_worker("a", "Corrected provider framing")
            monkeypatch.setattr(runtime.records, "compare_and_publish", publish)
            assert app.get("task/a")["execution"] == "interrupted"
            assert not app.get("app/run")["active_workers"]
        await engine.retry_worker("a", "Corrected the provider request framing")
        assert (await engine.run())["outcome"] == "completed", app.get("app/run")
        writes = [e for _, _, e in runtime.records.scan("effect/")
                  if e["request"]["payload"].get("capability_id") == "files.write"]
        assert len(writes) == 1, "Recovery must not redo the already completed edit"
        assert (await runtime.execute(original)).state == "failed"
        links = runtime.records.scan("recovery/")
        assert len(links) == 1 and links[0][2]["previous_operation_id"] == failure_id
        assert (config.state_path / "result/a.py").read_text() == "VALUE = 2\n"
        assert not runtime.uncertain()
        assert all(a.active == 0 for a in runtime.admission.values())
    finally:
        await runtime.close()


async def test_stopped_active_driver_does_not_spin_the_controller_loop(config):
    from polyinference.agent.tasks import make_task
    from polyinference.domain import Assignment

    runtime = await KernelRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        await engine.initialize()
        task, specs = make_task(app, Assignment(
            task_id="stopped", objective="Retained work", write_paths=["a.py"], read_paths=["a.py"], checks=["syntax"],
        ), "plan/stopped", app.get("head/provisional")["code"], "stopped")
        runtime.records.compare_and_publish(
            {"task/stopped": 0}, {"task/stopped": {**task, "execution": "in_progress"}}, specs
        )
        app.process(task["process_id"], "worker", task["spec_ref"], task)
        runtime.processes.finish(task["process_id"], state="paused")
        app.update("app/run", {**app.get("app/run"), "status": "active", "active_workers": [task["process_id"]]})
        result = await asyncio.wait_for(engine.run(), 2)
        assert result["outcome"] == "paused"
        assert app.get("task/stopped")["execution"] == "interrupted"
        assert not app.get("app/run")["active_workers"]
        assert not runtime.records.scan("effect/")
    finally:
        await runtime.close()


async def test_steering_during_output_delivery_is_reviewed_before_completion(config, monkeypatch):
    runtime = await KernelRuntime(config).open()
    provider = ScriptedAgent(two=False)
    await install(runtime, provider)
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    deliver = runtime.outputs.deliver
    steered = False

    async def incoming_update(delivery_id, files):
        nonlocal steered
        if not steered:
            steered = True
            from polyinference.cli import record_steering

            record_steering(config.state_path, "Review the accepted result again before finishing")
        return await deliver(delivery_id, files)

    monkeypatch.setattr(runtime.outputs, "deliver", incoming_update)
    try:
        assert (await engine.run())["outcome"] == "completed"
        run = app.get("app/run")
        assert run["steering_received"] == run["steering_applied"] == 1
        assert run["acceptance_attempts"] == 2
        assert provider.review_inputs[-1]["user_updates"][0]["sequence"] == 1
        for event in runtime.records.events(limit=1000):
            value = event.get("changes", {}).get("app/run", {}).get("value", {})
            if value.get("status") == "completed":
                assert value["steering_received"] == value["steering_applied"]
    finally:
        await runtime.close()


async def test_worker_requirements_include_only_updates_pinned_to_its_plan(config):
    from test_runtime import setup

    config = config.model_copy(update={"objective": "Build a 2D application"})
    runtime, app, _ = await setup(config)
    observations = []

    class Provider:
        async def generate(self, messages, max_output):
            observations.append(pinned(messages))
            return {"text": '{"kind":"needs_review","reason":"fixture"}', "model": "fixture", "usage": {"total_tokens": 5}}

        async def close(self):
            pass

    await install(runtime, Provider())
    app.update("plan/amended", {"steering_through": 1})
    app.update("steering/00000001", {"sequence": 1, "text": "Use 3D instead of 2D"})
    app.update("steering/00000002", {"sequence": 2, "text": "Add audio after this worker finishes"})
    app.update("fixture-task", {"plan_ref": "plan/amended", "assignment": {
        "task_id": "fixture", "objective": "Implement the view", "write_paths": ["a.py"], "checks": ["syntax"],
    }})
    try:
        await app.model({"process_id": "fixture", "workspace_id": "fixture-ws", "task_ledger_ref": "fixture-task",
                         "phase": "development", "logical_step": 0})
        assert observations[0]["user_objective"] == config.objective
        assert observations[0]["user_updates"] == [{"sequence": 1, "text": "Use 3D instead of 2D"}]
    finally:
        await runtime.close()


async def test_os_stops_repeated_permanent_failures_and_allows_explicit_recovery(config):
    from test_os import model_request
    from test_runtime import setup

    runtime, app, _ = await setup(config)

    class Provider:
        calls = 0
        corrected = False

        async def generate(self, *args):
            self.calls += 1
            if not self.corrected:
                raise ProviderError("Endpoint HTTP 400", category="invalid_request", status=400)
            return {"text": "A non-code answer", "model": "fixture", "usage": {"total_tokens": 3}}

        async def close(self):
            pass

    provider = Provider()
    await install(runtime, provider)
    try:
        first = await runtime.execute(model_request(app, "first"))
        second = await runtime.execute(model_request(app, "replacement-task"))
        blocked = await runtime.execute(model_request(app, "another-name"))
        assert first.state == second.state == blocked.state == "failed"
        assert provider.calls == 2
        assert first.extensions["polyinference/attempted-backend"]["submitted"]
        assert first.extensions["polyinference/provider-error"]["category"] == "invalid_request"
        provider.corrected = True
        runtime.processes.finish("fixture", state="paused")
        request = model_request(app, "explicit-recovery")
        recovered = await runtime.recover_model(second.operation_id, request, "Provider input corrected")
        assert recovered.state == "succeeded"
        assert provider.calls == 3
        assert runtime.processes.status("fixture")["state"] == "ready"
        assert (await runtime.execute(model_request(app, "first"))).state == "failed"
        assert (await runtime.execute(model_request(app, "after-recovery"))).state == "succeeded"
    finally:
        await runtime.close()


async def test_known_model_failure_drains_other_started_workers_before_returning(config):
    failed = asyncio.Event()
    scripted = ScriptedAgent(two=True)

    class Provider:
        async def generate(self, messages, max_output):
            data = pinned(messages)
            assignment = data.get("assignment", {})
            if assignment.get("task_id") == "a" and data.get("phase") == "reconciliation":
                failed.set()
                raise ProviderError("Endpoint HTTP 400", category="invalid_request", status=400)
            if assignment.get("task_id") == "b" and data.get("phase") == "development":
                await asyncio.wait_for(failed.wait(), 10)
            return await scripted.generate(messages, max_output)

        async def close(self):
            pass

    runtime = await KernelRuntime(config).open()
    await install(runtime, Provider())
    app = AgentServices(runtime, config)
    try:
        assert (await ProjectAgent(app).run())["outcome"] == "paused"
        assert app.get("task/a")["execution"] == "interrupted"
        assert app.get("task/b")["execution"] == "completed"
        assert app.get("report/1-b")
        assert not app.get("app/run")["active_workers"]
        assert all(a.active == 0 for a in runtime.admission.values())
        assert not (config.state_path / "result").exists()
    finally:
        await runtime.close()


async def test_os_cancellation_while_queued_prevents_provider_submission(config):
    from test_os import model_request
    from test_runtime import setup

    runtime, app, _ = await setup(config)

    class Provider:
        calls = 0

        async def generate(self, *args):
            self.calls += 1
            raise AssertionError("Cancelled queued request reached provider")

        async def close(self):
            pass

    provider = Provider()
    await install(runtime, provider)
    request = model_request(app, "queued-cancel")
    try:
        admission = runtime.admission["local"]
        async with admission.reserve(admission.token_limit):
            pending = asyncio.create_task(runtime.execute(request))

            async def queued():
                while admission.snapshot()["ordinary_waiters"] == 0:
                    await asyncio.sleep(0)

            await asyncio.wait_for(queued(), 2)
            runtime.processes.cancel("fixture", "Stop queued work")
        result = await pending
        assert result.state == "cancelled" and result.execution_termination == "not_started"
        assert provider.calls == 0
        assert admission.active == 0
        assert not runtime.processes.status("fixture")["pending_operations"]
    finally:
        await runtime.close()
