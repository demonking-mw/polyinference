# Use the UI

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

| Control or display | Behavior |
| --- | --- |
| Start run | Shows startup progress and selects the new run immediately. Rejected starts receive a run ID and startup process ID, remain selected as failed runs, and retain their error across polling. |
| Run selector | Reopen saved runs, including failed or interrupted runs. |
| Process/node list | Inspect the recorded execution order and individual node details. |
| Blue model node | Read the model's prompt and response. |
| Other nodes | Inspect state transitions, inputs, outputs and recorded operations. |
| Steering | Send new instructions while the selected run is active. |
| OS | Kernel health, active/finished processes, inference capacity, exclusive resources, private workspaces, outstanding operations and recovery diagnostics. Detailed budgets, reservation history and kernel trace expand on demand. |
| Agents (default) | Current workflow/plan, searchable task queue and full history, separate execution/verdict/senior review, shared notes/hazards, and project acceptance/output. Select a task or senior query to inspect evidence and phase-grouped execution nodes. |
| Inspect records | Open the shared inspector drawer to search every retained durable record, including schedule contracts, grants and workspace manifests. Artifact links open the retained text. |
| Save run · JSON | Download the selected run's full diagnostic snapshot, including records/revisions, retained events, checkpoints and exact artifact bytes. |
| Open snapshot | Inspect a saved version 2 JSON snapshot without live polling or provider requests; use Live runs to reconnect. |
| Costs | View provider estimates for the run and totals across saved runs. |

Failed startup attempts can be reopened and saved with **Save run · JSON**. The
snapshot includes the exact error, error type, submitted launch inputs and startup
process record, even when no agent nodes ran. They also enter the rolling history.

The OS uses cooperative cancellation and drain-before-review steering, rather than
forced model-request pre-emption. Admission is FIFO within ordinary and finishing
lanes, alternating between them when both have waiters. The process table shows
declared priorities; they do not replace this admission policy. Critical sections
show verification and shell permit ownership and ownership waiters. Entries in the
activity view sharing a journal sequence committed in one atomic transaction.
Use **Older transactions** to page through retained history and select an entry
for its historical value, or use the record explorer for its current value.

New requests record admission queue/hold timestamps and ownership waits. Older
runs may only have current records. The journal retains up to 10,000 transactions;
the console and export report any pruned history and legacy telemetry gaps.
Save captures records and events in one read transaction; checkpoints and artifacts
are captured separately, so a running workload can advance during capture. The
snapshot includes all retained diagnostic records and artifacts, including binary
artifacts encoded as base64. It does not contain private Git objects and is not a
runnable OS backup. Artifact read/integrity errors are listed in the snapshot.

Steering closes new task starts immediately. Workers that have already started,
including workers waiting for a gate or model slot, finish their original
assignment before the senior consumes the update. The panel shows received and
pending instructions. Steering is not an immediate worker interrupt.

Development allocation targets **10% senior / 90% junior by task count** over the
run. Setup, sprint planning and management calls do not count toward that split.
Rounding matters for small runs; it does not promise 10% of tokens, calls, elapsed
time or money. Exports include actual started-task allocation separately.

Cost reporting is approximate. Codex shows an **API-equivalent estimate**, not
an amount charged to your subscription or its remaining allowance. Missing usage
or unknown prices produce an incomplete estimate, marked with `+`; expand
**About cost estimates** for the explanation. The export retains rate dates and
source links. A zero Haiku count can be valid if no Haiku request has started;
check the endpoint bindings and recorded model operations before assuming a bug.
