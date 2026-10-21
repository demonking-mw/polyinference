"""Automatic snapshots share UI Save's schema and expire only managed archives."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

from polyinference import cli, history
from polyinference.ui import TestUI


def archive(directory, completed, suffix="fixture"):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (completed.strftime("%Y%m%dT%H%M%S%fZ") + "-" + suffix + ".json")
    path.write_text("{}")
    return path


def test_prune_uses_completion_time_and_keeps_boundary_and_unrelated_files(tmp_path):
    now = datetime(2026, 10, 18, tzinfo=timezone.utc)
    old = archive(tmp_path, now - timedelta(days=30, microseconds=1))
    boundary = archive(tmp_path, now - timedelta(days=30))
    recent = archive(tmp_path, now - timedelta(days=29))
    unrelated = tmp_path / "manual-save.json"
    unrelated.write_text("{}")
    state = tmp_path / "state"
    state.mkdir()
    nested = archive(state, now - timedelta(days=60))
    linked = archive(tmp_path, now - timedelta(days=40), "symlink")
    linked.unlink()
    linked.symlink_to(unrelated)

    history.prune_history(tmp_path, now)

    assert not old.exists()
    assert all(path.exists() for path in (boundary, recent, unrelated, nested, linked))


@pytest.mark.parametrize("outcome", ["completed", "paused", "error", "cancelled"])
async def test_cli_archives_completion_failure_and_resume(config, tmp_path, monkeypatch, outcome):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / ".polyinference" / "history"
    old = archive(directory, datetime.now(timezone.utc) - timedelta(days=31))

    async def run(self):
        self.app.update("app/run", {
            "status": "active" if outcome in {"error", "cancelled"} else outcome,
            "objective": config.objective,
        })
        if outcome == "error":
            raise RuntimeError("provider failed")
        if outcome == "cancelled":
            raise asyncio.CancelledError()

    monkeypatch.setattr(cli.ProjectAgent, "run", run)
    for _ in range(2):
        if outcome in {"error", "cancelled"}:
            exception = RuntimeError if outcome == "error" else asyncio.CancelledError
            with pytest.raises(exception):
                await cli.execute(config)
        else:
            assert (await cli.execute(config))["status"] == outcome

    assert not old.exists()
    paths = list(directory.glob("*.json"))
    assert len(paths) == 2
    documents = [json.loads(path.read_text()) for path in paths]
    assert len({document["run"]["id"] for document in documents}) == 2
    for document in documents:
        assert document["schema_version"] == 2
        assert document["run"]["status"] == ("failed" if outcome in {"error", "cancelled"} else outcome)
        assert document["configuration"] == config.model_dump(mode="json")
        assert document["run_record"]["objective"] == config.objective
        assert document["run"]["created_at"] <= document["run"]["finished_at"]
        if outcome == "error":
            assert document["run"]["error"] == "provider failed"
    assert (config.state_path / "records.sqlite").is_file()


async def test_default_ui_runner_archives_once_and_prunes(config, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / ".polyinference" / "history"
    old = archive(directory, datetime.now(timezone.utc) - timedelta(days=31))

    async def run(self):
        self.app.update("app/run", {"status": "completed"})

    monkeypatch.setattr(cli.ProjectAgent, "run", run)
    path = tmp_path / "config.json"
    path.write_text(config.model_dump_json())
    manager = TestUI(tmp_path / ".polyinference" / "ui", config_path=path)
    run_id = manager.start()
    for _ in range(250):
        if manager.active is None:
            break
        await asyncio.sleep(0.02)
    assert manager.active is None
    assert not old.exists()
    paths = list(directory.glob("*.json"))
    assert len(paths) == 1
    document = json.loads(paths[0].read_text())
    assert document["run"]["id"] == run_id
    assert document["run"]["status"] == "completed"


async def test_archive_failure_still_prunes_and_removes_partial_file(config, tmp_path, monkeypatch, caplog):
    old = archive(tmp_path, datetime.now(timezone.utc) - timedelta(days=31))

    async def unserializable(*args):
        return {"bad": object()}

    monkeypatch.setattr(history, "export_run", unserializable)
    await history.save_run_history(config, tmp_path)
    assert not list(tmp_path.glob("*.json"))
    assert not old.exists()
    assert not list(tmp_path.glob("tmp*"))
    assert "Could not save run history" in caplog.text
