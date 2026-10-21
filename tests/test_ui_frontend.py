"""Regression coverage for the actual browser script, including polling races."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is needed for frontend regression tests")
def test_start_run_feedback_and_selection():
    version = subprocess.check_output([shutil.which("node"), "-p", "process.versions.node"], text=True)
    if int(version.split(".")[0]) < 18:
        pytest.skip("Node.js 18+ is needed for the browser script and built-in test runner")
    result = subprocess.run(
        [shutil.which("node"), "--test", str(Path(__file__).with_name("ui_start.test.cjs"))],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
