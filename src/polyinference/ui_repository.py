"""Small filesystem repository picker; all development still uses private copies."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def git(path, *args):
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        timeout=15,
    )
    if result.returncode:
        raise ValueError("Choose a Git repository with a committed HEAD")
    return result.stdout


def repository(path, clean=False):
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Choose a repository root")
    selected = Path(path).expanduser().resolve()
    if not selected.is_dir():
        raise ValueError("Repository directory does not exist")
    root = Path(git(selected, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if selected != root:
        raise ValueError("Select the repository root: " + str(root))
    git(root, "rev-parse", "--verify", "HEAD")
    if clean and git(root, "status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError("Commit or stash changes in the selected repository before running")
    files = []
    for item in git(root, "ls-tree", "-r", "-z", "HEAD").split(b"\0"):
        if not item:
            continue
        metadata, name = item.split(b"\t", 1)
        if metadata.split()[0] in {b"100644", b"100755"}:
            files.append(name.decode())
    if not files:
        raise ValueError("Repository has no committed regular files")
    return root, files


def project(path, clean=False):
    """Inspect a project path without creating it; setup owns folder creation."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Choose a project directory")
    selected = Path(path).expanduser().resolve()
    if not selected.exists():
        return selected, []
    if not selected.is_dir():
        raise ValueError("Project path must be a directory")
    if (selected / ".git").exists():
        head = subprocess.run(
            ["git", "-C", str(selected), "rev-parse", "--verify", "HEAD"], capture_output=True, timeout=15
        )
        if head.returncode == 0:
            try:
                return repository(str(selected), clean)
            except ValueError as exc:
                if "no committed regular files" not in str(exc):
                    raise
                return selected, []
    files = []
    ignored = {".git", ".polyinference", "node_modules", "__pycache__", ".venv", ".venv-linux"}
    for directory, names, filenames in os.walk(selected, followlinks=False):
        names[:] = [
            name for name in names if name not in ignored and not (Path(directory) / name).is_symlink()
        ]
        for name in filenames:
            target = Path(directory) / name
            if target.is_symlink() or name.startswith(".env") or target.suffix in {".pem", ".key"}:
                continue
            files.append(target.relative_to(selected).as_posix())
            if len(files) > 10000:
                raise ValueError("Choose a smaller project directory")
    return selected, sorted(files)


def suggested_check(root, files):
    if "package.json" in files:
        try:
            scripts = json.loads((root / "package.json").read_text()).get("scripts", {})
            if scripts.get("test"):
                return ["npm", "test"]
        except (OSError, ValueError):
            pass
    if any(name.endswith(".py") for name in files):
        return [sys.executable, "-m", "pytest", "-q"]
    return []


def directories(path):
    selected = Path(path).expanduser().resolve()
    if not selected.exists():
        return {
            "path": str(selected), "parent": str(selected.parent), "directories": [],
            "is_repository": True, "exists": False,
        }
    if not selected.is_dir():
        raise ValueError("Directory does not exist")
    children = []
    for child in sorted(selected.iterdir(), key=lambda child: child.name.casefold()):
        if child.name.startswith(".") or child.name in {"node_modules", "__pycache__", "venv"}:
            continue
        try:
            if child.is_dir():
                children.append({"name": child.name, "path": str(child.resolve())})
        except OSError:
            continue
    try:
        root, _ = project(str(selected))
        is_repository = root == selected
    except ValueError:
        is_repository = False
    return {
        "path": str(selected),
        "parent": str(selected.parent),
        "directories": children,
        "is_repository": is_repository,
        "exists": True,
    }
