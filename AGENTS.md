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
