# Retry an unavailable model

[Configuration](configuration.md) · [OS retries](../modules/retries.md) · [Recovery](recovery.md)

Fresh coding-agent configurations with a native Codex cloud endpoint default to
`gpt-6.1-terra`, effort `high`, with seven subsequent fallback invocations. Choose
another default with the top-level **agent** option:

```json
{
  "default_retry_model": {
    "model": "gpt-6.1-terra",
    "reasoning_effort": "high",
    "fallback_calls": 7
  }
}
```

Set `default_retry_model: null` to disable the agent default. An explicit
`system.cloud.retry_model` overrides it, including explicit null. A primary already
using the alternate is not given a self-fallback. Existing saved runs are unchanged.
Bare RuntimeConfig has **no model default**; its caller can opt in with the same
object at `cloud.retry_model` (or another bound endpoint). The alternate must be
available through the same provider/protocol and support the declared envelope.
The opaque `codex_proxy` adapter rejects this option.

## Seven-call policy

1. A confirmed terminal **provider availability** failure retries the same logical
   request once on the alternate, preserving input/authority and any already-issued
   output-adaptation or caller response-repair feedback.
2. The next **seven logical invocations** use the alternate.
3. The following invocation probes the configured main model and its original effort. Success resets the policy;
   another availability failure opens another seven-invocation window.

Seven is the OS `RetryModel.fallback_calls` default, not an agent constant. Agent
input may override it (1–32); the retry of the failed request is additional to X.

An invocation is an OS model request, not a coding task or a physical transport/
response-repair attempt. All roles on the same endpoint binding share the window;
other bindings are independent. Selection and remaining counts survive restart.
Concurrent requests use durable selection order; an older primary result cannot
erase a newer primary failure. Replay never consumes another slot. A pre-submission
rejection returns its unused fallback slot. Alternate failure ends that retry;
it does not recursively switch back or start another availability retry.

## Authority and evidence

Trusted model capacity/unavailability, HTTP 429/5xx provider rejections and native
provider overload/rate/service diagnostics qualify. Authentication, permission,
quota, malformed output and invalid input retain their ordinary handling.
Lost delivery/native unknown effects still block: availability is not proof of stop.
The alternate uses the same admission lane, capabilities, data policy, context
envelope, inherited accounts, finishing reserves and original logical deadline.
One configured availability attempt is separate from the transport allowance;
it does not refill that allowance, response retries or application recoveries.

For a terminal native failure, the adapter can retain its thread ID and resume that
same thread with the alternate. Persisted tools and completed results remain in its
conversation; only OS-issued fallback intents can use that native thread. Repeated
old tool-call IDs replay their receipts. Changed arguments
for an old ID are rejected. Without that trusted continuation, an effectful native
job cannot be replayed. Provider-side opaque model fallback is disabled on start.
This does not authorize application task replacement or publish partial work.

Inspect `model-selection/`, `model-fallback-state/<binding>` and
`model-fallback/<root>` plus immutable effects, attempted backend and usage records.
The agent still owns semantic continuation, private-source reuse and acceptance.
Current runtime `simple-os/5` requires fresh state; preserve old runs on their frozen source.

[Regression fixtures](../../tests/test_model_fallback.py) cover routing, restart,
native continuation, callback deduplication, budgets, cancellation and deadlines.
They do not prove live model availability or successful product convergence.
