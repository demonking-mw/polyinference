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
    TaskAttempt,
)
from ..domain import (
    PROGRAM_VERSION,
    STATE_VERSION,
    GitPolicy,
    SeniorProposal,
    WorkerReply,
    canonical,
    digest,
    now,
    operation_fingerprint,
)
from ..ports import RuntimePorts
from .prompts import BOOTSTRAP, SENIOR, WORKER
from .runtime_policy import CheckSelection, CodingRuntimePolicy, configured_checks, purpose_checks
from .tasks import coding_tools


class ModelOperationFailure(RuntimeError):
    def __init__(self, result):
        super().__init__(result.error.message if result.error else "Model operation failed")
        self.result = result


def owns_process(records, process_id, program_id="polyinference"):
    process = records.get("process/" + process_id)
    if not process:
        return False
    program = process[1].get("program")
    if not program:
        spec = records.get(process[1].get("spec_ref", ""))
        program = spec[1].get("program") if spec else None
    return bool(program and program.get("program_id") == program_id)


def close_for_cancellation(records, process_id):
    """The coding agent owns its drain policy; cancellation itself is an OS action."""
    if not owns_process(records, process_id):
        return
    run = records.get("app/run")
    if run:
        records.compare_and_publish({"app/run": run[0]}, {"app/run": {
            **run[1], "starts_closed": True, "completion_proposed": False,
            "captured_workers": sorted(set(run[1]["active_workers"]) | set(run[1]["captured_workers"])),
        }})


class AgentServices:
    @property
    def check_definitions(self):
        return configured_checks(self.config, self.ports.records)

    @property
    def acceptance_check_definitions(self):
        return purpose_checks(self.config, self.ports.records, "acceptance")

    @property
    def task_check_definitions(self):
        checks = [*purpose_checks(self.config, self.ports.records, "task"), *self.acceptance_check_definitions]
        return list({check.name: check for check in checks}.values())

    @property
    def setup_check_definitions(self):
        return purpose_checks(self.config, self.ports.records, "prerequisite") or self.task_check_definitions

    def __init__(self, ports: RuntimePorts, config, run_id="run"):
        self.ports, self.config, self.run_id = ports, config, run_id
        self.worker_tasks = {}
        self.worker_limit = config.max_workers
        self.repository = None
        ports.processes.on_cancel = lambda pid: close_for_cancellation(ports.records, pid)
        ports.on_reconciled = self.reconciled
        from ..domain import Assessment, Candidate, NeedsReview

        ports.register_agent_protocol(
            "polyinference/senior-readonly/1", SeniorProposal.model_json_schema()
        )
        ports.register_agent_protocol(
            "polyinference/worker-phase/1",
            TypeAdapter(Candidate | Assessment | NeedsReview).json_schema(),
            workspace="workspace", brokered=True,
            instructions="Execute actions internally using polyinference_tool. Do not return an action as your "
            "final answer. Finish this phase with candidate, assessment or needs_review. "
            "The coding application owns phase changes and publication. "
            "Use only polyinference_tool for files and commands. Native shell, patch and "
            "filesystem tools must not modify the read-only native view.",
        )
        self.program = ProgramRef(
            program_id="polyinference",
            program_version=PROGRAM_VERSION,
            graph_digest=digest(b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))),
            state_schema_version=STATE_VERSION,
            prompt_bundle_digest=digest((WORKER + SENIOR + BOOTSTRAP).encode()),
        )
        self.runtime_policy = CodingRuntimePolicy(self)
        for check in self.check_definitions:
            ports.tools.register_check(check)
        ports.register_capability("checks.configure", self.runtime_policy.configure_checks, input_type=CheckSelection,
                                  effect_class="private_write", workspace=True)
        ports.register_publication_policy(self.program.program_id, self.runtime_policy.publication)
        if config.repository_mode == "in_place":
            from .repository import RepositoryWorkspaces

            ports.register_agent_protocol("polyinference/git-policy/1",
                                          GitPolicy.model_json_schema(), workspace="none")
            self.repository = RepositoryWorkspaces(self)
            ports.install_workspaces(self.repository)
            ports.register_capability("coding.prepare", self.repository.prepare_capability,
                                      effect_class="shared_write", workspace=False)
            ports.register_capability("coding.reconfigure", self.repository.reconfigure,
                                      effect_class="shared_write", workspace=False)
            ports.register_capability("coding.commit", self.repository.commit_capability,
                                      effect_class="shared_write", workspace=True)
            ports.register_capability("coding.publish", self.repository.publish,
                                      effect_class="shared_write", workspace=False)

    def get(self, key):
        row = self.ports.records.get(key)
        if not row:
            raise ValueError("Missing application record: " + key)
        return row[1]

    async def reconciled(self, request, result):
        """Restore coding work after the OS has established known termination."""
        pid = request.scope.process_id
        if not owns_process(self.ports.records, pid, self.program.program_id):
            return
        for key, _, task in self.ports.records.scan("task/"):
            if task["process_id"] != pid or task.get("report_ref"):
                continue
            if self.ports.records.get("workspace/" + task["workspace_id"]):
                await self.ports.workspaces.abort(task["workspace_id"])
            failure = ({"operation_id": request.operation_id,
                        "error": result.error.model_dump(mode="json") if result.error else None,
                        "diagnostics": result.extensions}
                       if isinstance(request.payload, (ModelQuery, AgentJob)) else None)
            self.update(key, {**task, "execution": "interrupted",
                              "exception": "Reconciled operation " + request.operation_id,
                              "model_failure": failure})
            attempt_key = "attempt/" + task["attempt_id"]
            attempt = self.get(attempt_key)
            self.update(attempt_key, {**attempt, "revision": attempt["revision"] + 1,
                                      "execution": "interrupted", "stop_reason": "operator reconciliation"})
        run = self.ports.records.get("app/run")
        if run:
            self.update("app/run", {**run[1], "status": "paused", "starts_closed": True,
                                    "completion_proposed": False,
                                    "active_workers": [p for p in run[1]["active_workers"] if p != pid],
                                    "captured_workers": [p for p in run[1]["captured_workers"] if p != pid],
                                    "blocker": "Termination reconciled; explicitly retry the model or revise the plan"})

    def update(self, key, body):
        if key.startswith("attempt/"):
            body = self.task_attempt(body).model_dump(mode="json")
        row = self.ports.records.get(key)
        self.ports.records.compare_and_publish({key: row[0] if row else 0}, {key: body})

    def task_attempt(self, body, update=None):
        """Validate the new value, preserving prose separately from reason codes.

        Normalizing the old reason also permits retiring an invalid historical
        attempt without losing the diagnostic that made its old schema invalid.
        """
        values = {**body, **(update or {})}
        previous, reason = body.get("stop_reason"), values.get("stop_reason")
        diagnostic = next((value for value in (reason, previous)
                           if value and (len(value) > 256 or any(c.isspace() for c in value))), None)
        if diagnostic:
            ref = self.ports.artifacts.put(diagnostic.encode(), self.scope(), "text/plain")
            values["extensions"] = {**values.get("extensions", {}),
                                    "polyinference/stop-detail": ref.model_dump(mode="json")}
        if reason and (len(reason) > 256 or any(c.isspace() for c in reason)):
            values["stop_reason"] = values["execution"]
        return TaskAttempt.model_validate(values)

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
        self.ports.processes.register(
            spec, endpoint_name, management=role == "senior",
            capabilities=[*coding_tools(self.config, task_data and task_data.get("category") == "setup"),
                          "workspace.commit", "workspace.retain", "records.publish",
                          *(["coding.commit", "coding.publish"] if self.repository else []),
                          *(["coding.prepare", "coding.reconfigure"]
                            if self.repository and process_id == "controller" else []),
                          *(["outputs.deliver"] if process_id == "controller" else [])],
        )

    def process_status(self, process_id, **updates):
        key = "process-status/" + process_id
        current = self.ports.records.get(key)
        status = ProcessStatus.model_validate({**current[1], **updates, "revision": current[1]["revision"] + 1})
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

    def user_updates(self, through):
        return sorted(
            (body for _, _, body in self.ports.records.scan("steering/") if body["sequence"] <= through),
            key=lambda body: body["sequence"],
        )

    def review_report(self, report):
        return {
            "record_id": report["record_id"],
            "task_spec_ref": report["task_spec_ref"],
            "verdict": report["verdict"],
            "code_location": report.get("code_location", "provisional"),
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
        contracts = [check.model_dump(mode="json") for check in self.task_check_definitions]
        contract_paths = [path for path in ("package.json", "pyproject.toml", "Makefile") if path in tree]
        contract_paths += [arg for check in contracts for arg in check["argv"] if arg in tree]
        selected = list(dict.fromkeys(contract_paths + self.config.allowed_write_paths + self.config.closure_paths))
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
            "check_contracts": contracts,
            "paths": sorted(tree)[:100],
            "omitted_path_count": max(0, len(tree) - 100),
            "contents": contents,
            "source_code": code,
        }

    def ensure_request(self, process_id, step, payload, view=None, protected=False, recovery=None):
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
            required_features=[
                *([Feature(feature_id="runtime/workspace-view", version="1")] if view else []),
                *([Feature(feature_id="runtime/model-recovery", version="1")] if recovery else []),
            ],
            extensions={
                **({"polyinference/workspace-view": view} if view else {}),
                **({"polyinference/recovery-of": recovery["operation_id"],
                    "polyinference/recovery-reason": recovery["reason"]} if recovery else {}),
            },
        )
        request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
        self.ports.records.compare_and_publish({}, {}, {key: request.model_dump(mode="json")})
        return request

    async def effect(self, process_id, step, payload, view=None, protected=False, recovery=None):
        result = await self.ports.operations.execute(
            self.ensure_request(process_id, step, payload, view, protected, recovery)
        )
        if not result.output_refs:
            raise RuntimeError("Effect returned no observation")
        return result, self.read(result.output_refs[0])

    def model_call_count(self, process_id):
        return sum(
            body["request"]["scope"]["process_id"] == process_id
            and body["request"]["payload"]["kind"] in {"model_query", "agent_job"}
            for _, _, body in self.ports.records.scan("effect/")
        )

    async def preserve_interrupted(self, task_ref):
        if not self.repository:
            return
        task = self.get(task_ref)
        if not self.ports.records.get("workspace/" + task["workspace_id"]):
            return
        try:
            ref = await self.repository.preserve_interrupted(task["workspace_id"])
            if ref:
                self.update(task_ref, {**task, "preserved_source_ref": ref})
        except Exception as exc:
            self.update(task_ref, {**task, "preservation_issue": str(exc)[:2000]})

    async def model_result(self, original):
        """The OS owns I/O recovery; application grammar stays in this agent."""
        result = await self.ports.operations.execute(original)
        if result.state != "succeeded":
            raise ModelOperationFailure(result)
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
        data = dict(data)
        memory = data.pop("memory", None)
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
        if memory is not None:
            parts.append(ContextPart(part_id="agent-memory",
                content=self.ports.artifacts.put(canonical(memory), self.scope(process_id)),
                part_kind="data", trust="retrieved", source_ref="agent/working-memory",
                required=True, compactable=True))
        omitted = []
        # Supply complete history; the OS applies the declared context policy.
        selected = history
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
        request_text = (
            "Host request: continue this invocation using the pinned application inputs above. "
            "The current phase is " + str(data.get("phase", "planning/review")) + ". "
            "Historical replies describe previous turns. Return the next response required by the current phase."
        )
        parts.append(ContextPart(
            part_id="current-request",
            content=self.ports.artifacts.put(request_text.encode(), self.scope(process_id), "text/plain"),
            part_kind="data", trust="application", source_ref="agent/current-phase", required=True,
        ))
        return ContextView(
            view_id=digest(canonical([p.model_dump(mode="json") for p in parts])),
            digest=digest(canonical([p.content.digest for p in parts])),
            parts=parts,
            memory_snapshot_refs=[],
            tool_catalog_digest=digest(
                canonical({"tools": coding_tools(self.config, setup=True)})
            ),
            maximum_input_tokens=self.config.limits.max_input_tokens_per_call,
            omitted_refs=omitted,
        )

    async def sync_setup(self, state):
        task_key = state["task_ledger_ref"]
        task = self.get(task_key)
        if task.get("category") != "setup":
            return
        from ..contracts import TaskSpec

        manifest = self.ports.workspaces.current(state["workspace_id"])
        selection = self.ports.records.get("branch-selection/" + manifest.workspace_id)
        selected = selection and not self.ports.records.get("setup/base-adopted")
        old_spec = TaskSpec.model_validate(self.get(task["spec_ref"]))
        names = [check.name for check in self.setup_check_definitions]
        if (
            not selected and old_spec.allowed_change_scope == manifest.allowed_write_paths
            and task["assignment"]["checks"] == names
        ):
            return
        base = selection[1]["code"] if selected else task["base"]
        spec_id = old_spec.record_id + ":prepared-" + str(manifest.generation) + "-" + digest(canonical(names))[7:19]
        spec = old_spec.model_copy(
            update={
                "record_id": spec_id,
                "base": CodeRevision.model_validate(base),
                "allowed_change_scope": manifest.allowed_write_paths,
                "acceptance_spec": self.artifact(names),
            }
        )
        attempt_key = "attempt/" + task["attempt_id"]
        attempt_body = self.get(attempt_key)
        attempt = self.task_attempt(
            attempt_body, update={"revision": attempt_body["revision"] + 1,
                                  "task_spec_ref": spec_id, "original_base": spec.base}
        )
        updates = {
            task_key: {
                **task,
                "base": base,
                "spec_ref": spec_id,
                "assignment": {**task["assignment"], "write_paths": manifest.allowed_write_paths, "checks": names},
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
        await self.ports.workspaces.retag_task_spec(manifest.workspace_id, spec_id, updates, immutable)

    async def model(self, state, senior=False):
        pid = state["process_id"]
        retained = self.ports.records.get(f"request/{pid}/model-{state['logical_step']}")
        if retained:
            result, output = await self.model_result(OperationRequest.model_validate(retained[1]))
            if not senior:
                await self.sync_setup(state)
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
            data = dict(state["input"])
            schema, instruction, phase = SeniorProposal.model_json_schema(), SENIOR, state["mode"]
        else:
            task = self.get(state["task_ledger_ref"])
            manifest = self.ports.workspaces.current(state["workspace_id"])
            current = await self.ports.workspaces.revision(state["workspace_id"])
            plan = self.ports.records.get(task.get("plan_ref", ""))
            data = {
                "assignment": task["assignment"],
                "user_objective": self.config.objective,
                "user_updates": self.user_updates(plan[1].get("steering_through", 0) if plan else 0),
                "requirement_policy": "Preserve the user's constraints; this assignment does not replace or narrow them.",
                "phase": state["phase"],
                "workspace_generation": manifest.generation,
                "workspace_view": manifest.view,
                "code": current.model_dump(mode="json"),
                "captured_head": state.get("captured_head"),
                "evidence": state.get("evidence", []),
                "hazards": [v for _, _, v in self.ports.records.scan("hazard/")],
                "memory": self.memory_view(),
                "configured_checks": [check.model_dump(mode="json") for check in self.check_definitions],
                "check_purposes": {purpose: [c.name for c in purpose_checks(self.config, self.ports.records, purpose)]
                                   for purpose in ("prerequisite", "task", "acceptance")},
            }
            schema, instruction, phase = TypeAdapter(WorkerReply).json_schema(), WORKER, state["phase"]
            if task.get("category") == "setup":
                instruction += BOOTSTRAP
                data["repository_setup"] = self.get("repository/setup")
            data["write_authority"] = self.ports.workspaces.authority(manifest.workspace_id)
            data["available_tools"] = coding_tools(self.config, task.get("category") == "setup")
        if self.repository:
            notes = self.ports.records.get("coding/startup-notes")
            data["startup_notes"] = notes[1]["notes"] if notes else []
            data["preparation_issues"] = self.repository.preparation_issues(
                None if senior else state["workspace_id"])
        data["response_budget"] = {
            "max_output_tokens": self.config.limits.max_output_tokens_per_call,
            "max_output_bytes": self.config.limits.max_output_bytes,
            "recommended_response_bytes": min(4096, self.config.limits.max_output_bytes),
            "policy": "Includes thinking. Use small complete responses and incremental edits across turns.",
        }
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
        request = self.ensure_request(
            pid,
            f"model-{state['logical_step']}",
            payload,
            view,
            protected=bool(state.get("verification_permit_ref")),
            recovery=state.get("model_recovery"),
        )
        result, output = await self.model_result(request)
        if not senior:
            await self.sync_setup(state)
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
        if self.repository and tool == "checks.run":
            await self.repository.prepare_dependencies(state)
        if self.repository:
            tool = {"workspace.commit": "coding.commit", "records.publish": "coding.publish"}.get(tool, tool)
        retained = self.ports.records.get(f"request/{state['process_id']}/{step}")
        if retained:
            result = await self.ports.operations.execute(OperationRequest.model_validate(retained[1]))
            return result, self.read(result.output_refs[0])
        capability = self.ports.capabilities.get(tool)
        workspace_id = state.get("workspace_id") if capability.workspace else None
        if workspace_id:
            args = {"generation": self.ports.workspaces.current(workspace_id).generation, **args}
        expected = await self.ports.workspaces.revision(workspace_id) if workspace_id else None
        payload = CapabilityCall(
            capability_id=tool,
            schema_digest=capability.schema_digest,
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
