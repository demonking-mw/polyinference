# PolyInference design reading route

[Developer onboarding](../dev-readme.md) · [Module guides](../docs/modules/README.md) · [All files](../docs/file-tree.html)

After implementing a fix or feature, update all affected design/module/settings
and usage docs plus [FIXES.md](../development-docs/FIXES.md) in the same change.
Use [documentation maintenance](../docs/maintenance.md) before handing off.

Current design entry points, aligned 20 October 2026:

> **Edited 2026-10-20 because** later fixes and user-directed changes supersede
> parts of the 17 October proposal. Start with the
> [accepted revision and open-gap ledger](simplified-os/DESIGN_REVISIONS.md),
> then use the current guides below. Frozen graphs, fixtures and the original
> audit retain historical semantics; their existence is not runtime conformance.

Implementation supplement, 19 October: [current runtime/agent wiring](simplified-os/RUNTIME_BOUNDARY.md)
explains how the existing OS services support both the coding agent and general
artifact-producing agents, with executable regression examples and recovery rules.

Historical visual readers: [Agent design](visuals/agent-design.html) ·
[Simplified OS design](visuals/os-design.html). They run offline and preserve
17 October stories/assumptions; see their [status notice](visuals/README.md).
They have not been regenerated as a projection of current runtime behavior.

1. [Simplified OS](simplified-os/README.md): current profile, endpoint admission, optional attached/isolated workspaces, serialized coding integration and explicit guarantee limits.
2. [Agent on LangGraph](langgraph-agent/README.md): application control flow and its cooperation with the OS through public framework APIs.
3. [Merged agent graph](polyinference-design/polyinference-agent-design-merged.html): preserved source diagram; [merge notes](polyinference-design/merged-agent-design-notes.md) explain its original execution/memory precedence. Accepted later revisions override its copy/publication assumptions.
4. [Source consolidation](simplified-os/SOURCES.md): all design families, the five lecture derivations and which older defaults are superseded.
5. [Joint integration audit](INTEGRATION_AUDIT.md): historical paired-design issues, contract checks and rationale; current behavior/limits are recorded in the boundary guide and revision ledger.

The [older OS proposal](polyinference-design/project_design.md) remains research/rationale. Its broader optional features are not the implementation checklist for the simplified OS. Contracts and examples beside each current design describe interfaces; no agent or OS runtime is implemented by these documentation artifacts.

Further routes: [design provenance](polyinference-design/README.md),
[implementation notes](implementation/README.md), [visual-reader source/status](visuals/README.md),
[original OS prompt](os-v1-prompt.md), [root brief](../PROJECT_BRIEF.md) and
[implementation plan](../IMPLEMENTATION_PLAN.md). [Design tool modules](../docs/modules/design-tools.md)
explain validators, merge tools and reader generation.
