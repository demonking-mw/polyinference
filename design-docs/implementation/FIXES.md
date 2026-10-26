# Implementation fix log

This append-only log covers new work on the runtime reliability branch. Earlier
cross-branch history was consulted; existing fix entries are not replaced here.

## FIX-0125 — Clean worker exceptions and bounded linked recovery (2026-10-25)

Clean `needs_review` workers previously paused the entire run, stayed in the active
set and could restart a finished graph at step zero. Parking now retains source,
fences settled execution and atomically queues an exception for senior review.
Explicit linked replacements share the original resource allowance and deadline;
unknown execution, exhausted allowances and conflicting source reuse do not retry.
Pending dependents require a validated replacement plan. Completion retains original
obligations until replacement reports are kept. JSON export includes recovery records.

The full schema constraints remain in prompts, rendered without redundant schema
display titles/whitespace so the added recovery schema does not crowd out previously
working module review packets. No objective, contract or authority pins are removed.

Implementation details and historical regression constraints: [worker recovery](WORKER_RECOVERY.md).

Validation: 27 focused recovery, diagnosis and inference-retry tests pass, plus lint,
compile and whitespace checks. The broader run passed 158 tests; its one failure
was a new conflict fixture incorrectly committing a scoped view. That fixture was
corrected to use integration and passes in the focused run. Earlier targeted module
planning and steering checks also passed (16 tests).

Additional independent verification: 28 recovery, diagnosis and inference-retry
tests pass on an immutable snapshot containing recovery alone. This includes the
publication-before-cleanup restart boundary: resume cleanup and detach completed
END graphs without new development calls or duplicate reports.

## FIX-0126 — OS execution observations and bounded agent stagnation (2026-10-25)

Repeated reads/checks could consume the full worker allowance without useful
evidence. The OS now exposes generic process/effect/future/admission observations
and optional named inspectors. The agent tracks tree/read/check novelty, emits an
uncertain-style application warning, and routes sustained stagnation to FIX-0125's
exception queue. Warning feedback costs no additional inference call and never
substitutes for assessment. Replay/restart preserves counters and event identities.
Read ranges allow documentation research to progress without requiring source edits.
UI/export records show observations, warnings, escalation and observer errors.

Historical protections retained: no fake validation tools (0cb6919), no early cached
delta sealing (FIX-0057/0089), no unknown-effect retry (FIX-0027/0117), physical attempt
charging (bb4f0df), bounded diagnosis (309713c), exact-tree acceptance (18cfb47) and
immutable module/dependency planning (191076c). Inspection failure cannot replace a
primary result. Native jobs are sampled between jobs rather than cancelled by time.

Defaults are eight idle decisions to warn and twelve to escalate, with observe/off
modes available. Live false-positive rates and effectiveness remain to be measured;
no preserved live run was replayed. Details: [progress monitoring](PROGRESS_MONITORING.md).

Final validation: all 174 tests pass, including HTTP UI/export, native broker paths,
restart/cleanup, source reuse, budgets, planning and progress-policy regressions.
Lint, byte compilation, JavaScript syntax and 22 local documentation links pass.
The wheel builds successfully and its extracted package imports the recovery and
progress interfaces. Build tools were isolated in `/tmp`; no live provider run or
deployment was performed.
