"""Local chat sessions and read-only OS inspection for general agents."""

from __future__ import annotations

import asyncio
import fcntl
import json
import logging
import os
import re
import shutil
import sqlite3
import threading
from collections import Counter
from functools import partial

from .config import RuntimeConfig
from .general_agents.os_v1 import run_v1, supports_model_endpoint, validate_v1_input
from .primitives import canonical, digest, now
from .ui_os import read_snapshot, runtime_view

AGENTS = {
    "simple": ("Simple", "Answer a question with optional document lookup", {"general": "General model"}),
    "supervisor": ("Supervisor", "Plan, delegate, and combine results",
                   {"local": "Local worker", "cloud": "Cloud planner and synthesis"}),
    "research": ("Research", "Find evidence in supplied documents",
                 {"local": "Local extraction", "cloud": "Cloud lead and report"}),
    "writer": ("Writer", "Draft, evaluate, and revise",
               {"local": "Local drafting and revision", "cloud": "Cloud planning and evaluation"}),
}
ACTIVE_EFFECTS = {"submitting", "active"}
TERMINAL = {"completed": "Succeeded", "failed": "Failed", "cancelled": "Cancelled"}
STEP_NAMES = {
    "decide": "Answer decision", "lookup": "Document lookup", "plan": "Plan",
    "work": "Local worker", "synthesize": "Synthesis", "evidence": "Evidence lookup",
    "extract": "Local extraction", "report": "Report", "brief": "Writing brief",
    "draft": "Draft", "evaluate": "Evaluation",
}
log = logging.getLogger(__name__)


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as file:
        file.write(canonical(value))
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)


def effect_unconfirmed(effect, live):
    result = effect.get("result") or {}
    return (effect.get("state") == "uncertain"
            or (not live and effect.get("state") in ACTIVE_EFFECTS)
            or result.get("execution_termination") == "unknown"
            or result.get("effects") == "unknown")


def process_view(row, spec, effects, lanes, live):
    state = row["state"]
    status = row["status"]
    wait = status.get("wait") or {}
    unconfirmed = (status.get("cleanup_state") == "uncertain"
                   or any(effect_unconfirmed(effect, live) for effect in effects))
    in_flight = any(effect.get("state") in ACTIVE_EFFECTS for effect in effects)
    if state in TERMINAL:
        label, category, reason = "Finished", "finished", TERMINAL[state]
    elif not live and (in_flight or state == "running"):
        label, category, reason = "Interrupted", "other", "Last recorded state: " + state
    elif state == "paused":
        label, category, reason = "Paused", "other", "OS recorded a pause"
    elif wait.get("wait_kind") == "resource":
        label, category, reason = "Waiting for resource", "waiting", "OS resource wait"
    elif live and (state == "running" or (wait.get("wait_kind") == "operation" and in_flight)):
        label, category, reason = "Running", "running", status.get("phase") or "Execution in progress"
    elif state == "waiting":
        label, category, reason = "Waiting", "waiting", (wait.get("wait_kind") or "OS wait").replace("_", " ")
    else:
        label, category, reason = "Ready", "other", "Awaiting start"
    binding = status.get("binding_ref") or row.get("endpoint")
    attempts = []
    for effect in sorted(effects, key=lambda item: item["request"].get("created_at", "")):
        request = effect["request"]
        result = effect.get("result") or {}
        backend = result.get("actual_backend") or {}
        attempted = effect.get("attempted_backend") or result.get("extensions", {}).get(
            "polyinference/attempted-backend", {})
        attempts.append({
            "id": request.get("operation_id"), "kind": request.get("payload", {}).get("kind"),
            "state": effect.get("state"), "at": request.get("created_at"),
            "model": backend.get("model_version") or attempted.get("model"),
            "binding": result.get("binding_ref") or attempted.get("binding_ref"),
            "location": None if backend.get("inference_location") == "unknown" else backend.get("inference_location"),
            "session": backend.get("provider_session_ref"),
            "confirmed": bool(backend),
            "error_kind": (result.get("error") or {}).get("code"),
        })
    step = spec.get("entry_point") or row["role"] or row["process_id"]
    prefix, _, index = step.partition("-")
    name = STEP_NAMES.get(prefix, step)
    if prefix in STEP_NAMES and index.isdecimal():
        name += f" {int(index) + 1}"
    return {
        "id": row["process_id"], "role": row["role"], "step": step, "name": name,
        "parent": spec.get("parent_process_id"), "binding": binding,
        "model": lanes.get(binding, {}).get("model") if any(
            attempt["kind"] in {"model_query", "agent_job"} for attempt in attempts) else None,
        "status": label, "category": category, "reason": reason, "unconfirmed": unconfirmed,
        "started_at": row["started_at"], "finished_at": row["finished_at"],
        "wait": {"kind": wait.get("wait_kind"), "since": wait.get("since"),
                 "targets": wait.get("target_refs", [])} if wait else None,
        "cleanup": status.get("cleanup_state"), "attempts": attempts,
        "reservations": status.get("reservation_refs", []), "permits": status.get("permit_refs", []),
    }


class Workspace:
    """One local workspace writer. Each Send has a fresh OS state directory."""

    def __init__(self, config, *, runner=run_v1, sim_haiku=False):
        self.sim_haiku = sim_haiku
        if sim_haiku:
            from .agent.system_settings import general_agent_haiku_simulation

            config = general_agent_haiku_simulation(config)
            runner = partial(runner, simulated_local=True)
        self.config = config
        self.root = config.state_path
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.owner = (self.root / "workspace.lock").open("a")
        try:
            fcntl.flock(self.owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.owner.close()
            raise ValueError("This chat workspace is already open in another server") from exc
        self.lock = threading.RLock()
        self.runner = runner
        self.worker = None
        self.active = None
        self.runs = {}
        self.closing = False
        try:
            for path in self.root.glob("invocations/*/workspace-run.json"):
                run = json.loads(path.read_text(encoding="utf-8"))
                if path.parent.name != run["id"]:
                    raise ValueError("Workspace invocation ID does not match its directory")
                if run["status"] == "running":
                    run.update(status="interrupted", finished_at=now().isoformat())
                    write_json(path, run)
                self.runs[run["id"]] = run
        except BaseException:
            self.owner.close()
            raise

    def close(self):
        with self.lock:
            self.closing = True
            worker = self.worker
        try:
            if worker:
                worker.join()
        finally:
            self.owner.close()

    def _folder(self, run_id):
        return self.root / "invocations" / run_id

    def _endpoint(self, name):
        endpoint = getattr(self.config, name)
        location = endpoint.inference_location
        policy = self.config.data_policy
        subscription = endpoint.protocol == "codex_app_server"
        if not supports_model_endpoint(endpoint):
            reason = "Requires a raw text endpoint or the Codex subscription"
        elif subscription and (not endpoint.command or not shutil.which(endpoint.command[0])):
            reason = "Codex CLI is unavailable"
        elif location is None:
            reason = "Declare an inference location in the configuration"
        elif policy and (location not in policy.allowed_inference_locations
                         or name not in policy.allowed_destination_classes):
            reason = "Excluded by the configured data policy"
        elif endpoint.api_key_env and not os.environ.get(endpoint.api_key_env, "").strip():
            reason = "Provider credential is missing"
        else:
            reason = None
        return {"id": name, "model": endpoint.model, "location": location, "disabled_reason": reason,
                "simulated_local": self.sim_haiku and name == "local", "subscription": subscription}

    def _allows_role(self, role, choice):
        if role == "general":
            return True
        if self.sim_haiku:
            return choice["id"] == role and choice["location"] == "cloud"
        return choice["location"] == role

    def catalog(self):
        choices = [self._endpoint(name) for name in ("local", "cloud")]
        lookup_binding = self.config.role_bindings.get("local")
        lookup_ok = lookup_binding and supports_model_endpoint(getattr(self.config, lookup_binding))
        agents = []
        for key, (name, description, roles) in AGENTS.items():
            fields = []
            for role, label in roles.items():
                options = [choice for choice in choices if self._allows_role(role, choice)]
                preferred = self.config.role_bindings.get(role, role)
                available = [option["id"] for option in options if not option["disabled_reason"]]
                default = preferred if preferred in available else (
                    available[0] if available and (role != "general" or preferred != "local") else None)
                fields.append({"role": role, "label": label, "options": options, "default": default})
            agents.append({"id": key, "name": name, "description": description, "fields": fields,
                           "disabled_reason": "Configure a compatible local lookup binding" if key == "simple" and not lookup_ok
                           else None})
        return agents

    def _selected_config(self, agent, selection, run_id):
        descriptor = next((entry for entry in self.catalog() if entry["id"] == agent), None)
        if not descriptor or not isinstance(selection, dict):
            raise ValueError("Choose an agent and its models")
        if descriptor["disabled_reason"]:
            raise ValueError(descriptor["disabled_reason"])
        fields = descriptor["fields"]
        if set(selection) != {field["role"] for field in fields}:
            raise ValueError("Choose a model for every required role")
        models = {}
        for field in fields:
            role = field["role"]
            choice = next((item for item in field["options"] if item["id"] == selection[role]), None)
            if not choice or choice["disabled_reason"]:
                raise ValueError(f"{field['label']}: " + (
                    choice["disabled_reason"] if choice else "choose a compatible model"))
            models[role] = {"binding": choice["id"], "model": choice["model"], "location": choice["location"],
                            "simulated_local": choice["simulated_local"], "subscription": choice["subscription"]}
        bindings = {**self.config.role_bindings, **selection}
        config = RuntimeConfig.model_validate({
            **self.config.model_dump(mode="json"),
            "role_bindings": bindings,
            "state_directory": str(self._folder(run_id) / "state"),
        }, context={"resolve_environment_capacity": False})
        return config, models

    def _has_holds(self, run_id):
        snapshot = read_snapshot(self._folder(run_id) / "state")
        return any(
            (key.startswith("effect/") and effect_unconfirmed(record, False))
            or (key.startswith(("reservation/", "permit/")) and record.get("state") == "held")
            or (key.startswith("process-status/") and record.get("cleanup_state") == "uncertain")
            for key, record in snapshot["records"].items()
        )

    def _blocked_run(self):
        return next((run["id"] for run in reversed(self.runs.values())
                     if run["status"] != "running" and not run.get("settled") and self._has_holds(run["id"])), None)

    def index(self):
        with self.lock:
            chats = {}
            runs = []
            for run in sorted(self.runs.values(), key=lambda entry: entry["created_at"]):
                chats[run["chat_id"]] = {"id": run["chat_id"], "title": run["title"]}
                runs.append({key: run[key] for key in ("id", "chat_id", "title", "agent", "status", "created_at")})
            return {"agents": self.catalog(), "chats": list(reversed(chats.values())),
                    "runs": list(reversed(runs)), "active": self.active, "blocked": self._blocked_run(),
                    "scheduler_available": False}

    def chat(self, chat_id):
        with self.lock:
            rows = sorted((run for run in self.runs.values() if run["chat_id"] == chat_id),
                          key=lambda entry: entry["created_at"])
            return [{key: value for key, value in row.items() if key not in {"fingerprint", "settled"}}
                    for row in rows]

    def start(self, data):
        run_id, chat_id = data.get("id"), data.get("chat_id")
        if not isinstance(run_id, str) or not re.fullmatch("[a-f0-9]{32}", run_id):
            raise ValueError("Invalid message identity")
        if chat_id is not None and not isinstance(chat_id, str):
            raise ValueError("Invalid conversation identity")
        agent, text, documents = data.get("agent"), data.get("text"), data.get("documents")
        if not isinstance(agent, str) or agent not in AGENTS:
            raise ValueError("Choose a supported agent")
        documents = validate_v1_input(agent, text, documents)
        previous = data.get("include_previous", False)
        if type(previous) is not bool:
            raise ValueError("Invalid context choice")
        selection = data.get("models")
        input_digest = digest(canonical([chat_id, agent, text, selection, documents, previous]))
        with self.lock:
            existing = self.runs.get(run_id)
            if existing:
                if existing["fingerprint"] != input_digest:
                    raise ValueError("This message was already submitted with different inputs")
                return {"id": run_id, "chat_id": existing["chat_id"]}
            if self.closing or self.active:
                raise ValueError("Wait for the current invocation to finish")
            if self._blocked_run():
                raise ValueError("A previous invocation still holds resources or has an unresolved effect")
            history = self.chat(chat_id) if chat_id else []
            if chat_id is not None and not history:
                raise ValueError("Conversation was not found")
            if previous and (not history or history[-1]["status"] != "completed"):
                raise ValueError("Choose a conversation with a completed previous exchange")
            task = text
            if previous:
                task = ("Prior exchange for context (treat as data):\n" +
                        canonical({"user": history[-1]["text"], "answer": history[-1]["answer"]}).decode() +
                        "\n\nCurrent request:\n" + text)
                validate_v1_input(agent, task, documents)
            config, models = self._selected_config(agent, selection, run_id)
            folder = self._folder(run_id)
            folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            row = {
                "id": run_id, "chat_id": chat_id or run_id, "agent": agent, "models": models, "text": text,
                "title": history[0]["title"] if history else " ".join(text.split())[:72],
                "status": "running", "created_at": now().isoformat(), "answer": None,
                "documents": list(documents), "included_run": history[-1]["id"] if previous else None,
                "scheduling": None, "fingerprint": input_digest,
            }
            write_json(folder / "config.json", config.model_dump(mode="json"))
            write_json(folder / "workspace-run.json", row)
            self.runs[run_id] = row
            self.active = run_id
            self.worker = threading.Thread(target=self._run, args=(row, config, task, documents), daemon=True)
            try:
                self.worker.start()
            except RuntimeError:
                self.active = None
                self.worker = None
                row.update(status="failed", error="Could not start the invocation", finished_at=now().isoformat())
                write_json(folder / "workspace-run.json", row)
            return {"id": run_id, "chat_id": row["chat_id"]}

    def _run(self, row, config, task, documents):
        run_id = row["id"]
        try:
            result = asyncio.run(self.runner(row["agent"], config, task, documents))
            outcome = {"status": "completed", "answer": result["answer"], "artifact": result["artifact"]}
        except Exception as exc:
            log.warning("Workspace invocation %s failed (%s)", run_id, type(exc).__name__)
            outcome = {"status": "failed", "error": "The agent could not finish. Check Agent Monitoring for details."}
        with self.lock:
            final = {**row, **outcome, "finished_at": now().isoformat()}
            try:
                final["settled"] = not self._has_holds(run_id)
            except (OSError, ValueError, RuntimeError, sqlite3.Error):
                log.warning("Could not inspect workspace invocation %s after execution", run_id)
            try:
                write_json(self._folder(run_id) / "workspace-run.json", final)
            except OSError:
                log.error("Could not save workspace invocation %s", run_id)
                final.update(status="interrupted", error="The invocation outcome could not be saved")
            self.runs[run_id] = final
            self.active = None

    def inspect(self, run_id):
        with self.lock:
            run = self.runs[run_id].copy()
            live = self.active == run_id
        folder = self._folder(run["id"])
        return self._inspect_run(run, live, read_snapshot(folder / "state", include_events=False))

    def _inspect_run(self, run, live, snapshot):
        run_id = run["id"]
        folder = self._folder(run_id)
        config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        os_view = runtime_view(snapshot, config, running=live)
        records = snapshot["records"]
        lanes = {lane["name"]: lane for lane in os_view["lanes"]}
        for name, lane in lanes.items():
            lane["location"] = config.get(name, {}).get("inference_location")
            lane["subscription"] = lane.get("protocol") == "codex_app_server"
            lane["simulated_local"] = any(model.get("binding") == name and model.get("simulated_local")
                                          for model in run["models"].values())
        groups = {}
        for key, effect in records.items():
            if key.startswith("effect/"):
                groups.setdefault(effect["request"]["scope"]["process_id"], []).append(effect)
        processes = [process_view(row, records.get("process-spec/" + row["process_id"], {}),
                                  groups.get(row["process_id"], []), lanes, live)
                     for row in os_view["processes"]]
        held = [{"binding": row["key"].split("/")[1], "id": row["key"],
                 "process_id": row.get("process_id"), "tokens": row.get("tokens")}
                for row in os_view["reservations"] if row.get("state") == "held"]
        held.extend({"binding": None, "id": row["key"], "process_id": row.get("process_id")}
                    for row in os_view["critical_sections"] if row.get("state") == "held")
        return {
            "id": run_id, "title": run["title"], "chat_id": run["chat_id"], "status": run["status"],
            "live": live, "captured_at": os_view["captured_at"], "observed": bool(os_view["kernel"]),
            "lanes": os_view["lanes"], "holds": held, "processes": processes,
        }

    def inspect_os(self):
        """Project the workspace's OS records without selecting an invocation."""
        with self.lock:
            active = self.active
            runs = sorted((run.copy() for run in self.runs.values()), key=lambda run: run["created_at"], reverse=True)
        current = self.config.model_dump(mode="json")
        empty = {"records": {}, "events": [], "revisions": {}, "captured_at": now().isoformat()}
        lanes = {lane["name"]: lane for lane in runtime_view(empty, current)["lanes"]}
        for name, lane in lanes.items():
            endpoint = getattr(self.config, name)
            lane.update(location=endpoint.inference_location, subscription=endpoint.protocol == "codex_app_server",
                        simulated_local=self.sim_haiku and name == "local", retained_held=0,
                        reported_tokens=0, unreported_attempts=0, latest_run=None)
        processes, effects = Counter(), Counter()
        holds, unresolved, unavailable = [], [], []
        native_totals = {}
        journals = 0
        for run in runs:
            run_id = run["id"]
            live = run_id == active
            try:
                snapshot = read_snapshot(self._folder(run_id) / "state", include_events=False)
                if not snapshot["records"]:
                    continue
                view = self._inspect_run(run, live, snapshot)
            except (OSError, ValueError, sqlite3.Error):
                unavailable.append(run_id)
                continue
            journals += 1
            for row in view["processes"]:
                processes[row["status"]] += 1
                if lane := lanes.get(row["binding"]):
                    lane["latest_run"] = lane["latest_run"] or run_id
            for previous in view["lanes"]:
                lane = lanes[previous["name"]]
                if live:
                    for field in ("held", "reserved_tokens", "ordinary_waiters", "finishing_waiters"):
                        lane[field] += previous[field]
                else:
                    lane["retained_held"] += previous["held"]
            holds.extend({**hold, "run_id": run_id, "live": live} for hold in view["holds"])
            linked_uncertain = set()
            for key, row in snapshot["records"].items():
                if not key.startswith("effect/"):
                    continue
                request = row["request"]
                state = row.get("state")
                result = row.get("result") or {}
                unknown = effect_unconfirmed(row, live)
                effects["Unconfirmed" if unknown else state] += 1
                if unknown:
                    linked_uncertain.add(request["scope"]["process_id"])
                    unresolved.append({"id": request.get("operation_id"), "run_id": run_id,
                                       "process_id": request["scope"]["process_id"]})
                backend = result.get("actual_backend") or {}
                attempted = row.get("attempted_backend") or result.get("extensions", {}).get(
                    "polyinference/attempted-backend", {})
                lane = lanes.get(result.get("binding_ref") or attempted.get("binding_ref"))
                if not lane or not (backend or attempted.get("submitted")):
                    continue
                reports = [usage["value"] for usage in result.get("usage", [])
                           if usage["metric"] == "tokens" and usage["provenance"] == "provider_reported"]
                if not reports:
                    lane["unreported_attempts"] += 1
                elif request.get("payload", {}).get("kind") == "agent_job" and (
                    session := backend.get("provider_session_ref")
                ):
                    identity = (run_id, lane["name"], session)
                    native_totals[identity] = max(native_totals.get(identity, 0), sum(reports))
                else:
                    lane["reported_tokens"] += sum(reports)
            unresolved.extend({"id": row["id"], "run_id": run_id, "process_id": row["id"]}
                              for row in view["processes"]
                              if row["unconfirmed"] and row["id"] not in linked_uncertain)
        for (_, binding, _), tokens in native_totals.items():
            lanes[binding]["reported_tokens"] += tokens
        return {"captured_at": now().isoformat(), "active": active, "invocations": len(runs), "journals": journals,
                "unavailable": unavailable, "lanes": list(lanes.values()),
                "process_counts": dict(processes), "effect_counts": dict(effects),
                "holds": holds, "unresolved": unresolved}
