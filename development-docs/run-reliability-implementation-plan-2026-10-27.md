# Run reliability: implementation plan and historical failure coverage

27 October 2026 · Analysis and proposed implementation only · [FIX-0133](FIXES.md#fix-0133)

Subsequently authorized implementation: [stage record and current verification](reliability-implementation-2026-10-27.md).
The plan below preserves its original proposed-state assessment.

[Current issues](current-iter-issues.md) · [Executive brief](workflow-readiness-brief-2026-10-27.md) · [Engineering analysis](workflow-readiness-analysis-2026-10-27.md) · [Existing cloud recovery change](local-task-granularity-and-cloud-recovery-2026-10-27.md)

## Executive assessment

**The next work should improve productive completion, while retaining the existing safety guarantees.** The latest run stopped because physics and menu workers stalled, their local replacements stalled again, and ordinary recovery depth was exhausted. Cloud senior review happened; cloud implementation did not happen for those replacements. Their lineages had used only 43/256 and 87/256 calls. More total calls or a longer transport timeout would not repair that control-flow decision.

The working tree already implements bounded cloud coding takeover, protects recovery roles from normal allocation, rewires ordinary pending consumers, narrows planner instructions and exposes actual tools. These changes are uncommitted and fixture-tested, with no fresh live qualification. They should be inspected and qualified, not independently rebuilt from an older report. Already-linked pending recovery consumers still require a safe lineage-preserving handoff design.

The remaining central work is a bounded worker state ledger, smaller verifiable assignments with complete dependencies, error-conditioned repair, and an early integrated application gate. Qualify the local backend on short tasks before trusting another broad unattended run. Repair the separate OS contract gaps U01–U04 before claiming arbitrary profiles are enforced correctly. Keep provider settings, application semantics and test infrastructure separate.

**This plan addresses most recurring orchestration mechanisms in the reviewed evidence, but cannot establish that most failed runs would now finish.** Malformed actions, semantic mistakes, inadequate model capability, unavailable infrastructure and genuinely unknown execution can still prevent delivery. The proposed repeated live gate is the evidence needed to move beyond that limitation. No fixes were implemented by this report.

## 1. Scope, current status and evidence standard

Reviewed checkout: `codex/simple-os-v1`, HEAD `5fe92f3e2122dbb19e12d3152644a32f2979f40b`, with the existing uncommitted FIX-0132 implementation and documentation. Earlier reports saying the working tree contained documentation changes only describe their investigation time; that is no longer the current tree. Existing changes belong to their original work and are preserved.

This report combines the executive direction in the workflow brief/analysis, the four explicit user judgments in the cloud recovery record, and the adjacent audit's separately identified follow-ups. Recommendations here remain proposed work. Historical generated-game bugs are included in coverage analysis; they do not become generic OS requirements or an instruction to repair preserved games now.

Evidence was gathered from current source, related fix entries and retained reports, plus read-only SQLite queries against the latest attempts. No historical model requests or commands were replayed. The historical reports are not independent controlled trials of the same implementation. The directory named `minecraft-v1-live-2026-10-27-0200` contains execution on **26 October**, not a new 27 October experiment.

Current status labels used below:

| Label | Meaning |
| --- | --- |
| Existing | Current source contains the mechanism; its particular historical checks retain their original limits. |
| Uncommitted/fixture-tested | FIX-0132 implementation exists in the working tree; recorded selected-case verification is not live qualification. |
| Proposed | Design in this report; no implementation or successful execution is claimed. |
| Uncertain | Available records do not isolate the cause or establish the expected benefit. |

### What was independently checked in retained records

Under the latest run directory, `attempt-02/state/records.sqlite` and `attempt-03/state/records.sqlite` were opened using SQLite `mode=ro` and `PRAGMA query_only=ON`.

| Query population | Attempt 2 | Attempt 3 | Combined |
| --- | ---: | ---: | ---: |
| `inference-attempt/` rows whose request role is `worker` | 49 | 130 | 179 |
| Those physical results with `ResponseValidationError` | 2 | 11 | 13 |
| Those results whose `runtime/context-receipt.omitted_refs` is nonempty | 38 | 107 | 145 |
| `diagnosis/` records | 0 | 0 | 0 |
| `effect/` rows in `uncertain` state at the saved stop | 0 | 0 | 0 |

This reproduces the reported totals with explicit populations. Counting all standalone context receipts instead gives 41 + 107 omissions; those include other invocations and must not replace the 145 local-result count. Neither count proves that omission caused a particular wrong decision.

Attempt 3's `proposal/senior-2` proposes `locomotion_v3_recovery` as `worker`; `proposal/senior-4` proposes `menu_shell_recovery` as `worker`. Their `task/` assignments retain those roles. Exception records `worker-exception/2-locomotion_v3_recovery` and `worker-exception/4-menu_shell_recovery` record 43 and 87 cumulative calls. Both say confirmed-stopped execution and known effects. The matching `process-account/` records retain predecessor, root, original grant, limits and deadline.

Attempt 2's `task/named_world_repository_recovery` is a completed `specialist`, linked to the local storage predecessor. This is a concrete example of cloud implementation yielding useful partial output; it is one success, not a general success-rate estimate. The previously retained management and cloud-resolution JSON audits provide additional payload, ancestry and actual backend evidence.

## 2. Executive direction mapped to concrete work

| Direction | Implementation package | Current situation |
| --- | --- | --- |
| Qualify local workers on short, observable tasks before broad projects. | Q1 | Bounded inference benchmark exists; the integrated qualification gate is proposed. |
| Keep completed work, digests, unresolved errors and next action available after history omission. | A1 | Shared senior memory and current inputs exist; automatic bounded worker state is missing. |
| Split movement, collision, persistence and migration; declare dependencies and acceptance. | A2 | Module contracts and new planner guidance exist; guidance alone cannot prove semantic size. |
| Fail upward from local work to actual cloud coding, outside normal staffing quotas. | A3 | Core policy is uncommitted/fixture-tested; live qualification and linked-consumer handling remain. |
| Expose the actual OS capabilities, including unsupported browser/MCP/service assumptions. | A2, A3, A6 | Current planner inventory explicitly states these limitations. |
| Make recovery change a demonstrated condition and improve semantic/error feedback. | A3, A4, A5 | Some diagnosis and feedback exist; immediate schema retries still commonly resample unchanged input. |
| Require a small playable/integrated path early, using real entry modules and DOM/browser evidence. | A6 | Existing check-purpose and exact-tree completion mechanisms support this; workload gates are insufficient. |
| Require three small completions and an interrupted/resumed run before scaling. | Q1, T1 | Proposed gate; not performed here. |
| Measure useful results, retained context, physical calls, costs, waits and exact stop causes. | T1 | Many raw records exist; consistent product-oriented projections need work. |
| Correct native input sizing and effort ambiguity without concealing capacity limits. | O1 | Mixed-lane configuration was corrected in fresh historical states; generic preflight and effort consistency need work. |
| Close declared runtime contract gaps and retain authority/accounting/uncertainty guarantees. | O2–O4 | U01–U04 remain open; they were not established as the latest stall's cause. |
| Extend documentation checks, repair the legacy smoke assertion and reconcile baseline failures. | T2 | Separate audit recommendations; no code repair is claimed. |

## 3. Ownership: where each implementation belongs

| Layer | Owns | Should not decide |
| --- | --- | --- |
| **Coding agent/application**: `agent/`, application domain/configuration | Task size and dependencies, requirements, canonical worker memory, diagnostic interpretation, staffing/escalation, source reuse, Git workflow, finishing strategy and product acceptance. Host Python controller logic is part of the agent. | Whether remote execution stopped, or permission to refill accounts, widen grants or ignore an OS rejection. |
| **Generic OS/runtime**: `runtime/`, contracts and ports | Faithful provider rendering, context preparation, generic process/effect authority, data policies, physical attempts, admission, deadlines, source-bound observations, replay and execution certainty. | What movement means, which game feature to build, whether a local developer needs a cloud repair, or whether a game is complete. |
| **Provider/deployment configuration** | Actual endpoint/model identity, context metadata, timing, sampling/effort, tokenizer knowledge, installed browser/Node dependencies and serving capacity. | An unmeasured claim about effective capacity, model competence or GPU throughput. |
| **Verification infrastructure** | Reproducible fixtures, real DOM/browser runners, exact-tree evidence, fault injection and qualification records. | Passing a fake DOM or unit suite off as actual application acceptance. |
| **Generated application** | Concrete interfaces, coordinate conventions, mounting, persistence wiring, inventory conservation and truthful feature documentation. | Adding application-specific rules to the OS. |

The [runtime boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md) and [open-gap ledger](../design-docs/simplified-os/DESIGN_REVISIONS.md#open-implementation-gaps) remain authoritative. General processes must still finish without Git, coding tasks, checks or source edits. There is no need for a new shared agent library or a general autonomous service platform to implement this plan.

## 4. Detailed implementation packages

### Q1 — Establish reproducible local and integrated qualification

**Owner:** verification/application setup. **Status:** proposed qualification, using existing runtime paths.

Build a small versioned task corpus: one existing-file repair; new-file creation followed by an update with the returned digest; one real DOM mount/event change; one save/load continuation; and a repair of a deliberately failing focused test. Keep each task's expected behavior and trusted evaluator independent of its worker-produced tests. The earlier short inference benchmark is useful context, not a substitute for these actual file/tool workflows.

Each trial needs a manifest of framework source (including uncommitted diff), task/check hashes, dependency versions, actual backend, sampling/effort, context/output targets, tool inventory, original resource ceilings and start time. Use fresh disposable projects/state; never change the old run pins. First hold source/model/profile constant. Then compare one factor at a time, especially ledger on/off and task size. A different model or quantization is a separate authorized trial, with its own cost and results.

**Acceptance:** trusted evaluators confirm the actual output; no supervisor source repair or altered acceptance; physical attempts and terminal causes are complete. Short-task failure sends work back to tool/protocol/model qualification, not automatically to a larger overnight project. Live calls are a later separately authorized activity, not part of this report.

### A1 — Add a bounded, source-backed worker state ledger

**Owner:** agent. **Status:** proposed. **Primary paths:** [services.py](../src/polyinference/agent/services.py), [worker.py and WorkerState](../src/polyinference/agent/worker.py), [progress.py](../src/polyinference/agent/progress.py), [domain records](../src/polyinference/domain.py) and application prompts; current context preparation stays in [runtime/context.py](../src/polyinference/runtime/context.py).

`memory_view()` currently projects shared senior summary/notes. `context()` pins application inputs and memory but makes the full trajectory optional. Workers already receive current phase, code, grants, checks and remaining physical model calls. Avoid duplicating those facts into an unbounded second history.

Introduce a proposed application record such as `worker-state/<attempt>` with a monotonically revised bounded projection: current tree/environment/workspace generation; a small set of outstanding obligation IDs; completed changes linked to source/evidence; recently touched file digests; current failed check/error references; concrete blockers; and the next focused action. Keep verified facts separate from a model's proposed next step. Suggested starting bounds are 8 KiB for the prepared projection, 16 recent file digests and four unresolved diagnostic summaries, measured against the whole request before adopting defaults. These are design starting points, not current settings or measured optimal values.

Update verified fields deterministically after settled tool/check/phase results. Current file mutations already return a digest in `runtime/tools.py`; consume that result rather than requesting a redundant OS feature. Key digest validity by source/generation, invalidate after integration, handoff or ambiguous shell edits, and reread when a valid current digest is unavailable. A partial read must not become proof of full-file knowledge. Keep full originals and references outside the compact projection.

Publish the ledger revision and a stable applied-event ID through compare-and-publish so restart cannot apply an event twice. A checkpoint should bind the projection revision it used; restart either reuses it or reconstructs from settled records. Prepare the ledger as required application context without making arbitrary model-written prose trusted instructions. Revalidate factual claims after source changes. If even the bounded required set does not fit, surface a typed admission blocker; do not silently drop the grant, objective or current error.

**Tests/acceptance:** force omission of early history, then update an existing file with the correct digest; retain a failing check and an unresolved dependency across omission; invalidate after shell mutation and recovery; restart between tool settlement and projection/checkpoint publication without duplicate updates; reject a stale ledger after an integration change. Check prepared requests, not just the canonical archive. Compare useful completion and repeated-read share against Q1's unchanged baseline.

**Risk:** summaries can preserve wrong conclusions and required memory can crowd out useful source. Bound it, prefer host-verifiable facts, and measure the tradeoff. History omission is observed; its causal contribution to stalls remains unisolated.

### A2 — Make local tasks small, completable and connected by explicit contracts

**Owner:** agent planning/review. **Status:** existing module/dependency mechanisms plus uncommitted guidance; stronger structured obligations proposed. **Paths:** [architecture.py](../src/polyinference/agent/architecture.py), [tasks.py](../src/polyinference/agent/tasks.py), [senior.py](../src/polyinference/agent/senior.py), [prompts.py](../src/polyinference/agent/prompts.py), [controller.py](../src/polyinference/agent/controller.py), application domain types.

Represent one observable behavior, one focused criterion, required interface versions, exact read/test closure and prerequisite ownership per local assignment. Validate presence and consistency of those fields; do not pretend a filename count or word-count heuristic can prove semantic simplicity. Senior review must still judge size. Keep the full product requirement visible even when a task covers only one obligation.

For the observed workload, plan input-to-motion, collision, persistence API, save migration, shell mounting and connected save/load as separate tasks. Establish an initial render/input path before unrelated feature breadth. A change to x/y coordinates needs an explicit consumer migration task and a connected check; accepting the core module does not certify an old x/z renderer. Shared test discovery, fixtures, entry HTML and package/config inputs must exist under accepted source or have a prerequisite owner before dependent dispatch.

Derive source/check closure from pinned runner/configuration and explicit plan declarations, not permission guesses. Required existing files may be readable without new write authority. Show what evidence is unavailable in a scoped view, and allow a truthful limitation instead of asking a worker to hunt host Git metadata. Preserve started assignments and interface versions; change only unstarted work through a validated new plan.

The new `capabilities()` view already says no browser, MCP, persistent services or native-tool bypass. Use that same inventory in planning and recovery. If a required verification capability is absent, create a scoped prerequisite or record a blocker; never ask the planner to invent it.

**Tests/acceptance:** reproduce RUN13's runner outside both workers' completion closure; reject the plan or add the prerequisite before starting. Cover exact mandatory test paths, missing entry HTML, interface migration and parallel disjoint writes with a shared test dependency. A real short-task trial must meet its focused criterion and integrate without surprise prerequisites.

**Limit:** automatic recovery fan-out is not supplied by smaller initial tasks. If a failed task must become several children, design explicit parent-obligation closure, one shared root account/deadline, partial completion and final integration. Defer that schema expansion until the one-replacement route is qualified; never create unrelated fresh accounts to simulate splitting.

### A3 — Complete and qualify failing upward to cloud coding

**Owner:** agent policy/controller. **Status:** core FIX-0132 uncommitted/fixture-tested; hardening and live qualification proposed. **Paths:** [cloud_recovery.py](../src/polyinference/agent/cloud_recovery.py), [exceptions.py](../src/polyinference/agent/exceptions.py), [routing.py](../src/polyinference/agent/routing.py), [tasks.py](../src/polyinference/agent/tasks.py), [senior.py](../src/polyinference/agent/senior.py), [controller.py](../src/polyinference/agent/controller.py); existing OS account binding in [lifecycle.py](../src/polyinference/runtime/lifecycle.py).

The current implementation already supplies the main intended transition:

1. A cleanly stopped, unpublished local development exception carries source and failure evidence to sprint review.
2. `offer()` checks cancellation, cloud binding, a finite cloud allowance, known effects and usable original resources. A compatible delta can be reused; a conflicting delta stays preserved while repair starts from current source.
3. `prepare()` converts eligible local retry, defer, stop or omitted/no-op proposals into a concrete specialist assignment. Source read requests can still precede final plan normalization. Raw and effective proposals remain separate.
4. Normal allocation preserves the validated recovery role. A default one cloud coding opportunity is separate from ordinary replacement depth, while calls/tokens/operations/grants/deadline remain inherited.
5. Ordinary pending consumers are replaced and rewired transitively. Cloud failure cannot bounce back to local or renew its own count. All normal reconciliation, assessment, integration and publication gates remain.

This is actual coding takeover, not merely calling a cloud reviewer. A routine transient response retry need not escalate an entire task immediately. The trigger is an eligible stopped task exception, with clear reasons for ineligibility. Do not raise the default cloud count to hide failures during qualification.

The known remaining handoff fails when an affected pending consumer already has `previous_process_id`; blindly cloning it would detach its original recovery account. Add an explicit pending-successor transaction: verify that the affected consumer has never started and has no submitted/prepared effects or active reservations; retain its predecessor/root/deadline/grants/contract; cancel only its obsolete unstarted assignment; publish the replacement spec, dependency mapping and account-lineage links atomically. Validate both its own failure lineage and the newly replaced provider. If the two lineages cannot be represented without contradictory obligations, return a structured unsupported-plan blocker. Do not merge budgets or reset a consumer's count. Started consumers remain immutable.

Treat diagnosis as a bounded choice, not an additional mandatory loop before every cloud worker. Existing read-only checking can classify a test failure or scope misunderstanding. The cloud worker can inspect retained evidence itself. If automatic pre-repair diagnosis is added, make its cost explicit, share the original account, and ensure it cannot consume all finishing/recovery capacity. A read-only checker must not be mistaken for an implementation worker.

**Tests/acceptance:** preserve the existing real fixture-dispatch, quota-immunity, no-op senior, zero-depth, source conflict, hard-boundary and finite-failure tests in `tests/test_cloud_recovery.py`. Add restart/CAS-conflict tests at the pending-successor transaction; reject a consumer that became started; prove every replacement's original account/deadline and obligation links survive. In a fresh live short workflow, observe actual specialist/backend identity and a checked repair after an injected local stall. Calling the cloud senior alone fails this criterion.

**Boundary dependency:** O2 must enforce mandatory location/data policies. Logical lane names alone do not establish a different physical model or permission to send protected context to cloud. Existing FIX-0132 is not proof that U01 is repaired.

### A4 — Make format and diagnostic repair use the actual error

**Owner:** agent repair semantics, with an optional generic OS event affordance. **Status:** validators, bounded retry windows, worker correction and diagnostic projections exist; production error-conditioned immediate replacement is proposed. **Paths:** [services.py](../src/polyinference/agent/services.py), [worker.py](../src/polyinference/agent/worker.py), [diagnostics.py](../src/polyinference/agent/diagnostics.py), [runtime/retry.py](../src/polyinference/runtime/retry.py), [ports.py](../src/polyinference/ports.py), provider rendering when needed.

The retained audit found eleven immediate schema follow-ups using the same payload, nine becoming valid, with no supplied replacement. That is useful resampling, but it does not carry the new error into task reasoning. Current `model_result()` awaits execution, so simply adding `offer_retry()` after the await cannot service the already-expired window.

Use a single application-owned retry observer for an outstanding logical request, driven by a durable waiting record/event. When the existing optional port is sufficient, observe the owning operation and submit a bounded replacement while it is waiting. If a notification interface is needed, add a negotiated generic validator-failure event through ports; keep WorkerReply grammar and repair text in the agent. Avoid a polling daemon or extra recursive model call in a default one-second window. Build concise deterministic feedback from validator paths/error class, the current phase and an artifact reference to rejected output. Preserve original required pins, role, schema and grants; `offer_retry()` already enforces those constraints and capacity.

Keep one complete validated action per reply. Suggest a smaller edit when output was genuinely cut off; classify malformed completed JSON separately. Never join a rejected prefix to a later response, execute an XML-looking tool call, or relax CAS. After immediate retry exhaustion, the next bounded worker decision receives the error and current ledger; persistent failure routes through A3 rather than an invisible fresh retry tree.

Maintain bounded check head/tail/error excerpts, canonical output references and source identity. These projections already exist in parts of services/diagnosis; consolidate and test them rather than claiming all diagnostics are absent. A scope narrative must name the actual failed operation, granted paths and evidence before it drives a plan change.

**Tests/acceptance:** assert that a known validator error reaches the next prepared payload; preserve all mandatory context; exercise an expired window, restart after an accepted replacement, cancellation and no-observer fallback. Combine malformed response, transport fault and output cutoff to prove original ceilings do not multiply. Cover native jobs with brokered effects as ineligible for blanket response replay. Measure whether valid replies lead to useful task results, not just a lower JSON failure count.

### A5 — Preserve progress and finishing capacity across repair layers

**Owner:** agent progress/finishing policy; OS enforcement remains generic. **Status:** eight/twelve decision novelty guard, remaining calls and final-phase reserves exist; richer decision inputs and combined-path qualification proposed. **Paths:** [progress.py](../src/polyinference/agent/progress.py), [worker.py](../src/polyinference/agent/worker.py), [services.py](../src/polyinference/agent/services.py), [runtime/retry.py](../src/polyinference/runtime/retry.py), [runtime/model_retries.py](../src/polyinference/runtime/model_retries.py), [runtime/lifecycle.py](../src/polyinference/runtime/lifecycle.py).

Keep novelty and semantic usefulness separate. A new read range or failed check can be legitimate evidence, while a new wrong edit may be useless. Do not make elapsed seconds, narration or provider activity reset a settled-decision stall. Add task-specific milestone/evidence deltas to review, without using an unverified model claim as proof of progress or preempting unknown execution.

Extend the already-pinned remaining-call value with bounded root remaining operations/tokens, original deadline, finishing reserves and recovery opportunities from existing OS resource views. Maintain separate counters for transport retries, response retries, consecutive grammar correction, stalled decisions, semantic replacements and cloud recoveries. Do not replace them with a misleading universal retry count.

Use the task ledger and short assignments to request a candidate before development reserve is reached. When finishing responses fail, preserve partial source and expose an eligible exception while resources still permit recovery; do not mint more reserved calls after exhaustion. A candidate-first instruction is guidance, not assurance that reconciliation/assessment can fit in four calls.

**Tests/acceptance:** repeated unchanged reads/checks warn/park; genuinely new read coverage does not; no false timer stall during a healthy long generation; physical retries and diagnosis consume the root account; multiple recovery layers cannot spend the finishing reserve twice. A task that cannot finish reports the exact blocking counter and retained-source reference. Tune thresholds only from controlled trial evidence.

### A6 — Make a real integrated milestone the planning backbone

**Owner:** agent acceptance and verification infrastructure; concrete repairs belong to the generated application. **Status:** check-purpose separation, module contracts and exact-tree semantic completion exist; adequate workload gates remain proposed. **Paths:** [runtime_policy.py](../src/polyinference/agent/runtime_policy.py), [review.py completion validation](../src/polyinference/agent/review.py), [architecture.py](../src/polyinference/agent/architecture.py), [controller.py](../src/polyinference/agent/controller.py), [docs/guides/checks.md](../docs/guides/checks.md), plus separately scoped application tests/entry modules.

Create the smallest vertical path early: load actual entry modules, mount visible output, perform one input that changes state, pause, save, reload and assert restored state. Add features while keeping that path working. Independently exercise both the module API and its consumer; a core coordinate test cannot certify the renderer. Keep setup/prerequisite, task and final-objective gates separate.

Provide real DOM/browser checks through explicitly configured command/check infrastructure. First create and check the browser runner/dependencies as a prerequisite. A finite test command can own an ephemeral server/browser and deterministic cleanup; this does not require pretending the model has browser/MCP tools or a persistent-service API. If suitable execution cannot be granted, report the missing infrastructure and withhold the relevant claim. Run on the production entry/bundle where applicable, not a disconnected imitation. Capture exports, console failures, state assertions and source identity.

For the observed game, independently catch missing `mountShell`, nonexistent `root.createElement`, array-style mutation of DOM collections, x/y versus x/z mismatch and absent storage wiring. The retained browser probe reached the missing export only; the other DOM concerns remain source findings until separately exercised. Do not rewrite those historical results as tests of all defects.

Keep the versioned original requirements separate from model-generated feature matrices. Use evidence-backed statuses such as implemented/tested/integrated/missing; no invented parity percentage. Selected-tool mining, inventory limits/migration, overflow conservation and item-registry consistency require explicit application tests if those features are planned. Better orchestration cannot itself implement these semantics.

**Tests/acceptance:** a deliberately disconnected renderer, missing export and fake-DOM-only implementation fail the integrated gate; narrow storage tests remain useful but cannot pass product acceptance. Evidence binds tree, environment, criterion and original requirements. The small qualification objective may finish independently; it must not silently narrow or complete the preserved broad Minecraft objective.

### O1 — Make context capacity and native effort explicit and consistent

**Owners:** agent context selection, OS faithful preparation/rendering, deployment settings. **Status:** generic preparation/receipts and mixed-endpoint configuration exist; improved preflight and a single effort authority proposed. **Paths:** [runtime/context.py](../src/polyinference/runtime/context.py), [runtime/inference.py](../src/polyinference/runtime/inference.py), [runtime/codex.py](../src/polyinference/runtime/codex.py), [agent/system_settings.py](../src/polyinference/agent/system_settings.py), [system_settings.py](../src/polyinference/system_settings.py), [services.py](../src/polyinference/agent/services.py), UI configuration.

Preflight each actual role binding using the adapter representation and mandatory packet estimate, including native schemas/tool envelopes and output headroom. Report required/prepared bytes, accounting unit, endpoint capacity source and role-specific allowance. The latest native stops were 54,085 > 49,152 and 103,227 > 98,304 conservative bytes before submission. The local server's 65,536 tokens did not mean the 49,152-byte local admission policy used the entire tokenizer window.

Keep conservative byte admission unless an adapter can provide a defensible tokenizer-aware bound; do not label bytes as measured provider tokens. Apply A1/A2's semantic projection first. If mandatory context still exceeds capacity, block with a clear configuration diagnosis; adjust future state/profile only through supported pins. Automatic optional compaction is already available and accounted for, but enabling it does not replace a canonical worker ledger or justify dropping mandatory authority.

The UI starts Codex with low effort while native turn construction sends `Endpoint.reasoning_effort`, default medium. Choose the endpoint field as the explicit authority for a new profile; remove the contradictory launcher override or derive it from that same value. Capture requested startup and actual turn effort in fixtures, and validate provider-supported values. Existing pinned configs retain their historical meaning. No claim about the best reasoning level follows from fixing configuration consistency.

**Tests/acceptance:** different local/native capacities in one run; growing senior/module packets fit or fail before submission; required data never disappears; optional whole tool groups remain intact; retry feedback is remeasured; actual native turn matches configured effort. A generous metadata limit is not a full-window benchmark or native hard generation guarantee.

### O2 — Enforce mandatory data policies and reject unsupported allocation contracts

**Owner:** generic OS. **Status:** proposed repairs of U01/U02, not observed causes of the final stall. **Paths:** [runtime/processes.py](../src/polyinference/runtime/processes.py), [runtime/kernel.py](../src/polyinference/runtime/kernel.py), [contracts.py](../src/polyinference/contracts.py), endpoint/backend capability metadata and runtime bootstrap.

At registration, compare `ScheduleContract.data_policy` to the resolved binding's attested inference location and destination classes. Check context/input artifact classifications against `maximum_classification`. At operation submission, repeat the check against the actual selected backend/inputs and reject unknown or conflicting mandatory constraints before provider contact. A lane named `local` is not proof of physical locality. Static backend metadata can support only its declared guarantee; do not manufacture attestations from URLs or role names. Response replacements, output recovery and cloud takeover must pass the same enforcement.

For distribution rules, specify exactly which semantics static routing can satisfy. Reject unsupported hard weights/windows/variation/rebinding guarantees at registration even if a caller omits an optional feature flag. Supported soft preferences may remain advisory only when explicitly represented that way. Return an actionable unsupported-contract result; never silently store an unenforced hard promise.

**Tests/acceptance:** restricted/local-only data bound to cloud rejects with zero submissions; unknown destination fails closed for mandatory constraints; allowed general non-coding process works; cloud recovery cannot bypass its predecessor's data policy. Unsupported hard schedules reject before process start, while supported static cases and declared soft preferences retain their documented behavior. Reopen incompatible saved state safely; do not rewrite historic specs to make them pass.

### O3 — Align registered process limits with actual execution authority

**Owner:** generic OS. **Status:** proposed U03 repair. **Paths:** [runtime/processes.py](../src/polyinference/runtime/processes.py), [runtime/kernel.py](../src/polyinference/runtime/kernel.py), [runtime/lifecycle.py](../src/polyinference/runtime/lifecycle.py), runtime/configuration contracts.

For the first bounded implementation, retain the current single runtime-limit envelope and **reject unequal `ProcessSpec.limits` at registration**. The open-gap ledger explicitly permits this uniform profile. Current registration accepts a narrower spec, but kernel operation validation requires `request.limits == RuntimeConfig.limits`; that is a mismatch in authority, not a reason to silently widen the spec.

Bind the accepted envelope into registration and validate requests against it and inherited recovery authority. Restore validates the same profile. Share root calls/tokens/operations/deadline across replacements as today. Supporting arbitrary narrower per-process limits is a later explicit extension requiring every admission, reservation, retry and finishing path to use the effective intersection; do not partially support it by changing only one comparison.

**Tests/acceptance:** mismatched registration rejects with no driver/effect; compatible general processes work; forged larger request fails; recovery retains the original cutoff and account; response/output/transport combinations cannot create a fresh envelope. An incompatible historical profile yields a compatibility diagnostic, not an automatic migration.

### O4 — Make paused residency and hibernation/readmission explicit

**Owner:** generic OS lifecycle/admission. **Status:** proposed U04 repair. **Paths:** [runtime/processes.py](../src/polyinference/runtime/processes.py), process status/contracts/ports and admission integration.

Current worker capacity counts unfinished driver tasks. A stopped paused driver drops out even though the declared residency design requires explicit hibernation/readmission. Track logical resident admission durably, independently of the Python task's `done()` state. Preserve management-process treatment explicitly.

Allow a resident paused process to hibernate only after settlement proves it has no active/unknown effects, held execution permits or unreconciled state that requires residency. Record a continuation/source reference and admission generation; release only the logical resident slot authorized by that transition. Unknown provider work still holds its own physical endpoint capacity. Resume requires readmission under the same identity/account/deadline before new execution.

**Tests/acceptance:** max-workers-one plus a paused resident blocks a second worker until safe hibernation; unknown effect prevents release; safe hibernation and readmission work across restart; duplicate requests release/acquire once; cancellation and management paths retain their semantics. This repairs admission truthfulness, not GPU scheduling or transparent live-process migration.

### T1 — Produce useful-progress and failure metrics from canonical records

**Owner:** agent/application reporting plus verification; generic OS supplies facts. **Status:** raw sources largely exist; consistent bounded projections proposed. **Paths:** agent review/reporting, [snapshots.py](../src/polyinference/snapshots.py), UI/export surfaces and a disposable qualification harness, subject to actual source ownership in the JSON tree.

For each trial, report task lineage, backend/model, started/completed/kept nonempty contributions, accepted integrated behaviors, time/physical generations per behavior, repeated read/check share, zero-delta attempts, context omissions/critical-fact availability, retry type, root resources, dependency waits and exact exit cause. Show requested versus actual routing, including model proposal and host policy adjustment. A new ledger revision is not progress credit.

Use a mutually exclusive physical-attempt accounting view to avoid counting both logical usage and its repair rows. Keep provider-reported usage separate from estimates and unknowns. Native jobs can contain many internal turns; do not compare one native job to one raw local generation. An unavailable comparable measure remains unavailable.

Resolve a superseded top-level blocker when a valid new plan changes its condition, retaining the old task's evidence. Started-then-cancelled work remains in historical accounting. Derive live/saved views from the same records; add bounded summary fields rather than relying on a pruned event tail as a complete trace.

**Tests/acceptance:** replay/export causes no extra charges; all 179 latest local physical rows reproduce the correct denominator; superseded started tasks stay visible; no stale current blocker after an actionable replacement; live/saved output agrees. Report completion and containment separately.

### T2 — Repair test/documentation tooling without overstating its guarantees

**Owners:** developer tooling/verification and application configuration. **Status:** audit recommendations proposed. **Paths:** [project_docs.py](../scripts/project_docs.py), [smoke_os_codex.py](../scripts/smoke_os_codex.py), relevant existing test files and [documentation guide](../docs/modules/documentation.md).

Extend documentation checks to maintained rendered HTML links/anchors, with explicit external/upstream/template and generated-output boundaries. Add extraction/coverage checks for exported schema defaults and a length advisory for new guides; keep semantic prose review manual. Preserve archived graph structure/data and make clear that a green structural check does not prove accurate explanations.

Repair the live smoke test's workflow mismatch: choose explicit isolated mode if its assertion is that source stays unchanged, or add an explicit in-place scenario asserting verified integration and retained user work. Do not run the paid smoke merely to validate this report; inspect its mode and use offline fixtures first.

Address the five confirmed baseline failures independently: use a controllable clock or event synchronization for the 25 ms total-deadline, 150 ms pacing observation and 100 ms resume-lookup fixtures, without changing production safety deadlines merely to turn tests green; update both simulator-capacity assertions from the stale hard-coded 32000 target to the configured 4096 target while retaining overlap/refill checks. Supply the existing Node runner explicitly for the skipped frontend cases. First reproduce each failure on the baseline; a demonstrated production defect still needs its own repair.

**Tests/acceptance:** known bad HTML anchor is caught; generated/template exceptions are narrow; schema drift is caught; the chosen smoke-mode assertion agrees with repository behavior; baseline tests become deterministic without weakened assertions. Preserve original failed records and label new results separately.

## 5. Order, dependencies and completion evidence

| Stage | Work and prerequisites | Exit condition |
| --- | --- | --- |
| 0 | Freeze evidence and review the existing FIX-0132 diff; implement Q1/T1 manifests and basic O1 preflight. | Reproducible short-task baseline and complete backend/account/source provenance. |
| 1 | Close O2/O3 for mandatory policy/authority correctness; repair T2's offline fixture mismatches independently. | Unsupported/conflicting profiles reject before effects; no authority widening. |
| 2 | Qualify the existing A3 takeover on short fixtures/live tasks; implement A1 and strengthen A2. | History omission does not erase current task state; actual eligible cloud repair executes; small tasks finish. |
| 3 | Implement A4/A5 and A3's pending-successor handoff with atomic lineage; add A6's browser prerequisite and vertical path. | Mixed retry/restart/dependency cases pass; a real integrated behavior succeeds on the checked tree. |
| 4 | Complete O4 and remaining T2 tooling; run a fresh integrated verification and package/docs checks. | Residency/readmission and all affected generic/agent regressions pass, with explicit baseline exceptions if any. |
| 5 | Run the repeated small workflow gate before increasing scope, concurrency or changing model/quantization. | Three consecutive end-to-end successes plus one interrupted/resumed success, no manual source repair or acceptance weakening. |

Independent work can be developed separately, but the source of every result must be identifiable. Report-document creation is not authorization to start these stages. Stage boundaries should produce reviewable code/docs and meaningful checks; do not carry speculative fixes into an untraceable large patch.

For each package, update its primary module guide, configuration/default references, affected design/issue status, FIX history and navigation in the same implementation. Add new fields/records only with explicit version/compatibility handling. Preserve historical source/configuration pins; the initial rollout can require fresh state rather than invent a general migration.

### Proposed qualification gate in detail

Use one fixed short integrated objective and an independent trusted evaluator. Require three consecutive completions within declared total time/cost envelopes, followed by a fourth scenario interrupted after a settled edit and resumed without losing source or duplicating effects. Also test restart after a cloud handoff using disposable fixture state. An external power failure with genuinely unknown work is a separate fault scenario, not proof that automatic resume is safe.

The controlled fixture gate must inject: malformed complete output; a genuine output cutoff; failed test with useful diagnostics; missing read closure; local settled stagnation; an unchanged/no-op senior plan; conflicting retained delta; already-linked pending consumer; native input overflow; cancellation; depleted accounts; and an unknown later response-repair attempt. Expected unsafe cases must stop with preserved evidence, not be counted as successful completion.

Require the actual entry/DOM/browser path, save/reload state and original small objective to pass on the accepted tree. Record useful contributions, cost, context-critical-fact retention and exact exit causes separately. Three successes are an initial engineering gate, not a statistical reliability claim. Only after it passes should an explicitly authorized broader product trial change one dimension at a time.

## 6. Historical failure coverage matrix

**Coverage means design coverage, not proof of successful historical rerun.** “Covered” means a concrete existing/proposed mechanism directly targets the recorded failure class. “Partial” means it improves detection/recovery or only a supported subset; model/product success remains unproved. “Not covered” means the cause is outside these fixes. Rows marked prospective are current source/design gaps, not claimed historical live causes.

| ID | Recorded failure or gap / evidence | Existing repair and proposed work | Coverage and remaining limit |
| --- | --- | --- | --- |
| F01 | V10 `d434799ad8e4`: completed response with no visible text became an unrecoverable generic error. | Existing normalized response facts and safe retries, FIX-0044/0045; A4 retains error-conditioned fallback. | **Covered** for known completed eligible responses. The old lost provider facts cannot be reconstructed. |
| F02 | V12, 24 October (27/120 inventory protocol failures), 25 October (20 validation failures), latest 13/179: invalid action grammar. | Existing validators/correction bounds; Q1, A1, A4 and smaller actions. | **Partial.** Better feedback and bounds cannot guarantee model compliance; nine of eleven unchanged retries becoming valid did not establish task progress. |
| F03 | V12 cutoffs/whitespace and 25 October confirmed length error. Latest malformed large write was not established as a cutoff. | Existing incomplete-output rejection/adaptation; O1 headroom and A4/A5 smaller responses/reserves. | **Partial.** Native hard generation control and effectful replay remain limited; format failures must not be mislabeled truncation. |
| F04 | V11 `2de3d5c5ab9b`: application estimate fit while serialized context exceeded the input limit. | Existing adapter-aware OS preparation, FIX-0055/0058; A1 and O1. | **Covered** as a preparation/admission mechanism. Truly oversized mandatory input still stops. |
| F05 | Latest attempts 1/2: native required packets exceeded configured ceilings. | Fresh historical profile correction; O1 per-binding preflight and compact required projections. | **Covered** for avoidable sizing/configuration mismatch, not unlimited context. |
| F06 | 24 October history omission and CAS rejections; latest 145 local-result omissions, repeated reads/digest mistakes. | Current mutation responses already return digests; A1 authoritative projection/invalidation, O1 receipt inspection. | **Partial.** Particular forgetting and quantization causation were not isolated. |
| F07 | V12 missing entry file; V13 shared test discovery; V14 exact mandatory test paths/grants disagreed. | Existing shared-check planning; A2 explicit closure, runner prerequisites and A6 interface checks. | **Covered** as planning validation, without borrowing write grants. |
| F08 | V12/V13 private candidate mentioned but `resume_from` absent; source reconstruction repeated. | Existing explicit source offers/handoff, FIX-0089 and merge safeguards; A3 qualification. | **Covered** for validated one-source reuse; conflicting/unknown or multi-source work still needs explicit planning. |
| F09 | 24 October wrong scope story caused a clean worker to globally pause with pending tasks. | Existing exception packets/parking/senior review, FIX-0125/0126; A2/A3/A4 evidence-based continuation. | **Covered** for clean stopped exceptions, not a grant to retry unknown effects. |
| F10 | 25 October audit used all 256 calls; latest physics/menu stalled without useful deltas. | Existing novelty guard; A1–A5 plus Q1. | **Partial.** Containment, finite cloud repair and smaller tasks improve opportunity; useful semantic convergence still depends on the worker. |
| F11 | Latest cloud senior proposed local replacements; ordinary depth exhausted with 43/256 and 87/256 calls. V12 also lacked deliberate specialist escalation. | Existing uncommitted A3 policy normalizes eligible exceptions to real cloud coding and preserves role through allocation. | **Covered** at the policy level, pending fresh live qualification. No observed allocator overwrite is attributed to the latest saved proposals. |
| F12 | Already-linked pending consumer cannot be automatically cloned without detaching lineage (prospective current limit). | A3 pending-successor CAS transaction and explicit unsupported-plan fallback. | **Covered by proposed design**, not implemented; unrelated fresh accounts are forbidden. |
| F13 | V13 Chromium smoke covered shell, not required gameplay; latest 25 unit tests passed while browser was unplayable. | Existing separate acceptance/exact-tree review; A6 independent vertical behavior gate. | **Covered** as an acceptance/detection gap. Passing it still requires actual application repair. |
| F14 | Repeated x/y versus x/z migration mismatch; latest private `mountShell` missing and browser save wiring absent. | A2 migration dependencies, A6 production-entry/DOM/storage checks and concrete scoped repair tasks. | **Partial.** Tests identify failures but cannot guarantee that implementation succeeds. |
| F15 | 24 October static inventory defects and false feature documentation; 25 October audit factual errors. | A2 versioned requirements; A6 independent feature/API/conservation tests and review. | **Partial.** This is domain/application correctness, not an OS scheduling defect; source findings are not all reproduced live bugs. |
| F16 | V12 interrupted native job; V14 submitted Haiku request became uncertain at 180.005 seconds. | Existing SSE/timers/typed lifecycle, explicit generation-only isolation and reconciliation; O1 profiles/Q1 fault cases. | **Partial.** Unsupported status/cancel and one-slot unknown computation can still require an honest stop. |
| F17 | Historical retry composition/response exhaustion could multiply submissions; restart could mis-handle later unknown repair ownership. | Existing FIX-0047/0117/0127; A3–A5 combined-path/restart checks. | **Covered** as an accounting/replay mechanism. Never equate prepared bookkeeping with termination. |
| F18 | U01–U04 data policy, unsupported hard distribution, limits and paused residency (prospective enforcement gaps). | O2–O4 explicit enforcement/rejection and durable admission. | **Covered by proposed design**, not implemented and not an established final-run cause. |
| F19 | V12 stale blocker and cancelled-start accounting; later application active-worker fields could outlive a stopped driver. | Existing accounting/cleanup fixes, T1 consistent live/saved derived status. | **Covered** for truthful management state. A display correction itself does not complete a task. |
| F20 | Confirmed external power interruption in early 24 October attempt; possible future hard outage or unavailable provider/model. | Preserve evidence, accounts and unknown holds; qualify recovery only when termination is known. | **Not covered as elimination of the cause.** Bounded recovery/diagnostics are possible; no software plan guarantees power, service availability or model competence. |

### Would this address most past failures?

**For recurring orchestration causes, yes, the combined existing mechanisms and remaining plan are a strong match.** Missing closure, non-materialized retained source, global clean-exception pauses, local-only recovery, avoidable context sizing and weak integration gates each have a concrete owning-layer change. These appear repeatedly across providers and runs, so they are more defensible engineering targets than assuming all failures came from one setting.

**For completed products, the answer is not yet established.** Latest physics attempts had no retained implementation delta, menu repair kept the same broken delta, and real integration remained absent. Most latest generations were schema-valid, so formatting alone is not the explanation. A cloud storage repair succeeded, but that does not predict the success rate of cloud physics/menu repairs. No matched same-source/model/task trial isolates ledger quality, task size, quantization or thinking settings. Unknown execution and missing actual capability must still stop safely.

The table groups failure mechanisms rather than counting independent incidents; prospective rows are explicitly separated. It is not a statistical sample or a percentage of failures prevented. The decisive next result is a repeatable small integrated completion under Q1, followed by the interrupted/resumed scenario. Until then the correct claim is “better targeted recovery with preserved safeguards,” not “long workflows are now reliable.”

## 7. Evidence routes and provenance

Portable repository evidence reviewed includes the linked 27 October brief/analysis, [cloud recovery implementation record](local-task-granularity-and-cloud-recovery-2026-10-27.md), [documentation/reliability audit](documentation-and-reliability-audit-2026-10-27.md), [merge verification record](branch-integration-audit-2026-10-26.md#verification-record), [real Strata investigation](local-strata-live-test-2026-10-26.md), [v10](run-d434799ad8e4-analysis.md), [v11](run-2de3d5c5ab9b-analysis.md), [v12](run-eb66fc618354-analysis.md), [v13](run-a1859f8644a5-analysis.md) and [v14](run-7086c575ef94-analysis.md). Related fix history was checked for ownership, supersession and earlier safeguards; this was a scoped analysis, not a revalidation of every historical entry or every upstream specification.

Machine-local evidence remains outside the maintained source inventory:

| Source | Exact location and useful records |
| --- | --- |
| 24 October local run | `/home/marven/Projects/pi/testing/minecraft-v1-run/README.md`, `UNFIXED-ISSUES-ANALYSIS.md`, `result-05/unfixed-analysis.json`, retained `state-05`. |
| 25 October local run | `/home/marven/Projects/pi/testing/minecraft-v1-live-2026-10-25-0300/REPORT.md`, `state-02`, `result-2026-10-25-0500` checks/browser/diagnosis and exports. |
| 26 October latest run | `/home/marven/Projects/pi/testing/minecraft-v1-live-2026-10-27-0200/REPORT.md`, attempt-02/03 SQLite state, accounting summaries, `result/recovery-lineage.json`, private deltas and independent checks/browser evidence. |
| Prior payload/routing audits | Same latest directory, `management-review-evidence-2026-10-27.json` and `cloud-resolution-audit-2026-10-27.json`. These are historical audits, not new live execution. |

Earlier v10–v14 reports retain exported record IDs, hashes and verification limits. Their original external export files were not exhaustively rediscovered or rehashed in this task. The latest two attempts' database queries provide additional direct evidence, rather than relying exclusively on prose. No historical source, account or journal was migrated or cleared.

## 8. Report maintenance and verification

This task adds the report, its navigation/index/issue pointers, an investigation-only FIX entry and a retained project note. It changes no runtime, agent, provider, configuration, test or generated-game implementation. No paid/live inference, browser/game execution, preserved-run resume, commit or push occurred.

Verification for this report: documentation generation and `--check`, report/link/whitespace review, and preservation hashes for existing implementation/test/example/script files and selected historical database/journal files. Exact observed results are recorded in FIX-0133. Historical FIX-0132's 227 passing selected cases plus one unchanged baseline failure, and the merge audit's 585 passing cases/five baseline failures/two skips, were not rerun or claimed as this report's tests.

Adjacent runtime/context/retry/process, check/acceptance, recovery and configuration guidance was reviewed for ownership and current-status consistency. Those execution guides require no behavioral edit for a planning report. Developer/onboarding rules and credential/setup flows are unchanged. The project note in AGENTS.md records this report's status and was read back; it installs no hooks or runtime automation.
