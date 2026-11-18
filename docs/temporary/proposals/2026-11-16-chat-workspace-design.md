# PolyInference workspace UI design

16 November 2026 · Initial workspace implemented · Design source
`feature/simple-agents` at `3d39890`

Launch the first stage with `polyinference workspace CONFIG`. It includes the
three views, role-aware model selection, retained chat history, and OS
inspection across all invocations in the workspace. The workspace accepts one active
invocation at a time. Scheduler policy, preemption acknowledgements, shared
resource totals, and importing detached snapshots remain proposed. See
`docs/guides/ui.md` for the implemented controls.

The workspace is for people who use an agent in chat and want to see how their
work uses local and cloud inference. A selector in the top header switches
between **Chat**, **OS Monitoring**, and **Agent Monitoring**. Agent Monitoring
uses the Windows Task Manager pattern of a sortable process table, status
filters, expandable groups, and details for the selected row.

## Workspace navigation

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ PolyInference           [Chat]  OS Monitoring  Agent Monitoring                  │
├──────────────────────┬───────────────────────────────────────────────────────────┤
│ + New chat           │ Compare deployment options                                │
│                      │                                                           │
│ Recent chats         │ You                                                       │
│ Compare deployment   │ Compare these two deployment options.                     │
│ Review team notes    │                                                           │
│                      │ Supervisor · Local A + Cloud B · Normal                   │
│                      │ Local worker waiting for a slot   View processes          │
│                      │                                                           │
│                      │ ┌───────────────────────────────────────────────────────┐ │
│                      │ │ Write a message…                                      │ │
│                      │ │ Supervisor ▾  Models ▾  Scheduling: Normal ▾          │ │
│                      │ │ Attach                                           Send │ │
│                      │ └───────────────────────────────────────────────────────┘ │
└──────────────────────┴───────────────────────────────────────────────────────────┘
```

The selector stays in the header above all three views and clearly marks the
active view, shown in brackets in the wireframes. In **Chat**, the Codex-style
sidebar holds **New chat** and **Recent chats**. Switching views preserves the
selected conversation and composer draft. **View processes** selects **Agent
Monitoring** and filters the table to that reply's invocation, with a link
back to the reply. **OS Monitoring** links a resource pool or blocker to the
matching rows in **Agent Monitoring**. On narrow windows, the chat sidebar and
process inspector can open as drawers.

| Destination | Default scope | What the user can see |
| --- | --- | --- |
| Chat | Selected conversation | Messages, agent and model choices, scheduling preference, and progress for each invocation. |
| OS Monitoring | All retained and active workspace invocations | System state, configured capacity, live reservations and waiters, reported usage, and retained holds. |
| Agent Monitoring | Work visible to the selected scope | Running, preempted, and finished processes across chats and runs the viewer can access. |

## Chat, agent selection, and model selection

The composer puts **Agent**, **Model** or **Models**, and **Scheduling** side
by side. Default to Simple when available. The agent menu describes each
workflow and shows the model roles it needs. The model menu changes with
the selected workflow.

| Agent | Picker description | Expected roles |
| --- | --- | --- |
| Simple | Answer a question, optionally using supplied documents | One general model, local or cloud, and optional document lookup |
| Supervisor | Plan, delegate, and combine results | Cloud planner and synthesis, local worker |
| Research | Find evidence in supplied documents and cite it | Cloud lead and report, local extraction |
| Writer | Draft, evaluate, and revise | Cloud planning and evaluation, local draft and revision |

For **Simple**, show a single **Model** menu. List eligible models under
**Local** and **Cloud**, with the configured model name for each option.
Use the configured `general` binding as the initial choice when eligible.
Selecting either option binds `general` to that endpoint for every model
step of the next invocation. The adapter still requires the `local` role
for its brokered document lookup. A cloud selection needs that role
configured but uses no local inference. The graph can include returned
excerpts in a later cloud prompt when data policy permits.

For **Supervisor**, **Research**, and **Writer**, show a **Models** menu
with one local choice and one cloud choice. Name the steps beside each
field. For example, Supervisor shows **Local worker** and **Cloud planner
and synthesis**. Research uses **Local extraction** and **Cloud lead and
report**. Writer uses **Local drafting and revision** and **Cloud planning
and evaluation**. These graphs require distinct local and cloud endpoints
with those locations declared in configuration. Every step using a given
role uses the model selected for that role.

```text
Simple · Model                      Supervisor · Models
  Local  ○ Local A                    Local worker               Local A ▾
  Cloud  ● Cloud B                    Cloud planner + synthesis  Cloud B ▾
```

Model names in the wireframes are illustrative. Start with the two
configured endpoints from V1 `RuntimeConfig`, which has one model per
endpoint. A field with a single compatible model can show its value
directly. Use the configured model name and declared location in the menu.
An explicit `--sim-haiku` launch offers the simulated local role as
**Cloud (local stand-in)** and still validates cloud data permission.
Any additional model profiles come from endpoint settings and must
resolve into the same two slots in a fresh configuration. The picker
offers raw-text or native Codex subscription endpoints that match the role and applicable data
policy. Keep endpoint URLs and credentials in settings. Explain blocked
choices and require a valid selection before Send. Show the destinations
for prompts and any attached document excerpts, including when an agent
switch changes which roles will receive them.

Each Send creates a fresh invocation and pins the agent, model and endpoint
for each role, effective configuration, input references, and scheduling
preference. A model change applies to the next Send. Show the pinned choices
on the reply and the recorded model and binding for each inference attempt
in Agent Monitoring. The app owns the conversation transcript and
explicitly selects any prior messages to pass as
context. The four shipped graphs currently return a final answer artifact per
CLI invocation. General multi-turn continuation, provider streaming, and
generic Resume require separate support. See `docs/modules/general-agents.md`.

While work is underway, show one changing line beside the reply using the
invocation's recorded progress, for example **Cloud planner running** or
**Local worker preempted**. If more than one process is active, summarize the
counts and link to the full list. A finished planner can coexist with an
unfinished reply. Display the final reply when the application records its
answer artifact.

## OS Monitoring

Start with workspace status and a freshness indicator. Show local and cloud
binding capacity from the current launch configuration, live reservations and
waiters, provider-reported tokens across retained invocations, and retained
holds. Include one total per native session and report missing usage separately.
Explain the type of wait, such as a local slot, cloud quota, or a held permit.
Use **Provider managed**, **Estimate**, or **Unavailable** where appropriate.
Selecting a pool opens the matching processes, including any that still hold
resources during suspension or reconciliation.

Show the coverage of the current view across the workspace's journals.
Shared totals require an authoritative shared pool or account
identity, with aliases counted once. Provider observations carry their own
timestamps. Keep endpoint configuration, capacity ceilings, and budgets in
operator settings, with inspection available in OS Monitoring. The current OS
projection and the proposed shared mechanisms are described in
`docs/modules/inspection.md` and
`docs/temporary/proposals/2026-11-08-scheduler-os-support.md`.

```text
PolyInference           Chat  [OS Monitoring]  Agent Monitoring
────────────────────────────────────────────────────────────────────────
Observed at 10:42:07 · All workspace invocations

Workspace idle · 4 finished processes · 0 retained holds

Binding           Live reserved / configured slots    Reported tokens
Local inference   0 / 1                               120
Cloud             0 / 1                               8,410
```

## Agent Monitoring

Use a Task Manager style table. The default **All** view puts active and
waiting work first, expands the selected invocation, and retains recent
finished rows. Top filters show **All**, **Running**, **Preempted**, **Waiting**,
and **Finished**, with counts for the current scope and search. Waiting includes
scheduler, resource, dependency, and user waits. All also includes ready, paused,
and pending preemption rows. Search by step, process ID, invocation, agent, or
model. Filter by Cloud/Local binding
and optionally group by binding. Group by invocation by default and nest
processes only where the OS records parent relationships.

```text
PolyInference           Chat  OS Monitoring  [Agent Monitoring]
────────────────────────────────────────────────────────────────────────
Processes   [All] [Running 1] [Preempted 1] [Waiting 1] [Finished 2]
            [All bindings ▾] [Search name or ID…]   Live · updated just now

Process / invocation       Binding  Status              Latest detail
▾ Compare deployment
  Cloud planner            Cloud    ■ Finished          Succeeded · 10:41
  Local worker             Local    ‖ Preempted         OS confirmed · 10:42
▾ Incident summary
  Extract notes            Local    ● Running           Inference in progress
  Prepare report           Cloud    ◷ Waiting           Waiting for dependency
▾ Review team notes
  Answer                   Cloud    ■ Finished          Failed · input rejected

Local worker   p-184
Preempt requested 10:42:05 → OS suspended 10:42:07
Local inference slot released · continuation retained
[View invocation]   [View OS resource pool]
```

The wireframe uses illustrative data. Default columns are step/role, binding,
status, time in state, and latest reason. The selected row exposes process ID,
parent and invocation IDs, current phase, configured model/endpoint, reported
destination when available, and a timestamped lifecycle including decisions and
OS acknowledgements. Usage columns are optional and label units, scope, and
provenance. Show a provider thread or session ID only when the provider exposes
one. Open the existing inspector for exact model attempts, artifacts, and
retained receipts. Chat, invocation, OS process, and model attempt each keep
their own identity.

Keep selection and scroll position while the table updates. On narrow windows
retain step, binding, and status, with the other fields accessible in the
inspector. Pair text with distinct icons and use color only as a secondary cue.
Show observations with their capture time. Retained invocations reopen from
their durable records with read-only controls. Detached snapshot import can
use the same status projection when supported.

### Status labels and evidence

| Label | Show it when | Detail in the table or inspector |
| --- | --- | --- |
| Queued by scheduler | A current scheduler record defers an eligible process. | Decision time and recorded reason. |
| Waiting for resource | The OS records a resource wait, including after scheduler admission. | Pool or quota, time waiting, blocker if known. |
| Waiting | The application or OS records a dependency, user, or other explicit wait. | What the process is waiting for. |
| Ready | The process is registered and ready, with no recorded execution or explicit wait yet. | Ready since; any scheduler decision if available. |
| Running | The OS records active execution. An in-flight model or tool call can be shown here when the OS observes it. | Current phase, binding, and elapsed time. |
| Preemption requested | A current scheduler request awaits a matching OS suspension acknowledgement. | Draining or awaiting a safe boundary. Preserve visible resource holds. |
| Preempted | The OS acknowledges suspension for that scheduler request and process generation. | Time suspended, continuation state, and what the OS says was released or retained. Keep the row and its identity through readmission. |
| Paused | The OS records a pause from another cause or lacks evidence linking it to scheduler preemption. | Recorded cause. A rejected or unsupported preemption appears in the decision history. |
| Finished | The OS records a terminal outcome. | **Succeeded**, **Failed**, or **Cancelled**, with end time and any remaining cleanup. |
| Execution unconfirmed | The OS records an unresolved effect or cannot confirm the extent of active execution. | Surface this as an attention badge alongside any known process state. Include the held resources and last observation. |

Where the OS awaits a matching model result, show observed in-flight work as
Running and name the operation. A process waiting for admission or an
unreconciled result keeps its corresponding wait or attention state. An OS
acknowledgement must match the request and current process generation to move
**Preemption requested** to **Preempted**. A process that finishes while
preemption is pending moves to **Finished** with its actual outcome. If a preempted process is
readmitted, show its observed wait or execution state on the same row and
retain the preemption in its timeline. Resource release is tracked separately
from process lifecycle and requires its own OS evidence.

## Scheduling preferences

The composer offers **Background**, **Normal**, **Urgent**, and **Custom**.
Normal is the default. Show the resolved values in the menu and on the saved
invocation. These are proposed UI mappings to the scheduler design's two
inputs.

| Preset | Importance (0–5) | Time sensitivity (0–5) |
| --- | --- | --- |
| Background | 1 | 0 |
| Normal | 2 | 2 |
| Urgent | 2 | 5 |
| Custom | User selected | User selected |

Importance affects process ordering. Time sensitivity asks for earlier
consideration. Child processes inherit or narrow the invocation's preferences
and still receive individual decisions. Changing the composer preference
applies to the next Send. Scheduler decisions and submitted processes are
read-only in the monitors. The scheduler can admit, defer, or
request preemption for one process. The OS owns resource allocation,
authorized placement, quota enforcement, and confirmed release. Original
budgets and deadlines apply regardless of the preset. See
`docs/temporary/proposals/2026-11-08-scheduler-process-policy.md`.

## Review scenarios and delivery order

1. Run Simple in two fresh invocations, first on the configured local model
   and then on the configured cloud model. The reply and its process details
   identify the corresponding endpoint. With document lookup enabled, the
   lookup appears as a tool step. Under a local-only policy, explain why the
   cloud option is unavailable and keep a compatible local choice.
2. Open a new chat, choose Supervisor, confirm the local and cloud models,
   and send once. Observe cloud planning,
   a local worker waiting for a slot, and cloud synthesis. Follow **View
   processes** into **Agent Monitoring**, then use the top selector to return
   to **Chat** and find the same reply and draft. The mixed agent requires
   both model roles. Changing the composer agent, model, or preset after
   Send applies to the next invocation.
3. Select **Agent Monitoring** while two invocations compete for capacity.
   The UI shows a scheduler-deferred process separately from one admitted but
   waiting for a local slot. Follow the slot link into **OS Monitoring** and
   inspect the same pool.
4. Record a preemption request while a provider operation is still active. The
   row displays **Preemption requested** with its reservation. On matching OS
   suspension acknowledgement, it becomes **Preempted**. Readmitting it keeps
   the process ID. A missing or stale acknowledgement preserves the current
   state and any unresolved hold.
5. Finish processes with success, failure, and cancellation. Each appears in
   **Finished** with its outcome, and a retained hold remains visible if
   cleanup is uncertain. A finished child does not complete its chat reply.
6. Load the same run from a saved snapshot or with partial telemetry. Confirm
   the capture time, status labels, and which resource facts are unavailable.

The initial stage implements agent and model selection for fresh invocations
and read-only monitoring across workspace OS records. The Scheduling picker
indicates that the scheduler is unavailable. Enable it and the scheduler
status labels when the OS and scheduler can supply durable preference,
decision, and acknowledgement records. Enable shared resource totals when
the OS can report their authoritative scope.
