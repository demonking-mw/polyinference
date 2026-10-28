"""Bounded deterministic working facts; immutable trajectories remain authoritative."""

from ..primitives import canonical, digest

LIMIT = 8192


def clipped(value, size=600):
    return str(value).encode()[:size].decode(errors="ignore")


def project(app, state, code):
    attempt = (state.get("attempt_id") or app.get(state["task_ledger_ref"]).get("attempt_id")
               or "process-" + state["process_id"])
    key = "worker-state/" + attempt
    saved = app.ports.records.get(key)
    prior = saved[1] if saved else {}
    identity = {k: code[k] for k in ("effective_tree_digest", "environment_digest")}
    identity["generation"] = app.ports.workspaces.current(state["workspace_id"]).generation
    same = prior.get("source") == identity
    files = dict(prior.get("files", {})) if same else {}
    errors = list(prior.get("errors", []))
    entries = app.history(state.get("trajectory_ref"))
    cursor = prior.get("through")
    start = next((i + 1 for i, entry in enumerate(entries) if entry["id"] == cursor), 0)
    for entry in entries[start:]:
        action, observation = entry.get("reply", {}), entry.get("observation", {})
        if not isinstance(observation, dict):
            continue
        tool = action.get("tool")
        if action.get("kind") in {"action", "candidate", "assessment", "needs_review"}:
            errors = [e for e in errors if e.get("kind") != "protocol"]
        if tool == "shell.run" and observation.get("changed"):
            files.clear()
        path = observation.get("path", action.get("arguments", {}).get("path"))
        if path and observation.get("digest"):
            files.pop(path, None)
            files[path] = {"digest": observation["digest"], "event": entry["id"]}
        elif tool == "files.delete" and path and not observation.get("error"):
            files.pop(path, None)
        problem = observation.get("error") or entry.get("feedback", {}).get("error")
        if tool and not problem:
            errors = [e for e in errors if not (e.get("kind") == "tool" and e.get("tool") == tool
                                                and e.get("path") == path)]
        if tool == "checks.run":
            criterion = observation.get("criterion_ref")
            errors = [e for e in errors if e.get("criterion") != criterion]
            if observation.get("status") != "passed":
                problem = "Check " + str(criterion) + ": " + str(observation.get("status"))
        if problem:
            summary = clipped(problem)
            errors = [e for e in errors if e["summary"] != summary]
            errors.append({"summary": summary, "event": entry["id"], "tool": tool, "path": path,
                           "kind": "protocol" if "feedback" in entry else "check" if tool == "checks.run" else "tool",
                           "criterion": observation.get("criterion_ref")})
        files = dict(list(files.items())[-16:])
        errors = errors[-4:]
    passed = {e["criterion_ref"] for e in state.get("evidence", []) if e.get("status") == "passed"
              and e.get("checked_code", {}).get("effective_tree_digest") == identity["effective_tree_digest"]
              and e.get("checked_code", {}).get("environment_digest") == identity["environment_digest"]}
    errors = [e for e in errors if e.get("criterion") not in passed]
    body = {"source": identity, "phase": state["phase"],
            "through": entries[-1]["id"] if entries else None,
            "trajectory_ref": state.get("trajectory_ref"), "files": files, "errors": errors,
            "evidence": [{k: e.get(k) for k in ("criterion_ref", "status", "output", "checked_code")}
                         for e in state.get("evidence", [])[-4:]],
            "next_step": "Resolve current error, then run the focused check" if errors else
                         "Finish one assigned behavior and submit a candidate" if state["phase"] == "development"
                         else "Follow the current phase using exact-source check evidence",
            "evicted_files": prior.get("evicted_files", 0) if same else 0,
            "evicted_errors": prior.get("evicted_errors", 0) if same else 0}
    while len(canonical(body)) > LIMIT and (body["files"] or body["errors"] or body["evidence"]):
        if body["files"]:
            body["files"].pop(next(iter(body["files"])))
            body["evicted_files"] += 1
        elif body["evidence"]:
            body["evidence"].pop(0)
        else:
            body["errors"].pop(0)
            body["evicted_errors"] += 1
    if len(canonical(body)) > LIMIT:
        raise ValueError("Required bounded worker state cannot fit")
    if body != prior:
        app.ports.records.compare_and_publish({key: saved[0] if saved else 0}, {key: body})
    return body


def repair(app, request, error):
    """Host-created feedback within the existing physical response retry allowance."""
    from ..contracts import ContextPart

    payload = request.payload
    parts = [p for p in payload.context.parts if p.required and p.part_id != "repair-feedback"]
    feedback = {"error": clipped(error.get("message", error), 1200),
                "instruction": "Return one complete response matching the current phase/schema; use a small action."}
    ref = app.artifact(feedback, request.scope.process_id)
    part = ContextPart(part_id="repair-feedback", content=ref, part_kind="data", trust="application",
                       source_ref="agent/response-repair", required=True)
    index = next((i for i, p in enumerate(parts) if p.part_id == "current-request"), len(parts))
    parts.insert(index, part)
    context = payload.context.model_copy(update={"parts": parts,
        "view_id": digest(canonical([p.model_dump(mode="json") for p in parts])),
        "digest": digest(canonical([p.content.digest for p in parts]))})
    return payload.model_copy(update={"context": context})
