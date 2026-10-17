from __future__ import annotations

import asyncio
import fcntl
import os
import tempfile
from pathlib import Path

from ..domain import digest


class Exclusive:
    """Durable logical ownership plus installation-wide OS advisory shell lock."""

    def __init__(self, records, wait_timeout=3600):
        self.records = records
        self.wait_timeout = wait_timeout
        self.conditions = {}
        self.shell_handles = {}
        self.depth = {}

    def _key(self, key):
        return "permit/" + key

    async def acquire(self, key, process_id):
        held = self.records.get(self._key(key))
        if held and held[1].get("process_id") == process_id:
            permit = held[1]["permit"]
            if key == "shell/installation":
                if permit in self.shell_handles:
                    self.depth[permit] = self.depth.get(permit, 1) + 1
                else:
                    path = Path(tempfile.gettempdir()) / f"polyinference-shell-{os.getuid()}.lock"
                    handle = path.open("a+")
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BaseException:
                        handle.close()
                        raise
                    self.shell_handles[permit] = (process_id, handle)
                    self.depth[permit] = 1
            return permit
        if key.startswith("verification") and any(p == process_id for p, _ in self.shell_handles.values()):
            raise RuntimeError("Cannot acquire verification while owning shell")
        condition = self.conditions.setdefault(key, asyncio.Lock())
        try:
            await asyncio.wait_for(condition.acquire(), self.wait_timeout)
        except asyncio.TimeoutError as exc:
            raise RuntimeError("Ownership queue deadline expired: " + key) from exc
        handle = None
        try:
            # An old logical owner is never expired automatically.
            held = self.records.get(self._key(key))
            if held and held[1].get("process_id"):
                raise RuntimeError(f"Retained ownership requires reconciliation: {key}")
            if key == "shell/installation":
                path = Path(tempfile.gettempdir()) / f"polyinference-shell-{os.getuid()}.lock"
                handle = path.open("a+")
                deadline = asyncio.get_running_loop().time() + self.wait_timeout
                while True:
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if asyncio.get_running_loop().time() >= deadline:
                            raise RuntimeError("Installation shell queue deadline expired")
                        await asyncio.sleep(0.05)
            version = held[0] if held else 0
            permit = digest(f"{key}:{process_id}:{version + 1}".encode())
            self.records.compare_and_publish(
                {self._key(key): version},
                {self._key(key): {"permit": permit, "process_id": process_id, "resource": key}},
            )
            self.depth[permit] = 1
            if handle:
                self.shell_handles[permit] = (process_id, handle)
            return permit
        except BaseException:
            if handle:
                handle.close()
            condition.release()
            raise

    def owns(self, permit, key, process_id):
        record = self.records.get(self._key(key))
        return bool(
            record and record[1].get("permit") == permit and record[1].get("process_id") == process_id
        )

    async def release(self, permit, process_id):
        matches = [
            (key, rev, body)
            for key, rev, body in self.records.scan("permit/")
            if body.get("permit") == permit and body.get("process_id") == process_id
        ]
        if len(matches) != 1:
            raise RuntimeError("Cannot release unowned permit")
        if self.depth.get(permit, 1) > 1:
            self.depth[permit] -= 1
            return
        self.depth.pop(permit, None)
        key, rev, body = matches[0]
        self.records.compare_and_publish({key: rev}, {key: {**body, "process_id": None}})
        if permit in self.shell_handles:
            _, handle = self.shell_handles.pop(permit)
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()
        lock = self.conditions.get(body["resource"])
        if lock and lock.locked():
            lock.release()
