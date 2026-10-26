from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from ..domain import SeniorProposal
from .architecture import catalog, validate_plan
from .exceptions import validate as validate_exceptions
from .exceptions import validate_sources
from .review import fit_snapshot, retrieve, validate_completion
from .worker import AppContext


class SeniorState(TypedDict, total=False):
    process_id: str
    workspace_id: str
    mode: str
    input: dict
    logical_step: int
    trajectory_ref: dict | None
    reply: dict
    proposal: dict
    error: str | None
    review_reads_used: int
    corrections_used: int
    route: str


async def submit(state, runtime: Runtime[AppContext]):
    return {"reply": await runtime.context.services.model(state, senior=True)}


async def validate(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    try:
        proposal = SeniorProposal.model_validate(state["reply"])
        reports = {report["record_id"]: report for report in state["input"].get("reports", [])}
        for disposition in proposal.dispositions:
            report = reports.get(disposition.report_ref)
            if not report:
                raise ValueError("Disposition is not in the pinned review input")
            if report.get("code_location") == "private" and disposition.action == "keep":
                raise ValueError("Private failed commit cannot be kept; reject it or assign a repair")
        for assignment in proposal.tasks:
            if app.config.write_scope == "explicit" and not set(assignment.write_paths) <= set(
                app.config.allowed_write_paths
            ):
                raise ValueError("Proposed write scope exceeds user grant")
            if not assignment.checks or not set(assignment.checks) <= {c.name for c in app.task_check_definitions}:
                raise ValueError("Unknown configured check")
            if assignment.resume_from and app.repository and not assignment.resume_from.startswith("worker-exception/"):
                source = next((s for s in state["input"].get("retained_sources", [])
                               if s["resume_from"] == assignment.resume_from), None)
                if not source or not source["available"]:
                    reason = source["reason"] if source else "Use a supplied retained_sources reference"
                    raise ValueError("Cannot resume retained source: " + reason)
                missing = set(source["required_write_paths"]) - set(assignment.write_paths)
                if missing:
                    raise ValueError("Replacement grant must include retained paths: " + ", ".join(sorted(missing)))
        checks = {c.name for c in app.task_check_definitions}
        tasks = {t.task_id: t for t in proposal.tasks}
        known = set(state["input"].get("all_task_ids", [])) | set(tasks)
        for assignment in proposal.tasks:
            if not set(assignment.dependencies) <= known:
                raise ValueError("Unknown task dependency")
        seen = set()
        for preparation in proposal.check_preparations:
            if preparation.check_name not in checks or preparation.task_id not in tasks:
                raise ValueError("Check preparation must name a configured check and its new owner task")
            if preparation.check_name in seen:
                raise ValueError("Each check preparation needs one owner")
            seen.add(preparation.check_name)
            for assignment in proposal.tasks:
                if (assignment.task_id != preparation.task_id and preparation.check_name in assignment.checks
                        and preparation.task_id not in assignment.dependencies):
                    raise ValueError(f"Check {preparation.check_name} needs dependency {preparation.task_id} "
                                     f"before task {assignment.task_id} can start")
        if proposal.read_requests:
            if state.get("review_reads_used", 0) + len(proposal.read_requests) > app.config.max_review_reads:
                raise ValueError(
                    "Review retrieval allowance exhausted; leave incomplete or plan follow-up work"
                )
            return {"proposal": proposal.model_dump(mode="json"), "error": None, "route": "read_context"}
        replacements = validate_exceptions(app, proposal, state["input"])
        validate_plan(proposal, [v for _, _, v in app.ports.records.scan("task/")], catalog(app))
        await validate_sources(app, proposal, replacements, state["input"]["head"])
        validate_completion(proposal, state["input"])
    except ValueError as exc:
        history = app.append_feedback(
            state.get("trajectory_ref"),
            f"invalid-{state['logical_step']}",
            {"error": str(exc)[:2000]},
            source_ref=f"request/{state['process_id']}/model-{state['logical_step']}",
            received=state["reply"],
        )
        return {
            "trajectory_ref": history,
            "logical_step": state["logical_step"] + 1,
            "error": str(exc),
            "corrections_used": state.get("corrections_used", 0) + 1,
            "route": "error",
        }
    if proposal.user_brief:
        result, output = await app.capability(
            state, "user-brief", "user.notify", {"text": proposal.user_brief}, "shared_write"
        )
        if result.state != "succeeded":
            raise RuntimeError(str(output))
    return {"proposal": proposal.model_dump(mode="json"), "error": None, "route": "done"}


async def read_context(state, runtime: Runtime[AppContext]):
    app = runtime.context.services
    requests = SeniorProposal.model_validate(state["proposal"]).read_requests
    views = await retrieve(app, state["input"], requests)
    history = state.get("trajectory_ref")
    try:
        snapshot = fit_snapshot(
            app, {**state["input"], "review_reads": [*state["input"].get("review_reads", []), *views]}
        )
    except ValueError as exc:
        snapshot = state["input"]
        history = app.append_feedback(
            history,
            f"read-bound-{state['logical_step']}",
            {"review_retrieval_error": str(exc)},
            source_ref="application/review-context",
        )
    return {
        "input": snapshot,
        "trajectory_ref": history,
        "logical_step": state["logical_step"] + 1,
        "review_reads_used": state.get("review_reads_used", 0) + len(requests),
        "route": "submit",
    }


def build_senior(checkpointer):
    graph = StateGraph(SeniorState, context_schema=AppContext)
    graph.add_node("submit", submit)
    graph.add_node("validate", validate)
    graph.add_node("read_context", read_context)
    graph.add_edge(START, "submit")
    graph.add_edge("submit", "validate")

    def bounded_route(state, config):
        if state["route"] == "read_context":
            return "read_context"
        if state.get("error") and state["corrections_used"] <= config.get("configurable", {}).get(
            "corrections", 1
        ):
            return "submit"
        return END

    graph.add_conditional_edges("validate", bounded_route)
    graph.add_edge("read_context", "submit")
    return graph.compile(checkpointer=checkpointer)
