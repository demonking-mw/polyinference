# Command line

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

You can run without the UI using the same configuration and environment:

```bash
polyinference run .polyinference/agent.json
polyinference status .polyinference/my-project-state
```

Run status is printed as JSON. `run` and `resume` exit with status 2 when the run
has not reached `completed`; inspect its blocker and evidence rather than treating
any saved commit as final success.

| Command | Purpose |
| --- | --- |
| `polyinference validate-config CONFIG` | Validate configuration structure. |
| `polyinference probe CONFIG --endpoint local` | Make one readiness request to the worker lane. Use `cloud` for the other lane. |
| `polyinference run CONFIG` | Start/drive a run in the configured state directory. Use fresh state for a new run. |
| `polyinference status STATE` | Inspect application status, task reports, heads and uncertain effects. |
| `polyinference steer STATE 'Updated instructions'` | Record steering for the running coordinator to consume. |
| `polyinference resume CONFIG` | Reopen persisted execution with its pinned configuration and implementation. |
| `polyinference operation STATE OPERATION_ID` | Inspect one journaled operation. |
| `polyinference export STATE OUTPUT.patch` | Export the initial-to-provisional code diff. |
| `polyinference ui --state STATE` | View a persisted run in the UI. |
| `polyinference ui --sim-batch N` | New-run remote Haiku simulation with N workers/slots (1..16), scoped to this server invocation. Works with --port/--config/--state; old state is inspection-only. |

Run `polyinference --help` or `polyinference COMMAND --help` for argument syntax.
`ui --state` imports an existing run for inspection; **Start run** still creates a
new run rather than resuming that imported run.
