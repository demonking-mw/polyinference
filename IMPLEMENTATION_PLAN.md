# Agent implementation plan

The current authority is `design-docs/langgraph-agent`, the simplified OS contracts,
the merged execution diagram and `design-docs/INTEGRATION_AUDIT.md` (A1–A9).
Historical research informs the implementation without expanding the placeholder OS.

1. Package the existing wire 2.0 and workspace contracts as a versioned SDK. Keep
   graph state at 2.1, pin program/prompt hashes, and use public LangGraph APIs.
2. Implement three graphs: deterministic sprint controller, reusable phased coding
   worker, and typed senior query. Keep application policy above generic ports.
3. Supply a small standalone runtime: static endpoint bindings, direct file tools,
   configured checks, SQLite records/effect journal, artifacts, persistent graph
   checkpoints, private workspaces, and shell/verification exclusion. No dynamic
   routing, MCP service, memory tiers, or model server implementation.
4. Support raw OpenAI-compatible/Gemini/Anthropic inference and a distinct Codex native-job adapter.
   Raw inference owns an explicit action/observation loop. Native jobs are submitted
   once per bounded phase; Codex coding jobs use host-brokered callbacks. Opaque
   native coding jobs fail negotiation. Senior jobs can use app-server or an
   explicitly scoped read-only proxy.
5. Exercise real Git workspaces and local HTTP/RPC fixtures: concurrent workers,
   changed heads, all verdicts, exact-tree evidence, review/steering races, replay,
   interrupted effects, budget exhaustion, scoped deltas, and final acceptance.
6. Document installation, endpoint configuration, runnable examples, adapter swap
   points, supported recovery, and the distinction between fixture and live tests.

The runtime will preserve the original private delta, require a post-merge model
turn, publish every assessed verdict with its unresolved report, and independently
check the reviewed final tree. Unknown effects remain visible and are never
automatically resubmitted. Required guarantees fail closed rather than being
represented by prompts.

Implemented and verified. The user's audit export is preserved in
`design-docs/implementation/user-agent-review.json`; its decisions are mapped to
the code in the implementation notes. See `design-docs/implementation/VALIDATION.md`
for the 64 covered tests, focused final checks and original design validators.

Codex CLI 0.163.0 passed a complete subscription-backed coding task. Claude's
native API is implemented and fixture-tested; live completion awaits replacement
of the supplied placeholder credential. See
`design-docs/implementation/PROVIDER_SETUP.md` for setup and live evidence.
Other provider deployments and hardware performance remain unverified.
