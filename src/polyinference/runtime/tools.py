"""Scoped files, configured checks and explicitly enabled foreground scripts."""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
from pathlib import Path

from ..domain import canonical, digest, now
from ..workspace_contracts import relative_path


class Tools:
    def __init__(self, config, workspaces, exclusive, artifacts, scope):
        self.config, self.workspaces, self.exclusive = config, workspaces, exclusive
        self.artifacts, self.scope = artifacts, scope

    async def call(self, payload, arguments):
        manifest = self.workspaces.current(payload.workspace_id)
        if arguments.get("generation") != manifest.generation:
            raise ValueError("Stale workspace generation")
        current = await self.workspaces.revision(manifest.workspace_id)
        if (
            payload.expected_code
            and current.effective_tree_digest != payload.expected_code.effective_tree_digest
        ):
            raise ValueError("Stale workspace content")
        root = self.workspaces.root_for(manifest)
        tool = payload.capability_id
        if tool == "repository.select_branch":
            name = arguments.get("name")
            if not isinstance(name, str) or not name or name.startswith("-"):
                raise ValueError("Supply a valid branch name")
            create = arguments.get("create") or False
            if not isinstance(create, bool):
                raise ValueError("create must be a boolean")
            return await self.workspaces.select_branch(manifest.workspace_id, name, create)
        if tool == "shell.run":
            from .shell import run

            return await run(self, manifest, arguments)
        if tool == "checks.run":
            return await self.check(manifest.workspace_id, arguments["name"])
        if tool == "files.list":
            return {"paths": sorted(self.workspaces.scan(root))}
        path = relative_path(arguments["path"])
        target = root / path
        if not target.resolve().is_relative_to(root.resolve()) or target.is_symlink():
            raise ValueError("Path escapes workspace")
        if tool == "files.read":
            cap = self.config.limits.max_output_bytes
            offset = arguments.get("offset", 0)
            requested = arguments.get("max_bytes", cap)
            if (
                isinstance(offset, bool)
                or not isinstance(offset, int)
                or offset < 0
                or isinstance(requested, bool)
                or not isinstance(requested, int)
                or not 1 <= requested <= cap
            ):
                raise ValueError("Read needs a nonnegative offset and bounded positive max_bytes")
            if not target.exists():
                # Bounded closure expansion at pinned B; no write authority expansion.
                base = await self.workspaces.tree(manifest.original_base.commit_id, manifest.process_id)
                if path not in base:
                    raise ValueError("Path does not exist at pinned base")
                if manifest.view != "development":
                    raise ValueError("Unknown path in complete integration tree")
                updated_tree = self.workspaces.scan(root)
                updated_tree[path] = base[path]
                from ..workspace_contracts import CopiedFile

                generation = manifest.generation + 1
                new = manifest.model_copy(
                    update={
                        "generation": generation,
                        "manifest_id": manifest.workspace_id + ":" + str(generation),
                        "private_root_ref": manifest.workspace_id + ":" + str(generation),
                        "copied_files": [
                            *manifest.copied_files,
                            CopiedFile(
                                path=path,
                                copied_digest=digest(base[path][1]),
                                writable=path in manifest.allowed_write_paths,
                            ),
                        ],
                    }
                )
                self.workspaces.materialize(self.workspaces.root_for(new), updated_tree)
                key = "workspace/" + manifest.workspace_id
                rev = self.workspaces.records.get(key)[0]
                self.workspaces.records.compare_and_publish(
                    {key: rev},
                    {key: new.model_dump(mode="json")},
                    {"manifest/" + new.manifest_id: new.model_dump(mode="json")},
                )
                target = self.workspaces.root_for(new) / path
            data = target.read_bytes()
            excerpt = data[offset : offset + requested]
            return {
                "path": path,
                "content": excerpt.decode(errors="replace"),
                "digest": digest(data),
                "offset": offset,
                "returned_bytes": len(excerpt),
                "total_bytes": len(data),
                "truncated": offset + len(excerpt) < len(data),
                "generation": self.workspaces.current(manifest.workspace_id).generation,
            }
        if path not in manifest.allowed_write_paths:
            manifest = self.workspaces.extend_setup_scope(manifest.workspace_id, [path])
            root = self.workspaces.root_for(manifest)
            target = root / path
        existing = target.read_bytes() if target.exists() else None
        if arguments.get("expected_digest") != (digest(existing) if existing is not None else None):
            raise ValueError("Write requires the current file digest (null only for new files)")
        if tool == "files.delete":
            target.unlink()
        elif tool == "files.write":
            data = arguments["content"].encode()
            if len(data) > self.config.limits.max_output_bytes:
                raise ValueError("File write exceeds output limit")
            if existing is None:
                original = await self.workspaces.tree(manifest.original_base.commit_id, manifest.process_id)
                if path in original and not target.exists():
                    raise ValueError("New destination exists outside scoped copy")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".polyinference-write")
            temporary.write_bytes(data)
            if target.exists():
                temporary.chmod(target.stat().st_mode & 0o777)
            temporary.replace(target)
        else:
            raise ValueError("Unknown capability")
        return {"path": path, "changed": True}

    async def check(self, workspace_id, name):
        manifest = self.workspaces.current(workspace_id)
        check = next((c for c in self.config.checks if c.name == name), None)
        if not check:
            raise ValueError("Only configured check names may execute")
        before = await self.workspaces.revision(workspace_id)
        invocation = self.artifacts.put(canonical(check), self.scope)
        if self.config.check_execution == "disabled":
            content = b"Configured checks are disabled; select a trusted or sandboxed check backend."
            status, exit_code = "unavailable", None
        else:
            argv = list(check.argv)
            root = self.workspaces.root_for(manifest)
            if self.config.check_execution == "bubblewrap":
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
                    "/workspace",
                    "--tmpfs",
                    "/tmp",
                    "--proc",
                    "/proc",
                    "--dev",
                    "/dev",
                    "--",
                    *argv,
                ]
            permit = await self.exclusive.acquire("shell/installation", manifest.process_id)
            proc = None
            try:
                proc = await asyncio.create_subprocess_exec(
                    *argv,
                    cwd=root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    stdin=asyncio.subprocess.DEVNULL,
                    start_new_session=True,
                    env={
                        "PATH": os.environ.get("PATH", ""),
                        "HOME": str(root),
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTEST_ADDOPTS": "-p no:cacheprovider",
                        "LANG": "C.UTF-8",
                    },
                )
                collected = bytearray()
                truncated = False

                async def drain():
                    nonlocal truncated
                    while chunk := await proc.stdout.read(8192):
                        remaining = self.config.limits.max_output_bytes - len(collected)
                        collected.extend(chunk[: max(remaining, 0)])
                        truncated |= len(chunk) > remaining
                    await proc.wait()

                try:
                    await asyncio.wait_for(drain(), check.timeout_seconds)
                    exit_code = proc.returncode
                    status = "passed" if exit_code == 0 else "failed"
                except asyncio.TimeoutError:
                    status, exit_code = "inconclusive", None
                finally:
                    # End the entire foreground process group, including children holding pipes.
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    await proc.wait()
                content = bytes(collected) + (b"\n[output truncated]" if truncated else b"")
            except FileNotFoundError:
                status, exit_code, content = "unavailable", None, b"Configured executable unavailable"
            finally:
                if proc is not None and proc.returncode is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                    await proc.wait()
                await self.exclusive.release(permit, manifest.process_id)
        after = await self.workspaces.revision(workspace_id)
        if after.effective_tree_digest != before.effective_tree_digest:
            status = "inconclusive"
            content += b"\nCheck modified source; evidence invalidated."
        output = self.artifacts.put(content, self.scope, "text/plain")
        return {
            "evidence_id": digest(
                canonical([workspace_id, name, before.model_dump(mode="json"), output.digest])
            ),
            "criterion_ref": name,
            "checked_code": before.model_dump(mode="json"),
            "status": status,
            "exit_code": exit_code,
            "invocation": invocation.model_dump(mode="json"),
            "output": output.model_dump(mode="json"),
            "completed_at": now().isoformat(),
        }
