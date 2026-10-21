"""Source classification and private, disposable execution state."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..primitives import canonical, digest

ENVIRONMENT_DIRS = {"node_modules", ".venv", ".venv-linux"}
DEPENDENCY_FILES = {"package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock",
                    "pnpm-lock.yaml", "pyproject.toml", "uv.lock", "poetry.lock", "Pipfile.lock"}


class WriteScopeError(ValueError):
    def __init__(self, workspace_id, phase, paths, allowed):
        self.detail = {"code": "write_scope_exceeded", "workspace_id": workspace_id,
                       "phase": phase, "paths": sorted(paths), "allowed_write_paths": sorted(allowed)}
        super().__init__(f"Private changes exceed write scope ({phase}): " + ", ".join(sorted(paths)))


def dependency_digest(tree):
    return digest(canonical({path: digest(data) for path, (_, data) in tree.items()
                             if Path(path).name in DEPENDENCY_FILES
                             or Path(path).name.startswith("requirements") and path.endswith(".txt")}))


def environment_dirs(root, protected=()):
    for directory, names, _ in os.walk(root, followlinks=False):
        for name in list(names):
            path = Path(directory) / name
            if name in ENVIRONMENT_DIRS:
                names.remove(name)
                relative = path.relative_to(root).as_posix()
                if not any(source == relative or source.startswith(relative + "/") for source in protected):
                    yield path
            elif path.is_symlink():
                names.remove(name)


def discard_environment(root, protected=()):
    for path in environment_dirs(root, protected):
        if path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)


def disk_bytes(root):
    total = 0
    for directory, _, files in os.walk(root, followlinks=False):
        for name in files:
            total += (Path(directory) / name).lstat().st_size
    return total


def storage_bytes(state_root):
    return sum(disk_bytes(state_root / name) for name in ("workspaces", "snapshots", "proxy-snapshot", "native"))


def copy_environment(source, destination, state_root, limit, protected=()):
    directories = list(environment_dirs(source, protected))
    if storage_bytes(state_root) + sum(disk_bytes(path) for path in directories) > limit:
        raise RuntimeError("Retained workspace storage budget exceeded")
    discard_environment(destination, protected)
    for path in directories:
        if path.is_symlink():
            raise ValueError("Execution environment root cannot be a symlink")
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Preserve links (npm executables and venv interpreters), never follow them
        # or share mutable dependency files between retained workspace generations.
        shutil.copytree(path, target, symlinks=True)
