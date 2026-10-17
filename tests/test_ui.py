"""Real HTTP test runner, checkpoint history and artifact-backed node inspection."""

from __future__ import annotations

import asyncio
import json
import threading

import httpx
import pytest
from conftest import ScriptedAgent

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.ui import TestUI, make_server, read_artifact, read_records


async def fixture_runner(config):
    class ConfiguredScript(ScriptedAgent):
        async def generate(self, *args, **kwargs):
            result = await super().generate(*args, **kwargs)
            reply = json.loads(result["text"])
            for task in reply.get("tasks", []):
                task["checks"] = [config.checks[0].name]
            result["text"] = json.dumps(reply)
            return result

    runtime = await StandaloneRuntime(config).open()
    try:
        for name in runtime.clients:
            await runtime.clients[name].close()
            runtime.clients[name] = ConfiguredScript(two=False)
        return await ProjectAgent(AgentServices(runtime, config)).run()
    finally:
        await runtime.close()


async def finished(client, run_id):
    for _ in range(500):
        response = await client.get("/api/run", params={"id": run_id})
        assert response.status_code == 200, response.text
        value = response.json()
        if value["status"] != "running":
            return value
        await asyncio.sleep(0.02)
    pytest.fail("UI test run did not finish")


async def test_ui_runs_real_agent_and_inspects_actual_nodes_over_http(config, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=fixture_runner)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            page = await client.get("/")
            assert page.status_code == 200 and "Run test" in page.text
            assert "innerHTML" not in page.text  # Prompt/code content is always rendered as text.
            assert (await client.get("/api/runs")).json()["objective"] == config.objective
            response = await client.post("/api/run", json={"objective": "Update a.py"})
            assert response.status_code == 202
            run_id = response.json()["id"]
            view = await finished(client, run_id)
            assert view["status"] == "completed", view
            assert {p["role"] for p in view["processes"]} == {"controller", "senior", "worker"}
            worker = next(p for p in view["processes"] if p["role"] == "worker")
            names = [n["name"] for n in worker["nodes"]]
            assert names[0] == "load" and names[-1] == "release"
            assert names.index("integrate") < names.index("checks") < names.index("publish")
            assert all(node["status"] == "completed" for node in worker["nodes"])
            model = next(n for n in worker["nodes"] if n["name"] == "model")
            data = (await client.get("/api/node", params={"run": run_id, "id": model["id"]})).json()
            operation = data["operations"][0]
            assert operation["prompt"][0]["role"] == "system"
            assert "Pinned application inputs:" in operation["prompt"][1]["content"]
            assert json.loads(operation["response"]["text"])["tool"] == "files.read"
            tool = next(n for n in worker["nodes"] if n["name"] == "tool")
            result = (await client.get("/api/node", params={"run": run_id, "id": tool["id"]})).json()
            assert not result["model_call"]
            assert result["operations"][0]["tool"] == "files.read"
            assert "VALUE = 1" in result["operations"][0]["response"]["content"]
            assert (await client.get("/api/node", params={"run": run_id, "id": "missing"})).status_code == 404

            # A second button press creates new run state; it never replays the completed test.
            second = (await client.post("/api/run", json={})).json()["id"]
            second_view = await finished(client, second)
            assert second != run_id and second_view["state"] != view["state"]
            assert second_view["status"] == "completed"
            assert len((await client.get("/api/runs")).json()["runs"]) == 2
            reloaded = TestUI(tmp_path / "ui", config_path=path)
            assert (await reloaded.view(run_id))["processes"] == view["processes"]
            # All node history is read from persisted records/checkpoints, not UI instrumentation.
            external = TestUI(tmp_path / "external", state=view["state"])
            saved = await external.view(next(iter(external.runs)))
            assert saved["processes"] == view["processes"]
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_ui_rejects_cross_origin_starts_and_unrecognized_hosts(config, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=fixture_runner)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin) as client:
            assert (await client.post("/api/run", json={})).status_code == 403
            assert (
                await client.post("/api/run", json={}, headers={"Origin": "http://unrelated.test"})
            ).status_code == 403
            assert (await client.get("/", headers={"Host": "unrelated.test"})).status_code == 403
            assert (
                await client.post("/api/run", content="{}", headers={"Origin": origin})
            ).status_code == 400
            assert not manager.runs
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_ui_busy_and_failed_runs_remain_inspectable(config, tmp_path):
    release = threading.Event()

    async def failure(_config):
        await asyncio.to_thread(release.wait)
        raise RuntimeError("Fixture provider failed")

    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=failure)
    run_id = manager.start()
    try:
        with pytest.raises(ValueError, match="already running"):
            manager.start()
    finally:
        release.set()
    for _ in range(100):
        if not manager.active:
            break
        await asyncio.sleep(0.02)
    view = await manager.view(run_id)
    assert view["status"] == "failed" and view["error"] == "Fixture provider failed"
    assert view["processes"] == []
    reloaded = TestUI(tmp_path / "ui", config_path=path)
    assert (await reloaded.view(run_id))["error"] == "Fixture provider failed"


def test_ui_reads_only_real_state_and_valid_content_addressed_artifacts(tmp_path):
    assert read_records(tmp_path / "absent") == {}
    assert not (tmp_path / "absent").exists()
    with pytest.raises(ValueError, match="records.sqlite"):
        TestUI(tmp_path / "ui", state=tmp_path)
    with pytest.raises(ValueError, match="Invalid artifact"):
        read_artifact(tmp_path, {"digest": "../../secret"})


async def test_ui_selects_another_repository_and_exports_complete_json(config, tmp_path):
    import shlex
    import subprocess
    from pathlib import Path

    source = tmp_path / "other"
    source.mkdir()
    (source / "a.py").write_text("VALUE = 1\n")
    (source / "b.py").write_text("VALUE = 1\n")
    subprocess.run(["git", "-C", str(source), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@localhost",
            "commit",
            "-qm",
            "other",
        ],
        check=True,
    )

    # No external task config: switching away from the greeting fixture grants the
    # committed files in this chosen root and uses its own configured check.
    manager = TestUI(tmp_path / "ui", runner=fixture_runner)
    base = manager.configuration().model_copy(update={"local": config.local, "cloud": config.cloud})
    manager.configuration = lambda: base
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            listing = (await client.get("/api/directories", params={"path": str(tmp_path)})).json()
            assert any(entry["path"] == str(source) for entry in listing["directories"])
            chosen = (await client.get("/api/repository", params={"path": str(source)})).json()
            assert chosen["repository"] == str(source) and chosen["file_count"] == 2
            assert chosen["clear_objective"]
            response = await client.post(
                "/api/run",
                json={
                    "objective": "Update a.py",
                    "repository": str(source),
                    "check_command": shlex.join(config.checks[0].argv),
                },
            )
            assert response.status_code == 202, response.text
            run_id = response.json()["id"]
            view = await finished(client, run_id)
            assert view["status"] == "completed", view
            assert view["repository"] == str(source)
            saved = json.loads((Path(view["state"]).parent / "config.json").read_text())
            assert saved["repository"] == str(source)
            assert saved["allowed_write_paths"] == ["a.py", "b.py"]
            exported = await client.get("/api/export", params={"id": run_id})
            assert exported.status_code == 200
            assert "attachment" in exported.headers["content-disposition"]
            document = exported.json()
            assert document["schema_version"] == 1 and document["run"]["repository"] == str(source)
            assert document["configuration"]["repository"] == str(source)
            assert document["reports"][0]["verdict"] == "successful"
            model_nodes = [
                node for process in document["processes"] for node in process["nodes"] if node["model_call"]
            ]
            assert model_nodes and model_nodes[0]["operations"][0]["prompt"]
            assert model_nodes[0]["operations"][0]["response"]["text"]
            assert document["effects"] and document["effects"][0]["request"]["operation_id"]
            assert "cost" in document["run"]
            assert (source / "a.py").read_text() == "VALUE = 1\n"
            assert not subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"]).strip()
            (source / "a.py").write_text("VALUE = 99\n")
            refused = await client.post(
                "/api/run",
                json={"objective": "another", "repository": str(source), "check_command": "python -m pytest"},
            )
            assert refused.status_code == 400 and "Commit or stash" in refused.json()["error"]
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_ui_steering_uses_the_same_atomic_capture_as_cli(config, tmp_path):
    from polyinference.cli import record_steering
    from polyinference.runtime.storage import Records

    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    initialized, release = threading.Event(), threading.Event()

    async def waiting(selected):
        runtime = await StandaloneRuntime(selected).open()
        try:
            app = AgentServices(runtime, selected)
            await ProjectAgent(app).initialize()
            run = app.get("app/run")
            app.update("app/run", {**run, "active_workers": ["worker-waiting"], "starts_closed": False})
            initialized.set()
            await asyncio.to_thread(release.wait)
        finally:
            await runtime.close()

    manager = TestUI(tmp_path / "ui", config_path=path, runner=waiting)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            run_id = (await client.post("/api/run", json={})).json()["id"]
            assert await asyncio.to_thread(initialized.wait, 5)
            reply = await client.post("/api/steer", json={"id": run_id, "text": "Keep the public signature."})
            assert reply.status_code == 202 and reply.json()["sequence"] == 1
            state = manager.runs[run_id]["state"]
            records = read_records(state)
            assert records["app/run"]["starts_closed"]
            assert records["app/run"]["captured_workers"] == ["worker-waiting"]
            assert records["steering/00000001"]["text"] == "Keep the public signature."
            assert record_steering(state, "Also update comments.") == 2
            exported = (await client.get("/api/export", params={"id": run_id})).json()
            assert [item["sequence"] for item in exported["steering"]] == [1, 2]
            view = (await client.get("/api/run", params={"id": run_id})).json()
            assert view["steering_received"] == 2 and view["steering_applied"] == 0
            assert (await client.post("/api/steer", json={"id": run_id, "text": "  "})).status_code == 400
            assert (
                await client.post(
                    "/api/steer",
                    json={"id": run_id, "text": "x"},
                    headers={"Origin": "http://unrelated.test"},
                )
            ).status_code == 403
            db = Records(__import__("pathlib").Path(state) / "records.sqlite")
            try:
                rev, run = db.get("app/run")
                db.compare_and_publish({"app/run": rev}, {"app/run": {**run, "status": "completed"}})
            finally:
                db.db.close()
            assert (
                await client.post("/api/steer", json={"id": run_id, "text": "too late"})
            ).status_code == 400
    finally:
        release.set()
        for _ in range(100):
            if not manager.active:
                break
            await asyncio.sleep(0.02)
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


def test_repository_picker_rejects_subdirectories_and_non_repositories(config, tmp_path):
    from polyinference.ui_repository import repository

    with pytest.raises(ValueError, match="Git repository"):
        repository(str(tmp_path))
    subdir = __import__("pathlib").Path(config.repository) / "nested"
    subdir.mkdir()
    with pytest.raises(ValueError, match="repository root"):
        repository(str(subdir))
