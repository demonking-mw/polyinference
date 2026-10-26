# Settings and example configurations

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

One OS settings schema, adjacent coding defaults, and explicit application workflow preferences.

| File | Responsibility |
| --- | --- |
| [src/polyinference/system_settings.py](../../src/polyinference/system_settings.py) | Generic RuntimeConfig, endpoint, context and inference safety settings. |
| [src/polyinference/config.py](../../src/polyinference/config.py) | AgentConfig workflow policy plus compatibility exports of OS settings. |
| [src/polyinference/agent/system_settings.py](../../src/polyinference/agent/system_settings.py) | Coding OS defaults and UI provider/resource preset. |
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
The optional [application simulator](inference-simulation.md) adds a separate
SimulationAgentConfig only for explicitly enabled buggy/slow runs. Its saved
inference_simulation block pins settings/seed for recovery; normal AgentConfig,
RuntimeConfig remains generic; new optional Endpoint.lifecycle and agent inference
policy fields are omitted when absent to preserve legacy serialization. --sim-inference
itself is a UI invocation permission, not a persisted preference.

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

## Integrated reliability branch (2026-10-26)

New top-level agent fields are inference_retry (two maximum physical attempts and
a one-second replacement window), check_diagnosis, acceptance_criteria,
max_review_reads (4), max_worker_recoveries (1), and progress_monitor
(enforce, warn_after=8, escalate_after=12). Progress supports observe/off modes.
Endpoint fields supports_temperature (true) and reasoning_effort (medium) belong
to the generic endpoint schema. Existing grouped system settings and separate
prerequisite/task/acceptance checks retain their ownership.
