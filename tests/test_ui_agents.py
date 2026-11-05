"""Agent monitoring retains historical reports and reads only explanatory artifacts."""

from __future__ import annotations

import hashlib

from polyinference.runtime.storage import Records
from polyinference.ui import TestUI
from polyinference.ui_agents import agent_snapshot


def test_monitor_loads_notes_and_review_reasons_without_loading_large_check_outputs():
    note = {"digest": "note"}
    reason = {"digest": "reason"}
    records = {
        "task/done": {"execution": "completed", "report_ref": "report/done"},
        "report/done": {"resolution": "unresolved", "assessment_summary": note,
                        "evidence": [{"output": {"digest": "large-check-output"}}]},
        "resolution/report/done": {"action": "keep", "resolution_ref": "resolution-event/1"},
        "resolution-event/1": {"reason": reason},
        "memory-note/done": {"content": note},
        "effect/model": {"request": {"payload": {"context": "large prompt"}}},
    }
    reads = []

    def read(ref):
        reads.append(ref["digest"])
        return "Explanation " + ref["digest"]

    view = agent_snapshot(records, read)
    assert reads == ["note", "reason"]
    assert "task/done" in view["records"] and "resolution-event/1" in view["records"]
    assert "effect/model" not in view["records"]
    assert view["records"]["report/done"]["resolution"] == "unresolved"
    assert view["texts"]["reason"] == "Explanation reason"


def test_missing_explanation_does_not_hide_task_history_and_long_text_is_bounded():
    def unavailable(ref):
        raise ValueError("Artifact digest mismatch")

    records = {"task/done": {"execution": "completed"},
               "report/done": {"assessment_summary": {"digest": "missing"}},
               "setup/legacy": []}
    view = agent_snapshot(records, unavailable)
    assert view["records"]["task/done"]["execution"] == "completed"
    assert "Artifact unavailable: Artifact digest mismatch" == view["texts"]["missing"]
    long = agent_snapshot(records, lambda ref: "a" * 13000)
    assert len(long["texts"]["missing"]) < 12100
    assert "Preview truncated" in long["texts"]["missing"]


async def test_live_resolution_refreshes_independently_of_graph_checkpoints(tmp_path):
    state = tmp_path / "state"
    records = Records(state / "records.sqlite")
    text = b'"Original explanation retained with the verdict."'
    digest = hashlib.sha256(text).hexdigest()
    (state / "artifacts").mkdir()
    (state / "artifacts" / digest).write_bytes(text)
    ref = {"digest": "sha256:" + digest}
    manager = TestUI(tmp_path / "ui")
    manager.runs["run"] = {"id": "run", "state": str(state), "created_at": "", "error": None}
    try:
        records.put_once("task/done", {
            "assignment": {"task_id": "done", "role": "worker"}, "execution": "completed",
            "report_ref": "report/done",
        })
        records.put_once("report/done", {"assessment_summary": ref, "resolution": "unresolved"})
        before = await manager.view("run")
        records.put_once("resolution/report/done", {"action": "keep", "resolution_ref": "resolution-event/1"})
        records.put_once("resolution-event/1", {"reason": ref, "report_ref": "report/done"})
        after = await manager.view("run")
        assert before["processes"] == after["processes"] == []
        assert "resolution/report/done" not in before["agents"]["records"]
        assert after["agents"]["records"]["resolution/report/done"]["action"] == "keep"
        assert after["agents"]["texts"][ref["digest"]] == text.decode()
        saved = await manager.export("run")
        assert saved["agents"] == after["agents"]
        assert saved["records"]["report/done"]["resolution"] == "unresolved"
    finally:
        records.db.close()
