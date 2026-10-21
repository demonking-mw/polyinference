"""Invocation-private tool homes and caches, outside assessed source trees."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


def _prepare(root):
    for name in ("home", "cache", "config", "data", "state", "tmp", "cache/npm", "cache/pip"):
        (root / name).mkdir(parents=True, exist_ok=True, mode=0o700)


@asynccontextmanager
async def tool_environment(workspaces, sandboxed=False):
    temporary = TemporaryDirectory(prefix="tool-environment-", dir=workspaces.config.state_path)
    try:
        await workspaces.blocking.run(_prepare, Path(temporary.name))
        visible = Path("/tool-environment") if sandboxed else Path(temporary.name)
        environment = {
            "PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
            "HOME": str(visible / "home"),
            "XDG_CACHE_HOME": str(visible / "cache"),
            "XDG_CONFIG_HOME": str(visible / "config"),
            "XDG_DATA_HOME": str(visible / "data"),
            "XDG_STATE_HOME": str(visible / "state"),
            "TMPDIR": str(visible / "tmp"), "TMP": str(visible / "tmp"), "TEMP": str(visible / "tmp"),
            "npm_config_cache": str(visible / "cache/npm"),
            "PIP_CACHE_DIR": str(visible / "cache/pip"),
            "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_ADDOPTS": "-p no:cacheprovider",
        }
        mounts = ["--bind", temporary.name, str(visible)] if sandboxed else []
        yield environment, mounts
    finally:
        # Join cleanup before releasing the command's installation-wide lease.
        await workspaces.blocking.run(temporary.cleanup)
