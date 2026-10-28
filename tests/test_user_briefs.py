"""Coding policy supplies briefs; the OS delivers the same messages to either launch mode."""

from __future__ import annotations

import json

import pytest
from conftest import ScriptedAgent

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.runtime.kernel import KernelRuntime
from polyinference.ui import TestUI, run_with_terminal_events
from polyinference.ui_os import read_snapshot, runtime_view


@pytest.mark.parametrize("ui_mode", [False, True])
async def test_sprint_briefs_and_worker_messages_reach_user(config, capsys, ui_mode):
    class Provider(ScriptedAgent):
        def __init__(self):
            super().__init__(two=False)
            self.notified = False
            self.briefs = []

        async def generate(self, messages, max_output, response_schema=None):
            data = json.loads(next(m["content"] for m in messages
                                   if m["content"].startswith("Pinned application inputs:\n")).split("\n", 1)[1])
            if "assignment" in data and not self.notified:
                self.notified = True
                assert "user.notify" in data["available_tools"]
                return {"text": json.dumps({"kind": "action", "tool": "user.notify",
                                            "arguments": {"text": "Worker is updating a.py."}}),
                        "model": "fixture", "usage": {"total_tokens": 5}}
            response = await super().generate(messages, max_output, response_schema)
            if "assignment" not in data:
                assert "EVERY invocation" in messages[0]["content"] and "user_brief" in messages[0]["content"]
                reply = json.loads(response["text"])
                if not data["all_task_ids"]:
                    assert data["previous_user_brief"] is None
                    brief = "Planning the value update. No commit has been verified yet."
                else:
                    assert data["previous_user_brief"] == self.briefs[-1]
                    assert all(e["status"] == "passed" for e in data["independent_review_evidence"])
                    brief = "Value update verified. Latest working commit: " + data["head"]["commit_id"]
                self.briefs.append(brief)
                response["text"] = json.dumps({**reply, "user_brief": brief})
            return response

    provider = Provider()

    async def runner(selected):
        runtime = await KernelRuntime(selected).open()
        for client in runtime.clients.values():
            await client.close()
        runtime.clients = {"local": provider, "cloud": provider}
        try:
            return await ProjectAgent(AgentServices(runtime, selected)).run()
        finally:
            await runtime.close()

    result = await run_with_terminal_events(runner, config, "ui-run") if ui_mode else await runner(config)
    assert result["outcome"] == "completed"
    snapshot = read_snapshot(config.state_path)
    messages = runtime_view(snapshot, {})["messages"]
    assert len(messages) == 3
    assert [message["text"] for message in messages] == [provider.briefs[0], "Worker is updating a.py.",
                                                       provider.briefs[1]]
    assert snapshot["records"]["head/provisional"]["code"]["commit_id"] in messages[-1]["text"]
    terminal = capsys.readouterr().out
    for message in messages:
        assert terminal.count(message["text"]) == 1
    manager = TestUI(config.state_path / "ui")
    manager.runs["run"] = {"id": "run", "state": str(config.state_path), "created_at": "", "error": None}
    view = await manager.view("run")
    assert view["os"]["messages"] == messages
    assert (await manager.export("run"))["os"]["messages"] == messages
