# Proposed scheduler process policy

## Part 2 — Standalone scheduler design

### 2.1 User contract and authority boundary

The scheduler answers only this question for each **individual OS process**:
may it run, must it wait, or should the OS preempt it from the running set?
Process admission and preemption are its entire mutating authority in V1.
Read-only observation supports those decisions; it does not add resource powers.

| Input | V1 process-policy use |
| --- | --- |
| Importance P, integer 0–5 | Order process admission and choose lower-ranked processes for preemption. It does not grant scarce resources or quota exemptions. |
| Time sensitivity T, integer 0–5 | Prefer earlier process service. It does not select a faster endpoint, model, effort or harness. |
| Original deadlines/expiry | Observe the OS-issued cutoff. A desired completion target may inform ranking but cannot extend that cutoff. |
| Root objective/parent identity | Group related processes for fair admission without confusing objective identity with recovery budget lineage. Each decision still names one process. |
| Read-only OS facts | Ready/running/resource-waiting/draining/suspended status, blockers, service observations, supported preemption and actual acknowledgements. |
| Fidelity | Future scheduler preference only; existing application/OS hard constraints remain binding. The scheduler cannot change execution distribution or model quality. |

The launcher/user owns preference values, program submission, grants, limits and
configured resource ceilings. Suggested P/T defaults remain 2/2, with strict
integer validation in 0–5. Child preferences inherit or narrow the authorized
root values. The scheduler neither creates children nor raises their authority.
A configured concurrency ceiling is enforced by the OS; admission cannot assign
a process a worker count, inference slot, token share or exclusive resource.

Package the scheduler separately with input/event coordination, process ranking,
process eligibility/preemption decisions and durable decision explanations. A pure
policy function consumes an OS process snapshot and proposes only run, wait or
preempt for a process ID. The service submits those controls through a typed public
port. It imports no concrete broker/storage/kernel, provider client, coding
controller or Git provider.

### 2.2 Select processes, not their operations

Agents/applications decide task meaning, dependencies, actual ready work and
acceptance. Launchers and the OS register processes and expose their readiness.
The scheduler considers those existing processes; it does not publish ready model
calls, prepare prompts, select a physical retry or submit a provider operation.

Once a process is admitted, the OS runs its continuation and distributes resources
for its requested operations. A process may be eligible but waiting for an OS
resource. That is distinct from being withheld by the scheduler. Admission does
not promise immediate execution, a particular endpoint or exclusive capacity.

Admitting a controller does not admit every child it might later create. Each
registered child receives its own eligibility decision. Ordinary children, recovery
processes and other programs retain the same process-control boundary; the OS
separately bounds trusted control services needed for settlement and protected
progress. A role name is not an exemption.

An objective with 100 ready child processes must not obtain 100 precedence slots
merely by fan-out. Group them under the original objective for admission fairness,
choose a root, then its oldest eligible individual process. This grouping changes
process ordering only. It does not partition endpoint pools, reserve one slot per
root or combine siblings' existing budget accounts. The OS remains responsible
for actual concurrent resource distribution.

### 2.3 Order process admission by importance, time sensitivity and aging

Retain the illustrative starting ranking:

**Score = 2P + T + floor(eligible process-wait seconds / 30).**

Higher scores are considered first; break ties by retained ready-entry sequence
and process ID. Do not cap the aging term at 15. A (0,0) process reaches a fresh
(5,5) process's base score after 450 eligible waiting seconds. This is a ranking
comparison, not a guaranteed service time or resource entitlement.

Eligible wait is time application-ready work is withheld by process policy.
Exclude dependency/user waits and OS-reported infeasibility such as exhausted
quota; retain previously earned credit while blocked. Track process service and
preemption from OS acknowledgements. No new age bonus is earned by renaming a
replacement or restarting the scheduler.

The OS independently retains ordinary/finishing operation lanes, resource fairness
and permit-holder progress. The scheduler may prefer an individual holder process
when the OS reports that its progress is needed, but cannot reorder operation
tickets, release locks, assign reserved resources or increase quota privilege.
OS safety may delay preemption until a protected phase settles.

### 2.4 Use OS resource observations without allocating resources

The OS reports why an admitted process is resource-waiting, and may expose a
labeled feasibility/release estimate. The scheduler can keep or defer that process
and admit another existing process whose work can progress. It cannot resolve a
resource block by selecting an endpoint, increasing a limit, reserving quota or
ordering another process's provider requests.

For example, a strict-cloud process blocked by its weekly allowance can wait while
a local-only process is admitted. If one process has application-authorized local
and cloud alternatives, the OS alone chooses whether and where it executes. The
scheduler's command is still run or wait for that process, without destination
arguments. The placement and quota research in Part 1 belongs to the OS.

Quota observations may inform which processes the scheduler considers useful to
admit. They are read-only. Hard quota enforcement, accounting, margins, rate gates,
window resets and any optional resource pacing remain OS-owned even when a
scheduler decision was based on those facts. Scheduler failure cannot bypass a
gate; scheduler priority cannot waive it.

### 2.5 Preempt an individual process through the OS

A preemption request asks the OS to remove one process from the running set so
others may receive service. It does not specify a resource vector, token checkpoint,
provider cancellation or replacement endpoint. The OS chooses the safe mechanism
and reports pending, unsupported or acknowledged suspension.

The illustrative earlier policy values may still guide **when to request process
preemption**: a 10-second review interval, 2-second minimum observed service and
two-point score gap. They are policy hypotheses, not endpoint timeouts or enforced
generation slices. A long native job may offer no safe short boundary.

Choose a lower-ranked process only when read-only OS facts indicate that pausing
it could help another admitted/ready process and protected-progress rules permit
the request. The OS independently checks actual feasibility and effects. Await
acknowledgement; do not mark the victim suspended, infer capacity release or issue
provider control calls. Record actual released/retained resources as observations.
Admission of the next process still requires OS resource enforcement.

Cap repeated preemption requests, deduplicate stable decision IDs and preserve
unconsumed wait credit. A nearly finished process can be left running. If the OS
reports no safe pause, allow it to drain and reconsider later. Re-admit a suspended
process with run on the same identity; the OS validates/readmits its continuation
under original authority, accounts and deadline.

Cancel-and-restart, semantic recovery and new task creation are outside scheduler
authority. Provider-side recomputation or KV preemption does not automatically
provide a safe host process pause/resume contract. Native callbacks do not release
the parent job's slot. Unknown execution retains all applicable OS holds.

### 2.6 Events, persistence and explanations

Run a policy pass on process registration/readiness, OS service/blocker changes,
preemption acknowledgement, authorized preference edits or expiry. A short timer,
initially one second, may refresh aging and recover missed notifications. Wait on
events/timers instead of busy-polling.

Each pass:

1. Read a revisioned process snapshot and reconcile previously issued decisions.
   A cursor gap requires a new snapshot; old acknowledgements cannot settle a newer
   process-control generation.
2. Filter on application readiness and original authority/deadlines. Observe OS
   infeasibility; do not rewrite it or claim resources to test a placement.
3. Rank individual processes with the chosen objective fairness and age policy.
4. Issue only process run, wait/not-before or preempt decisions with stable IDs and
   expected revisions. Never send a model-operation, resource-claim or endpoint
   selection command.
5. Reconcile OS acknowledgements and return to waiting. Actual dispatch, resource
   distribution, physical retries, settlement and provider lifecycle remain in the OS.

Persist policy version, authorized preference references, process/group identity,
ready age, decision sequence, not-before times, preemption history and OS receipt
references. OS process/resource records remain authoritative. Restarting the
scheduler must not register a second program, renew deadlines or erase committed
physical holds. It can rebuild process decisions without resubmitting provider work.

Explanations distinguish scheduler-withheld from OS-resource-waiting, draining and
acknowledged suspension. Examples: “waiting behind a more urgent process,” “allowed
to run; the OS is waiting for its cloud quota,” and “preemption requested; finishing
a protected operation.” Resource release and completion estimates stay labeled.
Only the application can declare objective acceptance.

### 2.7 Walkthroughs

**Ordinary admission.** Processes A and B are ready. The scheduler admits A and
defers B. The OS decides which authorized resources A receives. If A is blocked
by the OS's quota/capacity rules, the scheduler may admit B too or change their
eligibility; it cannot transfer a slot or quota from A to B itself.

**Urgent arrival.** A low-ranked process is running when an urgent process arrives.
The scheduler requests preemption of the low-ranked process and admits the urgent
one. The OS drains or checkpoints safely, retains unknown/active commitments, and
allocates resources to eligible work when possible. A request alone does not make
a one-slot engine have a free slot.

**Local versus cloud.** A process permits both destinations. The scheduler admits
the process; the OS applies its authorized resource policy to select local, cloud
or a resource wait. The scheduler cannot request cloud to meet T=5. A strict route
remains strict even if its process has the highest score.

**Many children.** An objective's 20 children and another objective's single child
are registered processes. Objective grouping prevents fan-out from buying priority,
but every run/wait/preempt decision names one child. The OS enforces original
budgets, configured concurrency and shared resource limits across all of them.

**Native tool wait.** The scheduler preempts a native process while it awaits a
brokered tool. The OS lets required callbacks and protected work settle. It does
not release the parent reservation or report the process suspended until evidence
supports that transition.

### 2.8 Build and validate in bounded stages

| Stage | Owner and deliverable | Exit evidence |
| --- | --- | --- |
| A: process-control and OS support | OS: versioned run/wait/preempt controls, observations, shared resource broker and physical settlement on fixed routes. A fixture dispatcher can exercise it without a scheduler implementation. | Scheduler resource/endpoint/dispatch commands are absent or rejected; two runtimes cannot over-admit one pool; artifact-only processes work. |
| B: process policy | Standalone scheduler: individual-process ranking, objective fairness, durable waiting/preemption decisions and explanations. | Deterministic replay issues only the three process decisions; no resource ledger writes, new provider intents or task creation. |
| C: launch/application integration | Launcher/app/OS: register independent processes, propagate authorized preferences, show policy wait versus OS resource wait, preserve protected progress and managed provider ownership. | Child admission is explicit; UI exit cannot kill shared work; same-checkout objectives serialize; acceptance remains agent-owned. |
| D: optional OS allocation/preemption extensions | OS/adapters: explicitly authorized dynamic resource allocation or verified provider checkpoint support. | The scheduler interface remains process-only; adapter receipts prove actual release, compatible continuation and preserved effects. Unsupported endpoints retain cooperative drain. |
| Future: fidelity | Separately design any new preference and compliance behavior. | No model/effort/harness/distribution change can be commanded by the V1 scheduler. |

Before live qualification, deterministic traces should compare process policy with
a FIFO process baseline under the same **OS resource policy**, arrivals, authority
and budgets. Do not attribute a changed OS allocator to better scheduler policy.

| Scenario | Required observation |
| --- | --- |
| Two runtimes or aliases share one engine/account | The OS counts physical capacity and applicable quotas once; scheduler admission cannot multiply supply. |
| Many children under one objective | Fairness operates on process decisions without assigning resource partitions or renewing accounts. |
| Process admitted without a free endpoint | State remains eligible/resource-waiting; no false running or dispatch acknowledgement. |
| Weekly quota exhausted; local-only process ready | OS enforces the block; the scheduler can admit the local-only process without routing the blocked process elsewhere. |
| Preempt during native callback, shell mutation or publication | OS drains protected work and retains physical/conflict ownership until safe suspension. |
| Checkpoint releases a slot but retains context memory | Only the OS decides whether another eligible process's full resource vector fits. |
| Process deferral/re-admission across reset or restart | Original grants, accounts, cutoff and unknown holds survive; scheduler creates no replacement attempt. |
| Retry, fallback, compaction or direct managed probe | Every physical submission receives OS resource admission and follows its process eligibility/protected-drain authority. |
| Scheduler tries endpoint/resource/settlement commands | No such command is in its capability set; forged controls reject before effects. |
| Two objectives share a checkout; one UI exits | Existing project leases serialize execution; shared provider ownership survives the client exit. |
| Non-coding artifact-only process | Completes without Git, edits, TaskReport or coding acceptance. |

Measure process admission/preemption wait, actual OS service and blocked durations,
deadline misses and objective fairness separately from OS endpoint utilization,
quota accuracy or provider throughput. Independently measure accepted coding
outcomes. Fixture replay cannot establish live checkpoint support or broad product
convergence.

### 2.9 Research and verification limits

This is a revised source-backed proposal, not runtime behavior or an implemented
scheduler. The earlier operation-placement, quota/pacing and resource-claim powers
are superseded by the 9 November process-only rule. Retained allocation formulas in
Part 1 are optional OS research. Score, aging and preemption-request values are
unvalidated policy hypotheses.

The 8 November research consulted the official OpenAI, Kubernetes, Ray and vLLM
references retained in the OS discussion, plus the ORCA published abstract. Direct
USENIX page/PDF fetches returned 403; no full-paper/performance review was claimed.
Those historical citations do not expand V1 scheduler authority. No account-specific
quota lookup, provider checkpoint probe, model inference or historical Resume was
performed for this correction. Earlier checks remain in FIX-0180/0182; today's
documentation verification is recorded separately in FIX-0183.
