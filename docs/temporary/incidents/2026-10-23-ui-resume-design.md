# Run Resume design and implementation history

<a id="ui-process-resume"></a>
## UI-RESUME-01 — Resume a selected paused process — 2026-10-21

Status: implemented; run-level continuation supersedes the original process-only
entry point. Current implementation: `development-docs/FIXES.md#fix-0111`.
Original process-level implementation: `development-docs/FIXES.md#fix-0102`; the historical
paragraphs below describe that earlier behavior.

The paused-run toolbar offers Resume run with a paused-process chooser and optional
steering; the process drawer retains Resume process. The visibility correction is
`development-docs/FIXES.md#fix-0105`. Blocked submissions expose their reason instead of
hiding the toolbar entry. Use the HTTP UI, not a direct file:// preview. The local
API records a generic OS resume-request, then reopens the same saved configuration
and routes continuation through the application's existing known-model retry,
accepted-output recovery or senior review. Prompt/config pins, budgets, deadlines,
source provenance and cancellation remain enforced. The agent module fingerprint
is unchanged, so the UI feature itself does not invalidate retained program pins.
Unsettled remote execution is refused pending reconciliation; the
run 7086c575ef94 timeout diagnosis (`docs/temporary/investigations/2026-10-21-run-7086c575ef94.md`) is not repaired or
automatically reconciled by this feature. JSON snapshots remain read-only.

Frontend guards cover duplicate sends, stale responses and draft preservation;
backend guards cover concurrent runs, state/config identity, unknown execution,
version mismatch and launch failures. Requests/outcomes remain inspectable and
exportable. No UI reconciliation assertion or automatic budget reset was added.

### Run-level Resume implementation — 2026-10-23

The paused/interrupted-run toolbar now has optional instructions and one Resume
button; it submits immediately without a chooser. Stable request IDs and local
drafts survive acknowledgement loss/page restart. Polling can acknowledge a lost
reply so a later pause receives a new request. Recovery progress is visible and
unsupported recovery produces a plain failure rather than a resolution form.

The HTTP layer loads exact saved settings and serializes drivers. Generic OS
intent acceptance is independent of execution certainty. OS-owned preparation
recovers host receipts, artifact-backed completed query responses and retrievable
HTTP Responses by saved response ID, with bounded lookup and retained accounting.
Unknown/native/synchronous operations without recovery evidence remain protected;
no automatic remote-cancel or host-descendant termination guarantee was added.

Agent-owned continuation handles all stopped workers, resumes eligible checkpoints,
uses linked model retries or senior review with retained source, and recovers
accepted-output delivery. Atomic steering receipts and durable continuation plans
cover interrupted activation. CLI resume CONFIG [--text instructions] uses the same
service. Server restart restores pending accepted/activated requests, including the
journal-to-metadata gap. An exact predecessor graph has an audited migration;
other pins, grants, budgets, deadlines and cancellation remain enforced. Original
manifests/effects remain evidence. See `development-docs/FIXES.md#fix-0111` for fresh checks.

<a id="ui-run-resume-design"></a>
### Proposed run-level Resume redesign — 2026-10-23

Status: historical proposal, implemented with the explicit provider/compatibility
limits described above in `development-docs/FIXES.md#fix-0111`. The original design-only
record is `development-docs/FIXES.md#fix-0110`. The following preserves that proposal. The user wants optional instructions followed
by one Resume click, with continuation/recovery decisions handled internally.

**Frontend and HTTP adapter.** Place an optional instructions field beside the
paused run's Resume button. Clicking Resume submits the run ID, text and a stable
request ID immediately. Remove the required drawer, process chooser and
reconciliation tasks from this path. Show Resuming, then Running when the agent
actually continues. Show a plain failure if continuation fails; keep technical
details in inspection. Retain text until durable acknowledgement, deduplicate
clicks/retries across reconnects, and restore progress after page/server restart.
POST /api/resume accepts a run-level request without process_id and returns 202
with its request reference; acceptance means the request was saved, not that work
has started. The server owns saved-config loading, one-driver exclusion and
status projection, not coding recovery decisions. Offline exports remain viewers.

**Agent.** A run-level continuation handler owns resuming the objective. Move
coding decisions currently in cli.apply_resume behind this agent interface;
CLI/UI call the same entry point. Inspect the whole run rather than guessing one
process in JavaScript. Resume an eligible checkpoint, request a linked recovery
for a known failed model step, send interrupted work through senior review with
its retained source, or recover accepted-output delivery as appropriate. Account
for every stopped worker so one selected process cannot leave others stranded.
Record optional instructions once before choosing new work; apply them at the
existing drain/review boundary. Routine task disposition and repair belong to the
agent. Preserve objective, amendments, workspaces, task/attempt provenance and
acceptance checks. Use bounded recovery and record an actionable failure when
progress is impossible. An ordinary task report must not become a user resolution
form.

**OS.** Separate durable acceptance of a resume intent from permission to execute.
A paused runtime with unsettled effects may accept the intent, while new effects
remain gated on execution certainty. Add a generic, restartable preparation step
that resolves host receipts, restores saved operation identity and asks the
appropriate execution adapter for status/result or confirmed cancellation. Join
host descendants before marking their work ended. Retain evidence and release
ownership/reservations only after settlement. Recovered successful results replay;
known failed results permit a distinct linked retry chosen by the caller. The OS
returns typed ready/waiting/failed facts, with no Git, coding task or acceptance
policy. Unknown execution is never rewritten as confirmed termination merely
because Resume was clicked. Bound recovery waits and retain a specific failure
instead of polling forever or instructing the user to reconcile journal rows.

**Coordination.** One durable request progresses through accepted, recovering,
continuing and running, or failed. OS recovery progress and the agent's workflow
outcome remain separate records linked to that request. A crash at any stage
resumes the pending request without duplicating effects or applying text twice.
Acquire the runtime's state ownership before effect preparation; HTTP locking
alone is insufficient against an external coordinator. Preserve saved grants,
configuration, budgets, cancellation and deadlines. A limit/configuration failure
is an explicit outcome, not a silent allowance reset or a fresh replacement run.

**Provider and saved-run compatibility.** Current raw HTTP adapters have no general
remote status/cancel contract; existing records may lack a recoverable handle.
Native thread/turn IDs are useful evidence, not proof of reconnect/cancel support.
Implement and verify capability-specific recovery before claiming that interrupted
provider jobs resume automatically. Unsupported unknown execution must produce a
plain, specific failure; hiding its old message alone does not meet the goal.
Changing agent modules changes graph_digest, so existing runs also need an
explicitly tested compatibility/migration path. Never ignore the saved program
pin. Preserve original manifests and effects; migrate only documented compatible
state. Arbitrary historical versions cannot be promised safe continuation.

**Implementation and verification split.** First establish generic OS intent,
recovery, restart and execution-gate contracts using a non-coding fixture. Next
implement agent run continuation and all-worker recovery against those ports.
Then connect the frontend/HTTP adapter to that service. Verify empty/nonempty
instructions, task review, known model failure, interrupted source, output recovery,
multiple workers, duplicate requests, restart at each stage, external ownership,
unknown provider work and unsupported recovery, limits and program compatibility.
End-to-end success means one click reaches actual useful agent execution without
a process/reconciliation choice, with no duplicate effects or lost work. Tests and
provider recovery are planned, not performed by this design task.
