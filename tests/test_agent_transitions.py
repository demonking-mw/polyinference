"""Agent data policy stays above OS storage and survives long interruption notes."""

from __future__ import annotations

import json

import pytest
from conftest import fixture_review_reply

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.contracts import ArtifactRef, TaskAttempt
from polyinference.runtime.kernel import KernelRuntime

REASON = (
    "Reconciliation confirms the tree contains only .gitignore; production-build fails with exit code 254. "
    "Preparing build prerequisites requires package.json and scaffold files, outside the assigned write scope "
    "of .gitignore. Expand setup write scope to permit these files. The host-selected pi-dev baseline was retained."
)


def pinned(messages):
    text = next(message["content"] for message in messages
                if message["content"].startswith("Pinned application inputs:\n"))
    return json.loads(text.split("\n", 1)[1])


@pytest.mark.parametrize("legacy_invalid", [False, True])
async def test_long_review_reason_retires_setup_and_activates_replacement(config, legacy_invalid):
    config = config.model_copy(update={
        "prepare_repository": True, "write_scope": "project",
        "objective": "Verify current source syntax after replacing interrupted setup",
    })
    runtime = await KernelRuntime(config).open()
    app = AgentServices(runtime, config)
    calls = []

    class Provider:
        async def generate(self, messages, max_output):
            data = pinned(messages)
            calls.append(data)
            if "assignment" in data:
                if data["assignment"]["task_id"] == "project_setup":
                    assert data["write_authority"]["may_add_project_paths"] is True
                    assert "files.write" in data["write_authority"]["capabilities"]
                    reply = {"kind": "needs_review", "reason": REASON}
                elif data["phase"] == "assessment":
                    reply = {"kind": "assessment", "verdict": "successful", "summary": "Current syntax verified"}
                else:
                    reply = {"kind": "candidate", "summary": "Ready to verify current source"}
            else:
                reply = {"goal": config.objective, "dispositions": [
                    {"report_ref": report["record_id"], "action": "keep", "reason": "Evidence checked"}
                    for report in data["reports"]
                ]}
                if "replacement" not in data["all_task_ids"]:
                    if legacy_invalid:
                        key = "attempt/setup-project"
                        version, body = runtime.records.get(key)
                        # Simulate data persisted by the old worker, bypassing the
                        # new agent write boundary, while preserving OS storage semantics.
                        runtime.records.compare_and_publish({key: version}, {key: {**body, "stop_reason": REASON}})
                    reply.update(tasks=[{
                        "task_id": "replacement", "objective": config.objective, "write_paths": ["a.py"],
                        "read_paths": ["a.py"], "checks": ["syntax"],
                    }], cancel_pending_task_ids=["project_setup"])
                else:
                    reply["complete"] = True
            return {"text": json.dumps(fixture_review_reply(reply, data)), "model": "fixture", "usage": {"total_tokens": 5}}

        async def close(self):
            pass

    for client in runtime.clients.values():
        await client.close()
    runtime.clients = {"local": Provider(), "cloud": Provider()}
    engine = ProjectAgent(app)
    try:
        result = await engine.run()
        assert result["outcome"] == "completed", app.get("app/run")
        attempt = TaskAttempt.model_validate(app.get("attempt/setup-project"))
        assert attempt.execution == "cancelled" and attempt.stop_reason == "superseded_by_plan"
        detail = ArtifactRef.model_validate(attempt.extensions["polyinference/stop-detail"])
        assert runtime.artifacts.read(detail).decode() == REASON
        assert app.get("task/replacement")["execution"] == "completed"
        assert app.get("review-batch/active")["state"] == "done"
        count = len(calls)
        assert (await engine.run())["outcome"] == "completed"
        assert len(calls) == count
        assert len(runtime.records.scan("attempt/")) == 2
    finally:
        await runtime.close()
