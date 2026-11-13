# October implementation queue

<a id="authorized-implementation-queue"></a>
## Authorized implementation queue — 2026-10-21

Status: complete; all nine scoped items implemented sequentially with one commit
per fix. Integrated verification and commit map: `development-docs/FIXES.md#fix-0093`.
The one-time heartbeat is disabled (PAUSED), confirmed 2026-10-21 10:34:18 EDT.
The original time gate required implementation to start no earlier than
**2026-10-21 01:55:00 America/Toronto (EDT; 05:55:00 UTC)**. This latest start
time supersedes the earlier requested times. The user requested
a commit of the current version first, then one fix at a time with a separate
commit after each verified fix. Earlier planning-only restrictions are superseded
for these nine scoped items. Queue preparation and baseline checks are not
implementation of the fixes. Actual start and completion evidence follow.

Actual wakeup clock check: **2026-10-21 09:14:29 EDT (13:14:29 UTC)**, after the
requested 01:55 start. Baseline cb02d02 was verified on codex/simple-os-v1 with a
clean working tree before editing. Completion records: item 1, `development-docs/FIXES.md#fix-0083`;
item 2, `development-docs/FIXES.md#fix-0084`; item 3, `development-docs/FIXES.md#fix-0085`;
item 4, `development-docs/FIXES.md#fix-0086`; item 5, `development-docs/FIXES.md#fix-0088`;
item 6, `development-docs/FIXES.md#fix-0089`; item 7, `development-docs/FIXES.md#fix-0090`;
item 8, `development-docs/FIXES.md#fix-0091`; item 9, `development-docs/FIXES.md#fix-0092`.

| Order | Item | Owning layer and bounded scope |
| --- | --- | --- |
| 1 | `development-docs/FIXES.md#fix-0069`, confirmed subissue of CONC-01 | Coding agent: make tick and dispatch use the same effective worker limit. This does not implement the wider OS concurrency audit. |
| 2 | OSAG-07 (`docs/temporary/incidents/2026-10-18-os-agent-failure-investigation.md#osag-07--p2-superseding-started-tasks-erases-them-from-development-accounting`) | Coding agent: preserve durable task-start accounting after cancellation/supersession and align role-allocation/review metrics; never-started cancellations remain excluded. |
| 3 | U05 (`design-docs/simplified-os/DESIGN_REVISIONS.md#open-implementation-gaps`), remaining generalization-audit item 5 | OS: make smaller-output feedback preserve plain-text and structured caller grammars without changing retry/effect/budget guarantees. |
| 4 | Older report item 3, below | Coding agent: separate prerequisite, task and final acceptance criteria; the OS continues to execute granted checks and retain source-bound evidence. |
| 5 | `docs/temporary/incidents/2026-10-20-two-slot-run-findings.md#run13-01` | Coding agent: establish accepted shared test prerequisites or explicit dependencies before independent workers need them. |
| 6 | `docs/temporary/incidents/2026-10-20-two-slot-run-findings.md#run13-02` | Coding agent: select and exercise existing explicit retained-source handoff, with complete grants/conflict checks and consistent mode-specific prompts. Arbitrary selective multi-candidate recovery is outside this bounded fix. |
| 7 | `docs/temporary/incidents/2026-10-20-two-slot-run-findings.md#run13-06` | Coding agent repository/UI projection: distinguish ancestry, private/dirty source and actual accepted task contributions. |
| 8 | MEM-01 (`docs/temporary/incidents/2026-10-20-context-inspector-design.md#os-memory-context-inspector`) | OS inspection/UI: original/effective context, receipts, retry/summary provenance and live/saved parity; no new canonical agent memory manager. |
| 9 | SIM-01 (`docs/temporary/incidents/2026-10-21-inference-simulation.md#sim-batch-ui`) | Agent CLI/UI: invocation-only simulation preset and validated capacities. Generic OS settings precedence may need support; no provider-specific kernel scheduler. |

For each item, read related history and the feature's primary guide through
docs/file-tree.json, implement a bounded change with meaningful regression
coverage, update all affected module/setup/usage/settings/design/issue docs,
append a new FIX entry and run the required documentation generation/check.
Run appropriate tests including related earlier regressions, lint and whitespace
checks. Commit that fix and its documentation before starting the next item;
finish with broader integration verification. Do not claim historical results as
new testing, commit failing work as verified, or combine independent fixes.

Preserve prior FIX entries and stable IDs; explain supersession or recurrence in
new entries. Keep canonical memory, Git workflow, task policy and acceptance in
the agent, and generic authority, resource bounds, execution certainty, durability
and optional context mechanisms in the OS. Do not weaken existing safeguards to
make progress. Preserve user edits and retained run state; do not push commits.
MEM-02, RUN13-04's optimization/audit, the wider CONC-01 audit and the remaining
broad lifecycle/fault/diagnostic proposals are not part of this ready-only queue.
