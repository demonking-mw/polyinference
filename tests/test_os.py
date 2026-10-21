from __future__ import annotations

import asyncio
import json

import pytest
from conftest import git

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.config import AgentConfig
from polyinference.contracts import OperationRequest
from polyinference.domain import digest
from polyinference.os_contracts import PrivateCommitReceipt, PrivateTaskReport
from polyinference.runtime.inference import Admission, EndpointError, UnknownExecution
from polyinference.runtime.kernel import KernelRuntime, UncertainEffect


def model_request(app, step="model-0"):
    from polyinference.contracts import ModelQuery

    context = app.context("Return a JSON object", {}, [], "fixture", {})
    return app.ensure_request(
        "fixture",
        step,
        ModelQuery(
            role="worker",
            phase="development",
            prompt_template_ref="prompt/1",
            context=context,
            response_schema_ref="worker/1",
            capability_requirements=[],
            temperature=0,
            session_ref=None,
        ),
    )


async def test_budget_actual_settlement_replay_and_process_effect_exclusion(config):
    from test_runtime import setup

    config = config.model_copy(
        update={"local": config.local.model_copy(update={"estimated_microusd_per_token": 2})}
    )
    runtime, app, _ = await setup(config)
    entered, finish = asyncio.Event(), asyncio.Event()

    class Provider:
        calls = 0

        async def generate(self, *args):
            self.calls += 1
            entered.set()
            await finish.wait()
            return {"text": "{}", "model": "fixture", "usage": {"total_tokens": 7}, "events": []}

        async def close(self):
            pass

    client = Provider()
    await runtime.clients["local"].close()
    runtime.clients["local"] = client
    request = model_request(app)
    first = asyncio.create_task(runtime.execute(request))
    try:
        await asyncio.wait_for(entered.wait(), 5)
        assert app.get("budget/run")["reserved_or_used"] > 7
        with pytest.raises(ValueError, match="one top-level"):
            await runtime.execute(model_request(app, "model-1"))
        finish.set()
        result = await first
        assert result.state == "succeeded"
        assert app.get("budget/run")["reserved_or_used"] == 7
        assert app.get("spend/run")["estimated_microusd"] == 14
        assert await runtime.execute(request) == result
        assert client.calls == 1
        assert app.get("budget/run")["reserved_or_used"] == 7
    finally:
        finish.set()
        await asyncio.gather(first, return_exceptions=True)
        await runtime.close()


async def test_model_deadline_before_admission_is_a_known_failure(config):
    from datetime import timedelta

    from test_runtime import setup

    from polyinference.domain import now, operation_fingerprint

    runtime, app, _ = await setup(config)
    request = model_request(app).model_copy(update={"deadline": now() + timedelta(milliseconds=80)})
    request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
    runtime.admission["local"].limit = 1
    try:
        async with runtime.admission["local"].reserve(1):
            result = await runtime.execute(request)
            assert result.state == "failed"
            assert "Admission deadline" in result.error.message
            assert not runtime.uncertain()
            assert runtime.admission["local"].active == 1
            assert not runtime.records.get("budget/run")
        assert runtime.admission["local"].active == 0
    finally:
        await runtime.close()


async def test_grants_logical_identity_and_finishing_lane_cannot_be_forged(config):
    from test_runtime import setup

    from polyinference.domain import operation_fingerprint

    runtime, app, _ = await setup(config)
    try:
        request = model_request(app)
        forged = request.model_copy(update={"conflict_keys": ["verification/project"]})
        forged = forged.model_copy(update={"intent_digest": operation_fingerprint(forged)})
        with pytest.raises(ValueError, match="ownership"):
            await runtime.execute(forged)
        runtime.workspaces.configure_grant("fixture-ws", capabilities=["files.read"])
        result, output = await app.capability(
            {"process_id": "fixture", "workspace_id": "fixture-ws"},
            "denied",
            "files.write",
            {"path": "a.py", "content": "BAD", "expected_digest": digest(b"VALUE = 1\n"), "generation": 1},
            "private_write",
        )
        assert result.state == "failed" and "grant" in output["error"]
        retained = OperationRequest.model_validate(app.get("request/fixture/denied"))
        forged = retained.model_copy(update={"operation_id": "new-alias"})
        forged = forged.model_copy(update={"intent_digest": operation_fingerprint(forged)})
        with pytest.raises(ValueError, match="Logical step"):
            await runtime.execute(forged)
    finally:
        await runtime.close()


async def test_search_patch_paged_reads_and_deleted_file_stays_deleted(config):
    from test_runtime import setup

    runtime, app, _ = await setup(config)
    state = {"process_id": "fixture", "workspace_id": "fixture-ws"}
    try:
        _, found = await app.capability(
            state, "search", "files.search", {"pattern": "VALUE", "generation": 1}
        )
        assert found["matches"][0]["path"] == "a.py"
        _, part = await app.capability(
            state, "read", "files.read", {"path": "a.py", "offset": 2, "limit": 3, "generation": 1}
        )
        assert part["content"] == "LUE" and part["next_offset"] == 5
        result, output = await app.capability(
            state,
            "patch",
            "files.patch",
            {
                "path": "a.py",
                "old_text": "1",
                "new_text": "2",
                "expected_digest": part["digest"],
                "generation": 1,
            },
            "private_write",
        )
        assert result.state == "succeeded"
        await app.capability(
            state,
            "delete",
            "files.delete",
            {"path": "a.py", "expected_digest": output["digest"], "generation": 1},
            "private_write",
        )
        result, output = await app.capability(
            state, "deleted-read", "files.read", {"path": "a.py", "generation": 1}
        )
        assert result.state == "failed" and "deleted" in output["error"]
        assert not (runtime.workspaces.root_for(runtime.workspaces.current("fixture-ws")) / "a.py").exists()
    finally:
        await runtime.close()


async def test_cooperative_cancel_drains_effect_and_exposes_interrupted_task(config):
    from conftest import ScriptedAgent

    runtime = await KernelRuntime(config).open()
    app, client = AgentServices(runtime, config), ScriptedAgent(two=False)
    engine = ProjectAgent(app)
    cancelled = False

    async def hook(data):
        nonlocal cancelled
        if "assignment" in data and not cancelled:
            cancelled = True
            runtime.processes.cancel("worker-1-a", "fixture stop")

    client.hook = hook
    for old in runtime.clients.values():
        await old.close()
    runtime.clients = {"local": client, "cloud": client}
    try:
        await engine.run()
        status = await runtime.processes.wait("worker-1-a", 1)
        assert status["state"] == "cancelled" and status["cancellation_requested"]
        assert not runtime.records.scan("report/")
        assert not app.get("app/run")["active_workers"]
        assert client.review_inputs[0]["interrupted_tasks"][0]["execution"] == "interrupted"
        assert not any(
            body["request"]["payload"].get("capability_id") == "files.read"
            for _, _, body in runtime.records.scan("effect/")
        )
    finally:
        await runtime.close()


async def test_four_workers_failure_retains_commit_drains_and_replans(config):
    for name in "cde":
        (config.repo_path / (name + ".py")).write_text("VALUE = 1\n")
    git(config.repo_path, "add", ".")
    git(
        config.repo_path,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=t@localhost",
        "commit",
        "-qm",
        "more files",
    )
    config = config.model_copy(
        update={
            "allowed_write_paths": [n + ".py" for n in "abcde"],
            "max_workers": 4,
            "senior_development_fraction": 0,
            "limits": config.limits.model_copy(update={"max_input_tokens_per_call": 64000}),
            "local": config.local.model_copy(
                update={"max_inflight": 4, "max_context_tokens": 128000, "reserved_context_tokens": 512000}
            ),
            "cloud": config.cloud.model_copy(
                update={"max_context_tokens": 128000, "reserved_context_tokens": 128000}
            ),
        }
    )
    runtime = await KernelRuntime(config).open()
    app, failure_published = AgentServices(runtime, config), asyncio.Event()
    engine = ProjectAgent(app)
    entered, calls = set(), {}
    all_started = asyncio.Event()
    review_count = 0
    initial_head = None
    publish = runtime._publish

    def observe_publish(batch, pid):
        publish(batch, pid)
        for key, report in batch["immutable"].items():
            if key.startswith("report/") and report["verdict"] == "fail":
                assert app.get("head/provisional")["code"] == initial_head
                assert app.get("app/run")["starts_closed"]
                assert len(app.get("app/run")["captured_workers"]) == 4
                assert app.get("task/e")["execution"] == "pending"
                failure_published.set()

    runtime._publish = observe_publish

    def assignment(name, path=None):
        return {
            "task_id": name,
            "objective": "Set value to two",
            "write_paths": [path or name + ".py"],
            "read_paths": [path or name + ".py"],
            "checks": ["syntax"],
        }

    class Provider:
        async def generate(self, messages, *args):
            nonlocal review_count, initial_head
            data = json.loads(
                next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
                    "Pinned application inputs:\n", 1
                )[1]
            )
            if "assignment" not in data:
                if not data["all_task_ids"]:
                    initial_head = data["head"]
                    reply = {"goal": "Concurrent update", "tasks": [assignment(n) for n in "abcde"]}
                else:
                    review_count += 1
                    assert not app.get("app/run")["active_workers"]
                    assert not runtime.records.get("permit/verification/project")[1]["process_id"]
                    assert "e" not in entered
                    if review_count == 1:
                        assert len(data["reports"]) == 4
                        assert {r["code_location"] for r in data["reports"]} == {"private", "provisional"}
                        reply = {
                            "goal": "Repair failed task",
                            "tasks": [assignment("repair", "a.py")],
                            "cancel_pending_task_ids": ["e"],
                            "dispositions": [
                                {
                                    "report_ref": r["record_id"],
                                    "action": "retry" if r["verdict"] == "fail" else "keep",
                                    "reason": "Reviewed drained sprint",
                                }
                                for r in data["reports"]
                            ],
                        }
                    else:
                        reply = {
                            "goal": "Finished",
                            "complete": True,
                            "dispositions": [
                                {
                                    "report_ref": r["record_id"],
                                    "action": "revert" if r["code_location"] == "private" else "keep",
                                    "reason": "Private candidate superseded by checked repair",
                                }
                                for r in data["reports"]
                            ],
                        }
            else:
                task, phase = data["assignment"], data["phase"]
                name = task["task_id"]
                if name in "abcd" and phase == "development":
                    entered.add(name)
                    if len(entered) == 4:
                        all_started.set()
                    await asyncio.wait_for(all_started.wait(), 15)
                    if name != "a":
                        await asyncio.wait_for(failure_published.wait(), 15)
                key = (name, phase)
                count = calls.get(key, 0)
                calls[key] = count + 1
                if phase == "development" and count == 0:
                    reply = {
                        "kind": "action",
                        "tool": "files.write",
                        "arguments": {
                            "path": task["write_paths"][0],
                            "content": "VALUE = 2\n",
                            "expected_digest": digest(b"VALUE = 1\n"),
                        },
                    }
                elif phase == "assessment":
                    reply = {
                        "kind": "assessment",
                        "verdict": "fail" if name == "a" else "successful",
                        "summary": "Exact-tree assessment",
                    }
                else:
                    reply = {"kind": "candidate", "summary": "Reconciled"}
            return {
                "text": json.dumps(reply),
                "usage": {"total_tokens": 10},
                "model": "fixture",
                "events": [],
            }

        async def close(self):
            pass

    for client in runtime.clients.values():
        await client.close()
    runtime.clients = {"local": Provider(), "cloud": Provider()}
    try:
        await asyncio.wait_for(engine.run(), 90)
        assert app.get("app/run")["status"] == "completed", app.get("app/run")
        assert review_count == 2
        failed = PrivateTaskReport.model_validate(app.get("report/1-a"))
        receipt = PrivateCommitReceipt.model_validate(app.get(failed.publication_receipt_ref))
        assert receipt.candidate == failed.final_code
        head = app.get("head/provisional")["code"]
        tree = await runtime.workspaces.tree(head["commit_id"])
        assert all(tree[n + ".py"][1] == b"VALUE = 2\n" for n in "abcd")
        assert tree["e.py"][1] == b"VALUE = 1\n"
        ancestors = (await runtime.workspaces.git("rev-list", head["commit_id"])).decode().splitlines()
        assert failed.candidate_commit_id not in ancestors
        assert app.get("task/e")["execution"] == "cancelled"
        assert not runtime.uncertain()
        assert all(v.active == 0 for v in runtime.admission.values())
        assert git(config.repo_path, "status", "--porcelain") == ""
        # Simulate losing the result after private receipt commit, then restart.
        # The receipt settles the exact original intent even after head/owner move.
        effect_key = "effect/" + receipt.publication_operation_id
        retained = app.get(effect_key)
        app.update(effect_key, {**retained, "state": "active", "result": None})
        await runtime.close()
        runtime = await KernelRuntime(config).open()
        assert not runtime.uncertain()
        settled = await runtime.execute(OperationRequest.model_validate(retained["request"]))
        assert settled.state == "succeeded"
        assert json.loads(runtime.artifacts.read(settled.output_refs[0]))["code_location"] == "private"
        assert runtime.records.get("head/provisional")[1]["code"] == head
        assert len(runtime.records.scan("report/")) == 5
    finally:
        await runtime.close()


async def test_admission_deadline_cancel_and_alternating_finishing_lane():
    admission = Admission(1, 100)
    order = []

    async def enter(name, finishing=False):
        async with admission.reserve(10, finishing):
            order.append(name)
            await asyncio.sleep(0)

    async with admission.reserve(100):
        with pytest.raises(EndpointError, match="deadline"):
            async with admission.reserve(1, timeout=0.01):
                pytest.fail("expired waiter admitted")
        cancelled = asyncio.create_task(enter("cancelled"))
        await asyncio.sleep(0)
        cancelled.cancel()
        await asyncio.gather(cancelled, return_exceptions=True)
        waiters = [
            asyncio.create_task(enter("ordinary1")),
            asyncio.create_task(enter("ordinary2")),
            asyncio.create_task(enter("finish1", True)),
            asyncio.create_task(enter("finish2", True)),
        ]
        await asyncio.sleep(0)
    await asyncio.gather(*waiters)
    assert order == ["finish1", "ordinary1", "finish2", "ordinary2"]
    assert admission.active == admission.tokens == 0


def test_environment_batch_size_is_validated_and_cloud_substitution(config, monkeypatch):
    monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", "1")
    pinned = AgentConfig.model_validate(config.model_dump())
    assert pinned.local.max_inflight == 1
    monkeypatch.setenv("POLYINFERENCE_LOCAL_BATCH_SIZE", "0")
    with pytest.raises(ValueError):
        AgentConfig.model_validate(config.model_dump())


async def test_unknown_capacity_survives_restart_and_explicit_reconciliation(config):
    from test_runtime import setup

    runtime, app, _ = await setup(config)

    class Disconnect:
        async def generate(self, *args):
            raise UnknownExecution("sent, then disconnected")

        async def close(self):
            pass

    await runtime.clients["local"].close()
    runtime.clients["local"] = Disconnect()
    app.update(
        "fixture-task",
        {
            "assignment": {
                "task_id": "fixture",
                "objective": "test",
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
    }
    with pytest.raises(UncertainEffect):
        await app.model(state)
    op = runtime.uncertain()[0]
    reserved = runtime.admission["local"].tokens
    await runtime.close()
    runtime = await KernelRuntime(config).open()
    try:
        assert runtime.admission["local"].active == 1
        assert runtime.admission["local"].tokens == reserved
        with pytest.raises(ValueError, match="evidence"):
            await runtime.reconcile_stopped(op, "")
        await runtime.reconcile_stopped(op, "Fixture provider has terminated; it never starts host tools.")
        assert not runtime.uncertain()
        assert runtime.admission["local"].active == runtime.admission["local"].tokens == 0
        assert runtime.processes.status("fixture")["cleanup_state"] == "complete"
        assert runtime.processes.status("fixture")["state"] == "paused"
        retained = runtime.records.get("effect/" + op)[1]
        result = await runtime.execute(OperationRequest.model_validate(retained["request"]))
        assert result.state == "failed" and result.execution_termination == "confirmed_stopped"
    finally:
        await runtime.close()


async def test_filesystem_cancellation_joins_mutation_without_blocking_loop():
    import threading

    from polyinference.runtime.blocking import BlockingIO

    io = BlockingIO()
    started, release, completed = threading.Event(), threading.Event(), threading.Event()

    def mutation():
        started.set()
        assert release.wait(5)
        completed.set()

    task = asyncio.create_task(io.run(mutation))
    try:
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.01)
        assert started.is_set()
        task.cancel()
        await asyncio.sleep(0.01)
        assert not task.done() and not completed.is_set()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert completed.is_set()
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)
        io.close()


async def test_status_handles_pending_tasks_and_publication_requires_minted_commit(
    config, monkeypatch, capsys
):
    from polyinference.cli import main

    runtime = await KernelRuntime(config).open()
    app = AgentServices(runtime, config)
    await ProjectAgent(app).initialize()
    try:
        app.update("task/pending", {"process_id": "pending", "execution": "pending", "report_ref": None})
        monkeypatch.setattr("sys.argv", ["polyinference", "status", str(config.state_path)])
        main()
        status = json.loads(capsys.readouterr().out)
        assert status["tasks"][0]["resolved"] is False
        permit = await runtime.exclusive.acquire("verification/project", "controller")
        head_version, head = runtime.records.get("head/provisional")
        with pytest.raises(ValueError, match="broker commit"):
            runtime._publish(
                {
                    "receipt_ref": "publication/forged",
                    "permit_ref": permit,
                    "expected": {"head/provisional": head_version},
                    "updates": {"head/provisional": head},
                    "immutable": {},
                },
                "controller",
            )
        assert runtime.records.get("head/provisional") == (head_version, head)
        await runtime.exclusive.release(permit, "controller")
    finally:
        await runtime.close()


async def test_bounded_command_output_and_timeout():
    import sys

    from polyinference.runtime.commands import command

    with pytest.raises(ValueError, match="output"):
        await command([sys.executable, "-c", "print('x' * 10000)"], timeout=5, output_limit=100)
    with pytest.raises(asyncio.TimeoutError):
        await command([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.1, output_limit=100)
