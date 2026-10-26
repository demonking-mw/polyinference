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
