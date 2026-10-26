"""Generic preparation of durable resume intents, independent of agent policy."""
from __future__ import annotations

import asyncio
import json

from ..contracts import ArtifactRef, ModelQuery, OperationRequest
from ..primitives import now
from .inference import IncompleteGeneration, ModelResponseError


def progress(records, request_ref, state, **details):
    key = "resume-preparation/" + request_ref
    old = records.get(key)
    records.compare_and_publish({key: old[0] if old else 0}, {
        key: {"state": state, "updated_at": now().isoformat(), **details},
    })


async def prepare(runtime, request_ref):
    """Requires the runtime's coordinator lease; never infer remote termination."""
    records = runtime.records
    if not records.get(request_ref):
        raise ValueError("Unknown resume request")
    progress(records, request_ref, "recovering")
    try:
        if any(not task.done() for task in runtime.inflight.values()):
            raise RuntimeError("Could not resume while previous work is still running.")
        await runtime.reconcile_known()
        for operation_id in runtime.uncertain(include_isolated=True):
            retained = records.get("effect/" + operation_id)[1]
            if "request" not in retained:
                raise RuntimeError("Could not resume: this saved operation lacks recovery metadata.")
            request = OperationRequest.model_validate(retained["request"])
            if any(row["request"]["operation_id"] != operation_id for _, _, row in runtime._unsettled_response_attempts(operation_id)):
                raise RuntimeError("Could not resume: an unsettled response-repair attempt requires explicit reconciliation.")
            if retained.get("isolated_generation"):
                # Physical reconciliation is independent of logical delivery. A
                # late result releases holds but never replaces the chosen answer.
                adapter = runtime.clients[runtime.config.role_bindings[request.payload.role]]
                receipt = records.get("model-response/" + operation_id)
                try:
                    if receipt:
                        response = json.loads(runtime.artifacts.read(ArtifactRef.model_validate(receipt[1]["response_ref"])))
                    else:
                        remaining = min(30, max(0, (request.deadline - now()).total_seconds()))
                        response = (await asyncio.wait_for(adapter.recover_operation(request, retained), remaining)
                                    if remaining > 0 and hasattr(adapter, "recover_operation") else None)
                    if response is not None:
                        await runtime.settle_recovered_model(request, response)
                except (ModelResponseError, IncompleteGeneration) as exc:
                    await runtime.settle_recovered_model(request, exc.response, failure=exc)
                except Exception:
                    pass  # Unavailable status never establishes termination.
                continue
            receipt = records.get("model-response/" + operation_id)
            # A query-only completed response has no native tools or host
            # descendants. Native jobs require their own audited recovery path.
            if isinstance(request.payload, ModelQuery) and receipt:
                await runtime.settle_recovered_model(
                    request, json.loads(runtime.artifacts.read(ArtifactRef.model_validate(receipt[1]["response_ref"]))))
                continue
            if isinstance(request.payload, ModelQuery):
                name = runtime.config.role_bindings[request.payload.role]
                adapter = runtime.clients[name]
                recover = getattr(adapter, "recover_operation", None)
                if recover:
                    remaining = min(30, getattr(runtime.config, name).timeout_seconds,
                                    max(0, (request.deadline - now()).total_seconds()))
                    if remaining > 0:
                        try:
                            result = await asyncio.wait_for(recover(request, retained), remaining)
                        except asyncio.TimeoutError as exc:
                            raise RuntimeError(
                                "Could not resume: the provider has not returned the previous request's outcome."
                            ) from exc
                        except (ModelResponseError, IncompleteGeneration) as exc:
                            await runtime.settle_recovered_model(request, exc.response, failure=exc)
                            continue
                        if result is not None:
                            # Only query-only normalized completed results may
                            # settle through this path. Native side effects need
                            # separate evidence, including broker/host cleanup.
                            await runtime.settle_recovered_model(request, result)
                            continue
            raise RuntimeError(
                "Could not resume: the previous operation's outcome is unavailable. "
                "Its provider does not support automatic recovery for this saved request."
            )
        if runtime.uncertain():
            raise RuntimeError("Could not resume while previous work is still running.")
        for _, _, effect in records.scan("effect/"):
            if effect.get("reconciliation") not in {"retained_completed_response", "durable_host_receipt"}:
                continue
            request = OperationRequest.model_validate(effect["request"])
            result = effect["result"]
            actual = next((item.get("value") for item in result.get("usage", [])
                           if item.get("metric") == "tokens" and item.get("provenance") == "provider_reported"), None)
            # Wire UsageMeasure values are floats, while token allocations use
            # integer counts. Restore a known integral count without rounding.
            if isinstance(actual, float) and actual.is_integer():
                actual = int(actual)
            if type(actual) is not int or actual < 0:
                actual = None
            runtime._settle_budget(request, actual)
            runtime._effect_status(request, False)
            notified = "resume-recovery-notified/" + request.operation_id
            if (result["state"] == "failed" and not effect.get("isolated_generation")
                    and runtime.on_reconciled and not records.get(notified)):
                from ..contracts import OperationResult

                await runtime.on_reconciled(request, OperationResult.model_validate(result))
                records.put_once(notified, {"request_ref": request_ref})
        for admission in runtime.admission.values():
            admission.restore()
        progress(records, request_ref, "ready")
    except Exception as exc:
        progress(records, request_ref, "failed", error=str(exc)[:2000])
        raise
