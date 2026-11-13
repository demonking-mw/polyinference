# Early OS and agent failure investigation

## OS/agent failure investigation — 2026-10-18

Status: report items 1, 2, 4, 5, 6 and 7 implemented, together with OS output
delivery and verified support for non-coding agents. Report items 3 and 8 remain
open in the historical report below; item 8 is now corrected by
`development-docs/FIXES.md#fix-0084`, and item 3 by `development-docs/FIXES.md#fix-0086`.
This file tracks current-version fixes; historical evidence remains below.

### Deferred work recorded before implementation

The numbered implementation report and the OSAG identifiers below use different
numbering. The user's selected report items map to request framing (OSAG-01 and
OSAG-06), write authority (OSAG-05), loop termination (OSAG-03), requirement
handoffs, provider diagnostics (OSAG-02), and explicit recovery (OSAG-04).

- **Report item 3 — P1: separate setup checks from final product acceptance.**
  Implemented by `development-docs/FIXES.md#fix-0086`. Historical problem: the setup-selected
  `development-prerequisites` command checks Node, npm and ignore rules, and the
  same immutable selection is reused for tasks and final acceptance. Introduce
  distinct prerequisite, task and final acceptance policies so a setup-only tree
  cannot satisfy the product objective. Preserve check provenance and prevent
  workers from weakening acceptance. Acceptance: a prerequisite-only repository
  cannot finish a game objective; launch, gameplay and world/player persistence
  requirements have corresponding final evidence.
- **Report item 8 / OSAG-07 — P2: preserve historical development starts.**
  Implemented by `development-docs/FIXES.md#fix-0084`. Historical problem: started tasks later cancelled as
  superseded disappear from accounting and allocation history. Count durable
  starts independently of final disposition; never-started cancellations must
  remain excluded. Acceptance: this incident counts four development starts,
  and role allocation uses the same documented historical basis.

Implementation must keep OS capabilities independent of coding-agent policy.
Artifact-only and read-only agents must be able to terminate successfully without
writing files, creating Git commits, running coding checks or publishing a code
workspace. Output delivery must use explicit runtime capabilities and must not
publish failed or unassessed worker work.

### Implementation and whole-run audit

Product search result: **no Minecraft implementation found** in the target folder,
the run workspaces/snapshots, either archived Minecraft run, or any private Git
commit, including unreferenced objects. The supplied export, archive and durable
database (including WAL) contain the same records. The only successful file writes
were one `.gitignore` update and four README roadmaps, retained as twelve workspace
copies across generations 1–3. All four workers failed on their first reconciliation
request. The earlier archive failed during startup before agent execution.

The selected implementation now includes:

- OS artifact-file delivery with an explicit destination, baseline conflict checks,
  durable intent/receipt, and replay protection. The coding agent delivers only a
  finally accepted tree. New projects use their selected directory; existing Git
  repositories use `STATE/result` unless configured otherwise.
- A separate `RuntimeConfig`, generic process registration/termination, and native
  protocol registration by the caller. Non-coding HTTP/native agents are covered
  without writes, coding checks, task reports or Git. Coding cancellation drain
  policy moved out of the OS process implementation.
- OSAG-01/06: explicit final host phase requests and strict Anthropic request fixtures.
- OSAG-05: effective project/explicit authority in planning context, with bounded
  individual worker grants retained.
- OSAG-03: immediate termination on non-actionable plans, stable review input
  comparison excluding rewritten memory, known model failures pausing the agent,
  and an OS circuit for repeated permanent model failures across operation names.
  Known failures drain other started workers. Stopped drivers cannot keep the
  controller spinning; OS driver deadlines and cancellation-before-submission
  are covered without requiring file output.
- Requirement handoffs: the full user objective accompanies every worker request;
  prompts preserve product constraints. The first historical roadmap had drifted
  into first-person movement and chunk-mesh rendering after losing the 2D requirement.
  Explicit user amendments remain ordered and pinned to each task's plan. Steering
  arriving during file delivery invalidates completion until a new review and
  acceptance incorporate it; delivery cannot acknowledge an older objective.
- OSAG-02: bounded sanitized provider diagnostics, error categories/request IDs,
  retry metadata, and separate attempted-backend information on failure.
- OSAG-04: explicit linked model recovery through `retry-model`, preserving private
  edits and rebuilding reconciliation state. Immutable original results, unknown
  effect exclusion, finite allowances, and program/configuration pins remain intact.
  Recovery activation updates its task, attempt, process and run ledger atomically;
  interruption after checkpoint preparation is recoverable. Accepted output has
  its own `retry-output` path, receipt reconciliation and verification-lease cleanup.

The historical incident is not rewritten or silently migrated. These fixes do not
create a Minecraft product retroactively. Later FIX-0086 and FIX-0084 corrections
cover report items 3 and 8 without changing historical run evidence.

Verification: the full Python suite passed with **157 passed, 1 skipped**. The
skipped frontend wrapper requires Node 18+; the default executable is Node 12.
Running the browser-script suite with the installed Node 22 passed all five tests.
The final CLI steering adjustment was additionally checked with four passing
steering/acceptance regressions. Ruff and `git diff --check` passed. Tests used
fixtures and local transports, with no live provider/model requests.

The regression scenarios include actual new-project file delivery, source-conflict
protection and delivery retry, binary/mode preservation, interrupted delivery,
lost delivery results and acceptance leases, model recovery after confirmed and
uncertain execution, interruption between recovery checkpoint and activation,
non-actionable plans, stopped drivers, worker draining, queued cancellation,
non-coding process deadlines, and steering during accepted-file delivery.

The incident exposes a likely provider compatibility bug, confirmed diagnostic and
planning-context defects, and weaknesses in recovery and accounting. The runtime
stopped publication safely, but the agent could replace interrupted tasks without
addressing the infrastructure failure that interrupted them.

### Incident and evidence

- Run: `40542ee7c378`; project: `/home/mawa/projects/testing/minecraft-v2`.
- Worker: `worker-3-document_scope_recovery_03`; task: `document_scope_recovery_03`.
- Failed operation: `model-5`, phase `reconciliation`, operation ID
  `sha256:eec4b90a22f987a45134641a34bf234cd9230abe93f31314e449857959a41001`.
- Request created: `2026-10-18T23:23:28.050576Z`; execution started:
  `23:23:28.063824Z`; finished: `23:23:28.246281Z` (about 182 ms executing).
- Result: `failed`, `EndpointError`, `Endpoint HTTP 400`, effects `known`, execution
  `confirmed_stopped`, no usage, no actual-backend metadata.
- Adjacent successful model operations identify `claude-haiku-5-5` through the
  `anthropic` protocol. The configured binding is named `local`, but its inference
  location is cloud; the binding name does not imply local inference.

Local evidence, relative to the repository root:

- State: `.polyinference/ui/runs/40542ee7c378/state/`.
- Export: `.polyinference/history/20261018T232516376230Z-03cde201338743e4804c4343a3abf5c8.json`.
- Context and output objects: `state/artifacts/<digest without sha256:>`.
- These are local diagnostic files and may not exist in another checkout. The
  investigation read the pasted operation, its referenced artifacts, this worker's
  records, run configuration, and relevant source/tests. It did not audit the whole run.

The worker's sequence was:

1. `model-0` returned an action wrapped in `<invoke_action>` tags instead of plain
   JSON. JSON parsing and union validation rejected it. A synthetic `invalid-0`
   call/result pair supplied feedback; no file tool executed for that invalid reply.
2. `model-1` recovered and called `files.list`; only `.gitignore` was present.
3. `model-2` wrote `README.md` successfully (10,690 bytes; content digest
   `sha256:c3ef4a5c32ca792ca974548235c0ec7ef022385308db68c8e92e7b8c0e4f7014`).
4. `model-3` requested `development-prerequisites`; it passed with exit code 0,
   reporting Node 22.17.1, npm 10.9.2 and required ignore rules. This was environment
   verification, not application acceptance evidence.
5. `model-4` returned `candidate`. The host preserved the private delta, acquired
   verification ownership, and materialized integration generation 2.
6. `model-5`, the first reconciliation query, received HTTP 400. No reconciliation
   reply, assessment, completion report, or publication followed for this task.
7. Cleanup restored a development view at generation 3 and released verification
   ownership. The process was paused; the task was later cancelled with
   `stop_reason=superseded_by_plan`. The README remained in the private delta and
   restored workspace. Cancellation did not mean its edits had never existed.

### OSAG-01 — P1: phase transitions produce unsupported Anthropic request framing

Confidence: request shape confirmed; exact cause of the server's 400 is a
high-confidence inference because the provider error body was discarded.

`AgentServices.context()` places current instructions and pinned inputs before
history. A completed `candidate` becomes a historical `message` without an
observation. `KernelRuntime._dispatch()` maps both `message` and `tool_call` parts
to the assistant role. The Anthropic adapter removes system messages into the
top-level system field but otherwise forwards the sequence unchanged.

All 11 referenced context artifacts were read and their SHA-256 hashes verified.
The reconstructed roles were:

```text
system, user,
assistant, user,  # invalid-output feedback pair
assistant, user,  # files.list and observation
assistant, user,  # files.write and observation
assistant, user,  # checks.run and observation
assistant        # completed candidate; nothing requests a new turn afterward
```

Haiku 5.5 rejects a final assistant turn as unsupported assistant prefill, even
with thinking disabled. See the official
[Haiku 5.5 migration guide, Replace assistant prefill](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide).
Tool loops avoid this particular problem because their observations end in a user
turn. A mandatory transition to reconciliation exposes it.

Relevant code: `src/polyinference/agent/services.py` (`context`, around line 329),
`src/polyinference/runtime/kernel.py` (message mapping, around line 474),
`src/polyinference/runtime/inference.py` (Anthropic payload, around line 190), and
`src/polyinference/agent/worker.py` (`consume` / `integrate`).

Fix direction: represent the current phase request as an explicit final user turn,
while preserving historical roles and trust boundaries. Validate model/provider
request constraints before submission. Do not strip history or reinterpret
retrieved text as instructions merely to satisfy the role constraint.

Acceptance: exercise development -> candidate -> reconciliation, reconciliation
-> checks -> assessment, and assessment repair -> reconciliation through the real
adapter. A fixture enforcing Haiku 5.5's final-role constraint should accept all
valid phase requests, without changing other providers' behavior.

### OSAG-02 — P1: provider errors lose the information needed for diagnosis and recovery

Confirmed in code and the recorded result. `HTTPInference.generate()` raises only
`Endpoint HTTP <status>` for every HTTP error, discarding the response body and
provider request ID. The kernel records a generic exception type and always sets
`retryable_after_reconciliation=False` in its generic exception handler. Services
then raise `RuntimeError` using only output text. The controller receives a string
rather than a structured infrastructure failure.

Backend metadata is created only after successful generation. Thus a request that
was submitted and rejected has `actual_backend=null`, `binding_ref=null`, and
`binding_generation=0`, despite having a known selected endpoint. These fields
must not be read as proof that no dispatch occurred.

Relevant code: `runtime/inference.py` around line 216; `runtime/kernel.py` around
lines 611 and 690; `agent/services.py` in both retained and fresh model-result paths.

Fix direction: preserve bounded, sanitized provider error code/message, HTTP status,
request ID, retry-after information, and selected endpoint/model. Keep attempted
binding information distinct from provider-confirmed execution metadata. Carry a
typed failure to the controller rather than flattening it into generic strings.
Distinguish invalid request, authentication/permission, rate limit, service failure,
and uncertain transport termination. Redact credentials and sensitive response
content; existing tests intentionally prevent raw provider details from leaking.

Acceptance: synthetic 400/401/403/429/5xx and disconnect cases retain useful safe
diagnostics and receive explicit recovery classifications. Verify sanitization and
that attempted dispatch remains visible when generation fails.

### OSAG-03 — P1: repeated infrastructure failures can bypass no-progress detection

The assignment and pinned memory already mention two earlier documentation
interruptions with HTTP 400. This worker hit another 400. That establishes repeated
symptoms; this investigation did not independently prove the earlier requests had
the same framing defect.

The controller permits safely interrupted tasks to be retired and replaced. Its
no-progress guard compares the entire review snapshot, including `all_task_ids`,
interrupted/pending task records and memory. New task IDs or rewritten notes change
the fingerprint even if the shared code, failing provider, failing phase, and
runtime configuration are unchanged. There is no equivalent recurrence guard for
the underlying infrastructure failure on this path. A sprint/query limit can stop
the loop eventually, but that is a resource limit rather than diagnosis.

Relevant code: `agent/controller.py` (`consume`, `review`, snapshot/fingerprint
around lines 396-427, and retirement around line 543).

Fix direction: track failures by a stable infrastructure signature, using structured
errors from OSAG-02, phase, model/protocol, and relevant configuration/version.
Repeated non-transient failures should pause affected dispatch and expose an
actionable blocker. Replacement IDs and memory changes must not reset recurrence.
Apply bounded backoff to genuinely transient failures rather than asking the senior
agent to solve transport errors through new coding assignments.

Acceptance: repeated equivalent failures across renamed replacement tasks stop
before consuming the sprint limit. Relevant configuration changes can allow an
explicit new attempt; unrelated failures and meaningful code progress do not
incorrectly trigger the guard.

### OSAG-04 — P1: immutable replay lacks an explicit recovery path for known failed model operations

`KernelRuntime.execute()` returns a recorded terminal result for an existing
operation. `AgentServices.model()` reuses a retained request at the same logical
step and raises again when its saved result is failed. Simply resuming the old
worker therefore does not retry this model call, even after fixing the adapter.

Returning the saved result is correct idempotency behavior. The gap is an explicit
way to supersede a definitively failed model operation with a new recovery attempt
while retaining the workspace, trajectory, and phase. Creating a whole replacement
assignment can repeat completed work. The senior's interrupted-task input also does
not directly include the preserved private delta or a structured recovery summary;
the delta exists in runtime storage, but is poorly exposed to the recovery decision.

Relevant code: `runtime/kernel.py` (`execute`, around line 221),
`agent/services.py` (`model`, around line 467), `agent/controller.py` (`drive` cleanup
and review input), and `runtime/workspace.py` (`abort`, around line 673).

Fix direction: define an explicit, audited recovery attempt with a new operation
identity linked to the failed operation, after validating its known terminal state
and corrected request intent. Preserve old records and reuse recoverable private
work. Expose recovery evidence to the controller/senior without publishing unassessed
changes. Account for restored workspace generations when resuming a phase.

Acceptance: a deterministic request failure followed by a framing fix can resume
without rewriting the completed README. Replaying the original operation still
returns its original failure. Unknown-effect operations remain blocked pending
reconciliation; recovery must not duplicate tool effects or bypass publication checks.

### OSAG-05 — P1: planning context misrepresents project-wide write authority

The recorded run configuration has `write_scope="project"` and
`allowed_write_paths=["README.md"]`. In project mode, `senior.validate()` permits
assigning additional paths; its allowlist restriction applies only in explicit
mode. However, the senior review snapshot supplies `allowed_write_paths` without
the `write_scope` that changes its meaning. The worker assignment and senior memory
then say application development requires an expanded write grant.

The worker correctly respected its own README-only assignment. The stack-level
problem is that the planner's inputs encouraged conflating that assignment with
the run's broader authority. The initial fallback list for an empty project comes
from `ui.configure_run()`; it must not be presented as the effective project-wide
ceiling when project mode is active.

Relevant code: `ui.py` around line 210; `agent/controller.py` review snapshot around
line 420; `agent/senior.py` around line 40; `agent/tasks.py` (`make_task`);
`runtime/workspace.py` (`extend_setup_scope`).

Fix direction: expose effective authority explicitly to the planner: scope mode,
whether it may assign new project-relative paths, any exclusions, and the difference
between run authority and a worker's assigned paths. Derive this from the same policy
used by validation and runtime enforcement. Do not relax individual worker scopes.

Acceptance: an empty project in project mode can receive tasks creating application
files without an invented permission blocker. Explicit mode still rejects paths
outside its grant; an existing worker cannot independently expand its assignment.

### OSAG-06 — P2: HTTP integration fixtures accept requests rejected by the real model

`tests/test_http_integration.py::test_complete_agent_over_real_http` covers both
chat and Anthropic over TCP, including the phase lifecycle. Its Anthropic fixture
checks headers and system placement, but accepts a final assistant turn and returns
200. The scripted agent in `tests/conftest.py` also ignores that restriction.
Therefore successful end-to-end tests do not establish compatibility with the
configured Haiku model. Existing Anthropic error tests cover terminal failures and
redaction, but do not exercise this rejected phase-transition request shape.

Fix direction: strengthen provider/model contract fixtures, particularly the
final-role rule implicated here. Keep protocol tests distinct from model-specific
constraints rather than pretending every Anthropic model has identical behavior.

Acceptance: demonstrate that the current request construction fails the strict
fixture, then passes after OSAG-01. Cover repairs and assert that failure does not
publish, lose the private delta, or retain verification ownership after a known stop.

### OSAG-07 — P2: superseding started tasks erases them from development accounting

Status: implemented by `development-docs/FIXES.md#fix-0084`, including pending-reservation
separation and legacy started-spec evidence. The original incident is retained below.

The export reports zero started development tasks despite this executed worker.
`agent/routing.py::accounting()` excludes every cancelled task, including tasks
which ran and were later cancelled as superseded. `allocate()` also excludes
cancelled tasks from its quota history. This can both misreport historical work and
distort the configured senior/junior allocation after recovery churn.

Fix direction: count durable starts or attempts independently of current task
disposition. Never-started cancelled tasks should stay out of the started count;
superseded tasks that actually ran must remain represented. Define whether allocation
uses started tasks or attempts and align reported metrics with that definition.

Acceptance: start a worker, interrupt it, supersede it, and verify its historical
start remains counted. Cancelling a pending task adds no start. Subsequent role
allocation follows the documented historical basis.

### Invariants to preserve and diagnostic cautions

- Publication was correctly blocked without reconciliation/assessment. Do not fix
  this incident by skipping mandatory phases or treating a candidate as success.
- The private README and its delta survived; no lost-edit or duplicate-publication
  bug was established. Cleanup released verification ownership after the known stop.
- The initial `<invoke_action>` formatting mistake recovered successfully and was
  separate from the final HTTP request failure.
- The failed query was not near its deadline: almost an hour remained. Reconstructed
  canonical message input was about 23 KB, below the conservative 96,000 input-token
  bound. No context/deadline exhaustion was indicated.
- `max_api_spend_microusd=0` is treated as no enforced spend ceiling by the current
  implementation; it does not explain this failure.
- Missing provider usage is not proof of zero consumption. The kernel conservatively
  settles unknown token usage at the reserved amount; preserve provenance and avoid
  presenting estimates as provider-reported usage.
- Suggested implementation order: OSAG-01 and OSAG-06 together; OSAG-02 before
  OSAG-03; then OSAG-04, OSAG-05, and OSAG-07. OSAG-05 can proceed independently.
