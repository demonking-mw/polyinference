"""Native telemetry volume must not decide whether a model job completes."""

from __future__ import annotations

import json
import sys

import pytest

from polyinference.config import Endpoint
from polyinference.runtime.codex import CodexAppServer, NativeEventLog, NativeJobStopped
from polyinference.runtime.inference import UnknownExecution


@pytest.fixture
def noisy_server(tmp_path):
    script = tmp_path / "noisy_server.py"
    script.write_text('''import json,sys
def send(value): print(json.dumps(value),flush=True)
mode=sys.argv[1]
for line in sys.stdin:
 m=json.loads(line);method=m.get("method")
 if method=="initialize":send({"id":m["id"],"result":{}})
 elif method=="thread/start":send({"id":m["id"],"result":{"thread":{"id":"thread-fixture"},"sandbox":{"type":"readOnly"},"approvalPolicy":"never"}})
 elif method=="turn/start":
  send({"id":m["id"],"result":{"turn":{"id":"turn-fixture"}}})
  for _ in range(2100):send({"method":"item/agentMessage/delta","params":{"delta":"private-text"*200}})
  if mode=="disconnect":sys.exit(0)
  if mode=="failed":
   send({"method":"turn/completed","params":{"turn":{"id":"turn-fixture","status":"failed","error":{"message":"fixture terminal failure"}}}})
   continue
  send({"method":"item/completed","params":{"item":{"type":"agentMessage","text":"{\\"complete\\":true}"}}})
  send({"method":"thread/tokenUsage/updated","params":{"threadId":"thread-fixture","turnId":"turn-fixture","tokenUsage":{"total":{"totalTokens":17}}}})
  # Evict the raw final-message and usage events; execution state must survive.
  for _ in range(2100):send({"method":"test/progress","params":{}})
  send({"id":99,"method":"item/tool/call","params":{"threadId":"thread-fixture","tool":"polyinference_tool","callId":"tool-fixture","arguments":{"tool":"files.list","arguments":{}}}})
  reply=json.loads(sys.stdin.readline());assert reply["id"]==99 and reply["result"]["success"]
  send({"method":"turn/completed","params":{"turn":{"id":"turn-fixture","status":"completed","items":[]}}})
''')
    return script


async def test_noisy_native_job_keeps_reply_usage_and_callbacks(noisy_server, tmp_path):
    adapter = CodexAppServer(Endpoint(
        protocol="codex_app_server", model="fixture",
        command=[sys.executable, str(noisy_server), "success"], timeout_seconds=10,
    ))
    calls = []

    async def callback(call_id, arguments):
        calls.append((call_id, arguments))
        return {"paths": []}

    result = await adapter.generate_job([], tmp_path, {"type": "object"}, callback, tools=[{
        "name": "files.list", "input_schema": {"type": "object", "properties": {}},
    }])
    assert json.loads(result["text"]) == {"complete": True}
    assert result["usage"]["total_tokens"] == 17
    assert calls == [("tool-fixture", {"tool": "files.list", "arguments": {}})]
    diagnostics = result["event_diagnostics"]
    assert diagnostics["received_events"] > 4000
    assert diagnostics["received_bytes"] > 4 * 1024 * 1024
    assert diagnostics["retained_bytes"] <= diagnostics["byte_limit"]
    assert len(result["events"]) <= diagnostics["event_limit"]
    assert diagnostics["dropped_events"] >= 2100
    assert not any(e["method"].endswith("/delta") for e in result["events"])
    assert not any(e["method"] == "thread/tokenUsage/updated" for e in result["events"])
    assert result["events"][-1]["method"] == "turn/completed"


@pytest.mark.parametrize("mode,error", [("disconnect", UnknownExecution), ("failed", NativeJobStopped)])
async def test_native_failures_keep_bounded_payload_free_diagnostics(noisy_server, tmp_path, mode, error):
    adapter = CodexAppServer(Endpoint(
        protocol="codex_app_server", model="fixture",
        command=[sys.executable, str(noisy_server), mode], timeout_seconds=10,
    ))
    with pytest.raises(error) as caught:
        await adapter.generate_job([], tmp_path, {"type": "object"})
    diagnostics = caught.value.native_diagnostics
    assert diagnostics["received_events"] >= 2100
    assert diagnostics["received_bytes"] > 4 * 1024 * 1024
    assert len(diagnostics["recent_events"]) <= 24
    assert diagnostics["dropped_events"] >= 2100
    assert "private-text" not in json.dumps(diagnostics)
    assert len(json.dumps(diagnostics)) < 12000


def test_native_event_retention_is_bounded_by_bytes_and_method_cardinality():
    events = NativeEventLog(byte_limit=200, event_limit=3)
    for index in range(100):
        events.record({"method": f"notification/{index}", "params": {"data": "x" * 100}}, 150)
    assert len(events.snapshot()) == 1
    assert events.diagnostics()["retained_bytes"] == 150
    assert events.diagnostics()["dropped_events"] == 99
    assert len(events.diagnostics()["methods"]) <= 33
    events.record({"method": "oversized", "params": {}}, 201)
    assert events.diagnostics()["retained_bytes"] == 150


@pytest.mark.parametrize("permissions", [
    {},
    {"sandbox": {"type": "workspaceWrite"}, "approvalPolicy": "never"},
    {"sandbox": {"type": "readOnly", "networkAccess": True}, "approvalPolicy": "never"},
    {"sandbox": {"type": "readOnly"}, "approvalPolicy": "onRequest"},
])
async def test_native_job_rejects_unconfirmed_permissions_before_starting_a_turn(tmp_path, permissions):
    script = tmp_path / "permission_server.py"
    script.write_text('''import json,sys
permissions=json.loads(sys.argv[1])
for line in sys.stdin:
 message=json.loads(line);method=message.get("method")
 if method=="turn/start":raise AssertionError("A model turn must not start")
 if method=="initialize":result={}
 elif method=="thread/start":result={"thread":{"id":"permission-test"},**permissions}
 else:continue
 print(json.dumps({"id":message["id"],"result":result}),flush=True)
''')
    endpoint = Endpoint(model="fixture", protocol="codex_app_server",
                        command=[sys.executable, str(script), json.dumps(permissions)], timeout_seconds=5)
    with pytest.raises(NativeJobStopped, match="did not confirm read-only"):
        await CodexAppServer(endpoint).generate_job([], tmp_path, {"type": "object"})
