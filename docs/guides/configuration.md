# Configure a repeatable run

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

All OS settings use the examples' `system` block. The [complete reference](../../design-docs/simplified-os/AGENT_SETTINGS.md) documents every field, default, context mode
and I/O recovery limit. Coding workflow choices such as `objective` and `max_sprints` stay outside that
block. The bundled agent's OS defaults and UI preferences live together in
[src/polyinference/agent/system_settings.py](../../src/polyinference/agent/system_settings.py). Legacy flat
configuration remains accepted; do not configure the same field in both locations. The field names below
refer to their entries inside `system` unless they are agent workflow settings.

Plain UI launches support [persistent machine defaults](launching.md) for local inference.
The machine's 128K coding preference is 114688 input + 16384 output tokens, with
one worker/slot; explicit configs and retained runs keep their own token settings.
UI-owned Strata instances are cleaned up at UI exit, including a provider-side
process-death watcher; separately started/reused runtimes remain separately owned.
Cloud agent jobs default to warning-only endpoint timeouts. Set
`"cloud_agent_timeout_interrupt": true` inside `system` to interrupt instead;
false keeps the same cloud job running. See [OS timeout behavior](os-tuning.md).
Original deadlines and explicit cancellation still apply; use fresh state.

Use a JSON configuration to pin your project, permissions, checks and endpoint settings:

```bash
mkdir -p .polyinference
cp examples/agent.mixed.json .polyinference/agent.json
```

UI-only `--sim-batch N` applies a validated invocation overlay after base loading, overriding the legacy
capacity environment variable. It preserves custom remote Anthropic fields; declared local endpoints and other protocols select Haiku. New-run config.json records effective values, not a future preference.
The bundled Haiku preset uses 96000 input/32000 output tokens; selecting the complete Haiku preset
also selects this pair. Existing remote Anthropic configurations keep their explicit limits.
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
| `local`, `cloud` | Provider protocols, URLs, model IDs, credential variables and concurrency. Local token capacity derives from local_token_limits; cloud has no OS token cap. |

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

`max_review_reads` defaults to 16 total source ranges per senior invocation, with at most eight per
proposal. Every planner message includes current read/correction allowances and planning/process limits;
explicit values and saved configurations retain their original limits.

[Endpoint testing](endpoint-testing.md) covers streaming timings, native/caller retry allowances and
explicit warm-up. [Budgets](budgets.md) covers execution backends, validation and launch commands. Preserve
saved configuration pins. [Model fallback](model-fallback.md) covers agent
`default_retry_model` (Terra/high/seven), endpoint overrides and disabling.

Configure [one local input/output pair](local-token-limits.md) under system.local_token_limits. Its sum
sets local context capacity and drives provider requests, admission and saved capacity views. Cloud agents
have no OS per-call token cap. Request-byte guards and campaign accounts remain independent. Strata launch
JSON can be synchronized with configure-local before restarting the server. Changed pins require fresh state.

For uncommitted delivery, select `repository_mode: "isolated"` before starting; private runtime commits do
not commit the user's branch. Review export status, baseline and conflicts before applying a patch. A
provisional export is not product acceptance. See [exports](exports.md) and the [local Strata
investigation](../../development-docs/local-strata-live-test-2026-10-26.md).
Optional `system.data_policy` sets mandatory run-wide location/destination/classification ceilings.
ProcessSpec can narrow them. Constrained endpoints need explicit `inference_location`; URLs do not attest it.
Static hard classes are supported; unsupported weights or unequal process/runtime limits reject before effects.
See [settings schemas/defaults](../settings-schema.json) and [qualification](qualification.md).

[Central OS configuration](os-tuning.md) owns generic defaults/bounds. Use `system.tuning` for operational
controls; coding presets remain application preferences. See the [per-file inventory](../os-config-inventory.md).
