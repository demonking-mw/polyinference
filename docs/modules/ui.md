# Loopback UI and project selection

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The local test runner hosts fresh runs, project selection and inspection without a frontend build.

| File | Responsibility |
| --- | --- |
| [src/polyinference/ui.py](../../src/polyinference/ui.py) | Loopback HTTP server, run manager, default fixture/config, launch/steer/export APIs and terminal reporting. |
| [src/polyinference/ui.html](../../src/polyinference/ui.html) | Packaged UI shell, launch controls, saved-run selection, snapshot opening and frontend behavior. |
| [src/polyinference/ui_repository.py](../../src/polyinference/ui_repository.py) | Filesystem/project picker, new/nested project observations and suggested checks. |

## Interface and ownership

The default preset uses Haiku workers/Codex seniors with one worker/slot. Every
Start run creates fresh state. A custom config preserves its grants/providers.
Snapshot viewing makes no provider requests. Picker observations are not acceptance.

## Principles to preserve

- Failed launches keep identity, exact inputs/errors and exportable evidence.
- Linux/WSL backend paths must not become Windows paths.
- Selecting a project must not overwrite unrelated existing source.
- Reporting observes durable state without controlling or replacing it.
- SIM-01 and MEM-01 are proposals, not implemented controls.

## Verification and related reading

[UI](../../tests/test_ui.py), [frontend wrapper](../../tests/test_ui_frontend.py)
and [browser logic](../../tests/ui_start.test.cjs).

[UI guide](../guides/ui.md) · [Project guide](../guides/projects.md) · [Inspection](inspection.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
