# P0 repairs and remaining work

<a id="p0-repairs-2026-10-29"></a>
## Current-version fixes — 29 October 2026

Current pins: **simple-os/6, agent-9-local-contracts/state 2.8**. The user authorized
all P0 repairs plus one local input/output pair and removal of OS cloud token caps.
Implementation and actual verification are in the P0 record (`development-docs/p0-repairs-2026-10-29.md`).
The pre-existing constants refactor and historical run evidence are preserved.

| Item | Status in this version |
| --- | --- |
| P0-01: local one-file contracts | Implemented: prompt requirements and agent validation at planning/allocation/task construction; tests/docs are explicit companions. |
| P0-02: configuration contradictions | Implemented: immutable nested tuning, environment proxy routing and inherited SQLite inspection timeouts. |
| P0-03: complexity-based cloud placement | Implemented: cloud_only_reason protects specialist work from ordinary allocation demotion. |
| P0-04: native output/budget semantics | Implemented: no cloud per-call token cap; completed local overages are distinct budget facts, with complete output retained and no smaller-response replay. |
| P0-05: passing check handoff | Implemented: source/environment/invocation-bound passing/failing receipts reach diagnosis and senior private review; scoped evidence-output paging is available. |
| Token settings special request | Implemented: local_token_limits is the single input/output pair; API requests, context/admission and restart configuration derive from it. Strata launch JSON can be synchronized before restart. |

The following remain **unimplemented follow-up tasks**, not completion claims:

| Priority / ID | Task and acceptance boundary |
| --- | --- |
| P1-06 | Finish retained, settled implementation separately from requesting another coding takeover. Assess reconciliation/assessment under original remaining resources; never refill allowances, bypass phases or replay completed effects. Verify a valid retained candidate can finish when authorized, otherwise preserve it with a precise blocker. |
| P1-07 | Reduce repeated diagnostic tool misuse. Source/evidence readers are bounded, but agents still need stronger paging examples, valid-path guidance and bounded correction for repeated oversized/unsupported requests. Verify the 4096-byte/path guards remain intact. |
| P1-08 | Qualify the actual local model on representative single-file contracts before another long campaign. Measure completed tasks, schema errors, repeated reads, steps/tokens per completion and source-backed integration. Preserve the full objective as milestones; fixture success alone is insufficient. |
| P1-09 | Archive campaign history before bounded journal pruning. Retention is tunable, but the default remains 10000 and old pruned events are unrecoverable. Add bounded archival/rotation and visible gaps; verify a campaign exceeding retention remains auditable. |
| P2-10 | Repair the Minecraft saved-world test helper to select the newly created save by stable ID, with deterministic duplicate-name/timestamp coverage. The preserved game/test source is unchanged by the P0 work. |
| P2-11 | Profile repeated prompts, prefix reuse and source rereads after convergence improves. Compare prompt processing with decode cost; no OS cache defect is established by current evidence. |

All older issue sections below remain historical evidence; later explicit fixes
supersede their former pending status. No old run is resumed or silently migrated.

28 October, 19:30 Minecraft continuation result (`docs/temporary/investigations/2026-10-28-minecraft-live-test-1930.md`):
the single real-local run ended paused at 06:46:33 Toronto on 29 October after
cloud recovery exhaustion. The reviewed partial output is uncommitted on pi-dev;
the full objective remains unmet. Final analysis, supported JSON export, browser
evidence and retained failures are in the user-requested Downloads directory linked
from the run record. See FIX-0160; earlier evidence and resource accounts are preserved.

Scheduled four-repair implementation (`development-docs/four-repairs-implementation-2026-10-28.md`)
implements agent source focus/diagnostic reads/search novelty, generic OS measurement
and caller priorities, agent-owned clean-output semantic handoff and replay-safe error
retirement. Fresh simple-os/5, agent-8/state 2.7 is required. No new live generation or
historical Resume is performed; final test/evidence limits are in the linked record.

Authorized model fallback and existing-browser repair (`development-docs/model-fallback-browser-repair-2026-10-28.md`)
implements agent-selected Terra/high/seven through the OS retry_model option and
trusted native continuation, initially with simple-os/4 state. Existing text-field
input leakage is repaired and actual Chromium checks retained. Its four-area plan
is now implemented in the scheduled batch above; old run evidence stays frozen.

Authorized reliability implementation (`development-docs/reliability-implementation-2026-10-27.md`)
tracks the OS/agent/qualification stages following FIX-0133. Changes require fresh
state; retained live evidence and the earlier cloud takeover remain preserved.

27/28 October scheduled Minecraft live result (`docs/temporary/investigations/2026-10-28-minecraft-live-test.md`):
four automatic cloud coding recoveries produced checked increments; the loading
recovery paused on provider model capacity. The partial browser foundation passes
44 host tests but lacks loading, physics and most requested gameplay. Actual
Chromium also finds text-field/game input leakage. No framework fix is claimed;
original resources, failed source and uncommitted delivery remain preserved.

Failure isolation and proposed repair order (`docs/temporary/investigations/2026-10-28-minecraft-failure-isolation.md`)
traces clean model failures bypassing cloud recovery, the effective 4096 output
target, prompt-only reply grammar, repeated local reads, conservative context
packing, a reproduced stale-error projection defect, incomplete diagnostic source,
browser-test gaps and the final effectful native-job stop. These are findings and
proposals; no implementation was changed by this follow-up.

Task/context/memory follow-up (`docs/temporary/investigations/2026-10-28-minecraft-failure-isolation.md#convergence-context-memory-followup`)
confirms all three read-only tasks lacked their assigned browser integrations.
Current OS replay reproduces a 49152-byte cap/48128-byte packing threshold, not a
fixed below-31K token limit; 29491 is an inactive compaction target. Current compact
worker-state probes confirm stale path-shaped tool errors and a second protocol
error-retirement defect for non-action replies. The user explicitly forbids fixes
in this investigation. Corrections to the earlier read counts and FileRead argument
claim are recorded in the follow-up; all implementation remains unchanged.
