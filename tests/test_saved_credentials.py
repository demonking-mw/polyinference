import os
from pathlib import Path

import pytest

from polyinference.cli import load_saved_credentials


@pytest.fixture
def credential_file(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    path = tmp_path / ".config" / "polyinference" / "anthropic.env"
    path.parent.mkdir(parents=True)
    return path


@pytest.mark.parametrize("prefix", ["", "export "])
def test_loads_saved_key(credential_file, prefix):
    credential_file.write_text(f"# private credentials\n{prefix}ANTHROPIC_API_KEY='test-key' # comment\n")
    load_saved_credentials()
    assert os.environ["ANTHROPIC_API_KEY"] == "test-key"


def test_preserves_environment(credential_file, monkeypatch):
    credential_file.write_text("ANTHROPIC_API_KEY=file-key\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "environment-key")
    load_saved_credentials()
    assert os.environ["ANTHROPIC_API_KEY"] == "environment-key"


def test_missing_file_is_optional(credential_file):
    load_saved_credentials()
    assert "ANTHROPIC_API_KEY" not in os.environ


def test_does_not_execute_shell_code(credential_file, tmp_path):
    marker = tmp_path / "executed"
    credential_file.write_text(f"ANTHROPIC_API_KEY='$(touch {marker})'\n")
    load_saved_credentials()
    assert not marker.exists()
    assert os.environ["ANTHROPIC_API_KEY"] == f"$(touch {marker})"


def test_error_does_not_expose_credential(credential_file):
    credential_file.write_text("ANTHROPIC_API_KEY='private-value\n")
    with pytest.raises(ValueError) as error:
        load_saved_credentials()
    assert "private-value" not in str(error.value)
