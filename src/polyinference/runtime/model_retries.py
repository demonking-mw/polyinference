"""Bounded OS retries of settled inference failures, independent of agent policy."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from ..contracts import AgentJob, ContextPart, Feature, InferencePolicy, ModelQuery, OperationRequest
from ..primitives import canonical, digest, now, operation_fingerprint
from .context import context_with_parts


class ModelRetries:
    def __init__(self, runtime):
        self.runtime = runtime
        self.tasks = {}

    def policy(self, request):
        value = request.extensions.get("runtime/inference-policy")
        if value is not None and not any(f.feature_id == "runtime/inference-policy" and f.version == "1"
                                         for f in request.required_features):
            raise ValueError("Inference policy requires runtime/inference-policy version 1")
        return InferencePolicy.model_validate(value if value is not None else {})

    def root(self, request):
        return request.extensions.get("runtime/inference-root", request.operation_id)

    def deadline(self, request):
        root = self.runtime.records.get("effect/" + self.root(request))
        original = OperationRequest.model_validate(root[1]["request"]) if root else request
        endpoint = getattr(self.runtime.config, self.runtime.config.role_bindings[request.payload.role])
        if not endpoint.lifecycle:
            return original.deadline
        return min(original.deadline, original.created_at + timedelta(seconds=endpoint.lifecycle.total_seconds))

    def counts(self, request):
        root = self.root(request)
        counts = {"native": 0, "caller": 0}
        for _, _, body in self.runtime.records.scan("model-retry/"):
            retry = body["request"]["extensions"]["runtime/model-retry"]
            if retry.get("budget_root_operation_id", retry["root_operation_id"]) == root:
                counts[retry.get("source", "native")] += 1
        return counts

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run(self, request, result):
        if (result.state == "succeeded" or not isinstance(request.payload, (ModelQuery, AgentJob))
                or request.extensions.get("runtime/model-retry")):
            return result
        key = request.operation_id
        if key not in self.tasks:
            self.tasks[key] = asyncio.create_task(self._resolve(request, result))
        task = self.tasks[key]
        try:
            return await asyncio.shield(task)
        finally:
            if task.done():
                self.tasks.pop(key, None)

    def authorize(self, request):
        retry = request.extensions["runtime/model-retry"]
        key = f"model-retry/{retry['root_operation_id']}/{retry['attempt']}"
        retained = self.runtime.records.get(key)
        if not retained or canonical(retained[1]["request"]) != canonical(request):
            raise ValueError("Model retry requires its durable OS-issued intent")

    def authorize_output(self, request):
        issued = self.runtime.records.get("output-retry/" + request.operation_id)
        if not issued or canonical(issued[1]) != canonical(request):
            raise ValueError("Output recovery requires its durable OS-issued intent")

    async def _resolve(self, original, result):
        rt = self.runtime
        outcome = rt.records.get("output-retry-outcome/" + original.operation_id)
        if outcome:
            retained = rt.records.get("effect/" + outcome[1]["operation_id"])
            if retained and (retained[1].get("delivery_result") or retained[1].get("result")):
                from ..contracts import OperationResult
                effective = OperationResult.model_validate(retained[1].get("delivery_result") or retained[1]["result"])
                if effective.state != "uncertain":
                    return effective
        if original.extensions.get("runtime/context-compaction"):
            return result
        result = await self._run(original, result)
        for index in range(min(rt.config.inference_safety.output_recoveries, rt.config.max_model_recoveries)):
            if not result.extensions.get("polyinference/incomplete-generation"):
                break
            # Reuse every generic safety/reserve guard, except the classification
            # that deliberately separates adaptation from unchanged transport retry.
            eligible = result.model_copy(update={"extensions": {
                k: v for k, v in result.extensions.items() if k != "polyinference/incomplete-generation"}})
            if self._blocked(original, eligible):
                break
            target = max(1, min(rt.config.inference_safety.smaller_response_bytes,
                                original.limits.max_output_bytes) // (2 ** index))
            text = ("The previous response hit an output limit and was discarded; none of its returned actions executed. "
                f"Recovery attempt {index + 1}: aim below {target} UTF-8 bytes of visible response content. "
                "Return a substantially smaller complete response under the same declared protocol. "
                "Preserve the objective, constraints and phase. Do not concatenate or repeat the partial response. "
                "Previously completed tool effects remain recorded and must not be repeated.")
            part = ContextPart(part_id="output-limit-feedback",
                content=rt.artifacts.put(text.encode(), original.scope, "text/plain"),
                part_kind="data", trust="application", source_ref="runtime/output-recovery", required=True)
            context = context_with_parts(original.payload.context,
                [p for p in original.payload.context.parts if p.part_id != part.part_id] + [part])
            step = "output-retry-" + digest(canonical([original.operation_id, index]))[7:]
            operation_id = digest(step.encode())
            key = "output-retry/" + operation_id
            saved = rt.records.get(key)
            if saved:
                request = OperationRequest.model_validate(saved[1])
            else:
                request = original.model_copy(update={"record_id": "request/" + step,
                    "created_at": now(), "logical_step_id": step, "operation_id": operation_id,
                    "payload": original.payload.model_copy(update={"context": context}),
                    "extensions": {**original.extensions, "runtime/inference-root": self.root(original), "runtime/output-retry": {
                        "root_operation_id": original.operation_id,
                        "previous_operation_id": result.operation_id, "attempt": index + 1}}})
                request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
                rt.records.put_once(key, request.model_dump(mode="json"))
            result = await rt._execute_once(request)
            result = await self._run(request, result)
            if result.state == "succeeded":
                break
        rt._update("output-retry-outcome/" + original.operation_id, {"operation_id": result.operation_id})
        return result

    async def wait_until(self, not_before):
        delay = (datetime.fromisoformat(not_before) - now()).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)

    def complete(self, original, result, reason):
        key = "model-retry-outcome/" + original.operation_id
        body = {"root_operation_id": original.operation_id, "result_operation_id": result.operation_id,
                "state": result.state, "reason": reason, "retry_counts": self.counts(original),
                "deadline": self.deadline(original).isoformat()}
        retained = self.runtime.records.get(key)
        if not retained or retained[1] != body:
            self.runtime._update(key, body)
        return result

    def _blocked(self, request, result):
        rt = self.runtime
        replaceable = result.extensions.get("runtime/undelivered-generation") and self.policy(request).replace_undelivered
        if not replaceable and (result.state != "failed" or result.effects != "known"
                or result.execution_termination != "confirmed_stopped"
                or not result.error or not result.error.retryable_after_reconciliation):
            return "failure is not safely retryable"
        if replaceable:
            name = result.extensions["runtime/undelivered-generation"]["binding"]
            if rt.admission[name].active >= getattr(rt.config, name).max_inflight:
                return "pending generation occupies endpoint capacity"
        # Adaptation is a distinct OS-issued intent, not an unchanged transport retry.
        if result.extensions.get("polyinference/incomplete-generation"):
            return "output limit requires response adaptation"
        if self.deadline(request) <= now():
            return "logical request deadline expired"
        if rt.closing or rt.uncertain():
            return "runtime closing or effects uncertain"
        control = rt.records.get("process-control/" + request.scope.process_id)
        process = rt.records.get("process/" + request.scope.process_id)[1]
        if control and control[1].get("cancel_requested"):
            return "process cancellation requested"
        if process["state"] in {"paused", "cancelled", "failed", "completed"}:
            return "process stopped"
        if isinstance(request.payload, AgentJob) and any(
            body["request"].get("causal_parent_ref") == result.operation_id
            and body["request"]["payload"]["kind"] == "capability_call"
            for _, _, body in rt.records.scan("effect/")
        ):
            return "native job has brokered effects; caller continuation required"
        operations = [body for _, _, body in rt.records.scan("effect/")
                      if body["request"]["scope"]["process_id"] == request.scope.process_id]
        reserve = request.limits.final_phase_reserve
        finishing = bool(process.get("management") or request.conflict_keys)
        reserved_steps = reserve.publication_steps + reserve.cleanup_steps if reserve and not finishing else 0
        if len(operations) >= request.limits.max_steps - reserved_steps:
            return "operation allowance exhausted"
        calls = sum(body["request"]["payload"]["kind"] in {"model_query", "agent_job"} for body in operations)
        reserved = (reserve.reconciliation_model_calls + reserve.assessment_model_calls
                    if reserve and not finishing else 0)
        if calls >= request.limits.max_model_calls - reserved:
            return "model-call allowance or finishing reserve reached"
        return None

    async def _run(self, original, result):
        rt = self.runtime
        policy = self.policy(original)
        allowance = rt.config.model_call_retries + policy.additional_retries
        for attempt in range(1, allowance + 1):
            key = f"model-retry/{original.operation_id}/{attempt}"
            retained = rt.records.get(key)
            if retained:
                # Settled replay wins even after the process has stopped. An
                # unfinished retry still passes every normal dispatch guard.
                body = retained[1]
            else:
                counts = self.counts(original)
                used = sum(counts.values())
                if used >= allowance:
                    return self.complete(original, result, "shared retry allowance exhausted")
                blocked = self._blocked(original, result)
                if blocked:
                    return self.complete(original, result, blocked)
                delay = max(rt.config.model_retry_delay_ms * 2 ** (attempt - 1),
                            result.error.retry_after_ms or 0)
                not_before = now() + timedelta(milliseconds=delay)
                if delay > rt.config.model_retry_max_delay_ms or not_before >= self.deadline(original):
                    return self.complete(original, result, "retry-after or backoff exceeds wait/deadline allowance")
                step = "model-retry-" + digest(canonical([original.operation_id, attempt]))[7:]
                request_key = "request/" + step
                request = original.model_copy(update={
                    "record_id": request_key, "created_at": now(), "logical_step_id": step,
                    "operation_id": digest(canonical(["model-retry", original.operation_id, attempt])),
                    "required_features": [*original.required_features,
                                          Feature(feature_id="runtime/model-retries", version="1")],
                    "extensions": {**original.extensions, "runtime/inference-root": self.root(original), "runtime/model-retry": {
                        "root_operation_id": original.operation_id,
                        "previous_operation_id": result.operation_id, "attempt": attempt,
                        "budget_root_operation_id": self.root(original),
                        "source": "native" if counts["native"] < rt.config.model_call_retries else "caller",
                    }},
                })
                request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
                body = {"request": request.model_dump(mode="json"), "not_before": not_before.isoformat(),
                        "previous_operation_id": result.operation_id}
                rt.records.compare_and_publish({}, {}, {key: body, request_key: body["request"]})
            request = OperationRequest.model_validate(body["request"])
            saved = rt.records.get("effect/" + request.operation_id)
            if not saved or not saved[1].get("result"):
                blocked = self._blocked(original, result)
                if blocked:
                    return self.complete(original, result, blocked)
                await self.wait_until(body["not_before"])
                # Cancellation, shutdown and allowance changes during backoff
                # must be observed before creating another submitted attempt.
                blocked = self._blocked(original, result)
                if blocked:
                    return self.complete(original, result, blocked)
            result = await rt._execute_once(request)
            if result.state == "succeeded":
                return self.complete(original, result, "recovered")
        return self.complete(original, result, "retry allowance exhausted")
