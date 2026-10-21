# Current runtime and agent wiring

Current wiring: 19 October 2026, documentation aligned 20 October 2026.
This describes the basic OS services after separating coding-agent policy.
General-agent examples are local regression fixtures, not a new agent product.

> **Edited 2026-10-20 because** full worktrees, mode-specific private candidates
> and optional OS context/output recovery supersede earlier design defaults. The
> [revision ledger](DESIGN_REVISIONS.md) records each reason, historical boundary
> and open implementation gap. No runtime behavior changes with this edit.

## In-place coding repositories

New coding runs use the actual supplied repository. `AgentConfig.repository_mode`
defaults to `in_place`; bare `RuntimeConfig` has no such workflow setting.
`agent/repository.py` implements Git policy and the application's workspace provider.
The coding app installs it with the OS's trusted `install_workspaces` bootstrap
method. No OS module imports it. The legacy private-copy provider remains available
through explicit `repository_mode: "isolated"` for existing consumers and fixtures.

Before setup edits, a read-only senior process resolves the user's Git instructions
into `coding/repository-policy`. Structured `git_policy`/`base_branch` configuration
can pin the decision. The application creates/selects a real integration branch
from current HEAD; the default is `codex/run-<state-id>`. "No new branches" also
disables worker branches and uses one editor on the current checkout. The coding
agent sends recoverable branch/policy errors back to its senior process for a
corrected decision. Attention notes reach setup without rejecting ordinary local
development; they do not authorize ignoring explicit user constraints.

Startup recovery is application policy in `agent/repository.py`, with observations
and prompts assembled by `agent/services.py` and `agent/prompts.py`. Nested project
initialization, Git selection retries and dependency preparation decisions use the
existing generic capability and record interfaces. Their diagnostics live under
`coding/` records. No OS hook, configuration field, wire contract or protocol rule
is added for this recovery flow. Other agents need no Git policy, setup task,
dependency preparation or coding acceptance checks to run or finish.

Workers check out full tracked source into linked task worktrees under the supplied
project's `.polyinference/worktrees/`. They share its actual common Git database.
The OS's `attach` method validates directory authority, ownership and write grants;
it does not infer Git branches, task policy or acceptance. Ordinary file tools cannot
address `.git` or runtime control data. The attached source view remains stable across
phase-generation changes; it is not recopied over user files.

The agent registers `coding.prepare`, `coding.commit` and `coding.publish` handlers
through the existing typed capability/effect mechanism. They own repository policy,
commit provenance, candidate scope and verified integration. Publication checks the
current root branch, HEAD, source/index cleanliness and task index before changing
the actual checkout. A candidate includes the captured integration commit and its
previous task tip; the root fast-forwards to the checked candidate. Failed/uncertain
candidates remain on real task branches. A replacement's explicit `resume_from`
names a retained candidate and receives its scoped edits with conflict checks.
The agent supplies read-only retained-source planning offers and validates exact
references/grants before dispatch; materialization rechecks current conflicts.
This adds no OS Git/source-reading capability or automatic publication authority.

Git and SQLite are separate resources: intent/outcome records and retained effects
do not make a filesystem merge atomic with report publication. A completed merge
whose report cannot be recorded is uncertain and stops further mutation.

> **Edited 2026-10-20 because** real task history and the user's actual checkout
> supersede sole-parent/provisional-all assumptions: retain the prior task tip
> when needed, integrate only successful verified candidates, and preserve
> failed/uncertain candidates for explicit repair/review (FIX-0040, R03/R04).

Generic
OS `filesystem/<canonical-resource-digest>` leases also hold advisory file locks
across independent runtimes. The agent derives the shared Git-directory identity
and owns the integration checkout for the run. External editors do not honor those
leases; detected edits or index/ref drift stop integration without overwriting them.

Attached workspaces never use private-copy directory rollback. A shell scope failure
preserves files and blocks further mutations on that workspace. Trusted shell still
has host privileges; after-command auditing is not a sandbox. The selected sandbox
or trusted execution backend retains its existing meaning.

The coding agent prepares dependencies before brokered checks. Locked npm projects
use `npm ci --ignore-scripts`; `dependency_prepare` supplies other explicit argv.
Commands still require the shell capability and its configured backend. Review and
acceptance check the root integration checkout, with source identity tied to evidence.
The OS executes commands and stores evidence; it does not select package managers.
The coding agent retains failed preparation output as an observation and continues
to configured checks so its engineers can repair and recheck prerequisites. Unknown
execution termination still stops mutation under the existing OS guarantees.

Completion updates the in-place output record without `outputs.deliver`. The agent
retains `coding/repository-summary` and sends a deterministic user message on normal
completion/failure/pause. UI, CLI status and exports include branch/commit/worktree
locations. The root stays on the integration branch; there is no automatic push,
merge-back or branch cleanup. The artifact delivery service remains optional for
other workflows.

The coding program marker is `agent-5-in-place-repository`, state schema `2.3`.
New runs require fresh state. Historical runs are not migrated or rewritten.
The OS remains `simple-os/2`; an artifact-only or workspace-none process still
requires no Git, coding task, check or code-writing finalization. MCP and shutdown
recovery are not expanded by this change. The sections below describe shared
mechanisms; private-copy details apply to the legacy optional provider.

The current agent negotiates `runtime/attached-workspace` for this layout.
Git-specific report extensions live in `agent/reports.py`; `os_contracts.py` is a
compatibility import. Git steering changes wait for started workers to drain.
An existing branch at a different commit needs a new run, preserving current
task/evidence identities.

## Responsibilities

| Function | OS responsibility | Calling agent responsibility |
| --- | --- | --- |
| Process lifecycle | Register identity, bound driver admission/deadlines, start/wait/cancel/finish and retain outputs/unfinished effects; process-limit and paused-residency gaps U03/U04 remain | Supply the program/continuation and decide what work to do; explicitly identify control processes |
| Inference | Admission, context/output bounds, provider transport, usage, durable results and uncertainty | Supply context, role binding and response grammar; interpret the result |
| Brokered tools | Check capability grants, input schema, effect class, identity and workspace preconditions; invoke the installed handler | Choose which existing capabilities to grant; supply application-specific handlers/instructions where needed |
| Workspaces and commands | Optional private file views, scoped edits, shell exclusion, source evidence, Git operations and temporary tool environments | Select paths, read/build closure and checks; request authorized scope changes |
| Records and publication | Atomic compare-and-swap, immutable objects, ownership and receipt replay | Validate application objects and install any program-specific publication policy |
| Artifacts and delivery | Store/read artifacts; deliver explicit files with baseline conflict protection | Decide which artifacts constitute the result and when it is acceptable to deliver them |
| User messages | Persist and display plain text in the UI and terminal with operation replay protection | Grant `user.notify`, decide when to speak, and supply the message content |

The OS does not require a TaskSpec, coding verdict, source edit, test or commit for
a general process to complete. A process may return artifacts or no output. The
bundled agent still requires its reconciliation, assessment and acceptance flow.

The runtime schedules bounded model operations. Token/GPU scheduling remains in
the inference server; agent continuation does not expose hidden reasoning state.

## Bootstrap and the capability boundary

The implemented guards are not complete validation of every ProcessSpec field.
Conflicting mandatory data policies/hard allocation schedules, narrower process
limits and paused-worker residency remain U01–U04 in the
[open-gap ledger](DESIGN_REVISIONS.md#open-implementation-gaps). They must be
honored or rejected; this guide does not endorse silent weakening. Current
RuntimeConfig.limits is the operation envelope, even when a stored spec differs.

Trusted application code opens `KernelRuntime`, installs its handlers/protocols,
and registers processes before issuing effects. Registration is a local Python
API, not a model-accessible operation. It does not discover tools or create MCP
servers. `src/polyinference/ports.py` defines the boundary.

A capability consists of a name, argument type, handler, effect class and whether
it requires a file workspace. Pydantic supplies the argument schema. The wire
descriptor is pinned under `runtime/capability/<name>`; changing it requires a new
state directory. Handler code is installed again on restart and is governed by
the caller's program/version pin, not serialized Python function addresses.
Native protocol definitions (schema, instructions, brokerage and workspace mode)
are likewise pinned under `runtime/agent-protocol/<name>`. Reinstalling the same
definition is valid; changing it under the same identity is rejected after restart.

For example, with an open runtime and an application-owned `ProcessSpec`:

```python
from polyinference.contracts import Wire

class Lookup(Wire):
    topic: str

async def lookup(request, arguments):
    return {"finding": arguments["topic"]}

runtime.register_capability("example.lookup", lookup, input_type=Lookup)
runtime.processes.register(spec, "local", capabilities=["example.lookup"])
runtime.register_agent_protocol(
    "example/1",
    {"type": "object", "properties": {"summary": {"type": "string"}}},
    workspace="none", brokered=True,
    instructions="Use the granted tool and return the supplied summary schema.",
)
```

The caller still constructs the existing `AgentJob` and stable `OperationRequest`.
An executable end-to-end example, including the complete spec/context/request and
real stdio transport, is `tests/test_capability_boundary.py`. A raw `ModelQuery`
does not need native protocol registration. The existing raw/native artifact-only
paths are covered by `tests/test_runtime_general.py`.

Register a process once. On restart, restore its persisted spec and continuation;
reinstall handlers and native protocols before new dispatch. Replaying a settled
operation returns its retained result before checking transient ownership. For a
model invocation with OS-selected retries, `execute(original)` projects the
effective retained attempt; every individual failed/successful effect remains
immutable. Replay follows that durable chain without another provider submission.

The bundled application's wiring is explicit:

| Handoff | Code and persisted authority |
| --- | --- |
| Bootstrap | `AgentServices.__init__` installs its two native protocols, `checks.configure`, publication policy, cancellation policy and reconciliation callback. Required registration is not skipped through optional `hasattr` checks. |
| Process creation | `AgentServices.process` builds the coding `ProcessSpec` and calls `processes.register`, supplying the capability maximum and management flag. The OS atomically writes the process, spec and mutable initial status. |
| Worker load | `agent/worker.py:load` supplies the workspace's narrower tool/check grant, paths and expansion flag. The OS atomically writes the workspace manifest and grant after materializing the private view. |
| Model input | `AgentServices.model` reads `workspaces.authority` for `write_authority`; the native adapter receives only the job's explicitly selected registered descriptors and the application's instructions. |
| Tool request | `AgentServices.capability` uses the registry's schema digest and binds workspace generation/content only for workspace capabilities. Native callbacks construct the same operation payload at the OS boundary. |
| Publication | The OS verifies capability/resource ownership, calls the installed program policy, then commits its returned batch with the receipt in one record transaction. |
| Recovery | The OS establishes effect certainty and invokes the installed reconciliation callback. The coding application changes its own task/run records; settled operations retain their original results. |

General agents use these same existing services, choosing only what they need.
The built-in `user.notify` capability takes `{"text": "Message for the user"}`
(1–16000 characters, nonblank), has effect class `shared_write`, and requires no
workspace, Git repository or coding records. Grant it in process registration and,
for native jobs, in `AgentJob.allowed_capabilities`. Direct callers use an ordinary
`CapabilityCall`. Each notification is retained under `user-message/<operation_id>`
and shown in the UI's **Messages from agents** panel, including saved snapshots.
The runtime also prints the full message immediately in the launch terminal for
both CLI and UI runs. Replay/recovery retains one message without printing it again;
a terminal failure leaves the durable UI message available. The OS does not infer
progress or verification claims. The coding sprint manager supplies its own
`user_brief` on each planning/review invocation and sends it through this capability.

They do not instantiate `AgentServices` merely to obtain OS functionality. Python
handlers and policies are trusted application bootstrap code; registration is not
a sandbox for untrusted Python plugins.

## Direct and native calls use the same authority

Direct `CapabilityCall` payloads carry the registered capability's `schema_digest`
and `effect_class`, plus an argument artifact. Use
`runtime.capabilities.get(name).schema_digest`; hashing the name is not the ABI.
The kernel rejects absent grants, changed schemas and forged effect classes before
calling the handler. Strict argument validation applies even if a provider emitted
JSON that passed its own schema check.

For native jobs, the installed protocol selects the output schema, optional
instructions and working view:

- `snapshot`: a prepared read-only Git or artifact snapshot.
- `workspace`: an existing process-owned file workspace.
- `none`: an empty private native working directory; no code workspace or Git is
  created. The historical `AgentJob.workspace_id` wire field remains present but
  is unused by this mode.

Only `AgentJob.allowed_capabilities`, checked against the process grant, are
advertised through the existing `polyinference_tool` transport envelope. Its
argument schemas come from those registered capabilities. The adapter supplies
no coding phase instructions. The bundled agent installs its own
`candidate`/`assessment`/`needs_review` instructions.

Native callbacks become ordinary journaled subordinate effects. The kernel derives
their effect class and schema digest from the capability, not model text. A stable
parent/call ID replays the original observation; changed arguments under the same
ID are rejected. A non-workspace tool does not get a fabricated file view. A
workspace tool receives the current host-issued generation/content binding.
The kernel checks generation and any supplied expected content before invoking
every registered workspace handler, including application-owned ones such as
`checks.configure`. Validation is not limited to the built-in file-tool handler.
The agent helper fills a missing host generation, but preserves an explicitly
supplied generation so stale-intent checks cannot be bypassed by refreshing it.
`generation` is host metadata only for workspace capabilities; for a capability
without a workspace it is an ordinary typed argument and participates in replay
comparison unchanged.

## Workspace grants and coding setup

Workspace creation requires a registered owner and atomically installs its
`workspace-grant/<id>` with the authoritative manifest. That grant narrows the
process capability set, specifies allowed check names, and explicitly permits or
forbids adding project-relative paths. Expansion is rejected under an explicit
filesystem scope. Current-generation, path, digest and final-delta checks remain.
An empty copied view or a read-only grant is valid; the calling agent supplies
the read/build closure it actually needs.

The coding worker's `load` passes its bounded tool/check grant to `create`.
Only project-mode setup opts into expansion. `workspaces.authority(id)` supplies
the prompt's `write_authority`, so the model sees the same permission that the
broker enforces. The OS no longer reads a TaskSpec's project-write extension.
The old wire field `task_spec_ref` and `retag_task_spec` method remain opaque
provenance references; the runtime does not interpret the referenced task.

`AgentServices` installs `checks.configure` from `agent/runtime_policy.py`.
That handler owns the initial-setup-only rule and immutable per-purpose
`setup/checks/<purpose>` selection. Its application-owned CheckSelection schema
distinguishes prerequisite, task and final acceptance checks. It registers ordinary
commands through `tools.register_check`, grants selected names to setup, and lets
`sync_setup` update the agent ledger/spec.
The OS stores immutable command definitions under `runtime/check/<name>` and
runs only granted names against the current source revision. It does not read
`task/project_setup`, `setup/completed` or `plan/`.

The agent now separates prerequisite, task and final acceptance policy (FIX-0086).
Explicit legacy config.checks remains combined task/final policy unless overridden;
setup-discovered task checks never silently authorize final completion. These
agent fields and criteria do not add coding-purpose interpretation to the OS.

## Publication and lifecycle data

`records.publish` requires a process capability grant and a currently owned
resource permit. `OperationRequest.conflict_keys` checks the actual named resources,
not an assumed coding lock. Atomicity and immutable receipts remain OS mechanisms.
Record names such as `app/run`, `report/` or `head/provisional` have no special
meaning in generic publication.

The coding agent installs a publication policy keyed by its program ID. That
policy checks the coding verification permit, broker-minted commit provenance,
expected shared head, report ownership and private-failure rules. Its updates
close starts and capture other workers when a verdict requires review, in the
same transaction as the publication. This preserves the four-worker drain path.

Publication policies must be reinstalled before new publication after restart.
A program that previously required a policy must not silently fall back to
generic publication while its handler is absent. Already committed receipts
remain replayable independently of retired permits.
`register_publication_policy` pins the requirement under
`runtime/publication-policy/<program_id>`. Missing code produces a known failed
new publication without changing the batch. Installing the handler afterward does
not rewrite that operation's failure: retry with a new operation/logical identity.

The agent also owns `TaskAttempt` validation. `task_attempt` validates the updated
value for park, publish, retirement, recovery and setup transitions. Human notes
are retained as artifacts through `polyinference/stop-detail`; `stop_reason`
contains a bounded code. Existing invalid long notes can be retained while the
attempt is retired. Generic OS storage does not validate this application schema.

Role names do not confer OS privileges. Management/reserve treatment is explicit;
`control_token_reserve` is an OS resource setting. `AgentConfig` accepts the former
`review_token_reserve` spelling as an alias and preserves coding defaults. Bare
`RuntimeConfig` has no coding phase reserve or predefined senior/worker roles.

## Context preparation and output recovery

The OS schema and all exported settings are documented together in
[AGENT_SETTINGS.md](AGENT_SETTINGS.md). Definitions live in
`system_settings.py`; the coding agent's defaults and UI choices live together in
`agent/system_settings.py`. JSON examples group OS preferences under `system`.

`runtime/context.py` measures the known final adapter request. Hard input/output
bounds, completion checks, effect certainty and receipts always apply. Optional
`auto_deal_context` allows whole optional groups to be omitted; independently
optional `auto_compaction` permits derived summaries only for explicitly eligible
blocks. Runtime defaults can be overridden per process and request. Manual,
automatic and hybrid agents use the same resource and authority guards. Original
memory/artifacts are immutable, summary calls inherit the same binding/grants,
and canonical memory remains agent-owned.

Confirmed output cutoffs and detectable completed overages use bounded OS
smaller-response recovery under the declared protocol. Feedback is remeasured;
new intents are charged without rewriting original failures. Unknown termination
requires reconciliation; native jobs with brokered effects are not blindly
replayed. Generic feedback preserves the caller's declared protocol and asks for
smaller visible response content, including for plain-text callers (FIX-0085).
Native hard generation-token limits remain unsupported and can be made
a pre-submission rejection through the strict enforcement requirement.

The agent still owns block semantics, canonical memory, grammar correction,
meaningful task/output units and acceptance. The coding agent separately retains
authorized interrupted edits under `coding/interrupted/`, exposes
`preserved_source_ref`, and accepts explicit `resume_from` reuse after scope and
base-conflict checks. This does not introduce Git policy into the OS.

## Bounded inference retries

The OS's `runtime/model_retries.py` retries eligible one-off inference failures on
either binding. `model_call_retries` defaults to one extra attempt (range 1–3);
`model_retry_delay_ms` defaults to 100 and `model_retry_max_delay_ms` to 60000.
Backoff grows exponentially and respects Retry-After. A wait that cannot fit the
configured allowance or original deadline escalates without resubmitting early.

Received empty/malformed responses, temporary service/rate-limit rejections,
known-unsubmitted connection failures and briefly full admission queues qualify.
Deterministic input/auth/grant failures do not. Submitted disconnects/timeouts
remain uncertain. Native jobs qualify only after known termination and before
any brokered effect; permission failures, cancellation and unbrokered mutations
remain stops. The application owns grammar correction; confirmed output-limit
adaptation is now OS-owned as described above. This generic OS service does not
choose coding actions or checks.

Retries retain the original context, role routing, deadline, limits and authority.
Every attempt has a new request/effect identity and its own charged reservation;
normal dispatch guards, cancellation and finishing reserves still apply. Internal
requests require the `runtime/model-retries` feature at version `1`.
`model-retry/<root>/<attempt>` retains the selected intent and absolute delay;
`model-retry-outcome/<root>` identifies the effective result and recovery reason.
Original per-attempt results are never rewritten. OS retries do not consume or
reset the caller's separate explicit/adaptive recovery allowance.

The permanent-failure circuit includes the pinned request intent so unrelated
invalid inputs cannot disable healthy requests. Successful explicit correction
clears the repaired intent's counter. Repeated identical bad inputs remain bounded.

These added configuration fields change the configuration pin. Use fresh state;
historical runs are not migrated or automatically resumed. The core wire schemas
and frozen proposal examples are unchanged. See the
[pause audit and verification limits](../../development-docs/pause-retry-audit-2026-10-20.md).

## Diagnosing a boundary failure

| Observation | Owner and next inspection |
| --- | --- |
| Capability exceeds process/workspace grant | OS rejected the requested authority. Compare the process capability list, `workspace-grant/<id>` and `workspaces.authority(id)` with the calling agent's request. Registration alone grants no process permission. |
| Schema/effect mismatch or strict argument error | OS rejected an invocation before the handler ran. Use the installed descriptor/digest; inspect the request's argument artifact. The provider's JSON acceptance does not override this check. |
| Stale workspace generation/content | OS rejected a stale view. Inspect the manifest and request binding; the agent must build a new intent from its current view rather than alter an old operation. |
| Reinstall publication policy | Bootstrap is incomplete after restart. Recreate the owning application's services before new publication; settled receipt replay remains available. |
| Coding commit/report invariant rejected | The application publication hook rejected the candidate. Inspect the verification permit, expected head and minted commit/report provenance; generic record publication does not impose this coding policy. |
| Long review/exception note | Agent lifecycle data. Inspect `polyinference/stop-detail` on the attempt and the task's diagnostic/history. The note is not a permission grant or an OS error code. |
| `UncertainEffect` / unknown execution | OS cannot prove the effects ended. Inspect the original effect and reconciliation evidence before new work; a missing local connection is insufficient. |

An application `needs_review` reply is a request to its controller. An OS process
may be parked/paused while the application reviews it. The run's `app/run.status`
and blocker are coding-application state; they are not a universal OS verdict that
the requested objective failed. Generic agents define their own completion policy.

## Failure, replay and compatibility

The basic execution rules are unchanged: stable IDs do not execute twice; source
scope checks remain; observer failures do not replace primary failures; and a
disconnect or local transport kill does not establish remote termination. An
exception during an external-write handler or result recording is uncertain,
so it cannot be silently repeated as a known failed tool invocation.

The kernel compatibility marker is `simple-os/2`, with coding program
`agent-5-in-place-repository` and state schema `2.3`. This identifies changed
registration/grant wiring within the current basic function set. It does not
introduce the planned next-version integration platform. Use new run/state
directories with this implementation. Older runs retain their original records
and require their pinned implementation; this change performs no migration.

The existing function set has the following regression evidence:

| Function | General-agent coverage | Coding-agent coverage |
| --- | --- | --- |
| Process start/wait/cancel/finish | `test_runtime_general.py`: artifact-only completion, terminal state, cancellation and driver deadline; `test_capability_boundary.py`: role names grant no management authority | `test_os.py`, `test_regressions.py`: bounded workers, cancellation, drain and terminal records |
| Inference and native output | `test_runtime_general.py`: raw/native non-coding output; `test_capability_boundary.py`: real stdio with app-owned schema/instructions and no code workspace | `test_native_worker.py`, `test_endpoints.py`, `test_http_integration.py`: coding phases and provider transport paths |
| Tool dispatch | `test_capability_boundary.py`: custom typed tool, denied grants/schema/effect/arguments, callback replay, ordinary `generation` data, workspace source preconditions and external-write uncertainty | `test_setup_tools.py`, `test_runtime.py`: file/shell/check calls, stale requests, scope and setup handoffs |
| Atomic publication | `test_capability_boundary.py`: unrelated application record names and resource permit, policy missing after restart, reinstallation and immutable failed outcomes | `test_os.py`, `test_recovery.py`, `test_regressions.py`: commit provenance, private failure, shared heads, receipts and replay |
| Artifacts and file delivery | `test_outputs.py`: explicit arbitrary file artifacts, baseline conflicts and interrupted delivery | `test_recovery.py`, `test_ui.py`: accepted-tree delivery, receipt recovery and exported evidence |
| Application lifecycle data | No coding task/attempt/report records are required by the general fixtures | `test_agent_transitions.py`: long review notes, old invalid attempts, setup retirement, replacement and replay; `test_setup_tools.py`: setup/check policy |

These tests use local transports and disposable repositories. The native fixture
exercises the actual adapter wire code, but does not claim fresh live-provider or
live-bubblewrap validation. See
[current-iteration results](../../development-docs/current-iter-issues.md) for the
final test counts and remaining deferred audit items.
