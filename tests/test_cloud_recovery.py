"""Real controller/runtime with deterministic model replies; no live provider calls."""

from __future__ import annotations

import pytest
from conftest import ScriptedAgent
from test_exception_recovery import connect, inputs, output, seed

from polyinference.agent.architecture import validate_plan
from polyinference.agent.cloud_recovery import capabilities, offer, prepare
from polyinference.agent.exceptions import park, validate, validate_sources
from polyinference.agent.prompts import SENIOR
from polyinference.agent.routing import allocate
from polyinference.agent.tasks import make_task
from polyinference.domain import Assignment, SeniorProposal


async def parked(config, **updates):
    runtime, app, engine = await connect(config)
    state = await seed(app, engine)
    if updates:
        app.update("task/a", {**app.get("task/a"), **updates})
    await park(app, state)
    packet = app.get("worker-exception/1-a")
    return runtime, app, engine, packet


@pytest.mark.parametrize("action", ["omitted", "defer", "stop", "retry"])
async def test_local_failure_gets_cloud_implementation_even_after_ordinary_depth(config, action):
    runtime, app, _, packet = await parked(config, recovery_depth=config.max_worker_recoveries)
    try:
        raw = {"goal": "No productive local work"}
        if action != "omitted":
            raw["exception_dispositions"] = [{
                "exception_ref": packet["exception_ref"], "action": action, "reason": "Local exhausted",
                **({"replacement_task_id": "a2", "changed_condition": "Read a narrower boundary"}
                   if action == "retry" else {}),
            }]
        if action == "retry":
            raw["tasks"] = [{**packet["assignment"], "task_id": "a2"}]
        snapshot = {"exceptions": [packet], "head": app.get("head/provisional")["code"]}
        proposal, changes = await prepare(app, SeniorProposal.model_validate(raw), snapshot)
        task = proposal.tasks[0]
        assert task.role == "specialist" and not proposal.complete
        assert proposal.exception_dispositions[0].action == "retry"
        assert changes[0]["model_action"] == action
        if action == "retry":
            assert "Read a narrower boundary" in proposal.exception_dispositions[0].changed_condition
            assert changes[0]["source"] == "fresh current base (senior choice)"
        replacements = validate(app, proposal, snapshot)
        validate_plan(proposal, [app.get("task/a")], {})
        await validate_sources(app, proposal, replacements, snapshot["head"])
        assert allocate(proposal.tasks, [], 0, protected_task_ids=replacements)[0].role == "specialist"
        new, _ = make_task(app, task, "plan/next", snapshot["head"], "2-a", predecessor=packet)
        assert new["cloud_recoveries"] == 1
        assert new["recovery_depth"] == config.max_worker_recoveries + 1
        assert new["previous_process_id"] == packet["process_id"]
        assert new["root_task_id"] == packet["root_task_id"]
        # Normalization is stable under replay, not a second new recovery task.
        replay, _ = await prepare(app, proposal, snapshot)
        assert replay.tasks == proposal.tasks
    finally:
        await runtime.close()


async def test_fallback_rewires_transitive_pending_consumers_without_mutating_old_tasks(config):
    runtime, app, engine, packet = await parked(config)
    try:
        for name, dependencies in (("b", ["a"]), ("c", ["b"])):
            assignment = Assignment(task_id=name, objective="Consume upstream behavior",
                                    write_paths=["b.py"], dependencies=dependencies, checks=["syntax"])
            task, specs = make_task(app, assignment, "plan/test", packet["original_base"], "1-" + name)
            app.ports.records.compare_and_publish({"task/" + name: 0}, {"task/" + name: task}, specs)
        originals = [v for _, _, v in runtime.records.scan("task/")]
        proposal, _ = await prepare(app, SeniorProposal(goal="Defer local failure"),
                                    {"exceptions": [packet], "head": packet["original_base"]})
        assert set(proposal.cancel_pending_task_ids) == {"b", "c"}
        by_id = {t.task_id: t for t in proposal.tasks}
        assert by_id["b_rewired"].dependencies == ["a_cloud"]
        assert by_id["c_rewired"].dependencies == ["b_rewired"]
        assert app.get("task/b")["assignment"]["dependencies"] == ["a"]
        validate_plan(proposal, originals, {})
        for client in runtime.clients.values():
            await client.close()
        runtime.clients = {name: NoopSenior() for name in runtime.clients}
        await engine.review()
        assert app.get("task/b")["execution"] == app.get("task/c")["execution"] == "cancelled"
        assert app.get("task/b_rewired")["assignment"]["dependencies"] == ["a_cloud"]
        assert app.get("task/c_rewired")["assignment"]["dependencies"] == ["b_rewired"]
        assert engine.ready() == ["task/a_cloud"]
    finally:
        await runtime.close()


class NoopSenior(ScriptedAgent):
    def __init__(self):
        super().__init__(two=False)
        self.worker_inputs = []
        self.senior_inputs = []

    async def generate(self, messages, *args, **kwargs):
        data = inputs(messages)
        if "assignment" in data:
            self.worker_inputs.append(data)
            return output({"kind": "assessment", "verdict": "successful", "summary": "Checked exact retained tree"}
                          if data["phase"] == "assessment" else {"kind": "candidate", "summary": "Ready"})
        self.senior_inputs.append(data)
        if data.get("exceptions"):
            return output({"goal": "No further local retry", "user_brief": "Local work stalled"})
        return await super().generate(messages, *args, **kwargs)


async def test_noop_senior_dispatches_real_cloud_worker_and_keeps_shared_account(config):
    config = config.model_copy(update={"max_worker_recoveries": 0, "senior_development_fraction": 0})
    runtime, app, engine, packet = await parked(config)
    client = NoopSenior()

    class LocalMustNotRun:
        async def generate(self, *args, **kwargs):
            pytest.fail("Cloud recovery dispatched to the local endpoint")

        async def close(self):
            pass

    try:
        for old in runtime.clients.values():
            await old.close()
        runtime.clients = {"local": LocalMustNotRun(), "cloud": client}
        original_deadline = runtime.resource_state(packet["process_id"])["deadline"]
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        task = app.get("task/a_cloud")
        assert task["assignment"]["role"] == "specialist"
        assert runtime.account(task["process_id"]) == packet["process_id"]
        assert runtime.resource_state(task["process_id"])["deadline"] == original_deadline
        assert runtime.inference_calls_used(task["process_id"]) == 3
        assert runtime.records.get("handoff/" + task["workspace_id"])
        assert client.worker_inputs[0]["recovery_context"]["reason"] == packet["reason"]
        assert client.worker_inputs[0]["recovery_context"]["source_reused"]
        assert "Cloud specialist" in client.worker_inputs[0]["recovery_context"]["changed_condition"]
        assert client.senior_inputs[0]["cloud_recovery_policy"]["offers"][0]["eligible"]
        assert client.senior_inputs[0]["runtime_capabilities"]["browser"] is False
        record = app.get("proposal/senior-1")
        assert not record["model_proposal"]["tasks"]
        assert record["policy_adjustments"][0]["effective_role"] == "specialist"
        assert "Cloud recovery policy scheduled" in record["proposal"]["user_brief"]
    finally:
        await runtime.close()


@pytest.mark.parametrize("blocker", ["disabled", "binding", "calls", "tokens", "steps", "deadline",
                                  "unknown", "cancel", "published", "setup", "cloud_exhausted"])
async def test_hard_boundaries_do_not_create_cloud_work(config, monkeypatch, blocker):
    runtime, app, _, packet = await parked(config)
    try:
        if blocker == "disabled":
            app.config = config.model_copy(update={"max_cloud_recoveries": 0})
        elif blocker == "binding":
            app.config = config.model_copy(update={"role_bindings": {**config.role_bindings, "specialist": "local"}})
        elif blocker == "calls":
            runtime.records.put_once("budget/model-calls/" + packet["process_id"],
                                     {"used": config.limits.max_model_calls})
        elif blocker in {"tokens", "steps"}:
            resource = runtime.resource_state(packet["process_id"])
            resource["remaining_tokens" if blocker == "tokens" else "remaining_operations"] = 0
            monkeypatch.setattr(runtime, "resource_state", lambda pid: resource)
        elif blocker == "deadline":
            process = app.get("process/" + packet["process_id"])
            app.update("process/" + packet["process_id"], {**process, "started_at": "2000-01-01T00:00:00+00:00"})
        elif blocker == "unknown":
            runtime.records.put_once("effect/unknown", {"state": "uncertain", "request": {}, "result": None})
        elif blocker == "cancel":
            app.update("process-control/" + packet["process_id"], {"cancel_requested": True})
        elif blocker in {"published", "setup"}:
            task = app.get("task/a")
            app.update("task/a", {**task, **({"report_ref": "report/test"} if blocker == "published"
                                           else {"category": "setup"})})
        else:
            packet = {**packet, "cloud_recoveries": config.max_cloud_recoveries}
        snapshot = {"exceptions": [packet], "head": packet["original_base"]}
        choice = await offer(app, packet, snapshot["head"])
        assert not choice["eligible"] and choice["reason"]
        proposal, changes = await prepare(app, SeniorProposal(goal="Leave blocked work visible"), snapshot)
        assert not changes and not proposal.tasks
    finally:
        await runtime.close()


async def test_conflicting_delta_uses_current_base_without_discarding_evidence(config, monkeypatch):
    runtime, app, _, packet = await parked(config)
    try:
        async def conflict(*args, **kwargs):
            raise ValueError("conflicts with changed current base")

        monkeypatch.setattr(runtime.workspaces, "validate_handoff", conflict)
        snapshot = {"exceptions": [packet], "head": packet["original_base"]}
        proposal, changes = await prepare(app, SeniorProposal(goal="Repair current base"), snapshot)
        assert proposal.tasks[0].resume_from is None
        assert "fresh current base" in changes[0]["source"]
        await validate_sources(app, proposal, validate(app, proposal, snapshot), snapshot["head"])
        assert app.get(packet["source_delta_ref"])["changes"]
    finally:
        await runtime.close()


async def test_cloud_failure_cannot_reset_count_or_bounce_to_local(config):
    runtime, app, _, packet = await parked(config, cloud_recoveries=1)
    try:
        for role, message in (("specialist", "Cloud recovery allowance"), ("worker", "Semantic recovery allowance")):
            proposal = SeniorProposal.model_validate({"goal": "Try again", "tasks": [{
                **packet["assignment"], "task_id": "again", "role": role, "resume_from": packet["exception_ref"],
            }], "exception_dispositions": [{"exception_ref": packet["exception_ref"], "action": "retry",
                "replacement_task_id": "again", "changed_condition": "New endpoint", "reason": "Try"}]})
            with pytest.raises(ValueError, match=message):
                validate(app, proposal, {"exceptions": [packet]})
    finally:
        await runtime.close()


async def test_role_rename_on_same_backend_is_not_a_changed_recovery_condition(config):
    config = config.model_copy(update={"role_bindings": {**config.role_bindings, "specialist": "local"}})
    runtime, app, _, packet = await parked(config)
    try:
        proposal = SeniorProposal.model_validate({"goal": "Rename", "tasks": [{
            **packet["assignment"], "task_id": "renamed", "role": "specialist",
        }], "exception_dispositions": [{"exception_ref": packet["exception_ref"], "action": "retry",
            "replacement_task_id": "renamed", "changed_condition": "Different role label", "reason": "Try"}]})
        with pytest.raises(ValueError, match="Renaming"):
            validate(app, proposal, {"exceptions": [packet]})
    finally:
        await runtime.close()


async def test_pending_recovery_consumer_cannot_be_cloned_with_a_fresh_account(config):
    runtime, app, _, packet = await parked(config)
    try:
        assignment = Assignment(task_id="b", objective="Consume provider", write_paths=["b.py"],
                                dependencies=["a"], checks=["syntax"])
        task, specs = make_task(app, assignment, "plan/test", packet["original_base"], "1-b")
        task["previous_process_id"] = "retained-budget-root"
        app.ports.records.compare_and_publish({"task/b": 0}, {"task/b": task}, specs)
        with pytest.raises(ValueError, match="lineage-preserving"):
            await prepare(app, SeniorProposal(goal="Recover provider"),
                          {"exceptions": [packet], "head": packet["original_base"]})
        assert app.get("task/b") == task
    finally:
        await runtime.close()


async def test_aliased_endpoint_is_not_automatic_cloud_recovery(config):
    runtime, app, _, packet = await parked(config.model_copy(update={"cloud": config.local}))
    try:
        result = await offer(app, packet, packet["original_base"])
        assert not result["eligible"] and "different declared" in result["reason"]
    finally:
        await runtime.close()


async def test_disabling_cloud_takeover_preserves_ordinary_local_recovery(config):
    from test_exception_recovery import Recovering

    from polyinference.config import CheckDiagnosis

    config = config.model_copy(update={"max_cloud_recoveries": 0,
                                       "check_diagnosis": CheckDiagnosis(max_rounds=0)})
    runtime, app, engine = await connect(config, Recovering(two=False))
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        new = app.get("task/a2")
        assert new["assignment"]["role"] == "worker" and new["cloud_recoveries"] == 0
        assert app.get("process-status/" + new["process_id"])["binding_ref"] == "local"
        assert runtime.account(new["process_id"]) == app.get("task/a")["process_id"]
    finally:
        await runtime.close()


@pytest.mark.parametrize("boundary", ["conflict", "after_publish"])
async def test_pending_linked_consumer_retargets_original_exception_without_new_allowance(config, monkeypatch, boundary):
    from polyinference.agent.exceptions import review_view
    from polyinference.contracts import CodeRevision
    from polyinference.ports import RecordConflict

    config = config.model_copy(update={
        "limits": config.limits.model_copy(update={"max_input_tokens_per_call": 96000}),
        "cloud": config.cloud.model_copy(update={"max_context_tokens": 128000, "reserved_context_tokens": 256000}),
    })
    runtime, app, engine, provider = await parked(config)
    try:
        base = provider["original_base"]
        original = Assignment(task_id="b", objective="Consume a", write_paths=["b.py"],
                              dependencies=["a"], checks=["syntax"])
        task, specs = make_task(app, original, "plan/test", base, "1-b")
        task["execution"] = "in_progress"
        app.ports.records.compare_and_publish({"task/b": 0}, {"task/b": task}, specs)
        app.process(task["process_id"], "worker", task["spec_ref"], task)
        await runtime.workspaces.create(task["workspace_id"], task["process_id"], task["spec_ref"],
                                        CodeRevision.model_validate(base), ["b.py"], [])
        await park(app, {"process_id": task["process_id"], "workspace_id": task["workspace_id"],
                         "attempt_id": task["attempt_id"], "task_ledger_ref": "task/b",
                         "task_spec_ref": task["spec_ref"], "phase": "development",
                         "logical_step": 0, "interrupted": "Known consumer failure", "evidence": [],
                         "verification_permit_ref": None})
        predecessor = app.get("worker-exception/1-b")
        queued = original.model_copy(update={"task_id": "b_repair", "resume_from": predecessor["exception_ref"]})
        pending, specs = make_task(app, queued, "plan/test", base, "2-b_repair", predecessor=predecessor)
        app.ports.records.compare_and_publish({"task/b_repair": 0}, {"task/b_repair": pending}, specs)
        app.update("exception-queue/1-b", {"exception_ref": predecessor["exception_ref"],
                   "action": "retry", "replacement_task_id": "b_repair"})
        snapshot = {"exceptions": review_view(app), "head": base}
        proposal, _ = await prepare(app, SeniorProposal(goal="Replace failed provider"), snapshot)
        linked = validate(app, proposal, snapshot)
        assert "b_repair" in proposal.cancel_pending_task_ids
        replacement = next(t for t in proposal.tasks if t.task_id.startswith("b_repair_rewired"))
        fresh, _ = make_task(app, replacement, "plan/next", base, "3-b", predecessor=linked[replacement.task_id])
        assert fresh["root_task_id"] == pending["root_task_id"]
        assert fresh["recovery_depth"] == pending["recovery_depth"]
        assert fresh["previous_process_id"] == pending["previous_process_id"]
        assert app.get("task/b_repair") == pending
        assert not app.ports.records.get("process/" + pending["process_id"])
        deadline = runtime.resource_state(predecessor["process_id"])["deadline"]
        for client in runtime.clients.values():
            await client.close()
        runtime.clients = {name: NoopSenior() for name in runtime.clients}
        publish = runtime.records.compare_and_publish
        queue_key = "exception-queue/1-b"

        def interrupt_transaction(expected, updates, immutable=None):
            if "task/b_repair_rewired" in updates:
                if boundary == "conflict":
                    return publish({**expected, queue_key: expected[queue_key] + 1}, updates, immutable)
                publish(expected, updates, immutable)
                raise RuntimeError("Crash after atomic successor publication")
            return publish(expected, updates, immutable)

        monkeypatch.setattr(runtime.records, "compare_and_publish", interrupt_transaction)
        with pytest.raises(RecordConflict if boundary == "conflict" else RuntimeError):
            await engine.review()
        if boundary == "conflict":
            assert app.get("task/b_repair")["execution"] == "pending"
            assert app.get(queue_key)["replacement_task_id"] == "b_repair"
            assert not runtime.records.get("task/b_repair_rewired")
        monkeypatch.setattr(runtime.records, "compare_and_publish", publish)
        await runtime.close()
        runtime, app, engine = await connect(config, NoopSenior())
        await engine.review()  # Resume the retained transaction without another senior proposal.
        current = app.get("task/b_repair_rewired")
        assert app.get("task/b_repair")["execution"] == "cancelled"
        assert app.get(queue_key)["replacement_task_id"] == "b_repair_rewired"
        assert app.get("task/b")["replacement_task_id"] == "b_repair_rewired"
        assert len([k for k, _, _ in runtime.records.scan("task/") if k == "task/b_repair_rewired"]) == 1
        assert current["previous_process_id"] == pending["previous_process_id"]
        app.process(current["process_id"], current["assignment"]["role"], current["spec_ref"], current)
        assert runtime.account(current["process_id"]) == predecessor["process_id"]
        assert runtime.resource_state(current["process_id"])["deadline"] == deadline
    finally:
        await runtime.close()


def test_planner_prompt_and_capabilities_describe_real_limits_and_small_behaviors(config):
    for shell in ("disabled", "trusted"):
        view = capabilities(config.model_copy(update={"shell_execution": shell}))
        assert ("shell.run" in view["worker_tools"]) == (shell != "disabled")
        assert not view["browser"] and not view["mcp"] and not view["persistent_services"]
        assert "repository.select_branch" not in view["worker_tools"]
    instruction = " ".join(SENIOR.split())
    assert "movement/input, collision, save/load and migration" in instruction
    assert "read_requests" in instruction and "no browser API/MCP/persistent services" in instruction


def test_allocation_cannot_promote_a_validated_local_recovery_past_disabled_cloud_policy():
    local = Assignment(task_id="local_retry", objective="Repair one behavior",
                       write_paths=["a.py"], checks=["syntax"])
    other = local.model_copy(update={"task_id": "ordinary"})
    recovery, ordinary = allocate([local, other], [], 1, protected_task_ids={local.task_id})
    assert recovery.role == "worker" and ordinary.role == "specialist"
