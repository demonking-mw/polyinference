# Providers and model routing

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

`local` and `cloud` are the names of two endpoint **lanes**. They do not guarantee
where inference happens: the default `local` lane points to Anthropic's cloud API.
Physical inference location is recorded separately.

The default bindings are:

| Role | Purpose | Lane / default backend |
| --- | --- | --- |
| `worker` | Junior development tasks | `local` / Anthropic Haiku |
| `senior` | Planning and review | `cloud` / Codex |
| `specialist` | Initial setup and senior development tasks | `cloud` / Codex |

All three bindings must be present in a custom configuration. They are pinned
for a run. To change models, providers or bindings, start a fresh state directory.

| Backend | Endpoint configuration | Authentication / example |
| --- | --- | --- |
| Anthropic | `protocol: "anthropic"`, `base_url: "https://api.anthropic.com/v1"` | `api_key_env: "ANTHROPIC_API_KEY"`; [Claude example](../../examples/agent.anthropic.json) |
| OpenAI API | `protocol: "responses"` or `"chat"`, `base_url: "https://api.openai.com/v1"` | `api_key_env: "OPENAI_API_KEY"`; [OpenAI example](../../examples/agent.openai.json) |
| Gemini | `protocol: "gemini"`, `base_url: "https://generativelanguage.googleapis.com/v1beta"` | `api_key_env: "GEMINI_API_KEY"`; [Gemini example](../../examples/agent.gemini.json) |
| Local compatible server | `protocol: "chat"` or `"responses"`, URL of your running server | Set its served model ID and any required credential variable. |
| Codex subscription | `protocol: "codex_app_server"`, `command: ["codex", "app-server"]` | Codex CLI login; [Codex example](../../examples/agent.codex.json) |
| Default mixed setup | Haiku `local` lane and Codex `cloud` lane | [Mixed example](../../examples/agent.mixed.json) |

Export the corresponding API credential before launching the CLI or UI. Set the
`model` field to the exact ID your endpoint serves. A ChatGPT login authenticates
Codex; raw OpenAI API calls use a separately configured API key. Local inference
requires you to install and run a compatible server yourself.

Coding roles using `codex_app_server` require **`brokered_tools: true`** so their
file, shell and check operations use the same host broker as raw LLM workers.
Planning/review queries remain read-only. Setup and senior development have file
and enabled shell/check tools through the worker protocol.

Codex receives a separate read-only input copy, a disabled native shell, no
approval escalation, and explicit instructions to use only the host broker for
files and commands. The runtime checks that input copy and the broker's source
views for unbrokered edits before callbacks and after a terminal reply. Native
tool telemetry alone never authorizes an edit. Raw chat/Responses/Anthropic
inference has no native filesystem tools; this distinction is about the harness,
not whether the model is hosted locally or in the cloud.

There is also an optional `codex_proxy` adapter for a separately installed,
compatible proxy with a pinned read-only snapshot. It supports senior queries;
opaque proxy coding jobs are rejected. No third-party proxy is installed by this
project. Use the native app-server path for Codex development.
