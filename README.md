# PolyInference

PolyInference pairs a LangGraph coding agent with a small orchestration OS. The current version is mainly to support polycode-v1, a coding agent designed for concurrency and to leverage the power of cloud SOTA models with local inferencing. In the agent, senior (cloud) plans and reviews, (local inference) workers implement, and the runtime records bounded
model/tool execution. The OS id designed to run any agents, many are/will be in development in v2. The current test system uses Codex for senior work and Anthropic Haiku as a local inference simulator for those without the hardware to run them.
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

## Integrated reliability branch (2026-10-26)

The reliability work is integrated with the simple OS runtime. Workers now support
[bounded exception recovery](design-docs/implementation/WORKER_RECOVERY.md),
[execution observations and stagnation warnings](design-docs/implementation/PROGRESS_MONITORING.md),
source-backed semantic review, and versioned module contracts. See the
[settings guide](docs/modules/settings.md) for controls and fresh-run requirements.
