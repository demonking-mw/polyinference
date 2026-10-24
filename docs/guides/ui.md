# Use the UI

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

| Control or display | Behavior |
| --- | --- |
| Start run | Shows startup progress and selects the new run immediately. Rejected starts receive a run ID and startup process ID, remain selected as failed runs, and retain their error across polling. |
| Inference mode (only with --sim-inference) | Choose normal, normal and buggy, or slow and buggy before Start. Set shared TPS, batch, bug rate and optional seed; inspect synthetic progress separately from actual provider costs. [Simulation guide](sim-inference.md). |
| Endpoint testing | Choose configured, small-cloud, local-inference or buffered timings for the local lane; click Test endpoint / warm up for one bounded query. No call on page open. [Policy and limits](endpoint-testing.md). |
| Run selector | Reopen saved runs, including failed or interrupted runs. |
| Process/node list | Inspect the recorded execution order and individual node details. |
| Resume | Select a paused/interrupted run, optionally type instructions beside Resume, then click once. Recovery and process selection happen internally. Resuming shows preparation; Running shows activation. The advanced process drawer remains available for inspection. |
| Blue model node | Read the model's prompt and response. |
| Other nodes | Inspect state transitions, inputs, outputs and recorded operations. |
| Steering | Send new instructions while the selected run is active. |
| OS | Kernel health, active/finished processes, inference capacity, exclusive resources, private workspaces, outstanding operations and recovery diagnostics. Detailed budgets, reservation history and kernel trace expand on demand. |
| Memory / context | Select an OS process or model operation. Inspect original and effective prepared input, individual retry attempts, ordered parts, opaque memory references, preparation receipts and summary provenance. Full artifact text loads on demand. |
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

Memory / context defaults to the newest outstanding caller invocation, otherwise
its latest retained outcome; compaction helpers stay separate. An operation opens
that exact attempt. Refresh preserves selection; the selector exposes other work.
Prepared input is labelled only when its embedded receipt matches; otherwise the
drawer explicitly shows original input. Byte bounds do not prove submission or
provider token usage. This view omits hidden reasoning, KV state and some adapter
framing. Node prompts label prepared/original origin and separate native transport
observations. Saved JSON uses retained records/artifacts entirely offline.

Steering closes new task starts immediately. Workers that have already started,
including workers waiting for a gate or model slot, finish their original
assignment before the senior consumes the update. The panel shows received and
pending instructions. Steering is not an immediate worker interrupt.

To continue a paused or interrupted run, select it, optionally fill in
**Instructions for continuing**, then click **Resume**. There is no required
process chooser or reconciliation form. The agent handles checkpoint continuation,
known-failure retries, interrupted-task review and accepted-output delivery.
Instructions enter its normal drain/review boundary once. Drafts and request
identity survive lost acknowledgements and page restart; repeated submission of
the same request does not start another run.

**Resuming** means the request was accepted and execution is being prepared.
Pending requests restore after server restart. Resume retains the run ID, private
work, authority, configuration, budgets and deadlines. Launch-form/simulation
changes apply only to new runs. An exact supported predecessor program can migrate
with recorded provenance; other incompatible programs are rejected.

The OS automatically uses retained host/completed-response evidence and retrieves
supported provider results. If a provider cannot recover an unknown operation,
the UI shows a plain failure while preserving it. This is not a request to edit
journals or assert that remote work stopped. Old synchronous HTTP requests without
a saved response handle and unknown native jobs may remain unrecoverable.
Saved JSON snapshots are read-only. An external --state needs its saved config.json
or matching --config. Restart the UI server after updating Python code, then reload
its HTTP URL (default http://127.0.0.1:8765); opening ui.html with file:// has no API.

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
