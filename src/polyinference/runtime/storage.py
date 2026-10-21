from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from ..contracts import ArtifactRef
from ..ports import RecordConflict
from ..primitives import canonical, digest


class Conflict(RecordConflict):
    pass


class Records:
    """Short transactions; immutable objects and CAS pointers share a commit."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS records (key TEXT PRIMARY KEY, revision INTEGER, body TEXT)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT)"
        )
        self.changed = asyncio.Event()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    def get(self, key):
        row = self.db.execute("SELECT revision,body FROM records WHERE key=?", (key,)).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def scan(self, prefix):
        return [
            (key, rev, json.loads(body))
            for key, rev, body in self.db.execute(
                "SELECT key,revision,body FROM records WHERE key>=? AND key<? ORDER BY key",
                (prefix, prefix + chr(0x10FFFF)),
            )
        ]

    def compare_and_publish(self, expected, updates, immutable=None):
        if set(updates) - set(expected):
            raise ValueError("Mutable pointers require expected versions")
        with self.transaction():
            for key, version in expected.items():
                current = self.get(key)
                if (current[0] if current else 0) != version:
                    raise Conflict(f"Version conflict: {key}")
            for key, body in (immutable or {}).items():
                current = self.get(key)
                if current and canonical(current[1]) != canonical(body):
                    raise Conflict(f"Immutable identity reused: {key}")
                if not current:
                    self.db.execute("INSERT INTO records VALUES (?,1,?)", (key, canonical(body).decode()))
            for key, body in updates.items():
                self.db.execute(
                    "INSERT OR REPLACE INTO records VALUES (?,?,?)",
                    (key, expected[key] + 1, canonical(body).decode()),
                )
            changes = {
                key: {"revision": expected[key] + 1, "state": body.get("state", body.get("status")), "value": body}
                for key, body in updates.items()
            }
            if changes or immutable:
                self.db.execute(
                    "INSERT INTO events(body) VALUES (?)",
                    (canonical({
                        "at": datetime.now(timezone.utc).isoformat(),
                        "changes": changes,
                        "immutable": list(immutable or {}),
                        "immutable_values": immutable or {},
                    }).decode(),),
                )
                self.db.execute(
                    "DELETE FROM events WHERE sequence <= (SELECT MAX(sequence)-10000 FROM events)"
                )
        self.changed.set()

    def events(self, after=0, limit=100):
        return [
            {"sequence": seq, **json.loads(body)}
            for seq, body in self.db.execute(
                "SELECT sequence,body FROM events WHERE sequence>? ORDER BY sequence LIMIT ?",
                (after, min(max(limit, 1), 1000)),
            )
        ]

    def put_once(self, key, body):
        self.compare_and_publish({}, {}, {key: body})


class Artifacts:
    def __init__(self, root: Path, max_bytes: int):
        self.root, self.max_bytes = root, max_bytes
        root.mkdir(parents=True, exist_ok=True)

    def put(self, data, scope, media_type="application/json"):
        hash_value = digest(data)
        path = self.root / hash_value[7:]
        if not path.exists():
            total = sum(p.stat().st_size for p in self.root.iterdir() if p.is_file())
            if total + len(data) > self.max_bytes:
                raise RuntimeError("Artifact storage budget exhausted")
            temporary = path.with_suffix(".partial")
            with temporary.open("wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(path)
        return ArtifactRef(
            artifact_id=hash_value,
            digest=hash_value,
            media_type=media_type,
            size_bytes=len(data),
            classification="project",
            scope=scope,
        )

    def read(self, ref):
        if ref.artifact_id != ref.digest:
            raise ValueError("Unknown artifact namespace")
        content = (self.root / ref.digest[7:]).read_bytes()
        if digest(content) != ref.digest or len(content) != ref.size_bytes:
            raise ValueError("Corrupt artifact")
        return content
