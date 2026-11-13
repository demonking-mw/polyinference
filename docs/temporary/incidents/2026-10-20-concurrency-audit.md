# OS concurrency audit

<a id="os-concurrency-audit"></a>
## CONC-01 — Audit OS concurrency for deadlocks and stalled progress — 2026-10-20

Status: open; double-check in the current version. Investigation/test follow-up,
not a claim that an OS deadlock has been reproduced. Context:
concurrency ownership (`development-docs/FIXES.md#fix-0067`) and
single-thread compatibility and agent capacity mismatch (`development-docs/FIXES.md#fix-0069`).

Check OS behavior with multiple workers and supported thread/executor arrangements,
including one event-loop thread and one local inference slot. Distinguish resident
worker count, endpoint max_inflight, aggregate context reservations and filesystem
executor capacity; multiple workers must remain usable when inference is serial.

- Exercise worker counts 1, 2 and 4 with one and multiple inference slots, mixed
  local/cloud work, and contention for context reservations. Check progress,
  admission fairness, starvation, busy loops and excessive scheduler/checkpoint work.
- Audit lock acquisition order and waits across inference admission,
  verification/project, shell/installation and the filesystem executor. Include
  native tool callbacks, compaction and retries; a waiting operation must not
  prevent the resource holder from completing and releasing capacity.
- Check cancellation, deadlines, review/drain, shutdown and restart while workers
  wait or hold resources. Confirm known-ended work releases capacity and wakes
  waiters; uncertain effects retain ownership until reconciliation without blind
  replay or duplicated effects.
- Check whether synchronous storage/artifact work or filesystem contention stalls
  the event loop under load. Separate slow but progressing work, queue timeout,
  livelock/starvation and genuine deadlock in diagnostics.

Use bounded deterministic fixtures with explicit progress/timeout assertions and
captured wait/ownership/reservation evidence. Cover general agents without Git or
coding records as well as the bundled coding agent. Existing concurrency tests
and earlier passes do not establish that this expanded audit has been completed.

The confirmed tick/dispatch capacity mismatch from FIX-0069 is corrected by
`development-docs/FIXES.md#fix-0083`: both predicates use the agent's effective worker_limit.
The wider OS audit remains open; this application correction does not establish
deadlock freedom. OS tests should not absorb Git policy. Preserve grants, budgets
and execution-certainty guarantees when addressing any findings.
