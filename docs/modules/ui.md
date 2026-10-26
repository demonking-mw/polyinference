# Loopback UI and project selection

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The local test runner hosts fresh runs, project selection and inspection without a frontend build.

| File | Responsibility |
| --- | --- |
| [src/polyinference/ui.py](../../src/polyinference/ui.py) | Loopback HTTP server, run manager, default fixture/config, launch/steer/resume/export APIs and terminal reporting. |
| [src/polyinference/ui.html](../../src/polyinference/ui.html) | Packaged UI shell, launch controls, saved-run selection, snapshot opening and frontend behavior. |
| [src/polyinference/agent/endpoint_probe.py](../../src/polyinference/agent/endpoint_probe.py) | Application-owned artifact-only 64-token endpoint probe using ordinary OS grants/accounting, without coding services or Git. |
| [src/polyinference/ui_repository.py](../../src/polyinference/ui_repository.py) | Filesystem/project picker, new/nested project observations and suggested checks. |

## Interface and ownership

The default preset uses Haiku workers/Codex seniors with one worker/slot. Every
Start run creates fresh state. A custom config preserves its grants/providers.
Snapshot viewing makes no provider requests. Endpoint testing offers explicit
cloud/local/buffered timing profiles and an on-click warm-up using an ordinary
bounded query. Probes serialize with launches/resumes; unknown probe state remains
a blocker across UI restart. See [endpoint testing](../guides/endpoint-testing.md). Picker observations are not acceptance.
Paused/interrupted runs show Resume with inline optional instructions. One click
submits the run; no process selection or reconciliation form is required.
POST /api/resume {id, text?, request_id?, process_id?} accepts a durable request
and reopens that run in the background. process_id supports the older inspector
control. Reusing request_id with the same input returns the same acknowledgement;
changed input is rejected. Pending requests restore after server restart, including
the gap before metadata save and activation before execution. Progress is projected
as Resuming until the agent activates work. Unsupported recovery is a plain error.
Direct file:// previews have no loopback API; use the server's HTTP URL. Resume
reloads the saved config (or matching --config for attached --state), suppresses ambient capacity overlays, keeps the run
ID and serializes launches/resumes under one manager lock. Saved authority, budgets,
deadlines and cancellation apply; agent compatibility and OS effect preparation
run before continuation. Background rejections remain inspectable; history/Save retain requests, outcomes and steering.
UI --sim-batch N (1..16) applies only to this TestUI instance's new configurations.
CLI, project selection, Start, display and saved config share the validated overlay.
Missing/blank simulation credentials retain an ordinary exportable startup failure.
--sim-inference reveals three modes before Start with validated per-run TPS, batch,
bug rate, seed and timing controls. Normal omits simulation config/client changes;
ordinary launches hide the controls and send the original payload. An active mode's
batch overrides --sim-batch for that run. Progress/incidents are separate from real
provider costs; live/saved inspection retains the same facts. See the
[simulator module](inference-simulation.md) and [usage](../guides/sim-inference.md).

## Principles to preserve

- Failed launches keep identity, exact inputs/errors and exportable evidence.
- Linux/WSL backend paths must not become Windows paths.
- Selecting a project must not overwrite unrelated existing source.
- Reporting observes durable state without controlling or replacing it.
- Memory / context is read-only, uses existing record/artifact endpoints, and works offline.
- Simulation never mutates environment/defaults/old state or bypasses Git/task policy.

## Verification and related reading

[UI](../../tests/test_ui.py), [frontend wrapper](../../tests/test_ui_frontend.py)
and [browser logic](../../tests/ui_start.test.cjs).

[UI guide](../guides/ui.md) · [Project guide](../guides/projects.md) · [Inspection](inspection.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.

## Integrated reliability branch (2026-10-26)

Live task rows expose the last worker progress observation. Shared Save/export
snapshots retain physical inference attempts and expanded attempted context,
retry windows, diagnoses, exception decisions, resource lineage, progress events,
review artifacts and interface contracts, alongside the existing schema-v2 records,
OS inspection, artifacts and checkpoints. Earlier saved snapshots remain viewable.
