# Application services and runtime policy installation

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

AgentServices assembles coding state and requests without making the OS interpret coding records.

| File | Responsibility |
| --- | --- |
| [src/polyinference/agent/__init__.py](../../src/polyinference/agent/__init__.py) | Application package boundary. |
| [src/polyinference/agent/services.py](../../src/polyinference/agent/services.py) | Ledger, memory/history/context assembly, process and effect creation, steering and setup synchronization. |
| [src/polyinference/agent/runtime_policy.py](../../src/polyinference/agent/runtime_policy.py) | Coding check configuration and publication policy installed at bootstrap. |
| [src/polyinference/agent/design_basis.py](../../src/polyinference/agent/design_basis.py) | Packaged design provenance and fingerprints. |

## Interface and ownership

Trusted bootstrap installs application protocols, capabilities, cancellation and
publication handlers. Processes receive explicit grants. Canonical memory and
history selection belong here; optional OS preparation produces derived views.
CheckSelection adds agent-only prerequisite/task/acceptance purposes to the generic
Check schema. Initial setup pins discovered criteria per purpose; explicit user
criteria cannot be replaced. setup_check_definitions, task_check_definitions and
acceptance_check_definitions select phase policy without changing OS check execution.
Senior context includes shared check commands/source previews and read-only
retained-source offers; these guide explicit dependencies and resume_from grants.
Mode-specific prompts distinguish in-place private uncertainty from legacy publication.

## Principles to preserve

- Reinstall pinned policies before new work after restart.
- Role labels never grant capability or management authority.
- Validate task lifecycle changes in the agent; generic records supply atomicity.
- Context omissions/summaries must not rewrite canonical memory or user constraints.

## Verification and related reading

[Setup tools](../../tests/test_setup_tools.py), [agent transitions](../../tests/test_agent_transitions.py),
[boundary](../../tests/test_capability_boundary.py) and [context](../../tests/test_context_safety.py).

[Memory implementation](../../development-docs/memory-implementation-report-2026-10-20.md) · [Runtime boundary](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
