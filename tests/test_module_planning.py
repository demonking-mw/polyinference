"""Module contracts survive planning, worker execution, review and plan replacement."""

from __future__ import annotations

import json

import pytest
from conftest import ScriptedAgent
from langgraph.runtime import Runtime

from polyinference.agent.architecture import catalog, pinned_context, validate_plan
from polyinference.agent.controller import ProjectAgent
from polyinference.agent.senior import validate
from polyinference.agent.services import AgentServices
from polyinference.agent.worker import AppContext
from polyinference.domain import Assignment, InterfaceContract, SeniorProposal
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.ui import TestUI


def interface(version=1, **updates):
    return InterfaceContract(
        **{
            "interface_id": "motion",
            "version": version,
            "description": "Simulation state consumed by the renderer",
            "inputs": "tick(state, intent), dt=0.05 seconds; x/y world units, y increases down",
            "outputs": "New state with fractional x/y, vx/vy in world units per second; no z",
            "invariants": ["Do not mutate input state; rendering only reads the returned snapshot"],
            "verification": ["Pass one returned physics snapshot directly to rendering"],
            "change_reason": "Add velocity representation; migrate the renderer" if version > 1 else "",
            **updates,
        }
    )


def assignment(name, **updates):
    return Assignment(
        **{
            "task_id": name,
            "objective": f"Implement the bounded {name} module",
            "write_paths": [name + ".py"],
            "read_paths": [name + ".py"],
            "checks": ["syntax"],
            "acceptance_criteria": ["Returned state matches the agreed data shape"],
            "non_goals": ["Do not build inventory or menus"],
            **updates,
        }
    )


def ledger(task, execution="pending"):
    return {"assignment": task.model_dump(mode="json"), "execution": execution}


def test_shared_boundary_requires_real_definition_and_module_acceptance():
    with pytest.raises(ValueError, match="acceptance_criteria"):
        assignment("a", provides=["motion@1"], acceptance_criteria=[])
    with pytest.raises(ValueError):
        assignment("a", consumes=["motion"])
    with pytest.raises(ValueError, match="unknown interface"):
        validate_plan(SeniorProposal(goal="render", tasks=[assignment("b", consumes=["motion@1"])]), [], {})
    with pytest.raises(ValueError, match="change_reason"):
        interface(2, change_reason="")


def test_consumer_requires_transitive_unfinished_provider_dependency():
    provider = assignment("a", provides=["motion@1"])
    bridge = assignment("bridge", dependencies=["a"])
    consumer = assignment("b", consumes=["motion@1"], dependencies=["bridge"])
    plan = SeniorProposal(
        goal="connect modules", tasks=[provider, bridge, consumer], interface_contracts=[interface()]
    )
    assert "motion@1" in validate_plan(plan, [], {})
    plan = plan.model_copy(update={"tasks": [provider, consumer.model_copy(update={"dependencies": []})]})
    with pytest.raises(ValueError, match="unfinished provider"):
        validate_plan(plan, [], {})
    # An existing implementation may be described without inventing a provider task.
    validate_plan(
        SeniorProposal(
            goal="render existing state", tasks=[consumer.model_copy(update={"dependencies": []})]
        ),
        [],
        {"motion@1": interface()},
    )


def test_replacement_validates_retained_dependencies_before_retiring_work():
    tasks = [ledger(assignment("a")), ledger(assignment("b", dependencies=["a"]))]
    proposal = SeniorProposal(goal="replace a", cancel_pending_task_ids=["a"], tasks=[assignment("a2")])
    with pytest.raises(ValueError, match="cancelled dependency"):
        validate_plan(proposal, tasks, {})
    with pytest.raises(ValueError, match="unstarted"):
        validate_plan(proposal, [ledger(assignment("a"), "in_progress")], {})
    replacement = proposal.model_copy(update={"cancel_pending_task_ids": ["a", "b"]})
    validate_plan(replacement, tasks, {})


def test_contract_versions_cannot_silently_retarget_pending_consumers():
    contracts = {"motion@1": interface()}
    with pytest.raises(ValueError, match="immutable"):
        validate_plan(
            SeniorProposal(goal="mutate", interface_contracts=[interface(outputs="z")]), [], contracts
        )
    with pytest.raises(ValueError, match="needs version 2"):
        validate_plan(SeniorProposal(goal="skip", interface_contracts=[interface(3)]), [], contracts)
    with pytest.raises(ValueError, match="Replace pending task"):
        validate_plan(
            SeniorProposal(goal="revise", interface_contracts=[interface(2)]),
            [ledger(assignment("b", consumes=["motion@1"]))],
            contracts,
        )
    # Started work keeps its pinned contract; a later design does not rewrite it.
    validate_plan(
        SeniorProposal(goal="future revision", interface_contracts=[interface(2)]),
        [ledger(assignment("b", consumes=["motion@1"]), "in_progress")],
        contracts,
    )


def test_replanning_detects_cycles_across_new_and_retained_tasks():
    retained = [ledger(assignment("a", dependencies=["b"]))]
    proposal = SeniorProposal(goal="cycle", tasks=[assignment("b", dependencies=["a"])])
    with pytest.raises(ValueError, match="cycle"):
        validate_plan(proposal, retained, {})


def test_explicit_adapter_can_consume_old_contract_and_provide_new_version():
    proposal = SeniorProposal(
        goal="bridge existing state to the new renderer",
        interface_contracts=[interface(2)],
        tasks=[
            assignment("adapter", consumes=["motion@1"], provides=["motion@2"]),
            assignment("renderer", consumes=["motion@2"], dependencies=["adapter"]),
        ],
    )
    validate_plan(proposal, [], {"motion@1": interface()})


async def test_invalid_module_plan_returns_senior_feedback_without_publishing(config):
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    try:
        await ProjectAgent(app).initialize()
        proposal = SeniorProposal(goal="bad boundary", tasks=[assignment("a", consumes=["missing@1"])])
        result = await validate(
            {
                "reply": proposal.model_dump(mode="json"),
                "input": {},
                "process_id": "senior-test",
                "logical_step": 0,
            },
            Runtime(context=AppContext(app)),
        )
        assert "unknown interface" in result["error"]
        assert result["route"] == "error" and result["trajectory_ref"]
        assert not runtime.records.scan("interface-contract/")
        assert not runtime.records.scan("task/")
    finally:
        await runtime.close()


async def test_revised_plan_publishes_contracts_atomically_and_preserves_old_pins(config):
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        await engine.initialize()

        async def apply(proposal):
            run = app.get("app/run")
            pid = "senior-" + str(run["sprint"] + 1)
            app.process(pid, "senior")
            batch = {
                "run": run,
                "head": app.get("head/provisional")["code"],
                "snapshot": {
                    "reports": [],
                    "all_task_ids": [v["assignment"]["task_id"] for _, _, v in runtime.records.scan("task/")],
                },
                "pid": pid,
                "query_index": run["sprint"] + 1,
                "fingerprint": pid,
                "proposal": proposal.model_dump(mode="json"),
            }
            await engine._apply_review(batch)
            return batch

        await apply(
            SeniorProposal(
                goal="first module plan",
                interface_contracts=[interface()],
                tasks=[
                    assignment("a", provides=["motion@1"]),
                    assignment("b", consumes=["motion@1"], dependencies=["a"]),
                ],
            )
        )
        old_spec = app.get("task-spec/b")
        original = pinned_context(app, old_spec)
        batch = await apply(
            SeniorProposal(
                goal="revised future work",
                interface_contracts=[interface(2)],
                cancel_pending_task_ids=["a", "b"],
                tasks=[
                    assignment("a2", write_paths=["a.py"], provides=["motion@2"]),
                    assignment("b2", write_paths=["b.py"], consumes=["motion@2"], dependencies=["a2"]),
                ],
            )
        )
        assert set(catalog(app)) == {"motion@1", "motion@2"}
        assert original == pinned_context(app, old_spec)
        assert original[0]["interface_contracts"][0]["version"] == 1
        assert pinned_context(app, app.get("task-spec/b2"))[0]["interface_contracts"][0]["version"] == 2
        assert app.get("task/a")["execution"] == app.get("task/b")["execution"] == "cancelled"
        assert engine.ready() == ["task/a2"]
        await engine._apply_review(batch)  # Replay cannot duplicate definitions or retarget old tasks.
        assert len(runtime.records.scan("plan/")) == 2
    finally:
        await runtime.close()


@pytest.mark.parametrize("native", [False, True])
async def test_worker_and_reviewer_receive_matching_pinned_interfaces(config, native):
    if native:
        config = config.model_copy(
            update={
                "local": config.local.model_copy(
                    update={"protocol": "codex_app_server", "brokered_tools": True}
                )
            }
        )
    runtime = await StandaloneRuntime(config).open()

    class Modules(ScriptedAgent):
        worker_packets = []

        async def generate(self, messages, *args, **kwargs):
            data = json.loads(
                next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
                    "Pinned application inputs:\n", 1
                )[1]
            )
            result = await super().generate(messages, *args, **kwargs)
            reply = json.loads(result["text"])
            if "assignment" in data:
                self.worker_packets.append(data)
            elif not data["all_task_ids"]:
                reply["interface_contracts"] = [interface().model_dump(mode="json")]
                reply["tasks"][0].update(provides=["motion@1"], acceptance_criteria=["Provide x/y state"])
                reply["tasks"][1].update(
                    consumes=["motion@1"], dependencies=["a"], acceptance_criteria=["Consume x/y without z"]
                )
            elif data["pending_tasks"]:
                reply["complete"] = False
                reply.pop("completion_assessment", None)
            result["text"] = json.dumps(reply)
            return result

        async def generate_job(self, messages, snapshot, schema, callback=None, **kwargs):
            return await self.generate(messages, 4000, response_schema=schema)

    client = Modules()
    await runtime.clients["local"].close()
    await runtime.clients["cloud"].close()
    runtime.clients = {"local": client, "cloud": client}
    app = AgentServices(runtime, config)
    try:
        assert (await ProjectAgent(app).run())["outcome"] == "completed", app.get("app/run")
        assert {p["assignment"]["task_id"] for p in client.worker_packets} == {"a", "b"}
        for packet in client.worker_packets:
            definition = packet["module_context"][0]["interface_contracts"][0]
            assert definition == interface().model_dump(mode="json")
            assert "no z" in definition["outputs"]
        for packet in client.review_inputs:
            assert packet["interface_contracts"] == [interface().model_dump(mode="json")]
            for report in packet["reports"]:
                assert report["task_contract"]["module_context"][0]["interface_contracts"][0] == definition
        ui = TestUI(config.state_path.parent / "viewer", state=config.state_path)
        exported = await ui.export(next(iter(ui.runs)))
        assert exported["interface_contracts"] == {"interface-contract/motion@1": definition}
    finally:
        await runtime.close()
