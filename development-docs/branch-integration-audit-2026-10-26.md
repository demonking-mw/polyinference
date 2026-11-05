# Reliability/simple OS integration audit — 2026-10-26

[Fix record](FIXES.md#fix-0127) · [Development records](README.md)

The user requested merging `fix/runtime-agent-reliability-20261024` (`cb2fae5`)
into `codex/simple-os-v1` (`26da7f7`), then explicitly asked whether their
implementations/fixes conflict. They share `5631c51`, not a parent/child history.
The merge preview found 21 conflicted files. The important conflicts are behavioral,
so neither whole-file side nor a preferred merge strategy is sufficient.

| Overlap | Conflict and integration decision | Verification route |
| --- | --- | --- |
| Runtime layout and authority | Reliability extended a monolithic adapter; simple OS moved dispatch into KernelRuntime and registered capabilities/protocols. Port extensions into the kernel and keep the adapter alias, generic RuntimeConfig, permission guards, native immutable input views and actual message roles. | Capability boundary, general runtime, native and endpoint suites. |
| Response/transport retries | Stacking malformed-response retries with transport retries refilled the response allowance (six calls instead of two). Keep transport/output recovery guards, share response-repair receipts across transport roots, block transport refill after response exhaustion, and preserve physical-call accounting. | Inference retries plus the mixed transport/response regression in test_branch_integration.py. |
| Published-worker cleanup | The older controller exception path changed a published task to interrupted and released its verification ownership. Preserve the report/attempt and permit; only resume a settled saved release checkpoint, never development at step zero. | Published-cleanup restart regression in test_exception_recovery.py. |
| Retained source on attached worktrees | The old handoff materializer removes files absent from its source tree, including .git and ignored dependencies on an attached root. Dispatch through the provider's materialize_view, preserving control files, environments and the original source checkout. | New attached handoff/replay regression in test_branch_integration.py; in-place repository/source tests. |
| Context preparation and resume | Anonymous physical-attempt identities disconnected compaction and original-operation receipts. Keep the first dispatch's actual effect identity; retain indexed physical receipts for later response repairs and authorize only durable OS-issued compaction under them. Generic processes keep the existing transport path. | New compaction/validation regression; context, lifecycle and resume suites. |
| Senior review size | Concatenating both instruction sets exhausted existing 24k review packets, even after optional previews were omitted. Consolidate duplicate prose while retaining source/grant/objective/schema pins and the same limits; do not raise defaults or remove mandatory input. | Module-planning and bounded retrieval/completion tests. |
| Check policy and completion | Retain separate prerequisite/task/acceptance checks, shared-check preparation and exact pinned runner/source previews alongside new semantic completion evidence. Private code_location still controls what can be kept; no semantic claim publishes private work. | In-place shared-check and semantic-review suites. |
| Setup retirement | Preserve the earlier setup interruption flow. The module planner may retire a settled interrupted task lacking an exception packet; the controller checks that effects and permits have settled first. Development exceptions still need explicit linked dispositions. | Long-reason setup transition regressions and module-plan tests. |
| Prerequisite diagnostics | New independent review checks leave their own preparation history. Completed checking-workspace failures remain retained, while global active preparation issues exclude completed reviews; current worker-scoped failures stay visible and retryable. | Failed dependency-preparation repair regression. |
| Source reuse and planning | Keep prior private/interrupted source offers and immutable started-task accounting. New fenced exceptions select one validated development delta and share original grants/accounts/deadlines. Interface versions and started assignments stay pinned. | Recovery, module planning, allocation and retained-source tests. |
| Read paging, cancellation and source scans | Retain next_offset alongside bounded read ranges. Explicit cancellation uses the existing cancelled lifecycle, separately from semantic exceptions. .npm is excluded only from initial non-Git import; cache-named source writes remain visible to scope auditing. The incoming cache fixture uses the existing isolated tool environment instead of requiring a blanket source exclusion. | OS paging/cancellation, runtime cache fixtures and tool-environment regressions. |
| Recovery checkpoints and physical attempts | A prepared recovery can stop at the newly inserted progress node. Unknown physical attempts retain their actual submission state and capacity through restart. An older completed root response cannot settle a later unknown repair attempt; that repair needs explicit provider/host reconciliation. Original-query recovery updates its physical receipt. Interruption while waiting for a replacement preserves completed attempt evidence and the accepted replacement. | Incident recovery, restart/capacity, durable replacement replay, and both new response-recovery regressions. |
| UI/export and provider settings | Extend shared schema-v2 Save/export rather than reviving the old exporter/UI. Preserve OS/message views, records/artifacts/checkpoints and add attempt, diagnosis, exception, interface and progress projections. Forward temperature through prepared streaming payloads and native reasoning effort without replacing native base instructions. | Snapshot/UI/export, HTTP/native and endpoint suites. |

The new native terminal-failure fixture explicitly requests one transport retry;
its assertion no longer depends on the other branch's different default policy.
No production retry allowance was reduced for that fixture.

Implementation status and final test results are recorded in FIX-0127. Verification
uses disposable repositories and mocked providers;
no live provider, retained application run, or other worktree is changed.
Known U01–U04 design gaps and the separate execution-profile branch are outside
this merge; historical evidence is retained rather than relabeled as newly tested.

## Verification record

The complete initial merged-tree run accounted for **590 cases**: **566 passed,
22 failed, 2 skipped** in 1694.32 seconds. All 118 source/test input hashes were
unchanged by the run. Failed results are retained; later corrections are separate
focused verification, not an all-green claim for this initial run.

Five failures also reproduced on untouched simple-OS commit `26da7f7`:

- `test_total_deadline_does_not_reset`: its 25 ms allowance expires before dispatch.
- `test_pacing_holds_admission_refills_independently_and_exceeds_network_timeout`:
  a fixed 150 ms observation occurs before provider entry.
- `test_generic_resume_retains_uncertainty_when_provider_lookup_times_out`:
  the 100 ms original deadline expires before lookup; the existing diagnostic differs.
- Both capacities of `test_simulated_worker_requests_overlap_to_capacity_and_refill_without_pairing`:
  the mock still expects a 32000 output request while the configured target is 4096.

These baseline fixtures/production timing defaults remain unchanged. The checks
are offline and do not establish live provider readiness or hardware performance.
The two skips require an unavailable Node executable in the normal test PATH;
30 frontend checks also passed independently with the available bundled Node.

The final focused results are recorded in [FIX-0127](FIXES.md#fix-0127). Additional
fixtures were updated to use generic OS response schemas where no coding grammar
is intended, to provide the new semantic completion contract, and to inspect
actual prepared transport input while preserving canonical history and the final
current-phase user request. Original behavioral assertions remain enforced.

| Verification | Result |
| --- | --- |
| Initial complete integrated run | 566 passed, 22 failed, 2 skipped (590 cases). |
| Original integration failures after correction | All 17 passed in the corrected-case run. |
| Final affected retry/recovery/progress/runtime/cache/source run | 78 passed, 1 skipped, 1 known baseline case deselected (245.71 seconds). |
| Critical restart and operator recovery | 6 passed. |
| Latest result per case across full and focused runs | 585 passed, 5 unchanged baseline failures, 2 skips (592 distinct cases). |
| Bundled Node frontend run | 30 passed; JavaScript syntax check passed. |
| Source and documentation | Ruff, Python compilation, documentation generation/check (297 files / 127 leaves), and whitespace checks passed. |
| Final package | Offline wheel built; new modules/UI asset, current retry source and runtime imports verified. |

The distinct-case total includes two new response-recovery regressions added after
the initial full run. Intermediate reruns exposed replacement-window receipt loss
and incompatible cache fixtures; both are corrected and pass in the final affected
run. The table combines separate runs; it does not claim one full-suite pass on the
final tree. No implementation/test edits address the five confirmed baseline failures.

Raw response-repair attempts with uncertain later execution require explicit
reconciliation. Generic original-query status recovery retains its existing path.
Fresh integrated program/state pins are required; historical runs use their pinned
source. No live provider, historical workload, other worktree or issue backlog was changed.
