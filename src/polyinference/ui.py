"""A loopback-only test runner and viewer for the standalone runtime."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shlex
import sqlite3
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .cli import execute, load_config, record_steering
from .config import AgentConfig
from .costs import combine_costs, run_cost
from .domain import Check
from .history import save_run_history
from .runtime.storage import Records
from .snapshots import detail, export_run, node_history, read_artifact, read_records, run_summary
from .ui_agents import agent_snapshot
from .ui_os import activity, read_snapshot, runtime_view
from .ui_repository import directories, project


class RunStartError(ValueError):
    def __init__(self, metadata):
        super().__init__(metadata["error"])
        self.metadata = metadata


def terminal_event(run_id, message):
    message = " ".join(str(message).split())[:300]
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{run_id}] {message}", flush=True)


def reporting_failure(errors, exc):
    message = f"{type(exc).__name__}: {exc}"[:500]
    if errors is not None and message not in errors and len(errors) < 20:
        errors.append(message)


def report_terminal_event(run_id, message, errors=None):
    try:
        terminal_event(run_id, message)
    except Exception as exc:
        reporting_failure(errors, exc)


def report_event_values(run_id, event, states, errors):
    values = {key: change.get("value") or {} for key, change in event.get("changes", {}).items()}
    values.update(event.get("immutable_values") or {})
    for key, value in values.items():
        if key.startswith("task/"):
            state = value.get("execution")
            if states.get(key) == state:
                continue
            states[key] = state
            label = {
                "in_progress": "started", "completed": "completed",
                "interrupted": "interrupted", "cancelled": "cancelled",
            }.get(state)
            if label:
                reason = value.get("exception") or value.get("stop_reason")
                report_terminal_event(run_id, f"Task {key[5:]} {label}" + (f": {reason}" if reason else ""), errors)
        elif key.startswith("hazard/"):
            report_terminal_event(run_id, f"Issue {key[7:]}: {value.get('summary') or value.get('verdict')}", errors)
        elif key.startswith("effect/") and value.get("state") in {"failed", "uncertain"}:
            if states.get(key) != value["state"]:
                states[key] = value["state"]
                error = ((value.get("result") or {}).get("error") or {}).get("message")
                report_terminal_event(run_id, f"Error {key}: {value.get('diagnostic') or error or value['state']}", errors)


async def run_with_terminal_events(runner, config, run_id, reporting_errors=None):
    task = asyncio.create_task(runner(config))
    path = config.state_path / "records.sqlite"
    sequence, states = 0, {}
    while True:
        await asyncio.wait({task}, timeout=0.5)
        events = []
        try:
            if path.is_file():
                with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
                    if db.execute("SELECT 1 FROM sqlite_master WHERE name='events'").fetchone():
                        events = db.execute(
                            "SELECT sequence,body FROM events WHERE sequence>? ORDER BY sequence", (sequence,)
                        ).fetchall()
        except sqlite3.Error:
            pass  # The runtime may still be initializing; retry on the next tick.
        except Exception as exc:
            reporting_failure(reporting_errors, exc)
        for sequence, body in events:
            try:
                report_event_values(run_id, json.loads(body), states, reporting_errors)
            except Exception as exc:
                reporting_failure(reporting_errors, exc)
        if task.done():
            return await task


def greeting_config(root, *, context=None):
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
    from .agent.system_settings import ui_system_settings

    return AgentConfig.model_validate(dict(
        system=ui_system_settings(source),
        objective=(
            "Fix greeting(name) to return exactly Hello, {name}! with the comma and exclamation mark. "
            "Preserve its public signature. Change only greeting.py. Use one small worker task and "
            "run the greeting check."
        ),
        max_sprints=27,
    ), context=context)


class TestUI:
    __test__ = False

    def __init__(self, root, config_path=None, state=None, runner=partial(execute, save_history=False), *, sim_batch=None):
        if sim_batch is not None and (type(sim_batch) is not int or not 1 <= sim_batch <= 16):
            raise ValueError("--sim-batch requires an integer from 1 to 16")
        self.sim_batch = sim_batch
        self.validation_context = {"resolve_environment_capacity": False} if sim_batch is not None else None
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
            config = (load_config(self.config_path, context=self.validation_context) if self.config_path else
                      greeting_config(self.root, context=self.validation_context))
            if self.sim_batch is not None:
                from .agent.system_settings import simulation_config
                config = simulation_config(config, self.sim_batch)
            return config

    def simulation_label(self, config):
        return (f"Remote Anthropic simulation · {config.local.model} · {config.local.max_inflight} slots · "
                f"{config.max_workers} workers (maximums; independent ready work required)")

    def repository_options(self, path):
        base = self.configuration()
        root, files = project(path)
        original = root == base.repo_path or self.config_path is not None
        argv = base.checks[0].argv if original and base.checks else []
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
                argv = shlex.split(check_command) if check_command is not None else []
                updates["checks"] = [Check(name="tests", argv=argv)] if argv else []
        if "checks" not in updates and check_command is not None:
            argv = shlex.split(check_command)
            updates["checks"] = [
                Check(
                    name=config.checks[0].name if config.checks else "tests", argv=argv,
                    timeout_seconds=config.checks[0].timeout_seconds if config.checks else 60,
                ),
                *config.checks[1:],
            ] if argv else config.checks
        return AgentConfig.model_validate({**config.model_dump(), **updates}, context=self.validation_context)

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
        metadata = self.runs[run_id]
        config_path = Path(metadata["state"]).parent / "config.json"
        configuration = json.loads(config_path.read_text()) if config_path.is_file() else {}
        return await export_run(metadata, configuration, self.active == run_id)

    def steer(self, run_id, text):
        if run_id not in self.runs:
            raise KeyError("Run not found")
        return record_steering(self.runs[run_id]["state"], text)

    def save(self, metadata):
        target = self.root / "runs" / metadata["id"] / "ui-run.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(metadata, indent=2))
        temporary.replace(target)

    def record_start_failure(self, metadata, exc):
        """Keep rejected launches inspectable even when no agent initialized."""
        metadata.update(
            error=str(exc) or type(exc).__name__, failure_stage="startup",
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        records = Records(Path(metadata["state"]) / "records.sqlite")
        try:
            records.put_once("process/" + metadata["process_id"], {
                "process_id": metadata["process_id"], "role": "startup", "state": "failed",
                "error": metadata["error"], "error_type": type(exc).__name__,
                "created_at": metadata["created_at"], "finished_at": metadata["finished_at"],
            })
        finally:
            records.db.close()
        self.save(metadata)
        self.runs[metadata["id"]] = metadata

    def start(self, objective=None, repository_path=None, check_command=None, base_branch=None):
        run_id = uuid.uuid4().hex[:12]
        directory = self.root / "runs" / run_id
        directory.mkdir(parents=True)
        metadata = {
            "id": run_id, "process_id": "startup-" + run_id,
            "state": str(directory / "state"), "repository": repository_path,
            "objective": objective if isinstance(objective, str) else "",
            "created_at": datetime.now(timezone.utc).isoformat(), "error": None,
            "reporting_errors": [],
            "launch_request": {
                "objective": objective, "repository": repository_path,
                "check_command": check_command, "base_branch": base_branch,
            },
        }
        try:
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
                config = config.model_copy(update={"state_directory": metadata["state"]})
                config = AgentConfig.model_validate(config.model_dump(), context=self.validation_context)
                (directory / "config.json").write_text(config.model_dump_json(indent=2))
                metadata.update(repository=config.repository, objective=config.objective)
                if self.sim_batch is not None:
                    name = config.local.api_key_env
                    if not name or not os.environ.get(name, "").strip():
                        raise ValueError("Simulation requires a nonempty credential in local.api_key_env "
                                         f"({name or 'not configured'}); set it on the backend host")
                self.save(metadata)
                self.runs[run_id] = metadata
                self.active = run_id

            def drive():
                report_terminal_event(run_id, f"Run started: {config.objective}", metadata["reporting_errors"])
                try:
                    result = asyncio.run(run_with_terminal_events(
                        self.runner, config, run_id, metadata["reporting_errors"]
                    ))
                    status = result.get("outcome", "finished") if isinstance(result, dict) else "finished"
                    try:
                        status = read_records(config.state_path).get("app/run", {}).get("status", status)
                    except Exception as exc:
                        reporting_failure(metadata["reporting_errors"], exc)
                    report_terminal_event(run_id, f"Run {status}", metadata["reporting_errors"])
                except Exception as exc:
                    metadata["error"] = str(exc) or type(exc).__name__
                    try:
                        if not read_records(config.state_path).get("app/run"):
                            with self.lock:
                                self.record_start_failure(metadata, exc)
                    except Exception as reporting_exc:
                        reporting_failure(metadata["reporting_errors"], reporting_exc)
                    report_terminal_event(run_id, f"Error: {exc}", metadata["reporting_errors"])
                finally:
                    try:
                        metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
                        with self.lock:
                            self.save(metadata)
                        asyncio.run(save_run_history(config, self.root.parent / "history", metadata))
                    finally:
                        with self.lock:
                            self.active = None

            threading.Thread(target=drive, name="polyinference-test", daemon=True).start()
            return run_id
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
            with self.lock:
                if self.active == run_id:
                    self.active = None
                self.record_start_failure(metadata, exc)
            raise RunStartError(metadata) from exc

    def summary(self, metadata, records=None, active=None):
        active = self.active == metadata["id"] if active is None else active
        if records is None:
            records = read_records(metadata["state"])
        config_path = Path(metadata["state"]).parent / "config.json"
        configuration = json.loads(config_path.read_text()) if config_path.is_file() else {}
        return run_summary(metadata, records, configuration, active, self.cost(metadata["state"], records))

    async def view(self, run_id):
        if run_id not in self.runs:
            raise KeyError("Run not found")
        metadata = self.runs[run_id]
        active = self.active == run_id
        snapshot = read_snapshot(metadata["state"])
        records = snapshot["records"]
        summary = self.summary(metadata, records, active)
        config_path = Path(metadata["state"]).parent / "config.json"
        configuration = json.loads(config_path.read_text()) if config_path.is_file() else {}
        os_view = runtime_view(snapshot, configuration, summary["status"] == "running")
        agents = agent_snapshot(records, lambda ref: read_artifact(metadata["state"], ref))
        def checkpoint_signature(path):
            try:
                stat = path.stat()
                return stat.st_mtime_ns, stat.st_size
            except FileNotFoundError:
                # SQLite may checkpoint and remove its WAL between UI polls.
                return 0, 0

        signature = (
            summary["status"],
            *(
                checkpoint_signature(path)
                for path in (
                    Path(metadata["state"]) / "checkpoints.sqlite",
                    Path(metadata["state"]) / "checkpoints.sqlite-wal",
                )
            ),
        )
        if self.cache.get(run_id, (None,))[0] == signature:
            return {**self.cache[run_id][1], **summary, "os": os_view, "agents": agents}
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
        return {**result, "os": os_view, "agents": agents}

    def record(self, run_id, key):
        if run_id not in self.runs:
            raise KeyError("Run not found")
        snapshot = read_snapshot(self.runs[run_id]["state"])
        if key not in snapshot["records"]:
            raise KeyError("Record not found")
        return {"key": key, "revision": snapshot["revisions"][key], "value": snapshot["records"][key]}

    def activity_page(self, run_id, before=None):
        if run_id not in self.runs:
            raise KeyError("Run not found")
        snapshot = read_snapshot(self.runs[run_id]["state"])
        events = [event for event in snapshot["events"] if before is None or event["sequence"] < before]
        page = events[-120:]
        return {
            "rows": activity(page, snapshot["records"]), "has_older": len(events) > len(page),
            "first_sequence": page[0]["sequence"] if page else None,
            "last_sequence": page[-1]["sequence"] if page else None,
        }

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
                if url.path == "/ui-monitor.js":
                    return self.respond(
                        200, Path(__file__).with_name("ui-monitor.js").read_text(), "text/javascript"
                    )
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
                            "check_command": shlex.join(config.checks[0].argv) if config.checks else "",
                            "base_branch": config.base_branch,
                            "browse_root": str(Path.cwd().parent),
                            "total_cost": combine_costs(unique.values()),
                            "configuration": manager.simulation_label(config) if manager.sim_batch is not None else str(manager.config_path)
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
                if url.path == "/api/record":
                    return self.respond(200, manager.record(query["run"][0], query["key"][0]))
                if url.path == "/api/artifact":
                    metadata = manager.runs[query["run"][0]]
                    return self.respond(200, {"text": read_artifact(
                        metadata["state"], {"digest": query["digest"][0]}
                    )})
                if url.path == "/api/activity":
                    before = int(query["before"][0]) if "before" in query else None
                    return self.respond(200, manager.activity_page(query["run"][0], before))
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
            except RunStartError as exc:
                asyncio.run(save_run_history(None, manager.root.parent / "history", exc.metadata))
                self.respond(400, {
                    "id": exc.metadata["id"], "process_id": exc.metadata["process_id"],
                    "status": "failed", "error": str(exc),
                })
            except KeyError:
                self.respond(404, {"error": "Run not found"})
            except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
                self.respond(400, {"error": str(exc)})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765, config_path=None, state=None, *, sim_batch=None):
    manager = TestUI(Path.cwd() / ".polyinference" / "ui", config_path, state, sim_batch=sim_batch)
    if sim_batch is not None:
        print(manager.simulation_label(manager.configuration()), flush=True)
    server = make_server(manager, port)
    print(f"PolyInference OS console: http://localhost:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
