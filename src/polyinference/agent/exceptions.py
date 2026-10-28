"""Clean semantic interruptions are review inputs, never fabricated worker reports."""

from ..contracts import CodeRevision, ProcessStatus
from ..domain import canonical, digest, now
from .routing import cloud_recovery


def pending(app):
    return [
        value
        for _, _, value in app.ports.records.scan("exception-queue/")
        if value["action"] in {"pending", "defer", "stop"}
    ]


def review_view(app):
    result = [{**app.get(item["exception_ref"]), "action": item["action"]} for item in pending(app)]
    for _, _, item in app.ports.records.scan("exception-queue/"):
        if item["action"] != "retry":
            continue
        task = app.ports.records.get("task/" + (item.get("replacement_task_id") or ""))
        if task and task[1]["execution"] == "pending" and task[1].get("previous_process_id"):
            result.append({**app.get(item["exception_ref"]), "action": "retry",
                           "pending_replacement_task_id": task[1]["assignment"]["task_id"]})
    return result


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
                    "model_failure": state.get("model_failure"),
                    "diagnosis": state.get("model_failure_diagnosis"),
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
    attempt = app.task_attempt(
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
        "cloud_recoveries": task.get("cloud_recoveries", 0),
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
        "model_failure": state.get("model_failure"),
        "diagnosis": state.get("model_failure_diagnosis"),
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


async def park_model_failure(app, state, failure):
    """Application handoff after bounded I/O repair, never another transport retry."""
    if not failure or failure.get("execution_termination") != "confirmed_stopped" or failure.get("effects") != "known":
        return False
    error = failure.get("error") or {}
    if (error.get("code") not in {"IncompleteGeneration", "ModelResponseError", "NativeJobStopped"}
            or error.get("retryable_after_reconciliation") is False
            or failure.get("diagnostics", {}).get("polyinference/model-unavailable")):
        return False
    reason = failure.get("diagnostics", {}).get("polyinference/model-output-error", {}).get("reason")
    if (error.get("code") == "NativeJobStopped" and reason != "invalid_native_output"
            or error.get("code") == "ModelResponseError" and reason not in {"empty_text", "unexpected_content"}):
        return False
    task = app.get(state["task_ledger_ref"])
    if task.get("exception_ref") and task.get("semantic_model_failure") == failure:
        return True
    control = app.ports.records.get("process-control/" + state["process_id"])
    if (state.get("phase") != "development" or task.get("category", "development") != "development"
            or task.get("report_ref") or (control and control[1].get("cancel_requested"))
            or app.ports.operations.uncertain()):
        return False
    reserve = app.config.limits.final_phase_reserve
    finishing = reserve.reconciliation_model_calls + reserve.assessment_model_calls if reserve else 2
    cutoff = app.ports.operations.process_deadline(state["process_id"])
    if cutoff is None:
        from datetime import datetime, timedelta

        cutoff = datetime.fromisoformat(app.get("process/" + state["process_id"])["started_at"]) + timedelta(
            milliseconds=app.config.limits.max_wall_time_ms)
    if (app.ports.operations.inference_calls_used(state["process_id"]) >= app.config.limits.max_model_calls - finishing
            or cutoff <= now()):
        return False
    resources = app.ports.operations.resource_state(state["process_id"])
    finishing_steps = finishing + (reserve.publication_steps + reserve.cleanup_steps if reserve else 2) + 1
    if (resources["remaining_operations"] < finishing_steps or resources["remaining_tokens"]
            < app.config.limits.max_input_tokens_per_call + app.config.limits.max_output_tokens_per_call):
        return False
    if app.ports.operations.settlement(state["process_id"])["pending_operations"]:
        return False
    from .diagnostics import diagnose

    reason = "Stopped unusable model output after bounded OS repair: " + str(error.get("message", ""))[:900]
    diagnosis = await diagnose(app, state, "model_output", reason=reason)
    await park(app, {**state, "model_failure": failure,
        "model_failure_diagnosis": diagnosis, "interrupted": reason})
    current = app.get(state["task_ledger_ref"])
    app.update(state["task_ledger_ref"], {**current, "model_failure": None,
        "semantic_model_failure": failure})
    return True


def validate_allowance(app, packet):
    """Original physical envelope; a backend change never refills it."""
    if packet.get("execution_termination") != "confirmed_stopped" or packet.get("effects") != "known":
        raise ValueError("Recovery requires confirmed stopped execution and known effects")
    task = app.get("task/" + packet["task_id"])
    if (task["execution"] != "interrupted" or task.get("report_ref")
            or task.get("category", "development") != "development"
            or task.get("exception_ref") != packet["exception_ref"]):
        raise ValueError("Recovery requires an unpublished clean development exception")
    control = app.ports.records.get("process-control/" + packet["process_id"])
    if control and control[1].get("cancel_requested"):
        raise ValueError("Explicit cancellation cannot become recovery")
    if app.ports.operations.uncertain():
        raise ValueError("Unsettled execution must be reconciled before handoff")
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
    finishing_steps = finishing + (reserve.publication_steps + reserve.cleanup_steps if reserve else 2) + 1
    if (
        resources["remaining_operations"] < finishing_steps
        or resources["remaining_tokens"]
        < app.config.limits.max_input_tokens_per_call + app.config.limits.max_output_tokens_per_call
    ):
        raise ValueError("Original operation/token allowance cannot safely start replacement work")


def validate(app, proposal, snapshot):
    visible = {e["exception_ref"]: e for e in snapshot.get("exceptions", [])}
    seen, replacements = set(), {}
    for decision in proposal.exception_dispositions:
        if decision.exception_ref in seen or decision.exception_ref not in visible:
            raise ValueError("Exception disposition must reference one pinned unresolved exception")
        seen.add(decision.exception_ref)
        packet = visible[decision.exception_ref]
        pending_id = packet.get("pending_replacement_task_id")
        if pending_id:
            old = app.get("task/" + pending_id)
            if (decision.action != "retry" or pending_id not in proposal.cancel_pending_task_ids
                    or old["execution"] != "pending"
                    or app.ports.records.get("process/" + old["process_id"])
                    or any(row["request"]["scope"].get("process_id") == old["process_id"]
                           for _, _, row in app.ports.records.scan("effect/"))):
                raise ValueError("Pending recovery retarget requires an unstarted lineage-preserving replacement")
        if decision.action != "retry":
            continue
        assignment = next((t for t in proposal.tasks if t.task_id == decision.replacement_task_id), None)
        if assignment is None or assignment.task_id in replacements:
            raise ValueError("Recovery needs exactly one new linked assignment")
        if pending_id:
            before = dict(old["assignment"])
            after = assignment.model_dump(mode="json")
            for field in ("task_id", "dependencies"):
                before.pop(field, None)
                after.pop(field, None)
            if before != after:
                raise ValueError("Pending recovery retarget must preserve its contract and source")
        if cloud_recovery(app.config, packet, assignment):
            if packet.get("cloud_recoveries", 0) >= app.config.max_cloud_recoveries:
                raise ValueError("Cloud recovery allowance exhausted; defer or stop")
        elif (packet.get("cloud_recoveries", 0)
              or packet["recovery_depth"] >= app.config.max_worker_recoveries):
            raise ValueError("Semantic recovery allowance exhausted; defer or stop")
        source = app.get("task/" + packet["task_id"])["assignment"]
        if (
            not cloud_recovery(app.config, packet, assignment)
            and assignment.objective == source["objective"]
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
        validate_allowance(app, packet)
        if not set(assignment.write_paths) <= set(source["write_paths"]):
            raise ValueError("Recovery cannot widen the original write grant")
        if assignment.resume_from not in {None, decision.exception_ref}:
            raise ValueError("Recovery may select only its predecessor's retained source")
        replacements[assignment.task_id] = {**packet, "changed_condition": decision.changed_condition}
    for assignment in proposal.tasks:
        if assignment.resume_from and assignment.task_id not in replacements and not (app.repository and any(s["resume_from"] == assignment.resume_from and s["available"] for s in snapshot.get("retained_sources", []))):
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
        if assignment.resume_from and assignment.task_id in replacements:
            await app.ports.workspaces.validate_handoff(
                replacements[assignment.task_id]["source_delta_ref"],
                CodeRevision.model_validate(head),
                assignment.write_paths,
            )
