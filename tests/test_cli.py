from __future__ import annotations

import json
import sys

from polyinference.cli import main
from polyinference.runtime.storage import Records


def test_status_handles_tasks_without_published_reports(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    records = Records(state / "records.sqlite")
    try:
        records.put_once("app/run", {"status": "paused"})
        records.put_once("task/pending", {"execution": "pending", "report_ref": None})
        records.put_once("task/interrupted", {"execution": "interrupted", "report_ref": None})
        records.put_once("task/completed", {"execution": "completed", "report_ref": "report/done"})
        records.put_once("resolution/report/done", {"action": "keep"})
    finally:
        records.db.close()
    monkeypatch.setattr(sys, "argv", ["polyinference", "status", str(state)])
    main()
    report = json.loads(capsys.readouterr().out)
    assert report["run"]["status"] == "paused"
    assert {task["execution"]: task["resolved"] for task in report["tasks"]} == {
        "pending": False,
        "interrupted": False,
        "completed": True,
    }


async def test_export_labels_incomplete_patch(config, tmp_path, monkeypatch, capsys):
    from test_runtime import setup

    runtime, app, _ = await setup(config)
    app.update("app/run", {**app.get("app/run"), "status": "paused", "blocker": "UI remains uncertain"})
    await runtime.close()
    destination = tmp_path / "partial.patch"
    monkeypatch.setattr(sys, "argv", ["polyinference", "export", config.state_directory, str(destination)])
    main()
    assert capsys.readouterr().out.strip() == str(destination)
    metadata = json.loads((tmp_path / "partial.patch.status.json").read_text())
    assert metadata["artifact_status"] == "partial_provisional"
    assert metadata["run_status"] == "paused"
    assert metadata["acceptance_ref"] is None
    assert metadata["blocker"] == "UI remains uncertain"
