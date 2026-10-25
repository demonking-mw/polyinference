"""Application-owned ledger, steering, context, requests and assessment policy."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import TypeAdapter

from ..contracts import (
    AgentJob,
    ArtifactRef,
    CapabilityCall,
    CheckEvidence,
    CodeRevision,
    ContextPart,
    ContextView,
    DataPolicy,
    DistributionPolicy,
    DistributionRule,
    Feature,
    ModelQuery,
    OperationRequest,
    Priority,
    ProcessSpec,
    ProcessStatus,
    ProgramRef,
    ScheduleContract,
    Scope,
)
from ..domain import (
    PROGRAM_VERSION,
    STATE_VERSION,
    SeniorProposal,
    WorkerReply,
    canonical,
    digest,
    now,
    operation_fingerprint,
)
from ..ports import RuntimePorts
from .prompts import BOOTSTRAP, SENIOR, WORKER
from .tasks import coding_tools


class AgentServices:
    def __init__(self, ports: RuntimePorts, config, run_id="run"):
        self.ports, self.config, self.run_id = ports, config, run_id
        self.worker_tasks = {}
        register = getattr(ports.operations, "register_response_validator", None)
        if register:
            register("worker/1", lambda text, payload: TypeAdapter(WorkerReply).validate_json(text))
            register("senior/1", lambda text, payload: SeniorProposal.model_validate_json(text))
        self.program = ProgramRef(
            program_id="polyinference",
            program_version=PROGRAM_VERSION,
            graph_digest=digest(b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))),
            state_schema_version=STATE_VERSION,
            prompt_bundle_digest=digest((WORKER + SENIOR + BOOTSTRAP).encode()),
        )

    def get(self, key):
        row = self.ports.records.get(key)
        if not row:
            raise ValueError("Missing application record: " + key)
        return row[1]

    def update(self, key, body):
        row = self.ports.records.get(key)
        self.ports.records.compare_and_publish({key: row[0] if row else 0}, {key: body})

    def scope(self, process_id=None):
        return Scope(
            tenant_id="standalone",
            project_id=digest(str(self.config.repo_path).encode()),
            run_id=self.run_id,
            process_id=process_id,
        )

    def artifact(self, value, process_id=None):
        return self.ports.artifacts.put(canonical(value), self.scope(process_id))

    def read(self, ref):
        if isinstance(ref, dict):
            ref = ArtifactRef.model_validate(ref)
        return json.loads(self.ports.artifacts.read(ref))

    def base(self, record_id):
        return dict(record_id=record_id, revision=1, scope=self.scope(), created_at=now())

    def process(self, process_id, role, task_ref=None, task_data=None):
        key = "process/" + process_id
        if self.ports.records.get(key):
            return
        endpoint_name = self.config.role_bindings[role]
        endpoint = getattr(self.config, endpoint_name)
        rule = DistributionRule(
            rule_id="static-role",
            roles=[role],
            phases=["*"],
            axis="inference_location",
            eligible_classes=[endpoint.physical_location],
            target_weights={},
            enforcement="hard",
            unit="agent_jobs" if endpoint.protocol.startswith("codex") else "model_decisions",
            accounting_scope="run",
            accounting_group_id=self.run_id,
            window_slots=1,
            max_total_variation=0,
            rounding_slack_slots=0,
            infeasible_action="reject",
        )
        schedule = ScheduleContract(
            priority=Priority(priority_class="normal", relative_value=50, aging_allowed=True, deadline=None),
            distribution=DistributionPolicy(
                policy_id="static/1",
                version=1,
                fidelity="strict",
                rules=[rule],
                max_rebindings=0,
                minimum_residence_ms=0,
                migration_boundaries=["before_start"],
            ),
            data_policy=DataPolicy(
                policy_ref="grant/run",
                allowed_inference_locations=[endpoint.physical_location],
                allowed_destination_classes=[endpoint_name],
                maximum_classification="project",
            ),
            requirements=[],
            prerequisites=[],
            resource_hints=[],
            conflict_keys=[],
            locality_refs=[],
        )
        spec_ref = "process-spec/" + process_id
        spec = ProcessSpec(
            **self.base(spec_ref),
            process_id=process_id,
            parent_process_id=None if process_id == "controller" else "controller",
            program=self.program,
            entry_point="controller"
            if process_id == "controller"
            else "senior"
            if role == "senior"
            else "worker",
            role=role,
            input_refs=[self.artifact({"task_ref": task_ref, "objective": self.config.objective})],
            task_spec_ref=task_ref,
            attempt_id=task_data["attempt_id"] if task_data else None,
            workspace_id=task_data["workspace_id"] if task_data else None,
            grant_ref="grant/run",
            budget_account_ref="budget/run",
            limits=self.config.limits,
            schedule=schedule,
            output_schema_ref="senior/1" if role == "senior" else "worker/1",
            resume_strategy="portable_context",
        )
        status = ProcessStatus(
            **self.base("process-status/" + process_id),
            process_spec_ref=spec_ref,
            state="ready",
            phase="initial" if role == "senior" else "development",
            owner_generation=1,
            binding_generation=1,
            binding_ref=endpoint_name,
            wait=None,
            pending_operations=[],
            reservation_refs=[],
            permit_refs=[],
            continuation_ref=None,
            terminal_result_ref=None,
            cancellation_requested=False,
        )
        self.ports.records.compare_and_publish(
            {key: 0},
            {
                key: {
                    "process_id": process_id,
                    "owner_generation": 1,
                    "role": role,
                    "task_ref": task_ref,
                    "state": "ready",
                    "program": self.program.model_dump(mode="json"),
                    "spec_ref": spec_ref,
                    "started_at": now().isoformat(),
                    "report_ref": None,
                }
            },
            {spec_ref: spec.model_dump(mode="json"), status.record_id: status.model_dump(mode="json")},
        )

    def process_status(self, process_id, **updates):
        key = "process-status/" + process_id
        current = self.ports.records.get(key)
        status = ProcessStatus.model_validate(current[1])
        status = status.model_copy(update={**updates, "revision": status.revision + 1})
        self.ports.records.compare_and_publish({key: current[0]}, {key: status.model_dump(mode="json")})

    def memory_view(self):
        working = self.ports.records.get("memory/working")
        covered = set(working[1]["covered_note_refs"]) if working else set()
        return {
            "senior_summary": working[1]["summary"] if working else None,
            "notes": [
                {**body, "comment": self.read(body["content"])}
                for key, _, body in self.ports.records.scan("memory-note/")
                if key not in covered
            ],
        }

    def review_report(self, report):
        return {
            "record_id": report["record_id"],
            "task_spec_ref": report["task_spec_ref"],
            "verdict": report["verdict"],
            "resolution": report["resolution"],
            "comment": self.read(report["assessment_summary"]),
            "captured_head": report["captured_head"],
            "final_code": report["final_code"],
            "candidate_commit_id": report["candidate_commit_id"],
            "hazard_refs": report["hazard_refs"],
            "evidence": [
                {
                    "criterion": e["criterion_ref"],
                    "status": e["status"],
                    "exit_code": e["exit_code"],
                    "checked_code": e["checked_code"],
                    "output_ref": e["output"],
                    "output_preview": self.ports.artifacts.read(ArtifactRef.model_validate(e["output"]))[
                        :800
                    ].decode(errors="replace"),
                }
                for e in report["evidence"]
            ],
        }

    async def repository_context(self, code):
        from ..contracts import CodeRevision

        tree = await self.ports.workspaces.tree(CodeRevision.model_validate(code).commit_id)
        selected = list(dict.fromkeys(self.config.allowed_write_paths + self.config.closure_paths))
        remaining, contents = 5000, []
        for path in selected:
            if path not in tree or remaining <= 0:
                continue
            content = tree[path][1]
            preview = content[: min(remaining, 2000)]
            remaining -= len(preview)
            contents.append(
                {
                    "path": path,
                    "digest": digest(content),
                    "content": preview.decode(errors="replace"),
                    "truncated": len(preview) < len(content),
                }
            )
        return {
            "paths": sorted(tree)[:100],
            "omitted_path_count": max(0, len(tree) - 100),
            "contents": contents,
            "source_code": code,
        }

    def ensure_request(self, process_id, step, payload, view=None, protected=False):
        key = f"request/{process_id}/{step}"
        existing = self.ports.records.get(key)
        if existing:
            request = OperationRequest.model_validate(existing[1])
            if canonical(request.payload) != canonical(payload):
                raise ValueError("Replayed logical step changed intent")
            return request
        created = now()
        limits = self.config.limits
        process = self.get("process/" + process_id)
        deadline = min(
            created + timedelta(milliseconds=limits.max_wall_time_ms),
            datetime.fromisoformat(process["started_at"]) + timedelta(milliseconds=limits.max_wall_time_ms),
        )
        request = OperationRequest(
            **{**self.base(key), "scope": self.scope(process_id)},
            operation_id=digest(f"{self.run_id}:{process_id}:{step}".encode()),
            logical_step_id=str(step),
            intent_digest=digest(canonical(payload)),
            causal_parent_ref=None,
            trace_id=self.run_id,
            grant_ref="grant/run",
            owner_generation=process["owner_generation"],
            expected_process_revision=1,
            expected_binding_generation=1,
            schedule_ref="static/1",
            budget_account_ref="budget/run",
            deadline=deadline,
            limits=limits,
            resources=[],
            conflict_keys=["verification/project"] if protected else [],
            safe_boundary="protected_phase" if protected else "settled_operation",
            replay_policy="reconcile_before_retry",
            payload=payload,
            required_features=[Feature(feature_id="runtime/workspace-view", version="1")] if view else [],
            extensions={"polyinference/workspace-view": view} if view else {},
        )
        if isinstance(payload, ModelQuery) and payload.phase == "development" and limits.final_phase_reserve:
            reserve = limits.final_phase_reserve
            request = request.model_copy(
                update={
                    "extensions": {
                        **request.extensions,
                        "polyinference/inference-call-reserve": reserve.reconciliation_model_calls
                        + reserve.assessment_model_calls,
                    }
                }
            )
        request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
        self.ports.records.compare_and_publish({}, {}, {key: request.model_dump(mode="json")})
        return request

    async def effect(self, process_id, step, payload, view=None, protected=False):
        result = await self.ports.operations.execute(
            self.ensure_request(process_id, step, payload, view, protected)
        )
        if not result.output_refs:
            raise RuntimeError("Effect returned no observation")
        return result, self.read(result.output_refs[0])

    def history(self, ref):
        return self.read(ref) if ref else []

    def append_history(self, ref, call_id, reply, observation=None):
        history = self.history(ref)
        # Stable call IDs allow a restarted node to retain the same complete pair.
        if any(entry["id"] == call_id for entry in history):
            return ref
        history.append({"id": call_id, "reply": reply, "observation": observation})
        return self.artifact(history).model_dump(mode="json")

    def context(self, instruction, data, history, process_id, schema):
        schema_text = "Return JSON matching this schema: " + json.dumps(schema)
        text = instruction + "\n" + schema_text
        data_text = "Pinned application inputs:\n" + json.dumps(data)
        instruction_ref = self.ports.artifacts.put(text.encode(), self.scope(process_id), "text/plain")
        parts = [
            ContextPart(
                part_id="instructions",
                content=instruction_ref,
                part_kind="instruction",
                trust="application",
                source_ref="prompt/1",
                required=True,
            )
        ]
        data_ref = self.ports.artifacts.put(data_text.encode(), self.scope(process_id), "text/plain")
        parts.append(
            ContextPart(
                part_id="pinned-data",
                content=data_ref,
                part_kind="data",
                trust="retrieved",
                source_ref="application-input-snapshot",
                required=True,
            )
        )
        omitted = []
        # Keep complete pairs; no partial provider tool-call records or mixed-worker histories.
        selected = []
        pinned_messages = [
            {"role": "system", "content": text},
            {"role": "user", "content": data_text},
        ]
        budget = self.config.limits.max_input_tokens_per_call - len(canonical(pinned_messages)) - 2000
        for entry in reversed(history):
            messages = [{"role": "assistant", "content": canonical(entry["reply"]).decode()}]
            if entry["reply"].get("kind") == "action":
                messages.append({"role": "user", "content": canonical(entry["observation"]).decode()})
            # The adapter bounds serialized messages, including the second JSON
            # escaping of tool content and each new message's separating comma.
            size = sum(len(canonical(message)) + 1 for message in messages)
            if size > budget:
                omitted.append(entry["id"])
                continue
            selected.insert(0, entry)
            budget -= size
        for entry in selected:
            call_id = entry["id"]
            action = entry["reply"].get("kind") == "action"
            content = self.ports.artifacts.put(canonical(entry["reply"]), self.scope(process_id))
            parts.append(
                ContextPart(
                    part_id=call_id + "/call",
                    content=content,
                    part_kind="tool_call" if action else "message",
                    trust="model",
                    source_ref=call_id,
                    required=False,
                    call_id=call_id if action else None,
                )
            )
            if action:
                observation = self.ports.artifacts.put(
                    canonical(entry["observation"]), self.scope(process_id)
                )
                parts.append(
                    ContextPart(
                        part_id=call_id + "/result",
                        content=observation,
                        part_kind="tool_result",
                        trust="external_tool",
                        source_ref=call_id,
                        required=False,
                        call_id=call_id,
                    )
                )
        return ContextView(
            view_id=digest(canonical([p.model_dump(mode="json") for p in parts])),
            digest=digest(canonical([p.content.digest for p in parts])),
            parts=parts,
            memory_snapshot_refs=[],
            tool_catalog_digest=digest(
                canonical({"tools": coding_tools(self.config), "setup_tool": "repository.select_branch"})
            ),
            maximum_input_tokens=self.config.limits.max_input_tokens_per_call,
            omitted_refs=omitted,
        )

    def sync_setup(self, state):
        task_key = state["task_ledger_ref"]
        task = self.get(task_key)
        if task.get("category") != "setup":
            return
        from ..contracts import TaskAttempt, TaskSpec

        manifest = self.ports.workspaces.current(state["workspace_id"])
        selection = self.ports.records.get("branch-selection/" + manifest.workspace_id)
        selected = selection and not self.ports.records.get("setup/base-adopted")
        old_spec = TaskSpec.model_validate(self.get(task["spec_ref"]))
        if not selected and old_spec.allowed_change_scope == manifest.allowed_write_paths:
            return
        base = selection[1]["code"] if selected else task["base"]
        spec_id = old_spec.record_id + ":prepared-" + str(manifest.generation)
        spec = old_spec.model_copy(
            update={
                "record_id": spec_id,
                "base": CodeRevision.model_validate(base),
                "allowed_change_scope": manifest.allowed_write_paths,
            }
        )
        attempt_key = "attempt/" + task["attempt_id"]
        attempt = TaskAttempt.model_validate(self.get(attempt_key))
        attempt = attempt.model_copy(
            update={"revision": attempt.revision + 1, "task_spec_ref": spec_id, "original_base": spec.base}
        )
        updates = {
            task_key: {
                **task,
                "base": base,
                "spec_ref": spec_id,
                "assignment": {**task["assignment"], "write_paths": manifest.allowed_write_paths},
            },
            attempt_key: attempt.model_dump(mode="json"),
        }
        immutable = {spec_id: spec.model_dump(mode="json")}
        if selected:
            run = self.get("app/run")
            if set(run["active_workers"]) - {state["process_id"]} or self.ports.records.scan("plan/"):
                raise ValueError("Base selection must precede development planning")
            for head in ("head/initial", "head/provisional", "head/reviewed"):
                updates[head] = {"code": base}
            info = self.get("repository/setup")
            updates["repository/setup"] = {
                **info,
                "base_branch": selection[1]["branch"],
                "base_commit": base["commit_id"],
            }
            immutable["setup/base-adopted"] = selection[1]
        self.ports.workspaces.retag_task_spec(manifest.workspace_id, spec_id, updates, immutable)

    async def model(self, state, senior=False):
        pid = state["process_id"]
        retained = self.ports.records.get(f"request/{pid}/model-{state['logical_step']}")
        if retained:
            result = await self.ports.operations.execute(OperationRequest.model_validate(retained[1]))
            output = self.read(result.output_refs[0])
            if (
                not senior
                and state["phase"] == "development"
                and result.error
                and result.error.code == "ReservedInferenceCalls"
            ):
                return {"kind": "candidate", "summary": "Development allowance ended; preserve final phases"}
            if result.state != "succeeded" and not (
                result.error and result.error.code == "ResponseValidationError"
            ):
                raise RuntimeError(str(output))
            if not senior:
                self.sync_setup(state)
            try:
                reply = json.loads(output["text"])
                if not senior and state["phase"] == "assessment" and reply.get("kind") == "assessment":
                    pinned_part = next(
                        part
                        for part in retained[1]["payload"]["context"]["parts"]
                        if part["part_id"] == "pinned-data"
                    )
                    pinned_text = self.ports.artifacts.read(
                        ArtifactRef.model_validate(pinned_part["content"])
                    ).decode()
                    expected = json.loads(pinned_text.split("Pinned application inputs:\n", 1)[1])["code"]
                    actual = await self.ports.workspaces.revision(state["workspace_id"])
                    if actual.effective_tree_digest != expected["effective_tree_digest"]:
                        reply["repair"] = True
                return reply
            except json.JSONDecodeError:
                return {"invalid_output": output["text"][:2000]}
        process = self.get("process/" + pid)
        role = "senior" if senior else process["role"]
        if senior:
            data = state["input"]
            schema, instruction, phase = SeniorProposal.model_json_schema(), SENIOR, state["mode"]
        else:
            task = self.get(state["task_ledger_ref"])
            manifest = self.ports.workspaces.current(state["workspace_id"])
            current = await self.ports.workspaces.revision(state["workspace_id"])
            data = {
                "assignment": task["assignment"],
                "phase": state["phase"],
                "remaining_model_calls": max(
                    0,
                    self.config.limits.max_model_calls
                    - getattr(
                        self.ports.operations, "inference_calls_used", lambda pid: state.get("calls", 0)
                    )(pid),
                ),
                "workspace_generation": manifest.generation,
                "workspace_view": manifest.view,
                "code": current.model_dump(mode="json"),
                "captured_head": state.get("captured_head"),
                "evidence": state.get("evidence", []),
                "hazards": [v for _, _, v in self.ports.records.scan("hazard/")],
                "memory": self.memory_view(),
            }
            schema, instruction, phase = TypeAdapter(WorkerReply).json_schema(), WORKER, state["phase"]
            if task.get("category") == "setup":
                instruction += BOOTSTRAP
                data["repository_setup"] = self.get("repository/setup")
                data["user_objective"] = self.config.objective
            data["available_tools"] = coding_tools(self.config, task.get("category") == "setup")
        context = self.context(instruction, data, self.history(state.get("trajectory_ref")), pid, schema)
        endpoint = getattr(self.config, self.config.role_bindings[role])
        if endpoint.protocol in {"codex_app_server", "codex_proxy"}:
            payload = AgentJob(
                role=role,
                objective=self.artifact(data, pid),
                context=context,
                workspace_id=state.get("workspace_id", "senior-snapshot"),
                allowed_capabilities=[]
                if senior
                else coding_tools(self.config, task.get("category") == "setup"),
                required_phase_protocol="polyinference/senior-readonly/1"
                if senior
                else "polyinference/worker-phase/1",
                required_guarantees=[],
                response_schema_ref="senior/1" if senior else "worker/1",
                session_ref=None,
            )
        else:
            payload = ModelQuery(
                role=role,
                phase=phase,
                prompt_template_ref="prompt/1",
                context=context,
                response_schema_ref="senior/1" if senior else "worker/1",
                capability_requirements=[],
                temperature=0,
                session_ref=None,
            )
        view = None
        if not senior:
            view = {
                "workspace_id": manifest.workspace_id,
                "manifest_ref": manifest.manifest_id,
                "generation": manifest.generation,
                "view": manifest.view,
            }
        result, output = await self.effect(
            pid,
            f"model-{state['logical_step']}",
            payload,
            view,
            protected=bool(state.get("verification_permit_ref")),
        )
        if (
            not senior
            and state["phase"] == "development"
            and result.error
            and result.error.code == "ReservedInferenceCalls"
        ):
            return {"kind": "candidate", "summary": "Development allowance ended; preserve final phases"}
        if result.state != "succeeded" and not (
            result.error and result.error.code == "ResponseValidationError"
        ):
            raise RuntimeError(output.get("error", "Model effect failed"))
        if len(output["text"].encode()) > self.config.limits.max_output_bytes:
            raise ValueError("Model output exceeds cap")
        if not senior:
            self.sync_setup(state)
        try:
            reply = json.loads(output["text"])
            if not senior and state["phase"] == "assessment" and reply.get("kind") == "assessment":
                after = await self.ports.workspaces.revision(state["workspace_id"])
                if after.effective_tree_digest != current.effective_tree_digest:
                    reply["repair"] = True
        except json.JSONDecodeError:
            reply = {"invalid_output": output["text"][:2000]}
        return reply

    async def capability(self, state, step, tool, args, effect_class="read"):
        retained = self.ports.records.get(f"request/{state['process_id']}/{step}")
        if retained:
            result = await self.ports.operations.execute(OperationRequest.model_validate(retained[1]))
            return result, self.read(result.output_refs[0])
        workspace_id = state.get("workspace_id")
        expected = await self.ports.workspaces.revision(workspace_id) if workspace_id else None
        payload = CapabilityCall(
            capability_id=tool,
            schema_digest=digest(tool.encode()),
            arguments=self.artifact(args, state["process_id"]),
            model_call_id=f"turn-{state['logical_step']}" if str(step).startswith("tool-") else None,
            workspace_id=workspace_id,
            expected_code=expected,
            effect_class=effect_class,
            reconciliation_strategy_ref="journal/1",
        )
        view = None
        if workspace_id:
            manifest = self.ports.workspaces.current(workspace_id)
            view = {
                "workspace_id": workspace_id,
                "manifest_ref": manifest.manifest_id,
                "generation": manifest.generation,
                "view": manifest.view,
            }
        return await self.effect(
            state["process_id"], step, payload, view, protected=bool(state.get("verification_permit_ref"))
        )

    async def checks(self, state, names):
        evidence = []
        for name in names:
            manifest = self.ports.workspaces.current(state["workspace_id"])
            result, output = await self.capability(
                state,
                f"check-{state['logical_step']}-{name}",
                "checks.run",
                {"name": name, "generation": manifest.generation},
                "private_write",
            )
            if result.state != "succeeded":
                raise RuntimeError("Check capability failed: " + str(output))
            evidence.append(CheckEvidence.model_validate(output).model_dump(mode="json"))
        return evidence
