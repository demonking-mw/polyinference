# Loopback UI and project selection

The local test runner hosts fresh runs, project selection and inspection without a frontend build.

| File | Responsibility |
| --- | --- |
| [src/polyinference/ui.py](../../src/polyinference/ui.py) | Loopback HTTP server, workspace routes, coding run manager, launch/steer/resume/export and terminal reporting. |
| [src/polyinference/ui.html](../../src/polyinference/ui.html) | Packaged UI shell, launch controls, saved-run selection, snapshot opening and frontend behavior. |
| [src/polyinference/ui_workspace.py](../../src/polyinference/ui_workspace.py) | Workspace launch, role-aware model catalog, durable chat metadata, request deduplication and an OS observation projection. |
| [ui-workspace.html](../../src/polyinference/ui-workspace.html), [ui-workspace.css](../../src/polyinference/ui-workspace.css), [ui-workspace.js](../../src/polyinference/ui-workspace.js) | Workspace header, chat composer, system-wide OS Monitoring and invocation-specific Agent Monitoring. |
| [src/polyinference/agent/endpoint_probe.py](../../src/polyinference/agent/endpoint_probe.py) | Application-owned artifact-only 64-token endpoint probe using ordinary OS grants/accounting, without coding services or Git. |
| [src/polyinference/ui_repository.py](../../src/polyinference/ui_repository.py) | Filesystem/project picker, new/nested project observations and suggested checks. |

## Interface and ownership

`polyinference workspace CONFIG` serves a separate local workspace using
generic `RuntimeConfig`. The peer `polyinference ui` command serves the coding
console. The workspace accepts a message ID, agent and compatible binding for
each model role, prompt, optional corpus, and explicit previous-exchange choice.
It checks those inputs before recording an invocation. The same message ID
and input returns the original acknowledgement. Changed input is rejected.
Each Send pins a fresh configuration under
`STATE/invocations/ID/config.json` and places the graph journal under
`STATE/invocations/ID/state/`. The application retains replies and source names.
Model selection validates configured locations, protocol, credentials and
applicable data policy. The standard GPT‑6.1 Sol Cloud option uses the
Codex subscription. The agent runner and OS verify the native account
and model before a turn. See `docs/guides/cloud-codex-default.md`.
The `--sim-haiku` launch flag overlays the local binding with the Haiku
preset with two slots. The model picker and pinned invocation identify it as a cloud
stand-in. The adapter preserves the other role and narrows the original data
policy to the authorized destination for each simulated step.

One workspace server owns a state root and accepts one active invocation at a
time. This bounds admission within that workspace. A restart keeps earlier
transcripts and reports interrupted work without replay. Durable holds or
unknown execution block new submissions in the workspace.
`GET /api/workspace/os` reads the workspace-wide observation independently
of the selected reply or invocation. Agent Monitoring keeps the per-invocation
process view and displays the scheduler capability as unavailable.
See `docs/guides/ui.md` for usage and
`docs/temporary/proposals/2026-11-16-chat-workspace-design.md` for the design.

### Coding console

Without machine preferences, the preset uses Haiku workers/Codex seniors with one worker/slot.
Machine defaults (`docs/guides/configuration.md`) replace local serving settings for plain UI launches. The launch footer displays the effective model, location/protocol, context, slots, workers
and sprint limit. Opt-in local_strata_profile preparation runs before saved-run
restoration and HTTP serving; startup failure prevents opening an unusable UI.
serve closes its owned provider on normal exit, Ctrl+C, SIGTERM/SIGHUP and later
startup errors, restoring prior signal handlers. Strata's process-death watcher
covers uncatchable termination. Reused runtimes are never adopted; see the
launch lifecycle and bounded drain (`docs/guides/launching.md`).
Every Start run creates fresh state. A custom config preserves its grants/providers.
Snapshot viewing makes no provider requests. Endpoint testing offers explicit
cloud/local/buffered timing profiles and an on-click warm-up using an ordinary
bounded query. Probes serialize with launches/resumes; unknown probe state remains
a blocker across UI restart. See endpoint testing (`docs/guides/endpoint-testing.md`). Picker observations are not acceptance.
Probe scheduling declares the endpoint protocol, not guessed physical placement;
the original run-wide data policy still blocks disallowed or unknown locations.
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
simulator module (`docs/modules/inference-simulation.md`) and usage (`docs/guides/sim-inference.md`).

Activity paging/labels share the resolved OS tuning (`docs/guides/os-tuning.md`) in
live and saved views. Resume text bounds are enforced by the canonical server
definition; the client retains rejected drafts without an independent fixed cap.

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
The [workspace integration](../../tests/test_ui_workspace.py) exercises role
selection, the loopback routes, live and finished inspection, deduplication and
restart using the real OS with scripted inference.

UI guide (`docs/guides/ui.md`) · Project guide (`docs/guides/projects.md`) · Inspection (`docs/modules/inspection.md`).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in `development-docs/FIXES.md`.
Follow documentation maintenance (`docs/maintenance.md`) in the same task.

Live and saved views project retry, diagnosis, resource and progress evidence
from the same records. See `docs/modules/inspection.md` for the projection contract.
