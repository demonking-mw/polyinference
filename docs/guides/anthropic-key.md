# Anthropic credentials

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

Get an API key for your own Anthropic account. Set `ANTHROPIC_API_KEY` in the
**same terminal that will launch the backend**. This Bash prompt avoids putting
the value directly in shell history:

```bash
read -rsp 'Anthropic API key: ' ANTHROPIC_API_KEY
printf '\n'
export ANTHROPIC_API_KEY
```

For reuse, you can put the following line in a private file outside the repository,
for example `~/.config/polyinference/anthropic.env`, using your editor:

```bash
export ANTHROPIC_API_KEY='replace-with-your-real-key'
```

Create the parent directory with `mkdir -p ~/.config/polyinference` before saving
the file. Restrict access to it:

```bash
chmod 600 ~/.config/polyinference/anthropic.env
```

PolyInference automatically loads `ANTHROPIC_API_KEY` from
`~/.config/polyinference/anthropic.env` when a command starts. An existing
environment variable takes priority. The file supports `KEY=value` and
`export KEY='value'` assignments and comments; shell commands and variable
expansion are not executed. Repository `.env` files are not loaded. A server that is
already running keeps its previous environment; after replacing a key, restart
the server when its active run has finished. Credential values belong in your
environment, while configurations contain only environment variable names.



Next: [Launch](launching.md) · [Other providers](providers.md).
