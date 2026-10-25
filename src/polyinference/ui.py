"""A loopback-only test runner and viewer for the standalone runtime."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shlex
import sqlite3
import subprocess
import sys
import threading
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from .agent.routing import accounting
from .cli import execute, load_config, record_steering
from .config import AgentConfig, Endpoint
from .costs import combine_costs, run_cost
from .domain import Check, default_limits
from .ui_repository import directories, project, suggested_check


def read_records(state):
    path = Path(state) / "records.sqlite"
    if not path.is_file():
        return {}
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='records'").fetchone():
            return {}
        return {key: json.loads(body) for key, body in db.execute("SELECT key,body FROM records")}


def read_artifact(state, ref):
    digest = ref.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Invalid artifact reference")
    root = Path(state) / "artifacts"
    path = root / digest[7:]
    if path.is_symlink():
        raise ValueError("Invalid artifact path")
    content = path.read_bytes()
    if "sha256:" + hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("Artifact digest mismatch")
    return content.decode(errors="replace")


async def checkpoints(state):
    path = Path(state) / "checkpoints.sqlite"
    if not path.is_file():
        return []
    async with aiosqlite.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        tables = await connection.execute(
            "SELECT name FROM sqlite_master WHERE name IN ('checkpoints', 'writes')"
        )
        if len(await tables.fetchall()) != 2:
            return []
        saver = AsyncSqliteSaver(connection)
        return [item async for item in saver.alist(None)]


async def node_history(state, running=False):
    """Each branch channel identifies the actual next node in these serial graphs."""
    groups = defaultdict(list)
    for item in await checkpoints(state):
        groups[item.config["configurable"]["thread_id"]].append(item)
    processes = []
    for pid, items in groups.items():
        items.sort(key=lambda item: item.checkpoint["id"])
        nodes = []
        for index, item in enumerate(items):
            if item.metadata.get("source") != "loop":
                continue
            before = item.checkpoint["channel_values"]
            following = items[index + 1] if index + 1 < len(items) else None
            writes = {name: value for _, name, value in item.pending_writes}
            for channel in before:
                if not channel.startswith("branch:to:"):
                    continue
                name = channel.removeprefix("branch:to:")
                status = (
                    "failed"
                    if "__error__" in writes
                    else "interrupted"
                    if "__interrupt__" in writes
                    else "completed"
                    if following
                    else "running"
                    if running
                    else "interrupted"
                )
                nodes.append(
                    {
                        "id": pid + ":" + item.checkpoint["id"] + ":" + name,
                        "name": name,
                        "phase": before.get("phase", before.get("mode", "")),
                        "status": status,
                        "started_at": item.checkpoint["ts"],
                        "finished_at": following.checkpoint["ts"] if following else None,
                        "logical_step": before.get("logical_step"),
                        "input": {k: v for k, v in before.items() if not k.startswith("branch:")},
                        "output": {k: v for k, v in writes.items() if not k.startswith("branch:")},
                        "model_call": name in {"model", "submit"},
                    }
                )
        if nodes:
            processes.append({"id": pid, "nodes": nodes, "started_at": items[0].checkpoint["ts"]})
    return sorted(processes, key=lambda process: process["started_at"])


def detail(state, node, records):
    effects = [
        value
        for key, value in records.items()
        if key.startswith("effect/") and value["request"]["scope"]["process_id"] == node["process_id"]
    ]
    matching = [
        effect
        for effect in effects
        if effect["request"]["created_at"] >= node["started_at"]
        and (not node["finished_at"] or effect["request"]["created_at"] < node["finished_at"])
    ]
    if node["model_call"]:
        step = "model-" + str(node["logical_step"])
        matching = [effect for effect in effects if effect["request"]["logical_step_id"] == step]
    operations = []
    for effect in sorted(matching, key=lambda effect: effect["request"]["created_at"]):
        request = effect["request"]
        payload = request["payload"]
        prompt = []
        for part in payload.get("context", {}).get("parts", []):
            role = (
                "system"
                if part["part_kind"] == "instruction" and part["trust"] in {"application", "user"}
                else "assistant"
                if part["part_kind"] in {"message", "tool_call"}
                else "user"
            )
            prompt.append({"role": role, "content": read_artifact(state, part["content"])})
        response = None
        if effect.get("result"):
            refs = effect["result"]["output_refs"]
            if refs:
                text = read_artifact(state, refs[0])
                try:
                    response = json.loads(text)
                except ValueError:
                    response = text
        # Codex persists the submitted application messages in its userMessage event.
        if payload["kind"] == "agent_job" and isinstance(response, dict):
            for event in response.get("events", []):
                item = event.get("params", {}).get("item", {})
                if item.get("type") != "userMessage":
                    continue
                for part in item.get("content", []):
                    try:
                        native = json.loads(part.get("text", ""))
                    except ValueError:
                        continue
                    if isinstance(native, list) and all(
                        isinstance(message, dict) and "role" in message and "content" in message
                        for message in native
                    ):
                        prompt = native
        arguments = read_artifact(state, payload["arguments"]) if payload.get("arguments") else None
        operations.append(
            {
                "id": request["operation_id"],
                "kind": payload["kind"],
                "tool": payload.get("capability_id"),
                "status": effect["state"],
                "prompt": prompt,
                "arguments": arguments,
                "response": response,
                "error": effect.get("diagnostic"),
            }
        )
    return {**node, "operations": operations}


def greeting_config(root):
    """One tiny committed fixture, independent of machine-specific smoke-test files."""
    source = root / "fixture"
    if not source.exists():
        source.mkdir(parents=True)
        (source / "greeting.py").write_text('def greeting(name):\n    return f"Hello {name}"\n')
        (source / "test_greeting.py").write_text(
            "import unittest\nfrom greeting import greeting\n\n"
            "class GreetingTest(unittest.TestCase):\n"
            "    def test_greeting(self):\n"
            '        self.assertEqual(greeting("Codex"), "Hello, Codex!")\n'
        )
        for argv in (
            ["init", "-q"],
            ["add", "."],
            [
                "-c",
                "user.name=PolyInference Test",
                "-c",
                "user.email=test@localhost",
                "commit",
                "-qm",
                "Disposable greeting fixture",
            ],
        ):
            subprocess.run(["git", "-C", str(source), *argv], check=True, capture_output=True)
    endpoint = Endpoint(
        protocol="codex_app_server",
        model="gpt-6.1-sol",
        max_context_tokens=128000,
        reserved_context_tokens=256000,
        max_inflight=1,
        timeout_seconds=180,
        inference_location="cloud",
    )
    return AgentConfig(
        prepare_repository=True,
        shell_execution="trusted",
        repository=str(source),
        objective=(
            "Fix greeting(name) to return exactly Hello, {name}! with the comma and exclamation mark. "
            "Preserve its public signature. Change only greeting.py. Use one small worker task and "
            "run the greeting check."
        ),
        allowed_write_paths=["greeting.py"],
        closure_paths=["greeting.py", "test_greeting.py"],
        checks=[Check(name="greeting", argv=[sys.executable, "-m", "unittest", "-q"])],
        check_execution="trusted",
        local=Endpoint(
            protocol="anthropic",
            base_url="https://api.anthropic.com/v1",
            model="claude-haiku-5-5",
            api_key_env="ANTHROPIC_API_KEY",
            max_context_tokens=128000,
            reserved_context_tokens=256000,
            max_inflight=1,
            timeout_seconds=180,
            inference_location="cloud",
        ),
        cloud=endpoint.model_copy(update={"brokered_tools": True}),
        role_bindings={"worker": "local", "senior": "cloud", "specialist": "cloud"},
        max_workers=1,
        max_sprints=9,
        limits=default_limits().model_copy(
            update={"max_input_tokens_per_call": 96000, "max_output_tokens_per_call": 8000}
        ),
    )


class TestUI:
    __test__ = False

    def __init__(self, root, config_path=None, state=None, runner=execute):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.config_path = Path(config_path).resolve() if config_path else None
        self.runner = runner
        self.lock = threading.RLock()
        self.active = None
        self.runs = {}
        self.cache = {}
        self.cost_cache = {}
        for path in self.root.glob("runs/*/ui-run.json"):
            metadata = json.loads(path.read_text())
            self.runs[metadata["id"]] = metadata
        if state:
            state = Path(state).resolve()
            if not (state / "records.sqlite").is_file():
                raise ValueError("State directory has no records.sqlite")
            run_id = "saved-" + hashlib.sha256(str(state).encode()).hexdigest()[:12]
            self.runs[run_id] = {
                "id": run_id,
                "state": str(state),
                "created_at": "",
                "error": None,
            }

    def configuration(self):
        with self.lock:
            return load_config(self.config_path) if self.config_path else greeting_config(self.root)

    def repository_options(self, path):
        base = self.configuration()
        root, files = project(path)
        original = root == base.repo_path or self.config_path is not None
        argv = base.checks[0].argv if original else suggested_check(root, files)
        return {
            "repository": str(root),
            "check_command": shlex.join(argv),
            "file_count": len(files),
            "clear_objective": not original,
            "scope": "Configured file scope" if self.config_path else "Selected project directory",
        }

    def configure_run(self, path=None, check_command=None):
        config = self.configuration()
        updates = {}
        if path is not None:
            root, files = project(path, clean=True)
            updates["repository"] = str(root)
            if root != config.repo_path and self.config_path is None:
                updates.update(
                    allowed_write_paths=files or ["README.md"], closure_paths=files, write_scope="project"
                )
                argv = (
                    shlex.split(check_command) if check_command is not None else suggested_check(root, files)
                )
                if not argv:
                    raise ValueError("Enter a check command for the selected repository")
                updates["checks"] = [Check(name="tests", argv=argv)]
        if "checks" not in updates and check_command is not None:
            argv = shlex.split(check_command)
            if not argv:
                raise ValueError("Enter a check command")
            updates["checks"] = [
                Check(
                    name=config.checks[0].name, argv=argv, timeout_seconds=config.checks[0].timeout_seconds
                ),
                *config.checks[1:],
            ]
        return AgentConfig.model_validate({**config.model_dump(), **updates})

    def cost(self, state, records):
        signature = tuple(
            (
                key,
                value["state"],
                tuple(ref["digest"] for ref in (value.get("result") or {}).get("output_refs", [])),
            )
            for key, value in sorted(records.items())
            if key.startswith("effect/")
        )
        if self.cost_cache.get(state, (None,))[0] != signature:
            self.cost_cache[state] = (signature, run_cost(records, lambda ref: read_artifact(state, ref)))
        return self.cost_cache[state][1]

    async def export(self, run_id):
        view = await self.view(run_id)
        state = self.runs[run_id]["state"]
        records = read_records(state)
        processes = []
        for process in view["processes"]:
            nodes = []
            for node in process["nodes"]:
                original = self.cache[run_id][2][node["id"]]
                try:
                    nodes.append(detail(state, original, records))
                except (ValueError, OSError) as exc:
                    nodes.append({**original, "export_error": str(exc)})
            processes.append({**process, "nodes": nodes})
        effects, inference_attempts = [], []
        for key, effect in records.items():
            attempt = key.startswith("inference-attempt/")
            if not attempt and not key.startswith("effect/"):
                continue
            outputs = []
            for ref in (effect.get("result") or {}).get("output_refs", []):
                try:
                    text = read_artifact(state, ref)
                    try:
                        output = json.loads(text)
                    except ValueError:
                        output = text
                    outputs.append({"ref": ref, "value": output})
                except (ValueError, OSError) as exc:
                    outputs.append({"ref": ref, "error": str(exc)})
            exported = {"record_ref": key, **effect, "outputs": outputs}
            if attempt:
                # A replacement may differ from the logical request. Export the
                # actual attempted context with its original trust/provenance.
                parts = []
                for part in effect["request"]["payload"].get("context", {}).get("parts", []):
                    try:
                        parts.append({**part, "text": read_artifact(state, part["content"])})
                    except (ValueError, OSError) as exc:
                        parts.append({**part, "export_error": str(exc)})
                inference_attempts.append({**exported, "context_parts": parts})
            else:
                effects.append(exported)
        config_path = Path(state).parent / "config.json"
        return {
            "schema_version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "run": {key: value for key, value in view.items() if key != "processes"},
            "configuration": json.loads(config_path.read_text()) if config_path.is_file() else None,
            "processes": processes,
            "effects": effects,
            "inference_attempts": inference_attempts,
            "retry_windows": {key: value for key, value in records.items() if key.startswith("retry/")},
            "check_diagnoses": {key: value for key, value in records.items() if key.startswith("diagnosis/")},
            "completion_reviews": {
                key: value for key, value in records.items() if key.startswith("completion-review/")
            },
            "review_artifacts": {
                key: value for key, value in records.items() if key.startswith("review-artifact/")
            },
            "reports": [value for key, value in records.items() if key.startswith("report/")],
            "steering": [value for key, value in sorted(records.items()) if key.startswith("steering/")],
            "run_record": records.get("app/run"),
            "repository_setup": records.get("repository/setup"),
        }

    def steer(self, run_id, text):
        if run_id not in self.runs:
            raise KeyError("Run not found")
        return record_steering(self.runs[run_id]["state"], text)

    def save(self, metadata):
        target = self.root / "runs" / metadata["id"] / "ui-run.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(metadata, indent=2))
        temporary.replace(target)

    def start(self, objective=None, repository_path=None, check_command=None, base_branch=None):
        with self.lock:
            if self.active:
                raise ValueError("A test is already running")
            config = self.configure_run(repository_path, check_command)
            if base_branch is not None:
                if not isinstance(base_branch, str) or len(base_branch) > 256:
                    raise ValueError("Enter a valid base branch")
                config = config.model_copy(update={"base_branch": base_branch.strip() or None})
            if objective is not None:
                if not isinstance(objective, str) or not objective.strip() or len(objective) > 16000:
                    raise ValueError("Enter a test objective of 1–16000 characters")
                config = config.model_copy(update={"objective": objective.strip()})
            run_id = uuid.uuid4().hex[:12]
            directory = self.root / "runs" / run_id
            directory.mkdir(parents=True)
            config = config.model_copy(update={"state_directory": str(directory / "state")})
            (directory / "config.json").write_text(config.model_dump_json(indent=2))
            metadata = {
                "id": run_id,
                "state": config.state_directory,
                "repository": config.repository,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
            self.runs[run_id] = metadata
            self.active = run_id
            self.save(metadata)

        def drive():
            try:
                asyncio.run(self.runner(config))
            except Exception as exc:
                metadata["error"] = str(exc)[:4000]
            finally:
                with self.lock:
                    self.save(metadata)
                    self.active = None

        threading.Thread(target=drive, name="polyinference-test", daemon=True).start()
        return run_id

    def summary(self, metadata):
        records = read_records(metadata["state"])
        run = records.get("app/run", {})
        status = (
            "running"
            if self.active == metadata["id"]
            else "failed"
            if metadata.get("error")
            else run.get("status", "interrupted")
        )
        if status == "active":
            status = "interrupted"
        source = metadata.get("repository")
        config_path = Path(metadata["state"]).parent / "config.json"
        configuration = json.loads(config_path.read_text()) if config_path.is_file() else {}
        if not source:
            source = configuration.get("repository")
        return {
            **metadata,
            "status": status,
            "objective": run.get("objective", ""),
            "error": metadata.get("error"),
            "repository": source,
            "cost": self.cost(metadata["state"], records),
            "development_allocation": accounting(
                records, configuration.get("senior_development_fraction", 0.1)
            ),
            "steering_received": run.get("steering_received", 0),
            "steering_applied": run.get("steering_applied", 0),
        }

    async def view(self, run_id):
        if run_id not in self.runs:
            raise KeyError("Run not found")
        metadata = self.runs[run_id]
        summary = self.summary(metadata)
        signature = (
            summary["status"],
            *(
                (path.stat().st_mtime_ns, path.stat().st_size) if path.exists() else (0, 0)
                for path in (
                    Path(metadata["state"]) / "checkpoints.sqlite",
                    Path(metadata["state"]) / "checkpoints.sqlite-wal",
                )
            ),
        )
        if self.cache.get(run_id, (None,))[0] == signature:
            return {**self.cache[run_id][1], **summary}
        records = read_records(metadata["state"])
        processes = await node_history(metadata["state"], summary["status"] == "running")
        details = {}
        for process in processes:
            record = records.get("process/" + process["id"], {})
            process["role"] = "controller" if process["id"] == "controller" else record.get("role", "process")
            for node in process["nodes"]:
                node["process_id"] = process["id"]
                details[node["id"]] = node
            process["nodes"] = [
                {key: value for key, value in node.items() if key not in {"input", "output"}}
                for node in process["nodes"]
            ]
        result = {**summary, "processes": processes}
        self.cache[run_id] = (signature, result, details)
        return result

    async def node(self, run_id, node_id):
        await self.view(run_id)
        node = self.cache[run_id][2].get(node_id)
        if node is None:
            raise KeyError("Node not found")
        state = self.runs[run_id]["state"]
        return detail(state, node, read_records(state))


def make_server(manager, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def allowed_host(self):
            return self.headers.get("Host") in {
                f"localhost:{self.server.server_port}",
                f"127.0.0.1:{self.server.server_port}",
            }

        def respond(self, status, value, content_type="application/json", filename=None):
            body = value.encode() if isinstance(value, str) else json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if filename:
                self.send_header("Content-Disposition", 'attachment; filename="' + filename + '"')
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.allowed_host():
                return self.respond(403, {"error": "Local access only"})
            url = urlsplit(self.path)
            query = parse_qs(url.query)
            try:
                if url.path == "/":
                    return self.respond(200, Path(__file__).with_name("ui.html").read_text(), "text/html")
                if url.path == "/api/runs":
                    runs = [manager.summary(value) for value in list(manager.runs.values())]
                    config = manager.configuration()
                    unique = {run["state"]: run["cost"] for run in runs}
                    return self.respond(
                        200,
                        {
                            "runs": sorted(runs, key=lambda run: run["created_at"], reverse=True),
                            "objective": config.objective,
                            "repository": config.repository,
                            "check_command": shlex.join(config.checks[0].argv),
                            "base_branch": config.base_branch,
                            "browse_root": str(Path.cwd().parent),
                            "total_cost": combine_costs(unique.values()),
                            "configuration": str(manager.config_path)
                            if manager.config_path
                            else "Haiku juniors + Codex setup/senior · 90/10 development · 9 sprints",
                        },
                    )
                if url.path == "/api/directories":
                    return self.respond(200, directories(query.get("path", [str(Path.cwd().parent)])[0]))
                if url.path == "/api/repository":
                    return self.respond(200, manager.repository_options(query["path"][0]))
                if url.path == "/api/export":
                    run_id = query["id"][0]
                    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", run_id)
                    return self.respond(
                        200, asyncio.run(manager.export(run_id)), filename="polyinference-" + safe + ".json"
                    )
                if url.path == "/api/run":
                    return self.respond(200, asyncio.run(manager.view(query["id"][0])))
                if url.path == "/api/node":
                    return self.respond(200, asyncio.run(manager.node(query["run"][0], query["id"][0])))
                return self.respond(404, {"error": "Not found"})
            except KeyError:
                self.respond(404, {"error": "Run or node not found"})
            except (ValueError, OSError, sqlite3.Error, subprocess.SubprocessError) as exc:
                self.respond(400, {"error": str(exc)})

        def do_POST(self):
            expected = {
                f"http://localhost:{self.server.server_port}",
                f"http://127.0.0.1:{self.server.server_port}",
            }
            if not self.allowed_host() or self.headers.get("Origin") not in expected:
                return self.respond(403, {"error": "Use the local test page"})
            if self.path not in {"/api/run", "/api/steer"}:
                return self.respond(404, {"error": "Not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536 or self.headers.get("Content-Type") != "application/json":
                    raise ValueError("Expected a small JSON request")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Expected an object")
                if self.path == "/api/steer":
                    sequence = manager.steer(data.get("id"), data.get("text"))
                    return self.respond(202, {"sequence": sequence})
                run_id = manager.start(
                    data.get("objective"),
                    data.get("repository"),
                    data.get("check_command"),
                    data.get("base_branch"),
                )
                self.respond(202, {"id": run_id})
            except KeyError:
                self.respond(404, {"error": "Run not found"})
            except (ValueError, OSError, subprocess.SubprocessError) as exc:
                self.respond(400, {"error": str(exc)})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765, config_path=None, state=None):
    manager = TestUI(Path.cwd() / ".polyinference" / "ui", config_path, state)
    server = make_server(manager, port)
    print(f"PolyInference test UI: http://localhost:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
