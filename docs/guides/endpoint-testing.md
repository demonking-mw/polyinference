# Endpoint lifecycle and testing (v1)

Configuration (`docs/guides/configuration.md`) · UI (`docs/guides/ui.md`) · Runtime boundary (`design-docs/simplified-os/RUNTIME_BOUNDARY.md`)

Choose transport/timings explicitly for cloud or local inference; lane names and
loopback URLs prove neither latency/capacity nor safe replay. Fixtures cover the contract.
The 26 October local Strata test (`docs/temporary/investigations/2026-10-26-local-strata-live-test.md`)
adds real local/native provider and GPU observations, with a failed product outcome;
it does not validate every transport, timing/fault path or full-window capacity.

| UI profile | Connect | First meaningful output | Output idle | Total logical request |
| --- | --- | --- | --- | --- |
| Small cloud | 10s | 180s | 90s | 600s |
| Local inference | 10s | 900s | 300s | 1800s |
| Buffered compatibility | 10s | No progress claim | No progress claim | 600s |

Total time includes queueing, preparation, backoff, output adaptation and every
attempt; the original process deadline can shorten it. Streaming watchdogs count
text/thinking deltas, not pings, headers or lifecycle events. Hidden reasoning is
not retained in telemetry. Output is returned only after a validated terminal
message; partial text/JSON never reaches the agent's action executor.

Anthropic Messages, chat completions and Responses support SSE. Gemini currently
requires explicit buffered mode. A server ignoring a streaming request produces a
protocol failure; there is no hidden resend in buffered mode. Without lifecycle
settings, old endpoints retain their timeout_seconds behavior and strict unknown
execution barrier. Native tool-using jobs retain their existing safety rules.

For JSON configuration, add this inside the selected system endpoint:

```json
"lifecycle": {
  "transport": "sse",
  "connect_seconds": 10,
  "first_output_seconds": 900,
  "idle_seconds": 300,
  "total_seconds": 1800
}
```

OS-native retries use system.model_call_retries (0–3). Bare OS default is one;
fresh coding-agent configs choose two. The agent can declare more at top level:

```json
"inference_policy": {"additional_retries": 1, "replace_undelivered": true}
```

Additional retries range from zero to three and follow the native allowance.
Thus the fresh UI permits initial + two native + one caller retry for eligible
failures. Output adaptation shares these counters, never resets them, and has its
own adaptation limit. Registered response validation, grammar correction and
linked worker recovery have separate agent settings (`docs/guides/agent-reliability.md`).
Every attempt passes grants, cancellation, finishing
reserve, capacity and campaign token/spend admission. Local raw output uses the single
local token pair (`docs/guides/local-token-limits.md`); cloud per-call caps are provider-owned.
Optional model fallback (`docs/guides/model-fallback.md`) handles confirmed provider availability
errors separately: one alternate attempt plus the caller-overridable OS seven-call
window. It retains the same accounts/deadline and does not refill ordinary retries.

Replacing an unknown call requires caller consent and trusted raw generation-only
adapter facts. The original physical execution stays unknown, holds capacity and
conservative token/spend reservations, and its delivery is permanently discarded.
At most one such pending generation per lane is isolated. A second unknown is a
barrier; a one-slot lane cannot submit a replacement until capacity is reconciled.
Isolated pending computation permits independent work, not resource oversubscription.
Late retrieved output may settle physical accounting but cannot become a chosen
answer. Native jobs, tools and external writes retain the strict global barrier.

For the UI procedure and its evidence, see [test or warm up an endpoint](endpoint-probes.md).
