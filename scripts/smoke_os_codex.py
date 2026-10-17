"""Opt-in live test: uses Codex allowance and retains a disposable run directory."""

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.config import AgentConfig, Endpoint
from polyinference.domain import Check, default_limits
from polyinference.runtime.kernel import KernelRuntime


async def main(model):
    root = Path(tempfile.mkdtemp(prefix="polyinference-os-live-"))
    repo = root / "source"
    repo.mkdir()
    (repo / "greeting.py").write_text('def greet():\n    return "Hello"\n')

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args]).decode().strip()

    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=OS Test", "-c", "user.email=os@localhost", "commit", "-qm", "baseline")
    endpoint = Endpoint(
        protocol="codex_app_server",
        model=model,
        brokered_tools=True,
        max_inflight=1,
        max_context_tokens=128000,
        reserved_context_tokens=128000,
    )
    config = AgentConfig(
        repository=str(repo),
        state_directory=str(root / "state"),
        objective='Change greeting.py so greet() returns exactly "Hello, OS!". Use one small coding task. No setup or unrelated changes.',
        allowed_write_paths=["greeting.py"],
        closure_paths=["greeting.py"],
        checks=[
            Check(
                name="greeting",
                argv=[sys.executable, "-c", 'from greeting import greet; assert greet() == "Hello, OS!"'],
            )
        ],
        local=Endpoint(model="unused"),
        cloud=endpoint,
        role_bindings={"senior": "cloud", "worker": "cloud", "specialist": "cloud"},
        limits=default_limits().model_copy(update={"max_input_tokens_per_call": 64000}),
        max_workers=1,
        max_sprints=3,
        check_execution="trusted",
    )
    runtime = KernelRuntime(config)
    try:
        await runtime.open()
        app = AgentServices(runtime, config)
        await ProjectAgent(app).run()
        run = app.get("app/run")
        reports = [body for _, _, body in runtime.records.scan("report/")]
        head = app.get("head/provisional")["code"]
        tree = await runtime.workspaces.tree(head["commit_id"])
        summary = {
            "state_directory": str(config.state_path),
            "status": run["status"],
            "reports": [
                {
                    "verdict": r["verdict"],
                    "reconciliations": len(r["reconciliation_turn_refs"]),
                    "assessments": len(r["assessment_turn_refs"]),
                }
                for r in reports
            ],
            "native_jobs": sum(
                body["request"]["payload"]["kind"] == "agent_job"
                for _, _, body in runtime.records.scan("effect/")
            ),
            "broker_callbacks": sum(
                bool(body["request"].get("causal_parent_ref"))
                for _, _, body in runtime.records.scan("effect/")
            ),
            "source_unchanged": git("status", "--porcelain") == ""
            and (repo / "greeting.py").read_text() == 'def greet():\n    return "Hello"\n',
            "final_source": tree["greeting.py"][1].decode(),
            "uncertain": runtime.uncertain(),
        }
        print(json.dumps(summary, indent=2), flush=True)
        assert run["status"] == "completed", summary
        assert summary["source_unchanged"] and not summary["uncertain"], summary
        assert reports and all(
            r["reconciliation_turn_refs"] and r["assessment_turn_refs"] for r in reports
        ), summary
    finally:
        await runtime.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Model available to the signed-in Codex account")
    asyncio.run(main(parser.parse_args().model))
