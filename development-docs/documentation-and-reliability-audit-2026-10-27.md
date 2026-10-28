# Documentation and workflow reliability review — 27 October 2026

[Development records](README.md) · [Investigations](investigations.md) · [FIX-0129](FIXES.md#fix-0129)

**Assessment:** documentation structure follows the intended tree, but content
maintenance had drifted after the reliability merge. The workflow is improving in
observability, source preservation and bounded recovery. The retained broad game
runs still do not demonstrate reliable unattended product delivery. No application,
runtime, test or configuration implementation was changed by this audit.

## Scope and documentation findings

Reviewed the main `polyinference` checkout at `5fe92f3`, including its existing
uncommitted documentation. The separate profiles worktree was not modified.
Checked the entire maintained inventory/navigation, current module/usage guides,
settings schemas and relevant execution paths; read the complete main fix ledger
and compared retained investigation/live-test reports. Historical specifications
were checked through their current-status routes, not exhaustively revalidated.
This is a source/report audit, not a fresh live run or a controlled benchmark.
Two separate workflow-readiness reports appeared during this audit: their
[brief](workflow-readiness-brief-2026-10-27.md) and
[analysis](workflow-readiness-analysis-2026-10-27.md) are preserved and registered
in the tree. Their additional record probes are separate work, not this audit's checks.

| Rule | Finding and correction |
| --- | --- |
| Tree navigation | Baseline check passed: 298 files / 128 leaves, one primary doc per leaf. The human module index nevertheless omitted recovery/progress and several merged source files; corrected it and registered new focused guides/report in JSON. |
| Sufficient, correct feature docs | Added nested reliability defaults/bounds, module/interface and exact-tree completion contracts, response-repair records and replacement rules. Corrected the actual review-read unit: total ranges, not rounds. |
| Prose agrees with code | Corrected the 4096-token raw request versus 32000 hard ceiling, native turn effort, resumed-run capacity overlays, exception-review behavior and integrated-state compatibility qualifications. |
| Concision | Split configuration/check/reliability procedures; shortened UI/tester explanations; merged duplicated worker/retry source descriptions. Kept historical evidence and stable FIX entries. |
| Fixes remain discoverable | Main entries retain causes, ownership, principles and actual verification. Added this correction as FIX-0129; earlier FIX-0080/0094/0098 already warned that structural checks cannot establish semantic completeness. |
| Current verification is distinguishable | Testing/setup routes now lead to the integrated-tree and real local records, including their failures. A prior small Codex success or passing unit suite is not current broad product acceptance. |

The checker validates Markdown plus generated tree HTML; it does not inspect
every standalone HTML body or HTML anchor, enforce useful source explanations,
or enforce prose length. The maintenance/tooling guides now state those limits.
Separate HTML inspection found moved-reference links in an archived graph; those
documentation links were repaired without changing graph layout or execution rules.
The editor template resolves links from its generated destination; upstream source
links and the UI's HTTP asset route are separate boundaries, not broken doc links.

## What the retained runs show

The following rows summarize historical evidence; none of these workloads was
rerun. The objectives, baselines, providers and source revisions differ.

| Evidence | Result | What it establishes |
| --- | --- | --- |
| Early incidents, [v10](run-d434799ad8e4-analysis.md), [v11](run-2de3d5c5ab9b-analysis.md), [v12](run-eb66fc618354-analysis.md) | Empty completed output, local serialized-input overflow, then uncertain native inventory work. V12 integrated terrain/movement; inventory remained private. | Infrastructure and context framing repeatedly interrupted otherwise useful work. Later fixes added retained failure facts, accurate preparation and guarded recovery; these do not retroactively complete old runs. |
| [Two-slot Haiku v13](run-a1859f8644a5-analysis.md), 20 October | 396 submissions; four successful reports including setup, seven uncertain assessments; stopped at sprint 9 without final acceptance. | Concurrency worked: 230.444 seconds of two-slot occupancy, no observed OS deadlock/capacity leak. Missing shared test prerequisites and ineffective private-source reuse consumed the plan; more slots did not solve readiness. |
| [Haiku v14](run-7086c575ef94-analysis.md), 21 October | Corrected foundation grants and reused eleven retained source paths, then paused on one submitted request at 180.005 seconds. | Explicit handoff improved; one unknown transport outcome could still stop the run. The old export cannot prove timeout versus disconnect/cancellation. Later SSE/lifecycle work addresses that mechanism, not proof that every outage is recoverable. |
| Local Qwen test, 25 October, frozen `cd227c3` | One worker used all 256 calls on an unfinished documentation audit; none of ten development tasks completed. 20 response-validation failures and three endpoint errors; no uncertain effects. | The main bottleneck was task convergence, not missing authentication or an observed GPU-memory failure. The first prerequisite task blocked the remaining plan; repeated passing core checks did not produce useful product evidence. |
| [Local Qwen test](local-strata-live-test-2026-10-26.md), 26 October, frozen `5fe92f3` | Three distinct configuration attempts; 179 physical local generations, 13 validation failures. Native linked recovery delivered storage; 25 exported-tree tests passed. Locomotion/menu recovery stalled; browser remained unplayable. Zero uncertain effects. | Stagnation was detected and returned to senior review; bounded recovery produced a useful partial result. Native packet sizing still required two fresh configurations. Local replacements still failed to converge, and storage tests did not cover browser integration. |

The 25/26 October tests used the requested IQ1_M model at 64K/batch 1 and
high/4096 thinking. The 26 October evidence directory is named
`minecraft-v1-live-2026-10-27-0200`, but execution occurred on **26 October**.
The later test reused a different partial baseline and changed framework/settings;
179 versus 256 generations is not a like-for-like productivity comparison.

Machine-local evidence, retained outside the source inventory:

- `testing/minecraft-v1-run/README.md` and `UNFIXED-ISSUES-ANALYSIS.md`: earlier local failures and proposed owner-specific repairs; several were subsequently implemented. Do not treat that old list as today's backlog.
- `testing/minecraft-v1-live-2026-10-25-0300/REPORT.md`: timing, 256-call audit, usage and failed product checks.
- `testing/minecraft-v1-live-2026-10-27-0200/REPORT.md`: three attempts, recovery lineage, independent 25-test result and actual browser failure.

## Trend and recurring failure patterns

**Smoother:** work and failures are more attributable; source reuse is explicit,
unknown execution is preserved honestly, diagnosis/review have real evidence,
and stalled workers can yield to bounded senior recovery. The latest storage
milestone is evidence of that path working. Old false tool-feedback, sampling and
review-packet issues have source fixes; recurrence is not proof those fixes vanished.

**Still unresolved:** workers repeatedly read/check unchanged material, lose the
thread of long tasks, emit invalid actions or stale create/write digests, and fail
to finish within useful evidence boundaries. In the latest run 145 receipts omitted
optional history; omission and stalls coincide, but causation is not isolated.
Increasing thinking/call budgets did not establish long-workflow reliability.

**Planning/integration recurs:** runner dependencies, exact required test paths,
module migration and available read context can each make an apparently scoped task
non-completable. Versioned contracts improve the representation; they do not prove
the plan implements those contracts. Recent delivered rendering still uses x/z
against an x/y core, and storage lacks browser wiring. The game remains unfinished.

**Verification quality remains pivotal:** successful effects, valid JSON, passing
task tests, published increments, senior keep and full objective acceptance are
different measures. The latest run correctly withheld completion, but useful
throughput remains low. Earlier Haiku runs integrated more scaffold/features than
recent local runs; provider/model and baseline differences prevent calling that
a measured regression in the framework.

**Management judgment:** containment and recovery are improving; end-to-end
reliability is not yet demonstrated. There is no comparable time series proving
overall acceleration or deterioration. Qualify local workers on short, measurable
tasks and use the same source/model/settings for comparisons before scaling scope.

## Code and policy follow-ups for the owner

These are recommendations for separately authorized work, not implemented fixes.

| Priority | Finding / owner | Concrete next step |
| --- | --- | --- |
| P1 | Agent convergence and recovery routing | Compare short coding tasks with observable browser/integration milestones. Track accepted nonempty contributions, recovery yield, idle decisions and completion per physical call. Consider bounded task-state/digest consolidation and an explicit recovery-role policy; the 10% quota can keep replacements local even after repeated local stalls. These are hypotheses/policy choices, not an isolated proven model or context root cause. |
| P2 | Native effort configuration conflict | [UI settings](../src/polyinference/agent/system_settings.py) start Codex with low effort, while [turn construction](../src/polyinference/runtime/codex.py) sends Endpoint.reasoning_effort, default medium. Pick one explicit source of truth and verify the captured turn. Docs now describe medium being sent; no provider-effort experiment was run. |
| P2 | Documentation validation coverage | Extend [project_docs.py](../scripts/project_docs.py) to check maintained rendered HTML/HTML anchors with explicit template/upstream boundaries. Add a schema/default coverage check and a length advisory; keep semantic review human/agent-owned. The existing green check missed the archived broken links and stale prose. |
| P2 | Legacy live smoke assertion | [smoke_os_codex.py](../scripts/smoke_os_codex.py) defaults to in-place AgentConfig but asserts the source greeting remains unchanged. Pin isolated mode for that test or assert verified in-place integration. Its [guide](../docs/modules/live-smoke.md) already flags the limit; do not treat the current script as valid in-place acceptance. |
| Existing, separate | Open runtime guarantees and baseline failures | [U01–U04](../design-docs/simplified-os/DESIGN_REVISIONS.md#open-implementation-gaps) remain declared gaps in data-policy enforcement, allocation rejection, process-limit authority and paused residency. The [integration record](branch-integration-audit-2026-10-26.md#verification-record) retains five baseline test failures. This audit does not reclassify them as approved design or newly fixed behavior. |

## Verification and limits

Documentation generation/check passed for 303 files / 133 leaves, and all 20
documentation-tool regressions passed. All five example configs validated; actual
UI effort/target and nested schema defaults/bounds were inspected offline.
Separate inspection checked 548 rendered-document links/anchors. Additional checks
covered guide lengths, source references, graph layout/script preservation,
all 121 earlier main FIX entries and task patch whitespace. All 126 protected
implementation/test/configuration files match audit-start hashes. No live provider, saved-run
resume, game repair, full runtime suite, commit or push was performed. Historical
runtime/game test counts above belong to their original reports.

Adjacent provider/authentication, exports/archive, workspace/source, context,
runtime boundary and accepted-revision guides were reviewed: their ownership,
credentials, evidence preservation and uncertainty rules still apply. Historical
designs and the original run reports retain their provenance. Project knowledge
was refreshed and read back in AGENTS.md; it does not install runtime automation.
