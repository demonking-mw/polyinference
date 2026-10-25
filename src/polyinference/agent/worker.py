from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from pydantic import TypeAdapter

from ..contracts import (
    CheckEvidence,
    CodeRevision,
    ExpectedVersion,
    MemoryItem,
    Publication,
    PublicationReceipt,
    TaskAttempt,
    TaskReport,
    UsageMeasure,
)
from ..domain import Action, Assessment, Candidate, NeedsReview, WorkerReply, digest


class WorkerState(TypedDict, total=False):
    process_id: str
    task_spec_ref: str
    task_ledger_ref: str
    attempt_id: str
    workspace_id: str
    workspace_generation: int
    workspace_view: str
    phase: str
    logical_step: int
    calls: int
    repairs: int
    trajectory_ref: dict | None
    verification_permit_ref: str | None
    captured_head: dict
    preserved_private_delta_ref: str
    reconciliation_turn_refs: list[str]
    assessment_turn_refs: list[str]
    evidence: list[dict]
    reply: dict
    route: str
    report_ref: str | None
    interrupted: str | None


@dataclass(frozen=True)
class AppContext:
    services: object


async def load(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    task = app.get(state["task_ledger_ref"])
    manifest = await app.ports.workspaces.create(
        state["workspace_id"],
        state["process_id"],
        state["task_spec_ref"],
        CodeRevision.model_validate(task["base"]),
        task["assignment"]["write_paths"],
        task["assignment"]["read_paths"],
    )
    return {"workspace_generation": manifest.generation, "workspace_view": manifest.view}


async def model(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    limits = app.config.limits
    calls = state.get("calls", 0)
    used = getattr(app.ports.operations, "inference_calls_used", lambda pid: 0)(state["process_id"])
    calls = max(calls, used)
    reserve = limits.final_phase_reserve
    reserved = reserve.reconciliation_model_calls + reserve.assessment_model_calls if reserve else 2
    if state["phase"] == "development" and calls >= limits.max_model_calls - reserved:
        return {"reply": {"kind": "candidate", "summary": "Development allowance ended"}}
    if calls >= limits.max_model_calls or state["logical_step"] >= limits.max_steps:
        return {"reply": {"kind": "needs_review", "reason": "Mandatory phase allowance exhausted"}}
    reply = await app.model(state)
    return {
        "reply": reply,
        "calls": calls + 1,
        "task_spec_ref": app.ports.workspaces.current(state["workspace_id"]).task_spec_ref,
    }


async def consume(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    step = state["logical_step"]
    try:
        reply = TypeAdapter(WorkerReply).validate_python(state["reply"])
        if isinstance(reply, Assessment) and state["phase"] != "assessment":
            raise ValueError("Verdict outside assessment phase")
        if isinstance(reply, Candidate) and state["phase"] == "assessment":
            raise ValueError("Assessment requires a verdict")
    except ValueError as exc:
        history = app.append_feedback(
            state.get("trajectory_ref"),
            f"invalid-{step}",
            {"error": str(exc)[:1500]},
            source_ref=f"request/{state['process_id']}/model-{step}",
            received=state["reply"],
        )
        return {"trajectory_ref": history, "logical_step": step + 1, "route": "model"}
    if isinstance(reply, Action):
        return {"route": "tool"}
    history = app.append_history(state.get("trajectory_ref"), f"turn-{step}", reply.model_dump(mode="json"))
    update = {"trajectory_ref": history, "logical_step": step + 1}
    if state["phase"] == "reconciliation":
        update["reconciliation_turn_refs"] = [*state.get("reconciliation_turn_refs", []), f"turn-{step}"]
    if isinstance(reply, NeedsReview):
        return {**update, "route": "park", "interrupted": reply.reason}
    if isinstance(reply, Candidate):
        return {**update, "route": "acquire" if state["phase"] == "development" else "checks"}
    if isinstance(reply, Assessment):
        update["assessment_turn_refs"] = [*state.get("assessment_turn_refs", []), f"turn-{step}"]
        if reply.repair and state.get("repairs", 0) < app.config.limits.max_repairs:
            return {
                **update,
                "route": "model",
                "phase": "reconciliation",
                "repairs": state.get("repairs", 0) + 1,
                "evidence": [],
            }
        return {**update, "route": "publish"}
    raise AssertionError("Unhandled reply")


async def tool(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    reply = Action.model_validate(state["reply"])
    manifest = app.ports.workspaces.current(state["workspace_id"])
    arguments = {**reply.arguments, "generation": manifest.generation}
    if state["phase"] == "assessment" and reply.tool in {"files.write", "files.delete", "shell.run"}:
        # An edit is a repair, not assessment evidence.
        if state.get("repairs", 0) >= app.config.limits.max_repairs:
            observation = {"error": "Repair allowance exhausted; assess the current tree"}
            result = None
        else:
            result, observation = await app.capability(
                state, f"tool-{state['logical_step']}", reply.tool, arguments, "private_write"
            )
    else:
        result, observation = await app.capability(
            state,
            f"tool-{state['logical_step']}",
            reply.tool,
            arguments,
            "private_write"
            if reply.tool
            in {"files.write", "files.delete", "checks.run", "shell.run", "repository.select_branch"}
            else "read",
        )
    app.sync_setup(state)
    history = app.append_history(
        state.get("trajectory_ref"),
        f"turn-{state['logical_step']}",
        reply.model_dump(mode="json"),
        observation,
    )
    update = {
        "trajectory_ref": history,
        "logical_step": state["logical_step"] + 1,
        "workspace_generation": app.ports.workspaces.current(state["workspace_id"]).generation,
        "task_spec_ref": app.ports.workspaces.current(state["workspace_id"]).task_spec_ref,
    }
    if (
        state["phase"] == "assessment"
        and reply.tool in {"files.write", "files.delete", "shell.run"}
        and result
        and result.state == "succeeded"
        and (reply.tool != "shell.run" or observation.get("changed"))
    ):
        update.update(phase="reconciliation", evidence=[], repairs=state.get("repairs", 0) + 1)
    return update


async def acquire(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    await app.ports.workspaces.preserve_delta(state["workspace_id"])
    permit = await app.ports.exclusive.acquire("verification/project", state["process_id"])
    return {"verification_permit_ref": permit}


async def integrate(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    head = CodeRevision.model_validate(app.get("head/provisional")["code"])
    manifest = await app.ports.workspaces.integrate(
        state["workspace_id"], head, state["verification_permit_ref"]
    )
    return {
        "captured_head": manifest.captured_head.model_dump(mode="json"),
        "preserved_private_delta_ref": manifest.preserved_delta_ref,
        "workspace_generation": manifest.generation,
        "workspace_view": "integration",
        "phase": "reconciliation",
        "evidence": [],
        "reconciliation_turn_refs": [],
        "assessment_turn_refs": [],
    }


async def checks(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    names = app.get(state["task_ledger_ref"])["assignment"]["checks"]
    evidence = await app.checks(state, names)
    return {"evidence": evidence, "phase": "assessment", "logical_step": state["logical_step"] + 1}


async def publish(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    pid = state["process_id"]
    report_ref = "report/" + state["attempt_id"]
    receipt_ref = "receipt/" + state["attempt_id"]
    # The receipt, rather than a rechecked transient view, is the replay boundary.
    if app.ports.records.get(receipt_ref):
        return {"report_ref": report_ref}
    staged = app.ports.records.get("staged/" + receipt_ref)
    if not staged:
        verdict = "uncertain" if state["reply"].get("repair") else state["reply"]["verdict"]
        summary = state["reply"]["summary"]
        current = await app.ports.workspaces.revision(state["workspace_id"])
        evidence = [CheckEvidence.model_validate(e) for e in state["evidence"]]
        required = set(app.get(state["task_ledger_ref"])["assignment"]["checks"])
        current_evidence = {
            e.criterion_ref
            for e in evidence
            if e.checked_code.effective_tree_digest == current.effective_tree_digest
        }
        if any(e.status == "failed" for e in evidence):
            verdict = "fail"
        elif required != current_evidence or any(e.status != "passed" for e in evidence):
            verdict = "uncertain"
        if not state.get("reconciliation_turn_refs") or not state.get("assessment_turn_refs"):
            raise RuntimeError("Missing mandatory phase turns")
        result, code_data = await app.capability(state, "commit", "workspace.commit", {}, "shared_write")
        if result.state != "succeeded":
            raise RuntimeError(str(code_data))
        final = CodeRevision.model_validate(code_data)
        # Trusted commit preparation may not change the assessed effective content.
        if final.effective_tree_digest != current.effective_tree_digest:
            raise RuntimeError("Commit tree differs from assessed tree")
        head = CodeRevision.model_validate(state["captured_head"])
        manifest = app.ports.workspaces.current(state["workspace_id"])
        hazard_refs = ["hazard/" + state["attempt_id"]] if verdict != "successful" else []
        report = TaskReport(
            **app.base(report_ref),
            task_spec_ref=state["task_spec_ref"],
            attempt_id=state["attempt_id"],
            process_id=pid,
            plan_ref=app.get(state["task_ledger_ref"])["plan_ref"],
            verdict=verdict,
            stop_reason=None,
            reconciliation_turn_refs=state["reconciliation_turn_refs"],
            assessment_turn_refs=state["assessment_turn_refs"],
            assessment_summary=app.artifact(summary, pid),
            original_base=manifest.original_base,
            captured_head=head,
            final_code=final,
            candidate_commit_id=final.commit_id,
            candidate_parent_commit_id=head.commit_id,
            preserved_private_delta_ref=state["preserved_private_delta_ref"],
            verification_permit_ref=state["verification_permit_ref"],
            publication_receipt_ref=receipt_ref,
            evidence=evidence,
            hazard_refs=hazard_refs,
            usage=[
                UsageMeasure.model_validate(measure)
                for _, _, operation in app.ports.records.scan("effect/")
                if operation["request"]["scope"]["process_id"] == pid and operation.get("result")
                for measure in operation["result"]["usage"]
            ],
        )
        head_version = app.ports.records.get("head/provisional")[0]
        receipt = PublicationReceipt(
            **app.base(receipt_ref),
            publication_operation_id=digest(f"{app.run_id}:{pid}:publication".encode()),
            report_ref=report_ref,
            previous_head=head,
            published_head=final,
            candidate_parent_commit_id=head.commit_id,
            verification_permit_ref=state["verification_permit_ref"],
            publication_record_revision=head_version + 1,
            event_intent_refs=[],
        )
        task_version, task = app.ports.records.get(state["task_ledger_ref"])
        attempt_key = "attempt/" + state["attempt_id"]
        attempt_version, attempt_body = app.ports.records.get(attempt_key)
        attempt = TaskAttempt.model_validate(attempt_body).model_copy(
            update={
                "revision": attempt_body["revision"] + 1,
                "execution": "completed",
                "report_ref": report_ref,
            }
        )
        expected = {
            "head/provisional": head_version,
            state["task_ledger_ref"]: task_version,
            attempt_key: attempt_version,
        }
        if app.get("head/provisional")["code"] != head.model_dump(mode="json"):
            raise RuntimeError("Captured head changed under verification")
        immutable = {report_ref: report.model_dump(mode="json"), receipt_ref: receipt.model_dump(mode="json")}
        note_ref = "memory-note/" + state["attempt_id"]
        memory = MemoryItem(
            **app.base(note_ref),
            memory_id=note_ref,
            semantic_kind="episode",
            content=report.assessment_summary,
            author_ref=pid,
            trust="model",
            provenance_refs=[report_ref],
            applicable_code=final,
            valid_until=None,
            supersedes_ref=None,
            tombstone=False,
            access_policy_ref="grant/run",
            retention_policy_ref="retain-run",
            tier_preference="working",
            pinned_by_refs=[report_ref],
            hazard_code_location="provisional",
        )
        immutable[note_ref] = memory.model_dump(mode="json")
        if hazard_refs:
            immutable[hazard_refs[0]] = {
                "report_ref": report_ref,
                "verdict": verdict,
                "commit": final.commit_id,
                "summary": summary,
                "location": "provisional",
            }
        batch = {
            "permit_ref": state["verification_permit_ref"],
            "receipt_ref": receipt_ref,
            "expected": expected,
            "updates": {
                "head/provisional": {"code": final.model_dump(mode="json")},
                attempt_key: attempt.model_dump(mode="json"),
                state["task_ledger_ref"]: {**task, "execution": "completed", "report_ref": report_ref},
            },
            "immutable": immutable,
        }
        app.ports.records.compare_and_publish({}, {}, {"staged/" + receipt_ref: batch})
    batch = app.get("staged/" + receipt_ref)
    report = TaskReport.model_validate(batch["immutable"][report_ref])
    payload = Publication(
        expected_versions=[ExpectedVersion(record_ref=k, revision=v) for k, v in batch["expected"].items()],
        expected_head=report.captured_head,
        candidate_commit_id=report.candidate_commit_id,
        candidate_parent_commit_id=report.candidate_parent_commit_id,
        final_code=report.final_code,
        report_ref=report_ref,
        evidence_refs=[e.evidence_id for e in report.evidence],
        permit_refs=[state["verification_permit_ref"]],
        verification_permit_ref=state["verification_permit_ref"],
        receipt_ref=receipt_ref,
        event_intent_refs=[],
    )
    result, output = await app.effect(pid, "publication", payload, protected=True)
    if result.state != "succeeded" or not app.ports.records.get(receipt_ref):
        raise RuntimeError("Publication lacks durable receipt: " + str(output))
    return {"report_ref": report_ref}


async def release(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    permit = state.get("verification_permit_ref")
    if permit and app.ports.exclusive.owns(permit, "verification/project", state["process_id"]):
        await app.ports.exclusive.release(permit, state["process_id"])
    process = app.get("process/" + state["process_id"])
    app.update(
        "process/" + state["process_id"], {**process, "state": "completed", "report_ref": state["report_ref"]}
    )
    app.process_status(
        state["process_id"],
        state="completed",
        phase="published",
        terminal_result_ref=state["report_ref"],
        cleanup_state="complete",
        pending_operations=[],
        permit_refs=[],
        wait=None,
    )
    return {"verification_permit_ref": None}


async def park(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    if app.ports.operations.uncertain():
        raise RuntimeError("Unknown effects retain ownership")
    if state.get("verification_permit_ref"):
        await app.ports.workspaces.abort(state["workspace_id"])
        await app.ports.exclusive.release(state["verification_permit_ref"], state["process_id"])
    task = app.get(state["task_ledger_ref"])
    app.update(
        state["task_ledger_ref"],
        {**task, "execution": "interrupted", "exception": state.get("interrupted", "needs_review")},
    )
    process = app.get("process/" + state["process_id"])
    app.update("process/" + state["process_id"], {**process, "state": "paused"})
    attempt_key = "attempt/" + state["attempt_id"]
    attempt_version, attempt_body = app.ports.records.get(attempt_key)
    attempt = TaskAttempt.model_validate(attempt_body).model_copy(
        update={
            "revision": attempt_body["revision"] + 1,
            "execution": "interrupted",
            "stop_reason": state.get("interrupted", "needs_review"),
        }
    )
    app.ports.records.compare_and_publish(
        {attempt_key: attempt_version}, {attempt_key: attempt.model_dump(mode="json")}
    )
    app.process_status(
        state["process_id"],
        state="paused",
        cleanup_state="complete",
        permit_refs=[],
        pending_operations=[],
        wait=None,
    )
    return {"verification_permit_ref": None}


def build_worker(checkpointer):
    graph = StateGraph(WorkerState, context_schema=AppContext)
    for name, function in [
        ("load", load),
        ("model", model),
        ("consume", consume),
        ("tool", tool),
        ("acquire", acquire),
        ("integrate", integrate),
        ("checks", checks),
        ("publish", publish),
        ("release", release),
        ("park", park),
    ]:
        graph.add_node(name, function)
    graph.add_edge(START, "load")
    graph.add_edge("load", "model")
    graph.add_edge("model", "consume")
    graph.add_conditional_edges(
        "consume",
        lambda s: s["route"],
        {key: key for key in ("model", "tool", "acquire", "checks", "publish", "park")},
    )
    for first, second in [
        ("tool", "model"),
        ("acquire", "integrate"),
        ("integrate", "model"),
        ("checks", "model"),
        ("publish", "release"),
    ]:
        graph.add_edge(first, second)
    graph.add_edge("release", END)
    graph.add_edge("park", END)
    return graph.compile(checkpointer=checkpointer)
