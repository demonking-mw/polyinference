# Local task granularity and cloud recovery — 27 October 2026

[Top current-version issue](current-iter-issues.md#local-task-cloud-recovery) ·
[Workflow analysis](workflow-readiness-analysis-2026-10-27.md)

Follow-up: the [authorized implementation and qualification record](reliability-implementation-2026-10-27.md)
supersedes the pending status/limitations below. This document retains the original
FIX-0132 implementation snapshot and its historical test results.

Status: implemented and fixture-verified; fresh live qualification pending. Changes remain uncommitted;
historical runs retain their original source, configuration and resource accounts.

## User judgments and required behavior

1. Local tasks remain too coarse. Movement/input, collision, persistence and save
   migration should be separate testable tasks, with explicit dependencies.
2. A retry may use the cloud senior worker more often than ordinary task allocation.
   The normal development ratio must not demote a justified recovery assignment.
3. Repeated local failure must eventually transfer implementation ownership to a
   cloud worker, rather than repeat local planning until the queue stops.
4. Recoverable stalls need a less restrictive, bounded path to cloud repair.
   Review alone is insufficient. Actual OS capabilities must be in planner inputs
   and system instructions: no assumed browser, MCP, unrestricted native tools or
   persistent service API.

## Evidence combined with those judgments

The latest final attempt reached cloud review for all four stalls. The senior
proposed local physics/menu replacements; both stalled again. Physics retained no
net source change and menu retained the same broken delta. Their shared accounts
had used 43/256 and 87/256 calls, but the one-replacement limit prevented another
recovery. No runnable queued task remained; the controller paused with exit 2.

The checking agent was configured for cloud but automatic stagnation bypassed its
node. The normal task-count allocator offers no guaranteed cloud repair. These
paths survived the merge; the issue is productive recovery and task sizing.

## Implementation scope

- Keep normal local work narrowly scoped: one observable behavior and its focused
  check. Treat migration and application integration as separate planned work.
- Give eligible, confirmed-stopped local failures a bounded cloud-specialist
  takeover with retained source and concrete failure evidence. Preserve an
  explicit cloud recovery through ordinary allocation; expose availability and
  reasons when recovery is impossible.
- Avoid an empty/no-op senior plan abandoning eligible cloud recovery. Keep
  pending consumers consistent when replacing their failed provider.
- Permit a dedicated cloud opportunity when ordinary semantic depth is exhausted,
  within the original call/token/operation/deadline envelope. Do not refill it.
- Pin the actual available tools and limitations in planning/review inputs and
  prompts, distinguishing source read requests from worker command capabilities.

This is agent/application policy. The generic OS still owns grants, settlement,
uncertainty, resource accounts and atomic evidence. Cloud is not permission to
widen writes, retry unknown effects, bypass exhausted physical resources, ignore
provider restrictions or claim browser verification that did not occur. Explicit
cancellation and already-published work must not become new recovery attempts.

## Required verification and completion limits

Regression coverage must demonstrate actual cloud assignment after local stall,
including a senior proposal that repeats local work or defers with eligible
resources; quota immunity; dependent rewiring; preserved lineage/delta/grants and
deadlines; finite cloud recovery; and rejection of unknown/exhausted/unsupported
cases. Prompt tests must reflect the actual shell/check/file capability inventory
and independent source review, without advertising browser/MCP support.

Update owning guides, configuration references, fix history and navigation. Run
focused recovery/planning/progress checks, appropriate integration checks and docs
generation/validation. Fixture success is not live-model reliability: a fresh,
separately recorded end-to-end qualification remains required. Do not resume or
rewrite the preserved Minecraft runs to test new program behavior.

## Implemented policy and remaining limits

A retry repairs a known failed request or starts explicitly changed work; it is
not proof of task progress. A stall is sustained lack of new tree identity, new
read coverage or new check evidence: warning after 8 settled decisions, escalation
after 12 by default. Repeated narration, identical checks and overlapping reads
do not count. Novel edits can still be wrong; acceptance remains separate.
Active/unknown effects are settled by the OS, not declared stopped by the planner.

The default `max_cloud_recoveries: 1` adds one cloud coding opportunity per clean
local lineage, independently of ordinary replacement depth. Eligible local
retry/defer/stop/omitted proposals become actual specialist assignments before
validation. A senior's stop is a planning decision; explicit operator cancellation
still blocks handoff. Normal quota cannot rewrite validated recovery roles.
Original/effective proposals and adjustments remain separately reviewable.

Automatic takeover retains a compatible source delta or reconstructs from the
current base if that delta conflicts. Pending ordinary consumers are cloned and
rewired transitively without changing started contracts. Already-linked pending
recovery consumers cannot be cloned automatically: retargeting that reservation's
lineage remains unsupported and can still pause planning. The policy rejects an
unsafe clone rather than creating a fresh account. One replacement per
exception remains the supported shape; automatic multi-source task splitting is
not implemented. Granularity is explicit planner guidance, not a heuristic word
count claiming to prove semantic task size.

The cloud worker gets predecessor failure/phase/source context and follows the
same checks, integration, reconciliation, assessment and publication gates. No
new OS capabilities were added. Planner task summaries retain full assignments,
constraints, lineage and record/spec refs while avoiding repeated dispatch/base/
workspace envelopes; canonical records and source pins remain unchanged. This
keeps the added capability/recovery metadata within default review fixtures.
Input-context admission, authentication/provider
outages, depleted original accounts/deadlines, unknown effects and genuinely
missing verification infrastructure can still stop a run. A stronger model cannot
manufacture browser evidence. Bounded cloud recovery can also fail; it cannot
silently bounce back to local work or renew its own allowance.

## Verification recorded for this change

All model responses in these checks are fixtures; test repositories are disposable.
Actual dispatch to the configured cloud lane, both isolated and in-place source
handoff, original account/deadline, failure context, transitive queue changes,
quota immunity and negative eligibility boundaries were exercised.

Reproduce the groups from the repository with `.venv-linux/bin/python -m pytest`.
Run them sequentially on this host: they contend for the installation-wide shell lock.

```bash
python -m pytest -q tests/test_cloud_recovery.py tests/test_exception_recovery.py tests/test_progress.py tests/test_check_diagnosis.py tests/test_validation_feedback.py
python -m pytest -q tests/test_module_planning.py tests/test_agent.py tests/test_setup_tools.py tests/test_semantic_review.py
python -m pytest -q tests/test_agent_transitions.py tests/test_native_worker.py tests/test_user_briefs.py tests/test_branch_integration.py tests/test_in_place_repository.py tests/test_context_safety.py tests/test_resume.py tests/test_project_docs.py
```

| Check | Observed result |
| --- | --- |
| Recovery/progress/diagnosis/feedback group | 57 passed. |
| Planning/setup/semantic-review group | 49 passed; two UI poll timeouts under parallel host load. Both later completed in their journals. |
| Native/in-place/context/resume/docs group | 116 passed; one 30-second serial-policy timeout under parallel host load and one known baseline failure below. |
| Three deadline-sensitive cases rerun sequentially | 3 passed in 36.86 seconds, without changing their timeouts. |
| Added same-backend role-rename guard and recovery validation | 2 passed, including one new case. |
| Final allocation/recovery checks | 6 passed; the duplicate ten-task run was interrupted because the main planning group already ran it successfully. |
| Latest result per selected case | 227 passed, 1 unchanged baseline failure across 228 distinct cases; combined runs, not one full-suite pass. |
| Static/package/docs | Ruff and whitespace checks passed; wheel built and contains the new module/config; docs generation/check passed for 306 files / 134 leaves. |

The remaining failure is
`test_generic_resume_retains_uncertainty_when_provider_lookup_times_out`:
its original 100 ms allowance expires before lookup and the diagnostic differs
from the fixture expectation. It is already reproduced on the untouched baseline
in the [integration audit](branch-integration-audit-2026-10-26.md#verification-record).
No runtime deadline or unknown-effect rule was relaxed for this change.

Early verification exposed review-context regressions from expanded instructions;
prompt compression and contract/lineage views fixed those cases without increasing
the default limit. Parallel host suites also contended for the installation-wide
shell lock; sequential reruns distinguish test polling limits from actual stalls.
The first offline package attempt lacked setuptools; a temporary isolated build
toolchain produced the checked wheel without changing the active virtualenv.

No live inference, preserved-run resume, new Minecraft acceptance or full-suite
green result is claimed. The P1 stays visible for fresh live qualification and the
documented unsupported pending-recovery handoff. Project knowledge was saved and
read back in AGENTS.md and docs/project-memory.md. Setup/authentication, endpoint
retry ownership, generic context/uncertainty and the runtime boundary were reviewed;
their enforcement contracts needed no change.
