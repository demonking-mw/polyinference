# Prompting redesign scope

<a id="prompt-01"></a>
## PROMPT-01 — Simplify agent prompting and milestone-driven sprint planning

**Priority: first implementation item. Status: open; test-only task support implemented separately.**
Implement **Stage A** of the audited analysis and corrected plan (`docs/temporary/proposals/2026-11-04-agent-prompting-audit.md`).
The earlier proposal (`docs/temporary/proposals/2026-11-04-agent-prompting-proposal.md`) is retained with an
audit correction notice. Its workflow shortcuts must not be implemented literally.
The original audit/documentation request did not authorize implementation. The later user request
authorized the test-only exception below; the broader prompting redesign remains future work.

**Implemented 2026-11-04, `development-docs/FIXES.md#fix-0178`:** `kind: test` runs existing
configured tests with no implementation file, local contract, write target or result path.
The agent records tested revision/observations/check receipts, without a source commit;
successful kept results release dependents, while failed/uncertain tests reach review.
Test authoring and product repairs remain edit tasks. This is the bounded testing part
of Stage B, not general inspection support or completion of Stage A/C. No runtime
implementation changed; the shared TaskSpec envelope now permits empty change scope.
Basic offline checks are recorded in FIX-0178; live testing is left to the user.

### Required outcome

The cloud sprint manager identifies the next milestone and verified status,
organizes concrete files/responsibilities/APIs, test scenarios, prerequisites and
integration ownership, then distributes single-purpose tasks and chooses useful
verification. Local writing tasks target one file. Preserve canonical local/shared
contracts, source closure, accepted dependencies, pending work and protected cloud
placement. Compact their presentation rather than deleting their semantics.

Fix the recorded prompt/response disagreement and repair-context loss first:
state the actual read allowance, define `focused_check` as a selected check ID,
retain the rejected answer and active constraints, and issue the correct current
phase request. Keep the final host message after history. Use existing registered
protocols and action contracts; preserve required pins and original resources.

Reduce duplicate instructions, repeated facts and discretionary manual rechecks.
Do not remove mandatory post-merge reconciliation, required assigned checks,
assessment, publication guards or independent final acceptance in this stage.
Matching diagnostic receipts do not automatically authorize skipping those steps.
AI retains engineering judgment within the declared task and evidence contract.

**Remaining bounded work:** Stage B's testing path is implemented as described above;
general inspection remains a separate proposal. Stage C considers specific evidence-backed reductions only after
their validity and publication implications are defined. Neither is a prerequisite
for prompt/repair correction, nor a license to bypass current completion guards.

### Ownership and implementation scope

**Agent-level work. No OS change is required or included in the core scope.**
Use existing registered protocols, granted actions, repair callbacks, records and
artifacts. Prefer recording rejected validator input in agent-owned state over
depending on private OS attempt-record layouts. The audit names potential OS
changes and defers them. Any newly
necessary OS change must state the missing public capability, why existing ports
cannot express it, and the smallest generic fix before proceeding.

Retain OS authority, typed action arguments, execution certainty, replay and
resource enforcement. Preserve old runs, original accounts/deadlines, private
source and unrelated edits. Use fresh program/state pins for changed contracts.

### Completion evidence

- A normal manager result includes milestone, status, concrete work organization,
  derived tasks and verification while retaining the pinned execution contracts.
- The recorded read/focused-check corrections retain the rejected answer and
  active constraints and avoid the observed restart of the same failure.
- Native/raw actions match the existing OS contract and final-message ordering.
  Current mandatory phases, required checks and final acceptance still work.
- Discretionary repeated commands are reduced without promoting worker/private
  evidence into independent acceptance or declaring unrun checks passed.
- Test-only support now has its own result/readiness path; retain the no-dummy-file,
  no-fabricated-commit and no-successful-code-report guarantees in follow-up work.
- Run one focused regression set for the changed boundaries. A short fresh live
  trial, only when separately authorized, should report useful completion,
  avoidable pauses, model/check counts and input size. Do not add a prompt-audit
  framework or extra critics as prerequisites.

The audit explains which suggestions would undo past fixes, why the immediate
prompt changes still hold, and the corrected staged plan. See `development-docs/FIXES.md#fix-0177`.
