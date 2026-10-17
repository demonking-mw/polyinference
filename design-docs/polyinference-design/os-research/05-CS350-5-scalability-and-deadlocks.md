# Polyinference OS design — 5. Scaling the two-tier pipeline and preventing deadlocks

## Current agent concurrency contract

Updated using the full agent HTML and the user's later clarifications. The HTML is the agent design, including OS-handled parts; the LLM OS is an application operating endpoints, not a computer-kernel subsystem. [Concurrent coding protocol](concurrent_coding_protocol.md) defines the current operational contract. It supersedes any earlier screenshot-based alternatives below where their scope differs.

Every in-progress coding process owns a codebase copy. Private development overlaps. Every shell/script command, including test/Git commands, acquires a global `shell_mutex`. A separate `verification_gate` serializes latest-head merge, at least one specially prompted development/reconciliation loop, the final one/few local-model testing/examination/assessment iterations, commit and provisional shared-head/report publication. Release verification only after that boundary; release shell after each confirmed command. When both are needed the order is **verification then shell**; an outside shell owner releases before requesting verification. The application coordinator keeps running throughout.

Assessment produces `fail / uncertain / successful`; every normal local completion remains `unresolved` until sprint-coordinator review. Publish completed commits provisionally with verdict/hazards so the next entrant receives them; this is not senior acceptance. Preserve one attributable net-change commit for senior revert and blast-radius analysis. Steering stops new local starts, waits only for the captured in-progress locals (including gate waiters) to finish, then goes to the planner.

| Current extension | Required behavior |
| --- | --- |
| L5-C01 | Each active coding attempt owns its copy, base revision and scoped tool context; no shared editing before publication. |
| L5-C02 | Shell and verification ownership are distinct, obey one acquisition order, and are not computer-OS locks. |
| L5-C03 | Each verifier merges the latest published head, runs reconciliation development and final assessment, and publishes its commit/report before releasing. |
| L5-C04 | Publication stays provisional/unresolved; unknown active effects retain applicable exclusion and senior rollback checks dependents. |


**Lecture basis:** CS350-5.pdf, Synchronization, 51 PDF pages / 44 numbered slides. Uses lectures 1–5 cumulatively with [kernel boundary](01-CS350-1-foundations.md), [process/handoff contracts](02-CS350-2-processes.md), [LangGraph execution](03-CS350-3-threads.md) and [synchronization protocols](04-CS350-4-concurrency.md). **Project references:** F26 Planning.pdf and the supplied agent-v1 screenshot. **Revision/research date:** 2026-10-16.

## 1. Selected scaling direction

Preserve the supplied application: cloud strategy/review → validated Task Queue → local coding workers → tools/verification → private candidate/TaskReport → controller/cloud review → project acceptance. Scale the number of coding-worker processes independently of local inference slots, host threads and tool-server instances.

Keep one coordinator and the chosen local model resident initially. Add concurrent work only when the residual-memory envelope and useful-completion measurements support it. A smaller kernel and fewer live tool servers are direct project goals, not secondary optimizations after adding a full agent platform.

## 2. Slide-to-design derivation, in order

PDF references distinguish ordering and MCS progressive reveals.

| PDF pages / numbered slides | Lecture concept | Polyinference consequence |
| --- | --- | --- |
| 1–2 / 1–2 | Synchronization outline | Evaluate contention and progress in the real mixed-tier pipeline. |
| 3 / 3 | Amdahl's law and commutativity | Cloud strategy, dependencies and integration bound useful speedup; independent reports/reads should avoid global serialization. |
| 4–5 / 4–5 | Lock discipline and granularity | Partition per-project/process/tool state only where a measured shared bottleneck justifies it. |
| 6–10 / 6–8 | Ordering and kernel spinlocks | Use supported primitives; host interrupt control is outside this user-space kernel's scope. |
| 11–16 / 9–14 | C11 atomics, publication and spinlocks | Native helpers need portable ordering; graph/model/tool waits should suspend. |
| 17–24 / 15–22 | Cache coherence, MSI, shared lines and false sharing | Reduce hot shared updates; version project context explicitly rather than inventing LLM cache coherence. |
| 25–31 / 23–29 | Test-and-set contention and test-test-and-set | Avoid repeated shared writes, retry storms and waking every worker for one slot. |
| 32–40 / 30–33 | MCS queues and handoff/release races | Use explicit waiter ownership and targeted admission with cancellation-safe queue removal. |
| 41–46 / 34–39 | Deadlock conditions, ordering and resource graphs | Prevent worker, memory, tool and tier cycles; retain explainable wait chains and recovery rules. |
| 47–48 / 40–41 | Wait channels | Couple typed waits with durable state and ready-queue notification. |
| 49–51 / 42–44 | Hand-over-hand locking and safe semaphore sleep | Wait registration/handoff must not lose ownership or notifications at abstraction boundaries. |

## 3. Research implications and limits

The scalable commutativity research relates interface semantics to conflict-free implementation opportunities under its model; a later paper provides a revised verified proof. Use it to remove unnecessary coordination, not to claim linear scaling across cloud services or a shared GPU. [Clements et al.](https://people.csail.mit.edu/nickolai/papers/clements-sc.pdf), [revised proof](https://arxiv.org/abs/1809.09550).

Mellor-Crummey/Scott's queue lock uses per-waiter nodes and local spinning. Borrow explicit queued handoff; an async admission queue is not an MCS lock. [Authors' synchronization algorithms](https://www.cs.rochester.edu/research/synchronization/pseudocode/ss.html). Linux lockdep demonstrates tracking lock-order dependencies to expose problematic cycles. Borrow diagnostic principles for application resources, not a claim that kernel lockdep checks LangGraph. [Linux lockdep](https://docs.kernel.org/locking/lockdep-design.html).

GCC documents portable atomic ordering, including cases where operations need a library fallback. Linux's false-sharing guidance recommends profiling and weighing layout changes against memory cost. Neither suggests that this Python kernel should begin with custom atomics or cache-line padding. [GCC atomics](https://gcc.gnu.org/onlinedocs/gcc/_005f_005fatomic-Builtins.html), [Linux false sharing](https://docs.kernel.org/kernel-hacking/false-sharing.html).

Hardware cache coherence and application versioning are different problems. In interpreting the lecture's MSI wording, Modified cache data can be current while backing memory is stale; MESI distinguishes Modified and Exclusive. Polyinference instead pins TaskSpec, documentation, candidate and model-input versions at service boundaries. [Intel cache/ordering discussion](https://www.intel.com/content/www/us/en/developer/articles/technical/fast-core-to-core-communications.html).

## 4. Identify the actual bottlenecks

The lecture's ideal fixed-workload bound is:

```text
T(n) = T(1) × [B + (1 − B)/n]
ideal speedup(n) = 1 / [B + (1 − B)/n]
```

`B` is the serial fraction and `n` equivalent parallel resources. Local and cloud models are not equivalent cores. Do not substitute the count of logical coding processes for `n` and predict inference throughput.

For this design, measure cloud strategy/review latency, dependency critical paths, local decode saturation, context reconstruction, tool/MCP startup, verification and serialized working-revision publication. Some waits overlap; a cloud call's elapsed time is not automatically serial CPU time. More workers may hide tool/cloud waiting while doing nothing for an already saturated decode service.

The relevant cost comparison includes initial cloud planning, every cloud review/replan, any explicitly allowed agent job, local execution resources, and failed repair/integration attempts. Count accepted TaskSpecs/project outcomes, not graph completions: a worker can correctly finish its protocol by reporting that it failed to solve the task.

## 5. Scheduling policy for the first two versions

### 5.1 Separate queue families and capacities

| Queue / capacity | G0 default design | G1 growth rule |
| --- | --- | --- |
| Controller commands/status/cancel | Responsive host control path, separate from long model calls | Preserve a bounded control-memory allowance and independent delivery path |
| Executable TaskSpecs | One active coding worker; FIFO among dependency-ready tasks | Increase worker-residency cap within memory; retain dependencies and claim uniqueness |
| Local inference | One shared service, one admitted decode initially | Change backend slot/memory configuration only after measured fit/quality/latency checks |
| Cloud strategy/review | Role-bound queue; one mutable conversation operation per controller | Share account quotas globally; use scoped sessions, not concurrent writes to one conversation |
| Shell / verification | One global shell operation; one reconciliation/assessment/commit owner | More private developers, with the same two global gates until an explicit protocol revision |
| Tool/MCP startup | One startup per instance generation, admitted peak memory | Share appropriate instances; additional workers do not each launch the same server |

The numerical defaults of one are conservative scope choices, not benchmark conclusions. Pending queue counts/bytes, maximum active processes and deadlines are finite configuration parameters. Keep kernel operation admission global even if multiple graph invocations each have their own `max_concurrency` setting.

Use per-process round-robin opportunities within a backend queue and FIFO age among equally eligible work. Do not hold a resource for a process simply because it has a long-lived controller/graph identity. Locality is a bounded preference, not authority to monopolize the service.

### 5.2 Variable-sized requests and starvation

A request must be compatible with configured total capacity before it enters an ordinary wait queue. A tool that can never coexist with the resident model is `BLOCKED_RESOURCE_CONFIGURATION`, not a transient wait that will resolve by polling.

For temporarily unavailable compatible work, maintain original enqueue age and a finite overtaking limit. If smaller/newer requests repeatedly bypass an older request, stop admitting new conflicting work while existing bounded operations drain, then admit the old request's complete resource vector atomically. Do not give it partial allocations while it waits. Unrelated resources/control work can continue. Active operations must already hold their full required vector; hidden nested allocations would invalidate this policy.

If resources cannot drain because of unresolved remote work, a non-reclaimable session or a failed backend, report that cause and honor the configured deadline. Bounded waiting claims depend on available capacity and terminating operations; a queue cannot guarantee progress through a permanently unavailable provider.

## 6. Memory-aware tool/model residency

Default to retaining the chosen local model. Register only the tools the v1 graph needs, keep compact metadata, start cold tool/MCP services on demand, and tear down restartable idle instances with zero leases under document 4's protocol. Keep prompts, queues, logs and retained graph state bounded; raw output offload still needs disk/retention limits.

Use idle age/LRU only among safely restartable, zero-lease services. Do not evict an active call, a stateful session lacking a recovery contract, or the model mid-generation. Confirm process exit/reclaimed memory before updating available capacity. Repeated server/model load churn is a measured failure mode to avoid.

If required tool peak plus model/inference/kernel/headroom cannot fit, the controller reports the resource issue and can ask cloud strategy for a smaller task or permitted lighter tool. A model/backend change creates a new ExecutionProfile for new runs; in G0, stop the old run and carry retained artifacts into a new run rather than mutate an active profile. A later explicit whole-run migration feature could relax that restriction. Shared model-service reconfiguration must also quiesce affected work. Do not silently transform a local coding TaskSpec into an unrestricted cloud coding job.

Measure host RAM and VRAM/unified domains separately. Worker count, model-slot count and tool-memory allowance are separate knobs. The plan supplies no hardware/model numbers, so choosing a GPU, model size or safe concurrency maximum remains subsequent deployment research.

## 7. Independent operations and unavoidable coordination

| Operations | Commutativity/independence condition | Design decision |
| --- | --- | --- |
| Read pinned Info Documentation/context | Immutable authorized versions and independent cursors | Read by artifact/version; no global mutable read position |
| Store reports for distinct attempts | Distinct IDs and no required total event order | Immutable keyed records; per-process causal/event sequences |
| Advance different private workers | Distinct continuations/workspaces and no shared invariant changed | Per-process ownership/mailboxes |
| Start/use the same tool server | Shared instance, memory and generation state | Coordinate startup and leases; transport concurrency is insufficient |
| Consume the last decode slot/cloud budget | Winner changes observable admission | Exact central reservation |
| Revise the plan or publish working revision | Affects active specs/accepted evidence | Expected-revision checks and controller/integration serialization |

Avoid one large mutable “all agents state” object or a global sequence number for every token/progress event unless required by the external contract. Batch approximate telemetry; keep grants, claims, settlement, plan/head pointers and accepted evidence authoritative. Different file paths do not prove coding tasks commute; shared API/build assumptions still require integration checks.

Retain coarse simple ownership until measured contention justifies per-project/process/backend partitioning. If future coordinators receive preallocated budget/capacity grants, their sum plus unallocated capacity must conserve the global limit. A crashed worker's grant cannot be duplicated while its old work can still consume it.

## 8. Prevent agent-specific deadlocks

| Cycle in this architecture | Why it stalls | Selected prevention |
| --- | --- | --- |
| Controller holds the only execution permit while waiting for its coding worker | Worker cannot acquire the permit to produce TaskReport | Async wait releases transient execution capacity; driver residency and backend permits are separate |
| Local worker retains a decode slot while waiting for a tool; another operation retains tool memory while requesting decode | Cross-stage hold-and-wait | Each phase requests its actual simultaneous vector; release no-longer-consumed capacity before the next phase |
| Integration owner waits for cloud review while review requires a result that needs integration ownership | Blocking across ownership boundary | Run merge/reconciliation-development/final-assessment inside verification ownership; never wait for senior review while holding it |
| MCP startup callback requests another resource while holding the lifecycle lock needed to publish readiness | Reentrant startup/control cycle | Run callbacks/startup outside internal locks; reserve known startup/call needs before launch |
| T1 depends on T2 and T2 depends on T1 | No task can become executable | Reject cyclic dependency publication; changed dependencies create a validated plan/spec revision |
| Worker holds workspace mutation authority while synchronously asking another task to mutate that checkout | Shared-workspace dependency cycle | One private writer; communicate via results or spawn an independent workspace under a declared feature |

Holding capacity while an actual operation consumes it is legitimate. Marking graph control WAITING does not make that capacity free. Prevention requires understanding resource ownership, not merely releasing counters whenever code awaits.

Declare a lock order for short multi-object transactions/sections, such as `(resource-class rank, stable object ID)`, with concrete ranks specified in the eventual implementation. All normal, callback and cleanup paths follow it. No model/tool/child/report wait occurs while holding these internal locks. Hand-over-hand locking is only for an actually ordered data structure with proven node lifetimes, not for passing mutexes between agents.

### 8.1 Wait diagnostics and recovery

A wait record contains process/task/operation ID, wait kind and target, resource units needed, known holder(s), start/deadline, last progress, and current plan/spec identity. G0 supports typed diagnostics and deadline handling. G1 adds dependency/resource-cycle checks before allowing richer combinations.

A cycle is sufficient evidence only under the relevant exclusive/single-instance assumptions. Multiple interchangeable resource instances require quantity/progress analysis. Waiting for explicit user input, a cloud outage or an unsatisfiable memory configuration is not automatically a mutex deadlock.

Recovery blocks new effects from the victim, revokes authoritative publication, requests cancellation, quarantines private candidates and releases only demonstrably unused resources. Remaining remote work stays supervised. Pick a victim based on safe cancellation, priority, work already spent and dependency impact. Bound/back off retries; immediately recreating the cycle is not recovery. Keep status/cancel/reconciliation responsive even when worker execution is saturated.

## 9. Native mechanisms: conditional research outcomes

C11 atomics, fences, false sharing and MCS are relevant if a future native kernel helper or serving component becomes a measured hotspot. Use maintained primitives first. A custom component must specify publication ordering, object lifetime/reclamation, supported architectures and cancellation/preemption behavior. An atomic counter cannot make the multi-record memory/claim budget invariant atomic.

Do not copy historical spinlock loads into racy C/C++, pad all Python objects to a guessed cache-line size, or busy-spin during model/network waits. Apply native layout/queue-lock tuning only with an end-to-end benefit that justifies its complexity and memory cost. This keeps the low-level lecture material connected to a real decision without making it mandatory v1 work.

## 10. Requirements and acceptance conditions

| ID | System requirement | Origin | Acceptance condition for a future build |
| --- | --- | --- | --- |
| L5-R01 | Concurrency increases MUST be justified by accepted outcomes, latency, cost, memory and contention. | p. 3; planning p. 3 | A worker-count sweep identifies where additional workers stop helping the strategy/local/verification pipeline. |
| L5-R02 | Independent process/report/context operations SHOULD avoid unnecessary global mutation. | pp. 3–5, 18–31 | Storing an unrelated TaskReport does not rewrite every worker's state; required budget coordination remains exact. |
| L5-R03 | Finer locking/partitioning MUST preserve all original invariants and acquisition order. | pp. 4–5, 42–46, 49 | Partitioning passes the same forced schedules and demonstrates improvement before adoption. |
| L5-R04 | Wait queues MUST suspend and support targeted wakeup plus safe cancellation/removal. | pp. 26–40, 48–51 | Cancelling a queued worker or MCP waiter leaves no leaked claim, lease or slot. |
| L5-R05 | Multi-resource requests MUST use atomic admission or declared acyclic acquisition; short metadata locks MUST NOT cross blocking service boundaries; the verification ownership permit has the explicit longer phase lifetime. | pp. 42–46 | Decode/tool/verification stages cannot retain cyclic partial allocations. |
| L5-R06 | A waiting controller MUST NOT occupy transient execution capacity needed by its worker. | pp. 43–46; L2-R04, L3-R04 | One host event loop can advance the worker that will produce the controller's awaited report. |
| L5-R07 | Every wait MUST identify its dependency/resource and a diagnostic/deadline outcome. | pp. 46, 48–51 | Inspection distinguishes cloud uncertainty, missing predecessor, active tool lease and impossible memory fit. |
| L5-R08 | Dependency publication MUST prevent unsupported cycles. | pp. 42–46 | The cloud's cyclic task breakdown is rejected before workers wait indefinitely. |
| L5-R09 | Recovery MUST revoke stale publication while retaining accounting for unresolved external work. | pp. 44–46; L4-R11, L4-R15 | Aborting a victim cannot free a cloud reservation still in use or let its late candidate overwrite a survivor. |
| L5-R10 | Any native synchronization extension MUST follow its language/architecture memory model and object-lifetime contract. | pp. 6–16, 33–40 | Appropriate publication/race/lifetime checks pass; historical pseudocode is not treated as a portable implementation. |
| L5-R11 | Cached prompts/results MUST bind input/plan/docs/task/model/tool versions and authorization scope. | pp. 18–24; application inference; L2-R09 | Replanning or changing a verifier/model prevents reuse of an incompatible result. |
| L5-R12 | Eligibility/locality policy MUST bound overtaking under stated capacity/termination assumptions. | pp. 26–40; L4-R13 | Continuous small or warm-session requests cannot indefinitely bypass older compatible work. |
| L5-R13 | Wait handoff MUST preserve authoritative state and ownership through cancellation/publication races. | pp. 48–51; L4-R05 | A completion between predicate check and subscription cannot strand the local worker or controller. |
| L5-R14 | Any later per-worker resource grants MUST conserve global capacity despite failure. | pp. 3–5, 44–46; L4-R02, L4-R10 | The same tool-memory/cloud allowance cannot be reclaimed and consumed by two owners. |
| L5-R15 | Tool/model residency policy MUST avoid active eviction and identify permanent incompatibility separately from temporary shortage. | pp. 3–5, 18–31; planning p. 1 | A too-large MCP dependency becomes an actionable blocked configuration, not an endless startup/model-reload loop. |
| L5-R16 | Capability growth MUST add only needed, versioned operations with memory, completion and recovery contracts. | pp. 4–5, 42–51; planning pp. 1–3 | Supporting a new agent tool/graph feature does not silently change existing process behavior or enable an entire harness. |

## 11. Cumulative reference execution

The following is an illustrative trace specification, not an executed project or benchmark.

| Event | Expected ownership and evidence |
| --- | --- |
| Cloud plan publishes eligible tasks | Each started worker gets a private copy at a recorded base. |
| W1 and W2 develop | Private edits/reasoning overlap; shell calls serialize globally. |
| W1 requests verification | Outside shell ownership is released first; W2 may continue private development. |
| W1 owns verification | Capture H0, merge, run reconciliation development, then final assessment loops. |
| W1 commits P1 | Publish provisional head P1 and completed-unresolved report before verification release. |
| W2 enters next | Merge P1 into its copy; run the special development loop even after a clean merge. |
| W2 assesses/commits P2 | Shell operations still serialize; publish P2/report before release. |
| Fail/uncertain assessment | Commit/report remains unresolved with hazards; provisional publication is not senior approval. |
| Senior review/revert | Examine original/later commits and blast radius; revert under verification/shell rules. |
| Steering arrives with W1/W2 started and W3 pending | Finish W1/W2, including gate waits; do not start W3; then invoke the planner. |
| Project acceptance | Review final resulting revision and required evidence; unresolved provisional history alone cannot prove success. |

This trace fixes what moves between tiers, what the kernel schedules, and where success is decided. It does not require cloud code generation to replace the selected local execution path.

## 12. Staged design for a future build

| Stage | Required design surface | Gate before expansion |
| --- | --- | --- |
| G0 / OS v1 | One declared coding application, controller + one local worker, role-bound inference, simple tools/optional minimal MCP, compact persistent records, bounded artifacts, scoped workspaces, status/cancel, validated TaskSpec/TaskReport | Trace the full mixed-tier path; fit measured residual memory; recover interrupted work without unsafe duplicate effects |
| G1 | Multiple instances of the same coding worker, bounded claims/queues, shared inference/tool services, exact reservations, targeted wakes, controlled integration and dependency diagnostics | Useful throughput improves while quality, memory, spend and liveness constraints hold |
| G2 | Additional agent programs/features, each with a manifest/ABI/state version and explicit added operation contracts | Existing runs remain pinned/compatible; unsupported features fail before effects |
| Optional deployment scaling | More coordinators, shared transactional authority and guarded takeover/checkpoints | Single-coordinator contention is demonstrated and stale writers cannot publish |
| Optional native optimization | Layout/atomic/queue-lock changes in a measured native hotspot | End-to-end benefit outweighs complexity and memory overhead |

The planning document asks to understand the complete system's data needs while implementing the minimum first version. The schemas provide stable identity, role, version, ownership and resource references now; optional subsystems remain absent until needed. General dynamic agents, learned routing, model swapping, distributed leases, vector memory and custom MCS locks are not required to support the supplied v1 graph.

## 13. Remaining research and evaluation specification

Compare the supplied cloud-strategy/local-execution design with cloud-only and local-only baselines on fixed repository snapshots and the same acceptance criteria. A later experiment can vary strategy/review frequency, task granularity and backend bindings explicitly. Measure accepted task/project rate, spend per accepted outcome, p50/p95 time, per-domain memory peaks, queue age, local repair frequency, cloud rounds, model/tool residency churn, verification time and integration conflicts. Do not infer savings from cloud token counts alone.

Required liveness scenarios include one-loop controller/worker waiting, cyclic task proposals, a cancelled queue head, an MCP service too large to coexist with the model, active tool teardown, replan during candidate verification, provider disconnection after submission, and stale-owner resumption if takeover is enabled.

The five lectures support foundations, processes, threads, concurrency and synchronization. Full scheduling-policy optimization, virtual-memory/filesystem design, durable-storage power-loss guarantees, distributed consensus, hardware/model selection and measured tier-allocation policies require further research. Those gaps are named without turning this documentation task into implementation of the planning document's project.
