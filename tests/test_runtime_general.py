"""The OS can host an agent with no coding program, checks, Git or file writes."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest

from polyinference.config import Endpoint, RuntimeConfig
from polyinference.contracts import (
    AgentJob,
    ContextPart,
    ContextView,
    ModelQuery,
    OperationRequest,
    ProcessSpec,
)
from polyinference.domain import digest, now, operation_fingerprint
from polyinference.runtime.kernel import KernelRuntime


@pytest.mark.parametrize("native", [False, True])
async def test_non_coding_agent_returns_artifact_and_terminates_without_workspace(tmp_path, native):
    endpoint = Endpoint(model="fixture", protocol="codex_app_server" if native else "chat")
    config = RuntimeConfig(
        repository=str(tmp_path / "unused-input"), state_directory=str(tmp_path / "state"),
        local=endpoint, cloud=endpoint, role_bindings={"researcher": "local"},
    )
    runtime = await KernelRuntime(config).open()
    scope = runtime.scope.model_copy(update={"process_id": "research"})
    prompt = runtime.artifacts.put(b"Summarize the supplied facts. Return a paragraph.", scope)
    examples = json.loads((Path(__file__).parents[1] / "design-docs/langgraph-agent/examples.json").read_text())
    template = next(r for r in examples["records"] if r["kind"] == "process_spec")
    spec = ProcessSpec.model_validate({
        **template, "record_id": "process-spec/research", "scope": scope.model_dump(mode="json"),
        "created_at": now(), "required_features": [], "extensions": {},
        "process_id": "research", "parent_process_id": None, "role": "researcher",
        "entry_point": "summarize", "task_spec_ref": None, "attempt_id": None,
        "workspace_id": None, "input_refs": [prompt], "limits": config.limits,
        "output_schema_ref": "research-summary/1", "grant_ref": "grant/run", "budget_account_ref": "budget/run",
        "program": {**template["program"], "program_id": "research", "program_version": "1"},
        "schedule": {**template["schedule"], "requirements": [], "conflict_keys": [], "locality_refs": []},
    })
    runtime.processes.register(spec, "local")
    context = ContextView(
        view_id="research-context", digest=digest(b"context"),
        parts=[ContextPart(part_id="facts", content=prompt, part_kind="data", trust="user",
                           source_ref="user", required=True)],
        memory_snapshot_refs=[], tool_catalog_digest=digest(b"no-tools"),
        maximum_input_tokens=config.limits.max_input_tokens_per_call, omitted_refs=[],
    )

    class Provider:
        async def generate(self, messages, max_output):
            return {"text": "The facts support the conclusion.", "model": "fixture", "usage": {"total_tokens": 5}}

        async def generate_job(self, messages, snapshot, schema):
            assert schema == {"type": "object", "properties": {"summary": {"type": "string"}}}
            assert Path(snapshot).is_dir()
            return await self.generate(messages, 100)

        async def close(self):
            pass

    await runtime.clients["local"].close()
    runtime.clients["local"] = Provider()
    if native:
        await runtime.workspaces.prepare_artifact_snapshot("facts", {"facts.txt": prompt})
        runtime.register_agent_protocol("research/1", {"type": "object", "properties": {"summary": {"type": "string"}}})
        payload = AgentJob(
            role="researcher", objective=prompt, context=context, workspace_id="facts",
            allowed_capabilities=[], required_phase_protocol="research/1", required_guarantees=[],
            response_schema_ref="research-summary/1", session_ref=None,
        )
    else:
        payload = ModelQuery(
            role="researcher", phase="summarize", prompt_template_ref="research/1", context=context,
            response_schema_ref="research-summary/1", capability_requirements=[], temperature=0, session_ref=None,
        )
    request = OperationRequest(
        record_id="request/research/summary", scope=scope, created_at=now(), revision=1,
        operation_id="research-summary", logical_step_id="summary", intent_digest=digest(b"pending"),
        causal_parent_ref=None, trace_id="run", grant_ref="grant/run", owner_generation=1,
        expected_process_revision=1, expected_binding_generation=1, schedule_ref="research/1",
        budget_account_ref="budget/run", deadline=now() + timedelta(seconds=30), limits=config.limits,
        resources=[], conflict_keys=[], safe_boundary="settled_operation",
        replay_policy="deduplicated", payload=payload,
    )
    request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})

    async def research():
        result = await runtime.execute(request)
        assert result.state == "succeeded", result.error
        runtime.processes.finish("research", output_refs=[r.model_dump(mode="json") for r in result.output_refs])
        return result

    try:
        result = await runtime.processes.start("research", research)
        status = await runtime.processes.wait("research", timeout=1)
        assert status["state"] == "completed"
        assert await runtime.execute(request) == result
        fresh = request.model_copy(update={"operation_id": "after-completion", "logical_step_id": "after-completion"})
        fresh = fresh.model_copy(update={"intent_digest": operation_fingerprint(fresh)})
        with pytest.raises(ValueError, match="stopped"):
            await runtime.execute(fresh)
        assert not runtime.records.scan("task/")
        assert not runtime.records.scan("report/")
        assert not runtime.records.scan("workspace/")
        assert not (config.state_path / "repository.git").exists()
        assert not config.repo_path.exists()
        assert runtime.records.get("process/research")[1]["output_refs"]
        # Even a driver that never queries a model or produces files is bounded.
        import asyncio

        bounded = spec.model_copy(update={
            "record_id": "process-spec/bounded", "process_id": "bounded", "created_at": now(),
            "scope": scope.model_copy(update={"process_id": "bounded"}),
            "limits": spec.limits.model_copy(update={"max_wall_time_ms": 50}),
        })
        runtime.processes.register(bounded, "local")
        with pytest.raises(asyncio.TimeoutError):
            await runtime.processes.start("bounded", asyncio.Event().wait)
        assert (await runtime.processes.wait("bounded", timeout=1))["state"] == "paused"
        # Other programs may use app/run for unrelated data; OS cancellation
        # must not interpret that record as a coding sprint.
        runtime.records.put_once("app/run", {"summary": "Research program state"})
        cancellable = bounded.model_copy(update={
            "record_id": "process-spec/cancellable", "process_id": "cancellable", "created_at": now(),
            "scope": scope.model_copy(update={"process_id": "cancellable"}),
        })
        runtime.processes.register(cancellable, "local")
        runtime.processes.cancel("cancellable")
        runtime.processes.finish("cancellable", state="cancelled")
        assert runtime.records.get("app/run")[1] == {"summary": "Research program state"}
    finally:
        await runtime.close()
