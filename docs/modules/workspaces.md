# Optional workspaces and source classification

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Generic source views, grants and private execution state support attached directories and explicit isolated copies.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/workspace.py](../../src/polyinference/runtime/workspace.py) | Workspace manifests/grants, attached authority, source snapshots, generations and legacy isolated integration helpers. |
| [src/polyinference/runtime/workspace_state.py](../../src/polyinference/runtime/workspace_state.py) | Declared-output/source classification, dependency identity, private environment copies and disk accounting. |

## Interface and ownership

A registered process receives an explicit narrower workspace grant. Attached
views are not copied over user source; coding RepositoryWorkspaces supplies Git
policy. General processes may use no workspace. Compatibility task refs are opaque.

## Principles to preserve

- Current generation/content and source scope remain authoritative.
- Tracked/granted source takes precedence over declared generated output.
- Ignore files never grant authority or hide protected source.
- Reuse private dependencies only while manifests/locks match.
- Attached scope failures preserve edits and block mutation; no copy rollback.

## Verification and related reading

[Workspace outputs](../../tests/test_workspace_outputs.py), [in-place repository](../../tests/test_in_place_repository.py),
[runtime](../../tests/test_runtime.py) and [capability boundary](../../tests/test_capability_boundary.py).

[Repository policy](repository.md) · [FIX-0034–0035](../../development-docs/FIXES.md#fix-0034).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
