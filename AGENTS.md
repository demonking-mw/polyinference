# Repository instructions for agents

These instructions apply throughout this repository. Follow any additional
instructions in the directory you work in as well.

## Before starting work

1. Read [the fix history](development-docs/FIXES.md) before investigating,
   editing, reviewing, or running repository checks. Read its maintenance rules
   and existing entries, including the design principles behind earlier fixes.
2. Identify entries related to the task. Use their evidence and regression
   coverage to avoid reintroducing a resolved problem or repeating a workaround.
3. Before changes involving the agent or OS, also read
   [the runtime/agent boundary guide](design-docs/simplified-os/RUNTIME_BOUNDARY.md).
   Coding workflow belongs to the coding agent. Keep OS interfaces usable by
   agents that need no Git, coding tasks, source edits, or acceptance checks.
4. Navigate with [the agent JSON tree](docs/file-tree.json) and read each affected
   feature's primary `doc`; [developer onboarding](dev-readme.md) links the wider
   setup, architecture and issue routes. Humans can use [the HTML tree](docs/file-tree.html).

For initial onboarding, a new session or lost context, follow the
[human/agent onboarding procedure](docs/contributor-onboarding.md) after reading
the fix history. Agents MUST add the [project knowledge](docs/project-memory.md)
to their available memory, project rules or project-specific `content.md`, verify
and report the saved location, and refresh it against current sources before work.
If persistence is unavailable, report session-only context and reload next session.
Report unread/inaccessible guidance before dependent work.

If you delegate repository work, include these reading and reporting requirements
in the handoff. Delegated agents must read the same documents before starting.

## Before finishing or handing off work

**A fix or feature is not complete until all related documentation is current.**
In the same task, update the affected module guides, setup/usage/configuration
references, design/issue docs and navigation. Review adjacent docs for impact;
state which needed no edit and why. Follow [documentation maintenance](docs/maintenance.md).
When files move or appear, update `docs/file-tree.json` (one primary doc per leaf),
run `python scripts/project_docs.py` and `python scripts/project_docs.py --check`.
Include documentation changes/review and checks in the final handoff. These are
the PolyInference project's persistent Codex instructions as well as repository rules.
Keep the onboarding procedure and project memory checklist current when rules,
design ownership, contributor setup or automation change.

Update [the fix history](development-docs/FIXES.md) in the same task. Record what
you changed or established; do not leave this to a later agent. Each independent
fix must explain:

- **Problem:** the observed symptom and trigger.
- **What was wrong:** the root cause and the layer that owns it.
- **How it was fixed:** the concrete change and affected paths.
- **Design principle enforced or reconstructed:** the general rule restored by
  the change, including the agent/OS boundary when relevant.
- **Verification:** checks actually run, their results, and material limits.

Use the entry template and stable IDs in the history. For a recurrence, link the
earlier entry and explain why the earlier fix or coverage did not prevent it.
Preserve previous entries; explicitly mark corrections or superseding decisions
instead of silently rewriting history. For investigation-only work, state that
no implementation changed and distinguish findings from unverified hypotheses.
Do not claim unrelated working-tree changes or historical test results as your
own work. Keep longer investigations in the issue documents and link them from
the history.


## Retained project knowledge

Reviewed 2026-10-23 for this PolyInference checkout; refresh from
[project memory](docs/project-memory.md), current FIXES and the boundary guide.
The agent owns task meaning, Git, canonical memory, grammar and acceptance. The
OS owns generic grants, processes, effects, admission, records and accounting;
providers own actual GPU/token scheduling. Non-coding programs need no Git/checks.
Preserve user work, immutable attempts, source authority, original budgets/deadlines
and historical evidence. Lost delivery proves no remote stop: optional raw-query
isolation retains physical holds and fences late output. Retries cannot reset
allowances. Report actual checks and limits; keep docs/navigation/history current.

## Integrated reliability branch (2026-10-26)

Retained project knowledge refreshed for codex/simple-os-v1, 2026-10-26: the
integrated kernel keeps generic runtime settings, registered capabilities, strict
unknown execution and attached repository safeguards. The agent owns module
contracts, source-backed semantic completion, bounded diagnosis and stagnation.
Response-validation retries must not multiply transport retry allowances. Linked
worker replacements inherit accounts, deadlines and grants. Use fresh integrated
program/state pins; preserve old runs on their original source. Current evidence:
[FIX-0127](development-docs/FIXES.md#fix-0127), worker recovery and progress guides.
This project-rule save was read back; it does not install runtime hooks.

Prepared retry bookkeeping never proves unknown execution stopped. Preserve actual
physical holds through restart; later unknown response repairs require explicit
reconciliation. Keep cache-named source visible to scope checks and preserve paged
read/cancellation compatibility while extending progress and recovery.

## Local live evidence (2026-10-26)

FIX-0128 records real Qwen/Strata 64K/batch-1 testing. Metadata capacity, conservative
prepared bytes and actual provider tokens differ; size mixed endpoints separately.
The test paused with stalled local work, not accepted gameplay. Preserve its states,
private deltas and unborn pi-dev source; no recovery allowance was reset. Exact
isolated exports remain uncommitted. See the investigation and local REPORT path.

## Documentation audit knowledge (2026-10-27)

Refreshed at 5fe92f3: use the focused check/reliability guides and the linked
documentation/run audit. Structural navigation checks do not prove prose accuracy
or validate all standalone HTML. Raw targets differ from hard ceilings; native
startup effort differs from the explicit turn field. Historical runs show improved
containment/recovery, not demonstrated broad product completion. Preserve original
run pins, private source, accounts and failed evidence; code follow-ups remain
unimplemented. This project-rule save was read back; it installs no automation.

Meeting review, 2026-10-27: FIX-0130 and the workflow readiness brief/analysis separate
execution success, valid grammar, evidence novelty and actual product completion.
Schema retries reuse the payload unless the owner offers a replacement; later
worker correction and semantic recovery are separate. Qualification, bounded worker
state and exceptional recovery routing remain proposals. Preserve all prior source,
run pins, accounts and evidence; this report changes no runtime or model settings.

Cloud-resolution audit, 2026-10-27 (FIX-0131): checking/exception/stagnation fixes
survived the merge. Four final stalls reached cloud senior review, but the senior
proposed local replacements; cloud-role assignments were not overwritten there.
Automatic stagnation bypasses the configured checker and parks for senior review.
Cloud review, read-only diagnosis and scoped specialist coding are distinct paths;
guaranteed cloud-first repair remains a proposed application policy.

Cloud coding recovery, 2026-10-27 (FIX-0132): the uncommitted application now gives
eligible clean local exceptions a finite specialist/cloud takeover, protected from
normal allocation and independent of ordinary semantic depth. Raw senior proposals
and effective adjustments remain separate. Original source, grants, shared budgets,
deadlines and unknown-effect guards remain authoritative. Planner guidance requests
one behavior/check per local task and pins actual tools: no browser/MCP/persistent
service API. Use fresh state; preserved live runs are unchanged. Fixture policy
checks do not establish live convergence. See the top current-iteration issue and
its linked implementation/verification record. This project-rule save was read back.

Reliability implementation planning, 2026-10-27 (FIX-0133): the scheduled report
separates agent task continuity/size/cloud coding/acceptance from OS enforcement,
provider setup and verification. Latest saved SQLite reproduces 179 local physical
attempts, 13 validation failures and 145 local-result context omissions. Cloud
takeover remains existing uncommitted work requiring fresh live qualification;
linked pending recovery and U01–U04 repairs remain proposals. Preserve historical
source/accounts/journals and all pre-existing edits. The new report changes no
runtime or model settings and authorizes no implementation or live runs. Refresh
against its source/status before starting any follow-up; this note installs no hooks.

Implementation authorized by the user on 2026-10-27: carry out the linked
reliability plan, preserving the pre-existing FIX-0132 tree and historical runs.
The report's analysis-only restriction describes its original task, not this new
authorization. Keep OS authority/admission separate from agent memory, planning,
recovery and acceptance. Baseline maintained-file hashes/archive are retained in
`/tmp/pi-reliability-implementation-start.*`; refresh the implementation record
and fix history as stages are verified. Fresh state is required for changed pins.

Current implementation, 2026-10-27 (FIX-0134–0146): runtime simple-os/3 validates
data/static allocation/uniform limits and explicit settled hibernation/readmission.
Agent-7/state 2.6 adds bounded worker facts/error-conditioned response repair;
pending linked recovery retargets preserve predecessor/root authority. Exact schema
and maintained documentation HTML checks accompany the new qualification harness.
Read the stage record for actual final test/live limits; no historical run is
migrated. The final offline gate and a narrow live browser gate passed: four ordinary
completions plus one settled resumed specialist worker completion preserved original
resources. Reporting-only corrections include direct native jobs without duplicate
retry counting. The actual OS tool environment is the browser preflight authority.
Byte-eviction counters replay idempotently within their source/generation view.
Endpoint probes declare protocol rather than URL-derived placement and retain run data constraints.
Broad product convergence remains unqualified; read the final suite/source evidence
in the stage record. This project-rule save was read back; it installs no hooks.

Final verification, 2026-10-27: full run 646 passed/five compatibility failures;
all 73 affected cases passed after fixes. The final 655 test IDs are covered across
those runs, not one all-green full rerun. Narrow live qualification passed four
ordinary Chromium workflows plus a settled cloud-worker resume. Both owned local
services drained/stopped; original 20 database/WAL hashes and project HEAD are
unchanged. Final source/profile artifacts and limitations are in the stage record.

Scheduled autonomous test preparation, 2026-10-27 (FIX-0147): the user authorized
fresh real-local Strata/Qwen IQ1_M 64K/batch-1 Minecraft testing at 22:30 Toronto,
without questions and with uncommitted morning delivery. Preparation/configuration
and retained context live under `../testing/minecraft-v1-live-2026-10-27-2230/`.
Reuse existing Codex login; preserve all prior edits, runs and unborn pi-dev source.
Keep task/Git/memory/acceptance in the agent, generic grants/effects/accounting in
the OS and actual GPU scheduling in the provider. Freeze current source and use
fresh state; isolated runtime history does not commit the user's branch. Preserve
original limits/deadlines and unknown-effect holds. Prepared files and installed
components are not evidence of a live run or accepted gameplay. Refresh current
sources, verify actual model/context/concurrency, report independent behavior
checks and update the final run record. No early inference was launched. This
retained note is separate from the explicit one-time app heartbeat.

Scheduled live result, 2026-10-28 (FIX-0148): actual Qwen IQ1_M/Strata 65536/one-slot
testing and four automatic cloud coding repairs produced checked increments. The
loading recovery paused on provider model capacity; no full objective was accepted.
The reviewed partial tree passes 44 host tests and real Chromium entry/pause/create/
save durability checks, but has no browser loading, gravity or jumping and leaks
text-field arrow input into movement. Its exact output is uncommitted on unborn
pi-dev; private loading failures remain separate. Preserve the 320 frozen source
pins, original root accounts/deadlines and all failed evidence. Owned services and
inhibitors ended; the heartbeat was deleted. Read the maintained live-result record
and local REPORT before follow-up. No framework implementation changed here. This
project-rule save was read back; it installs no runtime hook or new automation.

Failure isolation, 2026-10-28 (FIX-0149): distinguish terminal provider capacity
from earlier poor local convergence. Frozen evidence shows 37/280 raw generations
rejected, five subsequent local stalls and 214 context-omission calls. Conservative
49152-byte packing yielded at most 13839 actual prompt tokens on the real 65536
server. Clean model failures pause outside semantic cloud takeover; effectful native
jobs correctly require caller continuation. A corrected search can retain its old
path-specific error as an active working-state hint; diagnosis previews omitted
the failing entry/test and supplied no read capability. Browser checks were outside
the live feedback loop; kept tests do not establish physics or complete saved play.
Read the failure-isolation report for confidence, ownership and unimplemented repair
order. This investigation changes no implementation, pins, accounts or old evidence;
the original run remains stopped and uncommitted. This retained note was read back.

Task/context/worker-state follow-up, 2026-10-28 (FIX-0150): investigation only,
explicitly no fixes. All three read-only tasks needed missing entry/UI integrations;
existing core/repository APIs were insufficient and all workspace files stayed at
their starting trees. ContextService compares serialized UTF-8 bytes to 49152,
packing optional groups toward 48128; the 29491 compaction target was inactive.
This is not a fixed 31K-token limit. Current code exactly replays the saved receipt.
Stale search error hints reached seven inputs after a corrected call. A separate
current projection bug skips valid non-action replies with observation=None before
clearing protocol errors. These concern bounded worker_state, not canonical memory
corruption or a request for architectural expansion. FileRead supports limit and
max_bytes; the previous discrepancy claim was wrong. Canonical ordinary reads total
182/88 repeats ignoring injected generation; the prior 178/84 was a trailing
projection sample. Follow-up evidence preserves original records and all source;
no implementation/configuration/test changes or model calls occurred. Read back.

Authorized repair, 2026-10-28 (FIX-0151/0152): current runtime is simple-os/4,
agent-7/state 2.6; use fresh state. The OS exposes optional retry_model without a
model default; the coding agent chooses Terra/high via default_retry_model. Seven
subsequent fallback invocations is an OS default, overridable by agent input.
Latest policy: retry the failed logical request once on alternate, stay there for
X invocations, then probe configured primary/effort. Original admission/accounts/
deadlines and unknown-effect guards remain. Trusted same-thread native continuation
preserves tool receipts and scoped edits; never blindly replay effectful jobs.
Existing browser text-field isolation is repaired and real finite Chromium checks
retained; no gameplay feature was added. Convergence, context-unit sizing and
worker-state error-retirement changes remain plans. Read the current implementation
record for actual checks/limits; preserved runs/pins stay untouched and uncommitted.
This project-rule save was read back; it installs no automation or runtime hook.

Scheduled repairs, 2026-10-28 (FIX-0153–0156): current pins are simple-os/5,
agent-8-evidence-recovery/state 2.7; use fresh state. The agent owns source/failure
relevance, read-only frozen diagnosis, search novelty, resolved-error retirement
and clean unusable-output semantic recovery after configured bounded diagnosis.
The OS separates input tokens and
provenance, serialized byte ceilings, actual raw output reserve and whole-group
caller priorities. Provider counters are explicit same-origin opt-in; unavailable
routes retain conservative bounds and native hidden context stays unmeasured.
Original exceptions/trajectories, grants, root accounts/deadlines and uncertainty
remain authoritative. Existing Terra/high/seven routing is unchanged. Read the
[four-repair record](development-docs/four-repairs-implementation-2026-10-28.md)
for actual checks and limits; no live convergence or historical Resume is claimed.
The game and frozen run evidence remain untouched; this batch stays uncommitted.
The exact one-time development automation was deleted. This project-rule save
was read back; it installs no runtime hook or new automation.

Final four-repair verification, 2026-10-28: all 720 tests passed on the unchanged
full-suite-05 source; docs/schema/Ruff checks pass. Fifteen old evidence, 320 frozen
source and 14 game hashes, both HEADs and empty indexes are verified unchanged.
This new batch stays uncommitted. The implementation record discloses the legacy
historical graph-validator mismatch and two accidentally rejected native fixture
requests; no live convergence claim follows. Owned test processes and the exact
automation ended. This final project-rule save was read back.

The user subsequently authorized committing and pushing this batch on 2026-10-28.
Earlier uncommitted descriptions record its delivery state before that authorization.

Scheduled continuation, 2026-10-28 19:30 Toronto (FIX-0158): setup started on the
scheduled trigger and frozen CLI launched at 19:36:31. Evidence/retained knowledge
are in `../testing/minecraft-v1-live-2026-10-28-1930/`; read its content.md/REPORT.md
and the maintained 19:30 run record before follow-up. Current 329-file source,
14-file target baseline and existing pi-dev HEAD are preserved. Actual local
Qwen IQ1_M/Strata reports 65536 context and one sequence; its local Anthropic wire
protocol supports same-body token counting and makes no Anthropic/Haiku request.
The fresh run uses 8192 raw target/16384 hard ceiling and existing Terra/high/seven
fallback. Baseline 46 host/eight Chromium checks pass; final outcome is pending.
Keep task/Git/memory/acceptance in the agent, generic enforcement in the OS and GPU
scheduling in the provider. Preserve old evidence, source and original resources;
deliver user changes uncommitted. The retained note was read back and installs no
hook; the explicit in-chat heartbeat monitors the single already-started run.

Terminal continuation receipt, 2026-10-29 (FIX-0160): the single 19:30 test ended
paused at 06:46:33 Toronto after cloud recovery exhaustion; no product acceptance.
The exact reviewed partial tree is uncommitted on pi-dev. Final analysis/full
supported JSON and browser/private evidence are in
`/home/marven/Downloads/polyinference-minecraft-test-2026-10-28/` per the user's
latest delivery instruction. Read the maintained run record and Downloads analysis
before follow-up; preserve failed state and original limits, never blindly resume.
This saved note supersedes the historical pending status and installs no hook.


P0 implementation authorized 2026-10-29: current pins are simple-os/6,
agent-9-local-contracts/state 2.8. Every local development assignment requires
one production file with local_contract input/output shapes, functions/objects,
ownership/effects/errors and a focused observable check; only scoped tests/docs
accompany it. Irreducible cloud_only_reason work stays on cloud through allocation.
One system.local_token_limits pair drives raw local/API stand-in requests, context
and admission; Codex cloud inference has no OS per-call token cap even on the local
worker binding. Strata launch JSON can be synchronized before restart without
launching or reloading inference. Completed local overages retain full output as
budget violations; actual truncation/uncertainty guards stay intact. Matching
private passing/failing check receipts reach diagnosis/senior review without
becoming acceptance authority. Nested tuning is immutable; proxy/inspection paths
honor effective settings. Read development-docs/p0-repairs-2026-10-29.md for actual
verification and development-docs/current-iter-issues.md#p0-repairs-2026-10-29 for
remaining P1/P2 work. Preserve the starting uncommitted refactor and all frozen
runs/game source; use fresh state. This retained project-rule note installs no
runtime hook or automation. Verification is recorded with the implementation.

Final P0 verification, 2026-10-29: 759 offline full-regression cases passed without
failures/skips; all 24 P0 cases passed after the final startup-argument guard.
Host frontend tests passed 33 cases. Schema/docs/Ruff/whitespace and offline wheel
checks pass; all 77 packaged source assets match the final pin. Frozen framework
329, baseline game 14 and delivered game 14 hashes are unchanged. Source remains
uncommitted on codex/simple-os-v1, with fresh state required. The current-version
list retains all six P1/P2 follow-ups; fixture success is not live qualification.
This project-rule save was read back and installs no hook or automation.


Machine UI defaults, 2026-11-02 (FIX-0168): plain UI launches now read optional
XDG config/polyinference/ui-defaults.json; only local endpoint/token/worker/Strata
preferences are accepted. The machine selects real Qwen3.8 Flash-Next Coder IQ1_M,
49152 input + 16384 output = 65536 context, one worker and one Strata slot/group.
Explicit --config bypasses preferences; Resume retains saved pins and resources.
Explicit --sim-batch selects Haiku for a declared local Anthropic-compatible server.
Application preferences never change generic OS defaults or auto-launch providers.
Preserve existing source edits and all historical runs. Refresh against the settings
module/configuration guide and FIX-0168. This note installs no hook or automation.


Automatic local UI bootstrap, 2026-11-02 (FIX-0169), supersedes FIX-0168's manual
startup limitation: machine local_strata_profile=polyinference-default opts into
starting a stopped Strata profile and awaiting generation readiness before UI
restoration/HTTP serving. Matching ready engines are reused; live model/context/
slots are verified, failures surfaced, and no existing engine is restarted or
stopped. Explicit remote simulation skips bootstrap. UI exit leaves the engine
running; later UI launches start it again after shutdown. Agent/application owns
this deployment preference; generic OS defaults and saved run pins remain intact.
Refresh docs/guides/launching.md and agent/local_provider.py. No boot automation.


Native setup investigation, 2026-11-02 (FIX-0170): run 20739a315d3f paused before
local inference, 180.041963 seconds after cloud setup activation. Current UI cloud
native jobs still use 180 seconds for the whole tool-using call; local Strata's
1800-second setting is separate. FIX-0068's missing interrupt terminal drain and
conflated timeout/cancellation cause remain unimplemented. Nineteen host callbacks
settled, twelve scaffold files stayed private; no accepted contribution or checks.
Read current-iter-issues.md#run-20739a315d3f before recovery. Preserve saved pins,
resources and source; no blind Resume/replay or inference was performed. This
investigation changes documentation only and installs no runtime hook.


Cloud agent timeout policy, 2026-11-02 (FIX-0171): canonical OS RuntimeConfig now
exposes strict boolean cloud_agent_timeout_interrupt=false through system and
AgentConfig. For physically cloud-hosted AgentJob calls, endpoint.timeout_seconds
warns once and preserves the same job, connection, holds and callbacks; true
interrupts as before. Direct stdio and proxy transport follow this choice; raw
queries/local agents and original process/root deadlines/cancellation remain hard.
Warnings persist under runtime/warning/cloud-agent-timeout/. Use fresh state;
run 20739a315d3f and all historical resources/private source remain untouched.
Terminal acknowledgement draining and precise cancellation cause remain separate
follow-ups. Read the OS tuning guide and FIX-0171 for actual test results. This
retained note installs no runtime hook or automation.


Coding UI timing follow-up, 2026-11-02 (FIX-0172): the native cloud preset and
Codex/mixed examples now use 1800 seconds. Coding defaults, endpoint profiles and
simulation do not override cloud_agent_timeout_interrupt to true; inherit the OS
false default. Explicit user configurations remain authoritative. Raw Haiku and
generic Endpoint timeout defaults are unchanged; saved runs are not rewritten.


Provider lifecycle/token work, 2026-11-02: refreshed project-memory.md, current
settings/UI guides and related FIX-0154/0167–0172 against checkout 8b527c9 and
the existing uncommitted tree. Keep task/Git/memory/acceptance in the agent,
generic enforcement in the OS and provider scheduling/lifecycle in Strata.
Preserve historical runs, original accounts/pins, private game source and all
pre-existing edits; fresh launches alone take new machine preferences.
This retained project-rule note installs no runtime hook or automation.


128K coding preference and owned provider cleanup, 2026-11-02 (FIX-0173/0174):
this machine now selects 114688 input + 16384 output = 131072 context, one worker
and one Strata slot/group; output includes reasoning. Generic defaults and old
saved runs keep their own pair. Supersedes FIX-0169's UI leave-running policy:
new Strata runtimes receive --die-with-pid for the UI process and a 10-second drain
budget. UI normal/signal exit and startup failures close only captured owners/
instances. SIGKILL relies on Strata's identity-aware process-death watcher; reused
ready/starting runtimes are never adopted. Refresh agent/local_provider.py and the
launch guide; this retained knowledge installs no extra automation.

Senior review allowances, 2026-11-04 (FIX-0175), refreshed against checkout 8b527c9 and the existing
uncommitted tree: new AgentConfig instances default to 16 source ranges per senior invocation, still
eight per proposal and 4000 bytes per range. Planner messages expose current read/correction accounting,
planning bounds and process resources; native cloud per-call tokens remain provider-owned. Explicit
lower settings and historical run pins remain authoritative. Preserve original accounts/deadlines,
private game source and unrelated edits. Agent owns review meaning/grammar; OS owns generic execution
and accounting; provider owns token/GPU scheduling. Read project-memory.md and the FIX-0175 issue record
before follow-up. Offline prompt fixtures do not establish live convergence. This note installs no hook.

Prompting proposal, 2026-11-04 (FIX-0176): PROMPT-01 is the first current-iteration
implementation issue and links development-docs/agent-prompting-proposal-2026-11-04.md.
It proposes milestone/status/work organization/task distribution/verification,
one-file edits or one test/inquiry per local assignment, preserved repair context
and fewer redundant agent checks. It is unimplemented; current authorization is
documentation only. Core work belongs to the agent using existing OS actions;
potential OS changes are explicitly deferred. Preserve original source, grants,
accounts, deadlines and old runs. Read the proposal/status before future work.

Prompting audit, 2026-11-04 (FIX-0177): read the authoritative corrected plan in
development-docs/agent-prompting-audit-2026-11-04.md before implementing PROMPT-01.
It supersedes the earlier proposal's contract relaxation, mandatory-phase skipping,
receipt-as-acceptance, partial-read and trivial test-only-task shortcuts. Stage A
improves prompts/repair with existing canonical contracts, phases and evidence
requirements. Stage B defines honest testing results; Stage C isolates any later
optimization. All remain unimplemented. Preserve FIX-0023/0025, 0086/0088/0089,
0136/0137 and 0162/0164/0166 semantics and original accounts/source. No OS change
is required for Stage A; generic protections and current documentation still apply.
