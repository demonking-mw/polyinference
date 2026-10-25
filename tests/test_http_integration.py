"""Actual TCP HTTP -> inference adapter -> graph -> Git -> acceptance."""

from __future__ import annotations

import asyncio
import json
import threading
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.domain import digest
from polyinference.runtime.adapter import StandaloneRuntime


@pytest.mark.parametrize("protocol", ["chat", "anthropic"])
async def test_complete_agent_over_real_http(config, protocol, monkeypatch):
    monkeypatch.setenv("HTTP_FIXTURE_KEY", "fixture-credential")
    counts = defaultdict(int)
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["content-length"])))
            assert self.path == ("/v1/messages" if protocol == "anthropic" else "/v1/chat/completions")
            if protocol == "anthropic":
                assert self.headers["x-api-key"] == "fixture-credential"
                assert self.headers["anthropic-version"] == "2023-06-01"
                assert payload["system"] and all(m["role"] != "system" for m in payload["messages"])
            assert payload["temperature"] == 0
            assert "tools" not in payload
            data = json.loads(
                next(
                    m["content"] for m in payload["messages"] if "Pinned application inputs:" in m["content"]
                ).split("Pinned application inputs:\n", 1)[1]
            )
            with lock:
                if "assignment" not in data:
                    if not data["all_task_ids"]:
                        reply = {
                            "goal": "TCP test",
                            "tasks": [
                                {
                                    "task_id": "a",
                                    "objective": "Change a.py",
                                    "write_paths": ["a.py"],
                                    "read_paths": ["a.py"],
                                    "checks": ["syntax"],
                                }
                            ],
                        }
                    else:
                        reply = {
                            "goal": "Done",
                            "complete": True,
                            "memory_update": "The value was updated and reviewed.",
                            "dispositions": [
                                {"report_ref": r["record_id"], "action": "keep", "reason": "Reviewed"}
                                for r in data["reports"]
                            ],
                        }
                else:
                    phase = data["phase"]
                    count = counts[phase]
                    counts[phase] += 1
                    if phase == "development" and count == 0:
                        reply = {
                            "kind": "action",
                            "tool": "files.write",
                            "arguments": {
                                "path": "a.py",
                                "content": "VALUE = 2\n",
                                "expected_digest": digest(b"VALUE = 1\n"),
                            },
                        }
                    elif phase == "assessment":
                        reply = {
                            "kind": "assessment",
                            "verdict": "successful",
                            "summary": "TCP fixture checked the exact tree",
                        }
                    else:
                        reply = {"kind": "candidate", "summary": "Ready"}
            response = {
                "id": "http-fixture",
                "model": "http-fixture",
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(reply)}}],
                "usage": {"total_tokens": 25},
            }
            if protocol == "anthropic":
                response = {
                    "id": "msg-fixture",
                    "model": "http-fixture",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": json.dumps(reply)}],
                    "usage": {"input_tokens": 20, "output_tokens": 5},
                }
            body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = config.local.model_copy(
        update={
            "base_url": f"http://127.0.0.1:{server.server_port}/v1",
            "protocol": protocol,
            "api_key_env": "HTTP_FIXTURE_KEY",
        }
    )
    config = config.model_copy(update={"local": endpoint, "cloud": endpoint})
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    try:
        result = await ProjectAgent(app).run()
        assert result["outcome"] == "completed", app.get("app/run")
        assert runtime.records.scan("memory-note/")
        results = [
            value["result"]
            for _, _, value in runtime.records.scan("effect/")
            if value["request"]["payload"]["kind"] == "model_query"
        ]
        assert all(result["usage"][0]["value"] == 25 for result in results)
        memory = app.memory_view()
        assert memory["senior_summary"] == "The value was updated and reviewed."
        assert memory["notes"] == []
        # Immutable original comment remains with the report after memory refinement.
        report = runtime.records.scan("report/")[0][2]
        assert app.read(report["assessment_summary"]) == "TCP fixture checked the exact tree"
    finally:
        await runtime.close()
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)
