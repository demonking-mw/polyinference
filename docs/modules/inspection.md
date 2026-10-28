# Inspection, snapshots, history and costs

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Projections expose OS facts and coding history, sharing one diagnostic snapshot format.
The run toolbar exposes Resume and an optional instructions field for paused or
interrupted execution. Clicking submits a run-level request immediately; internal
process choice stays in the agent. Drafts and stable request IDs survive a lost
acknowledgement and page restart. Progress shows Resuming during preparation and
plain failures when recovery is unavailable. The advanced process drawer retains
its explicit process control. Duplicate sends and stale replies are guarded;
refresh preserves typed text. Offline snapshots cannot submit operator signals.

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
Repository UI facts separate ancestry, private/dirty source, recorded publication
and accepted contributions. Legacy merged fields prove no contribution; saved
snapshots retain their original evidence and use the same cautious rendering.
Schema-v2 snapshots also retain physical inference attempts, response-repair
windows, worker exceptions/recovery lineage and progress observations. The UI
shows the last worker progress observation; its novelty heuristic does not
certify correctness. See [progress policy](../../design-docs/implementation/PROGRESS_MONITORING.md).
The agent projection includes bounded worker-state views and the same canonical
physical-attempt/kept-source quality metrics in live and saved data. Native jobs,
raw generations and full product acceptance remain separate quantities; see
[qualification](../guides/qualification.md).
Direct effectful native jobs count once even without response-retry attempt rows;
per-task summaries retain bounded lineage, resource and identical-query metrics.

## Principles to preserve

- Separate process completion, verdict, senior acceptance and project completion.
- Distinguish live, historical, missing and pruned evidence.
- Snapshots contain artifact bytes, not private Git stores or a restorable backup.
- Observer/archive failures never replace primary outcomes.
- Memory / context reads original/prepared views and receipts by exact operation identity.
- Retry roots/outcomes group attempts; compaction helpers never replace caller input.
- Node prompts label their origin, retain originals and separate native transport observations.
- Load artifact text on demand; discard stale reads/errors after navigation or close.

## Verification and related reading

[OS monitor](../../tests/test_ui_os.py), [agent monitor](../../tests/test_ui_agents.py),
[history](../../tests/test_history.py), [costs](../../tests/test_costs.py) and [frontend](../../tests/ui_start.test.cjs).

[Archives](../guides/archives.md) · [Memory inspector design and coverage](../../development-docs/current-iter-issues.md#os-memory-context-inspector).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
