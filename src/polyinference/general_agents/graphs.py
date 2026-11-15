"""Four small, OS-independent LangGraph programs.

Only the context protocol below crosses the graph boundary. A normal LangGraph
caller may supply any implementation; os_v1 supplies a V1 kernel implementation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime


class AgentIO(Protocol):
    async def model(self, role: str, phase: str, prompt: str, step: str) -> str: ...
    async def lookup(self, query: str, step: str) -> str: ...


@dataclass(frozen=True)
class GraphContext:
    io: AgentIO


class AgentState(TypedDict, total=False):
    task: str
    answer: str
    documents: dict[str, str]
    plan: list[str]
    index: int
    findings: list[str]
    observation: str
    turns: int
    draft: str
    feedback: str
    approved: bool
    revisions: int


def _object(raw: str) -> dict:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object from the model")
    return value


def _items(raw: str, key: str, maximum: int = 3) -> list[str]:
    value = _object(raw).get(key)
    if not isinstance(value, list) or not 1 <= len(value) <= maximum or any(
        not isinstance(item, str) or not item.strip() or len(item) > 500 for item in value
    ):
        raise ValueError(f"Expected 1 to {maximum} nonempty {key} strings")
    return [item.strip() for item in value]


def _text(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("Model returned an empty answer")
    return value


def build_simple(checkpointer=None):
    """Bounded ReAct: decide, read one granted source, observe, repeat."""
    async def decide(state: AgentState, runtime: Runtime[GraphContext]):
        turn = state.get("turns", 0)
        prompt = ("Answer the user's task. If a supplied document would help, return exactly JSON "
                  '{"lookup":"short query"}. Otherwise return exactly JSON {"final":"answer"}. '
                  "Use at most three lookups. Do not invent a source.\nTask: " + state["task"] +
                  "\nPrevious observation: " + state.get("observation", "none"))
        reply = _object(await runtime.context.io.model("general", "decide", prompt, f"decide-{turn}"))
        if isinstance(reply.get("final"), str) and reply["final"].strip():
            return {"answer": reply["final"].strip(), "turns": turn + 1}
        if turn >= 3 or not isinstance(reply.get("lookup"), str) or not reply["lookup"].strip():
            raise ValueError("Simple agent exceeded lookup limit or returned an invalid decision")
        return {"observation": await runtime.context.io.lookup(reply["lookup"], f"lookup-{turn}"),
                "turns": turn + 1}

    graph = StateGraph(AgentState, context_schema=GraphContext)
    graph.add_node("decide", decide)
    graph.add_edge(START, "decide")
    async def route(state):
        return END if state.get("answer") else "decide"

    graph.add_conditional_edges("decide", route)
    return graph.compile(checkpointer=checkpointer)


def build_supervisor(checkpointer=None):
    """Cloud orchestrator, serial local workers, cloud synthesis."""
    async def plan(state: AgentState, runtime: Runtime[GraphContext]):
        raw = await runtime.context.io.model("cloud", "plan", "Break this task into 1-3 independent questions. "
            'Return only JSON {"tasks":["..."]}. Task: ' + state["task"], "plan")
        return {"plan": _items(raw, "tasks"), "index": 0, "findings": []}

    async def work(state: AgentState, runtime: Runtime[GraphContext]):
        index = state["index"]
        prompt = f"Answer this bounded subtask accurately. Mark uncertainty.\nMain task: {state['task']}\nSubtask: {state['plan'][index]}"
        finding = _text(await runtime.context.io.model("local", "work", prompt, f"work-{index}"))
        return {"findings": [*state["findings"], finding], "index": index + 1}

    async def synthesize(state: AgentState, runtime: Runtime[GraphContext]):
        prompt = "Synthesize the local findings into a direct answer. Resolve conflicts and keep uncertainty visible.\n" + json.dumps(
            {"task": state["task"], "subtasks": state["plan"], "findings": state["findings"]})
        return {"answer": _text(await runtime.context.io.model("cloud", "synthesize", prompt, "synthesize"))}

    graph = StateGraph(AgentState, context_schema=GraphContext)
    for name, node in (("plan", plan), ("work", work), ("synthesize", synthesize)):
        graph.add_node(name, node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "work")
    async def route(state):
        return "work" if state["index"] < len(state["plan"]) else "synthesize"

    graph.add_conditional_edges("work", route)
    graph.add_edge("synthesize", END)
    return graph.compile(checkpointer=checkpointer)


def build_research(checkpointer=None):
    """Lead researcher plans; local workers inspect supplied evidence; lead cites."""
    async def plan(state: AgentState, runtime: Runtime[GraphContext]):
        raw = await runtime.context.io.model("cloud", "research_plan", "Plan 1-3 distinct evidence questions. "
            'Return only JSON {"questions":["..."]}. Research task: ' + state["task"], "plan")
        return {"plan": _items(raw, "questions"), "index": 0, "findings": []}

    async def investigate(state: AgentState, runtime: Runtime[GraphContext]):
        index = state["index"]
        question = state["plan"][index]
        evidence = await runtime.context.io.lookup(question, f"evidence-{index}")
        prompt = "Extract only claims supported by this evidence. Include exact source IDs from the evidence. "
        prompt += "Say insufficient evidence when appropriate.\n" + json.dumps({"question": question, "evidence": evidence})
        finding = _text(await runtime.context.io.model("local", "extract", prompt, f"extract-{index}"))
        return {"findings": [*state["findings"], finding], "index": index + 1}

    async def report(state: AgentState, runtime: Runtime[GraphContext]):
        prompt = "Answer using the findings only. Cite source IDs beside supported claims; flag gaps.\n" + json.dumps(
            {"task": state["task"], "questions": state["plan"], "findings": state["findings"]})
        return {"answer": _text(await runtime.context.io.model("cloud", "research_report", prompt, "report"))}

    graph = StateGraph(AgentState, context_schema=GraphContext)
    for name, node in (("plan", plan), ("investigate", investigate), ("report", report)):
        graph.add_node(name, node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "investigate")
    async def route(state):
        return "investigate" if state["index"] < len(state["plan"]) else "report"

    graph.add_conditional_edges("investigate", route)
    graph.add_edge("report", END)
    return graph.compile(checkpointer=checkpointer)


def build_writer(checkpointer=None):
    """Cloud brief/evaluation, local drafting, at most one local revision."""
    async def brief(state: AgentState, runtime: Runtime[GraphContext]):
        raw = await runtime.context.io.model("cloud", "writing_brief", "Define 1-3 concrete criteria for this writing task. "
            'Return only JSON {"criteria":["..."]}. Task: ' + state["task"], "brief")
        return {"plan": _items(raw, "criteria"), "revisions": 0}

    async def draft(state: AgentState, runtime: Runtime[GraphContext]):
        prompt = "Write the requested text. Follow the criteria and feedback. Output only the draft.\n" + json.dumps(
            {"task": state["task"], "criteria": state["plan"], "feedback": state.get("feedback", ""),
             "prior_draft": state.get("draft", "")})
        step = f"draft-{state.get('revisions', 0)}"
        return {"draft": _text(await runtime.context.io.model("local", "draft", prompt, step))}

    async def evaluate(state: AgentState, runtime: Runtime[GraphContext]):
        prompt = 'Assess the draft against the criteria. Return only JSON {"approved":true|false,"feedback":"..."}.\n' + json.dumps(
            {"task": state["task"], "criteria": state["plan"], "draft": state["draft"]})
        verdict = _object(await runtime.context.io.model("cloud", "evaluate", prompt,
                                                               f"evaluate-{state.get('revisions', 0)}"))
        if not isinstance(verdict.get("approved"), bool) or not isinstance(verdict.get("feedback"), str):
            raise ValueError("Invalid writing evaluation")
        return {"approved": verdict["approved"], "feedback": verdict["feedback"],
                "revisions": state.get("revisions", 0) + (0 if verdict["approved"] else 1)}

    async def finish(state: AgentState, runtime: Runtime[GraphContext]):
        # The model's critique is advisory; a missed criterion stays visible.
        if state["approved"]:
            return {"answer": state["draft"]}
        return {"answer": f"{state['draft']}\n\n[Evaluator feedback: {state['feedback']}]"}

    graph = StateGraph(AgentState, context_schema=GraphContext)
    for name, node in (("brief", brief), ("draft", draft), ("evaluate", evaluate), ("finish", finish)):
        graph.add_node(name, node)
    graph.add_edge(START, "brief")
    graph.add_edge("brief", "draft")
    graph.add_edge("draft", "evaluate")
    async def route(state):
        return "finish" if state["approved"] or state["revisions"] >= 2 else "draft"

    graph.add_conditional_edges("evaluate", route)
    graph.add_edge("finish", END)
    return graph.compile(checkpointer=checkpointer)


BUILDERS = {"simple": build_simple, "supervisor": build_supervisor,
            "research": build_research, "writer": build_writer}
