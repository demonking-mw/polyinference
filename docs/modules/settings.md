# Settings and example configurations

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
deadlines remain bounded. See timeout behavior (`docs/guides/os-tuning.md`).
Operational buffer/retention controls use `system.tuning`;
central tuning (`docs/guides/os-tuning.md`) explains precedence, fresh-state rules and the
per-file audit (`docs/os-config-inventory.md`).
Agent-only prerequisite_checks and acceptance_checks stay at top level; legacy
checks remain combined task/final criteria unless acceptance_checks overrides them.
`POLYINFERENCE_LOCAL_BATCH_SIZE` overrides local endpoint admission only, unless
an explicit UI --sim-batch N invocation resolves capacity itself. The generic
validation context can skip that legacy overlay; system views reflect resolved
values without rereading ambient overrides. No simulation flag is serialized.
The coding settings module owns the complete Haiku factory and pure simulation
overlay (worker binding/cap, slots, full-context reservations), preserving custom
Anthropic fields and other providers/bindings. haiku_token_limits supplies the application
96000-input/32000-output preset for fresh Haiku UI runs and complete endpoint replacement;
explicit remote Anthropic pairs, machine preferences and generic OS defaults remain authoritative.
OS admission remains generic.
The optional application simulator (`docs/modules/inference-simulation.md`) uses
SimulationAgentConfig for enabled buggy/slow runs; its saved inference_simulation
block pins settings/seed for recovery. RuntimeConfig has no simulator policy.
Absent Endpoint.lifecycle and agent inference_policy fields are omitted. Cloud endpoint context-token
caps are absent. Legacy token fields migrate to system.local_token_limits; see
one local pair and provider startup (`docs/guides/local-token-limits.md`). --sim-inference is a UI invocation flag.

Optional Endpoint.lifecycle selects explicit transport/connect/first-output/idle/
total timing. The coding application chooses profiles; bare runtime fields contain
no cloud/local timing presets. AgentConfig.inference_policy is an application preference;
local_token_limits alone configures local input/output tokens. Cloud per-call token limits belong to the provider. See testing profiles and defaults (`docs/guides/endpoint-testing.md`).

The UI preset optionally overlays machine local endpoint/token/worker/Strata settings;
see configuration precedence (`docs/guides/configuration.md`). Optional agent
local_strata_profile enables automatic UI startup (`docs/guides/launching.md`). A declared local Anthropic
endpoint selects the remote preset when explicit simulation is requested.

## Principles to preserve

- Generic runtime defaults must not acquire coding role/phase assumptions.
- Lane names do not prove physical inference location.
- Context reservation must fit input plus output; workers and inflight slots differ.
- Changed configuration or incompatible program pins require fresh state; the
  exact graph-only Resume migration preserves the configuration. Secrets stay external.

## Verification and related reading

[Settings/context](../../tests/test_context_safety.py), [UI](../../tests/test_ui.py)
and [endpoints](../../tests/test_endpoints.py) cover settings and provider behavior.

Read the field tables in `design-docs/simplified-os/AGENT_SETTINGS.md` and the
agent policy settings in `docs/guides/agent-reliability.md`. Use
`docs/guides/configuration.md` to configure a fresh run.
