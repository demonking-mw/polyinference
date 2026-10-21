# PolyInference

PolyInference pairs a LangGraph coding agent with a small orchestration OS.
A senior plans and reviews, workers implement, and the runtime records bounded
model/tool execution. The OS also supports agents that produce artifacts without
code or Git. The default UI uses Codex for senior work and Anthropic Haiku for workers.
In the [UI](docs/guides/ui.md), OS processes and model operations expose a read-only
Memory / context drawer for retained original/prepared input and its provenance.

- [Setup](setup.md) — Linux, WSL, macOS and provider setup.
- [Use PolyInference](docs/README.md) — runs, UI, CLI, configuration and recovery.
- [Developer onboarding](dev-readme.md) — architecture, checks and contribution rules.
- [Project tree for humans](docs/file-tree.html) · [JSON tree for agents](docs/file-tree.json).

**After every fix or feature, update all affected docs and navigation in the same
change.** Agents: read [AGENTS.md](AGENTS.md) and the
[fix history](development-docs/FIXES.md) before work.
