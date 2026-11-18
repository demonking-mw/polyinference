"""Loopback workspace integration using the real OS journal and scripted inference."""

import asyncio
import json
import sys
import threading
from contextlib import contextmanager

import httpx
import pytest

from polyinference.agent.system_settings import codex_subscription_endpoint
from polyinference.config import Endpoint, RuntimeConfig
from polyinference.contracts import DataPolicy
from polyinference.runtime.codex import CodexAppServer
from polyinference.runtime.inference import HTTPInference
from polyinference.runtime.storage import Records
from polyinference.ui import make_server
from polyinference.ui_workspace import Workspace


def config_for(tmp_path):
    return RuntimeConfig(
        repository=str(tmp_path / "unused"),
        state_directory=str(tmp_path / "workspace"),
        local=Endpoint(model="on-device", inference_location="local", base_url="http://fixture.local/v1"),
        cloud=Endpoint(model="hosted", inference_location="cloud", base_url="http://fixture.cloud/v1"),
        role_bindings={"general": "cloud", "local": "local", "cloud": "cloud"},
        prepare_repository=False,
        checks=[],
        allowed_write_paths=[],
    )


@contextmanager
def server_for(workspace):
    with make_server(None, 0, workspace=workspace) as server:
        driver = threading.Thread(target=server.serve_forever, daemon=True)
        driver.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            with httpx.Client(base_url=origin, timeout=5, trust_env=False) as client:
                yield client, origin
        finally:
            server.shutdown()
            driver.join()


def payload(digit, agent="simple", models=None, **updates):
    return {"id": digit * 32, "agent": agent, "models": models or {"general": "local"},
            "text": "Summarize the notes", **updates}


def join(workspace):
    workspace.worker.join(timeout=8)
    assert not workspace.worker.is_alive()


def test_workspace_http_launch_model_selection_monitors_and_restart(tmp_path, monkeypatch):
    requested = []
    entered = threading.Event()
    release = threading.Event()
    replies = iter(['{"final":"local answer"}', '{"final":"cloud answer"}',
                    '{"tasks":["extract"]}', "local finding", "combined answer"])

    async def generate(self, messages, max_output, response_schema=None, **kwargs):
        requested.append((self.endpoint.model, messages))
        if len(requested) == 1:
            entered.set()
            assert await asyncio.to_thread(release.wait, 5)
        return {"text": next(replies), "model": self.endpoint.model + "-revision", "usage": {"total_tokens": 5}}

    monkeypatch.setattr(HTTPInference, "generate", generate)
    config = config_for(tmp_path)
    workspace = Workspace(config)
    try:
        with server_for(workspace) as (client, origin):
            headers = {"Origin": origin}
            assert "Agent Monitoring" in client.get("/").text
            assert client.get("/ui-workspace.css").is_success
            assert client.get("/ui-workspace.js").is_success
            index = client.get("/api/workspace").json()
            assert [agent["id"] for agent in index["agents"]] == ["simple", "supervisor", "research", "writer"]
            assert index["scheduler_available"] is False
            system = client.get("/api/workspace/os").json()
            assert system["active"] is None and system["invocations"] == 0
            limits = {"local": config.local.max_inflight, "cloud": config.cloud.max_inflight}
            assert {lane["name"]: lane["limit"] for lane in system["lanes"]} == limits
            send = "/api/workspace/send"
            assert client.post(send, json=payload("a")).status_code == 403
            first = client.post(send, json=payload("a"), headers=headers)
            assert first.status_code == 202
            assert entered.wait(5)
            assert client.post(send, json=payload("a"), headers=headers).json() == first.json()
            assert client.post(send, json=payload("a", text="different"), headers=headers).status_code == 400
            assert client.post(send, json=payload("b"), headers=headers).status_code == 400
            view = client.get("/api/workspace/invocation", params=first.json()).json()
            assert view["live"] and view["observed"]
            assert any(row["status"] == "Running" for row in view["processes"])
            assert any(row["held"] == 1 for row in view["lanes"])
            system = client.get("/api/workspace/os").json()
            assert system["active"] == first.json()["id"]
            assert system["process_counts"]["Running"] == 1
            assert next(lane for lane in system["lanes"] if lane["name"] == "local")["held"] == 1
            release.set()
            join(workspace)

            chat_id = first.json()["chat_id"]
            second = payload("b", models={"general": "cloud"}, chat_id=chat_id, include_previous=True)
            assert client.post(send, json=second, headers=headers).status_code == 202
            join(workspace)
            invalid = payload("c", agent="supervisor", models={"local": "cloud", "cloud": "cloud"})
            assert client.post(send, json=invalid, headers=headers).status_code == 400
            mixed = payload("c", agent="supervisor", models={"local": "local", "cloud": "cloud"})
            assert client.post(send, json=mixed, headers=headers).status_code == 202
            join(workspace)
            observed = client.get("/api/workspace/invocation", params={"id": mixed["id"]}).json()
            assert len(observed["processes"]) == 3
            assert all(row["status"] == "Finished" and row["reason"] == "Succeeded" for row in observed["processes"])
            assert {row["model"] for row in observed["processes"]} == {"on-device", "hosted"}
            assert {row["attempts"][0]["model"] for row in observed["processes"]} == {
                "on-device-revision", "hosted-revision",
            }
            assert [model for model, _ in requested] == ["on-device", "hosted", "hosted", "on-device", "hosted"]
            system = client.get("/api/workspace/os").json()
            assert system["active"] is None and system["invocations"] == system["journals"] == 3
            assert system["process_counts"] == {"Finished": 5}
            assert system["effect_counts"] == {"succeeded": 5}
            assert {lane["name"]: lane["reported_tokens"] for lane in system["lanes"]} == {"local": 10, "cloud": 15}
            assert all(lane["held"] == lane["retained_held"] == 0 and lane["limit"] == limits[lane["name"]]
                       for lane in system["lanes"])
            assert "local answer" in json.dumps(requested[1][1])
            assert not (tmp_path / "unused").exists()
    finally:
        release.set()
        workspace.close()
    restored = Workspace(config)
    try:
        assert [row["answer"] for row in restored.chat(chat_id)] == ["local answer", "cloud answer"]
        assert restored.start(second)["chat_id"] == chat_id
        assert len(requested) == 5
    finally:
        restored.close()


def test_workspace_authority_and_unconfirmed_restart(tmp_path):
    config = config_for(tmp_path).model_copy(update={"data_policy": DataPolicy(
        policy_ref="grant/test", allowed_inference_locations=["local"],
        allowed_destination_classes=["local"], maximum_classification="project",
    )})
    observed = threading.Event()

    async def uncertain(_agent, effective, _task, _documents):
        effective.state_path.mkdir(parents=True)
        records = Records(effective.state_path / "records.sqlite")
        try:
            records.put_once("effect/lost", {"state": "active", "request": {
                "operation_id": "lost", "scope": {"process_id": "p"},
            }})
            records.put_once("reservation/local/lost", {"state": "held", "process_id": "p", "tokens": 48})
            observed.set()
        finally:
            records.db.close()
        raise RuntimeError("Lost delivery")

    workspace = Workspace(config, runner=uncertain)
    try:
        assert workspace.catalog()[0]["fields"][0]["default"] == "local"
        with pytest.raises(ValueError, match="data policy"):
            workspace.start(payload("a", models={"general": "cloud"}))
        accepted = workspace.start(payload("a"))
        assert observed.wait(5)
        join(workspace)
        assert workspace.index()["blocked"] == accepted["id"]
        system = workspace.inspect_os()
        local = next(lane for lane in system["lanes"] if lane["name"] == "local")
        assert local["held"] == local["reserved_tokens"] == 0
        assert local["retained_held"] == 1
        assert system["holds"] == [{"id": "reservation/local/lost", "process_id": "p", "tokens": 48,
                                      "binding": "local", "run_id": accepted["id"], "live": False}]
        assert system["effect_counts"] == {"Unconfirmed": 1}
    finally:
        workspace.close()
    restored = Workspace(config, runner=uncertain)
    try:
        with pytest.raises(ValueError, match="unresolved effect"):
            restored.start(payload("b"))
        assert restored.start(payload("a")) == accepted
        assert not (config.state_path / "invocations" / ("b" * 32)).exists()
    finally:
        restored.close()


def test_workspace_haiku_simulation_preserves_cloud_placement(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-key")
    cloud_replies = iter(['{"questions":["What do the notes say?"]}', "combined answer"])
    submitted = []

    async def handle_request(_transport, request):
        body = json.loads(request.content)
        submitted.append(body["model"])
        if request.url.host == "fixture.cloud":
            assert body["temperature"] == 0
            if len(submitted) == 3:
                assert "local evidence" in body["messages"][-1]["content"]
            return httpx.Response(200, json={"model": "hosted", "choices": [
                {"message": {"content": next(cloud_replies)}, "finish_reason": "stop"},
            ]})

        assert request.method == "POST"
        assert str(request.url) == "https://api.anthropic.com/v1/messages"
        assert request.headers["x-api-key"] == "fixture-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        assert request.headers["content-type"] == "application/json"
        assert set(body) == {"model", "system", "messages", "max_tokens", "stream"}
        assert body["model"] == "claude-haiku-5-5"
        assert body["system"].startswith("Follow the application prompt.")
        assert [message["role"] for message in body["messages"]] == ["user"]
        assert "What do the notes say?" in body["messages"][-1]["content"]
        assert body["max_tokens"] == 32000
        assert body["stream"] is True
        events = [
            {"type": "message_start", "message": {"id": "msg-fixture", "model": body["model"],
                                                 "content": [], "usage": {"input_tokens": 3}}},
            {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": ""}},
            {"type": "content_block_delta", "index": 0, "delta": {"type": "signature_delta", "signature": "fixture"}},
            {"type": "content_block_stop", "index": 0},
            {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}},
            {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "local evidence"}},
            {"type": "content_block_stop", "index": 1},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 2}},
            {"type": "message_stop"},
        ]
        stream = "".join(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events)
        return httpx.Response(200, content=stream, headers={"content-type": "text/event-stream"})

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handle_request)
    config = config_for(tmp_path)
    workspace = Workspace(config, sim_haiku=True)
    try:
        local = next(lane for lane in workspace.inspect_os()["lanes"] if lane["name"] == "local")
        assert local["limit"] == 2
        assert local["token_limit"] == 256000
        mixed = payload("a", agent="research", models={"local": "local", "cloud": "cloud"})
        accepted = workspace.start(mixed)
        join(workspace)
        record = workspace.chat(accepted["chat_id"])[0]
        assert record["answer"] == "combined answer"
        assert record["models"]["local"]["simulated_local"]
        assert record["models"]["local"]["location"] == "cloud"
        inspection = workspace.inspect(accepted["id"])
        worker = next(row for row in inspection["processes"] if row["role"] == "local" and row["attempts"])
        assert worker["binding"] == "local"
        assert worker["attempts"][0]["location"] == "cloud"
        assert submitted == ["hosted", "claude-haiku-5-5", "hosted"]
    finally:
        workspace.close()

    restricted = config.model_copy(update={
        "state_directory": str(tmp_path / "restricted"),
        "data_policy": DataPolicy(policy_ref="grant/test", allowed_inference_locations=["local"],
                                  allowed_destination_classes=["local"], maximum_classification="project"),
    })
    workspace = Workspace(restricted, sim_haiku=True)
    try:
        with pytest.raises(ValueError, match="data policy"):
            workspace.start(payload("b"))
        assert not workspace.runs
    finally:
        workspace.close()


@pytest.mark.parametrize(("variant", "native_texts", "raw_texts"), [
    ("simple", ['{"final":"final answer"}'], []),
    ("supervisor", ['{"tasks":["step"]}', "final answer"], ["local result"]),
    ("research", ['{"questions":["fact"]}', "final answer"], ["local result"]),
    ("writer", ['{"criteria":["clear"]}', '{"approved":true,"feedback":""}'], ["final answer"]),
])
def test_workspace_all_agents_use_native_codex_for_cloud(tmp_path, monkeypatch, variant, native_texts, raw_texts):
    cloud = codex_subscription_endpoint().model_copy(update={"command": [sys.executable]})
    config = config_for(tmp_path).model_copy(update={"cloud": cloud})
    native_replies, raw_replies = iter(native_texts), iter(raw_texts)
    dispatched = []

    async def generate_job(self, messages, snapshot, schema, **options):
        assert self.endpoint.model == "gpt-6.1-sol"
        assert schema["properties"]["text"]["type"] == "string"
        assert options["require_subscription"] is True
        assert options["tools"] == [] and options["session_ref"] is None
        assert not list(snapshot.iterdir())
        dispatched.append("agent_job")
        return {"text": json.dumps({"text": next(native_replies)}), "model": self.endpoint.model,
                "session_id": "fixture-session", "usage": {"total_tokens": 5}}

    async def generate(self, *_args, **_kwargs):
        assert self.endpoint.inference_location == "local"
        dispatched.append("model_query")
        return {"text": next(raw_replies), "model": self.endpoint.model, "usage": {"total_tokens": 5}}

    monkeypatch.setattr(CodexAppServer, "generate_job", generate_job)
    monkeypatch.setattr(HTTPInference, "generate", generate)
    workspace = Workspace(config)
    try:
        bindings = {"general": "cloud"} if variant == "simple" else {"local": "local", "cloud": "cloud"}
        accepted = workspace.start(payload("a", agent=variant, models=bindings, documents={"doc": "fact exists"}))
        join(workspace)
        record = workspace.chat(accepted["chat_id"])[0]
        assert record["status"] == "completed"
        assert record["answer"] == "final answer"
        cloud_model = record["models"]["general" if variant == "simple" else "cloud"]
        assert cloud_model["subscription"] and cloud_model["model"] == "gpt-6.1-sol"
        inspection = workspace.inspect(accepted["id"])
        cloud_steps = [row for row in inspection["processes"] if row["binding"] == "cloud"]
        assert len(cloud_steps) == len(native_texts) == dispatched.count("agent_job")
        assert dispatched.count("model_query") == len(raw_texts)
        assert all(row["attempts"][0]["kind"] == "agent_job" for row in cloud_steps)
        system = workspace.inspect_os()
        assert next(lane for lane in system["lanes"] if lane["name"] == "cloud")["reported_tokens"] == 5
        assert not (tmp_path / "unused").exists()
    finally:
        workspace.close()
