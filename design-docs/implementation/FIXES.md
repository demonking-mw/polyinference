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
