# Command line and saved credentials

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The CLI loads configuration/environment and invokes application/runtime services for runs and inspection.

| File | Responsibility |
| --- | --- |
| [src/polyinference/cli.py](../../src/polyinference/cli.py) | Argument parsing, saved credential assignments, validate/probe/run/resume/status/export/steer/retry/reconcile/UI commands. |

## Interface and ownership

The installed `polyinference` entry point calls main(). Paths in configuration
resolve from its parent directory. CLI and UI share application/snapshot paths.
Probes make real requests; schema validation does not establish provider readiness.
UI-only --sim-batch N validates 1..16 and passes invocation policy to TestUI;
it does not modify saved credentials or ordinary run/resume configuration.

## Principles to preserve

- Existing environment values outrank private saved credential assignments.
- Parse credentials as data; never execute env files or auto-load repo .env.
- Resume must honor program/config pins and uncertain-effect ownership.
- A noncompleted run is distinguishable by exit status and durable blocker.

## Verification and related reading

[Saved credentials](../../tests/test_saved_credentials.py), [history](../../tests/test_history.py)
and [recovery](../../tests/test_recovery.py).

[CLI guide](../guides/cli.md) · [Credentials](../guides/anthropic-key.md) · [Recovery](../guides/recovery.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
