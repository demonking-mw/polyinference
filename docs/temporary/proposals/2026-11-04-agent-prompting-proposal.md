# Simpler agent prompts and milestone-driven sprint planning

Date: 2026-11-04. Status: **proposal; no implementation in this document**.
Implementation issue: PROMPT-01, at the top of the current iteration tracker (`docs/temporary/incidents/2026-11-04-prompting.md#prompt-01`).

> **Audit correction, 2026-11-04:** this earlier proposal is retained for history.
> Use the audited analysis and corrected implementation plan (`docs/temporary/proposals/2026-11-04-agent-prompting-audit.md`).
> Its corrections supersede the contract relaxation, phase skipping, proof/reuse,
> partial-read and test-only shortcuts below. The first implementation retains
> current contracts and completion guarantees while improving prompts and repair.

> **Later implementation, 2026-11-04:** the user explicitly authorized the test-only
> exception. `development-docs/FIXES.md#fix-0178` implements `kind: test` without an
> implementation file, result path or source commit. Test results use existing agent
> records and actual receipts. Test authoring/repairs remain edits. Other proposals
> below remain subject to the audit; this does not implement the wider redesign.

Development records (`development-docs/README.md`) · Proposal archive (`docs/temporary/proposals/README.md`) · Related run (`docs/temporary/incidents/2026-11-04-review-allowance.md#run-917e45c4b40a`)

## Purpose and scope

Improve the rate at which the agent completes useful work. Make assignments clear,
preserve useful context during repair, and remove avoidable rejection and repeated
verification. Token reduction is useful when it follows from these changes.

This supersedes the earlier conversational proposal where it suggested more
validation, detailed mandatory task paperwork, or adapter work as a prerequisite.
The preferred implementation is a small agent refactor using existing OS services.
**No OS change is required by the core proposal.** Runtime changes considered below
are explicitly deferred, outside PROMPT-01's implementation scope.

The current request authorizes this proposal and backlog issue only. It does not
authorize implementation, a live model test, or resumption of a historical run.
Earlier FIX-0175 limit exposure is already implemented; the changes below are not.

## What the current documents establish

The proposal was checked against current source and these documents. Historical
design statements and proposed changes are distinguished from current behavior.

| Document | Relevant established behavior |
| --- | --- |
| Agent design, senior queries and specialists (`design-docs/langgraph-agent/README.md#43-senior-queries-and-specialists`) | Cloud planning produces proposals; specialists perform coding through the worker path. One observable behavior and a focused check are the existing local-task intent. |
| P0 implementation record (`development-docs/p0-repairs-2026-10-29.md`) | Current local coding assignments require one production file plus permitted tests/docs and a detailed local contract. Coupled cloud work has an explicit exception. |
| Agent workflow (`docs/modules/agent-workflow.md`) | Dependencies wait for accepted contributions. Plans, started contracts, pending work and original recovery resources survive reviews. |
| Check selection (`docs/guides/checks.md`) | Prerequisite, task and final acceptance checks have distinct purposes. Discovery closes after setup/planning. Source/build closure and shared runner ownership matter. |
| Capability contract (`docs/modules/capabilities.md`) and direct/native authority (`design-docs/simplified-os/boundary/capabilities.md#direct-and-native-calls-use-the-same-authority`) | Registered typed capabilities define actual actions. Native tools use the same grants and effects as direct calls. Host metadata is not invented by the model. |
| Current local/cloud policy (`design-docs/simplified-os/RUNTIME_BOUNDARY.md`) | Decomposition, Git and acceptance are agent policy; generic admission, authority and accounting belong to the OS. |

The user's latest direction is more specific than the existing allowance for
supporting tests/docs: a local writing assignment should edit **one file**. Writing
another file is another assignment. A testing assignment should perform **one
coherent test or investigation** and need not invent a production file to edit.
Reading dependencies and doing a proportionate self-check do not expand an editing
assignment into a second implementation task. Implementing this requires changes
to agent task construction/validation and documentation, not to OS task semantics.

## P1 — Give every invocation one explicit assignment

**Old:** large shared instruction strings, broad JSON state and a final request to
"continue this invocation." The model infers what decision is required now.

**New:** one small agent-owned prompt assembly path selects instructions from the
role, current task, phase and transport. Each invocation receives:

1. What to accomplish or decide now.
2. Verified current status and relevant uncertainty.
3. The organization/assignment relevant to this invocation.
4. Evidence and permitted actions.
5. Current limits, with their scope and units.
6. The expected result and how to report a blocker.

Use the original objective once in a fresh coding/planning context; preserve user
constraints and applicable updates. Avoid repeating it inside several derived
fields. Include setup, recovery or migration guidance only when applicable.
Keep prompts and schemas small enough to understand without a separate glossary.
Use the existing graphs and bounded calls; this is not a new prompt framework or
a sequence of extra planning agents.

## P2 — Organize the effort before distributing tasks

The sprint manager should reason through the following sequence in its normal
planning invocation. These are thinking steps and concise output sections, not
five mandatory model calls or five new validation gates.

```mermaid
flowchart LR
    A[Next milestone] --> B[Current status]
    B --> C[Organization of the effort]
    C --> D[Task distribution from that organization]
    D --> E[Proportionate verification]
```

### Next milestone

Choose the next meaningful, observable increment toward the full objective.
State what the user or another component will be able to do when it is reached.
Keep later requirements in a concise backlog. Preserve the original objective and
existing acceptance requirements when deriving milestones; the breakdown cannot
silently narrow them. List consequential assumptions or unresolved scope questions.

**Old:** "use many small tasks," which can produce isolated helpers without a
usable product increment. **New:** identify the milestone first, then choose only
the necessary work to reach it. Do not inflate the task count to obtain cloud quota.

### Current status

Present a short, structured overview with evidence references:

| Include | What the manager needs to understand |
| --- | --- |
| Product status | Working behavior, partial implementation, missing behavior and uncertainty. |
| Current source | Integration tree, existing entry points/APIs and relevant changes since the previous review. |
| Existing effort | Accepted work, work awaiting review, ready/blocked pending tasks and interrupted work. Preserve valid pending work. |
| Environment | Dependency preparation command, required tools, runner availability and where earlier checks ran. |
| Verification | Check purpose, actual command, necessary source/test inputs, latest applicable outcomes and what those outcomes prove. |
| Authority and capacity | Effective write/read scope, actual tools, effective workers/placement, current review/run budgets and recovery eligibility. |
| Obligations | New user instructions, unresolved reports and recovery decisions requiring attention. |

Distinguish an executed command from a passed test. A failed dependency installation
means later behavior may not have been tested. A worker's passing check and an
independent check in another workspace describe different execution contexts.

### Organization of the effort

Make this explicit before task generation. The manager proposes a small concrete
organization for the selected milestone, grounded in the existing repository:

| Area | Required organization |
| --- | --- |
| New or changed code | File/directory layout, each file's responsibility, existing code to reuse, key inputs/outputs, and the entry points that connect the pieces. |
| Shared boundaries | Necessary function signatures/data shapes, who produces and consumes them, and ordering where files share state or APIs. Use detailed versioned contracts only when the boundary warrants them. |
| Test authoring | Test file, behavior/scenario, inputs or fixtures, expected result and runner integration. |
| Test execution | Exact scenario or bounded investigation, command/runner, required environment, source under test and result to report. Production editing is outside this assignment. |
| Prerequisites | Dependency/runner preparation owner, exact handoff commands, generated output locations and dependent tasks. |
| Integration | File or existing entry point that makes the milestone usable, who owns its edit, and its dependencies. |
| Verification | The smallest useful observation that will establish the milestone, plus explicit user-required/final checks. |

The organization should be concise: a file map, a few shared APIs, a test plan and
a dependency sketch. Do not require seven paragraphs of contract boilerplate for
every helper. Existing APIs should be referenced rather than redesigned routinely.

### Task distribution

Derive assignments from that organization. Each local agent does one thing:

- **Edit:** one target file, one bounded change, required read dependencies, and
  a concise expected result. Test/documentation authoring also counts as a file edit.
- **Test:** one coherent scenario or bounded investigation, required inputs and
  permitted execution tools, expected observations, and a result to report.
- **Inspect:** one specific question and relevant source/evidence, when inspection
  itself is the useful assignment. Do not create inspection tasks for obvious facts.

A pure testing or inspection task must not fail because it has no production
`implementation_path`. Support these through a small agent-level task-kind
distinction or equivalent construction rule. Reuse existing processes and tools;
do not add separate supervisors or a new graph for every task kind.

For every task, provide only: its purpose; target file or test/question; necessary
inputs/APIs; dependencies; relevant permissions; and a useful completion condition.
Make the effective placement clear before requiring a local or cloud contract.
Keep the coupled cloud exception for work that genuinely cannot be split safely.

Illustrative organization for the recorded project's next visible-world milestone:

| Organization element | Derived assignment | Depends on |
| --- | --- | --- |
| Existing toolchain helper | Edit that helper to make dependency preparation reproducible. | Current setup evidence. |
| Tile-grid provider file | Edit one grid implementation file with an agreed coordinate/data API. | Relevant preparation, if needed. |
| World-view file | Edit one rendering file consuming that grid API. | Accepted grid provider. |
| Application entry file | Edit the existing entry to connect world creation and rendering. | Accepted provider and view. |
| World-creation test file | Edit one test file for the declared visible-world scenario. | Agreed UI/entry behavior. |
| Scenario verification | Execute the declared world-creation scenario through the available foreground runner. | Accepted integration/test and a prepared environment. |

This is an example of deriving work from structure, not a committed architecture
or an instruction to implement Minecraft in this documentation task. The manager
should reuse existing files when suitable. A separate testing task is appropriate
when useful, not mandatory after every edit.

### Verification and continuity

Choose verification after understanding the milestone and organization. An edit
may finish after an engineer's source review or a small relevant self-check when
appropriate. A declared testing task should report what actually ran and its result.
Use a meaningful milestone check at integration, and retain explicit final criteria.

Resolve reports using evidence. Keep valid pending tasks and accepted providers;
add or replace work where necessary. Dependencies must describe when inputs become
available, including the existing acceptance barrier. Do not regenerate the whole
plan on every review or mistake a completed helper for a completed milestone.

The manager should normally return a short milestone/status summary, the work
organization, assignments, review decisions and verification plan. If key source
is missing, it can request it first without drafting speculative task contracts.
Completion still needs an honest assessment of the full objective.

## P3 — Match the actions the OS actually exposes

The current capability registry supplies name, input schema, effect class and
workspace requirements. Native jobs advertise only granted capabilities through
`polyinference_tool`; the OS converts calls into journaled `CapabilityCall` effects
and supplies workspace metadata. Raw workers return agent `Action` responses,
which the agent translates to those same effects.

| Invocation | Prompt/result must agree with existing execution |
| --- | --- |
| Native engineer | Use the advertised `polyinference_tool` with `tool` and `arguments`. Return the declared final engineering result, not a raw `Action`. |
| Raw engineer | Return an `Action` for one advertised operation, or the phase's final result. Tool names/arguments must match the installed contract. |
| Sprint manager | No coding tools. Use the agent's bounded evidence requests and return a planning/review result. |
| Native diagnosis | Use only its granted frozen-source/evidence readers. |
| Raw diagnosis | Use supplied previews and request permitted read expansion; do not claim native readers were called. |

Do not ask the model to manufacture schema digests, workspace generations, permits
or effect classes. The agent/OS already binds these. Avoid a second manual tool
catalog in native prompts; the advertised tools are authoritative. Raw examples
must stay aligned with the registered argument definitions.

Use existing protocol registration to select agent-owned schemas and instructions.
For native calls, supply the phase instructions once in the agent context and avoid
duplicating them in the optional protocol instruction string. Omit the pasted
full textual schema when the existing native `outputSchema` already supplies it.

The raw HTTP adapter currently accepts a `response_schema` argument but does not
attach a provider schema to its request. Keep a compact textual response contract
for that path. Do not assume native schema enforcement applies to raw APIs.
Simplify the model-facing response fields rather than introducing dynamic schema
registrations for every remaining-budget value.

These are agent instruction, registration and task/result changes. Keep OS grant,
argument, execution-certainty, replay, resource and source-precondition enforcement.

## P4 — Preserve useful evidence with less repeated context

**Old:** objective, assignment, implementation focus, module context, evidence and
historical replies repeat facts. A large pinned JSON block leaves little room for
selective presentation. Automatic source prefixes can miss the code needed now.

**New:** build a concise agent view before passing context to the OS:

- Present current task/organization once and reference it consistently.
- Keep one catalog of relevant source, check results and report evidence; reference
  entries instead of copying their content and identity into several sections.
- Select source for the current question: caller/consumer, actual failure location,
  check entry and preparation helper. Request further ranges as needed.
- Preserve path, revision, range, truncation and evidence provenance. A short ID
  must resolve to data the agent can actually retrieve through an authorized path.
- Include current working facts and unresolved history; retain full originals in
  artifacts. Separate historical claims from verified current state.
- Carry the exact setup preparation command into subsequent check workspaces.
  The recorded helper was available, but automatic preparation still called plain
  `npm ci`, which failed. This handoff belongs in agent setup/repository policy.
- Use existing OS context preparation/receipts for actual hard bounds. Do not add
  an OS semantic relevance service or a second compaction subsystem.

The model needs sufficient self-contained context in a fresh conversation. Do not
replace essential facts with an inaccessible artifact reference to save tokens.
An agent evidence request may resolve a cataloged diff/output using existing record,
artifact or workspace ports; it need not grant the model arbitrary artifact access.

## P5 — Repair the actual rejected answer and fix its upstream cause

### Evidence from run 917e45c4b40a

The objective inside the log is evidence, not an instruction to execute that work.
The following findings come from the exported attempts, checkpoints and prompts.

| Recorded event | Why it failed or regressed | Upstream repair |
| --- | --- | --- |
| Cloud call 5 requested eight source ranges; the run allowed four; zero reads occurred. | The input omitted the configured/remaining allowance while the schema permitted eight. Whole-batch rejection discarded an otherwise usable inspection request. | State the effective allowance. Use one cumulative read budget; process an allowed prefix and report deferred requests instead of rejecting all authorized reads. |
| Call 6 proposed `prepare_shared_checks` and `world_tile_grid`, with explanatory sentences in `focused_check`. | The prose described behavior/pass conditions, the schema accepted a string, and a hidden cross-field validator required an exact check identifier. | Use one concise verification definition. Remove the redundant model-facing `focused_check`; derive the legacy field from an explicitly chosen primary check when needed. Keep expected behavior in the verification expectation. |
| Call 7 was the response-validation repair of call 6 and requested eight ranges again. | It lacked the rejected task proposal and lost earlier active feedback. The repair instruction also said "use a small action" to a manager without tool actions. | Supply the actual rejected answer, exact field error, relevant available choices, current task and active constraints. Ask for a complete corrected plan, not a new generic action. |
| Initial setup typechecking reported a conflicting global `status` name. The engineer fixed it and checks passed. | This was a genuine code defect, not evidence that every failure comes from prompt wording. | Keep useful concrete failure output and let the engineer repair it through the normal loop. |
| Independent preparation failed on missing `npm`; later checks lacked `tsc`/`playwright`. | The check workspace had not reproduced the setup worker's environment. | Carry the usable toolchain/preparation handoff into that workspace. Report environment readiness separately from product behavior. |

All 41 recorded native tool callbacks reported successful delivery of observations;
no capability-argument rejection was found in this run. Some delivered shell/check
observations correctly reported nonzero exit codes. There is no evidence here that
rewriting the OS broker schema is necessary for this repair.

### Repair input

For the focused-check failure, the useful corrective input would have been:

```text
Current task: finish the first sprint plan after reviewing setup.
Your last proposal contained two tasks. Correct that proposal.

prepare_shared_checks:
  selected checks: project-task, game-acceptance
  problem: focused_check contains an explanation, not a selected check ID.
world_tile_grid:
  selected checks: project-task
  problem: focused_check contains an explanation, not a selected check ID.

Choose the intended primary check for each task. Preserve the expected behavior
in its verification description. Preserve unrelated decisions unless the same
repair exposes a genuine dependency or verification problem.

Active earlier constraint: this historical run allows four review ranges;
zero have been read. The previous eight-range request was not executed.

Rejected proposal: [inline complete retained JSON]
Relevant check definitions and preparation evidence: [compact actual inputs]
Remaining correction/resource allowance: [current authoritative values]

Return the complete corrected proposal. No model tool action is available here.
```

Use the historical four-read value only when reconstructing this old run. Fresh
configurations after FIX-0175 default to 16; never copy an old allowance into a
new live prompt.

One contextual issue also deserved attention: the preparation task selected both
`project-task` and `game-acceptance`. Preparing dependencies does not establish
unimplemented gameplay. The manager should select suitable readiness verification
without requiring future features to pass before preparation can be accepted.
This was a planning risk in the rejected proposal, not a later executed failure.

The agent can obtain the rejected response from retained failed-attempt output
references through existing record/artifact ports. At callback time the failed
attempt has already been recorded. Match the actual request/attempt; do not read
an unrelated latest response. Append repair information without changing existing
required context pins, role, schema, grants, deadline or retry allowance.

Avoid a chain of new critics or repair agents. Normalize harmless representation
differences where unambiguous; leave semantic choices to the owning model. The
implementation should fix the generating prompt/contract so the same ambiguity
does not recur; this does not authorize a model to rewrite its own instructions.

## P6 — Keep active constraints across correction layers

This is an additional cause found while investigating P5.

Call 6's request contained `invalid-0/feedback`, marked optional. That feedback
described the rejected read request. `worker_memory.repair()` kept only required
parts, so call 7 contained `repair-feedback` but no `invalid-0/feedback`. The previous
proposal was represented by an artifact reference the manager could not retrieve.
The new call therefore lost useful correction context even while retaining the
large original project packet.

**Old:** priority/required flags determine survival without distinguishing a
resolved historical error from an active constraint.

**New:** maintain a small agent-owned current correction state: the rejected
answer reference/content, unresolved errors, current effective limits and relevant
execution facts. Include it in correction input until resolved. Mark active facts
as required when constructing the request, or explicitly carry existing relevant
feedback into repair; do not drop it merely because it was previously optional.
Superseded errors should leave this view while remaining in historical artifacts.

Use a few clear categories of context rather than a complex priority optimizer.
Preserve whole action/observation pairs and all original resource accounting.
No OS retry policy or context-retention algorithm needs to change.

## P7 — Simplify the workflow and reduce checks

The earlier proposal placed too much emphasis on new validation. The revised
direction is fewer agent-level hurdles and more responsibility for the engineers
and sprint manager to make sensible decisions.

| Old | Proposed simpler behavior |
| --- | --- |
| One production file plus extra tests/docs bundled into a detailed local contract. | One-file editing assignment, or one test/investigation assignment. Keep the structural target clear; use concise API guidance where needed. |
| Separate `checks`, `focused_check`, `behavior` and repeated implementation-focus descriptions. | One verification expectation, with an optional primary registered check when appropriate. Derive legacy internal projections in the agent. |
| Many mandatory prose fields and optional output sections treated as schema obligations. | Require the few fields needed to execute the current assignment. Omit irrelevant sections; tolerate harmless explanatory metadata in agent results. |
| Three successful prerequisite runs on the same effective tree in this run. | Reuse the matching receipt inside the same valid execution context. Recheck when source, inputs, environment or invocation changes. |
| Routine broad checks for every small edit. | Let the engineer use source review or a focused self-check. Verify the integrated milestone meaningfully, then apply explicit final criteria. |
| Reconciliation and assessment model calls repeat conclusions on unchanged source. | Fast-path unchanged integration and reuse applicable evidence. Use an engineer continuation for real incoming changes or unresolved compatibility questions. |
| Every detected task-contract imperfection can reject the whole plan. | Keep execution-critical checks; give nonblocking feedback for stylistic detail and ordinary engineering judgment. Let the manager refine its plan. |
| Cumulative read allowance plus a separate eight-range proposal limit and whole-batch rejection. | Prefer one cumulative allowance, currently defaulting to 16, bounded by existing byte/resource limits. Report fulfilled/deferred reads. |
| A fresh checker/reviewer is a routine response to uncertainty. | Let the owning engineer repair from concrete feedback first. Use a separate diagnosis when it adds information or authority the engineer lacks. |

Reusing worker evidence must respect the actual source, invocation, process/workspace
and environment compatibility. Independent verification in a different workspace
still needs its environment prepared; matching tree hashes alone are insufficient.
Explicit user-required checks and declared final acceptance criteria remain required.
Unexecuted tests must never be labeled passed.

Retain OS authority, typed action arguments, source preconditions, budgets,
execution-certainty and replay protection. Retain the user's one-file/one-purpose
boundary and enough dependency validation to avoid impossible scheduling. Reduce
agent semantic/stylistic gates and redundant test/model passes, not those contracts.

These changes would deliberately revise current agent verification/publication
policy where it mechanically requires checks for every intermediate assignment.
They are proposed changes, not claims that the current guides already permit them.
Use fresh program/state pins when implementation changes those contracts.

## Prompt-family improvement chart

Columns apply the same seven points to every generated prompt family. A dash
means the point has no useful special application for that family.

| Prompt family | P1 Explicit assignment | P2 Effort organization | P3 Actual actions | P4 Relevant evidence | P5 Contextual repair | P6 Active constraints | P7 Simpler workflow |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Git policy | Select/change/correct branch policy. | Supply repository/branch facts only. | Return policy; no tools. | Latest user branch instructions and observation. | Failed selection and valid alternatives. | Retain latest user overrides. | Reuse explicit valid policy. |
| Setup | Prepare runnable prerequisites and handoff. | Initial files, runner and dependency command. | Setup-granted tools only. | Existing manifests and actual environment. | Failed command plus chosen toolchain. | Retain resolved branch and preparation decisions. | One readiness proof; no full-game verification. |
| Local edit | Change one named file for one purpose. | Its place, APIs and consumers. | Match native/raw worker protocol. | Target and necessary dependencies. | Actual rejected result or failing source. | Current digests, task and unresolved error. | Engineer self-check; avoid routine broad suite. |
| Local test/inspection | Execute one scenario or answer one question. | Fixtures, runner, inputs and expected observation. | Read/execute grants; no production edits. | Tested source and relevant outputs. | Failed invocation or unclear observation. | Tested revision and environment. | No invented implementation-file contract. |
| Reconciliation | Resolve actual incoming changes. | Affected ownership and shared APIs. | Existing scoped engineer tools. | Incoming diff and hazards. | Concrete conflict and current source. | Preserve task/base/permissions. | Skip model pass when no relevant change. |
| Assessment | Judge the current assignment result. | Milestone contribution and done condition. | Correct final-result protocol. | Current source and applicable receipts. | Exact missing/contradictory evidence. | Keep source/receipt identity. | Reuse engineer judgment and matching proof. |
| Manager initial plan | Choose milestone and organize effort. | Files, responsibilities, APIs, tests, owners, dependencies. | Planning result/evidence requests only. | Existing structure, setup and capability status. | Rejected plan plus exact actionable error. | Preserve objective, limits and assumptions. | One planning invocation; small useful batch. |
| Manager sprint review | Review results and advance milestone. | Update existing organization and pending work. | Decisions and next assignments. | Changes and unresolved obligations. | Failed decisions and actual plan. | Retain pending tasks and prior constraints. | No full replanning or automatic repeated suite. |
| Manager completion | Assess the full requested result. | Requirement/milestone coverage. | Completion proposal; no coding tools. | Relevant integration behavior and final checks. | Unmet criterion and supporting evidence. | Exact reviewed source and user scope. | One meaningful final assessment/check set. |
| Diagnosis | Explain one concrete failure. | Identify missing input or responsible boundary. | Native readers or raw read requests, as available. | Actual failure and frozen relevant source. | Prior diagnosis and remaining uncertainty. | Preserve trigger and matching source. | Invoke when engineer feedback is insufficient. |
| Cloud takeover | Repair one inherited assignment. | Failed boundary and retained work. | Cloud engineer's actual granted tools. | Failed approach and reusable source. | Changed implementation approach. | Same grants/account/deadline. | Coding takeover rather than another diagnosis loop. |
| Validation repair | Correct the retained rejected answer. | Preserve its task/organization. | Same role and permitted response. | Rejected JSON, field error and choices. | Specific correction request. | Carry unresolved earlier feedback. | One bounded correction; no extra critic. |
| Output-limit recovery | Return a smaller complete result. | Preserve the useful current assignment. | Original declared protocol. | Required context and execution facts. | Actual truncation/size feedback. | Keep completed tool effects and limits. | Shrink batch/detail; avoid repeating partial output. |
| Progress warning | Change approach on one stalled task. | Restate its unresolved purpose. | Existing tools and scope. | What has repeated and what remains unknown. | Concrete blocker/new approach. | Retire resolved warnings. | Feedback to owner before escalation. |
| Native continuation | Finish the interrupted invocation. | Retain original assignment. | Resume granted tools only. | Recorded conversation and host receipts. | Known interruption/remaining work. | Never replay completed effects. | Use only when settlement permits continuation. |
| Compaction | Summarize supplied data. | Preserve relevant responsibilities/unfinished work. | No tools. | Source segment and provenance. | Correct malformed summary only. | Retain uncertainty and unresolved facts. | Optional derived view; no new reviewer. |
| Endpoint probe | Return the requested readiness response. | — | No coding actions. | Minimal endpoint request. | Transport/format feedback only. | Original bounded probe. | Keep minimal; do not add agent policy. |

## Ownership and OS changes

### Core implementation: agent level

| Area | Existing owning code |
| --- | --- |
| Invocation-specific instructions, context and protocol registration | [prompts.py](../../../src/polyinference/agent/prompts.py), [services.py](../../../src/polyinference/agent/services.py), [schema.py](../../../src/polyinference/agent/schema.py). |
| Milestones, status, organization, assignments and simpler review policy | [controller.py](../../../src/polyinference/agent/controller.py), [senior.py](../../../src/polyinference/agent/senior.py), [domain.py](../../../src/polyinference/domain.py). |
| Single-purpose task construction, optional contract detail and effective placement | [tasks.py](../../../src/polyinference/agent/tasks.py), [architecture.py](../../../src/polyinference/agent/architecture.py), [routing.py](../../../src/polyinference/agent/routing.py). |
| Relevant evidence, active correction state and repair context | [review.py](../../../src/polyinference/agent/review.py), [worker_memory.py](../../../src/polyinference/agent/worker_memory.py), [diagnostics.py](../../../src/polyinference/agent/diagnostics.py). |
| Setup environment handoff and task/final-check policy | [setup.py](../../../src/polyinference/agent/setup.py), [repository.py](../../../src/polyinference/agent/repository.py), [runtime_policy.py](../../../src/polyinference/agent/runtime_policy.py), [worker.py](../../../src/polyinference/agent/worker.py). |

Retain original model/effect records, historical source, user changes and resource
envelopes. Preserve the agent/OS separation documented above. No implementation
should migrate old runs merely to pick up the new prompt or task shapes.

### OS changes considered, but not proposed for this implementation

| Potential OS change | Why it is OS-level | Decision and justification |
| --- | --- | --- |
| Change native broker schema generation or generic wrapper text. | [runtime/codex.py](../../../src/polyinference/runtime/codex.py) serves generic agents. | Defer. This run showed no broker argument rejection. Existing agent protocol registration can remove duplicate agent instructions without editing the adapter. |
| Add provider structured-output fields to raw requests. | [runtime/inference.py](../../../src/polyinference/runtime/inference.py) owns provider wire formats. | Defer. Agent prompts can retain a compact textual contract. A future transport fix would require protocol-specific evidence and compatibility checks; it is not necessary for PROMPT-01. |
| Change retry/context enforcement or add a new repair API. | [runtime/retry.py](../../../src/polyinference/runtime/retry.py) and [runtime/context.py](../../../src/polyinference/runtime/context.py) enforce generic invariants. | Not required. Existing repair callbacks and record/artifact ports support the proposed correction state and failed-answer lookup. Preserve required pins and original allowances. |
| Capture every final physical wire packet through a new runtime hook. | Only the adapter sees the final provider-specific packet. | Defer. Use existing agent prompt artifacts and preparation receipts first; label export limits honestly. Do not add telemetry infrastructure as a prerequisite to better assignments. |

If implementation finds a genuinely missing public OS capability, document the
specific missing operation, evidence that existing ports cannot express it, and
the smallest generic extension before changing OS code. A coding workflow
preference is not a justification for moving task semantics into the OS.

## Suggested implementation sequence and verification

1. Fix agent prompt/response agreement and the recorded repair-context loss. Use
   the two failed senior answers as concrete regression inputs. Simplify the
   verification field and read-budget handling at the same time.
2. Rework the manager input and output around milestone, status, work organization,
   distribution and verification. Support one-file and test/inspection assignments.
3. Reduce repeated source/history and repeated verification/model passes. Carry
   setup preparation decisions into independent execution contexts.
4. Update affected guides to describe actual implemented behavior and preserve
   prior evidence. Keep the prompt-family chart as a coverage checklist, not a new
   set of runtime gates.

Use a small focused set of implementation regressions for the changed boundaries.
Exercise a normal manager plan, the recorded corrections, a test-only assignment,
native/raw action agreement and valid receipt reuse versus a changed environment.
Do not build a new exhaustive prompt-scoring or multi-reviewer system.

When separately authorized, use a short fresh live workflow to judge whether work
actually finishes. Record completion, useful product behavior, failed/corrected
model attempts, unnecessary pauses, model/check count and input size. Successful
JSON parsing alone is not success. Lower input size alone is not success either;
the primary target is reliable useful progress with fewer avoidable stops.

## Evidence, limits and document maintenance

This proposal follows source at checkout `8b527c9` plus the existing uncommitted
tree, including FIX-0175. Relevant current sources are linked above. It also reads
the exported run `/home/marven/Downloads/polyinference-917e45c4b40a.json` and the
seven full application prompts retained under
`/home/marven/Projects/pi/session-artifacts/review-limits-2026-11-04/`.

The specific retry-context loss, field ambiguity, read rejection, TypeScript failure,
callback count and repeated passing checks were checked against that retained
evidence. The proposed improvements in success rate remain unmeasured. No new
model call, saved-run execution, code fix or production test was performed for
this document. Documentation navigation/link checks are recorded in FIX-0176.

Reviewed the agent services/workers/workflow, check, capability and boundary guides.
They remain descriptions of the current implementation; this proposal does not
silently edit them to claim that future policy already exists. Implementation must
update affected guides, onboarding/project memory when applicable, and fix history
in the same change. Proposal navigation and the implementation issue are updated
now. Earlier source changes, accounts, game files and historical documents remain
preserved.
