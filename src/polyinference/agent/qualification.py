"""Product-oriented accounting from canonical records; no execution or acceptance policy."""

from collections import Counter
from datetime import datetime, timedelta

from ..primitives import canonical


def task_metrics(records, physical):
    """Bounded task/lineage facts, including started work later superseded."""
    tasks = {k[5:]: v for k, v in records.items() if k.startswith("task/")}
    rows = []
    for task_id, task in tasks.items():
        pid = task.get("process_id")
        calls = [a for a in physical if a["request"].get("scope", {}).get("process_id") == pid]
        effects = [v for k, v in records.items() if k.startswith("effect/")
                   and v["request"].get("scope", {}).get("process_id") == pid]
        queries = {"read": [], "check": []}
        for effect in effects:
            payload = effect["request"]["payload"]
            tool = payload.get("capability_id")
            group = "read" if tool in {"files.read", "files.list", "files.search"} else "check" if tool == "checks.run" else None
            if group:
                queries[group].append(canonical([tool, payload.get("arguments", {}).get("digest"),
                                                 payload.get("expected_code")]))
        repeated = {name: {"calls": len(values), "identical_repeats": len(values) - len(set(values)),
                           "share": (len(values) - len(set(values))) / len(values) if values else None}
                    for name, values in queries.items()}
        report = records.get(task.get("report_ref") or "", {})
        resolution = records.get("resolution/" + (task.get("report_ref") or ""), {})
        receipt = next((v for k, v in records.items() if k.startswith("receipt/")
                        and v.get("report_ref") == task.get("report_ref") and "published_head" in v), {})
        account = records.get("process-account/" + (pid or ""), {})
        root = account.get("root", pid)
        process = records.get("process/" + (root or ""), {})
        limits = records.get(process.get("spec_ref", ""), {}).get("limits", {})
        deadline = account.get("deadline")
        if deadline is None and process.get("started_at") and limits.get("max_wall_time_ms"):
            deadline = (datetime.fromisoformat(process["started_at"].replace("Z", "+00:00"))
                        + timedelta(milliseconds=limits["max_wall_time_ms"])).isoformat()
        state = records.get("worker-state/" + (task.get("attempt_id") or ""))
        dependencies = task.get("assignment", {}).get("dependencies", [])
        waiting = [d for d in dependencies if records.get("resolution/" + (tasks.get(d, {}).get("report_ref") or ""), {})
                   .get("action") != "keep"]
        rows.append({"task_id": task_id, "process_id": pid, "root_task_id": task.get("root_task_id", task_id),
            "previous_process_id": task.get("previous_process_id"), "resource_account": root,
            "original_deadline": deadline, "original_limits": limits,
            "root_counters": {name: records.get("budget/" + name + "/" + (root or ""))
                              for name in ("model-calls", "steps", "process")},
            "requested_role": task.get("assignment", {}).get("role"),
            "binding": records.get("process-status/" + (pid or ""), {}).get("binding_ref"),
            "actual_backends": [dict(item) for item in sorted(
                {tuple(sorted((a.get("result") or {}).get("actual_backend", {}).items()))
                 for a in calls if (a.get("result") or {}).get("actual_backend")}, key=repr)],
            "started": bool(task.get("started_at") or task.get("execution") in {"in_progress", "completed", "interrupted"}),
            "execution": task.get("execution"), "kept": resolution.get("action") == "keep",
            "source_changed": bool(receipt and receipt.get("previous_head", {}).get("effective_tree_digest")
                                   != receipt.get("published_head", {}).get("effective_tree_digest")),
            "source_location": report.get("code_location"), "started_at": task.get("started_at"),
            "report_created_at": report.get("created_at"), "dependency_waits": waiting,
            "raw_generations": sum(a["request"]["payload"]["kind"] == "model_query" for a in calls),
            "native_jobs": sum(a["request"]["payload"]["kind"] == "agent_job" for a in calls),
            "failure_codes": dict(Counter((a.get("result", {}).get("error") or {}).get("code")
                                          for a in calls if (a.get("result") or {}).get("error"))),
            "repeated_tool_queries": repeated, "bounded_state_bytes": len(canonical(state)) if state else None,
            "exit_cause": task.get("exception") or task.get("stop_reason")})
    rows.sort(key=lambda row: row["task_id"])
    return {"total_tasks": len(rows), "started_tasks": sum(r["started"] for r in rows),
            "completed_tasks": sum(r["execution"] == "completed" for r in rows),
            "tasks": rows[-64:], "omitted_tasks": max(0, len(rows) - 64),
            "limits": "Identical read/check intents on the same source are repeats, not a correctness verdict. "
                      "Shell reads, semantic behavior counts, dependency wait duration and unrecorded facts are unavailable."}


def quality(records):
    attempt_rows = [(k, v) for k, v in records.items() if k.startswith("inference-attempt/")]
    roots = {k.removeprefix("inference-attempt/").rsplit("/", 1)[0] for k, _ in attempt_rows}
    # Effectful native jobs are deliberately ineligible for response replay and
    # therefore have no inference-attempt rows. Count the direct effect once.
    attempts = [v for _, v in attempt_rows] + [v for k, v in records.items() if k.startswith("effect/")
        and v.get("request", {}).get("payload", {}).get("kind") in {"model_query", "agent_job"}
        and v["request"]["operation_id"] not in roots]
    def submitted(attempt):
        result = attempt.get("result") or {}
        attempted = result.get("extensions", {}).get("polyinference/attempted-backend", {})
        effect = records.get("effect/" + attempt["request"]["operation_id"], {})
        return (attempted.get("submitted") is True or bool(result.get("actual_backend"))
                or effect.get("attempted_backend", {}).get("submitted") is True)

    physical = [a for a in attempts if submitted(a)]
    raw = [a for a in physical if a["request"]["payload"]["kind"] == "model_query"]
    native = [a for a in physical if a["request"]["payload"]["kind"] == "agent_job"]
    receipts = [(a.get("result") or {}).get("extensions", {}).get("runtime/context-receipt", {}) for a in raw]
    contributions = zero_delta = 0
    for key, receipt in records.items():
        if not key.startswith("receipt/") or "published_head" not in receipt:
            continue
        report = receipt.get("report_ref")
        resolution = records.get("resolution/" + (report or ""), {})
        if resolution.get("action") != "keep":
            continue
        if receipt["previous_head"]["effective_tree_digest"] != receipt["published_head"]["effective_tree_digest"]:
            contributions += 1
        else:
            zero_delta += 1
    run = records.get("app/run", {})
    def invalid(attempt):
        return ((attempt.get("result") or {}).get("error") or {}).get("code") == "ResponseValidationError"

    return {
        "status": run.get("status"), "exit_cause": run.get("blocker"),
        "physical_raw_generations": len(raw), "native_jobs": len(native),
        "prepared_or_unconfirmed_attempt_records": len(attempts) - len(physical),
        "response_validation_failures": sum(invalid(a) for a in attempts),
        "raw_response_validation_failures": sum(invalid(a) for a in raw),
        "native_response_validation_failures": sum(invalid(a) for a in native),
        "raw_context_omissions": sum(bool(r.get("omitted_refs")) for r in receipts),
        "largest_original_raw_bytes": max((r.get("original_bytes", 0) for r in receipts), default=0),
        "kept_nonempty_publications": contributions, "kept_zero_delta_publications": zero_delta,
        "source_note": "Physical attempts only; native jobs may contain multiple turns. Kept source is not product completion.",
        "cloud_adjustments": sum(len(v.get("policy_adjustments", []))
                                 for k, v in records.items() if k.startswith("proposal/")),
        "uncertain_effects": sum(v.get("state") == "uncertain" for k, v in records.items() if k.startswith("effect/")),
        "task_metrics": task_metrics(records, physical),
    }


def qualification_gate(trials):
    """Initial engineering gate, not a statistical reliability estimate."""
    standard = [t for t in trials if not t.get("interrupted")]
    resumed = [t for t in trials if t.get("interrupted")]
    pins = {t.get("profile_digest") for t in trials}
    def good(t):
        return (t.get("status") == "completed" and t.get("independent_check") == "passed"
                and not t.get("manual_repair") and not t.get("uncertain_effects")
                and not t.get("framework_changed") and not t.get("check_changed"))
    passed = (len(standard) >= 3 and all(good(t) for t in standard[-3:])
              and any(good(t) and t.get("resume_verified") for t in resumed)
              and len(pins) == 1 and None not in pins)
    return {"passed": passed, "consecutive_required": 3,
            "resume_required": True, "note": "Requires actual independently checked trials with identical profile pins."}
