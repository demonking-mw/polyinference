# Optional application inference simulator

[Modules](README.md) · [Usage](../guides/sim-inference.md) · [Runtime boundary](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md)

| File | Responsibility |
| --- | --- |
| [agent/inference_simulation.py](../../src/polyinference/agent/inference_simulation.py) | Opt-in settings/config subclass, Haiku capacity overlay, shared virtual decoder, seeded fault decisions/cooldowns, provider installation and inspection projection. |

UI --sim-inference reveals per-run controls; normal mode uses ordinary AgentConfig.
Only explicitly simulated runs use SimulationAgentConfig.inference_simulation.
CLI execute reinstalls the adapter after opening the kernel and before agent work;
load_config recognizes the saved block for exact resume/recovery. New normal launches
retain their schema, canonical configuration pin and original client. No generic OS
setting, agent planning policy or mandatory simulation dependency is added.

The application installs SimulatedHTTPInference on the local lane. It inherits
HTTP preparation/normalization/safety settings and implements the optional trusted
generate_operation(request, messages, max_output, prepared=...) adapter hook.
Kernel dispatch applies normal grants, limits, budget/spend checks, admission
and the original deadline. The adapter retains a separate real transport budget (lifecycle.total_seconds when
selected, otherwise timeout_seconds); synthetic pacing never proves provider progress. Generic
terminal_call cancels/retrieves terminal evidence without dropping exceptions during
Python 3.10 cancellation; default adapters retain their original invocation path.

SharedDecoder divides one nominal TPS budget between active virtual decoders,
advancing monotonic credits before membership changes. Average seeded speed factors
vary aggregate capacity within configured jitter. Slots remain held through
prefill/stalls/virtual decoding; unfinished remote calls also prevent delivery.
Buffered responses can cause conservative timing: remote token completion is opaque.
No timer task, storage transaction or shell/verification lease spans a sleep.

The simulation/inference/ record namespace retains:

- config: immutable simulator version and effective settings, including seed.
- decision/OPERATION: immutable fault, speed, stall and restart decisions.
- server: mutable cooldown, atomically published with its incident decision.
- attempt/OPERATION: progress, submitted/injected facts and terminal phase.
- provider/OPERATION: confirmed terminal response artifact before output pacing.

RNG selection hashes version, seed and operation identity; request order does not
consume a shared RNG. Each new retry gets a new identity. Settled OS replay returns
retained effects with no provider call, new fault draw or delay. A coordinator crash
during live or artificial work stays conservatively uncertain; this module does
not auto-reconcile the OS from its diagnostic provider receipt.

Preflight unavailable/restart uses ProviderError(submitted=False). Received empty/
malformed results use ModelResponseError; synthetic cutoff uses IncompleteGeneration.
Actual usage survives discarded visible output. Real provider errors retain their
facts; planned faults count as injected only when applied. Interrupted artificial
waits after terminal evidence are nonretryable known failures; unknown real execution
retains OS ownership/capacity. Cleanup retrieves created task outcomes. Partial output
never executes and no tool/source effect is fabricated. Cloud routing, budgets and
Git policy remain intact.

Inspection projects artifact-free progress to live UI and reads saved records
offline. Real response artifacts use ordinary record inspection/exports and existing
size/retention limits. Settings/seed are run evidence, never a future launch preference.
RuntimeConfig/Endpoint and default AgentConfig serialization are unchanged; changing
a simulated run's settings needs fresh state. VERSION and the immutable config
record pin simulator behavior.

Verification: [simulator regressions](../../tests/test_inference_simulation.py),
[legacy batch](../../tests/test_sim_batch.py), [browser checks](../../tests/ui_start.test.cjs)
and provider/retry/output/UI suites. PC performance/model quality need separate
evidence. Maintain usage, owning guides, navigation and
[FIXES.md](../../development-docs/FIXES.md); see [maintenance](../maintenance.md).
