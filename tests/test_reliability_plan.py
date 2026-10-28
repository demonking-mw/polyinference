"""Regression triggers from retained runs, using disposable state and fixture models."""

import asyncio
import json

import pytest
from test_exception_recovery import connect, seed
from test_progress import decision

from polyinference.agent.worker_memory import LIMIT, project
from polyinference.contracts import ProcessSpec
from polyinference.primitives import canonical


@pytest.mark.parametrize("providers", ["missing", "new", "retained"])
async def test_required_check_paths_need_complete_declared_dependency_ownership(config, providers):
    from langgraph.runtime import Runtime

    from polyinference.agent.senior import validate
    from polyinference.agent.tasks import make_task
    from polyinference.agent.worker import AppContext
    from polyinference.domain import Assignment, Check, SeniorProposal

    config = config.model_copy(update={"allowed_write_paths": ["a.py", "b.py", "c.py"], "closure_paths": [],
        "checks": [*config.checks, Check(name="behavior", argv=["unused-in-plan-validation"],
                                         required_paths=["a.py", "b.py"])]})
    runtime, app, _ = await connect(config)
    try:
        tasks = [Assignment(task_id=name, objective="Provide " + path, write_paths=[path], checks=["syntax"])
                 for name, path in (("pa", "a.py"), ("pb", "b.py"))]
        all_ids = []
        head = app.get("head/provisional")["code"]
        if providers == "retained":
            retained, specs = make_task(app, tasks.pop(0), "plan/test", head, "1-pa")
            app.ports.records.compare_and_publish({"task/pa": 0}, {"task/pa": retained}, specs)
            all_ids.append("pa")
        tasks.append(Assignment(task_id="consumer", objective="Use both inputs", write_paths=["c.py"],
                                checks=["behavior"], dependencies=[] if providers == "missing" else ["pa", "pb"]))
        result = await validate({"reply": SeniorProposal(goal="Connected checks", tasks=tasks).model_dump(mode="json"),
            "input": {"all_task_ids": all_ids, "head": head}, "process_id": "senior-test", "logical_step": 0},
            Runtime(context=AppContext(app)))
        if providers == "missing":
            assert result["route"] == "error" and "Check source closure missing" in result["error"]
        else:
            assert result["route"] == "done", result
        assert not runtime.records.scan("effect/")
    finally:
        await runtime.close()


@pytest.mark.parametrize("failure", ["limits", "location", "destination", "classification", "weights"])
async def test_registration_rejects_unsupported_authority_before_effects(config, failure):
    runtime, app, _ = await connect(config)
    try:
        app.process("control", "senior")
        original = app.get("process-spec/control")
        raw = {**original, "record_id": "process-spec/forged", "process_id": "forged"}
        raw = json.loads(json.dumps(raw))
        if failure == "limits":
            raw["limits"]["max_model_calls"] -= 1
        elif failure == "location":
            raw["schedule"]["data_policy"]["allowed_inference_locations"] = ["local"]
        elif failure == "destination":
            raw["schedule"]["data_policy"]["allowed_destination_classes"] = ["local"]
        elif failure == "classification":
            raw["schedule"]["data_policy"]["maximum_classification"] = "public"
        else:
            rule = raw["schedule"]["distribution"]["rules"][0]
            rule["eligible_classes"] = ["chat", "anthropic"]
            rule["target_weights"] = {"chat": 0.5, "anthropic": 0.5}
        with pytest.raises(ValueError):
            runtime.processes.register(ProcessSpec.model_validate(raw), "cloud")
        assert not runtime.records.get("process/forged")
        assert not runtime.records.scan("effect/")
    finally:
        await runtime.close()


async def test_paused_resident_requires_hibernation_and_readmission(config):
    runtime, app, _ = await connect(config.model_copy(update={"max_workers": 1}))
    try:
        for pid in ("a", "b"):
            app.process(pid, "worker")

        async def pause():
            runtime.processes.finish("a", state="paused")

        await runtime.processes.start("a", pause)
        with pytest.raises(RuntimeError, match="capacity"):
            runtime.processes.start("b", lambda: asyncio.sleep(0))
        runtime.processes.hibernate("a")
        await runtime.processes.start("b", lambda: asyncio.sleep(0))
        runtime.processes.hibernate("a")  # Replay must not release someone else's slot.
        assert runtime.records.get("process-residency/a")[1]["state"] == "hibernated"
        assert runtime.records.get("process-residency/b")[1]["state"] == "released"
    finally:
        await runtime.close()


async def test_returning_terminal_application_driver_releases_residency(config):
    runtime, app, _ = await connect(config.model_copy(update={"max_workers": 1}))
    try:
        app.process("published", "worker")
        app.process("next", "worker")

        async def publish():
            app.process_status("published", state="completed")

        await runtime.processes.start("published", publish)
        assert app.get("process/published")["state"] == "completed"
        assert app.get("process-residency/published")["state"] == "released"
        await runtime.processes.start("next", lambda: asyncio.sleep(0))
    finally:
        await runtime.close()


async def test_worker_ledger_keeps_digest_error_and_replays_without_growth(config):
    runtime, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        await decision(app, state)
        code = (await runtime.workspaces.revision(state["workspace_id"])).model_dump(mode="json")
        first = project(app, state, code)
        assert first["files"]["a.py"]["digest"]
        ref = state["trajectory_ref"]
        state["trajectory_ref"] = app.append_history(ref, "failed-edit", {"kind": "action", "tool": "files.write"},
                                                    {"error": "Write requires current digest"})
        current = project(app, state, code)
        assert "current digest" in current["errors"][0]["summary"]
        version = runtime.records.get("worker-state/" + state["attempt_id"])[0]
        assert project(app, state, code) == current
        assert runtime.records.get("worker-state/" + state["attempt_id"])[0] == version
        assert len(canonical(current)) <= LIMIT
        # A source identity change invalidates remembered CAS facts, not the original evidence.
        altered = {**code, "effective_tree_digest": "sha256:" + "0" * 64}
        assert project(app, state, altered)["files"] == {}
        assert app.history(ref)[-1]["observation"]["digest"]
    finally:
        await runtime.close()


def test_worker_ledger_replay_after_byte_eviction_keeps_the_same_revision():
    from types import SimpleNamespace

    class Records:
        def __init__(self):
            self.rows = {}
        def get(self, key):
            return self.rows.get(key)
        def compare_and_publish(self, expected, updates):
            for key, value in updates.items():
                self.rows[key] = expected[key] + 1, value

    records = Records()
    entries = [{"id": str(i), "reply": {"kind": "action", "tool": "files.read", "arguments": {
        "path": str(i) + "/" + "/".join(["a" * 240] * 4) + "/file.py"}},
        "observation": {"digest": "sha256:" + "1" * 64}} for i in range(16)]
    app = SimpleNamespace(ports=SimpleNamespace(records=records, workspaces=SimpleNamespace(
        current=lambda _: SimpleNamespace(generation=1))), history=lambda _: entries)
    state = {"attempt_id": "bounded", "workspace_id": "workspace", "process_id": "worker",
             "phase": "development", "trajectory_ref": "history"}
    code = {"effective_tree_digest": "sha256:" + "0" * 64, "environment_digest": "sha256:" + "2" * 64}
    first = project(app, state, code)
    revision = records.get("worker-state/bounded")[0]
    assert first["evicted_files"] > 0 and len(canonical(first)) <= LIMIT
    assert project(app, state, code) == first
    assert records.get("worker-state/bounded")[0] == revision


async def test_response_repair_conditions_next_physical_attempt_on_actual_error(config):
    from test_exception_recovery import inputs, output

    runtime, app, engine = await connect(config)
    observed = []

    async def generate(messages, *args, **kwargs):
        observed.append(messages)
        if len(observed) == 1:
            return output({"kind": "assessment", "verdict": "successful", "summary": "Wrong phase"})
        return output({"kind": "candidate", "summary": "Valid phase"})

    runtime.clients["local"].generate = generate
    try:
        state = await seed(app, engine)
        result = await app.model(state)
        assert result["kind"] == "candidate" and len(observed) == 2
        repaired = "\n".join(m["content"] for m in observed[1])
        assert "repair" in repaired.lower() or "phase" in repaired.lower()
        assert any("error" in m["content"] and "current phase/schema" in m["content"] for m in observed[1])
        assert inputs(observed[1])["assignment"]["task_id"] == "a"
        assert runtime.inference_calls_used(state["process_id"]) == 2
        assert not runtime.records.scan("response-repair-error/")
    finally:
        await runtime.close()


def test_qualification_gate_rejects_weak_checks_mixed_pins_and_missing_resume():
    from polyinference.agent.qualification import qualification_gate

    clean = {"status": "completed", "independent_check": "passed", "profile_digest": "same"}
    assert not qualification_gate([clean] * 3)["passed"]
    resumed = {**clean, "interrupted": True, "resume_verified": True}
    assert qualification_gate([clean] * 3 + [resumed])["passed"]
    assert not qualification_gate([clean] * 3 + [{**resumed, "profile_digest": "different"}])["passed"]
    assert not qualification_gate([clean] * 2 + [{**clean, "independent_check": "failed"}, resumed])["passed"]


def test_quality_does_not_count_prepared_work_as_provider_generation():
    from polyinference.agent.qualification import quality

    record = {"request": {"operation_id": "queued", "payload": {"kind": "model_query"}},
              "state": "prepared", "result": None}
    first = quality({"inference-attempt/queued/0": record})
    assert first["physical_raw_generations"] == 0
    assert first["prepared_or_unconfirmed_attempt_records"] == 1
    second = quality({"inference-attempt/queued/0": record,
                      "effect/queued": {"state": "active", "attempted_backend": {"submitted": True}}})
    assert second["physical_raw_generations"] == 1


def test_validation_metrics_keep_raw_and_native_denominators_separate():
    from polyinference.agent.qualification import quality

    def failed(kind, operation):
        return {"request": {"operation_id": operation, "payload": {"kind": kind}},
                "result": {"actual_backend": {"submitted": True}, "error": {"code": "ResponseValidationError"}}}

    result = quality({"inference-attempt/raw/0": failed("model_query", "raw"),
                      "inference-attempt/native/0": failed("agent_job", "native")})
    assert result["response_validation_failures"] == 2
    assert result["raw_response_validation_failures"] == result["native_response_validation_failures"] == 1


def test_native_effects_without_response_retry_rows_are_counted_once():
    from polyinference.agent.qualification import quality

    job = {"request": {"operation_id": "native", "scope": {"process_id": "cloud-worker"},
                       "payload": {"kind": "agent_job"}}, "state": "succeeded",
           "result": {"actual_backend": {"model_version": "cloud-model"}}}
    records = {"effect/native": job, "task/recovery": {"process_id": "cloud-worker", "execution": "completed"}}
    direct = quality(records)
    assert direct["native_jobs"] == direct["task_metrics"]["tasks"][0]["native_jobs"] == 1
    records["inference-attempt/native/0"] = job
    assert quality(records)["native_jobs"] == 1


def test_task_metrics_retain_cancelled_started_work_and_identical_source_queries():
    from polyinference.agent.qualification import quality

    def read(operation):
        return {"request": {"operation_id": operation, "scope": {"process_id": "old"}, "payload": {
            "kind": "capability_call", "capability_id": "files.read", "arguments": {"digest": "same-range"},
            "expected_code": {"effective_tree_digest": "same-tree"}}}}

    result = quality({"task/old": {"process_id": "old", "execution": "cancelled", "started_at": "saved",
                      "assignment": {"dependencies": ["missing"], "role": "worker"}},
                      "task/unstarted": {"process_id": "pending", "execution": "cancelled"},
                      "effect/read1": read("read1"), "effect/read2": read("read2")})["task_metrics"]
    assert result["started_tasks"] == 1
    old = next(t for t in result["tasks"] if t["task_id"] == "old")
    assert old["dependency_waits"] == ["missing"]
    assert old["repeated_tool_queries"]["read"] == {"calls": 2, "identical_repeats": 1, "share": 0.5}


def test_creation_qualification_requires_an_observed_digest_based_update():
    import importlib.util
    from pathlib import Path
    from types import SimpleNamespace

    spec = importlib.util.spec_from_file_location("qualification_harness", Path(__file__).parents[1] / "scripts/qualify_workflow.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    values = {"create": {"path": "solution.py", "expected_digest": None},
              "created": {"digest": "new-digest"}, "update": {"path": "solution.py", "expected_digest": "stale"},
              "updated": {"digest": "updated-digest"}}
    def mutation(step, arguments, output):
        return {"state": "succeeded", "request": {"created_at": step, "payload": {
            "capability_id": "files.write", "arguments": arguments}}, "result": {"output_refs": [output]}}

    records = {"effect/create": mutation("1", "create", "created")}
    app = SimpleNamespace(read=values.__getitem__)
    assert not module.creation_check(app, records, "solution.py")
    records["effect/update"] = mutation("2", "update", "updated")
    assert not module.creation_check(app, records, "solution.py")
    values["update"]["expected_digest"] = "new-digest"
    assert module.creation_check(app, records, "solution.py")


async def test_browser_preflight_uses_check_environment_and_blocks_model_work(config, tmp_path, monkeypatch):
    import importlib.util
    from contextlib import asynccontextmanager
    from pathlib import Path

    spec = importlib.util.spec_from_file_location("qualification_preflight", Path(__file__).parents[1] / "scripts/qualify_workflow.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "profile.json"
    path.write_text(config.model_dump_json())
    output = tmp_path / "new-trials"
    monkeypatch.setattr(module.sys, "argv", ["qualify", "--config", str(path), "--case", "workflow", "--output", str(output)])
    monkeypatch.setenv("QUALIFICATION_BROWSER_TOOLS", str(tmp_path / "tools"))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path / "browsers"))
    closed = []

    class Runtime:
        workspaces = object()
        async def open(self):
            return self
        async def close(self):
            closed.append(True)

    @asynccontextmanager
    async def environment(workspaces):
        assert workspaces is Runtime.workspaces
        yield {"PATH": "/check-tools"}, []

    def unavailable(argv, *, env, **kwargs):
        assert "--tools=" + str(tmp_path / "tools") in argv
        assert "--browsers=" + str(tmp_path / "browsers") in argv
        assert "--preflight" in argv and env == {"PATH": "/check-tools"}
        raise RuntimeError("Browser unavailable before any model work")

    monkeypatch.setattr(module, "KernelRuntime", lambda config: Runtime())
    monkeypatch.setattr(module, "tool_environment", environment)
    monkeypatch.setattr(module.subprocess, "run", unavailable)
    with pytest.raises(RuntimeError, match="before any model work"):
        await module.main()
    assert closed == [True] and not output.exists()


@pytest.mark.parametrize("tool", ["files.write", "files.patch", "files.delete", "shell.run"])
def test_qualification_interrupt_recognizes_every_settled_source_mutation(tool):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location("qualification_interrupt", Path(__file__).parents[1] / "scripts/qualify_workflow.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.settled_edit({"reply": {"tool": tool}, "observation": {"changed": True}})
    assert not module.settled_edit({"reply": {"tool": tool}, "observation": {"changed": True, "error": "failed"}})
    assert not module.settled_edit({"reply": {"tool": "files.read"}, "observation": {"digest": "same"}})


def test_exported_default_drift_is_detected(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[1] / "scripts/settings_docs.py"
    spec = importlib.util.spec_from_file_location("settings_docs_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = tmp_path / "schema.json"
    monkeypatch.setattr(module, "TARGET", target)
    module.run()
    data = json.loads(target.read_text())
    data["RuntimeConfig"]["$defs"]["Endpoint"]["properties"]["reasoning_effort"]["default"] = "low"
    target.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="drift"):
        module.run(check=True)


async def test_unknown_effect_prevents_hibernation_and_preserves_resident_slot(config):
    runtime, app, _ = await connect(config.model_copy(update={"max_workers": 1}))
    try:
        app.process("paused", "worker")
        app.process("next", "worker")
        runtime.processes.admit("paused")
        runtime.records.put_once("effect/unknown-fixture", {
            "request": {"scope": {"process_id": "paused"}}, "state": "uncertain", "result": None})
        runtime.processes.finish("paused", state="paused")
        with pytest.raises(ValueError, match="settled"):
            runtime.processes.hibernate("paused")
        with pytest.raises(RuntimeError, match="capacity"):
            runtime.processes.admit("next")
        assert runtime.records.get("effect/unknown-fixture")[1]["state"] == "uncertain"
    finally:
        await runtime.close()


async def test_resident_admission_survives_runtime_restart(config):
    from polyinference.runtime.kernel import KernelRuntime

    config = config.model_copy(update={"max_workers": 1})
    runtime, app, _ = await connect(config)
    app.process("paused", "worker")
    app.process("next", "worker")
    runtime.processes.admit("paused")
    runtime.processes.finish("paused", state="paused")
    await runtime.close()
    runtime = await KernelRuntime(config).open()
    try:
        with pytest.raises(RuntimeError, match="capacity"):
            runtime.processes.admit("next")
        runtime.processes.hibernate("paused")
        runtime.processes.admit("next")
        assert runtime.records.get("process-residency/next")[1]["state"] == "resident"
    finally:
        await runtime.close()


@pytest.mark.parametrize("reservation_state", ["waiting", "held"])
async def test_physical_reservation_blocks_hibernation_until_released(config, reservation_state):
    runtime, app, _ = await connect(config.model_copy(update={"max_workers": 1}))
    try:
        app.process("paused", "worker")
        app.process("next", "worker")
        runtime.processes.admit("paused")
        runtime.processes.finish("paused", state="paused")
        key = "reservation/local/retained"
        runtime.records.put_once(key, {"process_id": "paused", "state": reservation_state})
        with pytest.raises(ValueError, match="physical reservations"):
            runtime.processes.hibernate("paused")
        with pytest.raises(RuntimeError, match="capacity"):
            runtime.processes.admit("next")
        revision, reservation = runtime.records.get(key)
        runtime.records.compare_and_publish({key: revision}, {key: {**reservation, "state": "released"}})
        runtime.processes.hibernate("paused")
        runtime.processes.admit("next")
    finally:
        await runtime.close()


async def test_replacement_driver_uses_original_account_deadline(tmp_path):
    from datetime import timedelta

    from polyinference.primitives import now
    from polyinference.runtime.processes import Processes
    from polyinference.runtime.storage import Records

    records = Records(tmp_path / "records.sqlite")
    processes = Processes(records, 1)
    records.put_once("process/child", {"state": "ready", "spec_ref": "spec/child", "started_at": now().isoformat()})
    records.put_once("process-status/child", {"state": "ready", "revision": 1})
    records.put_once("spec/child", {"created_at": now().isoformat(), "limits": {"max_wall_time_ms": 60000}})
    records.put_once("process-account/child", {"deadline": (now() + timedelta(milliseconds=50)).isoformat()})
    future = processes.start("child", asyncio.Event().wait)
    try:
        done, _ = await asyncio.wait({future}, timeout=0.3)
        assert future in done, "Replacement driver must not receive a fresh host execution clock"
        with pytest.raises(TimeoutError):
            await future
    finally:
        await processes.close()
        records.db.close()
