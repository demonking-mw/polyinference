"""Command line entry points; no credentials are written to state."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .agent.controller import ProjectAgent
from .agent.services import AgentServices
from .config import AgentConfig
from .history import save_run_history
from .runtime.kernel import KernelRuntime
from .runtime.storage import Conflict, Records


def load_saved_credentials():
    """Read the private credential file as data, without executing shell code."""
    if "ANTHROPIC_API_KEY" in os.environ:
        return
    path = Path.home() / ".config" / "polyinference" / "anthropic.env"
    if not path.is_file():
        return
    for number, line in enumerate(path.read_text().splitlines(), 1):
        try:
            parts = shlex.split(line, comments=True)
        except ValueError:
            raise ValueError(f"Invalid credential file syntax at {path}:{number}") from None
        if parts[:1] == ["export"]:
            parts = parts[1:]
        if not parts:
            continue
        if len(parts) != 1 or "=" not in parts[0]:
            raise ValueError(f"Expected KEY=value at {path}:{number}")
        name, value = parts[0].split("=", 1)
        if name == "ANTHROPIC_API_KEY":
            os.environ.setdefault(name, value)


def load_config(path, *, context=None):
    source = Path(path).resolve()
    text = source.read_text()
    model = AgentConfig
    document = json.loads(text) if '"inference_simulation"' in text else None
    if isinstance(document, dict) and "inference_simulation" in document:
        from .agent.inference_simulation import SimulationAgentConfig

        model = SimulationAgentConfig
        context = {**(context or {}), "resolve_environment_capacity": False}
    config = model.model_validate_json(text, context=context)
    return config.model_copy(
        update={
            "repository": str((source.parent / config.repository).resolve()),
            "state_directory": str((source.parent / config.state_directory).resolve()),
            **({"output_directory": str((source.parent / config.output_directory).resolve())}
               if config.output_directory is not None else {}),
        }
    )


async def apply_resume(engine, request_ref):
    """Compatibility entry point; coding policy belongs to the agent."""
    if engine.app.ports.records.get("resume-outcome/" + request_ref):
        raise ValueError("This resume request has already been handled")
    await engine.resume(request_ref)


async def execute(config, *, save_history=True, retry_task=None, retry_reason=None, retry_output_reason=None,
                  resume_request_ref=None):
    metadata = {
        "id": uuid.uuid4().hex[:12],
        "state": str(config.state_path),
        "repository": config.repository,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
    runtime = KernelRuntime(config)
    try:
        await runtime.open()
        if getattr(config, "inference_simulation", None) is not None:
            from .agent.inference_simulation import install_simulation

            await install_simulation(runtime, config.inference_simulation)
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        if resume_request_ref is not None:
            await engine.initialize()
            await engine.resume(resume_request_ref)
        if retry_task is not None:
            await engine.initialize()
            await engine.retry_worker(retry_task, retry_reason or "explicit model recovery")
        if retry_output_reason is not None:
            await engine.initialize()
            engine.retry_outputs(retry_output_reason)
        await engine.run()
        return app.get("app/run")
    except BaseException as exc:
        metadata["error"] = str(exc)[:4000] or type(exc).__name__
        raise
    finally:
        try:
            await runtime.close()
        finally:
            if save_history:
                metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
                await save_run_history(config, metadata=metadata)


async def probe_endpoint(config, name):
    """One small readiness request; never starts an application run."""
    from .runtime.codex import CodexAppServer
    from .runtime.inference import HTTPInference

    endpoint = getattr(config, name)
    messages = [{"role": "user", "content": 'Return only {"status":"ready"}. Use no tools.'}]
    if endpoint.protocol == "codex_proxy":
        raise ValueError("Probe the proxy through its separately pinned snapshot configuration")
    client = CodexAppServer(endpoint) if endpoint.protocol == "codex_app_server" else HTTPInference(endpoint)
    try:
        if endpoint.protocol == "codex_app_server":
            with tempfile.TemporaryDirectory(prefix="polyinference-probe-") as directory:
                result = await client.generate_job(
                    messages,
                    Path(directory),
                    {
                        "type": "object",
                        "properties": {"status": {"type": "string"}},
                        "required": ["status"],
                        "additionalProperties": False,
                    },
                )
        else:
            result = await client.generate(messages, 64)
        return {
            "endpoint": name,
            "protocol": endpoint.protocol,
            "model": result["model"],
            "reply": result["text"],
            "usage": result["usage"],
        }
    finally:
        await client.close()


def record_steering(state_directory, text):
    """Share the same atomic steering write between the CLI and local UI."""
    if not isinstance(text, str) or not text.strip() or len(text) > 16000:
        raise ValueError("Enter steering instructions of 1–16000 characters")
    path = Path(state_directory).resolve() / "records.sqlite"
    if not path.is_file():
        raise ValueError("Wait until the run has initialized")
    records = Records(path)
    try:
        for _ in range(5):
            retained = records.get("app/run")
            if not retained:
                raise ValueError("Wait until the run has initialized")
            version, run = retained
            if run["status"] == "completed":
                raise ValueError("Completed run is immutable; start a new run")
            sequence = run["steering_received"] + 1
            try:
                records.compare_and_publish(
                    {"app/run": version},
                    {
                        "app/run": {
                            **run,
                            "status": "active" if run["status"] == "paused" else run["status"],
                            "starts_closed": True,
                            "steering_received": sequence,
                            "captured_workers": sorted(
                                set(run["captured_workers"]) | set(run["active_workers"])
                            ),
                            "completion_proposed": False,
                        }
                    },
                    {f"steering/{sequence:08d}": {"sequence": sequence, "text": text.strip()}},
                )
                return sequence
            except Conflict:
                continue
        raise ValueError("Run state changed repeatedly; please send the update again")
    finally:
        records.db.close()


def main():
    parser = argparse.ArgumentParser(description="PolyInference portable LangGraph coding agent")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "resume", "validate-config"):
        item = sub.add_parser(name)
        item.add_argument("config")
        if name == "resume":
            item.add_argument("--text", default="", help="Optional instructions for continuing the run")
    item = sub.add_parser("ui")
    item.add_argument("--port", type=int, default=8765)
    item.add_argument("--config")
    item.add_argument("--state")
    def simulation_slots(value):
        try:
            count = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("--sim-batch requires an integer from 1 to 16") from None
        if not 1 <= count <= 16:
            raise argparse.ArgumentTypeError("--sim-batch requires an integer from 1 to 16")
        return count
    item.add_argument("--sim-batch", type=simulation_slots, metavar="N",
                      help="Invocation-only remote Haiku simulation with N workers/slots (1..16)")
    item.add_argument("--sim-inference", action="store_true",
                      help="Show opt-in normal/buggy/slow-buggy inference controls before Start")
    item = sub.add_parser("probe")
    item.add_argument("config")
    item.add_argument("--endpoint", choices=["local", "cloud"], default="cloud")
    item = sub.add_parser("status")
    item.add_argument("state_directory")
    item = sub.add_parser("steer")
    item.add_argument("state_directory")
    item.add_argument("text")
    item = sub.add_parser("export")
    item.add_argument("state_directory")
    item.add_argument("output")
    item = sub.add_parser("operation")
    item.add_argument("state_directory")
    item.add_argument("operation_id")
    item = sub.add_parser("events")
    item.add_argument("state_directory")
    item.add_argument("--after", type=int, default=0)
    item = sub.add_parser("cancel")
    item.add_argument("state_directory")
    item.add_argument("process_id")
    item.add_argument("--reason", default="operator cancellation")
    item = sub.add_parser("reconcile")
    item.add_argument("config")
    item.add_argument("operation_id")
    item.add_argument(
        "--confirm-stopped",
        action="store_true",
        required=True,
        help="Attest that provider execution AND host descendants have ended",
    )
    item.add_argument("--evidence", required=True, help="Text file recording termination evidence")
    item = sub.add_parser("retry-model")
    item.add_argument("config")
    item.add_argument("task_id")
    item.add_argument("--reason", required=True)
    item = sub.add_parser("retry-output")
    item.add_argument("config")
    item.add_argument("--reason", required=True)
    args = parser.parse_args()
    try:
        load_saved_credentials()
        if args.command == "retry-output":
            result = asyncio.run(execute(load_config(args.config), retry_output_reason=args.reason))
            print(json.dumps(result, indent=2))
            if result["status"] != "completed":
                sys.exit(2)
            return
        if args.command == "retry-model":
            result = asyncio.run(execute(load_config(args.config), retry_task=args.task_id, retry_reason=args.reason))
            print(json.dumps(result, indent=2))
            if result["status"] != "completed":
                sys.exit(2)
            return
        if args.command == "reconcile":

            async def recover():
                runtime = KernelRuntime(load_config(args.config))
                try:
                    await runtime.open()
                    AgentServices(runtime, runtime.config)
                    await runtime.reconcile_stopped(args.operation_id, Path(args.evidence).read_text())
                    return runtime.diagnostics()
                finally:
                    await runtime.close()

            print(json.dumps(asyncio.run(recover()), indent=2))
            return
        if args.command == "ui":
            from .ui import serve

            serve(args.port, args.config, args.state, sim_batch=args.sim_batch,
                  **({"sim_inference": True} if args.sim_inference else {}))
            return
        if args.command == "probe":
            print(json.dumps(asyncio.run(probe_endpoint(load_config(args.config), args.endpoint)), indent=2))
            return
        if args.command in {"run", "resume", "validate-config"}:
            config = load_config(args.config)
            if args.command == "validate-config":
                print("Configuration valid; endpoint availability has not been tested.")
                return
            request_ref = None
            if args.command == "resume":
                from .runtime.processes import request_resume

                records = Records(config.state_path / "records.sqlite")
                try:
                    request_ref = request_resume(records, text=args.text)
                finally:
                    records.db.close()
            result = asyncio.run(execute(config, resume_request_ref=request_ref))
            print(json.dumps(result, indent=2))
            if result["status"] != "completed":
                sys.exit(2)
            return
        records = Records(Path(args.state_directory).resolve() / "records.sqlite")
        try:
            if args.command == "events":
                print(json.dumps(records.events(args.after), indent=2))
            elif args.command == "cancel":
                from .agent.services import close_for_cancellation
                from .runtime.processes import request_cancel

                request_cancel(records, args.process_id, args.reason)
                close_for_cancellation(records, args.process_id)
                print("Cancellation recorded; the current effect settles before the process stops.")
            elif args.command == "status":
                run = records.get("app/run")
                report = {
                    "run": run[1] if run else None,
                    "processes": [value for _, _, value in records.scan("process-status/")],
                    "reservations": [
                        value for _, _, value in records.scan("reservation/") if value["state"] == "held"
                    ],
                    "owners": [value for _, _, value in records.scan("permit/") if value.get("process_id")],
                    "provisional": records.get("head/provisional"),
                    "reviewed": records.get("head/reviewed"),
                    "repository_setup": records.get("repository/setup"),
                    "repository_summary": records.get("coding/repository-summary"),
                    "tasks": [
                        {
                            **body,
                            "resolved": bool(
                                body.get("report_ref")
                                and records.get("resolution/" + body["report_ref"])
                                and records.get("resolution/" + body["report_ref"])[1]["action"]
                                in {"keep", "revert"}
                            ),
                        }
                        for _, _, body in records.scan("task/")
                    ],
                    "uncertain_operations": [
                        key[7:] for key, _, value in records.scan("effect/") if value["state"] == "uncertain"
                    ],
                }
                print(json.dumps(report, indent=2))
            elif args.command == "export":
                setup = records.get("repository/setup")
                git_directory = (setup[1].get("common_git_directory") if setup else None) or str(
                    Path(args.state_directory).resolve() / "repository.git")
                initial = records.get("head/initial")[1]["code"]["commit_id"]
                final = records.get("head/provisional")[1]["code"]["commit_id"]
                patch = subprocess.check_output(
                    [
                        "git",
                        "--git-dir",
                        git_directory,
                        "diff",
                        "--binary",
                        initial,
                        final,
                    ]
                )
                Path(args.output).resolve().write_bytes(patch)
                print(str(Path(args.output).resolve()))
            elif args.command == "operation":
                value = records.get("effect/" + args.operation_id)
                print(json.dumps(value[1] if value else None, indent=2))
            else:
                sequence = record_steering(args.state_directory, args.text)
                print(f"Steering {sequence} recorded; started workers finish before review.")
        finally:
            records.db.close()
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
