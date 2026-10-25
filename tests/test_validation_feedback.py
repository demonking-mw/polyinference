from __future__ import annotations

import json

import pytest
from langgraph.runtime import Runtime
from test_runtime import setup

from polyinference.agent.senior import validate
from polyinference.agent.worker import AppContext, consume
from polyinference.runtime.codex import native_context


@pytest.mark.parametrize(
    "reply",
    [
        {"invalid_output": "not JSON"},
        {"kind": "action", "tool": "protocol.validation", "arguments": {}},
        {"kind": "assessment", "verdict": "successful", "summary": "wrong phase"},
    ],
)
async def test_worker_validation_feedback_is_data_not_a_fabricated_tool(config, reply):
    runtime, app, _ = await setup(config)
    state = {"process_id": "fixture", "phase": "development", "logical_step": 3, "reply": reply}
    try:
        result = await consume(state, Runtime(context=AppContext(app)))
        history = app.history(result["trajectory_ref"])
        assert len(history) == 1 and "reply" not in history[0]
        feedback = history[0]["feedback"]
        assert app.read(feedback["received_output_ref"]) == reply
        assert history[0]["source_ref"] == "request/fixture/model-3"
        view = app.context("trusted", {"objective": "work"}, history, "fixture", {})
        parts = [part for part in view.parts if part.part_id.endswith("/feedback")]
        assert len(parts) == 1 and parts[0].part_kind == "data" and parts[0].call_id is None
        assert not any(part.part_kind in {"tool_call", "tool_result"} for part in view.parts)
        messages = [
            {
                "role": "system" if p.part_kind == "instruction" else "user",
                "content": runtime.artifacts.read(p.content).decode(),
            }
            for p in view.parts
        ]
        assert json.loads(messages[-1]["content"])["application_feedback"] == feedback
        instructions, native = native_context(messages)
        assert "application_feedback" not in instructions
        assert "application_feedback" in native[-1]["text"]
        assert result["route"] == "model"
    finally:
        await runtime.close()


async def test_senior_validation_feedback_preserves_proposal_and_deduplicates(config):
    runtime, app, _ = await setup(config)
    state = {"process_id": "fixture", "logical_step": 0, "reply": {"invalid_output": "bad proposal"}}
    try:
        result = await validate(state, Runtime(context=AppContext(app)))
        again = await validate(
            {**state, "trajectory_ref": result["trajectory_ref"]}, Runtime(context=AppContext(app))
        )
        history = app.history(again["trajectory_ref"])
        assert len(history) == 1 and "feedback" in history[0]
        assert app.read(history[0]["feedback"]["received_output_ref"]) == state["reply"]
        assert "reply" not in history[0]
    finally:
        await runtime.close()


async def test_feedback_does_not_split_real_tool_pairs(config):
    runtime, app, _ = await setup(config)
    try:
        ref = app.append_history(
            None,
            "read",
            {"kind": "action", "tool": "files.read", "arguments": {"path": "a.py"}},
            {"content": "VALUE = 1"},
        )
        ref = app.append_feedback(ref, "invalid", {"error": "invalid response"}, source_ref="request/model")
        view = app.context("trusted", {}, app.history(ref), "fixture", {})
        calls = [part.call_id for part in view.parts if part.part_kind == "tool_call"]
        results = [part.call_id for part in view.parts if part.part_kind == "tool_result"]
        assert calls == results == ["read"]
    finally:
        await runtime.close()
