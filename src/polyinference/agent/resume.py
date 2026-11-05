"""Coding continuation policy; the OS supplies execution preparation only."""
from __future__ import annotations

from ..primitives import canonical, digest, now


def progress(records, request_ref, state):
    key = "resume-progress/" + request_ref
    old = records.get(key)
    records.compare_and_publish({key: old[0] if old else 0}, {
        key: {"state": state, "updated_at": now().isoformat()},
    })

# Exact predecessor shipped with process-level Resume. Graph topology, prompts,
# process/task schemas and operation identities are unchanged by this migration.
COMPATIBLE_GRAPH = "sha256:50fa4c434f2228f76f46644080c2c5bd18df6f805e1b2d378483cc58dc9b2ca8"


def migrate_program(app):
    run = app.get("app/run")
    old, current = run["program"], app.program.model_dump(mode="json")
    if old == current:
        return
    if old.get("graph_digest") != COMPATIBLE_GRAPH or {
        k: v for k, v in old.items() if k != "graph_digest"
    } != {k: v for k, v in current.items() if k != "graph_digest"}:
        raise RuntimeError("Program/graph/prompt version changed; resume requires the pinned implementation")
    key = "coding/resume-program-migration/" + current["graph_digest"].split(":")[-1]
    row = app.ports.records.get("app/run")
    app.ports.records.compare_and_publish({"app/run": row[0]}, {
        "app/run": {**row[1], "program": current},
    }, {key: {"from": old, "to": current, "reason": "run_resume_control_compatible_v1"}})


async def resume_run(engine, request_ref):
    app = engine.app
    request = app.get(request_ref)
    outcome_key = "resume-outcome/" + request_ref
    previous = app.ports.records.get(outcome_key)
    run = app.get("app/run")
    if previous and (run["status"] not in {"active", "delivering"} or engine.workers):
        return
    if run["status"] == "completed":
        raise ValueError("Completed runs cannot be resumed")
    control = app.ports.records.get("process-control/controller")
    if control and control[1].get("cancel_requested"):
        raise ValueError("This run was cancelled and cannot be resumed")
    await app.ports.operations.prepare_resume(request_ref)
    progress(app.ports.records, request_ref, "continuing")
    pid = request.get("process_id")
    plan_key = "coding/resume-plan/" + request_ref
    if previous:
        # Execution had started before coordinator loss. Prepare continuation
        # from today's retained tasks, rather than reusing the original plan.
        signature = [(key, task) for key, _, task in app.ports.records.scan("task/")]
        plan_key += "/restart-" + digest(canonical(signature)).split(":")[-1]
    plan = app.ports.records.get(plan_key)
    if not plan:
        stopped = []
        for key, _, task in app.ports.records.scan("task/"):
            process = app.ports.records.get("process/" + task["process_id"])
            if process and process[1]["state"] in {"paused", "failed", "cancelled", "ready", "running"}:
                if task["execution"] in {"in_progress", "interrupted"}:
                    stopped.append(key)
        checkpoints = []
        for key in stopped:
            task = app.get(key)
            control = app.ports.records.get("process-control/" + task["process_id"])
            if task["execution"] == "in_progress" and not task.get("model_failure") and not (
                control and control[1].get("cancel_requested")
            ):
                saved = await engine.worker.aget_state({"configurable": {"thread_id": task["process_id"]}})
                if saved.next:
                    checkpoints.append(key)
        selected = next((key for key in stopped if app.get(key).get("model_failure")
                         and (pid is None or app.get(key)["process_id"] == pid)
                         and not (app.ports.records.get("process-control/" + app.get(key)["process_id"])
                                  or (0, {}))[1].get("cancel_requested")), None)
        plan = (1, {"tasks": stopped, "retry": selected if not checkpoints else None,
                    "checkpoints": checkpoints,
                    "delivery": not request.get("text") and bool(run.get("acceptance_ref"))})
        app.ports.records.put_once(plan_key, plan[1])
    plan = plan[1]
    # All stopped workers are represented in senior review, including workers
    # other than an optional legacy process selection.
    for key in plan["tasks"]:
        task = app.get(key)
        if (task.get("report_ref") or key in plan["checkpoints"]
                or (key == plan["retry"] and task["execution"] == "in_progress"
                    and not task.get("model_failure"))):
            continue
        if task["execution"] != "completed":
            await app.preserve_interrupted(key)
            if not await engine.settle_stopped_worker(key, "operator_resume_for_review"):
                raise RuntimeError("Could not resume while previous work is still running.")
    run = app.get("app/run")
    app.update("app/run", {**run, "active_workers": [], "captured_workers": [],
                          "status": "active", "starts_closed": True,
                          "blocker": None, "completion_proposed": False})
    if request.get("text"):
        engine.steer(request["text"], request_ref=request_ref)
    if plan["checkpoints"]:
        pids = [app.get(key)["process_id"] for key in plan["checkpoints"]]
        app.update("app/run", {**app.get("app/run"), "active_workers": pids, "captured_workers": pids})
        for key, pid in zip(plan["checkpoints"], pids):
            process = app.get("process/" + pid)
            app.update("process/" + pid, {**process, "state": "ready"})
            await engine.launch(key, resume=True)
    elif plan["retry"]:
        task = app.get(plan["retry"])
        if task.get("model_failure"):
            await engine.retry_worker(task["assignment"]["task_id"], request.get("text") or "User requested resume")
        else:
            # The retry checkpoint/ledger was committed before a coordinator
            # restart. Reattach it rather than minting another recovery intent.
            pid = task["process_id"]
            process = app.get("process/" + pid)
            app.update("process/" + pid, {**process, "state": "ready"})
            app.update("app/run", {**app.get("app/run"), "active_workers": [pid], "captured_workers": [pid]})
            await engine.launch(plan["retry"], resume=True)
    elif plan["delivery"]:
        engine.retry_outputs("User requested resume")
    if not previous:
        app.update(outcome_key, {"state": "applied", "process_id": request.get("process_id"),
                                 "applied_at": now().isoformat()})
    progress(app.ports.records, request_ref, "running")
