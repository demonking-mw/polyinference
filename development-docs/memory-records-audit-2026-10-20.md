# Historical memory and OS context interventions — 2026-10-20

Investigation only. No product implementation, configuration or retained run
state changed. Agent-written summaries are excluded from OS compaction counts.

## Findings

Accumulated conversation/tool history has exceeded the configured input
allowance. The shared senior summary and worker notes have remained much smaller.
The reviewed evidence contains one confirmed input-size rejection, and a newer
run contains 32 successful OS history-omission interventions. It contains no
OS model-based summary-compaction calls or applied summaries.

| Measurement | Result |
| --- | ---: |
| Saved files parsed | 28 |
| Distinct runs after deduplication | 15 |
| Runs containing model operations | 13 |
| Model-operation effects, including retries/native jobs | 546 |
| Explicit shared-memory views decoded | 537 |
| Largest shared-memory content | 4,977 UTF-8 bytes |
| Confirmed input-overflow failures | 1 |
| Runs with the newer OS context receipts | 1 |
| OS preparations with receipts in that run | 181 |
| Preparations omitting optional history | 32 (17.7%) |
| Original requests strictly exceeding their allowance | 31 (17.1%) |
| Preparations applying OS summaries | 0 |
| Durable OS summary child requests/effects/cache entries | 0 / 0 / 0 |

The 537 shared-memory measurements include both legacy memory embedded in pinned
application inputs and the newer separate `agent-memory` block. They measure the
canonical JSON content of the memory view, including note metadata, not just the
senior's prose. The five model operations in an early schema-1 export lack the
artifact evidence needed for this measurement; four other operations are Git
policy decisions without the shared memory view.

All input totals below use the runtime's UTF-8 byte accounting as a conservative
token bound. They are not provider tokenizer measurements or proof that a remote
model's physical context window was exhausted.

## Confirmed stop: Minecraft v11, run 2de3d5c5ab9b

The request `worker-3-recover_playable_foundation/model-44` was rejected locally,
before provider submission:

| Component | Bytes |
| --- | ---: |
| Full serialized message input | 96,529 |
| Configured input allowance | 96,000 |
| Required messages, including shared memory | 14,421 |
| Additional optional conversation/tool history | 82,108 |
| Shared memory content within the required input | 1,681 |
| Senior summary text within that memory | 1,649 |

Optional history accounts for about 85% of the serialized message input. The
memory view has no uncovered worker notes at this request. This is evidence of
history growth and the old packing/accounting mismatch, not a shared-memory
summary overwhelming the input by itself. The saved error is `Required context
does not fit; no silent pin removal`, with `submitted=false`.

The failure predates the new OS context service. The earlier
[run investigation](run-2de3d5c5ab9b-analysis.md) established that omitting two
old optional pairs would have brought the request under the allowance. This
audit independently remeasured its full/required input and shared-memory content.

## Successful OS intervention: Minecraft v12, run eb66fc618354

This run contains 181 context receipts. Each records `auto_deal_context=true`
and `auto_compaction=false`.

- The OS omitted old optional history in 32 preparations: 17.7% of all 181.
- In 31 preparations the original request exceeded 96,000 bytes. One more
  intervention supplied the configured safety headroom while already under the
  hard allowance.
- All 32 interventions occurred in `worker-3-mining_inventory_03`, which had 71
  model-operation effects including retries. Thus 45.1% of that worker's model
  preparations needed history reduction.
- Every omission affected optional history and preserved complete tool pairs.
  No required memory/instruction/current-input part was omitted.
- No request failed with a recorded input overflow. The run ultimately paused
  for uncertain native termination, described in the
  [separate run investigation](run-eb66fc618354-analysis.md).

The largest original request demonstrates the distinction especially clearly:

| Measurement at worker-3/model-69 | Bytes |
| --- | ---: |
| Original prepared-adapter input | 156,320 |
| Allowance | 96,000 |
| Input after OS history omission | 90,697 |
| Required input | 14,095 |
| Shared-memory content | 940 |

For that request the OS omitted 36 parts, comprising 18 complete call/result
pairs. Across the 32 interventions, the largest resulting prepared request was
94,917 bytes. Shared memory peaked at 4,004 bytes elsewhere in this run.

These are 32 distinct request preparations, not 32 permanent compactions of
stored memory. Later calls again supply retained history and may omit its old
prefix again. Original history remains stored.

## What the zero compaction count means

OS compaction is counted through `context-call/` requests, model effects marked
`runtime/context-compaction`, `context-summary/` cache entries and the `summaries`
and `compaction_operations` fields in preparation receipts. All are empty/absent
in the reviewed run records. Senior `memory_update` proposals, output-cutoff
retries, agent-side history selection and provider/native internal session
behavior are not counted as OS compaction.

The newer run's summary-compaction option was explicitly disabled. Older reviewed
runs lack the newer context receipts and predate this service. Consequently zero
recorded OS summaries is not evidence that enabling compaction would never help.
What is established is that optional-history omission was sufficient for every
recorded oversized preparation in the newer run.

## Scope, evidence and checks

Inputs were the 16 matching run exports in `C:/Users/bh349/Downloads` and 12
rolling snapshots under this repository's `.polyinference/history`. Duplicate
exports/archives were counted once per run ID, selecting complete records first,
then greater effect/record coverage and later export time. Two retained runs
failed before any model operation. This is a local saved-record sample, not a
census of every execution or a workload benchmark.

[Machine-readable results](memory-records-audit-2026-10-20.json) retain the
selected source filenames/SHA-256 hashes, snapshot inventory, per-run counts,
overflow details, largest memory views and all 32 intervention measurements.
The analysis helper is retained locally at
`.polyinference/memory-audit-20261020.py`.

Validation performed for this audit:

- Parsed all 28 input files without errors and deduplicated them to 15 runs.
- Reconstructed serialized full/required message arrays and decoded 537 shared
  memory views from saved artifacts.
- Checked that all 181 receipt records exactly match their retained prepared
  receipts and fit their declared allowances.
- Verified all 32 omission sets affect only optional parts and retain whole tool
  call/result groups; independently checked zero OS summary markers.
- Verified size and SHA-256 integrity of all 1,025 artifacts in the v12 export,
  631 in v11 and 749 in the export containing the largest memory view.
- Cross-checked v11/v12 measurements against the earlier investigations, without
  claiming their historical tests as new checks.

Older generic HTTP 400 diagnostics and early exports have incomplete evidence;
absence of a classified overflow there cannot exclude every hidden upstream
cause. Native internal session state is outside these explicit OS receipts.
No live inference, run resume, UI execution or product test suite was performed.
