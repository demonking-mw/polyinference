# Measure input capacity without mixing units

[Context module](../modules/context.md) · [Settings](../../design-docs/simplified-os/AGENT_SETTINGS.md) · [Configuration](configuration.md)

`simple-os/5` separates three facts: serialized adapter UTF-8 bytes, measured or
conservatively bounded input tokens, and output reservation. It requires fresh
state; old runs keep their original source, receipts, settings and accounts.

The input token allowance is the minimum of ContextView.maximum_input_tokens,
Limits.max_input_tokens_per_call and endpoint context minus output reservation.
Raw adapters reserve their actual enforced request output cap, including a smaller
explicit runtime/output-tokens value. Native output is not hard-enforced, so its
hard configured allowance stays reserved and hidden native context stays unmeasured.

## Opt into a provider counter

Endpoint `input_token_count_path` is null by default. An explicit relative route
on the same provider can count the **complete prepared request body**, for example:

```json
{
  "system": {
    "local": {
      "protocol": "chat",
      "base_url": "http://127.0.0.1:8099/v1",
      "model": "your-served-model",
      "max_context_tokens": 65536,
      "reserved_context_tokens": 65536,
      "input_token_count_path": "/chat/completions/input_tokens"
    },
    "max_model_request_bytes": 400000
  }
}
```

This is an endpoint fragment, not a complete run configuration. Declare the real
served model and an actually supported counting route before a fresh run. Recent
[llama.cpp counting routes](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md#post-v1chatcompletionsinput_tokens-token-counting)
accept the chat body and return `{"input_tokens": 123}`. Responses/message counting
routes use their corresponding prepared raw body. Server/version support is not
inferred from its URL; older Strata servers may lack this route. There was no new
live-server qualification for this change.

Counting uses the same client, credentials, origin, data constraints and logical
deadline. It generates no model output and grants no tools. Redirects are disabled;
response bytes and count types are bounded. Missing, rejected, timed-out or malformed
counts fall back to the labeled conservative byte bound. This can still underuse
capacity; the OS must not invent a tokenizer ratio or report hidden context as exact.
Native adapters reject this raw counter setting.

## Independent byte ceiling and optional packing

`max_model_request_bytes` is an independent serialized-adapter byte ceiling.
When absent, min(context maximum_input_tokens, max_input_tokens_per_call) retains
the old byte ceiling for compatibility. Raising the explicit byte ceiling does not
raise token/model/output limits. Oversized inputs are never sent to the counter.
Admission and token accounts reserve measured input tokens, or the conservative
bound, plus output. Receipts retain byte counts and token provenance separately.
The inspector displays both; cached preparations reject changed token measurements.

ContextPart.retention_priority is a caller-owned 0–100 hint (default 0). Packing
removes low-priority optional groups first, oldest on ties. Tool pairs stay whole;
required parts remain protected. Recovery headroom applies separately in each
budget's own units. Compaction remains independently opt-in; originals stay immutable.
The OS does not inspect coding meaning. The agent supplies current source/failure
priorities and retains source-backed worker facts; resolved old errors lose priority.

Verification uses fixture counters for 64K sizing, actual output reserve, byte
ceilings, malformed counts and group retention, plus generic processes without Git.
A server-reported count is a provider fact, not independent hardware attestation.
