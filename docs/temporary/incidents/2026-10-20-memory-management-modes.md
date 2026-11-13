# Memory management proposals

<a id="memory-management-modes"></a>
## MEM-02 — OS automatic memory mode and explicit agent memory management — 2026-10-20

Status: open for implementation in the current version. User-requested planning
only; no implementation or configuration changed by this entry. Deliver both
work items below. Context: memory ownership (`docs/temporary/investigations/2026-10-20-memory-implementation.md`),
saved-run measurements (`docs/temporary/investigations/2026-10-20-memory-records.md`),
`development-docs/FIXES.md#fix-0066` and `development-docs/FIXES.md#fix-0070`.

### Problem and existing baseline

Long worker trajectories can overwhelm the input allowance even while shared
memory stays small. The historical audit found a local input rejection with
96,529 bytes against a 96,000-byte allowance; shared memory contributed only
1,681 bytes. A newer run needed OS history omission on 32/181 preparations,
including 31 originally oversized requests. Its largest input fell from 156,320
to 90,697 bytes. It performed zero OS summary compactions; compaction was disabled.
Agent-written summaries do not count as OS compaction in these measurements.

Existing ContextService preparation, optional-group omission, explicitly eligible
derived summaries and receipts are foundations to extend. The coding defaults
enable auto_deal_context and leave auto_compaction off. This issue requests a
complete usable management mode and explicit memory operations, not a claim that
the existing compaction machinery is absent or already solves memory lifecycle.

Here memory means explicit agent memory, conversation/tool history and their
active model-input views. The C analogy concerns ownership, allocation, handles
and lifetime; it does not request a native heap or physical RAM/VRAM scheduler.

### 1. Implement OS automatic memory management mode

Provide a directly selectable, opt-in automatic mode. The agent declares required
inputs and transformation permissions; the OS maintains a bounded active input
view using generic memory/context mechanisms.

- Cover history as well as explicitly eligible memory blocks. Select/page the
  active set, omit eligible complete groups and invoke bounded summarization
  when the selected policy permits it. Protect exact inputs and complete tool
  relationships. Do not merely turn on a flag and assume every source may be lost.
- Expose trigger/target pressure, headroom and compaction budgets together with
  effective process policy and request overrides. Build on existing settings;
  choose final API/configuration names during implementation. Preserve a manual
  mode with automatic transformations disabled, plus hybrid per-block control.
- Return durable handles/references to managed views and derived summaries so
  later requests can reuse them, append new material and retire old active
  entries. Avoid requiring every call to rebuild an ever-growing full transcript
  and repeatedly discard the same prefix. Reuse only compatible source versions,
  trust, process authority and policy; restart/replay must not repeat settled calls.
- Canonical facts and agent memory remain agent-owned. The OS manages the active
  representation and retains original/source provenance. Its summaries must not
  silently become canonical updates or acquire instruction authority.
- Measure the final adapter representation. If protected input still cannot fit,
  return bounded pressure/failure evidence to the agent for paging, consolidation
  or task decomposition. Preserve limits, budgets, grants, routing and uncertain
  execution handling. Report unsupported adapter operations explicitly.
- Record original/prepared size, selected/released/omitted entries, source/summary
  references, reasons and cost. Count OS history omission, OS model compaction
  and agent canonical-memory updates separately. Reuse MEM-01's inspection design.

### 2. Implement explicit agent-side memory management support

Give agent programs an intentional manual interface, analogous to explicit memory
management in C. The application chooses what to remember and when to release it;
the OS provides generic scoped storage, versioned handles and lifecycle guarantees.
Expose model-callable tools only when the application grants them. Non-coding
agents must be able to use the same mechanisms without coding records or Git.

| C-inspired operation | Agent-memory behavior to support |
| --- | --- |
| Allocate | Create a memory item/region and obtain a stable scoped handle with an owner, size/budget and lifetime. |
| Read / write / resize | Read referenced content and explicitly replace, append or consolidate it through versioned updates with source provenance. This need not promise in-place mutation. |
| Reference / select / page | Choose which items or excerpts enter a particular ContextView; retain large source/history elsewhere and retrieve it by handle when needed. |
| Pin / unpin | Declare exact required content, required-but-compactable representation, or optional material; enforce these declarations when preparing a request. |
| Free / release | Remove an item or region from the active working set and future automatic inclusion, including at scope end; retain evidence still referenced by operations, checkpoints or reports. |

Specify ownership transfer/sharing, process/task/run lifetimes, expected-version
checks, invalid/stale/released-handle errors and accounting. A released handle
must not silently read unrelated content or reactivate old memory. Distinguish
releasing an active reference from physically deleting immutable artifacts and
records; this feature must not erase evidence needed for replay or recovery.
Do not promise general artifact garbage collection through an active-set release.

Wire this into the bundled coding agent: let its controller/workers deliberately
select, consolidate, pin and release history/notes rather than always submitting
the whole trajectory plus every uncovered note. The senior owns canonical
summary meaning and coverage; adopting a derived OS summary is an explicit agent
update. Preserve authoritative objectives/steering separately. Manual agents
must be able to manage their input without enabling automatic compaction.

### Ownership, integration and acceptance

Keep this version to OS services and agent policy. A shared agent library remains
deferred. MEM-01 is the read-only inspector and does not itself implement either
work item here. Automatic, manual and hybrid modes should share handles, storage
and execution guards rather than introducing incompatible memory stores.

Required checks when implementing:

- Run long deterministic histories through automatic mode on supported local/cloud
  raw/native paths. Verify bounds, whole pairs, protected input, source retention,
  bounded compaction cost and truthful unsupported/failure outcomes.
- Demonstrate multi-request managed-view reuse and restart/replay without duplicate
  summary calls, duplicated entries or silent restoration of released material.
- Exercise explicit allocation, versioned updates, selection/paging, pinning,
  consolidation and release in a non-coding fixture and the coding agent. Verify
  released entries leave later input, shared/pinned evidence remains available,
  and invalid ownership/stale/released references fail deterministically.
- Cover manual mode with zero automatic interventions and hybrid mode with exact
  per-item transformation permissions. Agent-directed changes remain possible.
- Retain counters and before/after evidence sufficient to distinguish OS omission,
  OS summary calls/cache reuse, agent consolidation and explicit releases. Reuse
  the saved-run pressure patterns as regression inputs without treating their
  historical outcomes as tests of the new feature.

This entry records requested work and acceptance criteria only. No new memory
API, mode, default change, tool, lifecycle behavior or passing regression is
claimed as implemented by this documentation task.
