# Repository instructions for agents

Apply these rules throughout the PolyInference checkout. Also follow any
instructions in the directory you work in.

## Before work

1. Read `development-docs/FIXES.md` before investigating, editing, reviewing or
   running repository checks. Read its maintenance rules and entries, including
   design principles. Use related evidence and regressions to avoid recurrence.
2. Before agent or OS changes, read `design-docs/simplified-os/RUNTIME_BOUNDARY.md`
   and its relevant contracts. Coding policy belongs to the agent; general OS
   programs must need no Git, coding tasks, source edits or acceptance checks.
3. Navigate with [the agent JSON tree](docs/file-tree.json) and read each affected
   feature's primary `doc`. `dev-readme.md` is the contributor entry point.
4. On a new session or after context loss, follow `docs/contributor-onboarding.md`.
   You must save `docs/project-memory.md` in available project memory, project
   rules or project-specific `content.md`, read back the save, and report its
   location. If unavailable, report session-only context and reload next session.
   Refresh against current sources. Report unread guidance before dependent work.

When delegation is authorized, pass these reading and reporting requirements
to the delegated agents. Preserve existing staged and unstaged work, historical
source pins, original grants, budgets and deadlines, and uncertain-effect holds.

## Before finishing or handing off

A fix or feature is incomplete until affected module guides, setup, usage,
configuration, design, task and navigation docs are current. Follow
`docs/maintenance.md`. State which adjacent docs needed no edit and why.

Every note except the root has exactly one incoming Markdown link, from its
parent. Update that link and `docs/file-tree.json` when adding or moving files.
Every feature has one primary `doc` explaining its owned code. Put draft analysis,
proposals and handoffs in `docs/temporary/` as `YYYY-MM-DD-short-topic.md`.
Verify callers, CI and test-suite membership before deleting any script.

Maintain the Obsidian graph as part of doc changes. Keep the graph filter and
module groups current when notes are added, moved or reclassified. Keep the
README accent, key navigation group, spare colors and search examples usable.
Update the reading map when critical routes change. Follow
`docs/obsidian-graph.md` for the preset, layout, and validation commands.

Update `development-docs/FIXES.md` in the same task. Use the next ID and the
entry template: symptom/trigger, owning root cause, concrete change or findings,
design principle, and actual checks and limits. Link recurrences to earlier fixes.
Preserve prior decisions and explicitly mark corrections. Investigation entries
must say no implementation changed and distinguish findings from hypotheses.

Run `python scripts/project_docs.py` and `python scripts/project_docs.py --check`.
Report the documentation review, checks and their limits. Keep contributor
onboarding and retained project knowledge current when project rules change.

Retained project rules refreshed and read back for `da94312` on 2026-11-12.
The agent owns task meaning, Git, canonical memory and acceptance; the OS owns
generic grants, effects, admission and accounting; providers own token/GPU
scheduling. The proposed scheduler only requests run, wait or preemption for
individual processes. Preserve original authority and evidence. This is
repository guidance; it installs no runtime hook or automation.

## Retained checklist refreshed 2026-11-13

Source: docs/project-memory.md at working checkout HEAD da94312; existing
uncommitted documentation retained. Review date: 2026-11-13.

### Project knowledge to retain

Agents must save this checklist in project memory, project rules or
project-specific `content.md`, verify the save and report where. Record the
checkout and review date. Refresh before each task and after context loss.

| Owner | Responsibilities |
| --- | --- |
| Coding agent | Task meaning and dependencies, Git, source reuse, canonical memory, reply grammar, check purpose, recovery intent and final acceptance. |
| OS | Generic grants, process and effect execution, admission, durable records, accounting, replay, certainty and optional workspace/context services. |
| Provider | Protocol behavior and actual token/GPU scheduling; a lane name is not evidence of physical placement. |
| Scheduler (proposed) | Admit, defer or request preemption of one process at a time. The OS still distributes resources and establishes release. |

General OS programs need no Git, coding task, source edit or acceptance check.
Keep the public runtime boundary usable without the coding application.
Preserve existing work, source authority, original grants, deadlines, accounts
and immutable evidence. A disconnect or stopped driver does not prove a remote
effect ended. Isolating an undelivered raw response retains the physical hold
and fences late delivery. Retries cannot refill allowances or replay unknown
tool effects. Resume uses original pins and explicit compatibility rules.

The coding agent requires one production file and an explicit contract for local
edits. Required cloud work stays on cloud. Test-only assignments can run existing
checks with no source-write target or commit; a kept test observation does not
supply a code contribution or independent final acceptance. Exact-source receipts
support review; keep fixture, browser and live results separate.

Read effective values from the current settings and launch guides. A local token
pair drives request/packing/admission limits; native cloud per-call limits are
provider-owned. The UI may stop only a Strata instance it started and owns.
Use fresh state for changed program/configuration pins. Current compatibility is
documented in the runtime boundary's Resume guide.

Before work read the complete fix history. Update all affected documentation and
the history in the same task. Maintain one primary guide per module and one
incoming note link per non-root note. CI checks structure and exported settings;
run the required checks and report actual results and limits. Use dated
temporary notes and promote durable decisions into the maintained guide and
FIXES.md. Loading these rules does not install hooks or automation.
