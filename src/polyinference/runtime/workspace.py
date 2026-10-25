"""Scoped physical copies and complete integration views over an isolated Git store."""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import signal
import sys
from pathlib import Path

from ..contracts import CodeRevision
from ..domain import canonical, digest
from ..workspace_contracts import CopiedFile, DeltaChange, WorkspaceDelta, WorkspaceManifest, relative_path

IGNORED = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    ".npm",
    ".venv",
    ".venv-linux",
}
ENVIRONMENT = digest(canonical({"adapter": "standalone-1", "tools": "configured-argv-1"}))


class Workspaces:
    def __init__(self, config, records, exclusive, artifacts, scope):
        self.config, self.records, self.exclusive = config, records, exclusive
        self.artifacts, self.scope = artifacts, scope
        self.environment_digest = digest(
            canonical(
                {
                    "adapter": "standalone-1",
                    "checks": [c.model_dump(mode="json") for c in config.checks],
                    "execution": config.check_execution,
                    "shell_execution": config.shell_execution,
                    "python": sys.version,
                    "platform": platform.platform(),
                    "environment_policy": "fixed-during-run",
                }
            )
        )
        self.root = config.state_path / "workspaces"
        self.gitdir = config.state_path / "repository.git"
        self.root.mkdir(parents=True, exist_ok=True)

    async def prepare_snapshot(self, code, snapshot_id):
        tree = await self.tree(code.commit_id, snapshot_id)
        return self._prepare_tree_snapshot(tree, code, snapshot_id)

    async def prepare_workspace_snapshot(self, workspace_id, snapshot_id):
        tree = await self.private_tree(workspace_id)
        return self._prepare_tree_snapshot(tree, self.code(tree), snapshot_id, proxy=False)

    async def private_tree(self, workspace_id):
        return self.scan(self.root_for(self.current(workspace_id)))

    def _prepare_tree_snapshot(self, tree, code, snapshot_id, proxy=True):
        root = self.config.state_path / "snapshots" / snapshot_id
        if root.exists() and self.scan(root) != tree:
            raise ValueError("An immutable native snapshot cannot be replaced")
        self.materialize(root, tree)
        endpoint = getattr(self.config, self.config.role_bindings["senior"])
        proxy_root = None
        if proxy and endpoint.protocol == "codex_proxy":
            expected = (self.config.state_path / "proxy-snapshot").resolve()
            if (
                not endpoint.readonly_snapshot_root
                or Path(endpoint.readonly_snapshot_root).resolve() != expected
            ):
                raise ValueError("Configure the read-only proxy at STATE/proxy-snapshot")
            proxy_root = expected
            if proxy_root.is_symlink():
                raise ValueError("Proxy snapshot cannot be a symlink")
            proxy_root.mkdir(parents=True, exist_ok=True)
            # Preserve the directory inode: the separately launched proxy may use it as CWD.
            self.scan(proxy_root)
            for entry in proxy_root.iterdir():
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
            self.materialize(proxy_root, tree)
        self.records.put_once(
            "snapshot/" + snapshot_id,
            {
                "code": code.model_dump(mode="json"),
                "snapshot_id": snapshot_id,
                "proxy_root": str(proxy_root) if proxy_root else None,
            },
        )
        return snapshot_id

    def snapshot_root(self, snapshot_id):
        retained = self.records.get("snapshot/" + snapshot_id)
        if not retained:
            raise ValueError("Unknown native snapshot")
        if retained[1].get("proxy_root"):
            return Path(retained[1]["proxy_root"])
        return self.config.state_path / "snapshots" / snapshot_id

    async def command(self, args, process_id="runtime", input_data=None, env=None):
        permit = await self.exclusive.acquire("shell/installation", process_id)
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", **(env or {})},
                start_new_session=True,
            )
            output, error = await process.communicate(input_data)
            if process.returncode:
                raise RuntimeError(
                    f"Trusted command failed ({process.returncode}): {error.decode(errors='replace')[:1000]}"
                )
            return output
        finally:
            if process is not None and process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                await process.wait()
            # Trusted Git process groups have ended before ownership is released.
            await self.exclusive.release(permit, process_id)

    async def git(self, *args, process_id="runtime", input_data=None, env=None):
        return await self.command(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "core.autocrlf=false",
                "--git-dir",
                str(self.gitdir),
                *args,
            ],
            process_id,
            input_data,
            env,
        )

    async def initialize(self):
        if not self.gitdir.exists():
            has_head = False
            if (self.config.repo_path / ".git").exists():
                try:
                    await self.command(
                        ["git", "-C", str(self.config.repo_path), "rev-parse", "--verify", "HEAD"]
                    )
                    has_head = True
                except RuntimeError:
                    pass
            if has_head:
                dirty = await self.command(
                    [
                        "git",
                        "-C",
                        str(self.config.repo_path),
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    ]
                )
                if dirty.strip():
                    raise ValueError("Commit or remove dirty/untracked source inputs before starting a run")
                await self.command(
                    [
                        "git",
                        "clone",
                        "--bare",
                        "--no-local",
                        "--no-hardlinks",
                        str(self.config.repo_path),
                        str(self.gitdir),
                    ]
                )
            elif self.config.prepare_repository:
                await self.command(["git", "init", "--bare", "--initial-branch=main", str(self.gitdir)])
                exclusions = [
                    ".git",
                    ".polyinference",
                    "node_modules",
                    ".npm",
                    ".venv",
                    ".venv-linux",
                    "__pycache__",
                ]
                await self.git(
                    "--work-tree",
                    str(self.config.repo_path),
                    "-C",
                    str(self.config.repo_path),
                    "add",
                    "--all",
                    "--",
                    ".",
                    *[":(glob,exclude)**/" + name + "/**" for name in exclusions],
                    ":(glob,exclude)**/.env*",
                    ":(glob,exclude)**/*.pem",
                    ":(glob,exclude)**/*.key",
                )
                tree = (await self.git("write-tree")).decode().strip()
                commit = (
                    (
                        await self.git(
                            "commit-tree",
                            tree,
                            input_data=b"PolyInference initial project baseline\n",
                            env=self.identity(),
                        )
                    )
                    .decode()
                    .strip()
                )
                await self.git("update-ref", "refs/heads/main", commit)
            else:
                raise ValueError(
                    "Repository needs a committed HEAD; enable prepare_repository for initial setup"
                )
        if self.config.base_branch and not self.records.get("repository/setup"):
            await self.git("check-ref-format", "--branch", self.config.base_branch)
            await self.git("rev-parse", "--verify", "refs/heads/" + self.config.base_branch)
            await self.git("symbolic-ref", "HEAD", "refs/heads/" + self.config.base_branch)
        commit = (await self.git("rev-parse", "HEAD")).decode().strip()
        if self.config.prepare_repository and not await self.tree(commit):
            commit = await self.seed_empty_baseline(commit)
        branches = (
            (await self.git("for-each-ref", "--format=%(refname:short)", "refs/heads")).decode().splitlines()
        )
        branch = (await self.git("symbolic-ref", "--short", "HEAD")).decode().strip()
        if not self.records.get("repository/setup"):
            self.records.compare_and_publish(
                {"repository/setup": 0},
                {
                    "repository/setup": {
                        "base_branch": branch,
                        "base_commit": commit,
                        "branches": branches,
                        "git_initialized": not (self.config.repo_path / ".git").exists(),
                        "source_repository": str(self.config.repo_path),
                        "isolated": True,
                    }
                },
            )
        tree = await self.tree(commit)
        return self.code(tree, commit)

    async def seed_empty_baseline(self, commit, process_id="runtime"):
        # The unchanged workspace SDK requires a nonempty dependency closure.
        # A useful ignore file supplies that seed without writing into the source checkout.
        env = {**self.identity(), "GIT_INDEX_FILE": str(self.config.state_path / "baseline.index")}
        content = b".polyinference/\n.env\n.venv/\nnode_modules/\n__pycache__/\n"
        oid = (
            (await self.git("hash-object", "-w", "--stdin", input_data=content, process_id=process_id))
            .decode()
            .strip()
        )
        await self.git("read-tree", "--empty", env=env, process_id=process_id)
        await self.git(
            "update-index",
            "--add",
            "--cacheinfo",
            "100644",
            oid,
            ".gitignore",
            env=env,
            process_id=process_id,
        )
        tree = (await self.git("write-tree", env=env, process_id=process_id)).decode().strip()
        result = (
            (
                await self.git(
                    "commit-tree",
                    tree,
                    "-p",
                    commit,
                    env=env,
                    process_id=process_id,
                    input_data=b"Prepare empty project Git baseline\n",
                )
            )
            .decode()
            .strip()
        )
        await self.git("update-ref", "HEAD", result, process_id=process_id)
        return result

    @staticmethod
    def identity():
        return {
            "GIT_AUTHOR_NAME": "PolyInference",
            "GIT_AUTHOR_EMAIL": "agent@localhost",
            "GIT_COMMITTER_NAME": "PolyInference",
            "GIT_COMMITTER_EMAIL": "agent@localhost",
        }

    async def select_branch(self, workspace_id, name, create=False):
        manifest = self.current(workspace_id)
        spec = self.records.get(manifest.task_spec_ref)
        if not spec or "repository.select_branch" not in spec[1]["allowed_capabilities"]:
            raise ValueError("Branch selection is available only to the initial setup task")
        if manifest.view != "development":
            raise ValueError("Select the base branch before integration")
        retained = self.records.get("branch-selection/" + workspace_id)
        if retained:
            if retained[1]["branch"] != name:
                raise ValueError("The initial branch was already selected")
            return retained[1]
        before = self.scan(self.root_for(manifest))
        if any(
            digest(before[file.path][1]) != file.copied_digest
            for file in manifest.copied_files
            if file.path in before
        ) or set(before) != {file.path for file in manifest.copied_files}:
            raise ValueError("Select the branch before editing files")
        await self.git("check-ref-format", "--branch", name, process_id=manifest.process_id)
        try:
            commit = (
                (
                    await self.git(
                        "rev-parse", "--verify", "refs/heads/" + name, process_id=manifest.process_id
                    )
                )
                .decode()
                .strip()
            )
        except RuntimeError:
            if not create:
                raise ValueError("Requested base branch does not exist: " + name) from None
            commit = manifest.original_base.commit_id
            await self.git("update-ref", "refs/heads/" + name, commit, process_id=manifest.process_id)
        await self.git("symbolic-ref", "HEAD", "refs/heads/" + name, process_id=manifest.process_id)
        tree = await self.tree(commit, manifest.process_id)
        if not tree:
            commit = await self.seed_empty_baseline(commit, manifest.process_id)
            tree = await self.tree(commit, manifest.process_id)
        code = self.code(tree, commit)
        generation = manifest.generation + 1
        allowed = (
            sorted(set(tree) | set(manifest.allowed_write_paths))
            if self.config.write_scope == "project"
            else manifest.allowed_write_paths
        )
        new = manifest.model_copy(
            update={
                "generation": generation,
                "manifest_id": workspace_id + ":" + str(generation),
                "private_root_ref": workspace_id + ":" + str(generation),
                "original_base": code,
                "allowed_write_paths": allowed,
                "copied_files": [
                    CopiedFile(path=p, copied_digest=digest(v[1]), writable=p in allowed)
                    for p, v in sorted(tree.items())
                ],
            }
        )
        self.materialize(self.root_for(new), tree)
        key = "workspace/" + workspace_id
        result = {"branch": name, "code": code.model_dump(mode="json"), "workspace_id": workspace_id}
        self.records.compare_and_publish(
            {key: self.records.get(key)[0]},
            {key: new.model_dump(mode="json")},
            {
                "manifest/" + new.manifest_id: new.model_dump(mode="json"),
                "branch-selection/" + workspace_id: result,
            },
        )
        return result

    def retag_task_spec(self, workspace_id, spec_id, updates, immutable):
        manifest = self.current(workspace_id)
        generation = manifest.generation + 1
        new = manifest.model_copy(
            update={
                "task_spec_ref": spec_id,
                "generation": generation,
                "manifest_id": workspace_id + ":" + str(generation),
                "private_root_ref": workspace_id + ":" + str(generation),
            }
        )
        self.materialize(self.root_for(new), self.scan(self.root_for(manifest)))
        updates = {**updates, "workspace/" + workspace_id: new.model_dump(mode="json")}
        self.records.compare_and_publish(
            {key: self.records.get(key)[0] for key in updates},
            updates,
            {**immutable, "manifest/" + new.manifest_id: new.model_dump(mode="json")},
        )

    def extend_setup_scope(self, workspace_id, paths):
        manifest = self.current(workspace_id)
        spec = self.records.get(manifest.task_spec_ref)
        if not spec or not spec[1].get("extensions", {}).get("polyinference/project-write"):
            raise ValueError("Write outside assigned scope")
        added = sorted(set(paths) - set(manifest.allowed_write_paths))
        if not added:
            return manifest
        generation = manifest.generation + 1
        new = manifest.model_copy(
            update={
                "generation": generation,
                "manifest_id": workspace_id + ":" + str(generation),
                "private_root_ref": workspace_id + ":" + str(generation),
                "allowed_write_paths": sorted(set(manifest.allowed_write_paths) | set(added)),
            }
        )
        self.materialize(self.root_for(new), self.scan(self.root_for(manifest)))
        key = "workspace/" + workspace_id
        self.records.compare_and_publish(
            {key: self.records.get(key)[0]},
            {key: new.model_dump(mode="json")},
            {"manifest/" + new.manifest_id: new.model_dump(mode="json")},
        )
        return new

    async def tree(self, commit, process_id="runtime"):
        listing = await self.git("ls-tree", "-rz", commit, process_id=process_id)
        result = {}
        for item in listing.split(b"\x00"):
            if not item:
                continue
            header, path = item.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            name = path.decode()
            relative_path(name)
            if kind != "blob" or mode not in {"100644", "100755"}:
                raise ValueError("Submodules and symlinks are unsupported workspace inputs")
            size = int((await self.git("cat-file", "-s", oid, process_id=process_id)).decode())
            if size + sum(len(v[1]) for v in result.values()) > self.config.max_workspace_bytes:
                raise RuntimeError("Workspace input exceeds copy budget")
            data = await self.git("cat-file", "blob", oid, process_id=process_id)
            result[name] = (mode, data)
            if sum(len(v[1]) for v in result.values()) > self.config.max_workspace_bytes:
                raise RuntimeError("Workspace copy budget exceeded")
        return result

    def code(self, tree, commit=None):
        identity = [(path, mode, digest(data)) for path, (mode, data) in sorted(tree.items())]
        return CodeRevision(
            repository_id=self.scope.project_id,
            commit_id=commit,
            effective_tree_digest=digest(canonical(identity)),
            environment_digest=self.environment_digest,
            includes_uncommitted_inputs=commit is None,
        )

    def current(self, workspace_id):
        record = self.records.get("workspace/" + workspace_id)
        if not record:
            raise ValueError("Unknown workspace")
        return WorkspaceManifest.model_validate(record[1])

    def root_for(self, manifest):
        # Root references are host-issued IDs, never caller paths.
        return self.root / manifest.workspace_id / str(manifest.generation)

    def scan(self, root):
        tree = {}
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if any(p in IGNORED for p in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError("Workspace symlinks are forbidden")
            if not path.is_file():
                continue
            name = relative.as_posix()
            relative_path(name)
            tree[name] = ("100755" if path.stat().st_mode & 0o111 else "100644", path.read_bytes())
            if sum(len(v[1]) for v in tree.values()) > self.config.max_workspace_bytes:
                raise RuntimeError("Workspace budget exceeded")
        return tree

    async def revision(self, workspace_id):
        manifest = self.current(workspace_id)
        return self.code(self.scan(self.root_for(manifest)))

    def materialize(self, root, tree):
        root.mkdir(parents=True, exist_ok=True)
        for name, (mode, data) in tree.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if mode == "100755" else 0o644)

    async def create(self, workspace_id, process_id, task_ref, base, write_paths, read_paths):
        existing = self.records.get("workspace/" + workspace_id)
        if existing:
            return self.current(workspace_id)
        tree = await self.tree(base.commit_id, process_id)
        paths = set(write_paths + read_paths + self.config.closure_paths)
        scoped = {p: data for p, data in tree.items() if p in paths}
        # An otherwise empty newly initialized project has one host-prepared seed.
        if not scoped and set(tree) == {".gitignore"}:
            scoped = dict(tree)
        # A new-file-only task still needs a pinned read/build closure.
        if not scoped and tree:
            raise ValueError("Assignment must include at least one existing closure file")
        manifest = WorkspaceManifest(
            manifest_id=workspace_id + ":1",
            workspace_id=workspace_id,
            process_id=process_id,
            task_spec_ref=task_ref,
            generation=1,
            view="development",
            materialization="scoped",
            private_root_ref=workspace_id + ":1",
            original_base=base,
            captured_head=None,
            effective_code=None,
            copied_files=[
                CopiedFile(path=p, copied_digest=digest(v[1]), writable=p in write_paths)
                for p, v in sorted(scoped.items())
            ],
            allowed_write_paths=write_paths,
            closure_basis_ref=task_ref,
            preserved_delta_ref=None,
        )
        self.materialize(self.root_for(manifest), scoped)
        self.records.put_once("manifest/" + manifest.manifest_id, manifest.model_dump(mode="json"))
        self.records.compare_and_publish(
            {"workspace/" + workspace_id: 0}, {"workspace/" + workspace_id: manifest.model_dump(mode="json")}
        )
        return manifest

    async def preserve_delta(self, workspace_id):
        manifest = self.current(workspace_id)
        existing = self.records.get("private-delta/" + workspace_id)
        if existing:
            return "private-delta/" + workspace_id
        if manifest.view != "development":
            raise RuntimeError("Only original development view defines the private delta")
        base = await self.tree(manifest.original_base.commit_id, manifest.process_id)
        current = self.scan(self.root_for(manifest))
        copied = {f.path for f in manifest.copied_files}
        changed = {p for p in copied | set(current) if base.get(p) != current.get(p)}
        if not changed <= set(manifest.allowed_write_paths):
            raise ValueError("Private changes exceed write scope")
        changes = []
        modes = {}
        for path in sorted(changed):
            # Absence of an uncopied base path never implies deletion or safe addition.
            if path not in copied and path in base:
                raise ValueError("Add destination exists in original base outside the copy")
            content = current.get(path)
            ref = self.artifacts.put(content[1], self.scope, "application/octet-stream") if content else None
            modes[path] = content[0] if content else None
            changes.append(
                DeltaChange(
                    path=path,
                    expected_base_digest=digest(base[path][1]) if path in base else None,
                    content=ref,
                    action="delete" if not content else "modify" if path in base else "add",
                )
            )
        key = "private-delta/" + workspace_id
        delta = WorkspaceDelta(
            delta_id=key,
            workspace_id=workspace_id,
            development_manifest_ref=manifest.manifest_id,
            original_base=manifest.original_base,
            changes=changes,
        )
        self.records.put_once("delta-modes/" + workspace_id, {"modes": modes})
        self.records.put_once(key, delta.model_dump(mode="json"))
        return key

    async def validate_handoff(self, delta_ref, base, write_paths):
        delta = WorkspaceDelta.model_validate(self.records.get(delta_ref)[1])
        original = await self.tree(delta.original_base.commit_id)
        target = await self.tree(base.commit_id)
        if not {c.path for c in delta.changes} <= set(write_paths):
            raise ValueError("Retained source exceeds replacement write grant")
        for change in delta.changes:
            if original.get(change.path) != target.get(change.path):
                raise ValueError("Retained source conflicts with current base: " + change.path)
        return delta

    async def apply_handoff(self, workspace_id, delta_ref):
        key = "handoff/" + workspace_id
        existing = self.records.get(key)
        if existing:
            if existing[1]["delta_ref"] != delta_ref:
                raise ValueError("Workspace source handoff is immutable")
            return
        manifest = self.current(workspace_id)
        if manifest.view != "development":
            raise ValueError("Source handoff requires an unstarted development view")
        delta = await self.validate_handoff(delta_ref, manifest.original_base, manifest.allowed_write_paths)
        tree = self.scan(self.root_for(manifest))
        modes = self.records.get("delta-modes/" + delta.workspace_id)[1]["modes"]
        for change in delta.changes:
            if change.action == "delete":
                tree.pop(change.path, None)
            else:
                tree[change.path] = (modes[change.path], self.artifacts.read(change.content))
        for change in delta.changes:
            if change.action == "delete":
                (self.root_for(manifest) / change.path).unlink(missing_ok=True)
        self.materialize(self.root_for(manifest), tree)
        self.records.put_once(key, {"delta_ref": delta_ref})

    async def integrate(self, workspace_id, head, permit_ref):
        manifest = self.current(workspace_id)
        if not self.exclusive.owns(permit_ref, "verification/project", manifest.process_id):
            raise ValueError("Integration requires current verification ownership")
        if manifest.view == "integration":
            return manifest
        delta_ref = await self.preserve_delta(workspace_id)
        delta = WorkspaceDelta.model_validate(self.records.get(delta_ref)[1]).model_dump(mode="json")
        modes = self.records.get("delta-modes/" + workspace_id)[1]["modes"]
        base = await self.tree(manifest.original_base.commit_id, manifest.process_id)
        integrated = await self.tree(head.commit_id, manifest.process_id)
        from ..contracts import ArtifactRef

        for change in delta["changes"]:
            path = change["path"]
            original, incoming = base.get(path), integrated.get(path)
            private = (
                (modes[change["path"]], self.artifacts.read(ArtifactRef.model_validate(change["content"])))
                if change["content"]
                else None
            )
            if incoming != original and incoming != private:
                if (
                    original
                    and incoming
                    and private
                    and b"\x00" not in original[1] + incoming[1] + private[1]
                ):
                    scratch = self.root / workspace_id / "merge"
                    scratch.mkdir(parents=True, exist_ok=True)
                    for label, value in (("current", incoming), ("base", original), ("private", private)):
                        (scratch / label).write_bytes(value[1])
                    permit = await self.exclusive.acquire("shell/installation", manifest.process_id)
                    try:
                        proc = await asyncio.create_subprocess_exec(
                            "git",
                            "merge-file",
                            "-p",
                            str(scratch / "current"),
                            str(scratch / "base"),
                            str(scratch / "private"),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        output, _ = await proc.communicate()
                        if proc.returncode not in {0, 1}:
                            raise ValueError("Merge failed")
                        private = (private[0], output)
                    finally:
                        await self.exclusive.release(permit, manifest.process_id)
                else:
                    raise ValueError(f"Explicit conflict needs new assignment: {path}")
            if private is None:
                integrated.pop(path, None)
            else:
                integrated[path] = private
        generation = manifest.generation + 1
        new = manifest.model_copy(
            update={
                "manifest_id": workspace_id + ":" + str(generation),
                "generation": generation,
                "view": "integration",
                "materialization": "complete",
                "private_root_ref": workspace_id + ":" + str(generation),
                "captured_head": head,
                "effective_code": self.code(integrated),
                "copied_files": [
                    CopiedFile(
                        path=p, copied_digest=digest(value[1]), writable=p in manifest.allowed_write_paths
                    )
                    for p, value in sorted(integrated.items())
                ],
                "preserved_delta_ref": delta_ref,
            }
        )
        self.materialize(self.root_for(new), integrated)
        rev = self.records.get("workspace/" + workspace_id)[0]
        self.records.compare_and_publish(
            {"workspace/" + workspace_id: rev},
            {"workspace/" + workspace_id: new.model_dump(mode="json")},
            {"manifest/" + new.manifest_id: new.model_dump(mode="json")},
        )
        return new

    async def abort(self, workspace_id):
        manifest = self.current(workspace_id)
        if manifest.view == "development":
            return
        # Keep original delta and abandoned integrated files; retire old generation.
        dev = self.records.get("manifest/" + workspace_id + ":1")[1]
        generation = manifest.generation + 1
        restored = WorkspaceManifest.model_validate(
            {
                **dev,
                "generation": generation,
                "manifest_id": workspace_id + ":" + str(generation),
                "private_root_ref": workspace_id + ":" + str(generation),
            }
        )
        original = WorkspaceManifest.model_validate(dev)
        self.materialize(self.root_for(restored), self.scan(self.root_for(original)))
        rev = self.records.get("workspace/" + workspace_id)[0]
        self.records.compare_and_publish(
            {"workspace/" + workspace_id: rev},
            {"workspace/" + workspace_id: restored.model_dump(mode="json")},
            {"manifest/" + restored.manifest_id: restored.model_dump(mode="json")},
        )

    async def commit(self, workspace_id, head, operation_id):
        existing = self.records.get("commit/" + operation_id)
        if existing:
            return CodeRevision.model_validate(existing[1])
        manifest = self.current(workspace_id)
        final = self.scan(self.root_for(manifest))
        previous = await self.tree(head.commit_id, manifest.process_id)
        changed = {p for p in final.keys() | previous.keys() if final.get(p) != previous.get(p)}
        if not changed <= set(manifest.allowed_write_paths):
            raise ValueError("Final H-to-P delta exceeds write grant")
        index = self.root / workspace_id / "trusted.index"
        env = {
            "GIT_INDEX_FILE": str(index),
            "GIT_AUTHOR_NAME": "PolyInference",
            "GIT_AUTHOR_EMAIL": "agent@polyinference.local",
            "GIT_COMMITTER_NAME": "PolyInference",
            "GIT_COMMITTER_EMAIL": "agent@polyinference.local",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000",
        }
        await self.git("read-tree", "--empty", process_id=manifest.process_id, env=env)
        for path, (mode, content) in sorted(final.items()):
            oid = (
                (
                    await self.git(
                        "hash-object", "-w", "--stdin", input_data=content, process_id=manifest.process_id
                    )
                )
                .decode()
                .strip()
            )
            await self.git(
                "update-index",
                "--add",
                "--cacheinfo",
                mode,
                oid,
                path,
                process_id=manifest.process_id,
                env=env,
            )
        tree = (await self.git("write-tree", process_id=manifest.process_id, env=env)).decode().strip()
        commit = (
            (
                await self.git(
                    "commit-tree",
                    tree,
                    "-p",
                    head.commit_id,
                    input_data=f"PolyInference operation {operation_id}\n".encode(),
                    process_id=manifest.process_id,
                    env=env,
                )
            )
            .decode()
            .strip()
        )
        code = self.code(final, commit)
        self.records.put_once("commit/" + operation_id, code.model_dump(mode="json"))
        return code
