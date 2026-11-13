# Portable endpoint lifecycle proposal

<a id="portable-endpoint-testing"></a>
## Portable endpoint lifecycle and testing — proposal, 2026-10-23

Status: proposed; no implementation, configuration or retained run changed.
Related: run14 transport findings (`docs/temporary/incidents/2026-10-21-haiku-timeout-findings.md#run14-findings`), `development-docs/FIXES.md#fix-0113`,
`development-docs/FIXES.md#fix-0114`, current simulator (`docs/modules/inference-simulation.md`).
The user requires the local lane to support both small cloud models and actual
local inference. Local/cloud remain logical binding IDs; URL, model size and
physical location never determine timeout, authority or effect certainty.

### Common inference lifecycle

Extend the existing adapters and OS services; do not add a shared agent library.
Raw Anthropic, OpenAI-compatible chat and Responses adapters emit common lifecycle
facts: submitted, response headers/IDs, optional prefill progress, output progress,
terminal completion or typed failure. Use internal SSE where supported, accumulating
one complete response under the existing byte/token/completion guards. The caller
still owns reply grammar; plain-text agents remain valid. Partial JSON or a stream
EOF without the protocol's terminal evidence cannot execute. HTTP 200 and heartbeat
traffic are not completion. Keep hidden reasoning private; progress can count
bytes/events without retaining reasoning text. Aggregate progress updates (for
example, once per second), persist terminal/cause evidence promptly, and prevent
observer failures from changing execution outcomes.

Trusted adapters declare streaming, result-retrieval and confirmed-cancel support,
and whether a request is strictly generation-only. Disable provider/server tools
for that classification. Never infer these guarantees from localhost, a lane name,
a model's claim or generic OpenAI compatibility. Unknown capability stays strict.
A non-streaming fallback is explicit/visible and uses its total deadline without
pretending intermediate progress is observable. A rejected streaming negotiation
can fall back only as a new recorded attempt after a known rejection.
Native tool-using jobs keep their separate broker/continuation protocol.

### Timers and response budgets

Add optional structured timing preferences in system_settings.Endpoint. Names below
are proposed, not fields accepted by the current configuration schema. Replace the
ordinary raw-call blanket wait_for(endpoint.timeout_seconds) with a common lifecycle
watchdog. Keep one absolute hard deadline for the logical request, including OS
admission, retry backoff and all attempts, also capped by its original operation/
process deadline. First-output waiting begins at provider submission, excluding OS
admission; remote queue/prefill remains part of that observed wait.

| Proposed setting | Small-cloud starting profile | Slow local-server starting profile |
| --- | --- | --- |
| connect_seconds | 10 | 10 |
| first_output_seconds | 180 | 900 |
| output_idle_seconds | 90 | 300 |
| total_seconds, all attempts included | 600 | 1800 |

These are editable starting assumptions, not provider requirements or measured
hardware guarantees. Keep transport read/liveness observation distinct from model
progress. Pings show a live connection but do not reset output-stall or hard-total
limits. Verified prefill progress can update the displayed phase; it cannot extend
the absolute deadline. Providers without intermediate events get the explicit
non-streaming policy. Long silent reasoning needs a suitably configured profile.
Normal and simulated paths use the same watchdog; artificial pacing must remain
separate from actual provider completion/cancellation evidence.

The coding agent should choose modest per-request output targets (for example,
4k tokens for interactive testing) through the existing runtime/output-tokens path,
while retaining the 32k hard ceiling for assignments that need it. Do not silently
lower existing saved limits. A 32k response at 5 tokens/s takes about 107 minutes
before prefill; raising every timeout cannot make that fit a one-hour process.
Use smaller complete actions/tasks when the chosen throughput/time budget requires
it. Learn/display observed time-to-first-output and per-stream speed at the selected
concurrency; do not multiply single-stream speed by slots or claim GPU admission.
Profile selection and response sizing belong to the application.

### Recovery by possible effects

Phase 1 preserves today's unknown-effect barrier while fixing transport/timers.
Phase 2 is an explicit proposed refinement of the current global uncertainty rule
(R13), not a description of present behavior:

- Known unsubmitted or confirmed failed transient requests use linked OS retries,
  bounded backoff/Retry-After and a suggested two extra attempts for new profiles.
  Every attempt has its own immutable intent, reservation and accounting. Adapter/
  SDK internal retries stay disabled so submissions cannot escape OS accounting.
- For a trusted generation-only request with no delivered host/provider tool effects,
  an unavailable result can be logically superseded under an explicit bounded-recovery
  policy. Preserve the old uncertain effect and outstanding provider-work record;
  never label it confirmed stopped. The old attempt loses delivery authority through
  a durable generation identity, so late output cannot execute actions. Only the
  selected complete validated result wins the logical request through an atomic
  outcome record; restart/replay cannot create another submission or winner.
- Keep the old token/spend reservation conservatively charged and its endpoint slot
  held until actual terminal or verified cancel evidence. A new attempt needs spare
  capacity and remaining budgets/deadline. Allow at most one overlapping replacement
  per endpoint; if it also becomes unknown, issue no further replacement until
  pending work is reconciled. Normal slot/token reservations still bound all pending
  generations. This avoids hidden duplicate GPU work or billing.
- With a one-slot local server and no cancellation/status support, automatic retry
  must wait; show the endpoint as unavailable rather than silently exceed capacity.
  An optional adapter may abort an individual request when it can verify completion.
  Restart is automatic only for an explicitly app-owned exclusive service under a
  service-control lease, never an arbitrary shared local server.
- A generation-only uncertainty can block its worker/endpoint while independent
  work continues within unaffected capacity. Unknown writes, native jobs, provider
  tools and unverified execution modes retain the strict runtime barrier. Running
  out of retry/capacity/time budget produces a precise durable reason, not a loop.

This distinction changes dispatch semantics and requires its own feature/schema
version, crash/replay tests and an explicit boundary/revision update when implemented.
Old runs retain strict semantics and exact pins; do not retrofit the unresolved
7086c575ef94 request or reset its already elapsed deadline. New profiles apply to
new runs. Selecting another model/provider automatically is outside this proposal.

### Testing and UI

Use three layers: deterministic offline lifecycle tests with an injectable clock;
local fixture HTTP/SSE servers exercising the real parsers/cancellation paths; and
explicitly requested live cloud/local smoke tests. Existing seeded live fault/TPS
simulation stays application-owned. It must be labelled as buffered provider-output
pacing, not evidence that missing-terminal streams or real hardware were tested.
Extend fixtures to inject failures before headers, between deltas and at completion,
so real Haiku generation is unnecessary for fast recovery tests.

Required cases include:

- A healthy generation beyond 180 seconds completes under the new budget; slow
  prefill and two-slot shared throughput do not trigger the wrong watchdog.
- Only heartbeats, a genuine output stall, malformed/truncated SSE, missing terminal,
  a mid-stream error after HTTP 200 and a non-streaming server follow distinct paths.
- Retry-After, permanent 4xx, token/output limits, cancellation, overall deadline,
  queue saturation and final-phase reserves compose without allowance resets.
- A timeout after partial JSON executes no action; a late superseded result cannot
  write files or become a second winner, including after coordinator restart.
- Unknown generation holds accounting/slot capacity; a one-slot server cannot gain
  an extra active request. Verified cancellation releases once; repeated resume,
  crash during publication and late usage settlement cannot double-charge/release.
- An unknown tool-bearing operation still blocks dispatch; an independent permitted
  request can continue only for the new audited generation-only classification.

UI status should show Queued, Waiting for model, Generating, Recovering attempt 2/3,
Waiting for endpoint, or Paused with a useful reason. Display last progress, elapsed
and remaining hard budget and the effective timing/profile before Start. Advanced
inspection/export includes original exception cause, timeout stage, provider request
ID, attempt chain, terminal/cancel evidence and outstanding work. Distinguish actual
provider token usage from estimated progress. Optional Test endpoint/Warm up runs a
small bounded probe only when clicked, never on page open, and does not promise to
cancel or control a server it does not own.

### Implementation order and ownership

1. OS/adapter: typed progress/failure facts, internal SSE accumulation, complete
   response receipts, separate watchdogs and compatibility mapping. Update inference,
   kernel and system_settings; keep coding preferences out of generic services.
2. OS recovery: bounded generation-only supersession, outstanding-work accounting,
   delivery fencing and restart-safe logical outcomes in model_retries, admission,
   kernel/resume. Preserve strict native/effectful behavior. Application defaults
   select timing/retry/response targets; no OS Git or coding acceptance policy.
3. UI/tests: progress and a bounded endpoint probe, fixture scenarios, saved/live
   parity and explicit live smoke runs. Keep the existing simulator opt-in; share
   lifecycle rules without turning artificial completion into remote-stop proof.

Before each stage is considered implemented, update its owning module guides,
settings/examples, usage/recovery references, runtime boundary/revision ledger,
test inventory and navigation in the same change. This proposal adds no current
API, changes no launch defaults and claims none of the listed tests as executed.
Official grounding: [Anthropic streaming](https://platform.claude.com/docs/en/build-with-claude/streaming),
[llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
and [vLLM serving](https://docs.vllm.ai/en/latest/serving/online_serving/).

<a id="endpoint-agent-os-split"></a>
### Agent/OS separation review — 2026-10-23

Status: design clarification only; no runtime, configuration or current boundary
changed. `development-docs/FIXES.md#fix-0115` records the review. This section refines
policy ownership and generation-replacement authorization in the proposal above;
the earlier broad wording is not permission for the OS to decide coding workflow.

The project defines the agent as a portable application supplying its objective,
workflow, context, reply grammar and semantic decisions through RuntimePorts. The
OS supplies generic execution, admission, authority, persistence and recovery
mechanisms; a process needs no coding tasks, repository, tests or commits. The
inference server owns token/GPU scheduling. Sources:
agent/runtime contract (`design-docs/langgraph-agent/README.md#3-agentruntime-boundary`),
OS modules/processes (`design-docs/simplified-os/README.md#3-four-implementation-modules`),
current responsibilities (`design-docs/simplified-os/RUNTIME_BOUNDARY.md#responsibilities`)
and SDK ports (`docs/modules/sdk.md`).

#### Agent design

- Choose timing profiles, requested response size, retry tolerance and whether an
  undelivered result may be discarded and replaced. The example small-cloud/local
  presets and 4k testing target are application/deployment preferences, not OS
  meanings attached to the local binding or a coding-worker role.
- Supply objective, context, output grammar, canonical memory and permitted
  flexibility. Interpret a returned answer; choose smaller actions/tasks, repair,
  replan, wait or stop when generic recovery is exhausted. Registered application
  handlers still own coding Git, check selection, review and acceptance.
- Decide how an affected operation changes the application: keep other independent
  tasks running, await an endpoint, or pause the run. The OS reports operation/
  resource readiness and enforces admission; it never traverses the task DAG,
  creates a replacement foundation task or changes app/run.status on its own.
- Express recovery permission declaratively at process/request registration. An
  agent author should not implement Anthropic SSE, HTTP error classification or
  backoff. Runtime services execute the authorized generic policy automatically.
- Own tester scenarios and simulator installation through bootstrap, and issue any
  clicked endpoint probe as an ordinary bounded query. The UI projects execution
  facts and application choices; it cannot authorize weaker recovery on its own.

#### OS design

- Normalize raw provider transport and stream/terminal/error/usage facts behind
  adapter contracts. Provider-specific SSE decoding stays inside adapters; kernel
  dispatch sees generic operations. Bound response bytes/tokens and withhold
  incomplete output, without requiring JSON, WorkerReply or coding phases.
- Define generic timing/recovery preference schemas and enforce effective grants,
  absolute deadlines, capacity, reservations, budgets and final reserves. Measure
  queue/prefill/output timing and distinguish heartbeat traffic from output.
  Fixed coding profiles and physical hardware performance policy stay outside.
- Implement known-safe transient retries, cancellation/result lookup when supported,
  durable attempt identities, resource quarantine and late-result delivery fencing.
  Preserve every original result and charge every real submission. The caller's
  requested policy narrows what is permitted; it cannot waive an OS safety guard.
- Expose typed operational status/results through SDK/RuntimePorts, so another
  application or another runtime can implement the same contract. Do not inspect
  task/report/setup/coding memory records to decide whether a request may execute.
- Retain outstanding compute and capacity until verified terminal/cancel evidence.
  Return blocked resource facts when a one-slot server cannot safely accept a
  replacement. Any optional server control requires an explicitly registered,
  authorized service and lease; never restart an arbitrary local daemon.

#### Required correction to generation-only replacement

The previous proposal's phrase generation-only was necessary but insufficient.
Technical absence of tool effects does not decide whether discarding an answer is
acceptable. Replacement requires all of the following:

1. The caller explicitly permits replacement of an undelivered response; default
   compatibility behavior remains strict. A caller that already exposed streamed
   content needs an explicit delivery policy, not an inference of replaceability.
2. The trusted adapter and actual granted execution path establish that no provider
   or host tools/external effects can run for that attempt. A caller-supplied label,
   localhost URL or model claim is not evidence of this property.
3. The OS can isolate old response delivery and preserve original pending-work
   reservations, limits, data/routing policy and identity. A replacement needs its
   own capacity/budget; an unavailable slot cannot be manufactured by abandonment.

Only then can the generic OS service carry out an authorized replacement, without
asserting that the original remote work ended. Keep separate facts for remote
execution certainty, logical delivery eligibility and application continuation.
For unknown effects that fail these conditions, preserve the strict barrier.
This remains a proposed, versioned refinement to R13; current guarantees do not
change. Application consent cannot turn an uncertain write into a safe query.
Existing generic output-limit adaptation remains OS-owned within its declared
protocol and allowance (FIX-0058/0085); semantic task decomposition remains agent-owned.

An example portable exchange is: an application requests text with a declared
budget and replacement policy; the OS validates it, streams internally and applies
only the permitted recovery; it returns a complete result or typed failure/pending
resource facts; the application decides what to do next. No Git or coding outcome
appears in this exchange. OS monitoring can show provider progress while the agent
view separately shows task/sprint state. GPU batching remains a provider mechanism.

#### Independence checks and source observation

For implementation acceptance, require a bare RuntimeConfig summarization process
with arbitrary role names and no workspace/Git/TaskSpec/checks to exercise streaming,
retry, cancellation and exhaustion. Run the coding agent against a fake/replacement
RuntimePorts implementation to test wait/replan/pause decisions. Contract tests
must reject unauthorized replacement, unsupported mandatory features and attempted
replay of uncertain writes, while preserving ordinary plain-text callers.
Keep optional simulation installed outside the kernel, and test that runtime paths
neither import agent modules nor read coding record namespaces for these decisions.

Fresh static import inspection found no direct imports of polyinference.agent in
24 runtime/settings/ports Python files. This is limited evidence, not proof against
dynamic coupling or an executed general-agent conformance suite. One existing
agent-side portability dependency remains: agent/worker.py imports WriteScopeError
from runtime/workspace_state.py. Put that shared exception/result contract in the
SDK/ports layer, retaining a compatibility re-export, when implementing the boundary
cleanup. The observation does not establish a current runtime failure, and no
source changed. Keep future protocol preference/result types in the existing SDK;
no additional shared-agent-library layer is needed (FIX-0054).
