# Setup

[Documentation](docs/README.md) · [Setup](setup.md) · [Developer guide](dev-readme.md)

| Requirement | Details |
| --- | --- |
| Operating system | macOS, Linux, or Linux inside WSL. Native Windows is not supported by the POSIX runtime. |
| Python | Python 3.10 or later, including `venv` and `pip`. |
| System tools | Git and Bash; `curl` for the linked Codex installer. |
| Default junior provider | An Anthropic API key with access to the configured model. |
| Default senior provider | Codex CLI installed and signed in on the same macOS/Linux/WSL host as PolyInference. |
| Project tools | Any compiler, interpreter, package manager and dependencies required by your target project's checks. |

The implementation has been exercised on Ubuntu 22.04 in WSL with Python 3.10.12
and Codex CLI 0.163.0. Keep the repository and runtime state on the Linux
filesystem, for example `~/projects/polyinference`, rather than `/mnt/c/...`.
Use Linux paths in the UI, such as `/home/yourname/projects/my-app`.

The UI is packaged with the Python application. It needs no frontend build,
JavaScript package installation or separate development server. Node/npm are only
needed if your target project uses them.

## Choose your environment

- **Linux:** [install Python dependencies](docs/guides/install.md), configure
  [Codex](docs/guides/codex-login.md) and [Anthropic](docs/guides/anthropic-key.md),
  then [launch](docs/guides/launching.md). Linux supports optional bubblewrap.
- **Windows / WSL:** run those same Bash commands inside your Linux distribution.
  Install Codex and credentials inside WSL too; keep source/state on its Linux
  filesystem and use Linux paths. Open the loopback UI in your Windows browser.
- **macOS:** use your package manager for Python and Git, then follow the same
  install/login steps. Select explicitly enabled `trusted` command execution;
  the Linux bubblewrap backend is unavailable.
- **Other model/server settings:** [provider selection](docs/guides/providers.md),
  [repeatable configuration](docs/guides/configuration.md) and the full
  [OS settings reference](design-docs/simplified-os/AGENT_SETTINGS.md).

For serial Codex/Haiku or invocation-only `ui --sim-batch N` experiments, use the
[tester checklist](codex-haiku-setup.md). Simulation uses paid remote requests;
opening the UI does not send a generation request.
Optional `ui --sim-inference` exposes slow/faulty modes before Start; ordinary
launches remain unchanged. See [inference simulation](docs/guides/sim-inference.md).
For remote host recovery and OS deployment details, use the
[OS runbook](design-docs/simplified-os/RUNBOOK.md).

After installation, follow [first run](docs/guides/first-run.md), then
[your project](docs/guides/projects.md). Contributors must read
[developer onboarding](dev-readme.md) and update all affected docs after fixes/features.

