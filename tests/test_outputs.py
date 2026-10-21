from __future__ import annotations

import pytest

from polyinference.runtime.kernel import KernelRuntime


def file_artifact(runtime, path, content, mode="100644"):
    return {"path": path, "mode": mode,
            "content": runtime.artifacts.put(content, runtime.scope, "application/octet-stream").model_dump(mode="json")}


async def test_delivery_binary_modes_deletions_and_replay_preserve_later_user_edits(config, tmp_path):
    runtime = await KernelRuntime(config).open()
    root = tmp_path / "delivered"
    root.mkdir()
    obsolete = root / "obsolete.txt"
    obsolete.write_text("old")
    (root / "unrelated.txt").write_text("keep")
    runtime.outputs.prepare(root, {"obsolete.txt": runtime.outputs.fingerprint(obsolete)})
    files = [file_artifact(runtime, "images/raw.bin", b"\0\xff\x01"),
             file_artifact(runtime, "run.sh", b"#!/bin/sh\nexit 0\n", "100755")]
    try:
        result = await runtime.outputs.deliver("release", files)
        assert (root / "images/raw.bin").read_bytes() == b"\0\xff\x01"
        assert (root / "run.sh").stat().st_mode & 0o111
        assert not obsolete.exists()
        assert (root / "unrelated.txt").read_text() == "keep"
        (root / "run.sh").write_text("user edit")
        assert await runtime.outputs.deliver("release", files) == result
        assert (root / "run.sh").read_text() == "user edit"
    finally:
        await runtime.close()


async def test_delivery_conflict_is_detected_before_any_file_is_written(config, tmp_path):
    runtime = await KernelRuntime(config).open()
    root = tmp_path / "delivered"
    root.mkdir()
    (root / "existing.txt").write_text("original")
    runtime.outputs.prepare(root, {"existing.txt": runtime.outputs.fingerprint(root / "existing.txt")})
    files = [file_artifact(runtime, "new.txt", b"new"), file_artifact(runtime, "existing.txt", b"updated")]
    (root / "existing.txt").write_text("user change after start")
    try:
        with pytest.raises(ValueError, match="changed since start"):
            await runtime.outputs.deliver("release", files)
        assert not (root / "new.txt").exists()
        assert (root / "existing.txt").read_text() == "user change after start"
        assert not runtime.records.scan("output-delivery/")
    finally:
        await runtime.close()


async def test_interrupted_delivery_resumes_from_its_own_intent(config, tmp_path, monkeypatch):
    root = tmp_path / "delivered"
    runtime = await KernelRuntime(config).open()
    runtime.outputs.prepare(root, {})
    files = [file_artifact(runtime, "a.txt", b"a"), file_artifact(runtime, "b.txt", b"b")]
    original = runtime.outputs.write_files

    def interrupted(root, baseline, desired):
        original(root, baseline, {"a.txt": desired["a.txt"]})
        raise RuntimeError("simulated host interruption")

    monkeypatch.setattr(runtime.outputs, "write_files", interrupted)
    with pytest.raises(RuntimeError, match="interruption"):
        await runtime.outputs.deliver("release", files)
    assert not runtime.records.scan("output-delivery/")
    await runtime.close()
    runtime = await KernelRuntime(config).open()
    try:
        result = await runtime.outputs.deliver("release", files)
        assert result["file_count"] == 2
        assert (root / "a.txt").read_bytes() == b"a"
        assert (root / "b.txt").read_bytes() == b"b"
    finally:
        await runtime.close()
