# Four general LangGraph agents on OS V1

These are small, trusted Python applications. The graphs have no PolyInference
import; the adapter uses the shipped OS. Use `polyinference run-agent` for one task or `polyinference run-agents` for a concurrent batch.

| File | Responsibility |
| --- | --- |
| [graphs.py](../../src/polyinference/general_agents/graphs.py) | Four public `StateGraph` designs and their `AgentIO` context protocol. |
| [os_v1.py](../../src/polyinference/general_agents/os_v1.py) | Bind graph model/lookup requests to V1 processes, durable effects and artifacts. |
| [__init__.py](../../src/polyinference/general_agents/__init__.py) | Export graph builders and context for external LangGraph callers. |
| [general-agents.v1.json](../../examples/general-agents.v1.json) | OS-only `RuntimeConfig` with raw local and GPT-6.1 Sol via the Codex ChatGPT subscription. |

| Design | LangGraph path | Roles | Source pattern |
| --- | --- | --- | --- |
| `simple` | Bounded decide → optional lookup → observe → answer | General model plus read lookup | Anthropic's bounded tool-using agent loop |
| `supervisor` | Plan 1–3 subtasks → local worker for each → synthesize | Cloud planner/synthesizer, local worker | Orchestrator–workers |
| `research` | Plan evidence questions → lookup and local extraction → cited report | Cloud lead/reporter, local extractor | Multi-agent research lead/worker, restricted to supplied documents |
| `writer` | Set criteria → local draft → cloud evaluate → at most one local revision | Cloud planner/evaluator, local drafter | Evaluator–optimizer |

The source designs are [Anthropic's building-block patterns](https://www.anthropic.com/research/building-effective-agents)
and [multi-agent research account](https://www.anthropic.com/research/multi-agent-research-system).
They describe patterns, not tested performance for these PolyInference implementations.
The research graph copies the lead/worker *shape*, with serial workers and a bounded
supplied corpus. The writer is the fourth design because the request listed three
categories while asking for four agents. No agent promises a quality gain without
qualification on its target models and tasks.

## Run

Edit `examples/general-agents.v1.json` for your raw-text local endpoint and
a **fresh** state directory per task or batch. The example uses GPT-6.1 Sol
through the Codex ChatGPT subscription. Authenticate first with `codex login`.
You may also configure a compatible raw-text Cloud endpoint. The three
multi-level designs require distinct bindings declared `inference_location`
`local` and `cloud` in the ordinary profile. The explicit Haiku stand-in uses
cloud inference and must also satisfy cloud placement policy.
`repository` field is required by V1 settings but the path is not opened. No Git,
checks, source writes, native tool calls, package install or local model startup is
part of these programs. The CLI takes the task as text and optionally a JSON object
of source ID → document text:

```bash
polyinference run-agent examples/general-agents.v1.json simple "Summarize the supplied notes" --documents notes.json
polyinference run-agent examples/general-agents.v1.json supervisor "Explain the tradeoffs"
polyinference run-agent examples/general-agents.v1.json research "What do the supplied records show?" --documents notes.json
polyinference run-agent examples/general-agents.v1.json writer "Draft a concise project update"
```

Successful invocations produce JSON with `answer` and an artifact reference. A
repeated completed invocation replays settled effects. A paused or uncertain
process remains held for operator inspection; this runner has no generic Resume.
Use a new state directory for new input or changed graph/configuration. `research`
searches only supplied documents; it has no browser or external search. Its citation
instructions ask for source IDs but there is no automatic claim verification.
The simple agent also uses only that lookup. The corpus is limited to 64 documents
and 128 KB. Each query returns at most three excerpts of 2,000 characters, chosen
to cover query terms within each selected document.

## Concurrent batches

`polyinference run-agents CONFIG MANIFEST [--sim-haiku]` runs a JSON array of
invocations on one kernel. Each entry has a unique `id`, `design`, `task`,
optional `documents` object and optional `binding` for Simple. For example:

```json
[
  {"id":"research-notes","design":"research","task":"Which result was reproduced?","documents":{"record":"The second run reproduced the result."}},
  {"id":"quick-check","design":"simple","binding":"cloud","task":"Summarize the notes","documents":{"notes":"The comparison control passed."}}
]
```

Use a fresh state directory for a different manifest or configuration. Set
`max_workers` to at least the number of entries. All entries share the configured
kernel budget and endpoint slots. An invocation owns its checkpoint, processes,
effect identities, result and corpus grant. Results arrive as an array with one
entry per invocation; CLI exit status is nonzero if any invocation fails.
An identical completed batch can be read from its saved state without submitting
new inference. A paused or uncertain effect needs operator inspection.

`--sim-haiku` uses the remote Claude Haiku 5.5 stand-in at the local role.
Both model bindings then use cloud-hosted inference.

Research states its 500-character question limit and permits one corrected
plan after a settled invalid reply. A correction uses its own journaled step.

## V1 adaptation and difficulty

The pure graphs pass `AgentIO` through public LangGraph runtime context. The V1
adapter creates one static-role OS process per model/tool step, so a cloud node
cannot impersonate a local process. It creates immutable `ModelQuery` or typed
`CapabilityCall` intents with stable step IDs, saves them before execution, and
uses the OS journal for replay, grants, budgets, deadlines and result artifacts.
The only tool is a read-only `sources.lookup` capability over the supplied corpus.
The graph uses the OS SQLite checkpointer; no LangGraph internals are patched.
The shared GPT‑6.1 Sol binding uses a tool-free native `AgentJob`. The
adapter pins a subscription-only protocol with an empty private working
directory and a typed text envelope. It unwraps that envelope into the
graph's existing text contract. Raw endpoints continue to use
`ModelQuery`, and document lookup is a separate capability effect.
For Anthropic model queries, the adapter delegates sampling to the provider.
The Haiku stand-in sends a streaming Messages request with a 32,000-token
output ceiling, a top-level system instruction and a final user message.
Anthropic documents the removal of legacy sampling fields and the default
adaptive thinking behavior in its [Haiku 5.5 migration guide](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide).


| Modification | Difficulty | Reason |
| --- | --- | --- |
| Pass `model` and `lookup` through graph context | Low | Public `context_schema` and async nodes suffice. |
| Convert text decisions to V1 effects | Moderate | V1 raw adapters have final text, not native typed tool calls; strict JSON and a brokered lookup replace stock `ToolNode`. |
| Keep cloud/local roles and replay stable | Moderate | V1 pins a role per process and an intent per operation; the adapter creates serial step processes and immutable requests. |
| Resume arbitrary interrupted graphs or native tool agents | High, outside this implementation | V1 has no generic graph activation or typed chat/tool-turn adapter. Paused/uncertain effects require operator reconciliation; stock `create_agent` cannot be dropped in unchanged. |

The graph driver itself runs in trusted application Python; every model and lookup
effect enters OS V1. This is not an isolation boundary for arbitrary third-party
Python plugins. The CLI is the supported entry; the current UI remains the coding
application UI. The adapter supports whole-invocation replay for settled effects,
not generic human interrupts or independent multi-turn chat sessions. It executes
workers serially because V1 permits one active top-level effect per process.

## Verification

`tests/test_general_agents.py` runs all four pure graphs with scripted replies
and all four through the real OS journal and process boundary. The OS tests
substitute an in-memory LangGraph saver because this host's async SQLite
connection stalls; persistent graph checkpoint recovery is therefore unverified.
These are shape and boundary checks, not model-quality evaluations. No local
inference or live cloud call was made. See `development-docs/FIXES.md#fix-0192`
for exact results and host limits.

A four-invocation regression uses the real journal and SQLite checkpoints
with scripted providers. It verifies one kernel, endpoint limits, corpus
isolation and replay of a completed batch. The scoped CLI verification
used loopback HTTP for both bindings with scripted responses.
