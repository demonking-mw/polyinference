from __future__ import annotations

import asyncio
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from ..contracts import (
    AgentProgram,
    CodeRevision,
    DesignBasis,
    MergedWorkerProtocol,
    Requirement,
    ReviewResolution,
    SprintPlan,
    TaskSpec,
)
from ..domain import SeniorProposal, canonical, digest, now
from ..ports import RecordConflict
from .design_basis import DESIGN_BASIS
from .routing import allocate, development_history, was_started
from .senior import build_senior
from .services import ModelOperationFailure
from .tasks import make_task
from .worker import AppContext, build_worker


class ControllerState(TypedDict, total=False):
    process_id: str
    logical_step: int
    next_transition: str
    outcome: str


class ProjectAgent:
    """One driver per process. Worker invocations are independent graph threads."""

    def __init__(self, services):
        self.app = services
        self.worker = build_worker(services.ports.checkpointer)
        self.senior = build_senior(services.ports.checkpointer)
        self.workers = {}
        services.engine = self
        self.controller = build_controller(services.ports.checkpointer)

    @property
    def context(self):
        return AppContext(self.app)

    async def initialize(self):
        app = self.app
        if app.ports.records.get("app/run"):
            if app.get("app/run")["program"] != app.program.model_dump(mode="json"):
                raise RuntimeError(
                    "Program/graph/prompt version changed; resume requires the pinned implementation"
                )
            if app.repository:
                await app.repository.initialize()
            return
        requirements = [
            Requirement(feature_id="runtime/" + name, version="1", necessity="required")
            for name in (
                "effect-journal",
                "private-workspace",
                "global-shell-exclusion",
                "verification-exclusion",
                "atomic-record-publication",
                "attached-workspace" if app.repository else "scoped-workspace-copy",
                "workspace-view",
                "direct-tools",
                "artifacts",
                "persistent-checkpoints",
                "fixed-role-routing",
                "output-delivery",
            )
        ]
        for feature, enabled in (
            ("repository-baseline", app.config.prepare_repository),
            ("shell-run", app.config.shell_execution != "disabled"),
            ("project-scope", app.config.write_scope == "project"),
        ):
            if enabled:
                requirements.append(
                    Requirement(feature_id="runtime/" + feature, version="1", necessity="required")
                )
        app.ports.negotiate(requirements)
        manifest = AgentProgram(
            **app.base("program/manifest"),
            program=app.program,
            entry_points=["controller", "worker", "senior"],
            required_runtime_features=requirements,
            optional_runtime_features=[],
            migration_registry_ref=None,
            design_basis=DesignBasis.model_validate(DESIGN_BASIS),
            worker_protocol=MergedWorkerProtocol(),
        )
        if not app.ports.records.get(manifest.record_id):
            app.ports.records.compare_and_publish(
                {}, {}, {manifest.record_id: manifest.model_dump(mode="json")}
            )
        app.process("controller", "senior")
        if app.repository:
            result, output = await app.capability({"process_id": "controller"}, "repository-prepare",
                                                  "coding.prepare", {}, "shared_write")
            if result.state != "succeeded":
                raise ValueError(output.get("error", str(output)))
            initial = CodeRevision.model_validate(output)
        else:
            initial = await app.ports.workspaces.initialize()
        if not app.repository and hasattr(app.ports, "outputs"):
            setup = app.get("repository/setup")
            destination = app.config.output_directory or (
                str(app.config.repo_path) if setup.get("git_initialized")
                else str(app.config.state_path / "result")
            )
            baseline = await app.ports.workspaces.tree(initial.commit_id)
            app.ports.outputs.prepare(destination, {
                path: {"mode": mode, "digest": digest(content)}
                for path, (mode, content) in baseline.items() if (app.config.repo_path / path).is_file()
            } if destination == str(app.config.repo_path) else {})
        run = {
            "program": app.program.model_dump(mode="json"),
            "objective": app.config.objective,
            "status": "active",
            "sprint": 0,
            "plan_ref": None,
            "starts_closed": True,
            "active_workers": [],
            "steering_received": 0,
            "steering_applied": 0,
            "captured_workers": [],
            "completion_proposed": False,
            "senior_queries": 0,
            "acceptance_attempts": 0,
            "last_review_fingerprint": None,
        }
        app.ports.records.compare_and_publish(
            {"app/run": 0, "head/provisional": 0, "head/reviewed": 0, "head/initial": 0},
            {
                "app/run": run,
                "head/initial": {"code": initial.model_dump(mode="json")},
                "head/provisional": {"code": initial.model_dump(mode="json")},
                "head/reviewed": {"code": initial.model_dump(mode="json")},
            },
        )
        app.process("controller", "senior")

    async def run(self):
        app = self.app
        try:
            await self.initialize()
            result = await self._run()
            # A known worker failure closes starts, but other started workers
            # retain their finish paths. Do not tear them down with the runtime.
            if self.workers and app.get("app/run")["status"] != "active" and not app.ports.operations.uncertain():
                self.close_starts()
                while self.workers:
                    await asyncio.wait(self.workers.values(), return_when=asyncio.FIRST_COMPLETED)
                    await self.consume()
            return {**result, "outcome": app.get("app/run")["status"]}
        except BaseException as exc:
            row = app.ports.records.get("app/run")
            run = row[1] if row else {}
            if run.get("status") == "active":
                app.update("app/run", {**run, "status": "paused", "starts_closed": True,
                                       "blocker": str(exc)[:2000] or type(exc).__name__})
            raise
        finally:
            if app.repository:
                try:
                    summary = await app.repository.summary()
                    app.update("coding/repository-summary", summary)
                    await app.capability({"process_id": "controller"}, "repository-summary-" + digest(canonical(summary)),
                                         "user.notify", {"text": app.repository.summary_message(summary)}, "shared_write")
                except Exception as exc:
                    app.update("coding/repository-summary-error", {"error": str(exc)[:2000]})
                finally:
                    await app.repository.close_run()
            if hasattr(app.ports, "processes"):
                if app.ports.records.get("process/controller"):
                    row = app.ports.records.get("app/run")
                    app.ports.processes.finish(
                        "controller", state="completed" if row and row[1]["status"] == "completed" else "paused"
                    )

    async def _run(self):
        if self.app.ports.operations.uncertain():
            raise RuntimeError("Uncertain effects require reconciliation; no replacement is dispatched")
        if self.app.get("app/run")["status"] in {"active", "delivering"}:
            controller = self.app.get("process/controller")
            if controller["state"] in {"completed", "paused", "failed"}:
                self.app.update("process/controller", {**controller, "state": "ready"})
                self.app.process_status("controller", state="ready")
        if self.app.config.prepare_repository and not self.app.ports.records.get("setup/completed"):
            from .setup import prepare

            await prepare(self)
            if self.app.get("app/run")["status"] != "active":
                return {"outcome": self.app.get("app/run")["status"]}
        if self.app.get("app/run")["status"] == "delivering":
            try:
                await self.deliver_outputs()
            finally:
                # Acceptance may have committed immediately before a crash,
                # leaving its old verification lease attached to the controller.
                owner = self.app.ports.records.get("permit/verification/project")
                if owner and owner[1].get("process_id") == "controller":
                    await self.app.ports.exclusive.release(owner[1]["permit"], "controller")
            if self.app.get("app/run")["status"] != "active":
                return {"outcome": self.app.get("app/run")["status"]}
        saved = await self.controller.aget_state({"configurable": {"thread_id": "controller"}})
        initial = None if saved.next else {"process_id": "controller", "logical_step": 0}
        result = await self.controller.ainvoke(
            initial,
            {"configurable": {"thread_id": "controller"}, "recursion_limit": 10000},
            context=self.context,
            durability="sync",
        )
        return result

    async def deliver_outputs(self):
        app = self.app
        run = app.get("app/run")
        if app.repository:
            receipt = app.get(run["acceptance_ref"])
            await app.repository.assert_target(receipt["code"]["commit_id"])
            app.update("app/run", {**run, "status": "completed", "output": {
                "directory": str(app.config.repo_path), "branch": app.get("repository/setup")["base_branch"],
                "commit": receipt["code"]["commit_id"], "in_place": True}})
            return True
        receipt = app.get(run["acceptance_ref"])
        tree = await app.ports.workspaces.tree(receipt["code"]["commit_id"])
        files = [{"path": path, "mode": mode,
                  "content": app.ports.artifacts.put(content, app.scope(), "application/octet-stream").model_dump(mode="json")}
                 for path, (mode, content) in sorted(tree.items())]
        result, output = await app.capability(
            {"process_id": "controller", "logical_step": "delivery"},
            "deliver-" + run["acceptance_ref"] + "-" + str(run.get("output_delivery_attempt", 1)), "outputs.deliver",
            {"delivery_id": run["acceptance_ref"], "files": files}, "shared_write",
        )
        if result.state != "succeeded":
            app.update("app/run", {**app.get("app/run"), "status": "paused",
                                   "blocker": output.get("error", "Output delivery failed")})
            return False
        version, current = app.ports.records.get("app/run")
        head = app.ports.records.get("head/provisional")
        reviewed = app.ports.records.get("head/reviewed")
        current_acceptance = (
            current["status"] == "delivering"
            and current.get("acceptance_ref") == run["acceptance_ref"]
            and current["steering_received"] == receipt["steering_through"]
            and head[1]["code"] == reviewed[1]["code"] == receipt["code"]
        )
        if not current_acceptance:
            app.update("app/run", {**current, "output": output,
                                   "status": "active" if current["status"] == "delivering" else current["status"],
                                   "starts_closed": True, "completion_proposed": False})
            return False
        try:
            app.ports.records.compare_and_publish(
                {"app/run": version, "head/provisional": head[0], "head/reviewed": reviewed[0]},
                {"app/run": {**current, "status": "completed", "output": output}},
            )
            return True
        except RecordConflict:
            return False

    def retry_outputs(self, reason):
        app = self.app
        run = app.get("app/run")
        if not reason.strip() or run["status"] != "paused" or not run.get("acceptance_ref"):
            raise ValueError("Output recovery needs a paused accepted run and an explicit reason")
        receipt = app.get(run["acceptance_ref"])
        if (app.ports.operations.uncertain() or run["active_workers"]
                or receipt["code"] != app.get("head/provisional")["code"]
                or receipt["code"] != app.get("head/reviewed")["code"]
                or receipt["steering_through"] != run["steering_received"]):
            raise ValueError("Output recovery requires current acceptance and known stopped effects")
        app.update("app/run", {**run, "status": "delivering", "blocker": None,
                               "output_delivery_attempt": run.get("output_delivery_attempt", 1) + 1,
                               "output_delivery_reason": reason[:4000]})

    async def retry_worker(self, task_id, reason):
        """Explicitly recover a known model failure without repeating private edits."""
        app = self.app
        if not reason.strip():
            raise ValueError("Recovery needs a reason")
        if self.workers or app.get("app/run")["active_workers"] or app.ports.operations.uncertain():
            raise ValueError("Drain active work and reconcile unknown effects before recovery")
        key = "task/" + task_id
        task = app.get(key)
        failure = task.get("model_failure")
        if task["execution"] != "interrupted" or not failure:
            raise ValueError("Task has no recoverable model failure")
        original = app.get("effect/" + failure["operation_id"])
        if original["state"] != "failed" or original["result"]["execution_termination"] != "confirmed_stopped":
            raise ValueError("Recovery requires a confirmed stopped model operation")
        pid, wid = task["process_id"], task["workspace_id"]
        control = app.ports.records.get("process-control/" + pid)
        if control and control[1].get("cancel_requested"):
            raise ValueError("A cancelled process cannot be recovered as a model retry")
        if hasattr(app.ports.operations, "recovery_allowed"):
            app.ports.operations.recovery_allowed(failure["operation_id"], app.scope(pid))
        config = {"configurable": {"thread_id": pid}}
        saved = await self.worker.aget_state(config)
        values = dict(saved.values)
        if not values or saved.next != ("model",):
            raise ValueError("Recovery requires a checkpoint stopped at the model node")
        manifest = app.ports.workspaces.current(wid)
        if manifest.view == "integration":
            # A previous recovery may have checkpointed the new phase before
            # atomically activating its driver. Rebuild from the original delta.
            await app.ports.workspaces.abort(wid)
            owner = app.ports.records.get("permit/verification/project")
            if owner and owner[1].get("process_id") == pid:
                await app.ports.exclusive.release(owner[1]["permit"], pid)
            manifest = app.ports.workspaces.current(wid)
        updates = {"logical_step": values["logical_step"] + 1,
                   "workspace_generation": manifest.generation,
                   "verification_permit_ref": None,
                   "model_recovery": {"operation_id": failure["operation_id"], "reason": reason[:4000]}}
        if values["phase"] in {"reconciliation", "assessment"}:
            permit = await app.ports.exclusive.acquire("verification/project", pid)
            try:
                manifest = await app.ports.workspaces.integrate(
                    wid, CodeRevision.model_validate(app.get("head/provisional")["code"]), permit
                )
                updates.update(
                    phase="reconciliation", workspace_view="integration",
                    workspace_generation=manifest.generation, verification_permit_ref=permit,
                    captured_head=manifest.captured_head.model_dump(mode="json"), evidence=[],
                    reconciliation_turn_refs=[], assessment_turn_refs=[],
                )
                await self.worker.aupdate_state(config, updates, as_node="integrate")
            except BaseException:
                await app.ports.exclusive.release(permit, pid)
                raise
        else:
            updates.update(phase="development", workspace_view="development")
            await self.worker.aupdate_state(config, updates, as_node="load")
        ledger = {key: {**task, "execution": "in_progress", "model_failure": None}}
        attempt = app.get("attempt/" + task["attempt_id"])
        ledger["attempt/" + task["attempt_id"]] = {**attempt, "execution": "in_progress",
                                                  "revision": attempt["revision"] + 1, "stop_reason": None}
        for process_id in (pid, "controller"):
            process = app.get("process/" + process_id)
            ledger["process/" + process_id] = {**process, "state": "ready", "error": None}
            status = app.get("process-status/" + process_id)
            ledger["process-status/" + process_id] = {
                **status, "state": "ready", "revision": status["revision"] + 1,
                **({"phase": updates["phase"], "cleanup_state": "none",
                    "permit_refs": [updates["verification_permit_ref"]] if updates.get("verification_permit_ref") else []}
                   if process_id == pid else {}),
            }
        run = app.get("app/run")
        ledger["app/run"] = {**run, "status": "active", "starts_closed": True,
                              "active_workers": [pid], "captured_workers": [pid],
                              "completion_proposed": False, "blocker": None}
        app.ports.records.compare_and_publish(
            {name: app.ports.records.get(name)[0] for name in ledger}, ledger
        )
        await self.launch(key, resume=True)

    def steer(self, text):
        app = self.app
        process = app.get("process/controller")
        app.update("process/controller", {**process, "state": "ready"})
        app.process_status("controller", state="ready")
        version, run = app.ports.records.get("app/run")
        sequence = run["steering_received"] + 1
        active = set(run["active_workers"])
        app.ports.records.compare_and_publish(
            {"app/run": version},
            {
                "app/run": {
                    **run,
                    "starts_closed": True,
                    "steering_received": sequence,
                    "captured_workers": sorted(active | set(run["captured_workers"])),
                    "status": "active",
                    "completion_proposed": False,
                }
            },
            {
                f"steering/{sequence:08d}": {
                    "sequence": sequence,
                    "text": text,
                    "received_at": now().isoformat(),
                }
            },
        )
        return sequence

    async def launch(self, task_ref, resume=False):
        app = self.app
        task = app.get(task_ref)
        pid = task["process_id"]
        if pid in self.workers:
            return
        app.process(pid, task["assignment"]["role"], task["spec_ref"], task)
        initial = {
            "process_id": pid,
            "task_spec_ref": task["spec_ref"],
            "task_ledger_ref": task_ref,
            "attempt_id": task["attempt_id"],
            "workspace_id": task["workspace_id"],
            "phase": "development",
            "logical_step": 0,
            "calls": 0,
            "repairs": 0,
            "trajectory_ref": None,
            "verification_permit_ref": None,
            "reconciliation_turn_refs": [],
            "assessment_turn_refs": [],
            "evidence": [],
            "report_ref": None,
        }
        saved = await self.worker.aget_state({"configurable": {"thread_id": pid}})
        if resume and saved.next:
            initial = None

        async def drive():
            try:
                process = app.get("process/" + pid)
                app.update("process/" + pid, {**process, "state": "running"})
                app.process_status(pid, state="running", phase="development")
                return await self.worker.ainvoke(
                    initial,
                    {"configurable": {"thread_id": pid}, "recursion_limit": 2000},
                    context=self.context,
                    durability="sync",
                )
            except Exception as exc:
                # Retain unknown effects and ownership. Definite stopped work may be parked.
                process = app.get("process/" + pid)
                app.update("process/" + pid, {**process, "state": "paused", "error": str(exc)[:2000]})
                unknown = [
                    key
                    for key in app.ports.operations.uncertain()
                    if app.get("effect/" + key)["request"]["scope"]["process_id"] == pid
                ]
                if not unknown:
                    await app.preserve_interrupted(task_ref)
                    owner = app.ports.records.get("permit/verification/project")
                    if owner and owner[1].get("process_id") == pid:
                        await app.ports.workspaces.abort(task["workspace_id"])
                        await app.ports.exclusive.release(owner[1]["permit"], pid)
                    current_task = app.get(task_ref)
                    failure = ({"operation_id": exc.result.operation_id,
                                "error": exc.result.error.model_dump(mode="json") if exc.result.error else None,
                                "diagnostics": exc.result.extensions}
                               if isinstance(exc, ModelOperationFailure) else None)
                    app.update(task_ref, {**current_task, "execution": "interrupted",
                                          "exception": str(exc)[:2000], "model_failure": failure})
                    attempt_key = "attempt/" + current_task["attempt_id"]
                    attempt = app.get(attempt_key)
                    updated_attempt = app.task_attempt(attempt, update={
                        "revision": attempt["revision"] + 1, "execution": "interrupted",
                        "stop_reason": str(exc)[:2000]})
                    app.update(attempt_key, updated_attempt.model_dump(mode="json"))
                app.process_status(
                    pid,
                    state="paused",
                    cleanup_state="uncertain" if unknown else "complete",
                    **({} if unknown else {"permit_refs": [], "pending_operations": [], "wait": None}),
                )
                raise

        processes = getattr(app.ports, "processes", None)
        self.workers[pid] = processes.start(pid, drive) if processes else asyncio.create_task(drive())

    async def settle_stopped_worker(self, task_ref, reason):
        app = self.app
        task = app.get(task_ref)
        pid = task["process_id"]
        if any(body["request"]["scope"].get("process_id") == pid
               and body["state"] in {"prepared", "submitting", "active", "uncertain"}
               for _, _, body in app.ports.records.scan("effect/")):
            return False
        if app.ports.records.get("workspace/" + task["workspace_id"]):
            await app.ports.workspaces.abort(task["workspace_id"])
        owner = app.ports.records.get("permit/verification/project")
        if owner and owner[1].get("process_id") == pid:
            await app.ports.exclusive.release(owner[1]["permit"], pid)
        if task["execution"] != "completed":
            app.update(task_ref, {**task, "execution": "interrupted", "exception": reason})
            attempt_key = "attempt/" + task["attempt_id"]
            attempt = app.get(attempt_key)
            if attempt["execution"] != "interrupted":
                app.update(attempt_key, {**attempt, "execution": "interrupted",
                                         "revision": attempt["revision"] + 1, "stop_reason": reason})
        app.process_status(pid, cleanup_state="complete", permit_refs=[], pending_operations=[], wait=None)
        return True

    async def consume(self):
        app = self.app
        # Reattach active invocations after a supported safe interruption.
        run = app.get("app/run")
        tasks = {body["process_id"]: key for key, _, body in app.ports.records.scan("task/")}
        for pid in run["active_workers"]:
            if pid not in self.workers:
                if app.get("process/" + pid)["state"] in {"paused", "cancelled", "failed"}:
                    known = await self.settle_stopped_worker(tasks[pid], "Worker driver stopped; explicit recovery required")
                    current = app.get("app/run")
                    app.update("app/run", {**current, "status": "paused", "starts_closed": True,
                                            "active_workers": [p for p in current["active_workers"] if p != pid] if known else current["active_workers"],
                                            "blocker": "Worker driver stopped; explicitly recover or retire its retained work"})
                    continue
                await self.launch(tasks[pid], resume=True)
        finished = [pid for pid, task in self.workers.items() if task.done()]
        for pid in finished:
            future = self.workers.pop(pid)
            failure = RuntimeError("Worker driver cancelled") if future.cancelled() else future.exception()
            version, run = app.ports.records.get("app/run")
            task_ref = tasks[pid]
            task = app.get(task_ref)
            if failure or task["execution"] == "interrupted":
                known = await self.settle_stopped_worker(task_ref, str(failure) if failure else task.get("exception", "needs review"))
                unknown = not known or bool(app.ports.operations.uncertain())
                version, run = app.ports.records.get("app/run")
                app.ports.records.compare_and_publish(
                    {"app/run": version},
                    {
                        "app/run": {
                            **run,
                            "starts_closed": True,
                            "status": "paused" if unknown or failure or task.get("model_failure") else "active",
                            "active_workers": run["active_workers"]
                            if unknown
                            else [p for p in run["active_workers"] if p != pid],
                            "captured_workers": [p for p in run["active_workers"] if p != pid],
                            "blocker": str(failure)
                            if failure
                            else task.get("exception", "worker needs review"),
                        }
                    },
                )
                continue
            app.ports.records.compare_and_publish(
                {"app/run": version},
                {
                    "app/run": {
                        **run,
                        "active_workers": [p for p in run["active_workers"] if p != pid],
                        "captured_workers": [p for p in run["captured_workers"] if p != pid],
                    }
                },
            )
        return app.get("app/run")

    def ready(self):
        app = self.app
        tasks = app.ports.records.scan("task/")
        by_id = {body["assignment"]["task_id"]: body for _, _, body in tasks}
        result = []
        for key, _, body in tasks:
            if body["execution"] != "pending":
                continue
            eligible = True
            for dep in body["assignment"]["dependencies"]:
                source = by_id.get(dep)
                resolution = (
                    app.ports.records.get("resolution/" + source["report_ref"])
                    if source and source.get("report_ref")
                    else None
                )
                if not resolution or resolution[1]["action"] != "keep":
                    eligible = False
            if eligible:
                result.append(key)
        return result

    async def dispatch(self):
        app = self.app
        for key in self.ready():
            version, run = app.ports.records.get("app/run")
            if run["starts_closed"] or len(run["active_workers"]) >= app.worker_limit:
                break
            task_version, task = app.ports.records.get(key)
            if task["execution"] != "pending":
                continue
            base = app.get("head/provisional")["code"]
            original_spec = TaskSpec.model_validate(app.get(task["spec_ref"]))
            spec_ref = task["spec_ref"] + ":started"
            spec = original_spec.model_copy(
                update={"record_id": spec_ref, "base": CodeRevision.model_validate(base)}
            )
            attempt_key = "attempt/" + task["attempt_id"]
            attempt_version, attempt_body = app.ports.records.get(attempt_key)
            attempt = app.task_attempt(attempt_body,
                update={
                    "revision": attempt_body["revision"] + 1,
                    "task_spec_ref": spec_ref,
                    "original_base": CodeRevision.model_validate(base),
                    "execution": "in_progress",
                }
            )
            app.ports.records.compare_and_publish(
                {"app/run": version, key: task_version, attempt_key: attempt_version},
                {
                    "app/run": {**run, "active_workers": [*run["active_workers"], task["process_id"]]},
                    key: {**task, "execution": "in_progress", "base": base, "spec_ref": spec_ref,
                          "started_at": task.get("started_at") or now().isoformat()},
                    attempt_key: attempt.model_dump(mode="json"),
                },
                {spec_ref: spec.model_dump(mode="json")},
            )
            await self.launch(key)

    def close_starts(self):
        app = self.app
        version, run = app.ports.records.get("app/run")
        app.ports.records.compare_and_publish(
            {"app/run": version},
            {
                "app/run": {
                    **run,
                    "starts_closed": True,
                    "captured_workers": sorted(set(run["captured_workers"]) | set(run["active_workers"])),
                }
            },
        )

    async def review(self):
        app = self.app
        batch = app.ports.records.get("review-batch/active")
        if batch and batch[1]["state"] == "applying":
            await self._apply_review(batch[1])
            return
        self.close_starts()
        # Existing workers keep their original authority and every finish path open.
        while app.get("app/run")["active_workers"]:
            if app.get("app/run")["status"] == "paused":
                return
            if self.workers:
                await asyncio.wait(self.workers.values(), return_when=asyncio.FIRST_COMPLETED)
            await self.consume()
        version, run = app.ports.records.get("app/run")
        if app.repository and run["steering_received"]:
            through = run["steering_received"]
            await app.repository.apply_steering(app.user_updates(through))
            version, run = app.ports.records.get("app/run")
            if run["steering_received"] != through:
                return
        if run["sprint"] >= app.config.max_sprints or run["senior_queries"] >= app.config.max_sprints * 3:
            app.update("app/run", {**run, "status": "budget_stopped", "blocker": "Sprint/query limit"})
            return
        head = app.get("head/provisional")["code"]
        reports = [
            body
            for key, _, body in app.ports.records.scan("report/")
            if not app.ports.records.get("resolution/" + key)
            or app.get("resolution/" + key)["action"] in {"retry", "defer"}
        ]
        steering = [
            body
            for _, _, body in app.ports.records.scan("steering/")
            if run["steering_applied"] < body["sequence"] <= run["steering_received"]
        ]
        pending = [v for _, _, v in app.ports.records.scan("task/") if v["execution"] == "pending"]
        previous = app.ports.records.get(f"proposal/senior-{run['senior_queries']}")
        snapshot = {
            "objective": run["objective"],
            "reviewed_head": app.get("head/reviewed")["code"],
            "previous_user_brief": previous[1]["proposal"].get("user_brief") if previous else None,
            "repository_setup": (app.ports.records.get("repository/setup") or (0, {}))[1],
            "development_allocation": {
                "senior_fraction": app.config.senior_development_fraction,
                "tasks": [
                    {"task_id": body["assignment"]["task_id"], "role": body["assignment"]["role"],
                     "started": was_started(body), "reserved": body["execution"] == "pending"}
                    for body in development_history(
                        (body for _, _, body in app.ports.records.scan("task/")), reserve_pending=True)
                ],
            },
            "repository_context": await app.repository_context(head),
            "head": head,
            "reports": [app.review_report(report) for report in reports],
            "steering": steering,
            "user_updates": app.user_updates(run["steering_received"]),
            "pending_tasks": pending,
            "interrupted_tasks": [
                v for _, _, v in app.ports.records.scan("task/") if v["execution"] == "interrupted"
            ],
            "all_task_ids": [v["assignment"]["task_id"] for _, _, v in app.ports.records.scan("task/")],
            "allowed_write_paths": app.config.allowed_write_paths,
            "write_scope": app.config.write_scope,
            "write_authority": {
                "mode": app.config.write_scope,
                "may_assign_new_project_paths": app.config.write_scope == "project",
                "explicit_paths": app.config.allowed_write_paths if app.config.write_scope == "explicit" else None,
                "description": (
                    "May assign new project-relative file paths. allowed_write_paths is the initial seed, not a ceiling."
                    if app.config.write_scope == "project" else "Assignments must stay inside explicit_paths."
                ),
            },
            "memory": app.memory_view(),
            "closure_paths": app.config.closure_paths,
            "configured_checks": [c.name for c in app.check_definitions],
            "previous_acceptance": run.get("acceptance_failure"),
        }
        progress = {k: v for k, v in snapshot.items()
                    if k not in {"memory", "all_task_ids", "development_allocation", "previous_user_brief"}}
        fingerprint = digest(canonical(progress))
        if fingerprint == run.get("last_review_fingerprint"):
            app.update(
                "app/run",
                {**run, "status": "paused", "blocker": "Review made no progress on unchanged input"},
            )
            return
        query_index = run["senior_queries"] + 1
        app.update("app/run", {**run, "senior_queries": query_index})
        # Compare against the new application version so late ingress invalidates this query.
        expected_version = app.ports.records.get("app/run")[0]
        pid = f"senior-{query_index}"
        app.process(pid, "senior")
        if reports:
            evidence = await self.review_checks(pid, query_index, head)
            snapshot["independent_review_evidence"] = evidence
        endpoint = getattr(app.config, app.config.role_bindings["senior"])
        if endpoint.protocol in {"codex_app_server", "codex_proxy"}:
            await app.ports.workspaces.prepare_snapshot(
                CodeRevision.model_validate(head), pid, binding_ref=app.config.role_bindings["senior"]
            )
        query = {
            "process_id": pid,
            "mode": "initial" if run["plan_ref"] is None else "sprint_review",
            "input": snapshot,
            "logical_step": 0,
            "trajectory_ref": None,
            "workspace_id": pid,
        }
        result = await self.senior.ainvoke(
            query,
            {"configurable": {"thread_id": pid}, "recursion_limit": 20},
            context=self.context,
            durability="sync",
        )
        if result.get("error"):
            app.update("app/run", {**app.get("app/run"), "status": "paused", "blocker": result["error"]})
            return
        app.ports.records.compare_and_publish(
            {},
            {},
            {
                "proposal/" + pid: {
                    "proposal": result["proposal"],
                    "head": head,
                    "steering_through": run["steering_received"],
                }
            },
        )
        if (
            app.ports.records.get("app/run")[0] != expected_version
            or app.get("head/provisional")["code"] != head
        ):
            return  # Preserve stale proposal; never acknowledge newer input or reopen starts.
        batch = {
            "state": "applying",
            "proposal": result["proposal"],
            "pid": pid,
            "query_index": query_index,
            "run": run,
            "head": head,
            "snapshot": snapshot,
            "fingerprint": fingerprint,
        }
        app.update("review-batch/active", batch)
        await self._apply_review(batch)

    async def _apply_review(self, batch):
        app = self.app
        run, head, snapshot = batch["run"], batch["head"], batch["snapshot"]
        pid, query_index, fingerprint = batch["pid"], batch["query_index"], batch["fingerprint"]
        reports = snapshot["reports"]
        if app.get("app/run")["sprint"] > run["sprint"]:
            app.update("review-batch/active", {**batch, "state": "done"})
            return
        proposal = SeniorProposal.model_validate(batch["proposal"])
        retained = [
            body
            for _, _, body in app.ports.records.scan("task/")
            if body["assignment"]["task_id"] not in proposal.cancel_pending_task_ids or was_started(body)
        ]
        proposal = proposal.model_copy(
            update={"tasks": allocate(proposal.tasks, retained, app.config.senior_development_fraction)}
        )
        plan_ref = f"plan/{run['sprint'] + 1}"
        for assignment in proposal.tasks:
            if app.ports.records.get("task/" + assignment.task_id):
                raise ValueError("New tasks need new IDs; retry must be a linked new assignment")
            known = set(snapshot["all_task_ids"]) | {t.task_id for t in proposal.tasks}
            if not set(assignment.dependencies) <= known:
                raise ValueError("Unknown task dependency")
        known_reports = {r["record_id"] for r in reports}
        if any(d.report_ref not in known_reports for d in proposal.dispositions):
            raise ValueError("Disposition does not belong to the pinned review")
        # Each disposition has an independent durable intent/receipt; there is no atomic Git batch.
        for index, disposition in enumerate(proposal.dispositions):
            await self.resolve(pid, query_index, index, disposition)
        # New steering during disposition application stays pending; do not activate the old plan.
        current_version, current_run = app.ports.records.get("app/run")
        if current_run["steering_received"] != run["steering_received"]:
            app.update("review-batch/active", {**batch, "state": "superseded"})
            return
        final_head = app.get("head/provisional")["code"]
        unresolved = self.unresolved()
        updates = {}
        immutable_specs = {}
        expected = {"app/run": current_version}
        for assignment in proposal.tasks:
            key = "task/" + assignment.task_id
            task, specs = make_task(
                app,
                assignment,
                plan_ref,
                final_head,
                f"{run['sprint'] + 1}-{assignment.task_id}",
            )
            expected[key] = 0
            updates[key] = task
            immutable_specs.update(specs)
        for task_id in proposal.cancel_pending_task_ids:
            key = "task/" + task_id
            retained = app.ports.records.get(key)
            if not retained or retained[1]["execution"] not in {"pending", "interrupted"}:
                raise ValueError("Only an unstarted or safely interrupted task may be retired")
            task = retained[1]
            expected[key] = retained[0]
            updates[key] = {**task, "execution": "cancelled", "stop_reason": "superseded_by_plan"}
            attempt_key = "attempt/" + task["attempt_id"]
            attempt_version, attempt_body = app.ports.records.get(attempt_key)
            expected[attempt_key] = attempt_version
            updates[attempt_key] = (
                app.task_attempt(attempt_body,
                    update={
                        "revision": attempt_body["revision"] + 1,
                        "execution": "cancelled",
                        "stop_reason": "superseded_by_plan",
                    }
                )
                .model_dump(mode="json")
            )
        # Reviewed head cannot jump over unresolved contributing work.
        if not unresolved:
            reviewed_version = app.ports.records.get("head/reviewed")[0]
            expected["head/reviewed"] = reviewed_version
            updates["head/reviewed"] = {"code": final_head}
        plan = SprintPlan(
            **app.base(plan_ref),
            parent_plan_ref=run["plan_ref"],
            senior_query_ref=pid,
            goal=app.artifact(proposal.goal),
            task_spec_refs=[
                updates["task/" + assignment.task_id]["spec_ref"] for assignment in proposal.tasks
            ],
            resolution_refs=["resolution/" + d.report_ref for d in proposal.dispositions],
            input_report_refs=sorted(known_reports),
            steering_from=run["steering_applied"],
            steering_through=run["steering_received"],
            expected_head=CodeRevision.model_validate(head),
        )
        updates["app/run"] = {
            **current_run,
            "sprint": run["sprint"] + 1,
            "plan_ref": plan_ref,
            "steering_applied": run["steering_received"],
            "starts_closed": proposal.complete,
            "captured_workers": [],
            "completion_proposed": proposal.complete,
            "last_review_fingerprint": fingerprint,
            "blocker": None,
        }
        if proposal.memory_update is not None:
            memory = app.ports.records.get("memory/working")
            expected["memory/working"] = memory[0] if memory else 0
            updates["memory/working"] = {
                "summary": proposal.memory_update,
                "covered_note_refs": [key for key, _, _ in app.ports.records.scan("memory-note/")],
                "source_query": pid,
                "source_head": final_head,
            }
        actionable = any(
            body["execution"] == "pending" and body["assignment"]["task_id"] not in proposal.cancel_pending_task_ids
            for _, _, body in app.ports.records.scan("task/")
        ) or bool(proposal.tasks)
        if not proposal.complete and not actionable and not proposal.dispositions:
            updates["app/run"].update(
                status="paused", starts_closed=True,
                blocker="Plan has no actionable tasks and does not propose completion; waiting for new input",
            )
        app.ports.records.compare_and_publish(
            expected, updates, {**immutable_specs, plan_ref: plan.model_dump(mode="json")}
        )
        app.update("review-batch/active", {**batch, "state": "done"})
        if (not proposal.complete and not proposal.dispositions and not self.ready()
                and not app.get("app/run")["active_workers"]):
            app.update("app/run", {**app.get("app/run"), "status": "paused", "starts_closed": True,
                                   "blocker": "No runnable tasks; resolve the blocker or supply new input"})
        app.process_status(pid, state="completed", phase="reviewed", terminal_result_ref="proposal/" + pid)

    async def review_checks(self, pid, query_index, head):
        app = self.app
        permit = await app.ports.exclusive.acquire("verification/project", pid)
        try:
            code = CodeRevision.model_validate(head)
            tree = await app.ports.workspaces.tree(code.commit_id, pid)
            wid = f"review-checks-{query_index}"
            await app.ports.workspaces.create(
                wid,
                pid,
                "review/" + pid,
                code,
                (list(tree) if app.config.write_scope == "project" else list(app.config.allowed_write_paths)),
                list(tree),
            )
            await app.ports.workspaces.integrate(wid, code, permit)
            state = {
                "process_id": pid,
                "workspace_id": wid,
                "logical_step": "review",
                "verification_permit_ref": permit,
            }
            return await app.checks(state, [c.name for c in app.check_definitions])
        finally:
            if not app.ports.operations.uncertain():
                await app.ports.exclusive.release(permit, pid)

    def unresolved(self):
        app = self.app
        return [
            key
            for key, _, _ in app.ports.records.scan("report/")
            if not app.ports.records.get("resolution/" + key)
            or app.get("resolution/" + key)["action"] in {"retry", "defer"}
        ]

    async def resolve(self, pid, query_index, index, disposition):
        app = self.app
        key = "resolution/" + disposition.report_ref
        old = app.ports.records.get(key)
        if old and old[1].get("query") == query_index:
            return
        report = app.get(disposition.report_ref)
        private = report.get("code_location") == "private"
        if private and disposition.action == "keep":
            raise ValueError("Private failed code cannot be kept; reject it or assign a repair")
        if disposition.action == "revert" and not private:
            await self.revert(pid, query_index, index, disposition)
            return
        resolution = ReviewResolution(
            **app.base(f"resolution-event/{query_index}/{index}"),
            report_ref=disposition.report_ref,
            senior_query_ref=pid,
            action=disposition.action,
            reason=app.artifact(disposition.reason),
            reviewed_resulting_code=CodeRevision.model_validate(app.get("head/provisional")["code"]),
            revert_commit_id=None,
            followup_task_refs=[],
            evidence_refs=[
                e["evidence_id"]
                for e in app.get("review-batch/active")["snapshot"].get("independent_review_evidence", [])
            ],
        )
        app.ports.records.compare_and_publish(
            {key: old[0] if old else 0},
            {
                key: {
                    "action": disposition.action,
                    "query": query_index,
                    "resolution_ref": resolution.record_id,
                }
            },
            {resolution.record_id: resolution.model_dump(mode="json")},
        )

    async def revert(self, pid, query_index, index, disposition):
        app = self.app
        receipt_ref = f"senior-receipt/{query_index}/{index}"
        if app.ports.records.get(receipt_ref):
            return
        permit = await app.ports.exclusive.acquire("verification/project", pid)
        try:
            report = app.get(disposition.report_ref)
            head = CodeRevision.model_validate(app.get("head/provisional")["code"])
            parent = await app.ports.workspaces.tree(report["candidate_parent_commit_id"], pid)
            candidate = await app.ports.workspaces.tree(report["candidate_commit_id"], pid)
            current = await app.ports.workspaces.tree(head.commit_id, pid)
            touched = {p for p in parent.keys() | candidate.keys() if parent.get(p) != candidate.get(p)}
            # Conservative inverse: do not silently overwrite any later edit.
            if any(current.get(p) != candidate.get(p) for p in touched):
                raise RuntimeError("Revert overlaps later edits; requires a specialist repair assignment")
            workspace_id = f"senior-revert-{query_index}-{index}"
            manifest = await app.ports.workspaces.create(
                workspace_id,
                pid,
                disposition.report_ref,
                head,
                sorted(set(current) | touched)
                if app.config.write_scope == "project"
                else list(app.config.allowed_write_paths),
                list(current),
            )
            manifest = await app.ports.workspaces.integrate(workspace_id, head, permit)
            # Trusted inverse is the only direct tree manipulation in application review;
            # use scoped file capabilities so the OS remains the effect authority.
            state = {
                "process_id": pid,
                "workspace_id": workspace_id,
                "logical_step": index,
                "verification_permit_ref": permit,
            }
            for path in sorted(touched):
                current_digest = digest(current[path][1]) if path in current else None
                tool = "files.write" if path in parent else "files.delete"
                args = {"path": path, "expected_digest": current_digest, "generation": manifest.generation}
                if path in parent:
                    args["content"] = parent[path][1].decode()
                result, output = await app.capability(
                    state, f"revert-{index}-{path}", tool, args, "private_write"
                )
                if result.state != "succeeded":
                    raise RuntimeError(str(output))
            evidence = await app.checks(state, [c.name for c in app.check_definitions])
            if any(e["status"] != "passed" for e in evidence):
                raise RuntimeError("Reverted resulting tree did not pass independent checks")
            result, code = await app.capability(
                state, f"revert-commit-{index}", "workspace.commit", {}, "shared_write"
            )
            if result.state != "succeeded":
                raise RuntimeError(str(code))
            key = "resolution/" + disposition.report_ref
            old = app.ports.records.get(key)
            head_version = app.ports.records.get("head/provisional")[0]
            resolution = ReviewResolution(
                **app.base(f"resolution-event/{query_index}/{index}"),
                report_ref=disposition.report_ref,
                senior_query_ref=pid,
                action="revert",
                reason=app.artifact(disposition.reason),
                reviewed_resulting_code=CodeRevision.model_validate(code),
                revert_commit_id=code["commit_id"],
                followup_task_refs=[],
                evidence_refs=[e["evidence_id"] for e in evidence],
            )
            args = {
                "permit_ref": permit,
                "receipt_ref": receipt_ref,
                "expected": {"head/provisional": head_version, key: old[0] if old else 0},
                "updates": {
                    "head/provisional": {"code": code},
                    key: {"action": "revert", "query": query_index, "resolution_ref": resolution.record_id},
                },
                "immutable": {
                    resolution.record_id: resolution.model_dump(mode="json"),
                    receipt_ref: {
                        "previous_head": head.model_dump(mode="json"),
                        "published_head": code,
                        "resolution_ref": resolution.record_id,
                        "evidence": evidence,
                    },
                },
            }
            result, output = await app.capability(
                state, f"revert-publish-{index}", "records.publish", args, "shared_write"
            )
            if result.state != "succeeded":
                raise RuntimeError(str(output))
        finally:
            if not app.ports.operations.uncertain():
                # Definite aborted inverse remains private, never a fabricated worker report.
                await app.ports.exclusive.release(permit, pid)

    async def accept(self):
        app = self.app
        self.close_starts()
        version, run = app.ports.records.get("app/run")
        if run["active_workers"] or self.unresolved() or run["steering_received"] != run["steering_applied"]:
            return False
        if any(
            t["execution"] not in {"completed", "cancelled"} for _, _, t in app.ports.records.scan("task/")
        ):
            return False
        head = app.get("head/provisional")["code"]
        if app.get("head/reviewed")["code"] != head:
            return False
        permit = await app.ports.exclusive.acquire("verification/project", "controller")
        try:
            # Pin every completion authority before checks; ingress can still run.
            version, run = app.ports.records.get("app/run")
            if run["active_workers"] or app.ports.operations.uncertain():
                return False
            attempt = run["acceptance_attempts"] + 1
            app.ports.records.compare_and_publish(
                {"app/run": version}, {"app/run": {**run, "acceptance_attempts": attempt}}
            )
            version, run = app.ports.records.get("app/run")
            head_version = app.ports.records.get("head/provisional")[0]
            reviewed_version = app.ports.records.get("head/reviewed")[0]
            code = CodeRevision.model_validate(head)
            tree = await app.ports.workspaces.tree(code.commit_id, "controller")
            wid = f"acceptance-{attempt}"
            await app.ports.workspaces.create(
                wid,
                "controller",
                run["plan_ref"] or "initial",
                code,
                list(tree) if app.config.write_scope == "project" else list(app.config.allowed_write_paths),
                list(tree),
            )
            await app.ports.workspaces.integrate(wid, code, permit)
            state = {
                "process_id": "controller",
                "workspace_id": wid,
                "logical_step": attempt,
                "verification_permit_ref": permit,
            }
            evidence = await app.checks(state, [c.name for c in app.check_definitions])
            current = await app.ports.workspaces.revision(wid)
            passing = bool(evidence) and all(
                e["status"] == "passed"
                and e["checked_code"]["effective_tree_digest"] == head["effective_tree_digest"]
                and e["checked_code"]["environment_digest"] == head["environment_digest"]
                for e in evidence
            )
            passing &= current.effective_tree_digest == head["effective_tree_digest"]
            if not passing:
                latest = app.get("app/run")
                app.update(
                    "app/run",
                    {
                        **latest,
                        "completion_proposed": False,
                        "acceptance_failure": evidence,
                        "starts_closed": True,
                    },
                )
                return False
            if app.ports.records.get("app/run")[0] != version:
                return False
            if app.ports.operations.uncertain() or self.unresolved() or app.get("app/run")["active_workers"]:
                return False
            receipt = f"acceptance-receipt/{attempt}"
            args = {
                "permit_ref": permit,
                "receipt_ref": receipt,
                "expected": {
                    "app/run": version,
                    "head/provisional": head_version,
                    "head/reviewed": reviewed_version,
                },
                "updates": {"app/run": {**run, "status": "delivering", "acceptance_ref": receipt,
                                         "output_delivery_attempt": 1}},
                "immutable": {
                    receipt: {
                        "code": head,
                        "plan_ref": run["plan_ref"],
                        "steering_through": run["steering_applied"],
                        "evidence": evidence,
                    }
                },
            }
            result, _ = await app.capability(
                state, f"acceptance-publish-{attempt}", "records.publish", args, "shared_write"
            )
            if result.state == "succeeded" and app.ports.records.get(receipt) is not None:
                return await self.deliver_outputs()
            return False
        finally:
            if not app.ports.operations.uncertain():
                await app.ports.exclusive.release(permit, "controller")


async def tick(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    engine = app.engine
    run = await engine.consume()
    if run["status"] != "active":
        return {"next_transition": "finish", "outcome": run["status"]}
    if run["completion_proposed"] and not run["active_workers"]:
        if await engine.accept():
            return {"next_transition": "finish", "outcome": "completed"}
        run = app.get("app/run")
        if run["completion_proposed"]:
            app.update("app/run", {**run, "completion_proposed": False})
    run = app.get("app/run")
    ready = engine.ready()
    if run["starts_closed"] or (not ready and not run["active_workers"]):
        return {"next_transition": "review"}
    if ready and len(run["active_workers"]) < app.worker_limit:
        return {"next_transition": "dispatch"}
    return {"next_transition": "wait"}


async def dispatch(state, runtime: Runtime[AppContext]):
    await runtime.context.services.engine.dispatch()
    return {"logical_step": state["logical_step"] + 1}


async def review(state, runtime: Runtime[AppContext]):
    await runtime.context.services.engine.review()
    return {"logical_step": state["logical_step"] + 1}


async def wait(state, runtime: Runtime[AppContext]):
    engine = runtime.context.services.engine
    if engine.workers:
        await asyncio.wait(engine.workers.values(), return_when=asyncio.FIRST_COMPLETED)
    else:
        if not engine.app.get("app/run")["starts_closed"]:
            raise RuntimeError("No actionable work or active worker")
    return {"logical_step": state["logical_step"] + 1}


def build_controller(checkpointer):
    graph = StateGraph(ControllerState, context_schema=AppContext)
    for name, function in (("tick", tick), ("dispatch", dispatch), ("review", review), ("wait", wait)):
        graph.add_node(name, function)
    graph.add_edge(START, "tick")
    graph.add_conditional_edges(
        "tick",
        lambda s: s["next_transition"],
        {"dispatch": "dispatch", "review": "review", "wait": "wait", "finish": END},
    )
    for node in ("dispatch", "review", "wait"):
        graph.add_edge(node, "tick")
    return graph.compile(checkpointer=checkpointer)
