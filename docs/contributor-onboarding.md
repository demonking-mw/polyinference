# Onboard a human or development agent

[Project](../README.md) · [Developer guide](../dev-readme.md) · [Project memory](project-memory.md)

Use this procedure before contributing, including when an AI is asked to read the
project docs and onboard itself. It establishes shared knowledge and a repeatable
work routine. These are contributor instructions; they do not add requirements
to programs running on the PolyInference OS.

## Human setup checklist

- Give collaborators access to the current checkout and its documentation. Start
  at README; use the [human tree](file-tree.html) or [agent tree](file-tree.json).
- Follow [setup](../setup.md) on Linux, WSL or macOS. Install the test extra using
  [testing](testing.md). Configure credentials only when needed; offline checks
  need no live provider. Keep secrets outside source and agent memory.
- Open the assistant in this checkout and confirm it receives [AGENTS.md](../AGENTS.md).
  For another harness or a ChatGPT project, explicitly supply the instructions and
  readable repository/docs access or current copies. A path/link alone does not
  establish access. Use its project-instruction entry point to require this
  procedure at session startup and before project work.
- Enable an available project-scoped memory/rules mechanism or project-specific
  `content.md`. Ask the agent to add the knowledge below and verify the save.
  If persistence is unavailable, supply this route each session.
- Use the prompt below and review the onboarding receipt. Resolve missing access
  before work depends on unread guidance; do not assume every AI auto-loads it.

## Required reading and agent setup

1. Read [AGENTS.md](../AGENTS.md) and the complete [fix history](../development-docs/FIXES.md),
   including maintenance rules, prior decisions, supersession and verification limits.
   Read long output in chunks; a truncated response is not a completed reading.
2. Read [architecture](architecture.md), the [current design route](../design-docs/README.md),
   [runtime/agent boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md) and
   [accepted revisions/open gaps](../design-docs/simplified-os/DESIGN_REVISIONS.md).
   Follow the route to the agent and OS primary designs; distinguish current rules
   from historical graphs and proposed interfaces.
3. Read [developer onboarding](../dev-readme.md), [maintenance](maintenance.md),
   [testing](testing.md) and the [project memory checklist](project-memory.md).
   The [field guide](onboarding.html) adds illustrated background and the lecture.
4. Walk the JSON tree to understand ownership. For the assigned area, read each
   primary `doc`, related fixes and linked usage/settings/design guides. Review
   [current work](../development-docs/current-iter-issues.md) and
   [future work](../development-docs/next-iteration.md); a proposal is not implementation.
   For reliability work, read the [current stage record](../development-docs/reliability-implementation-2026-10-27.md)
   and [qualification procedure](guides/qualification.md). Keep fixture, browser
   runner and actual live-model results separate; use fresh state for changed pins.
5. **If you are an agent, you MUST add this project's rules, important information
   and design/preservation principles to your available memory, project rules or
   project-specific `content.md`.** Use the [memory checklist](project-memory.md),
   retaining its meaning and source pointers with checkout/revision and review date.
   Preserve existing rules, verify the save and report its location. If persistent
   storage is unavailable, explicitly report session-only context and reload next
   session; never claim unavailable platform memory or an unverified save.

## Every request, restart and handoff

Before project work, refresh instructions/history and retained knowledge against
current sources; read affected feature guides and newer decisions. Inspect the
working tree and preserve other people's edits, staged work and active operations.
Choose checks appropriate to the task. Remembered facts point to current evidence;
resolve design contradictions explicitly instead of accepting bugs as policy.
A new request does not authorize an unrelated backlog or saved-run task.

Before finishing, update affected docs, navigation and FIXES in the same task;
run required checks and report results/limits, adjacent-doc review and memory status.
For authorized delegation, pass this route, scope, constraints and preservation
requirements; the receiver must read the same guidance before work. After context
loss, repeat setup before dependent work. Follow [maintenance](maintenance.md).

## Reusable onboarding request

> Read README.md and follow docs/contributor-onboarding.md through the project tree.
> Onboard with the rules, current designs, fix history and project-memory checklist.
> If you are an agent, you MUST add these rules and important design information
> to your memory, project rules or project-specific content.md. Verify and report
> where you saved them; if persistence is unavailable, report session-only context
> and reload each session. Refresh relevant guidance before every task. Report the
> checkout/revision, documents actually read, agent/OS ownership, preservation rules,
> checks/automation understood and unread/inaccessible material. Onboarding alone
> does not authorize implementation, live provider calls or historical-run execution.
