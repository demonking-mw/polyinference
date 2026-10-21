# Source consolidation and decisions

Original consolidation: 17 October 2026; accepted decisions aligned 20 October 2026.
Read the [minimal OS specification](README.md) and [design index](../README.md).

> **Edited 2026-10-20 because** later fixes explicitly reverse the scoped-copy,
> all-verdict publication and mandatory physical-memory assumptions and add optional
> context services. [DESIGN_REVISIONS.md](DESIGN_REVISIONS.md) records why, which
> original artifacts remain historical, and which implementation gaps are not
> authorized revisions. Earlier source evidence is preserved below.

The subsequent [joint integration audit](../INTEGRATION_AUDIT.md) tightens review/acceptance barriers, gate-abort recovery, worker residency and scoped-delta validation in the paired current designs. Older research's plan-quarantine rule does not revoke captured workers merely because ordinary review or steering was received. The hybrid map remains the default; explicit comparison runs may choose another feasible fixed map before starting.

## Precedence

1. Latest user directions and their recorded accepted revisions govern the current
   OS/agent profile: default full tracked worktrees in the actual project, verified
   integration, generic OS services and optional submitted-context assistance.
2. The merged graph supplies the original execution/memory baseline. Keep its bytes
   and identity; later R02–R04 supersede its copy/publication/commit assumptions.
3. The five lecture-derived notes, prior OS proposal and concurrency protocol explain mechanisms and rationale. Older defaults do not override the current scope.
4. Historical agent graphs and reference handbooks explain alternatives and evolution.

The five original lecture PDFs and planning PDF are not present in this checkout. This consolidation uses their supplied ordered derivations and requirement tables, not a new claim to have inspected the PDFs themselves. No hardware/model capacity or performance result can be inferred from those documents.

## Five-lecture contribution

| Supplied material | Fundamental lesson retained | Translation to this workload |
| --- | --- | --- |
| [1. Foundations](../polyinference-design/os-research/01-CS350-1-foundations.md), L1-R01–R14 | A narrow application-level kernel mediates authority/resources through a stable boundary. Keep the memory envelope explicit. | LangGraph is the frontend; one shared local model/cloud adapter are execution resources. Store histories off-heap and keep the runtime small. No privileged kernel work. |
| [2. Processes](../polyinference-design/os-research/02-CS350-2-processes.md), L2-R01–R14 | Identity, private state, explicit creation/wait/exit, process versus operation, durable result and scoped streams. | Each assignment has one invocation, code workspace and continuation; all model calls share weights. A cloud job/session is not the process identity. |
| [3. Threads](../polyinference-design/os-research/03-CS350-3-threads.md), L3-R01–R14 | Independent continuations, async waits, bounded blocking work, one owner and common dispatch/resume hooks. | A driver waiting for inference yields its host coroutine while the request remains active. Several requests feed c-batching; Python thread count is not model capacity. |
| [4. Concurrency](../polyinference-design/os-research/04-CS350-4-concurrency.md), L4-R01–R17 | Atomic claims/reservations/publication, durable effect IDs, safe notifications and short metadata transactions. | Reserve local context/in-flight and cloud allowance atomically; publish head/report/receipt together. The long verifier permit is separate from short database locks. |
| [5. Scalability/deadlocks](../polyinference-design/os-research/05-CS350-5-scalability-and-deadlocks.md), L5-R01–R16 | Useful throughput, shared bottlenecks, fairness, lock ordering and explicit waits. | Do not count agents as GPU cores. Keep model batching concurrent but final publication serial; prohibit shell-to-verification inversion and review waits inside verification. |

The low-level lecture mechanisms—spinlocks, MCS, native atomics/cache-line layout and host-kernel preemption—are not required to implement these application protocols. The supplied notes already distinguish the conceptual lessons from copying those mechanisms.

## Existing document families

| Documents examined | Consolidated decision |
| --- | --- |
| [Merged HTML](../polyinference-design/polyinference-agent-design-merged.html), [JSON](../polyinference-design/polyinference-agent-design-merged.json), [merge notes](../polyinference-design/merged-agent-design-notes.md), merge/check scripts | Current architecture has 23 nodes/57 edges; memory has 19/21. Names/layout/editor geometry concern the diagram; the OS implements behavioral contracts, not a runtime process for every box. |
| [Prior OS project design](../polyinference-design/project_design.md), [main concurrency protocol](../polyinference-design/concurrent_coding_protocol.md), [research copy](../polyinference-design/os-research/concurrent_coding_protocol.md), [agent suggestions](../polyinference-design/agent_suggestion.md), [research index](../polyinference-design/os-research/README.md) | Retain private development, two permits, mandatory reconciliation/assessment, provisional publication, unresolved results, delayed steering and effect-safe recovery. The copied protocol is duplicate content, not another independent requirement. |
| [Agent design](../langgraph-agent/README.md), [wire models](../langgraph-agent/contracts.py), [schema](../langgraph-agent/contract.schema.json), [examples](../langgraph-agent/examples.json), validation helper | Reuse 2.0 process/query/report/publication contracts. Add a negotiated scoped-workspace/core-profile extension instead of forcing every future runtime feature into the minimal OS. |
| [Root brief](../../PROJECT_BRIEF.md), [design brief](../polyinference-design/PROJECT_BRIEF.md) | Keep the small reference workload and outcome-based comparison. Their discovery-first/one-worker framing is historical, not the current complete execution policy. |
| [Older user graph](../polyinference-design/polyinference-agent-graph.html), [AI-modified graph](../polyinference-design/ai-modified_agent_graph.html), [AI JSON](../polyinference-design/modified_agent_graph.json), v0/v1 graphs below | Historical provenance. Current private-failure rules come from explicit later O04/FIX-0040 decisions, not an implicit restoration of an old graph. Do not bypass assessment or treat raw inference as a completed native job. |
| [v0 JSON](../../references/docs/polyinference-agent-structure-v0.json), [v1 JSON](../../references/docs/polyinference-agent-structure-v1.json), [v1 HTML](../../references/docs/polyinference-agent-v1.html), [v1-1 HTML](../../references/docs/polyinference-agent-v1-1.html), [editor sources/notes](../../references/docs/agent-design/README.md), [architecture study](../../references/docs/agent-structures.html) | Preserve the evolution toward deterministic sprint orchestration. Editor/template assets and their checks are not an OS engine. |
| [mini-SWE handbook](../../references/docs/mini-swe-agent-handbook.md) | Reuse narrow model/environment boundaries and bounded action/observation loops. Do not adopt a shell completion marker as proof of project acceptance. |
| [Deep Agents handbook](../../references/docs/deepagents-agent-handbook.md) | Keep graph/checkpoint/store/backend distinctions and per-process context. Its MCP, skills, subagents and terminal host are not core requirements. |
| [Claude Code handbook](../../references/docs/claude-code-agent-handbook.md) | Keep capability mediation, output offload and source attribution. Its larger product/team/memory platform is outside this OS. The reconstructed snapshot's limitations still apply. |
| [Repository-mapping guide](../../references/docs/repo-mapping-guide.md) | Include enough source/config/test closure and freshness metadata. Start with declared paths plus bounded expansion, not an automatic repository graph/indexing service. |
| [Cloud-agent proxy brief](../../references/codex-agent-proxy-brief.md) | Select one actual protocol and prove its limits/tool visibility/cancellation contract. API compatibility alone does not imply agent execution or brokered shell control. No proxy is installed or selected here. |

Vendored agent source trees are supporting implementations rather than additional PolyInference design authority. This task does not port or audit those entire repositories.

## Resolved scattered defaults

| Older statement | Core decision now |
| --- | --- |
| One coding worker and one local decode initially | Permit bounded multiple workers/in-flight local requests in the completed core. One-worker bring-up remains a test configuration. |
| Full versus partial development copies | Default in-place coding uses full tracked worktrees with bounded writes (FIX-0040). Scoped copies and complete private integration remain the explicit legacy path. |
| All normally assessed verdicts publish provisionally | Superseded by O04/FIX-0040: default in-place fail/uncertain stays private; successful verified candidates integrate. Legacy isolated uncertain assessment still publishes provisionally. |
| Snapshot/pause a running model as though it were a CPU thread | Checkpoint explicit graph state at supported boundaries; reconcile active external work. Backend token/KV scheduling is separate. |
| General memory/MCP/resource platform | Generic tools/records/artifacts plus optional context packing/compaction now. Canonical memory stays agent-owned. Rich tiers/indexes, MCP lifecycle and automatic routing remain deferred. |
| OS intercepts arbitrary graph execution | Explicit public-API effect nodes and an external LangGraph adapter; no private framework patch. |
| One semaphore called concurrency | Separate driver admission, endpoint requests/context, shell and verification. The server owns batching; original paused-worker residency semantics remain an open implementation gap. |
| OS-managed physical fit and automatic cleanup | Physical RAM/VRAM admission, migration and automatic GC are explicitly deferred; configured quotas and explicit archival have narrower guarantees. |
| Caller-only provider/output recovery | OS bounded known-ended transient/cutoff recovery uses durable charged identities; agents retain grammar and semantic decomposition. |
| Mandatory external SDK/shared agent library | Current RuntimePorts is directly usable. The optional shared library is deferred until demonstrated reuse. |

## Primary technical checks

Checked official documentation on 17 October 2026. The OS policies above are engineering synthesis, not features claimed to be supplied automatically by these projects.

- The inference engine exposes sequence/token scheduling configuration and prefill/decode tradeoffs; the adapter describes measured/configured capacity while the engine schedules tokens. [vLLM scheduler](https://docs.vllm.ai/en/stable/api/vllm/config/scheduler/), [optimization](https://docs.vllm.ai/en/stable/configuration/optimization/)
- Public graph nodes/runtime context, checkpoint durability and interrupt replay support additive integration. They do not make external effects transactional. [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), [checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers), [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

The implementation still needs actual hardware/model/backend configuration, measured capacities, chosen endpoint credentials and adapter conformance tests. No fixed throughput, quality or memory fit is established by this design.
