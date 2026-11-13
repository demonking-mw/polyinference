# Local task sizing and cloud recovery

<a id="local-task-cloud-recovery"></a>
## P1 — Local task granularity and cloud worker recovery — 2026-10-27

**Status: implemented in the uncommitted tree; the small live gate passed, including actual cloud-worker resume. Combined framework results and limits are in the implementation record (`development-docs/reliability-implementation-2026-10-27.md`).**
Requirements, user judgments, evidence and verification plan (`docs/temporary/proposals/2026-10-27-local-task-and-cloud-recovery.md`).
Split coarse local assignments into independently testable behaviors; turn eligible
local stalls into bounded cloud-worker repair, preserve that route outside normal
task-share rounding, and tell the sprint planner the OS's actual capabilities.
Keep original accounts/deadlines, source authority and unknown-effect safeguards.
The earlier 227-case result belongs to FIX-0132. The authorized follow-up adds
bounded worker state, error-conditioned repair, OS enforcement and qualification.
Already-linked unstarted recovery consumers now support lineage-preserving
retargeting, including transaction-conflict/restart coverage. Started contracts
remain pinned. Read the current record before claiming long-run reliability.

Detailed proposed implementation plan and historical failure coverage (`docs/temporary/proposals/2026-10-27-run-reliability-plan.md`)
separates agent changes, OS guarantees, provider setup and verification.
It records the earlier cloud takeover and pending-consumer limitation at planning
time; its analysis-only scope was superseded by the user's implementation request.

Read the fix history and design principles (`development-docs/FIXES.md`) before repository work, as
required by `AGENTS.md`, and update it before finishing. This file
retains detailed investigations and historical results. The fix history records
subsequent corrections, including recoverable startup failures and the required
agent/OS boundary; consult it before treating an older implementation note below
as current behavior.

Current cross-run assessment: 27 October documentation/reliability audit (`docs/temporary/investigations/2026-10-27-documentation-and-reliability-audit.md`).
Its historical recommendations distinguish orchestration mechanisms from product
convergence. The authorized follow-up implements the selected plan and static
U01–U04 repairs; current qualification limits remain in the implementation record.
