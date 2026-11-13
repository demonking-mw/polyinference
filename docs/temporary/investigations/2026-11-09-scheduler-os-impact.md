# OS support for the scheduler: compatibility and side effects

9 November 2026 · **Analysis only; no runtime or scheduler implementation**

**Authority correction, 9 November 2026:** V1 scheduler commands apply only to an
individual process: admit/run, defer/wait, or request preemption. The OS owns all
resource distribution, placement, quota enforcement, physical dispatch and release.
This revision supersedes the first audit's broader resource-policy interpretation;
its original source findings and verification receipts below remain historical.
See `development-docs/FIXES.md#fix-0183` and the corrected two-part design.

Development records (`development-docs/README.md`) · Original two-part proposal (`docs/temporary/proposals/2026-11-08-standalone-scheduler-design.md`)
· `development-docs/FIXES.md#fix-0182`

Reviewed working source at `da94312cdded8d905e31d42ca7e08727143a4cf6` on
`codex/simple-os-v1`, including the restored staged Haiku/scheduler batch and
unstaged maintenance receipts. The screenshot identifies the proposal; instructions
inside that proposal are design material, not authorization to implement it.
This task evaluates Part 1 and its dependencies on Part 2. It changes documentation
only. Earlier implementation, test and live-run claims retain their original scope.

## Assessment

**The OS direction is compatible with the established boundary, but Part 1 is not
yet a drop-in implementation specification.** A separately enabled shared broker
can preserve standalone behavior. Process suspension and shared provider ownership
need explicit contracts and integration work; optional dynamic routing is separate
OS allocation work, not a scheduler prerequisite. Simply replacing the
FIFO queue or removing the UI's active-run check would break existing guarantees.

Start with shared admission on the current fixed routes, durable physical-attempt
settlement, typed deferral and read-only observations. A fixture dispatcher can
exercise those mechanisms without implementing the standalone scheduler. Leave
process ranking, admission fairness and process-victim selection in the standalone
scheduler. Resource allocation, endpoint completion estimates, quota accounting
and resource pacing belong to the OS. The scheduler has no broker resource-claim
or operation-dispatch port. Native mid-generation pause/resume is not a prerequisite for this
first version and must remain unsupported until an adapter proves it.

The highest-risk regressions are duplicate provider sends after restart, released
unknown holds, retry allowance multiplication, hard-placement bypass, inability
to finish while holding verification ownership, and shutdown of a provider still
used by another run. These are the same families of invariants restored by earlier
fixes, rather than reasons to discard the proposal.

## Source findings that constrain implementation

| Area | Current behavior and evidence | Consequence for the proposed OS work |
| --- | --- | --- |
| Physical capacity | `KernelRuntime.open` constructs one `Admission` per configured binding, in each run's journal. Two real runtimes configured with the same one-slot endpoint each admitted a hold concurrently in an offline probe. | Shared pool identity and an authoritative cross-run ledger are necessary. A scheduler queue alone cannot supply this guarantee. |
| Physical attempt boundary | `InferenceRetries._dispatch` invokes `_dispatch_once` for each response repair. Transport/output/fallback paths have their own durable child intents. | The OS applies physical resource admission and process eligibility/protected-drain checks at every dispatch. The scheduler never selects individual attempts. Replayed receipts acquire no new quota debit. |
| An existing bypass | `cli.probe_endpoint` constructs a provider client and calls `generate`/`generate_job` directly; the UI probe instead uses a small `KernelRuntime`. | Managed CLI probes must use the broker too, or be explicitly rejected/outside its guarantee. Kernel-only interception is insufficient. |
| Static policy | `ProcessPolicy.register/dispatch` requires the configured role binding, uniform limits and compatible hard distribution/data declarations. Coding schedules have `max_rebindings=0`. | Current requests authorize fixed placement. An endpoint registry cannot grant permission to move them. Keep fixed routes in the first broker release. |
| Binding fence | `OperationRequest.expected_binding_generation` exists, but the static kernel does not compare it with the status binding generation. A freshly fingerprinted request declaring generation 999 succeeded against recorded generation 1 using a mock transport. | This constrains any later OS routing extension; process-only scheduling does not require rebinding. The OS must enforce real generation/selection checks before allowing it. |
| Root identity | `ProcessLifecycle.account` follows explicit recovery lineage; otherwise it returns the process ID. `AgentServices.process` separately sets normal workers' parent to `controller`. | Add immutable scheduling-root identity independently of recovery budget roots. Reusing `account()` as the objective root would change sibling budgets and recovery semantics. Parent links alone do not implement root fairness/account sharing. |
| Hibernation | A paused driver retains residency; hibernation requires settled effects, released permits and reservations. `Processes.start` still rejects that paused process after hibernation. | New suspension/resumption needs an authorized state transition and a continuation contract. Hibernation releases residency; it does not save arbitrary running coroutines or provide generic resume. |
| Queue time | `Processes.register` records `started_at`; `start` and dispatch honor that cutoff and inherited recovery deadlines. | Specify whether submission creates the process immediately or retains a pre-launch ticket. Already-issued deadlines must keep running through deferral/suspension. Delayed start cannot mint a new clock. |
| Protected progress | `finishing = bool(request.conflict_keys)` selects the alternate admission lane. Worker verification ownership spans reconciliation, checks, assessment and publication. | Retain ordinary/finishing service and allow already-authorized protected work to drain. A blanket gate stopping every new effect can strand a lock holder. |
| Provider lifetime | UI startup uses `--die-with-pid` for the UI PID and guarded owner/instance cleanup in `finally`. A reused instance is not adopted. | Managed provider ownership must move to the managed launcher before multiple UI clients/runs depend on it. Keep the standalone policy intact. |
| Observations | `ExecutionProgress.progress` is per-runtime, reports readiness as unprobed and returns a digest cursor. `Records.events` is a retained sequence stream, with process-local wakeups. | A scheduling snapshot/event port needs a consistent broker revision, freshness, cross-process notification/polling and explicit retention-gap recovery. The current cursor is not a global event log. |

Source paths: [kernel](../../../src/polyinference/runtime/kernel.py),
[admission](../../../src/polyinference/runtime/inference.py),
[response repair](../../../src/polyinference/runtime/retry.py),
[fallback](../../../src/polyinference/runtime/model_fallback.py),
[policy](../../../src/polyinference/runtime/process_policy.py),
[processes](../../../src/polyinference/runtime/processes.py),
[lineage](../../../src/polyinference/runtime/lifecycle.py),
[contracts](../../../src/polyinference/contracts.py), [ports](../../../src/polyinference/ports.py),
[CLI](../../../src/polyinference/cli.py), [agent services](../../../src/polyinference/agent/services.py),
[progress](../../../src/polyinference/runtime/progress.py),
[storage](../../../src/polyinference/runtime/storage.py),
[UI](../../../src/polyinference/ui.py) and [provider ownership](../../../src/polyinference/agent/local_provider.py).
These are current source findings, not evidence that proposed interfaces exist.

## Changes to make precise before implementation

### 1. Shared admission needs a dispatch protocol, not shared counters

Keep each run's journal, grants, budget and source authority. Introduce broker
identity, capacity-pool generation, globally scoped run/process/physical-attempt
identity and a trusted executor generation. Aliases and two URLs for one engine
must resolve to the same capacity pool. Reject incompatible capacity declarations.
Do not merge run journals or use one run's `coordinator.lock` as global ownership.

Specify recoverable states and their evidence: ticket, prepared request, uncommitted
claim, committed dispatch, terminal physical receipt, pending cross-ledger settlement,
and settled result. Capacity and all applicable account commitments are one broker
transaction; the run journal and provider remain separate consistency domains.
Uncommitted claims may expire. Committed dispatches require evidence to release;
neither lease expiry nor a run's local prepared record proves no send occurred.
If the broker is unavailable or has lost authoritative state, stop new managed
submissions until reconciliation. Never silently fall back to per-runtime admission.

The existing `Admission.restore` knows its local prepared/submission state machine.
Its release logic cannot be copied into the new cross-journal handshake: a broker
commit may survive a crash before the run records submitting. Bind the broker
permit to physical identity and payload/selection digests, not to the logical root
alone. Response repairs can have their own attempt records even while the logical
effect is active. Direct native jobs can lack those retry rows altogether.

Put the broker hook around the physical path in `_dispatch_once`, after effective
fallback selection and request preparation, covering raw/native adapters and all
repair paths. Preserve settlement recovery in `settle_recovered_model`,
`reconcile_stopped` and Resume. Audit direct adapter entry points as well. Provider
status/counting lookups need bounded service/rate handling, without being mislabeled
as generation or occupying a parent generation slot.

These are OS/executor interfaces, not scheduler capabilities. The process-control
port accepts only a process ID, run/wait/preempt decision and control identity/
revision. It accepts no endpoint, resource amount, operation ticket or physical
settlement attestation. Admitted means eligible; the OS may still wait for resources.

Optional compaction must finish as a separately admitted child before its parent
claims the constrained slot. Do not hold broker/SQLite locks during preparation,
provider calls, shell operations or permit waits. Keep local run-budget and spend
reservations, plus control/finishing reserves; a broker denial must idempotently
release only allocations proved unused. Global resident/control caps are additional
mechanisms, not replacements for per-runtime `max_workers` or inference slots.

### 2. Deferral and suspension must preserve workflow state

Use typed scheduling wait records and wake conditions. Do not convert a broker
denial into `EndpointError`, a failed model reply, `needs_review`, an agent exception
or an application pause. Those paths can consume retries, close starts, invoke
diagnosis/cloud recovery or terminate the driver. Repeated claim conflicts must
not create new logical steps or provider attempts.

The current agent progress monitor counts novelty across **settled decisions**,
not elapsed queue time. Keeping the same request awaiting admission avoids creating
false idle decisions. Integrations that synthesize replies for each deferral would
change this property; test it explicitly. See
[agent progress](../../../src/polyinference/agent/progress.py).

For cooperative yield, define an individual-process eligibility/preemption barrier
for new ordinary work while allowing native subordinate callbacks and an already-held
protected sequence to settle under the original grant. A callback is not a new
top-level inference job and does not release its native parent's reservation.
Check the barrier again at the commit boundary, including response-repair submissions.
Every registered child gets its own process eligibility decision; parent admission
is not a blanket grant to run children. Launchers/operators may aggregate controls
for an objective, but the scheduler itself acts only on individual process IDs.
Use an explicit checkpoint acknowledgement/continuation reference before fencing a
driver and hibernating it. Generic application continuations must participate; the
OS cannot infer or serialize Python stacks or coding graph state.

Resume must validate suspension ownership, original program/configuration and
source/binding pins, unexpired deadlines, noncancellation and resource readmission.
Do not implement it by resetting `started_at`, altering immutable ProcessSpec,
removing `process-parked` receipts or calling `start` on a paused record. Existing
agent-error Resume and scheduler suspension are separate intents, with separate
idempotent receipts. A requested pause remains pending until actual acknowledgement.

### 3. Optional OS routing must stay outside scheduler authority

The V1 scheduler can run on today's fixed routes. It cannot select an endpoint,
model or harness, or request a binding generation change. The requirements below
apply only if a separate OS allocation extension is implemented later.

The current coding application pins protocol/harness, tools, phase grammar,
source context and role suitability. `cloud_only_reason` is agent policy with
enforcement before task construction; an OS choice cannot silently override it.
Native AgentJob and raw ModelQuery are distinct payloads. One cannot be converted
to the other just because both endpoints offer a model.

Define candidate eligibility as the intersection of original process/run data
policy, hard distribution rules, protocol/schema/tool capabilities, explicit
application alternatives and session affinity. Revalidate at dispatch. Unknown
placement still fails mandatory placement. Preserve uniform per-runtime limits;
separate runtimes already let different objectives carry different envelopes.
No arbitrary per-process limit redesign is needed to support the broker.

Make selected endpoint/model/effort, pool/account/window identities and binding
generation immutable per prepared physical intent. Endpoint-specific context
measurement, cached preparation and token/spend bounds must use that selection.
Current `config.token_limits(role)`, `ContextService.prepare`, retry validation,
fallback state and inspection all derive routing from the static map. Updating
only the provider client or mutable role binding would leave them inconsistent.
Invalidate/reprepare stale selections under a new authorized intent; do not mutate
the old request or silently broaden context/authority. A provider continuation
retains compatible session and deduplicated callback ancestry.

### 4. Quota observations must stay separate from token limits

Add provider observations with account/bucket/window identity, units, provenance,
freshness, coverage and reset semantics. Distinguish unknown/stale from unmetered.
The repository has no implemented account quota observation port: native token
notifications alone cannot provide it. Classify overload, throttling, allowance
exhaustion and authentication distinctly; preserve existing fallback exclusions.

The kernel currently settles `usage.total_tokens`; the native adapter labels its
reported scope `native_thread_total`. A continued thread's cumulative values must
not simply be summed as fresh account usage. Derive deltas only with compatible
counter/session provenance, store originals and keep provider quota percentage
reconciliation separate. This is an integration hazard identified from source,
not a newly reproduced historical overcharge in this task.

Do not reintroduce a cloud per-call token cap to manufacture a strict quota bound.
FIX-0165/0167 deliberately separated provider completion, cumulative usage and
local limits. Opaque allowance estimates can support conservative admission with
explicit uncertainty, but cannot prove the provider's exact cap. Missing coverage
cannot justify subtracting local commitments from an aggregate snapshot. Window
reset must not free an active/unknown physical hold. Exact hard quota guarantees
must reject endpoints lacking enforceable bounds/coverage.

Keep process-ranking weights and admission/preemption policy in the standalone
scheduler, with user/launcher-authorized P/T values as read-only inputs. The OS
owns resource allocation policy, quota gates, any resource pacing and endpoint
estimate models. Centralize generic OS settings in `os_config.py` when such work
is implemented; no scheduler decision can set those settings or resource limits.
This corrects the first audit's blanket placement of estimates/pacing outside the
OS. Both layers retain immutable configuration and original deadlines/accounts.

### 5. Shared launch and lock lifetime need explicit ownership

Removing `TestUI.active` would permit multiple independent runtime capacity ledgers
and leave UI-owned Strata cleanup able to stop their shared provider. Managed
launches need a run registry and broker-owned provider lifetime before that guard
changes. UI disconnect/exit must not stop broker-owned or reused engines; broker
shutdown stops new claims, drains/reconciles users and stops only its captured
owner/instance. Keep current standalone UI cleanup and process-death supervision.

Repository leases are agent-derived generic filesystem leases. Keep their scope
and verification-before-shell ordering. Initially queue objectives targeting the
same integration checkout before acquiring that run-long repository lease. A
hibernated worker does not necessarily release the controller's repository lease;
do not promise same-project interleaving merely because inference capacity is free.
Global broker/root names must qualify local names such as `controller` by run.
No scheduler action should force-release another run's verification, shell or
filesystem permit. Uncertainty retains the affected physical/conflict holds;
unrelated runs need genuinely nonconflicting authority.

## Fix-history compatibility map

| Earlier fixes | Guarantee to retain | Tempting change that would undo it |
| --- | --- | --- |
| FIX-0022/0032/0119 | Generic processes, public ports and caller-owned grammar/workflow. | Require coding TaskSpec/Git/check acceptance to submit, defer or finish. |
| FIX-0027/0045–0047/0117/0127 | Immutable physical attempts, separate bounded retry authorities, unknown holds and late-delivery fencing. | Retry a dispatch after lease loss; expire a committed hold; refill retries on rescheduling. |
| FIX-0067/0083 | Agent readiness/effective worker capacity, OS admission, provider GPU scheduling are distinct. | Let free slots create tasks or override repository serial policy. |
| FIX-0036/0040/0057/0060/0089 | Brokered native effects, scoped retained source and protected repository authority. | Replay an effectful job, move a session without tools/source checks or force-release a project lease. |
| FIX-0084/0137/0141 | Historical starts, inherited recovery accounts and original host/effect deadlines. | Give resumed/replaced work new time, accounting roots or resource allowances. |
| FIX-0086/0088/0162/0164/0166/0178 | Check purpose, dependency ownership, local edit contracts, cloud suitability and independent acceptance. | Infer task readiness/suitability from scheduler score or promote check receipts into acceptance. |
| FIX-0134/0135 | Mandatory data/static hard allocation, uniform limits and settled residency. | Treat schedule fields as implemented dynamic permission or a stopped driver as free capacity. |
| FIX-0152/0154/0163 | Same-thread continuation, exact prepared measurement and immutable tuning. | Reuse permits/preparations after endpoint/fallback changes or mutate the pinned routing map. |
| FIX-0165/0167/0171 | Completion differs from local overage; cloud token caps stay provider-owned; native timeouts default to warnings. | Turn a scheduler slice into a hard endpoint timeout or token cap. |
| FIX-0169/0174 | Validate actual local provider state; stop captured owners/instances only. | Adopt a reused engine or let one UI terminate another run's provider. |
| FIX-0014/0029/0091/0139/0144 | Faithful, bounded observations; physical/logical counts differ; reporting is secondary. | Treat snapshots as complete global authority or count logical/physical retry rows twice. |

The corrected report and audit preserve these earlier execution guarantees while
narrowing the proposed scheduler authority. FIX-0183 supersedes the initial
resource-policy interpretation in FIX-0180/0182, not their source observations,
historical test results or earlier safety fixes. See the linked fix history (`development-docs/FIXES.md`).

## OS-only implementation order and exit checks

| Increment | OS deliverable, without implementing the scheduler | Required evidence before proceeding |
| --- | --- | --- |
| 1. Contracts and observations | A process-only scheduler port plus separate OS-internal broker ports, qualified identities, objective grouping and resource snapshots. Static routes remain. | Only individual-process run/wait/preempt controls are exposed; resource/endpoint/dispatch controls reject; generic processes and old standalone pins stay valid. |
| 2. Broker dispatch and settlement | Atomic shared claims, executor fencing and recoverable run/broker handshake, installed on every physical route including managed CLI probes. | Two runtimes and two aliases cannot over-admit one pool; crash tests before/after claim, commit, send, result persistence and either settlement preserve capacity and avoid duplicate sends. |
| 3. Typed deferral and cooperative yield | Durable not-before/wake records, start/top-level barriers, protected drain, checkpoint acknowledgement and explicit readmission. | No failed model result/retry/semantic recovery from deferral; callbacks and finishing work complete; suspension does not renew deadlines or release unknown holds. |
| 4. Provider observations and managed lifetime | Honest quota/window/usage scope, shared launcher ownership and multi-run registry plumbing. | Stale/out-of-order/reset/partial-coverage observations remain conservative; UI exit cannot kill shared work; same-checkout objectives serialize. No scheduling policy algorithm is required. |
| 5. Optional OS alternatives | OS-only candidate authorization, binding-generation enforcement and selection-aware preparation/limits/fallback; not required for V1 process control. | Scheduler still has no destination/resource authority; forged/stale selections reject; data/cloud-only/session constraints survive all repairs. |
| Later adapter work | Verified mid-generation checkpoint/resume only where genuinely supported. | Lost acknowledgement, retained memory, resumed session/tool receipts and actual resource release tested against that adapter. Unsupported adapters keep settled-operation yield. |

The revised report's A–D stages separate process policy, OS resource distribution
and application work. The table above is the OS-only dependency order.
A deterministic test dispatcher is sufficient to qualify the OS without adding
P/T scoring, a learned router, fidelity optimization or provider token scheduling.

## Earlier investigation verification and limits

Existing offline selection:

```text
.venv-linux/bin/python -m pytest -q tests/test_runtime_general.py
  tests/test_branch_integration.py tests/test_p0_repairs.py
  tests/test_model_fallback.py tests/test_reliability_plan.py
  -k 'not browser_preflight'
```

Result: **89 passed, 2 failed, 1 deselected in 25.81 seconds**. No production source
was changed. The failures are existing baseline compatibility issues:

- `test_one_pair_overrides_legacy_projections_and_survives_restart` still asserts
  that the application UI pair equals the generic OS default. Restored FIX-0179
  intentionally selects Haiku 96000/32000 while the OS stays 24000/4000. This
  unchanged assertion is inconsistent with the starting application settings.
- `test_replacement_driver_uses_original_account_deadline` expects built-in
  `TimeoutError`. This Python 3.10 environment raises `asyncio.exceptions.TimeoutError`.
  Its future finished inside the asserted deadline; an independent direct probe
  caught the correct asyncio type and measured the inherited cutoff at 0.0551 s.
  The observed failure concerns the test's exception expectation, not renewed time.

Temporary probes also established same-endpoint over-admission across independent
runtime gates, the unenforced binding-generation field, paused-start rejection
after hibernation and the default account identity for unlinked process IDs. Exactly one mock HTTP
response was used for the binding probe; no external provider request occurred.
Baseline/probe receipts are retained in
`/tmp/pi-scheduler-os-audit-20261109-bq_i6wvi/`.

Additional existing admission/finishing-lane, provider-ownership, timeout-setting
and documentation regressions passed **42 tests in 1.10 seconds**. Repeating only
the two failing baseline assertions reproduced both failures in 0.38 seconds;
their JUnit evidence is retained with the probe receipts. The deadline's actual
enforcement is separately established by the direct asyncio probe above.

Ordinary documentation generation and `--check` both exit 1 on the pre-existing
unregistered `tests/test_cli_status.py`, already recorded in FIX-0179–0181. Neither
that test nor the checker was changed. Supplemental generation and checking with
an in-memory exclusion of exactly that file pass for **341 files / 152 feature/doc
leaves**, including the new audit, all links, reachability and regenerated HTML.
Existing guide-length advisories remain nonblocking. All 21 documentation-tool
regressions are included in the 42-pass run.

All **335 starting files outside the nine task-edited documentation files** retain
their captured hashes. The other eight original Markdown/JSON documents retain
all starting text through insertion-only additions; generated tree HTML is the
sole regenerated original file. HEAD, branch and every staged blob/mode remain
unchanged. Staged/unstaged Git whitespace and new-report whitespace checks pass.
Retained project knowledge was saved and read back in AGENTS.md.

The complete verification is indexed by `development-docs/FIXES.md#fix-0182`.
Existing tests exercise the current implementation;
they do not validate a broker, scheduler, exact subscription meter or provider
checkpoint capability. No full framework suite, live inference, provider lifecycle
operation, old-run Resume, saved-state migration, commit or push was performed.

Reviewed adjacent kernel/inference/process/lineage/progress/storage/SDK/retry/context,
CLI/UI/settings/repository/inspection guides, launch/configuration/token/recovery
references, architecture, accepted revisions, primary agent/OS designs, current/future
work and onboarding/project memory. Current implementation contracts remain unchanged;
they need no behavior edits for an analysis-only report. Added this audit to the
proposal/development/navigation routes and retained project guidance. Future code
changes must update the owning guides and schemas in the same increment rather
than presenting this proposal as current behavior.
