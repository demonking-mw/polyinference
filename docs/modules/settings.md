# Settings and example configurations

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

One OS settings schema, adjacent coding defaults, and explicit application workflow preferences.

| File | Responsibility |
| --- | --- |
| [src/polyinference/system_settings.py](../../src/polyinference/system_settings.py) | Generic RuntimeConfig, endpoint, context and inference safety settings. |
| [src/polyinference/config.py](../../src/polyinference/config.py) | AgentConfig workflow policy plus compatibility exports of OS settings. |
| [src/polyinference/agent/system_settings.py](../../src/polyinference/agent/system_settings.py) | Coding OS defaults and UI provider/resource preset. |
| [examples/agent.mixed.json](../../examples/agent.mixed.json) | Codex senior + Haiku worker sample; 27 sprints and 32k output. |
| [examples/agent.anthropic.json](../../examples/agent.anthropic.json) | Anthropic-only sample with 32k output allowance. |
| [examples/agent.codex.json](../../examples/agent.codex.json) | Brokered Codex sample. |
| [examples/agent.openai.json](../../examples/agent.openai.json) | Raw OpenAI endpoint sample. |
| [examples/agent.gemini.json](../../examples/agent.gemini.json) | Raw Gemini endpoint sample. |

## Interface and ownership

JSON groups OS preferences under `system`; workflow fields stay at the top level.
Legacy flat input remains accepted, but duplicate placements are rejected.
`POLYINFERENCE_LOCAL_BATCH_SIZE` overrides local endpoint admission only.

## Principles to preserve

- Generic runtime defaults must not acquire coding role/phase assumptions.
- Lane names do not prove physical inference location.
- Context reservation must fit input plus output; workers and inflight slots differ.
- Changed configuration/program pins require fresh state; secrets stay external.

## Verification and related reading

[Settings/context cases](../../tests/test_context_safety.py), [UI export assertions](../../tests/test_ui.py)
and [endpoint tests](../../tests/test_endpoints.py). Validate all five examples.

[Complete field/default reference](../../design-docs/simplified-os/AGENT_SETTINGS.md) · [Configuration](../guides/configuration.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
