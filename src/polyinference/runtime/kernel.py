"""Small runtime: durable effects, static routing, direct capabilities and storage."""

from __future__ import annotations

import asyncio
import fcntl
import json
import math
from contextlib import AsyncExitStack
from datetime import datetime, timedelta

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ..contracts import (
    ActualBackend,
    AgentJob,
    ArtifactRef,
    CapabilityCall,
    ErrorDetail,
    ModelQuery,
    OperationRequest,
    OperationResult,
    Publication,
    Scope,
    UsageMeasure,
)
from ..primitives import canonical, digest, now, operation_fingerprint
from .capabilities import Capabilities
from .codex import CodexAppServer, CodexProxy
from .context import ContextService, InputOverflow
from .exclusive import Exclusive
from .inference import (
    Admission,
    EndpointError,
    HTTPInference,
    IncompleteGeneration,
    ModelResponseError,
    ProviderError,
    UnknownExecution,
    model_unavailable,
    terminal_call,
)
from .lifecycle import ProcessLifecycle
from .messages import Messages, UserNotification
from .model_fallback import ModelFallback
from .model_retries import ModelRetries
from .outputs import Outputs
from .process_policy import ProcessPolicy
from .processes import Processes
from .progress import ExecutionProgress
from .retry import InferenceRetries, ReservedInferenceCalls
from .storage import Artifacts, Records
from .tool_contracts import FILE_CAPABILITIES
from .tools import Tools
from .workspace import Workspaces


class UncertainEffect(RuntimeError):
    pass


class ProcessCancelled(RuntimeError):
    pass


class KernelRuntime(ExecutionProgress, ProcessLifecycle, InferenceRetries):
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
        self.process_policy = ProcessPolicy(config, self.records)
        self.processes = Processes(self.records, config.max_workers, self.process_policy)
        self.outputs = Outputs(config, self.records, self.artifacts)
        self.messages = Messages(self.records)
        self.clients = {}
        self.fallback_clients = {}
        self.admission = {}
        self.inflight = {}
        self.response_validators = {}
        self.response_schemas = {}
        self.response_repairs = {}
        self.model_fallback = ModelFallback(self)
        self.retry_events = {}
        self.progress_sources = {}
        self.model_retries = ModelRetries(self)
        self.agent_protocols = {}
        self.contexts = ContextService(self)
        self.capabilities = Capabilities(self.records)
        self.publication_policies = {}
        self.stack = AsyncExitStack()
        self.closing = False
        self.on_reconciled = None
        self.register_capability(
            "user.notify", self.messages.notify, input_type=UserNotification,
            effect_class="shared_write", workspace=False,
            description="Show a plain-text message to the user in the UI and terminal.",
        )
        for name, (input_type, effect_class) in FILE_CAPABILITIES.items():
            self.register_capability(name, self._file_capability, input_type=input_type,
                                     effect_class=effect_class, workspace=True)
        for name, workspace in (("workspace.commit", True), ("workspace.retain", True),
                                ("records.publish", False), ("outputs.deliver", False)):
            self.register_capability(name, self._system_capability, effect_class="shared_write",
                                     workspace=workspace)
        for check in config.checks:
            self.tools.register_check(check)

    def register_capability(self, name, handler, **options):
        return self.capabilities.register(name, handler, **options)

    def install_workspaces(self, provider):
        """Trusted application bootstrap may supply an optional file-resource provider."""
        self.workspaces.blocking.close()
        self.workspaces = provider
        self.tools.workspaces = provider

    def publish_records(self, arguments, process_id):
        """Publish an explicit application's batch through the normal OS guards."""
        return self._publish(arguments, process_id)

    def register_publication_policy(self, program_id, policy):
        self.records.put_once("runtime/publication-policy/" + program_id, {"required": True})
        self.publication_policies[program_id] = policy

    async def _file_capability(self, request, arguments):
        return await self.tools.call(request.payload, arguments)

    async def _system_capability(self, request, arguments):
        payload = request.payload
        if payload.capability_id in {"workspace.retain", "records.publish"}:
            if payload.capability_id == "workspace.retain":
                staged = self.records.get("staged/" + arguments["receipt_ref"])
                if not staged:
                    raise ValueError("Missing staged record batch")
                arguments = staged[1]
            self._publish(arguments, request.scope.process_id)
            return {"receipt_ref": arguments["receipt_ref"], "published": True}
        if payload.capability_id == "workspace.commit":
            manifest = self.workspaces.current(payload.workspace_id)
            owner = self.records.get("permit/verification/project")
            if not owner or owner[1].get("process_id") != request.scope.process_id:
                raise ValueError("Commit preparation requires verification ownership")
            actual = await self.workspaces.revision(payload.workspace_id)
            if payload.expected_code and actual != payload.expected_code:
                raise ValueError("Commit content precondition failed")
            code = await self.workspaces.commit(payload.workspace_id, manifest.captured_head, request.operation_id)
            return code.model_dump(mode="json")
        return await self.outputs.deliver(arguments["delivery_id"], arguments["files"])

    def register_agent_protocol(self, name, schema, *, workspace="snapshot", brokered=False, instructions=""):
        """The calling agent owns its output grammar and phase policy."""
        if workspace not in {"snapshot", "workspace", "none"}:
            raise ValueError("Unknown native workspace kind")
        definition = {"schema": schema, "workspace": workspace, "brokered": brokered,
                      "instructions": instructions}
        if name in self.agent_protocols and self.agent_protocols[name] != definition:
            raise ValueError("Native protocol already registered with another definition")
        self.records.put_once("runtime/agent-protocol/" + name, {"digest": digest(canonical(definition))})
        self.agent_protocols[name] = json.loads(canonical(definition))

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
                "attached-workspace",
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
                "inference-retry",
                "readonly-query",
                "process-recovery",
                "execution-progress",
                "output-delivery",
                "model-recovery",
                "model-retries",
                "model-fallback",
                "inference-policy",
                "generic-processes",
                "artifact-snapshots",
                "user-messages",
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
        kernel = self.records.get("runtime/kernel")
        if kernel and kernel[1].get("version") != "simple-os/4":
            raise RuntimeError("Runtime authority/residency changed: use original source or fresh state")
        self.records.put_once("runtime/kernel", {"version": "simple-os/4"})
        from ..contracts import ProcessSpec

        for _, _, process in self.records.scan("process/"):
            self.process_policy.register(ProcessSpec.model_validate(self.records.get(process["spec_ref"])[1]),
                                         self.config.role_bindings.get(process["role"]))
        for name in sorted(set(self.config.role_bindings.values())):
            endpoint = getattr(self.config, name)
            cls = (
                CodexAppServer
                if endpoint.protocol == "codex_app_server"
                else (CodexProxy if endpoint.protocol == "codex_proxy" else HTTPInference)
            )
            self.clients[name] = cls(endpoint)
            if endpoint.retry_model:
                alternative = endpoint.model_copy(update={"model": endpoint.retry_model.model,
                    "reasoning_effort": endpoint.retry_model.reasoning_effort, "retry_model": None})
                self.fallback_clients[name] = cls(alternative)
                self.fallback_clients[name].output_cap = self.config.max_model_response_bytes
                if isinstance(self.fallback_clients[name], HTTPInference):
                    self.fallback_clients[name].require_completion_metadata = self.config.inference_safety.require_completion_metadata
            if hasattr(self.clients[name], "output_cap"):
                self.clients[name].output_cap = self.config.max_model_response_bytes
            if isinstance(self.clients[name], HTTPInference):
                self.clients[name].require_completion_metadata = self.config.inference_safety.require_completion_metadata
            if isinstance(self.clients[name], CodexProxy):
                self.clients[name].http.output_cap = self.config.max_model_response_bytes
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
        for key, revision, body in self.records.scan("ownership-wait/"):
            if body["state"] == "waiting":
                self.records.compare_and_publish({key: revision}, {key: {**body, "state": "interrupted"}})
        return self

    async def reconcile_known(self):
        """Only host-verifiable receipts/commit records can settle automatically."""
        for key, rev, body in self.records.scan("effect/"):
            if body["state"] != "uncertain":
                continue
            from ..contracts import OperationRequest

            request = OperationRequest.model_validate(body["request"])
            payload = request.payload
            attempts = self.records.scan("inference-attempt/" + request.operation_id + "/")
            if attempts and all((value.get("result") and value["result"]["execution_termination"] == "confirmed_stopped" and value["result"]["effects"] != "unknown") or (value["state"] == "prepared" and value["request"]["operation_id"] != request.operation_id) for _, _, value in attempts):
                self.records.compare_and_publish({key: rev}, {key: {**body, "state": "prepared", "result": None}})
                continue
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
                elif payload.capability_id == "outputs.deliver":
                    receipt = self.records.get("output-delivery/" + arguments["delivery_id"])
                    if receipt:
                        output = receipt[1]
                elif payload.capability_id == "user.notify":
                    message_ref = "user-message/" + request.operation_id
                    if self.records.get(message_ref):
                        output = {"message_ref": message_ref}
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
        await self.model_retries.close()
        tasks = list(self.inflight.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for client in self.clients.values():
            await client.close()
        for client in self.fallback_clients.values():
            await client.close()
        self.workspaces.blocking.close()
        await self.stack.aclose()
        self.exclusive.close()
        self.records.db.close()
        self.driver.close()

    def uncertain(self, *, include_isolated=False):
        return [key[7:] for key, _, body in self.records.scan("effect/")
                if body["state"] == "uncertain" and (include_isolated or not body.get("isolated_generation"))]

    def _isolate_generation(self, request, exc, started, prepared):
        """Quarantine one undelivered raw generation, retaining all physical holds."""
        if not isinstance(request.payload, ModelQuery) or not self.model_retries.policy(request).replace_undelivered:
            return None
        name = self.config.role_bindings[request.payload.role]
        endpoint = getattr(self.config, name)
        # Trusted raw adapter only: never infer safety from a URL or binding name.
        if type(self.clients[name]) is not HTTPInference or not endpoint.lifecycle:
            return None
        wire = prepared.get("payload") if isinstance(prepared, dict) else None
        if not isinstance(wire, dict) or any(field in wire for field in (
                "tools", "functions", "tool_choice", "function_call")):
            return None
        if getattr(exc, "diagnostics", {}).get("cause") not in {
                "ReadTimeout", "ReadError", "RemoteProtocolError", "TimeoutError", "missing_terminal"}:
            return None
        pending = [body for _, _, body in self.records.scan("effect/")
                   if body.get("isolated_generation") and body["isolated_generation"]["binding"] == name
                   and body["state"] == "uncertain"]
        counts = self.model_retries.counts(request)
        if (pending or sum(counts.values()) >= self.config.model_call_retries + self.model_retries.policy(request).additional_retries
                or self.model_retries.deadline(request) <= now() or self.closing):
            return None
        marker = {"binding": name, "root_operation_id": self.model_retries.root(request),
                  "delivery": "discarded", "execution_termination": "unknown",
                  "execution_class": "generation_only", "basis": "builtin_raw_adapter_and_tool_free_wire"}
        result = OperationResult(record_id="result/" + request.operation_id, revision=1,
            scope=request.scope, created_at=now(), operation_id=request.operation_id,
            logical_step_id=request.logical_step_id, state="uncertain", output_refs=[],
            paired_call_id=None, binding_ref=name, binding_generation=1, actual_backend=None,
            usage=[], execution_termination="unknown", effects="none", started_at=started,
            finished_at=now(), error=ErrorDetail(code="UndeliveredGeneration", message=str(exc)[:4000],
                retryable_after_reconciliation=False, retry_after_ms=None), continuation_ref=None,
            extensions={"runtime/undelivered-generation": marker})
        return marker, result

    def _update(self, key, body):
        current = self.records.get(key)
        self.records.compare_and_publish({key: current[0] if current else 0}, {key: body})

    async def execute(self, request):
        result = await self._execute_once(request)
        handled, result = await self.model_fallback.recover(request, result)
        if handled:
            return result
        result = await self.model_retries.run(request, result)
        _, result = await self.model_fallback.recover(request, result, final=True)
        return result

    async def _execute_once(self, request):
        key = "effect/" + request.operation_id
        saved = self.records.get(key)
        expected_digest = operation_fingerprint(request)
        self.negotiate(request.required_features)
        if isinstance(request.payload, (ModelQuery, AgentJob)):
            self.model_retries.policy(request)
            if request.extensions.get("runtime/inference-root") and not (
                    request.extensions.get("runtime/model-retry") or request.extensions.get("runtime/output-retry")
                    or request.extensions.get("runtime/model-fallback")):
                raise ValueError("Inference retry root requires an OS-issued intent")
        if request.intent_digest != expected_digest:
            raise ValueError("Intent fingerprint mismatch")
        if request.scope.run_id != self.run_id or request.scope.project_id != self.scope.project_id:
            raise ValueError("Unauthenticated runtime scope")
        if saved:
            if saved[1]["fingerprint"] != expected_digest:
                raise ValueError("Operation ID reused with changed intent")
            if saved[1].get("delivery_result"):
                return OperationResult.model_validate(saved[1]["delivery_result"])
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
        if self.records.get("process-parked/" + request.scope.process_id):
            raise ValueError("Parked process cannot start new effects")
        if process[1]["state"] in {"completed", "cancelled", "failed", "paused"}:
            raise ValueError("Process is stopped; an explicit recovery or new process is required")
        control = self.records.get("process-control/" + request.scope.process_id)
        if control and control[1].get("cancel_requested"):
            raise ValueError("Process cancellation requested; no new operations may start")
        if request.owner_generation != process[1]["owner_generation"]:
            raise ValueError("Stale owner generation")
        if request.grant_ref != "grant/run" or request.budget_account_ref != "budget/run":
            raise ValueError("Unknown grant or budget account")
        if request.limits != self.config.limits:
            raise ValueError("Operation limits differ from the pinned or inherited process grant")
        self.process_policy.dispatch(request, process[1])
        started = process[1].get("started_at")
        if started:
            cutoff = datetime.fromisoformat(started.replace("Z", "+00:00")) + timedelta(milliseconds=request.limits.max_wall_time_ms)
            if now() >= cutoff or request.deadline > cutoff:
                raise ValueError("Operation exceeds the process wall-time allowance")
        recovery = request.extensions.get("polyinference/recovery-of")
        if request.extensions.get("runtime/model-fallback"):
            self.model_fallback.authorize(request)
        elif request.extensions.get("runtime/model-retry"):
            # The originating recovery was already authorized. Revalidate the
            # OS-issued retry intent without charging another caller recovery.
            self.model_retries.authorize(request)
        elif request.extensions.get("runtime/output-retry"):
            self.model_retries.authorize_output(request)
        elif recovery:
            self._authorize_recovery(request, recovery)
        for resource in request.conflict_keys:
            owner = self.records.get("permit/" + resource)
            if not owner or owner[1].get("process_id") != request.scope.process_id:
                raise ValueError("Protected operation requires current resource ownership: " + resource)
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
        if self.records.get("process-parked/" + request.scope.process_id):
            raise ValueError("Parked process cannot start new effects")
        cutoff = self.process_deadline(request.scope.process_id)
        if cutoff and (request.deadline > cutoff or now() >= cutoff):
            raise ValueError("Recovery exceeds original process deadline")
        account = self.records.get("process-account/" + request.scope.process_id)
        if account and (request.limits.model_dump(mode="json") != account[1]["limits"] or request.grant_ref != account[1]["grant_ref"]):
            raise ValueError("Recovery cannot enlarge inherited limits or grants")
        parent = self.records.get("effect/" + request.causal_parent_ref) if request.causal_parent_ref else None
        if parent is None and request.causal_parent_ref and request.extensions.get("runtime/context-compaction"):
            index = self.records.get("inference-attempt-index/" + request.causal_parent_ref)
            if index:
                parent = self.records.get(index[1]["record_ref"])
        if request.causal_parent_ref:
            if (
                not parent
                or parent[1]["state"] not in {"active", "prepared"}
                or parent[1]["request"]["scope"] != request.scope.model_dump(mode="json")
            ):
                raise ValueError("Subordinate effect requires its active parent and inherited scope")
            if request.extensions.get("runtime/context-compaction"):
                self.contexts.authorize_compaction(request, parent[1])
            else:
                if not isinstance(request.payload, CapabilityCall) or parent[1]["state"] != "active":
                    raise ValueError("Only broker callbacks or OS-issued compaction may be subordinate")
                self.capabilities.get(request.payload.capability_id)
                if request.payload.capability_id not in parent[1]["request"]["payload"].get("allowed_capabilities", []):
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
        body = {"fingerprint": expected_digest, "state": "prepared", "request": request.model_dump(mode="json"), "result": None}
        if saved:
            self._update(key, body)
        else:
            self.prepare_effect(request, key, body)
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
            ("budget/process/" + self.account(request.scope.process_id), request.limits.max_total_tokens),
        ]
        expected, updates = {}, {}
        for key, limit in keys:
            process = self.records.get("process/" + request.scope.process_id)[1]
            if key == "budget/run" and not process.get("management", False):
                limit -= self.config.control_token_reserve
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
            ("spend/process/" + self.account(request.scope.process_id), request.limits.max_api_spend_microusd),
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
        for pointer in ("budget/run", "budget/process/" + self.account(request.scope.process_id)):
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
            for pointer in ("spend/run", "spend/process/" + self.account(request.scope.process_id)):
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
                "state": status.state if status.state in {"completed", "cancelled", "failed", "paused"}
                else "waiting" if pending else "ready",
                "wait": wait,
                "pending_operations": pending,
            }
        )
        self.records.compare_and_publish({key: retained[0]}, {key: updated.model_dump(mode="json")})

    async def _dispatch_once(self, request, key):
        started = now()
        payload = request.payload
        usage, backend = [], None
        state, termination, effects, error = "succeeded", "confirmed_stopped", "known", None
        outputs = []
        saved = self.records.get(key)[1]
        dispatched = False
        extensions = {}
        try:
            model_deadline = (self.model_retries.deadline(request)
                              if isinstance(payload, (ModelQuery, AgentJob)) else request.deadline)
            if model_deadline <= now():
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
                endpoint, client, selection = self.model_fallback.select(request, key)
                if selection:
                    extensions["runtime/model-selection"] = selection
                attempted = {"binding_ref": name, "model": endpoint.model, "protocol": endpoint.protocol,
                             "submitted": False}
                extensions["polyinference/attempted-backend"] = attempted
                circuit = self.records.get(self._model_failure_key(request))
                if circuit and circuit[1]["count"] >= self.config.max_repeated_model_failures and not request.extensions.get("polyinference/recovery-of"):
                    raise EndpointError("Model dispatch stopped after repeated permanent failures; explicit recovery required")
                output_tokens = min(request.limits.max_output_tokens_per_call,
                    request.extensions.get("runtime/output-tokens", request.limits.max_output_tokens_per_call))
                if not isinstance(output_tokens, int) or isinstance(output_tokens, bool) or output_tokens < 1:
                    raise ValueError("Invalid output-token allowance")
                protocol = self.agent_protocols.get(payload.required_phase_protocol) if isinstance(payload, AgentJob) else None
                def measure(messages):
                    if isinstance(client, HTTPInference):
                        prepared = client.prepare(messages, output_tokens, temperature=getattr(payload, "temperature", None))
                    elif isinstance(client, CodexProxy):
                        prepared = client.http.prepare(messages, output_tokens, temperature=getattr(payload, "temperature", None))
                    elif isinstance(client, CodexAppServer):
                        if not protocol:
                            raise EndpointError("Unsupported native phase protocol")
                        prepared = client.prepare(messages, protocol["schema"],
                            tools=self.capabilities.descriptors(payload.allowed_capabilities) if protocol["brokered"] else [],
                            instructions=protocol["instructions"], max_output=output_tokens)
                    else:
                        prepared = messages
                    return prepared, len(canonical(prepared))
                if (self.config.inference_safety.require_output_token_enforcement
                        and endpoint.protocol in {"codex_app_server", "codex_proxy"}):
                    raise EndpointError("Selected native adapter cannot enforce a hard output-token limit")
                messages, prepared, receipt = await self.contexts.prepare(request, measure)
                if self.uncertain():
                    raise EndpointError("Context preparation left uncertain effects; reconcile before submission")
                extensions["runtime/context-receipt"] = receipt
                extensions["runtime/output-token-enforcement"] = endpoint.protocol in {"chat", "responses", "gemini", "anthropic"}
                input_bound = receipt["submitted_bytes"]
                reserved = input_bound + output_tokens
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
                finishing = bool(request.conflict_keys)
                async with self.admission[name].reserve(
                    reserved,
                    finishing,
                    request.operation_id,
                    max(0, (model_deadline - now()).total_seconds()),
                    process_id=request.scope.process_id,
                ):
                    if model_deadline <= now():
                        raise EndpointError("Deadline expired before provider submission")
                    counter = "budget/model-calls/" + self.account(request.scope.process_id)
                    count = self.inference_calls_used(request.scope.process_id)
                    if count >= request.limits.max_model_calls:
                        raise EndpointError("Model call allowance exhausted (including retries)")
                    reserve = request.extensions.get("polyinference/inference-call-reserve", 0)
                    if isinstance(reserve, bool) or not isinstance(reserve, int) or not 0 <= reserve <= request.limits.max_model_calls:
                        raise EndpointError("Invalid inference call reserve")
                    if count >= request.limits.max_model_calls - reserve:
                        raise ReservedInferenceCalls("Caller-reserved inference allowance reached")
                    self._update(counter, {"used": count + 1})
                    self._reserve_budget(request, reserved)
                    self._reserve_spend(request, reserved, endpoint)
                    self._update(key, {**saved, "state": "submitting"})
                    control = self.records.get("process-control/" + request.scope.process_id)
                    if control and control[1].get("cancel_requested"):
                        raise ProcessCancelled("Cancellation requested before model submission")
                    self._update(key, {**saved, "state": "active"})
                    timeout = min(endpoint.timeout_seconds, (model_deadline - now()).total_seconds())
                    if isinstance(payload, ModelQuery) and endpoint.lifecycle:
                        timeout = max(0, (model_deadline - now()).total_seconds())
                    if isinstance(payload, ModelQuery):
                        if endpoint.protocol not in {"chat", "responses", "gemini", "anthropic"}:
                            raise EndpointError("Native backend requires AgentJob")
                        if hasattr(client, "validate_messages"):
                            client.validate_messages(messages)
                        dispatched = True
                        attempted["submitted"] = True
                        if isinstance(client, HTTPInference) and hasattr(client, "generate_operation"):
                            # Trusted raw adapters may own service latency separately
                            # from network timeouts. All OS guards still surround the
                            # invocation, including the original deadline/reservation.
                            result = await terminal_call(
                                client.generate_operation(request, messages, output_tokens, prepared=prepared),
                                max(0, (model_deadline - now()).total_seconds()),
                            )
                        else:
                            async def remember_response(provider):
                                current = self.records.get(key)[1]
                                self._update(key, {**current, "provider": provider})

                            async def remember_progress(facts):
                                self._update("inference-progress/" + request.operation_id, {
                                    **facts, "at": now().isoformat(), "operation_id": request.operation_id,
                                    "deadline": model_deadline.isoformat(),
                                    "retry": request.extensions.get("runtime/model-retry"),
                                    "binding": name})

                            result = await asyncio.wait_for(
                                client.generate(messages, output_tokens,
                                    **({"prepared": prepared, "observer": remember_response, "progress": remember_progress}
                                       if type(client) is HTTPInference else
                                       {"prepared": prepared} if isinstance(client, HTTPInference) else {})),
                                timeout,
                            )
                        self.records.put_once("model-response/" + request.operation_id, {
                            "response_ref": self.artifacts.put(canonical(result), request.scope).model_dump(mode="json")})
                    else:
                        callback = None
                        protocol = self.agent_protocols.get(payload.required_phase_protocol)
                        if not protocol:
                            raise EndpointError("Unsupported native phase protocol")
                        process = self.records.get("process/" + request.scope.process_id)[1]
                        if not set(payload.allowed_capabilities) <= set(process.get("capabilities", [])):
                            raise ValueError("Native tool set exceeds the process grant")
                        schema = protocol["schema"]
                        if protocol["workspace"] == "none":
                            snapshot = self.config.state_path / "native" / digest(request.scope.process_id.encode())[7:]
                            await self.workspaces.blocking.run(lambda: snapshot.mkdir(parents=True, exist_ok=True))
                        elif protocol["workspace"] == "snapshot":
                            snapshot = self.workspaces.snapshot_root(payload.workspace_id)
                        else:
                            manifest = self.workspaces.current(payload.workspace_id)
                            if manifest.process_id != request.scope.process_id:
                                raise ValueError("Native workspace owner mismatch")
                            # Native tools see an immutable input copy, never the
                            # writable broker directory (which changes generations).
                            snapshot = await self.workspaces.native_view(payload.workspace_id, request.operation_id)
                        native_before = await self.workspaces.scan_exact_async(snapshot)
                        broker_views = {}

                        async def remember_broker_views():
                            if protocol["workspace"] == "workspace":
                                root = self.workspaces.root_for(self.workspaces.current(payload.workspace_id))
                                broker_views[root] = None
                                for root in broker_views:
                                    broker_views[root] = await self.workspaces.scan_async(root)

                        async def unbrokered_changes():
                            current = await self.workspaces.scan_exact_async(snapshot)
                            changes = [path for path in native_before.keys() | current.keys()
                                       if native_before.get(path) != current.get(path)]
                            for root, expected in broker_views.items():
                                current = await self.workspaces.scan_async(root)
                                changes.extend(path for path in expected.keys() | current.keys()
                                               if expected.get(path) != current.get(path))
                            return sorted(set(changes))

                        await remember_broker_views()
                        if protocol["brokered"]:
                            if not endpoint.brokered_tools:
                                raise EndpointError("Native backend lacks brokered tools")
                            tool_descriptors = self.capabilities.descriptors(payload.allowed_capabilities)
                            async def callback(call_id, arguments):
                                changes = await unbrokered_changes()
                                if changes:
                                    raise UnknownExecution("Native harness modified files outside the broker: "
                                                           + ", ".join(changes))
                                observation = await self._native_callback(request, call_id, arguments)
                                await remember_broker_views()
                                return observation
                        # Direct app-server has native shell disabled: only actual broker
                        # callbacks take shell. An opaque read-only proxy needs wider exclusion.
                        from .codex import NativeJobStopped

                        native_shell = None
                        if endpoint.protocol == "codex_proxy":
                            native_shell = await self.exclusive.acquire(
                                "shell/installation", request.scope.process_id
                            )
                        try:
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
                                if isinstance(client, CodexAppServer)
                                else {}
                            )
                            if isinstance(client, CodexAppServer):
                                options.update(
                                    tools=tool_descriptors if callback else [],
                                    instructions=protocol["instructions"],
                                    prepared=prepared, max_output=output_tokens,
                                    session_ref=(payload.session_ref
                                        if request.extensions.get("runtime/model-fallback") else None),
                                )
                            elif isinstance(client, CodexProxy):
                                options.update(max_output=output_tokens, prepared=prepared)
                            dispatched = True
                            attempted["submitted"] = True
                            if callback:
                                result = await asyncio.wait_for(
                                    client.generate_job(
                                        messages, snapshot, schema, callback, **options
                                    ),
                                    timeout,
                                )
                            else:
                                result = await asyncio.wait_for(
                                    client.generate_job(messages, snapshot, schema, **options),
                                    timeout,
                                )
                            paths = await unbrokered_changes()
                            if paths:
                                raise NativeJobStopped("Native harness modified files outside the broker: "
                                                       + ", ".join(paths))
                        except (NativeJobStopped, IncompleteGeneration, ProviderError, ModelResponseError) as exc:
                            paths = await unbrokered_changes()
                            if native_shell:
                                await self.exclusive.release(native_shell, request.scope.process_id)
                            if paths:
                                raise NativeJobStopped("Native harness modified files outside the broker: "
                                                       + ", ".join(paths), retryable=False) from exc
                            raise
                        except BaseException as exc:
                            failure = UnknownExecution(
                                "Native job did not establish a terminal result: "
                                + type(exc).__name__
                                + ": "
                                + str(exc)[:1500]
                            )
                            failure.native_diagnostics = getattr(exc, "native_diagnostics", None)
                            raise failure from exc
                        else:
                            if native_shell:
                                await self.exclusive.release(native_shell, request.scope.process_id)
                reported_usage = result.get("usage") or {}
                emitted = reported_usage.get("output_tokens", reported_usage.get("completion_tokens",
                    reported_usage.get("outputTokens")))
                if isinstance(emitted, int) and not isinstance(emitted, bool) and emitted > output_tokens:
                    raise IncompleteGeneration(result, "reported_output_limit_exceeded", output_tokens)
                if len(result["text"].encode()) > request.limits.max_output_bytes:
                    result = {**result, "text": result["text"].encode()[:request.limits.max_output_bytes].decode(errors="replace")}
                    raise IncompleteGeneration(result, "response_byte_limit", output_tokens)
                backend = ActualBackend(
                    catalog_ref="static/1",
                    backend_id=name,
                    model_version=result["model"],
                    harness_version=endpoint.protocol,
                    inference_location=endpoint.physical_location,
                    harness_location="local",
                    provider_session_ref=result.get("session_id"),
                )
                if circuit:
                    self._update(self._model_failure_key(request), {"count": 0})
                recovered = request.extensions.get("polyinference/recovery-of")
                if recovered:
                    previous = self.records.get("effect/" + recovered)
                    if previous:
                        failure_key = self._model_failure_key(OperationRequest.model_validate(previous[1]["request"]))
                        if self.records.get(failure_key):
                            self._update(failure_key, {"count": 0})
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
                capability, arguments = await self._authorize_capability(request)
                self._update(key, {**saved, "state": "submitting"})
                dispatched = True
                if payload.workspace_id:
                    manifest = self.workspaces.current(payload.workspace_id)
                    if manifest.process_id != request.scope.process_id:
                        raise ValueError("Workspace belongs to another process")
                try:
                    result = await capability.handler(request, arguments)
                    outputs = [self.artifacts.put(canonical(result), request.scope)]
                except Exception as exc:
                    if capability.effect_class == "external_write":
                        raise UnknownExecution("External capability did not establish its effects") from exc
                    raise
            elif isinstance(payload, Publication):
                process = self.records.get("process/" + request.scope.process_id)[1]
                if "records.publish" not in process.get("capabilities", []):
                    raise ValueError("Record publication exceeds the process grant")
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
            self._update(key, {**self.records.get(key)[1], "state": "uncertain", "diagnostic": str(exc),
                               "failure": {"category": "unknown_execution", "error_type": type(exc).__name__,
                                           **getattr(exc, "diagnostics", {})},
                               "native_diagnostics": getattr(exc, "native_diagnostics", None),
                               "attempted_backend": extensions.get("polyinference/attempted-backend")})
            isolated = self._isolate_generation(request, exc, started, prepared if isinstance(payload, ModelQuery) else None)
            if isolated:
                marker, result = isolated
                self._update(key, {**self.records.get(key)[1], "isolated_generation": marker,
                                   "delivery_result": result.model_dump(mode="json")})
                self._effect_status(request, False)
                return result
            raise UncertainEffect(request.operation_id) from exc
        except Exception as exc:
            if isinstance(payload, (ModelQuery, AgentJob)) and (getattr(exc, "model_unavailable", False) or
                    isinstance(exc, ProviderError) and model_unavailable(
                        exc.diagnostics.get("provider_message"), exc.diagnostics.get("provider_code"),
                        exc.diagnostics.get("http_status"))):
                extensions["polyinference/model-unavailable"] = {"model": endpoint.model}
                if getattr(exc, "native_continuation", None):
                    extensions["runtime/native-continuation"] = exc.native_continuation
            if isinstance(exc, InputOverflow):
                extensions["runtime/io-error"] = exc.diagnostics
            if isinstance(exc, ProviderError) and exc.diagnostics["category"] == "input_overflow":
                extensions["runtime/io-error"] = exc.diagnostics
            failed_response = exc.response if isinstance(exc, (IncompleteGeneration, ModelResponseError)) else None
            total = (failed_response.get("usage") or {}).get("total_tokens") if failed_response else None
            if not isinstance(total, int) or isinstance(total, bool) or total < 0:
                total = None
            submitted = dispatched and not (isinstance(exc, ProviderError) and not exc.diagnostics["submitted"])
            self._settle_budget(request, total if failed_response else (None if submitted else 0))
            if failed_response:
                extension = ("polyinference/incomplete-generation" if isinstance(exc, IncompleteGeneration)
                             else "polyinference/model-output-error")
                extensions[extension] = exc.diagnostics
                backend = ActualBackend(
                    catalog_ref="static/1", backend_id=name, model_version=failed_response["model"],
                    harness_version=endpoint.protocol, inference_location=endpoint.physical_location,
                    harness_location="local", provider_session_ref=None,
                )
                usage = [UsageMeasure(
                    metric="tokens", unit="tokens", value=total,
                    provenance="provider_reported" if total is not None else "unknown",
                    account_scope_ref=request.budget_account_ref,
                )]
            if getattr(exc, "native_diagnostics", None):
                extensions["polyinference/native-diagnostics"] = exc.native_diagnostics
            state, termination = "failed", "confirmed_stopped"
            if isinstance(exc, ProcessCancelled):
                state, termination = "cancelled", "not_started"
            error = ErrorDetail(
                code=type(exc).__name__,
                message=str(exc)[:4000],
                retryable_after_reconciliation=getattr(exc, "retryable", False),
                retry_after_ms=getattr(exc, "diagnostics", {}).get("retry_after_ms"),
            )
            if isinstance(exc, ProviderError):
                extensions["polyinference/provider-error"] = exc.diagnostics
                if not exc.diagnostics["submitted"] and "polyinference/attempted-backend" in extensions:
                    extensions["polyinference/attempted-backend"]["submitted"] = False
                if not exc.retryable:
                    failure_key = self._model_failure_key(request)
                    prior = self.records.get(failure_key)
                    self._update(failure_key, {"count": (prior[1]["count"] if prior else 0) + 1,
                                               "last_operation_id": request.operation_id,
                                               "diagnostic": exc.diagnostics})
            detail = getattr(exc, "detail", {})
            if detail:
                extensions["polyinference/workspace-error"] = detail
            diagnostic = {"error": str(exc)[:4000], **detail}
            if isinstance(exc, ProviderError):
                diagnostic["provider_detail"] = canonical(exc.diagnostics).decode()
            outputs = [self.artifacts.put(canonical(failed_response or diagnostic), request.scope)]
        result = OperationResult(
            extensions=extensions,
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

    def _model_failure_key(self, request):
        endpoint = getattr(self.config, self.config.role_bindings[request.payload.role])
        return "model-failures/" + digest(canonical({
            "role": request.payload.role, "model": endpoint.model, "protocol": endpoint.protocol,
            "endpoint": endpoint.base_url, "phase": getattr(request.payload, "phase", None),
            "protocol_id": getattr(request.payload, "required_phase_protocol", None),
            "configuration": self.records.get("runtime/config")[1]["digest"],
            "intent": request.intent_digest,
        }))

    def _authorize_recovery(self, request, failed_id):
        root = self.recovery_allowed(failed_id, request.scope, operation_id=request.operation_id)
        if not isinstance(request.payload, (ModelQuery, AgentJob)):
            raise ValueError("Recovery requires a model operation")
        if not request.extensions.get("polyinference/recovery-reason"):
            raise ValueError("Recovery needs an explicit reason")
        self.records.put_once("recovery/" + request.operation_id, {
            "previous_operation_id": failed_id, "reason": request.extensions["polyinference/recovery-reason"],
            "request_digest": request.intent_digest, "root_operation_id": root,
        })

    def recovery_allowed(self, failed_id, scope, *, operation_id=None):
        prior = self.records.get("effect/" + failed_id)
        if not prior:
            raise ValueError("Recovery requires a known failed model operation")
        original = prior[1]
        result = original.get("result") or {}
        if (original["state"] != "failed" or result.get("execution_termination") != "confirmed_stopped"
                or result.get("effects") != "known"
                or original["request"]["scope"] != scope.model_dump(mode="json")
                or original["request"]["payload"]["kind"] not in {"model_query", "agent_job"}):
            raise ValueError("Only a confirmed stopped model failure in the same process may be recovered")
        chain = failed_id
        while True:
            extensions = self.records.get("effect/" + chain)[1]["request"].get("extensions", {})
            older = (extensions.get("polyinference/recovery-of")
                     or extensions.get("runtime/model-retry", {}).get("previous_operation_id"))
            if not older:
                break
            chain = older
        count = sum(body.get("root_operation_id", body["previous_operation_id"]) == chain
                    for _, _, body in self.records.scan("recovery/"))
        existing = self.records.get("recovery/" + operation_id) if operation_id else None
        if not existing and count >= self.config.max_model_recoveries:
            raise ValueError("Model recovery allowance exhausted")
        return chain

    async def recover_model(self, failed_id, request, reason):
        """An explicit new intent; immutable replay of the original still wins."""
        if not reason.strip():
            raise ValueError("Recovery needs a reason")
        if request.operation_id == failed_id:
            raise ValueError("Recovery needs a new operation identity")
        if self.uncertain():
            raise ValueError("Reconcile unknown effects before recovery")
        request = request.model_copy(update={"extensions": {
            **request.extensions, "polyinference/recovery-of": failed_id,
            "polyinference/recovery-reason": reason[:4000],
        }})
        request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
        self._authorize_recovery(request, failed_id)
        process_key = "process/" + request.scope.process_id
        process = self.records.get(process_key)
        if process and process[1]["state"] == "paused":
            self._update(process_key, {**process[1], "state": "ready"})
            status_key = "process-status/" + request.scope.process_id
            status = self.records.get(status_key)
            if status:
                self._update(status_key, {**status[1], "state": "ready", "revision": status[1]["revision"] + 1,
                                          "wait": None, "pending_operations": []})
        return await self.execute(request)

    async def _authorize_capability(self, request):
        payload = request.payload
        capability = self.capabilities.get(payload.capability_id)
        process = self.records.get("process/" + request.scope.process_id)[1]
        if payload.capability_id not in process.get("capabilities", []):
            raise ValueError("Capability exceeds the process grant")
        if payload.effect_class != capability.effect_class:
            raise ValueError("Capability effect class differs from its registered ABI")
        if payload.schema_digest != capability.schema_digest:
            raise ValueError("Capability argument schema differs from its registered ABI")
        arguments = json.loads(self.artifacts.read(payload.arguments))
        if capability.workspace:
            if not payload.workspace_id:
                raise ValueError("Capability requires a workspace")
            manifest = self.workspaces.current(payload.workspace_id)
            grant = self.workspaces.grant(payload.workspace_id)
            blocked = self.records.get("workspace-blocked/" + payload.workspace_id)
            if blocked and capability.effect_class != "read":
                failure = ValueError("Attached workspace blocked after scope violation: " + blocked[1]["reason"])
                failure.detail = {"workspace_id": payload.workspace_id, "paths": blocked[1]["paths"],
                                  "allowed_write_paths": manifest.allowed_write_paths}
                raise failure
            if manifest.process_id != request.scope.process_id or grant.process_id != request.scope.process_id:
                raise ValueError("Workspace belongs to another process")
            if payload.capability_id not in grant.capabilities:
                raise ValueError("Capability exceeds the workspace grant")
            generation = arguments.get("generation")
            if generation != manifest.generation:
                raise ValueError("Stale workspace generation")
            if payload.expected_code:
                current = await self.workspaces.revision(payload.workspace_id)
                if current.effective_tree_digest != payload.expected_code.effective_tree_digest:
                    raise ValueError("Stale workspace content")
            arguments = capability.arguments({k: v for k, v in arguments.items() if k != "generation"})
            arguments["generation"] = generation
        else:
            arguments = capability.arguments(arguments)
        return capability, arguments

    async def _native_callback(self, parent, call_id, arguments):
        if (
            not isinstance(arguments, dict)
            or arguments.get("tool") not in parent.payload.allowed_capabilities
        ):
            raise ValueError("Native tool outside grant")
        callback_root = self.model_fallback.callback_root(parent)
        existing_count = sum(
            1
            for _, _, value in self.records.scan("effect/")
            if value["request"].get("causal_parent_ref") in {parent.operation_id, callback_root}
        )
        capability = self.capabilities.get(arguments["tool"])
        manifest = self.workspaces.current(parent.payload.workspace_id) if capability.workspace else None
        args = arguments.get("arguments", {})
        if manifest:
            args = {**args, "generation": manifest.generation}
        payload = CapabilityCall(
            capability_id=arguments["tool"],
            schema_digest=capability.schema_digest,
            arguments=self.artifacts.put(canonical(args), parent.scope),
            model_call_id=call_id,
            workspace_id=manifest.workspace_id if manifest else None,
            expected_code=await self.workspaces.revision(manifest.workspace_id) if manifest else None,
            effect_class=capability.effect_class,
            reconciliation_strategy_ref="journal/1",
        )
        operation_id = digest(canonical([callback_root, call_id]))
        retained = self.records.get("effect/" + operation_id)
        if retained:
            child = __import__(
                "polyinference.contracts", fromlist=["OperationRequest"]
            ).OperationRequest.model_validate(retained[1]["request"])
            original = json.loads(self.artifacts.read(child.payload.arguments))
            if child.payload.capability_id != arguments["tool"] or {
                k: v for k, v in original.items() if not capability.workspace or k != "generation"
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
        } if manifest else None
        if not retained:
            child = child.model_copy(update={"extensions": {"polyinference/workspace-view": view} if view else {}})
            child = child.model_copy(update={"intent_digest": operation_fingerprint(child)})
        result = await self.execute(child)
        observation = json.loads(self.artifacts.read(result.output_refs[0]))
        presented = {"state": result.state, "observation": observation}
        ref = observation.get("output") if isinstance(observation, dict) else None
        if isinstance(ref, dict) and ref.get("media_type") == "text/plain":
            raw = self.artifacts.read(ArtifactRef.model_validate(ref))
            cap = min(3000, parent.limits.max_output_bytes)
            excerpt = raw if len(raw) <= cap else raw[:cap // 2] + b"\n[...truncated...]\n" + raw[-cap // 2:]
            presented["diagnostics"] = {"output_ref": ref, "text": excerpt.decode(errors="replace"), "truncated": len(raw) > cap}
        return presented

    def _publish(self, arguments, process_id):
        receipt = self.records.get(arguments["receipt_ref"])
        if receipt:
            return  # Prior atomic publication wins replay, regardless of retired permits.
        if not any(owner.get("permit") == arguments["permit_ref"] and owner.get("process_id") == process_id
                   for _, _, owner in self.records.scan("permit/")):
            raise ValueError("Publication requires a currently owned resource permit")
        process = self.records.get("process/" + process_id)[1]
        spec = self.records.get(process["spec_ref"])[1]
        program_id = spec["program"]["program_id"]
        policy = self.publication_policies.get(program_id)
        if self.records.get("runtime/publication-policy/" + program_id) and policy is None:
            raise ValueError("Reinstall the program's publication policy before new publication: " + program_id)
        if policy:
            arguments = policy(arguments, process_id)
        expected, updates = arguments["expected"], arguments["updates"]
        self.records.compare_and_publish(expected, updates, arguments["immutable"])

    def diagnostics(self):
        return {
            "kernel": "simple-os/2",
            "admission": {name: value.snapshot() for name, value in self.admission.items()},
            "processes": [value for _, _, value in self.records.scan("process-status/")],
            "uncertain_operations": self.uncertain(),
            "owners": [value for _, _, value in self.records.scan("permit/") if value.get("process_id")],
            "budgets": {key: value for key, _, value in self.records.scan("budget/")},
            "spend": {key: value for key, _, value in self.records.scan("spend/")},
        }

    async def prepare_resume(self, request_ref):
        from .resume import prepare

        await prepare(self, request_ref)

    async def settle_recovered_model(self, request, response, *, failure=None):
        """Settle a retained completed raw response; never execute its text here."""
        if not isinstance(request.payload, ModelQuery) or not isinstance(response.get("text"), str):
            raise ValueError("Recovery requires a completed query-only response")
        key = "effect/" + request.operation_id
        old = self.records.get(key)
        if old[1]["state"] != "uncertain":
            return
        if any(row["request"]["operation_id"] != request.operation_id for _, _, row in self._unsettled_response_attempts(request.operation_id)):
            raise ValueError("Unsettled response-repair attempts require explicit reconciliation")
        name = self.config.role_bindings[request.payload.role]
        endpoint = getattr(self.config, name)
        total = (response.get("usage") or {}).get("total_tokens")
        total = total if type(total) is int and total >= 0 else None
        result = OperationResult(
            record_id="result/" + request.operation_id, revision=1, scope=request.scope,
            created_at=now(), operation_id=request.operation_id, logical_step_id=request.logical_step_id,
            state="failed" if failure else "succeeded", output_refs=[self.artifacts.put(canonical(response), request.scope)],
            paired_call_id=None, binding_ref=None, binding_generation=0,
            actual_backend=ActualBackend(
                catalog_ref="static/1", backend_id=name, model_version=response["model"],
                harness_version=endpoint.protocol, inference_location=endpoint.physical_location,
                harness_location="local", provider_session_ref=response.get("session_id")),
            usage=[UsageMeasure(metric="tokens", unit="tokens", value=total,
                                provenance="provider_reported" if total is not None else "unknown",
                                account_scope_ref=request.budget_account_ref)],
            execution_termination="confirmed_stopped", effects="known",
            started_at=request.created_at, finished_at=now(),
            error=ErrorDetail(code=type(failure).__name__, message=str(failure)[:4000],
                              retryable_after_reconciliation=False, retry_after_ms=None) if failure else None,
            continuation_ref=None,
        )
        self.records.compare_and_publish({key: old[0]}, {key: {
            **old[1], "state": result.state, "result": result.model_dump(mode="json"),
            "reconciliation": "retained_completed_response",
        }})
        index = self.records.get("inference-attempt-index/" + request.operation_id)
        if index:
            attempt_key = index[1]["record_ref"]
            revision, attempt = self.records.get(attempt_key)
            self.records.compare_and_publish({attempt_key: revision}, {attempt_key: {
                **attempt, "state": result.state, "result": result.model_dump(mode="json"),
                "reconciliation": "retained_completed_response"}})
        total = (response.get("usage") or {}).get("total_tokens")
        self._settle_budget(request, total if type(total) is int and total >= 0 else None)
        self._effect_status(request, False)
        for admission in self.admission.values():
            admission.restore()
        return result

    async def reconcile_stopped(self, operation_id, evidence):
        """Operator attestation, never an inference from connection loss or timeout.

        Caller must establish provider AND host effects have stopped. A reconciled
        effect is failed. Any later recovery is a separate, explicitly linked intent.
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
        for attempt_key, revision, row in self._unsettled_response_attempts(operation_id):
            attempted = OperationRequest.model_validate(row["request"])
            stopped = result.model_copy(update={"record_id": "result/" + attempted.operation_id,
                "operation_id": attempted.operation_id, "logical_step_id": attempted.logical_step_id,
                "started_at": attempted.created_at})
            self.records.compare_and_publish({attempt_key: revision}, {attempt_key: {
                **row, "state": "failed", "result": stopped.model_dump(mode="json"),
                "reconciliation": "operator_confirmed_stopped", "evidence": ref.model_dump(mode="json")}})
            self._settle_budget(attempted)
            self._effect_status(attempted, False)
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
        if self.on_reconciled:
            await self.on_reconciled(request, result)
