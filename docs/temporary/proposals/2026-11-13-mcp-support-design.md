# MCP support for the PolyInference OS

Date: 2026-11-13 (America/Toronto). Status: proposed architecture; design only; awaiting owner decisions.
Source: working checkout on `codex/simple-os-v1`, HEAD
`da94312cdded8d905e31d42ca7e08727143a4cf6`, including pre-existing staged and
unstaged changes. HEAD alone does not describe the inspected documentation.

## Handoff checkpoint

User requests an MCP design, not implementation, with careful OS source review,
questions beyond the original four, and explicit major decisions for user review.
Keep this document updated after each investigation phase. It records evidence,
concise rationale, alternatives and unresolved work, not private internal deliberation.
Do not implement, invoke providers, resume historical runs, stage or commit changes.
Do not delegate: no delegation is authorized. Preserve the existing dirty checkout.

Completed: read onboarding, project memory, maintenance, architecture, runtime
boundary and module ownership tree; inspected kernel/process/capability/storage/
inference primary guides. Git status obtained through approved WSL execution;
Windows Git cannot read this UNC cwd, sandbox WSL returned E_ACCESSDENIED.
Authorized WSL read succeeded. Baseline contains extensive documentation moves,
staged settings changes and tests; none are this task's work.

Current handoff status: design complete for owner review; both required documentation commands passed. The supporting paths and protocol verification listed as pending at earlier checkpoints have been reviewed. The historical FIX reads included truncated output; relevant regression entries were reread in bounded chunks, but this document does not claim an independently verified exhaustive history read. A future implementing agent must satisfy the complete-history reading requirement before changing code. No implementation or live qualification has occurred.

Confirmed findings (source symbols are indexed below in the completed design): direct CapabilityCall dispatch bypasses inference admission; AgentJob holds admission across native callbacks; native transport awaits callbacks inline. Process residency is distinct from inference admission. Hibernation requires settled effects, so it cannot park a live remote call. Capability dispatch marks dispatched before invoking the handler. Unknown effects can block new dispatch globally. The capability registry accepts typed Python schemas and pins descriptor digests; arbitrary MCP JSON schemas need a deliberate adapter. Data-policy enforcement for model dispatch is not automatically remote-tool egress enforcement. Each Runtime owns its admission controller; shared endpoint concurrency needs an explicit coordination scope.

## Questions to carry through the investigation

1. How does a worker yield for MCP without occupying inference capacity?
2. What does a continuously running kernel simplify, and what still needs durable recovery?
3. How are serial and concurrent MCP endpoints admitted safely?
4. Which decisions need the user's review, and which questions remain open?
5. Does the raw-model path differ from a native provider job containing tools?
6. Does tool waiting retain worker residency, grants, budgets or endpoint holds?
7. Can multiple runtimes share an MCP server without oversubscribing it?
8. What happens after disconnect, cancellation, crash or lost acknowledgement?
9. How are schema changes, authentication, data placement and remote side effects constrained?
10. Can server callbacks require inference and deadlock a serial endpoint?

## Investigation journal

### Checkpoint 1: scope and onboarding

The design must separate inference admission, process residency and remote-effect
certainty. Existing guides describe strict unknown-effect holds and immutable
attempts. An async wait alone cannot establish physical inference release.
The native-job callback path requires particular inspection before promising the
same behavior as a tool call between raw model operations. These are investigation
leads, not a completed implementation audit.

Preservation receipts and original document copies: `C:\Users\bh349\AppData\Local\Packages\openai.codex_2p2nqsd0c76g0\AC\#!sandbox.{315cd5a1-62bd-4a1a-8934-ce35a99da90b}\Temp\polyinference-mcp-design-32_puqgc`.
Checks so far: read-only source guidance and Git status/revision only. No tests,
provider calls or documentation generation yet. Next: finish guidance, trace
execution/settlement paths and record exact symbols and evidence here.

### Checkpoint 2: execution and ownership findings

The naive design of wrapping a network await in a registered capability works only for the direct-call inference-slot property. It does not release a native job reservation, distinguish queued work from sent work, or coordinate endpoints across runtime instances. The design therefore needs separate MCP admission and execution receipts plus an explicit native-provider support boundary. Provider pause must mean certified physical capacity release, not merely a local counter decrement. The filesystem executor has one worker and cancellation-joining semantics; remote MCP work must not use it. Existing generic grants, original deadlines, effect uncertainty and provider ownership remain authoritative.

Relevant regression families reviewed: FIX-0032/0036 (generic boundary and broker enforcement), 0045/0047 (original budget on retries), 0067/0069 (resource distinctions), 0117/0127 (isolation and physical settlement), 0134/0135 (data policy and residency), 0141 (deadlines), 0152/0154 (callback receipts and byte/token distinctions), 0167/0171/0174 (provider accounting, timeout and lifetime), 0182/0183 (scheduler audit and process-only scope), 0184/0185 (documentation migration). No implementation changes or runtime tests. Next: review supporting paths and protocol revisions, then write decision records and acceptance scenarios.

## Proposed design in one page

Make MCP an OS-managed capability transport with its own durable admission and
completion machinery. Keep model execution and remote tool execution as separate
operations wherever the provider permits that separation. An MCP wait owns no
inference reservation, but can still own process residency, remote concurrency,
conflict protection, memory and unresolved-effect obligations.

The first supported strict path should be a completed model turn followed by a
host-brokered CapabilityCall. Do not claim this property for the current native
AgentJob callback path: it keeps its inference admission reservation across the
callback. Supporting native jobs with the same guarantee requires a provider
contract that proves suspension and prevents resumption before readmission, or
an application/provider integration that ends each inference turn before tool
execution. This is the main owner decision, D2 below.

Use trusted endpoint profiles to specify concurrency scopes and limits. Default
unknown endpoint concurrency to one. Share admission across every participating
runtime using the same constrained endpoint/account. Separate request capacity,
remote task capacity, rate limits and mutation conflict locks. More connections
do not make a serial server concurrent.

Persist queued intent before dispatch, remote identity when known, terminal
receipts before releasing capacity, and a replayable continuation reference.
Cancellation acknowledgement, timeout, socket closure and local lease expiry
are not remote termination evidence. Preserve today's uncertain-effect barrier
until a separate scoped-uncertainty design is approved.

The kernel's event loop can wait and wake continuations without another LLM
turn. It does not need to repeatedly ask the model whether a tool finished.
However, the current Runtime is opened and closed by its owner; it is not an
always-available installation daemon. Crash recovery and shutdown ownership
remain necessary.

## Evidence map: inspected behavior and implications

Paths are relative to the repository. Symbol names are the primary locator;
line numbers are observations from this working checkout, not permanent pins.
Source evidence describes current behavior, not an endorsement of every edge
case. No MCP implementation is established merely by a wire record naming MCP.

| Evidence | Observed behavior | Design consequence |
| --- | --- | --- |
| `src/polyinference/runtime/kernel.py`, `_execute_once`, about 467 | Fingerprint/replay checks precede fresh dispatch; grants, scope, deadlines and a single active top-level effect are enforced | MCP must participate in stable intent/replay; several concurrent tools in one process need a new contract |
| Same, `_dispatch_once`, about 720 | Inference admission wraps ModelQuery and AgentJob execution | Direct tool calls need no inference slot; native callbacks occur inside an admitted job |
| Same, CapabilityCall branch, about 1057 | Marks submission/dispatched before awaiting the capability handler; persists returned artifact | An internal handler queue cannot accurately distinguish waiting from submitted effects |
| Same, `_authorize_capability`, about 1270 | Checks explicit grants, pinned schema/effect, optional workspace identity/generation | Discovery cannot confer permission; do not invent workspace generations for non-workspace tools |
| Same, `_native_callback`, about 1309 | Child operation identity uses retained callback root and call ID; arguments must agree; original limits survive | MCP callback retries must preserve child identities and parent lineage |
| `src/polyinference/runtime/codex.py`, `generate_job` | Reader awaits broker callback inline; job terminal event is distinct from callback result; interruption lacks full terminal drain | An async MCP handler alone does not release native capacity or provide reliable cancellation |
| `src/polyinference/runtime/inference.py`, `Admission` | Bounded queues, retained reservations; unknown execution keeps capacity; controller instances are runtime-local | Reuse principles, not the model counter; explicitly define shared endpoint ownership |
| `src/polyinference/runtime/processes.py`, `start`, `hibernate`; `runtime/lifecycle.py`, `park_process` | Process start applies inherited/original deadline; hibernation requires settled work and no permits | Tool wait is not current hibernation; residency and elapsed budget remain charged |
| `src/polyinference/runtime/capabilities.py`, `Capability`, registry | Python TypeAdapter validation and pinned descriptor digest | General MCP JSON Schema requires a deliberate validated representation, not guessed Python types |
| `src/polyinference/contracts.py`, `CapabilityDescriptor`, about 824 | Wire record already names transport, effect, replay/cancel guarantees, server class and protocol features | Align new runtime descriptor with existing vocabulary; do not confuse design fields with active enforcement |
| `src/polyinference/runtime/process_policy.py`, `data`, `dispatch` | Model/job inputs receive destination data-policy checks | Remote tool arguments and outputs need explicit egress checks; model locality alone is insufficient |
| `src/polyinference/runtime/exclusive.py`, `Exclusive.acquire` | Logical ownership is retained; host advisory locks only for special shell/filesystem keys; generic keys use local async locks and records | A new generic key is not an installation-wide counted MCP limiter |
| `src/polyinference/runtime/storage.py`, `Records.compare_and_publish`, `Artifacts.put` | CAS and immutable records share a SQLite transaction; artifact files are written separately | Terminal receipt and local permit transition can be atomic in one store; remote send and local commit cannot |
| `src/polyinference/runtime/resume.py`, `prepare` | Recovers selected model/host receipts; otherwise refuses unknown outcome | MCP requires an explicit recovery adapter and ownership fencing, not reuse of raw-model recovery |
| `src/polyinference/runtime/retry.py`, `_dispatch` | Bounded response retries exclude effectful jobs/tools | Do not route remote mutations through inference repair retries |
| `src/polyinference/runtime/blocking.py` | Shared single-worker filesystem executor, cancellation joins outstanding work | Network waits and blocking SDKs must not monopolize the filesystem executor |
| `src/polyinference/agent/worker.py`, `model`, `tool`, acquire/release phases | Raw application separates model and tool operations; verification can span several later phases | Existing raw structure is a useful integration point, but semantic locks may legitimately remain held |
| `src/polyinference/agent/services.py`, `capability`, about 944 | Retains/replays OperationRequest; obtains registered capability; includes optional workspace pins | Preserve this replay boundary; bootstrap registration alone does not expose arbitrary tools |
| `src/polyinference/domain.py`, `Action`, about 234 | Bundled worker action tools use an explicit Literal grammar | Coding application needs an explicit MCP action/catalog change; OS support is not automatic worker support |

Guides consulted include `docs/modules/kernel.md`, `processes.md`,
`capabilities.md`, `inference.md`, `storage.md`, `sdk.md`, `retries.md`,
`agent-workers.md`, the services/context/commands/inspection ownership routes in
`docs/file-tree.json`, and `design-docs/simplified-os/RUNTIME_BOUNDARY.md` with its
capability, inference, continuation, retry, workspace and repository contracts.
Existing future scheduler proposals are proposals, not required infrastructure.

## Protocol baseline and deliberately bounded support

Protocol references were checked on 2026-11-13. The current published revision
is 2026-07-28, which introduces a stateless core and multi round-trip input
requests. Older 2025-11-25 integrations use initialization and negotiated
connection capabilities. These require separate wire adapters behind one OS
operation model. [Current release](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/blog/content/posts/2026-07-28-spec-ga/index.md),
[legacy lifecycle](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/lifecycle.mdx).

| Profile | Proposed treatment |
| --- | --- |
| 2026-07-28 core | Preferred new profile; explicit per-request version/capabilities and validated discovery; no invented legacy session requirement |
| 2025-11-25 core | Compatibility profile only when selected/tested; retain initialization and session behavior required by that transport/server |
| Streamable HTTP | Async network adapter, explicit principal and destination identity, bounded response handling |
| stdio | Long-lived owned child or explicitly shared broker-owned child; structured protocol output separated from bounded stderr diagnostics |
| Tools | Initial feature scope: discovery and allowed calls, with pinned input/output schemas and bounded typed content |
| Resources/prompts/subscriptions | Not implicitly enabled by tools support; separate grants, byte limits and lifecycle review |
| Tasks extension | Explicit optional profile, disabled until durable recovery and permit accounting pass qualification |
| Input requests, legacy sampling/elicitation | Default unsupported unless an explicit host/application route is configured; no hidden new inference allowance |

Current multi round-trip requests return `InputRequiredResult` and continuation
state that the client returns with answers. They are not equivalent to restarting
a failed mutation with fresh arguments. Retain the exchange identity, opaque
state and input-response IDs. [MRTR specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/patterns/mrtr.mdx).

The 2026-07-28 Tasks extension uses `tasks/get`, `tasks/update`, and `tasks/cancel`.
It can return a task handle instead of a final result. Cancellation is cooperative;
an acknowledgement does not guarantee a cancelled terminal state. Results can
expire. OS policy should retain reconciliation state even when the protocol
permits a client to discard it after cancelling. A missing task is not proof that
its effect never happened. [Tasks specification](https://modelcontextprotocol.github.io/ext-tasks/specification/2026-07-28/tasks.html).

A tool's declared schemas and structured output must be handled explicitly;
content may include text, images, audio and resource references. Tool metadata
is not a grant or sufficient evidence of safe effects. [Tools specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx).

The exact Python SDK package/version is unresolved. Select it only after checking
Python-version compatibility, wire profiles, cancellation behavior, buffering,
reconnection and automatic retry defaults against this design. Protocol support
must be advertised only for implemented, tested profiles. Do not claim a generic
endpoint max-concurrency discovery mechanism: use trusted deployment profiles.

### Checkpoint 3: supporting paths and protocol reconciliation

Reviewed retained ownership, SQLite publication, generic Resume, inference retry,
worker grammar and service capability construction. Found that current exclusive
permits cannot simply be repurposed into a cross-runtime counted limiter and
that generic Resume lacks MCP reconciliation. Verified the modern/legacy
protocol distinction using official specification sources. Earlier tentative
session-based terminology is corrected: connection ownership and logical remote
state still matter, but the modern core is stateless at the protocol layer.
A concurrent documentation task added FIX-0186; this task must select the next
unused FIX ID at publication time and preserve that entry.

## Decision records

Each record gives the requirement, code evidence, alternatives, recommendation,
cost and what could change the recommendation. These are reviewable engineering
rationales, not a transcript of private internal deliberation. Recommendations
remain proposals until the owner accepts them.

### D1 — Keep MCP within generic capabilities

**Requirement and evidence.** Non-coding processes must use tools without Git,
checks or coding task records. CapabilityCall already carries grants, intent,
arguments and effect classification. CapabilityDescriptor already has transport
and protocol vocabulary.

**Alternatives.** Put MCP in the coding worker; expose it directly inside provider
harnesses; make it a new inference backend; or add an OS capability transport.
Worker-only support duplicates authority/recovery. Direct provider access hides
remote effects from the host. An inference backend incorrectly couples tool
latency to model capacity.

**Recommendation.** The OS owns the broker, grants, transport admission, receipts
and recovery. The application owns tool selection, interpretation and any user
approval policy. The provider owns actual model scheduling. Bootstrap installs
trusted endpoint profiles and explicit capability versions. A model cannot
register an endpoint or enlarge its own grants by quoting discovered metadata.

**Cost and change criterion.** This needs a small generic transport/execution
boundary rather than just a handler wrapper. Reconsider a provider-managed route
only if it supplies equivalent host-verifiable grants, identities, settlement and
capacity-release evidence. Convenience alone is not equivalence.

### D2 — Release inference capacity only at a real execution boundary [OWNER REVIEW]

**Requirement and evidence.** The user's no-inference-thread requirement means
no admitted inference execution held solely for a tool wait. Python coroutine,
CPU thread, provider GPU work and a local Admission reservation are different
resources. Direct CapabilityCall avoids model admission; AgentJob holds it while
native callbacks run. The current native adapter provides no certified suspension
contract.

**Alternatives.** Decrement admission inside every callback; keep native slots
and document an exception; require provider suspension; or end each model turn
before executing tools. Counter-only release risks admitting extra jobs while
the provider still owns physical resources, and permits uncontrolled native
resumption. An exception does not satisfy the strict requirement.

**Recommendation.** V1 strict MCP support uses completed model turns and separate
host tool operations. Raw text action turns fit the current application; native
structured tool-call support is a separate integration concern. Gate native MCP
behind either explicit turn termination or a certified suspend/readmit/resume
protocol. Do not label today's native callback path compliant.

A future suspension receipt must identify the job/generation, establish which
resources were released, prevent autonomous resumption, retain all descendant
effects, and require a fresh admission before resume. Suspension of token
production does not automatically release KV-cache memory; report any retained
provider allocation separately.

**Cost and change criterion.** Splitting native turns can lose harness continuity
or add prompt/prefill cost. Provider suspension could preserve continuity but
requires support that is not evidenced here. Owner must choose initial support
scope and whether native parity blocks launch. A tested provider contract would
justify changing the preferred native path.

### D3 — Event-driven waits; no mandatory new daemon [OWNER REVIEW]

**Requirement and evidence.** The kernel should wait without LLM polling.
Async operations and durable records already provide suitable mechanisms.
Runtime.open/close still have a finite owner-managed lifetime.

**Alternatives.** Model-driven polling; a thread per tool; an installation daemon
from day one; or runtime-owned async broker tasks with explicit shared admission.
Model polling burns inference allowance. A thread per network wait wastes host
resources. A mandatory daemon enlarges deployment and authentication scope.

**Recommendation.** Use async transports, durable wait records and events to
wake the caller. Optional task-status polling is deterministic host work, bounded
by server guidance, backoff, deadlines and rate budget. The OS does not need a
model to determine that an HTTP response arrived. If a synchronous adapter is
unavoidable, isolate it in a bounded dedicated executor or subprocess, never the
filesystem executor; cancellation must account for still-running work.

**Cost and change criterion.** Without a daemon, closing the runtime stops local
observation; recovery resumes from durable evidence later. A long-lived broker
service becomes appropriate when several runtimes need shared server ownership
or unattended completion after application exit. That deployment choice must
name the supervisor and durable owner. A conventional OS also runs continuously;
the useful distinction here is host event handling independent of LLM turns.

### D4 — Model endpoint capacity explicitly [OWNER REVIEW]

**Requirement and evidence.** A serial endpoint must not receive overlapping work;
a concurrent one should use its allowed capacity. Existing model admission is
runtime-local and Exclusive's generic keys are not a shared counted semaphore.

**Alternatives.** One global tool lock; one lock per connection; adaptive probing;
or trusted hierarchical concurrency profiles. A global lock wastes independent
servers. Connection-local locks allow several connections to overload one
backend. Probing with real mutations is unsafe and does not discover account
quotas reliably.

**Recommendation.** Define endpoint identity, deployment/replica identity,
auth principal/account scope, concurrency groups and capacities in trusted
configuration. Unknown capacity defaults to one per configured constrained group.
A call may need a server-wide and a tool/resource-group permit. Admit the complete
set atomically or acquire in a fixed order with rollback; never hold one permit
while indefinitely waiting for another. Keep rate budgets separate from inflight
limits. Fair queues should interleave processes/accounts, with bounded lengths
and explicit queue-full outcomes; FIFO within a process where ordering matters.

An illustrative profile might permit four requests at a service, two for an
account, and one mutation on a particular document. Its effective concurrency
is constrained by all three, not just the largest number. A server being
single-threaded internally does not necessarily mean it forbids concurrent
requests; configure the external contract, not a guess about its implementation.

**Cost and change criterion.** Conservative defaults underuse some endpoints.
Raise limits from deployment guarantees and controlled tests, not tool hints.
Replicas increase capacity only if state isolation and backend/account quotas
permit it. A cluster-wide limit requires a shared coordinator or gateway; a
local lock cannot constrain independent clients outside that scope.

### D5 — Share admission authority across the actual contention scope [OWNER REVIEW]

**Requirement and evidence.** Multiple Runtime instances can point to the same
server. Per-run SQLite records and Python locks do not provide a universal gate.
Host advisory locking already exists for a few specific resources, but does not
supply general remote concurrency accounting.

**Alternatives.** Require one owning runtime; shared local broker; shared database
leases; or endpoint/gateway-enforced admission. Each can be correct within a
stated deployment boundary. None automatically constrains arbitrary third-party
clients.

**Recommendation.** Start with a single broker/admission owner per configured
endpoint group on one installation, or explicitly reject unsupported shared
ownership. Store persistent permit identities and uncertain holds. Use a
coordinator generation to fence stale local dispatchers. For multi-host use,
require a shared broker/gateway or equivalent external admission authority.
An expired owner lease allows takeover of observation, not assumed release of
remote execution capacity. Reconcile outstanding calls before reusing holds.

**Cost and change criterion.** Shared ownership adds operational complexity and
can become an availability bottleneck. Single-owner deployment is simpler but
must be stated as a product restriction. Owner must select the required initial
scope: one runtime, one installation, or several hosts. That decision drives
storage topology; this document does not pretend an in-process semaphore solves
all three.

### D6 — Separate request slots, remote execution and semantic conflicts

**Requirement and evidence.** A returned task ID may close an HTTP exchange while
remote work continues. A mutation may also require exclusive access to logical
state. The existing application sometimes holds verification ownership across
several operations for semantic reasons.

**Alternatives.** Hold every resource until final completion; release all at an
HTTP response; or track each resource independently. The first can block status
and cancellation behind long tasks. The second can exceed real remote capacity
or admit conflicting writes.

**Recommendation.** Track transport request capacity, logical remote execution
capacity, rate allowance and conflict ownership separately. Task acceptance
releases only the request capacity justified by the endpoint profile. Remote
execution occupancy remains until trustworthy terminal evidence. Reserve a
bounded control path for status/cancellation that does not wait behind the very
task it must control. This is not permission to exceed a server's hard transport
limit: if it truly cannot process control concurrently, record that limitation.

Do not acquire shell/verification permits merely because a call is MCP. If a
particular tool can mutate the protected workspace, retain appropriate conflict
protection and require mediated workspace access. Never release a necessary
semantic lock just to improve throughput. Reject unsupported dependency cycles;
future lock splitting needs operation-specific correctness evidence.

**Cost and change criterion.** More counters and states complicate inspection.
They are justified because different events release different resources.
Collapse counters only when the endpoint contract proves their lifetimes
identical. This is a useful design test: ask what exact event makes each resource
safe to reuse.

### D7 — Add a true pre-dispatch queue boundary

**Requirement and evidence.** The current kernel marks capability dispatch before
calling its handler. external_write handler exceptions become unknown effects.
Thus even a queue timeout before socket use could look like a lost remote write.

**Alternatives.** Queue inside an ordinary handler; queue before creating any
operation record; or extend generic effect execution with explicit prepared,
queued, dispatch-intent and terminal evidence. The first loses certainty. The
second loses durable identity, charging and restart visibility while waiting.

**Recommendation.** Record and charge the logical operation once, then queue
before remote dispatch. Keep admission/adapter phases visible to the generic
kernel. Recheck revocation, generation, deadline and endpoint pins immediately
before sending. A durable dispatch-intent precedes the send. After that boundary,
a crash without terminal evidence is conservatively unknown even if the send
might never have happened. An adapter can establish known-not-submitted only
with positive local evidence, not absence of a remote ID.

**Cost and change criterion.** This requires a generic execution hook or staged
capability contract, and state-schema compatibility planning. It is larger than
registering an MCP handler, but avoids misclassifying queue cancellation and
makes fair admission observable. A wrapper-only prototype could explore protocol
compatibility, but cannot qualify as the finished design.

### D8 — Preserve effects, replay and cancellation truth [OWNER REVIEW]

**Requirement and evidence.** Current unknown effects block further work except
narrowly approved raw-generation isolation. Stable intent and retained callback
IDs prevent duplicate dispatch. Existing tool retries are deliberately restricted.

**Alternatives.** Retry every disconnect; trust a JSON-RPC ID as idempotency; drop
holds after a timeout; or require durable outcome evidence. The first three can
duplicate mutations or oversubscribe a still-busy server.

**Recommendation.** Distinguish business outcome, execution termination and
effect certainty. A tool error result is not necessarily transport failure and
may describe partial changes. Cancellation request is an intent, not settlement.
A closed local stdio child does not prove delegated external work ended. Known
read-only tools can still be running and consuming server capacity after a
socket loss. Retain those holds too.

Use one logical operation ID with distinct transport-attempt IDs where an attempt
is authorized. Automatic retransmission of effects needs an actual endpoint
idempotency/reconciliation contract; request IDs alone provide correlation.
Persist a completed response before delivery and replay it without re-executing.
Keep immutable original outcomes; append reconciliation evidence and fence late
responses from changing the chosen logical result.

**Cost and change criterion.** Conservative uncertainty can halt unrelated work
under today's global barrier. Keep that behavior for initial support. Scoped
uncertainty could improve availability but requires a separate conflict-domain
proof and owner approval; MCP transport work should not silently weaken it.
Read-repeatable classification can justify a new read attempt only under explicit
policy, while prior physical occupancy is still accounted for.

### D9 — Pin schemas and authority independently of discovery

**Requirement and evidence.** Registry digests and grants are already strict.
MCP schemas need not correspond to a simple Python model. The worker grammar is
also a separate application constraint.

**Alternatives.** Advertise all discovered tools; coerce arbitrary schemas into
Python types; or register approved versioned descriptors with exact validation.
The first widens authority; lossy conversion can accept inputs the tool contract
rejects or reject valid inputs without explanation.

**Recommendation.** Preserve canonical schema documents and declared dialect;
validate against a supported, bounded JSON Schema implementation. Explicitly
reject unsupported schema features and remote reference resolution unless
pre-approved and pinned. Namespace capability identity by configured server,
tool name and descriptor version. Pin effect/replay/cancellation policies from
trusted host configuration, plus protocol profile and schema digests. Refresh
catalogs as new versions; do not mutate grants in flight. Cache discovery by
endpoint/principal/profile, not globally across tenants.

The application chooses which granted tools appear in its action grammar and
prompt. Present a bounded catalog or lookup capability rather than dumping every
schema into every model context. Selection still requires host authorization;
a missing prompt entry is not a security boundary.

**Cost and change criterion.** Schema compatibility and version churn need explicit
errors and operator workflows. A limited schema subset may be a reasonable V1
choice if advertised. Evidence of a correct exact translation could simplify
some adapters, but should not erase the source schema or its digest.

### D10 — Enforce tool egress and credentials at the host boundary

**Requirement and evidence.** Current model locality checks do not automatically
cover remote capability arguments. A local model can send sensitive data to a
remote tool. Existing artifact defaults also do not establish complete remote
classification propagation.

**Alternatives.** Trust the tool name/description; reuse only model policy; or
check the actual endpoint, principal, argument artifacts and allowed data classes.
Only the last follows the real data path.

**Recommendation.** Keep credential references in trusted endpoint configuration
and resolve secrets inside the broker. Never expose credentials in model context,
operation arguments or ordinary audit events. Pin destination identity and auth
principal; reject unauthorized redirects or endpoint substitutions. Check egress
before send and each newly supplied input response. Treat server descriptions,
instructions and output as untrusted data. Resource URLs are references, not
permission to fetch. Downloads require another authorized, bounded effect.

Retain typed content and artifact references with byte/media/classification
limits. Bound streamed input before materializing it and budget artifact storage.
Validate structured output without interpreting schema failure as proof that the
remote mutation did not occur. A result too large to store is a recovery problem,
not a reason to rerun the operation.

**Cost and change criterion.** Correct redaction and classification require more
than a transport SDK. First support can restrict media and destinations, with
explicit rejection. Broader support follows policy and storage qualification.

### D11 — Make input requests explicit, bounded continuations [OWNER REVIEW]

**Requirement and evidence.** A server may need human input or model sampling.
Current native subordinate admission permits specific capability callbacks;
it does not establish a general recursively callable model scheduler.

**Alternatives.** Automatically service every input request; deny all; or enable
specific handlers with inherited authority and budgets. Automatic service can
create hidden costs and deadlocks, including a parent holding the only model
slot while asking for another model call.

**Recommendation.** Initial strict support disables unsolicited sampling and
unconfigured input flows. If enabled, publish a durable input-required state,
route to the owning application/user or a separately authorized model operation,
and retain original deadlines and accounting. Bound recursion depth, number of
round trips and answer bytes. Keep transport readers independent of slow
callbacks. The provider resumption rules in D2 still apply.

**Cost and change criterion.** Some servers will be unusable under this subset;
report missing capabilities before normal work where discovery permits it.
Owner should identify required servers before approving broader support.
A designed continuation dispatcher and deadlock tests would justify expansion.

### D12 — Keep waiting residency explicit; defer live hibernation

**Requirement and evidence.** max_workers/residency is not a model-slot limit.
Current park/hibernate requires settled effects and no permits. A worker waiting
on a remote call can therefore release inference while remaining resident.

**Alternatives.** Treat every tool wait as hibernation; retain resident async
continuations; or add durable live-I/O parking. The first violates current
lifecycle invariants. The third needs callback delivery, owner fencing and
activation recovery that the runtime does not yet establish.

**Recommendation.** Retain bounded resident continuations initially. Expose the
wait reason so occupancy is understandable. Bound outstanding calls, queue bytes,
result bytes and remote tasks separately. A future durable wait state could
release process residency while the broker owns the effect, but must not be
implemented by calling today's hibernate method.

**Cost and change criterion.** Enough waiting workers can fill residency even
when model capacity is free. Owner should decide whether that limits the intended
workload. Measure it before adding live-I/O parking; if thousands of concurrent
remote waits are required, that extension becomes core scope rather than polish.

## Proposed execution contract

This section describes records and transitions, not final Python APIs. Keep
external transport details out of the public process scheduling interface.

### Durable records and ownership

| Record | Minimum retained facts | Owner |
| --- | --- | --- |
| Endpoint profile | Configured endpoint identity, transport/revision, auth reference and principal scope, allowed features, concurrency groups, rate policy, data policy, recovery guarantees, configuration digest | Trusted host bootstrap |
| Capability version | Endpoint profile reference, remote tool name, exact schema digests, effect/conflict policy, output bounds and cancellation/replay guarantees | OS registry after host approval |
| Logical operation | Original account, process/scope/generation, intent digest, arguments/artifact references, descriptor pins, deadline, logical step charge, continuation reference | OS effect journal |
| Admission entry | Queue order, required capacity vector, queue deadline, state, owner generation, issued permit IDs | Broker/admission owner |
| Transport attempt | Logical operation ID, unique attempt ID, dispatch-intent timestamp, transport correlation ID, actual endpoint/principal, send knowledge, remote task/reconciliation identity if supplied | Transport adapter with OS persistence |
| Remote execution | Known remote identity, current observed status, last evidence, control attempts, retained execution/conflict holds | Broker recovery owner |
| Terminal receipt | Original response or bounded retained evidence, result classification, termination/effect certainty, usage provenance, artifact refs, delivery fence | OS settlement |
| Continuation delivery | Result reference, generation, pending/consumed marker or replayable equivalent | Application continuation via OS ports |

Secrets are referenced, never copied into these public records. Opaque continuation
state may be sensitive and needs protected storage and expiration policy. Audit
events must not duplicate unrestricted response bodies. The current record/event
storage emits values, so redaction must be designed at write boundaries rather
than assumed to exist downstream.

Endpoint capacity and run effects may live in different stores. A single SQLite
transaction only covers records in the same database. If using a shared broker
with per-run journals, use stable permit/operation IDs and a replayable settlement
outbox/inbox handshake. Persist completion in the broker, acknowledge it durably
in the run, then mark delivery; retries replay receipts. Do not claim atomic
cross-store commit. Recover conservatively if either side is unavailable.

### State and release table

The names below are conceptual. They need a schema-version decision before
implementation; do not overload an existing process state with a new meaning.

| State/event | Evidence required | Resources and next action |
| --- | --- | --- |
| Prepared | Authorized immutable intent and accounting recorded | No inference or endpoint execution hold; eligible to enqueue |
| Queued | Durable admission request; no dispatch-intent yet | Queue/memory budget and residency may remain; withdraw safely on deadline/revocation |
| Dispatch-intent | Owner fenced, grants/deadline rechecked, endpoint permits retained, attempt committed | May have been sent after this point; crash requires reconciliation |
| Submitted / running | Adapter send evidence, possibly remote task identity | Retain applicable request/execution/conflict holds; wait asynchronously |
| Input required | Version-valid response, correlation and continuation state retained | No model use unless separately authorized; keep original account/deadline and applicable remote holds |
| Task accepted | Remote task identity persisted | Release only completed request permit; retain remote execution/conflict holds |
| Terminal observed | Valid evidence of remote outcome and termination within adapter contract | Store response and certainty facts; do not yet wake with unpersisted data |
| Settled | Durable receipt plus consistent hold transition | Release justified holds, queue durable delivery, wake continuation |
| Uncertain | Could have executed; evidence insufficient | Retain relevant capacity/conflict holds; apply current global uncertainty barrier; reconcile without blind resend |
| Cancel requested | Durable control intent | Deliver bounded cancel request where supported; stay running/uncertain until adequate evidence |

A terminal protocol response can establish that a request ended without proving
all side effects or delegated jobs ended. Endpoint adapters must define what
counts as terminal for the resource they account for. A tool intentionally
starting a detached job needs an explicit task/job contract; a success string
alone cannot make the broker track unknown background work correctly.

At the response boundary, store enough bounded evidence to prevent a duplicate
send even if output validation or artifact publication fails. Reserve response
storage where feasible. If a full response cannot be retained, keep the minimal
identity/terminal evidence and classify missing output separately. A crash after
remote execution but before any local receipt remains uncertain. There is no
local transaction that eliminates that network gap.

### Normal call sequence

1. The model completes a valid action turn; inference execution settles and its
   reservation releases through the normal path.
2. The application creates a stable CapabilityCall intent referencing an approved
   descriptor. The OS validates grants, scope, arguments, data destination and
   original budget/deadline.
3. The broker durably queues the call. No LLM is active for this wait. Other
   eligible processes may use inference capacity.
4. The admission owner grants all required endpoint resources. The OS revalidates
   transient authority and commits dispatch-intent before transport submission.
5. The async adapter handles the response, task observation or configured input
   exchange. It does not block the event loop on synchronous SDK work.
6. The OS stores terminal evidence, settles holds and exposes a replayable result.
7. The owning continuation consumes the result. If it needs further reasoning,
   it requests a new model operation through ordinary inference admission.

Two callers replaying the same intent attach to the same execution/result. They
do not consume two queue entries or send two mutations. A changed argument or
capability version requires a new intent; it cannot reuse the old operation ID.

### Budgets and shutdown

Queue wait, execution, user-input wait, backoff and continuation all consume the
original elapsed deadline. Count a logical tool step once; count physical
attempts, status requests, bytes and endpoint charges separately. Do not charge
MCP latency as model tokens or create free model sampling. New endpoint budgets
must be explicit generic accounting dimensions with caller inheritance. Status
and cancellation need bounded operational allowance so exhausting normal tool
quota does not silently disable cleanup.

When a process deadline expires, stop new semantic work. Continue only explicitly
authorized reconciliation/cleanup under a separately bounded OS maintenance
policy; do not extend the user's work allowance. This maintenance-policy contract
is an open implementation prerequisite, not a claim about current behavior.
Without it, preserve the hold for later operator recovery.

On shutdown: stop new submissions, durably withdraw known-unsent queue entries,
record outstanding work, attempt bounded cleanup, and close only transports or
subprocesses owned by this broker. Do not terminate shared endpoint services
because a UI or run closes. Awaiting local cancellation does not prove remote
completion. Restart takes a new owner generation, restores holds and attaches to
known remote identities before admitting replacement work.

## Worked scenarios and review calculations

These are design exercises, not measurements or executed tests.

### A. Two workers, one model slot, one serial MCP endpoint

Worker A uses the model and ends its turn, then enters an MCP call that takes
30 seconds. Model occupancy becomes zero; endpoint execution occupancy is one.
Worker B can use the single model slot during those 30 seconds. If B also calls
the same serial MCP endpoint, B queues without holding the model slot. When A's
terminal receipt is stored, its endpoint permit becomes available to B; A's
next model turn independently competes for model admission.

If both workers count against max_workers, their process residency remains two.
This design does not promise a third worker can start. If A is instead a current
native AgentJob blocked inside its callback, its admission remains one: the
example does not work until D2 is resolved. This is the distinguishing acceptance
test for the user's first requirement.

### B. Eight calls to an endpoint with capacity three

With one shared execution group of capacity three, at most three calls run and
five queue. If each occupies the endpoint for two seconds and has no dependencies,
the idealized completion batches are at 2, 4 and 6 seconds. This ignores network,
queue fairness, rate limits and provider variability; it is not a throughput
promise. A single lock would take about 16 seconds under the same assumptions.
Per-runtime gates set to three across two runtimes could send six simultaneously,
which violates the shared capacity. This explains why D4 and D5 are separate.

For stable average load, the familiar estimate L = arrival rate × mean duration
can guide capacity planning. Ten calls per second at two seconds per call imply
about twenty executing calls on average. A capacity-three endpoint cannot serve
that load without queue growth, rejection or lower arrivals. A larger queue
changes waiting time, not sustainable throughput. Bound it.

### C. Queued cancellation versus lost mutation acknowledgement

Call A waits behind a serial endpoint and is cancelled before dispatch-intent.
The broker withdraws its queue entry and reports known-not-submitted. No remote
reconciliation is required. Call B has committed dispatch-intent and the service
may have created an external object before the connection breaks. It becomes
uncertain; do not retry B merely because its JSON-RPC request ID is known. Query
by an endpoint-supported idempotency/status key, retain evidence, or require
operator reconciliation. The ordinary handler wrapper cannot cleanly implement
this distinction because current dispatch marking precedes handler execution.

### D. Long remote task and cancellation

The server returns a task handle quickly. Its request slot can be reused if the
profile allows, while one remote execution hold remains. Deterministic status
observation does not reserve inference. A cancel acknowledgement arrives; keep
the execution hold because acknowledgement alone does not establish stopping.
A terminal status later settles the physical execution, while effect certainty
still reflects whether partial external changes are known. If the task expires
before observation, keep uncertainty rather than inventing success or rollback.

### E. Input request and dependency cycle

A server needs model-generated input while the outer native job holds the only
model slot. Automatically submitting another model call deadlocks. Releasing
the counter without suspension evidence risks overcommit. Initial support must
reject that unsupported input feature or use the completed-turn path. Even then,
a nested tool request that requires the same serial endpoint can deadlock against
the outer call's remote hold. Bound or prohibit reentrant dependencies, or use a
server contract that explicitly releases the relevant resource while waiting.

### F. Result arrives during cancellation or owner takeover

Cancellation and completion may race. Use CAS on the owned operation generation
and record both facts. A valid terminal result can settle capacity even after
logical delivery was cancelled; it must not revive the cancelled continuation.
A stale broker can submit neither replacement work nor final delivery under a
new owner generation. Local fencing cannot stop an old already-sent remote
request unless the endpoint supports remote fencing, so recovery retains its hold.

### G. Catalog drift and revoked credentials

A server changes a tool's schema or effect behavior while a call is queued.
Keep the old descriptor pin. If that exact contract can no longer be honored,
fail before send and require a new explicitly authorized intent/version. Do not
silently widen arguments or swap principals. Already-completed receipt replay
remains historical evidence; fresh network calls, including recovery calls,
still require valid access. Credential rotation may preserve principal identity;
a change of account is a new authority decision.

## Questions added for owner and implementation review

The questions are intentionally broader than the recommended first slice.
Unanswered entries do not imply permission to choose a broader scope.

| ID | Question | Current recommendation or missing evidence |
| --- | --- | --- |
| Q01 | Does no inference thread mean no OS reservation, no active provider generation, or no retained GPU memory? | Define separately; guarantee no reservation for direct waits; physical release needs provider evidence |
| Q02 | Must native AgentJob MCP be supported in the first release? | Major blocker; prefer strict completed-turn path first |
| Q03 | Can a native provider attest suspend and gate resume, including retained memory? | Not established by current adapter |
| Q04 | Is a runtime-scoped broker sufficient, or must work survive UI/application exit unattended? | Determines daemon/supervisor requirement |
| Q05 | Is sharing required across runs, users, installations or hosts? | Select actual admission scope before storage design |
| Q06 | Which concrete servers and protocol revisions are launch targets? | Needed to pin SDK, transports and conformance fixtures |
| Q07 | Are endpoint limits per connection, process, account, tool, resource or deployment? | Trusted profile; unknown defaults to one |
| Q08 | Who owns capacity changes, and what evidence permits raising them? | Host/operator, not model discovery hints |
| Q09 | Are several replicas independent, and do they share backend quota or mutable state? | No automatic replication assumption |
| Q10 | Must calls preserve ordering within a process or across a resource? | Initial one top-level effect per process; explicit conflict keys |
| Q11 | Are parallel tool batches within one worker required? | Defer; current top-level-effect contract rejects general fan-out |
| Q12 | How should fairness work across tenants, accounts and interactive/background calls? | Bounded per-owner queues; precise weights unresolved |
| Q13 | How large may queues, responses, streamed media and task populations become? | Explicit byte/count budgets required; values need workload evidence |
| Q14 | Which tools support true idempotency or status lookup after acknowledgement loss? | Required per endpoint; request ID alone insufficient |
| Q15 | What counts as terminal for tools that start detached work? | Require explicit task/job contract |
| Q16 | How long are remote task/results retained, and can recovery outlast that TTL? | Store receipts early; expiry does not clear uncertainty |
| Q17 | Can read-only work continue remotely after cancellation and consume scarce capacity? | Assume yes absent termination proof |
| Q18 | Should one uncertain endpoint block unrelated endpoints? | Preserve current global barrier initially; scoped change separate |
| Q19 | Who may reconcile uncertain mutations and what proof is accepted? | Trusted adapter/operator path; exact public interface unresolved |
| Q20 | What maintenance allowance permits status/cancel after user deadline or budget exhaustion? | Separate bounded cleanup authority; cannot extend semantic work |
| Q21 | Is live-I/O parking necessary to avoid filling max_workers with waits? | Defer unless target workload requires it |
| Q22 | Which data classes may reach each endpoint and auth principal? | Explicit tool egress policy |
| Q23 | May a tool access local workspace files or mutate the actual repository? | Only through granted mediated access; MCP is not a sandbox |
| Q24 | How are server executable installation, environment and credential access authorized? | Trusted bootstrap; spawning a process does not confine it |
| Q25 | Are remote resource fetches, prompts and subscriptions in scope? | Separate grants/features; initially defer |
| Q26 | Which schema dialect/features and references are supported? | Preserve exact schema; bounded validation; reject unsupported parts |
| Q27 | How should catalog drift affect queued and replayed calls? | Pin queued intent; replay retained receipts; new versions require new authority |
| Q28 | Are sampling, human elicitation or URL-based input flows required? | Explicit handlers only; no default hidden model work |
| Q29 | What input-request recursion and round-trip limits are appropriate? | Must inherit original authority and deadlines; values unresolved |
| Q30 | How are sensitive opaque continuation tokens retained and redacted? | Protected broker state; avoid event-body leakage |
| Q31 | How are business errors, partial mutations and malformed output presented to the agent? | Keep outcome/termination/certainty separate |
| Q32 | How can a caller recover if storage is exhausted after a successful mutation? | Minimal durable terminal evidence; never automatic mutation replay |
| Q33 | Which endpoint monetary/rate costs are reserved and how are unknown charges reported? | Separate from inference token accounting |
| Q34 | What changes are needed in the bundled worker grammar, catalog and context packing? | Explicit application integration; no implicit all-tools exposure |
| Q35 | Which old runtime states can Resume after the new record schema lands? | Fresh-state default unless migration is explicitly designed and tested |
| Q36 | What diagnostics can users see without leaking secrets or cross-tenant tool data? | State/hold/queue/recovery evidence with redaction |
| Q37 | Can control requests reach a truly serial or hung server? | Bounded control lane helps only when server supports it; no guarantee otherwise |
| Q38 | Which shared-provider lifecycle operations may the UI initiate? | Only owned resources; shared broker/service lifetime is explicit |

## Acceptance plan for a future implementation

No tests below were implemented or executed as part of this design. These are
criteria for accepting a later change, not evidence that MCP already works.

| Area | Required observable result |
| --- | --- |
| Inference independence | With one model slot, A waiting on MCP does not prevent B's model turn; assert both local admission and provider execution evidence appropriate to the path |
| Native honesty | Current opaque callback path rejects strict-release capability or is clearly excluded; suspended path cannot resume before readmission |
| Endpoint admission | Serial maximum observed concurrency is one; capacity-N is never exceeded; two runtimes respect the same configured shared group |
| Queue semantics | Queue cancellation/deadline/revocation is known-unsent; no socket call; no leaked permits; original logical charge retained correctly |
| Crash boundaries | Crash before send, after dispatch-intent, after remote mutation, after receipt persistence and before delivery; restart never blindly duplicates an uncertain mutation |
| Recovery | Durable receipt replays once logically; task ID/status recovery respects original account; expired/missing status stays uncertain |
| Cancellation races | Cancel acknowledgement alone does not release remote occupancy; late terminal evidence releases justified holds without reviving delivery |
| Deadlocks | Serial endpoint input recursion and one-slot model callbacks are rejected or resolved by an explicitly tested contract |
| Authority | Unlisted tools, changed schemas, cross-principal replay substitution, unauthorized redirects and disallowed egress fail before submission |
| Content/storage | Oversized streamed payload is bounded; malformed structured output does not imply no side effect; storage exhaustion cannot trigger duplicate mutation |
| Lifecycle | Closing one run cannot stop shared services; stale owner cannot dispatch/deliver; restart restores uncertain occupancy |
| Generality | Non-coding program invokes a tool and completes with an artifact, without Git/check/task requirements |
| Protocol profiles | Separate 2026-07-28 and supported legacy fixtures; no wrong handshake/task-method assumptions; unsupported input features fail explicitly |
| Accounting | Waiting consumes elapsed deadline; retries do not refill budget; MCP control costs and model calls are separately observable |

Relevant existing regression homes include `tests/test_runtime.py` (unknown
remote effects and native release), `tests/test_os.py` (admission, cancellation,
restart holds and filesystem nonblocking behavior), `tests/test_inference_lifecycle.py`
(generation-only isolation), `tests/test_capability_boundary.py`,
`tests/test_runtime_general.py`, `tests/test_contracts.py`, and
`tests/test_native_worker.py`. Extend the appropriate ownership tests rather than
assuming an MCP protocol conformance test proves OS settlement correctness.
Use local deterministic fake servers and crash/fault injection first. Live provider
qualification is a separate authorized step and must report its limits.

## Proposed implementation order, without implementing it

1. Owner review of D2, D3, D5, D8, D11 and Q01/Q06/Q21; pin initial supported
   execution paths, deployment scope, endpoint profiles and protocol versions.
2. Define generic staged effect/admission/receipt interfaces and state versioning.
   Prove known-unsent versus uncertain dispatch and cross-store recovery first.
3. Add a strict tools-only transport slice for a deterministic server and a
   non-coding process. Qualify inference independence and serial admission.
4. Add bounded concurrent endpoints, shared ownership, authority/data checks,
   output limits and failure recovery. Qualify cancellation and crash boundaries.
5. Integrate the bundled worker's grammar/catalog and context handling explicitly.
6. Add optional tasks/input flows and native suspension only after their separate
   contracts pass. Do not advertise all MCP features because basic tools work.

Promotion into maintained module/setup/usage/configuration docs should happen
when an accepted implementation changes those interfaces. This proposal itself
does not create settings, install a server, authorize credentials or change
Resume compatibility.

### Checkpoint 4: design drafted and ready for structural verification

Completed the twelve decision records, resource/state model, seven worked
scenarios, expanded question register and future acceptance plan. The central
recommendation is a generic broker with a real pre-dispatch boundary and strict
completed-turn support first. Unresolved high-impact choices are explicitly
marked; no implementation is authorized by this document. Next: check source
references and documentation structure, record actual verification and append
the next available FIX entry without disturbing concurrent documentation work.

## Documentation review and verification receipts

This task adds the proposal, its single parent link and its JSON navigation node;
regenerates the HTML file map; records an MCP design-review item under runtime
and provider tasks; and appends a FIX investigation entry. The retained project
checklist is saved in `AGENTS.md` and was read back against
`docs/project-memory.md` on 2026-11-13. The replacement user-provided instructions
include that retained checklist; no runtime hook was added.

Reviewed adjacent kernel, process, capability, inference, storage, SDK, retry,
context, worker and services guides, the runtime boundary, and setup/usage/settings
ownership routes. They describe current behavior and need no MCP interface or
configuration edits because none shipped. Onboarding and canonical project
memory need no rule changes. Existing scheduler-support documentation was updated
by another task during this investigation; its current distinction between
implemented local admission and proposed shared resource handling agrees with
this design. Preserve those concurrent edits.

The first WSL documentation-generator run failed because the new document had
Windows code-page bytes. The file was converted to UTF-8 and the rerun passed:
392 files, 202 notes, 201 tree links and README reachability verified. Final
check-mode and post-ledger results are recorded below when complete. These checks
validate documentation structure and navigation, not MCP correctness.

Source/test path references in this proposal were checked for existence. No
production source or tests were edited by this task; no runtime tests, provider
calls, saved-run changes, staging or commits were performed. Existing and
concurrent changes include other documentation, scripts and tests. The original
temporary preservation directory recorded at checkpoint 1 was not available
after the interruption, so no final byte-for-byte baseline comparison is claimed.
Git's current diff was inspected without resetting or restoring any existing work.

For a handoff, read the recommendation page, D2/D5/D7/D8, the state table and owner
questions first. Then re-read current source and applicable guidance: HEAD alone
is insufficient because this checkout contains concurrent changes. Treat all
acceptance scenarios as future work. Remaining product work is owner review and,
only when separately requested, implementation and qualification.

### Checkpoint 5: final verification and handoff

After adding FIX-0190 and the runtime/provider review task, both required commands
passed in WSL: `python3 scripts/project_docs.py` and
`python3 scripts/project_docs.py --check`. Each reported 392 files, 202 notes and
201 Obsidian tree links, with README reachability verified. The generator updated
the maintained HTML map. No implementation tests or live qualifications were run.
The document is ready for owner review; unresolved decisions are intentional,
not omitted implementation. No further tool execution is required to read it.
