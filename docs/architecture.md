# Architecture at a glance

[Documentation](README.md) · [Setup](../setup.md) · [Developer guide](../dev-readme.md)

| Path | Purpose |
| --- | --- |
| `src/polyinference/agent/` | Controller, independent worker graphs, senior review, setup, routing and prompts. |
| `src/polyinference/runtime/` | Simple OS kernel, admission, process supervision, provider clients and workspace/tool broker. |
| `src/polyinference/contracts.py` / `workspace_contracts.py` | Packaged SDK wire and workspace types. |
| `src/polyinference/ports.py` | Runtime service interfaces implemented by the bundled kernel. |
| `src/polyinference/ui.py` / `ui.html` | Local testing backend and frontend. |
| `examples/` | Editable provider/task configurations. |
| `tests/` | Implementation tests. |
| `testing/` | Ignored disposable projects created while testing the agent. |
| `.polyinference/` | Ignored local state, fixtures and artifacts; project-local task worktrees. Only explicit legacy isolated mode owns a private Git store. |

Start with the [design documentation index](../design-docs/README.md),
[LangGraph agent design](../design-docs/langgraph-agent/README.md),
[simplified OS design](../design-docs/simplified-os/README.md),
[implementation/adapter notes](../design-docs/implementation/README.md) and
[implementation plan](../IMPLEMENTATION_PLAN.md). The implementation incorporates
[the user's agent-review answers](../design-docs/implementation/user-agent-review.json).
The canonical wire/workspace data structures remain the integration boundary for
current and future runtimes; provider transport details stay inside the kernel's
endpoint adapters. The StandaloneRuntime import is a compatibility alias.

## Ownership

The coding agent decides tasks, Git workflow, check selection, canonical memory
and acceptance. The OS supplies generic process/effect, resource, capability,
storage and optional workspace/context services. General agents can finish
without Git, source edits or checks. Provider token/GPU scheduling is external.

Use the [module index](modules/README.md) for source responsibilities and
the [tree](file-tree.html) for every file. Update the owning guides whenever
implementation changes. See [documentation maintenance](maintenance.md).

