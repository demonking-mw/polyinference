"""Small runtime: durable effects, static routing, direct capabilities and storage."""

from __future__ import annotations

import asyncio
import fcntl
import json
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
from .storage import Artifacts, Records
from .tools import Tools
from .workspace import Workspaces


class UncertainEffect(RuntimeError):
    pass


class StandaloneRuntime:
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
        self.exclusive = Exclusive(self.records)
        self.workspaces = Workspaces(config, self.records, self.exclusive, self.artifacts, self.scope)
        self.tools = Tools(config, self.workspaces, self.exclusive, self.artifacts, self.scope)
        self.operations = self
        self.clients = {}
        self.admission = {}
        self.inflight = {}
        self.stack = AsyncExitStack()

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
        for name in sorted(set(self.config.role_bindings.values())):
            endpoint = getattr(self.config, name)
            cls = (
                CodexAppServer
                if endpoint.protocol == "codex_app_server"
                else (CodexProxy if endpoint.protocol == "codex_proxy" else HTTPInference)
            )
            self.clients[name] = cls(endpoint)
            self.admission[name] = Admission(endpoint.max_inflight, endpoint.reserved_context_tokens)
        # Recovery does not infer that a lost process/HTTP connection means stopped.
        for key, rev, body in self.records.scan("effect/"):
            if body["state"] in {"submitting", "active"}:
                self.records.compare_and_publish({key: rev}, {key: {**body, "state": "uncertain"}})
        await self.reconcile_known()
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
                if payload.capability_id == "records.publish" and self.records.get(arguments["receipt_ref"]):
                    output = {"published": True, "receipt_ref": arguments["receipt_ref"]}
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
        for client in self.clients.values():
            await client.close()
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
        if self.uncertain():
            raise UncertainEffect("Reconcile uncertain effects before dispatch")
        process = self.records.get("process/" + request.scope.process_id)
        if not process:
            raise ValueError("Unknown process principal")
        if request.owner_generation != process[1]["owner_generation"]:
            raise ValueError("Stale owner generation")
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
                and body["state"] in {"active", "submitting"}
            ):
                raise ValueError("Only one top-level active effect per process")
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
        keys = [
            ("budget/run", self.config.run_token_budget),
            ("budget/process/" + request.scope.process_id, request.limits.max_total_tokens),
        ]
        expected, updates = {}, {}
        for key, limit in keys:
            saved = self.records.get(key)
            used = saved[1]["reserved_or_used"] if saved else 0
            if used + amount > limit:
                raise EndpointError("Aggregate token budget exhausted: " + key)
            expected[key] = saved[0] if saved else 0
            updates[key] = {"reserved_or_used": used + amount}
        self.records.compare_and_publish(expected, updates)
        # Keep conservative reservations when reliable provider accounting is absent.

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
            self._update(key, {**saved, "state": "submitting"})
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
                self._reserve_budget(request, reserved)
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
                async with self.admission[name].reserve(reserved, finishing):
                    self._update(key, {**saved, "state": "active"})
                    timeout = min(endpoint.timeout_seconds, (request.deadline - now()).total_seconds())
                    if isinstance(payload, ModelQuery):
                        if endpoint.protocol not in {"chat", "responses", "gemini", "anthropic"}:
                            raise EndpointError("Native backend requires AgentJob")
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
                        # Native built-in command visibility cannot supply per-command brokerage.
                        # Conservatively exclude other managed shell activity for the bounded job.
                        from .codex import NativeJobStopped

                        native_shell = await self.exclusive.acquire(
                            "shell/installation", request.scope.process_id
                        )
                        try:
                            if callback:
                                result = await asyncio.wait_for(
                                    self.clients[name].generate_job(messages, snapshot, schema, callback),
                                    timeout,
                                )
                            else:
                                result = await asyncio.wait_for(
                                    self.clients[name].generate_job(messages, snapshot, schema), timeout
                                )
                        except NativeJobStopped:
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
                # Native harnesses may make multiple internal model calls. Never
                # leave a known total below the initial application reservation.
                if total is not None and total > reserved:
                    extra = total - reserved
                    pointers = ["budget/run", "budget/process/" + request.scope.process_id]
                    rows = {key: self.records.get(key) for key in pointers}
                    self.records.compare_and_publish(
                        {key: row[0] for key, row in rows.items()},
                        {
                            key: {"reserved_or_used": row[1]["reserved_or_used"] + extra}
                            for key, row in rows.items()
                        },
                    )
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
                if payload.workspace_id:
                    manifest = self.workspaces.current(payload.workspace_id)
                    if manifest.process_id != request.scope.process_id:
                        raise ValueError("Workspace belongs to another process")
                arguments = json.loads(self.artifacts.read(payload.arguments))
                if payload.capability_id == "records.publish":
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
                staged = self.records.get("staged/" + payload.receipt_ref)
                if not staged:
                    raise ValueError("Missing immutable publication batch")
                self._publish(staged[1], request.scope.process_id)
                outputs = [self.artifacts.put(canonical({"receipt_ref": payload.receipt_ref}), request.scope)]
            else:
                raise ValueError("Unsupported payload")
        except (UnknownExecution, asyncio.TimeoutError, asyncio.CancelledError) as exc:
            self._update(key, {**saved, "state": "uncertain", "diagnostic": str(exc)})
            raise UncertainEffect(request.operation_id) from exc
        except Exception as exc:
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
        self._update(key, {**saved, "state": state, "result": result.model_dump(mode="json")})
        self._effect_status(request, False)
        return result

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
        if existing_count >= parent.limits.max_steps:
            raise ValueError("Native callback allowance exhausted")
        manifest = self.workspaces.current(parent.payload.workspace_id)
        args = {**arguments.get("arguments", {}), "generation": manifest.generation}
        payload = CapabilityCall(
            capability_id=arguments["tool"],
            schema_digest=digest(arguments["tool"].encode()),
            arguments=self.artifacts.put(canonical(args), parent.scope),
            model_call_id=call_id,
            workspace_id=manifest.workspace_id,
            expected_code=await self.workspaces.revision(manifest.workspace_id),
            effect_class="read" if arguments["tool"] in {"files.read", "files.list"} else "private_write",
            reconciliation_strategy_ref="journal/1",
        )
        operation_id = digest(canonical([parent.operation_id, call_id]))
        retained = self.records.get("effect/" + operation_id)
        if retained:
            child = __import__(
                "polyinference.contracts", fromlist=["OperationRequest"]
            ).OperationRequest.model_validate(retained[1]["request"])
        else:
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
        self.records.compare_and_publish(arguments["expected"], arguments["updates"], arguments["immutable"])
