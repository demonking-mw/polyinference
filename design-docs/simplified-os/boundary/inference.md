# Context preparation and output recovery

## Context preparation and output recovery

The OS schema and all exported settings are documented together in
`design-docs/simplified-os/AGENT_SETTINGS.md`. Definitions live in
`system_settings.py`, with generic values/operational bounds in `os_config.py`;
the coding agent's defaults and UI choices live together in
`agent/system_settings.py`. JSON examples group OS preferences under `system`.
The coding UI's invocation-only --sim-batch N overlay owns provider selection and
worker/slot/reservation sizing. Generic validation supports resolving capacity
without rereading the legacy environment override; the OS receives ordinary
validated settings. Admission has no Claude-specific scheduling or Git policy.

UI --sim-inference additionally enables an application-installed raw HTTP adapter
for optional pacing/fault injection, documented in the
simulator guide (`docs/modules/inference-simulation.md`). Only explicit
SimulationAgentConfig runs carry its settings; normal AgentConfig/RuntimeConfig
pins and default provider paths are unchanged. Trusted HTTPInference subclasses
may implement generate_operation(request, messages, max_output, prepared=...).
Generic dispatch retains admission, grants, budgets, completion checks and the
original deadline; the adapter owns transport timeout and test service latency.
terminal_call retrieves terminal cancellation evidence before settlement. This
adds no generic OS simulator setting, GPU scheduler or coding recovery policy.
Known provider completion may end an artificial wait safely; a live disconnect
remains uncertain. Diagnostic simulator receipts do not auto-reconcile active work.

`runtime/context.py` measures the known final adapter request. Hard input/output
bounds, completion checks, effect certainty and receipts always apply. Optional
`auto_deal_context` allows whole optional groups to be omitted; independently
optional `auto_compaction` permits derived summaries only for explicitly eligible
blocks. Runtime defaults can be overridden per process and request. Manual,
automatic and hybrid agents use the same resource and authority guards. Original
memory/artifacts are immutable, summary calls inherit the same binding/grants,
and canonical memory remains agent-owned.
The read-only OS Memory / context drawer joins exact operation IDs to retained
original/prepared views and receipts. Retry provenance groups caller attempts;
compaction helpers remain separate. Live and saved node prompts label their
origin and expose original/native observations separately. Prepared bytes and
dispatch markers never establish remote receipt, termination or hidden state.

Confirmed output cutoffs and detectable completed overages use bounded OS
smaller-response recovery under the declared protocol. Feedback is remeasured;
new intents are charged without rewriting original failures. Unknown termination
requires reconciliation; native jobs with brokered effects are not blindly
replayed. Generic feedback preserves the caller's declared protocol and asks for
smaller visible response content, including for plain-text callers (FIX-0085).
Native hard generation-token limits remain unsupported and can be made
a pre-submission rejection through the strict enforcement requirement.

The agent still owns block semantics, canonical memory, grammar correction,
meaningful task/output units and acceptance. The coding agent separately retains
authorized interrupted edits under `coding/interrupted/`, exposes
`preserved_source_ref`, and accepts explicit `resume_from` reuse after scope and
base-conflict checks. This does not introduce Git policy into the OS.
