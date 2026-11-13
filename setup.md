# Setup

Use macOS, Linux or a Linux distribution inside WSL. Install Python 3.10 or
later with `venv`/`pip`, Git and Bash. Native Windows does not run the POSIX
runtime. In WSL, install and run the tools inside Linux; keep source and state
on the Linux filesystem and enter Linux paths in the UI.

For the bundled cloud senior preset, install and sign in to Codex on the
same host. For the bundled Haiku worker preset, configure Anthropic credentials.
A real local server can replace the stand-in. Install the target project's own
check tools; the bundled PolyInference UI needs no frontend build.

Linux supports the optional bubblewrap command backend. On macOS, explicitly
choose the trusted backend if you authorize host commands. Read the provider
guide before launching a configuration that makes paid requests.

- [Install PolyInference](docs/guides/install.md)
- [Provider setup](docs/guides/setup-providers.md)
