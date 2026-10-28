# Settings and example configurations

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

One OS settings schema, adjacent coding defaults, and explicit application workflow preferences.

| File | Responsibility |
| --- | --- |
| [src/polyinference/system_settings.py](../../src/polyinference/system_settings.py) | Generic RuntimeConfig, endpoint, context and inference safety settings. |
| [src/polyinference/config.py](../../src/polyinference/config.py) | AgentConfig workflow policy plus compatibility exports of OS settings. |
| [src/polyinference/agent/system_settings.py](../../src/polyinference/agent/system_settings.py) | Coding OS defaults and UI provider/resource preset. |
| [scripts/settings_docs.py](../../scripts/settings_docs.py) | Generate/check exact exported settings schemas and nested defaults. |
| [docs/settings-schema.json](../settings-schema.json) | Generated current RuntimeConfig/AgentConfig schemas; check with the activated environment. |
| [examples/agent.mixed.json](../../examples/agent.mixed.json) | Codex senior + Haiku worker sample; 27 sprints, streaming and a 4096 target inside the 32k output ceiling. |
| [examples/agent.anthropic.json](../../examples/agent.anthropic.json) | Anthropic-only streaming sample with a smaller target inside its 32k ceiling. |
| [examples/agent.codex.json](../../examples/agent.codex.json) | Brokered Codex sample. |
| [examples/agent.openai.json](../../examples/agent.openai.json) | Raw OpenAI endpoint sample. |
| [examples/agent.gemini.json](../../examples/agent.gemini.json) | Raw Gemini endpoint sample. |

## Interface and ownership

JSON groups OS preferences under `system`; workflow fields stay at the top level.
Legacy flat input remains accepted, but duplicate placements are rejected.
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
Absent Endpoint.lifecycle and agent inference_policy/model_output_target_tokens
fields are omitted from serialization. --sim-inference is a UI invocation flag.

Optional Endpoint.lifecycle selects explicit transport/connect/first-output/idle/
total timing. The coding application chooses profiles; bare runtime fields contain
no cloud/local presets. AgentConfig.inference_policy and model_output_target_tokens
are top-level application preferences. See [testing profiles and defaults](../guides/endpoint-testing.md).

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
Their defaults, ranges and recovery interactions are in the
[agent reliability reference](../guides/agent-reliability.md).
Endpoint `supports_temperature` defaults to true and rejects an explicit unsupported
sampling request. `reasoning_effort` defaults to medium and is sent on native turns;
the turn field takes precedence over a command-line startup default.
The UI launcher no longer supplies a conflicting low-effort override.
Agent `default_retry_model` selects the native cloud alternate (Terra/high/seven).
Generic Endpoint.retry_model is optional with no OS default. Explicit null disables
and survives serialization; see [fallback configuration](../guides/model-fallback.md).
Optional `system.data_policy` constrains every process/replacement; narrower
ProcessSpec policies remain enforceable. Explicit endpoint location is required
to satisfy a local-only/cloud-only constraint. Fresh state pins these contracts.
