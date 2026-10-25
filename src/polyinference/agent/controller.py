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
    TaskAttempt,
    TaskSpec,
)
from ..domain import SeniorProposal, canonical, digest, now
from .architecture import catalog, validate_plan
from .design_basis import DESIGN_BASIS
from .exceptions import obligation_satisfied, review_view, validate_sources
from .exceptions import validate as validate_exceptions
from .review import check_view, code_identity, contract, evidence_catalog, fit_snapshot, validate_completion
from .routing import allocate
from .senior import build_senior
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
            return
        requirements = [
            Requirement(feature_id="runtime/" + name, version="1", necessity="required")
            for name in (
                "effect-journal",
                "private-workspace",
                "global-shell-exclusion",
                "verification-exclusion",
                "atomic-record-publication",
                "scoped-workspace-copy",
                "workspace-view",
                "direct-tools",
                "artifacts",
                "persistent-checkpoints",
                "fixed-role-routing",
                "process-recovery",
                "execution-progress",
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
            entry_points=["controller", "worker", "senior", "check_diagnosis"],
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
        initial = await app.ports.workspaces.initialize()
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
        await self.initialize()
        if self.app.ports.operations.uncertain():
            raise RuntimeError("Uncertain effects require reconciliation; no replacement is dispatched")
        if self.app.config.prepare_repository and not self.app.ports.records.get("setup/completed"):
            from .setup import prepare

            await prepare(self)
            if self.app.get("app/run")["status"] != "active":
                return {"outcome": self.app.get("app/run")["status"]}
        saved = await self.controller.aget_state({"configurable": {"thread_id": "controller"}})
        initial = None if saved.next else {"process_id": "controller", "logical_step": 0}
        return await self.controller.ainvoke(
            initial,
            {"configurable": {"thread_id": "controller"}, "recursion_limit": 10000},
            context=self.context,
            durability="sync",
        )

    def steer(self, text):
        app = self.app
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
        if task["execution"] != "in_progress" and not (resume and task["execution"] == "completed"):
            return
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
        elif resume and task["execution"] == "completed":
            status = app.get("process-status/" + pid)
            facts = app.ports.operations.settlement(pid)
            if (
                status.get("cleanup_state") != "complete"
                or facts["pending_operations"]
                or facts["permit_refs"]
            ):
                raise RuntimeError(
                    "Completed worker has no resumable cleanup checkpoint; reconcile ownership"
                )
            return  # A completed END checkpoint needs detachment, never a fresh invocation.
        elif resume and saved.values:
            raise RuntimeError("Finished worker graph disagrees with its active task")

        async def drive():
            try:
                return await self.worker.ainvoke(
                    initial,
                    {
                        "configurable": {"thread_id": pid},
                        "recursion_limit": 6 * app.config.limits.max_steps + 128,
                    },
                    context=self.context,
                    durability="sync",
                )
            except Exception as exc:
                # Retain unknown effects and ownership. Definite stopped work may be parked.
                process = app.get("process/" + pid)
                app.update("process/" + pid, {**process, "state": "paused", "error": str(exc)[:2000]})
                raise

        self.workers[pid] = asyncio.create_task(drive())

    async def consume(self):
        app = self.app
        # Reattach active invocations after a supported safe interruption.
        run = app.get("app/run")
        tasks = {body["process_id"]: key for key, _, body in app.ports.records.scan("task/")}
        for pid in run["active_workers"]:
            if pid not in self.workers:
                await self.launch(tasks[pid], resume=True)
                if pid not in self.workers:
                    task = app.get(tasks[pid])
                    if task["execution"] != "completed" and not task.get("exception_ref"):
                        raise RuntimeError("Active worker lacks a resumable or safely completed invocation")
                    version, current = app.ports.records.get("app/run")
                    app.ports.records.compare_and_publish(
                        {"app/run": version},
                        {
                            "app/run": {
                                **current,
                                "starts_closed": current["starts_closed"]
                                or task["execution"] == "interrupted",
                                "active_workers": [p for p in current["active_workers"] if p != pid],
                                "captured_workers": [p for p in current["captured_workers"] if p != pid],
                            }
                        },
                    )
        finished = [pid for pid, task in self.workers.items() if task.done()]
        for pid in finished:
            future = self.workers.pop(pid)
            failure = future.exception()
            version, run = app.ports.records.get("app/run")
            task_ref = tasks[pid]
            task = app.get(task_ref)
            if failure or (task["execution"] == "interrupted" and not task.get("exception_ref")):
                app.ports.records.compare_and_publish(
                    {"app/run": version},
                    {
                        "app/run": {
                            **run,
                            "starts_closed": True,
                            "status": "paused",
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
                        "starts_closed": run["starts_closed"] or task["execution"] == "interrupted",
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
            if run["starts_closed"] or len(run["active_workers"]) >= app.config.max_workers:
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
            attempt = TaskAttempt.model_validate(attempt_body).model_copy(
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
                    key: {
                        **task,
                        "execution": "in_progress",
                        "base": base,
                        "spec_ref": spec_ref,
                        "started_at": now().isoformat(),
                    },
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
        report_views = [await app.review_report(report) for report in reports]
        snapshot = {
            "objective": run["objective"],
            "repository_setup": (app.ports.records.get("repository/setup") or (0, {}))[1],
            "development_allocation": {
                "senior_fraction": app.config.senior_development_fraction,
                "tasks": [
                    {"task_id": body["assignment"]["task_id"], "role": body["assignment"]["role"]}
                    for _, _, body in app.ports.records.scan("task/")
                    if body.get("category", "development") == "development"
                    and body["execution"] != "cancelled"
                ],
            },
            "repository_context": await app.repository_context(
                head, [p for r in report_views for p in r["changed_paths"]]
            ),
            "head": head,
            "reports": report_views,
            "exceptions": review_view(app),
            "steering": steering,
            "pending_tasks": pending,
            "interface_contracts": [c.model_dump(mode="json") for c in catalog(app).values()],
            "all_task_ids": [v["assignment"]["task_id"] for _, _, v in app.ports.records.scan("task/")],
            "allowed_write_paths": app.config.allowed_write_paths,
            "write_scope": app.config.write_scope,
            "memory": app.memory_view(),
            "closure_paths": app.config.closure_paths,
            "configured_checks": [c.name for c in app.config.checks],
            "previous_acceptance": run.get("acceptance_failure"),
            "acceptance_contract": contract(app, head),
        }
        stable = {k: v for k, v in snapshot.items() if k != "memory"}
        stable["exceptions"] = [{k: v for k, v in e.items() if k != "action"} for e in snapshot["exceptions"]]
        fingerprint = digest(canonical(stable))
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
        # Check the current head even when all reports were resolved previously.
        # A source review or a syntax check alone is not project acceptance.
        evidence = await self.review_checks(pid, query_index, head)
        snapshot["independent_review_evidence"] = [
            {key: e[key] for key in ("evidence_id", "criterion_ref", "status")}
            | {"checked_code": code_identity(e["checked_code"])}
            for e in evidence
        ]
        snapshot["independent_check_diagnostics"] = [check_view(app, e, cap=1500) for e in evidence]
        snapshot["review_evidence_catalog"] = evidence_catalog(snapshot)
        try:
            snapshot = fit_snapshot(app, snapshot)
        except ValueError as exc:
            app.update(
                "app/run",
                {
                    **app.get("app/run"),
                    "status": "paused",
                    "blocker": str(exc),
                    "review_input_ref": app.artifact(snapshot).model_dump(mode="json"),
                },
            )
            return
        endpoint = getattr(app.config, app.config.role_bindings["senior"])
        if endpoint.protocol in {"codex_app_server", "codex_proxy"}:
            await app.ports.workspaces.prepare_snapshot(CodeRevision.model_validate(head), pid)
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
            {
                "configurable": {"thread_id": pid, "corrections": app.config.max_senior_corrections},
                "recursion_limit": 80,
            },
            context=self.context,
            durability="sync",
        )
        if result.get("error"):
            app.update("app/run", {**app.get("app/run"), "status": "paused", "blocker": result["error"]})
            return
        # Retrieval changes the pinned review packet; retain exactly what was seen.
        snapshot = result["input"]
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
        replacements = validate_exceptions(app, proposal, snapshot)
        interfaces = validate_plan(proposal, [v for _, _, v in app.ports.records.scan("task/")], catalog(app))
        await validate_sources(app, proposal, replacements, head)
        retained = [
            body
            for _, _, body in app.ports.records.scan("task/")
            if body["assignment"]["task_id"] not in proposal.cancel_pending_task_ids
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
        await validate_sources(app, proposal, replacements, final_head)
        completion = proposal.complete
        completion_failure = None
        if completion:
            try:
                validate_completion(proposal, snapshot)
                if final_head != head:
                    raise ValueError("Head-changing dispositions require a fresh resulting-tree review")
            except ValueError as exc:
                completion = False
                completion_failure = {"semantic_review": str(exc)}
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
                interfaces=interfaces,
                predecessor=replacements.get(assignment.task_id),
            )
            expected[key] = 0
            updates[key] = task
            immutable_specs.update(specs)
        for decision in proposal.exception_dispositions:
            packet = app.get(decision.exception_ref)
            old_key = "task/" + packet["task_id"]
            old_version, old_task = app.ports.records.get(old_key)
            queue_key = "exception-queue/" + old_task["attempt_id"]
            queue_version, queue = app.ports.records.get(queue_key)
            expected[queue_key] = queue_version
            updates[queue_key] = {
                **queue,
                **decision.model_dump(mode="json"),
                "review_ref": "proposal/" + pid,
            }
            if decision.action == "retry":
                expected[old_key] = old_version
                updates[old_key] = {**old_task, "replacement_task_id": decision.replacement_task_id}
        for interface in proposal.interface_contracts:
            key = "interface-contract/" + interface.reference
            if not app.ports.records.get(key):
                immutable_specs[key] = interface.model_dump(mode="json")
        for task_id in proposal.cancel_pending_task_ids:
            key = "task/" + task_id
            retained = app.ports.records.get(key)
            if not retained or retained[1]["execution"] != "pending":
                raise ValueError("Only an existing unstarted task may be cancelled")
            task = retained[1]
            expected[key] = retained[0]
            updates[key] = {**task, "execution": "cancelled", "stop_reason": "superseded_by_plan"}
            attempt_key = "attempt/" + task["attempt_id"]
            attempt_version, attempt_body = app.ports.records.get(attempt_key)
            expected[attempt_key] = attempt_version
            updates[attempt_key] = (
                TaskAttempt.model_validate(attempt_body)
                .model_copy(
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
            "starts_closed": completion,
            "captured_workers": [],
            "completion_proposed": completion,
            "semantic_completion": {
                "proposal_ref": "proposal/" + pid,
                "head": head,
                "contract": snapshot.get("acceptance_contract"),
                "assessment": proposal.completion_assessment.model_dump(mode="json"),
            }
            if completion
            else None,
            "last_review_fingerprint": fingerprint,
        }
        if completion_failure:
            updates["app/run"]["acceptance_failure"] = completion_failure
        if any(d.action == "stop" for d in proposal.exception_dispositions):
            updates["app/run"].update(
                status="paused", starts_closed=True, blocker="Senior stopped worker exception recovery"
            )
        if completion:
            semantic = {
                **updates["app/run"]["semantic_completion"],
                "review_ref": "completion-review/" + pid,
                "evidence_catalog": snapshot["review_evidence_catalog"],
            }
            updates["app/run"]["semantic_completion"] = semantic
            immutable_specs[semantic["review_ref"]] = semantic
        if proposal.memory_update is not None:
            memory = app.ports.records.get("memory/working")
            expected["memory/working"] = memory[0] if memory else 0
            updates["memory/working"] = {
                "summary": proposal.memory_update,
                "covered_note_refs": [key for key, _, _ in app.ports.records.scan("memory-note/")],
                "source_query": pid,
                "source_head": final_head,
            }
        app.ports.records.compare_and_publish(
            expected, updates, {**immutable_specs, plan_ref: plan.model_dump(mode="json")}
        )
        app.update("review-batch/active", {**batch, "state": "done"})
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
            return await app.checks(state, [c.name for c in app.config.checks])
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
        if disposition.action == "revert":
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
            evidence = await app.checks(state, [c.name for c in app.config.checks])
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
        if any(not obligation_satisfied(app, t) for _, _, t in app.ports.records.scan("task/")):
            return False
        head = app.get("head/provisional")["code"]
        if app.get("head/reviewed")["code"] != head:
            return False
        semantic = run.get("semantic_completion")
        retained = app.ports.records.get(semantic["review_ref"]) if semantic else None
        proposal_record = app.ports.records.get(semantic["proposal_ref"]) if semantic else None
        if (
            not semantic
            or not retained
            or retained[1] != semantic
            or not proposal_record
            or semantic["head"] != head
            or semantic["contract"] != contract(app, head)
            or proposal_record[1]["head"] != head
            or proposal_record[1]["steering_through"] != run["steering_applied"]
            or proposal_record[1]["proposal"].get("completion_assessment") != semantic["assessment"]
        ):
            app.update(
                "app/run",
                {
                    **run,
                    "completion_proposed": False,
                    "acceptance_failure": {
                        "semantic_review": "Missing or stale source-backed completion review"
                    },
                },
            )
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
            evidence = await app.checks(state, [c.name for c in app.config.checks])
            current = await app.ports.workspaces.revision(wid)
            passing = all(
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
                "updates": {"app/run": {**run, "status": "completed", "acceptance_ref": receipt}},
                "immutable": {
                    receipt: {
                        "code": head,
                        "plan_ref": run["plan_ref"],
                        "steering_through": run["steering_applied"],
                        "evidence": evidence,
                        "semantic_review": semantic,
                    }
                },
            }
            result, _ = await app.capability(
                state, f"acceptance-publish-{attempt}", "records.publish", args, "shared_write"
            )
            return result.state == "succeeded" and app.ports.records.get(receipt) is not None
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
    if ready and len(run["active_workers"]) < app.config.max_workers:
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
