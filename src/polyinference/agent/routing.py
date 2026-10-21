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


def allocate(assignments, retained, fraction):
    # Pending tasks reserve future quota but are not historical starts in accounting.
    prior = development_history(retained, reserve_pending=True)
    senior = sum(task["assignment"]["role"] == "specialist" for task in prior)
    quota = max(
        0, min(len(assignments), math.floor((len(prior) + len(assignments)) * fraction + 0.5) - senior)
    )
    preferred = sorted(range(len(assignments)), key=lambda i: assignments[i].role != "specialist")
    chosen = set(preferred[:quota])
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
