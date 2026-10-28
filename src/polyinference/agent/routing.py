"""Stable task-count allocation; management invocations never enter this denominator."""

from __future__ import annotations

import math


def was_started(task):
    # Older task records retain the immutable dispatch-time spec even after retirement.
    return bool(task.get("started_at") or task.get("spec_ref", "").endswith(":started")
                or task["execution"] not in {"pending", "cancelled"})


def development_history(retained, *, reserve_pending=False):
    return [task for task in retained if task.get("category", "development") == "development"
            and (was_started(task) or (reserve_pending and task["execution"] == "pending"))]


def cloud_recovery(config, packet, assignment):
    """A coding-role handoff, distinct from cloud management or read-only diagnosis."""
    return (
        assignment.role == "specialist"
        and config.role_bindings["specialist"] == "cloud"
        and (packet.get("cloud_recoveries", 0) > 0
             or (packet["assignment"]["role"] == "worker"
                 and config.role_bindings["worker"] == "local"))
    )


def allocate(assignments, retained, fraction, *, protected_task_ids=()):
    # Pending tasks reserve future quota but are not historical starts in accounting.
    prior = development_history(retained, reserve_pending=True)
    senior = sum(task["assignment"]["role"] == "specialist" for task in prior)
    quota = max(
        0, min(len(assignments), math.floor((len(prior) + len(assignments)) * fraction + 0.5) - senior)
    )
    fixed = {i for i, task in enumerate(assignments) if task.task_id in protected_task_ids}
    chosen = {i for i in fixed if assignments[i].role == "specialist"}
    preferred = sorted((i for i in range(len(assignments)) if i not in fixed),
                       key=lambda i: assignments[i].role != "specialist")
    chosen.update(preferred[:max(0, quota - len(chosen))])
    return [
        assignment.model_copy(update={"role": "specialist" if i in chosen else "worker"})
        for i, assignment in enumerate(assignments)
    ]


def accounting(records, fraction=0.1):
    tasks = development_history(task for key, task in records.items() if key.startswith("task/"))
    senior = sum(task["assignment"]["role"] == "specialist" for task in tasks)
    return {
        "target_senior_fraction": fraction,
        "started_development_tasks": len(tasks),
        "senior_tasks": senior,
        "junior_tasks": len(tasks) - senior,
        "actual_senior_fraction": senior / len(tasks) if tasks else None,
        "basis": "Started development tasks; setup, planning and management excluded",
    }
