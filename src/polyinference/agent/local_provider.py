"""Prepare local provider settings and bootstrap an explicitly selected UI profile."""

import json
import os
import shutil
import subprocess
import sys
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import httpx


def _runtime_command(executable, profile, action, *options, allow_failed=False):
    try:
        result = subprocess.run([executable, "runtime", action, "--profile", profile,
                                 *options, "--output", "json"], capture_output=True, text=True,
                                timeout=330 if action == "start" else 40 if action == "stop" else 15)
        facts = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise ValueError(f"Strata {action} failed for profile {profile}: {exc}") from exc
    if not isinstance(facts, dict):
        raise ValueError(f"Strata {action} returned invalid runtime status for {profile}")
    if result.returncode and not (allow_failed or facts.get("state") == "starting"):
        raise ValueError(f"Strata {action} failed for profile {profile}: {facts.get('error', facts)}")
    return facts


@dataclass
class OwnedStrataRuntime:
    """A UI-started runtime; stop only the captured owner/instance, once."""

    executable: str
    profile: str
    owner_id: str
    instance_id: str | None = None
    _closed: bool = field(default=False, init=False)

    def close(self):
        if self._closed:
            return
        self._closed = True
        options = ["--wait", "30", "--if-owner-id", self.owner_id]
        if self.instance_id is not None:
            options += ["--if-instance-id", self.instance_id]
        try:
            result = _runtime_command(self.executable, self.profile, "stop", *options)
            if result.get("state") != "stopped" or result.get("ok") is False:
                raise ValueError(str(result.get("error", result)))
        except ValueError as exc:
            # Do not mask the original UI/startup failure or kill a replacement.
            # Strata's --die-with-pid watcher remains the process-exit fallback.
            print(f"Strata cleanup failed for profile {self.profile}: {exc}", file=sys.stderr, flush=True)


def ensure_ui_local_provider(config):
    """Prepare the provider, returning cleanup ownership only for a new runtime."""
    profile = config.local_strata_profile
    if profile is None or config.local.inference_location != "local":
        return
    if urlsplit(config.local.base_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Automatic Strata startup requires a loopback local endpoint")
    executable = shutil.which("strata")
    if executable is None:
        candidate = Path.home() / ".local" / "bin" / "strata"
        if candidate.is_file():
            executable = str(candidate)
    if executable is None:
        raise ValueError("Install Strata or add it to PATH before launching the configured UI")

    def command(action, *options):
        return _runtime_command(executable, profile, action, *options, allow_failed=action == "start")

    status = command("status")
    preparation = sync_local_provider(config)
    if preparation["restart_required"] and status.get("state") != "stopped":
        raise ValueError("Strata launch settings changed; stop the existing profile before relaunching the UI")
    owned = None
    try:
        if status.get("state") == "stopped":
            print(f"Starting Strata profile {profile}; loading the local model...", flush=True)
            status = command("start", "--wait", "300", "--die-with-pid", str(os.getpid()),
                             "--shutdown-timeout", "10")
            # A racing start that lost the profile lease returns no new owner.
            # Never stop by profile name alone, including on startup failure.
            if not status.get("owner_id"):
                raise ValueError(f"Strata start returned no runtime owner: {status.get('error', status)}")
            owned = OwnedStrataRuntime(executable, profile, status["owner_id"], status.get("instance_id"))
        deadline = time.monotonic() + 300
        while status.get("state") == "starting" and time.monotonic() < deadline:
            time.sleep(1)
            status = command("status")
        if owned is not None:
            if status.get("owner_id") != owned.owner_id:
                raise ValueError("Strata runtime owner changed during UI startup")
            if owned.instance_id is not None and status.get("instance_id") != owned.instance_id:
                raise ValueError("Strata runtime instance changed during UI startup")
            if owned.instance_id is None:
                owned.instance_id = status.get("instance_id")
        if status.get("state") != "ready" or not status.get("generation_ready"):
            raise ValueError(f"Strata profile {profile} is not generation-ready: {status.get('error', status)}")
        try:
            with httpx.Client(timeout=10, trust_env=False) as client:
                response = client.get(config.local.base_url.rstrip("/") + "/telemetry")
                response.raise_for_status()
                telemetry = response.json()
            model, work = telemetry.get("model", {}), telemetry.get("work", {})
            if (model.get("id") != config.local.model or not model.get("loaded")
                    or model.get("context") != config.local_token_limits.context_tokens
                    or work.get("slots_effective") != config.local.max_inflight):
                raise ValueError("Running Strata model/context/slots do not match the UI configuration")
        except (httpx.HTTPError, ValueError, AttributeError) as exc:
            raise ValueError(f"Strata profile {profile} readiness check failed: {exc}") from exc
        print(f"Strata ready: {config.local.model}, {model['context']} context, {work['slots_effective']} slots", flush=True)
        return owned
    except BaseException:
        if owned is not None:
            owned.close()
        raise


def strata_configuration(config, document):
    """Return a Strata launch document with input + output context capacity."""
    if not isinstance(document, dict):
        raise ValueError("Strata launch configuration must be a JSON object")
    result = deepcopy(document)
    args = result.get("args")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise ValueError("Strata launch configuration must contain an args string list")
    positions = [i for i, value in enumerate(args)
                 if value == "--max-context" or value.startswith("--max-context=")]
    if len(positions) > 1:
        raise ValueError("Strata launch configuration has an ambiguous --max-context")
    value = str(config.local_token_limits.context_tokens)
    if positions:
        index = positions[0]
        if args[index] == "--max-context":
            if index + 1 >= len(args) or not args[index + 1].isdecimal() or int(args[index + 1]) <= 0:
                raise ValueError("Strata launch configuration needs a positive --max-context value")
            args[index + 1] = value
        else:
            previous = args[index].split("=", 1)[1]
            if not previous.isdecimal() or int(previous) <= 0:
                raise ValueError("Strata launch configuration needs a positive --max-context value")
            args[index] = "--max-context=" + value
    else:
        args.extend(["--max-context", value])
    return result


def sync_local_provider(config, path=None):
    """Write startup settings only; never signal, reload or start a provider."""
    selected = path or config.local_strata_config
    pair = config.local_token_limits
    facts = {"input_tokens": pair.input_tokens, "output_tokens": pair.output_tokens,
             "strata_max_context": pair.context_tokens, "cloud_token_caps": None,
             "restart_required": False}
    if selected is None:
        return facts
    if config.token_limits_for_binding("local") is None:
        raise ValueError("Strata startup configuration requires a capped local endpoint, not a native cloud harness")
    target = Path(selected).resolve()
    raw = target.read_bytes()
    document = json.loads(raw)
    updated = strata_configuration(config, document)
    if updated != document:
        backup = target.with_name(target.name + ".before-polyinference")
        if not backup.exists():
            backup.write_bytes(raw)
            backup.chmod(target.stat().st_mode & 0o777)
        temporary = target.with_name(target.name + ".polyinference-tmp")
        temporary.write_text(json.dumps(updated, indent=2) + "\n")
        temporary.chmod(target.stat().st_mode & 0o777)
        temporary.replace(target)
        facts["restart_required"] = True
    facts["strata_config"] = str(target)
    return facts
