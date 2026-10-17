"""Bounded foreground scripts sharing the installation shell gate with checks."""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
from pathlib import Path


def restore(workspaces, root, before):
    # root is host-issued and always lives inside this run's private workspace tree.
    assert root.resolve().is_relative_to(workspaces.root.resolve())
    for entry in root.iterdir():
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()
    workspaces.materialize(root, before)


async def run(tools, manifest, arguments):
    if tools.config.shell_execution == "disabled":
        raise ValueError("Shell execution is disabled")
    script = arguments.get("script")
    if not isinstance(script, str) or not script.strip() or len(script) > 16000:
        raise ValueError("Supply a shell script of 1-16000 characters")
    timeout = arguments.get("timeout_seconds") or 60
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 600:
        raise ValueError("Shell timeout must be between 0 and 600 seconds")
    root = tools.workspaces.root_for(manifest)
    cwd = (root / (arguments.get("cwd") or ".")).resolve()
    if not cwd.is_relative_to(root.resolve()) or not cwd.is_dir():
        raise ValueError("Shell cwd must be an existing directory inside the workspace")
    before = tools.workspaces.scan(root)
    argv = ["bash", "-c", script]
    if tools.config.shell_execution == "bubblewrap":
        if not shutil.which("bwrap"):
            raise ValueError("bubblewrap requested but unavailable")
        prefix = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session"]
        for system in ("/usr", "/bin", "/lib", "/lib64", "/etc"):
            if Path(system).exists():
                prefix += ["--ro-bind", system, system]
        argv = prefix + [
            "--bind",
            str(root),
            "/workspace",
            "--chdir",
            "/workspace/" + cwd.relative_to(root.resolve()).as_posix(),
            "--tmpfs",
            "/tmp",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--",
            *argv,
        ]
    permit = await tools.exclusive.acquire("shell/installation", manifest.process_id)
    process = None
    output = bytearray()
    truncated = False
    timed_out = False
    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
            env={
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(root),
                "LANG": "C.UTF-8",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTEST_ADDOPTS": "-p no:cacheprovider",
            },
        )

        async def drain():
            nonlocal truncated
            while chunk := await process.stdout.read(8192):
                remaining = max(0, tools.config.limits.max_output_bytes - len(output))
                output.extend(chunk[:remaining])
                truncated |= len(chunk) > remaining
            await process.wait()

        try:
            await asyncio.wait_for(drain(), timeout)
        except asyncio.TimeoutError:
            timed_out = True
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await process.wait()
        try:
            after = tools.workspaces.scan(root)
            changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
            if not changed <= set(manifest.allowed_write_paths):
                tools.workspaces.extend_setup_scope(manifest.workspace_id, sorted(changed))
        except Exception:
            restore(tools.workspaces, root, before)
            raise
        return {
            "stdout": output.decode(errors="replace"),
            "exit_code": process.returncode,
            "timed_out": timed_out,
            "truncated": truncated,
            "changed": bool(changed),
            "changed_paths": sorted(changed),
            "cwd": cwd.relative_to(root.resolve()).as_posix(),
        }
    finally:
        if process is not None and process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await process.wait()
        await tools.exclusive.release(permit, manifest.process_id)
