# Coding repository policy and retained source

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Default coding work uses the selected actual repository, integration branch and linked task worktrees.

| File | Responsibility |
| --- | --- |
| [src/polyinference/agent/repository.py](../../src/polyinference/agent/repository.py) | Git policy/setup, RepositoryWorkspaces, preparation, verified integration, retained candidates and interrupted-source handoff. |
| [src/polyinference/agent/reports.py](../../src/polyinference/agent/reports.py) | Coding-specific task reports, commit receipts and validation. |
| [src/polyinference/os_contracts.py](../../src/polyinference/os_contracts.py) | Compatibility imports of application-owned report extensions. |

## Interface and ownership

The agent installs RepositoryWorkspaces over generic OS attached-directory grants
and leases. In-place is the default; isolated mode is explicit. Failed preparation
reaches engineers as evidence; configured checks still run after known failure.

## Principles to preserve

- The user-selected path is authoritative, including new/nested projects.
- Git choices, retries, dependency commands and acceptance are coding policy.
- Protect root branch/HEAD/index and existing edits before integration.
- Preserve failed/uncertain source privately; reuse needs explicit resume_from, scope and base checks.
- Git mutations and SQLite report publication are separate effects; uncertain outcomes stop mutation.

## Verification and related reading

[In-place repository](../../tests/test_in_place_repository.py), [recovery](../../tests/test_recovery.py)
and [workspace outputs](../../tests/test_workspace_outputs.py).

[Boundary: repository guarantees](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md#in-place-coding-repositories) · [FIX-0001](../../development-docs/FIXES.md#fix-0001) · [FIX-0060](../../development-docs/FIXES.md#fix-0060).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
