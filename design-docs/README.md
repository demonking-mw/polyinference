# PolyInference design reading route

Current design entry points, updated 17 October 2026:

Interactive visual readers: [Agent design](visuals/agent-design.html) · [Simplified OS design](visuals/os-design.html). Both run offline and include focused diagrams, shared execution stories and review notes.

1. [Simplified OS](simplified-os/README.md): the minimum runtime to build, including local continuous batching, private scoped code copies and merge/test/commit exclusion.
2. [Agent on LangGraph](langgraph-agent/README.md): application control flow and its cooperation with the OS through public framework APIs.
3. [Merged agent graph](polyinference-design/polyinference-agent-design-merged.html): current diagram authority; [merge notes](polyinference-design/merged-agent-design-notes.md) explain execution/memory precedence.
4. [Source consolidation](simplified-os/SOURCES.md): all design families, the five lecture derivations and which older defaults are superseded.
5. [Joint integration audit](INTEGRATION_AUDIT.md): paired-design issues, corrections, supporting evidence and remaining implementation checks.

The [older OS proposal](polyinference-design/project_design.md) remains research/rationale. Its broader optional features are not the implementation checklist for the simplified OS. Contracts and examples beside each current design describe interfaces; no agent or OS runtime is implemented by these documentation artifacts.
