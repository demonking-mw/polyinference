"""Generic bounded inference retry. Semantic validators are supplied by callers.

Attempts have durable identities distinct from replay of the logical operation.
Effectful jobs/tools and uncertain execution never get blind re-execution.
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import datetime, timedelta

from ..contracts import AgentJob, ErrorDetail, ModelQuery, OperationRequest, OperationResult, UsageMeasure
from ..primitives import canonical, digest, now, operation_fingerprint
from .inference import EndpointError


class ReservedInferenceCalls(EndpointError):
    """The caller reserved its remaining call capacity for later work."""


class InferenceRetries:
    def _unsettled_response_attempts(self, operation_id):
        pending = []
        for key, revision, row in self.records.scan("inference-attempt/" + operation_id + "/"):
            result = row.get("result")
            if (result and (result["execution_termination"] == "unknown" or result["effects"] == "unknown")) or (not result and (row["state"] != "prepared" or row["request"]["operation_id"] == operation_id)):
                pending.append((key, revision, row))
        return pending

    def inference_calls_used(self, process_id):
        row = self.records.get("budget/model-calls/" + self.account(process_id))
        return row[1]["used"] if row else 0

    def register_response_validator(self, schema_ref, validator):
        self.response_validators[schema_ref] = validator

    def register_response_repair(self, schema_ref, repair):
        """Optional synchronous owner callback; no model dispatch or retry allowance is added."""
        if repair is None:
            self.response_repairs.pop(schema_ref, None)
        else:
            self.response_repairs[schema_ref] = repair

    def register_response_schema(self, schema_ref, schema):
        fingerprint = digest(canonical(schema))
        key = "response-schema/" + schema_ref
        prior = self.records.get(key)
        if prior and prior[1]["digest"] != fingerprint:
            raise ValueError("Response schema changed within this run")
        self.records.put_once(key, {"digest": fingerprint, "schema": schema})
        self.response_schemas[schema_ref] = schema

    async def offer_retry(self, operation_id, replacement, *, process_id):
        """Optional owning-agent correction; absence of a repair agent is supported."""
        key = "retry/" + operation_id
        saved = self.records.get(key)
        if not saved or saved[1]["state"] != "waiting":
            raise ValueError("No replacement window is open")
        row = saved[1]
        if now() >= datetime.fromisoformat(row["until"]) or row.get("replacement"):
            raise ValueError("Replacement window expired or already used")
        original = OperationRequest.model_validate(self.records.get("effect/" + operation_id)[1]["request"])
        if process_id != original.scope.process_id:
            raise ValueError("Replacement belongs to another process")
        replacement = type(original.payload).model_validate(replacement)
        before, after = original.payload.model_dump(), replacement.model_dump()
        for field in ("context", "temperature"):
            before.pop(field, None)
            after.pop(field, None)
        if before != after:
            raise ValueError("Replacement cannot change role, phase, schema or capability grants")
        prior = original.payload.context
        proposed = replacement.context
        pins = {part.part_id: part for part in proposed.parts}
        if (
            proposed.maximum_input_tokens > prior.maximum_input_tokens
            or proposed.tool_catalog_digest != prior.tool_catalog_digest
        ):
            raise ValueError("Replacement cannot expand context or tool authority")
        if any(pins.get(part.part_id) != part for part in prior.parts if part.required):
            raise ValueError("Replacement must preserve required context pins")
        for part in proposed.parts:
            scope = part.content.scope
            if (scope.tenant_id, scope.project_id, scope.run_id) != (
                original.scope.tenant_id,
                original.scope.project_id,
                original.scope.run_id,
            ) or scope.process_id not in {None, process_id}:
                raise ValueError("Replacement context is outside the caller's data scope")
        bound = min(proposed.maximum_input_tokens, original.limits.max_input_tokens_per_call)
        if sum(part.content.size_bytes for part in proposed.parts) > bound:
            raise ValueError("Replacement context does not fit")
        messages = [
            {
                "role": "system"
                if part.part_kind == "instruction" and part.trust in {"application", "user"}
                else "assistant"
                if part.part_kind in {"message", "tool_call"}
                else "user",
                "content": self.artifacts.read(part.content).decode(),
            }
            for part in proposed.parts
        ]
        size = len(canonical(messages))
        endpoint = getattr(self.config, self.config.role_bindings[replacement.role])
        if size > bound or size + original.limits.max_output_tokens_per_call > endpoint.max_context_tokens:
            raise ValueError("Replacement context does not fit")
        if now() >= datetime.fromisoformat(row["until"]):
            raise ValueError("Replacement window expired")
        self.records.compare_and_publish(
            {key: saved[0]}, {key: {**row, "replacement": replacement.model_dump(mode="json")}}
        )
        self.retry_events[operation_id].set()

    async def _dispatch(self, request, key):
        payload = request.payload
        eligible = isinstance(payload, ModelQuery) or (
            isinstance(payload, AgentJob) and not payload.allowed_capabilities
        )
        if not eligible or not hasattr(self.config, "inference_retry") or payload.response_schema_ref not in self.response_validators:
            return await self._dispatch_once(request, key)
        self._update(key, {**self.records.get(key)[1], "state": "active"})
        self._effect_status(request, True)
        attempts, outputs, current = [], [], request
        policy = self.config.inference_retry
        try:
            for index in range(policy.max_attempts):
                attempt_id = digest(canonical([request.operation_id, "inference-attempt", index]))
                attempt_key = "inference-attempt/" + request.operation_id + f"/{index}"
                prior = self.records.get(attempt_key)
                if prior:
                    child = OperationRequest.model_validate(prior[1]["request"])
                    if not prior[1].get("result") and prior[1]["state"] != "prepared":
                        raise RuntimeError("Unreconciled inference attempt")
                else:
                    child = request if index == 0 else current.model_copy(
                        update={
                            "record_id": "request/" + attempt_id,
                            "operation_id": attempt_id,
                            "logical_step_id": request.logical_step_id + f"/attempt-{index}",
                        }
                    )
                    child = child.model_copy(update={"intent_digest": operation_fingerprint(child)})
                    self._update(
                        attempt_key,
                        {
                            "request": child.model_dump(mode="json"),
                            "fingerprint": child.intent_digest,
                            "state": "prepared",
                            "result": None,
                        },
                    )
                self.records.put_once("inference-attempt-index/" + child.operation_id, {"record_ref": attempt_key})
                if prior and prior[1].get("result"):
                    result = OperationResult.model_validate(prior[1]["result"])
                else:
                    result = await self._dispatch_once(child, key if index == 0 else attempt_key)
                    retained_attempt = self.records.get(attempt_key)[1]
                    self._update(attempt_key, {**retained_attempt, "state": result.state, "result": result.model_dump(mode="json")})
                output = self._read_inference_output(result)
                if result.state != "uncertain":
                    self._update(key, {**self.records.get(key)[1], "state": "active", "result": None})
                    self._effect_status(request, True)
                if result.state == "succeeded":
                    validator = self.response_validators.get(child.payload.response_schema_ref)
                    if validator:
                        try:
                            validator(output["text"], child.payload)
                        except Exception as exc:
                            result = result.model_copy(
                                update={
                                    "state": "failed",
                                    "error": ErrorDetail(
                                        code="ResponseValidationError",
                                        message=str(exc)[:2000],
                                        retryable_after_reconciliation=True,
                                        retry_after_ms=None,
                                    ),
                                }
                            )
                            row = self.records.get(attempt_key)[1]
                            self._update(
                                attempt_key,
                                {**row, "state": "failed", "result": result.model_dump(mode="json")},
                            )
                attempts.append(
                    {
                        "record_ref": attempt_key,
                        "operation_id": child.operation_id,
                        "state": result.state,
                        "error": result.error.model_dump(mode="json") if result.error else None,
                    }
                )
                outputs.append((result, output))
                if (
                    result.state == "succeeded"
                    or result.execution_termination != "confirmed_stopped"
                    or result.effects == "unknown"
                    or bool(result.extensions.get("polyinference/incomplete-generation"))
                    or (result.error and result.error.code not in {"ResponseValidationError", "RuntimeError", "EndpointError"})
                    or index + 1 >= policy.max_attempts
                    or request.deadline <= now()
                ):
                    break
                root = self.model_retries.root(request)
                used_retries = self.records.scan("response-retry/" + root + "/")
                retry_receipt = "response-retry/" + root + "/" + child.operation_id
                if not self.records.get(retry_receipt):
                    if len(used_retries) >= policy.max_attempts - 1:
                        break
                    self.records.put_once(retry_receipt, {"operation_id": child.operation_id})
                event = self.retry_events[request.operation_id] = asyncio.Event()
                until = min(request.deadline, now() + timedelta(seconds=policy.replacement_wait_seconds))
                retry_key = "retry/" + request.operation_id
                retained = self.records.get(retry_key)
                if not retained or retained[1]["attempt"] != index + 1:
                    self._update(
                        retry_key,
                        {
                            "state": "waiting",
                            "attempt": index + 1,
                            "process_id": request.scope.process_id,
                            "until": until.isoformat(),
                            "error": attempts[-1]["error"],
                            "replacement": None,
                        },
                    )
                row = self.records.get(retry_key)[1]
                until = min(request.deadline, datetime.fromisoformat(row["until"]))
                repair = self.response_repairs.get(payload.response_schema_ref)
                if repair and not row.get("replacement") and now() < until:
                    try:
                        replacement = repair(request, row["error"] or {})
                        if inspect.isawaitable(replacement):
                            if inspect.iscoroutine(replacement):
                                replacement.close()
                            raise TypeError("Response repair must be synchronous")
                        if replacement is not None:
                            await self.offer_retry(request.operation_id, replacement,
                                                   process_id=request.scope.process_id)
                    except Exception as exc:
                        # Optional feedback cannot replace the physical execution outcome.
                        self._update("response-repair-error/" + request.operation_id,
                                     {"error": type(exc).__name__, "attempt": row["attempt"]})
                    row = self.records.get(retry_key)[1]
                if row["state"] == "waiting" and not row.get("replacement"):
                    try:
                        await asyncio.wait_for(event.wait(), max(0, (until - now()).total_seconds()))
                    except asyncio.TimeoutError:
                        pass
                row = self.records.get(retry_key)[1]
                current = (
                    request.model_copy(update={"payload": type(payload).model_validate(row["replacement"])})
                    if row.get("replacement")
                    else request
                )
                self._update(retry_key, {**row, "state": "consumed"})
            last, output = outputs[-1]
            output = {
                **output,
                "inference_attempts": attempts,
                "usage": _sum_usage([body.get("usage") for _, body in outputs]),
            }
            if last.state != "succeeded":
                output["error"] = last.error.message if last.error else "Inference attempts exhausted"
                if last.error and last.error.code == "ResponseValidationError":
                    output.setdefault("text", "")
            usage = [
                UsageMeasure(
                    metric="tokens",
                    unit="tokens",
                    value=sum(r.usage[0].value for r, _ in outputs)
                    if all(r.usage and r.usage[0].value is not None for r, _ in outputs)
                    else None,
                    provenance="provider_reported"
                    if all(r.usage and r.usage[0].value is not None for r, _ in outputs)
                    else "unknown",
                    account_scope_ref=request.budget_account_ref,
                )
            ]
            combined = last.model_copy(
                update={
                    "record_id": "result/" + request.operation_id,
                    "operation_id": request.operation_id,
                    "logical_step_id": request.logical_step_id,
                    "output_refs": [
                        self.artifacts.put(canonical(output), request.scope),
                        *[ref for r, _ in outputs for ref in r.output_refs],
                    ],
                    "usage": usage,
                    "started_at": outputs[0][0].started_at,
                }
            )
            self._update(
                key, {**self.records.get(key)[1], "state": combined.state, "result": combined.model_dump(mode="json")}
            )
            return combined
        except BaseException:
            # A lost driver may leave an attempt running; only explicit reconciliation
            # of its durable result can make this operation retryable after restart.
            root = self.records.get(key)[1]
            if "child" in locals() and child.operation_id == request.operation_id:
                attempt = self.records.get(attempt_key)
                # The logical operation remains active while awaiting a repair.
                # Do not replace a settled physical receipt with that wait state.
                if not attempt[1].get("result"):
                    self._update(attempt_key, {**attempt[1], "state": root["state"], "result": root.get("result"),
                        **{name: root[name] for name in ("failure", "provider") if name in root}})
            self._update(key, {**root, "state": "uncertain", "result": None})
            raise
        finally:
            self.retry_events.pop(request.operation_id, None)
            if self.records.get(key)[1].get("result"):
                self._effect_status(request, False)

    def _read_inference_output(self, result):
        import json

        return json.loads(self.artifacts.read(result.output_refs[0])) if result.output_refs else {}


def _sum_usage(values):
    if not values or any(not isinstance(value, dict) for value in values):
        return None
    result = {}
    for key in set().union(*values):
        parts = [value.get(key, 0) for value in values]
        if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in parts):
            result[key] = sum(parts)
        elif all(isinstance(value, dict) for value in parts):
            result[key] = _sum_usage(parts)
    return result
