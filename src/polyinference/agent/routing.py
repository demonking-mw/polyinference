"""Stable task-count allocation; management invocations never enter this denominator."""

from __future__ import annotations

import math


def allocate(assignments, retained, fraction):
    prior = [
        task
        for task in retained
        if task.get("category", "development") == "development"
        and (
            task["execution"] != "cancelled"
            or task.get("started_at")
            or task.get("spec_ref", "").endswith(":started")
        )
    ]
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
    tasks = [
        task
        for key, task in records.items()
        if key.startswith("task/")
        and task.get("category", "development") == "development"
        and (
            task["execution"] not in {"pending", "cancelled"}
            or task.get("started_at")
            or task.get("spec_ref", "").endswith(":started")
        )
    ]
    senior = sum(task["assignment"]["role"] == "specialist" for task in tasks)
    return {
        "target_senior_fraction": fraction,
        "started_development_tasks": len(tasks),
        "senior_tasks": senior,
        "junior_tasks": len(tasks) - senior,
        "actual_senior_fraction": senior / len(tasks) if tasks else None,
        "basis": "Started development tasks; setup, planning and management excluded",
    }
