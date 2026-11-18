# Setup

Use macOS, Linux or a Linux distribution inside WSL. Install Python 3.10 or
later with `venv`/`pip`, Git and Bash. Native Windows does not run the POSIX
runtime. In WSL, install and run the tools inside Linux; keep source and state
on the Linux filesystem and enter Linux paths in the UI.

For the bundled cloud senior preset, install and sign in to Codex on the
same host. For the bundled Haiku worker preset, configure Anthropic credentials.
A real local server can replace the stand-in. Install the target project's own
check tools; the bundled PolyInference UI needs no frontend build.
For native Codex on Linux or WSL, put `bwrap` on PATH if the Codex CLI
installation has no bundled bubblewrap helper. See `docs/guides/codex-login.md`.

The general-agent chat workspace also needs no frontend build. Prepare a
copy of `examples/general-agents.v1.json` with your inference endpoints and
use `polyinference workspace CONFIG`. See `docs/guides/ui.md`.

Linux supports the optional bubblewrap command backend. On macOS, explicitly
choose the trusted backend if you authorize host commands. Read the provider
guide before launching a configuration that makes paid requests.

- [Install PolyInference](docs/guides/install.md)
- [Provider setup](docs/guides/setup-providers.md)
