# Two-slot run follow-ups

<a id="run-a1859f8644a5-findings"></a>
## First two-slot run: recovery and concurrency findings — 2026-10-20

Status: open findings; analysis only. The only implementation change in this task
is increasing the UI/mixed-example sprint allowance from 9 to 27 (derived senior
query ceiling 27 to 81). Full run analysis (`docs/temporary/investigations/2026-10-20-run-a1859f8644a5.md`) and
[measured evidence](../investigations/run-a1859f8644a5-evidence.json) distinguish observed failures,
source findings and unmeasured performance hypotheses. History:
`development-docs/FIXES.md#fix-0076`, `development-docs/FIXES.md#fix-0077`.

The run admitted two local-lane operations together for 230.444 seconds, with
5 ms median / 436 ms maximum admission delay, and ended with no retained active
reservation or uncertain effect. The contested verification permit was acquired
after 6.693 s. No OS deadlock was established. Sprints 3–9 each started one task;
application dependencies and recovery, rather than inference capacity, limited
later parallelism. CONC-01 remains open beyond this workload.

<a id="run13-01"></a>
### RUN13-01 — P1: establish shared test prerequisites before parallel dispatch

Implemented in `development-docs/FIXES.md#fix-0088`: source/command planning context,
explicit check-preparation ownership and validated dependencies, with a real
two-worktree test-discovery regression. The evidence below is retained.

Owner: coding agent planning/check policy. Sprint 2 required the persistence
worker to add automatically discovered tests, but its write grant excluded the
hardcoded runner. Only the parallel canvas worker could edit that runner, and
its candidate stayed private. Persistence's direct 12-test run passed while the
configured build omitted those tests, producing an uncertain report and an extra
specialist recovery sprint. Disjoint write sets alone did not make completion
independent; this was not an observed concurrent file-write race.

Before dispatch, inspect shared build/test contracts, establish discovery once,
or assign its preparation as a dependency with a clear owner. Do not let one
worker's private/unaccepted infrastructure become an implicit prerequisite for
another. Add a two-worktree regression where both add independent tests and
configured checks actually run both after integration; retain scope isolation.

<a id="run13-02"></a>
### RUN13-02 — P1: materialize private candidates through explicit handoff

Bounded explicit-handoff fix implemented in `development-docs/FIXES.md#fix-0089`.
Planning gets actionable source/grant/conflict offers and mode-correct prompts;
invalid handoffs receive bounded corrections before dispatch. Arbitrary selective
multi-candidate recovery remains outside this item. Historical evidence follows.

Owner: coding agent planner/prompts/recovery. Sprints 4–6 named private candidates
in prose with resume_from null; sprint 6 parked because current-view file tools
could not inspect the named source. Sprints 7–8 restarted from the old shared
baseline. Sprint 9's explicit resume_from successfully supplied the retained
canvas implementation. Existing preservation was available but poorly used.

Use the existing resume_from/private-candidate or preserved_source_ref mechanism
when planning reuse, with complete grants and base-conflict checks. For selective
multi-candidate recovery, provide a concrete permitted read/materialization path
or explicitly authorize reconstruction; do not invent a commit-reading tool.
Reconcile the contradictory legacy/in-place senior prompt statements about
uncertain publication. Keep uncertain candidates private.

Related: FIX-0040, FIX-0060 and the still-open prompt finding in FIX-0068.
Earlier tests validate explicit provider reuse, not planner selection. Add a
senior-to-replacement regression proving source survives without manual Git
access, and that unavailable reuse produces one actionable correction rather
than repeated reconstruction. Preserve grant/conflict refusal coverage.

<a id="run13-03"></a>
### RUN13-03 — P1: make bounded implementation and verification tasks converge

Owner: coding agent assignment, repair and acceptance policy. Seven candidates
were uncertain despite passing configured build evidence. Browser smoke testing
was conditional in the first canvas task; later tasks bundled recovery, gameplay,
observability, browser setup, state assertions and docs. Sprint 5's five passing
Chromium tests did not exercise the requested movement/mining/placement state;
sprints 5/7/8 exhausted two repairs. Sprint 9's implementation-only handoff still
needed bundle/count evidence. Gameplay stayed private and blocked save/load work.

Specify attainable per-task criteria and actual tooling/checks before dispatch;
split implementation and browser verification deliberately, preserving source
between them. Teach recovery to choose a smaller missing unit using the exact
report instead of reissuing the whole slice from baseline. Browser evidence must
exercise state, inventory and lifecycle behavior; compilation is insufficient.
Do not bypass OS publication safeguards or silently accept uncertain code.
Add bounded fixtures for missing browser capability, helper-only success,
repair exhaustion and retained-source verification handoff. Final product
acceptance must still require the real objective, including save/load.

<a id="run13-04"></a>
### RUN13-04 — P2: audit global command serialization and journal churn

Owner: OS workspace/exclusive/storage mechanisms; coding Git callers supply
workload. 6,960 of the retained 10,000 events are shell/installation ownership
events; 24,313 earlier events, including the parallel phase, were pruned.
Workspaces.command serializes trusted Git reads as well as writes under that
installation-wide resource. The tail alone has 1,740 release events and about
76.3 s of ownership. This establishes churn/serialization, not a measured
throughput bottleneck or deadlock.

Extend CONC-01 with a two-worktree workload containing repeated Git reads, builds,
long shell work and a finishing worker. Measure command count, wait/hold time,
event-loop delay and storage/event-retention cost. Evaluate safe batching and
resource granularity only from that evidence; preserve mutation exclusion,
FIFO/progress, cancellation and unknown-effect retention. Retain useful bounded
summary/transition evidence so short lock cycles do not erase the concurrency
diagnostics. Add cross-runtime and generic non-coding coverage as applicable.

<a id="run13-05"></a>
### RUN13-05 — P2: reduce protocol and execution-environment correction churn

Owner: coding agent reply/tool construction and provider protocol integration.
There were 67 malformed worker replies (23 during the first two sprints, 44
later), with XML-like prefixes and invalid JSON escaping; maximum consecutive
streak two. There is no evidence these came from concurrent-history mixing.
Twenty-one 8k cutoffs recovered successfully. FIX-0075 already raised the current
limit to 32k; that is prior work, not a fix performed by this investigation.

Investigate a reliable provider-supported structured action path and smaller
incremental edits while preserving strict validation. Replay the observed
malformed shapes in both serial and concurrent fixtures, checking isolation and
bounded correction rather than accepting arbitrary text around a tool call.
Surface schema limits and invocation-local scratch setup clearly: this run also
requested timeout 900 above the 600 schema bound, read a nonexistent pinned path,
submitted a non-unique patch, and used unset PW_SCRATCH in a later command.
Treat ordinary compile/test failures as repair observations. Verify any claimed
improvement under the current 32k setting without assuming the cap alone solves it.

<a id="run13-06"></a>
### RUN13-06 — P2: distinguish ancestor tips from accepted task contributions

Implemented in `development-docs/FIXES.md#fix-0090`: distinct ancestry, source,
publication and kept nonempty-contribution facts in new summaries/UI. Old saved
merged fields remain ancestry-only and unverified; history is not migrated.

Owner: coding repository summary/UI projection. The parked sprint-6 worker had
no new commit and its HEAD equaled the accepted persistence baseline, yet
coding/repository-summary reported merged:true. The field measures ancestry,
not successful task publication. This repeats FIX-0068's open metadata finding
with a clean empty worktree instead of a dirty one; no incorrect merge occurred.

Expose tip ancestry, private/dirty delta and actual task publication/contribution
as distinct facts. Add summary coverage for untouched, interrupted, private and
accepted workers so an inherited baseline is never presented as accepted new
gameplay. Do not rewrite historical commit/report evidence.
