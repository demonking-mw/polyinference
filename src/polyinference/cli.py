"""Command line entry points; no credentials are written to state."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .agent.controller import ProjectAgent
from .agent.services import AgentServices
from .config import AgentConfig
from .runtime.kernel import KernelRuntime
from .runtime.storage import Conflict, Records


def load_config(path):
    source = Path(path).resolve()
    config = AgentConfig.model_validate_json(source.read_text())
    return config.model_copy(
        update={
            "repository": str((source.parent / config.repository).resolve()),
            "state_directory": str((source.parent / config.state_directory).resolve()),
        }
    )


async def execute(config):
    runtime = KernelRuntime(config)
    try:
        await runtime.open()
        app = AgentServices(runtime, config)
        engine = ProjectAgent(app)
        await engine.run()
        return app.get("app/run")
    finally:
        await runtime.close()


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
    item = sub.add_parser("ui")
    item.add_argument("--port", type=int, default=8765)
    item.add_argument("--config")
    item.add_argument("--state")
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
    args = parser.parse_args()
    try:
        if args.command == "reconcile":

            async def recover():
                runtime = KernelRuntime(load_config(args.config))
                try:
                    await runtime.open()
                    await runtime.reconcile_stopped(args.operation_id, Path(args.evidence).read_text())
                    return runtime.diagnostics()
                finally:
                    await runtime.close()

            print(json.dumps(asyncio.run(recover()), indent=2))
            return
        if args.command == "ui":
            from .ui import serve

            serve(args.port, args.config, args.state)
            return
        if args.command == "probe":
            print(json.dumps(asyncio.run(probe_endpoint(load_config(args.config), args.endpoint)), indent=2))
            return
        if args.command in {"run", "resume", "validate-config"}:
            config = load_config(args.config)
            if args.command == "validate-config":
                print("Configuration valid; endpoint availability has not been tested.")
                return
            result = asyncio.run(execute(config))
            print(json.dumps(result, indent=2))
            if result["status"] != "completed":
                sys.exit(2)
            return
        records = Records(Path(args.state_directory).resolve() / "records.sqlite")
        try:
            if args.command == "events":
                print(json.dumps(records.events(args.after), indent=2))
            elif args.command == "cancel":
                from .runtime.processes import request_cancel

                request_cancel(records, args.process_id, args.reason)
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
                initial = records.get("head/initial")[1]["code"]["commit_id"]
                final = records.get("head/provisional")[1]["code"]["commit_id"]
                patch = subprocess.check_output(
                    [
                        "git",
                        "--git-dir",
                        str(Path(args.state_directory).resolve() / "repository.git"),
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
