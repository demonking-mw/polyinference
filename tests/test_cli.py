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
