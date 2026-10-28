# Current iteration issues

[Scheduled four-repair implementation](four-repairs-implementation-2026-10-28.md)
implements agent source focus/diagnostic reads/search novelty, generic OS measurement
and caller priorities, agent-owned clean-output semantic handoff and replay-safe error
retirement. Fresh simple-os/5, agent-8/state 2.7 is required. No new live generation or
historical Resume is performed; final test/evidence limits are in the linked record.

[Authorized model fallback and existing-browser repair](model-fallback-browser-repair-2026-10-28.md)
implements agent-selected Terra/high/seven through the OS retry_model option and
trusted native continuation, initially with simple-os/4 state. Existing text-field
input leakage is repaired and actual Chromium checks retained. Its four-area plan
is now implemented in the scheduled batch above; old run evidence stays frozen.

[Authorized reliability implementation](reliability-implementation-2026-10-27.md)
tracks the OS/agent/qualification stages following FIX-0133. Changes require fresh
state; retained live evidence and the earlier cloud takeover remain preserved.

[27/28 October scheduled Minecraft live result](minecraft-live-test-2026-10-28.md):
four automatic cloud coding recoveries produced checked increments; the loading
recovery paused on provider model capacity. The partial browser foundation passes
44 host tests but lacks loading, physics and most requested gameplay. Actual
Chromium also finds text-field/game input leakage. No framework fix is claimed;
original resources, failed source and uncommitted delivery remain preserved.

[Failure isolation and proposed repair order](minecraft-failure-isolation-2026-10-28.md)
traces clean model failures bypassing cloud recovery, the effective 4096 output
target, prompt-only reply grammar, repeated local reads, conservative context
packing, a reproduced stale-error projection defect, incomplete diagnostic source,
browser-test gaps and the final effectful native-job stop. These are findings and
proposals; no implementation was changed by this follow-up.

[Task/context/memory follow-up](minecraft-failure-isolation-2026-10-28.md#convergence-context-memory-followup)
confirms all three read-only tasks lacked their assigned browser integrations.
Current OS replay reproduces a 49152-byte cap/48128-byte packing threshold, not a
fixed below-31K token limit; 29491 is an inactive compaction target. Current compact
worker-state probes confirm stale path-shaped tool errors and a second protocol
error-retirement defect for non-action replies. The user explicitly forbids fixes
in this investigation. Corrections to the earlier read counts and FileRead argument
claim are recorded in the follow-up; all implementation remains unchanged.

<a id="local-task-cloud-recovery"></a>
## P1 — Local task granularity and cloud worker recovery — 2026-10-27

**Status: implemented in the uncommitted tree; the small live gate passed, including actual cloud-worker resume. Combined framework results and limits are in the [implementation record](reliability-implementation-2026-10-27.md).**
[Requirements, user judgments, evidence and verification plan](local-task-granularity-and-cloud-recovery-2026-10-27.md).
Split coarse local assignments into independently testable behaviors; turn eligible
local stalls into bounded cloud-worker repair, preserve that route outside normal
task-share rounding, and tell the sprint planner the OS's actual capabilities.
Keep original accounts/deadlines, source authority and unknown-effect safeguards.
The earlier 227-case result belongs to FIX-0132. The authorized follow-up adds
bounded worker state, error-conditioned repair, OS enforcement and qualification.
Already-linked unstarted recovery consumers now support lineage-preserving
retargeting, including transaction-conflict/restart coverage. Started contracts
remain pinned. Read the current record before claiming long-run reliability.

[Detailed proposed implementation plan and historical failure coverage](run-reliability-implementation-plan-2026-10-27.md)
separates agent changes, OS guarantees, provider setup and verification.
It records the earlier cloud takeover and pending-consumer limitation at planning
time; its analysis-only scope was superseded by the user's implementation request.

Read [the fix history and design principles](FIXES.md) before repository work, as
required by [AGENTS.md](../AGENTS.md), and update it before finishing. This file
retains detailed investigations and historical results. The fix history records
subsequent corrections, including recoverable startup failures and the required
agent/OS boundary; consult it before treating an older implementation note below
as current behavior.

Current cross-run assessment: [27 October documentation/reliability audit](documentation-and-reliability-audit-2026-10-27.md).
Its historical recommendations distinguish orchestration mechanisms from product
convergence. The authorized follow-up implements the selected plan and static
U01–U04 repairs; current qualification limits remain in the implementation record.

<a id="router-distillation-tutorial"></a>
## Agent-router distillation research tutorial — 2026-10-22

Status: documented; research instructions only, outside the current runtime fixes.
The [HTML learning guide](router-training-guide.html) explains training fundamentals,
distillation, RLAIF, model/thinking choices, synthetic data and two-pass summaries;
its labs include the step-by-step distillation walkthrough and later feedback work.
The [Markdown tutorial](router-distillation-tutorial.md) covers Opus labels,
a small LoRA student on the user's reported 16 GB GPU, validation, inference and
evaluation, with RLAIF as a later stage. The user reports written Anthropic
permission for this research project. Recording the tutorial does not implement
a learned router, change process settings or reopen the completed fix queue.
Next-version work remains in the [routing proposal](next-iteration.md#learned-agent-routing).
Documentation verification and limits: [FIX-0106](FIXES.md#fix-0106).
Expanded learning-guide verification: [FIX-0107](FIXES.md#fix-0107).

<a id="authorized-implementation-queue"></a>
## Authorized implementation queue — 2026-10-21

Status: complete; all nine scoped items implemented sequentially with one commit
per fix. Integrated verification and commit map: [FIX-0093](FIXES.md#fix-0093).
The one-time heartbeat is disabled (PAUSED), confirmed 2026-10-21 10:34:18 EDT.
The original time gate required implementation to start no earlier than
**2026-10-21 01:55:00 America/Toronto (EDT; 05:55:00 UTC)**. This latest start
time supersedes the earlier requested times. The user requested
a commit of the current version first, then one fix at a time with a separate
commit after each verified fix. Earlier planning-only restrictions are superseded
for these nine scoped items. Queue preparation and baseline checks are not
implementation of the fixes. Actual start and completion evidence follow.

Actual wakeup clock check: **2026-10-21 09:14:29 EDT (13:14:29 UTC)**, after the
requested 01:55 start. Baseline cb02d02 was verified on codex/simple-os-v1 with a
clean working tree before editing. Completion records: item 1, [FIX-0083](FIXES.md#fix-0083);
item 2, [FIX-0084](FIXES.md#fix-0084); item 3, [FIX-0085](FIXES.md#fix-0085);
item 4, [FIX-0086](FIXES.md#fix-0086); item 5, [FIX-0088](FIXES.md#fix-0088);
item 6, [FIX-0089](FIXES.md#fix-0089); item 7, [FIX-0090](FIXES.md#fix-0090);
item 8, [FIX-0091](FIXES.md#fix-0091); item 9, [FIX-0092](FIXES.md#fix-0092).

| Order | Item | Owning layer and bounded scope |
| --- | --- | --- |
| 1 | [FIX-0069](FIXES.md#fix-0069), confirmed subissue of CONC-01 | Coding agent: make tick and dispatch use the same effective worker limit. This does not implement the wider OS concurrency audit. |
| 2 | [OSAG-07](#osag-07--p2-superseding-started-tasks-erases-them-from-development-accounting) | Coding agent: preserve durable task-start accounting after cancellation/supersession and align role-allocation/review metrics; never-started cancellations remain excluded. |
| 3 | [U05](../design-docs/simplified-os/DESIGN_REVISIONS.md#open-implementation-gaps), remaining generalization-audit item 5 | OS: make smaller-output feedback preserve plain-text and structured caller grammars without changing retry/effect/budget guarantees. |
| 4 | Older report item 3, below | Coding agent: separate prerequisite, task and final acceptance criteria; the OS continues to execute granted checks and retain source-bound evidence. |
| 5 | [RUN13-01](#run13-01) | Coding agent: establish accepted shared test prerequisites or explicit dependencies before independent workers need them. |
| 6 | [RUN13-02](#run13-02) | Coding agent: select and exercise existing explicit retained-source handoff, with complete grants/conflict checks and consistent mode-specific prompts. Arbitrary selective multi-candidate recovery is outside this bounded fix. |
| 7 | [RUN13-06](#run13-06) | Coding agent repository/UI projection: distinguish ancestry, private/dirty source and actual accepted task contributions. |
| 8 | [MEM-01](#os-memory-context-inspector) | OS inspection/UI: original/effective context, receipts, retry/summary provenance and live/saved parity; no new canonical agent memory manager. |
| 9 | [SIM-01](#sim-batch-ui) | Agent CLI/UI: invocation-only simulation preset and validated capacities. Generic OS settings precedence may need support; no provider-specific kernel scheduler. |

For each item, read related history and the feature's primary guide through
docs/file-tree.json, implement a bounded change with meaningful regression
coverage, update all affected module/setup/usage/settings/design/issue docs,
append a new FIX entry and run the required documentation generation/check.
Run appropriate tests including related earlier regressions, lint and whitespace
checks. Commit that fix and its documentation before starting the next item;
finish with broader integration verification. Do not claim historical results as
new testing, commit failing work as verified, or combine independent fixes.

Preserve prior FIX entries and stable IDs; explain supersession or recurrence in
new entries. Keep canonical memory, Git workflow, task policy and acceptance in
the agent, and generic authority, resource bounds, execution certainty, durability
and optional context mechanisms in the OS. Do not weaken existing safeguards to
make progress. Preserve user edits and retained run state; do not push commits.
MEM-02, RUN13-04's optimization/audit, the wider CONC-01 audit and the remaining
broad lifecycle/fault/diagnostic proposals are not part of this ready-only queue.

<a id="run14-findings"></a>
## Run 7086c575ef94 findings — 2026-10-21

Status: investigated; follow-ups open, no implementation changed.
[Evidence and limits](run-7086c575ef94-analysis.md) · [FIX-0100](FIXES.md#fix-0100).

- OS/adapter diagnostics: a submitted Haiku call became uncertain after 180.005
  seconds with a 180-second timeout. Preserve timeout origin and chained transport/
  cancellation facts so these causes are distinguishable. The actual trigger is
  strongly consistent with timeout but not conclusively retained. Keep unknown
  execution out of blind retry; timeout tuning alone does not reconcile this call.
- Transport/deadline follow-up (2026-10-23): [official Anthropic guidance and
  fresh source probes](run-7086c575ef94-analysis.md#anthropic-documentation-follow-up--2026-10-23)
  establish non-streaming large-output requests plus a UI-selected 180-second
  whole-generation limit. Implement internal SSE accumulation and distinguish
  inactivity from total deadlines; SSE alone leaves the kernel cutoff intact.
  Retain typed cause/request/progress diagnostics and explicit durable retry
  accounting. This is an open integration repair, not an implemented change or
  proof that every earlier pause had the same cause.
- Coding planning: one preparation owner received four top-level tests while its
  required runner demanded four different tests/acceptance paths. Check exact
  mandatory-path ownership/grants before dispatch without weakening assertions.
  FIX-0088's owner/dependency validation does not validate this single-owner case.
  The next plan corrected the grant and used an explicit retained-source handoff;
  that handoff worked, but the replacement paused before writing or verification.

Only setup reached pi-dev. Direct 36/36 foundation tests are historical private
worktree evidence; no development contribution or final product was accepted.
This is not a reproduced OS deadlock, context overflow or simulation fault.

<a id="portable-endpoint-testing"></a>
## Portable endpoint lifecycle and testing — proposal, 2026-10-23

Status: proposed; no implementation, configuration or retained run changed.
Related: [run14 transport findings](#run14-findings), [FIX-0113](FIXES.md#fix-0113),
[FIX-0114](FIXES.md#fix-0114), [current simulator](../docs/modules/inference-simulation.md).
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
changed. [FIX-0115](FIXES.md#fix-0115) records the review. This section refines
policy ownership and generation-replacement authorization in the proposal above;
the earlier broad wording is not permission for the OS to decide coding workflow.

The project defines the agent as a portable application supplying its objective,
workflow, context, reply grammar and semantic decisions through RuntimePorts. The
OS supplies generic execution, admission, authority, persistence and recovery
mechanisms; a process needs no coding tasks, repository, tests or commits. The
inference server owns token/GPU scheduling. Sources:
[agent/runtime contract](../design-docs/langgraph-agent/README.md#3-agentruntime-boundary),
[OS modules/processes](../design-docs/simplified-os/README.md#3-four-implementation-modules),
[current responsibilities](../design-docs/simplified-os/RUNTIME_BOUNDARY.md#responsibilities)
and [SDK ports](../docs/modules/sdk.md).

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

<a id="ui-process-resume"></a>
## UI-RESUME-01 — Resume a selected paused process — 2026-10-21

Status: implemented; run-level continuation supersedes the original process-only
entry point. Current implementation: [FIX-0111](FIXES.md#fix-0111).
Original process-level implementation: [FIX-0102](FIXES.md#fix-0102); the historical
paragraphs below describe that earlier behavior.

The paused-run toolbar offers Resume run with a paused-process chooser and optional
steering; the process drawer retains Resume process. The visibility correction is
[FIX-0105](FIXES.md#fix-0105). Blocked submissions expose their reason instead of
hiding the toolbar entry. Use the HTTP UI, not a direct file:// preview. The local
API records a generic OS resume-request, then reopens the same saved configuration
and routes continuation through the application's existing known-model retry,
accepted-output recovery or senior review. Prompt/config pins, budgets, deadlines,
source provenance and cancellation remain enforced. The agent module fingerprint
is unchanged, so the UI feature itself does not invalidate retained program pins.
Unsettled remote execution is refused pending reconciliation; the
[run 7086c575ef94 timeout diagnosis](run-7086c575ef94-analysis.md) is not repaired or
automatically reconciled by this feature. JSON snapshots remain read-only.

Frontend guards cover duplicate sends, stale responses and draft preservation;
backend guards cover concurrent runs, state/config identity, unknown execution,
version mismatch and launch failures. Requests/outcomes remain inspectable and
exportable. No UI reconciliation assertion or automatic budget reset was added.

### Run-level Resume implementation — 2026-10-23

The paused/interrupted-run toolbar now has optional instructions and one Resume
button; it submits immediately without a chooser. Stable request IDs and local
drafts survive acknowledgement loss/page restart. Polling can acknowledge a lost
reply so a later pause receives a new request. Recovery progress is visible and
unsupported recovery produces a plain failure rather than a resolution form.

The HTTP layer loads exact saved settings and serializes drivers. Generic OS
intent acceptance is independent of execution certainty. OS-owned preparation
recovers host receipts, artifact-backed completed query responses and retrievable
HTTP Responses by saved response ID, with bounded lookup and retained accounting.
Unknown/native/synchronous operations without recovery evidence remain protected;
no automatic remote-cancel or host-descendant termination guarantee was added.

Agent-owned continuation handles all stopped workers, resumes eligible checkpoints,
uses linked model retries or senior review with retained source, and recovers
accepted-output delivery. Atomic steering receipts and durable continuation plans
cover interrupted activation. CLI resume CONFIG [--text instructions] uses the same
service. Server restart restores pending accepted/activated requests, including the
journal-to-metadata gap. An exact predecessor graph has an audited migration;
other pins, grants, budgets, deadlines and cancellation remain enforced. Original
manifests/effects remain evidence. See [FIX-0111](FIXES.md#fix-0111) for fresh checks.

<a id="ui-run-resume-design"></a>
### Proposed run-level Resume redesign — 2026-10-23

Status: historical proposal, implemented with the explicit provider/compatibility
limits described above in [FIX-0111](FIXES.md#fix-0111). The original design-only
record is [FIX-0110](FIXES.md#fix-0110). The following preserves that proposal. The user wants optional instructions followed
by one Resume click, with continuation/recovery decisions handled internally.

**Frontend and HTTP adapter.** Place an optional instructions field beside the
paused run's Resume button. Clicking Resume submits the run ID, text and a stable
request ID immediately. Remove the required drawer, process chooser and
reconciliation tasks from this path. Show Resuming, then Running when the agent
actually continues. Show a plain failure if continuation fails; keep technical
details in inspection. Retain text until durable acknowledgement, deduplicate
clicks/retries across reconnects, and restore progress after page/server restart.
POST /api/resume accepts a run-level request without process_id and returns 202
with its request reference; acceptance means the request was saved, not that work
has started. The server owns saved-config loading, one-driver exclusion and
status projection, not coding recovery decisions. Offline exports remain viewers.

**Agent.** A run-level continuation handler owns resuming the objective. Move
coding decisions currently in cli.apply_resume behind this agent interface;
CLI/UI call the same entry point. Inspect the whole run rather than guessing one
process in JavaScript. Resume an eligible checkpoint, request a linked recovery
for a known failed model step, send interrupted work through senior review with
its retained source, or recover accepted-output delivery as appropriate. Account
for every stopped worker so one selected process cannot leave others stranded.
Record optional instructions once before choosing new work; apply them at the
existing drain/review boundary. Routine task disposition and repair belong to the
agent. Preserve objective, amendments, workspaces, task/attempt provenance and
acceptance checks. Use bounded recovery and record an actionable failure when
progress is impossible. An ordinary task report must not become a user resolution
form.

**OS.** Separate durable acceptance of a resume intent from permission to execute.
A paused runtime with unsettled effects may accept the intent, while new effects
remain gated on execution certainty. Add a generic, restartable preparation step
that resolves host receipts, restores saved operation identity and asks the
appropriate execution adapter for status/result or confirmed cancellation. Join
host descendants before marking their work ended. Retain evidence and release
ownership/reservations only after settlement. Recovered successful results replay;
known failed results permit a distinct linked retry chosen by the caller. The OS
returns typed ready/waiting/failed facts, with no Git, coding task or acceptance
policy. Unknown execution is never rewritten as confirmed termination merely
because Resume was clicked. Bound recovery waits and retain a specific failure
instead of polling forever or instructing the user to reconcile journal rows.

**Coordination.** One durable request progresses through accepted, recovering,
continuing and running, or failed. OS recovery progress and the agent's workflow
outcome remain separate records linked to that request. A crash at any stage
resumes the pending request without duplicating effects or applying text twice.
Acquire the runtime's state ownership before effect preparation; HTTP locking
alone is insufficient against an external coordinator. Preserve saved grants,
configuration, budgets, cancellation and deadlines. A limit/configuration failure
is an explicit outcome, not a silent allowance reset or a fresh replacement run.

**Provider and saved-run compatibility.** Current raw HTTP adapters have no general
remote status/cancel contract; existing records may lack a recoverable handle.
Native thread/turn IDs are useful evidence, not proof of reconnect/cancel support.
Implement and verify capability-specific recovery before claiming that interrupted
provider jobs resume automatically. Unsupported unknown execution must produce a
plain, specific failure; hiding its old message alone does not meet the goal.
Changing agent modules changes graph_digest, so existing runs also need an
explicitly tested compatibility/migration path. Never ignore the saved program
pin. Preserve original manifests and effects; migrate only documented compatible
state. Arbitrary historical versions cannot be promised safe continuation.

**Implementation and verification split.** First establish generic OS intent,
recovery, restart and execution-gate contracts using a non-coding fixture. Next
implement agent run continuation and all-worker recovery against those ports.
Then connect the frontend/HTTP adapter to that service. Verify empty/nonempty
instructions, task review, known model failure, interrupted source, output recovery,
multiple workers, duplicate requests, restart at each stage, external ownership,
unknown provider work and unsupported recovery, limits and program compatibility.
End-to-end success means one click reaches actual useful agent execution without
a process/reconciliation choice, with no duplicate effects or lost work. Tests and
provider recovery are planned, not performed by this design task.

<a id="os-concurrency-audit"></a>
## CONC-01 — Audit OS concurrency for deadlocks and stalled progress — 2026-10-20

Status: open; double-check in the current version. Investigation/test follow-up,
not a claim that an OS deadlock has been reproduced. Context:
[concurrency ownership](FIXES.md#fix-0067) and
[single-thread compatibility and agent capacity mismatch](FIXES.md#fix-0069).

Check OS behavior with multiple workers and supported thread/executor arrangements,
including one event-loop thread and one local inference slot. Distinguish resident
worker count, endpoint max_inflight, aggregate context reservations and filesystem
executor capacity; multiple workers must remain usable when inference is serial.

- Exercise worker counts 1, 2 and 4 with one and multiple inference slots, mixed
  local/cloud work, and contention for context reservations. Check progress,
  admission fairness, starvation, busy loops and excessive scheduler/checkpoint work.
- Audit lock acquisition order and waits across inference admission,
  verification/project, shell/installation and the filesystem executor. Include
  native tool callbacks, compaction and retries; a waiting operation must not
  prevent the resource holder from completing and releasing capacity.
- Check cancellation, deadlines, review/drain, shutdown and restart while workers
  wait or hold resources. Confirm known-ended work releases capacity and wakes
  waiters; uncertain effects retain ownership until reconciliation without blind
  replay or duplicated effects.
- Check whether synchronous storage/artifact work or filesystem contention stalls
  the event loop under load. Separate slow but progressing work, queue timeout,
  livelock/starvation and genuine deadlock in diagnostics.

Use bounded deterministic fixtures with explicit progress/timeout assertions and
captured wait/ownership/reservation evidence. Cover general agents without Git or
coding records as well as the bundled coding agent. Existing concurrency tests
and earlier passes do not establish that this expanded audit has been completed.

The confirmed tick/dispatch capacity mismatch from FIX-0069 is corrected by
[FIX-0083](FIXES.md#fix-0083): both predicates use the agent's effective worker_limit.
The wider OS audit remains open; this application correction does not establish
deadlock freedom. OS tests should not absorb Git policy. Preserve grants, budgets
and execution-certainty guarantees when addressing any findings.

<a id="run-a1859f8644a5-findings"></a>
## First two-slot run: recovery and concurrency findings — 2026-10-20

Status: open findings; analysis only. The only implementation change in this task
is increasing the UI/mixed-example sprint allowance from 9 to 27 (derived senior
query ceiling 27 to 81). [Full run analysis](run-a1859f8644a5-analysis.md) and
[measured evidence](run-a1859f8644a5-evidence.json) distinguish observed failures,
source findings and unmeasured performance hypotheses. History:
[FIX-0076](FIXES.md#fix-0076), [FIX-0077](FIXES.md#fix-0077).

The run admitted two local-lane operations together for 230.444 seconds, with
5 ms median / 436 ms maximum admission delay, and ended with no retained active
reservation or uncertain effect. The contested verification permit was acquired
after 6.693 s. No OS deadlock was established. Sprints 3–9 each started one task;
application dependencies and recovery, rather than inference capacity, limited
later parallelism. CONC-01 remains open beyond this workload.

<a id="run13-01"></a>
### RUN13-01 — P1: establish shared test prerequisites before parallel dispatch

Implemented in [FIX-0088](FIXES.md#fix-0088): source/command planning context,
explicit check-preparation ownership and validated dependencies, with a real
two-worktree test-discovery regression. The evidence below is retained.

Owner: coding agent planning/check policy. Sprint 2 required the persistence
worker to add automatically discovered tests, but its write grant excluded the
hardcoded runner. Only the parallel canvas worker could edit that runner, and
its candidate stayed private. Persistence's direct 12-test run passed while the
configured build omitted those tests, producing an uncertain report and an extra
specialist recovery sprint. Disjoint write sets alone did not make completion
independent; this was not an observed concurrent file-write race.

Before dispatch, inspect shared build/test contracts, establish discovery once,
or assign its preparation as a dependency with a clear owner. Do not let one
worker's private/unaccepted infrastructure become an implicit prerequisite for
another. Add a two-worktree regression where both add independent tests and
configured checks actually run both after integration; retain scope isolation.

<a id="run13-02"></a>
### RUN13-02 — P1: materialize private candidates through explicit handoff

Bounded explicit-handoff fix implemented in [FIX-0089](FIXES.md#fix-0089).
Planning gets actionable source/grant/conflict offers and mode-correct prompts;
invalid handoffs receive bounded corrections before dispatch. Arbitrary selective
multi-candidate recovery remains outside this item. Historical evidence follows.

Owner: coding agent planner/prompts/recovery. Sprints 4–6 named private candidates
in prose with resume_from null; sprint 6 parked because current-view file tools
could not inspect the named source. Sprints 7–8 restarted from the old shared
baseline. Sprint 9's explicit resume_from successfully supplied the retained
canvas implementation. Existing preservation was available but poorly used.

Use the existing resume_from/private-candidate or preserved_source_ref mechanism
when planning reuse, with complete grants and base-conflict checks. For selective
multi-candidate recovery, provide a concrete permitted read/materialization path
or explicitly authorize reconstruction; do not invent a commit-reading tool.
Reconcile the contradictory legacy/in-place senior prompt statements about
uncertain publication. Keep uncertain candidates private.

Related: FIX-0040, FIX-0060 and the still-open prompt finding in FIX-0068.
Earlier tests validate explicit provider reuse, not planner selection. Add a
senior-to-replacement regression proving source survives without manual Git
access, and that unavailable reuse produces one actionable correction rather
than repeated reconstruction. Preserve grant/conflict refusal coverage.

<a id="run13-03"></a>
### RUN13-03 — P1: make bounded implementation and verification tasks converge

Owner: coding agent assignment, repair and acceptance policy. Seven candidates
were uncertain despite passing configured build evidence. Browser smoke testing
was conditional in the first canvas task; later tasks bundled recovery, gameplay,
observability, browser setup, state assertions and docs. Sprint 5's five passing
Chromium tests did not exercise the requested movement/mining/placement state;
sprints 5/7/8 exhausted two repairs. Sprint 9's implementation-only handoff still
needed bundle/count evidence. Gameplay stayed private and blocked save/load work.

Specify attainable per-task criteria and actual tooling/checks before dispatch;
split implementation and browser verification deliberately, preserving source
between them. Teach recovery to choose a smaller missing unit using the exact
report instead of reissuing the whole slice from baseline. Browser evidence must
exercise state, inventory and lifecycle behavior; compilation is insufficient.
Do not bypass OS publication safeguards or silently accept uncertain code.
Add bounded fixtures for missing browser capability, helper-only success,
repair exhaustion and retained-source verification handoff. Final product
acceptance must still require the real objective, including save/load.

<a id="run13-04"></a>
### RUN13-04 — P2: audit global command serialization and journal churn

Owner: OS workspace/exclusive/storage mechanisms; coding Git callers supply
workload. 6,960 of the retained 10,000 events are shell/installation ownership
events; 24,313 earlier events, including the parallel phase, were pruned.
Workspaces.command serializes trusted Git reads as well as writes under that
installation-wide resource. The tail alone has 1,740 release events and about
76.3 s of ownership. This establishes churn/serialization, not a measured
throughput bottleneck or deadlock.

Extend CONC-01 with a two-worktree workload containing repeated Git reads, builds,
long shell work and a finishing worker. Measure command count, wait/hold time,
event-loop delay and storage/event-retention cost. Evaluate safe batching and
resource granularity only from that evidence; preserve mutation exclusion,
FIFO/progress, cancellation and unknown-effect retention. Retain useful bounded
summary/transition evidence so short lock cycles do not erase the concurrency
diagnostics. Add cross-runtime and generic non-coding coverage as applicable.

<a id="run13-05"></a>
### RUN13-05 — P2: reduce protocol and execution-environment correction churn

Owner: coding agent reply/tool construction and provider protocol integration.
There were 67 malformed worker replies (23 during the first two sprints, 44
later), with XML-like prefixes and invalid JSON escaping; maximum consecutive
streak two. There is no evidence these came from concurrent-history mixing.
Twenty-one 8k cutoffs recovered successfully. FIX-0075 already raised the current
limit to 32k; that is prior work, not a fix performed by this investigation.

Investigate a reliable provider-supported structured action path and smaller
incremental edits while preserving strict validation. Replay the observed
malformed shapes in both serial and concurrent fixtures, checking isolation and
bounded correction rather than accepting arbitrary text around a tool call.
Surface schema limits and invocation-local scratch setup clearly: this run also
requested timeout 900 above the 600 schema bound, read a nonexistent pinned path,
submitted a non-unique patch, and used unset PW_SCRATCH in a later command.
Treat ordinary compile/test failures as repair observations. Verify any claimed
improvement under the current 32k setting without assuming the cap alone solves it.

<a id="run13-06"></a>
### RUN13-06 — P2: distinguish ancestor tips from accepted task contributions

Implemented in [FIX-0090](FIXES.md#fix-0090): distinct ancestry, source,
publication and kept nonempty-contribution facts in new summaries/UI. Old saved
merged fields remain ancestry-only and unverified; history is not migrated.

Owner: coding repository summary/UI projection. The parked sprint-6 worker had
no new commit and its HEAD equaled the accepted persistence baseline, yet
coding/repository-summary reported merged:true. The field measures ancestry,
not successful task publication. This repeats FIX-0068's open metadata finding
with a clean empty worktree instead of a dirty one; no incorrect merge occurred.

Expose tip ancestry, private/dirty delta and actual task publication/contribution
as distinct facts. Add summary coverage for untouched, interrupted, private and
accepted workers so an inherited baseline is never presented as accepted new
gameplay. Do not rewrite historical commit/report evidence.

<a id="memory-management-modes"></a>
## MEM-02 — OS automatic memory mode and explicit agent memory management — 2026-10-20

Status: open for implementation in the current version. User-requested planning
only; no implementation or configuration changed by this entry. Deliver both
work items below. Context: [memory ownership](memory-implementation-report-2026-10-20.md),
[saved-run measurements](memory-records-audit-2026-10-20.md),
[FIX-0066](FIXES.md#fix-0066) and [FIX-0070](FIXES.md#fix-0070).

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

<a id="os-memory-context-inspector"></a>
## MEM-01 — Inspect an agent's memory and effective context from the OS — 2026-10-20

Status: implemented in [FIX-0091](FIXES.md#fix-0091), including the read-only
drawer, retry metadata, node prompt correction and live/saved coverage. The
original design/acceptance criteria below are retained for traceability;
MEM-02's new memory management APIs remain outside scope.
Initial investigation: [FIX-0062](FIXES.md#fix-0062).
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
| The coding app already displays shared notes. | [ui-monitor.js:renderNotes](../src/polyinference/ui-monitor.js) reads memory/working and uncovered memory-note/ records. This is useful application state, not a general OS memory contract. |
| Memory is already an ordinary context block. | [agent/services.py:context](../src/polyinference/agent/services.py) creates agent-memory when supplied; ContextView.memory_snapshot_refs is currently empty there. Other agents may use entirely different IDs. |
| Original and prepared inputs are retained separately. | [runtime/context.py:ContextService.prepare](../src/polyinference/runtime/context.py) keeps the effect request unchanged, writes context-receipt/<operation_id>, and writes context-prepared/<operation_id> only after fitting the bound. |
| Preparation receipts already describe intervention. | They contain original_bytes, submitted_bytes, required_bytes, input_allowance, unit, policy, omitted_refs, summaries, compaction_operations and prepared_digest. No new runtime recording is required. |
| Model retries and summaries are distinct effects. | [runtime/model_retries.py](../src/polyinference/runtime/model_retries.py) records explicit retry roots/previous attempts; context.py marks summary calls with runtime/context-compaction. A newest-effect heuristic alone selects the wrong call during compaction. |
| Existing OS operation rows omit these relationships. | [ui_os.py:runtime_view](../src/polyinference/ui_os.py) exposes process, kind, timestamps and causal parent, but not retry markers or context references. Extend this small projection rather than fetching every full request during polling. |
| Prompt inspection can show the wrong input version. | [snapshots.py:detail](../src/polyinference/snapshots.py) reconstructs Prompt from the original context.parts. A retained native userMessage may override it; neither path uniformly identifies effective prepared context. Model-node matching by logical_step_id also misses OS retries with new step IDs. |
| Read-only access and saved evidence already exist. | [ui.py:TestUI.record and make_server](../src/polyinference/ui.py) provide /api/record and /api/artifact. snapshots.export_run includes records, revisions and exact artifact bytes in schema_version 2. |
| OS projection refreshes independently of graph checkpoints. | TestUI.view rebuilds runtime_view before its checkpoint cache return. Derive the new operation metadata there; do not cache it only with node history. |

The current [runtime boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md#context-preparation-and-output-recovery)
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
| [src/polyinference/ui_os.py](../src/polyinference/ui_os.py) | Extend runtime_view operation rows with small context/relationship/outcome metadata from the same records snapshot. Include no artifact bodies. |
| [src/polyinference/ui-monitor.js](../src/polyinference/ui-monitor.js) | Add shared live/saved readers, pure invocation-selection helpers, process/operation actions and the context drawer. Reuse existing drawer, Back, Refresh, record and artifact affordances. |
| [src/polyinference/ui.html](../src/polyinference/ui.html) | Preserve HTTP status in API errors if needed; invalidate pending inspections on drawer close; render explicit prompt-origin labels. Add only small styling/control changes needed by the existing drawer. |
| [src/polyinference/snapshots.py](../src/polyinference/snapshots.py) | Make node Prompt distinguish effective prepared input from original input. Include linked retry attempts for a model node using provenance, not only logical_step_id, while keeping summary helpers separately identified. Apply the same projection in live node details and export_run. |
| [README.md](../README.md) | Describe the new control and its retained-invocation scope after implementation. |
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


<a id="sim-inference-ui"></a>
## SIM-02 — Opt-in inference pacing and fault modes — 2026-10-21

Status: implemented; verification recorded in [FIX-0096](FIXES.md#fix-0096).
Implements [FIX-0095's proposal](FIXES.md#fix-0095) under the user's later explicit
implementation request. SIM-01 below remains the concurrency-only launch preset.

UI --sim-inference reveals normal, normal and buggy, and slow and buggy modes before
Start. The default selection is 30 shared output TPS, batch 2, bug rate 5%, with an
optional seed and advanced timing controls. Normal/no flag retain the original
AgentConfig/client path. Buggy/slow configs explicitly pin settings in the optional
application config subclass and reinstall only the local-lane adapter on recovery.
The selected batch beats legacy/environment capacity without altering defaults,
later launches, custom Anthropic fields, old state or ordinary default config pins.

The application adapter supplies virtual shared decoding, startup/prompt latency,
seeded speed/stalls, normalized transient/output failures and endpoint restart
cooldowns. The OS retains admission, budgets, grants, completion bounds, recovery
and uncertainty; its only addition is a generic operation-aware HTTP adapter hook
and cancellation-safe terminal invocation. Actual usage survives discarded output;
diagnostics distinguish decisions, applied faults, real provider facts and progress.

This is a buffered service approximation, not a GPU/KV/model-quality emulator.
Only new calls during cooldown fail; already submitted calls can finish. A seed
repeats decisions for the same operation IDs, not all concurrent wall timing. A
coordinator crash stays conservatively uncertain even if a simulator diagnostic
receipt exists. Full provider responses are retained as diagnostic artifacts with
the existing snapshot/storage limits; partial actions never execute.

Ownership/record schema: [module guide](../docs/modules/inference-simulation.md).
Controls/limits/recovery: [usage](../docs/guides/sim-inference.md) and
[settings reference](../design-docs/simplified-os/AGENT_SETTINGS.md#optional-application-inference-simulation).
Regression checks are in test_inference_simulation.py and the real UI script tests;
actual final counts and environment limits belong in FIX-0096.

<a id="sim-batch-ui"></a>
## SIM-01 — Launch-scoped Claude batch simulation — 2026-10-20

Status: implemented in [FIX-0092](FIXES.md#fix-0092) under the authorized queue.
The original design/required checks below are retained; actual fixture/live
verification is in that entry. Related research: [FIX-0061](FIXES.md#fix-0061).
README identifies this file as the current-version issue tracker.

### Requested behavior and scope

`polyinference ui --sim-batch 2` should launch the usual UI with Claude Haiku as
the local inference stand-in, two local inference slots and capacity for two
workers. No custom JSON or environment export should be needed. The existing
Start run interaction remains; this flag does not invent an objective or bypass
project selection. The override belongs to this UI invocation: new runs created
by that server use it, while a later `polyinference ui` uses its normal config and
inherited environment. Do not write the flag into source defaults, user settings,
credential files, shell profiles or os.environ. Existing environment values remain
unchanged; absent the flag, their existing behavior remains supported.

Persist each created run's effective config in its existing config.json/export,
so diagnostics and exact-config recovery remain possible. This is historical
run evidence, not a preference to load for future launches. Opening old history
or --state must not rewrite its saved configuration or change old runtime pins.

### Findings and owning layers

- `cli.py:main` currently accepts ui --port/--config/--state, but no batch flag.
  `serve` constructs TestUI, whose configuration() reloads either a JSON config or
  greeting_config(); configure_run() then validates another merged dictionary.
- `agent/system_settings.py:ui_system_settings` supplies the complete default
  Haiku endpoint, max_inflight:1 and max_workers:1. `system_settings.py` defines
  Endpoint and generic limits. Its environment_capacity validator can overwrite
  local.max_inflight on every validation, including RuntimeConfig.system.
- `runtime/inference.py` already implements async HTTP and bounded Admission;
  kernel.open builds admission from endpoint limits. No GPU scheduler, Python
  thread pool, second API key or Message Batches integration is needed.
- Agent readiness and repository task-branch policy determine useful parallel
  tasks. Disabling task branches retains its one-editor rule. Setup, dependencies,
  senior queries, verification and acceptance retain their current ordering.

Place the flag/preset in CLI/UI and the coding application's adjacent settings
module. The OS continues to receive ordinary validated Endpoint/max_workers
values. Keep Claude defaults and coding workflow out of generic OS admission.

### Implementation design

1. Add optional ui-only `--sim-batch N` (default None). Accept integers 1..16,
   matching the smaller of max_workers' 16 and Endpoint.max_inflight's 32 limits.
   Reject zero, negatives, fractions and larger values with an argparse error.
   Thread the optional value through serve and TestUI as an instance attribute;
   preserve existing call signatures by adding an optional keyword parameter.
2. Reuse/extract a complete Haiku Endpoint factory next to ui_system_settings,
   used by both default UI configuration and the simulation preset. Default fields:
   protocol anthropic, base_url https://api.anthropic.com/v1, model currently
   claude-haiku-5-5, api_key_env ANTHROPIC_API_KEY, timeout_seconds 180,
   max_context_tokens 128000 and inference_location cloud. Recheck model support
   when implementing; no model/credential access has been tested in this task.
3. Resolve a fresh base configuration, then apply a pure, validated simulation
   overlay: worker binding local, max_workers=N, local.max_inflight=N and
   local.reserved_context_tokens=max(existing reservation,
   N * local.max_context_tokens). Preserve per-call input/output limits, real
   budgets, finishing reserves and configured senior/cloud provider behavior.
   For --config with an Anthropic local endpoint, clone its complete fields,
   preserving custom model, URL, credential reference, timeout and prices. For a
   non-Anthropic local endpoint, the explicit simulation flag selects the complete
   default Haiku factory instead. Announce the effective provider/model and slots
   so this replacement is visible. Respect other role bindings; a non-worker role
   already bound local will share that lane. Preserve relative-path resolution.
4. Explicit CLI selection must beat POLYINFERENCE_LOCAL_BATCH_SIZE, including a
   stale value of 1. Do not temporarily mutate the environment or edit config JSON.
   Use validation context to suppress only the legacy capacity environment overlay
   when resolving an explicit simulation preset, then validate the complete merged
   configuration. Thread this context through initial JSON/default construction
   and configure_run revalidation. Never pass local={max_inflight:N} as an endpoint:
   it loses required model and provider fields. Revalidate after complete-field
   updates rather than relying on model_copy(update=...) to perform validation.
   Treat RuntimeConfig.system as a view of resolved values; if that property is
   used, it must not reread the ambient capacity override and undo the selection.
   No serialized simulation flag or new generic runtime setting is required.
5. Apply the overlay consistently whenever that TestUI instance builds a fresh
   config: UI defaults, repository selection, Start run, effective-config display
   and per-run config persistence. Keep the unmodified base independent of the
   result. A second TestUI instance without the flag must have normal defaults.
   Show a concise launch message with simulated slots, worker cap and the remote
   nature of Haiku; two slots mean a maximum, not guaranteed two active requests.
6. Validate the complete effective config and a nonempty referenced API credential
   before starting a simulation run, with a sanitized actionable error if missing.
   Keep startup failure observable through the existing UI launch-error/export
   path; do not let an unhandled credential exception kill the server. Continue
   using load_saved_credentials before UI bootstrap (existing environment wins).
   Retain native Anthropic framing: POST /v1/messages, x-api-key,
   anthropic-version:2023-06-01, system outside messages, final user turn,
   model and max_tokens. stream:false permits concurrent requests. Keep the
   existing response classification, retries and credential redaction. No automatic
   billed generation is needed merely to open the UI. Valid config/credential
   presence cannot guarantee network, billing balance or account model access.

### Required acceptance and verification at implementation time

- CLI parsing and plumbing: omitted flag preserves behavior; 1, 2 and 16 reach
  TestUI; invalid inputs fail; --port/--config/--state continue to work.
- Launch isolation: construct a simulated manager and then a normal manager in
  the same interpreter; only the first has the override. Check no environment,
  input JSON, global defaults or old saved runs changed. Also exercise separate
  CLI launches. Preserve deliberate pre-existing environment settings.
- Precedence through the full startup path: with environment batch size 1,
  --sim-batch 2 must produce max_workers:2, local.max_inflight:2 and sufficient
  reservation in configuration(), configure_run(), saved config and kernel
  Admission. Cover absent/malformed stale environment values with an explicit
  valid flag, grouped JSON, complete Endpoint preservation and resolved system
  views; do not accidentally weaken ordinary no-flag environment validation.
- Provider startup regression: default flag path must construct the real
  HTTPInference adapter with mock transport while preserving its actual headers.
  Assert full URL, model, headers, payload and physical location; assert senior
  Codex settings survive. Cover custom Anthropic settings and non-Anthropic
  replacement. Missing/blank credentials and fixture 401/404/429 responses yield
  visible sanitized diagnostics, without treating retries as new worker capacity.
- Meaningful concurrency: use two independent scripted worker tasks and the real
  adapter/admission path with a blocking mock or local TCP fixture. Demonstrate
  two overlapping requests, no third concurrent request, independent histories,
  and a waiting third request admitted when either slot completes. Check token
  reservation release and existing uncertainty retention; do not require paired
  completion. Repeat the baseline with one slot. The greeting demo intentionally
  requests one small worker, so it cannot prove two-slot occupancy.
- Preserve Git no-task-branch serialization and dependency/verification ordering.
  Verify history/export records retain effective settings. Use existing focused
  UI, saved-credential, Anthropic, endpoint/admission and grouped-settings suites,
  add regressions for this behavior, and run the required checks for the actual
  patch. If credentials/network are available, verify the selected model with
  the Models API and run a bounded live two-request smoke check; report separately
  from fixture evidence. A 429 still means shared account limits, not bad wiring.
- Update README, codex-haiku-setup.md, the central settings reference and fix history
  with usage, precedence, invocation scope and simulated-versus-real batching.

### Research sources and limits

Official Anthropic references: [Messages](https://platform.claude.com/docs/en/api/messages/create),
[authentication](https://platform.claude.com/docs/en/manage-claude/authentication),
[Models API](https://platform.claude.com/docs/en/api/models/list),
[rate limits](https://platform.claude.com/docs/en/api/rate-limits) and
[batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing).
Messages are stateless, so histories remain caller-owned. Organization limits
are shared. Concurrent calls emulate admission/slot refill; they do not reproduce
local GPU contention, token-step batching, KV memory use, latency or throughput.

This task inspected the current CLI/UI/settings, provider and kernel paths and
existing regression sources. No implementation/configuration changed, no tests
were run, no credentials were read and no live provider calls were made. The
checks above are planned requirements, not completed verification.

## In-place coding repositories — 2026-10-19

The coding agent now uses the supplied actual repository by default. The proposal
is [in-place-repository-plan.md](in-place-repository-plan.md); current maintenance
instructions and the agent/OS split are in
[RUNTIME_BOUNDARY.md](../design-docs/simplified-os/RUNTIME_BOUNDARY.md#in-place-coding-repositories).
Existing unrelated working-tree changes were preserved and are not attributed to
this implementation.

- `agent/repository.py` owns instruction resolution, actual Git initialization,
  integration/task branches, linked worktrees, scoped commits, failed-candidate
  reuse, dependency preparation, verified integration and deterministic reporting.
  The coding app installs it explicitly; runtime modules do not import it.
- Defaults create a unique branch from current HEAD. Explicit current-branch and
  no-new-branch instructions disable task branches and serialize editing. Named
  branches override the generated name. Later Git steering waits for active workers
  to drain. Changing to an existing branch at another commit requires a new run,
  preserving the task/evidence baseline. Unsupported actions produce a blocker.
- OS additions are attached directory resources, authority/content checks, mutation
  blocking after attached-workspace scope failure, generic cross-runtime filesystem
  leases, and trusted workspace-provider/publication bootstrap entry points.
  Generic raw/native agents still need no Git or coding workspace. No MCP platform,
  research-agent product or expanded shutdown recovery was added.
- Passing candidates update the actual root checkout before overall completion.
  Failed/uncertain candidates remain on real task branches and worktrees. Root/task
  branch, HEAD, index and source drift are checked before integration. Attached
  failures do not invoke destructive private-copy rollback. File capabilities cannot
  address Git/runtime control data; trusted shell retains its documented host access.
- Git and SQLite remain separate resources. The coding publication policy requires
  a real-integration receipt before advancing its recorded head. A completed merge
  whose report cannot be recorded is uncertain; record CAS does not make Git atomic.
- Review and acceptance check the integration checkout. The agent prepares locked
  npm dependencies or an explicit `dependency_prepare` argv through bounded shell
  capabilities. Granted source still takes precedence over generated outputs.
- The agent reports original/current/integration branches, commit and unfinished
  worker locations when stopping normally. UI, CLI status and JSON expose them;
  patch export reads the actual Git database. Acceptance requires no final copy-back.
  Optional artifact delivery remains available to other workflows.
- `repository_mode: "isolated"` explicitly retains the legacy private-copy path.
  Existing protocol fixtures select it; dedicated real-Git and default-UI tests
  exercise the new default. New coding runs use `agent-5-in-place-repository`,
  state schema `2.3`, and require fresh state. Historical runs were not migrated.

Verification uses disposable repositories and local provider fixtures: concurrent
merges, current/named branch overrides, policy inference before mutation, fresh
setup, failed-candidate handoff, external/staged file preservation, cross-run leases,
dependency preparation, steering, source/output classification, CLI export, default
UI providers and raw/native non-coding agents. No live-model or network npm
validation is claimed.

Verification completed in WSL using `.venv-linux` and Linux Node/npm 22:
`python -m pytest -q --tb=short --maxfail=3` passed **248 tests in 414.76 s**,
with no skips. The final immutable-native-snapshot metadata guard was then
verified with its new regression, native-worker, general-agent and capability
boundary suites: **27 passed in 17.47 s**. Ruff and `git diff --check` pass;
Git retains the pre-existing CRLF normalization notice for `test_setup_tools.py`.

## Coding policy separated from the existing OS functions — 2026-10-19

Status: implemented and verified: **201 tests passed**. This section
supersedes the implementation status of audit items 1, 2 and 6 below. The scope is
the current basic function set working for both a coding agent and a general
agent. There is no new research-agent product, MCP integration, discovery service,
or next-version OS platform in this change. Existing unrelated dirty files are
not attributed to this work.

The detailed maintenance guide is
[Current runtime and agent wiring](../design-docs/simplified-os/RUNTIME_BOUNDARY.md).
It documents registration order, the authority records, each agent/OS handoff,
failure ownership, restart requirements and compatibility. README and the OS
runbook/design reading routes link to it.

### What moved, and why

The computer-OS analogy now governs the actual call path: an agent program chooses
its task protocol and policy; the OS authenticates a process's requested operation,
enforces its authority and resource bounds, dispatches the installed handler, and
retains the outcome. Expensive bounded execution is inference; the inference
server still schedules tokens/GPU work.

- **Capability ABI and grants (OS mechanism).** `runtime/capabilities.py` registers
  typed arguments, effect class and whether a file workspace is required.
  Definitions are pinned across restart. The process grants the maximum set;
  `workspace-grant/<id>` narrows it, carries check names and explicitly controls
  path expansion. Registration is trusted local bootstrap, not permission for
  every model/process to call a tool. Direct and native calls use this same ABI.
- **Native protocol and tool exposure (agent/driver boundary).** The app-server
  driver builds its advertised tool schema from the selected descriptors instead
  of a hard-coded coding-tool list. The agent supplies its reply schema and phase
  instructions. `workspace="none"` uses an empty private native directory without
  a TaskSpec, Git store or file workspace. Native protocol definitions are pinned
  as well as capability definitions. Call IDs become durable subordinate effects;
  identical callbacks replay and changed arguments are rejected.
- **Workspace and checks (OS resources, agent selection).** The runtime no longer
  reads `task/project_setup`, `setup/completed`, `setup/checks`, `plan/` or a TaskSpec
  project-write extension to decide authority. `agent/runtime_policy.py` implements
  initial-setup check selection. It registers immutable command resources and
  updates the explicit grant. Worker load sets project expansion only for setup
  in project mode; prompts read the effective grant through `write_authority`.
  Empty/read-only file views are valid; callers select the required source closure.
- **Publication (generic transaction, coding invariants).** The OS checks the
  actual named resource/permit and performs atomic expected-version publication.
  It does not interpret `app/run`, `report/` or `head/provisional`. The coding app
  installs a policy for verification ownership, broker-minted commits/current
  parents, report ownership and private-failure rules. The same transaction still
  closes starts and captures outstanding workers when review is required.
- **Lifecycle/limits (OS identity, agent workflow).** A role called `senior` does
  not grant management privileges. The app passes the management flag explicitly;
  bare `RuntimeConfig` has generic roles/limits and zero control reserve. Coding
  defaults stay in `AgentConfig`; the old `review_token_reserve` spelling remains
  an input alias. Generic processes may finish with artifacts or no output.
- **Attempt updates (agent bug).** `AgentServices.task_attempt` validates the new
  record, normalizes prose to bounded reason codes and preserves full diagnostics
  in an artifact referenced by `polyinference/stop-detail`. Park, exception,
  cancellation, retirement, publication, setup retagging and recovery use that
  boundary. It also normalizes old invalid reasons while retiring a task. This
  fixes the 317-character interruption/retirement crash investigated below without
  teaching generic OS storage the coding application's schema.

### Wiring defects caught while making the boundary explicit

1. Moving `checks.configure` out of the file-tool implementation would otherwise
   bypass its old generation/content preconditions. Those checks now run in the
   kernel for **every registered workspace handler**, before handler dispatch.
   Agent-created requests bind current generation and content for workspace
   capabilities, including commit/private retention. Non-workspace capabilities
   do not inherit a workspace merely because the caller's graph state has one.
   The existing stale-view regression caught an initial helper change that
   replaced an explicitly supplied generation with the current value. The helper
   now fills only a missing generation, preserving explicit stale-intent rejection.
2. A non-workspace tool may legitimately have an argument named `generation`.
   Callback replay previously stripped that name unconditionally as workspace
   metadata. It is now preserved for non-workspace tools; the real stdio fixture
   sends it on a duplicated callback and verifies one handler execution.
3. A program's publication callback was originally only in memory. On restart,
   omitting app bootstrap could silently fall back to generic publication. The OS
   now persists the requirement under `runtime/publication-policy/<program_id>`
   and refuses new publication until the handler is reinstalled. No application
   data changes on rejection. Completed effects/receipts still replay; installing
   a handler does not change a previously failed operation's recorded result.
4. The coding app manually constructed process/status records separately from
   `Processes.register`. It now uses the same atomic OS registration as general
   agents, passing its explicit maximum capabilities and management flag. The
   runtime ports declare the services and callbacks actually used by bootstrap;
   required registrations no longer silently disappear behind optional checks.
5. Updated task-attempt records were often created with unvalidated
   `model_copy(update=...)`; old invalid notes could also fail before retirement
   replaced them. The application write boundary validates the merged value and
   retains diagnostics, and cancelled setup is not resurrected on the next run.

### Verification and practical limits

- `tests/test_capability_boundary.py`: typed grant/schema/effect/argument denials;
  a real app-server stdio transport with a non-coding output grammar/tool, ordinary
  `generation` data, duplicate replay and rejected arguments; generic publication
  under an unrelated resource name; external-write uncertainty; role privilege
  isolation; capability/protocol ABI checks across restart; missing-publication-
  policy restart refusal/reinstallation; workspace handler source preconditions.
- `tests/test_agent_transitions.py`: long valid review note, normal and injected
  old-invalid attempt data, setup authority visibility, senior replacement,
  complete diagnostic retention and replay without duplicate activation.
- Existing coverage exercises coding setup/check selection, native workers,
  publication guards, failed-worker drain, scope/isolation, cancellation,
  inference bounds, recovery, outputs and UI/export paths. Fixtures that depended
  on implicit TaskSpec privileges were changed to configure explicit grants.
- Final complete suite: **201 passed in 330.58 seconds**, using
  `.venv-linux/bin/python -m pytest -q --tb=short --maxfail=3` in WSL. The focused
  boundary/transition/UI checks also passed (**14 tests**). During validation the
  suite caught an outdated UI export compatibility-marker assertion and the
  stale-generation helper regression described above; both are corrected.
- `.venv-linux/bin/python -m ruff check src tests` and `git diff --check` pass.
  Documentation links were checked locally. Git reports an existing CRLF
  normalization notice for `tests/test_setup_tools.py`.

All execution here uses local fixtures and disposable repositories. No fresh
live-provider or live-bubblewrap validation was performed. Historical run exports
and state were not modified. New state uses kernel compatibility marker
`simple-os/2`, coding program `agent-4-capability-boundary`, state schema `2.2`.
This is an ABI change within the current basic OS, not the planned integration
platform. Use a new run/state directory; older runs require their pinned code and
are not automatically migrated.

The audit's broader fault-scope/circuit taxonomy, persistent scratch lifetimes,
phase-specific output strategy, structured diagnostic causes, and separate
business-acceptance contracts remain deferred. They are not prerequisites or
claims of this bounded implementation.

## Generalization audit of this chat's fixes — 2026-10-19

Status: historical architecture/source review with two local probes. The current
implementation status is in the section above; the following describes the code
at the time of the audit, before those changes.
This audit covers the fixes documented below, including the initial provider,
authority, recovery, delivery and process changes, then telemetry, reporting,
output-limit and tool-environment fixes. The long interruption-reason defect
was investigated-only at audit time. Existing unrelated working-tree changes are not attributed
to this chat merely because they appear in Git's diff.

### Use an OS boundary, not an incident-patch boundary

The useful comparison is a computer OS providing mechanisms to applications.
Here the applications are agent programs and expensive execution is inference.
The repository's simplified-OS design already makes this distinction: the kernel
owns processes/effects/admission/ownership, while the task ledger and sprint
decisions belong to the agent. The runtime admits bounded inference operations;
the model server retains responsibility for token/GPU scheduling. A durable agent
continuation is not a copy of hidden reasoning or a conventional CPU register set.

| Computer OS concept | Agent/inference counterpart | Boundary to preserve |
| --- | --- | --- |
| Process and execution context | Agent identity, program version, context references, continuation and outstanding effects | A process must not require a coding task or a Git commit to exist or finish. |
| System call and device driver | Brokered capability invocation and provider adapter | Validate grants/arguments/effect identity; keep coding reply grammar in the calling agent. |
| Address space, filesystem namespace and temporary storage | Private source view, environment/config/cache, artifacts and scratch | Separate source, disposable data and persistent process state, with explicit lifetimes. |
| Resource limits and admission | Tokens/context reservations, model concurrency, bytes, deadlines and spend estimates | Report the exhausted resource; the agent decides how to simplify its work. |
| Error codes and fault containment | Typed failure category, fault scope, termination/effect certainty and causal references | A malformed request, an unavailable endpoint and unknown remote execution need different handling. |
| Journal and recovery | Durable intent/result IDs, receipts, checkpoint references and linked new attempts | Replay preserves the old result; a new execution requires an authorized new identity. |
| Kernel trace buffer and observer processes | Bounded native telemetry and UI/terminal reporters | Dropping diagnostics must not change execution facts or replace the primary failure. |

There are no incident-ID or Minecraft-specific branches in the reviewed `src`
tree. The remaining hard-coding mostly targets the reference coding agent's
workflow, rather than a particular incident. Some constants are legitimate safety
bounds; replacing every literal with configuration would not address the important
architectural coupling.

### Foundations worth retaining

- **Telemetry fix — OS mechanism, broadly applicable.** `NativeEventLog` bounds
  observations while terminal state, final reply and usage survive independently.
  This is the equivalent of a bounded trace buffer, rather than execution depending
  on whether logs fit. The Codex event names belong in that protocol's driver.
- **Request framing — appropriate agent/driver split.** The agent adds an explicit
  current request after historical replies, while the Anthropic adapter checks its
  supported request shape. The final-request fix applies to phase transitions,
  not just the historical Haiku failure. Requiring a final user turn for all
  Anthropic requests is a deliberately restricted common subset, not support for
  every model's possible prefill capabilities.
- **Recovery identities — OS mechanism with agent policy above it.** Original
  effects remain immutable, recovery attempts are linked and bounded, and unknown
  remote execution retains resources until reconciled. The coding agent's choice
  to rebuild reconciliation after a failed assessment belongs in its controller.
  A killed local transport is correctly not proof that remote execution stopped.
- **Process completion and file delivery — useful separation already introduced.**
  `Processes.finish` accepts artifact-only or empty results. `Outputs` delivers
  explicit file artifacts with baseline checks and intent/receipt replay, without
  deciding whether the user's objective is met. The coding agent gates delivery
  on its own acceptance. These are reusable beyond code generation.
- **Source isolation — generalized cause, not a cache-name exemption.** The npm
  fix isolates HOME/XDG/temp paths for both checks and shell. It does not ignore
  arbitrary `.npm` files or weaken source grants. npm/pip environment variables
  are compatibility details appropriate to an execution-environment profile.

### Highest-value places to generalize

1. **Registered capabilities and effective grants — OS/agent boundary.**
   `runtime/tools.py:checks.configure` reads `task/project_setup`, `setup/completed`
   and `plan/`; `configured_checks` resolves `setup/checks`; kernel check grants
   also special-case that record. `Workspaces.extend_setup_scope` uses a
   `polyinference/project-write` flag on an agent TaskSpec. These mechanisms know
   the reference application's lifecycle. An OS should enforce a versioned grant
   for a resource/capability and return its effective authority; the agent should
   decide when setup may select/seal checks or request additional explicit paths.
   Derive prompt-visible authority from that same grant, rather than separately
   reconstructing it. This addresses the latest run's missing setup-authority
   explanation without adding another phase-specific prompt exception. Keep
   explicit-scope restrictions, generation checks and immutable check provenance.

2. **Native brokerage must not prescribe an application's return protocol — OS
   provider adapter and capability ABI.** Protocol registration is generic, but
   `CodexAppServer.generate_job` advertises a fixed coding-tool schema and tells
   every brokered job to finish with `candidate`, `assessment` or `needs_review`.
   The kernel's subordinate-effect allowlist and callback construction likewise
   assume a code workspace and classify just three file tools as reads. Register
   capability schemas/effect classes/resource requirements, then pass the granted
   subset through the adapter. Let the calling agent supply phase grammar and
   instructions. A researcher with a brokered non-file tool should not need a
   TaskSpec, coding response or fake workspace to use the same OS. The current
   non-coding regressions cover HTTP and read-only native fixtures; they do not
   prove arbitrary brokered applications work. This is remaining coupling around
   the generalized registration fix, not a regression caused by event retention.

3. **Fault scope and retry eligibility — OS fault handling, agent recovery policy.**
   HTTP stop reasons are already normalized across four protocols, but kernel
   result handling still checks particular Python exception classes and ad-hoc
   extension keys. The permanent-failure circuit is keyed by role/model/endpoint,
   phase/protocol and configuration, not error category/code or request cause.
   Different request-specific invalid-input failures therefore accumulate in one
   counter. Two unrelated malformed requests can block later healthy requests in
   the same bucket. Like an OS distinguishing a caller's EINVAL from a failed
   device, classify fault scope explicitly: operation/input, credential/account,
   endpoint, resource limit, application, or unknown execution. Endpoint health
   and repeated equivalent bad requests need separate containment policies. Keep
   exact original intents and explicit recovery; do not turn all errors into an
   automatic retry loop. Retry-after metadata is currently retained, not an
   implemented general backoff scheduler.

4. **Tool environment as an owned resource — OS process/environment lifetime.**
   The source-contamination fix creates a fresh HOME/config/cache for each
   invocation and destroys it afterward. That is safe for disposable housekeeping,
   but local tool configuration or user-local installations cannot survive a
   later shell/check invocation. A normal process environment has a defined
   lifetime across child commands. Separate invocation scratch from optional
   process/workspace/run-owned tool state, preserving isolation from source and
   other principals. Account for its disk usage and specify cleanup/restart
   behavior. Current temporary environments sit outside the workspace scanner's
   budgeted tree. Trusted provider authentication, brokered tool homes and
   host-maintenance commands need distinct profiles; applying the same empty
   HOME to the Codex provider would break its authenticated service context.
   Shared subprocess supervision can consolidate group termination, deadlines,
   output draining and lease cleanup while retaining these separate profiles.

5. **Output-limit recovery as an agent strategy using OS resource facts — mostly
   agent policy, with a normalized OS outcome.** `AgentServices.model_result`
   targets 4 KB then 2 KB, repeats the same token cap, and advises scaffolds/file
   patches or a smaller planning increment. This is bounded coding-agent policy,
   not a general inference resource manager. A fixed byte target is not a token
   budget and may not solve a thinking-only cutoff or fit another output schema.
   Give the agent structured limit/usage/completion facts and let its phase/task
   strategy choose a smaller action, decomposition, compact response or an
   authorized budget change. Centralize the strategy's limits instead of repeating
   4,096 in both recovery and `response_budget`. Keep the raw-query-only automatic
   eligibility until stronger effect guarantees exist: a native job may already
   have executed tools, so copying the message that 'none of its actions executed'
   to native retries would be incorrect. The OS should enforce the chosen budget
   and retry identity, not decide to write a scaffold.

6. **Typed lifecycle updates — agent application persistence.** The latest
   317-character `stop_reason` crash exposes a family of writes, not one oversized
   string. The controller's exception path also writes up to 2,000 characters to
   the same 256-character field; settlement uses unbounded reasons, while worker
   parking validates only before `model_copy(update=...)`. Introduce an agent-owned
   validated transition/write boundary with short reason codes and complete
   diagnostics retained separately. Apply it to park, exception, cancellation,
   retirement and recovery, including old invalid records. The OS generic JSON
   store should retain its transaction/version contract, not interpret coding
   attempts. This is analogous to an application validating its own database
   objects, separate from filesystem or storage-driver correctness. This defect
   was diagnosed before this audit; the implementation section above records its fix.

7. **Diagnostic causes as structured references — observer/application boundary.**
   The terminal reporter now cannot replace a runner outcome, which generalizes
   well. The summary still treats `app/run.blocker` as either arbitrary text or
   an operation ID and resolves only `effect/<blocker>`. Keep a structured cause
   with owner/layer, category, operation/resource reference and detail reference,
   and make terminal/UI/export render the same facts. Application task failures
   and observer failures should remain separate from OS process/effect failures.
   Numeric caps on event retention or reporting errors are reasonable defaults;
   they are less important than getting this ownership and causality right.

8. **Business success and semantic progress — agent policy, not kernel policy.**
   Objective propagation is generic, but prompts alone cannot prove feature
   completion. The shared setup/task/final check selection is still a known open
   issue. Separate prerequisite, task and final acceptance contracts in the agent;
   let the OS execute pinned checks and bind evidence to revisions. Likewise,
   excluding memory from the review fingerprint helps, but pending/interrupted
   task metadata can still change without product progress. The agent should
   define useful progress; the OS should enforce budgets/deadlines and report
   consumption. Renaming tasks or checking Node availability must not stand in
   for an implemented product.

### Order and verification

First fix the invalid agent lifecycle records and expose effective authority to
setup. Then establish the capability/grant boundary and fault taxonomy, since both
make subsequent generalization safer. Follow with explicit environment lifetimes
and phase-aware response strategies. The existing scheduler, effect journal and
uncertain-execution rules are foundations to preserve during these changes.

Add cross-application regressions, not just more variants of the original incident:
an artifact-only agent; a native agent with a custom brokered tool and non-coding
schema; two unrelated bad requests versus repeated credential failure; linked
retry after a resource cutoff versus uncertain execution; a two-command tool
setup/check sequence; scratch quotas and restart cleanup; long application
diagnostics across park/retire/replay; and observer failures with stable causes.
Assert these invariants rather than fixing tests to the literal 4 KB retry target.

Verification in this audit: source/design/test review, a search finding no incident
IDs or Minecraft-specific runtime branches, and two read-only Linux probes. The
probes confirmed that different request contexts share the circuit bucket, and
that a HOME `.toolrc` disappears before the next invocation; both temporary
environments were cleaned. The latter demonstrates the current lifetime contract,
not a newly observed production failure. No providers were contacted, no historical
state was changed, and the full regression suite was not rerun for this analysis.
The last full verification at audit time was 188 passed as recorded below. Current
verification is recorded in the implementation section above.

## Agent interruption bookkeeping breaks senior recovery — 2026-10-19

Status: investigation preserved below; the attempt-validation and prompt-authority
fixes are now implemented in the boundary refactor documented above.
Incident: run `e94b7049eeda`, repository
`/home/mawa/projects/testing/mincraft-6`.

### Ownership: agent implementation, not a demonstrated OS defect

Here, "agent" includes the Python controller/worker workflow and its prompt
assembly, not just the model's decisions. The design explicitly assigns task
ledgers and sprint decisions to the agent (`design-docs/simplified-os/README.md`,
section 3). `TaskAttempt` is an agent application contract. Its invalid update is
written by `agent/worker.py` and later rejected by `agent/controller.py`.

The OS record service intentionally stores generic application JSON with
compare-and-swap/atomicity guarantees; it does not interpret or validate each
agent's task schema. Persisting the payload supplied by the agent is not evidence
of a storage bug. Schema validation for this record belongs at the agent's write
boundary. Likewise, omitting already-supported setup authority from the model's
inputs belongs to agent prompt/context assembly.

The observed OS behavior was sound: model/tool operations settled, check failures
were recorded against the correct source revision, temporary caches stayed outside
source, leases/capacity were released, and the uncommitted replacement plan was
not partially activated. The controller's decision to pause after its own exception
is agent policy. No new OS scheduling, isolation, grant-enforcement, or transactional
storage defect is demonstrated by this run.

### What stopped the run

The visible blocker is an agent-side `TaskAttempt.stop_reason` validation failure,
not a failed model operation. `contracts.py` types this field as `Identifier`,
whose maximum length is 256 characters. The setup worker returned a valid
`needs_review` reply with a 317-character explanation. `agent/worker.py:park`
first validates the previous attempt, then uses `model_copy(update=...)` to put
that explanation into `stop_reason`. Pydantic does not validate those updates.
The generic record store consequently persisted an invalid attempt at
`attempt/setup-project` revision 4. Its complete explanation is also retained
in the task's `exception` field and model history.

The worker parked successfully at `05:48:19Z`, released its verification permit,
and allowed senior review to continue. Senior inference completed successfully at
`05:48:38Z`: the proposal retired `project_setup` and created
`bootstrap_game_project`, with explicit paths for `package.json`, a lockfile,
HTML, JavaScript, styles and README. The proposal was durably staged in
`review-batch/active`, state `applying`.

`ProjectAgent._apply_review` then tried to validate the old attempt before
replacing its reason with the valid short code `superseded_by_plan`. That read
rejected the already-persisted 317-character value. The controller paused the
run and exposed the Pydantic exception as the blocker. The atomic plan activation
had not happened: no `task/bootstrap_game_project` or `plan/1` was committed.
There were no uncertain effects; both model lanes and both critical sections
were released. This is a recoverable agent application-data/schema defect,
rather than evidence of unfinished provider execution.

### Why setup asked for review

Setup selected `production-build` (`npm run build`) while the source contained
only `.gitignore`. All six recorded check invocations returned a normal failed
check, exit 254, because `package.json` did not exist. Reconciliation/assessment
repeated without creating the scaffold, including two assessment replies asking
for repair. The worker eventually asked to expand its `.gitignore`-only scope.

That authority diagnosis was misleading. The run used `write_scope=project`,
and its setup task specs already contained `polyinference/project-write=true`.
`Tools.run` and `Workspaces.extend_setup_scope` can extend the setup grant when
new explicit project paths are written; the existing setup regression exercises
this through a new file created by shell. No rejected scaffold-write attempt is
present in this export. However, setup's pinned inputs expose the initial
`assignment.write_paths` without the project-write policy or an explanation of
automatic extension. The bootstrap prompt asks for prerequisites without making
that authority explicit. This is an agent context/prompt defect, not
proof that the runtime forbade those files. The previously documented distinction
between setup checks and final product acceptance remains a separate policy issue.

The previous housekeeping fix is working: npm logs point to
`state/tool-environment-*/cache/npm`, the source digest stays stable across the
checks, and no cache-related write-scope violation occurred.

### Repair direction and verification

- Keep `stop_reason` consistent with its contract: use a bounded reason code and
  retain the complete human explanation separately, or deliberately introduce a
  bounded diagnostic-text contract. Do not silently write arbitrary prose into
  an identifier field. Audit other interruption/exception writers, including
  the controller path that currently allows up to 2,000 characters.
- Validate updated task-attempt records at the agent's write boundary before
  persistence, not just their old values. Do not add task-specific validation to
  the generic OS record store. Include recovery/retirement of already-invalid
  persisted attempts; fixing only new writes will not unblock this staged review.
- Supply setup with its effective write authority and explain when new project
  paths may extend the seed scope. Preserve explicit-scope restrictions.
- Add an integration regression with a long valid `needs_review.reason`, senior
  replacement/retirement, and restart/replay of the staged review. Check that
  the full explanation survives and the replacement is activated exactly once.

A read-only probe using the installed Linux dependencies and this export
reproduced the mismatch: `model_copy` accepted 317 characters, then
`TaskAttempt.model_validate` rejected the serialized copy with
`string_too_long`, maximum 256. The export confirms `review-batch/active=applying`
and the absent replacement task. No code changes or historical-state edits were
made for this investigation; the regression suite was not rerun.

## Tool housekeeping caused a false write-scope pause — 2026-10-19

Status: OS fix implemented and verified. Incident: run `667b821fa4b0`, repository
`/home/mawa/projects/testing/minecraft-5`. This is separate from the provider
output-limit and native-event incidents below.

### Failure sequence and ownership

The run was still in automatic setup. The setup workspace's write grant contained
only `.gitignore`; senior planning and development had not started. Setup selected
`npm test` as its check before a `package.json` existed. The command returned 254
with an ENOENT error for that missing manifest.

The OS launched the check with `HOME` set to the private source root. npm therefore
created `.npm/_logs/2026-10-19T05_24_02_715Z-debug-0.log` and
`.npm/_update-notifier-last-checked` inside the workspace. The workspace scanner
uses fixed exclusions rather than `.gitignore`; `.npm` was not excluded. The check
first became inconclusive because it appeared to modify source. At the following
worker `acquire`, `Workspaces.preserve_delta` rejected those extra files with
`Private changes exceed write scope`, before issuing a verification permit.

That host exception paused the task/process, and the controller closed further
starts and durably paused the run. The driver then exited. This was not a model
operation waiting for a reply: all eight recorded OS effects had succeeded, no
effect was uncertain, and no execution lane or lock remained held. The failed
npm subprocess was represented in check evidence. The private workspace survived,
but there was no publication, final report or automatic retry of the host node.

The primary stack bug was placing ordinary tool housekeeping in assessed source.
The scope guard correctly rejected files outside the setup grant. Selecting a
product check before its manifest existed is a separate agent/setup-policy issue;
this change does not make that command pass or weaken acceptance.

### Implemented fix

- `runtime/tool_environment.py` supplies one temporary environment per check or
  shell invocation, under runtime state and outside the workspace tree. `HOME`,
  XDG cache/config/data/state, temporary-file paths, npm cache and pip cache all
  point into it. Commands retain their source working directory and existing
  bounded execution/output policy. They do not inherit the operator's home.
- `runtime/tools.py` and `runtime/shell.py` share this environment. Bubblewrap
  receives an explicit writable `/tool-environment` bind separate from
  `/workspace`. Cleanup completes before releasing the installation-wide shell
  lease, including failure, timeout, cancellation and process-start failure.
- `runtime/workspace.py` versions the environment policy in the execution
  environment digest as `isolated-tool-environment-v1`.
- Source scanning, evidence invalidation and write grants are unchanged. There
  is no new `.npm` ignore exemption: an actual unauthorized `.npm/source.js`
  written in the source root must still invalidate evidence and fail preservation.

### Verification and operational limits

`tests/test_tool_environment.py` covers successful, failed, timed-out, unavailable
and cancelled checks; shell housekeeping; sandbox mount/path mapping; and genuine
out-of-scope source changes. A real native Linux Node/npm regression runs
`npm test` without a manifest: it remains a failed check, its source revision stays
unchanged, and delta preservation succeeds. Temporary directories and shell leases
are checked after cleanup. The sandbox test verifies mount construction; it does
not execute bubblewrap.

The full Linux suite passed: **188 passed** in 201 seconds, including the native
npm regression and browser-script checks with Linux Node 22. Ruff passed for
`src` and `tests`; whitespace checks passed for the changed files.

The historical paused run and contaminated workspace were not rewritten or
resumed. Restart the backend to load the fix for new invocations. A missing
`package.json` still needs a suitable check or the project files it requires.

## Output-token cutoff paused a recoverable worker — 2026-10-19

Status: implemented and verified. Incident: run `f5bcd770dbe6`, repository
`/home/mawa/projects/testing/minecraft4`, worker `worker-1-content_registry`.

### What happened

Setup completed, reconciled, passed assessment and published. The senior planning
call also completed successfully. The first development worker listed its files,
then its next model query (`model-1`, operation
`sha256:ff05b9c0014897bef89fb917e4897446f2131565d4481de428b10c42f4c2e32a`)
stopped at `2026-10-19T04:56:11Z` with `Anthropic did not complete: max_tokens`.
The configured per-call output budget was 8,000 tokens. No development file write
had executed; the only development tool observation was `files.list`.

The assignment was a substantial content registry. The stop reason confirms an
output-token cutoff, but the old adapter discarded the partial reply and usage,
so the export cannot establish how much of the budget was thinking versus visible
JSON. Haiku 5.5 thinking is enabled by default and counts toward `max_tokens`;
see the official [migration guide](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide).
This was a confirmed stopped generation, not an unknown transport failure.

The host correctly refused to execute incomplete JSON. The stack defects were
treating this cutoff as a generic terminal provider failure, pausing the whole
agent without a smaller-response recovery, and losing provider usage/stop metadata.
The export's unpriced call and missing actual-backend fields reflect that loss.

The previous incident's fixes were working: the senior native call retained 20
events while discarding 1,212 text deltas, and the UI reported the durable paused
state with the original blocker and no terminal-reporting errors.

### Fix

- `runtime/inference.py`: output-token stops produce a typed `IncompleteGeneration`
  observation, with partial visible text, provider/model ID, normalized usage,
  stop reason and the requested output limit. Thinking text is excluded. Equivalent
  chat `length`, Responses `max_output_tokens`, and Gemini `MAX_TOKENS` stops receive
  the same classification. The adapter never returns partial text as a completed
  actionable response, even if that text happens to be syntactically valid JSON.
- `runtime/kernel.py`: keep the original operation failed/confirmed stopped, retain
  its incomplete-output artifact and classification, record the actual backend and
  provider-reported token usage, and settle budgets using that usage. Output limits
  do not count as permanent authentication/request failures in the circuit breaker.
- `agent/services.py`: recover only classified, known-stopped HTTP model queries.
  Use new, durably linked operation IDs within `max_model_recoveries` (default two),
  preserving the original request/result. Each new request adds trusted feedback
  asking for a smaller complete response, with progressively lower visible-JSON
  targets (normally 4 KB, then 2 KB). It never executes or continues the partial JSON.
  Scaffolds and subsequent small patches replace large whole-file responses.
- The actual configured output-token cap stays unchanged. The original objective,
  workspace grant, phase, model-call limits, recovery allowance, process deadline
  and final-phase reserve still apply. Unknown execution and other provider failures
  do not take this automatic recovery path. Exhaustion still pauses safely.
- Recovery requests/results are replayable without another provider submission,
  including after the recovery allowance is exhausted. Workers count actual durable
  model operations so recovery calls cannot silently consume the final-phase reserve.
- Worker prompts and pinned `response_budget` inputs now encourage small actions
  from the first call, before a cutoff occurs.

### Verification

`tests/test_output_limits.py` adds 11 cases covering visible and thinking-only
cutoffs, other supported HTTP protocols, recovery after one/two failures, immutable
replay, no partial tool execution, usage/budget settlement, finite exhaustion, and
the mandatory-phase reserve. The tests use local fixture transports, not live models.

The full Linux suite passed: **178 passed, 1 skipped** in 202 seconds. This includes
the earlier native-event, reporting, recovery and export regressions. The final
progressive response-size guidance was additionally verified by rerunning all
11 output-limit tests. Ruff passed for `src` and `tests`; whitespace checks passed.
The historical run and its failure records were not rewritten.

## Native event overflow and reporting failure — 2026-10-19

Status: fixes implemented; Linux regressions verified in the output-limit follow-up
above, superseding the initial verification limitation. This section concerns
run `daec3ddd8884`, distinct from the historical HTTP 400 incident below.

### Failure sequence

Setup completed and published successfully. The first senior planning operation,
`senior-1/model-0` (`sha256:a1bd9134b8ddbd719f11ff2745a978803a9d5ed58212fb30b6baee5a60afe8db`),
stopped at `2026-10-19T04:19:38Z` with `Native event limit exceeded`. The adapter
counted all native notifications, including text deltas, against a 2,000-event /
4 MB execution limit. The export did not retain the failed stream or identify which
threshold fired. The OS correctly kept the submitted operation uncertain and paused
the run. No development assignments had started.

The terminal reporter then evaluated `value.get("result", {}).get("error")` on
an uncertain effect containing `"result": null`. The resulting `AttributeError`
(`'NoneType' object has no attribute 'get'`) replaced the visible execution error.
The summary gave the reporter's error precedence over the durable paused state.

### Implemented changes

- `runtime/codex.py`: event retention is now a bounded rolling buffer, independent
  of execution. Streaming deltas are counted but discarded. Receiving more than
  2,000 notifications or 4 MB no longer ends a healthy call. Final assistant text,
  latest usage and terminal state are tracked independently, including notifications
  arriving before the turn-start RPC response. Tool callbacks still execute through
  the broker; their effects retain the existing durable audit trail. The buffer's
  bounds, transport line bound, reply bound and execution deadlines remain enforced.
- Native success results include retention counters. Failures carry bounded native
  diagnostics: received event/byte counts, retained/dropped counts, bounded method
  counts, and the last 24 event types/sizes. Failure summaries omit prompt text,
  response text and tool arguments. The kernel preserves these through native
  exception wrapping, in uncertain effect records or known-failure result extensions.
  The OS view and JSON export expose them.
- `ui.py`: terminal reporting handles null results. Printing, event parsing and
  reporting reads cannot replace a runner result or exception. Reporting failures
  are deduplicated and bounded in a separate `reporting_errors` metadata list, which
  is included in saved/exported run metadata.
- `snapshots.py` / `ui.html`: summaries preserve a durable paused state and resolve
  operation-ID blockers to their original diagnostics. The blocker ID remains
  available separately; the user-facing status displays `blocker_detail`.

### Regression coverage and verification

- `tests/test_native_events.py`: noisy stdio server emits over 4 MB of deltas and
  more than 4,000 notifications; reply, usage and callbacks must survive retention
  eviction. Disconnect and confirmed failure preserve bounded payload-free
  diagnostics. Separate checks bound retained bytes and method cardinality.
- `tests/test_runtime.py`: known and uncertain native failures retain diagnostics
  through the kernel; existing assertions still enforce the distinction between
  released and retained admission reservations.
- `tests/test_ui.py`: null-result reporting, broken terminal output, original runner
  exceptions, durable pause summaries, and exports with separate reporting errors.
- `tests/ui_start.test.cjs`: paused runs display their original operation diagnostic
  instead of an opaque hash. All **6 browser-script tests passed**.
- Python syntax checks passed. Local probes executed the actual adapter definitions
  with an in-memory transport, exercising normal and early terminal delivery after
  4,204 events, disconnect, confirmed failure and transport cleanup. Event-retention,
  logger and summary probes also passed. These probes do not replace Linux pytest
  or exercise real subprocess timing. `git diff --check` passed for tracked changes.
- Initially the Linux regression command could not execute: automatic approval review rejected
  WSL launches because its selected reviewer model was at capacity. This was an
  approval-service failure, not a test failure or a finding that the command was
  unsafe. It was subsequently covered by the full Linux run above. Focused rerun:

  ```bash
  .venv-linux/bin/python -m pytest -q tests/test_native_events.py tests/test_endpoints.py tests/test_runtime.py tests/test_ui.py tests/test_ui_os.py tests/test_history.py
  ```

The historical run and its uncertain operation were not modified. An interrupted
local session is not automatically treated as proof of provider termination;
existing reconciliation requirements and retained-capacity safeguards remain intact.

## OS/agent failure investigation — 2026-10-18

Status: report items 1, 2, 4, 5, 6 and 7 implemented, together with OS output
delivery and verified support for non-coding agents. Report items 3 and 8 remain
open in the historical report below; item 8 is now corrected by
[FIX-0084](FIXES.md#fix-0084), and item 3 by [FIX-0086](FIXES.md#fix-0086).
This file tracks current-version fixes; historical evidence remains below.

### Deferred work recorded before implementation

The numbered implementation report and the OSAG identifiers below use different
numbering. The user's selected report items map to request framing (OSAG-01 and
OSAG-06), write authority (OSAG-05), loop termination (OSAG-03), requirement
handoffs, provider diagnostics (OSAG-02), and explicit recovery (OSAG-04).

- **Report item 3 — P1: separate setup checks from final product acceptance.**
  Implemented by [FIX-0086](FIXES.md#fix-0086). Historical problem: the setup-selected
  `development-prerequisites` command checks Node, npm and ignore rules, and the
  same immutable selection is reused for tasks and final acceptance. Introduce
  distinct prerequisite, task and final acceptance policies so a setup-only tree
  cannot satisfy the product objective. Preserve check provenance and prevent
  workers from weakening acceptance. Acceptance: a prerequisite-only repository
  cannot finish a game objective; launch, gameplay and world/player persistence
  requirements have corresponding final evidence.
- **Report item 8 / OSAG-07 — P2: preserve historical development starts.**
  Implemented by [FIX-0084](FIXES.md#fix-0084). Historical problem: started tasks later cancelled as
  superseded disappear from accounting and allocation history. Count durable
  starts independently of final disposition; never-started cancellations must
  remain excluded. Acceptance: this incident counts four development starts,
  and role allocation uses the same documented historical basis.

Implementation must keep OS capabilities independent of coding-agent policy.
Artifact-only and read-only agents must be able to terminate successfully without
writing files, creating Git commits, running coding checks or publishing a code
workspace. Output delivery must use explicit runtime capabilities and must not
publish failed or unassessed worker work.

### Implementation and whole-run audit

Product search result: **no Minecraft implementation found** in the target folder,
the run workspaces/snapshots, either archived Minecraft run, or any private Git
commit, including unreferenced objects. The supplied export, archive and durable
database (including WAL) contain the same records. The only successful file writes
were one `.gitignore` update and four README roadmaps, retained as twelve workspace
copies across generations 1–3. All four workers failed on their first reconciliation
request. The earlier archive failed during startup before agent execution.

The selected implementation now includes:

- OS artifact-file delivery with an explicit destination, baseline conflict checks,
  durable intent/receipt, and replay protection. The coding agent delivers only a
  finally accepted tree. New projects use their selected directory; existing Git
  repositories use `STATE/result` unless configured otherwise.
- A separate `RuntimeConfig`, generic process registration/termination, and native
  protocol registration by the caller. Non-coding HTTP/native agents are covered
  without writes, coding checks, task reports or Git. Coding cancellation drain
  policy moved out of the OS process implementation.
- OSAG-01/06: explicit final host phase requests and strict Anthropic request fixtures.
- OSAG-05: effective project/explicit authority in planning context, with bounded
  individual worker grants retained.
- OSAG-03: immediate termination on non-actionable plans, stable review input
  comparison excluding rewritten memory, known model failures pausing the agent,
  and an OS circuit for repeated permanent model failures across operation names.
  Known failures drain other started workers. Stopped drivers cannot keep the
  controller spinning; OS driver deadlines and cancellation-before-submission
  are covered without requiring file output.
- Requirement handoffs: the full user objective accompanies every worker request;
  prompts preserve product constraints. The first historical roadmap had drifted
  into first-person movement and chunk-mesh rendering after losing the 2D requirement.
  Explicit user amendments remain ordered and pinned to each task's plan. Steering
  arriving during file delivery invalidates completion until a new review and
  acceptance incorporate it; delivery cannot acknowledge an older objective.
- OSAG-02: bounded sanitized provider diagnostics, error categories/request IDs,
  retry metadata, and separate attempted-backend information on failure.
- OSAG-04: explicit linked model recovery through `retry-model`, preserving private
  edits and rebuilding reconciliation state. Immutable original results, unknown
  effect exclusion, finite allowances, and program/configuration pins remain intact.
  Recovery activation updates its task, attempt, process and run ledger atomically;
  interruption after checkpoint preparation is recoverable. Accepted output has
  its own `retry-output` path, receipt reconciliation and verification-lease cleanup.

The historical incident is not rewritten or silently migrated. These fixes do not
create a Minecraft product retroactively. Later FIX-0086 and FIX-0084 corrections
cover report items 3 and 8 without changing historical run evidence.

Verification: the full Python suite passed with **157 passed, 1 skipped**. The
skipped frontend wrapper requires Node 18+; the default executable is Node 12.
Running the browser-script suite with the installed Node 22 passed all five tests.
The final CLI steering adjustment was additionally checked with four passing
steering/acceptance regressions. Ruff and `git diff --check` passed. Tests used
fixtures and local transports, with no live provider/model requests.

The regression scenarios include actual new-project file delivery, source-conflict
protection and delivery retry, binary/mode preservation, interrupted delivery,
lost delivery results and acceptance leases, model recovery after confirmed and
uncertain execution, interruption between recovery checkpoint and activation,
non-actionable plans, stopped drivers, worker draining, queued cancellation,
non-coding process deadlines, and steering during accepted-file delivery.

The incident exposes a likely provider compatibility bug, confirmed diagnostic and
planning-context defects, and weaknesses in recovery and accounting. The runtime
stopped publication safely, but the agent could replace interrupted tasks without
addressing the infrastructure failure that interrupted them.

### Incident and evidence

- Run: `40542ee7c378`; project: `/home/mawa/projects/testing/minecraft-v2`.
- Worker: `worker-3-document_scope_recovery_03`; task: `document_scope_recovery_03`.
- Failed operation: `model-5`, phase `reconciliation`, operation ID
  `sha256:eec4b90a22f987a45134641a34bf234cd9230abe93f31314e449857959a41001`.
- Request created: `2026-10-18T23:23:28.050576Z`; execution started:
  `23:23:28.063824Z`; finished: `23:23:28.246281Z` (about 182 ms executing).
- Result: `failed`, `EndpointError`, `Endpoint HTTP 400`, effects `known`, execution
  `confirmed_stopped`, no usage, no actual-backend metadata.
- Adjacent successful model operations identify `claude-haiku-5-5` through the
  `anthropic` protocol. The configured binding is named `local`, but its inference
  location is cloud; the binding name does not imply local inference.

Local evidence, relative to the repository root:

- State: `.polyinference/ui/runs/40542ee7c378/state/`.
- Export: `.polyinference/history/20261018T232516376230Z-03cde201338743e4804c4343a3abf5c8.json`.
- Context and output objects: `state/artifacts/<digest without sha256:>`.
- These are local diagnostic files and may not exist in another checkout. The
  investigation read the pasted operation, its referenced artifacts, this worker's
  records, run configuration, and relevant source/tests. It did not audit the whole run.

The worker's sequence was:

1. `model-0` returned an action wrapped in `<invoke_action>` tags instead of plain
   JSON. JSON parsing and union validation rejected it. A synthetic `invalid-0`
   call/result pair supplied feedback; no file tool executed for that invalid reply.
2. `model-1` recovered and called `files.list`; only `.gitignore` was present.
3. `model-2` wrote `README.md` successfully (10,690 bytes; content digest
   `sha256:c3ef4a5c32ca792ca974548235c0ec7ef022385308db68c8e92e7b8c0e4f7014`).
4. `model-3` requested `development-prerequisites`; it passed with exit code 0,
   reporting Node 22.17.1, npm 10.9.2 and required ignore rules. This was environment
   verification, not application acceptance evidence.
5. `model-4` returned `candidate`. The host preserved the private delta, acquired
   verification ownership, and materialized integration generation 2.
6. `model-5`, the first reconciliation query, received HTTP 400. No reconciliation
   reply, assessment, completion report, or publication followed for this task.
7. Cleanup restored a development view at generation 3 and released verification
   ownership. The process was paused; the task was later cancelled with
   `stop_reason=superseded_by_plan`. The README remained in the private delta and
   restored workspace. Cancellation did not mean its edits had never existed.

### OSAG-01 — P1: phase transitions produce unsupported Anthropic request framing

Confidence: request shape confirmed; exact cause of the server's 400 is a
high-confidence inference because the provider error body was discarded.

`AgentServices.context()` places current instructions and pinned inputs before
history. A completed `candidate` becomes a historical `message` without an
observation. `KernelRuntime._dispatch()` maps both `message` and `tool_call` parts
to the assistant role. The Anthropic adapter removes system messages into the
top-level system field but otherwise forwards the sequence unchanged.

All 11 referenced context artifacts were read and their SHA-256 hashes verified.
The reconstructed roles were:

```text
system, user,
assistant, user,  # invalid-output feedback pair
assistant, user,  # files.list and observation
assistant, user,  # files.write and observation
assistant, user,  # checks.run and observation
assistant        # completed candidate; nothing requests a new turn afterward
```

Haiku 5.5 rejects a final assistant turn as unsupported assistant prefill, even
with thinking disabled. See the official
[Haiku 5.5 migration guide, Replace assistant prefill](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide).
Tool loops avoid this particular problem because their observations end in a user
turn. A mandatory transition to reconciliation exposes it.

Relevant code: `src/polyinference/agent/services.py` (`context`, around line 329),
`src/polyinference/runtime/kernel.py` (message mapping, around line 474),
`src/polyinference/runtime/inference.py` (Anthropic payload, around line 190), and
`src/polyinference/agent/worker.py` (`consume` / `integrate`).

Fix direction: represent the current phase request as an explicit final user turn,
while preserving historical roles and trust boundaries. Validate model/provider
request constraints before submission. Do not strip history or reinterpret
retrieved text as instructions merely to satisfy the role constraint.

Acceptance: exercise development -> candidate -> reconciliation, reconciliation
-> checks -> assessment, and assessment repair -> reconciliation through the real
adapter. A fixture enforcing Haiku 5.5's final-role constraint should accept all
valid phase requests, without changing other providers' behavior.

### OSAG-02 — P1: provider errors lose the information needed for diagnosis and recovery

Confirmed in code and the recorded result. `HTTPInference.generate()` raises only
`Endpoint HTTP <status>` for every HTTP error, discarding the response body and
provider request ID. The kernel records a generic exception type and always sets
`retryable_after_reconciliation=False` in its generic exception handler. Services
then raise `RuntimeError` using only output text. The controller receives a string
rather than a structured infrastructure failure.

Backend metadata is created only after successful generation. Thus a request that
was submitted and rejected has `actual_backend=null`, `binding_ref=null`, and
`binding_generation=0`, despite having a known selected endpoint. These fields
must not be read as proof that no dispatch occurred.

Relevant code: `runtime/inference.py` around line 216; `runtime/kernel.py` around
lines 611 and 690; `agent/services.py` in both retained and fresh model-result paths.

Fix direction: preserve bounded, sanitized provider error code/message, HTTP status,
request ID, retry-after information, and selected endpoint/model. Keep attempted
binding information distinct from provider-confirmed execution metadata. Carry a
typed failure to the controller rather than flattening it into generic strings.
Distinguish invalid request, authentication/permission, rate limit, service failure,
and uncertain transport termination. Redact credentials and sensitive response
content; existing tests intentionally prevent raw provider details from leaking.

Acceptance: synthetic 400/401/403/429/5xx and disconnect cases retain useful safe
diagnostics and receive explicit recovery classifications. Verify sanitization and
that attempted dispatch remains visible when generation fails.

### OSAG-03 — P1: repeated infrastructure failures can bypass no-progress detection

The assignment and pinned memory already mention two earlier documentation
interruptions with HTTP 400. This worker hit another 400. That establishes repeated
symptoms; this investigation did not independently prove the earlier requests had
the same framing defect.

The controller permits safely interrupted tasks to be retired and replaced. Its
no-progress guard compares the entire review snapshot, including `all_task_ids`,
interrupted/pending task records and memory. New task IDs or rewritten notes change
the fingerprint even if the shared code, failing provider, failing phase, and
runtime configuration are unchanged. There is no equivalent recurrence guard for
the underlying infrastructure failure on this path. A sprint/query limit can stop
the loop eventually, but that is a resource limit rather than diagnosis.

Relevant code: `agent/controller.py` (`consume`, `review`, snapshot/fingerprint
around lines 396-427, and retirement around line 543).

Fix direction: track failures by a stable infrastructure signature, using structured
errors from OSAG-02, phase, model/protocol, and relevant configuration/version.
Repeated non-transient failures should pause affected dispatch and expose an
actionable blocker. Replacement IDs and memory changes must not reset recurrence.
Apply bounded backoff to genuinely transient failures rather than asking the senior
agent to solve transport errors through new coding assignments.

Acceptance: repeated equivalent failures across renamed replacement tasks stop
before consuming the sprint limit. Relevant configuration changes can allow an
explicit new attempt; unrelated failures and meaningful code progress do not
incorrectly trigger the guard.

### OSAG-04 — P1: immutable replay lacks an explicit recovery path for known failed model operations

`KernelRuntime.execute()` returns a recorded terminal result for an existing
operation. `AgentServices.model()` reuses a retained request at the same logical
step and raises again when its saved result is failed. Simply resuming the old
worker therefore does not retry this model call, even after fixing the adapter.

Returning the saved result is correct idempotency behavior. The gap is an explicit
way to supersede a definitively failed model operation with a new recovery attempt
while retaining the workspace, trajectory, and phase. Creating a whole replacement
assignment can repeat completed work. The senior's interrupted-task input also does
not directly include the preserved private delta or a structured recovery summary;
the delta exists in runtime storage, but is poorly exposed to the recovery decision.

Relevant code: `runtime/kernel.py` (`execute`, around line 221),
`agent/services.py` (`model`, around line 467), `agent/controller.py` (`drive` cleanup
and review input), and `runtime/workspace.py` (`abort`, around line 673).

Fix direction: define an explicit, audited recovery attempt with a new operation
identity linked to the failed operation, after validating its known terminal state
and corrected request intent. Preserve old records and reuse recoverable private
work. Expose recovery evidence to the controller/senior without publishing unassessed
changes. Account for restored workspace generations when resuming a phase.

Acceptance: a deterministic request failure followed by a framing fix can resume
without rewriting the completed README. Replaying the original operation still
returns its original failure. Unknown-effect operations remain blocked pending
reconciliation; recovery must not duplicate tool effects or bypass publication checks.

### OSAG-05 — P1: planning context misrepresents project-wide write authority

The recorded run configuration has `write_scope="project"` and
`allowed_write_paths=["README.md"]`. In project mode, `senior.validate()` permits
assigning additional paths; its allowlist restriction applies only in explicit
mode. However, the senior review snapshot supplies `allowed_write_paths` without
the `write_scope` that changes its meaning. The worker assignment and senior memory
then say application development requires an expanded write grant.

The worker correctly respected its own README-only assignment. The stack-level
problem is that the planner's inputs encouraged conflating that assignment with
the run's broader authority. The initial fallback list for an empty project comes
from `ui.configure_run()`; it must not be presented as the effective project-wide
ceiling when project mode is active.

Relevant code: `ui.py` around line 210; `agent/controller.py` review snapshot around
line 420; `agent/senior.py` around line 40; `agent/tasks.py` (`make_task`);
`runtime/workspace.py` (`extend_setup_scope`).

Fix direction: expose effective authority explicitly to the planner: scope mode,
whether it may assign new project-relative paths, any exclusions, and the difference
between run authority and a worker's assigned paths. Derive this from the same policy
used by validation and runtime enforcement. Do not relax individual worker scopes.

Acceptance: an empty project in project mode can receive tasks creating application
files without an invented permission blocker. Explicit mode still rejects paths
outside its grant; an existing worker cannot independently expand its assignment.

### OSAG-06 — P2: HTTP integration fixtures accept requests rejected by the real model

`tests/test_http_integration.py::test_complete_agent_over_real_http` covers both
chat and Anthropic over TCP, including the phase lifecycle. Its Anthropic fixture
checks headers and system placement, but accepts a final assistant turn and returns
200. The scripted agent in `tests/conftest.py` also ignores that restriction.
Therefore successful end-to-end tests do not establish compatibility with the
configured Haiku model. Existing Anthropic error tests cover terminal failures and
redaction, but do not exercise this rejected phase-transition request shape.

Fix direction: strengthen provider/model contract fixtures, particularly the
final-role rule implicated here. Keep protocol tests distinct from model-specific
constraints rather than pretending every Anthropic model has identical behavior.

Acceptance: demonstrate that the current request construction fails the strict
fixture, then passes after OSAG-01. Cover repairs and assert that failure does not
publish, lose the private delta, or retain verification ownership after a known stop.

### OSAG-07 — P2: superseding started tasks erases them from development accounting

Status: implemented by [FIX-0084](FIXES.md#fix-0084), including pending-reservation
separation and legacy started-spec evidence. The original incident is retained below.

The export reports zero started development tasks despite this executed worker.
`agent/routing.py::accounting()` excludes every cancelled task, including tasks
which ran and were later cancelled as superseded. `allocate()` also excludes
cancelled tasks from its quota history. This can both misreport historical work and
distort the configured senior/junior allocation after recovery churn.

Fix direction: count durable starts or attempts independently of current task
disposition. Never-started cancelled tasks should stay out of the started count;
superseded tasks that actually ran must remain represented. Define whether allocation
uses started tasks or attempts and align reported metrics with that definition.

Acceptance: start a worker, interrupt it, supersede it, and verify its historical
start remains counted. Cancelling a pending task adds no start. Subsequent role
allocation follows the documented historical basis.

### Invariants to preserve and diagnostic cautions

- Publication was correctly blocked without reconciliation/assessment. Do not fix
  this incident by skipping mandatory phases or treating a candidate as success.
- The private README and its delta survived; no lost-edit or duplicate-publication
  bug was established. Cleanup released verification ownership after the known stop.
- The initial `<invoke_action>` formatting mistake recovered successfully and was
  separate from the final HTTP request failure.
- The failed query was not near its deadline: almost an hour remained. Reconstructed
  canonical message input was about 23 KB, below the conservative 96,000 input-token
  bound. No context/deadline exhaustion was indicated.
- `max_api_spend_microusd=0` is treated as no enforced spend ceiling by the current
  implementation; it does not explain this failure.
- Missing provider usage is not proof of zero consumption. The kernel conservatively
  settles unknown token usage at the reserved amount; preserve provenance and avoid
  presenting estimates as provider-reported usage.
- Suggested implementation order: OSAG-01 and OSAG-06 together; OSAG-02 before
  OSAG-03; then OSAG-04, OSAG-05, and OSAG-07. OSAG-05 can proceed independently.

## I/O safety implementation completed — 2026-10-20

The OS/agent fixes following run 2de3d5c5ab9b are implemented and locally verified.
See [FIX-0058 through FIX-0060](FIXES.md#fix-0058) and the
[verification report](io-safety-verification-2026-10-20.md) for checks, capability
limits and fresh-state requirements. The shared agent library remains deferred.
All exported settings are documented in the
[central OS reference](../design-docs/simplified-os/AGENT_SETTINGS.md).


<a id="endpoint-testing-v1"></a>
## Endpoint lifecycle implementation v1 — 2026-10-23

The earlier [portable testing proposal](#portable-endpoint-testing) and
[agent/OS split](#endpoint-agent-os-split) now have an initial implementation.
The [current usage/settings guide](../docs/guides/endpoint-testing.md) is the
behavioral reference; earlier design paragraphs remain evidence of the proposal.
OS-native retries now precede optional caller-authorized retries, with separate
durable counters and one shared original logical deadline. Output adaptation
cannot reset them. The fresh coding agent selects two native retries; the UI adds
one caller retry and a smaller 4096-token raw target inside the 32000 hard ceiling.

SSE Anthropic/chat/Responses assembly, meaningful-output watchdogs, explicit local
and small-cloud timings, cause/stage diagnostics, retained physical holds,
discarded-delivery fencing and a bounded on-click generic probe are implemented.
One-slot endpoints can expose isolated pending computation but cannot submit a
replacement while it holds the slot. A second unknown remains blocking. No native
or tool uncertainty is relabelled safe. New settings are opt-in for old/custom
configurations; saved runs are not automatically migrated.

V1 limits: Gemini has explicit buffered transport; unsupported SSE is not silently
resent. Raw query isolation trusts the built-in adapter only, excluding native
jobs and simulator subclasses. The existing TPS simulator still paces completed
responses and does not prove actual provider streaming/GPU behavior. Probe
admission serializes within one UI manager, not across independent runtimes.
Unsupported status/cancel APIs cannot resolve or reclaim pending computation.
See [FIX-0117](FIXES.md#fix-0117), [FIX-0118](FIXES.md#fix-0118) and
[FIX-0119](FIXES.md#fix-0119) for actual verification and boundaries.
