from __future__ import annotations

import json
import subprocess
import sys

import pytest

from polyinference.config import AgentConfig, Endpoint
from polyinference.domain import Check


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.STDOUT).decode().strip()


def fixture_completion(data):
    """Deterministic reviewer response, not a live model's semantic validation."""
    return {
        "reviewed_tree_digest": data["acceptance_contract"]["reviewed_tree_digest"],
        "criteria": [
            {
                "criterion_id": c["criterion_id"],
                "verdict": "met",
                "rationale": "Fixture inspected supplied source/checks",
                "evidence_refs": [e["evidence_id"] for e in data["review_evidence_catalog"]],
            }
            for c in data["acceptance_contract"]["criteria"]
        ],
    }


@pytest.fixture
def repository(tmp_path):
    repo = tmp_path / "source"
    repo.mkdir()
    (repo / "a.py").write_text("VALUE = 1\n")
    (repo / "b.py").write_text("VALUE = 1\n")
    (repo / "untouched.txt").write_text("must survive partial copies\n")
    git(repo, "init", "-q")
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "base")
    return repo


@pytest.fixture
def config(repository, tmp_path):
    return AgentConfig(
        repository=str(repository),
        state_directory=str(tmp_path / "state"),
        objective="Set VALUE to 2 in a.py and b.py",
        allowed_write_paths=["a.py", "b.py"],
        closure_paths=["a.py"],
        checks=[
            Check(
                name="syntax",
                argv=[
                    sys.executable,
                    "-c",
                    "import ast,pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('.').glob('*.py')]",
                ],
            )
        ],
        local=Endpoint(model="local-fixture", base_url="http://fixture/v1"),
        cloud=Endpoint(model="cloud-fixture", base_url="http://fixture/v1"),
        check_execution="trusted",
    )


class ScriptedAgent:
    def __init__(self, verdict="successful", two=True):
        self.verdict, self.two = verdict, two
        self.counts = {}
        self.active = self.peak = 0
        self.initial_calls = 0
        self.review_inputs = []
        self.hook = None

    async def generate(self, messages, max_output, response_schema=None, **kwargs):
        import asyncio

        from polyinference.domain import digest

        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            await asyncio.sleep(0.15)
            data = json.loads(
                next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
                    "Pinned application inputs:\n", 1
                )[1]
            )
            if self.hook:
                await self.hook(data)
            if "assignment" not in data:
                if not data["all_task_ids"]:
                    self.initial_calls += 1
                    names = ["a", "b"] if self.two else ["a"]
                    reply = {
                        "goal": "Update values",
                        "tasks": [
                            {
                                "task_id": name,
                                "objective": f"Set VALUE to 2 in {name}.py",
                                "write_paths": [name + ".py"],
                                "read_paths": [name + ".py"],
                                "checks": ["syntax"],
                            }
                            for name in names
                        ],
                    }
                else:
                    self.review_inputs.append(data)
                    reply = {
                        "goal": "Finished",
                        "complete": True,
                        "completion_assessment": fixture_completion(data),
                        "dispositions": [
                            {"report_ref": r["record_id"], "action": "keep", "reason": "Inspected changes"}
                            for r in data["reports"]
                        ],
                    }
            else:
                assignment, phase = data["assignment"], data["phase"]
                name = assignment["task_id"]
                count = self.counts.get((name, phase), 0)
                self.counts[(name, phase)] = count + 1
                if phase == "development" and count == 0:
                    reply = {"kind": "action", "tool": "files.read", "arguments": {"path": name + ".py"}}
                elif phase == "development" and count == 1:
                    reply = {
                        "kind": "action",
                        "tool": "files.write",
                        "arguments": {
                            "path": name + ".py",
                            "expected_digest": digest(b"VALUE = 1\n"),
                            "content": "VALUE = 2\n",
                        },
                    }
                elif phase == "assessment":
                    reply = {
                        "kind": "assessment",
                        "verdict": self.verdict,
                        "summary": "Checked exact integration tree",
                    }
                else:
                    reply = {"kind": "candidate", "summary": "Inspected incoming changes"}
            return {
                "text": json.dumps(reply),
                "usage": {"total_tokens": 50},
                "model": "fixture",
                "events": [],
            }
        finally:
            self.active -= 1

    async def close(self):
        pass
