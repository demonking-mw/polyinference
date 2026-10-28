"""Application policy for productive, bounded coding handoff; never an OS retry."""

from __future__ import annotations

from ..contracts import CodeRevision
from ..domain import Assignment, ExceptionDisposition, SeniorProposal
from .exceptions import validate_allowance
from .tasks import coding_tools


def capabilities(config):
    return {
        "worker_tools": coding_tools(config),
        "setup_only_tools": ["repository.select_branch", "checks.configure"],
        "senior_source_access": "Pinned previews + read_requests only",
        "shell_execution": config.shell_execution,
        "check_execution": config.check_execution,
        "browser": False,
        "mcp": False,
        "persistent_services": False,
        "native_tools": "Host broker only",
    }


async def offer(app, packet, head):
    """Explain ineligibility rather than letting a changed role bypass a hard boundary."""
    result = {"exception_ref": packet["exception_ref"], "eligible": False, "resume_from": None}
    try:
        if packet.get("pending_replacement_task_id"):
            raise ValueError("An existing pending recovery already owns this lineage")
        task = app.get("task/" + packet["task_id"])
        if (task.get("category", "development") != "development"
                or task["execution"] != "interrupted" or task.get("report_ref")
                or task.get("exception_ref") != packet["exception_ref"]):
            raise ValueError("Only unpublished clean development exceptions can transfer")
        control = app.ports.records.get("process-control/" + packet["process_id"])
        if control and control[1].get("cancel_requested"):
            raise ValueError("Explicit cancellation is not a recovery request")
        if app.config.role_bindings["specialist"] != "cloud":
            raise ValueError("Specialist is not bound to the configured cloud coding endpoint")
        local = app.config.local
        cloud = app.config.cloud
        def target(endpoint):
            transport = endpoint.command if endpoint.protocol == "codex_app_server" else endpoint.base_url
            return endpoint.protocol, endpoint.model, transport
        if target(local) == target(cloud):
            raise ValueError("Cloud recovery needs a different declared implementation backend")
        policy = app.config.data_policy
        endpoint = app.config.cloud
        if policy and ("cloud" not in policy.allowed_destination_classes
                       or (endpoint.inference_location not in policy.allowed_inference_locations
                           and not (endpoint.inference_location is None
                                    and {"local", "cloud"} <= set(policy.allowed_inference_locations)))):
            raise ValueError("Cloud recovery conflicts with the mandatory run data policy")
        used = packet.get("cloud_recoveries", 0)
        if used >= app.config.max_cloud_recoveries:
            raise ValueError("Cloud recovery allowance exhausted or disabled")
        if not used and not (packet["assignment"]["role"] == "worker"
                             and app.config.role_bindings["worker"] == "local"):
            raise ValueError("This exception is not local work awaiting cloud takeover")
        validate_allowance(app, packet)
        if app.ports.operations.uncertain():
            raise ValueError("Unsettled execution must be reconciled before handoff")
    except ValueError as exc:
        return {**result, "reason": str(exc)}
    try:
        await app.ports.workspaces.validate_handoff(
            packet["source_delta_ref"], CodeRevision.model_validate(head),
            packet["assignment"]["write_paths"],
        )
        result["resume_from"] = packet["exception_ref"]
        source = "retained development delta"
    except ValueError as exc:
        # A stale delta cannot be blindly applied; a cloud worker can reconstruct
        # the same contract from the current base, within the original grant.
        source = "fresh current base; retained source cannot apply: " + str(exc)[:300]
    return {**result, "eligible": True, "reason": source}


async def policy_view(app, packets, head):
    return {
        "max_cloud_recoveries": app.config.max_cloud_recoveries,
        "ordinary_replacement_limit": app.config.max_worker_recoveries,
        "offers": [await offer(app, packet, head) for packet in packets],
    }


async def prepare(app, proposal, snapshot):
    """Normalize local retry/defer/stop/no-op to a real, auditable cloud assignment.

    Validation still runs on the resulting plan before any publication. Only pending
    consumers can be cloned; started assignments and interface contracts never move.
    """
    if proposal.read_requests:
        return proposal, []
    tasks = list(proposal.tasks)
    decisions = {d.exception_ref: d for d in proposal.exception_dispositions}
    existing = [v for _, _, v in app.ports.records.scan("task/")]
    used_ids = {t["assignment"]["task_id"] for t in existing} | {t.task_id for t in tasks}
    cancelled = list(proposal.cancel_pending_task_ids)
    remap, adjustments = {}, []

    def unique(task_id, suffix):
        stem, i = task_id[:50] + "_" + suffix, 1
        candidate = stem
        while candidate in used_ids:
            candidate, i = f"{stem}_{i}", i + 1
        used_ids.add(candidate)
        return candidate

    for packet in snapshot.get("exceptions", []):
        choice = await offer(app, packet, snapshot["head"])
        if not choice["eligible"]:
            continue
        decision = decisions.get(packet["exception_ref"])
        replacement = next((t for t in tasks if decision and decision.action == "retry"
                            and t.task_id == decision.replacement_task_id), None)
        if replacement is None:
            replacement = Assignment.model_validate({
                **packet["assignment"],
                "task_id": unique(packet["task_id"], "cloud"),
                "role": "specialist",
                "resume_from": choice["resume_from"],
            })
            tasks.append(replacement)
        else:
            replacement = replacement.model_copy(update={"role": "specialist"})
            tasks = [replacement if t.task_id == replacement.task_id else t for t in tasks]
        source = choice["reason"] if replacement.resume_from else (
            "fresh current base (senior choice)" if choice["resume_from"] else choice["reason"]
        )
        condition = "Cloud specialist implements the pinned contract using failure evidence; " + source
        prior = decision.changed_condition if decision and decision.action == "retry" else ""
        if prior and not prior.endswith(condition):
            condition = prior[:3200] + "; " + condition
        elif prior:
            condition = prior
        remap[packet["task_id"]] = replacement.task_id
        decisions[packet["exception_ref"]] = ExceptionDisposition(
            exception_ref=packet["exception_ref"], action="retry",
            replacement_task_id=replacement.task_id,
            reason="Bounded cloud coding takeover of a confirmed-stopped local lineage",
            changed_condition=condition,
        )
        adjustments.append({"exception_ref": packet["exception_ref"],
                            "model_action": decision.action if decision else "omitted",
                            "replacement_task_id": replacement.task_id,
                            "effective_role": "specialist", "source": source})

    if not remap:
        return proposal, []
    # Retiring a failed provider must atomically replace every still-pending
    # downstream assignment, transitively, rather than leave an unrunnable queue.
    while True:
        affected = [t for t in existing if t["execution"] == "pending"
                    and t["assignment"]["task_id"] not in cancelled
                    and set(t["assignment"]["dependencies"]) & remap.keys()]
        if not affected:
            break
        for task in affected:
            if task.get("previous_process_id"):
                packet = next((e for e in snapshot.get("exceptions", [])
                               if e.get("pending_replacement_task_id") == task["assignment"]["task_id"]), None)
                if (not packet or app.ports.records.get("process/" + task["process_id"])
                        or task.get("started_at")):
                    raise ValueError("Pending recovery consumer needs explicit lineage-preserving replanning")
                validate_allowance(app, packet)
            original = Assignment.model_validate(task["assignment"])
            replacement_id = unique(original.task_id, "rewired")
            remap[original.task_id] = replacement_id
            cancelled.append(original.task_id)
            tasks.append(original.model_copy(update={"task_id": replacement_id}))
            if task.get("previous_process_id"):
                decisions[packet["exception_ref"]] = ExceptionDisposition(
                    exception_ref=packet["exception_ref"], action="retry", replacement_task_id=replacement_id,
                    reason="Retarget an unstarted recovery after its provider changed",
                    changed_condition=task.get("recovery_condition") or "Preserve original recovery lineage",
                )
    tasks = [t.model_copy(update={"dependencies": [remap.get(d, d) for d in t.dependencies]}) for t in tasks]
    brief = "Cloud recovery policy scheduled " + ", ".join(a["replacement_task_id"] for a in adjustments) + "."
    raw = proposal.model_dump(mode="json")
    raw.update(tasks=[t.model_dump(mode="json") for t in tasks],
               exception_dispositions=[d.model_dump(mode="json") for d in decisions.values()],
               cancel_pending_task_ids=cancelled, complete=False, completion_assessment=None,
               user_brief=(proposal.user_brief or "")[:8000 - len(brief) - 1] + "\n" + brief)
    return SeniorProposal.model_validate(raw), adjustments
