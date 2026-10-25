"""Clean semantic interruptions are review inputs, never fabricated worker reports."""

from ..contracts import CodeRevision, ProcessStatus, TaskAttempt
from ..domain import canonical, digest, now


def pending(app):
    return [
        value
        for _, _, value in app.ports.records.scan("exception-queue/")
        if value["action"] in {"pending", "defer", "stop"}
    ]


def review_view(app):
    return [{**app.get(item["exception_ref"]), "action": item["action"]} for item in pending(app)]


async def park(app, state):
    pid = state["process_id"]
    ref = "worker-exception/" + state["attempt_id"]
    if app.ports.records.get(ref):
        return
    if app.ports.operations.uncertain() or app.ports.records.get("receipt/" + state["attempt_id"]):
        raise RuntimeError("Uncertain or published work cannot become a semantic exception")
    intent_key = "park-intent/" + state["attempt_id"]
    retained = app.ports.records.get(intent_key)
    if retained:
        intent = retained[1]
    else:
        manifest = app.ports.workspaces.current(state["workspace_id"])
        snapshot = "park-" + state["attempt_id"]
        await app.ports.workspaces.prepare_workspace_snapshot(state["workspace_id"], snapshot)
        # Integration already sealed the original delta. Never flatten H-relative repairs into it.
        delta_ref = await app.ports.workspaces.preserve_delta(state["workspace_id"])
        intent = {
            "source_delta_ref": delta_ref,
            "abandoned_view_ref": snapshot,
            "phase": state["phase"],
            "manifest": manifest.model_dump(mode="json"),
            "diagnostics_ref": app.artifact(
                {
                    "reason": state.get("interrupted") or "needs_review",
                    "trajectory_ref": state.get("trajectory_ref"),
                    "evidence": state.get("evidence", []),
                    "last_check_evidence": state.get("last_check_evidence"),
                }
            ).model_dump(mode="json"),
        }
        app.ports.records.compare_and_publish({}, {}, {intent_key: intent})
    permit = state.get("verification_permit_ref")
    if permit:
        await app.ports.workspaces.abort(state["workspace_id"])
        if app.ports.exclusive.owns(permit, "verification/project", pid):
            await app.ports.exclusive.release(permit, pid)
    receipt = app.ports.operations.park_process(pid)
    task_version, task = app.ports.records.get(state["task_ledger_ref"])
    attempt_key = "attempt/" + state["attempt_id"]
    attempt_version, attempt = app.ports.records.get(attempt_key)
    attempt = TaskAttempt.model_validate(
        {
            **attempt,
            "revision": attempt["revision"] + 1,
            "execution": "interrupted",
            "stop_reason": "needs_review",
        }
    ).model_dump(mode="json")
    packet = {
        "exception_ref": ref,
        "task_id": task["assignment"]["task_id"],
        "process_id": pid,
        "attempt_ref": attempt_key,
        "root_task_id": task.get("root_task_id", task["assignment"]["task_id"]),
        "recovery_depth": task.get("recovery_depth", 0),
        "reason": (state.get("interrupted") or "needs_review")[:1200],
        "verdict": "uncertain",
        "execution_termination": "confirmed_stopped",
        "effects": "known",
        "original_base": task["base"],
        "assignment": task["assignment"],
        "task_spec_ref": task["spec_ref"],
        "calls_used": app.ports.operations.inference_calls_used(pid),
        "progress_attention": state.get("progress_attention"),
        "progress_ref": "worker-progress/" + pid if app.ports.records.get("worker-progress/" + pid) else None,
        "cleanup_receipt_ref": "process-parked/" + pid,
        **{k: v for k, v in intent.items() if k != "manifest"},
    }
    run_version, run = app.ports.records.get("app/run")
    status_key = "process-status/" + pid
    status_version, status = app.ports.records.get(status_key)
    status = ProcessStatus.model_validate(
        {
            **status,
            "revision": status["revision"] + 1,
            "state": "paused",
            "phase": "needs_review",
            "owner_generation": receipt["owner_generation"],
            "cleanup_state": "complete",
            "permit_refs": [],
            "pending_operations": [],
            "wait": None,
        }
    ).model_dump(mode="json")
    app.ports.records.compare_and_publish(
        {
            state["task_ledger_ref"]: task_version,
            attempt_key: attempt_version,
            "app/run": run_version,
            "exception-queue/" + state["attempt_id"]: 0,
            status_key: status_version,
        },
        {
            state["task_ledger_ref"]: {**task, "execution": "interrupted", "exception_ref": ref},
            attempt_key: attempt,
            status_key: status,
            "exception-queue/" + state["attempt_id"]: {"exception_ref": ref, "action": "pending"},
            "app/run": {
                **run,
                "starts_closed": True,
                "active_workers": [p for p in run["active_workers"] if p != pid],
                "captured_workers": [p for p in run["captured_workers"] if p != pid],
            },
        },
        {ref: packet},
    )


def validate(app, proposal, snapshot):
    visible = {e["exception_ref"]: e for e in snapshot.get("exceptions", [])}
    seen, replacements = set(), {}
    for decision in proposal.exception_dispositions:
        if decision.exception_ref in seen or decision.exception_ref not in visible:
            raise ValueError("Exception disposition must reference one pinned unresolved exception")
        seen.add(decision.exception_ref)
        packet = visible[decision.exception_ref]
        if decision.action != "retry":
            continue
        if packet["recovery_depth"] >= app.config.max_worker_recoveries:
            raise ValueError("Semantic recovery allowance exhausted; defer or stop")
        assignment = next((t for t in proposal.tasks if t.task_id == decision.replacement_task_id), None)
        if assignment is None or assignment.task_id in replacements:
            raise ValueError("Recovery needs exactly one new linked assignment")
        source = app.get("task/" + packet["task_id"])["assignment"]
        if (
            assignment.objective == source["objective"]
            and not assignment.resume_from
            and digest(
                canonical(
                    {
                        k: assignment.model_dump(mode="json")[k]
                        for k in ("write_paths", "read_paths", "checks", "dependencies")
                    }
                )
            )
            == digest(
                canonical({k: source[k] for k in ("write_paths", "read_paths", "checks", "dependencies")})
            )
        ):
            raise ValueError("Renaming unchanged work is not a recovery condition")
        reserve = app.config.limits.final_phase_reserve
        finishing = reserve.reconciliation_model_calls + reserve.assessment_model_calls if reserve else 2
        used = app.ports.operations.inference_calls_used(packet["process_id"])
        cutoff = app.ports.operations.process_deadline(packet["process_id"])
        process = app.get("process/" + packet["process_id"])
        if cutoff is None:
            from datetime import datetime, timedelta

            cutoff = datetime.fromisoformat(process["started_at"]) + timedelta(
                milliseconds=app.config.limits.max_wall_time_ms
            )
        if used >= app.config.limits.max_model_calls - finishing or cutoff <= now():
            raise ValueError("Original worker allowance exhausted; recovery cannot refill it")
        resources = app.ports.operations.resource_state(packet["process_id"])
        finishing_steps = (
            finishing + (reserve.publication_steps + reserve.cleanup_steps if reserve else 2) + 1
        )
        if (
            resources["remaining_operations"] < finishing_steps
            or resources["remaining_tokens"]
            < app.config.limits.max_input_tokens_per_call + app.config.limits.max_output_tokens_per_call
        ):
            raise ValueError("Original operation/token allowance cannot safely start replacement work")
        if not set(assignment.write_paths) <= set(source["write_paths"]):
            raise ValueError("Recovery cannot widen the original write grant")
        if assignment.resume_from not in {None, decision.exception_ref}:
            raise ValueError("Recovery may select only its predecessor's retained source")
        replacements[assignment.task_id] = packet
    for assignment in proposal.tasks:
        if assignment.resume_from and assignment.task_id not in replacements:
            raise ValueError("Source reuse requires a linked exception disposition")
        if assignment.task_id not in replacements and any(
            set(assignment.write_paths) & set(e["assignment"]["write_paths"]) for e in visible.values()
        ):
            raise ValueError("Work overlapping an unresolved exception needs a linked recovery")
    if proposal.complete and visible:
        raise ValueError("Unresolved exceptions cannot complete the project")
    return replacements


def obligation_satisfied(app, task):
    if task["execution"] != "interrupted" or not task.get("exception_ref"):
        return task["execution"] in {"completed", "cancelled"}
    queue = app.get("exception-queue/" + task["attempt_id"])
    if queue["action"] != "retry":
        return False
    replacement = app.get("task/" + queue["replacement_task_id"])
    if replacement["execution"] == "interrupted":
        return obligation_satisfied(app, replacement)
    resolution = (
        app.ports.records.get("resolution/" + replacement["report_ref"])
        if replacement.get("report_ref")
        else None
    )
    return bool(replacement["execution"] == "completed" and resolution and resolution[1]["action"] == "keep")


async def validate_sources(app, proposal, replacements, head):
    for assignment in proposal.tasks:
        if assignment.resume_from:
            await app.ports.workspaces.validate_handoff(
                replacements[assignment.task_id]["source_delta_ref"],
                CodeRevision.model_validate(head),
                assignment.write_paths,
            )
