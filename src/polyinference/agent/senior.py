from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from ..domain import SeniorProposal
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
    except ValueError as exc:
        history = app.append_history(
            state.get("trajectory_ref"),
            f"invalid-{state['logical_step']}",
            {"kind": "action", "tool": "proposal.validation"},
            {"error": str(exc)[:2000]},
        )
        return {"trajectory_ref": history, "logical_step": state["logical_step"] + 1, "error": str(exc)}
    if proposal.user_brief:
        result, output = await app.capability(
            state, "user-brief", "user.notify", {"text": proposal.user_brief}, "shared_write"
        )
        if result.state != "succeeded":
            raise RuntimeError(str(output))
    return {"proposal": proposal.model_dump(mode="json"), "error": None}


def build_senior(checkpointer):
    graph = StateGraph(SeniorState, context_schema=AppContext)
    graph.add_node("submit", submit)
    graph.add_node("validate", validate)
    graph.add_edge(START, "submit")
    graph.add_edge("submit", "validate")

    def route(state):
        if state.get("error") and state["logical_step"] <= 1:
            return "submit"
        return END

    def bounded_route(state, config):
        if state.get("error") and state["logical_step"] <= config.get("configurable", {}).get(
            "corrections", 1
        ):
            return "submit"
        return END

    graph.add_conditional_edges("validate", bounded_route)
    return graph.compile(checkpointer=checkpointer)
