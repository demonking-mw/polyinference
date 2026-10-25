# Execution observations and agent progress policy

`operations.progress(process_id)` is a read-only OS interface. It reports retained
process phase/wait state, effects and termination certainty, live futures, permits,
resource account/call usage, endpoint admission capacity/queue/reservations and the
original deadline. It does not probe providers or claim remote readiness: endpoint
readiness remains `unprobed`. Recent effects are bounded to 32 with a total count.
A stable cursor identifies activity; agents must not equate a changed cursor with
meaningful task progress. This interface requires no task, workspace or Git context.
`operations.resource_state(process_id)` exposes the same remaining shared allowances
for recovery readiness; exhausted operation or token accounts cannot start replacements.

Host code can register named, bounded synchronous inspectors with
`register_progress_source(name, inspector)`, for future maps or other execution
structures. Inspectors must perform no I/O. Missing optional state stays absent;
inspection exceptions are reported as unavailable and do not change execution.
These extra observations cannot override journal certainty or authorize cleanup.

The coding agent calls this interface between settled decisions. Its policy tracks:

- Previously unseen workspace tree identities and protocol phase transitions.
- New file/document read coverage, identified by path, actual content digest and
  merged byte ranges. `files.read` accepts bounded `offset` and `max_bytes`.
- New configured-check outcomes for the exact tree and environment.

It tracks both ordinary tool history and journaled broker callbacks. Repeating a
read, overlapping already read ranges, rechecking unchanged code, returning to a
previous tree, changing timestamps/IDs or printing different shell text does not
reset the idle counter. Narration, memory rewrites and endpoint activity do not
count as evidence. Novelty is a heuristic: a new tree is not proof of correctness.
All normal reconciliation, checks, assessment and exact-tree senior acceptance
still apply.

`progress_monitor` defaults to `{"mode":"enforce","warn_after":8,"escalate_after":12}`.
`observe` records warnings and would-escalate events without stopping work; `off`
disables the policy. Escalation must follow warning by at least one decision. The
defaults are initial tuning values, not calibrated by a new live provider run.

At the warning threshold the agent appends application-origin `task_attention`
feedback with `verdict=uncertain`, the evidence gap and a concrete response request.
It consumes no extra inference call. This resembles worker uncertainty in confidence
and evidence shape; it is not an assessed report, fake tool output or physical
uncertainty. The worker can change approach, finish a candidate or request review.
Warnings describe a boundary between settled operations; only the fenced exception
packet claims confirmed process termination after cleanup.
Evidence gain clears the current stall episode. Continued stagnation enters the
[clean exception workflow](WORKER_RECOVERY.md), preserving source and releasing
ownership before the senior decides recovery. It never fabricates assessment.

Counters, seen evidence, warning IDs and cached decisions survive replay/restart.
Observation never calls `preserve_delta` or seals an in-progress development delta.
Observer failure leaves primary execution alone. Active/prepared/unknown effects
suppress semantic escalation and retain the existing strict reconciliation rules.
No timer kills a provider job or declares cancellation successful. Native jobs are
observed at settled application boundaries; this does not interrupt internal model
loops inside a long-running native job. Repository setup retains its existing policy.

The UI shows the last progress observation per worker. JSON export includes counters,
execution observations, warning/escalation events and observer errors, alongside
exception/recovery provenance. New program/state pins require fresh run state.
