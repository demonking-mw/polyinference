# Proposed OS support for process scheduling

## Part 1 — OS changes and exposures the scheduler needs

Implementation audit: 2026-11-13, working checkout at `da94312`. **Implemented**
means the current code executes the stated behavior at the scope shown.
**Partial** identifies working pieces and the missing part of the proposal.
**Not implemented** identifies a proposed behavior with no current execution path.
The audit is based on source inspection. Runtime and provider behavior were not
exercised for this update.

### 1.1 What already exists, and what is missing

PolyInference already has useful execution mechanisms. The missing boundaries are
process eligibility controlled by the standalone scheduler, and shared resource
distribution/physical dispatch controlled by the OS. They must remain separate.

| Current behavior | Status and source |
| --- | --- |
| Per-runtime inflight limits, configured aggregate context reservations, FIFO within each lane, alternating ordinary and finishing lanes | **Implemented.** `Admission.reserve` checks queue position, slots and configured tokens together. `KernelRuntime.open` creates a separate gate for each configured binding in each runtime. [Admission](../../../src/polyinference/runtime/inference.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Static `local`/`cloud` role routing, hard distribution rules and data constraints | **Implemented.** `RuntimeConfig.role_bindings` selects a binding, and `ProcessPolicy.register` and `dispatch` check the declared destination, physical location, classification and hard role/phase rules. [Settings](../../../src/polyinference/system_settings.py) · [Process policy](../../../src/polyinference/runtime/process_policy.py) |
| Priority, schedule, resource and binding metadata | **Implemented as records.** `ProcessSpec`, `ProcessStatus` and `OperationRequest` carry these declarations or references. Priority has class and relative value (0–100). `Admission._front` reads lane and FIFO order, so priority metadata does not change queue order. [Contracts](../../../src/polyinference/contracts.py) · [Admission](../../../src/polyinference/runtime/inference.py) |
| Coding application defaults | **Implemented in the application.** `AgentServices.process` creates normal priority 50 with static hard distribution. The proposed importance/time preferences are not propagated. [Agent services](../../../src/polyinference/agent/services.py) |
| Explicit host continuations, durable residency, cancellation, settled hibernation | **Implemented.** `Processes.start`, `admit`, `cancel` and `hibernate` enforce these within one runtime. `start` rejects paused records. See §1.6 for suspension and readmission. [Processes](../../../src/polyinference/runtime/processes.py) |
| Read-only local observations | **Implemented.** `ExecutionProgress.progress` combines process status, wait, settlement, deadline, remaining allowances, effects and endpoint counts. [Progress](../../../src/polyinference/runtime/progress.py) |
| Native usage, terminal results and broker callbacks | **Implemented.** `CodexAppServer.generate_job` handles token-usage notifications, terminal turns and callbacks. The usage scope is cumulative native thread. See §1.5 for account quotas. [Codex adapter](../../../src/polyinference/runtime/codex.py) |
| Single-active-run UI | **Implemented in the launcher.** `TestUI.start` rejects another active run. Its run metadata can represent historical runs. [UI](../../../src/polyinference/ui.py) |
| Exclusive resources, immutable records, bounded retries and inherited resource accounts | **Implemented.** `Exclusive.acquire`, `Records.compare_and_publish`, `ModelRetries` and `ProcessLifecycle.bind_recovery` preserve ownership, effect evidence and the original allowance and cutoff. [Exclusive resources](../../../src/polyinference/runtime/exclusive.py) · [Storage](../../../src/polyinference/runtime/storage.py) · [Retries](../../../src/polyinference/runtime/model_retries.py) · [Lineage](../../../src/polyinference/runtime/lifecycle.py) |

The relevant established decisions are `development-docs/FIXES.md#fix-0067`,
`development-docs/FIXES.md#fix-0087`, `development-docs/FIXES.md#fix-0117`,
`development-docs/FIXES.md#fix-0134`, `development-docs/FIXES.md#fix-0135`,
`development-docs/FIXES.md#fix-0154`, `development-docs/FIXES.md#fix-0164` and
`development-docs/FIXES.md#fix-0167`. The
runtime boundary (`design-docs/simplified-os/RUNTIME_BOUNDARY.md`) governs
ownership; richer fields in historical designs do not prove implemented scheduling.

### 1.2 Use a shared resource broker across separate run executors

| Item | Status and source |
| --- | --- |
| Separate run state, continuation storage, journal and uniform limit envelope | **Implemented.** `KernelRuntime.__init__` and `open` use `state_path` for records, artifacts, coordinator ownership and checkpoints. `ProcessPolicy.register` rejects process limits that differ from the runtime envelope. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Process policy](../../../src/polyinference/runtime/process_policy.py) |
| Per-runtime resident worker cap and separate inference capacity | **Implemented.** `Processes.admit` counts durable residents, and `KernelRuntime.open` configures independent inference gates. [Processes](../../../src/polyinference/runtime/processes.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Control and finishing capacity | **Partial.** Trusted registration can set `management=True`, which exempts the process from the worker residency cap. `_reserve_budget` protects a run-level control token reserve. Operations holding conflict keys get a finishing lane and still use the same endpoint capacity. A separate bounded host/control pool and caps on managed roots or control invocations are missing. [Processes](../../../src/polyinference/runtime/processes.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Admission](../../../src/polyinference/runtime/inference.py) |
| Shared endpoint/account/rate broker and installation-wide resident cap | **Not implemented.** `KernelRuntime.open` constructs `Admission` per binding with the run's own `Records`. `Processes.admit` reads that run's residency rows. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Processes](../../../src/polyinference/runtime/processes.py) |
| Resource identities and registry | **Partial.** `Scope` carries tenant/project/run/process identity. `KernelRuntime` pins its configuration and results retain binding, model, protocol and optional session. Local recovery-account roots come from `ProcessLifecycle.account`. There is no shared registry for versioned endpoint IDs, physical-pool aliases and cross-client capacity agreement, authenticated allowance accounts, bucket/windows or scheduler objective roots. [Contracts](../../../src/polyinference/contracts.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Lineage](../../../src/polyinference/runtime/lifecycle.py) |
| Mandatory managed permits, including probes and automatic attempts | **Not implemented.** Normal dispatch and the UI probe use per-runtime admission. The CLI readiness test calls `generate` or `generate_job` directly. There is no managed-mode permit requirement or accounting for external clients. [Kernel](../../../src/polyinference/runtime/kernel.py) · [UI probe](../../../src/polyinference/agent/endpoint_probe.py) · [CLI](../../../src/polyinference/cli.py) |

Keep each objective's application state, source, continuation and per-run journal
separate. Add one OS-owned broker for the installation's shared endpoint pools,
subscription accounts, rate gates and physical admission permits. Every managed
executor uses it. The scheduler receives read-only summaries and sends process
eligibility/preemption decisions to process control; it does not call the broker's
resource-claim, placement, dispatch or settlement interfaces.

This allows different runs to retain their existing uniform per-runtime limit
envelopes. Version 1 need not implement arbitrary per-process limits inside one
runtime, which the current OS deliberately rejects. A global resident-process cap
is additional to each runtime's worker cap; it is separate from inference capacity.

Reserve bounded host/control capacity for coordination, reconciliation and required
finishing work so a full worker pool cannot block its own release. Control treatment
is a trusted, bounded declaration, never a privilege inferred from a role name.
These operations still consume real endpoint slots and account allowance; an internal
finishing reserve cannot guarantee external provider availability. Bound admitted
roots and control invocations as well as their worker processes.

The broker needs stable resource identities:

| Identity | Meaning |
| --- | --- |
| Endpoint ID | A versioned model/protocol/session destination, with a configuration digest. |
| Capacity-pool ID | The real shared engine or concurrency pool. Two URLs pointing at the same engine consume one pool. |
| Account ID | The authenticated allowance owner; opaque to scheduling policy and containing no credentials. |
| Metered bucket and window ID | A specific provider limit and its generation/reset boundary. Several endpoints may charge the same bucket. |
| Run, root objective, process and operation IDs | Globally scoped identities. Existing local IDs such as `controller` must be qualified by their run. |

For the first deployment, map today's `local` and `cloud` aliases into a registry
with two entries. Require the shared pool's configuration to agree across clients;
reject conflicting claims about its capacity. More entries can be added without
changing the policy algorithm. Different models remain separate authorized choices,
even when they share hardware or an account.

A bypassing process can invalidate a global capacity guarantee. In managed mode,
all inference submissions must present a broker permit, including probes and
automatic retry paths. Existing standalone mode can retain its current local
admission, clearly outside the managed installation-wide guarantee. Provider use
from other applications remains external consumption to observe conservatively.

### 1.3 Expose process control; keep resource interfaces inside the OS

| Item | Status and source |
| --- | --- |
| Generic process registration and ordinary execution | **Implemented.** `ProcessPorts` exposes host-supplied continuation start, status, cancellation, terminal wait and finish. `Processes` implements them without requiring coding tools, Git, a workspace or acceptance checks. [Ports](../../../src/polyinference/ports.py) · [Processes](../../../src/polyinference/runtime/processes.py) |
| Scheduler `run` | **Not implemented.** `Processes.start` requires a caller-supplied factory, admits immediately or raises when resident capacity is full, and rejects a paused process. There is no scheduler eligibility command or same-process suspension readmission. [Processes](../../../src/polyinference/runtime/processes.py) |
| Scheduler `wait` and optional not-before time | **Not implemented.** `Processes.wait` observes a terminal or paused status. `ModelRetries.wait_until` delays retry attempts only. Neither withholds process eligibility. [Processes](../../../src/polyinference/runtime/processes.py) · [Retries](../../../src/polyinference/runtime/model_retries.py) |
| Scheduler `preempt` and pending/unsupported/confirmed receipt | **Not implemented.** `ProcessLifecycle.park_process` fences already-settled work. It rejects pending effects or permits and returns no scheduler decision receipt. [Lineage](../../../src/polyinference/runtime/lifecycle.py) |
| Decision identity, control revision, ownership and authority checks | **Partial.** Operator `request_resume` deduplicates request IDs and compares the process/control records before recording intent. `_execute_once` checks the effect owner's generation, scope, grants and deadline. There is no scheduler decision ID, expected revision or authenticated scheduler control port. [Processes](../../../src/polyinference/runtime/processes.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Scheduler observations and event recovery | **Partial.** `ExecutionProgress.progress` exposes a local snapshot with wait, settlement, usage, capacity, a content-hash cursor and `observed_at`. `Exclusive._wait` records ownership waits and the UI shows them beside held permits. `Records.events(after)` pages retained per-run journal records. There is no scheduler feed with readiness/eligibility, preemption capabilities and receipts, shared quota, or gap recovery. The journal carries full record values and is not a redacted scheduler interface. [Progress](../../../src/polyinference/runtime/progress.py) · [Exclusive resources](../../../src/polyinference/runtime/exclusive.py) · [OS view](../../../src/polyinference/ui_os.py) · [Storage](../../../src/polyinference/runtime/storage.py) |
| Separate OS dispatch, preparation, claims, settlement and recovery | **Partial.** `ProcessPolicy.dispatch`, `_dispatch_once` and `prepare_resume` enforce static authority, prepare payloads, reserve per-run capacity and budgets, submit, settle and reconcile. Shared quotas and process eligibility integration are missing. These calls are generic runtime services with no scheduler command wrapper. [Process policy](../../../src/polyinference/runtime/process_policy.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Resume preparation](../../../src/polyinference/runtime/resume.py) |
| Immutable process specs and rejection of unsupported required features | **Implemented.** `Processes.register` inserts the spec as an immutable record. `KernelRuntime.negotiate` rejects unsupported required feature IDs and versions. [Processes](../../../src/polyinference/runtime/processes.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Preference revision, `20P` mapping, time sensitivity and negotiated process-control feature | **Not implemented.** `AgentServices.process` supplies fixed priority 50 and `KernelRuntime.negotiate` has no scheduler process-control feature. [Agent services](../../../src/polyinference/agent/services.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |

The following are **conceptual contracts to add**, not currently callable SDK
methods. The scheduler's only mutating commands target one authenticated process
ID. A process is a registered program/continuation, not a model call, provider slot
or whole objective's unnamed set of children. The ports require no coding services,
Git, workspace or acceptance checks.

| Scheduler command | Meaning and OS response |
| --- | --- |
| Admit a process (`run`) | Make this individual process eligible to run or resume. The OS still validates authority, continuation and deadlines and independently allocates resources; eligible may remain resource-waiting. |
| Defer a process (`wait`) | Withhold this process's next admission, optionally until a not-before time. An active process needs a preemption request to leave the running set; wait does not silently cancel its effects. |
| Preempt a process | Request removal of this individual process from the running set to make room for others. The OS chooses a safe drain/checkpoint method and returns pending, unsupported, or a confirmed suspension receipt. Only that receipt establishes which resources were actually released. |

Commands carry process identity, a stable decision ID and expected control/owner
revision. They contain no endpoint/model choice, resource vector, token/slot amount,
quota commitment, physical operation dispatch or termination attestation. Re-admitting
a suspended process uses `run` on the same identity; the OS performs safe readmission.
Explicit cancellation, task replacement and program submission remain with their
existing authorized launcher/application/operator paths, outside scheduler powers.

Read-only ports expose process readiness/eligibility, OS resource-blocked reasons,
running/draining/suspended state, usage and quota observations, wait-for relations,
preemption capabilities/receipts, and cursor-based events with freshness and gap
recovery. The scheduler may use those facts to choose processes; it cannot modify
them. Raw prompts, private source and canonical memory are unnecessary.

The OS/executor's separate interfaces register programs, obtain application-ready
operations, validate permitted endpoints, prepare exact requests, claim capacity
and quota, commit physical dispatch, settle/reconcile and recover continuations.
**None of these resource interfaces is a scheduler command.** The OS distributes
resources among eligible processes using its own authorized policy. Providers
still perform token/GPU scheduling inside their serving engines.

User/launcher preference changes produce a new policy revision without mutating
immutable ProcessSpec or past operations. A launcher can map importance `P` to
existing relative priority `20P`, with an extension for time sensitivity. Scheduler
selection cannot raise those authorized values, change grants or set resource
ceilings. Negotiate the process-control extension when mandatory; unsupported
runtimes must reject it instead of silently promising this behavior.

### 1.4 Close the reservation and submission races

| Item | Status and source |
| --- | --- |
| Step 1: durable intent, exact preparation, original-account budgets, separate compaction | **Implemented per run.** `_execute_once` journals the intent. `_dispatch_once` selects the fallback variant before preparing and measuring the adapter body. `_reserve_budget` and `_reserve_spend` charge the original account before submission, inside the local admission permit. `ContextService._compact` submits its own effect and awaits it before the parent enters `Admission.reserve`. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Context](../../../src/polyinference/runtime/context.py) · [Lineage](../../../src/polyinference/runtime/lifecycle.py) |
| Step 2: one atomic shared resource and quota claim, with rollback | **Partial.** `Admission.reserve` takes the configured slot and token capacity together in one local gate. `_settle_budget` can settle a known unsubmitted error to zero and is idempotent. Capacity, run/process budgets and estimated spend use separate updates. There is no shared transaction across capacity, quotas and rate limits. [Admission](../../../src/polyinference/runtime/inference.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Step 3: expiring uncommitted broker claim with fenced commit | **Not implemented.** Admission has a bounded wait, and effect execution checks owner generation. `Admission.reserve` has no broker lease, expiry generation or fenced commit. [Admission](../../../src/polyinference/runtime/inference.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Step 4: persist dispatch state, retain unknown holds, reconcile a cross-journal commit gap | **Partial.** `_dispatch_once` persists `submitting` then `active` before sending. `_execute_once` replays saved receipts or joins the live dispatch. `KernelRuntime.open` turns interrupted submitting/active effects into uncertainty, and `Admission.restore` restores unsettled holds from the run journal. There is no external commit record to reconcile. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Admission](../../../src/polyinference/runtime/inference.py) |
| Step 5: retained terminal evidence and idempotent settlement | **Partial.** `_dispatch_once` persists results and usage per operation or physical retry ID. `_settle_budget`, `settle_recovered_model` and `reconcile_stopped` settle or recover local accounting under retained evidence. There is no second ledger, pending cross-ledger settlement link or general exactly-once provider billing guarantee. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Physical response attempts](../../../src/polyinference/runtime/retry.py) |
| Fresh admission for OS-managed retries, response repair, smaller-output attempts, fallback, native continuations and compaction | **Implemented within the run.** Those paths use `_execute_once` or `_dispatch_once`, which enters the endpoint gate for the selected request. Pure receipt replay returns before that path. The CLI readiness probe bypasses it, and there is no managed eligibility or protected-drain check. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Response repair](../../../src/polyinference/runtime/retry.py) · [Retries](../../../src/polyinference/runtime/model_retries.py) · [Fallback](../../../src/polyinference/runtime/model_fallback.py) · [Context](../../../src/polyinference/runtime/context.py) · [CLI](../../../src/polyinference/cli.py) |
| Bounded retries and short-lived admission and SQLite locks | **Implemented for the current paths.** `ModelRetries` checks retained counts and the original deadline. `Admission.reserve` releases its condition lock before yielding to dispatch, and `Records.compare_and_publish` uses a synchronous SQLite transaction. Resource permits and the per-state coordinator lock can remain held. Scheduler deferral and a shared broker lock protocol are missing. [Retries](../../../src/polyinference/runtime/model_retries.py) · [Admission](../../../src/polyinference/runtime/inference.py) · [Storage](../../../src/polyinference/runtime/storage.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |

One transaction in the shared broker should cover capacity and all quota windows.
There is no transaction spanning a run's SQLite journal, this broker and a remote
provider. Use a durable handshake rather than claiming cross-system atomicity:

1. The executor persists the operation intent and prepares the exact selected
   payload. It validates and reserves the existing run/process budget under the
   original account. Preparatory inference, such as optional compaction, is a
   separately OS-admitted child operation and completes before the parent claims
   a slot. It is not a new scheduler-selected model-call ticket.
2. For an eligible process, the OS executor asks its broker to claim the simultaneous
   shared resource vector and all relevant quota/rate commitments. A failed claim consumes no provider
   service and rolls back the broker transaction. The executor releases any unused
   run-budget reservation through an idempotent outcome.
3. A short, configurable lease may expire an **uncommitted** broker claim. An
   executor must atomically commit that claim with its current fencing generation
   before it may send. A stale or expired claim cannot be committed.
4. After commitment, persist the submitting state and send once under the claimed
   operation owner. A committed hold never expires merely because a lease, process
   or connection disappears. A crash between broker commit and the run's submitting
   record is also reconciled; a local `prepared` record alone cannot free that hold.
5. Store terminal evidence and usage under the physical-attempt ID. Settle both
   ledgers idempotently, retaining a pending settlement link if either side fails.
   A crash after send requires evidence, not another send. Provider idempotency
   may help where documented; no general exactly-once billing promise is possible.

This protocol permits conservative temporary holds, but never double allocation.
Resolve the effective primary/fallback model and effort before preparing and
claiming its request. An availability switch is not permission to reuse a reservation
whose applicable bucket, input size or resource requirements changed.
It must include transport retries, response-validation retries, smaller-output
attempts, availability fallbacks, native continuations, probes and compaction
children. Each actual provider submission gets a new physical admission decision
on its existing lineage. The OS checks process eligibility and protected-drain
authority; the scheduler does not choose or admit individual attempts. Pure
receipt replay gets none. Existing retry allowances remain finite; process deferral
neither spends nor renews them.

A parent must not reserve the last slot while awaiting a helper that needs it.
Likewise, no broker/database lock spans inference, a shell command, a permit wait
or a network status lookup. A one-process local server still has one slot after
lost delivery; logical abandonment cannot create another.

### 1.5 Normalize provider quota and performance facts

| Item | Status and source |
| --- | --- |
| Independent provider-account observations, metered buckets and window discovery | **Not implemented.** `CodexAppServer.generate_job` handles job RPC, callbacks and thread token notifications. It does not call `account/rateLimits/read`, consume account-limit updates, or publish account/bucket/window observations. `ExecutionProgress.progress` reports local budgets and gate counts. Provider units, applicability, freshness, coverage, reset semantics and the proposed known/estimated/stale/unavailable/unmetered states are missing. [Codex adapter](../../../src/polyinference/runtime/codex.py) · [Progress](../../../src/polyinference/runtime/progress.py) |
| Error categories and retry hints | **Partial.** `HTTPInference.rejected` records authentication, permission, rate limit and service/model availability categories, provider code and bounded `Retry-After` (seconds or HTTP date). `ModelRetries._run` uses the hint within its delay and original deadline. An HTTP 429 is a rate-limit category by default. There is no normalized distinction between request/token throttling and allowance exhaustion, organization/project/model window tracking or separate admission gates for RPM/TPM. [HTTP adapter](../../../src/polyinference/runtime/inference.py) · [Retries](../../../src/polyinference/runtime/model_retries.py) |
| Per-operation performance and progress facts | **Partial.** Admission persists queue and admit times. Kernel context receipts record submitted sizes and output bounds, and operation results retain start/finish times and backend identity when available. Raw SSE records elapsed time and last meaningful output. Buffered calls expose waiting and completion, and native jobs retain thread/turn and bounded events. There is no uniform performance observation with a dedicated first-output timestamp, concurrent load at dispatch and uncertainty. [Admission and HTTP adapter](../../../src/polyinference/runtime/inference.py) · [Context](../../../src/polyinference/runtime/context.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Codex adapter](../../../src/polyinference/runtime/codex.py) |
| Enforced sequence and configured context capacity, with GPU scheduling provider-owned | **Implemented.** `Admission.reserve` bounds active calls and configured aggregate token reservations. `_dispatch_once` invokes the selected adapter inside that reservation. Token iteration and GPU/KV allocation remain with the provider. [Admission](../../../src/polyinference/runtime/inference.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Completion estimates for allocation or scheduler observation | **Not implemented.** `ExecutionProgress.progress` exposes counts and current facts, with no endpoint completion prediction. The proposal in §1.8 remains research. [Progress](../../../src/polyinference/runtime/progress.py) |
| Usage scope and safe native-thread deltas | **Partial.** The native adapter labels `completion.usage_scope` as `native_thread_total`; result artifacts retain that label and usage. `_dispatch_once` and `settle_recovered_model` pass reported `total_tokens` into `_settle_budget`. There is no compatible-counter delta or account-window attribution. [Codex adapter](../../../src/polyinference/runtime/codex.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |

Add an OS/provider observation service independent of a running model call.
For each account/bucket/window expose unit, used/remaining or total where known,
reset/rolling-window semantics, next reset, observation revision/time, report-lag
and coverage information where supplied, applicability and source. Distinguish
`unmetered`, `known`, `estimated`, `stale` and `unavailable`; a missing quota field
does not mean unlimited capacity. RPM/TPM throttles and concurrency are separate
constraints from subscription allowances.

Official OpenAI documentation exposes `account/rateLimits/read`, update
notifications, multiple metered buckets and window usage/reset fields. Those
observations support an adapter; they do not establish an absolute token allowance
or identify which local receipts a snapshot already includes.
[Codex app-server documentation](https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt).

The current pricing guidance says usage depends on model, context, reasoning,
tools and other work. Five-hour limits apply to some plans; weekly limits may
also apply, and Pro currently has no five-hour limit. Therefore support the
research's five-hour/weekly *example* as two applicable windows, while discovering
the actual account's windows and units. “Local messages” in subscription guidance
still use hosted inference; they are different from unmetered local GPU serving.
[Official usage guidance](https://learn.chatgpt.com/docs/pricing#what-are-the-usage-limits-for-my-plan).

Normalize rate-limit denials and retry times without guessing that every HTTP 429
means weekly exhaustion. Separate temporary request/token throttling, allowance
exhaustion, provider overload and authentication failure. Existing raw API limits
also have organization/project/model scopes; honor their documented retry hints.
[OpenAI API rate-limit documentation](https://developers.openai.com/api/docs/guides/rate-limits).

Performance observations need input/output sizes, queue/admission/start/first-output/
terminal times, concurrent load, protocol/model identity and uncertainty. Do not
invent token progress for buffered or opaque native calls. The OS may estimate
completion time for its resource-distribution policy and expose labeled estimates
to the process scheduler; reading an estimate grants no placement authority. Configured
sequence/context reservations remain the enforceable V1 contract. Actual GPU/KV
allocation and token iteration scheduling stay in Strata or another serving backend.

Usage observations must also state their scope: one request, one turn or a cumulative
native thread. Repeated native continuations cannot charge the full thread total
as new consumption on every receipt. Derive a delta only from compatible, trustworthy
counter observations; retain unknown/estimated attribution otherwise. Thread token
deltas still do not establish percentage-window usage or its billing time.

### 1.6 Make preemption an explicit capability

| Proposed mode | Response to a process preemption request | Current status and source |
| --- | --- | --- |
| Settled-operation yield | The OS prevents the process's next ordinary operation and acknowledges suspension at a valid continuation boundary. This is the proposed V1 baseline on supported executors. | **Partial.** `park_process` fences settled work and calls `hibernate`, which rejects unsettled effects, permits and reservations. There is no scheduler request, pending yield at the next boundary or resumable checkpoint handshake. `Processes.start` rejects paused records. [Lineage](../../../src/polyinference/runtime/lifecycle.py) · [Processes](../../../src/polyinference/runtime/processes.py) |
| Drain to a checkpoint | The OS lets the current operation/protected sequence settle before suspending the process. Occupied resources remain held during drain. | **Partial.** The kernel rejects new ordinary effects for paused, parked or cancelled processes. Admission retains active or unknown reservations, and protected work requires owned permits. `park_process` rejects unsettled work rather than registering a pending drain. There is no preemption barrier that admits only protected work until a checkpoint. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Admission](../../../src/polyinference/runtime/inference.py) · [Lineage](../../../src/polyinference/runtime/lifecycle.py) |
| Provider checkpoint and resume | The OS may pause the same generation/job only through an advertised, tested adapter and a receipt identifying the checkpoint and released/retained resources. The scheduler cannot select that adapter operation. | **Not implemented.** Codex can resume a thread for a later turn. Its `turn/interrupt` path raises `UnknownExecution` without waiting for terminal proof. There is no provider checkpoint capability, pause receipt or live generation readmission. [Codex adapter](../../../src/polyinference/runtime/codex.py) · [Ports](../../../src/polyinference/ports.py) |
| Cancel and restart | Outside V1 scheduler authority. Existing explicitly authorized cancellation/recovery keeps its own semantics; preemption cannot silently become a charged restart. | **Implemented for existing cancellation and explicit recovery.** `Processes.cancel` records a cancellation request, `_execute_once` blocks new effects, and `bind_recovery` requires a new ready identity under inherited authority. There is no scheduler cancel/restart command. [Processes](../../../src/polyinference/runtime/processes.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Lineage](../../../src/polyinference/runtime/lifecycle.py) |

| Supporting item | Status and source |
| --- | --- |
| Pause receipt, resource vector and certainty | **Partial.** `park_process` records owner generation, time and local settlement facts. `hibernate` releases resident capacity only after checking effects, permits and physical reservations. Unknown outcomes continue to hold endpoint capacity. There is no provider/session checkpoint format, usage and release vector, compatible resume destination or scheduler acknowledgement. [Lineage](../../../src/polyinference/runtime/lifecycle.py) · [Processes](../../../src/polyinference/runtime/processes.py) · [Admission](../../../src/polyinference/runtime/inference.py) |
| Native callbacks keep the parent job's permit | **Implemented.** `_dispatch_once` awaits `generate_job` inside `Admission.reserve`; `_native_callback` invokes scoped subordinate tools through the kernel while the job is active. Callback waits do not release the parent slot. The interrupt terminal-drain gap remains. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Codex adapter](../../../src/polyinference/runtime/codex.py) |
| Cloud-agent warning-only timeout and original authority | **Implemented for current execution.** The default `cloud_agent_timeout_interrupt` is `false`. `_await_agent_job` warns and awaits the same task; the outer original deadline and authorized cancellation still apply. `request_resume` rejects cancelled processes and the kernel checks inherited deadlines before dispatch. Scheduler review timing is unimplemented. [OS defaults](../../../src/polyinference/os_config.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Processes](../../../src/polyinference/runtime/processes.py) |

The pause receipt must identify the operation/attempt, provider instance/session,
continuation format, consumed usage, resources released and retained, compatible
resume destination and certainty. Saving KV state while keeping all needed memory
reserved might release a decode opportunity, but not the context capacity another
request needs. The OS tests the full resource vector before dispatching any other
process's work. The scheduler cannot request a particular vector's release or
count predicted release as capacity. Lost acknowledgement means pending/unknown.

Native AgentJob calls are particularly important: the provider owns an internal
model/tool loop. A tool wait does not end the parent job, release its cloud slot or
expose a portable generation checkpoint. The documented Codex interrupt operation
is cancellation followed by a terminal turn status, not a promise of resumable
mid-generation execution. PolyInference's existing missing terminal-drain follow-up
must be resolved before claiming reliable interruption settlement.
[App-server lifecycle](https://learn.chatgpt.com/docs/app-server#lifecycle-overview),
`development-docs/FIXES.md#fix-0068`, `development-docs/FIXES.md#fix-0170`.

Preserve the current warning-only cloud-agent endpoint timeout option. A process
preemption review interval is neither an endpoint timeout nor a process deadline. Original
deadlines and explicit cancellation continue to apply even to suspended work.

### 1.7 Integrate launch, ownership and recovery

| Item | Status and source |
| --- | --- |
| Independent run state and program pins | **Implemented.** `TestUI.start` allocates a run ID and directory and records run metadata. `KernelRuntime.open` checks the runtime and configuration pins. `ProjectAgent` checks program identity on the application path. [UI](../../../src/polyinference/ui.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Coding controller](../../../src/polyinference/agent/controller.py) |
| Multi-objective managed submission and lifecycle display | **Partial.** `TestUI.runs` catalogs runs and `runtime_view` shows local process and wait state. `TestUI.start` rejects simultaneous work and the CLI starts one configured run per invocation. There is no managed queue, scheduler-deferred/suspending state or operator aggregate scheduler control. [UI](../../../src/polyinference/ui.py) · [OS view](../../../src/polyinference/ui_os.py) · [CLI](../../../src/polyinference/cli.py) |
| Individual process registration and scheduler eligibility for each child | **Partial.** `AgentServices.process` registers individual processes and the controller starts workers through `Processes.start`. The application supplies the ready work. The OS checks local residency and authority, with no separate scheduler decision for parents or children and no scheduler suspension state distinct from other pauses. [Agent services](../../../src/polyinference/agent/services.py) · [Coding controller](../../../src/polyinference/agent/controller.py) · [Processes](../../../src/polyinference/runtime/processes.py) |
| Guarded standalone provider ownership | **Implemented in the launcher.** `ensure_ui_local_provider` returns cleanup ownership only for an instance it started. `OwnedStrataRuntime.close` passes owner and, when known, instance guards. UI shutdown calls that cleanup. [Local provider launcher](../../../src/polyinference/agent/local_provider.py) · [UI](../../../src/polyinference/ui.py) |
| Managed provider lifetime, separate scheduler/broker fencing and restart | **Not implemented.** There is no shared owner that drains all broker users before shutdown, scheduler decision/age reconciliation or fenced broker leader. The current coordinator lock is per state directory, and the existing journal cursor is per run. [Local provider launcher](../../../src/polyinference/agent/local_provider.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Storage](../../../src/polyinference/runtime/storage.py) |
| Per-run coordinator ownership, restart and original accounts/deadlines | **Implemented.** `KernelRuntime` takes an exclusive coordinator lock, reconciles retained effects and restores unresolved reservations on open. `ProcessLifecycle.bind_recovery` retains grant, limits, account and cutoff; `Processes.start` bounds the replacement driver by that cutoff. Scheduler decision state and cross-run settlement are absent. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Admission](../../../src/polyinference/runtime/inference.py) · [Lineage](../../../src/polyinference/runtime/lifecycle.py) · [Processes](../../../src/polyinference/runtime/processes.py) |
| Repository exclusion, verification-before-shell and uncertain effects | **Implemented at current scope.** `RepositoryWorkspaces.acquire` uses OS filesystem leases for the selected checkout and common Git directory. `Exclusive.acquire` enforces verification-before-shell, and `_execute_once` blocks new work on unresolved strict effects in the run. The managed queue that would expose both submitted objectives while conflicting execution waits and shared physical accounting are missing. [Repository application](../../../src/polyinference/agent/repository.py) · [Exclusive resources](../../../src/polyinference/runtime/exclusive.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Version negotiation and original state pins | **Partial.** `KernelRuntime.negotiate` rejects unknown required features, and `open` checks config and kernel compatibility. Application Resume checks program/state pins. No scheduler/broker feature version, preference/root propagation, alternative-route declaration or scheduler checkpoint cooperation is wired. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Application Resume](../../../src/polyinference/agent/resume.py) · [Agent services](../../../src/polyinference/agent/services.py) |

The UI/CLI should submit several independent objectives, each with its own state
and program pins, and show queued/running/deferred/suspending/suspended/blocked/
finished status plus a plain reason. Launchers/applications submit programs and
register their individual processes; the scheduler does not create objectives or
tasks. A scheduler-requested process suspension is distinct from an agent exception
or user pause. Each child needs its own process eligibility decision; admitting a
parent grants no automatic admission to all children. The OS blocks new ordinary
work for a preempted process and drains its existing protected work. An operator's
run-level suspend may aggregate individual controls, but is not an extra scheduler
command. One native process can remain draining for a long time.

In managed mode the shared broker launcher, rather than a particular UI client,
owns any provider instance it starts. Tie that instance to the broker's lifetime,
retain captured owner/instance guards and drain active users before shutdown.
Never adopt a reused engine or stop another run's replacement instance. Today's
UI-owned cleanup remains valid in standalone mode; see
the launch guide (`docs/guides/launching.md`) and `development-docs/FIXES.md#fix-0174`.

Keep independent runtime/executor leases and separate fenced ownership for the
process-control leader and OS resource broker. Scheduler restart restores process
decisions/ages and reconciles acknowledgements. OS restart reconstructs physical
attempts, committed holds, accounts and pending settlements before allocating.
A cursor gap triggers snapshot recovery. Neither restart resets original budgets,
deadlines, process age or unknown holds. Scheduler availability/loss is not proof
that a process or provider execution stopped.

For coding applications, preserve the shared repository lease and verification-
before-shell order. Initially serialize independent objectives targeting the same
integration checkout; they can both be submitted and visible, while their conflicting
execution waits. Do not solve this by moving Git policy into the scheduler. Unknown
native/tool effects retain the existing barrier within their runtime and all shared
conflict/physical holds; unrelated run execution requires nonconflicting authority.

Implementation would affect public contracts/ports, settings, kernel dispatch,
admission/process policy/lifecycle, provider adapters, progress/inspection and
launch management. The existing coding agent needs only preference/root propagation,
eligible-route declarations and checkpoint cooperation. Its decomposition, memory,
Git, local contracts, cloud-only work and acceptance stay application-owned.
Introduce negotiated scheduling/broker versions and fresh run/state pins; preserve
historical runs on their original implementation.

### 1.8 OS-owned allocation research retained from the earlier draft

The following placement estimates, delay tolerances, quota accounting modes and
pacing formulas are retained research for the **OS resource allocator**. They are
not scheduler controls, not prerequisites for process-only admission/preemption,
and not implemented defaults. The initial OS broker may keep today's fixed routes
and resource rules. Any later allocator must receive explicit application-authorized
alternatives and preserve hard constraints. User P/T values are read-only authorized
inputs; a scheduler cannot change them to obtain a resource allocation or quota
privilege. No scheduler command selects an endpoint, window, reservation amount
or pacing exemption. The OS applies every allocation and quota decision itself.

The earlier research's [Kubernetes filter/score/reserve comparison](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
is background for OS allocation, not a V1 scheduler capability set. Likewise,
[vLLM preemption architecture](https://docs.vllm.ai/en/latest/design/arch_overview/#preemption)
and the [ORCA paper/abstract](https://www.usenix.org/conference/osdi22/presentation/yu)
concern backend execution granularity. Those references do not establish a portable
process checkpoint or permit the standalone scheduler to control a serving engine.

#### OS endpoint placement research

| Item | Status and source |
| --- | --- |
| Static eligibility, exact request size, configured capacity and run/process budgets | **Implemented.** `ProcessPolicy` checks the pinned binding against data/location and hard distribution rules. `_dispatch_once` measures and reserves the selected request. `_reserve_spend` checks estimated spend when the endpoint supplies a rate. Configuring a run or process spend ceiling requires a rate for physically cloud-hosted bindings. [Process policy](../../../src/polyinference/runtime/process_policy.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Settings](../../../src/polyinference/system_settings.py) |
| Authorized fallback and session affinity | **Implemented for configured model fallback.** `ModelFallback.select` uses the original binding and a retained model/effort selection. `recover` carries a compatible native session into a new authorized attempt when available. This path has no general endpoint candidate set or binding-generation change. [Fallback](../../../src/polyinference/runtime/model_fallback.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Completion-delay estimator, historical quantiles, load/size grouping and confidence | **Not implemented.** Admission and adapter observations provide timing and size inputs, but dispatch never scores endpoint candidates, predicts queue/prefill/execution/session delay, or stores confidence and prediction error. [Kernel](../../../src/polyinference/runtime/kernel.py) · [HTTP adapter](../../../src/polyinference/runtime/inference.py) |
| Dynamic choice between unmetered and metered destinations, P/T tolerances and revisable wait | **Not implemented.** Dispatch uses the static binding and its configured fallback. The endpoint's local FIFO contains pending reservations. There is no completion-delay comparison, P/T tolerance, OS candidate wait set, reevaluation or placement hysteresis. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Fallback](../../../src/polyinference/runtime/model_fallback.py) · [Admission](../../../src/polyinference/runtime/inference.py) |
| Mid-generation migration and authorized cross-endpoint movement between requests | **Not implemented.** The kernel records static binding generation for model results. There is no generation check for dynamically changing a binding, migration or session reconstruction across endpoints. [Contracts](../../../src/polyinference/contracts.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) · [Codex adapter](../../../src/polyinference/runtime/codex.py) |

For every permitted endpoint, estimate:

**Completion delay = capacity wait + request preparation/prefill + remaining
execution + resume/session overhead.**

For raw inference, use input size, expected output length and measured rates at
the prospective concurrent load. Include cold startup where applicable. Avoid
counting prefill twice if the observed first-output measurement already includes
it. For native jobs, use wall-time observations for comparable jobs, including
tool waits and internal turns. Dividing one final visible reply by decode TPS is
not a useful estimate for a native agent job.

Begin with conservative historical duration/output quantiles grouped by endpoint,
operation kind and rough size. Record confidence and prediction error; fall back
to configured estimates when samples are missing. Do not multiply solo TPS by
batch size. A backend's sequence limit, batch token budget, OS inflight cap and
remote request concurrency are different quantities. Keep pending operations in
the OS resource wait set; endpoint queues contain only committed dispatches. This
queue is separate from the scheduler's process eligibility set.

The placement estimate has a precedent in token-load and cache-aware routing;
[Ray Serve's routing documentation](https://docs.ray.io/en/latest/serve/llm/architecture/routing-policies.html)
describes both load balancing and routing using prefill/decode load. An optional later OS allocator needs
only the measured load estimate; cache-aware routing can wait for trustworthy
backend telemetry.

Among endpoints that pass all hard constraints, compare the best unmetered
endpoint with the best quota-limited endpoint using this editable delay tolerance:

| Time sensitivity T | Extra completion delay accepted to conserve subscription allowance |
| --- | --- |
| 0 | 120 seconds |
| 1 | 60 seconds |
| 2 | 30 seconds |
| 3 | 10 seconds |
| 4 | 3 seconds |
| 5 | 0 seconds |

If unmetered completion is within that tolerance, choose it. Otherwise choose
the fastest quota-admissible endpoint. If only one category is permitted, choose
within it. At T=5 a tie can use unmetered service. Importance influences ordering
and quota access; T controls this latency tradeoff. Original model, tool, data,
context, cloud-only and session constraints always filter candidates first.

Here unmetered means no provider allowance, not zero monetary or energy cost.
Campaign spend bounds still filter every candidate; paid API service cannot acquire
an unlimited spending entitlement by lacking a subscription window. The motivating
unmetered option is an explicitly configured local server with no per-token fee.

A short wait for a busy fast endpoint can beat immediate service on a slow one.
Keep that choice as a revisable plan with a wakeup, not a long endpoint queue or
an early quota/slot reservation. Reconsider when capacity or estimates change.
Prefer the current compatible session on close estimates and apply a configurable
placement hysteresis to avoid repeated moves. Mid-generation migration is excluded;
moving between requests still requires authorized context/session reconstruction
and a new binding-generation receipt. A hard static binding stays pinned unless
the application explicitly declares alternatives under the new contract.

#### OS subscription accounting research

| Item | Status and source |
| --- | --- |
| Local run/process token and spend ledgers, reservations and settlement | **Implemented.** `_reserve_budget`, `_reserve_spend` and `_settle_budget` apply aggregate local accounting to the original process account. `Admission.restore` retains unknown physical work. These ledgers apply even without provider subscription telemetry. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Admission](../../../src/polyinference/runtime/inference.py) |
| Shared account/bucket/window ledger and every-window admission | **Not implemented.** The kernel keys accounting by run/process and per-binding reservations. There are no authenticated provider allowance owners, cross-run commitments, rate gates or metered/unmetered admission modes. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Progress](../../../src/polyinference/runtime/progress.py) |
| Absolute-unit and opaque/estimated allowance modes | **Not implemented.** The native adapter reports thread usage, and the kernel can settle reported tokens or keep the local reservation when usage is unknown. No window-bound reservation, coverage watermark, per-window estimate/margin/confidence, one-job-per-account guard or post-settlement account refresh exists. [Codex adapter](../../../src/polyinference/runtime/codex.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Cloud per-call token behavior | **Implemented.** `RuntimeConfig.token_limits_for_binding` returns no per-call pair on the cloud binding or for physically cloud-hosted native jobs. `_dispatch_once` derives its output allowance from that pair. The local binding can still enforce its token pair on a remote raw simulation endpoint. There is no strict quota eligibility mode to exclude providers without enforceable allowance bounds. [Settings](../../../src/polyinference/system_settings.py) · [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Observation coverage, external usage, resets, rolling windows and unavailable data | **Not implemented.** There is no account observation to reconcile against receipts, track staleness or reset generations, or gate on unavailable telemetry. Local reservation restoration depends on retained execution evidence and keeps unknown physical holds independent of any account-window reset. [Codex adapter](../../../src/polyinference/runtime/codex.py) · [Admission](../../../src/polyinference/runtime/inference.py) |

Maintain one broker ledger per account/bucket/window, shared across every endpoint,
run, model fallback and process that consumes it. Each dispatch must pass **every**
applicable window and any separate request/token rate gate. Five-hour headroom
cannot compensate for an exhausted week. Unmetered local inference skips provider
quota gates while still obeying context, capacity, process and campaign budgets.

For each window keep:

- Provider observations, their units, freshness, window generation and reset semantics.
- Locally committed usage not yet covered by an authoritative observation.
- Reservations for active or resumable work, including unknown physical attempts.
- A configurable safety margin and any reporting-lag or estimate uncertainty.

Support two accounting modes:

| Mode | Admission and reconciliation |
| --- | --- |
| Absolute units with enforceable bounds/coverage | Reserve a conservative per-request bound in that window's units. Replace local debits with provider-covered usage only when a watermark, receipt identity or documented equivalent establishes coverage. Settle actual usage once. |
| Opaque percentage or estimated allowance | Estimate consumption separately for each window, with margins and confidence. Start with one active job per account and refresh observations after settlement and on updates. This is conservative risk control, not an exact token budget or a provable provider cap. |

There is no universal conversion from input/output tokens to Codex percentage.
Native jobs may perform several generations and have no OS per-call token cap.
A completion-time estimate is not an enforceable usage bound. Do not reduce the
existing cloud token behavior merely to make quota estimates look exact. If a user
requires a strict quota guarantee, exclude a destination that cannot supply an
enforceable bound; estimated mode must be an explicit deployment choice.

Snapshot overlap is a real limitation of the original research's no-double-counting
goal. With an aggregate percentage and no coverage watermark, the OS cannot
know whether a new provider snapshot already includes a local request or an external
application's usage. In that case retain unresolved local commitments conservatively,
even if this temporarily counts some usage twice. Do not erase them merely because
the percentage rose, a job ended or a timer elapsed. Consolidate only with coverage
evidence or a confirmed window transition that settles the relevant ambiguity.
This can underuse an opaque allowance; it must be visible as accounting uncertainty.

At a reset, refresh the provider's state and create a new window generation. Do not
free a still-running job's physical hold or erase charges attributable to the new
window. Cross-reset/unknown jobs require adapter attribution or conservative new-
window commitments. Out-of-order observations cannot roll usage backward within
one window. A genuinely rolling window needs its provider's release schedule,
rather than a fabricated fixed reset. Unavailable telemetry blocks new metered
work by default; it does not silently authorize unlimited use.

#### OS quota enforcement and pacing research

| Item | Status and source |
| --- | --- |
| Hard `U + c <= Q` per provider window and all-window gating | **Not implemented.** `_reserve_budget` and `_reserve_spend` enforce local totals. They have no provider window, percentage reconciliation or hard gate in provider units. [Kernel](../../../src/polyinference/runtime/kernel.py) |
| Ordinary spending ceiling and authorized P/T bypass, including elapsed-window and remainder pacing | **Not implemented.** The local token reserve depends on trusted `management` registration. The kernel has no pacing formula, P/T quota privileges, window fraction, protected provider allowance or allowance wakeup. [Kernel](../../../src/polyinference/runtime/kernel.py) · [Processes](../../../src/polyinference/runtime/processes.py) |
| RPM/TPM gate, provider retry hints, typed denial and deferred wakeup | **Partial.** Admission records capacity waits and expires them at the operation deadline. The HTTP adapter records bounded `Retry-After`, and `ModelRetries._run` can sleep until the authorized retry time. There is no token bucket or rolling rate counter, quota/pacing-specific denial or wakeup that leaves the original operation deferred without a failed attempt. [Admission and HTTP adapter](../../../src/polyinference/runtime/inference.py) · [Retries](../../../src/polyinference/runtime/model_retries.py) |

Use the research's two-gate policy as the initial configurable default. For a
confirmed resettable window, define:

- `Q`: the window's total allowance after its safety margin, in its own units.
- `U`: conservatively accounted usage and outstanding commitments in those units.
- `c`: the additional request commitment for that same window.
- `f`: fraction of the confirmed window elapsed, clamped to 0–1.

**Hard gate, every request: U + c must be at most Q.**

In opaque/estimated mode this is a hard rule for local admission against estimates;
it is not proof that the provider's actual opaque usage cannot exceed the estimate.

**Ordinary spending ceiling: N = 0.8 × Q × (0.1 + 0.9 × f).**

Ordinary work requires `U+c <= N` as well. A root with **P >= 4 or T >= 4** may
bypass this soft ceiling and use the remaining protected allowance. It cannot
bypass the hard gate. Aging and inherited priority do not grant this privilege;
use the root's authorized P/T values. Every request, including privileged work,
contributes to U. Urgent consumption can therefore delay ordinary work until its
ceiling catches up. A stream of urgent work can exhaust the hard allowance; the
reserve is a preference, not a guarantee of future urgent service.

The formula gives ordinary work 8% of Q immediately, rising to 80% by the end;
it protects 20% for privileged arrivals. It may leave allowance unused. The constants
are hypotheses to evaluate, not values justified by the literature or existing
PolyInference measurements. Apply the formula independently to five-hour and weekly
windows. Do not infer f from a countdown unless the adapter establishes the window's
start/reset semantics. If only remaining allowance and reset time are known, anchor
an equivalent paced allowance to that observed remainder and time-to-reset; record
that policy separately rather than inventing an original full-window budget.

For example, Q=500,000 weekly units and f=0.5 gives N=220,000. With U=250,000, an
ordinary request cannot use that week even if the short window is mostly empty.
An important request costing 10,000 can use it if it also fits the short window and
all other gates. If the weekly hard headroom is only 5,000, it must wait or use an
authorized unmetered endpoint. All numbers in this example are hypothetical.

Temporary RPM/TPM admission can use a provider-compatible token bucket or rolling
counter independently of this slow-window pacing. Respect Retry-After and original
deadlines; wake at the earliest relevant gate change. A denial should report quota,
pacing, throttle, unknown usage, capacity or incompatibility distinctly. Keeping the OS resource wait deferred avoids manufacturing repeated failed model attempts while waiting.
