# Module guides

[Developer onboarding](../../dev-readme.md) · [Architecture](../architecture.md) · [HTML tree](../file-tree.html) · [Agent JSON](../file-tree.json)

Each feature has one primary guide naming every owned source file, its interface,
ownership and design principles. Closely related Python modules share a guide.

| Feature | Files |
| --- | --- |
| [Contracts and runtime ports](sdk.md) | __init__.py, contracts.py, workspace_contracts.py, execution_contracts.py, ports.py, primitives.py |
| [Settings and example configurations](settings.md) | system_settings.py, config.py, system_settings.py, agent.mixed.json, agent.anthropic.json, agent.codex.json, agent.openai.json, agent.gemini.json |
| [Coding controller, setup and task allocation](agent-workflow.md) | controller.py, setup.py, tasks.py, routing.py |
| [Worker/senior graphs and reply grammar](agent-workers.md) | worker.py, senior.py, prompts.py, domain.py |
| [Application services and runtime policy installation](agent-services.md) | __init__.py, services.py, runtime_policy.py, design_basis.py |
| [Coding repository policy and retained source](repository.md) | repository.py, reports.py, os_contracts.py |
| [Kernel and durable effect execution](kernel.md) | kernel.py, adapter.py, __init__.py |
| [Process lifecycle](processes.md) | processes.py |
| [Capability registration and tool ABI](capabilities.md) | capabilities.py, tool_contracts.py |
| [Persistence, exclusive resources and blocking I/O](storage.md) | storage.py, exclusive.py, blocking.py |
| [Endpoint admission and provider adapters](inference.md) | inference.py, codex.py |
| [Optional context preparation](context.md) | context.py |
| [Bounded OS model retries](retries.md) | model_retries.py |
| [Optional workspaces and source classification](workspaces.md) | workspace.py, workspace_state.py |
| [File tools, checks and foreground commands](commands.md) | tools.py, shell.py, commands.py, tool_environment.py |
| [Artifact delivery and user messages](delivery.md) | outputs.py, messages.py |
| [Command line and saved credentials](cli.md) | cli.py |
| [Loopback UI and project selection](ui.md) | ui.py, ui.html, ui_repository.py |
| [Inspection, snapshots, history and costs](inspection.md) | snapshots.py, history.py, ui_os.py, ui_agents.py, ui-monitor.js, costs.py |

Supporting modules: [design tools](design-tools.md), [live smoke runner](live-smoke.md),
[documentation tools](documentation.md), [packaging](packaging.md) and
[test suite](../../tests/README.md).

After any fix or feature, update all affected guides and related usage, settings,
design and issue docs, then [FIXES.md](../../development-docs/FIXES.md). Regenerate
and check navigation using the [maintenance contract](../maintenance.md).
