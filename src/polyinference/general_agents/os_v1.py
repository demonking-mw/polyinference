"""Adapt the four public LangGraph programs to the shipped OS V1 wire."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, Field

from ..config import RuntimeConfig
from ..contracts import (
    CapabilityCall,
    ContextPart,
    ContextView,
    DataPolicy,
    DistributionPolicy,
    DistributionRule,
    ModelQuery,
    OperationRequest,
    Priority,
    ProcessSpec,
    ProgramRef,
    ScheduleContract,
)
from ..primitives import canonical, digest, now, operation_fingerprint
from ..runtime.kernel import KernelRuntime
from .graphs import BUILDERS, GraphContext


class LookupArgs(BaseModel):
    query: str = Field(min_length=1, max_length=500)


def _search(documents: dict[str, str], query: str) -> dict:
    words = set(re.findall(r"[a-z0-9]{3,}", query.lower()))
    ranked = sorted(documents.items(), key=lambda item: (-sum(item[1].lower().count(w) for w in words), item[0]))
    hits = [{"source_id": source, "excerpt": content[:2000]} for source, content in ranked[:3]
            if not words or any(word in content.lower() for word in words)]
    return {"query": query, "hits": hits}


class V1AgentIO:
    """One durable, role-pinned OS process and one journaled effect per graph action."""

    def __init__(self, runtime: KernelRuntime, variant: str, task: str, documents: dict[str, str]):
        self.runtime, self.variant, self.task, self.documents = runtime, variant, task, documents
        source = Path(__file__).with_name("graphs.py").read_bytes()
        adapter = Path(__file__).read_bytes()
        fingerprint = digest(source + adapter + variant.encode())
        self.program = ProgramRef(program_id="general-agents/" + variant, program_version="1",
                                  graph_digest=fingerprint, state_schema_version="1",
                                  prompt_bundle_digest=digest(source))
        pinned_program = runtime.records.get("general-agents/program")
        if pinned_program and pinned_program[1] != self.program.model_dump(mode="json"):
            raise ValueError("Saved agent program changed; use the original source or fresh state")
        runtime.records.put_once("general-agents/program", self.program.model_dump(mode="json"))
        self.run_input = digest(canonical({"variant": variant, "task": task, "documents": documents}))
        pinned = runtime.records.get("general-agents/input")
        if pinned and pinned[1]["digest"] != self.run_input:
            raise ValueError("Saved agent input changed; use a fresh state directory")
        runtime.records.put_once("general-agents/input", {"digest": self.run_input})
        self._register_lookup()

    def _register_lookup(self):
        async def handler(_request, arguments):
            return _search(self.documents, arguments["query"])

        self.runtime.register_capability("sources.lookup", handler, input_type=LookupArgs,
                                         effect_class="read", workspace=False,
                                         description="Search the immutable supplied document corpus by keywords.")

    def _scope(self, process_id):
        return self.runtime.scope.model_copy(update={"process_id": process_id})

    def _schedule(self, role: str, binding: str) -> ScheduleContract:
        endpoint = getattr(self.runtime.config, binding)
        policy = self.runtime.config.data_policy or DataPolicy(policy_ref="grant/run",
            allowed_inference_locations=["local", "cloud"],
            allowed_destination_classes=sorted(set(self.runtime.config.role_bindings.values())),
            maximum_classification="project")
        if self.variant != "simple" and role in {"local", "cloud"}:
            policy = policy.model_copy(update={"allowed_inference_locations": [role]})
        return ScheduleContract(
            priority=Priority(priority_class="normal", relative_value=50, aging_allowed=True, deadline=None),
            distribution=DistributionPolicy(policy_id="general-agents/static/1", version=1, fidelity="strict",
                rules=[DistributionRule(rule_id="static-role", roles=[role], phases=["*"], axis="harness_class",
                    eligible_classes=[endpoint.protocol], enforcement="hard", unit="model_decisions",
                    accounting_scope="run", accounting_group_id=self.runtime.run_id, window_slots=1,
                    max_total_variation=0, rounding_slack_slots=0, infeasible_action="reject")],
                max_rebindings=0, minimum_residence_ms=0, migration_boundaries=["before_start"]),
            data_policy=policy,
            requirements=[], prerequisites=[], resource_hints=[], conflict_keys=[], locality_refs=[])

    async def _effect(self, role: str, step: str, payload_factory, *, capability=False):
        process_id = f"ga-{self.variant}-{'tool' if capability else role}-{step}"
        if len(process_id) > 256 or not re.fullmatch(r"[A-Za-z0-9_.-]+", process_id):
            raise ValueError("Invalid graph step identity")
        binding = self.runtime.config.role_bindings[role]
        scope = self._scope(process_id)
        process = self.runtime.records.get("process/" + process_id)
        if not process:
            input_ref = self.runtime.artifacts.put(canonical({"task": self.task, "step": step}), scope)
            spec = ProcessSpec(record_id="process-spec/" + process_id, revision=1, scope=scope,
                created_at=now(), process_id=process_id, parent_process_id=None, program=self.program,
                entry_point=step, role=role, input_refs=[input_ref], task_spec_ref=None, attempt_id=None,
                workspace_id=None, grant_ref="grant/run", budget_account_ref="budget/run",
                limits=self.runtime.config.limits, schedule=self._schedule(role, binding),
                output_schema_ref="general-agents/text/1", resume_strategy="portable_context")
            self.runtime.processes.register(spec, binding,
                capabilities=["sources.lookup"] if capability else [])
            process = self.runtime.records.get("process/" + process_id)
        request_key = "general-agents/request/" + process_id
        retained = self.runtime.records.get(request_key)
        if retained:
            request = OperationRequest.model_validate(retained[1])
        else:
            payload = payload_factory(scope)
            started = datetime.fromisoformat(process[1]["started_at"].replace("Z", "+00:00"))
            deadline = started + timedelta(milliseconds=self.runtime.config.limits.max_wall_time_ms - 1)
            request = OperationRequest(record_id="request/" + process_id, revision=1, scope=scope,
                created_at=now(), operation_id="ga-effect-" + process_id,
                logical_step_id=step, intent_digest=digest(b"pending"), causal_parent_ref=None,
                trace_id=self.runtime.run_id, grant_ref="grant/run", owner_generation=1,
                expected_process_revision=1, expected_binding_generation=1,
                schedule_ref="general-agents/static/1", budget_account_ref="budget/run",
                deadline=deadline, limits=self.runtime.config.limits, resources=[], conflict_keys=[],
                safe_boundary="settled_operation", replay_policy="deduplicated", payload=payload)
            request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
            self.runtime.records.put_once(request_key, request.model_dump(mode="json"))

        async def perform():
            result = await self.runtime.execute(request)
            if result.state != "succeeded":
                raise RuntimeError(f"{role}/{step}: {result.state}: {result.error}")
            self.runtime.processes.finish(process_id,
                output_refs=[ref.model_dump(mode="json") for ref in result.output_refs])
            return result

        if process[1]["state"] == "completed":
            result = await self.runtime.execute(request)
        elif process[1]["state"] == "paused":
            raise RuntimeError(f"Process {process_id} is paused; inspect and reconcile it before continuing")
        else:
            result = await self.runtime.processes.start(process_id, perform)
        if result.state != "succeeded" or not result.output_refs:
            raise RuntimeError(f"No successful effect result for {process_id}")
        return json.loads(self.runtime.artifacts.read(result.output_refs[0]))

    async def model(self, role: str, phase: str, prompt: str, step: str) -> str:
        if role not in self.runtime.config.role_bindings:
            raise ValueError(f"Missing role binding: {role}")

        def payload(scope):
            instruction = self.runtime.artifacts.put(
                b"Follow the application prompt. Return only the requested text or JSON. Do not call native tools.",
                scope, "text/plain")
            task = self.runtime.artifacts.put(prompt.encode(), scope, "text/plain")
            parts = [ContextPart(part_id="instruction", content=instruction, part_kind="instruction",
                                 trust="application", source_ref="general-agents/prompt/1", required=True),
                     ContextPart(part_id="task", content=task, part_kind="data", trust="user",
                                 source_ref="general-agents/input", required=True)]
            context = ContextView(view_id=digest(canonical([p.model_dump(mode="json") for p in parts])),
                digest=digest(canonical([p.content.digest for p in parts])), parts=parts,
                memory_snapshot_refs=[], tool_catalog_digest=digest(b"no-native-tools"),
                maximum_input_tokens=self.runtime.config.limits.max_input_tokens_per_call, omitted_refs=[])
            return ModelQuery(role=role, phase=phase, prompt_template_ref="general-agents/prompt/1",
                context=context, response_schema_ref="general-agents/text/1",
                capability_requirements=[], temperature=0, session_ref=None)

        output = await self._effect(role, step, payload)
        return output["text"]

    async def lookup(self, query: str, step: str) -> str:
        def payload(scope):
            cap = self.runtime.capabilities.get("sources.lookup")
            return CapabilityCall(capability_id="sources.lookup", schema_digest=cap.schema_digest,
                arguments=self.runtime.artifacts.put(canonical({"query": query}), scope),
                model_call_id=None, workspace_id=None, expected_code=None, effect_class="read",
                reconciliation_strategy_ref="journal/1")

        output = await self._effect("local", step, payload, capability=True)
        return json.dumps(output, ensure_ascii=False)


async def run_v1(variant: str, config: RuntimeConfig, task: str,
                 documents: dict[str, str] | None = None) -> dict:
    """Run or replay a graph with a pinned input and V1 effect journal.

    A new invocation uses a fresh state directory. Settled steps replay with
    original config/input; paused and uncertain effects remain held by V1.
    """
    if variant not in BUILDERS:
        raise ValueError(f"Unknown agent design: {variant}")
    if not isinstance(task, str) or not task.strip() or len(task) > 12000:
        raise ValueError("Task must have 1 to 12000 characters")
    documents = {} if documents is None else documents
    if not isinstance(documents, dict) or any(
        not isinstance(k, str) or not 1 <= len(k) <= 128 or not isinstance(v, str)
        for k, v in documents.items()
    ):
        raise ValueError("Documents must map source IDs of 1-128 characters to text")
    if len(documents) > 64 or sum(len(v.encode()) for v in documents.values()) > 128_000:
        raise ValueError("Supplied corpus exceeds the V1 agent input bound")
    required_roles = {"general", "local"} if variant == "simple" else {"cloud", "local"}
    if not required_roles <= set(config.role_bindings):
        raise ValueError("Configure role_bindings for " + ", ".join(sorted(required_roles)))
    if any(getattr(config, config.role_bindings[role]).protocol not in
           {"chat", "responses", "anthropic", "gemini"} for role in required_roles):
        raise ValueError("These text graphs require raw text-capable endpoints")
    if variant != "simple" and (
        config.role_bindings["cloud"] == config.role_bindings["local"]
        or getattr(config, config.role_bindings["cloud"]).inference_location != "cloud"
        or getattr(config, config.role_bindings["local"]).inference_location != "local"
    ):
        raise ValueError("Multi-level agents require distinct endpoints explicitly declared cloud and local")
    runtime = await KernelRuntime(config).open()
    try:
        io = V1AgentIO(runtime, variant, task, documents)
        graph = BUILDERS[variant](runtime.checkpointer)
        thread = {"configurable": {"thread_id": "general-agents-" + variant}, "recursion_limit": 32}
        saved = await graph.aget_state(thread)
        if saved.values and not saved.next and saved.values.get("answer"):
            result = saved.values
        else:
            initial = None if saved.values else {"task": task, "documents": documents}
            result = await graph.ainvoke(initial, thread, context=GraphContext(io))
        key = "general-agents/result/" + variant
        retained = runtime.records.get(key)
        if retained:
            output = retained[1]
        else:
            answer_ref = runtime.artifacts.put(result["answer"].encode(), runtime.scope, "text/plain")
            output = {"variant": variant, "answer": result["answer"], "artifact": answer_ref.model_dump(mode="json")}
            runtime.records.put_once(key, output)
        return output
    finally:
        await runtime.close()
