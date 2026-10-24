# Command line and saved credentials

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The CLI loads configuration/environment and invokes application/runtime services for runs and inspection.

| File | Responsibility |
| --- | --- |
| [src/polyinference/cli.py](../../src/polyinference/cli.py) | Argument parsing, saved credential assignments, validate/probe/run/resume/status/export/steer/retry/reconcile/UI commands. |

## Interface and ownership

The installed `polyinference` entry point calls main(). Paths in configuration
resolve from its parent directory. CLI and UI share application/snapshot paths.
execute(..., resume_request_ref=...) calls ProjectAgent.resume after loading the
saved configuration and validating program compatibility. Coding recovery policy
lives in agent/resume.py; apply_resume remains a compatibility wrapper. CLI resume
CONFIG [--text instructions] records a run-level intent and uses this same service.
Successful activation records resume-outcome/; preparation/failure remains durable.
The agent permits its exact documented predecessor through an audited migration;
arbitrary historical programs/configurations remain incompatible.
Probes make real requests; schema validation does not establish provider readiness.
UI-only --sim-batch N validates 1..16 and passes invocation policy to TestUI;
it does not modify saved credentials or ordinary run/resume configuration.
UI-only --sim-inference reveals opt-in controls. execute installs an application
adapter only for SimulationAgentConfig; load_config recognizes that explicit saved
block for exact recovery without reapplying ambient batch overrides. Plain configs
retain AgentConfig and their original pins. Probes contact the actual provider.
See [simulation ownership](inference-simulation.md) and [usage](../guides/sim-inference.md).

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
