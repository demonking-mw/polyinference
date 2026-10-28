# Workflow completion: engineering analysis and decision record

27 October 2026 · Investigation only; no runtime, agent or provider implementation changed.

Subsequent implementation: [local task granularity and cloud recovery](local-task-granularity-and-cloud-recovery-2026-10-27.md).
The analysis below describes the investigated revision and preserved live runs;
the new uncommitted policy must be qualified with fresh state, not those old runs.

[Meeting brief](workflow-readiness-brief-2026-10-27.md) · [FIX-0130](FIXES.md#fix-0130) ·
[Latest live investigation](local-strata-live-test-2026-10-26.md) ·
[Merge audit](branch-integration-audit-2026-10-26.md)

## Scope and current codebase

Reviewed current `codex/simple-os-v1` at merge `5fe92f3`, its working documentation,
the pinned latest live source, saved SQLite records, exports and prior run reports.
Current implementation source is unchanged from the merged revision. Existing
documentation edits and unrelated work were preserved. This review launched no
inference, resumed no old run, changed no budgets and made no game implementation.

The merged reliability work addresses retry multiplication, shared recovery accounts,
clean exception review, retained-source handoff, progress observations, module
contracts and exact-tree semantic completion. It also preserves unknown-execution
barriers and source authority. These are material safeguards, not evidence that a
long application-building loop converges. The latest test reached safe failure rather
than accepting private unfinished work.

Historical framework verification is 585 passed, five unchanged baseline failures
and two skips, using the latest result per case across several runs. It is not one
green full-suite result on the final tree. This documentation review reruns only
documentation/navigation and whitespace checks; it claims no new framework suite.
Known baseline fixture failures remain separate from the live stagnation finding.

The user reports no successful long-running workflow to date. The inspected three
Minecraft test periods support lack of accepted end-to-end delivery for this workload.
They do not establish that every subtask or every possible project has failed.

## What the retained runs establish

| Run | Literal stop | Useful output and limit of evidence |
| --- | --- | --- |
| 24 October, final attempt | Worker voluntarily requested review with an incorrect scope explanation; old controller paused globally. It had used 120 of 128 calls, not exhausted them. | Documentation and simulation foundation were kept; inventory candidate stayed private. Seven downstream tasks never started. No playable game. Some historical defects identified then are fixed in current source. |
| 25 October, final attempt | Mandatory phase allowance exhausted after a local audit consumed 256 calls. Earlier attempt exhausted review retrieval. | Native README setup change only. No gameplay development task completed; repeated passed checks did not establish product progress. Source was pinned before the later recovery/progress integration. |
| 26 October, attempts 1/2 | Required native input 54,085>49,152, then 103,227>98,304 conservative bytes, before provider submission. | First is setup-only; second retained a storage implementation completed by native specialist recovery. Separate configurations/states, not retries that rewrote old limits. |
| 26 October, final attempt | Stagnation fences, one linked recovery per root exhausted, then `No runnable tasks; resolve the blocker or supply new input`, paused/exit 2. | No net physics delta in any of three physics attempts; unchanged private menu delta after recovery. No final acceptance attempt. |

Latest development totals: 179 local physical generations, 13 schema-validation
failure records, 145 receipts with optional-history omission, largest original
packet 237,382 bytes. Counts include response retries and repeated/cached input.
Final independent tests passed 25 cases: 11 inherited core and 14 storage cases.
The browser remained black/overprinted with an x/z renderer against an x/y core.
Private menu code did not export `mountShell`; its real-browser probe failed before
the additional questionable DOM calls were reached. No new UI suite was produced.

The final receiving project remains unborn `pi-dev`, unstaged and uncommitted.
Only exact checked setup/storage exports were applied. Private source, original
inputs, all configurations, failed outcomes and three supported UI exports remain.
All stopped exports report zero uncertain effects. Authentication and sustained real
local generation succeeded. No latest-run persistent authentication outage, GPU OOM
or expired total worker allowance is established as the final stopping cause.

## How the stopping rules work

“Agent” includes application/controller code running on the host, not only the LLM.
In particular, `agent/routing.py` and `agent/progress.py` are agent policy, not generic
OS scheduling. “Uncertain task progress” and “unknown physical execution” are distinct.

| Condition | Intuitive meaning | Current handling |
| --- | --- | --- |
| Transport retry | The request failed in a way that is established safe to try again. | OS filters retryability, termination/effects, remaining budget, backoff and deadline. Coding default is two extra transport retries; caller extras are separately declared. Permanent input/auth/grant failures are not cured by repetition. |
| Schema retry | A completed eligible raw/read-only response did not satisfy the application validator. | Agent supplies grammar; OS applies it and records physical attempts. Default `inference_retry.max_attempts=2` includes the first attempt. Effectful native jobs are not blanket eligible. |
| Worker grammar correction | After lower-level handling, a reply is still not a usable action/candidate/assessment/review request. | Agent adds diagnostic feedback and advances to a new decision. Default three corrections means the fourth consecutive invalid logical reply parks. A valid reply resets this streak. |
| Stall | Settled decisions have not produced new tracked evidence. | Agent warns at eight idle decisions and parks at twelve in enforce mode. This counter is separate from grammar errors and physical retries. |
| Failed check | A command finished and reports a product/test failure. | Its execution can be successful while its check status is failed. Agent inspects evidence, edits/repairs, or uses bounded diagnosis; OS does not decide what code to write. |
| Worker recovery | A stopped task needs a changed implementation approach. | Agent senior chooses retry/defer/stop. Retry requires a new linked task and stated changed condition; default maximum is one replacement per root. OS binds original account, grants, limits and deadline. |
| Unknown execution | A disconnect/cancellation did not prove what the remote computation or tool did. | OS retains uncertainty and conflicting ownership; reconcile before unsafe continuation. Optional generation-only isolation needs adapter facts, explicit consent and spare capacity. One-slot serving does not gain another slot by losing a connection. |
| Input overflow | Required prepared input cannot fit the declared endpoint allowance. | OS stops before submission. Agent/setup must reduce permitted input or correct actual endpoint configuration through supported new intent/state. Deleting required authority/objective data is not a repair. |
| No runnable work | Required providers are deferred, dependencies cannot become ready, and no allowed assignment remains. | Agent controller pauses; an unfinished obligation cannot become completion. This was the final latest-run stop. |
| Budget/phase exhaustion | Call, operation, token, deadline, review or sprint allowance is no longer sufficient. | Runtime enforces its resource bounds; agent reserves finishing work and can propose a candidate before development exhaustion. Mandatory-phase exhaustion still stops without an accepted result. Latest profile used 256 calls/root, 1,024 steps, four hours/process and 18 sprints. |
| Incompatible resume | Saved code/configuration/program identities no longer match. | Explicit compatibility rules apply. Arbitrary historical states are not migrated by editing their journals; preserve pinned source and use supported fresh execution or a separately implemented migration. |

### Exactly what is a stall?

Progress is sampled between settled application decisions. A generation still running,
a pending operation or a physical uncertainty barrier is not a twelve-decision stall.
Native jobs are observed at application boundaries; their internal model loops are
not preempted by this policy. Setup and explicit model-recovery paths have exceptions.

The implementation credits previously unseen tree/environment identities, protocol
phases, file listings, file content/range coverage and check tuples. A check tuple
includes criterion, tree, environment and status; even a new failed outcome can be
informative. Novelty resets idle to zero. Re-reading identical bytes or overlapping
already read ranges does not. Returning to a previously seen tree, timestamp changes,
narration, rewritten memory and mere endpoint activity do not earn progress credit.

Examples: reading a new part of a file resets idle; rereading the same part does not.
Rerunning the same passed test on the same tree is not progress. A new wrong edit can
count as novelty and still fail acceptance. A valid repeated read resets the grammar
error streak, but not necessarily the stall counter. Thus neither “valid JSON” nor
“the model is busy” proves that the task is advancing. The eight/twelve thresholds
are tuning choices with live fencing evidence, not calibrated productivity bounds.

Automatic stagnation routes directly to parking/senior review. The bounded checking
agent exists for explicit `needs_review` and relevant failure paths; a stall does not
automatically run a stronger diagnosing worker first. On clean parking, source and
diagnostics are retained, the process is fenced and owned permits are released.

### Exactly what can recovery change?

One replacement per disposition is supported; automatic fan-out into several resumed
subtasks is not. Reusing a private delta requires explicit `resume_from`, compatible
base and covering grants. Pending dependents must be cancelled/replaced with corrected
IDs; started assignments/contracts remain pinned. New unlinked overlapping work cannot
evade unresolved exception obligations. Defer leaves the objective unfinished.

The replacement does not get a fresh 256-call allowance or a new four-hour clock.
Diagnosis also shares the worker account. Senior management has separate bounded
resources. More descriptive recovery wording alone does not establish a changed
execution strategy. The latest menu replacement retained the identical final delta.

The normal specialist allocation is rounded by task count with pending reservations,
excluding management/setup. At fraction 0.1, four slots yield zero specialist quota;
five yield one. The host-coded agent allocator can override the model's proposed
role. Latest linked recoveries stayed local; the earlier storage recovery was native.
This policy is not failure-severity-aware and is not generic OS model selection.
The later cloud-resolution audit below qualifies causation: both final replacement
roles were already `worker` in the cloud senior's saved pre-allocation proposals.
They were not cloud-specialist requests overwritten by the allocator.

## Cloud-resolution fix history: present, but a narrower guarantee

**The cloud escalation fixes exist and were not overwritten by the merge.** The
earlier report needed to distinguish cloud review, cloud diagnosis and cloud repair
more explicitly. A normal specialist quota can constrain repair allocation, but
its ability to rewrite roles is not proof that it did so in the saved final run.

| Implementation | Actual guarantee | History/current verification |
| --- | --- | --- |
| `309713c`, configured checking agent | Non-passed configured checks and explicit worker `needs_review` can invoke bounded read-only diagnosis. | Ancestor of current HEAD. `agent/diagnostics.py` is byte-identical to the pre-merge fix tip. `CheckDiagnosis.role` defaulted to `worker` when introduced and still does; cloud was never mandatory. |
| `073f523`, FIX-0125 | Clean stopped workers become senior-review exceptions rather than immediately pausing the entire run; linked recovery retains source/accounts/deadlines. | Ancestor of HEAD; exception queue, senior dispositions and linked replacements remain present. |
| `cb2fae5`, FIX-0126 | Sustained stagnation enters the same clean exception/senior-review path. | Ancestor of HEAD. Its original worker graph already routed `progress → park`, bypassing the checking-agent node; the merge preserved that route. |
| Separate `a07f007` profiles branch | Explicit read-only diagnostic execution for a user-requested diagnostic job. | Not merged into HEAD. This is a different feature from automatic cloud stall repair; it is not a missing cloud-rescue patch. The other worktree was not modified. |

The [implementation fix log](../design-docs/implementation/FIXES.md) records FIX-0125
and FIX-0126. Current [worker graph](../src/polyinference/agent/worker.py),
[diagnosis](../src/polyinference/agent/diagnostics.py),
[application configuration](../src/polyinference/config.py),
[controller allocation](../src/polyinference/agent/controller.py) and
[routing policy](../src/polyinference/agent/routing.py) establish the remaining paths.

Three cloud responsibilities must be separated:

- **Checking agent:** read-only classification, diagnostic evidence and bounded read
  expansion/guidance. It does not write the implementation, even when bound to cloud.
- **Senior resolver:** read-only review/planning that returns retry/defer/stop and
  proposed tasks. Cloud reasoning here does not itself execute the source repair.
- **Specialist worker:** actual scoped implementation under the worker protocol.
  This is the cloud path that completed the earlier storage recovery.

Normally completed reports also await senior resolution. FIX-0125/0126 extend that
review to clean interruptions that never produced a completed worker report.

Both latest development configs explicitly selected `check_diagnosis.role=specialist`
and `specialist → cloud`. Nevertheless both saved states have zero `diagnosis/`
records. Automatic stagnation is an agent-generated attention/parking event, not a
worker `NeedsReview` response or a failed-check trigger. Its uncertain-style warning
does not automatically call the configured checker.

| Retained event | Cloud involvement | Repair execution/result |
| --- | --- | --- |
| Attempt 2 storage stall | Cloud senior proposed `specialist` recovery. | Allocator retained specialist; native recovery completed storage and 25 tests passed. |
| Attempt 3 locomotion stall | Cloud `senior-2` reviewed it. | Senior proposed `worker`; allocated `worker`; local recovery stalled. |
| Attempt 3 locomotion recovery stall | Cloud `senior-3` reviewed it. | Recovery depth was exhausted; deferred, with no implementation delta. |
| Attempt 3 menu stall | Cloud `senior-4` reviewed it. | Senior proposed `worker`; allocated `worker`; local recovery stalled with the same delta. |
| Attempt 3 menu recovery stall | Cloud `senior-5` reviewed it. | Recovery depth exhausted; deferred; final controller had no runnable work. |

Saved native backend identities confirm `gpt-6.1-sol` cloud senior calls. Proposal
records are saved before `_apply_review` runs allocation, so this comparison checks
the senior's requested role against the actual issued assignment. It does not infer
intent from the already allocated task. Attempt 2's later physics review could not
finish because its follow-up native packet exceeded the input ceiling.
The senior prompt describes the normal allocation rule, so that policy may also
influence its proposals. Matching requested/issued roles rules out an observed
overwrite here; it does not isolate why the senior chose local replacements.

**Management correction:** the cloud decision path was exercised; effective repair
did not follow. There is no inspected historical rule guaranteeing that most stalls
become cloud-executed repairs. If that is the product requirement, implement it as an
explicit application recovery policy: eligible stall gets bounded cloud diagnosis,
then a concrete repair/decomposition decision, with an allowed specialist repair
outside normal task-share rounding when needed. Keep inherited accounts/deadlines,
write scope, provider/data restrictions, source provenance and recovery depth. Test
the trigger and actual issued role, not merely that a cloud review call occurred.
Choose this route on the first permitted replacement when justified; spending that
sole replacement on another local loop can leave no recovery depth for later cloud
coding. This does not authorize another attempt after an account is exhausted or
while physical execution remains unknown.
This is a proposed enhancement, not a repair implemented by this report.

## Agent, OS and provider ownership

The matrix describes responsibilities and implemented mechanisms in the consistent
profile exercised here, not complete enforcement of every OS declaration. Existing
[U01–U04 gaps](../design-docs/simplified-os/DESIGN_REVISIONS.md#open-implementation-gaps)
remain: conflicting process data policies are not fully validated, unsupported hard
allocation schedules are not always rejected, narrower registered process limits
can differ from the runtime execution envelope, and paused residency lacks the
specified hibernation/readmission transition. Uniform settings are a precaution,
not a fix. These gaps are separate from the latest observed stagnation stop and
must be resolved before claiming general enforcement across arbitrary profiles.

| Topic | Agent/application owns | Generic OS/runtime owns | Provider/server owns or limits |
| --- | --- | --- | --- |
| Decomposition and integration | Tasks, done criteria, dependencies, interface versions, closure, role allocation and changed recovery strategy. | Starts/waits, grants, resource permits and execution observations. | Actual serving concurrency and generation behavior. |
| Canonical memory | Meaning of plans, progress, notes, unresolved errors, source digests and next steps. Shared senior summary/notes already exist. | Durable original records/artifacts, derived-view provenance and scoped access. | The model reasons only over delivered input and its supported session behavior. |
| Context selection | Marks required/optional/compactable parts and chooses what semantic state must remain. Current assignment, contracts, memory and progress attention are pinned. | Measures adapter representation, packs whole optional groups and enforces capacity. It cannot decide which gameplay fact is important. | Actual tokenizer/window and native harness context; configured metadata is not a full-window measurement. |
| Compaction | Selects eligible content and retains authoritative semantic memory. | Optional bounded summarization on the same binding/account/deadline, immutable originals and receipts. | Summary quality is model-dependent. |
| Reply grammar | Defines WorkerReply/schema and useful corrective feedback. | Executes registered validators and bounded physical attempts, preserving failures/usage. | Strata advertises prompt-and-validate, not constrained decoding. Schema support is not a guarantee of valid generation. |
| Confirmed model output cutoff | Chooses smaller edits/output units and task continuation; no automatic code chunking is supplied by generic retry. | Recognizes terminal cutoff/overage, retains evidence, rejects partial actions and issues bounded smaller-response adaptation. | Raw token limits include thinking. Native hard generation-token enforcement is unavailable; strict requirement rejects before submission. |
| Clipped tool/check preview | Selects sufficient diagnostic excerpts and retrieves authorized full evidence when needed. | Retains full artifacts/references and bounded presentation. | This is not a model token cutoff. |
| Stale file/CAS or scope rejection | Refreshes correct source/digest and repairs within authority; escalates a concrete missing grant instead of inventing one. | Enforces digest/generation/grant preconditions and preserves source. | Role/model capability does not grant more filesystem authority. |
| Known failed inference | Chooses semantic repair and allowed extra retry policy. | Classifies safe retryability, records each attempt and enforces admission/accounting. | Returned error and terminal metadata must support the classification. |
| Unknown execution | Supplies a legitimate continuation/recovery intent and respects unresolved effects. | Holds ownership, reconciles evidence and prevents unsafe duplicate dispatch. | Recovery/status handles and cancellation proof vary; losing transport is insufficient. |
| Product acceptance | Meaningful task/final checks, exact-tree review, kept contributions and the user's full objective. | Executes registered operations and guards atomic publication/provenance. A non-coding OS process needs no Git or product checks. | A completed model request is not a feature or product verdict. |

### Context behavior that matters in this configuration

The coding default enables deterministic packing but leaves lossy compaction off.
The latest run inherited that policy. Capacity is the minimum of the declared view
limit, shared per-call input limit and endpoint context minus output headroom. Local
65,536 minus 16,384 yielded 49,152 conservative UTF-8 bytes. This is not 49,152
tokenizer-counted tokens. Raising the native shared ceiling fixed native packet
admission; it did not increase this local allowance.

The OS removes oldest optional complete groups first, preserving tool call/result
pairs and required input. It retains original history and omission receipts. Tool
history emitted by the current application is not marked compactable. Merely turning
on OS summarization does not create a useful worker task ledger or authorize arbitrary
summarization of every tool pair. A required packet can overflow even after all
optional history is removed. Do not disable bounds or pretend the model has more
capacity to conceal that problem.

The application already includes shared memory and current progress attention.
The gap is a bounded, verified worker state projection that survives history omission:
completed changes, latest necessary per-file digests, current failing evidence,
unresolved obligations and the next small action. The OS's preserved archive does
not provide those semantics automatically. Memory growth itself must remain bounded.

### Three different things called truncation

1. **Provider output cutoff:** explicit length/max-output terminal or detected overage.
   Partial returned actions never execute. OS asks for a smaller complete answer,
   subject to safety, resource, adaptation and retry bounds. Native brokered effects
   already performed cannot simply be repeated. Raw output admission is not the same
   guarantee as native hard generation control.
2. **Malformed but completed JSON:** use application validation/correction. The latest
   long malformed write was below the token ceiling; a token-limit root cause is not
   established. Do not concatenate its prefix with a later reply and execute it.
3. **Presentation/input omission:** a short diagnostic preview or omitted prompt history
   retains its original artifact. The agent needs appropriate retrieval/state selection;
   retrying generation unchanged does not make the missing information appear.

There are separate response-validation, transport, smaller-output, grammar-correction,
check-repair and semantic-replacement bounds. They are not one universal retry count.
All physical work must retain resource/deadline accounting; combined-path tests should
verify ceilings and finishing reserves instead of assuming each setting is independent.

## New evidence from this source/data review

The immediate response-retry path offers the owner a replacement window, default one
second. Without a supplied replacement it reuses the original payload. The coding
application registers validators but has no production caller of `offer_retry` in
current source; the other references are port definitions and tests.

Saved latest-run records confirm eleven automatic local follow-ups after schema
failure, all with identical payloads and zero supplied replacement payloads. Nine
follow-ups became schema-valid; two failed validation again. This is useful format
recovery through repeated generation, not evidence of task-level repair. A valid
replacement reply can choose a different action from the original failed write.
Only later worker correction adds application diagnostic history. This finding does
not justify blaming all stagnation on JSON, which failed on 13 of 179 generations.

## Failure assessment and recommended priority

| Finding | Confidence | Consequence and next owner |
| --- | --- | --- |
| Large multi-behavior assignments remain despite module contracts. Latest physics added migration/versioning to movement/collision work; menu combined many screens. | Observed task scopes; contribution to failure is an inference. | Agent: define small behavior-plus-check deliverables, not just fewer filenames or more detailed instructions. |
| History omission is frequent and no dedicated automatic bounded worker ledger is visible. | Observed receipts and current context construction. Forgetting of any particular fact is not isolated. | Agent first; OS supports accurate measurement/provenance. Compare ledger vs history under otherwise identical tasks. |
| Cloud senior review occurred, but recoveries retained local execution; normal quota does not guarantee exceptional escalation. Automatic stall bypasses diagnostic worker. | All four final stalls reached cloud review. The senior proposed both local roles; no cloud role was overwritten in those cases. Benefit of a different repair route is not yet measured. | Agent: connect cloud review to an evidence-based repair decision, explicit exceptional routing and inherited-account rules. |
| A complete dependency chain waits for failed foundations; no early playable milestone is delivered. | Observed pending/cancelled consumers and black final browser. | Agent/planner: start with the smallest integrated path and keep it exercised as features grow. |
| Protocol errors and wrong API/CAS behavior reduce efficiency. Same-payload retry recovered format in nine cases. | Observed; formatting is a contributor, not the dominant demonstrated stop. | Agent + adapter interface: qualify tool/grammar reliability and improve error-conditioned repair before adding larger model budgets. |
| Broad project ambition makes poor qualification evidence. Model, quantization, history, task design and recovery were not independently varied. | Experimental limitation. | Test owner: controlled short coding/tool tasks, then integrated repeated runs. Do not assume either model incapacity or orchestration innocence. |
| Unit checks and operation-success counts can look healthy while product progress is absent. | Observed 25 passing tests, zero physics delta, no UI suite, failed browser. | Agent + test owner: make actual entry-point/DOM/browser behavior part of milestone evidence. |
| Unknown execution, exhausted bounds, incompatible pins, missing closure and bounded review can stop future work. | Implemented guard paths; not the latest final physical-uncertainty cause. | Preserve OS guarantees. Improve preflight, typed diagnostics and tested recovery affordances rather than weakening them. |

The model/quantization may impose a reliability floor, but this run is not a controlled
quantization or model comparison. Likewise, no persistent latest-run OOM or auth outage
explains the final stop. Ordinary source/permission safeguards should not be weakened
to turn a failing run green. A new tree/valid reply is a weak progress signal, not a
substitute for an accepted behavior.

## Proposed management sequence and exit criteria

1. **Establish a bounded qualification baseline.** Pin this source/profile and a small
   task set: one concrete file repair, a real DOM mount/event task, and a save/load
   continuation task. Repeat without supervisor code edits. Record execution validity,
   grammar validity, evidence novelty, kept feature and final outcome separately. If
   short clean tasks fail, address model/tool-protocol suitability before expanding
   orchestration. Model or quantization alternatives require separate recorded trials.
2. **Repair task continuity and task sizing.** Add a compact worker state projection
   with source/evidence references, bounded errors and current digests; measure exactly
   what remains in each prepared request. Split physics/migration and UI mounting/forms
   into testable milestones. Explicitly design parent obligations/account lineage if
   implementing multi-task recovery; current one-replacement semantics do not supply it.
3. **Make recovery change a demonstrated condition.** Use the concrete last failure and
   retained diff, not only a longer prompt. Consider one bounded diagnosis before a
   stall is parked, or an evidence-based specialist exception outside normal task-share
   rounding. Make semantic feedback available to response repair. Preserve cumulative
   account, grant, deadline and uncertain-effect guarantees; test mixed retry layers.
4. **Require an early integrated product gate.** Render a visible world/player, exercise
   an input, pause, save, reload and verify state through actual entry modules. Include
   real DOM tests; a bespoke fake DOM must not certify nonexistent browser APIs. Keep
   narrow unit tests as additional evidence and the full original requirement open.
5. **Qualify sustained operation.** Proposed initial gate: three consecutive small
   end-to-end completions plus an interrupted/resumed run, within declared total time
   and cost, with no manual implementation or acceptance weakening. Include a known
   malformed reply, a genuine output cutoff and a failed test in controlled fixtures;
   test unknown-execution handling separately using proper termination evidence. Only
   then expand project size or worker concurrency. This is not a statistical SLO.

Useful measures are time and physical generations per kept behavior, repeated-read
share, zero-delta attempts, context omission and retained critical facts, retry type,
remaining root allowance, dependency wait and exact exit reason. Keep native multi-turn
jobs distinct from raw local generations. A green process counter or large token spend
does not establish useful output. Broad overnight trials should pause as a qualification
strategy until the small workflow gate passes; this report does not schedule or run it.

## Source and evidence routes

Current implementation: [agent progress](../src/polyinference/agent/progress.py),
[worker graph](../src/polyinference/agent/worker.py),
[context construction](../src/polyinference/agent/services.py),
[role allocation](../src/polyinference/agent/routing.py),
[controller](../src/polyinference/agent/controller.py),
[diagnosis](../src/polyinference/agent/diagnostics.py),
[exception packets](../src/polyinference/agent/exceptions.py),
[OS context](../src/polyinference/runtime/context.py),
[response retries](../src/polyinference/runtime/retry.py),
[transport/output adaptation](../src/polyinference/runtime/model_retries.py),
[inference normalization](../src/polyinference/runtime/inference.py),
[kernel accounting](../src/polyinference/runtime/kernel.py), and
[recovery lineage](../src/polyinference/runtime/lifecycle.py).

Contracts/guides: [boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md),
[progress policy](../design-docs/implementation/PROGRESS_MONITORING.md),
[worker recovery](../design-docs/implementation/WORKER_RECOVERY.md),
[OS settings](../design-docs/simplified-os/AGENT_SETTINGS.md),
[configuration](../docs/guides/configuration.md), [retries](../docs/modules/retries.md),
[context](../docs/modules/context.md), and [workers](../docs/modules/agent-workers.md).
These guides were reviewed; this report does not change their execution contracts.
The concurrent [documentation/reliability audit](documentation-and-reliability-audit-2026-10-27.md)
adds broader retained-run history and separate code/tooling follow-ups. Its edits
are preserved and not claimed as changes made for this meeting report.

Machine-local retained evidence, not committed source:

- `/home/marven/Projects/pi/testing/minecraft-v1-run/README.md` and its result-05 records.
- `/home/marven/Projects/pi/testing/minecraft-v1-live-2026-10-25-0300/REPORT.md` and state-02.
- `/home/marven/Projects/pi/testing/minecraft-v1-live-2026-10-27-0200/REPORT.md`, attempt-02/03
  records, accounting summaries, exact exports, private diffs and browser evidence.
- Same latest directory: `management-review-evidence-2026-10-27.json` records this review's
  read-only payload/format-outcome comparison. It dispatched no inference.
- Same directory: `cloud-resolution-audit-2026-10-27.json` records ancestor/blob checks,
  configured cloud-checker roles, empty diagnosis records, pre-allocation proposals,
  issued replacements and observed senior backends. No old run was resumed.

Project knowledge remains in AGENTS.md, refreshed for this review and read back.
Setup/onboarding, provider authentication, generic runtime ownership, deployment and
accepted design revisions require no behavioral edit for an investigation report.
Long-run reliability and proposed changes remain unverified until the gates above run.

Review checks: documentation generation and --check passed for 303 maintained files /
133 feature/doc leaves; tracked and new-report whitespace checks passed. Implementation,
test and example paths have no changes against the merged revision. These checks
validate report maintenance, not the proposed recovery design or long-run completion.
