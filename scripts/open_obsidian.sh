#!/usr/bin/env bash
set -euo pipefail

vault=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
display_args=()
if [[ "${1:-}" == --x11 ]]; then
  display_args=(--ozone-platform=x11)
  shift
elif [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
  wayland_socket=$WAYLAND_DISPLAY
  if [[ $wayland_socket != /* ]]; then
    wayland_socket="${XDG_RUNTIME_DIR:-}/$wayland_socket"
  fi
  if [[ -S $wayland_socket ]]; then
    display_args=(--ozone-platform=wayland)
  fi
fi

case "${1:-}" in
  '')
    uri=$(python3 -c 'from urllib.parse import quote; import sys; print("obsidian://open?path=" + quote(sys.argv[1], safe=""))' \
      "$vault/README.md")
    ;;
  --install)
    if ! command -v obsidian >/dev/null; then
      if [[ $(dpkg --print-architecture) != amd64 ]]; then
        printf 'This installer uses the Obsidian amd64 package.\n' >&2
        exit 1
      fi
      (
        package_dir=$(mktemp -d)
        package="$package_dir/obsidian.deb"
        trap 'rm -f -- "$package"; rmdir -- "$package_dir"' EXIT
        chmod 755 "$package_dir"
        curl -fL --output "$package" \
          https://github.com/obsidianmd/obsidian-releases/releases/download/v1.15.1/obsidian_1.15.1_amd64.deb
        printf '%s  %s\n' f77b6dfc8c040214f2febad2b1b9b051b6a838a47b0f4fb90a31cfcb79b8fcec \
          "$package" | sha256sum --check --status
        sudo apt-get install "$package"
      )
    fi
    uri='obsidian://choose-vault'
    ;;
  --choose-vault)
    uri='obsidian://choose-vault'
    ;;
  *)
    printf 'Usage: bash %s [--x11] [--install | --choose-vault]\n' "$0" >&2
    exit 2
    ;;
esac

if ! command -v obsidian >/dev/null; then
  printf 'Run this script with --install inside Ubuntu WSL first.\n' >&2
  exit 1
fi
if [[ $uri == 'obsidian://choose-vault' ]]; then
  printf 'Choose Open folder as vault, then select %s\n' "$vault"
fi
exec obsidian "${display_args[@]}" "$uri"
