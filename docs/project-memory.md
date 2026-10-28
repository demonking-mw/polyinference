# Project knowledge to retain

[Onboarding procedure](contributor-onboarding.md) · [Architecture](architecture.md) · [Rules](../AGENTS.md)

**Agents MUST add the rules and important information on this page to their
available memory, project rules or project-specific `content.md`, then verify and
report the saved location.** Humans should keep it as their contributor checklist.
Retain meaning and source pointers with your checkout/revision and review date;
refresh from current sources before work; exclude private/platform instructions.

## Purpose and ownership to remember

PolyInference pairs a portable LangGraph coding agent with an orchestration OS.
The local/cloud vision combines capable senior planning/review with local worker
inference and concurrent work. The current tester path can use Codex seniors and
remote Anthropic Haiku as a local-lane stand-in. Lane names do not prove physical
location; simulated overlap or TPS does not establish measured GPU performance.

The agent's [cloud recovery policy](guides/agent-reliability.md) gives eligible
clean local exceptions a finite coding takeover with original resources. Planner
guidance requires small behaviors and actual tool inventory; it adds no browser/MCP.
Changed recovery/program pins require fresh state and fresh live qualification.

The current implementation uses runtime `simple-os/5`, agent-8-evidence-recovery/state 2.7.
[Four scheduled repairs](../development-docs/four-repairs-implementation-2026-10-28.md)
keep source relevance, error retirement and semantic recovery in the agent. The OS
separates token/provenance, byte ceilings and output reservation with caller priorities;
provider counting is explicit opt-in. Native hidden context remains unmeasured.
The OS exposes optional retry_model; the agent selects Terra/high/seven through
default_retry_model. Caller input overrides OS defaults. Availability routing and
trusted same-thread continuation preserve original accounts and tool receipts;
unknown effects still block. Read [model fallback](guides/model-fallback.md).
Static data/allocation policy and uniform limits are enforced; paused residency
requires explicit safe hibernation/readmission. Bounded worker facts and error-aware
response repair retain original evidence and physical retry bounds. Pending linked
recovery retargets preserve their original root. Read the current
[implementation/verification record](../development-docs/reliability-implementation-2026-10-27.md)
and [qualification guide](guides/qualification.md); fixture/browser-runner checks
remain distinct from live model qualification and broad product completion.

| Owner | Decisions and guarantees to preserve |
| --- | --- |
| Agent/application | Task meaning, decomposition/dependencies, Git/repository policy, source reuse, canonical memory, response grammar, check purpose, acceptance and continuation. |
| OS/runtime | Generic process/effect execution, grants, admission, durable records/artifacts, replay, transport/accounting facts, optional workspace/context assistance and evidence-based recovery. |
| Provider/server | Provider protocol behavior and actual token/GPU scheduling. Adapters normalize provider facts; the OS does not invent hardware performance. |

Agents use replaceable [runtime ports](modules/sdk.md). A general OS process must
be able to finish without requiring Git, coding tasks, source edits or acceptance checks.
Optional OS packing/compaction transforms only permitted input; the application
owns canonical memory and semantics. Contributor setup belongs to developer tooling,
not every program hosted on the OS. Read the [boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md)
and [revisions/open gaps](../design-docs/simplified-os/DESIGN_REVISIONS.md) before changing these layers.

## Preservation rules to apply

- Preserve user constraints, effective grants, budgets, deadlines and mandatory
  context. Progress, recovery, role names and ignored files do not expand authority.
- Protect other contributors' edits and source. In-place coding uses the selected
  project and verified integration; private/interrupted work requires explicit
  scoped reuse. Retained source is not automatically accepted output.
- Keep execution, assessment, publication, senior acceptance and product completion
  distinct. A passing setup/build check or inherited commit proves neither a new
  contribution nor completion. The agent chooses meaningful final acceptance.
- Preserve immutable attempts, receipts, original inputs and diagnostics. A timeout,
  disconnect or lost acknowledgement does not prove remote termination. Do not
  blindly replay uncertain effects or execute incomplete model output.
- Explicit generation-only isolation may discard delivery while retaining physical
  holds; native/tool uncertainty remains blocking. OS-native and caller retries
  share root deadlines/allowances; local lane names prove neither location nor safety.
- Keep recovery bounded and accounted for. A retry is a new authorized intent;
  it cannot reset allowances, weaken grants or erase failures. Optional summaries
  are derived input views, not replacements for retained originals.
- Preserve verification-before-shell ordering and source-bound evidence when
  changing execution. Ignore rules and generated-output declarations cannot hide
  tracked/granted source edits. Keep credentials and transient state out of Git.
- Use current guides and accepted revisions. Preserve historical graphs, fix entries,
  stable IDs and provenance; mark corrections/supersession explicitly. Keep open
  gaps and future proposals visible until independently fixed and verified.

## Maintenance and actual automation

Read [fix history](../development-docs/FIXES.md) before work and use related entries
against recurrence. Every fix/feature includes affected module/setup/usage/settings/
design/issue docs, adjacent-doc review and a FIX entry in the same task: problem,
root cause/owner, concrete change/findings, design principle and actual checks/limits.
Investigation-only entries must explicitly say no implementation changed.
The [JSON tree](file-tree.json) has one primary guide per leaf, explicit ownership
and explained source responsibilities. Update it for new/moved files; run
`python scripts/project_docs.py` then `python scripts/project_docs.py --check`.
The [push/PR workflow](../.github/workflows/docs.yml) runs that check automatically
for coverage/ownership, paths, links/anchors, reachability and generated HTML.
It cannot write explanations or prove prose accuracy. [Testing](testing.md) lists
pytest, Ruff, packaging and documentation checks; configuration does not prove they
ran. Report only your actual checks and limits; label historical results, hypotheses,
provider readiness and hardware estimates. Follow [maintenance](maintenance.md).

## Memory and session boundaries

Use supported project-scoped storage; preserve existing rules and exclude secrets,
private prompts and transient run state. If adding a tracked memory file, give it
primary ownership/navigation under the normal maintenance contract. If persistence
is unavailable, report that limitation, retain session context and reload on restart.
Reading a page does not install hooks, schedule automation, configure another agent
or guarantee platform memory. Refresh changed rules and pass this route in authorized
handoffs. Maintain this checklist when rules, ownership, setup or automation change.
