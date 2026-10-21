# Current design revisions — 2026-10-20

This records the accepted changes from the 17 October OS/agent baseline and the
reasons for them. Read it with the [runtime boundary](RUNTIME_BOUNDARY.md),
[deployment guide](RUNBOOK.md) and [settings reference](AGENT_SETTINGS.md).
[FIX-0072](../../development-docs/FIXES.md#fix-0072) records this documentation-only
alignment. No runtime behavior is changed by this document.

> **Edited 2026-10-20 because** later fixes, user-directed repository behavior
> and optional context services supersede parts of the original design. A dated
> marker explains a strong contradiction at the affected reading point. An
> observed implementation defect is not adopted as policy merely to make the
> documentation match the code.

## Authority and historical material

Use the current guides and the accepted revisions below for the implemented
profile. The original merged graph, its source fingerprints, contract examples,
17 October audit and static visual readers preserve their historical baseline.
They are not evidence that all of that baseline is implemented or still governs
publication, workspace layout, physical resources or optional services.

The OS provides generic execution and resource mechanisms. Applications select
workflow, context semantics, output grammar, Git policy and acceptance. The
bundled coding agent is one application; a general process may use inference,
records, artifacts and user messages without a Git repository or coding task.

## Accepted revisions

| ID | Earlier content | Current rule and reason | Evidence / owner |
| --- | --- | --- | --- |
| R01 | Coding grammar, task state and publication assumptions inside runtime paths. | Register typed capabilities, native protocols and application publication/reconciliation policies. A process can finish with artifacts or no output. This restores the intended boundary and lets future agents avoid coding conventions. | [FIX-0022](../../development-docs/FIXES.md#fix-0022), [FIX-0032](../../development-docs/FIXES.md#fix-0032); OS mechanisms, application semantics. |
| R02 | Partial development copies and a private authoritative Git store, followed by copy-back. | Default coding uses the actual project, full tracked task worktrees and separately bounded write grants. This makes work discoverable, preserves ordinary branch history and avoids incomplete build visibility. Legacy isolated copies remain explicit. More readable source does not grant more writes. | [FIX-0040](../../development-docs/FIXES.md#fix-0040), [in-place design](../../development-docs/in-place-repository-plan.md); coding agent chooses layout, OS attaches authorized roots. |
| R03 | Every normally assessed verdict advances the provisional head. | Default in-place coding integrates only successful verified candidates. Failed and uncertain candidates remain attributable private branches/reports for review and repair. With task branches disabled, non-successful edits remain uncommitted in the selected checkout. This prevents unverified work from being fast-forwarded into the user's integration checkout. Legacy isolated mode retains provisional publication for uncertain assessments. | [O04](IMPLEMENTATION.md), [replacement publication design](../../development-docs/in-place-repository-plan.md#worker-finish-and-integration-protocol), [worker finalization](../../src/polyinference/agent/worker.py); coding policy. |
| R04 | Every worker candidate has sole parent H. | In-place candidates retain captured integration H and, when different, the prior task tip as parents. Fast-forward only the exact checked candidate; there is no additional unchecked merge tree. This preserves real task ancestry and permits safe worktree-aware Git integration. Git and record publication remain separate consistency domains. | [FIX-0040](../../development-docs/FIXES.md#fix-0040), [repository implementation](../../src/polyinference/agent/repository.py); coding agent. |
| R05 | Missing project setup, a branch-selection error or failed dependency preparation stops useful work immediately. | The coding agent performs bounded setup correction, initializes the selected project and returns known preparation failures as observations for repair/recheck. Unknown termination, user constraints and data preservation still stop unsafe continuation. Other agents need none of this setup. | [FIX-0001](../../development-docs/FIXES.md#fix-0001)–[FIX-0003](../../development-docs/FIXES.md#fix-0003), [FIX-0017](../../development-docs/FIXES.md#fix-0017), [FIX-0019](../../development-docs/FIXES.md#fix-0019); coding agent. |
| R06 | Each unusable/transient inference failure reaches the application immediately. | The OS filters eligible known-ended failures with bounded backoff and separately journaled/charged attempts. Replay projects the effective retained result; original failures are immutable. This removes duplicated provider recovery from agents. Uncertain execution and native jobs with brokered effects cannot be blindly repeated. | [FIX-0044](../../development-docs/FIXES.md#fix-0044)–[FIX-0047](../../development-docs/FIXES.md#fix-0047); OS transport/accounting. |
| R07 | Agent-side history estimates and caller-owned cutoff adaptation are sufficient; no optional OS context service. | Measure the known final adapter representation. Offer optional whole-group packing and explicitly authorized lossy compaction, with immutable sources and visible receipts. OS smaller-response recovery is remeasured and uses new accounted intents. Agents retain canonical memory, block semantics, grammar and task decomposition. This repairs the recorded serialization mismatch and makes direct OS use practical. | [FIX-0049](../../development-docs/FIXES.md#fix-0049), [FIX-0053](../../development-docs/FIXES.md#fix-0053), [FIX-0058](../../development-docs/FIXES.md#fix-0058); [current service plan](../../development-docs/optional-os-context-management-proposal-2026-10-20.md). |
| R08 | Replacement reuse requires a candidate commit; interrupted pre-commit work may be reconstructed. | The coding agent preserves authorized interrupted source under explicit references and restores only on an explicit resume_from with grant/base checks. It neither copies unauthorized files nor treats retained work as accepted. This covers the pre-candidate handoff gap. | [FIX-0057](../../development-docs/FIXES.md#fix-0057), [FIX-0060](../../development-docs/FIXES.md#fix-0060); coding agent. |
| R09 | Source scans treat build output and tool housekeeping as source, or generations discard installed dependencies. | Declare generated outputs; tracked/granted source takes precedence. Retain compatible private dependency state by manifest/lock identity. Use invocation-private tool homes/caches outside source. This avoids false scope failures without making ignore files into grants. Tool homes are temporary per command; persistent process-owned tool configuration remains a separate follow-up. | [FIX-0031](../../development-docs/FIXES.md#fix-0031), [FIX-0034](../../development-docs/FIXES.md#fix-0034), [FIX-0035](../../development-docs/FIXES.md#fix-0035); OS file/evidence mechanisms, agent output/dependency choices. |
| R10 | Raw APIs and native agent jobs can be treated as equivalent model calls, or native limits can be assumed. | Native jobs require effective read-only permissions, explicit brokered tools and source-view checks. Known request bytes are conservative accounting, not an exact tokenizer or proof of hidden harness context. Native hard generation-token enforcement is unavailable; strict requests reject before submission. The opaque HTTP proxy remains read-only and owns no Codex login itself. | [FIX-0036](../../development-docs/FIXES.md#fix-0036), [FIX-0050](../../development-docs/FIXES.md#fix-0050), [FIX-0058](../../development-docs/FIXES.md#fix-0058), [FIX-0065](../../development-docs/FIXES.md#fix-0065); adapter capability reporting. |
| R11 | Physical RAM/VRAM admission, automatic retention, migration or a broader platform are current requirements. | O02 defers physical memory management. This version uses configured request/context/token/spend/output/artifact/workspace limits, a single coordinator and explicit archival. Git/SQLite history has no total physical quota; use host storage controls when needed. MCP lifecycle, distributed recovery and migration remain outside scope. This keeps the current OS implementable without claiming hardware or storage guarantees it lacks. | [Implementation scope decisions](IMPLEMENTATION.md), [retention limits](RUNBOOK.md#retention-and-export); OS/deployment boundary. |
| R12 | A one-worker/one-request test demonstrates the intended multi-request local-serving result. | UI defaults deliberately serialize worker/lane use for bring-up. Cloud-backed local-lane calls can test concurrent admission when both workers and slots are configured, but do not reproduce GPU batching, KV pressure or throughput. The server still owns token scheduling; fixture overlap is not a hardware benchmark. | [FIX-0048](../../development-docs/FIXES.md#fix-0048), [FIX-0061](../../development-docs/FIXES.md#fix-0061); deployment/test configuration. |
| R13 | An OS label implies protected hosted Python processes, preemptive drivers or transparent recovery of remote execution. | Trusted application code shares a cooperative host event loop; trusted shell has host privileges. Optional command/native sandboxes have their own limits. Any uncertain effect conservatively blocks new runtime dispatch until reconciliation; status/inspection remain available. This is a deliberate single-project safety boundary, not general isolation between arbitrary programs. The global shell gate and verification-before-shell order remain required. | [Runtime trust boundary](RUNTIME_BOUNDARY.md#bootstrap-and-the-capability-boundary), [recovery](RUNBOOK.md#recovery), [kernel guards](../../src/polyinference/runtime/kernel.py); OS scope and safety logic. |
| R14 | Settings are scattered or an additional shared agent library is required now. | The OS schema is in system_settings.py, coding defaults/UI choices are adjacent in agent/system_settings.py, and JSON uses one system block. A shared library is deferred until real reuse justifies a third surface. Direct OS access remains supported. | [FIX-0054](../../development-docs/FIXES.md#fix-0054), [FIX-0059](../../development-docs/FIXES.md#fix-0059), [complete settings reference](AGENT_SETTINGS.md); OS schema and agent preferences. |

## Open implementation gaps

These observations are **not accepted design revisions**. Documentation must not
remove the corresponding requirements merely to agree with current code.

| ID | Required behavior and current gap | Owning path |
| --- | --- | --- |
| U01 | A process's mandatory inference-location, destination and classification constraints must be honored or rejected. Current dispatch follows configured role_bindings without validating conflicting ProcessSpec data-policy declarations. | [kernel dispatch](../../src/polyinference/runtime/kernel.py), [process registration](../../src/polyinference/runtime/processes.py) |
| U02 | Unsupported hard allocation semantics must be rejected even when the caller omits a feature flag. Current process registration stores such schedules without that semantic rejection. Static routing remains a justified scope choice; silent acceptance does not. | [process registration](../../src/polyinference/runtime/processes.py) |
| U03 | Registered process limits must match actual execution authority. Current registration accepts a narrower ProcessSpec.limits, while operations require RuntimeConfig.limits and use that global envelope. A uniform-limit profile would be reasonable if incompatible specs were rejected at registration. | [operation validation](../../src/polyinference/runtime/kernel.py) |
| U04 | The original residency rule keeps paused workers counted until explicit safe hibernation/readmission. Current max_workers counts unfinished driver tasks; a stopped paused driver drops out without that transition. The difference is unresolved, not an approved automatic hibernation policy. | [driver accounting](../../src/polyinference/runtime/processes.py) |
| U05 — resolved | Generic output recovery preserves caller grammar after [FIX-0085](../../development-docs/FIXES.md#fix-0085). Earlier feedback requested visible JSON even from plain-text callers; generic feedback now requests smaller response content under the same declared protocol. Internal compaction retains its own legitimate JSON contract. | [output recovery](../../src/polyinference/runtime/model_retries.py) |

Until repaired, configuring consistent role bindings and one limits envelope is
a caller-side precaution, not proof of OS enforcement. Setting
inference_safety.output_recoveries to zero disables the generic smaller-response
attempts; it does not weaken incomplete-output rejection.

## Verification scope

The documentation alignment checked current source, fixes and regression
definitions. It changes no implementation, configuration, generated schema,
frozen graph or historical test result. The [I/O completion report](../../development-docs/io-safety-verification-2026-10-20.md)
records the existing 327-test full run and the later 73-case verification, their
ordering and limits; these are historical results, not checks rerun for this edit.
The four contract issues U01–U04 were reproduced in memory-only probes during
the preceding audit; U05 was subsequently resolved with protocol-preservation
regressions in FIX-0085. No live provider or
hardware benchmark is claimed.
