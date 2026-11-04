# Settings and example configurations

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

One OS settings schema, adjacent coding defaults, and explicit application workflow preferences.

| File | Responsibility |
| --- | --- |
| [src/polyinference/os_config.py](../../src/polyinference/os_config.py) | Canonical generic defaults, operational validation ceilings and typed OSTuning; no application policy. |
| [src/polyinference/system_settings.py](../../src/polyinference/system_settings.py) | Generic RuntimeConfig, endpoint, context and inference safety settings. |
| [src/polyinference/config.py](../../src/polyinference/config.py) | AgentConfig workflow policy plus compatibility exports of OS settings. |
| [src/polyinference/agent/system_settings.py](../../src/polyinference/agent/system_settings.py) | Coding OS defaults, UI provider/resource preset and validated machine preference loading. |
| [src/polyinference/agent/local_provider.py](../../src/polyinference/agent/local_provider.py) | Derive Strata startup context from the local token pair, retaining the previous launch file; opt-in UI bootstrap starts/reuses a named Strata runtime, checks live capacity and returns an identity-guarded cleanup handle only for a new instance, with provider-side process-death supervision. |
| [scripts/settings_docs.py](../../scripts/settings_docs.py) | Generate/check exact exported settings schemas and nested defaults. |
| [docs/settings-schema.json](../settings-schema.json) | Generated current RuntimeConfig/AgentConfig schemas; check with the activated environment. |
| [examples/agent.mixed.json](../../examples/agent.mixed.json) | Codex senior + Haiku worker sample; 27 sprints, streaming and one local input/output token pair. |
| [examples/agent.anthropic.json](../../examples/agent.anthropic.json) | Anthropic streaming sample with the same canonical local pair. |
| [examples/agent.codex.json](../../examples/agent.codex.json) | Brokered Codex sample. |
| [examples/agent.openai.json](../../examples/agent.openai.json) | Raw OpenAI endpoint sample. |
| [examples/agent.gemini.json](../../examples/agent.gemini.json) | Raw Gemini endpoint sample. |

## Interface and ownership

JSON groups OS preferences under `system`; workflow fields stay at the top level.
Legacy flat input remains accepted, but duplicate placements are rejected.
`system.cloud_agent_timeout_interrupt` defaults false in canonical RuntimeConfig
DEFAULTS and is inherited by AgentConfig; cloud native timeouts warn and continue.
The coding UI preset uses a 1800-second cloud threshold and does not override
the OS false default. Set true for interruption; raw/local calls, explicit cancellation and original
deadlines remain bounded. See [timeout behavior](../guides/os-tuning.md).
Operational buffer/retention controls use `system.tuning`;
[central tuning](../guides/os-tuning.md) explains precedence, fresh-state rules and the
[per-file audit](../os-config-inventory.md).
Agent-only prerequisite_checks and acceptance_checks stay at top level; legacy
checks remain combined task/final criteria unless acceptance_checks overrides them.
`POLYINFERENCE_LOCAL_BATCH_SIZE` overrides local endpoint admission only, unless
an explicit UI --sim-batch N invocation resolves capacity itself. The generic
validation context can skip that legacy overlay; system views reflect resolved
values without rereading ambient overrides. No simulation flag is serialized.
The coding settings module owns the complete Haiku factory and pure simulation
overlay (worker binding/cap, slots, full-context reservations), preserving custom
Anthropic fields and other providers/bindings. OS admission remains generic.
The optional [application simulator](inference-simulation.md) uses
SimulationAgentConfig for enabled buggy/slow runs; its saved inference_simulation
block pins settings/seed for recovery. RuntimeConfig has no simulator policy.
Absent Endpoint.lifecycle and agent inference_policy fields are omitted. Cloud endpoint context-token
caps are absent. Legacy token fields migrate to system.local_token_limits; see
[one local pair and provider startup](../guides/local-token-limits.md). --sim-inference is a UI invocation flag.

Optional Endpoint.lifecycle selects explicit transport/connect/first-output/idle/
total timing. The coding application chooses profiles; bare runtime fields contain
no cloud/local timing presets. AgentConfig.inference_policy is an application preference;
local_token_limits alone configures local input/output tokens. Cloud per-call token limits belong to the provider. See [testing profiles and defaults](../guides/endpoint-testing.md).

The UI preset optionally overlays machine local endpoint/token/worker/Strata settings;
see [configuration precedence](../guides/configuration.md). Optional agent
local_strata_profile enables [automatic UI startup](../guides/launching.md). A declared local Anthropic
endpoint selects the remote preset when explicit simulation is requested.

## Principles to preserve

- Generic runtime defaults must not acquire coding role/phase assumptions.
- Lane names do not prove physical inference location.
- Context reservation must fit input plus output; workers and inflight slots differ.
- Changed configuration or incompatible program pins require fresh state; the
  exact graph-only Resume migration preserves the configuration. Secrets stay external.

## Verification and related reading

[Settings/context cases](../../tests/test_context_safety.py), [UI export assertions](../../tests/test_ui.py)
and [endpoint tests](../../tests/test_endpoints.py). Validate all five examples.

[Complete field/default reference](../../design-docs/simplified-os/AGENT_SETTINGS.md) · [Configuration](../guides/configuration.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.

## Reliability settings

Top-level `inference_retry`, `check_diagnosis`, `acceptance_criteria`,
`max_review_reads`, `max_worker_recoveries`, `max_cloud_recoveries` and
`progress_monitor` are agent policy.
`max_review_reads` defaults to 16 ranges per senior invocation (0–16); each proposal still allows eight.
The planner receives the configured, used and remaining allowances on every message.
Their defaults, ranges and recovery interactions are in the
[agent reliability reference](../guides/agent-reliability.md).
Endpoint supports_temperature defaults true; unsupported explicit sampling rejects.
Native reasoning_effort defaults medium; the turn overrides command-line startup.
The UI launcher supplies no conflicting low-effort override.
Agent `default_retry_model` selects the native cloud alternate (Terra/high/seven).
Generic Endpoint.retry_model is optional with no OS default. Explicit null disables
and survives serialization; see [fallback configuration](../guides/model-fallback.md).
Endpoint.input_token_count_path opts raw endpoints into same-provider measurement.
System max_model_request_bytes separates the byte ceiling from token allowances;
null uses the canonical 4 MiB request ceiling. See [measurement](../guides/context-measurement.md).
Optional system.data_policy constrains processes/replacements; ProcessSpec can narrow it.
Constrained endpoints need declared location. Fresh state pins these contracts.
