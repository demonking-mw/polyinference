# Use the UI

## General-agent workspace

Run `./scripts/launch-v2.sh` for the bundled Haiku stand-in and Codex Cloud
configuration. See `docs/guides/launching.md` for setup and overrides.

Start with `examples/general-agents.v1.json`. Its Cloud binding uses
`gpt-6.1-sol` through Codex app-server. Sign in with ChatGPT in the
environment running PolyInference. Configure and start your local endpoint
separately, or use the Haiku stand-in below. Open the reported loopback
address in your browser.

```bash
polyinference workspace /path/to/your-general-agents.json --port 8766
```

Add `--sim-haiku` to use remote Haiku in the local model role. This requires
`ANTHROPIC_API_KEY` and a data policy that permits the cloud destination
through the local binding. Mixed agents still use the separately configured
cloud binding for their cloud role. The picker labels the stand-in as cloud
inference. It has two inference slots, each with a 96,000-token input allowance
and a 32,000-token output ceiling, including thinking. Workspace startup only loads configuration
and serves the page.

The Cloud option shows **GPT‑6.1 Sol · Cloud (Codex subscription)** in the
standard configuration. The native app-server checks for a ChatGPT login
before submitting each turn. See `docs/guides/cloud-codex-default.md`.

- **Chat** has the agent and model pickers beside the composer. Simple uses
  either a compatible local or cloud model. Supervisor, Research, and Writer
  each show a field for their local and cloud roles. The composer previews
  permitted destinations for prompts and excerpts. Research looks up only
  the documents you attach.
- **OS Monitoring** shows the whole workspace without selecting an invocation.
  It shows current capacity and live reservations and waiters, retained holds,
  process and operation totals, and provider-reported tokens across retained
  records. It labels missing reports and unavailable provider quotas.
- **Agent Monitoring** shows sortable process rows and recorded model
  attempts. **View processes** under a reply opens that invocation directly.

Attach up to 64 UTF-8 text files totaling at most 128 KB. Each Send starts a
fresh invocation. Select **Include previous exchange** to pass the preceding
completed exchange as context. Prompts and included context must fit the
agent's 12,000-character task bound. The server retains chats and per-invocation
records under the configured state directory. You can reopen settled or
interrupted invocations for inspection.

The workspace accepts one invocation at a time. Unresolved effects and
resource holds remain visible and prevent new Sends in that workspace.
Scheduling and preemption controls require the standalone scheduler and its OS
acknowledgements. Current views show running, waiting, paused, and finished
processes using recorded OS state.

## Coding console

| Control or display | Behavior |
| --- | --- |
| Start run | Shows startup progress and selects the new run immediately. Rejected starts receive a run ID and startup process ID, remain selected as failed runs, and retain their error across polling. |
| Inference mode (only with --sim-inference) | Choose normal, normal and buggy, or slow and buggy before Start. Set shared TPS, batch, bug rate and optional seed; inspect synthetic progress separately from actual provider costs. Simulation guide (`docs/guides/sim-inference.md`). |
| Endpoint testing | Choose configured, small-cloud, local-inference or buffered timings for the local lane; click Test endpoint / warm up for one bounded query. No call on page open. Policy and limits (`docs/guides/endpoint-testing.md`). |
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

Failed starts retain inputs, error type and startup process in Save and rolling
history, even when no agent nodes ran.

Admission is FIFO within ordinary/finishing lanes and alternates when both wait.
Declared process priorities do not replace that policy. Critical sections show
verification/shell owners and waiters. Activity entries sharing a journal sequence
committed atomically. **Older transactions** opens retained historical values;
the record explorer shows current values.

Queue/hold timing is recorded for new requests; older telemetry may be absent.
The journal retains up to 10,000 transactions and reports pruning. Save captures
records/events together, then checkpoints/artifacts separately: a running workload
can advance during capture. Binary artifacts use base64; integrity/read errors are
listed. Private Git objects are absent. See snapshot limits (`docs/guides/archives.md`).

Memory / context defaults to the newest outstanding caller invocation, otherwise
its latest retained outcome; compaction helpers stay separate. An operation opens
that exact attempt. Refresh preserves selection; the selector exposes other work.
Prepared input is labelled only when its embedded receipt matches; otherwise the
drawer explicitly shows original input. Byte bounds do not prove submission or
provider token usage. This view omits hidden reasoning, KV state and some adapter
framing. Node prompts label prepared/original origin and separate native transport
observations. Saved JSON uses retained records/artifacts entirely offline.

Steering closes new task starts. Started workers, including gate/model-slot waiters,
finish their assignment before senior review consumes the update. Received/pending
instructions remain visible; this does not immediately interrupt a worker.

**Resuming** means accepted intent and preparation; it does not prove remote
termination. Drafts/request identity survive lost acknowledgements and restart;
duplicate submission does not create a second run. Saved authority, config, source,
budgets and deadlines persist. New-launch settings do not alter resumed runs.
Unsupported provider recovery or incompatible program pins produce a plain error.
See recovery and compatibility (`docs/guides/recovery.md`) and explicit retries (`docs/guides/retrying.md`).
Snapshots are read-only; external --state needs saved config.json or matching
--config. Restart after Python updates and use the HTTP URL (default
http://127.0.0.1:8765); opening ui.html through file:// has no API.

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
