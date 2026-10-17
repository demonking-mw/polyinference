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
            paths = sorted((await self.workspaces.scan_async(root)))
            limit = min(max(int(arguments.get("limit") or 1000), 1), 1000)
            offset = max(int(arguments.get("offset") or 0), 0)
            return {
                "paths": paths[offset : offset + limit],
                "total": len(paths),
                "offset": offset,
                "truncated": offset + limit < len(paths),
            }
        if tool == "files.search":
            pattern = arguments.get("pattern")
            if not isinstance(pattern, str) or not pattern or len(pattern) > 1000:
                raise ValueError("Search requires a nonempty literal pattern of at most 1000 characters")
            matches, size = [], 0
            for path, (_, content) in (await self.workspaces.scan_async(root)).items():
                if b"\x00" in content:
                    continue
                for line, text in enumerate(content.decode(errors="replace").splitlines(), 1):
                    if pattern in text:
                        match = {"path": path, "line": line, "text": text[:1000]}
                        size += len(canonical(match))
                        if len(matches) >= 100 or size > self.config.limits.max_output_bytes:
                            return {"matches": matches, "truncated": True, "view": manifest.view}
                        matches.append(match)
            return {"matches": matches, "truncated": False, "view": manifest.view}
        path = relative_path(arguments["path"])
        target = root / path
        if not target.resolve().is_relative_to(root.resolve()) or target.is_symlink():
            raise ValueError("Path escapes workspace")
        if tool == "files.read":
            if not target.exists():
                if path in {entry.path for entry in manifest.copied_files}:
                    raise ValueError("File was deleted in this workspace")
                # Bounded closure expansion at pinned B; no write authority expansion.
                base = await self.workspaces.tree(manifest.original_base.commit_id, manifest.process_id)
                if path not in base:
                    raise ValueError("Path does not exist at pinned base")
                if manifest.view != "development":
                    raise ValueError("Unknown path in complete integration tree")
                updated_tree = await self.workspaces.scan_async(root)
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
                await self.workspaces.materialize_async(self.workspaces.root_for(new), updated_tree)
                key = "workspace/" + manifest.workspace_id
                rev = self.workspaces.records.get(key)[0]
                self.workspaces.records.compare_and_publish(
                    {key: rev},
                    {key: new.model_dump(mode="json")},
                    {"manifest/" + new.manifest_id: new.model_dump(mode="json")},
                )
                target = self.workspaces.root_for(new) / path
            data = target.read_bytes()
            cap = min(
                max(int(arguments.get("limit") or self.config.limits.max_output_bytes), 1),
                self.config.limits.max_output_bytes,
            )
            offset = max(int(arguments.get("offset") or 0), 0)
            return {
                "path": path,
                "content": data[offset : offset + cap].decode(errors="replace"),
                "digest": digest(data),
                "truncated": len(data) > offset + cap,
                "offset": offset,
                "next_offset": offset + cap if len(data) > offset + cap else None,
                "generation": self.workspaces.current(manifest.workspace_id).generation,
            }
        if path not in manifest.allowed_write_paths:
            manifest = await self.workspaces.extend_setup_scope(manifest.workspace_id, [path])
            root = self.workspaces.root_for(manifest)
            target = root / path
        existing = target.read_bytes() if target.exists() else None
        if arguments.get("expected_digest") != (digest(existing) if existing is not None else None):
            raise ValueError("Write requires the current file digest (null only for new files)")
        if tool == "files.delete":
            target.unlink()
        elif tool in {"files.write", "files.patch"}:
            if tool == "files.patch":
                old, new = arguments.get("old_text"), arguments.get("new_text")
                if not existing or not isinstance(old, str) or not old or not isinstance(new, str):
                    raise ValueError("Patch requires an existing file and literal old_text/new_text")
                text = existing.decode()
                if text.count(old) != 1:
                    raise ValueError("Patch must match exactly one occurrence")
                data = text.replace(old, new, 1).encode()
            else:
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
        return {
            "path": path,
            "changed": True,
            "digest": digest(target.read_bytes()) if target.exists() else None,
        }

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
