import json
import subprocess
import sys

from polyinference.runtime.storage import Records


def test_status_rejects_missing_state_directory(tmp_path):
    missing = tmp_path / "missing"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "polyinference.cli",
            "status",
            str(missing),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert not missing.exists()
    assert "records.sqlite" in result.stderr
    assert "State database not found" in result.stderr


def test_status_rejects_directory_without_database(tmp_path):
    state_dir = tmp_path / "empty-state"
    state_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "polyinference.cli",
            "status",
            str(state_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert not (state_dir / "records.sqlite").exists()
    assert "State database not found" in result.stderr


def test_status_reads_existing_database(tmp_path):
    database_path = tmp_path / "records.sqlite"

    records = Records(database_path)
    records.db.close()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "polyinference.cli",
            "status",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )

    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["run"] is None
    assert report["tasks"] == []
    assert report["uncertain_operations"] == []
