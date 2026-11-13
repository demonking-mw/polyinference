# PolyInference OS V1 and LangChain agents

Reviewed 2026-11-13 on `codex/simple-os-v1`, HEAD `da94312`, using the current
working tree. Status: investigation. No implementation changed. The target is a
trusted Python agent built with LangChain's `create_agent`, running its model
calls and effectful tools through PolyInference. A custom LangGraph is the
comparison baseline. Existing source and historical run state were preserved.

## What already works

The bundled coding application compiles controller, worker and senior LangGraph
graphs. Its own services build `ProcessSpec`, `ContextView`, `ModelQuery` or
`AgentJob`, and `CapabilityCall` intents. `KernelRuntime` supervises registered
async factories, admits effects, meters inference, validates capabilities,
records durable results, and supplies an `AsyncSqliteSaver`. A standalone
program can bypass `AgentServices`, register a typed capability, and return an
artifact without a Git checkout, a file workspace, or coding records. See
`src/polyinference/ports.py`, `src/polyinference/runtime/processes.py`,
`src/polyinference/agent/services.py` and `tests/test_runtime_general.py`.

An offline probe confirmed a Git-free, checkpointed `StateGraph` with a
program-specific text/JSON protocol can run two model turns through the real
HTTP adapter with a mock transport, call a registered read capability between
them, finish with an artifact, and replay all three receipts without repeating
an effect. This is the smallest supported integration today. Using a normal
LangChain provider client and ordinary Python tools inside a driver would run
the Python workflow under the driver deadline while bypassing PolyInference's
model admission, effect accounting, tool grants and receipt replay.

## Compatibility gaps and their owners

| Surface | Observed V1 behavior | Work to support an adapted `create_agent` |
| --- | --- | --- |
| Dependencies | `pyproject.toml` requires Python 3.10+ and pins LangGraph `1.2.16` and SQLite saver `3.1.2`. `requirements.lock` has `langchain-core==1.6.12` and `langgraph-prebuilt==1.1.1`. The WSL test environment has no `langchain` package. | Pin a compatible optional LangChain extra and test the resolved dependency set on Python 3.11+. Check core/graph/checkpointer compatibility before changing the base pins. Current [LangChain package metadata](https://pypi.org/project/langchain/) sets Python 3.11 as the minimum. |
| Process hosting | `ProcessPorts.start` takes an async factory supplied by trusted Python bootstrap. The program and entry point fields record identity. The CLI `execute` creates `ProjectAgent(AgentServices(...))`, and the UI's regular run path uses that runner. `RuntimeConfig` still requires a repository path and both endpoint objects, even if they stand for an unused directory and one effective endpoint. | Put a trusted program runner and an intent builder above the OS. Resolve a pinned factory, register the process and capabilities, compile with the saver, invoke asynchronously, publish artifacts and close the driver. A program manifest, launcher and program-aware inspection can be added to the integration surface. See `runtime/processes.py:115`, `cli.py:80`, `ui.py:155`, and `system_settings.py:129` under `src/polyinference/`. |
| Typed chat and tool calls | `ContextPart` can mark complete tool pairs for packing. `context_messages` still maps call content to assistant text and result content to user text. The raw `ModelQuery` carries a catalog digest and response-schema reference, with no native tool descriptors or `tool_choice`. The raw HTTP path assembles and checks text. Chat tool-call finishes and Responses function calls are rejected. Anthropic rejects tool stops/blocks. The chat SSE assembler keeps only a marker when a tool delta arrives. Gemini requests JSON text. The kernel's result byte check assumes `result["text"]`. | A prompt shim can synthesize `AIMessage.tool_calls` from validated text and encode tool history as text. That is a controlled demonstration with prompt/quality tradeoffs. Native fidelity needs a versioned, provider-neutral chat request/result, plus a `BaseChatModel` adapter implementing async generation and `bind_tools`. Start with one tool-capable buffered provider. Preserve roles, schema/choice, call IDs, arguments, correlated results, stop reason and usage. Measure the actual submitted wire and bound the whole structured output. See `src/polyinference/contracts.py:365`, `runtime/context.py:20`, `runtime/inference.py:352` and `:646`, `runtime/inference_stream.py:101`, and `runtime/kernel.py:1021`. [LangChain messages](https://docs.langchain.com/oss/python/langchain/messages) · [BaseChatModel](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel) |
| Tool authority | The OS already registers typed handlers and checks process grant, schema digest, effect class and optional workspace generation/content before invocation. Native Codex `AgentJob` callbacks reuse the broker through active parent intents. Normal LangChain tools are Python callables. | Provide wrapped tools or async tool middleware that dispatches granted `CapabilityCall`s, then constructs the matching `ToolMessage`. Resolve names, effect classes and digests from the trusted registry. Treat provider tool-call IDs as correlation data and persist stable OS IDs separately. Return known failures as tool errors only where policy allows, and surface uncertain effects as a run blocker. Pure application transforms can remain ordinary Python. See `src/polyinference/runtime/kernel.py:1270` and `:1309`. [Tool middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom) |
| Parallel execution | The kernel rejects a second active top-level effect under one process. Separate registered processes can overlap within OS limits. The installed `ToolNode` executes two calls concurrently. Independent LangGraph branches can also reach model or tool effects concurrently. | Serialize mediated calls per OS process for initial support, including graph fan-out or batching where used. Use separate OS processes only for explicit independently admitted branches with inherited accounts and deadlines. Transparent intra-process parallelism requires a separate OS design for accounting, cancellation, partial settlement and effect ordering. See `src/polyinference/runtime/kernel.py:579` and `tests/test_os.py:39`. |
| Checkpoints and restart | The kernel supplies an async SQLite saver and a separate effect journal. `request_resume` stores an operator signal and optional text. `prepare_resume` reconciles retained evidence. Coding `ProjectAgent.resume` chooses the application continuation. A driver that simply returns from an interrupted graph can be auto-finished by `Processes.start`. | Map graph thread/run/checkpoint identity to an OS process and each model/tool invocation to a durable logical intent. Persist intents before dispatch and reuse them after replay. Detect graph interrupts and record a paused driver before returning. Recreate the pinned graph and resume the same thread only after OS readiness, using `Command(resume=...)` for dynamic interrupts. Generic human input may need structured payloads beyond V1's text signal. A later user turn on the same thread needs an explicit OS process/account lifecycle. See `src/polyinference/runtime/processes.py:12` and `:115`, `runtime/kernel.py:254`, and `agent/resume.py:35`. [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) · [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers) |
| Structured output, streaming and telemetry | Raw paths retain final text, usage and terminal evidence. HTTP SSE observes timing/progress and assembles the terminal response internally. It exposes no typed chunks to the application. Native jobs can use a registered response schema. | Define which LangChain structured-output mode the selected raw adapter supports. Tool-based structured output is application data, while real tool effects require grants. Initially expose completed messages and graph progress. Token/tool-delta streaming later needs a bounded observational channel and terminal validation before any tool runs. Correlate framework traces with OS operation IDs without making traces accounting or authority records. [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output) · [LangGraph streaming](https://docs.langchain.com/oss/python/langgraph/streaming) |
| Models, context and retries | Registered roles bind to configured local/cloud lanes under data policy and uniform limits. V1 has bounded availability fallback, context packing/compaction and retry policy. The isolated-unknown replacement path is restricted to trusted, tool-free raw wires. | Pin the first model and keep LangChain middleware from expanding OS routing, grants or retry allowance. Leave canonical messages with LangChain. Measure history plus schemas in the actual wire, preserve complete tool exchanges, and start with explicit context ownership. Keep structured tool requests on the strict uncertainty path until a supported adapter can attest appropriate execution semantics. See `src/polyinference/runtime/process_policy.py:52`, `runtime/kernel.py:419` and `runtime/context.py:69`. |
| Arbitrary agent packages | Trusted Python shares the host interpreter and can call the filesystem, network and subprocesses outside the broker. The optional command sandbox applies to a command path. It does not contain the Python graph or arbitrary plugins. | An audited in-process adapter can support trusted code. Enforced third-party hosting would need a separate process boundary, broker RPC, credential/network/filesystem policy and supervised lifecycle. Deep Agents backends, arbitrary MCP/provider plugins, embeddings, and remote/distributed runners add integration work if chosen as a target. See `design-docs/simplified-os/DESIGN_REVISIONS.md` R11/R13. [LangChain MCP](https://docs.langchain.com/oss/python/langchain/mcp) |

## Smallest credible compatibility target

Keep the LangChain graph and its prompts. Replace model construction with a
PolyInference chat model, expose selected tools through broker wrappers, and
invoke the graph via a trusted async runner. Use one pinned tool-capable raw
endpoint, text messages plus typed tool turns, serial effects per process,
SQLite checkpoints and final-message delivery. This is a moderate integration
for a single supported profile. Native chat needs runtime and provider-adapter
changes. A text/JSON shim requires mostly application work and is suitable for a
controlled proof. Broad drop-in support for existing LangChain packages is a
larger hosting and compatibility project. The standalone scheduler proposal is
independent of this first milestone.

For a durable runner, OS preparation and process activation are separate steps.
`prepare_resume` records readiness after effect reconciliation, but it does
not move a paused process to ready. `Processes.start` rejects a paused process,
and the bundled application performs its own record transitions. A supported
integration should expose or standardize that guarded activation step instead
of requiring each LangChain application to copy the coding application's record
writes. The runner must retain the original process deadline and budget across
resume. A fresh conversation turn is a separate policy decision from resuming
the same invocation.

An acceptance run should use a real `create_agent` instance, a deterministic
model fixture and a non-coding lookup tool. Its first model response should be a
typed tool-only turn. Verify that the second request contains the correct tool
result and that the final assistant output is delivered. Exercise denial before
handler execution, two calls from one assistant message, restart after the tool
settles and before graph checkpoint advancement, interrupt/resume, deadline and
account continuity, and blocking on uncertain effects. Then qualify a single
real endpoint with supported native tool calling. These are proposed checks.

## Verification

- The offline WSL run of `tests/test_runtime_general.py`,
  `tests/test_capability_boundary.py`, `tests/test_inference_lifecycle.py` and
  `tests/test_os.py` passed 67 tests in 21.57 seconds. Existing fixtures cover
  general processes, broker grants, native callbacks, effect exclusion, replay
  and uncertain execution. They do not run `langchain.agents.create_agent`.
- The buffered chat normalization probe rejected a standard tool-only turn with
  `Non-complete generation: tool_calls`. The SSE assembler retained a marker
  without its ID. A compiled graph using the pinned `ToolNode` started two tools
  concurrently and returned two correctly correlated tool messages.
- The custom `StateGraph` proof used mock HTTP and disposable state. The probe
  replayed inside one live kernel and made no live inference call. A generic
  restart after an effect and before the graph checkpoint remains unverified.
- A static `interrupt_before` probe left a pending node in the SQLite graph
  checkpoint while the direct OS driver finished as `completed`. The OS rejected
  the subsequent resume request because it requires a paused process. Dynamic
  `interrupt()` probes on the installed Python 3.10 stack failed inside LangGraph
  with a missing runnable context, so they did not test the OS resume mapping.
- Documentation generation and `--check` passed on the WSL working tree.
  They cover inventory, navigation and links. The reviewed setup, runtime,
  agent, CLI/UI, settings, design and current task guides still describe the
  shipped behavior. The compatibility target is recorded here as analysis.
- Related decisions are recorded in `development-docs/FIXES.md#fix-0007`,
  `#fix-0022`, `#fix-0032`, `#fix-0111`, `#fix-0117` and `#fix-0183`.
