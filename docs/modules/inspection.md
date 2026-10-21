# Inspection, snapshots, history and costs

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Read-only projections expose OS facts and coding history, sharing one diagnostic snapshot format.

| File | Responsibility |
| --- | --- |
| [src/polyinference/snapshots.py](../../src/polyinference/snapshots.py) | Shared live/saved readers, process/node detail and version-2 snapshot serialization. |
| [src/polyinference/history.py](../../src/polyinference/history.py) | Completion/failure/resume archives and 30-day managed archive pruning. |
| [src/polyinference/ui_os.py](../../src/polyinference/ui_os.py) | Generic OS projection from a durable journal snapshot. |
| [src/polyinference/ui_agents.py](../../src/polyinference/ui_agents.py) | Coding task/verdict/review/acceptance projection. |
| [src/polyinference/ui-monitor.js](../../src/polyinference/ui-monitor.js) | OS/Agents monitors, record/artifact drawers and live/saved rendering. |
| [src/polyinference/costs.py](../../src/polyinference/costs.py) | Approximate provider/API-equivalent cost estimates and aggregation. |

## Interface and ownership

UI Save and automatic archives use the same serializer. Records/events share
a read transaction; checkpoints/artifacts are separate reads. Costs are diagnostic
estimates, not provider billing or subscription allowance.

## Principles to preserve

- Separate process completion, verdict, senior acceptance and project completion.
- Distinguish live, historical, missing and pruned evidence.
- Snapshots contain artifact bytes, not private Git stores or a restorable backup.
- Observer/archive failures never replace primary outcomes.
- Effective-context visibility remains MEM-01; original prompts may differ from prepared views.

## Verification and related reading

[OS monitor](../../tests/test_ui_os.py), [agent monitor](../../tests/test_ui_agents.py),
[history](../../tests/test_history.py), [costs](../../tests/test_costs.py) and [frontend](../../tests/ui_start.test.cjs).

[Archives](../guides/archives.md) · [Memory inspector proposal](../../development-docs/current-iter-issues.md#os-memory-context-inspector).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
