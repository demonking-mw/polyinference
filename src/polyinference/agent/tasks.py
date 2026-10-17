"""Construct the same task/attempt envelopes for setup and development."""

from __future__ import annotations

from ..contracts import CodeRevision, Prerequisite, TaskAttempt, TaskSpec


def coding_tools(config, setup=False):
    tools = ["files.list", "files.read", "files.write", "files.delete", "checks.run"]
    if config.shell_execution != "disabled":
        tools.append("shell.run")
    if setup:
        tools.append("repository.select_branch")
    return tools


def make_task(app, assignment, plan_ref, base, attempt, category="development"):
    task = {
        "assignment": assignment.model_dump(mode="json"),
        "category": category,
        "plan_ref": plan_ref,
        "execution": "pending",
        "base": base,
        "spec_ref": "task-spec/" + assignment.task_id,
        "process_id": "worker-" + attempt,
        "attempt_id": attempt,
        "workspace_id": "workspace-" + attempt,
        "report_ref": None,
    }
    spec = TaskSpec(
        **app.base(task["spec_ref"]),
        extensions={"polyinference/project-write": True}
        if category == "setup" and app.config.write_scope == "project"
        else {},
        task_id=assignment.task_id,
        plan_ref=plan_ref,
        objective=app.artifact(assignment.objective),
        allowed_change_scope=assignment.write_paths,
        prerequisites=[
            Prerequisite(record_ref="task/" + dep, required_state="kept") for dep in assignment.dependencies
        ],
        base=CodeRevision.model_validate(base),
        acceptance_spec=app.artifact(assignment.checks),
        context_refs=[],
        memory_snapshot_refs=[],
        allowed_capabilities=coding_tools(app.config, category == "setup"),
        worker_process_spec_ref="process-spec/" + task["process_id"],
        report_schema_ref="task-report/2",
    )
    task_attempt = TaskAttempt(
        **app.base("attempt/" + attempt),
        task_spec_ref=spec.record_id,
        process_spec_ref=spec.worker_process_spec_ref,
        workspace_id=task["workspace_id"],
        original_base=spec.base,
        previous_attempt_ref=None,
        execution="pending",
        report_ref=None,
        stop_reason=None,
    )
    return task, {
        spec.record_id: spec.model_dump(mode="json"),
        task_attempt.record_id: task_attempt.model_dump(mode="json"),
    }
