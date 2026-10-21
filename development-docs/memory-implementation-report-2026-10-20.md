# Current memory implementation — 2026-10-20

This report describes the checked-out source, not a particular live run. No
implementation changed during this investigation.

Follow-up: [historical memory and OS context interventions](memory-records-audit-2026-10-20.md)
measures retained executions and distinguishes shared memory, history omission
and actual OS summary-compaction calls.

The coding agent owns canonical memory. Its senior engineer chooses the shared
summary, workers contribute assessment notes, and deterministic application code
persists and selects those records. The OS owns storage, replay, context bounds
and optional context preparation. There is no separate autonomous memory-manager
process in the current implementation.

## Ownership and active mechanisms

| Memory or state | Who supplies or manages it | Current implementation |
| --- | --- | --- |
| Shared working summary | Senior model proposes the text; coding controller commits it | `memory/working`, replaced when a valid applied `SeniorProposal` includes `memory_update` |
| Worker handoff notes | Worker supplies its assessment summary; worker application code creates the record | Immutable `memory-note/<attempt_id>` containing a `MemoryItem` with report/code provenance |
| Per-process conversation history | Coding application | Immutable artifact snapshots containing replies and paired tool observations, referenced by `trajectory_ref` |
| Resumable graph state | Application defines state; runtime supplies persistence | LangGraph checkpoints in `checkpoints.sqlite` |
| Durable records and content | OS storage services | Versioned/immutable records in `records.sqlite`; content-addressed files under `artifacts/` |
| Context omission and optional summarization | OS, under the caller's declared policy | Derived prepared contexts and receipts; canonical agent records are not rewritten |

### Shared memory lifecycle

1. When a worker publishes an assessed task report, application code creates an
   episode note from the report's assessment summary. It records the author,
   model trust, report provenance, applicable code and private/provisional code
   location. The note is included in the publication batch with the report and
   receipt. This also covers failed reports that reach publication; an interrupted
   worker that never publishes does not automatically produce this episode note.
2. `AgentServices.memory_view()` returns the current senior summary and every
   note absent from `covered_note_refs`, loading each note's content artifact.
   Selection is a record-prefix scan, without relevance ranking or filtering by
   the current task, code applicability or age.
3. The controller includes that view in senior planning/review input. Workers
   receive it when a new model request is built. Replaying an existing request
   retains that request's original input rather than silently refreshing it.
4. The senior may return `memory_update`. When its plan is applied, the controller
   atomically replaces `memory/working` with that text, the current note-reference
   list, `source_query` and `source_head`. Those notes become covered and disappear
   from the next active memory view. Their original records and content remain.
5. If the senior omits `memory_update`, the summary and coverage stay unchanged.
   The update is optional, is a replacement rather than an automatic merge, and
   has no dedicated string-length bound or semantic completeness validator.

Sources: [worker publication](../src/polyinference/agent/worker.py),
[memory selection and prompt assembly](../src/polyinference/agent/services.py),
[planning and summary publication](../src/polyinference/agent/controller.py),
[proposal schema](../src/polyinference/domain.py) and
[senior instructions](../src/polyinference/agent/prompts.py).

## Memory versus model context

The agent builds an explicit `ContextView` for each model operation. Instructions,
application inputs and the current host request are required. Shared memory is
placed in a separate required, compactable `agent-memory` data block, with
`retrieved` trust. Historical replies and complete tool call/result pairs are
optional. The agent supplies its full retained trajectory; the OS decides whether
optional history must be omitted under the enabled context policy.

The generic runtime defaults both `auto_deal_context` and `auto_compaction` to
false. The bundled coding agent enables `auto_deal_context` by default, while
leaving `auto_compaction` false. Thus normal coding runs can drop old optional
history groups to fit the measured request, but do not automatically call a model
to summarize shared memory.

If both settings are enabled, the OS may summarize explicitly compactable blocks
when input pressure exceeds `compaction_trigger` (default 0.8), targeting a
smaller prepared input (`compaction_target` defaults to 0.6). Required instructions
and noncompactable data remain protected; tool pairs are not silently summarized.
If protected input still cannot fit, preparation fails rather than removing it.

Compaction uses bounded, tool-free child model calls on the parent's role binding.
It is not necessarily performed by the senior model: a worker request uses that
worker's binding. Summary calls share process authority, deadlines and real
budgets. The implementation supports raw inference and native `codex_app_server`
summary jobs; `codex_proxy` currently declines compaction. Originals remain
immutable, and summaries/prepared views are derived artifacts. Records under
`context-summary/`, `context-call/`, `context-prepared/` and `context-receipt/`
retain cache, call and transformation evidence. This OS service does not write
`memory/working` or mark worker notes covered.

Sources: [context assembly](../src/polyinference/agent/services.py),
[OS preparation](../src/polyinference/runtime/context.py),
[generic settings](../src/polyinference/system_settings.py),
[coding defaults](../src/polyinference/agent/system_settings.py) and
[runtime boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md).

## Persistence, scope and limits

Memory belongs to the selected state directory. The runtime opens
`records.sqlite`, `artifacts/` and `checkpoints.sqlite` there. Content is addressed
by digest; mutable pointers use version checks, and immutable record identities
cannot be reused with changed content. History artifacts preserve complete
reply/observation entries and deduplicate stable call IDs.

This supports durable continuation within the same compatible run/state. The
current code has no automatic cross-run project-memory import, global knowledge
store, embedding index, semantic retrieval, implemented tier migration, or active
expiry/forgetting policy for episode notes. `MemoryItem` carries retention/tier/
expiry metadata, but the current memory view does not enforce those semantics.
`MemoryQuery` and `MemorySnapshot` exist as contracts; the kernel dispatches model,
tool and publication requests and rejects other payloads, so there is no active
`MemoryQuery` execution path. The bundled agent leaves `memory_snapshot_refs`
empty in task specifications and constructed context views.

Preservation is bounded by storage budgets, not an implemented semantic garbage
collector. The record event journal retains at most 10,000 events. The rolling
diagnostic archive has a separate 30-day cleanup policy; it does not delete the
operational run state. An oversized required memory block can still prevent a
request from fitting when compaction is disabled or cannot sufficiently reduce it.
Uncovered notes can accumulate if the senior does not consolidate them.

Sources: [storage](../src/polyinference/runtime/storage.py),
[runtime initialization and dispatch](../src/polyinference/runtime/kernel.py),
[memory contracts](../src/polyinference/contracts.py),
[task creation](../src/polyinference/agent/tasks.py) and
[archive retention](../src/polyinference/history.py).

## Visibility and verification

Agents > Shared notes & hazards displays the current senior summary and uncovered
worker notes, with access to retained provenance. Generic records/artifacts and
recorded node prompts are inspectable. The dedicated OS memory/effective-context
drawer remains a design in [MEM-01](current-iter-issues.md#os-memory-context-inspector),
not implemented behavior. Existing prompt inspection does not uniformly label the
effective prepared context, as recorded in [FIX-0062](FIXES.md#fix-0062) and
[FIX-0064](FIXES.md#fix-0064).

Verification performed for this report: source inspection of the application,
runtime, contracts, configuration, storage and viewer paths; offline execution
of the actual AST-extracted `memory_view`, `history` and `append_history` methods
with in-memory records/artifacts. Probes passed for empty/populated memory,
covered-note filtering while retaining originals, complete history entries and
stable-ID deduplication. Source assertions confirmed generic automation defaults
and the required/compactable flags on coding memory.

Existing `test_http_integration.py` checks published notes and the senior summary;
`test_context_safety.py` covers optional compaction, immutable originals, protected
inputs and replay/restart behavior. Those tests were inspected, not rerun for this
report. No live run, provider request, UI execution or complete test suite was
performed. Claims describe source behavior and the limited probes above.

UTF-8 Python checks passed for report links, the history ID/index/required
sections and added-text whitespace. Windows Git inspection did not complete
reliably against the WSL filesystem (`Function not implemented`); a completed
Git diff check or reliable whole-working-tree status is not claimed.
