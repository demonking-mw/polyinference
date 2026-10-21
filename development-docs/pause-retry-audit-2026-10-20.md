# Pause and retry audit — 2026-10-20

Status: resumed review and full local verification complete. See
[FIX-0047](FIXES.md#fix-0047) for final results and
[the handoff's resumption record](HANDOFF-2026-10-20.md#resumed-work--2026-10-20).
Related history: [FIX-0043](FIXES.md#fix-0043) through [FIX-0047](FIXES.md#fix-0047).

## Scope

Reviewed all explicit paused-state writes in the runtime, coding agent and CLI/UI
projections, and the exception boundaries that turn lower-level errors into a
process/run pause. The inventory groups reachable causes by effect guarantees;
unexpected exceptions are included because the driver/controller can pause on any
unhandled exception. Parked OS processes and paused application runs are distinct.

## Gaps found and changes made

| Gap | Implementation | Relationship to earlier work |
| --- | --- | --- |
| Empty, blank, thinking-only, malformed JSON/response shape or unexpected model output immediately escalated and lost diagnostics. | Normalize failure facts/usage without hidden reasoning; allow one safe OS retry. | FIX-0043 identified it; FIX-0024 covered HTTP rejections; FIX-0030 covered token cutoffs only. |
| HTTP 429/5xx were marked retryable but had no automatic retry/backoff. | New durable attempt, exponential delay, Retry-After, wait/deadline limits. | Completes missing recovery after FIX-0024/FIX-0026 without reintroducing endless replacement loops. |
| All HTTP disconnects were uncertain, even connection establishment/pool acquisition failures before submission. | Known-unsubmitted connect/connect-timeout/pool-timeout retries; zero inference charge for that unsubmitted attempt. | Refines FIX-0027 certainty rules; a submitted read/write disconnect still cannot be retried. |
| A briefly full inference queue immediately failed. | Known-unsubmitted resource rejection with the same bounded OS retry. | Preserves FIX-0026 admission/deadline limits; no capacity increase. |
| Confirmed-stopped native failures before tools could stop on one transient terminal/envelope issue. | Retry before any brokered effect; inspect native/source views on known failures too. | Preserves FIX-0028 telemetry, FIX-0032 generic grants/protocols and FIX-0036 native authority. Failed permissions, native cancellation and unbrokered mutations remain stops. |
| The permanent-failure circuit grouped unrelated request inputs together. | Include the pinned intent fingerprint; a successful explicit correction clears the repaired input's counter. | Addresses the open fault-scope finding in FIX-0024/FIX-0041 while preserving FIX-0026 identical-failure containment and FIX-0027 explicit recovery. |

## Pause inventory and decisions

| Cause / owning code | Decision and retry policy |
| --- | --- |
| Unusable raw response; `runtime/inference.py` to worker/controller | Fixed: one extra safe OS attempt by default, then escalation with retained diagnostics. Rejected content never executes. |
| Rate limit / temporary service rejection | Fixed: bounded backoff. A provider wait exceeding the configured wait allowance or remaining deadline escalates rather than resubmitting early. |
| Connect/client-pool failure before submission | Fixed: retry as unsubmitted; submitted read/write failures remain uncertain. |
| Inference admission queue full | Fixed: bounded retry. Queue deadline expiry remains a hard boundary. |
| Native terminal/envelope failure before callbacks | Fixed: one retry after confirmed termination, with original authority and view checks. |
| Native failure after any brokered callback | Keep stop: restarting the job may repeat tools. Caller continuation/reconciliation must decide next work. |
| Native permission handshake failure / unbrokered mutation | Keep stop: no retry may authorize execution or accept mutated input. |
| HTTP 400/401/403, missing credentials, unsupported protocol/feature | Keep correction/escalation: identical inputs do not fix credentials, schemas or grants. Repeated identical invalid inputs remain bounded; corrected unrelated inputs are independent. |
| Submitted disconnect/timeout, native exit without terminal turn, uncompleted oversized transport | Keep uncertainty, capacity and ownership until reconciliation. A lost connection is not proof of termination. |
| Output-token cutoff | Preserve FIX-0030's bounded agent adaptation: smaller complete response, linked intent, no partial execution. The OS does not repeat an unchanged request for a known output-size mismatch. Transient retry followed by cutoff composes with this strategy. |
| Invalid coding action/proposal, missing mandatory phase | Existing worker feedback and bounded senior correction remain. Exhausted/invalid reconciliation or assessment must not manufacture success. The OS does not interpret coding grammar. |
| Required pinned context larger than backend/input limit | Keep rejection. Caller must build an authorized smaller request; never silently remove user constraints. |
| Token/spend/call/step/time/storage limits or finishing reserve | Keep stop. Every retry charges the same budgets, creates a new reservation and preserves finishing capacity. |
| Cancellation, stopped process, stale owner, unknown principal, runtime shutdown | Keep rejection. Retry waits recheck cancellation/shutdown before dispatch; settled replay is still available after termination. |
| Stopped driver / unexpected application or graph exception | Keep pause: an arbitrary driver may already have mutated data. Classified model failures now get filtered earlier. Other already-started workers still drain when effects are known (FIX-0026). |
| Dirty project, active Git operation, changed branch/HEAD/index or integration conflict | Keep preservation guards. Recoverable startup branch/policy choices already receive three correction attempts (FIX-0001/FIX-0002). Never reset or blindly merge over user changes. |
| Known failed dependency preparation | Already reaches the engineer as evidence and retries on later checks (FIX-0003). Unknown termination still stops mutation. |
| File/tool failure, denied scope/check, stale generation/digest, schema/effect mismatch | Ordinary tool outcomes reach the agent. Critical check/commit/publication failures may escalate. Correct intent/grants/view; do not retry stale/forbidden mutations unchanged. |
| Check nonzero exit, timeout, missing executable or disabled check backend | Retain adverse evidence; existing repair/recheck/review decides next work. Do not rerun until one passes and treat that as proof. |
| Shell timeout, source scope violation, generated/source confusion | Known terminated commands return observations; attached scope failures preserve/block files. Unknown descendants retain ownership. No generic replay of mutating commands. FIX-0031/FIX-0034/FIX-0035 remain intact. |
| Verification/shell/filesystem lease deadline or retained ownership | Keep bounded wait/exclusion. A deadline cannot authorize stealing a lease. |
| Commit/report provenance rejection, stale head, publication CAS or missing receipt | Keep guard and require fresh evidence. Durable receipts already replay/reconcile; Git integration followed by failed report publication remains uncertain (FIX-0040). |
| Storage/record/artifact error | Keep transactional/CAS/immutable guarantees. SQLite already bounds lock waiting. A generic retry cannot establish whether a transaction or external effect committed. |
| Acceptance check failure or steering/head changed during acceptance | Preserve acceptance invalidation and return to review where supported. No retry may fake passing evidence or unchanged input. |
| Explicit needs-review / parked worker / interrupted assessment | Preserve application review. A parked OS process is not automatically a failed application run. |
| Empty plan, unchanged review fingerprint, no runnable work, exhausted sprint/query allowance | Keep bounded no-progress stops (FIX-0026). Rewritten narrative is not new evidence; real repair/steering may reactivate work. |
| Output delivery conflict/partial delivery or changed accepted root | Keep preservation and explicit recovery; use existing intents/receipts, never overwrite external edits (FIX-0021/FIX-0027). |
| Notification/terminal/snapshot/reporting error | Preserve observer isolation and durable notification replay (FIX-0029/FIX-0038). Reporting cannot replace the original outcome; durable storage errors follow the storage rule. |
| Program/configuration pin mismatch, coordinator conflict, incompatible restart | Keep rejection. Require compatible implementation/new state; no silent migration or takeover. |

## Implemented retry contract

`runtime/model_retries.py` runs at `KernelRuntime.execute`, on either binding,
without coding records or Git. Defaults: one extra safe attempt, 100 ms initial
backoff, 60-second maximum permitted wait; one to three retries are configurable.
Delay grows exponentially and never undercuts Retry-After. Application response
adaptation retains its separate `max_model_recoveries` allowance.

Each retry has a new OS-issued request, operation/logical identity, budget and
reservation. Context, routing, deadline, scope, limits and authority are unchanged.
Internal retry requests require `runtime/model-retries/1`. Original per-attempt
results remain immutable. Public `execute(original)` projects the effective
retained retry result; replay follows the same chain without another submission.
Raw individual results remain inspectable under `effect/<operation_id>`.

`model-retry/<root>/<attempt>` stores the intent and absolute backoff time before
submission. `model-retry-outcome/<root>` records the effective result and why
retry succeeded, was suppressed or exhausted its allowance. An unchanged replay
does not rewrite that status. Concurrent callers join one sequence. Shutdown
cancels pending waits while existing submitted-effect uncertainty stays intact.

The new configuration fields change the pinned configuration: use fresh run
state, with no migration/resume of historical runs. Core wire schemas and frozen
proposal examples are unchanged. Current boundary/deployment notes describe the
explicitly requested implementation behavior, not a broader design rewrite.

## Verification at handoff

Final focused command: **39 passed** (36 new retry cases, the two existing
known/unknown native cases, and permanent-failure explicit recovery).

The first full suite reported **280 passed, two skipped, one failed**. Its sole
failure was the old assertion that a known-stopped effect-free native failure
must submit exactly once. That expectation now allows the intended second
attempt while unknown execution still allows only one. During the correction a
different matching assertion was briefly edited; it was restored before final
focused verification. The second full run was stopped at the user's request;
there is no final all-green full-suite claim. Rerun the full suite tomorrow.

All tests use local fixtures. No live provider, original paused run or real game
implementation was executed. The handoff lists the final checks and review work.

## Resumed review — 2026-10-20

The review found one composition gap in the first implementation: an OS retry of
an already-authorized adaptive recovery also consumed a caller recovery slot.
[FIX-0047](FIXES.md#fix-0047) records the reproduced failure and correction.
Authorization now distinguishes the retained OS-issued intent from a fresh
application recovery. Tests cover both orderings of OS retry/output adaptation,
replay, one/two caller recovery slots, and rejection of unissued retry metadata.
The pause decisions above remain unchanged; no additional authority or budget
exception was introduced.

The pre-correction resumed full run passed 289 tests with two Linux environment
skips. Final post-correction full run: **292 passed, two skipped in 292.39 seconds**
with `.venv-linux/bin/python -m pytest -q -rs`. All **14 browser-script checks**
passed separately on Windows Node. Lint passed for the changed implementation
and test files. This supersedes the pending verification status recorded at the
original handoff, preserving that earlier record above.

The Linux frontend wrapper skips because `/usr/bin/node` is v12.22.9 and needs
Node 18+; its actual script suite was exercised successfully on Windows. The other
skip needs a supported native Linux Node/npm pair for npm housekeeping. That
environment-specific reproduction remains a material coverage limit. No live
provider, historical run, native npm installation or game acceptance was performed.
