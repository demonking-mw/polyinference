# Budgets and command execution

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

Additional settings worth reviewing:

| Setting | Effect |
| --- | --- |
| `prepare_repository: true` (coding default) | Create missing project directories, initialize Git at the selected actual project when needed, and run specialist setup before planning. Legacy isolated mode uses its private store. Known setup/preparation failures reach the agent for bounded repair. |
| `base_branch` | Pin an existing branch through the coding agent's Git policy. Default in-place runs otherwise select/create their integration branch from actual HEAD, subject to user instructions. |
| `write_scope` | `explicit` restricts development to file grants; `project` allows task grants anywhere in the selected project directory, including new files. |
| `shell_execution` | `disabled`, `trusted` or `bubblewrap`. Default UI and mixed example use `trusted`. |
| `check_execution` | Independently enables configured checks using `trusted` or `bubblewrap`. Generic default is `disabled`, which yields unavailable check evidence. |
| `senior_development_fraction` | Default `0.1`: target share of development tasks assigned to the specialist. |
| `max_workers` | Concurrent started workers; UI default is 1, generic config default is 2. |
| `POLYINFERENCE_LOCAL_BATCH_SIZE` | Environment override for local-lane `max_inflight` (1–32); pinned at startup. Use 1 for a cloud API substitution experiment. |
| `control_token_reserve` | Parent token allowance reserved for control processes; the coding agent reserves 32,000 for planning/review. The former `review_token_reserve` input spelling is accepted. |
| `run_spend_budget_microusd` | Optional estimated run cost bound; requires an explicit endpoint token-price estimate. |
| `max_sprints` | UI/mixed example use 27 sprints and up to 81 senior queries; generic config default is 8 sprints. |
| `limits` / `run_token_budget` | Per-process allowances, final-phase reserves and parent token allowance. Set them before starting. |

**`trusted` shell/check execution runs code on your host.** Workspace-relative
working directories and post-run scope checks are not an OS security sandbox.
Use it for projects and commands you trust. The optional `bubblewrap` mode needs
`bwrap` installed and a compatible Linux environment; this backend has not been
validated by the live-provider checks. Shell scripts run in a bounded foreground
process group with captured output and a timeout; background services are outside
this placeholder's tool profile. Shell tools receive a minimal environment rather
than inheriting provider credential variables.

Validate, optionally probe both providers, then launch the UI with your config:

```bash
polyinference validate-config .polyinference/agent.json
polyinference probe .polyinference/agent.json --endpoint local
polyinference probe .polyinference/agent.json --endpoint cloud
polyinference ui --config .polyinference/agent.json
```

Validation checks the schema, not authentication, model availability or the
project's test environment. Each probe sends one small real request without
starting a project run; it does not prove the entire coding/tool workflow works.
The UI uses your configuration as its template, but still gives every **Start run**
click a new state directory under `.polyinference/ui/runs/`.

Related: [Configuration](configuration.md) · [OS settings](../../design-docs/simplified-os/AGENT_SETTINGS.md).
