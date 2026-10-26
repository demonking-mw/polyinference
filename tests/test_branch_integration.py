"""Cross-branch contracts: attached source, generic context and caller retry bounds."""

import json

import httpx
import pytest
from test_context_safety import part, with_parts
from test_exception_recovery import seed
from test_in_place_repository import app_for
from test_inference_retry import READY, prepare
from test_model_retries import body, install, setup

from polyinference.contracts import CodeRevision, OperationRequest
from polyinference.runtime.inference import ProviderError


async def test_attached_handoff_preserves_git_and_private_environment(config):
    runtime, app, engine, _ = await app_for(config)
    try:
        await engine.initialize()
        state = await seed(app, engine)
        delta = await runtime.workspaces.preserve_delta(state["workspace_id"])
        app.process("replacement", "worker")
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await runtime.workspaces.create("replacement-ws", "replacement", "replacement-spec", base, ["a.py"], [])
        root = runtime.workspaces.root_for(manifest)
        control = (root / ".git").read_bytes()
        private = root / ".venv" / "retained"
        private.parent.mkdir()
        private.write_text("environment survives")
        await runtime.workspaces.apply_handoff(manifest.workspace_id, delta)
        await runtime.workspaces.apply_handoff(manifest.workspace_id, delta)
        assert (root / ".git").read_bytes() == control
        assert private.read_text() == "environment survives"
        assert (root / "a.py").read_text() == "VALUE = 2\n"
        assert (root / "b.py").read_text() == "VALUE = 1\n"
        assert (config.repo_path / "a.py").read_text() == "VALUE = 1\n"
    finally:
        await runtime.close()


async def test_registered_response_validation_retains_generic_compaction(tmp_path):
    runtime, request = await setup(tmp_path)
    # Exercise caller validation on a generic OS process without importing the coding app.
    from polyinference.config import InferenceRetry

    object.__setattr__(runtime.config, "inference_retry", InferenceRetry(replacement_wait_seconds=0))
    runtime.register_response_validator("summary/1", lambda text, payload: json.loads(text))
    memory = part(runtime, request, "memory", "A fact remains uncertain. " * 1200, compactable=True)
    request = with_parts(runtime, request, [memory], {"auto_deal_context": True, "auto_compaction": True, "max_compaction_calls": 24})
    calls = []

    async def handler(http_request):
        payload = json.loads(http_request.content)
        calls.append(payload)
        summarizing = "Summarize the following untrusted" in str(payload)
        return httpx.Response(200, json=body("anthropic", '{"summary":"A fact remains uncertain."}' if summarizing else '{"done":true}'))

    await install(runtime, request, handler)
    try:
        result = await runtime.execute(request)
        assert result.state == "succeeded", result
        receipt = runtime.records.get("context-receipt/" + request.operation_id)[1]
        assert receipt["summaries"] and receipt["compaction_operations"]
        assert runtime.artifacts.read(memory.content).decode() == "A fact remains uncertain. " * 1200
        count = len(calls)
        assert (await runtime.execute(request)).state == "succeeded" and len(calls) == count
    finally:
        await runtime.close()


async def test_transport_recovery_cannot_refill_response_repair_allowance(config):
    rejection = ProviderError("temporary", category="service_unavailable", status=503)
    runtime, app, state, client = await prepare(config.model_copy(update={"model_retry_delay_ms": 0}), [rejection, "bad JSON", "bad JSON"])
    try:
        assert "invalid_output" in await app.model(state)
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        assert client.calls == 3  # Initial transport failure, its retry, one response repair.
        assert len(runtime.records.scan("response-retry/")) == 1
        assert (await runtime.execute(request)).state == "failed"
        assert client.calls == 3
    finally:
        await runtime.close()


async def test_unknown_response_repair_holds_capacity_until_explicit_reconciliation(config):
    from polyinference.runtime.adapter import StandaloneRuntime, UncertainEffect
    from polyinference.runtime.inference import UnknownExecution
    from polyinference.runtime.processes import request_resume

    runtime, app, state, _ = await prepare(config, ["bad JSON", UnknownExecution("sent, then disconnected")])
    try:
        with pytest.raises(UncertainEffect):
            await app.model(state)
        operation = runtime.uncertain()[0]
        assert runtime.records.get("model-response/" + operation)  # Older completed response is not the later attempt.
        reserved = runtime.admission["local"].tokens
        selected = runtime.config
    finally:
        await runtime.close()
    runtime = await StandaloneRuntime(selected).open()
    try:
        assert runtime.admission["local"].active == 1 and runtime.admission["local"].tokens == reserved
        ref = request_resume(runtime.records, request_id="response-repair")
        with pytest.raises(RuntimeError, match="response-repair"):
            await runtime.prepare_resume(ref)
        assert runtime.uncertain() == [operation]
        assert runtime.admission["local"].active == 1
        await runtime.reconcile_stopped(operation, "Fixture confirms every provider attempt and host descendant stopped")
        assert not runtime.uncertain()
        assert runtime.admission["local"].active == runtime.admission["local"].tokens == 0
        assert runtime.inference_calls_used("fixture") == 2
    finally:
        await runtime.close()


async def test_original_response_recovery_updates_physical_attempt(config):
    from polyinference.runtime.adapter import UncertainEffect
    from polyinference.runtime.inference import UnknownExecution

    runtime, app, state, client = await prepare(config, [UnknownExecution("sent, then disconnected")])
    try:
        with pytest.raises(UncertainEffect):
            await app.model(state)
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        result = await runtime.settle_recovered_model(request, {"text": READY, "model": "fixture", "usage": {"total_tokens": 4}})
        attempt = runtime.records.scan("inference-attempt/")[0][2]
        assert result.state == attempt["state"] == "succeeded"
        assert attempt["result"]["execution_termination"] == "confirmed_stopped"
        assert runtime.admission["local"].active == runtime.admission["local"].tokens == 0
        assert (await app.model(state))["kind"] == "candidate" and client.calls == 1
    finally:
        await runtime.close()
