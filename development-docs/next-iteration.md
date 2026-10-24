# Next iteration backlog

Ideas recorded here are deferred, not requirements for the current implementation.

<a id="learned-agent-routing"></a>
## Fine-tuned agent routing model — proposed on 2026-10-21

Status: consider for the next version; outside the current implementation scope.
Source: the user's next-version idea.

Consider fine-tuning a routing model that takes descriptions of all available
agents, their available settings, and the incoming prompt. Its output selects
which agent and settings should handle that prompt.

The router would own this application-level selection policy. Its recommendation
must stay within available agents, supported settings and user constraints; the
OS continues to enforce authority and resource admission.

Research starting point recorded 2026-10-22:
[HTML learning guide with background and practical labs](router-training-guide.html)
and the
[step-by-step Opus router-distillation tutorial](router-distillation-tutorial.md).
It covers task/registry inputs, supported agent/settings outputs, teacher labels,
a 1.5B LoRA student for the user's reported 16 GB GPU, held-out evaluation and
a later RLAIF path. The user reports written Anthropic permission for this
research project. This is documentation, not an implemented routing feature;
production data, evaluation gates, settings integration and deployment remain
future design work. Current-version documentation record:
[FIX-0106](FIXES.md#fix-0106) and [current tracker](current-iter-issues.md#router-distillation-tutorial).
The HTML guide also records optional thinking, targeted synthetic-data and
summarize-then-route experiments, plus distinct DPO and online RLAIF procedures.
These remain research options; [FIX-0107](FIXES.md#fix-0107) records documentation
verification, not implementation or training results.

<a id="quota-aware-task-scheduler"></a>
## Quota-aware task scheduler — proposed on 2026-10-21

Status: proposed for the next iteration; outside the current implementation scope.
Source: the user's next-iteration request.

Design a scheduler that considers all tasks and their settings, especially
priority, fidelity and time sensitivity, together with cloud-inference rate
limits, remaining quota and reset windows. It should schedule the whole task
set, commanding the OS to add/submit tasks or withhold them from running for a
specified duration, then reconsider the schedule as tasks and capacity change.

Include multi-window provider limits, such as the user's example of Codex
five-hour and weekly usage windows. These are planning examples, not fixed or
verified account entitlements; use the configured or reported limits for the
actual account/provider.

Scheduling policy belongs in a scheduler/controller above the OS. The OS should
provide generic submission, timed deferral and admission mechanisms, enforce
grants and resource limits, and report execution/quota facts without interpreting
coding tasks. Deferring pending starts must be distinguished from interrupting
running work; safe interruption/resumption and the timing/quota contract remain
future design work. Coordinate with the routing proposal when selected agents
or settings affect quota demand.

<a id="shared-agent-support-library"></a>
## Shared agent support library — deferred on 2026-10-20

Status: proposed for the next stage; explicitly excluded from the current fix.
Source: the user's request to keep the current system split between OS and agent.
Earlier design: [three-layer responsibility proposal](agent-os-overflow-responsibility-proposal-2026-10-20.md).
Current plan: [optional OS context handling](optional-os-context-management-proposal-2026-10-20.md).

Consider an optional caller-side library once several real agent implementations
show which patterns are worth sharing. Candidate helpers include declarative
context construction, response-schema validation, application recovery loops,
checkpoint/handoff utilities and convenience wrappers over OS context services.

The motivation is to reduce duplicated agent code without adding coding workflow
to the OS. The cost is a third architectural surface, versioning and lifecycle
complexity. The user considers that premature for the current stage.

Do not introduce this library, require it, or route the current fix through it.
For now, generic execution safety and optional automatic context/compaction
services belong to the OS; coding-specific choices and semantic recovery belong
directly to the coding agent. Future evaluation should preserve direct OS access,
support non-coding agents and derive the library from demonstrated reuse.
