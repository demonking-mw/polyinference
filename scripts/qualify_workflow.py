"""Fresh disposable coding trials; --fixture is offline, --config explicitly uses its providers."""

from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from polyinference.agent.cloud_recovery import capabilities
from polyinference.agent.controller import ProjectAgent
from polyinference.agent.qualification import qualification_gate, quality
from polyinference.agent.services import AgentServices
from polyinference.config import AgentConfig, Endpoint
from polyinference.contracts import ArtifactRef
from polyinference.costs import run_cost
from polyinference.domain import Check
from polyinference.primitives import canonical, digest, now
from polyinference.runtime.kernel import KernelRuntime
from polyinference.runtime.processes import request_resume
from polyinference.runtime.tool_environment import tool_environment

FIXTURE_SOURCE = "def combine(left, right):\n    return left + right\n"
BROWSER_CHECK = Path(__file__).with_name("browser_check.mjs").resolve()


class QualificationPause(RuntimeError):
    """A deliberate settled-boundary interruption, distinct from implementation failures."""


def settled_edit(entry):
    observation = entry.get("observation", {})
    return (entry.get("reply", {}).get("tool") in {"files.write", "files.patch", "files.delete", "shell.run"}
            and not observation.get("error")
            and bool(observation.get("changed") or observation.get("changed_paths")))


def corpus(case):
    if case == "workflow":
        return "app.js", {
            "index.html": '<div id="app"></div><script type="module">import {mount} from "./app.js";mount(document.querySelector("#app"));</script>',
            "app.js": '''export function mount(root) {
  let value = Number(localStorage.getItem('value') || 0);
  root.innerHTML = '<output id="value"></output><button id="increment">add</button><button id="pause">pause</button><button id="save">save</button><output id="status">playing</output>';
  const output = root.querySelector('#value'); output.textContent = String(value);
  root.querySelector('#increment').onclick = () => { value++; output.textContent = String(value); };
  root.querySelector('#pause').onclick = () => { root.querySelector('#status').textContent = 'paused'; };
  root.querySelector('#save').onclick = () => { /* persist current value */ };
}\n''',
        }, [shutil.which("node") or "node", str(BROWSER_CHECK),
            "--tools=" + str(Path(os.environ.get("QUALIFICATION_BROWSER_TOOLS", ".")).resolve()),
            *(["--browsers=" + str(Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"]).resolve())]
              if os.environ.get("PLAYWRIGHT_BROWSERS_PATH") else [])], (
            "Make Save persist the current value across reload; preserve entry, input and pause behavior.")
    if case == "save":
        return "solution.py", {"solution.py": "import json\ndef restore(blob):\n    return {}\n"}, [
            sys.executable, "-c", "from solution import restore; assert restore('{\"name\":\"world\",\"x\":7}') == {'name':'world','x':7}"], "Implement restore(blob) to preserve the supplied JSON world state."
    if case == "create":
        return "solution.py", {"README.md": "Disposable create/update qualification.\n"}, [
            sys.executable, "-c", "from solution import combine; assert combine(2,3)==5; assert combine(-4,2)==-2"], (
            "Create solution.py with combine(left,right) initially returning zero, then update it to add both numbers. "
            "Use files.write to create it and a subsequent files.write/files.patch with its returned digest to update it.")
    return "solution.py", {"solution.py": "def combine(left, right):\n    return left - right\n"}, [
        sys.executable, "-c", "from solution import combine; assert combine(2,3)==5; assert combine(-4,2)==-2"], "Repair combine(left,right) to add both numbers, including negative values."


def creation_check(app, records, source):
    previous = None
    for effect in sorted((v for k, v in records.items() if k.startswith("effect/")),
                         key=lambda value: value["request"]["created_at"]):
        payload = effect["request"]["payload"]
        if payload.get("capability_id") not in {"files.write", "files.patch"} or effect["state"] != "succeeded":
            continue
        arguments = app.read(payload["arguments"])
        refs = (effect.get("result") or {}).get("output_refs", [])
        if arguments.get("path") != source or not refs:
            continue
        observation = app.read(refs[0])
        if observation.get("error") or not observation.get("digest"):
            continue
        if previous and arguments.get("expected_digest") == previous:
            return True
        if payload["capability_id"] == "files.write" and arguments.get("expected_digest") is None:
            previous = observation["digest"]
    return False


class Fixture:
    """Explicit scripted provider for orchestration qualification, never a live-quality claim."""
    async def generate(self, messages, *args, **kwargs):
        data = json.loads(next(m["content"].split("Pinned application inputs:\n", 1)[1]
                               for m in messages if m["content"].startswith("Pinned application inputs:")))
        if "repository_observation" in data:
            reply = {"mode": "new", "task_branches": True, "reason": "Disposable qualification"}
        elif "assignment" not in data:
            if not data["all_task_ids"]:
                reply = {"goal": "One repair", "tasks": [{"task_id": "repair", "objective": data["objective"],
                    "write_paths": ["solution.py"], "read_paths": ["solution.py"], "checks": ["behavior"],
                    "behavior": "Adding two numbers", "focused_check": "behavior"}]}
            else:
                reply = {"goal": "Checked result", "complete": True,
                    "dispositions": [{"report_ref": r["record_id"], "action": "keep", "reason": "Fixture source review"}
                                     for r in data["reports"]],
                    "completion_assessment": {"reviewed_tree_digest": data["acceptance_contract"]["reviewed_tree_digest"],
                        "criteria": [{"criterion_id": c["criterion_id"], "verdict": "met", "rationale": "Fixture source/check review",
                            "evidence_refs": [e["evidence_id"] for e in data["review_evidence_catalog"]]}
                                     for c in data["acceptance_contract"]["criteria"]]}}
        elif data["phase"] == "assessment":
            reply = {"kind": "assessment", "verdict": "successful", "summary": "Exact behavior check"}
        elif data["phase"] != "development":
            reply = {"kind": "candidate", "summary": "Ready for checks"}
        else:
            remembered = data["worker_state"]["files"].get("solution.py")
            if not remembered:
                reply = {"kind": "action", "tool": "files.read", "arguments": {"path": "solution.py"}}
            elif remembered["digest"] == digest(FIXTURE_SOURCE.encode()):
                reply = {"kind": "candidate", "summary": "One behavior implemented"}
            else:
                reply = {"kind": "action", "tool": "files.write", "arguments": {"path": "solution.py",
                    "expected_digest": remembered["digest"], "content": FIXTURE_SOURCE}}
        return {"text": json.dumps(reply), "model": "qualification-fixture", "usage": {"total_tokens": 30}}

    async def close(self):
        pass


async def trial(base, root, case, fixture=False, interrupt=False):
    source, files, argv, objective = corpus(case)
    repo = root / "project"
    repo.mkdir(parents=True)
    for name, body in files.items():
        (repo / name).write_text(body)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Qualification", "-c",
                    "user.email=qualification@example.invalid", "commit", "-qm", "qualification baseline"], check=True)
    config = AgentConfig.model_validate({**base.model_dump(mode="json"), "repository": str(repo),
        "state_directory": str(root / "state"), "output_directory": None, "repository_mode": "in_place",
        "objective": objective + " Change only the assigned source; preserve the independent check.",
        "write_scope": "explicit", "allowed_write_paths": [source], "closure_paths": list(files),
        "prepare_repository": False, "checks": [Check(name="behavior", argv=argv,
            required_paths=list(dict.fromkeys([*files, source]))).model_dump()],
        "prerequisite_checks": [], "acceptance_checks": None, "acceptance_criteria": [],
        "dependency_prepare": []}, context={"resolve_environment_capacity": False})
    environment = {"python": sys.version, "node": None, "playwright": None}
    environment["packages"] = {name: importlib.metadata.version(name)
                               for name in ("langgraph", "langgraph-checkpoint-sqlite", "pydantic", "httpx")}
    if case == "workflow":
        environment["node"] = subprocess.check_output([argv[0], "--version"]).decode().strip()
        package = Path(os.environ.get("QUALIFICATION_BROWSER_TOOLS", ".")) / "node_modules/playwright/package.json"
        environment["playwright"] = json.loads(package.read_text())["version"]
    framework_root = Path(__file__).parents[1]
    framework_files = sorted([p for p in (framework_root / "src/polyinference").rglob("*")
                              if p.suffix in {".py", ".js", ".html"}]
                             + [Path(__file__).resolve(), BROWSER_CHECK, framework_root / "pyproject.toml"])
    profile_config = config.model_dump(mode="json")
    for name in ("repository", "state_directory", "output_directory"):
        profile_config.pop(name, None)
    pins = {"case": case, "source": files, "argv": argv, "environment": environment,
            "agent_profile": profile_config, "tool_inventory": capabilities(config),
            "browser_check_digest": digest(BROWSER_CHECK.read_bytes()) if case == "workflow" else None,
            "limits": config.limits.model_dump(mode="json"),
            "local": config.local.model_dump(mode="json"), "cloud": config.cloud.model_dump(mode="json"),
            "role_bindings": config.role_bindings, "fixture": fixture,
            "framework": {str(p.relative_to(framework_root)): digest(p.read_bytes()) for p in framework_files}}
    (root / "manifest.json").write_bytes(canonical({"started_at": now().isoformat(), "profile": pins,
                                                  "config": config.model_dump(mode="json")}))
    with tarfile.open(root / "framework-source.tar.gz", "w:gz") as archive:
        for path in framework_files:
            archive.add(path, arcname=str(path.relative_to(framework_root)), recursive=False)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=framework_root, capture_output=True)
    changes = subprocess.run(["git", "diff", "--no-ext-diff", "--binary", "HEAD", "--", "src", "scripts", "pyproject.toml"],
                             cwd=framework_root, capture_output=True)
    (root / "framework-revision.json").write_bytes(canonical({
        "head": revision.stdout.decode().strip() if revision.returncode == 0 else None,
        "diff_available": changes.returncode == 0}))
    if changes.returncode == 0:
        (root / "framework-dirty.patch").write_bytes(changes.stdout)
    runtime = await KernelRuntime(config).open()
    interrupted = False
    interruption_resources = {}
    started = time.monotonic()

    async def connect(runtime):
        if fixture:
            for client in runtime.clients.values():
                await client.close()
            runtime.clients = {name: Fixture() for name in runtime.clients}
        app = AgentServices(runtime, config)
        return app, ProjectAgent(app)

    try:
        app, engine = await connect(runtime)
        if interrupt:
            original_model, original_review = app.model, engine.review
            written = False

            async def model(state, senior=False):
                nonlocal written
                if not senior and not written and any(settled_edit(e)
                                                      for e in app.history(state.get("trajectory_ref"))):
                    written = True
                    return {"kind": "needs_review", "reason": "Qualification pause after a settled edit"}
                return await original_model(state, senior=senior)

            async def review():
                if written and runtime.records.scan("worker-exception/"):
                    raise QualificationPause("Qualification host interruption at settled recovery boundary")
                return await original_review()

            app.model, engine.review = model, review
        try:
            await engine.run()
        except QualificationPause:
            if not interrupt or not written or runtime.uncertain():
                raise
            interrupted = True
            interruption_resources = {p["process_id"]: runtime.resource_state(p["process_id"])
                                      for _, _, p in runtime.records.scan("process/") if not p.get("management")}
        if interrupted:
            await runtime.close()
            runtime = await KernelRuntime(config).open()
            app, engine = await connect(runtime)
            intent = request_resume(runtime.records, text="Continue the preserved qualification task.",
                                    request_id="qualification-resume")
            await engine.resume(intent)
            await engine.run()
        records = {k: v for k, _, v in runtime.records.scan("")}
        check = subprocess.run(argv, cwd=repo, capture_output=True, timeout=120)
        (root / "independent-check.log").write_bytes(check.stdout + check.stderr)
        protocol_passed = case != "create" or creation_check(app, records, source)
        resumed_resources = {pid: runtime.resource_state(pid) for pid in interruption_resources}
        budgets_preserved = all(resumed_resources[pid]["account"] == before["account"]
                                and resumed_resources[pid]["deadline"] == before["deadline"]
                                and resumed_resources[pid]["remaining_model_calls"] <= before["remaining_model_calls"]
                                and resumed_resources[pid]["remaining_operations"] <= before["remaining_operations"]
                                for pid, before in interruption_resources.items())
        result = {**quality(records), "profile_digest": digest(canonical(pins)), "fixture": fixture,
                  "framework_changed": any(not (Path(__file__).parents[1] / name).exists()
                                           or digest((Path(__file__).parents[1] / name).read_bytes()) != expected
                                           for name, expected in pins["framework"].items()),
                  "independent_check": "passed" if check.returncode == 0 and protocol_passed else "failed",
                  "protocol_check": "passed" if protocol_passed else "failed", "manual_repair": False,
                  "independently_verified_behaviors": [case] if check.returncode == 0 and protocol_passed
                  and app.get("app/run")["status"] == "completed" else [],
                  "cost": run_cost(records, lambda ref: app.ports.artifacts.read(ArtifactRef.model_validate(ref)).decode()),
                  "check_changed": case == "workflow" and digest(BROWSER_CHECK.read_bytes()) != pins["browser_check_digest"],
                  "interruption_resources": interruption_resources, "resumed_resources": resumed_resources,
                  "interrupted": interrupted, "resume_verified": interrupted and budgets_preserved
                  and app.get("app/run")["status"] == "completed",
                  "elapsed_seconds": time.monotonic() - started}
        (root / "result.json").write_bytes(canonical(result))
        return result
    except (asyncio.CancelledError, KeyboardInterrupt):
        (root / "result.json").write_bytes(canonical({"status": "interrupted", "exit_cause": "Qualification cancelled",
            "profile_digest": digest(canonical(pins)), "fixture": fixture, "independent_check": "not_completed",
            "interrupted": True, "resume_verified": False,
            "uncertain_effects": len(runtime.uncertain())}))
        raise
    except Exception as exc:
        result = {"status": "failed", "exit_cause": str(exc)[:2000], "error_type": type(exc).__name__,
                  "profile_digest": digest(canonical(pins)), "fixture": fixture,
                  "independent_check": "not_completed", "interrupted": interrupted, "resume_verified": False}
        (root / "result.json").write_bytes(canonical(result))
        return result
    finally:
        await runtime.close()


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--config", type=Path)
    mode.add_argument("--fixture", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=["repair", "create", "save", "workflow"], default="repair")
    args = parser.parse_args()
    if args.fixture and args.case != "repair":
        parser.error("The fixture provider qualifies repair orchestration only; other cases require --config")
    base = AgentConfig.model_validate_json(args.config.read_text()) if args.config else AgentConfig(
        repository="unused", objective="Qualification", allowed_write_paths=["solution.py"],
        checks=[Check(name="behavior", argv=[sys.executable, "-c", "pass"])], check_execution="trusted",
        local=Endpoint(model="qualification-worker-fixture"), cloud=Endpoint(model="qualification-specialist-fixture"))
    if base.check_execution == "disabled":
        parser.error("Qualification requires explicitly configured check execution")
    if args.case == "workflow":
        with TemporaryDirectory(prefix="qualification-preflight-") as directory:
            preflight = await KernelRuntime(base.model_copy(update={"state_directory": directory})).open()
            try:
                async with tool_environment(preflight.workspaces) as (environment, _):
                    subprocess.run([*corpus("workflow")[2], "--preflight"], env=environment, check=True, timeout=60)
            finally:
                await preflight.close()
    args.output.mkdir(parents=True, exist_ok=False)
    trials = []
    for index in range(4):
        trials.append(await trial(base, args.output / f"trial-{index + 1}", args.case,
                                  fixture=args.fixture, interrupt=index == 3))
        (args.output / "results.json").write_bytes(canonical({"trials": trials, "gate": qualification_gate(trials)}))
    print(json.dumps({"output": str(args.output), "fixture": args.fixture, "gate": qualification_gate(trials)}, indent=2))
    return 0 if qualification_gate(trials)["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
