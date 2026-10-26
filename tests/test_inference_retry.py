from __future__ import annotations

import asyncio
import json

import pytest
from test_runtime import setup

from polyinference.contracts import ArtifactRef, ContextPart, OperationRequest
from polyinference.domain import canonical, digest
from polyinference.runtime.adapter import StandaloneRuntime, UncertainEffect
from polyinference.runtime.inference import UnknownExecution


class Client:
    def __init__(self, outputs):
        self.outputs, self.calls, self.messages = outputs, 0, []

    async def generate(self, messages, *args, **kwargs):
        self.messages.append(messages)
        value = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        if isinstance(value, Exception):
            raise value
        return {"text": value, "model": "retry-fixture", "usage": {"total_tokens": 5}, "events": []}

    async def close(self):
        pass


READY = '{"kind":"candidate","summary":"ready"}'


async def prepare(config, outputs, wait=0.01):
    config = config.model_copy(
        update={
            "inference_retry": config.inference_retry.model_copy(update={"replacement_wait_seconds": wait})
        }
    )
    runtime, app, _ = await setup(config)
    await runtime.clients["local"].close()
    client = runtime.clients["local"] = Client(outputs)
    app.update(
        "fixture-task",
        {
            "assignment": {
                "task_id": "fixture",
                "objective": "bounded",
                "write_paths": ["a.py"],
                "checks": ["syntax"],
            }
        },
    )
    state = {
        "process_id": "fixture",
        "workspace_id": "fixture-ws",
        "task_ledger_ref": "fixture-task",
        "phase": "development",
        "logical_step": 0,
    }
    return runtime, app, state, client


@pytest.mark.parametrize(
    "failure", ["not json", '{"kind":"action","tool":"made_up"}', RuntimeError("unfamiliar backend failure")]
)
async def test_os_retries_without_any_agent_repair_structure(config, failure):
    runtime, app, state, client = await prepare(config, [failure, READY])
    try:
        assert (await app.model(state))["kind"] == "candidate"
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        result = await runtime.execute(request)
        assert client.calls == 2 and result.state == "succeeded"
        assert len(runtime.records.scan("inference-attempt/")) == 2
        assert app.get("budget/model-calls/fixture")["used"] == 2
        assert (await app.model(state))["kind"] == "candidate"
        assert client.calls == 2  # Logical replay is not another retry.
        if isinstance(failure, str):
            assert result.usage[0].value == 10
        else:
            assert result.usage[0].value is None  # Unknown usage never becomes zero.
    finally:
        await runtime.close()


async def test_agent_replacement_in_window_wins_without_widening_authority(config):
    runtime, app, state, client = await prepare(config, ["bad", READY], wait=1)

    async def repair():
        while not runtime.records.scan("retry/"):
            await asyncio.sleep(0.001)
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        payload = request.payload
        part = ContextPart(
            part_id="repair",
            content=app.artifact("Use valid JSON", "fixture"),
            part_kind="data",
            trust="application",
            source_ref="agent-repair",
            required=False,
        )
        context = payload.context.model_copy(update={"parts": [*payload.context.parts, part]})
        context = context.model_copy(
            update={
                "view_id": digest(canonical(context.model_dump()["parts"])),
                "digest": digest(canonical(context.model_dump()["parts"])),
            }
        )
        replacement = payload.model_copy(update={"context": context})
        with pytest.raises(ValueError, match="another process"):
            await runtime.offer_retry(request.operation_id, replacement, process_id="other")
        with pytest.raises(ValueError, match="role"):
            await runtime.offer_retry(
                request.operation_id, replacement.model_copy(update={"role": "senior"}), process_id="fixture"
            )
        with pytest.raises(ValueError, match="pins"):
            await runtime.offer_retry(
                request.operation_id,
                replacement.model_copy(update={"context": context.model_copy(update={"parts": [part]})}),
                process_id="fixture",
            )
        large = part.model_copy(
            update={
                "part_id": "oversize",
                "content": app.artifact("x" * config.limits.max_input_tokens_per_call, "fixture"),
            }
        )
        with pytest.raises(ValueError, match="does not fit"):
            await runtime.offer_retry(
                request.operation_id,
                payload.model_copy(
                    update={"context": context.model_copy(update={"parts": [*context.parts, large]})}
                ),
                process_id="fixture",
            )
        await runtime.offer_retry(request.operation_id, replacement, process_id="fixture")

    try:
        result, _ = await asyncio.wait_for(asyncio.gather(app.model(state), repair()), 5)
        assert result["kind"] == "candidate" and client.calls == 2
        assert any(m["content"] == json.dumps("Use valid JSON") for m in client.messages[1])
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        with pytest.raises(ValueError, match="window"):
            await runtime.offer_retry(request.operation_id, request.payload, process_id="fixture")
    finally:
        await runtime.close()


async def test_retry_exhaustion_is_bounded_and_does_not_fabricate_success(config):
    runtime, app, state, client = await prepare(config, ["always bad"])
    try:
        assert "invalid_output" in await app.model(state)
        assert client.calls == 2
        effects = runtime.records.scan("effect/")
        assert len(effects) == 1 and effects[0][2]["state"] == "failed"
        assert effects[0][2]["result"]["error"]["code"] == "ResponseValidationError"
        assert not runtime.uncertain()
    finally:
        await runtime.close()


async def test_uncertain_execution_keeps_ownership_and_never_blindly_retries(config):
    runtime, app, state, client = await prepare(config, [UnknownExecution("lost after send"), READY])
    try:
        with pytest.raises(UncertainEffect):
            await app.model(state)
        assert client.calls == 1 and len(runtime.uncertain()) == 1
        assert runtime.admission["local"].active == 1
    finally:
        await runtime.close()


async def test_raw_attempts_obey_shared_call_limit(config):
    config = config.model_copy(
        update={
            "limits": config.limits.model_copy(
                update={
                    "max_model_calls": 2,
                    "final_phase_reserve": config.limits.final_phase_reserve.model_copy(
                        update={"reconciliation_model_calls": 1, "assessment_model_calls": 1}
                    ),
                }
            )
        }
    )
    runtime, app, state, client = await prepare(config, ["bad", READY])
    try:
        state["phase"] = "reconciliation"
        assert (await app.model(state))["kind"] == "candidate"
        with pytest.raises(RuntimeError, match="allowance exhausted"):
            await app.model({**state, "logical_step": 1})
        assert client.calls == 2
    finally:
        await runtime.close()


async def test_completed_attempt_recovery_does_not_resubmit_or_recharge(config):
    runtime, app, state, client = await prepare(config, ["bad", READY])
    try:
        await app.model(state)
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        key = "effect/" + request.operation_id
        row = app.get(key)
        runtime._update(key, {**row, "state": "active", "result": None})
        before = app.get("budget/model-calls/fixture")
        config = runtime.config
    finally:
        await runtime.close()
    runtime = await StandaloneRuntime(config).open()
    runtime.register_response_validator("worker/1", lambda text, payload: json.loads(text))
    await runtime.clients["local"].close()
    runtime.clients["local"] = client
    try:
        result = await runtime.execute(request)
        assert result.state == "succeeded" and client.calls == 2
        assert runtime.records.get("budget/model-calls/fixture")[1] == before
    finally:
        await runtime.close()


async def test_costs_count_each_attempt_without_double_counting_logical_operation(config):
    from polyinference.costs import run_cost

    runtime, app, state, _ = await prepare(config, ["bad", READY])
    try:
        await app.model(state)
        records = {key: body for key, _, body in runtime.records.scan("")}
        costs = run_cost(
            records, lambda ref: runtime.artifacts.read(ArtifactRef.model_validate(ref)).decode()
        )
        assert costs["calls"] == 2
    finally:
        await runtime.close()


async def test_durable_accepted_replacement_survives_interruption(config):
    runtime, app, state, client = await prepare(config, ["bad", READY], wait=10)
    task = asyncio.create_task(app.model(state))
    try:

        async def waiting():
            while not runtime.records.scan("retry/"):
                await asyncio.sleep(0.001)

        await asyncio.wait_for(waiting(), 5)
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        part = ContextPart(
            part_id="durable-repair",
            content=app.artifact("retained correction", "fixture"),
            part_kind="data",
            trust="application",
            source_ref="repair",
            required=False,
        )
        payload = request.payload.model_copy(
            update={
                "context": request.payload.context.model_copy(
                    update={"parts": [*request.payload.context.parts, part]}
                )
            }
        )
        await runtime.offer_retry(request.operation_id, payload, process_id="fixture")
        runtime.inflight[request.operation_id].cancel()
        await asyncio.gather(task, return_exceptions=True)
        cfg = runtime.config
    finally:
        await runtime.close()
    runtime = await StandaloneRuntime(cfg).open()
    runtime.register_response_validator("worker/1", lambda text, payload: json.loads(text))
    await runtime.clients["local"].close()
    runtime.clients["local"] = client
    try:
        result = await runtime.execute(request)
        assert result.state == "succeeded" and client.calls == 2
        assert any("retained correction" in m["content"] for m in client.messages[-1])
    finally:
        await runtime.close()


async def test_http_failure_retries_and_keeps_private_details_out_of_exception_text(config, monkeypatch):
    import httpx

    from polyinference.runtime.inference import HTTPInference

    monkeypatch.setenv("RETRY_TEST_KEY", "private-test-secret")
    runtime, app, state, _ = await prepare(config, [])
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                502, json={"error": {"code": "structured_output_failed", "message": "private-test-secret"}}
            )
        return httpx.Response(
            200,
            json={
                "model": "fixture",
                "choices": [{"finish_reason": "stop", "message": {"content": READY}}],
                "usage": {"total_tokens": 5},
            },
        )

    endpoint = config.local.model_copy(update={"api_key_env": "RETRY_TEST_KEY"})
    runtime.clients["local"] = HTTPInference(
        endpoint, httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    try:
        assert (await app.model(state))["kind"] == "candidate" and calls == 2
        first = runtime.records.scan("inference-attempt/")[0][2]
        output = app.read(first["result"]["output_refs"][0])
        assert "structured_output_failed" in output["provider_detail"]
        assert "private-test-secret" not in output["provider_detail"]
        assert "private-test-secret" not in first["result"]["error"]["message"]
    finally:
        await runtime.close()


async def test_retries_preserve_caller_final_phase_capacity(config):
    config = config.model_copy(update={"limits": config.limits.model_copy(update={"max_model_calls": 5})})
    runtime, app, state, client = await prepare(config, ["bad", READY])
    try:
        result = await app.model(state)
        assert result["kind"] == "candidate" and "final phases" in result["summary"]
        assert client.calls == 1
        assert app.get("budget/model-calls/fixture")["used"] == 1
        assert not runtime.uncertain()
    finally:
        await runtime.close()
