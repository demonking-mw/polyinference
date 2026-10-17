# Agent implementation notes

The bundled runtime is now simple OS v1. The current OS audit decisions and
failure policy are recorded in [the OS implementation plan](../simplified-os/IMPLEMENTATION.md);
see its [runbook](../simplified-os/RUNBOOK.md) and [validation](../simplified-os/VALIDATION.md).

The behavioral sources are the LangGraph revision 4 design, simplified OS, merged
execution contract, integration audit A1–A9, and the user's
[user-agent-review.json](user-agent-review.json). Historical diagrams and research
remain unchanged. The implementation plan is [at the repository root](../../IMPLEMENTATION_PLAN.md).

## Package boundary

| Package | Responsibility |
| --- | --- |
| `polyinference.contracts` | Packaged wire 2.0 Pydantic types from the design |
| `polyinference.workspace_contracts` | Workspace generation, manifest and delta extension |
| `polyinference.domain` | Typed model replies, plans, assignments and finite limits |
| `polyinference.ports` | Replaceable generic records/artifacts/effects/workspace/ownership ports |
| `polyinference.agent` | Three public-API LangGraph entries, task ledger, steering, notes and acceptance |
| `polyinference.runtime` | Simple OS kernel for macOS/Linux/WSL and endpoint clients |

Graph context holds live services. Checkpoints hold IDs, compact counters and
artifact references. Workers are separate graph invocations with separate
`thread_id=process_id`; neither `Send` nor a shared transcript is used as a
process ledger. Generic runtime code does not parse sprint prompts.

A future OS implements the same ports, persistent saver and wire envelopes. It
must preserve CAS publication, the replay-before-dispatch boundary, exact
workspace generations/content, and ownership semantics. The agent's graph code
does not import provider clients, SQLite or the standalone scheduler. File-tree
and native-snapshot operations are explicit workspace-port methods.

## User review decisions

| Review | Implementation |
| --- | --- |
| A01 | Typed result processor routes action/candidate/assessment/needs_review; controller transitions are deterministic |
| A02 | Large configurable allowance, bounded repairs and reserved reconciliation/assessment/publication; exhausted work remains interrupted |
| A03 | Integration always returns to a development/reconciliation model turn before checks |
| A04 | Three verdicts, immutable report, independent resolution, commit receipt, persistent explanation and shared note |
| A05 | Atomic started-worker capture; setup and all waiters count; pending work does not drain |
| A06 | Senior can revert across the project grant, beyond an individual worker's narrower assignment; conflicting later edits require a repair |
| A07 | Verification and CAS protect shared publication and completion; private reasoning overlaps |
| A08 | OpenAI, Gemini, Anthropic, local-compatible inference and Codex native phase jobs; cloud API may replace the worker lane |

## Effects and publication

A stable process/step operation ID names immutable semantic intent. The runtime
persists prepared/submitting before transport. Replay returns a retained result
before checking current transient generation or permit. Mutating transports are
not automatically retried.

The worker preserves B-to-development changes, acquires verification, captures H,
assembles a complete private H view, three-way merges, reasons again, runs checks,
assesses, creates P with sole parent H, and atomically publishes head/report/
hazards/note/attempt/receipt. A real empty commit supports no-diff normal reports.
All verdicts publish reports. Failed work retains a private commit and does not
advance the shared head. Failure atomically closes new starts; already-started
workers drain and publish before review. Failed or missing evidence cannot become
successful. Private failed reports must be retried/rejected, never directly kept.
Read-only omissions never become deletes. Add destinations must be absent in B.

Git objects precede the metadata transaction; source refs are not authoritative.
The isolated Git store avoids writes to the user's source checkout. Hooks/filters
are absent from trusted commit construction. Check/environment and content digests
are recorded; the configured execution environment must remain fixed during a run.

Senior keep/retry/defer are independent dispositions. Revert has its own
capability-call intent and receipt, and checks the resulting full tree. Pending
batches are durable and replay completed receipts. A conservative inverse refuses
to overwrite later modifications of the same paths. The senior can assign a
broader specialist repair instead.

Review closes starts and drains workers before querying senior. Independent sprint
checks are supplied to senior; verification is released before waiting for that
query. Completion reacquires verification, checks the reviewed resulting head,
and compares head/plan/input versions, no active worker/effect, and disposition
closure. New steering invalidates an in-flight acceptance attempt.

## Codex integration

The direct adapter follows the official app-server initialize/thread/start/
turn/start/turn-completed protocol. Planning/review jobs use immutable read-only snapshots. Initial setup and senior coding
assignments use the same brokered worker entry point as junior coding assignments.
Coding roles require `brokered_tools=true`: each bounded development,
reconciliation or assessment phase is one native job. Codex owns its internal
loop and calls an experimental dynamic host tool. Actual callbacks become
subordinate CapabilityCall operations with inherited scope/budget/parent identity.
The parent cloud occupancy is retained. Native item notifications are observations.

The native sandbox is read-only with restricted snapshot reads. File mutation and
configured checks, enabled foreground scripts and setup branch selection use the host broker. The adapter denies native approval and
unknown callback requests. Direct native jobs acquire the installation shell
gate only for brokered commands/checks, so model reasoning can overlap. An opaque
read-only proxy retains conservative shell ownership for the entire native job.

The proxy brief's mehdic path remains configurable for read-only senior work;
its HTTP surface does not establish brokered coding/cancellation guarantees.
No proxy was installed. The official app-server path supplies the richer fallback.
Its dynamic-tool fields are experimental: tests verify the selected wire shape,
and a deployment must confirm its installed Codex version supports it.

Primary protocol references checked for implementation:
[Codex app-server](https://learn.chatgpt.com/docs/app-server),
[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence),
[Gemini generateContent](https://ai.google.dev/api/generate-content).
The current generated official Codex DynamicToolSpec/CallParams/CallResponse types
were also inspected. CLI 0.163.0 passed a real subscription-backed coding task.
See [provider setup and live evidence](PROVIDER_SETUP.md). Anthropic Messages is
also supported; its supplied placeholder produced the expected HTTP 401.
The Claude wire protocol and complete agent flow are tested with TCP fixtures.

## Deliberately small runtime

One coordinator and project; static bindings; one local and one cloud lane;
bounded concurrent requests; FIFO shell/verification gates; alternating verifier
and ordinary inference admission; records, artifacts and persistent checkpoints.
No dynamic migration, weighted allocation, model residency manager, MCP lifecycle,
distributed failover, autonomous memory tiering or model-serving engine is added.
Unknown remote work is an explicit operator/provider reconciliation boundary.

The supported Python/framework versions are pinned in pyproject and the tested
lockfile. Contract tests compare the SDK types to the design Python models under
the same Pydantic release, and validate the original fixtures. Older frozen JSON
schema exports differ cosmetically under newer Pydantic's const/enum generation.

## Initial setup, branch baselines and development allocation

The default UI starts one `category=setup`, `role=specialist` task before sprint
planning. It reads the full user objective with the `BOOTSTRAP` instructions and
uses the ordinary worker graph, mandatory final phases and publication receipts.
It is not a planning query and does not increment the sprint or development-task
allocation counters. New folders/unborn repositories get a private Git baseline;
existing checkouts must be clean. An empty project receives a minimal private
`.gitignore` seed to satisfy the unchanged nonempty workspace-closure contract.
The source checkout is not switched or committed.

`repository.select_branch` is available only through an initial setup TaskSpec's
capability grant and only before edits/integration. It resolves a local branch in
the isolated store (or creates a requested new branch). The selected CodeRevision
becomes initial/provisional/reviewed head before ordinary assignments exist. A new
versioned manifest, linked TaskSpec and TaskAttempt preserve base provenance. Git
initialization and identity are local to the run; no global Git configuration changes.

Senior development is represented by `role=specialist`, using the same worker
entry point with the cloud binding. The coordinator rounds the configured senior
share cumulatively over development assignments, preferring planner nominations.
Setup and cancelled tasks are excluded. Export accounting reports started coding
tasks independently of planner/model-call totals.

The new optional runtime feature requirements are `repository-baseline/1`,
`shell-run/1` and `project-scope/1` (each prefixed `runtime/`). The OS implements
WorkspacePorts.select_branch and asynchronous atomic retag_task_spec; the agent never touches
workspace files directly. `TaskSpec.extensions["polyinference/project-write"]`
expresses a project-root setup grant; ordinary tasks still receive exact file
write sets. Shell execution uses CapabilityCall, bounded output/deadline/process
cleanup and the same installation gate. Shell output is an observation, not
configured acceptance evidence. Mutations during assessment trigger reconciliation
and fresh checks, including when a settled model result is replayed.

Wire 2.0 SDK records and the original workspace schemas are unchanged. The new
program version prevents silently resuming an older graph/prompt implementation.
A future OS must implement the advertised optional features or reject negotiation.
Trusted shell execution is a host execution mode, not filesystem isolation; the
bubblewrap mode enforces a restricted workspace environment when available.
