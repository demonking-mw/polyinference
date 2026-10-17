# Polyinference OS design — 2. Processes, requests and tier handoffs

## Current agent concurrency contract

Updated using the full agent HTML and the user's later clarifications. The HTML is the agent design, including OS-handled parts; the LLM OS is an application operating endpoints, not a computer-kernel subsystem. [Concurrent coding protocol](concurrent_coding_protocol.md) defines the current operational contract. It supersedes any earlier screenshot-based alternatives below where their scope differs.

Every in-progress coding process owns a codebase copy. Private development overlaps. Every shell/script command, including test/Git commands, acquires a global `shell_mutex`. A separate `verification_gate` serializes latest-head merge, at least one specially prompted development/reconciliation loop, the final one/few local-model testing/examination/assessment iterations, commit and provisional shared-head/report publication. Release verification only after that boundary; release shell after each confirmed command. When both are needed the order is **verification then shell**; an outside shell owner releases before requesting verification. The application coordinator keeps running throughout.

Assessment produces `fail / uncertain / successful`; every normal local completion remains `unresolved` until sprint-coordinator review. Publish completed commits provisionally with verdict/hazards so the next entrant receives them; this is not senior acceptance. Preserve one attributable net-change commit for senior revert and blast-radius analysis. Steering stops new local starts, waits only for the captured in-progress locals (including gate waiters) to finish, then goes to the planner.

| Current extension | Required behavior |
| --- | --- |
| L2-C01 | Each active coding attempt owns its copy, base revision and scoped tool context; no shared editing before publication. |
| L2-C02 | Shell and verification ownership are distinct, obey one acquisition order, and are not computer-OS locks. |
| L2-C03 | Each verifier merges the latest published head, runs reconciliation development and final assessment, and publishes its commit/report before releasing. |
| L2-C04 | Publication stays provisional/unresolved; unknown active effects retain applicable exclusion and senior rollback checks dependents. |


**Lecture basis:** CS350-2.pdf, Process abstraction, 32 PDF pages / 31 numbered slides. Builds on [document 1](01-CS350-1-foundations.md) using lectures 1–2 only. **Project context:** planning pp. 1–3, the uploaded agent HTML and subsequent user clarifications. **Revision/research date:** 2026-10-16.

## 1. Decide what a process means in this application

Use two logical process roles in the registered `coding-v1` application:

- A **project controller process** executes the host Orchestrator / Loop Handler, cloud query/result processing, task publication, report review and project acceptance. Strategy/review inference is an operation owned by this process.
- A **coding worker process** is one instance of Local coding agent loop executing one immutable TaskSpec attempt through local inference, tools, verification and a TaskReport. It terminates after that report is durable. A later task gets a new logical process, even if the same host worker executes it.

G0 has one controller and at most one coding worker at a time. This is one mixed-tier coding application; the controller is not an additional autonomous coding agent. G1 admits several instances of the same worker program. G2 can register additional program/role definitions. This is a proposed process mapping; the screenshot does not make every box a separate process.

A logical process is an ownership/recovery unit, not necessarily an OS subprocess, container or model instance. Multiple logical processes can share a host event loop and a local model server. Actual generated commands remain host-supervised subprocesses. The two entry roles may be small graph definitions or declared entry points; v1 need not support arbitrary graph composition.

| Entity | Identity and purpose | Must remain distinct from |
| --- | --- | --- |
| ProjectRun | `project_id`, objective, accepted plan revision, provisional working revision and senior dispositions, pinned ExecutionProfile version, project limits | A single coding task or cloud conversation |
| AgentProgram | `program_id`, graph/version, entry roles, required kernel feature subset | A live execution |
| Process | `process_id`, role, grants, private continuation, accounting | Host PID and model-server instance |
| TaskSpec | `task_id + spec_revision`, one bounded unit of coding work | A graph node or an arbitrary text prompt |
| Task attempt | `task_attempt_id`, process/workspace executing a TaskSpec | A new strategic task |
| Operation | `operation_id`, one inference, tool call or publication intent | A process, or a provider retry attempt |
| LangGraph continuation | `thread_id`, namespace and checkpoint reference | Host thread, model KV cache, provider session |
| Backend session/job | Provider-specific session/turn/job IDs | Kernel authority or local continuation |

## 2. Slide-to-design derivation, in order

References use PDF pages; the first printed slide 14 appears twice.

| PDF pages / numbered slides | Lecture concept | Polyinference consequence |
| --- | --- | --- |
| 1–4 / 1–4 | Process abstraction and APIs | Define an execution unit and request contract beneath the chosen agent. |
| 5–7 / 5–7 | Program instances, utilization and concurrency | Instantiate the local worker program repeatedly without duplicating model weights; overlap waits, not just threads. |
| 8 / 8 | Private machine view and explicit sharing | Isolate TaskSpec attempts, context, workspace and handles; communicate through TaskSpec/TaskReport. |
| 9–10 / 9–10 | Lecture outline | No independent requirement. |
| 11–13 / 11–13 | Create, wait, exit, signal, program replacement | Specify spawn/wait/cancel/finish and fresh role entry, rather than copying live graph sessions. |
| 14–19 / 14–18 | Shell supervises child execution | Controller waits on a durable report while the kernel supervises the worker and its tools. |
| 20–21 / 19–20 | Descriptor sharing and redirection | Give model/tool streams scoped handles, independent cursors where needed, and explicit inheritance. |
| 22–23 / 21–22 | Pipes and stream closure | Bound observations and define progress, EOF, failure and terminal result semantics. |
| 24–25 / 23–24 | Fork versus explicit spawn | Use explicit TaskSpec/limits/handles; do not fork the GPU-serving runtime. |
| 26 / 25 | Lecture outline | No independent requirement. |
| 27–28 / 26–27 | PCB and lifecycle states | Persist process state, wait reason, continuation and owned operations. |
| 29–30 / 28–29 | Ready queues, dispatch and preemption | Separate queue eligibility, process control and actual backend occupancy. |
| 31–32 / 30–31 | Context save/restore and cost | Restore logical context by references; avoid copying full histories or reloading the model at every switch. |

## 3. Research and selected mechanisms

LangGraph persistence records workflow state under thread/checkpoint identities. Use a persistent saver and synchronous durability initially for resumable runs. This does not serialize a Python stack or atomically commit external work. [LangGraph checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers).

Asynchronous subprocess supervision must drain stdout/stderr; waiting on an undrained pipe can deadlock, while collecting unlimited output in memory also fails the planning document's memory constraint. Stream into bounded artifacts and return a small observation. [Python subprocess APIs](https://docs.python.org/3/library/asyncio-subprocess.html).

Git worktrees provide separate checkouts but share repository metadata. They are a useful same-owner workspace mechanism, with host protection still required. Use separate repositories where isolation requires it. [Git worktree](https://git-scm.com/docs/git-worktree). CUDA has restrictions around process forking; keep the local serving backend independently managed. [PyTorch multiprocessing guidance](https://github.com/pytorch/pytorch/blob/main/docs/source/notes/multiprocessing.md).

## 4. Records to define before implementation

These are conceptual schemas and field contracts, not implementation code. V1 stores the populated core fields; it does not prebuild every future subsystem.

### 4.1 Process control block

| Field group | Required fields / semantics |
| --- | --- |
| Identity | `process_id`, `project_id`, `parent_process_id`, `program_id`, `program_version`, `execution_profile_version`, role (`controller` or `coding_worker`) |
| Input | `input_ref`; for workers, `task_id`, `spec_revision`, `task_attempt_id`, immutable `base_revision` |
| Lifecycle | `state`, monotonic `state_revision`, `wait_kind`, `wait_target`, creation/deadline/last-progress timestamps |
| Continuation | `state_schema_version`, LangGraph thread/namespace, last published checkpoint reference |
| Authority | Kernel-issued `grant_ref`, workspace ID, authorized artifact/tool/backend scopes |
| Resource ownership | Limits/reservation references, outstanding operation IDs, known and uncertain external work |
| Result and cleanup | `terminal_result_ref`, cancellation intent, cleanup status; retain result after releasing host resources |
| Later ownership extension | Worker/owner generation and lease information only if takeover is enabled; do not rely on unguarded concurrent checkpoint writes |

The PCB and graph state have different jobs. The PCB owns authority and scheduling state. Graph state owns the application's plan/execution position. Both refer to the same immutable inputs and operation IDs. A checkpoint cannot overwrite a grant or resurrect a cancelled process.

### 4.2 Cloud-to-local TaskSpec

| Field | Required meaning |
| --- | --- |
| `task_id`, `spec_revision`, `project_id`, `plan_revision` | Kernel-assigned identity and exact strategy version; preserve a cloud proposal's tag only as source metadata |
| `objective`, `scope` | One bounded deliverable and permitted change scope |
| `depends_on`, `dependency_result_refs` | Predecessors and the accepted outputs actually used |
| `base_revision`, `documentation_refs`, `context_refs` | Exact repository/context inputs; materialized before the task becomes executable |
| `required_tool_ids`, `backend_role` | Validated subset of existing project grants; coding role initially maps to local inference |
| `acceptance_spec_ref` | Required checks and deliverable conditions, retained from the accepted task definition |
| `limits` | Iterations, repairs, output/context size, deadlines and applicable resource/spend limits |
| `report_contract_version` | Expected TaskReport format |

Cloud output is a **proposal**. Cloud Result Processor validates schema, finite limits, dependencies, scope and required capabilities before publication. The kernel assigns IDs and enforces the effective grant. A proposal that needs a predecessor can wait with a dependency-relative input description; the host publishes a new, immutable executable spec revision with concrete inputs once dependencies are accepted. A worker never runs against a moving `latest` reference.

### 4.3 Local-to-cloud TaskReport

A TaskReport contains `task_id`, `spec_revision`, `task_attempt_id`, `process_id`, `plan_revision`, base revision, private candidate commit/patch reference, verification evidence references, actual usage, and `execution=completed; resolution=unresolved; verdict=fail / uncertain / successful; separate stop_reason`. It also includes a bounded explanation, unresolved assumptions and any requested strategy decision.

A `successful` assessment justifies the local verdict for the identified final tree. It remains unresolved until senior review, even after provisional shared-head publication. Reports can be read repeatedly after the worker exits. The controller passes only a bounded, policy-filtered report/context packet to cloud review; full tool logs stay available by reference.

### 4.4 Kernel request and result envelope

| Envelope field | Contract |
| --- | --- |
| `request_schema_version` | Reject incompatible requests before external work |
| `execution_profile_version` | Pin role/backend bindings and effective model/resource configuration to the admitted run |
| `project_id`, `process_id` | Bound to the authenticated runtime caller, including the controller; caller-supplied IDs alone grant nothing |
| `operation_id` | Stable identity for one intended effect; preserved across graph replay |
| `kind`, `payload` | A supported operation with validated parameters and versioned input handles |
| `expected_state_revision` | Reject stale state-changing commands |
| `grant_ref`, `deadline`, `resource_request` | Authority, finite lifetime, and admission requirements |
| `trace_parent` | Causal relation to a strategy round, TaskSpec attempt or prior operation |

The kernel computes/stores a request fingerprint and assigns separate transport/backend attempt IDs. Reusing an operation ID with different intent is an error. Repeating the same intent returns the retained receipt/result or current status, rather than creating another side effect. Detailed crash coordination is added in document 4.

A receipt identifies the operation and its admission state. A terminal result carries status, typed error if any, bounded output/artifact references, backend identity and ExecutionProfile version, known usage and termination certainty. Required error categories include invalid schema, unsupported feature, policy denial, capacity wait, stale revision, timeout, cancellation, backend failure and uncertain external outcome. A token delta is progress, not a terminal result.

## 5. Minimal operation set and permissions

| Operation | Caller and behavior |
| --- | --- |
| `process.spawn` | Controller starts the declared worker entry with one executable TaskSpec, scoped handles and limits; no ambient credential inheritance |
| `process.wait/status/cancel` | Controller or authorized user inspects/waits/cancels; waiting releases transient host execution capacity |
| `inference.submit` | Controller requests strategy/review, worker requests coding; kernel resolves the role binding and backend execution kind |
| `operation.wait/cancel` | Observe/stop a particular inference, tool or publication intent; distinguish cancellation requested from confirmed termination |
| `tool.call` | Worker or verifier requests a registered direct/MCP tool in its workspace with output/deadline limits |
| `artifact.read/write` | Access bounded content or create immutable output within authorized scope |
| `task.publish/claim/report` | Controller publishes validated work; kernel claims for one worker and retains report identity |
| `workspace.commit` | Prepare a private candidate for TaskReport; provisional publication occurs under verification ownership; senior resolution/revert is separate |

These can be in-process methods in G0. They are a conceptual ABI; this research does not implement an RPC server. A wrapper around mini-SWE-agent/Deep Agents must funnel model and tool effects through these operations rather than leave a parallel direct-client path.

## 6. Lifecycle and scheduling contract

Generic process states are `NEW`, `READY`, `RUNNING`, `WAITING`, optional `PAUSED`, `CANCELLING`, and terminal `SUCCEEDED`, `FAILED`, `CANCELLED`. Allowed normal transitions are new→ready→running, running→waiting→ready, running→ready at a safe yield, and running→terminal after a durable result. Any nonterminal state can enter cancellation. Terminal states cannot become runnable again; a retry uses a new attempt identity.

`RUNNING` means graph control is advancing. A worker awaiting local inference is `WAITING(INFERENCE, operation_id)` even while the model service is actively decoding. The controller may be `WAITING(CHILD_REPORT, process_id)` or `WAITING(CLOUD, operation_id)`. Resource reservations belong to outstanding operations and do not disappear when process control waits.

Task lifecycle is separate: proposed work is validated, waits for dependencies/capacity, is claimed and executed, then produces a report. Every completed local report is unresolved; only sprint-coordinator review can resolve it. Provisional publication does not accept the task. Failed checks can return to bounded local repair within the same attempt; changed scope/input/strategy creates a new spec revision/attempt. Process success means the role's output contract completed; for a worker, a durable fail or uncertain assessment report can be a correctly completed protocol without a successfully solved task.

Initially use FIFO among eligible ready work, with round-robin opportunities at supported graph/operation boundaries. Do not scan by process ID, spin on empty queues, or pretend to snapshot an arbitrary running node. The realization in LangGraph is specified in document 3. This lecture motivates dispatch; it does not select a full heterogeneous scheduling policy.

Spawn validates inputs, prepares workspace/continuation and grants, and publishes readiness only after setup is complete. Failure rolls back partial allocations or marks visible cleanup work. Cancellation prevents new dispatch, contains local command descendants, closes owned streams, retains results, and transfers unresolved remote work to a visible supervisor before reclaiming ownership. Optional snapshot branching/program replacement is deferred and must never copy a live remote job.

## 7. Workspace, stream and memory behavior

Each coding attempt owns a private codebase copy at its recorded base. Ordinary private development overlaps, but every shell command uses shell_mutex. Before final assessment, acquire verification_gate with shell ownership released, merge the latest provisional shared head, run at least one reconciliation-development loop, then assess, commit and publish the head with an unresolved report before release. Senior review is a later disposition, not the publication gate. Record original base, captured head, merge/WIP refs, final tree and attributable published commit.

Capture stdout and stderr concurrently into capped artifacts. Return a bounded observation containing exit status, a useful excerpt, truncation flag and full-artifact handle where retention permits. Define EOF, broken consumer, timeout and producer failure explicitly. A process exiting closes only its owned handles; provider/MCP sessions owned by a shared service have separate lifetimes. Independent artifact readers receive independent cursors.

Model weights are shared by the serving service. Process records contain compact references and bounded summaries, not copies of weights, raw provider clients, full tool logs or open connections. The host execution worker is reusable; its memory must not retain an exited process's private context indefinitely.

## 8. Requirements and acceptance conditions

| ID | System requirement | Origin | Acceptance condition for a future build |
| --- | --- | --- | --- |
| L2-R01 | Controller and coding workers MUST have distinct logical process identities and private continuations. | pp. 5, 8, 27; D | Several worker instances share the model service but cannot overwrite each other's workspace/checkpoint. |
| L2-R02 | Process and TaskSpec state transitions MUST be durable, versioned and distinct. | pp. 27–28 | A successful unresolved report cannot directly mark ProjectRun accepted; duplicate completion cannot resurrect a terminal process. |
| L2-R03 | Spawn MUST publish only a fully scoped, initialized worker or a visible setup failure. | pp. 11, 24–25 | Failure between checkout creation and readiness leaks neither runnable work nor untracked memory/reservations. |
| L2-R04 | Cloud/child/backend waits MUST be event-driven and release transient orchestration capacity. | pp. 6, 11, 28–30 | A controller waiting on cloud review does not block an authorized ready local worker. |
| L2-R05 | Only one graph driver MUST advance a process continuation. | pp. 27–31; L1-R03 | Duplicate start/resume requests cannot double-run a tool or compete to publish state. |
| L2-R06 | Cancellation MUST supervise local descendants and retain uncertain external operations. | pp. 12, 19, 30 | A tool child cannot keep changing the accepted workspace after containment is reported; remote uncertainty remains inspectable. |
| L2-R07 | TaskReports and terminal results MUST outlive the executing host worker. | pp. 11–12, 19 | The controller recovers the same report after worker exit/restart without rerunning its task. |
| L2-R08 | Tool/result streams MUST have byte limits, closure, error and backpressure semantics. | pp. 20–23; planning p. 1 | A verbose verifier cannot exhaust residual RAM or hang on an undrained stderr pipe. |
| L2-R09 | Recovery MUST bind the exact TaskSpec, input revisions, graph/ExecutionProfile versions and operation references. | pp. 27, 31–32 | Restart cannot accidentally continue task T under a revised plan, changed model binding or moving documentation reference. |
| L2-R10 | Local model residency MUST be shared; process/session state MUST remain scoped. | pp. 7–8, 32 | A second worker adds no second weight copy by default and receives no other worker's conversation. |
| L2-R11 | Any later branch/program replacement MUST use explicit fresh identities and compatible state, without copying live side effects. | pp. 11, 24–25 | An attempted branch of active cloud work is rejected or made quiescent before snapshotting. |
| L2-R12 | Dispatch order MUST use explicit eligibility/queue policy, independent of IDs. | pp. 28–30 | Renaming process IDs cannot change scheduling priority. |
| L2-R13 | Tier handoffs MUST use validated, bounded TaskSpec/TaskReport contracts. | pp. 8, 20–23; planning p. 1; D | A report missing candidate/evidence identity cannot satisfy a task; unbounded prose cannot become an executable queue item. |
| L2-R14 | Every side-effecting request MUST carry a stable operation identity and structured outcome. | pp. 15–17 of lecture 1; pp. 11–23 here; planning p. 1 | Replaying one request returns its known outcome/status; changing its payload under the same ID fails validation. |

## 9. First-version decisions and example

Use one controller context plus one coding worker at a time, compact records in the embedded transactional metadata store, immutable artifacts on disk, and a persistent LangGraph saver. Keep PID/host worker/provider IDs separate. Add schema/feature versions now, but populate lease/distributed extensions only when that feature is enabled.

For a reference workload such as adding JSON output to a toy CLI, cloud strategy may propose T1 formatter, T2 CLI wiring depending on T1, and T3 documentation. The host validates these tasks. G0 executes them serially with explicit bases and checks. G1 may run eligible independent tasks concurrently; integration still validates their shared project assumptions. This is an illustrative workload for design reasoning, not project code to build in this task.

**Next:** [Lecture 3 — LangGraph execution and bounded host tasks](03-CS350-3-threads.md).
