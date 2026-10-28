# Configure a repeatable run

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

All OS settings use the examples' `system` block. The [complete reference](../../design-docs/simplified-os/AGENT_SETTINGS.md) documents every field, default, context mode
and I/O recovery limit. Coding workflow choices such as `objective` and `max_sprints` stay outside that
block. The bundled agent's OS defaults and UI preferences live together in
[src/polyinference/agent/system_settings.py](../../src/polyinference/agent/system_settings.py). Legacy flat
configuration remains accepted; do not configure the same field in both locations. The field names below
refer to their entries inside `system` unless they are agent workflow settings.

The UI defaults are useful for a first test. Use a JSON configuration to pin your own project, permissions,
checks and endpoint settings:

```bash
mkdir -p .polyinference
cp examples/agent.mixed.json .polyinference/agent.json
```

UI-only `--sim-batch N` applies a validated invocation overlay after base loading, overriding the legacy
capacity environment variable. It preserves complete custom Anthropic endpoint fields; other local protocols
select the full remote Haiku preset. New-run config.json records effective values, not a future preference.
See [scope/precedence and recovery](../../codex-haiku-setup.md). UI --sim-inference additionally reveals
per-run fault/pacing controls. Only an explicitly buggy/slow run saves an application-level
inference_simulation block outside system; absent lifecycle/policy fields preserve legacy serialization.
Saved explicit blocks restore simulation during CLI recovery and keep resolved capacity. See [settings,
precedence and limitations](sim-inference.md).

Edit `.polyinference/agent.json` before running it. The example's repository, objective and file names are
placeholders. At minimum, update these fields:

| Field | What to set |
| --- | --- |
| `repository` | Absolute host path to the target root, e.g. `/home/yourname/projects/my-app`. |
| `state_directory` | A fresh directory, e.g. `"./my-project-state"`. In this copied config that resolves to `.polyinference/my-project-state/`. |
| `objective` | The full development request and acceptance criteria. |
| `allowed_write_paths` | Exact project-relative writable file names, including intended new files, when using the default `write_scope: "explicit"`. |
| `closure_paths` | Additional project-relative source, manifests, scripts and test files needed in the initial worker view. |
| `checks` | Named task checks. Explicitly supplied legacy checks also serve final acceptance when acceptance_checks is omitted. |
| `prerequisite_checks` | Agent workflow field at top level: environment/setup checks, excluded from product acceptance. Default []. |
| `acceptance_checks` | Agent workflow field at top level: final product checks. Omitted/null retains explicitly configured legacy checks; [] requires setup discovery of final criteria. |
| `local`, `cloud` | Provider protocols, URLs, accessible model IDs, credential variable names and concurrency/context settings. |

`repository` and `state_directory` resolve relative to the **configuration file's parent directory**, not
your terminal's working directory. Source file grants and closure paths resolve relative to the target
repository; use POSIX paths such as `src/example.py`, not Windows paths or absolute file paths. The check
executable runs from the private workspace, so use an absolute executable path when you need a particular
virtual environment.

See [check selection](checks.md) for command examples, setup discovery, generated outputs, dependency state
and task/final verification. Source grants remain enforced even when checks produce files. [Agent
reliability](agent-reliability.md) documents response validation, diagnosis, semantic criteria, linked
replacements and stagnation settings. `max_cloud_recoveries` defaults to 1: eligible stopped local work
transfers to the cloud coding specialist outside normal task-share quota and ordinary recovery depth, with
original accounts/deadlines. Set 0 before a fresh run to disable that route. It requires worker→local and
specialist→cloud bindings; capability manifests do not advertise browser/MCP/service support. Endpoint
`supports_temperature` and `reasoning_effort` remain inside local/cloud. The integrated program requires
fresh state.

[Endpoint testing](endpoint-testing.md) covers streaming timings, native/caller retry allowances and
explicit warm-up. [Budgets](budgets.md) covers execution backends, validation and launch commands. Preserve
saved configuration pins. [Model fallback](model-fallback.md) covers agent
`default_retry_model` (Terra/high/seven), endpoint overrides and disabling.

For mixed native/local runs, size each endpoint from its actual model/server metadata. Context preparation
uses the smaller of the shared input limit and that endpoint's context minus actual raw output headroom.
Optional input_token_count_path counts the complete raw body on the same provider; absent/failed counters
retain a conservative byte/token bound. Separate max_model_request_bytes must also fit. See [measurement
and independent ceilings](context-measurement.md); configured 65,536 capacity alone does not prove utilization. A shared limit sized only for the local lane can unnecessarily stop native
review. Changing a saved limit is not a supported way to rewrite an existing run's pinned configuration or
replenish its accounts.

For uncommitted delivery, select `repository_mode: "isolated"` before starting; private runtime commits do
not commit the user's branch. Review export status, baseline and conflicts before applying a patch. A
provisional export is not product acceptance. See [exports](exports.md) and the [local Strata
investigation](../../development-docs/local-strata-live-test-2026-10-26.md).
Optional `system.data_policy` sets mandatory run-wide location/destination/classification ceilings.
ProcessSpec can narrow them. Constrained endpoints need explicit `inference_location`; URLs do not attest it.
Static hard classes are supported; unsupported weights or unequal process/runtime limits reject before effects.
See [settings schemas/defaults](../settings-schema.json) and [qualification](qualification.md).
