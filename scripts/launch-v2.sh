#!/usr/bin/env bash
set -euo pipefail

usage() {
    printf 'Usage: %s [CONFIG [PORT]]\n' "$0"
}

if [[ ${1:-} == --help || ${1:-} == -h ]]; then
    usage
    exit 0
fi
if (( $# > 2 )); then
    usage >&2
    exit 2
fi

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
config="${1:-$root/examples/general-agents.v1.json}"
port="${2:-8766}"

if [[ -n ${VIRTUAL_ENV:-} && -x "$VIRTUAL_ENV/bin/python" ]]; then
    python="$VIRTUAL_ENV/bin/python"
elif [[ -x "$root/.venv-linux/bin/python" ]]; then
    python="$root/.venv-linux/bin/python"
elif [[ -x "$root/.venv/bin/python" ]]; then
    python="$root/.venv/bin/python"
else
    printf 'Install PolyInference in a virtual environment using setup.md, then run this script.\n' >&2
    exit 1
fi

# Codex may be installed in the user bin directory on WSL.
export PATH="$PATH:$HOME/.local/bin"
exec "$python" -m polyinference.cli workspace "$config" --port "$port" --sim-haiku
