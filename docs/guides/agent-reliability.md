# Coding-agent reliability settings

[Configuration](configuration.md) · [Settings schema](../modules/settings.md) · [Worker
protocol](../modules/agent-workers.md)

These fields belong at the top level of AgentConfig, outside `system`. Defaults and bounds come from
[config.py](../../src/polyinference/config.py). An explicit nested object uses that object's schema
defaults; it does not recursively merge an earlier application preset. Use fresh state when changing pinned
settings.

| Field | Default / bounds | Behavior |
| --- | --- | --- |
| `inference_retry.max_attempts` | 2; 2–8 | Maximum response-validation attempts, including the initial attempt, for eligible registered queries. |
| `inference_retry.replacement_wait_seconds` | 1; 0–60 seconds | Window for the owning agent to offer a corrected request after a known failed response. Without an offer, retry the original bounded request. |
| `check_diagnosis.role` | worker; worker/specialist/senior | Role used for the read-only checking agent; actual endpoint follows role bindings. |
| `check_diagnosis.max_rounds` | 1; 0–3 | Bounded diagnosis rounds; zero disables diagnosis. |
| `check_diagnosis.max_read_paths` | 16; 1–32 | Maximum requested read-expansion paths. No write expansion is granted. |
| `check_diagnosis.instructions` | empty string | Additional application diagnosis instructions. |
| `acceptance_criteria` | [] | Additional semantic criteria; the full objective always remains a required criterion. |
| `max_review_reads` | 4; 0–16 | Total requested source ranges per senior invocation, not model rounds; at most eight ranges per proposal, within the remaining allowance. |
| `max_worker_recoveries` | 1; 0–3 | Ordinary semantic replacement depth per root; cloud takeover has its separate limit below. |
| `max_cloud_recoveries` | 1; 0–3 | Dedicated specialist/cloud attempts per local exception lineage, outside ordinary depth and task-share quota. Zero disables this route. |
| `progress_monitor.mode` | enforce; off/observe/enforce | Disable policy, record only, or escalate persistent stagnation. |
| `progress_monitor.warn_after` | 8; 2–128 decisions | Warn after this many settled decisions without new evidence. |
| `progress_monitor.escalate_after` | 12; 3–256 decisions | Escalate after this many; must exceed warn_after. |

Each acceptance criterion has `criterion_id` (1–80 letters/digits/underscore/hyphen), `description` (1–4000
characters) and `required_checks` (default []). IDs are unique; `objective` is reserved. Required check
names must be configured in task or final checks. See [check purposes](checks.md). Passing checks alone
cannot replace the source-backed assessment of every criterion on the exact reviewed tree. Each read range
has a relative path, offset (default 0) and max_bytes (default 2000; 1–4000). Requested ranges consume the
allowance even within one proposal.

Response validation, transport retry, output adaptation and worker grammar correction are separate
mechanisms. `inference_retry` is not an extra transport budget for every failed attempt: response-repair
exhaustion cannot restart through transport retry. Physical calls remain charged to their original resource
account. Native jobs with brokered tools and unknown effects cannot be blindly repeated. See [retry
ownership and records](../modules/retries.md) and [endpoint policy](endpoint-testing.md) for
OS-native/caller retry allowances.

Clean worker exceptions preserve a scoped development delta and abandoned-view snapshot. Eligible local
exceptions transfer to a specialist bound to `cloud`, including retry/defer/stop/omitted senior decisions.
The application records the raw model proposal and effective policy adjustments. This is coding takeover,
not merely cloud review or read-only diagnosis. Ordinary allocation cannot demote it. Cloud failures cannot
bounce back to local or reset their cloud count. Ineligible exceptions retain retry/defer/stop semantics and
exact blocker reasons. Explicit `resume_from=exception_ref` selects the retained delta; without it the
replacement starts fresh. Replacement grants cannot exceed the original grant; accounts, reserves and
absolute deadlines carry forward. Deferring an exception allows independent work but leaves a completion
obligation. Source conflicts use a fresh current base for automatic cloud repair while preserving the old
delta. Pending consumers are replaced transitively; started contracts stay pinned. No role change bypasses
unknown effects, explicit cancellation, publication, exhausted resources or unavailable cloud binding. See
[worker recovery](../../design-docs/implementation/WORKER_RECOVERY.md).

Progress uses new tree identities, nonoverlapping file-read coverage and new check evidence. Repeated
reads/checks, renamed/empty search queries, narration and rewritten memory do not reset stagnation. Active or unknown execution suppresses
semantic escalation; native jobs are sampled between settled jobs. Thresholds are initial tuning values, not
a measured guarantee that a worker will complete. See [progress
policy](../../design-docs/implementation/PROGRESS_MONITORING.md).

Planner inputs include actual tools/capability limits and cloud eligibility. Local planning requests one
observable behavior and focused check per task: movement, collision, save/load and migration are separate
work. Focused source/check evidence must establish consumer integration; existing APIs alone do not. Native
diagnosis may read its frozen source through a bounded readonly capability; raw diagnosis uses previews.
Resolved search/protocol errors retire from worker hints and retention priority; old histories stay immutable.
Clean retryable output exhaustion after OS repair receives bounded diagnosis before linked recovery. This guidance is not a semantic task-size validator. Browser/MCP/persistent service APIs are
unavailable; installed foreground test dependencies must be established with real evidence.

The integrated reliability implementation requires fresh program/state pins. The exact historical graph-only
Resume exception does not authorize arbitrary migration across this merge. Keep old runs with their original
code and config. The [27 October stage](../../development-docs/reliability-implementation-2026-10-27.md)
used runtime simple-os/3; current [four repairs](../../development-docs/four-repairs-implementation-2026-10-28.md)
require simple-os/5, agent-8-evidence-recovery/state 2.7 and preserve [model fallback](model-fallback.md). Bounded worker memory, explicit finishing resources and error-conditioned physical response
repair are included. An unstarted linked recovery consumer may be retargeted with its original
predecessor/contract/account; started contracts and source authority stay pinned. See
[qualification](qualification.md) for separate fixture/live completion gates. The [integration
audit](../../development-docs/branch-integration-audit-2026-10-26.md) records offline verification and
outstanding baseline failures; the [local live
investigation](../../development-docs/local-strata-live-test-2026-10-26.md) records the separate failed
product test.
