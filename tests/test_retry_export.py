from __future__ import annotations

import asyncio

from test_inference_retry import READY, prepare

from polyinference.contracts import ContextPart, OperationRequest
from polyinference.domain import canonical, digest
from polyinference.ui import TestUI


async def test_ui_export_preserves_real_replacement_attempt_and_context(config, tmp_path):
    runtime, app, state, client = await prepare(config, ["malformed original reply", READY], wait=1)

    async def correct():
        while not runtime.records.scan("retry/"):
            await asyncio.sleep(0.001)
        request = OperationRequest.model_validate(app.get("request/fixture/model-0"))
        part = ContextPart(
            part_id="correction",
            content=app.artifact("Use a valid reply", "fixture"),
            part_kind="data",
            trust="application",
            source_ref="agent/correction",
            required=False,
        )
        parts = [*request.payload.context.parts, part]
        context = request.payload.context.model_copy(
            update={
                "parts": parts,
                "view_id": digest(canonical([p.model_dump(mode="json") for p in parts])),
                "digest": digest(canonical([p.content.digest for p in parts])),
            }
        )
        await runtime.offer_retry(
            request.operation_id,
            request.payload.model_copy(update={"context": context}),
            process_id="fixture",
        )

    repair = asyncio.create_task(correct())
    try:
        assert (await app.model(state))["kind"] == "candidate"
        await repair
        assert client.calls == 2
    finally:
        if not repair.done():
            repair.cancel()
            await asyncio.gather(repair, return_exceptions=True)
        await runtime.close()

    manager = TestUI(tmp_path / "ui", state=config.state_directory)
    exported = await manager.export(next(iter(manager.runs)))
    attempts = sorted(exported["inference_attempts"], key=lambda item: item["record_ref"])
    assert len(attempts) == 2
    assert attempts[0]["state"] == "failed" and attempts[1]["state"] == "succeeded"
    assert attempts[0]["result"]["error"]["code"] == "ResponseValidationError"
    assert attempts[0]["outputs"][0]["value"]["text"] == "malformed original reply"
    assert not any(p["part_id"] == "correction" for p in attempts[0]["context_parts"])
    corrected = next(p for p in attempts[1]["context_parts"] if p["part_id"] == "correction")
    assert corrected["text"] == '"Use a valid reply"'
    assert corrected["trust"] == "application" and corrected["source_ref"] == "agent/correction"
    assert next(iter(exported["retry_windows"].values()))["state"] == "consumed"
    # The logical operation stays a single original intent; replay is not another attempt.
    models = [e for e in exported["effects"] if e["request"]["payload"]["kind"] == "model_query"]
    assert len(models) == 1
    assert not any(p["part_id"] == "correction" for p in models[0]["request"]["payload"]["context"]["parts"])
