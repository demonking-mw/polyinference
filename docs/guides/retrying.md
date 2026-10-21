# Explicit model and delivery recovery

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

Known stopped model failures pause the agent with their structured diagnostics.
After correcting the reported problem, explicitly recover a task without repeating
its private edits:

```bash
polyinference retry-model /absolute/path/to/agent.json TASK_ID --reason "Corrected the provider request"
```

Recovery creates a new operation linked to the original failure. Ordinary replay
still returns the original result. Unknown execution requires reconciliation first.
Configuration and program version pins still apply; an old run from a different
implementation is not silently migrated by this command. Start a fresh run for
incompatible versions. Recovery attempts and repeated permanent failures are bounded
by `max_model_recoveries` and `max_repeated_model_failures` (both default to 2).
For a paused plan that needs revised instructions, queue them with `polyinference
steer STATE "instructions"` and invoke `polyinference resume CONFIG` to continue.

If accepted-file delivery stops because the destination changed, restore or resolve
that destination and explicitly retry delivery:

```bash
polyinference retry-output /absolute/path/to/agent.json --reason "Resolved the output conflict"
```

This checks that acceptance is still current and retries only file delivery; it
does not rerun the models. An original failed operation remains immutable.



Also read [limits and uncertainty](recovery.md) and the [OS runbook](../../design-docs/simplified-os/RUNBOOK.md).
