from __future__ import annotations

import asyncio
import base64
import hashlib
import json

from polyinference.runtime.exclusive import Exclusive
from polyinference.runtime.inference import Admission
from polyinference.runtime.storage import Records
from polyinference.ui import TestUI
from polyinference.ui_os import activity, artifact_references, export_artifacts, read_snapshot, runtime_view


async def test_admission_history_tracks_wait_hold_and_cancellation(tmp_path):
    records = Records(tmp_path / "records.sqlite")
    admission = Admission(1, 100, records)
    entered = asyncio.Event()

    async def waiter():
        async with admission.reserve(30, finishing=True, operation_id="second", process_id="p2"):
            entered.set()

    try:
        async with admission.reserve(20, operation_id="first", process_id="p1"):
            task = asyncio.create_task(waiter())
            for _ in range(100):
                if records.get("reservation/local/second"):
                    break
                await asyncio.sleep(0)
            snapshot = read_snapshot(tmp_path)
            view = runtime_view(snapshot, {"local": {"max_inflight": 1, "reserved_context_tokens": 100}})
            assert view["lanes"][0]["held"] == 1
            assert view["lanes"][0]["finishing_waiters"] == 1
            assert snapshot["records"]["reservation/local/second"]["process_id"] == "p2"
            assert not entered.is_set()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        reservation = records.get("reservation/local/first")[1]
        assert reservation["queued_at"] <= reservation["admitted_at"] <= reservation["released_at"]
        assert records.get("reservation/local/second")[1]["state"] == "withdrawn"
        transitions = [row["state"] for row in activity(read_snapshot(tmp_path)["events"], {})
                       if row["key"] == "reservation/local/first"]
        assert transitions == ["waiting", "held", "released"]
    finally:
        records.db.close()


async def test_exclusive_wait_history_and_atomic_ownership(tmp_path):
    records = Records(tmp_path / "records.sqlite")
    exclusive = Exclusive(records)
    try:
        first = await exclusive.acquire("verification/project", "p1")
        second = asyncio.create_task(exclusive.acquire("verification/project", "p2"))
        await asyncio.sleep(0)
        waiting = runtime_view(read_snapshot(tmp_path), {})["ownership_waits"]
        assert any(row["process_id"] == "p2" and row["state"] == "waiting" for row in waiting)
        await exclusive.release(first, "p1")
        permit = await asyncio.wait_for(second, 2)
        await exclusive.release(permit, "p2")
        history = activity(read_snapshot(tmp_path)["events"], {})
        owners = [row["value"]["process_id"] for row in history if row["key"] == "permit/verification/project"]
        assert owners == ["p1", None, "p2", None]
        retained = records.get("permit/verification/project")[1]
        assert retained["acquired_at"] <= retained["released_at"]
        assert all(row["at"] for row in history)
    finally:
        records.db.close()


async def test_os_view_refreshes_without_checkpoint_changes(tmp_path):
    state = tmp_path / "run" / "state"
    state.mkdir(parents=True)
    records = Records(state / "records.sqlite")
    manager = TestUI(tmp_path / "ui")
    manager.runs["fixture"] = {"id": "fixture", "state": str(state), "created_at": "", "error": None}
    try:
        before = await manager.view("fixture")
        assert not before["os"]["critical_sections"]
        records.compare_and_publish({"permit/verification/project": 0}, {
            "permit/verification/project": {"resource": "verification/project", "process_id": "p1"},
        })
        after = await manager.view("fixture")
        assert before["processes"] == after["processes"] == []
        assert after["os"]["critical_sections"][0]["process_id"] == "p1"
    finally:
        records.db.close()


def test_legacy_and_pruned_journal_are_explicit(tmp_path):
    records = Records(tmp_path / "records.sqlite")
    try:
        records.db.execute("INSERT INTO events(sequence,body) VALUES (?,?)", (
            125, json.dumps({"changes": {"process/p1": {"revision": 2, "state": "ready"}}, "immutable": []}),
        ))
        view = runtime_view(read_snapshot(tmp_path), {})
        assert view["journal"]["pruned_events"] == 124
        assert view["journal"]["legacy_events"] == 1
        assert view["activity"][0]["at"] is None
        assert view["activity"][0]["value"] is None
        assert read_snapshot(tmp_path / "missing")["records"] == {}
    finally:
        records.db.close()


def test_artifact_export_keeps_exact_binary_bytes_and_reports_corruption(tmp_path):
    root = tmp_path / "artifacts"
    root.mkdir()
    content = b"\x00\xffbinary artifact\n"
    name = hashlib.sha256(content).hexdigest()
    (root / name).write_bytes(content)
    (root / ("0" * 64)).write_bytes(b"corrupt")
    (root / "unfinished.partial").write_bytes(b"not published")
    rows = export_artifacts(tmp_path)
    assert len(rows) == 2
    assert "error" in next(row for row in rows if row["digest"] == "sha256:" + "0" * 64)
    exported = next(row for row in rows if row["digest"] == "sha256:" + name)
    assert base64.b64decode(exported["data"]) == content


def test_restart_does_not_reanimate_queued_reservations(tmp_path):
    records = Records(tmp_path / "records.sqlite")
    try:
        records.compare_and_publish({"reservation/local/pending": 0}, {
            "reservation/local/pending": {"operation_id": "pending", "state": "waiting", "tokens": 20},
        })
        admission = Admission(1, 100, records)
        admission.restore()
        assert admission.active == 0
        assert records.get("reservation/local/pending")[1]["state"] == "interrupted"
    finally:
        records.db.close()


def test_export_reports_missing_referenced_artifacts(tmp_path):
    ref = {"artifact_id": "sha256:" + "a" * 64, "digest": "sha256:" + "a" * 64}
    references = artifact_references({"nested": [ref, {"digest": "sha256:" + "b" * 64}]})
    rows = export_artifacts(tmp_path, references)
    assert len(rows) == 1 and rows[0]["digest"] == ref["digest"]
    assert "error" in rows[0] and "data" not in rows[0]


async def test_completion_during_snapshot_does_not_look_like_interruption(tmp_path, monkeypatch):
    import polyinference.ui as ui

    state = tmp_path / "state"
    state.mkdir()
    records = Records(state / "records.sqlite")
    records.compare_and_publish({"app/run": 0}, {"app/run": {"status": "active"}})
    manager = TestUI(tmp_path / "ui")
    manager.runs["fixture"] = {"id": "fixture", "state": str(state), "created_at": "", "error": None}
    manager.active = "fixture"

    def finish_during_read(path):
        snapshot = read_snapshot(path)
        if manager.active:
            records.compare_and_publish({"app/run": 1}, {"app/run": {"status": "completed"}})
            manager.active = None
        return snapshot

    monkeypatch.setattr(ui, "read_snapshot", finish_during_read)
    try:
        assert (await manager.view("fixture"))["status"] == "running"
        assert (await manager.view("fixture"))["status"] == "completed"
    finally:
        records.db.close()
