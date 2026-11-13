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
`development-docs/FIXES.md#fix-0106` and current tracker (`docs/temporary/incidents/2026-10-22-router-tutorial-record.md#router-distillation-tutorial`).
The HTML guide also records optional thinking, targeted synthetic-data and
summarize-then-route experiments, plus distinct DPO and online RLAIF procedures.
These remain research options; `development-docs/FIXES.md#fix-0107` records documentation
verification, not implementation or training results.

<a id="quota-aware-task-scheduler"></a>
## Quota-aware process scheduler — proposed on 2026-10-21

Status: proposed for the next iteration; outside the current implementation scope.
Source: the user's next-iteration request.

Research/design is in the standalone scheduler report (`docs/temporary/proposals/2026-11-08-standalone-scheduler-design.md`),
developed 8 November and authority-corrected 9 November. **V1 scheduler authority
is only individual-process admission, waiting or preemption requests. The OS
distributes resources.** This supersedes earlier wording assigning task submission,
operation dispatch, placement, resource claims or quota allocation to the scheduler.
All new interfaces remain unimplemented; no current-version work or live run is
authorized by this proposal.

Part 1 specifies OS process-control support, resource admission/accounting,
safe suspension/readmission, observations and shared provider ownership. Part 2
defines only ranking/fairness and run/wait/preempt decisions for existing process
IDs. Read the corrected OS impact audit (`docs/temporary/investigations/2026-11-09-scheduler-os-impact.md`)
and `development-docs/FIXES.md#fix-0183` before implementation.

The scheduler may observe urgency, time sensitivity and OS-reported quota/resource
blockers to choose which individual processes may run or should leave the running
set. It cannot create tasks/programs, pick endpoints/models, assign slots/tokens,
reserve quota, dispatch operations or attest release. Parent admission does not
automatically admit children. A run decision is eligibility; the OS can still
report a resource wait. A preemption request is pending until the OS establishes
a safe continuation and actual retained/released resources.

The OS owns resource distribution, authorized routing, capacity and every applicable
quota/rate gate. Five-hour/weekly Codex windows remain planning examples, not verified
entitlements. Optional placement and pacing research is OS-owned, independently
of process scheduling. Fidelity optimization remains future work; current hard
constraints, grants, budgets/deadlines, protected progress and unknown holds remain.

<a id="shared-agent-support-library"></a>
## Shared agent support library — deferred on 2026-10-20

Status: proposed for the next stage; explicitly excluded from the current fix.
Source: the user's request to keep the current system split between OS and agent.
Earlier design: three-layer responsibility proposal (`docs/temporary/proposals/2026-10-20-overflow-responsibility-proposal.md`).
Current plan: optional OS context handling (`docs/temporary/proposals/2026-10-20-optional-os-context-proposal.md`).

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
