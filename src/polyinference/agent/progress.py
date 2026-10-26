"""Evidence novelty and stagnation policy; execution facts come from the OS port."""

from ..domain import canonical, digest


def merge_ranges(ranges, start, end):
    merged = []
    for left, right in sorted([*ranges, [start, end]]):
        if merged and left <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], right)
        else:
            merged.append([left, right])
    return merged


def evidence_features(evidence):
    code = evidence.get("checked_code", {})
    if not code or evidence.get("status") not in {"passed", "failed", "inconclusive", "unavailable"}:
        return []
    return [
        [
            "check",
            evidence.get("criterion_ref"),
            code.get("effective_tree_digest"),
            code.get("environment_digest"),
            evidence["status"],
        ]
    ]


def observe_tool(tool, arguments, observation, reads):
    if not isinstance(observation, dict) or observation.get("error"):
        return []
    if tool == "checks.run":
        return evidence_features(observation)
    if tool == "files.list" and "paths" in observation:
        return [["listing", sorted(observation["paths"])]]
    if tool != "files.read" or not observation.get("digest"):
        return []
    key = digest(canonical([observation.get("path", arguments.get("path")), observation["digest"]]))
    start = observation.get("offset", 0)
    size = observation.get("returned_bytes", len(observation.get("content", "").encode()))
    before = reads.get(key, [])
    after = merge_ranges(before, start, start + size)
    added = sum(b - a for a, b in after) - sum(b - a for a, b in before)
    reads[key] = after
    # Overlapping reads and renamed requests do not gain credit for already seen bytes.
    return [["read", key, after]] if added else []


async def inspect_progress(app, state):
    policy = app.config.progress_monitor
    if state.get("model_recovery") or policy.mode == "off" or app.get(state["task_ledger_ref"]).get("category") == "setup":
        return {"progress_route": "model"}
    pid = state["process_id"]
    key = "worker-progress/" + pid
    current = app.ports.records.get(key)
    prior = current[1] if current else {}
    token = f"{state['phase']}:{state['logical_step']}"
    if prior.get("token") == token:
        return prior["result"]
    try:
        execution = await app.ports.operations.progress(pid)
    except Exception as exc:
        # Optional observation failure cannot replace the underlying execution result.
        app.update("progress-observer-error/" + pid, {"error": type(exc).__name__, "token": token})
        return {"progress_route": "model"}
    if execution["settlement"]["pending_operations"] or execution["dispatch_blocked_by_uncertainty"]:
        return {"progress_route": "model"}
    code = await app.ports.workspaces.revision(state["workspace_id"])
    features = [["tree", code.effective_tree_digest, code.environment_digest], ["phase", state["phase"]]]
    reads = prior.get("read_ranges", {})
    entries = set(prior.get("history_entries", []))
    for entry in app.history(state.get("trajectory_ref")):
        entry_key = entry["id"]
        if entry_key in entries:
            continue
        entries.add(entry_key)
        reply = entry.get("reply", {})
        features += observe_tool(
            reply.get("tool"), reply.get("arguments", {}), entry.get("observation"), reads
        )
    operations = set(prior.get("operation_ids", []))
    for effect in execution["recent_effects"]:
        if effect["operation_id"] in operations:
            continue
        operations.add(effect["operation_id"])
        if effect["state"] == "succeeded" and effect.get("capability") and effect["output_refs"]:
            features += observe_tool(
                effect["capability"],
                app.read(effect["arguments_ref"]),
                app.read(effect["output_refs"][0]),
                reads,
            )
    for evidence in state.get("evidence", []):
        features += evidence_features(evidence)
    seen = set(prior.get("seen_features", []))
    observed = {digest(canonical(feature)) for feature in features}
    novel = bool(observed - seen)
    seen |= observed
    idle = 0 if novel or not prior else prior["idle_decisions"] + 1
    warned = bool(prior.get("warned")) and not novel
    escalated = bool(prior.get("escalated")) and not novel
    status = "progress" if novel else "idle"
    history = state.get("trajectory_ref")
    attention = None
    if idle >= policy.warn_after:
        attention = {
            "kind": "task_attention",
            "verdict": "uncertain",
            "reason": f"No new source, read coverage or check result in {idle} settled decisions",
            "idle_decisions": idle,
            "request": "Choose a concrete changed approach, finish a ready candidate, or request needs_review with the blocker. Repeated reads/checks and rewritten narration do not establish progress.",
            "execution_state": "between_settled_operations",
            "effects": "known",
        }
        status = "warning"
    stop = idle >= policy.escalate_after and policy.mode == "enforce"
    if idle >= policy.escalate_after:
        status = "needs_review" if stop else "would_escalate"
    if (attention and not warned) or (idle >= policy.escalate_after and not escalated):
        event_ref = f"progress-event/{pid}/{token}"
        event = {
            "status": status,
            "attention": attention,
            "execution_ref": app.artifact(execution).model_dump(mode="json"),
            "code": code.model_dump(mode="json"),
        }
        app.ports.records.compare_and_publish({}, {}, {event_ref: event})
        history = app.append_feedback(
            history, "progress-" + token, {**attention, "event_ref": event_ref}, source_ref=event_ref
        )
        warned = True
    escalated = escalated or idle >= policy.escalate_after
    result = {
        "progress_route": "park" if stop else "model",
        "trajectory_ref": history,
        "progress_attention": attention,
    }
    if stop:
        result["interrupted"] = attention["reason"] + "; bounded progress warning did not resolve the stall"
    app.ports.records.compare_and_publish(
        {key: current[0] if current else 0},
        {
            key: {
                "token": token,
                "status": status,
                "idle_decisions": idle,
                "warned": warned,
                "escalated": escalated,
                "seen_features": sorted(seen),
                "read_ranges": reads,
                "history_entries": sorted(entries),
                "operation_ids": sorted(operations),
                "execution": execution,
                "result": result,
            }
        },
    )
    return result
