# Codex installation and login

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

Install Codex in the **same macOS/Linux/WSL environment as the backend**. WSL
needs its own Linux installation even if you use the Windows desktop app. Skip the installation command if `codex --version` already works there.
The official Linux installer is documented in the
[Codex CLI quickstart](https://learn.chatgpt.com/docs/codex/cli):

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Follow the installer's PATH instructions, reopening your terminal if necessary.
Then activate the PolyInference virtual environment again and sign in:

```bash
codex --version
codex login
codex login status
```

Use the ChatGPT account you intend to use for Codex. The default integration
launches `codex app-server` automatically; you do not start an app-server manually
or paste a subscription token into a PolyInference JSON file. Subscription access
and available models depend on your account/workspace.
[Official authentication guidance](https://learn.chatgpt.com/docs/auth).

If the browser callback cannot complete in WSL or on a remote machine, try:

```bash
codex login --device-auth
```

Device login must be enabled for your account/workspace; follow the URL and code
shown by the CLI. Run `codex login status` afterward to confirm the authentication
method. For the default mixed setup, an `OPENAI_API_KEY` is not required.
[Device authentication instructions](https://learn.chatgpt.com/docs/auth#login-on-headless-devices).



Next: [Anthropic credentials](anthropic-key.md) · [Launch](launching.md).
