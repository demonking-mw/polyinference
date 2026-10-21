# Install PolyInference

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

Run the commands in **Bash** on macOS, Linux or WSL. On macOS, install Python 3.10+
and Git using your preferred package manager; skip the Ubuntu package commands.
`bubblewrap` execution requires Linux; use explicitly enabled `trusted` commands
on macOS. Codex uses its own platform sandbox for native jobs.



## Install the application

On Ubuntu/Debian, install the system prerequisites if needed:

```bash
sudo apt update
sudo apt install -y git bash curl python3 python3-venv python3-pip
```

Clone and install:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/demonking-mw/polyinference.git
cd polyinference
python3 -m venv .venv-linux
source .venv-linux/bin/activate
python -m pip install -e '.[test]'
polyinference --help
```

The `test` extra includes pytest and Ruff, useful for testing the implementation
and for the UI's suggested Python check. A runtime-only installation can use
`python -m pip install -e .` instead. Direct dependencies are pinned in
[pyproject.toml](../../pyproject.toml); [requirements.lock](../../requirements.lock) records the
complete tested environment. To reproduce those transitive versions, install
`python -m pip install -r requirements.lock` before the editable installation.



Next: [Codex login](codex-login.md) and [Anthropic credentials](anthropic-key.md), then [launch](launching.md).
