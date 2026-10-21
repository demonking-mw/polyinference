# Run a1859f8644a5: first two-slot inference test

Investigated 2026-10-20 (America/Toronto). Input:
`C:\Users\bh349\Downloads\polyinference-a1859f8644a5.json`.
Measurements: [machine-readable evidence](run-a1859f8644a5-evidence.json).
Open work: [current-version findings](current-iter-issues.md#run-a1859f8644a5-findings).

The run exercised concurrent inference successfully. Its main failure was a
repeated private-candidate recovery/verification cycle that consumed the sprint
allowance and prevented later work from becoming independently runnable. There
is no observed OS deadlock, admission starvation, capacity leak or conflicting
source write in this export. This is a narrower conclusion than completing the
open [CONC-01 audit](current-iter-issues.md#os-concurrency-audit).

Only the UI/mixed-example sprint budget was changed by this task: **9 to 27**,
with the existing derived senior-query ceiling increasing **27 to 81**. No
concurrency, recovery, prompt, tool, acceptance or generated-game implementation
was changed. The retained run remains immutable and was not resumed.

## Outcome and actual exhausted resource

The Minecraft v13 run lasted from 20:57:49 to 22:14:12 EDT on October 20
(00:57:49–02:14:12 UTC on October 21), about 76 minutes. It ended
`budget_stopped`, blocker `Sprint/query limit`, at sprint 9 and senior query 9.
The run used 11,138,203 tokens against 64,000,000; its largest worker account
used 2,248,969 against a 16,000,000 process allowance. Neither token cap caused
the stop. The controller checks the sprint/query ceiling before another senior
review, so the final uncertain report received no next review.

There were 396 model submissions (378 Haiku/local-lane, 18 Codex/cloud-lane),
790 effects, 11 reports and no final acceptance attempt. Four reports were
successful, including setup; seven were uncertain application assessments.
Here `verdict: uncertain` means insufficient coding evidence or unfinished
requirements. It does **not** mean remote execution remained uncertain: no
uncertain effects or unreleased inference reservations remained at capture.

The accepted integration branch `pi-dev` ended at
`bdc80f8c4b8ae4c6df9effbec32f66e5b97ac4ae`: scaffold, menu shell, simulation,
persistence module and test discovery. Gameplay remained private, most recently
at `b04f5a890cc528eb2f5e894221fb6bc84a925a80`. User-facing save/load was not
connected. The broad through-2020 objective was still unfinished.

## What the concurrency test establishes

Effective settings were `max_workers: 2`, local `max_inflight: 2`, cloud
`max_inflight: 1`, with 256,000 aggregate context reservation per endpoint.
The local lane actually used the remote Anthropic API. These are asynchronous
independent inference operations, not a benchmark of local GPU threads or
continuous-batching throughput.

| Sprint | Concurrent worker assignments | Time with two admitted local operations |
| --- | --- | ---: |
| 1 | Original interface and simulation foundation | 60.054 s |
| 2 | Canvas integration and persistence core | 170.390 s |
| 3–9 | One started assignment per sprint | 0 s |

The maximum admitted local concurrency was exactly two, with **230.444 seconds**
of overlap. Local admission waits had a 5 ms median, 37 ms p95 and 436 ms maximum
over all 378 reservations. Cloud maximum concurrency was one, as configured.
These timings measure OS reservation occupancy, not provider token/GPU execution.

Both parallel pairs had disjoint explicit write paths. History content-reference
process scopes matched their owning model operations throughout the export.
That checks metadata isolation, not the semantic absence of every possible
cross-process data leak; intended shared project memory is a separate input.

Verification correctly serialized integration/reconciliation/checks/assessment/
publication. In sprint 2, persistence queued for `verification/project` at
01:13:04.273948 UTC and acquired it at 01:13:10.966897, a **6.693 s** wait.
The canvas worker finished and released the resource. No deadlock is indicated.
The whole persistence `acquire` graph node took 8.485 s because it also preserved
the private delta; graph-node duration is not pure lock-wait duration.

The controller has only 59 recorded nodes: 30 ticks, 10 reviews, 9 dispatches
and 10 waits. This does not exhibit FIX-0069's repeated no-op dispatch loop.
Task branches were enabled, so the effective worker limit was not reduced to
one by the no-branches policy. Review/drain barriers and task readiness explain
the later single-worker execution; a free inference slot cannot invent work.

## What went wrong

### Shared test prerequisites were missing from the parallel plan (RUN13-01)

Sprint 2 assigned persistence to add tests that must run through existing Node
test discovery, while granting only `src/game/persistence.ts` and
`tests/persistence.test.ts`. The existing runner hardcoded the simulation test.
The other worker alone could edit `scripts/test.mjs`, but its canvas candidate
remained private. The persistence worker's independent tests passed 12/12, yet
the configured build did not run them, so its assessment stayed uncertain.

This is an agent task-graph/scope defect: disjoint writes did not imply
independent completion. The plan needed automatic discovery before dispatch,
or an explicit runner prerequisite/owner and dependency. The senior specialist
spent sprint 3 repairing discovery and the weak snapshot test. The OS correctly
did not borrow another worker's grant or publish its private runner change.

### Private source was repeatedly named but not materialized (RUN13-02)

Sprints 4, 5 and 6 asked for recovery from private commits while leaving
`assignment.resume_from: null`. Raw workers' normal file tools expose the current
workspace, not arbitrary private Git commits. Sprint 6 explicitly parked on
that mismatch. Sprints 7 and 8 then restarted from the accepted persistence
baseline; sprint 7 produced helpers without wiring the game.

Only sprint 9 used the existing mechanism correctly:
`resume_from: f332848746d16b35e7847b2c3f90b37e1afb59ec`. Its assessment confirms
that the previous canvas session survived into the repaired tree. Preservation
existed; the planner repeatedly failed to select it. This narrows the recurrence
of FIX-0040/FIX-0060: their provider tests prove explicit reuse, not that senior
plans use the field. The conflicting senior prompt sentences identified in
FIX-0068 also remain: an older sentence says uncertain work is provisional,
while the in-place amendment correctly says it stays private.

### Implementation and verification units did not converge (RUN13-03)

The configured check stayed `npm run build`. Its script eventually ran the Node
tests too, but Chromium verification was never a configured criterion. The
sprint-2 canvas objective made browser smoke testing conditional on tooling;
the assessment nevertheless retained an uncertain result for missing browser
evidence. Later assignments bundled source recovery, gameplay, observability,
browser infrastructure, stateful assertions and documentation into one task.

Sprint 5 did run Chromium: after a selector failure, the recorded command
reported five passing tests. Assessment correctly found that those tests covered
shell/selection/pause/resize/re-entry rather than walking, jumping, mining and
placement with state assertions. Sprints 5, 7 and 8 exhausted the two-repair
allowance. Sprint 9 implemented the observation hook and stronger mining test,
but remained uncertain for missing production-bundle/count evidence. Its task
explicitly deferred browser verification to a later step.

The result was a blocked gameplay dependency chain, repeated private work, and
no start of the pending save-interface assignment (later superseded). The agent
needs bounded tasks with attainable, explicit acceptance criteria and deliberate
source/evidence handoffs. This is not a reason to merge uncertain candidates or
weaken OS publication checks. Build success alone does not establish playability.

### Global command serialization dominates retained telemetry (RUN13-04)

Of the last 10,000 events, **6,960** concern acquiring/releasing
`shell/installation`. They cover about 23.19 minutes at the end, when only one
development worker was active. The preceding **24,313 events were pruned**,
including both parallel pairs. Durable reservation records still establish
inference overlap, but complete early shell contention history is unavailable.

`runtime/workspace.py:Workspaces.command` takes this installation-wide lock for
every trusted command; the coding repository's read-only Git tree/status work
uses that same path. Thus independent worktrees do not imply independent Git/
shell execution. The retained tail contains 1,740 release events, totaling about
76.3 s of ownership, most individually short. Event volume alone does not prove
this serialization caused material slowdown or event-loop starvation. Audit
contention, storage cost, lock granularity and diagnostic retention before
changing it; preserve mutual exclusion and termination guarantees.

### Response/tool inefficiency amplified recovery (RUN13-05)

There were **67 invalid worker replies**, often prefixed with XML-like tags or
`_action`, requiring another model turn. Twenty-three occurred in the first two
parallel sprints and 44 afterward; the maximum consecutive streak was two.
These are not evidence of concurrent history mixing. The application kept
rejecting malformed replies instead of executing their apparent JSON payloads.

There were also **21 8,000-token cutoffs**. All 21 retained output-recovery
outcomes point to successful attempts; they did not pause the run. FIX-0075 had
already raised the current UI/example limit to 32,000 before this analysis;
the saved run used the older 8,000 setting. Do not attribute that existing edit
to this task, or assume it eliminates large-response/grammar failures.

Three tool effects failed validation/preconditions (timeout 900 above schema
maximum 600, nonexistent pinned-base path, and non-unique patch). Eleven shell
observations had nonzero exit status, including ordinary compile/test failures.
One later script redirected to `$PW_SCRATCH/test.log` without setting the variable
in that invocation and attempted `/test.log`; shell environment setup does not
persist across calls. Preserve and act on these observations rather than treating
them as OS concurrency failures.

Context assistance worked: 66/396 preparations omitted optional history,
reducing an original peak of 144,478 bytes; the largest submitted representation
was 94,959 within the 96,000-byte allowance. No OS compaction occurred; it was
disabled. There was no unrecovered input-overflow recurrence.

### Repository summary overstates an empty worker's integration (RUN13-06)

The sprint-6 parked worker is shown as `merged: true`, although it produced no
new gameplay candidate: its tip equals the already accepted persistence head.
`RepositoryWorkspaces.summary` computes the flag from ancestry alone. This is
the FIX-0068 metadata issue again, now for a clean/no-new-commit worktree rather
than that investigation's dirty worktree. The ancestry fact is true; the label
does not establish task contribution or accepted gameplay. No bad merge is
shown. Distinguish these states in the agent's repository projection.

## Verification and limits of this investigation

Parsed the complete 165,672,779-byte supplied export, 790 effects, 1,920 artifacts
and 1,175 checkpoints. Verified every artifact's declared size and SHA-256.
Swept half-open admission intervals, inspected task/plan/report/assessment and
lock records, counted actual invalid-reply nodes and output recovery targets,
and checked history-reference ownership. Exact counting definitions and
measurements are in the linked evidence JSON; timestamps there are UTC.

The recorded agent-source digest is reproduced exactly by the current agent
modules after substituting the former 8,000 value for FIX-0075's 32,000 output
setting. This supports using current controller/repository/worker source to
explain the run; it is not a complete historical runtime-module hash match.

New focused regression run: **20 passed in 48.70 s**, using WSL Python:

```text
.venv-linux/bin/python -m pytest tests/test_ui.py tests/test_endpoints.py::test_two_requests_overlap_and_finishing_lane_does_not_exclude_ordinary tests/test_os.py::test_four_workers_failure_retains_commit_drains_and_replans tests/test_in_place_repository.py::test_default_real_repository_merges_concurrent_workers_before_completion -q
```

These are disposable local fixtures, not a replay of the user's workload or
proof that the open findings are fixed. No new concurrency regressions were
added. The supplied log's project tests/browser runs are historical observations,
not checks rerun here. No live provider, GPU benchmark, game playtest, run resume,
full suite, commit or push was performed.
