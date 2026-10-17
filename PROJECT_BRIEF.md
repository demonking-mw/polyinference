# Polyinference — project brief

## Purpose

Polyinference explores how a long-running agent can combine the cost efficiency of local language models with the stronger capabilities of cloud models. A local model may handle a bounded task well while struggling with the full range of agent decisions. Cloud models can cover those gaps, but using them for every inference can be expensive.

The project will build an inference and execution layer that assigns work to available models and preserves continuity when models change. The central question is **when and how a cheaper inference can replace a more expensive one without degrading the task outcome**. Evaluation must include local resource use, extra turns, retries, context transfer, and latency.

## System concept

The system has three layers:

| Layer | Responsibility | Approach |
|---|---|---|
| Agent design | Task control flow, tools, and completion behavior | Use an existing framework; start with a small coding agent on LangGraph |
| Agent OS / kernel | Model routing, budgets, context preparation, tool policy, resource lifecycle, and execution records | Build this layer; it is the core of Polyinference |
| Models and capabilities | Local/cloud inference endpoints, execution environments, MCP servers, and other tools | Reuse existing implementations selected for the available hardware and tasks |

“Kernel” describes an application-level control layer. It manages an agent's inference and capability resources while relying on LangGraph for graph execution and checkpoint semantics.

The longer-term vision is to accept an agent design, adapt it to an available model stack, and run it. Stage 1 supports only the LangGraph subset used by one reference agent; general graph optimization comes later.

## Initial design decisions

**Target framework:** LangGraph. The first reference workload is a simple coding agent operating on one repository and one task at a time. This makes model routing observable in a realistic feedback loop while keeping the agent design manageable.

**Starting points:** mini-swe-agent v2 provides a clear feedback loop and replaceable model/environment contracts. Deep Agents demonstrates LangGraph composition, context management, and backend boundaries; its SDK and terminal application have different scopes.

The initial preference is a thin LangGraph loop inspired by mini-swe-agent, borrowing selected necessities from the richer harnesses. Keep inference routing explicit. Adopting the Deep Agents SDK remains an alternative if it reduces effort without obscuring routing or adding unused behavior.

The accompanying [interactive architecture study](references/docs/agent-structures.html) compares these references and proposes the Stage 1 graph in detail.

## Stage 1 scope

Build a vertical slice with:

1. One agent graph, one repository, and tools for discovery, reading, patching, and configured checks.
2. One local endpoint and one cloud endpoint behind a common inference interface.
3. A cloud-only baseline and an experimental hybrid policy: bounded local discovery, then conservative cloud escalation.
4. Shared state, provider-compatible context, bounded output, checkpoint/resume, and structured usage/execution records.
5. Tool policy, constrained execution, and limits on retries, steps, time, and spending. Support one configured MCP adapter when a workload requires it.
6. Completion evidence tied to the current workspace state, with failures and unavailable checks reported clearly.

Use one conversation and working state. Switching models does not require another agent. Defer supervisors, teams, autonomous memory, marketplaces, dynamic scheduling, and graph rewriting until measurements justify them.

## Stage 1 evaluation

Run fixed coding tasks from identical revisions under cloud-only, local-only, and hybrid configurations. Keep the harness, instructions, limits, and evaluator comparable; record intentional routing differences.

Measure:

- Final-patch success using independent checks.
- Cloud usage/spend and local inference/resource use.
- End-to-end latency, extra turns, retries, and context-transfer overhead.
- Escalation reasons and recovery after interruption or failure.

Predeclare acceptable quality and latency margins. A lower cloud bill is useful only when those targets hold. A well-supported negative result is still a valid research outcome.

## Completion criteria

The reference agent runs reproducibly through the kernel, switches models without losing valid task/tool state, resumes supported interruptions, and produces comparable evaluation records. The result identifies what can be offloaded locally, what must escalate, and the measured cost of that decision.

## Open decisions

- Hardware, memory budget, inference runtime, and model choices.
- Initial tasks and quality/latency margins.
- Workspace isolation and cloud data-sharing policy.
- Whether MCP is needed for the first workload.
- How much to reuse from Deep Agents versus implement as a thin LangGraph loop.

Resolve these through the smallest reproducible experiments rather than expanding the agent architecture in advance.
