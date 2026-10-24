# Endpoint lifecycle and testing (v1)

[Configuration](configuration.md) · [UI](ui.md) · [Runtime boundary](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md)

The local lane can serve a small cloud model or genuine local inference. Choose
transport and timings explicitly; neither its name nor a loopback URL proves
latency, capacity or safe replay. This version has offline fixture coverage, not
live provider/GPU validation.

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
"inference_policy": {"additional_retries": 1, "replace_undelivered": true},
"model_output_target_tokens": 4096
```

Additional retries range from zero to three and follow the native allowance.
Thus the fresh UI permits initial + two native + one caller retry for eligible
failures. Output adaptation shares these counters, never resets them, and has its
own existing adaptation limit. Grammar correction and explicit application
recovery remain separate. Every attempt passes grants, cancellation, finishing
reserve, capacity and token/spend admission. Hard output ceilings remain intact;
the smaller target applies to raw queries. Saved explicit values win over defaults.

Replacing an unknown call requires caller consent and trusted raw generation-only
adapter facts. The original physical execution stays unknown, holds capacity and
conservative token/spend reservations, and its delivery is permanently discarded.
At most one such pending generation per lane is isolated. A second unknown is a
barrier; a one-slot lane cannot submit a replacement until capacity is reconciled.
Isolated pending computation permits independent work, not resource oversubscription.
Late retrieved output may settle physical accounting but cannot become a chosen
answer. Native jobs, tools and external writes retain the strict global barrier.

Expand Endpoint testing in the UI, select timings, then click Test endpoint / warm
up. It submits one ordinary 64-token query, with no tools/Git/workspace and no
retries. Opening the page never warms a model. Probes and their journals live
under .polyinference/ui/probes/; a pending/uncertain probe blocks another launch
or probe in that manager. Use the saved generic RuntimeConfig with KernelRuntime.reconcile_stopped and
actual termination evidence before further work; the UI observes settled records.
Restarting the UI does not clear this guard. This
is bring-up tooling, not a shared admission service across independent OS runs.

Inspect inference-progress/<operation> for last output, elapsed time and deadline;
model-retry/<root>/<attempt> records source (native/caller), and retry outcomes
record both counters. effect records retain transport cause/stage, physical
uncertainty and discarded delivery. Save run preserves them; snapshots stay read-only.

Offline tests use deterministic parser fixtures, mock transports, bounded timing
faults and real loopback SSE fixtures. The optional TPS simulator still paces
completed real responses; it does not emulate a provider's streaming decoder or
prove GPU scheduling. Real provider/cold-start tests require a separate explicit
live run. See [fixture coverage](../../tests/test_inference_lifecycle.py).
