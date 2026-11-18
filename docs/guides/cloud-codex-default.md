# Default cloud model for PolyInference agents

Use **GPT‑6.1 Sol** (`gpt-6.1-sol`) through the **Codex ChatGPT
subscription** for the Cloud role. This is the shared application default
for the coding console and the four general agents. Configure the standard
cloud endpoint with `protocol: "codex_app_server"` and
`command: ["codex", "app-server"]`. Sign in to Codex with ChatGPT inside
the environment running PolyInference and check `codex login status`.
The workspace verifies the app-server account type before submission and
rejects API-key authentication.

| Agent | Cloud role |
| --- | --- |
| Simple | General model when Cloud is selected. The bundled configuration selects Cloud by default. |
| Supervisor | Plan and synthesize. |
| Research | Lead and report. |
| Writer | Plan and evaluate. |

The local binding stays separately configured. `workspace --sim-haiku`
uses remote Haiku for the local role and labels it as a cloud-hosted
stand-in. It preserves the configured Cloud binding and must satisfy the
same cloud data permissions.

Applications choose the binding; the OS enforces the grant, budget,
deadline, and provider contract. The general agents use a tool-free
native Codex job in an empty read-only working directory. Local raw text
steps and the explicit document lookup keep their own contracts. The
shared preset is in `src/polyinference/agent/system_settings.py` and the
general-agent example is `examples/general-agents.v1.json`.

When changing a launch profile, use the new binding for fresh invocations.
Retained runs keep their original model and provider evidence. On Linux
and WSL, the Codex CLI needs access to its Linux sandbox helper. Install
your distribution's `bubblewrap` package when the CLI has no bundled copy.
