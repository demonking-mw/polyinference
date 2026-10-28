# PolyInference

**Reliability implementation:** [Changes and verification](development-docs/reliability-implementation-2026-10-27.md).
The [current issue record](development-docs/current-iter-issues.md#local-task-cloud-recovery)
and [small workflow qualification guide](docs/guides/qualification.md) describe scope and limits.

PolyInference pairs a LangGraph coding agent with a small orchestration OS.
The current coding application, polycode-v1, combines cloud senior planning/review
with local worker implementation and bounded, recorded model/tool execution.
The OS also supports general agents; broader agent support is planned for v2.
The default tester preset uses Codex seniors and remote Anthropic Haiku workers
as a local-lane stand-in. Actual local serving uses an explicitly configured server.
In the [UI](docs/guides/ui.md), OS processes and model operations expose a read-only
Memory / context drawer for retained original/prepared input and its provenance.
Use `polyinference ui --sim-batch 2` for an invocation-only remote Haiku simulation
with two worker slots; see the [tester setup](codex-haiku-setup.md) for limits.
Use `polyinference ui --sim-inference` to opt into normal, buggy or slow/buggy
inference with per-run TPS, batch and failure controls; see the
[simulation guide](docs/guides/sim-inference.md). Ordinary launches are unchanged.

- [Setup](setup.md) — Linux, WSL, macOS and provider setup.
- [Use PolyInference](docs/README.md) — runs, UI, CLI, configuration and recovery.
- [Developer onboarding](dev-readme.md) — architecture, checks and contribution rules.
- [Onboard a human or AI contributor](docs/contributor-onboarding.md) — required reading, memory/project-rule setup and the every-task routine.
- [Developer field guide](docs/onboarding.html) — illustrated onboarding lecture, LLM background and stack-by-stack starting paths.
- [Project tree for humans](docs/file-tree.html) · [JSON tree for agents](docs/file-tree.json).

**After every fix or feature, update all affected docs and navigation in the same
change.** Agents: read [AGENTS.md](AGENTS.md) and the
[fix history](development-docs/FIXES.md) before work.

The integrated reliability implementation supports
[bounded exception recovery](design-docs/implementation/WORKER_RECOVERY.md),
[execution observations and stagnation warnings](design-docs/implementation/PROGRESS_MONITORING.md),
source-backed review and versioned module contracts. See
[agent reliability settings](docs/guides/agent-reliability.md) for controls and
fresh-run requirements, and the
[documentation/run review](development-docs/documentation-and-reliability-audit-2026-10-27.md)
for current findings and historical limits.
