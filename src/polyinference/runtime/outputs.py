"""Optional delivery of arbitrary file artifacts, independent of Git or agent policy."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from ..contracts import ArtifactRef
from ..primitives import canonical, digest
from ..workspace_contracts import relative_path


class Outputs:
    def __init__(self, config, records, artifacts):
        self.config, self.records, self.artifacts = config, records, artifacts
        self.lock = asyncio.Lock()

    def prepare(self, directory, baseline):
        root = Path(directory).absolute()
        if root.is_symlink() or root.resolve() != root:
            raise ValueError("Output directory must not traverse symlinks")
        if root == root.parent or (
            root.is_relative_to(self.config.state_path)
            and not root.is_relative_to(self.config.state_path / "result")
        ):
            raise ValueError("Invalid output directory")
        value = {"directory": str(root), "baseline": baseline}
        self.records.put_once("outputs/target", value)
        return value

    async def deliver(self, delivery_id, files):
        async with self.lock:
            return await self._deliver(delivery_id, files)

    async def _deliver(self, delivery_id, files):
        target = self.records.get("outputs/target")
        if not target:
            raise ValueError("No output destination has been prepared")
        target = target[1]
        root = Path(target["directory"])
        identity = digest(canonical({"target": target, "files": files}))
        receipt_key = "output-delivery/" + delivery_id
        receipt = self.records.get(receipt_key)
        if receipt:
            if receipt[1]["digest"] != identity:
                raise ValueError("Output delivery identity reused with different files")
            return receipt[1]
        desired, total = await asyncio.to_thread(self.read_files, files)
        intent_key = "output-intent/" + delivery_id
        intent = self.records.get(intent_key)
        if intent and intent[1]["digest"] != identity:
            raise ValueError("Output delivery intent changed")
        head = self.records.get("outputs/head")
        baseline = (intent[1]["baseline"] if intent else head[1]["files"] if head else target["baseline"])
        await asyncio.to_thread(self.preflight, root, baseline, desired, bool(intent))
        self.records.put_once(intent_key, {"digest": identity, "files": files, "baseline": baseline})
        # Cancellation cannot release the delivery lock while writes still run.
        task = asyncio.create_task(asyncio.to_thread(self.write_files, root, baseline, desired))
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            await task
            raise
        receipt = {"digest": identity, "directory": str(root), "file_count": len(files), "bytes": total}
        self.records.compare_and_publish(
            {"outputs/head": head[0] if head else 0},
            {"outputs/head": {"delivery_id": delivery_id,
                              "files": {name: self.content_fingerprint(mode, content)
                                        for name, (mode, content) in desired.items()}}},
            {receipt_key: receipt},
        )
        return receipt

    def read_files(self, files):
        desired = {}
        total = 0
        for item in files:
            name = relative_path(item["path"])
            if name in desired or item["mode"] not in {"100644", "100755"}:
                raise ValueError("Invalid or duplicate output file")
            content = self.artifacts.read(ArtifactRef.model_validate(item["content"]))
            total += len(content)
            if total > self.config.max_workspace_bytes:
                raise ValueError("Output delivery exceeds file budget")
            desired[name] = (item["mode"], content)
        return desired, total

    def preflight(self, root, baseline, desired, recovering):
        if root.is_symlink() or root.resolve() != root:
            raise ValueError("Output directory changed to a symlink")
        # Check every affected file before the first mutation. A persisted intent
        # permits recovery of this delivery's own partially completed writes.
        for name in set(baseline) | set(desired):
            path = root / relative_path(name)
            if path.is_symlink() or path.resolve() != path or path.exists() and not path.is_file():
                raise ValueError("Output file path is unsafe: " + name)
            current = self.fingerprint(path) if path.exists() else None
            wanted = self.content_fingerprint(*desired[name]) if name in desired else None
            allowed = [baseline.get(name)]
            if recovering:
                allowed.append(wanted)
            if current not in allowed:
                raise ValueError("Output destination changed since start: " + name)

    def write_files(self, root, baseline, desired):
        root.mkdir(parents=True, exist_ok=True)
        for name, (mode, content) in sorted(desired.items()):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and self.fingerprint(path) == self.content_fingerprint(mode, content):
                continue
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.chmod(0o755 if mode == "100755" else 0o644)
                temporary.replace(path)
            finally:
                if temporary:
                    temporary.unlink(missing_ok=True)
        for name in set(baseline) - set(desired):
            (root / name).unlink(missing_ok=True)

    @staticmethod
    def content_fingerprint(mode, content):
        return {"mode": mode, "digest": digest(content)}

    @classmethod
    def fingerprint(cls, path):
        return cls.content_fingerprint("100755" if path.stat().st_mode & 0o111 else "100644", path.read_bytes())
