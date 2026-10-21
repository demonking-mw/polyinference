# Optional OS context handling and memory compaction

20 October 2026. Historical proposal; implementation status is now recorded in
[FIX-0058](FIXES.md#fix-0058) and the
[OS settings reference](../design-docs/simplified-os/AGENT_SETTINGS.md). The
original investigation/design-only statements below describe the pre-change
baseline and are preserved as history.

Design only at the time of writing, following the user's request for agent-controlled
automatic context handling and optional automatic memory compaction. No
implementation, configuration or tests changed.

This explicitly refines the service placement in
[FIX-0052's responsibility proposal](agent-os-overflow-responsibility-proposal-2026-10-20.md).
The current-stage system has two owners: OS and agent. The OS should offer a
generic optional context-management service, enabled directly by caller policy;
the kernel remains the final resource/effect enforcer. A shared agent library
is deferred to the [next iteration backlog](next-iteration.md#shared-agent-support-library)
and is not part of this fix or a dependency for its API.

## Current-stage fix ownership

The following split supersedes the earlier three-layer proposal. All items are
planned, not implemented by this documentation task.

| ID | Owner | Planned change |
| --- | --- | --- |
| OS-1 | OS | Prepare and measure the exact final adapter request, expose effective enforcement capabilities, and enforce input/output/response-byte bounds consistently on local and cloud bindings. |
| OS-2 | OS | Classify output cutoffs and unverified completion, withhold incomplete actionable results, preserve diagnostics/effects and provide bounded safe response recovery under the declared protocol. Unknown termination requires reconciliation. |
| OS-3 | OS | Expose per-process defaults and per-request `auto_deal_context` policy; manual mode reports pressure/overflow without rewriting, while automatic mode can pack explicitly eligible groups. |
| OS-4 | OS | Offer separately optional automatic compaction, with trigger/target, budgets, fitting compaction calls, source/trust lineage and immutable original memory/artifacts. Manual, automatic and hybrid agent use must all work. |
| OS-5 | OS | Always report original/final sizes, intervention receipts and retained context references. Preserve ordinary records/artifacts/checkpoints and effect ownership without interpreting Git or coding acceptance. |
| OS-6 | OS | Retain and expose concrete scope-violation facts, including offending paths, without broadening grants or overwriting unexpected attached-directory files. |
| AGENT-1 | Agent | Separate instructions, memory, artifact excerpts and history into blocks; declare which are verbatim, compactable or omittable, and choose the assistance policy explicitly. |
| AGENT-2 | Agent | Own canonical memory updates, semantic summarization, paging/task decomposition and authorized binding choices when protected inputs cannot fit or assistance is disabled/exhausted. Handle typed failures in the agent driver. |
| AGENT-3 | Agent | Declare generated test outputs or use permitted scratch before commands run. Preserve real test exit status and inspect reported failures; do not infer acceptance from a successful pipeline alone. |
| AGENT-4 | Agent | Reuse interrupted coding work through explicit preserved artifacts/deltas and repository-aware handoff, including work that has not reached a candidate commit. Use generic OS retention, without making Git an OS prerequisite. |
| AGENT-5 | Agent | Define meaningful response units and task acceptance, verify complete evidence/documents, and finish reconciliation/publication before presenting a candidate as integrated working output. |

The optional context service is an OS facility, not an additional mandatory
architectural layer. Agents use its public policy and operation interfaces
directly. Agent-owned implementation remains in the coding application for this
stage; a reusable agent library is future work only.

## Current implementation and responsibility

There is no general implemented OS automatic memory-compaction service or
`auto_deal_context` setting. The search scope was `src/polyinference`, including
runtime, configuration, public ports and the context/memory contracts.

[AgentServices.context](../src/polyinference/agent/services.py) performs bounded
optional-history selection. [AgentServices.memory_view](../src/polyinference/agent/services.py)
combines a senior-written working summary with uncovered notes.
[controller.py](../src/polyinference/agent/controller.py) updates `memory/working`
from `proposal.memory_update` and records the note references it covers. These
are coding-agent behaviors, not enforced OS compaction. The `MemorySnapshot`
contract is not evidence of an active automatic compactor.

An agent owns the prompt, memory and artifact selection it supplies, so repeatedly
oversized inputs can reveal an agent-design defect. The OS still owns truthful
limits, correct final sizing, enforcement and classified failure delivery.
Automatic assistance should not conceal poor context construction from authors.

## Small kernel, optional OS service

Keep prepared-request measurement, authority, endpoint capabilities, byte/token
bounds, completion facts, durable identities and effect certainty in the kernel/
adapters. Put optional packing and compaction orchestration in an OS-provided
service operating through those same mechanisms. It should have no knowledge of
Git, coding tasks, business acceptance or a particular agent framework.

The service accepts opaque context blocks and explicit allowed transformations.
Model-based summaries are ordinary accounted inference operations with no tool
side effects, inherited data policy and bounded budgets. They do not get an
implicit cloud route or extra authority. This provides OS assistance directly
while preserving a small compulsory execution contract.

## Agent-facing settings and modes

Proposed settings, not existing configuration fields:

- `auto_deal_context`: permit automatic repair of submitted context before the
  intended inference operation. With it disabled, return size/pressure facts and
  reject an oversized request unchanged, without an automatic rewrite.
- `auto_compaction`: separately permit model-based summarization of eligible
  blocks. Keeping this off allows deterministic omission/packing without paying
  for or accepting lossy summaries.
- Trigger utilization, target utilization, compaction call/token/time limits,
  permitted inference bindings and per-block transformation permissions.

Support process defaults with explicit per-request overrides, recorded in the
effective request policy and constrained by process grants. A lower-trust model
tool invocation cannot grant itself a new inference location or disable hard
limits. The core default should perform no implicit lossy transformations; an
explicit automatic preset makes onboarding simple.

| Agent mode | Expected behavior |
| --- | --- |
| Manual | Agent constructs and manages context; automatic rewriting and compaction are off. OS measures, reports pressure and enforces the cap. The agent may still invoke the compaction service explicitly. |
| Automatic packing | Agent opts into OS packing of eligible whole groups; automatic model summaries remain off. |
| Automatic packing and compaction | Agent authorizes both, with block eligibility and a budget. OS prepares a fitting derived context when possible. |
| Hybrid | Agent supplies its own memory summaries for some blocks and permits OS packing/compaction for selected other blocks, or enables assistance only on particular calls. |

No setting disables output-cutoff rejection, scope checks, budget enforcement or
uncertain-execution protection. A manual-context agent still receives all OS
execution safety guarantees.

## Context blocks and memory ownership

The author must expose boundaries rather than submitting every input as a single
indivisible pinned JSON blob. Blocks can declare:

- **Verbatim/pinned:** include unchanged; instructions, constraints and any
  exact evidence the caller protects are never automatically summarized or cut.
- **Compactable:** the caller explicitly allows a derived summary to represent
  the block. Some such blocks may be required to remain represented, which is
  different from permission to omit them entirely.
- **Omittable:** the caller allows whole-block omission, ordered by declared
  priority or recency. Tool calls/results retain their group integrity.

Agent memory and artifacts retain their original immutable source content. The
automatic service constructs a versioned model-input view containing summaries
and references; it does not overwrite or delete the agent's canonical memory.
If the agent wants to adopt a summary as its persistent working memory, that is
an explicit normal record update with provenance and version checks. Hybrid
agents can reuse the returned context snapshot or summary references on later
requests without surrendering ownership of their memory store.

Summaries preserve source references and source trust/classification. Summarizing
retrieved text must not turn it into a system instruction or new authority. A
summary is lossy; schema/size checks do not prove semantic equivalence. The agent
defines what must remain exact and whether a summary is sufficient for its task.

## Input handling and automatic-compaction flow

1. Prepare and measure the complete request including adapter overhead, planned
   output and recovery headroom. Record the original size and block contributions.
2. With automatic handling off, return a pressure warning for fitting near-limit
   requests or a typed overflow result for an oversized request. The latter is
   delivered to host code independently of the oversized model prompt.
3. With automatic handling on, apply only permitted transformations. Pack whole
   optional groups, prefer reusable derived views, and compact eligible blocks
   when the chosen policy enables summaries. Do not infer transformation
   permission merely from content being labelled memory or artifact.
4. Trigger proactive compaction at a configurable pressure threshold and aim
   below a separate target to avoid repeated near-limit repairs. For example,
   80% trigger and 60% target are illustrative tunable starting points, not
   measured optimal defaults. Forced overflow handling uses the same path.
5. Large compaction inputs are processed in fitting bounded chunks, preserving
   declared protected groups. Each summarization stage uses the same OS sizing
   and output-safety checks. Limit hierarchy depth/calls; never recursively
   compact forever or spend protected finishing reserves.
6. Re-prepare and measure the final derived context, including all feedback. Submit
   only the fitting immutable prepared request. Record a durable linked attempt
   and compaction receipt so replay/restart does not repeat charged summaries.
7. If protected inputs cannot fit, compaction is disallowed, permission is missing,
   or budget/attempt limits are exhausted, preserve originals and return a typed
   unsatisfied request to the agent. The agent chooses paging, decomposition,
   reclassification of inputs or an authorized alternative binding.

Proactive compaction operates on declared process context or a submitted context
view. The OS does not scan an agent's arbitrary records, source files or memory
stores in the background. A newly initialized agent can choose entirely manual
memory, entirely assisted working-context management or a mixture.

## Always expose the pressure and intervention

Every inference result should carry a bounded receipt indicating the chosen mode,
original/final size and measurement certainty, limit, context snapshot, omitted
blocks, summary-to-source references, compaction usage and whether assistance was
needed. Retain the details in OS inspection independently of what the model saw.
Also expose pressure before the cap is reached. Successful assistance is still
an observable intervention, not an invisible fix.

This lets an author disable assistance to reproduce the native agent's oversized
request, or leave assistance enabled while measuring how often the agent depends
on it. The caller sees the original pressure even when a smaller derived request
succeeds. Diagnostic measurement alone does not incur summarization cost.

## Output safety and its relationship to these settings

OS cutoff classification, non-execution of incomplete replies, output-limit
enforcement capability reporting, byte bounds and termination/effect certainty
remain unconditional. Generic bounded smaller-response handling can be provided
by the OS inference service under the process's declared response/recovery
protocol and budget. The agent still defines a meaningful output unit and handles
semantic decomposition. A context setting cannot authorize acceptance of partial
actions or replay of a native job that already performed effects.

The response-recovery request, and any compaction request, goes through the same
selected context policy and final measurement. Unknown termination requires
reconciliation; it is not another compaction or retry opportunity.

## Plan and validation boundary

Implement in stages only after authorization for implementation:

1. Unified prepared-request measurement and typed I/O outcomes on every adapter.
2. Effective per-process/per-request context policy and always-visible receipts.
3. OS optional deterministic packing service, with manual and hybrid coverage.
4. Optional bounded compaction service with immutable sources and explicit
   lineage/trust preservation, then proactive thresholds and reuse.
5. Integrate the coding agent by exposing separate memory/artifact/history blocks
   and selecting its policy explicitly, without making those coding structures
   OS concepts.

Required tests include off-versus-on behavior on the same oversized context,
per-request overrides, compactable-required versus verbatim blocks, whole tool
pairs, original-memory preservation, missing permission, trust preservation,
compaction input/output overflow, exhausted budgets and unknown termination,
restart/replay, intervention visibility and manual/automatic/hybrid agents on
both local and cloud bindings. Include non-coding and direct-caller fixtures.

For this design-only task, inspected actual context/memory/runtime/configuration/
ports paths and the prior boundary proposals. Confirmed no implemented general
runtime compactor or automatic-context switch; distinguished agent summaries
from OS facilities. Checked documentation links, stable IDs, required ledger
sections and whitespace. No implementation tests, model calls, compaction,
provider installation or run resume occurred.
