# OS memory and context inspection design

<a id="os-memory-context-inspector"></a>
## MEM-01 — Inspect an agent's memory and effective context from the OS — 2026-10-20

Status: implemented in `development-docs/FIXES.md#fix-0091`, including the read-only
drawer, retry metadata, node prompt correction and live/saved coverage. The
original design/acceptance criteria below are retained for traceability;
MEM-02's new memory management APIs remain outside scope.
Initial investigation: `development-docs/FIXES.md#fix-0062`.
README routes current-version defects and designs to this document.

### Requested behavior and ownership

Add **OS > Processes > select a process > Memory / context**, also reachable
from a model operation. It should answer: "What explicit input was available
to this agent invocation, and what did OS context preparation change?"

The first version is a read-only inspection feature. The OS exposes retained
ContextViews, artifacts and transformation receipts without interpreting coding
memory conventions. Agents continue to own canonical memory, its updates and
what they include in each call. Keep Agents > Shared notes & hazards for the
coding application's current shared summary and handoff notes.

Label the new drawer **Memory / context** and explain that it shows a retained
invocation input. It does not expose model hidden reasoning, provider KV state,
native harness internals or all application records the process could read next.
A completed process shows its last retained invocation, with that label.

### Research findings and existing mechanisms

| Finding | Source and consequence |
| --- | --- |
| The coding app already displays shared notes. | [ui-monitor.js:renderNotes](../../../src/polyinference/ui-monitor.js) reads memory/working and uncovered memory-note/ records. This is useful application state, not a general OS memory contract. |
| Memory is already an ordinary context block. | [agent/services.py:context](../../../src/polyinference/agent/services.py) creates agent-memory when supplied; ContextView.memory_snapshot_refs is currently empty there. Other agents may use entirely different IDs. |
| Original and prepared inputs are retained separately. | [runtime/context.py:ContextService.prepare](../../../src/polyinference/runtime/context.py) keeps the effect request unchanged, writes context-receipt/<operation_id>, and writes context-prepared/<operation_id> only after fitting the bound. |
| Preparation receipts already describe intervention. | They contain original_bytes, submitted_bytes, required_bytes, input_allowance, unit, policy, omitted_refs, summaries, compaction_operations and prepared_digest. No new runtime recording is required. |
| Model retries and summaries are distinct effects. | [runtime/model_retries.py](../../../src/polyinference/runtime/model_retries.py) records explicit retry roots/previous attempts; context.py marks summary calls with runtime/context-compaction. A newest-effect heuristic alone selects the wrong call during compaction. |
| Existing OS operation rows omit these relationships. | [ui_os.py:runtime_view](../../../src/polyinference/ui_os.py) exposes process, kind, timestamps and causal parent, but not retry markers or context references. Extend this small projection rather than fetching every full request during polling. |
| Prompt inspection can show the wrong input version. | [snapshots.py:detail](../../../src/polyinference/snapshots.py) reconstructs Prompt from the original context.parts. A retained native userMessage may override it; neither path uniformly identifies effective prepared context. Model-node matching by logical_step_id also misses OS retries with new step IDs. |
| Read-only access and saved evidence already exist. | [ui.py:TestUI.record and make_server](../../../src/polyinference/ui.py) provide /api/record and /api/artifact. snapshots.export_run includes records, revisions and exact artifact bytes in schema_version 2. |
| OS projection refreshes independently of graph checkpoints. | TestUI.view rebuilds runtime_view before its checkpoint cache return. Derive the new operation metadata there; do not cache it only with node history. |

The current runtime boundary (`design-docs/simplified-os/boundary/inference.md#context-preparation-and-output-recovery`)
requires immutable original memory, optional observable transformations and
agent-owned semantics. This feature makes those guarantees inspectable. It
does not add an OS memory manager, change compaction policy or require a new
settings field, protocol marker or state migration.

### Interface and invocation selection

1. Add Memory / context beside Status and Specification & limits in showProcess.
   Add the same action in showOperation for model_query and agent_job only.
   Opening from an operation selects that exact attempt.
2. For a process, list only its model operations. Group transport/output retries
   with their originating invocation using explicit retry provenance. Keep a
   selector for individual attempts; retain failed originals.
3. Default to the newest invocation with an outstanding non-helper attempt;
   otherwise use the latest retained invocation. Use created_at with operation_id
   as a deterministic tie-breaker, not lexical IDs or logical-step numbers.
   Keep uncertain attempts visibly marked. If more than one invocation is
   outstanding, show that fact and let the user select either.
4. Within an invocation, prefer its current outstanding attempt, then its retained
   effective outcome, then the newest retained attempt. Follow explicit
   model-retry-outcome and output-retry-outcome references when available; do
   not infer the outcome from success-looking text or a newer unrelated call.
5. Identify runtime/context-compaction helper calls separately and link them from
   their parent receipt. They never replace the caller invocation by default.
   A generic causal_parent_ref alone is insufficient to label a call a summary.
6. No model effects means "No model context recorded for this process." A
   process without LangGraph checkpoints, Git or coding records must still work.

For relationships, expose the request's runtime/model-retry and
runtime/output-retry markers, logical_step_id, causal_parent_ref and compaction
flag as small operation metadata. Output recovery followed by a transport retry
has nested roots: follow root/previous edges transitively, with a visited set
and same-process checks. Preserve an incomplete/malformed chain as separate
inspectable attempts with an explanation, rather than guessing or looping.
Retained retry intents without an effect may be shown as scheduled when that
record is available; never invent a prepared context for them.

### Drawer contents and data mapping

Keep two views: **Effective prepared input** by default when retained, and
**Original supplied input**. If preparation is unavailable, select and clearly
label the original view. Never silently substitute it under the effective label.

| Display | Authoritative data |
| --- | --- |
| Process, selected operation, phase/step, creation time and state | effect/<id>.request.scope, request.logical_step_id, request.created_at and effect.state; phase is optional application metadata |
| Original input | effect/<id>.request.payload.context |
| Effective prepared input | context-prepared/<id>.context |
| Receipt for that prepared view | context-prepared/<id>.receipt; show standalone context-receipt/<id> when preparation failed or is incomplete |
| Recorded submission evidence | effect.result.extensions["polyinference/attempted-backend"].submitted, or effect.attempted_backend for uncertain execution |
| Compaction provenance | receipt.summaries source/summary ArtifactRefs, receipt.compaction_operations and each part's derived_from |
| Referenced memory snapshots | ContextView.memory_snapshot_refs, shown as opaque references with record links only where records actually exist |

Show parts in their recorded order. Each row has part_id, part_kind, source_ref,
trust, required, compactable, call_id where present, artifact digest and declared
size. Expand or open full content on demand. Summaries link to both source and
derived artifacts. Mark parts omitted by preparation in the original view;
preserve whole tool call/result relationships and do not concatenate them into
an unexplained summary. Display declared memory snapshot references without
assuming they are artifact digests or shared-memory record names.

Show original/prepared/required bytes and allowance together with the receipt's
unit: utf8_bytes_conservative_token_bound. Label the metric as the measured
adapter-input byte bound, not provider tokenizer usage. submitted_bytes is a
historical field name for prepared size; it does not prove submission. Show
the effective context policy and intervention status in an expandable receipt.

Use "Submission recorded", "Recorded as not submitted" or "Submission evidence
unavailable". A dispatch-attempt marker does not prove remote receipt, and
effect.state == active alone is insufficient. Keep uncertain termination
separate from preparation and submission. Input overflow can leave a receipt
but no context-prepared record; show the failed bound and original input,
without fabricating a fitting prepared view. If receipt/context identities
disagree, show the discrepancy and raw records instead of merging them.

The prepared ContextView shows selected application messages. Adapter-added
tools, native protocol instructions, response schemas and provider framing are
not all represented as context parts; prepared_digest describes the measured
adapter payload. Do not call this a complete wire dump or reconstruct private
native state. Link existing operation/protocol evidence where useful.

### Loading, refresh, saved runs and failure behavior

Reuse GET /api/record?run=<run>&key=<key> and
GET /api/artifact?run=<run>&digest=<digest>. Add no endpoint or database. Introduce
small shared browser readers that return record/artifact data for either the
live API or savedDocument.records/artifacts. Reuse them in existing record and
artifact inspectors as practical. Preserve endpoint host checks, digest/path
validation and no-store responses.

Fetch the selected effect, optional prepared record and optional receipt in
parallel; handle each result separately. Promise.allSettled provides individual
success/failure results, so a missing optional receipt need not hide the original
context. [Browser API reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled).
Preserve HTTP status on api() errors, or in the new reader, so expected 404
absence is distinct from a failed request. Keep other errors visible in the
affected section. Read content only after selection/expansion; reuse the
existing digest-verified live artifact reader and report saved artifact errors.

Capture run ID, saved-document identity, selected process/operation and the
existing inspection generation before awaiting. Increment/invalidate the
generation on drawer close, Back, selection changes, run changes and snapshot
switches. Discard stale responses, including errors. Preserve the selected
attempt during normal polls; show when newer work exists rather than replacing
the text being read. Refresh details updates metadata and availability without
silently moving to another attempt.

Separate live record requests are not one journal transaction. Show the
OS-list capture time and detail-fetch time; tie all joins to the exact operation
ID and use the immutable prepared record's embedded receipt for that view.
A record created between polling and inspection becomes available on refresh.
Do not claim a globally atomic live memory snapshot.

Saved snapshots must open this drawer using records/artifacts already in the
JSON and make zero network/provider calls. Derive missing additive operation
metadata from saved records for older schema_version 2 exports. Keep old exports
usable when prepared context, receipts, checkpoints or artifacts are absent.
Show absence, export errors and malformed references explicitly. Existing
snapshots capture records/events together and artifacts/checkpoints separately;
preserve that documented limitation. No schema-version bump is needed for
additive optional viewer fields.

Use the existing element()/textContent path for all retained text, including
prompts and code. It inserts text without parsing it as HTML.
[DOM API reference](https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent).
Keep long content collapsed initially, allow full text on demand, and keep the
drawer keyboard-accessible through the existing dialog and button controls.

### Implementation work for this version

| Path | Planned change |
| --- | --- |
| [src/polyinference/ui_os.py](../../../src/polyinference/ui_os.py) | Extend runtime_view operation rows with small context/relationship/outcome metadata from the same records snapshot. Include no artifact bodies. |
| [src/polyinference/ui-monitor.js](../../../src/polyinference/ui-monitor.js) | Add shared live/saved readers, pure invocation-selection helpers, process/operation actions and the context drawer. Reuse existing drawer, Back, Refresh, record and artifact affordances. |
| [src/polyinference/ui.html](../../../src/polyinference/ui.html) | Preserve HTTP status in API errors if needed; invalidate pending inspections on drawer close; render explicit prompt-origin labels. Add only small styling/control changes needed by the existing drawer. |
| [src/polyinference/snapshots.py](../../../src/polyinference/snapshots.py) | Make node Prompt distinguish effective prepared input from original input. Include linked retry attempts for a model node using provenance, not only logical_step_id, while keeping summary helpers separately identified. Apply the same projection in live node details and export_run. |
| `README.md` | Describe the new control and its retained-invocation scope after implementation. |
| Existing UI/history/context regression files | Add the acceptance coverage below; reuse local scripted transports and browser timing fixtures. |

For node details, keep prompt as a list of role/content messages for compatibility.
Add explicit prompt_origin and selected operation identity; prefer the prepared
ContextView and offer original input separately. Keep native userMessage as
separately labelled observed transport evidence, rather than silently overriding
a prepared view. Artifact errors should affect the relevant content block, not
prevent inspection/export of the whole node. Do not infer success or execute
any retained action while inspecting it.

Implement the metadata/readers and drawer first, then correct node prompt
projection in the same feature task so the two UI routes agree. This refines
FIX-0062's initial viewer-only sketch: the runtime already records enough data,
but a small OS projection change avoids heavy request downloads and provides
correct retry selection. No agent-side edit is required.

### Acceptance and regression coverage

These were required future checks when this design was written; actual
implementation verification is recorded in FIX-0091.

| Case | Required result and likely coverage |
| --- | --- |
| Manual context, no OS intervention | Original and prepared views agree; ordered content and metadata match the request. tests/test_ui_os.py and tests/test_ui.py. |
| Automatic history omission | Effective view omits the whole optional tool pair; original content and omission receipt remain inspectable. Build on tests/test_context_safety.py fixtures. |
| Compaction on either inference binding | Effective summary and original memory are both readable with correct provenance/trust; a newer helper call never becomes the default agent invocation. Context fixtures plus tests/ui_start.test.cjs. |
| Input overflow and preparation before admission | Receipt without prepared record and prepared-but-unsubmitted states receive distinct labels; prepared size never becomes a submission claim. Backend projection and browser fixtures. |
| Transport retry, output retry and their composition | Failed original and every attempt remain selectable; explicit outcomes select the right attempt, including nested roots. A different process/invocation is never selected. Retry fixtures and browser tests. |
| Unknown execution or missing submission facts | Preserve uncertainty and display only retained submission evidence, including effect.attempted_backend. Never infer false/true from absence or state alone. |
| Generic agent and no model calls | No coding records, Git or checkpoints are required; empty context state is clear and usable. General-agent fixture plus OS UI tests. |
| Live update with unchanged checkpoints | New prepared records/receipts appear on refresh despite the graph cache; an explicitly selected historical attempt stays selected. Extend tests/test_ui_os.py's refresh regression. |
| Delayed fetch, close, Back, run/snapshot change | Stale content and stale errors never replace the new drawer or reopen a closed drawer. Extend tests/ui_start.test.cjs deferred-response cases. |
| Saved current and older version-2 JSON | Same retained parts/receipts as live; no fetch calls; absent optional metadata is derived from records or labelled unavailable. tests/test_ui.py, tests/test_history.py and browser harness. |
| Missing/corrupt artifact or receipt | Other sections remain usable, full original input is not mislabelled effective, export preserves explicit errors. Reuse current artifact/export regressions. |
| Literal hostile markup and long content | Markup displays as text, full content remains accessible, opening the drawer does not fetch every artifact in the run. Browser fixture and HTTP UI checks. |
| Both inspection routes and archival | Process drawer, node Prompt, manual Save and rolling history agree on operation identity and prompt origin. Existing shared serializer remains the single export path. |

Suggested focused implementation checks:
`.venv-linux/bin/python -m pytest tests/test_ui.py tests/test_ui_os.py tests/test_ui_agents.py tests/test_context_safety.py tests/test_model_retries.py tests/test_history.py -q`
and `node --test tests/ui_start.test.cjs` with Node 18+. Follow with lint/whitespace
checks and a manual browser inspection of a local fixture plus its saved JSON.
No live provider request is necessary to establish this viewer behavior.

### Research verification and remaining limits

For this documentation task, traced README's issue routing, the runtime boundary,
ContextPart/ContextView contracts, agent memory assembly, preparation and
submission records, nested retry provenance, UI cache/readers, snapshot export,
and existing Python/Node regression sources. Checked browser API documentation
linked above. The earlier FIX-0062 baseline passed 45 existing UI/context tests;
that was the preceding investigation and is not a new result or evidence that
this unimplemented feature works.

Only this current-version design and its required FIXES.md record changed.
No implementation, settings, new tests, live provider/UI inspection or run
resume was performed. Validate the acceptance matrix when implementing MEM-01.
