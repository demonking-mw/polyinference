# Coding-agent reliability settings

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
| `max_review_reads` | 16; 0–16 | Total requested source ranges per senior invocation, not model rounds; at most eight ranges per proposal, within the remaining allowance. |
| `max_senior_corrections` | 1; 0–3 | Additional proposal corrections after validation failures; source retrieval does not refill this allowance. |
| `max_worker_recoveries` | 1; 0–3 | Ordinary semantic replacement depth per root; cloud takeover has its separate limit below. |
| `max_cloud_recoveries` | 1; 0–3 | Dedicated specialist/cloud attempts per local exception lineage, outside ordinary depth and task-share quota. Zero disables this route. |
| `progress_monitor.mode` | enforce; off/observe/enforce | Disable policy, record only, or escalate persistent stagnation. |
| `progress_monitor.warn_after` | 8; 2–128 decisions | Warn after this many settled decisions without new evidence. |
| `progress_monitor.escalate_after` | 12; 3–256 decisions | Escalate after this many; must exceed warn_after. |

Each acceptance criterion has `criterion_id` (1–80 letters/digits/underscore/hyphen), `description` (1–4000
characters) and `required_checks` (default []). IDs are unique; `objective` is reserved. Required check
names must be configured in task or final checks. See check purposes (`docs/guides/checks.md`). Passing checks alone
cannot replace the source-backed assessment of every criterion on the exact reviewed tree. Each read range
has a relative path, offset (default 0) and max_bytes (default 2000; 1–4000). Requested ranges consume the
allowance even within one proposal.

Every planner message includes `review_limits`: configured, used and remaining reads and corrections,
the eight-range proposal ceiling, and the 4000-byte range ceiling. These counters refresh after retrieval
and validation failures. An oversized batch is rejected before retrieval and does not consume reads.
`planning_limits` exposes sprint/worker/recovery, diagnosis, progress and response-retry settings.
Planner and worker inputs also carry `resource_limits`, current `resources`, `finishing_reserve` and
`response_budget` for process calls, operations, tokens, deadline, bytes and final phases. Native cloud
per-call token limits remain provider-owned and appear as null; byte and aggregate resource bounds still
apply. Explicit configurations and saved runs keep their pinned limits; the new default applies to fresh
configurations.

Response validation, transport retry, output adaptation and worker grammar correction are separate
mechanisms. `inference_retry` is not an extra transport budget for every failed attempt: response-repair
exhaustion cannot restart through transport retry. Physical calls remain charged to their original resource
account. Native jobs with brokered tools and unknown effects cannot be blindly repeated. See retry records (`docs/modules/retries.md`) and endpoint policy (`docs/guides/endpoint-testing.md`) for
OS-native/caller retry allowances.

For execution behavior after a failure, see [worker recovery and progress](worker-recovery.md).
