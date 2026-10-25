# Bounded worker exception recovery

A worker's `needs_review` first retains the existing bounded checking-agent diagnosis.
If it cannot continue, parking preserves a scoped development delta and an immutable
snapshot of the abandoned view before releasing verification. Integration repairs
remain separate from the original development delta. A durable parking intent allows
replay after abort or fencing. Published work cannot be turned into an exception.

The runtime checks for unsettled effects, live futures and owned permits, then fences
the process generation. The agent atomically publishes a validated interrupted
attempt, an immutable exception packet and its queue entry, removing the process
from active/captured workers. The reason code is short; full diagnostics remain in
artifacts. Completed parked graphs are never relaunched at step zero.
Published workers with pending cleanup checkpoints resume that existing cleanup.
Completed END workers detach only after checking settled effects and released permits;
neither path restarts development or publishes a second report.

New starts close while already running workers finish. Senior review receives
exceptions separately from assessed reports and can `retry`, `defer` or `stop`:

- `retry` needs a new task ID, a specific changed condition and a linked predecessor.
  `max_worker_recoveries` defaults to one per root (allowed range zero through three).
  Explicit `resume_from=exception_ref` selects one retained development delta;
  otherwise the new assignment starts fresh. Reuse is checked against the current
  base and exact replacement write grant before planning and at materialization.
- `defer` permits independent work but leaves an unresolved objective obligation.
- `stop` pauses for steering. Neither defer nor stop permits project completion.

Affected pending dependents must be cancelled and replaced together with their new
dependency IDs. Started assignments and interface contract versions stay pinned.
Original interrupted attempts remain evidence and count as started work. Their
obligations resolve only when linked replacement work is assessed and explicitly kept.
New unlinked work overlapping an unresolved exception's write scope is rejected.

The OS owns generic process settlement, fencing and inherited resource accounts; it
does not interpret task verdicts or decide what to retry. Replacements and diagnosis
share the original root's physical inference calls, conservative token reservations,
logical operation allowance and absolute deadline. Transport retries charge each
physical attempt once; replay of a settled operation remains available after fencing.
Senior management calls retain their separately bounded process/run allowance.

This first version supports one replacement per disposition, not a split with
multiple automatically resumed sources. Conflicting reuse requires an explicit
repair plan. Unexpected host failures and unknown physical execution still fail
closed; no timer cancels a provider job or expires another owner's permit.

Program/state pins changed; use fresh state for this implementation. Existing runs
require their original pinned source. Export JSON includes exception packets,
decisions and recovery account lineage.

## Historical fixes retained

The investigation reviewed the full fix ledger on the profiles branch and the
runtime reliability commits present here. The implementation preserves:

- FIX-0022/0032: generic OS mechanisms rather than coding/report policy in the OS.
- FIX-0023/0025: actual message roles, current requests and immutable authority pins.
- FIX-0027/0047: linked new identities, distinct retry allowances and strict unknowns.
- FIX-0033: validate the merged interrupted attempt; diagnostics are not reason codes.
- FIX-0057/0060/0089: preserve source and distinguish original deltas from integration.
- FIX-0084: executed retired work remains in allocation; unstarted cancellation does not.
- `bb4f0df`, `0cb6919`, `309713c`, `18cfb47`, `cd227c3`: physical retry charging,
  application-origin feedback, bounded diagnosis, exact-tree review and provenance.
- `191076c`: immutable interface versions and resulting-plan dependency validation.

The larger profiles-branch ledger is not copied or rewritten on this implementation
branch. The local [fix log](FIXES.md) records the changes made here.
