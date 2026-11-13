# Repository integration and separation of coding policy

## In-place coding repositories — 2026-10-19

The coding agent now uses the supplied actual repository by default. The proposal
is in-place-repository-plan.md (`docs/temporary/proposals/2026-10-19-in-place-repository-plan.md`); current maintenance
instructions and the agent/OS split are in
RUNTIME_BOUNDARY.md (`design-docs/simplified-os/boundary/repository.md#in-place-coding-repositories`).
Existing unrelated working-tree changes were preserved and are not attributed to
this implementation.

- `agent/repository.py` owns instruction resolution, actual Git initialization,
  integration/task branches, linked worktrees, scoped commits, failed-candidate
  reuse, dependency preparation, verified integration and deterministic reporting.
  The coding app installs it explicitly; runtime modules do not import it.
- Defaults create a unique branch from current HEAD. Explicit current-branch and
  no-new-branch instructions disable task branches and serialize editing. Named
  branches override the generated name. Later Git steering waits for active workers
  to drain. Changing to an existing branch at another commit requires a new run,
  preserving the task/evidence baseline. Unsupported actions produce a blocker.
- OS additions are attached directory resources, authority/content checks, mutation
  blocking after attached-workspace scope failure, generic cross-runtime filesystem
  leases, and trusted workspace-provider/publication bootstrap entry points.
  Generic raw/native agents still need no Git or coding workspace. No MCP platform,
  research-agent product or expanded shutdown recovery was added.
- Passing candidates update the actual root checkout before overall completion.
  Failed/uncertain candidates remain on real task branches and worktrees. Root/task
  branch, HEAD, index and source drift are checked before integration. Attached
  failures do not invoke destructive private-copy rollback. File capabilities cannot
  address Git/runtime control data; trusted shell retains its documented host access.
- Git and SQLite remain separate resources. The coding publication policy requires
  a real-integration receipt before advancing its recorded head. A completed merge
  whose report cannot be recorded is uncertain; record CAS does not make Git atomic.
- Review and acceptance check the integration checkout. The agent prepares locked
  npm dependencies or an explicit `dependency_prepare` argv through bounded shell
  capabilities. Granted source still takes precedence over generated outputs.
- The agent reports original/current/integration branches, commit and unfinished
  worker locations when stopping normally. UI, CLI status and JSON expose them;
  patch export reads the actual Git database. Acceptance requires no final copy-back.
  Optional artifact delivery remains available to other workflows.
- `repository_mode: "isolated"` explicitly retains the legacy private-copy path.
  Existing protocol fixtures select it; dedicated real-Git and default-UI tests
  exercise the new default. New coding runs use `agent-5-in-place-repository`,
  state schema `2.3`, and require fresh state. Historical runs were not migrated.

Verification uses disposable repositories and local provider fixtures: concurrent
merges, current/named branch overrides, policy inference before mutation, fresh
setup, failed-candidate handoff, external/staged file preservation, cross-run leases,
dependency preparation, steering, source/output classification, CLI export, default
UI providers and raw/native non-coding agents. No live-model or network npm
validation is claimed.

Verification completed in WSL using `.venv-linux` and Linux Node/npm 22:
`python -m pytest -q --tb=short --maxfail=3` passed **248 tests in 414.76 s**,
with no skips. The final immutable-native-snapshot metadata guard was then
verified with its new regression, native-worker, general-agent and capability
boundary suites: **27 passed in 17.47 s**. Ruff and `git diff --check` pass;
Git retains the pre-existing CRLF normalization notice for `test_setup_tools.py`.

## Coding policy separated from the existing OS functions — 2026-10-19

Status: implemented and verified: **201 tests passed**. This section
supersedes the implementation status of audit items 1, 2 and 6 below. The scope is
the current basic function set working for both a coding agent and a general
agent. There is no new research-agent product, MCP integration, discovery service,
or next-version OS platform in this change. Existing unrelated dirty files are
not attributed to this work.

The detailed maintenance guide is
Current runtime and agent wiring (`design-docs/simplified-os/RUNTIME_BOUNDARY.md`).
It documents registration order, the authority records, each agent/OS handoff,
failure ownership, restart requirements and compatibility. README and the OS
runbook/design reading routes link to it.

### What moved, and why

The computer-OS analogy now governs the actual call path: an agent program chooses
its task protocol and policy; the OS authenticates a process's requested operation,
enforces its authority and resource bounds, dispatches the installed handler, and
retains the outcome. Expensive bounded execution is inference; the inference
server still schedules tokens/GPU work.

- **Capability ABI and grants (OS mechanism).** `runtime/capabilities.py` registers
  typed arguments, effect class and whether a file workspace is required.
  Definitions are pinned across restart. The process grants the maximum set;
  `workspace-grant/<id>` narrows it, carries check names and explicitly controls
  path expansion. Registration is trusted local bootstrap, not permission for
  every model/process to call a tool. Direct and native calls use this same ABI.
- **Native protocol and tool exposure (agent/driver boundary).** The app-server
  driver builds its advertised tool schema from the selected descriptors instead
  of a hard-coded coding-tool list. The agent supplies its reply schema and phase
  instructions. `workspace="none"` uses an empty private native directory without
  a TaskSpec, Git store or file workspace. Native protocol definitions are pinned
  as well as capability definitions. Call IDs become durable subordinate effects;
  identical callbacks replay and changed arguments are rejected.
- **Workspace and checks (OS resources, agent selection).** The runtime no longer
  reads `task/project_setup`, `setup/completed`, `setup/checks`, `plan/` or a TaskSpec
  project-write extension to decide authority. `agent/runtime_policy.py` implements
  initial-setup check selection. It registers immutable command resources and
  updates the explicit grant. Worker load sets project expansion only for setup
  in project mode; prompts read the effective grant through `write_authority`.
  Empty/read-only file views are valid; callers select the required source closure.
- **Publication (generic transaction, coding invariants).** The OS checks the
  actual named resource/permit and performs atomic expected-version publication.
  It does not interpret `app/run`, `report/` or `head/provisional`. The coding app
  installs a policy for verification ownership, broker-minted commits/current
  parents, report ownership and private-failure rules. The same transaction still
  closes starts and captures outstanding workers when review is required.
- **Lifecycle/limits (OS identity, agent workflow).** A role called `senior` does
  not grant management privileges. The app passes the management flag explicitly;
  bare `RuntimeConfig` has generic roles/limits and zero control reserve. Coding
  defaults stay in `AgentConfig`; the old `review_token_reserve` spelling remains
  an input alias. Generic processes may finish with artifacts or no output.
- **Attempt updates (agent bug).** `AgentServices.task_attempt` validates the new
  record, normalizes prose to bounded reason codes and preserves full diagnostics
  in an artifact referenced by `polyinference/stop-detail`. Park, exception,
  cancellation, retirement, publication, setup retagging and recovery use that
  boundary. It also normalizes old invalid reasons while retiring a task. This
  fixes the 317-character interruption/retirement crash investigated below without
  teaching generic OS storage the coding application's schema.

### Wiring defects caught while making the boundary explicit

1. Moving `checks.configure` out of the file-tool implementation would otherwise
   bypass its old generation/content preconditions. Those checks now run in the
   kernel for **every registered workspace handler**, before handler dispatch.
   Agent-created requests bind current generation and content for workspace
   capabilities, including commit/private retention. Non-workspace capabilities
   do not inherit a workspace merely because the caller's graph state has one.
   The existing stale-view regression caught an initial helper change that
   replaced an explicitly supplied generation with the current value. The helper
   now fills only a missing generation, preserving explicit stale-intent rejection.
2. A non-workspace tool may legitimately have an argument named `generation`.
   Callback replay previously stripped that name unconditionally as workspace
   metadata. It is now preserved for non-workspace tools; the real stdio fixture
   sends it on a duplicated callback and verifies one handler execution.
3. A program's publication callback was originally only in memory. On restart,
   omitting app bootstrap could silently fall back to generic publication. The OS
   now persists the requirement under `runtime/publication-policy/<program_id>`
   and refuses new publication until the handler is reinstalled. No application
   data changes on rejection. Completed effects/receipts still replay; installing
   a handler does not change a previously failed operation's recorded result.
4. The coding app manually constructed process/status records separately from
   `Processes.register`. It now uses the same atomic OS registration as general
   agents, passing its explicit maximum capabilities and management flag. The
   runtime ports declare the services and callbacks actually used by bootstrap;
   required registrations no longer silently disappear behind optional checks.
5. Updated task-attempt records were often created with unvalidated
   `model_copy(update=...)`; old invalid notes could also fail before retirement
   replaced them. The application write boundary validates the merged value and
   retains diagnostics, and cancelled setup is not resurrected on the next run.

### Verification and practical limits

- `tests/test_capability_boundary.py`: typed grant/schema/effect/argument denials;
  a real app-server stdio transport with a non-coding output grammar/tool, ordinary
  `generation` data, duplicate replay and rejected arguments; generic publication
  under an unrelated resource name; external-write uncertainty; role privilege
  isolation; capability/protocol ABI checks across restart; missing-publication-
  policy restart refusal/reinstallation; workspace handler source preconditions.
- `tests/test_agent_transitions.py`: long valid review note, normal and injected
  old-invalid attempt data, setup authority visibility, senior replacement,
  complete diagnostic retention and replay without duplicate activation.
- Existing coverage exercises coding setup/check selection, native workers,
  publication guards, failed-worker drain, scope/isolation, cancellation,
  inference bounds, recovery, outputs and UI/export paths. Fixtures that depended
  on implicit TaskSpec privileges were changed to configure explicit grants.
- Final complete suite: **201 passed in 330.58 seconds**, using
  `.venv-linux/bin/python -m pytest -q --tb=short --maxfail=3` in WSL. The focused
  boundary/transition/UI checks also passed (**14 tests**). During validation the
  suite caught an outdated UI export compatibility-marker assertion and the
  stale-generation helper regression described above; both are corrected.
- `.venv-linux/bin/python -m ruff check src tests` and `git diff --check` pass.
  Documentation links were checked locally. Git reports an existing CRLF
  normalization notice for `tests/test_setup_tools.py`.

All execution here uses local fixtures and disposable repositories. No fresh
live-provider or live-bubblewrap validation was performed. Historical run exports
and state were not modified. New state uses kernel compatibility marker
`simple-os/2`, coding program `agent-4-capability-boundary`, state schema `2.2`.
This is an ABI change within the current basic OS, not the planned integration
platform. Use a new run/state directory; older runs require their pinned code and
are not automatically migrated.

The audit's broader fault-scope/circuit taxonomy, persistent scratch lifetimes,
phase-specific output strategy, structured diagnostic causes, and separate
business-acceptance contracts remain deferred. They are not prerequisites or
claims of this bounded implementation.
