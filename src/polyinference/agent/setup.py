"""The initial cloud setup task uses the ordinary worker publication protocol."""

from __future__ import annotations

import asyncio

from ..contracts import CodeRevision, SprintPlan
from ..domain import Assignment
from .tasks import make_task


class SetupAssignment(Assignment):
    # Only setup can begin before acceptance checks have been discovered.
    checks: list[str]


async def prepare(engine):
    app = engine.app
    key = "task/project_setup"
    retained = app.ports.records.get(key)
    if not retained:
        base = app.get("head/provisional")["code"]
        tree = await app.ports.workspaces.tree(base["commit_id"])
        paths = sorted(tree) if app.config.write_scope == "project" else app.config.allowed_write_paths
        assignment = SetupAssignment(
            task_id="project_setup",
            role="specialist",
            objective="Prepare Git/branch and requested development prerequisites for: "
            + app.config.objective,
            write_paths=paths or app.config.allowed_write_paths,
            read_paths=sorted(tree),
            checks=[check.name for check in app.setup_check_definitions],
        )
        task, specs = make_task(app, assignment, "setup/plan", base, "setup-project", "setup")
        plan = SprintPlan(
            **app.base("setup/plan"),
            extensions={"polyinference/plan-kind": "setup"},
            parent_plan_ref=None,
            senior_query_ref=task["process_id"],
            goal=app.artifact(assignment.objective),
            task_spec_refs=[task["spec_ref"]],
            resolution_refs=[],
            input_report_refs=[],
            steering_from=0,
            steering_through=0,
            expected_head=CodeRevision.model_validate(base),
        )
        app.ports.records.compare_and_publish(
            {key: 0}, {key: task}, {**specs, plan.record_id: plan.model_dump(mode="json")}
        )
    task = app.get(key)
    if task["execution"] == "cancelled":
        return  # An explicitly retired setup is replaced by the senior's new plan.
    if task["execution"] != "completed":
        run_version, run = app.ports.records.get("app/run")
        updates = {
            "app/run": {**run, "active_workers": sorted(set(run["active_workers"]) | {task["process_id"]})}
        }
        expected = {"app/run": run_version}
        resume = task["execution"] != "pending"
        if not resume:
            task_version, task = app.ports.records.get(key)
            attempt_key = "attempt/" + task["attempt_id"]
            attempt_version, body = app.ports.records.get(attempt_key)
            attempt = app.task_attempt(body,
                update={"revision": body["revision"] + 1, "execution": "in_progress"}
            )
            expected.update({key: task_version, attempt_key: attempt_version})
            updates.update(
                {key: {**task, "execution": "in_progress"}, attempt_key: attempt.model_dump(mode="json")}
            )
        app.ports.records.compare_and_publish(expected, updates)
        await engine.launch(key, resume=resume)
        await asyncio.wait([engine.workers[task["process_id"]]])
        await engine.consume()
    task = app.get(key)
    if task["execution"] == "completed":
        app.ports.records.compare_and_publish(
            {},
            {},
            {
                "setup/completed": {
                    "report_ref": task["report_ref"],
                    "process_id": task["process_id"],
                }
            },
        )
