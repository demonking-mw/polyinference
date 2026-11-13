# One local input/output token pair

Configuration (`docs/guides/configuration.md`) · Context measurement (`docs/guides/context-measurement.md`) · OS settings (`docs/modules/settings.md`)

Configure the local worker lane once, including when a Claude API endpoint stands
in for a local model:

```json
{
  "system": {
    "local_token_limits": {"input_tokens": 49152, "output_tokens": 16384}
  }
}
```

This machine's UI preference uses 114688 input + 16384 output = 131072 (128K),
one worker/slot. The 112K/16K split favors code/tool/history with output room for
reasoning and edits. It is a practical starting choice, not a benchmarked optimum.
Change preferences before a fresh run; old runs retain their saved pair.

Generic OS defaults remain 24000 input and 4000 output tokens. The bundled Haiku
UI preset and mixed/Anthropic examples select 96000 input + 32000 output = 128000.
Explicit simulation that replaces a different/local endpoint with the complete
Haiku preset selects that same pair; an already configured remote Anthropic
endpoint retains its explicit pair. Machine preferences and explicit configurations
remain authoritative, and saved runs keep their original limits.
Changing this pair before a fresh run changes OS input enforcement/packing, provider request output tokens,
worker budget instructions, saved capacity profiles and endpoint admission.
Local context is input + output (65536 in the example); aggregate reservation is
that sum times local max_inflight. Thinking counts toward output.
Provider input counters remain explicit opt-in; absent counters use conservative
byte bounds with disclosed provenance. Serialized request bytes have their own
transport limit and are never interpreted as a second configurable token cap.

Legacy Limits per-call fields and local endpoint context/reservation fields are
compatibility projections. Old input is migrated once when the pair is absent;
an explicit pair overrides stale projections. model_output_target_tokens is an
input-only migration alias, absent from saved configuration and the current schema.
Compaction and readiness probes use the same pair; legacy compaction_output_tokens is retired.
A contradictory alias plus explicit output_tokens rejects. New configuration and
simple-os/6 require fresh state; historical runs retain their original code/pins.

For a local server, [synchronize Strata startup configuration](strata-startup-config.md).

## Cloud agents

The cloud lane has no PolyInference per-call input/output token cap or aggregate
endpoint context-token admission ceiling. Codex receives no token allowance in
its instructions, even when bound to the local worker lane. A provider-completed response is not rejected for cumulative
thread output usage. Native hidden context remains unmeasured. Cloud raw requests
omit optional output-token fields; a provider requiring an explicit output field
must be used through the capped local lane or a provider-managed native harness.

Campaign call/step/time/token/spend accounts, byte transport bounds, authority and
confirmed-termination guards still apply. Provider-reported usage settles accounts;
visible-input reservation is not an upper bound on native hidden consumption.
Uncapped per-call generation is not a provider-enforced campaign dollar quota.

A completed local overage is CompletedBudgetExceeded with complete output retained,
usage scope and budget facts. It is not IncompleteGeneration and receives no
automatic smaller-response replay. Real truncated output remains non-executable.
Candidate validity, checks, reconciliation, publication and acceptance stay separate.

Verification: [incident regressions](../../tests/test_p0_repairs.py) exercise restart,
wire payloads, Strata JSON, uncapped native cloud completion and exact accounting.
