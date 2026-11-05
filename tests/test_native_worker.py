"""A real stdio native job owns its internal loop; callbacks remain host effects."""

from __future__ import annotations

import json
import sys

import pytest
from conftest import ScriptedAgent

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.runtime.adapter import StandaloneRuntime


async def test_codex_brokered_worker_uses_same_phase_and_publication_protocol(config, tmp_path):
    script = tmp_path / "native.py"
    script.write_text(r"""import json,sys
def send(value):
 print(json.dumps(value),flush=True)
def receive():
 return json.loads(sys.stdin.readline())
for line in sys.stdin:
 message=json.loads(line); method=message.get("method")
 if method=="initialize":
  assert message["params"]["capabilities"]["experimentalApi"]
  send({"id":message["id"],"result":{}})
 elif method=="thread/start":
  assert message["params"]["dynamicTools"][0]["name"]=="polyinference_tool"
  assert message["params"]["permissions"]=="polyinference_readonly"
  assert "Return exactly one JSON object" in message["params"]["developerInstructions"]
  assert "baseInstructions" not in message["params"]
  assert message["params"]["approvalPolicy"]=="never"
  assert message["params"]["config"]["features.shell_tool"] is False
  assert "Never use native shell, apply_patch" in message["params"]["developerInstructions"]
  send({"id":message["id"],"result":{"thread":{"id":"native-thread"},"sandbox":{"type":"readOnly"},"approvalPolicy":"never"}})
 elif method=="turn/start":
  text=next(item["text"] for item in message["params"]["input"] if "Pinned application inputs:" in item["text"])
  data=json.loads(text.split("Pinned application inputs:\n".replace("\\n","\n"),1)[1])
  phase=data["phase"]
  if phase=="development":
   from hashlib import sha256
   send({"id":3,"method":"item/tool/call","params":{"threadId":"native-thread","turnId":"native-turn",
      "callId":"write-native","tool":"polyinference_tool","arguments":{"tool":"files.write","arguments":{
       "path":"a.py","expected_digest":"sha256:"+sha256(b"VALUE = 1\n".replace(b"\\n",b"\n")).hexdigest(),
       "content":"VALUE = 2\n".replace("\\n","\n")}}}})
   response=receive()
   assert response["id"]==3
   observation=json.loads(response["result"]["contentItems"][0]["text"])
   assert observation["state"]=="succeeded",observation
  send({"id":message["id"],"result":{"turn":{"id":"native-turn"}}})
  reply={"kind":"assessment","verdict":"successful","summary":"Native phase and host evidence inspected"} if phase=="assessment" else {"kind":"candidate","summary":"Native phase finished"}
  send({"method":"thread/tokenUsage/updated","params":{"threadId":"native-thread","turnId":"native-turn","tokenUsage":{"total":{"totalTokens":70000}}}})
  send({"method":"item/completed","params":{"item":{"type":"agentMessage","text":json.dumps({"reply":reply})}}})
  send({"method":"turn/completed","params":{"turn":{"id":"native-turn","status":"completed","items":[]}}})
""")
    # Simplify the quoted fixture so its generated source uses actual newline escapes.
    value = script.read_text().replace(
        'Pinned application inputs:\\n".replace("\\\\n","\\n")', 'Pinned application inputs:\\n"'
    )
    value = value.replace('b"VALUE = 1\\n".replace(b"\\\\n",b"\\n")', 'b"VALUE = 1\\n"')
    value = value.replace('"VALUE = 2\\n".replace("\\\\n","\\n")', '"VALUE = 2\\n"')
    script.write_text(value)
    native = config.local.model_copy(
        update={
            "protocol": "codex_app_server",
            "brokered_tools": True,
            "command": [sys.executable, str(script)],
            "timeout_seconds": 5,
        }
    )
    config = config.model_copy(update={"local": native})
    runtime = await StandaloneRuntime(config).open()
    await runtime.clients["cloud"].close()
    runtime.clients["cloud"] = ScriptedAgent(two=False)
    app = AgentServices(runtime, config)
    try:
        result = await ProjectAgent(app).run()
        assert result["outcome"] == "completed", app.get("app/run")
        report = runtime.records.scan("report/")[0][2]
        assert report["verdict"] == "successful"
        assert report["reconciliation_turn_refs"] and report["assessment_turn_refs"]
        children = [
            value for _, _, value in runtime.records.scan("effect/") if value["request"]["causal_parent_ref"]
        ]
        assert len(children) == 1
        assert children[0]["request"]["payload"]["capability_id"] == "files.write"
        parent = app.get("effect/" + children[0]["request"]["causal_parent_ref"])
        assert parent["request"]["payload"]["kind"] == "agent_job"
        assert parent["state"] == "succeeded"
        assert parent["result"]["usage"][0]["value"] == 70000
        assert (
            runtime.records.get("budget/process/" + parent["request"]["scope"]["process_id"])[1][
                "reserved_or_used"
            ]
            >= 210000
        )
        tree = await runtime.workspaces.tree(report["candidate_commit_id"])
        assert tree["a.py"][1] == b"VALUE = 2\n"
        assert runtime.records.get("permit/shell/installation")[1]["process_id"] is None
    finally:
        await runtime.close()


@pytest.mark.parametrize("target", ["native_source", "native_ignored", "broker_source", "retired_view", "before_callback"])
async def test_unbrokered_native_writes_are_rejected_even_inside_source_grant(config, target):
    native = config.cloud.model_copy(update={"protocol": "codex_app_server", "brokered_tools": True})
    config = config.model_copy(update={"cloud": native, "prepare_repository": True, "write_scope": "project"})
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    input_roots = []

    class Unbrokered:
        async def generate_job(self, messages, snapshot, schema, callback=None):
            manifest = runtime.workspaces.current("workspace-setup-project")
            broker_root = runtime.workspaces.root_for(manifest)
            assert snapshot != broker_root
            assert "read-only" in messages[0]["content"]
            input_roots.append(snapshot)
            if target in {"native_source", "before_callback"}:
                (snapshot / "a.py").write_text("unbrokered")
                if target == "before_callback":
                    await callback("should-not-run", {"tool": "files.write", "arguments": {
                        "path": "README.md", "content": "unreachable", "expected_digest": None}})
                    pytest.fail("A callback after input tampering must not execute")
            elif target == "native_ignored":
                (snapshot / "node_modules").mkdir()
                (snapshot / "node_modules/hidden").write_text("unbrokered")
            else:
                if target == "retired_view":
                    observed = await callback("expand", {"tool": "files.write", "arguments": {
                        "path": "README.md", "content": "registered", "expected_digest": None}})
                    assert observed["state"] == "succeeded", observed
                    assert runtime.workspaces.current(manifest.workspace_id).generation > manifest.generation
                (broker_root / "a.py").write_text("unbrokered")
            return {"text": json.dumps({"kind": "candidate", "summary": "done"}),
                    "usage": {"total_tokens": 10}, "model": "fixture", "events": []}

        async def close(self):
            pass

    await runtime.clients["cloud"].close()
    runtime.clients["cloud"] = Unbrokered()
    try:
        result = await ProjectAgent(app).run()
        assert result["outcome"] == "paused", app.get("app/run")
        assert input_roots and not runtime.records.scan("report/")
        effects = [value for _, _, value in runtime.records.scan("effect/")
                   if value["request"]["payload"]["kind"] == "agent_job"]
        if target == "before_callback":
            assert effects[-1]["state"] == "uncertain"
            assert "outside the broker" in effects[-1]["diagnostic"]
            assert runtime.uncertain()  # No terminal reply: do not invent stopped execution.
            assert not any(value["request"]["causal_parent_ref"] for _, _, value in runtime.records.scan("effect/"))
        else:
            assert effects[-1]["state"] == "failed"
            assert "outside the broker" in effects[-1]["result"]["error"]["message"]
            assert not runtime.uncertain()  # A returned terminal job is known stopped.
        head = app.get("head/provisional")["code"]
        assert (await runtime.workspaces.tree(head["commit_id"]))["a.py"][1] == b"VALUE = 1\n"
        if target.startswith("native") or target == "before_callback":
            root = runtime.workspaces.root_for(runtime.workspaces.current("workspace-setup-project"))
            assert (root / "a.py").read_text() == "VALUE = 1\n"
    finally:
        await runtime.close()
