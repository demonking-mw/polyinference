# Simulate slower, less reliable local inference

[Documentation](../README.md) · [Launch](launching.md) · [Tester setup](../../codex-haiku-setup.md)

```bash
polyinference ui --sim-inference
```

The flag reveals inference controls before **Start run**. Opening the UI makes no
provider call. Without the flag, controls stay hidden and ordinary configuration,
clients, timeouts, retries and launch payloads retain their existing path.
The flag is UI-only and works with --port, --config, --state and --sim-batch N.

| Mode | Behavior |
| --- | --- |
| 1. Normal | Existing behavior, including any explicit legacy --sim-batch selection; no simulator or extra config field. |
| 2. Normal and buggy | Existing provider speed with injected failures; select batch and bug rate. |
| 3. Slow and buggy | Shared output TPS, startup/prompt delay, variable speed, occasional stalls and injected failures. |

The initial selection is slow and buggy: **30 shared TPS, batch 2, bug rate 5%**.
These are testing assumptions, not measurements of a PC or a particular model.
At 30 TPS, two decoding calls receive approximately 15 TPS each; a remaining call
gets released capacity. Additional requests wait in ordinary OS admission.
Batch accepts 1–16 and configures worker/slot capacity and full-context reservations.
Independent ready tasks and existing Git/task rules still determine occupancy.

TPS must be positive (at most 100000); bug rate accepts 0–100%. A blank seed generates
one for the run. Enter an integer from 0 to 9007199254740991 to select a seed.
Decisions repeat for the same seed, simulator version and operation IDs;
concurrent timing is not a bit-for-bit performance replay. New retries have new IDs.

Expand timing options for startup seconds (default 1.5), estimated prompt TPS (2000),
speed variation (±20%), stall chance (5%), stall duration (3 seconds) and server
restart duration (15 seconds). Startup includes estimated prompt tokens divided by
prompt TPS. Prompt estimates use UTF-8 bytes / 4. Output pacing uses provider output
token counts, falling back explicitly to UTF-8 bytes / 4 when those counts are absent.
Speed varies within the configured range; TPS is the nominal aggregate capacity.

Bug rate means the chance that a new admitted attempt starts an incident while the
simulated server is healthy. Selected incidents are 40% temporary unavailable, 20%
empty response, 15% malformed response, 20% incomplete output and 5% restart.
Unavailability/restart rejects before submission. Output faults discard or truncate
a real terminal response while retaining actual usage and a full diagnostic copy.
A restart also rejects subsequent attempts during its cooldown; already submitted
calls can finish. Therefore affected-attempt rate can exceed the incident rate.

Existing bounded retries, smaller-output recovery and escalation handle these
outcomes. A restart can outlast a retry. Partial output never becomes tool actions;
no source files, permissions or successful tool results are changed to invent bugs.
The network retains its endpoint timeout; artificial pacing can exceed it but stays
within the original operation/process deadline. Cancellation after real completion
ends artificial waiting as a known, nonretryable failure. Interrupted live provider
work stays uncertain and requires ordinary reconciliation.

Active/saved runs display settings, seed, incidents and last reported phases
and virtual token progress. OS admission shows queued requests. **Save run · JSON**
includes settings, durable decisions, progress and real provider response artifacts.
Historical progress is a last observation, not proof that inference is still running.

Simulation applies to the **local lane**, using the existing complete Haiku preset
overlay (custom Anthropic fields survive). Default cloud seniors are unaffected;
custom roles already bound local share simulation. Haiku remains remote, with
actual API costs and reasoning quality. Buffered delivery is delayed; no true token
stream, GPU/KV memory, model-quality degradation or actual server crash is emulated.

Settings live only in each run's config, not future launch preferences. Existing
history/--state is read unchanged. For exact recovery, deliberately pass that saved
config to resume/retry-model; its explicit inference_simulation block reinstalls
the adapter and preserves resolved capacity despite ambient batch overrides. Plain
configs retain their schema and pins. Probes still test the real provider directly.
