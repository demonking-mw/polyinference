"""Small runtime: durable effects, static routing, direct capabilities and storage."""

from __future__ import annotations

import asyncio
import fcntl
import json
import math
from contextlib import AsyncExitStack

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ..contracts import (
    ActualBackend,
    AgentJob,
    CapabilityCall,
    ErrorDetail,
    ModelQuery,
    OperationResult,
    Publication,
    Scope,
    UsageMeasure,
)
from ..domain import canonical, digest, now, operation_fingerprint
from .codex import CodexAppServer, CodexProxy
from .exclusive import Exclusive
from .inference import Admission, EndpointError, HTTPInference, UnknownExecution
from .processes import Processes
from .storage import Artifacts, Records
from .tools import Tools
from .workspace import Workspaces


class UncertainEffect(RuntimeError):
    pass


class KernelRuntime:
    def __init__(self, config, run_id="run"):
        self.config, self.run_id = config, run_id
        self.scope = Scope(
            tenant_id="standalone", project_id=digest(str(config.repo_path).encode()), run_id=run_id
        )
        self.config.state_path.mkdir(parents=True, exist_ok=True)
        self.driver = (self.config.state_path / "coordinator.lock").open("a+")
        try:
            fcntl.flock(self.driver, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.driver.close()
            raise RuntimeError("Another coordinator owns this state directory") from exc
        self.records = Records(config.state_path / "records.sqlite")
        self.artifacts = Artifacts(config.state_path / "artifacts", config.max_artifact_bytes)
        self.exclusive = Exclusive(self.records, config.limits.max_wall_time_ms / 1000)
        self.workspaces = Workspaces(config, self.records, self.exclusive, self.artifacts, self.scope)
        self.tools = Tools(config, self.workspaces, self.exclusive, self.artifacts, self.scope)
        self.operations = self
        self.processes = Processes(self.records, config.max_workers)
        self.clients = {}
        self.admission = {}
        self.inflight = {}
        self.stack = AsyncExitStack()
        self.closing = False

    def negotiate(self, requirements):
        supported = {
            "runtime/" + name
            for name in (
                "model-query",
                "effect-journal",
                "private-workspace",
                "global-shell-exclusion",
                "verification-exclusion",
                "atomic-record-publication",
                "scoped-workspace-copy",
                "workspace-view",
                "local-cbatch-admission",
                "direct-tools",
                "artifacts",
                "persistent-checkpoints",
                "fixed-role-routing",
                "repository-baseline",
                "shell-run",
                "project-scope",
                "agent-job",
                "native-broker-callbacks",
            )
        }
        for requirement in requirements:
            if getattr(requirement, "necessity", "required") == "required" and (
                requirement.feature_id not in supported or requirement.version != "1"
            ):
                raise ValueError("Unsupported required runtime feature: " + requirement.feature_id)

    async def open(self):
        self.checkpointer = await self.stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string(str(self.config.state_path / "checkpoints.sqlite"))
        )
        pinned = self.records.get("runtime/config")
        fingerprint = digest(canonical(self.config))
        if pinned and pinned[1]["digest"] != fingerprint:
            raise RuntimeError("Configuration changed: start a new run/state directory")
        self.records.put_once("runtime/config", {"digest": fingerprint, "run_id": self.run_id})
        self.records.put_once("runtime/kernel", {"version": "simple-os/1"})
        for name in sorted(set(self.config.role_bindings.values())):
            endpoint = getattr(self.config, name)
            cls = (
                CodexAppServer
                if endpoint.protocol == "codex_app_server"
                else (CodexProxy if endpoint.protocol == "codex_proxy" else HTTPInference)
            )
            self.clients[name] = cls(endpoint)
            if hasattr(self.clients[name], "output_cap"):
                self.clients[name].output_cap = self.config.max_model_response_bytes
            self.admission[name] = Admission(
                endpoint.max_inflight,
                endpoint.reserved_context_tokens,
                records=self.records,
                name=name,
                max_queued=self.config.max_queued_operations,
            )
        # Recovery does not infer that a lost process/HTTP connection means stopped.
        for key, rev, body in self.records.scan("effect/"):
            if body["state"] in {"submitting", "active"}:
                self.records.compare_and_publish({key: rev}, {key: {**body, "state": "uncertain"}})
        await self.reconcile_known()
        for admission in self.admission.values():
            admission.restore()
        return self

    async def reconcile_known(self):
        """Only host-verifiable receipts/commit records can settle automatically."""
        for key, rev, body in self.records.scan("effect/"):
            if body["state"] != "uncertain":
                continue
            from ..contracts import OperationRequest

            request = OperationRequest.model_validate(body["request"])
            payload = request.payload
            output = None
            if isinstance(payload, Publication) and self.records.get(payload.receipt_ref):
                output = {"receipt_ref": payload.receipt_ref}
            elif isinstance(payload, CapabilityCall):
                arguments = json.loads(self.artifacts.read(payload.arguments))
                if payload.capability_id in {"records.publish", "workspace.retain"} and self.records.get(
                    arguments["receipt_ref"]
                ):
                    output = {
                        "receipt_ref": arguments["receipt_ref"],
                        **(
                            {"code_location": "private"}
                            if payload.capability_id == "workspace.retain"
                            else {"published": True}
                        ),
                    }
                elif payload.capability_id == "workspace.commit":
                    retained = self.records.get("commit/" + request.operation_id)
                    if retained:
                        output = retained[1]
            if output is None:
                continue
            result = OperationResult(
                record_id="result/" + request.operation_id,
                revision=1,
                scope=request.scope,
                created_at=now(),
                operation_id=request.operation_id,
                logical_step_id=request.logical_step_id,
                state="succeeded",
                output_refs=[self.artifacts.put(canonical(output), request.scope)],
                paired_call_id=None,
                binding_ref=None,
                binding_generation=0,
                actual_backend=None,
                usage=[],
                execution_termination="confirmed_stopped",
                effects="known",
                started_at=request.created_at,
                finished_at=now(),
                error=None,
                continuation_ref=None,
            )
            self.records.compare_and_publish(
                {key: rev},
                {
                    key: {
                        **body,
                        "state": "succeeded",
                        "result": result.model_dump(mode="json"),
                        "reconciliation": "durable_host_receipt",
                    }
                },
            )

    async def close(self):
        if self.closing:
            return
        self.closing = True
        await self.processes.close()
        tasks = list(self.inflight.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for client in self.clients.values():
            await client.close()
        self.workspaces.blocking.close()
        await self.stack.aclose()
        self.records.db.close()
        self.driver.close()

    def uncertain(self):
        return [key[7:] for key, _, body in self.records.scan("effect/") if body["state"] == "uncertain"]

    def _update(self, key, body):
        current = self.records.get(key)
        self.records.compare_and_publish({key: current[0] if current else 0}, {key: body})

    async def execute(self, request):
        key = "effect/" + request.operation_id
        saved = self.records.get(key)
        expected_digest = operation_fingerprint(request)
        self.negotiate(request.required_features)
        if request.intent_digest != expected_digest:
            raise ValueError("Intent fingerprint mismatch")
        if request.scope.run_id != self.run_id or request.scope.project_id != self.scope.project_id:
            raise ValueError("Unauthenticated runtime scope")
        if saved:
            if saved[1]["fingerprint"] != expected_digest:
                raise ValueError("Operation ID reused with changed intent")
            if saved[1].get("result"):
                return OperationResult.model_validate(saved[1]["result"])
            if request.operation_id in self.inflight:
                return await asyncio.shield(self.inflight[request.operation_id])
            if saved[1]["state"] != "prepared":
                raise UncertainEffect(request.operation_id)
        if self.closing:
            raise RuntimeError("Kernel is closing")
        if self.uncertain():
            raise UncertainEffect("Reconcile uncertain effects before dispatch")
        process = self.records.get("process/" + request.scope.process_id)
        if not process:
            raise ValueError("Unknown process principal")
        if request.owner_generation != process[1]["owner_generation"]:
            raise ValueError("Stale owner generation")
        if request.grant_ref != "grant/run" or request.budget_account_ref != "budget/run":
            raise ValueError("Unknown grant or budget account")
        if request.limits != self.config.limits:
            raise ValueError("Operation limits differ from the pinned process grant")
        if request.conflict_keys and not (
            self.records.get("permit/verification/project")
            and self.records.get("permit/verification/project")[1].get("process_id")
            == request.scope.process_id
        ):
            raise ValueError("Protected operation requires current verification ownership")
        logical_key = "logical/" + digest(canonical([request.scope.process_id, request.logical_step_id]))
        logical = self.records.get(logical_key)
        if logical and logical[1]["operation_id"] != request.operation_id:
            raise ValueError("Logical step already has an operation ID")
        if not saved:
            prior = [
                body
                for _, _, body in self.records.scan("effect/")
                if body["request"]["scope"]["process_id"] == request.scope.process_id
            ]
            if len(prior) >= request.limits.max_steps:
                raise ValueError("Process operation allowance exhausted")
            if (
                isinstance(request.payload, (ModelQuery, AgentJob))
                and sum(body["request"]["payload"]["kind"] in {"model_query", "agent_job"} for body in prior)
                >= request.limits.max_model_calls
            ):
                raise ValueError("Process model-call allowance exhausted")
        parent = (
            self.records.get("effect/" + request.causal_parent_ref) if request.causal_parent_ref else None
        )
        if request.causal_parent_ref:
            if (
                not parent
                or parent[1]["state"] != "active"
                or parent[1]["request"]["scope"] != request.scope.model_dump(mode="json")
            ):
                raise ValueError("Subordinate effect requires its active parent and inherited scope")
            if not isinstance(request.payload, CapabilityCall) or request.payload.capability_id not in {
                "files.list",
                "files.read",
                "files.search",
                "files.patch",
                "files.write",
                "files.delete",
                "checks.run",
                "shell.run",
                "repository.select_branch",
            }:
                raise ValueError("Only actual broker tool callbacks may be subordinate")
            if request.payload.capability_id not in parent[1]["request"]["payload"].get(
                "allowed_capabilities", []
            ):
                raise ValueError("Subordinate tool exceeds its parent capability grant")
        if isinstance(request.payload, (ModelQuery, AgentJob)) and request.payload.role != process[1]["role"]:
            raise ValueError("Model role differs from authenticated process binding")
        for _, _, body in self.records.scan("effect/"):
            if (
                not request.causal_parent_ref
                and body["request"]["scope"]["process_id"] == request.scope.process_id
                and body["state"] in {"prepared", "active", "submitting"}
                and body["request"]["operation_id"] != request.operation_id
                and not body["request"].get("causal_parent_ref")
            ):
                raise ValueError("Only one top-level active effect per process")
        self.records.put_once(logical_key, {"operation_id": request.operation_id})
        self._update(
            key,
            {
                "fingerprint": expected_digest,
                "state": "prepared",
                "request": request.model_dump(mode="json"),
                "result": None,
            },
        )
        task = asyncio.create_task(self._dispatch(request, key))
        self.inflight[request.operation_id] = task
        try:
            return await asyncio.shield(task)
        finally:
            if task.done():
                self.inflight.pop(request.operation_id, None)

    def _reserve_budget(self, request, amount):
        allocation = "allocation/" + request.operation_id
        if self.records.get(allocation):
            return
        keys = [
            ("budget/run", self.config.run_token_budget),
            ("budget/process/" + request.scope.process_id, request.limits.max_total_tokens),
        ]
        expected, updates = {}, {}
        for key, limit in keys:
            if key == "budget/run" and request.payload.role != "senior":
                limit -= self.config.review_token_reserve
            saved = self.records.get(key)
            used = saved[1]["reserved_or_used"] if saved else 0
            if used + amount > limit:
                raise EndpointError("Aggregate token budget exhausted: " + key)
            expected[key] = saved[0] if saved else 0
            updates[key] = {"reserved_or_used": used + amount}
        self.records.compare_and_publish(
            expected,
            updates,
            {allocation: {"amount": amount, "process_id": request.scope.process_id, "settled": False}},
        )

    def _reserve_spend(self, request, amount, endpoint):
        rate = endpoint.estimated_microusd_per_token
        if rate is None:
            return
        key = "spend-allocation/" + request.operation_id
        if self.records.get(key):
            return
        cost = math.ceil(amount * rate)
        expected, updates = {}, {}
        for pointer, limit in (
            ("spend/run", self.config.run_spend_budget_microusd),
            ("spend/process/" + request.scope.process_id, request.limits.max_api_spend_microusd),
        ):
            saved = self.records.get(pointer)
            used = saved[1]["estimated_microusd"] if saved else 0
            if limit and used + cost > limit:
                raise EndpointError("Estimated spend budget exhausted: " + pointer)
            expected[pointer] = saved[0] if saved else 0
            updates[pointer] = {"estimated_microusd": used + cost}
        self.records.compare_and_publish(
            expected, updates, {key: {"cost": cost, "rate": rate, "settled": False}}
        )

    def _settle_budget(self, request, actual=None):
        key = "allocation/" + request.operation_id
        retained = self.records.get(key)
        if not retained or retained[1]["settled"]:
            return
        allocation = retained[1]
        amount = actual if isinstance(actual, int) and actual >= 0 else allocation["amount"]
        expected, updates = (
            {key: retained[0]},
            {key: {**allocation, "amount": amount, "settled": True, "provider_reported": actual is not None}},
        )
        for pointer in ("budget/run", "budget/process/" + request.scope.process_id):
            row = self.records.get(pointer)
            expected[pointer] = row[0]
            updates[pointer] = {
                "reserved_or_used": row[1]["reserved_or_used"] + amount - allocation["amount"]
            }
        spend_key = "spend-allocation/" + request.operation_id
        spend = self.records.get(spend_key)
        if spend and not spend[1]["settled"]:
            cost = math.ceil(amount * spend[1]["rate"])
            expected[spend_key] = spend[0]
            updates[spend_key] = {**spend[1], "cost": cost, "settled": True}
            for pointer in ("spend/run", "spend/process/" + request.scope.process_id):
                row = self.records.get(pointer)
                expected[pointer] = row[0]
                updates[pointer] = {
                    "estimated_microusd": row[1]["estimated_microusd"] + cost - spend[1]["cost"]
                }
        self.records.compare_and_publish(expected, updates)

    def _effect_status(self, request, active):
        from ..contracts import ProcessStatus, WaitReason

        key = "process-status/" + request.scope.process_id
        retained = self.records.get(key)
        if not retained:
            return
        status = ProcessStatus.model_validate(retained[1])
        pending = list(status.pending_operations)
        if active and request.operation_id not in pending:
            pending.append(request.operation_id)
        if not active:
            pending = [value for value in pending if value != request.operation_id]
        wait = (
            WaitReason(
                wait_kind="operation",
                target_refs=pending,
                holder_refs=[],
                since=now(),
                deadline=request.deadline,
                diagnostic_ref=None,
            )
            if pending
            else None
        )
        updated = status.model_copy(
            update={
                "revision": status.revision + 1,
                "state": "waiting" if pending else "ready",
                "wait": wait,
                "pending_operations": pending,
            }
        )
        self.records.compare_and_publish({key: retained[0]}, {key: updated.model_dump(mode="json")})

    async def _dispatch(self, request, key):
        started = now()
        payload = request.payload
        usage, backend = [], None
        state, termination, effects, error = "succeeded", "confirmed_stopped", "known", None
        outputs = []
        saved = self.records.get(key)[1]
        dispatched = False
        try:
            if request.deadline <= now():
                raise EndpointError("Operation deadline expired before dispatch")
            requirement = request.extensions.get("polyinference/workspace-view")
            if requirement:
                from ..workspace_contracts import ViewRequirement

                view = ViewRequirement.model_validate(requirement)
                current = self.workspaces.current(view.workspace_id)
                if (current.generation, current.manifest_id, current.view) != (
                    view.generation,
                    view.manifest_ref,
                    view.view,
                ):
                    raise ValueError("Stale workspace generation/view")
                if current.process_id != request.scope.process_id:
                    raise ValueError("Workspace view belongs to another process")
            self._effect_status(request, True)
            if isinstance(payload, (ModelQuery, AgentJob)):
                name = self.config.role_bindings[payload.role]
                endpoint = getattr(self.config, name)
                messages = []
                for part in payload.context.parts:
                    text = self.artifacts.read(part.content).decode()
                    messages.append(
                        {
                            "role": "system"
                            if part.part_kind == "instruction" and part.trust in {"application", "user"}
                            else "assistant"
                            if part.part_kind in {"message", "tool_call"}
                            else "user",
                            "content": text,
                        }
                    )
                # UTF-8 byte count is a conservative token bound, not an average chars/token guess.
                input_bound = len(canonical(messages))
                reserved = input_bound + request.limits.max_output_tokens_per_call
                if input_bound > min(
                    payload.context.maximum_input_tokens, request.limits.max_input_tokens_per_call
                ):
                    raise EndpointError("Required context does not fit; no silent pin removal")
                if reserved > endpoint.max_context_tokens:
                    raise EndpointError("Context/output cannot fit backend")
                manifest_ref = request.extensions.get("polyinference/workspace-view")
                if manifest_ref:
                    current = self.workspaces.current(manifest_ref["workspace_id"])
                    from ..workspace_contracts import ViewRequirement

                    required_view = ViewRequirement.model_validate(manifest_ref)
                    if (current.generation, current.manifest_id, current.view) != (
                        required_view.generation,
                        required_view.manifest_ref,
                        required_view.view,
                    ):
                        raise ValueError("Stale model workspace view")
                finishing = bool(request.conflict_keys and "verification/project" in request.conflict_keys)
                async with self.admission[name].reserve(
                    reserved,
                    finishing,
                    request.operation_id,
                    max(0, (request.deadline - now()).total_seconds()),
                ):
                    if request.deadline <= now():
                        raise EndpointError("Deadline expired before provider submission")
                    self._reserve_budget(request, reserved)
                    self._reserve_spend(request, reserved, endpoint)
                    self._update(key, {**saved, "state": "submitting"})
                    self._update(key, {**saved, "state": "active"})
                    timeout = min(endpoint.timeout_seconds, (request.deadline - now()).total_seconds())
                    if isinstance(payload, ModelQuery):
                        if endpoint.protocol not in {"chat", "responses", "gemini", "anthropic"}:
                            raise EndpointError("Native backend requires AgentJob")
                        dispatched = True
                        result = await asyncio.wait_for(
                            self.clients[name].generate(messages, request.limits.max_output_tokens_per_call),
                            timeout,
                        )
                    else:
                        from pydantic import TypeAdapter

                        from ..domain import Assessment, Candidate, NeedsReview, SeniorProposal

                        callback = None
                        if payload.required_phase_protocol == "polyinference/senior-readonly/1":
                            snapshot = self.workspaces.snapshot_root(payload.workspace_id)
                            schema = SeniorProposal.model_json_schema()
                        elif (
                            payload.required_phase_protocol == "polyinference/worker-phase/1"
                            and endpoint.brokered_tools
                        ):
                            manifest = self.workspaces.current(payload.workspace_id)
                            if manifest.process_id != request.scope.process_id:
                                raise ValueError("Native workspace owner mismatch")
                            snapshot = self.workspaces.root_for(manifest)
                            schema = TypeAdapter(Candidate | Assessment | NeedsReview).json_schema()

                            async def callback(call_id, arguments):
                                return await self._native_callback(request, call_id, arguments)
                        else:
                            raise EndpointError("Unsupported native phase protocol")
                        # Direct app-server has native shell disabled: only actual broker
                        # callbacks take shell. An opaque read-only proxy needs wider exclusion.
                        from .codex import NativeJobStopped

                        native_shell = None
                        if endpoint.protocol == "codex_proxy":
                            native_shell = await self.exclusive.acquire(
                                "shell/installation", request.scope.process_id
                            )
                        try:
                            dispatched = True

                            async def observer(event, thread_id, turn_id):
                                current = self.records.get(key)[1]
                                self._update(
                                    key,
                                    {
                                        **current,
                                        "provider": {
                                            "event": event,
                                            "thread_id": thread_id,
                                            "turn_id": turn_id,
                                        },
                                    },
                                )

                            options = (
                                {"observer": observer}
                                if isinstance(self.clients[name], CodexAppServer)
                                else {}
                            )
                            if callback:
                                result = await asyncio.wait_for(
                                    self.clients[name].generate_job(
                                        messages, snapshot, schema, callback, **options
                                    ),
                                    timeout,
                                )
                            else:
                                result = await asyncio.wait_for(
                                    self.clients[name].generate_job(messages, snapshot, schema, **options),
                                    timeout,
                                )
                        except NativeJobStopped:
                            if native_shell:
                                await self.exclusive.release(native_shell, request.scope.process_id)
                            raise
                        except BaseException as exc:
                            raise UnknownExecution(
                                "Native job did not establish a terminal result: "
                                + type(exc).__name__
                                + ": "
                                + str(exc)[:1500]
                            ) from exc
                        else:
                            if native_shell:
                                await self.exclusive.release(native_shell, request.scope.process_id)
                backend = ActualBackend(
                    catalog_ref="static/1",
                    backend_id=name,
                    model_version=result["model"],
                    harness_version=endpoint.protocol,
                    inference_location=endpoint.physical_location,
                    harness_location="local",
                    provider_session_ref=result.get("session_id"),
                )
                raw_usage = result.get("usage")
                total = raw_usage.get("total_tokens") if raw_usage else None
                if not isinstance(total, int) or isinstance(total, bool) or total < 0:
                    total = None
                self._settle_budget(request, total)
                usage = [
                    UsageMeasure(
                        metric="tokens",
                        unit="tokens",
                        value=total,
                        provenance="provider_reported" if total is not None else "unknown",
                        account_scope_ref=request.budget_account_ref,
                    )
                ]
                outputs = [self.artifacts.put(canonical(result), request.scope)]
            elif isinstance(payload, CapabilityCall):
                self._authorize_capability(request)
                self._update(key, {**saved, "state": "submitting"})
                dispatched = True
                if payload.workspace_id:
                    manifest = self.workspaces.current(payload.workspace_id)
                    if manifest.process_id != request.scope.process_id:
                        raise ValueError("Workspace belongs to another process")
                arguments = json.loads(self.artifacts.read(payload.arguments))
                if payload.capability_id == "workspace.retain":
                    staged = self.records.get("staged/" + arguments["receipt_ref"])
                    if not staged:
                        raise ValueError("Missing private commit batch")
                    self._publish(staged[1], request.scope.process_id)
                    result = {"receipt_ref": arguments["receipt_ref"], "code_location": "private"}
                elif payload.capability_id == "records.publish":
                    self._publish(arguments, request.scope.process_id)
                    result = {"published": True, "receipt_ref": arguments["receipt_ref"]}
                elif payload.capability_id == "workspace.commit":
                    owner = self.records.get("permit/verification/project")
                    if not owner or owner[1].get("process_id") != request.scope.process_id:
                        raise ValueError("Commit preparation requires verification ownership")
                    actual = await self.workspaces.revision(payload.workspace_id)
                    if (
                        payload.expected_code
                        and actual.effective_tree_digest != payload.expected_code.effective_tree_digest
                    ):
                        raise ValueError("Commit content precondition failed")
                    head = self.workspaces.current(payload.workspace_id).captured_head
                    code = await self.workspaces.commit(payload.workspace_id, head, request.operation_id)
                    result = code.model_dump(mode="json")
                else:
                    result = await self.tools.call(payload, arguments)
                outputs = [self.artifacts.put(canonical(result), request.scope)]
            elif isinstance(payload, Publication):
                self._update(key, {**saved, "state": "submitting"})
                dispatched = True
                staged = self.records.get("staged/" + payload.receipt_ref)
                if not staged:
                    raise ValueError("Missing immutable publication batch")
                self._publish(staged[1], request.scope.process_id)
                outputs = [self.artifacts.put(canonical({"receipt_ref": payload.receipt_ref}), request.scope)]
            else:
                raise ValueError("Unsupported payload")
        except (UnknownExecution, asyncio.TimeoutError, asyncio.CancelledError) as exc:
            if not dispatched:
                self._update(key, {**saved, "state": "prepared"})
                if isinstance(payload, (ModelQuery, AgentJob)):
                    await self.admission[self.config.role_bindings[payload.role]].release_unsubmitted(
                        request.operation_id
                    )
                self._effect_status(request, False)
                raise
            self._update(key, {**self.records.get(key)[1], "state": "uncertain", "diagnostic": str(exc)})
            raise UncertainEffect(request.operation_id) from exc
        except Exception as exc:
            self._settle_budget(request, None if dispatched else 0)
            state, termination = "failed", "confirmed_stopped"
            error = ErrorDetail(
                code=type(exc).__name__,
                message=str(exc)[:4000],
                retryable_after_reconciliation=False,
                retry_after_ms=None,
            )
            outputs = [self.artifacts.put(canonical({"error": str(exc)[:4000]}), request.scope)]
        result = OperationResult(
            record_id="result/" + request.operation_id,
            revision=1,
            scope=request.scope,
            created_at=now(),
            operation_id=request.operation_id,
            logical_step_id=request.logical_step_id,
            state=state,
            output_refs=outputs,
            paired_call_id=getattr(payload, "model_call_id", None),
            binding_ref=backend.backend_id if backend else None,
            binding_generation=1 if backend else 0,
            actual_backend=backend,
            usage=usage,
            execution_termination=termination,
            effects=effects,
            started_at=started,
            finished_at=now(),
            error=error,
            continuation_ref=None,
        )
        self._update(
            key, {**self.records.get(key)[1], "state": state, "result": result.model_dump(mode="json")}
        )
        self._effect_status(request, False)
        return result

    def _authorize_capability(self, request):
        payload = request.payload
        process = self.records.get("process/" + request.scope.process_id)[1]
        if payload.capability_id == "records.publish":
            if process["role"] != "senior":
                raise ValueError("Record publication capability requires a senior process")
            return
        if payload.capability_id in {"workspace.commit", "workspace.retain"}:
            return  # Ownership, content and final write scope are validated by the broker.
        if not payload.workspace_id:
            raise ValueError("Tool requires a workspace")
        manifest = self.workspaces.current(payload.workspace_id)
        spec = self.records.get(manifest.task_spec_ref)
        if spec and spec[1].get("kind") != "task_spec":
            spec = None
        allowed = (
            spec[1].get("allowed_capabilities", [])
            if spec
            else [
                "files.list",
                "files.read",
                "files.search",
                "files.patch",
                "files.write",
                "files.delete",
                "checks.run",
            ]
        )
        if not spec and self.config.shell_execution != "disabled":
            allowed.append("shell.run")
        if payload.capability_id not in allowed:
            raise ValueError("Capability exceeds the task grant")
        if payload.capability_id == "checks.run" and spec:
            arguments = json.loads(self.artifacts.read(payload.arguments))
            from ..contracts import ArtifactRef

            permitted = json.loads(
                self.artifacts.read(ArtifactRef.model_validate(spec[1]["acceptance_spec"]))
            )
            if arguments.get("name") not in permitted:
                raise ValueError("Check exceeds the task grant")

    async def _native_callback(self, parent, call_id, arguments):
        if (
            not isinstance(arguments, dict)
            or arguments.get("tool") not in parent.payload.allowed_capabilities
        ):
            raise ValueError("Native tool outside grant")
        existing_count = sum(
            1
            for _, _, value in self.records.scan("effect/")
            if value["request"].get("causal_parent_ref") == parent.operation_id
        )
        manifest = self.workspaces.current(parent.payload.workspace_id)
        args = {**arguments.get("arguments", {}), "generation": manifest.generation}
        payload = CapabilityCall(
            capability_id=arguments["tool"],
            schema_digest=digest(arguments["tool"].encode()),
            arguments=self.artifacts.put(canonical(args), parent.scope),
            model_call_id=call_id,
            workspace_id=manifest.workspace_id,
            expected_code=await self.workspaces.revision(manifest.workspace_id),
            effect_class="read"
            if arguments["tool"] in {"files.read", "files.list", "files.search"}
            else "private_write",
            reconciliation_strategy_ref="journal/1",
        )
        operation_id = digest(canonical([parent.operation_id, call_id]))
        retained = self.records.get("effect/" + operation_id)
        if retained:
            child = __import__(
                "polyinference.contracts", fromlist=["OperationRequest"]
            ).OperationRequest.model_validate(retained[1]["request"])
            original = json.loads(self.artifacts.read(child.payload.arguments))
            if child.payload.capability_id != arguments["tool"] or {
                k: v for k, v in original.items() if k != "generation"
            } != arguments.get("arguments", {}):
                raise ValueError("Native callback ID reused with changed arguments")
        else:
            if existing_count >= parent.limits.max_steps:
                raise ValueError("Native callback allowance exhausted")
            child = parent.model_copy(
                update={
                    "record_id": "request/" + operation_id,
                    "operation_id": operation_id,
                    "logical_step_id": parent.logical_step_id + "/" + call_id,
                    "intent_digest": digest(canonical(payload)),
                    "causal_parent_ref": parent.operation_id,
                    "payload": payload,
                }
            )
        view = {
            "workspace_id": manifest.workspace_id,
            "manifest_ref": manifest.manifest_id,
            "generation": manifest.generation,
            "view": manifest.view,
        }
        if not retained:
            child = child.model_copy(update={"extensions": {"polyinference/workspace-view": view}})
            child = child.model_copy(update={"intent_digest": operation_fingerprint(child)})
        result = await self.execute(child)
        return {"state": result.state, "observation": json.loads(self.artifacts.read(result.output_refs[0]))}

    def _publish(self, arguments, process_id):
        receipt = self.records.get(arguments["receipt_ref"])
        if receipt:
            return  # Prior atomic publication wins replay, regardless of retired permits.
        if not self.exclusive.owns(arguments["permit_ref"], "verification/project", process_id):
            raise ValueError("Publication requires current verification permit")
        expected, updates = dict(arguments["expected"]), dict(arguments["updates"])
        reports = [v for k, v in arguments["immutable"].items() if k.startswith("report/")]
        candidate = (updates.get("head/provisional") or {}).get("code")
        if reports:
            candidate = reports[0]["final_code"]
        if candidate:
            head = self.records.get("head/provisional")
            if expected.get("head/provisional") != head[0]:
                raise ValueError("Code publication requires expected shared head")
            minted = [
                value
                for _, _, value in self.records.scan("commit-info/")
                if value["code"] == candidate and value["process_id"] == process_id
            ]
            if not minted or minted[0]["parent"] != head[1]["code"]:
                raise ValueError("Candidate must be a broker commit parented on the current shared head")
        for report in reports:
            if report["process_id"] != process_id:
                raise ValueError("Report belongs to another process")
            private = report.get("code_location") == "private"
            if private and "head/provisional" in updates:
                raise ValueError("Private failed commit must not advance the shared head")
            if report["verdict"] != "successful":
                version, run = self.records.get("app/run")
                expected["app/run"] = version
                updates["app/run"] = {
                    **run,
                    "starts_closed": True,
                    "completion_proposed": False,
                    "review_reason": "worker_" + report["verdict"],
                    "captured_workers": sorted(set(run["captured_workers"]) | set(run["active_workers"])),
                }
        self.records.compare_and_publish(expected, updates, arguments["immutable"])

    def diagnostics(self):
        return {
            "kernel": "simple-os/1",
            "admission": {name: value.snapshot() for name, value in self.admission.items()},
            "processes": [value for _, _, value in self.records.scan("process-status/")],
            "uncertain_operations": self.uncertain(),
            "owners": [value for _, _, value in self.records.scan("permit/") if value.get("process_id")],
            "budgets": {key: value for key, _, value in self.records.scan("budget/")},
            "spend": {key: value for key, _, value in self.records.scan("spend/")},
        }

    async def reconcile_stopped(self, operation_id, evidence):
        """Operator attestation, never an inference from connection loss or timeout.

        Caller must establish provider AND host effects have stopped. A reconciled
        effect is failed, never retried under a new ID; the worker returns to review.
        """
        if any(not task.done() for task in self.inflight.values()):
            raise ValueError("Reconcile only with dispatch stopped")
        key = "effect/" + operation_id
        retained = self.records.get(key)
        if not retained or retained[1]["state"] != "uncertain":
            raise ValueError("Operation is not uncertain")
        if not evidence.strip() or len(evidence.encode()) > self.config.limits.max_output_bytes:
            raise ValueError("Supply bounded evidence of provider and host termination")
        from ..contracts import OperationRequest

        request = OperationRequest.model_validate(retained[1]["request"])
        pid = request.scope.process_id
        ref = self.artifacts.put(evidence.encode(), request.scope, "text/plain")
        result = OperationResult(
            record_id="result/" + operation_id,
            revision=1,
            scope=request.scope,
            created_at=now(),
            operation_id=operation_id,
            logical_step_id=request.logical_step_id,
            state="failed",
            output_refs=[
                self.artifacts.put(
                    canonical(
                        {
                            "error": "Stopped after operator reconciliation",
                            "evidence": ref.model_dump(mode="json"),
                        }
                    ),
                    request.scope,
                )
            ],
            paired_call_id=None,
            binding_ref=None,
            binding_generation=0,
            actual_backend=None,
            usage=[],
            execution_termination="confirmed_stopped",
            effects="known",
            started_at=request.created_at,
            finished_at=now(),
            error=ErrorDetail(
                code="ReconciledStop",
                message="Operator confirmed termination; review retained work",
                retryable_after_reconciliation=False,
                retry_after_ms=None,
            ),
            continuation_ref=None,
        )
        self.records.compare_and_publish(
            {key: retained[0]},
            {
                key: {
                    **retained[1],
                    "state": "failed",
                    "result": result.model_dump(mode="json"),
                    "reconciliation": "operator_confirmed_stopped",
                    "evidence": ref.model_dump(mode="json"),
                }
            },
        )
        self._settle_budget(request)  # Unknown usage stays conservatively charged.
        self._effect_status(request, False)
        for admission in self.admission.values():
            admission.restore()
        if any(
            self.records.get("effect/" + op)[1]["request"]["scope"]["process_id"] == pid
            for op in self.uncertain()
        ):
            return
        for _, _, owner in self.records.scan("permit/"):
            if owner.get("process_id") == pid:
                await self.exclusive.release(owner["permit"], pid)
        for task_key, revision, task in self.records.scan("task/"):
            if task["process_id"] != pid or task.get("report_ref"):
                continue
            if self.records.get("workspace/" + task["workspace_id"]):
                await self.workspaces.abort(task["workspace_id"])
            self.records.compare_and_publish(
                {task_key: revision},
                {
                    task_key: {
                        **task,
                        "execution": "interrupted",
                        "exception": "Reconciled operation " + operation_id,
                    }
                },
            )
            attempt_key = "attempt/" + task["attempt_id"]
            attempt = self.records.get(attempt_key)
            if attempt:
                self._update(
                    attempt_key,
                    {
                        **attempt[1],
                        "revision": attempt[1]["revision"] + 1,
                        "execution": "interrupted",
                        "stop_reason": "operator reconciliation",
                    },
                )
        process = self.records.get("process/" + pid)
        if process:
            self._update("process/" + pid, {**process[1], "state": "paused"})
        status = self.records.get("process-status/" + pid)
        if status:
            self._update(
                "process-status/" + pid,
                {
                    **status[1],
                    "revision": status[1]["revision"] + 1,
                    "state": "paused",
                    "cleanup_state": "complete",
                    "permit_refs": [],
                    "pending_operations": [],
                    "wait": None,
                },
            )
        run = self.records.get("app/run")
        if run:
            self.records.compare_and_publish(
                {"app/run": run[0]},
                {
                    "app/run": {
                        **run[1],
                        "starts_closed": True,
                        "status": "active",
                        "completion_proposed": False,
                        "active_workers": [value for value in run[1]["active_workers"] if value != pid],
                        "captured_workers": [value for value in run[1]["captured_workers"] if value != pid],
                    }
                },
            )
