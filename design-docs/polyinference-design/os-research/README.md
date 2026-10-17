# Polyinference OS research notes

The five lecture derivations remain ordered. All now incorporate the current [private-copy/two-mutex concurrency protocol](concurrent_coding_protocol.md), the full agent HTML and user clarifications. The LLM OS is an application operating endpoints; no computer-OS kernel work is implied.

## Read in lecture order

| Order | Lecture source | PDF pages / numbered slides | Revised design focus |
| --- | --- | --- | --- |
| 1 | CS350-1.pdf — Introduction | 17 / 15 | [Kernel boundary, cloud strategy/local execution, minimal features and memory envelope](01-CS350-1-foundations.md) |
| 2 | CS350-2.pdf — Process abstraction | 32 / 31 | [Controller/worker processes, request ABI, TaskSpec and TaskReport](02-CS350-2-processes.md) |
| 3 | CS350-3.pdf — Threads | 29 / 29 | [Proposed LangGraph steps/state, submit/wait boundaries and host execution](03-CS350-3-threads.md) |
| 4 | CS350-4.pdf — Concurrency | 50 / 44 | [Plan/task claims, resource reservations, tool lifecycle, recovery and publication](04-CS350-4-concurrency.md) |
| 5 | CS350-5.pdf — Synchronization | 51 / 44 | [Pipeline scaling, memory residency, deadlocks, cumulative trace and staged scope](05-CS350-5-scalability-and-deadlocks.md) |

Each lecture's document was revised before moving to the next lecture. A document uses its own lecture and earlier ones; document 5 assembles the cumulative design. Ordered derivation tables account for all 179 PDF pages, including administrative/outline pages and repeated reveals. References use PDF pages where printed slide numbers repeat. Requirement IDs use `Lx-Ryy`; the revised set contains 75 numbered requirements with origins and future acceptance conditions.

## Reference evidence and its status

| Reference | What was actually available/read | How it is used |
| --- | --- | --- |
| Original five CS350 PDFs | All five lectures, in order | OS concepts from which requirements/designs are derived |
| F26 Planning.pdf, p. 1 | Project layers/workstreams, process interface, minimum kernel and residual-memory/tool constraint | Priorities and system constraints; marked P1/planning p. 1 in tables |
| F26 Planning.pdf, p. 2 | Small LangGraph subset, simple coding-agent base, increasing system versions | Feature-driven scope and compatibility; P2 |
| F26 Planning.pdf, p. 3 | Mixed local/cloud cost-quality goal, agent/framework → custom midend → existing backends | Architecture intent and evaluation goal; P3 |
| Agent-v1 screenshot in this chat | Visible component labels and cloud-strategy/local-execution structure | Role/component mapping; marked D where abbreviated |
| WSL HTML path | Not accessible from the cloud workspace | The user supplied the screenshot as a substitute; no HTML contents are claimed |
| Primary technical sources linked in each document | Framework/protocol documentation and original research, checked 2026-10-16 | Constraints on proposed mechanisms, with claims separated from engineering inference |

Imperatives and work items inside the planning PDF are reference statements about the future project. They do not authorize carrying out those workstreams in this task. No coding agent was built or ported, no model/MCP service was installed, and no performance experiments were performed. Example traces and acceptance conditions specify later validation.

Some screenshot labels/edges are truncated. The cloud strategy versus local execution roles and visible component names are reference evidence. The process mapping, exact node/record/operation names, SQLite choice, kernel placement, default capacities and handoff contracts are proposed engineering decisions. The original screenshot-based contracts have since been updated using the supplied full HTML, user clarifications and concurrency model.

## What changed from the first draft

The first draft treated local/cloud execution too much like a generic model router. This revision uses the supplied cloud strategy and local coding loop as the reference application. It assigns each screenshot component an application/kernel responsibility and defines the data/control handoffs between them.

The core process interface now includes ProjectRun, AgentProgram, Process, TaskSpec, task attempt, Operation and TaskReport identities. A versioned ExecutionProfile binds roles to the selected model/backend stack. The graph design names controller/worker steps and persisted state. Resource scheduling distinguishes resident graph processes, active decodes, cloud calls, tools and MCP-server memory. Recovery covers uncertain submission, duplicate reports, replanning and the separate checkpoint/artifact/metadata domains.

Memory-constrained local MCP/tools are part of admission and lifecycle design. The minimal kernel supports only the registered first agent's graph/action/tool subset; adopting mini-SWE-agent or Deep Agents does not expand that scope automatically. Their project links inform agent-base research, not a new implementation task.

## Chosen defaults and growth boundaries

The custom kernel is a program-level coordinator operating LLM/tool endpoints. It uses a single coordinator, embedded transactional metadata, persistent graph continuations, immutable artifacts/private workspaces, a shared local model service and role-bound backend adapters. The default strategy/review operation is cloud model inference; a cloud agent endpoint is an explicit adapter profile with separately declared guarantees.

G0 is one mixed-tier coding application with a controller context and one coding worker at a time. The controller is host orchestration, not an extra autonomous coding agent. G1 runs many instances of that coding worker while sharing bounded inference/tool services. G2 adds agent programs/features under explicit manifests and versioned contracts. Multiple kernel coordinators and native synchronization optimization are separate, optional deployment decisions.

“MUST” denotes the proposed build contract, “SHOULD” a default allowing an explicit documented exception, and “MAY” an optional feature. Requirements apply when their associated feature is enabled. Distributed ownership requirements do not require G0 to deploy leases or a cluster. Hardware, models, numerical memory/spend/latency limits and final agent-base choice remain open deployment inputs because the references do not determine them.

The future OS should preserve the distinction between a waiting graph and an active backend: async waiting can release a host execution opportunity while inference memory, a cloud job or a tool lease remains occupied. The cumulative execution trace in document 5 follows this distinction from the user objective to project acceptance.


The current concurrency model replaces task-long global editing ownership: private development overlaps, shell commands serialize, and merge→reconciliation development→final assessment→commit/publication is a separate serialized phase. Completed reports remain unresolved until senior review.
