# Polyinference OS design — 4. Synchronizing plans, work, memory and results

## Current agent concurrency contract

Updated using the full agent HTML and the user's later clarifications. The HTML is the agent design, including OS-handled parts; the LLM OS is an application operating endpoints, not a computer-kernel subsystem. [Concurrent coding protocol](concurrent_coding_protocol.md) defines the current operational contract. It supersedes any earlier screenshot-based alternatives below where their scope differs.

Every in-progress coding process owns a codebase copy. Private development overlaps. Every shell/script command, including test/Git commands, acquires a global `shell_mutex`. A separate `verification_gate` serializes latest-head merge, at least one specially prompted development/reconciliation loop, the final one/few local-model testing/examination/assessment iterations, commit and provisional shared-head/report publication. Release verification only after that boundary; release shell after each confirmed command. When both are needed the order is **verification then shell**; an outside shell owner releases before requesting verification. The application coordinator keeps running throughout.

Assessment produces `fail / uncertain / successful`; every normal local completion remains `unresolved` until sprint-coordinator review. Publish completed commits provisionally with verdict/hazards so the next entrant receives them; this is not senior acceptance. Preserve one attributable net-change commit for senior revert and blast-radius analysis. Steering stops new local starts, waits only for the captured in-progress locals (including gate waiters) to finish, then goes to the planner.

| Current extension | Required behavior |
| --- | --- |
| L4-C01 | Each active coding attempt owns its copy, base revision and scoped tool context; no shared editing before publication. |
| L4-C02 | Shell and verification ownership are distinct, obey one acquisition order, and are not computer-OS locks. |
| L4-C03 | Each verifier merges the latest published head, runs reconciliation development and final assessment, and publishes its commit/report before releasing. |
| L4-C04 | Publication stays provisional/unresolved; unknown active effects retain applicable exclusion and senior rollback checks dependents. |


**Lecture basis:** CS350-4.pdf, Concurrency, 50 PDF pages / 44 numbered slides. Uses lectures 1–4 and builds on [the kernel](01-CS350-1-foundations.md), [process/request schemas](02-CS350-2-processes.md) and [graph execution](03-CS350-3-threads.md). **Project context:** cloud strategy feeding local work, multiple future coding workers and a tight local memory budget. **Revision/research date:** 2026-10-16.

## 1. Selected synchronization architecture

Start with one kernel coordinator and one transactional authority for ProjectRun, process, task, operation, reservation and tool-server lifecycle records. Use an embedded SQLite store on local storage as the default metadata design. A separate persistent LangGraph saver and immutable artifact/Git storage may share the deployment but are not assumed to share its transactions.

Use bounded asynchronous queues and per-process command ownership in the host. Database mutations validate expected revisions and constraints. Provider calls, model decoding, tool-server startup, tests and candidate construction occur outside coordination transactions. The shared local model remains an existing backend service.

G1 means multiple logical coding workers, not necessarily multiple kernel coordinators. Keep this distinction: a single coordinator can serve many slow external operations and avoids premature distributed ownership machinery. Multiple kernel owners are an optional later deployment feature.

## 2. Slide-to-design derivation, in order

PDF references distinguish repeated reveals.

| PDF pages / numbered slides | Lecture concept | Polyinference consequence |
| --- | --- | --- |
| 1–3 / 1–3 | Process/thread review and outline | Shared kernel records need ownership despite private worker continuations. |
| 4–11 / 4–8 | Lost read-modify-write updates | Task claims, cloud budget and residual-memory reservations must change atomically. |
| 12–16 / 9–13 | Atomics/locks and publication flags | Publish complete TaskSpecs/results before declaring them runnable/available. |
| 17–24 / 14–20 | Sequential consistency, compiler/CPU ordering, fences | Use supported primitives and storage contracts; plain flags or Python interpreter behavior are insufficient. |
| 25–29 / 21–24 | Producer/consumer races | The cloud-result producer and local-worker consumers must coordinate queue capacity and claims together. |
| 30 / 25 | Mutual exclusion, progress and bounded waiting | Protect single ownership while ensuring eligible tasks eventually get a turn. |
| 31–34 / 26–29 | Mutex APIs and race-free discipline | State which service protects every mutable record/session/workspace. |
| 35–36 / 30–31 | Lock/yield loops | Keep critical work short and suspend on real conditions. |
| 37–42 / 32–36 | Conditions, predicate loops and lost wakeups | Task availability, operation completion and tool readiness need safe register/recheck/wake protocols. |
| 43–44 / 37–38 | Monitors | Encapsulate reservation, task-claim and tool-lifecycle methods so callers cannot bypass invariants. |
| 45–47 / 39–41 | Semaphores and bounded buffers | Limit admitted inference/tool occupancy without confusing it with rate, spend or memory. |
| 48–50 / 42–44 | Benign races and detection | Keep authoritative grants/cost/claims exact; use forced schedules and appropriate race instrumentation. |

The lecture's illustrative “benign races” are not permission to approximate budgets or initialization. Its semaphore buffer example also needs additional index protection for multiple producers/consumers. Do not port informal racy C examples as production synchronization.

## 3. Research and guarantees to rely on

Asyncio locks/conditions/semaphores synchronize tasks, not arbitrary host threads, and condition predicates must be rechecked. [Python synchronization](https://docs.python.org/3/library/asyncio-sync.html). SQLite WAL permits readers and a writer together but only one writer at a time and requires suitable local storage. This fits the initial single-coordinator choice; contention is a later measurement. [SQLite WAL](https://www.sqlite.org/wal.html).

If deployment later uses PostgreSQL, default isolation does not automatically make every multi-step invariant safe, and stronger isolation may require transaction retries. [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html). The API's stable operation IDs express repeated intent, following the explicit-idempotency pattern; actual backend support must be checked. [AWS idempotent API design](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

MCP initialization and tool-schema negotiation are protocol steps, not evidence that a server fits memory or that its side effects can be repeated safely. [MCP lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle), [MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools). Kernel resource/lifecycle coordination remains necessary around them.

For future distributed ownership, etcd's API illustrates checking ownership together with the protected update. A lease expiring does not terminate a paused caller. [etcd concurrency](https://etcd.io/docs/v3.6/dev-guide/api_concurrency_reference_v3/). Language memory ordering, database serializability and cloud event ordering remain different contracts. [Go memory model](https://go.dev/ref/mem). Native race tools can help native components; they do not prove the application protocols below. [ThreadSanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html).

## 4. Concrete shared-resource invariants

| Shared object | Owner and protected invariant |
| --- | --- |
| Accepted plan / Info Documentation revision | Controller publishes a complete validated version; tasks pin a version and never read a half-updated plan |
| Task Queue | Task service admits bounded records and gives one active attempt ownership of an executable TaskSpec |
| Process continuation | One graph driver; lifecycle/revision checks reject stale commands and cancelled-process dispatch |
| Operation journal | One logical effect ID/fingerprint; repeated callbacks settle once |
| Local memory ledger | Model/serving residency counted once per domain; tool-server residency and per-call/worker peaks cannot be double-granted |
| Cloud account/project budgets | Committed usage plus outstanding reservations remains within the admission policy |
| Tool/MCP server instance | One startup per generation; active leases prevent idle teardown; readiness is published only after initialization |
| Mutable provider/MCP session | Explicit owner/queue; transport multiplexing alone does not authorize concurrent session mutation |
| Workspace and working head | Worker develops privately; verification owner reconciles, assesses and publishes a provisional head/report before release; senior review is separate |
| TaskReport / project acceptance | Durable evidence and exact identities precede notifications or final acceptance |

## 5. Queue and plan revision protocol

### 5.1 Publish and claim

Cloud Result Processor builds a proposed plan outside the transaction. The task service then validates finite limits, granted features, dependency IDs, queue byte/count capacity and the expected ProjectRun revision. It atomically publishes the immutable plan/task records and new plan pointer. A partial batch is not silently exposed as a complete plan.

Claiming selects a task with satisfied dependencies and a materialized immutable base/context, verifies the still-authorized plan/spec and available worker-residency allowance, and conditionally assigns one attempt/process. Expensive checkout setup occurs outside the transaction; the process becomes runnable only when setup succeeds. A second claimant sees the existing claim. Setup failure becomes an explicit failed/rolled-back claim with retryable cleanup, not an invisible lost task.

Task claims reserve process residency, not every backend resource the task may ever use. Each subsequent operation is admitted against its own simultaneous needs. A worker can be claimed but waiting for inference capacity; its bounded resident memory still counts.

### 5.2 Replanning while workers exist

A new strategy is a new plan revision. Never edit the TaskSpec being executed in place. Plan publication serializes with claims and authoritative integration. Superseded work is marked as such and prevented from new privileged dispatch/publication under the old revision, according to the selected cancellation policy.

Default G0/G1 behavior is conservative: retain old attempt outputs as evidence, quarantine their candidate from canonical integration, and require explicit controller revalidation/carry-forward under the new plan before using it. Cloud review cannot erase the cost/history of rejected work. Changing Info Documentation likewise affects newly materialized specs, not an in-flight worker's pinned inputs.

## 6. Resource admission and tool-server lifecycle

For consumable budget `b`, maintain `committed_usage[b] + outstanding_reservations[b] <= admission_limit[b]`. For renewable resource `r`, admit only when existing reservations plus the request fit usable capacity. Apply the per-memory-domain equation in document 1; distinguish permanent/service residency from operation peaks.

The admission transaction validates process state, plan/grant eligibility, the complete resource vector and the request fingerprint, then creates reservations and a PREPARED operation. Either all required simultaneous resources are reserved or none are. Do not hold an inference slot while merely queuing for a tool that must run first. Request-count permits, token/request rate limits, memory and cumulative spend are separate constraints.

A hard spend cap needs a trustworthy bound on all billable work. Raw bounded generations can use configured prices and maximum outputs; an opaque agent job with unbounded internal work cannot satisfy that cap through an estimate. Similarly, measured memory peaks plus headroom guide admission, but hard memory containment requires backend/host enforcement. Record an overrun honestly and block new admissions; do not clamp the usage counter to hide it.

### 6.1 Single startup, leased use, safe teardown

A direct tool needs no resident server unless its implementation does. For local MCP servers, record `server_id`, instance/generation, lifecycle state, resident-memory reservation, negotiated schema/version, active lease count and idle timestamp.

```text
STOPPED -> STARTING -> READY -> DRAINING -> STOPPING -> STOPPED
                  \-> FAILED
```

The coordinator atomically selects one startup owner and reserves its peak. Startup/initialize/discovery happens outside the transaction; competing callers wait on that generation's readiness instead of spawning duplicates. Publish READY only when the transport, required capabilities and expected tool schemas are confirmed; convert the startup allowance to its retained resident allowance without double-counting, while per-call peaks remain separate. Failure wakes waiters with a typed failure and settles/reconciles the owned reservation once.

Dispatch acquires a lease on a READY instance and the call's additional peak/capacity before the call starts. A server with an active/granted call lease cannot be torn down as idle. DRAINING refuses new leases. Idle teardown is allowed only with zero leases and a declared safe restart/state policy; memory is released after confirmed exit/reclamation, not when a stop request was sent. A shared server must still scope every call to its process/workspace.

Use bounded tool descriptions and observation artifacts. If a server cannot fit alongside the local model, return a resource incompatibility/wait outcome. Repeatedly unloading/reloading the model or restarting the server without a policy is thrashing, not progress. Selection of eviction/fairness policy is refined in document 5.

## 7. Operation journal, waits and graph replay

### 7.1 Journal states and ambiguous submissions

Persist the stable logical-step/operation mapping before an external effect. Its record includes input fingerprint/revisions, owner, role/backend kind, grants, reservations, provider IDs when known, output/evidence refs, and known usage.

```text
PREPARED -> SUBMITTING -> ACTIVE -> SUCCEEDED | FAILED | CANCELLED
                    \-> UNCERTAIN -> reconciled terminal outcome
```

Only PREPARED is known not to have started external submission. Commit SUBMITTING before sending. A crash/timeout after that point can be ambiguous even without a returned provider ID. Preserve the operation and relevant reservation; query by supported idempotency key/job ID, reconnect to a known session, or obtain confirmed termination. Do not blindly retry an unknown non-idempotent tool or agent job. If reconciliation is impossible, leave a visible blocked outcome under an explicit resolution policy.

Graph replay looks up the original logical operation: return its retained result, await known active work, or reconcile uncertainty. A fresh graph invocation/transport attempt does not authorize a second effect. Reusing its ID with a changed TaskSpec/context is rejected. SDK retry behavior must honor the same policy, rather than create hidden submissions.

### 7.2 Settlement and wakeup

Once a complete result artifact is available under the configured storage guarantee, one transaction conditionally records terminal status, charges known usage, releases only unused resources, and records pending notifications. Duplicate/reordered completion cannot settle twice. Uncertain cancellation keeps capacity attributed until safe reconciliation or a documented conservative allocation policy resolves it.

Waiters check authoritative state, register through an atomic condition protocol or durable event cursor, and recheck after registration/wakeup. Publication happens before readiness notification. Notifications may repeat or be lost during restart; replay/cursor recovery and a bounded repair scan rediscover committed results. A busy poll loop is not the mechanism. Wake the eligible waiter(s) for changed capacity; broadcast only for a predicate affecting all, such as shutdown/revocation.

## 8. Serialized reconciliation, assessment and provisional publication

Each process develops on a private copy. The current [two-mutex protocol](concurrent_coding_protocol.md) requires shell serialization independently of verification admission. Acquire verification_gate only after releasing outside shell ownership; inside it acquire shell_mutex individually for commands. Merge latest head, run a specially prompted development loop, then final local assessment. No other process enters verification or changes the shared head until commit/publication completes.

The authoritative `provisional_head` points to immutable Git content; review dispositions are separate. Publish each normal completion, including fail/uncertain, with its verdict/hazards and resolution=unresolved. This lets the next process reconcile with the predecessor's actual published code without confusing publication with senior approval.

Store original base, private delta/ref, captured head, final assessed tree, evidence and one attributable commit parented on the captured head. Ensure artifacts exist, then in a short transaction compare expected head/plan authority and publish head/report/notification intent. Keep verification ownership until durable publication; reconcile convenience Git refs afterward. A crash is not an atomic rollback of Git/provider effects. Idempotent replay returns the same report/head outcome rather than creating a second commit.

Senior revert uses verification ownership and shell ownership for commands, checks later dependent work and blast radius, and publishes a recorded inverse change. Final project acceptance still requires senior resolution and current project evidence. Unknown active shell/publication effects retain the applicable exclusion until reconciled. These are application-level ownership records; no computer-kernel integration is required.

## 9. Later multi-coordinator ownership

Before allowing two kernel workers to overlap ownership, add durable monotonic owner generations and require receiving services to check the current generation atomically with dispatch/state/publication. A stale owner may remain alive after a lease expires. Isolate its workspace and reconcile external operations rather than assuming takeover stopped them.

Guard checkpoint writes too: either the saver enforces ownership, old drivers are confirmed stopped before takeover, or writes are isolated and only an epoch-checked authoritative checkpoint pointer is published. An ordinary shared saver plus a process lease is insufficient. This is an enabling requirement for that later feature; G1 coding concurrency can retain one coordinator and omit distributed leases.

## 10. Requirements and acceptance conditions

| ID | System requirement | Origin | Acceptance condition for a future build |
| --- | --- | --- | --- |
| L4-R01 | Every shared object MUST have one declared owner/synchronization scope. | pp. 4–12, 32–34 | Review can locate protection for plans, tasks, claims, sessions, memory, reports and working revision. |
| L4-R02 | Admission MUST atomically reserve all simultaneously needed resources or none. | pp. 4–11, 25–30; L1-R08 | Two workers cannot each obtain the final local-memory allowance or cloud budget. |
| L4-R03 | Completion/report settlement MUST be idempotent and terminal state stable. | pp. 12–24, 27; L2-R02 | Duplicate TaskReport/cloud callbacks neither double-charge nor double-release capacity. |
| L4-R04 | Short metadata locks/coordination transactions MUST NOT span external waits; verification_gate intentionally remains owned across reconciliation/development/assessment/publication. | pp. 35–39 | A slow MCP initialize or cloud review does not retain a global state lock. |
| L4-R05 | Wait registration/publication MUST prevent lost wakeups and recheck predicates. | pp. 37–42 | A task published just before a worker subscribes is still discovered; a spurious wake cannot claim nonexistent work. |
| L4-R06 | Queue capacity, task claims and process setup state MUST remain consistent under cancellation/failure. | pp. 25–29, 38–39, 46–47 | Two claimants get at most one attempt; a cancelled setup cannot lose the queue item or leak residency. |
| L4-R07 | External effects MUST use stable journal intent and declared retry/reconciliation behavior. | publication derivation; documents 1–3; retry research | Crash after agent-job send but before receipt cannot silently create another job. |
| L4-R08 | Budget/memory guarantees MUST distinguish enforced bounds from estimates. | atomic reservation derivation; planning p. 1 | An opaque job cannot be admitted under a claimed hard spend cap without a supported bound; measured RSS is not misrepresented as enforcement. |
| L4-R09 | Provisional publication MUST validate expected plan/task/head and final-tree evidence before releasing verification ownership; the report remains unresolved. | pp. 4–11, 30, 43–44 | A patch verified before another integration cannot publish without revalidation against the accepted candidate. |
| L4-R10 | Inference, memory and cloud limits MUST remain global across enabled coding workers. | pp. 12, 32–34, 46; L3-R03 | Per-worker semaphores cannot each grant the entire shared GPU/tool-memory capacity. |
| L4-R11 | Any later ownership takeover MUST fence state, checkpoint and artifact publication. | atomic publication derivation; ownership research | An old driver resumed after reassignment cannot overwrite the new continuation or accepted result. |
| L4-R12 | Authoritative accounting MUST be exact within the declared storage guarantee; approximate telemetry MUST be separate. | pp. 49–50 | Dropped progress metrics cannot change grants, accepted claims, settlement or project acceptance. |
| L4-R13 | Eligible work MUST have a declared progress/starvation policy under bounded service assumptions. | p. 30 | Continuous new arrivals cannot indefinitely bypass an old eligible local task. |
| L4-R14 | Durable result publication MUST precede notification, and notification handling MUST tolerate duplicates. | pp. 13–24, 37–42 | Restart after report commit but before wakeup still lets cloud review find the report. |
| L4-R15 | Cancellation MUST separate revoked commit authority from confirmed backend termination. | pp. 30, 37–42; L1-R07 | Late output cannot publish after cancellation; an unresolved cloud job remains owned/accounted. |
| L4-R16 | Shared tool startup/teardown MUST use generation ownership and active-call leases. | pp. 12, 30, 37–47; planning p. 1 | Simultaneous first callers launch one server; idle eviction cannot kill an admitted active call. |
| L4-R17 | Replanning MUST publish immutable versions and explicitly disposition old work. | pp. 13–24, 43–44; D | A worker started under the old plan cannot silently commit under the new one. |

## 11. Forced schedules to validate later

Exercise simultaneous claim of one task; two requests for the last memory/budget unit; two first users of a cold MCP server; idle teardown racing an incoming lease; report completion before wait registration; duplicate completion; replan racing private/canonical commit; provider success with a lost response; and restart between candidate storage and working-pointer publication.

Check the invariants after each transition, including retained uncertain work and the memory still consumed by a stopping server. G0 needs these single-coordinator protocols. G1 adds load and shared-worker interleavings. Distributed ownership instrumentation is required only when that feature is enabled. These are design acceptance scenarios; no project implementation/tests were run during this research.

**Next:** [Lecture 5 — scaling the two-tier pipeline and preventing resource cycles](05-CS350-5-scalability-and-deadlocks.md).
