"""Source classification and private, disposable execution state."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..os_config import DEFAULT_TUNING
from ..ports import WriteScopeError as WriteScopeError  # compatibility re-export
from ..primitives import canonical, digest

# Historical import views; runtime callers pass their resolved per-run tuning.
ENVIRONMENT_DIRS = frozenset(DEFAULT_TUNING.environment_directory_names)
DEPENDENCY_FILES = frozenset(DEFAULT_TUNING.dependency_file_names)


def dependency_digest(tree, tuning=DEFAULT_TUNING):
    return digest(canonical({path: digest(data) for path, (_, data) in tree.items()
                             if Path(path).name in tuning.dependency_file_names
                             or Path(path).name.startswith(tuning.dependency_requirements_prefix) and path.endswith(tuning.dependency_requirements_suffix)}))


def environment_dirs(root, protected=(), tuning=DEFAULT_TUNING):
    for directory, names, _ in os.walk(root, followlinks=False):
        for name in list(names):
            path = Path(directory) / name
            if name in tuning.environment_directory_names:
                names.remove(name)
                relative = path.relative_to(root).as_posix()
                if not any(source == relative or source.startswith(relative + "/") for source in protected):
                    yield path
            elif path.is_symlink():
                names.remove(name)


def discard_environment(root, protected=(), tuning=DEFAULT_TUNING):
    for path in environment_dirs(root, protected, tuning):
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


def copy_environment(source, destination, state_root, limit, protected=(), tuning=DEFAULT_TUNING):
    directories = list(environment_dirs(source, protected, tuning))
    if storage_bytes(state_root) + sum(disk_bytes(path) for path in directories) > limit:
        raise RuntimeError("Retained workspace storage budget exceeded")
    discard_environment(destination, protected, tuning)
    for path in directories:
        if path.is_symlink():
            raise ValueError("Execution environment root cannot be a symlink")
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Preserve links (npm executables and venv interpreters), never follow them
        # or share mutable dependency files between retained workspace generations.
        shutil.copytree(path, target, symlinks=True)
