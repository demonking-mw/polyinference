"""The runtime hosts brokered applications without a coding ledger or grammar."""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import Field

from polyinference.config import Endpoint, RuntimeConfig
from polyinference.contracts import (
    AgentJob,
    CapabilityCall,
    ContextPart,
    ContextView,
    OperationRequest,
    ProcessSpec,
    Wire,
)
from polyinference.domain import digest, now, operation_fingerprint
from polyinference.ports import RecordConflict
from polyinference.runtime.kernel import KernelRuntime, UncertainEffect


class Lookup(Wire):
    topic: str
    limit: int = Field(default=2, gt=0, le=5)
    generation: int = 1


def process(runtime, *, capabilities=(), role="analyst", process_id="research"):
    examples = json.loads((Path(__file__).parents[1] / "design-docs/langgraph-agent/examples.json").read_text())
    template = next(value for value in examples["records"] if value["kind"] == "process_spec")
    scope = runtime.scope.model_copy(update={"process_id": process_id})
    prompt = runtime.artifacts.put(b"Summarize supplied evidence.", scope)
    spec = ProcessSpec.model_validate({
        **template, "record_id": "process-spec/" + process_id, "scope": scope.model_dump(mode="json"),
        "created_at": now(), "required_features": [], "extensions": {},
        "process_id": process_id, "parent_process_id": None, "role": role,
        "entry_point": "research", "task_spec_ref": None, "attempt_id": None,
        "workspace_id": None, "input_refs": [prompt], "limits": runtime.config.limits,
        "output_schema_ref": "research-summary/1", "grant_ref": "grant/run", "budget_account_ref": "budget/run",
        "program": {**template["program"], "program_id": "research", "program_version": "1"},
        "schedule": {**template["schedule"], "requirements": [], "conflict_keys": [], "locality_refs": []},
    })
    runtime.processes.register(spec, "local", capabilities=capabilities)
    return spec, prompt


def request(runtime, spec, payload, step):
    value = OperationRequest(
        record_id="request/" + spec.process_id + "/" + step, scope=spec.scope, created_at=now(), revision=1,
        operation_id=spec.process_id + "-" + step, logical_step_id=step, intent_digest=digest(b"pending"),
        causal_parent_ref=None, trace_id="run", grant_ref="grant/run", owner_generation=1,
        expected_process_revision=1, expected_binding_generation=1, schedule_ref="research/1",
        budget_account_ref="budget/run", deadline=now() + timedelta(seconds=30), limits=spec.limits,
        resources=[], conflict_keys=[], safe_boundary="settled_operation",
        replay_policy="deduplicated", payload=payload,
    )
    return value.model_copy(update={"intent_digest": operation_fingerprint(value)})


def call(runtime, name, arguments, *, effect_class=None, schema_digest=None):
    capability = runtime.capabilities.get(name)
    return CapabilityCall(
        capability_id=name, schema_digest=schema_digest or capability.schema_digest,
        arguments=runtime.artifacts.put(json.dumps(arguments).encode(), runtime.scope),
        model_call_id=None, workspace_id=None, expected_code=None,
        effect_class=effect_class or capability.effect_class, reconciliation_strategy_ref="journal/1",
    )


def configuration(tmp_path, endpoint=None, role="analyst"):
    endpoint = endpoint or Endpoint(model="fixture")
    return RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
                         local=endpoint, cloud=endpoint, role_bindings={role: "local"})


@pytest.mark.parametrize("denial", ["grant", "schema", "effect", "arguments"])
async def test_custom_capability_is_typed_granted_and_replayable(tmp_path, denial):
    runtime = await KernelRuntime(configuration(tmp_path)).open()
    calls = []

    async def lookup(operation, arguments):
        calls.append(arguments)
        assert operation.scope.process_id == "research"
        return {"finding": arguments["topic"]}

    runtime.register_capability("research.lookup", lookup, input_type=Lookup)
    spec, _ = process(runtime, capabilities=[] if denial == "grant" else ["research.lookup"])
    options = {"effect_class": "private_write"} if denial == "effect" else (
        {"schema_digest": digest(b"wrong schema")} if denial == "schema" else {})
    arguments = {"topic": "trees", "limit": 0 if denial == "arguments" else 2}
    denied = request(runtime, spec, call(runtime, "research.lookup", arguments, **options), "denied")
    try:
        result = await runtime.execute(denied)
        assert result.state == "failed" and not calls
        assert await runtime.execute(denied) == result
        if denial != "grant":
            accepted = request(runtime, spec, call(runtime, "research.lookup", {"topic": "trees"}), "accepted")
            result = await runtime.execute(accepted)
            assert result.state == "succeeded" and len(calls) == 1
            assert await runtime.execute(accepted) == result and len(calls) == 1
        assert not runtime.records.scan("task/") and not runtime.records.scan("workspace/")
    finally:
        await runtime.close()


async def test_user_notification_without_coding_state_is_durable_and_replayable(tmp_path, capsys):
    from polyinference.ui_os import read_snapshot, runtime_view

    config = configuration(tmp_path)
    runtime = await KernelRuntime(config).open()
    spec, _ = process(runtime, capabilities=["user.notify"])
    text = "Research progress\n" + "Complete finding. " * 50 + "\x1b[2J"
    operation = request(runtime, spec, call(runtime, "user.notify", {"text": text}), "notify")
    try:
        result = await runtime.execute(operation)
        assert result.state == "succeeded", result.error
        assert await runtime.execute(operation) == result
        output = capsys.readouterr().out
        assert output.count("Research progress") == 1
        assert "Complete finding. " * 50 in output  # No terminal-event truncation.
        assert "\x1b" not in output
        messages = runtime_view(read_snapshot(config.state_path), {})["messages"]
        assert len(messages) == 1 and messages[0]["text"] == text
        assert messages[0]["scope"]["process_id"] == "research"
        assert not runtime.records.scan("task/") and not runtime.records.scan("workspace/")
        assert not (config.state_path / "repository.git").exists()
        # Simulate interruption after the durable message but before effect settlement.
        key = "effect/" + operation.operation_id
        row = runtime.records.get(key)
        runtime.records.compare_and_publish({key: row[0]}, {key: {**row[1], "state": "uncertain", "result": None}})
    finally:
        await runtime.close()
    runtime = await KernelRuntime(config).open()
    try:
        assert runtime.records.get(key)[1]["state"] == "succeeded"
        assert (await runtime.execute(operation)).state == "succeeded"
        assert len(runtime_view(read_snapshot(config.state_path), {})["messages"]) == 1
        assert not capsys.readouterr().out  # Reconciliation does not reprint the message.
    finally:
        await runtime.close()


@pytest.mark.parametrize("denial", ["grant", "blank", "oversize", "extra"])
async def test_user_notification_enforces_grant_and_arguments(tmp_path, capsys, denial):
    runtime = await KernelRuntime(configuration(tmp_path)).open()
    spec, _ = process(runtime, capabilities=[] if denial == "grant" else ["user.notify"])
    arguments = {"text": "hello"}
    if denial == "blank":
        arguments["text"] = " \n "
    elif denial == "oversize":
        arguments["text"] = "a" * 16001
    elif denial == "extra":
        arguments["process_id"] = "someone-else"
    try:
        result = await runtime.execute(request(runtime, spec, call(runtime, "user.notify", arguments), "denied"))
        assert result.state == "failed"
        assert not runtime.records.scan("user-message/")
        assert not capsys.readouterr().out
    finally:
        await runtime.close()


@pytest.mark.parametrize("error", [BrokenPipeError, ValueError])
async def test_user_notification_survives_closed_terminal(tmp_path, monkeypatch, error):
    def closed(*args, **kwargs):
        raise error("closed terminal")

    monkeypatch.setattr("polyinference.runtime.messages.print", closed, raising=False)
    runtime = await KernelRuntime(configuration(tmp_path)).open()
    spec, _ = process(runtime, capabilities=["user.notify"])
    try:
        operation = request(runtime, spec, call(runtime, "user.notify", {"text": "Still available in UI"}), "notify")
        result = await runtime.execute(operation)
        assert result.state == "succeeded", result.error
        assert len(runtime.records.scan("user-message/")) == 1
    finally:
        await runtime.close()


async def test_native_research_tool_uses_real_transport_without_coding_protocol(tmp_path):
    script = tmp_path / "research_server.py"
    script.write_text('''import json,sys
def send(value): print(json.dumps(value),flush=True)
for line in sys.stdin:
 message=json.loads(line);method=message.get("method")
 if method=="initialize":send({"id":message["id"],"result":{}})
 elif method=="thread/start":
  instructions=message["params"].get("developerInstructions", "")
  schema=message["params"]["dynamicTools"][0]["inputSchema"]
  assert schema["properties"]["tool"]["enum"]==["research.lookup","user.notify"]
  assert "topic" in schema["properties"]["arguments"]["anyOf"][0]["properties"]
  send({"id":message["id"],"result":{"thread":{"id":"research-thread"},"sandbox":{"type":"readOnly"},"approvalPolicy":"never"}})
 elif method=="turn/start":
  messages=message["params"]["input"]
  prompt=json.dumps(messages)+instructions
  assert "candidate" not in prompt and "assessment" not in prompt and "files.write" not in prompt
  assert "supplied summary schema" in prompt
  for index,limit in enumerate([2,2,0]):
   send({"id":100+index,"method":"item/tool/call","params":{
    "threadId":"research-thread","callId":"lookup-1" if index<2 else "invalid-lookup",
    "tool":"polyinference_tool","arguments":{"tool":"research.lookup","arguments":{"topic":"trees","limit":limit,"generation":7}}}})
   reply=json.loads(sys.stdin.readline())
   observation=json.loads(reply["result"]["contentItems"][0]["text"])
   assert observation["state"]==("succeeded" if index<2 else "failed"),observation
  for index in range(2):
   send({"id":110+index,"method":"item/tool/call","params":{
    "threadId":"research-thread","callId":"notification-1","tool":"polyinference_tool",
    "arguments":{"tool":"user.notify","arguments":{"text":"Research findings are ready."}}}})
   reply=json.loads(sys.stdin.readline())
   observation=json.loads(reply["result"]["contentItems"][0]["text"])
   assert observation["state"]=="succeeded",observation
  send({"id":message["id"],"result":{"turn":{"id":"research-turn"}}})
  send({"method":"item/completed","params":{"item":{"type":"agentMessage","text":json.dumps({"summary":"Trees are supported by evidence."})}}})
  send({"method":"turn/completed","params":{"turn":{"id":"research-turn","status":"completed","items":[]}}})
''')
    endpoint = Endpoint(model="fixture", protocol="codex_app_server", brokered_tools=True,
                        command=[sys.executable, str(script)], timeout_seconds=10)
    runtime = await KernelRuntime(configuration(tmp_path, endpoint)).open()
    calls = []

    async def lookup(operation, arguments):
        calls.append(arguments)
        assert arguments["generation"] == 7
        return {"evidence": ["trees"]}

    runtime.register_capability("research.lookup", lookup, input_type=Lookup)
    runtime.register_agent_protocol(
        "research/1", {"type": "object", "properties": {"summary": {"type": "string"}}},
        workspace="none", brokered=True, instructions="Return findings using the supplied summary schema.",
    )
    spec, prompt = process(runtime, capabilities=["research.lookup", "user.notify"])
    context = ContextView(
        view_id="research-context", digest=digest(b"context"),
        parts=[ContextPart(part_id="facts", content=prompt, part_kind="data", trust="user",
                           source_ref="user", required=True)],
        memory_snapshot_refs=[], tool_catalog_digest=digest(b"research-tools"),
        maximum_input_tokens=spec.limits.max_input_tokens_per_call, omitted_refs=[],
    )
    operation = request(runtime, spec, AgentJob(
        role=spec.role, objective=prompt, context=context, workspace_id="unused",
        allowed_capabilities=["research.lookup", "user.notify"],
        required_phase_protocol="research/1", required_guarantees=[],
        response_schema_ref="research-summary/1", session_ref=None,
    ), "summarize")
    try:
        result = await runtime.execute(operation)
        assert result.state == "succeeded", result.error
        output = json.loads(runtime.artifacts.read(result.output_refs[0]))
        assert json.loads(output["text"])["summary"] == "Trees are supported by evidence."
        assert len(calls) == 1
        children = [body for _, _, body in runtime.records.scan("effect/")
                    if body["request"]["causal_parent_ref"] == operation.operation_id]
        assert len(children) == 3 and {value["state"] for value in children} == {"succeeded", "failed"}
        assert [body["text"] for _, _, body in runtime.records.scan("user-message/")] == [
            "Research findings are ready."
        ]
        assert all(value["request"]["payload"]["workspace_id"] is None for value in children)
        runtime.processes.finish(spec.process_id, output_refs=result.output_refs)
        assert await runtime.execute(operation) == result and len(calls) == 1
        assert not runtime.records.scan("task/") and not runtime.records.scan("report/")
        assert not runtime.records.scan("workspace/") and not runtime.config.repo_path.exists()
    finally:
        await runtime.close()


async def test_generic_publication_does_not_interpret_application_record_names(tmp_path):
    runtime = await KernelRuntime(configuration(tmp_path)).open()
    spec, _ = process(runtime, capabilities=["records.publish"])
    permit = await runtime.exclusive.acquire("research/catalog", spec.process_id)
    values = {"app/run": {"summary": "Research state"}, "head/provisional": {"code": "not a Git revision"}}
    args = {"receipt_ref": "research-receipt/1", "permit_ref": permit,
            "expected": {key: 0 for key in values}, "updates": values,
            "immutable": {"research-receipt/1": {"done": True},
                          "report/research": {"summary": "No coding verdict required"}}}
    operation = request(runtime, spec, call(runtime, "records.publish", args), "publish")
    operation = operation.model_copy(update={"conflict_keys": ["research/catalog"]})
    operation = operation.model_copy(update={"intent_digest": operation_fingerprint(operation)})
    try:
        result = await runtime.execute(operation)
        assert result.state == "succeeded", result.error
        assert runtime.records.get("app/run")[1] == values["app/run"]
        await runtime.exclusive.release(permit, spec.process_id)
        assert await runtime.execute(operation) == result
        unowned = operation.model_copy(update={"operation_id": "unowned", "logical_step_id": "unowned"})
        unowned = unowned.model_copy(update={"intent_digest": operation_fingerprint(unowned)})
        with pytest.raises(ValueError, match="resource ownership"):
            await runtime.execute(unowned)
    finally:
        await runtime.close()


async def test_external_tool_failure_preserves_unknown_effects(tmp_path):
    runtime = await KernelRuntime(configuration(tmp_path)).open()

    async def external(operation, arguments):
        raise RuntimeError("Remote receipt was lost")

    runtime.register_capability("research.send", external, effect_class="external_write")
    spec, _ = process(runtime, capabilities=["research.send"])
    operation = request(runtime, spec, call(runtime, "research.send", {}), "send")
    try:
        with pytest.raises(UncertainEffect):
            await runtime.execute(operation)
        with pytest.raises(UncertainEffect):
            await runtime.execute(operation)
        assert runtime.uncertain() == [operation.operation_id]
    finally:
        await runtime.close()


async def test_role_name_does_not_grant_management_privileges(tmp_path):
    config = configuration(tmp_path, role="senior")
    assert config.limits.final_phase_reserve is None
    runtime = await KernelRuntime(config).open()
    spec, _ = process(runtime, role="senior")
    try:
        runtime.processes.cancel(spec.process_id)
        assert runtime.records.get("process-control/" + spec.process_id)[1]["cancel_requested"]
        assert runtime.records.get("process/" + spec.process_id)[1]["management"] is False
    finally:
        await runtime.close()


async def test_capability_and_native_protocol_abis_survive_restart(tmp_path):
    config = configuration(tmp_path)
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}

    async def lookup(operation, arguments):
        return arguments

    runtime = await KernelRuntime(config).open()
    try:
        runtime.register_capability("research.lookup", lookup, input_type=Lookup)
        runtime.register_agent_protocol("research/1", schema, workspace="none", instructions="Summarize.")
        schema["properties"]["injected"] = {"type": "string"}
        assert "injected" not in runtime.agent_protocols["research/1"]["schema"]["properties"]
    finally:
        await runtime.close()

    runtime = await KernelRuntime(config).open()
    try:
        with pytest.raises(RecordConflict, match="Immutable identity reused"):
            runtime.register_capability("research.lookup", lookup, input_type=Lookup, effect_class="private_write")
        with pytest.raises(RecordConflict, match="Immutable identity reused"):
            runtime.register_agent_protocol("research/1", schema, workspace="none", instructions="Summarize.")
        schema["properties"].pop("injected")
        runtime.register_capability("research.lookup", lookup, input_type=Lookup)
        runtime.register_agent_protocol("research/1", schema, workspace="none", instructions="Summarize.")
    finally:
        await runtime.close()


async def test_required_publication_policy_cannot_disappear_after_restart(tmp_path):
    config = configuration(tmp_path)
    runtime = await KernelRuntime(config).open()
    calls = []

    def policy(arguments, process_id):
        calls.append(arguments["receipt_ref"])
        return arguments

    runtime.register_publication_policy("research", policy)
    spec, _ = process(runtime, capabilities=["records.publish"])
    permit = await runtime.exclusive.acquire("research/catalog", spec.process_id)

    def publication(runtime, index):
        receipt = "research-receipt/" + str(index)
        args = {"receipt_ref": receipt, "permit_ref": permit,
                "expected": {"research/catalog": index - 1},
                "updates": {"research/catalog": {"version": index}},
                "immutable": {receipt: {"done": True}}}
        return request(runtime, spec, call(runtime, "records.publish", args), "publish-" + str(index))

    first = publication(runtime, 1)
    try:
        settled = await runtime.execute(first)
        assert settled.state == "succeeded" and calls == ["research-receipt/1"]
    finally:
        await runtime.close()

    runtime = await KernelRuntime(config).open()
    try:
        assert await runtime.execute(first) == settled and len(calls) == 1
        second = publication(runtime, 2)
        denied = await runtime.execute(second)
        assert denied.state == "failed" and "Reinstall" in denied.error.message
        assert runtime.records.get("research/catalog")[1] == {"version": 1}
        assert not runtime.records.get("research-receipt/2")
        runtime.register_publication_policy("research", policy)
        assert await runtime.execute(second) == denied  # Installing a handler does not rewrite history.
        retry = second.model_copy(update={"operation_id": "policy-retry", "logical_step_id": "policy-retry"})
        retry = retry.model_copy(update={"intent_digest": operation_fingerprint(retry)})
        assert (await runtime.execute(retry)).state == "succeeded"
        assert calls == ["research-receipt/1", "research-receipt/2"]
        await runtime.exclusive.release(permit, spec.process_id)
    finally:
        await runtime.close()


async def test_registered_workspace_handlers_share_source_preconditions(config):
    runtime = await KernelRuntime(config).open()
    calls = []

    async def inspect(operation, arguments):
        calls.append(arguments)
        return {"checked": True}

    runtime.register_capability("example.inspect", inspect, input_type=dict[str, str], workspace=True)
    spec, _ = process(runtime, capabilities=["example.inspect"])
    try:
        base = await runtime.workspaces.initialize()
        manifest = await runtime.workspaces.create("view", spec.process_id, "opaque/provenance", base,
                                                   [], ["a.py"], capabilities=["example.inspect"])
        code = await runtime.workspaces.revision(manifest.workspace_id)
        for index, denial in enumerate(("generation", "content", None)):
            payload = call(runtime, "example.inspect", {
                "topic": "source", "generation": manifest.generation + (denial == "generation"),
            }).model_copy(update={
                "workspace_id": manifest.workspace_id,
                "expected_code": code.model_copy(update={"effective_tree_digest": digest(b"old")})
                if denial == "content" else code,
            })
            operation = request(runtime, spec, payload, "inspect-" + str(index))
            result = await runtime.execute(operation)
            assert result.state == ("succeeded" if denial is None else "failed")
            assert len(calls) == (1 if denial is None else 0)
        assert calls == [{"topic": "source", "generation": manifest.generation}]
        assert not runtime.records.scan("task/")
    finally:
        await runtime.close()
