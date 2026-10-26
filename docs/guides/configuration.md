# Configure a repeatable run

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

All OS settings are configured together in the examples' `system` block. The
[complete OS settings reference](../../design-docs/simplified-os/AGENT_SETTINGS.md)
documents every field, default, context mode and I/O recovery limit. Coding
workflow choices such as `objective` and `max_sprints` stay outside that block.
The bundled agent's OS defaults and UI preferences live together in
[src/polyinference/agent/system_settings.py](../../src/polyinference/agent/system_settings.py).
Legacy flat configuration remains accepted; do not configure the same field in
both locations. The field names below refer to their entries inside `system`
unless they are agent workflow settings.

The UI defaults are useful for a first test. Use a JSON configuration to pin your
own project, permissions, checks and endpoint settings:

```bash
mkdir -p .polyinference
cp examples/agent.mixed.json .polyinference/agent.json
```

UI-only `--sim-batch N` applies a validated invocation overlay after base loading,
overriding the legacy capacity environment variable. It preserves complete custom
Anthropic endpoint fields; other local protocols select the full remote Haiku
preset. New-run config.json records effective values, not a future preference.
See [scope/precedence and recovery](../../codex-haiku-setup.md).
UI --sim-inference additionally reveals per-run fault/pacing controls. Only an
explicitly buggy/slow run saves an application-level inference_simulation block
outside system; absent lifecycle/policy fields preserve legacy serialization.
Saved explicit blocks restore simulation during CLI recovery and keep resolved
capacity. See [settings, precedence and limitations](sim-inference.md).

Edit `.polyinference/agent.json` before running it. The example's repository,
objective and file names are placeholders. At minimum, update these fields:

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

Setup runs prerequisite checks when present, otherwise available task/product
checks for compatibility. Development assignments may select task/product checks,
not prerequisite-only checks. Final completion requires nonempty final criteria
and passing evidence against the exact reviewed tree and current user objective.

Initial setup can discover a combined command for each unconfigured purpose with
`checks.configure {name, argv, purpose, timeout_seconds?, output_paths?}`.
The purpose is `prerequisite`, `task` (default) or `acceptance`. A discovered task
check is never automatically promoted to final acceptance. Selections are pinned
per purpose; workers cannot replace configured criteria or change them after
setup/planning. Reused check names must have identical command definitions.
Use fresh state after this capability-schema change; old runs are not migrated.
The agent must choose checks that exercise the objective: a purpose label alone
cannot turn a weak command into evidence of product behavior.

For example, replace the check with this object inside the `checks` list, using
an interpreter that has your project's dependencies installed:

```json
{
  "name": "tests",
  "argv": ["/absolute/path/to/project-venv/bin/python", "-m", "pytest", "-q"],
  "timeout_seconds": 120
}
```

`repository` and `state_directory` resolve relative to the **configuration file's
parent directory**, not your terminal's working directory. Source file grants
and closure paths resolve relative to the target repository; use POSIX paths
such as `src/example.py`, not Windows paths or absolute file paths. The check
executable runs from the private workspace, so use an absolute executable path
when you need a particular virtual environment.

For a build check, declare project-relative generated directories with
`"output_paths": ["dist"]` (without a trailing slash). Automatic setup selects
these alongside the command. Declared outputs are excluded from source evidence
and commits; tracked and explicitly granted source files always remain source.
`.gitignore` cannot hide a source change. Check selection, including outputs, is
fixed for the run. Installed `node_modules` and private virtual environments are
copied independently across workspace generations when dependency inputs match;
a changed manifest or lockfile invalidates that execution state before the next
command. Dependency copies are private and count against storage limits.

Scope errors report the offending paths, grant, and phase. Before integration,
the worker receives a bounded opportunity to correct its setup or request review;
the runtime retains its work and never expands source authority merely because a
check produced files.



For streaming timings, OS-native versus caller retries and a bounded endpoint
warm-up, see [endpoint lifecycle/testing](endpoint-testing.md). New fields are
opt-in for custom configs; preserve saved configuration pins.

Next: [Budgets and execution settings](budgets.md) includes validation, probes and launch commands. Update configuration docs and module guides after changing settings.

## Integrated reliability branch (2026-10-26)

The agent can configure inference_retry, check_diagnosis, acceptance_criteria,
max_review_reads, max_worker_recoveries and progress_monitor at the top level.
See [settings](../modules/settings.md), [worker recovery](../../design-docs/implementation/WORKER_RECOVERY.md)
and [progress policy](../../design-docs/implementation/PROGRESS_MONITORING.md).
Endpoint supports_temperature and reasoning_effort remain inside local/cloud.
The combined program/state schema requires a fresh run; keep old run evidence.
