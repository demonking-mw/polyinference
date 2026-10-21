# Fix history and design principles

This is the repository's durable record of fixes and the reasoning they must
preserve. Every agent must read it before starting repository work and update it
before finishing or handing off. [The root agent instructions](../AGENTS.md)
establish that requirement for this repository.

## Maintenance rules

- Append an entry for each independent fix. For work that only investigates an
  issue, record its findings and explicitly say no implementation changed.
- Use the next unused `FIX-NNNN` ID, an ISO date, a descriptive title, and a status.
  Use the user's local date when available. Keep IDs and existing links stable.
- Explain the symptom, root cause, implementation, and design principle
  separately. A file list or "fixed the bug" is not an explanation.
- State which layer owns the decision. Keep application policy in its agent;
  give the OS generic mechanisms and guarantees that other agent types can use.
  Recoverable application errors should reach the responsible agent as evidence
  for a bounded recovery decision. Progress does not authorize bypassing grants,
  user constraints, data preservation, or execution-certainty guarantees.
- Search this history for related fixes. If a problem recurs, link the earlier
  entry, describe the uncovered trigger or regression, and say how verification
  now addresses it. Do not assume similar symptoms have the same root cause.
- Record exact verification and its limits. Separate checks run for this change
  from results quoted from older investigations. Link evidence instead of
  inventing a previous implementation or claiming unperformed validation.
- Preserve earlier entries. Add an explicit correction or superseding entry
  when the explanation or design changes. Do not erase failed approaches or
  unresolved limits that are needed to understand a recurrence.
- Keep detailed investigations in
  [current-iter-issues.md](current-iter-issues.md) and other relevant development
  notes, and link them here. Those notes remain historical evidence; this file
  is the required starting point and index of fixes going forward.

FIX-0001 through FIX-0004 were established from this chat on 2026-10-19.
The historical backfill in FIX-0005 through FIX-0041 was added afterward from
20 earlier repository chats (85 retained turns). IDs reflect recording order,
not implementation chronology. Each historical entry names its source and
distinguishes design-only work, completed implementation, investigation, and
later supersession. Historical test results were not rerun for the backfill.

See [the source-chat audit](CHAT_HISTORY.md) for coverage, exact chat titles/IDs,
verification limitations, and unresolved findings. It confirms an earlier
missing-directory startup relaxation (FIX-0017), followed by an in-place
repository migration (FIX-0040) and the later nested-directory repair (FIX-0001).
The recurring startup principle is established; the earlier implementation did
not cover the later provider's enclosing-repository trigger.

## Index

| ID | Date | Fix |
| --- | --- | --- |
| [FIX-0001](#fix-0001) | 2026-10-19 | Start a selected project inside an enclosing repository |
| [FIX-0002](#fix-0002) | 2026-10-19 | Let the coding agent correct recoverable Git setup errors |
| [FIX-0003](#fix-0003) | 2026-10-19 | Let the coding agent repair failed dependency preparation |
| [FIX-0004](#fix-0004) | 2026-10-19 | Require agents to read and maintain a durable fix history |
| [FIX-0005](#fix-0005) | 2026-10-16 | Preserve the editable graph while clarifying views and labels |
| [FIX-0006](#fix-0006) | 2026-10-17 | Recover graph information lost across design versions |
| [FIX-0007](#fix-0007) | 2026-10-17 | Define portable contracts and close agent/OS handoff gaps |
| [FIX-0008](#fix-0008) | 2026-10-17 | Make design review inspectable and keep translations as data |
| [FIX-0009](#fix-0009) | 2026-10-17 | Build the agent against replaceable runtime and provider interfaces |
| [FIX-0010](#fix-0010) | 2026-10-17 | Expose run processes, project selection, exports, costs, and steering |
| [FIX-0011](#fix-0011) | 2026-10-17 | Correct worker bindings and short demonstration budgets |
| [FIX-0012](#fix-0012) | 2026-10-17 | Give setup and senior coders the tools needed for prerequisite work |
| [FIX-0013](#fix-0013) | 2026-10-17 | Load saved provider credentials without executing environment files |
| [FIX-0014](#fix-0014) | 2026-10-17 | Capture OS inspection evidence in live and saved views |
| [FIX-0015](#fix-0015) | 2026-10-18 | Keep generated projects and runtime history out of version control |
| [FIX-0016](#fix-0016) | 2026-10-18 | Use one serializer for manual save and rolling run archives |
| [FIX-0017](#fix-0017) | 2026-10-18 | Relax the existing-directory prerequisite for starting a project |
| [FIX-0018](#fix-0018) | 2026-10-18 | Make successful and failed launches visible and exportable |
| [FIX-0019](#fix-0019) | 2026-10-18 | Let the coding agent discover an omitted check command |
| [FIX-0020](#fix-0020) | 2026-10-18 | Report core run and task events in the UI server terminal |
| [FIX-0021](#fix-0021) | 2026-10-18 | Deliver accepted artifacts instead of leaving results only in private state |
| [FIX-0022](#fix-0022) | 2026-10-18 | Allow processes to finish without code, Git, or coding reports |
| [FIX-0023](#fix-0023) | 2026-10-18 | Represent phase transitions as current host requests |
| [FIX-0024](#fix-0024) | 2026-10-18 | Retain structured provider failure facts |
| [FIX-0025](#fix-0025) | 2026-10-18 | Preserve effective authority and full requirements through task handoffs |
| [FIX-0026](#fix-0026) | 2026-10-18 | Stop non-actionable planning and repeated known failures |
| [FIX-0027](#fix-0027) | 2026-10-18 | Recover a known failed model operation with a new linked intent |
| [FIX-0028](#fix-0028) | 2026-10-19 | Bound retained native telemetry without aborting healthy generation |
| [FIX-0029](#fix-0029) | 2026-10-19 | Keep reporting failures from replacing execution outcomes |
| [FIX-0030](#fix-0030) | 2026-10-19 | Recover bounded incomplete model output without executing partial JSON |
| [FIX-0031](#fix-0031) | 2026-10-19 | Keep tool home/cache housekeeping outside source authority |
| [FIX-0032](#fix-0032) | 2026-10-19 | Move coding grammar and policy out of generic OS dispatch |
| [FIX-0033](#fix-0033) | 2026-10-19 | Validate agent lifecycle updates and preserve long diagnostic notes |
| [FIX-0034](#fix-0034) | 2026-10-19 | Separate declared build outputs from protected source |
| [FIX-0035](#fix-0035) | 2026-10-19 | Preserve dependencies across workspace generations |
| [FIX-0036](#fix-0036) | 2026-10-19 | Verify native harness permissions and detect unbrokered edits |
| [FIX-0037](#fix-0037) | 2026-10-19 | Separate OS monitoring from agent task and review history |
| [FIX-0038](#fix-0038) | 2026-10-19 | Provide generic durable agent-to-user messages |
| [FIX-0039](#fix-0039) | 2026-10-19 | Request evidence-based sprint briefs and working-commit claims |
| [FIX-0040](#fix-0040) | 2026-10-19 | Work and integrate in the user's actual repository by default |
| [FIX-0041](#fix-0041) | 2026-10-19 | Record remaining run-quality and generalization findings without calling them fixed |
| [FIX-0042](#fix-0042) | 2026-10-19 | Backfill the fix ledger from past repository chats |
| [FIX-0043](#fix-0043) | 2026-10-19 | Diagnose a completed model response with no visible text |
| [FIX-0044](#fix-0044) | 2026-10-20 | Retain facts for unusable completed model responses |
| [FIX-0045](#fix-0045) | 2026-10-20 | Filter safe one-off model failures with durable OS retries |
| [FIX-0046](#fix-0046) | 2026-10-20 | Scope permanent-failure containment to the request being repaired |
| [FIX-0047](#fix-0047) | 2026-10-20 | Keep OS retries separate from application recovery allowances |
| [FIX-0048](#fix-0048) | 2026-10-20 | Document the Codex and serial Haiku tester setup |
| [FIX-0049](#fix-0049) | 2026-10-20 | Diagnose context-packing overflow after gameplay recovery |
| [FIX-0050](#fix-0050) | 2026-10-20 | Audit input and output cap safeguards across inference adapters |
| [FIX-0051](#fix-0051) | 2026-10-20 | Propose bounded OS recovery for inference overflow |
| [FIX-0052](#fix-0052) | 2026-10-20 | Separate OS overflow guarantees from reusable agent recovery policy |
| [FIX-0053](#fix-0053) | 2026-10-20 | Propose agent-controlled OS context handling and optional compaction |
| [FIX-0054](#fix-0054) | 2026-10-20 | Defer the shared library and assign current fixes to OS or agent |
| [FIX-0055](#fix-0055) | 2026-10-20 | Implement OS context and output recovery; final verification pending |
| [FIX-0056](#fix-0056) | 2026-10-20 | Consolidate exported OS settings and coding configuration |
| [FIX-0057](#fix-0057) | 2026-10-20 | Preserve interrupted coding edits and improve scope/evidence handling |
| [FIX-0058](#fix-0058) | 2026-10-20 | Complete OS I/O safety and compaction verification |
| [FIX-0059](#fix-0059) | 2026-10-20 | Finish the unified OS settings reference and grouped validation |
| [FIX-0060](#fix-0060) | 2026-10-20 | Verify interrupted-source handoff and consecutive correction policy |
| [FIX-0061](#fix-0061) | 2026-10-20 | Research concurrent Claude requests for local inference simulation |
| [FIX-0062](#fix-0062) | 2026-10-20 | Inspect UI memory visibility and propose an OS context drawer |
| [FIX-0063](#fix-0063) | 2026-10-20 | Design a launch-scoped UI batch simulation flag |
| [FIX-0064](#fix-0064) | 2026-10-20 | Design OS memory and effective-context inspection for this version |
| [FIX-0065](#fix-0065) | 2026-10-20 | Clarify Codex proxy authentication and plan usage |
| [FIX-0066](#fix-0066) | 2026-10-20 | Audit current memory implementation and management ownership |
| [FIX-0067](#fix-0067) | 2026-10-20 | Trace coding-agent concurrency and OS admission ownership |
| [FIX-0068](#fix-0068) | 2026-10-20 | Analyze an interrupted native inventory repair and retained progress |
| [FIX-0069](#fix-0069) | 2026-10-20 | Assess single-thread compatibility and find inconsistent worker-cap routing |
| [FIX-0070](#fix-0070) | 2026-10-20 | Measure historical memory pressure and OS context interventions |
| [FIX-0071](#fix-0071) | 2026-10-20 | Record a current-version OS concurrency and deadlock audit |
| [FIX-0072](#fix-0072) | 2026-10-20 | Align current OS and agent documentation with justified revisions |
| [FIX-0073](#fix-0073) | 2026-10-20 | Record automatic and explicit memory management for this version |
| [FIX-0074](#fix-0074) | 2026-10-20 | Confirm the current UI setting for two Claude requests |
| [FIX-0075](#fix-0075) | 2026-10-20 | Raise Haiku generation and OS output limits to 32k |
| [FIX-0076](#fix-0076) | 2026-10-20 | Triple the UI and mixed-example sprint allowance |
| [FIX-0077](#fix-0077) | 2026-10-20 | Analyze the first two-slot run and record recovery/concurrency findings |
| [FIX-0078](#fix-0078) | 2026-10-20 | Locate and summarize the current-version implementation tracker |
| [FIX-0079](#fix-0079) | 2026-10-20 | Assess evidence, implementation readiness and ownership of seven backlog items |
| [FIX-0080](#fix-0080) | 2026-10-20 | Add concise module docs and a complete human/agent navigation tree |
| [FIX-0081](#fix-0081) | 2026-10-21 | Reassess unfinished older backlog items against current implementation |
| [FIX-0082](#fix-0082) | 2026-10-21 | Preserve a tested current-version checkpoint and schedule sequential fixes |
| [FIX-0083](#fix-0083) | 2026-10-21 | Wait at the effective coding-worker capacity |
| [FIX-0084](#fix-0084) | 2026-10-21 | Retain cancelled development starts in accounting and allocation |
| [FIX-0085](#fix-0085) | 2026-10-21 | Preserve caller grammar in generic output recovery |
| [FIX-0086](#fix-0086) | 2026-10-21 | Separate setup prerequisites from final product acceptance |
| [FIX-0085](#fix-0085) | 2026-10-21 | Record future learned routing and quota-aware task scheduling |


## Entry template

Copy this template, assign the next ID, and add its index row. Replace every
placeholder. Link earlier entries for related or recurring problems.

```markdown
<a id="fix-NNNN"></a>
## FIX-NNNN — YYYY-MM-DD — Descriptive title

Status: implemented / investigated / reverted / superseded
Related history: earlier fix IDs or detailed investigation links, if applicable.

### Problem
Observed behavior, trigger, and impact.

### What was wrong
Root cause, faulty assumption, and responsible layer. Mark hypotheses as such.

### How it was fixed
Concrete changes and affected paths. For investigation-only work, state that no
implementation changed and describe what was established or remains open.

### Design principle enforced or reconstructed
The general rule restored by the edit and why it belongs in this layer.

### Verification
Checks actually performed, results, evidence, and limits. Identify historical
results separately. For a recurrence, explain the added regression coverage.
```

<a id="fix-0001"></a>
## FIX-0001 — 2026-10-19 — Start a selected project inside an enclosing repository

Status: implemented.
Related history: [in-place repository implementation](current-iter-issues.md#in-place-coding-repositories--2026-10-19)
and [runtime/agent boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md#in-place-coding-repositories).

Historical cross-reference added during backfill: [FIX-0017](#fix-0017) records
the earlier request and implementation to relax missing-folder startup.
[FIX-0040](#fix-0040) later changed repository providers and exposed this distinct
enclosing-root guard. Preserve the earlier setup invariant across provider changes;
the nested-project regression here covers the gap that the earlier tests missed.

### Problem

A run for `/home/mawa/projects/testing/minecraft-v9` stopped immediately with
`Choose the actual repository root: /home/mawa/projects/testing`. The selected
project had no local Git repository, and no setup engineer received the objective.

### What was wrong

The coding agent treated the result of `git rev-parse --show-toplevel` as a
requirement on the selected directory. Git discovers enclosing repositories, so
a legitimate new project inside an existing checkout was rejected. The same
discovery could also supply an unrelated parent branch or commit as its baseline.
This was coding-agent repository policy, not an OS execution failure.

### How it was fixed

[agent/repository.py](../src/polyinference/agent/repository.py) treats a different
enclosing root as context, initializes Git at the selected project path, and
records a startup note for the setup engineer. It does not inherit the enclosing
repository's HEAD or branch. The common Git-directory lease is acquired for the
selected project's actual repository rather than for its enclosing repository.
The existing root, branch, and index preservation checks still protect integration.

### Design principle enforced or reconstructed

The user's selected project directory defines the coding application's project
boundary. Ambient Git discovery must not replace that choice. The coding agent
owns initialization and baseline policy; the OS supplies generic execution,
directory authority, and resource coordination. A general agent must not need
Git or a coding workspace to run.

### Verification

`test_fresh_project_setup_writes_and_commits_at_requested_path` in
[test_in_place_repository.py](../tests/test_in_place_repository.py) covers new
projects both outside and inside another repository. It verifies setup reaches
the engineer, the requested `pi-dev` branch and project files exist locally,
parent files are absent from the new history, and the parent's HEAD and branch
are unchanged. See the shared verification record below. This reproduces the
directory trigger using disposable repositories; no live game-building run was
performed.

<a id="fix-0002"></a>
## FIX-0002 — 2026-10-19 — Let the coding agent correct recoverable Git setup errors

Status: implemented.
Related history: [FIX-0001](#fix-0001) and
[earlier agent/OS separation](current-iter-issues.md#coding-policy-separated-from-the-existing-os-functions--2026-10-19).

### Problem

An existing branch name, a missing requested branch, or an invalid Git policy
could stop startup before development. A policy attention note could also reject
ordinary local development instead of reaching the setup engineer.

### What was wrong

The coding agent applied its initial policy once and treated validation or Git
command errors as terminal. The reasoning agent had no correction turn containing
the failed selection and the available local branches. The application also
raised immediately on the policy's `blocker` field.

### How it was fixed

[agent/repository.py](../src/polyinference/agent/repository.py) observes local
branches and sends recoverable policy/branch errors back to the senior process.
Correction requests include `setup_error` and, when available, the previous
policy. Startup permits up to three policy/setup attempts with distinct durable
request identities. The successful policy becomes the run's recorded policy.
Attention notes are retained under `coding/startup-notes` and supplied to setup
through [agent/services.py](../src/polyinference/agent/services.py).

### Design principle enforced or reconstructed

Recoverable application failures are inputs to the responsible agent's decision
loop. Retry policy and Git choices belong to the coding agent, using generic OS
capabilities and records. Recovery is bounded and preserves explicit user
constraints. It does not grant forbidden actions or weaken protection of existing
edits, an active Git operation, or uncertain execution.

### Verification

`test_repository_setup_sends_recoverable_errors_back_to_agent` covers branch
collisions, missing branches, and invalid policy. It verifies the agent receives
the failure and branch observations and selects a working policy.
`test_policy_attention_note_reaches_setup_instead_of_rejecting_start` verifies
an attention note does not reject startup. Both are in
[test_in_place_repository.py](../tests/test_in_place_repository.py). See the
shared verification record below. Exhausting correction attempts or encountering
a data-preservation/authority condition can still stop a run.

<a id="fix-0003"></a>
## FIX-0003 — 2026-10-19 — Let the coding agent repair failed dependency preparation

Status: implemented.
Related history: [FIX-0002](#fix-0002) and
[dependency preparation ownership](../design-docs/simplified-os/RUNTIME_BOUNDARY.md#in-place-coding-repositories).

### Problem

A failed prerequisite command could interrupt a worker before configured checks
and assessment, preventing the agent from diagnosing and repairing its setup.

### What was wrong

The coding agent raised a runtime exception when automatic dependency preparation
failed. This conflated a known unsuccessful prerequisite command with an inability
to continue execution. Its output did not reach the engineer as a repairable
observation.

### How it was fixed

[agent/repository.py](../src/polyinference/agent/repository.py) retains failed
preparation output in `coding/dependencies/<workspace>` and allows configured
checks to run. [agent/services.py](../src/polyinference/agent/services.py) supplies
each worker with preparation issues for its own workspace and supplies the senior
with the broader diagnostic view. [agent/prompts.py](../src/polyinference/agent/prompts.py)
directs engineers to repair prerequisites and request rechecks. Failed preparation
is retried on later check attempts; successful preparation clears the active
diagnostic. Unknown execution termination still stops further mutation.

### Design principle enforced or reconstructed

Keep execution facts separate from application judgments. The OS enforces grants,
executes commands, and retains outcomes; the coding agent chooses dependencies,
repair work, and acceptance policy. A failed setup command is evidence for repair,
not proof that useful work is impossible. Continuing must not manufacture passing
check evidence or allow one worker's environment error to redirect another worker.

### Verification

`test_failed_dependency_preparation_reaches_agent_and_can_be_retried` in
[test_in_place_repository.py](../tests/test_in_place_repository.py) exercises a
failed prerequisite and failed check, agent-directed shell repair, a repair/recheck
cycle, task completion, and cleared diagnostics. It also checks that unrelated
workspaces do not receive the issue. See the shared verification record below.
These are local scripted-agent tests; package-manager network installation was
not validated.

### Shared verification for FIX-0001 through FIX-0003

Performed during the implementation in this chat, before the documentation-only
FIX-0004 task:

- **79 passed:** `.venv-linux/bin/python -m pytest tests/test_in_place_repository.py tests/test_setup_tools.py tests/test_capability_boundary.py tests/test_ui.py tests/test_user_briefs.py -q`.
- **2 passed:** `.venv-linux/bin/python -m pytest tests/test_runtime_general.py -q`.
  These verify non-coding agents can finish without Git, coding tasks, or a file
  workspace.
- **1 focused check passed** after the final workspace-diagnostic scoping edit:
  `.venv-linux/bin/python -m pytest tests/test_in_place_repository.py::test_failed_dependency_preparation_reaches_agent_and_can_be_retried -q`.
- Ruff passed for the three changed agent modules and the repository regression
  file. `git diff --check` passed with the existing CRLF normalization notice for
  `tests/test_setup_tools.py`.

The fix added no OS runtime code, OS configuration field, wire contract, or
coding-specific runtime hook. Existing general capability and non-coding agent
tests were used to check that boundary. These results are targeted verification,
not a claim that the complete repository test suite or live providers were run.

<a id="fix-0004"></a>
## FIX-0004 — 2026-10-19 — Require agents to read and maintain a durable fix history

Status: implemented.
Related history: [FIX-0001](#fix-0001), [FIX-0002](#fix-0002), and
[FIX-0003](#fix-0003).

### Problem

The user recalled requesting a similar fix previously and wanted subsequent
agents to retain both the implementation history and the design ideas behind it.

### What was wrong

Detailed investigations existed in development notes, but no root `AGENTS.md`
required agents to read them before starting or to record each fix consistently.
There was no required structure separating symptoms, causes, implementation, and
design principles, or requiring recurring problems to be linked to earlier fixes.
This gap made prior reasoning easier to miss; it does not prove the cause of a
particular earlier regression.

### How it was fixed

Added [AGENTS.md](../AGENTS.md) requiring agents to read this history before work,
review the boundary guide for agent/OS changes, pass these requirements to any
delegated agents, and update the history before finishing. Established this file
with stable IDs, an entry template, recurrence and verification rules, and records
of the fixes from this chat. Linked it from [README.md](../README.md) and
[current-iter-issues.md](current-iter-issues.md) so the existing reading routes
lead here.

### Design principle enforced or reconstructed

Preserve why a fix exists alongside what changed. Repository maintenance needs a
shared, discoverable history and explicit ownership of keeping it current.
Recurring defects should refine the explanation and regression coverage instead
of accumulating disconnected patches or silently erasing prior decisions.

### Verification

Documentation-only change. Checked the required reading/update instructions,
entry structure, index anchors, relative links, and patch whitespace. No runtime
behavior changed and no implementation tests were rerun for this documentation
task. Earlier implementation results are recorded separately above.

<a id="fix-0005"></a>

## FIX-0005 — 2026-10-16 — Preserve the editable graph while clarifying views and labels

Status: Implemented in design artifacts; not runtime behavior.
Source: [Refine polyinference agent graph](CHAT_HISTORY.md#chat-01)

### Problem

The early agent diagram combined workflow states, crowded arrows with labels and group boxes, and left detailed views inconsistent with the user's edited full architecture.

### What was wrong

Presentation revisions mixed changes to the diagram's meaning with changes to the editor. Secondary views and movable labels did not consistently preserve the user's chosen layout.

### How it was fixed

Refined the existing `references/docs/polyinference-agent-v1.html` and `polyinference-agent-v1-1.html` in place. Updated cloud, local, and recovery views from the approved full architecture; added an independent edge-free memory view; made pipeline labels draggable with separate saved positions and undo/redo; removed the oversized banner.

### Design principle enforced or reconstructed

Keep the author's design authoritative and preserve editing controls while improving its representation. Derived views must reflect the same workflow without silently changing the source view.

### Verification

Historical chat reports offline graph checks passed and all five tabs remained usable. Some local-file browser previews were blocked; those turns did not establish full visual/download correctness.

<a id="fix-0006"></a>

## FIX-0006 — 2026-10-17 — Recover graph information lost across design versions

Status: Implemented in design artifacts.
Source: [Merge agent graph designs](CHAT_HISTORY.md#chat-04)

### Problem

The AI-generated execution graph had useful connections, while the user's version had the preferred node layout and memory model. Versioning had lost information between them.

### What was wrong

Neither revision alone preserved all required content. A wholesale replacement would have discarded approved layout or memory relationships.

### How it was fixed

Merged execution descriptions and connections while preserving the user's node names and positions and keeping the memory model byte-for-byte unchanged. Repository provenance is in [merged-agent-design-notes.md](../design-docs/polyinference-design/merged-agent-design-notes.md) and the adjacent merged HTML/JSON.

### Design principle enforced or reconstructed

Reconcile versions by explicit ownership of each part of the design. Preserve approved content and provenance rather than treating a generated revision as automatically authoritative.

### Verification

Historical record reports 23 nodes, 57 arrows, preserved memory bytes, and layout/routing checks. Browser interaction testing was blocked; no runtime implementation was verified.

<a id="fix-0007"></a>

## FIX-0007 — 2026-10-17 — Define portable contracts and close agent/OS handoff gaps

Status: Implemented in design documents and validators; runtime followed later.
Source: [Design OS-independent LangGraph](CHAT_HISTORY.md#chat-03); [Audit OS and agent designs](CHAT_HISTORY.md#chat-05)

### Problem

The approved graph, merged execution graph, agent proposal, and OS proposal disagreed about publication, review, restart, authority, and completion.

### What was wrong

Missing cross-layer invariants permitted stale-plan publication, incorrectly attributed resumed deltas, deadlocked capacity, fake worker reports for senior reverts, and inconsistent steering/evidence semantics.

### How it was fixed

Updated the LangGraph and simplified-OS designs, typed contracts, examples, and semantic validators. Adopted the merged graph's contract-2.0 baseline, then added review/acceptance barriers, attributable resume, explicit publication receipts, separate worker/control capacity, scoped delta rules, subordinate callbacks, and feasible static role maps. See [INTEGRATION_AUDIT.md](../design-docs/INTEGRATION_AUDIT.md).

### Design principle enforced or reconstructed

An agent owns workflow and success judgments; the OS owns execution guarantees and resource mechanisms. Encode the handoff invariants explicitly, using public LangGraph interfaces rather than a framework fork.

### Verification

Historical design validation progressed from 35 example records/29 rejected combinations to 76 invalid combinations rejected and 159 graph routes checked. These results validate design artifacts, not a running OS. Earlier proposal choices were superseded by the merged graph and later runtime decisions.

<a id="fix-0008"></a>

## FIX-0008 — 2026-10-17 — Make design review inspectable and keep translations as data

Status: Implemented in design-reader artifacts.
Source: [Audit OS and agent designs](CHAT_HISTORY.md#chat-05)

### Problem

Scattered designs were hard to review visually, and the English/Mandarin implementation initially duplicated content in language-specific Python modules.

### What was wrong

The review surface lacked an interactive reading route, and translation data was coupled to duplicated implementation files.

### How it was fixed

Added interactive `design-docs/visuals/agent-design.html` and `os-design.html`, diagrams, scenarios, review-note export, printing, and responsive styles. Added an English/Simplified-Chinese switch preserving selections/notes, then replaced `content_zh.py` and `ui_zh.py` with `zh-CN.json` and rebuilt both readers.

### Design principle enforced or reconstructed

Make architecture review accessible without altering its semantics. Localize content as data over shared behavior instead of maintaining parallel code implementations.

### Verification

Historical initial readers were browser-checked at desktop/phone widths. Later translation/build/JavaScript checks passed; the bilingual visual preview was blocked by local-file policy. Those are separate verification scopes.

<a id="fix-0009"></a>

## FIX-0009 — 2026-10-17 — Build the agent against replaceable runtime and provider interfaces

Status: Implemented; original placeholder runtime later expanded.
Source: [Build LangGraph agent](CHAT_HISTORY.md#chat-06); [Connect LangGraph to ChatGPT](CHAT_HISTORY.md#chat-02)

### Problem

The designs needed an executable agent without coupling its graph to a particular OS implementation or treating an agentic Codex job as a plain model call.

### What was wrong

There was no implemented portable process/query/effect boundary or complete provider path for testing the planned graphs.

### How it was fixed

Implemented deterministic controller, senior-query, and reusable worker graphs over runtime ports, with OpenAI/Gemini/local-model adapters and brokered Codex jobs. Added Anthropic support afterward and documented setup in [PROVIDER_SETUP.md](../design-docs/implementation/PROVIDER_SETUP.md). The earlier proxy brief was research/documentation, not proof that a third-party proxy was installed.

### Design principle enforced or reconstructed

Separate orchestration from execution and distinguish raw inference from an agent runtime with its own tools. Keep credentials external to source/configuration values.

### Verification

Historical initial implementation reported 47 tests plus design/source checks. Provider follow-up reported 64 tests and a real disposable Codex coding task. Live Anthropic access initially returned 401 for the supplied placeholder and was explicitly not claimed as working in that setup turn.

<a id="fix-0010"></a>

## FIX-0010 — 2026-10-17 — Expose run processes, project selection, exports, costs, and steering

Status: Implemented; monitor layout later superseded by FIX-0037.
Source: [Build LangGraph agent](CHAT_HISTORY.md#chat-06)

### Problem

Testing required inspecting internal state, and users lacked a simple way to choose a project, inspect node prompts/results, save diagnostics, or steer a running objective.

### What was wrong

The first backend implementation had no adequate user-facing run/inspection controls.

### How it was fixed

Added a loopback test UI with fresh-run selection, process/node detail inspection, repository input and folder picker, JSON process export, approximate provider costs, and atomic steering ingress. Expanded README setup/testing instructions.

### Design principle enforced or reconstructed

Expose durable execution evidence and effective run inputs through a small inspection interface. User steering must enter through the same recorded authority path as CLI updates.

### Verification

Historical UI foundation reported 68 passing tests and a live Codex UI run; project/export/cost/steering follow-up reported 77 tests and browser checks. These counts belong to those revisions, not today's code.

<a id="fix-0011"></a>

## FIX-0011 — 2026-10-17 — Correct worker bindings and short demonstration budgets

Status: Implemented as coding-application defaults.
Source: [Build LangGraph agent](CHAT_HISTORY.md#chat-06); [Configure OS models](CHAT_HISTORY.md#chat-07)

### Problem

The Haiku cost remained zero because both nominal local/cloud lanes actually used Codex, and the three-sprint greeting-demo allowance stopped larger tasks early.

### What was wrong

Lane names were mistaken for provider identities, and demonstration routing/limits were being used for general development.

### How it was fixed

Routed junior workers to Anthropic Haiku and seniors to Codex, increased the UI sprint limit from 3 to 9 and associated senior-query allowance from 9 to 27, and updated mixed-provider defaults. A later explicit user request changed Codex reasoning from medium to low.

### Design principle enforced or reconstructed

Treat provider bindings and budgets as explicit application configuration. Diagnose effective routing from recorded backend identity; do not change cost counters to conceal an unused provider.

### Verification

Historical routing/budget change reported 78 tests, including completion beyond the old cap. Subsequent model-default updates are configuration changes, not a guarantee of account model availability. No historical quota percentage is recorded here as current.

<a id="fix-0012"></a>

## FIX-0012 — 2026-10-17 — Give setup and senior coders the tools needed for prerequisite work

Status: Implemented; Git location policy later superseded by FIX-0040.
Source: [Build LangGraph agent](CHAT_HISTORY.md#chat-06)

### Problem

Runs needed Git initialization, user-requested branch/prerequisite handling, and some senior coding work before ordinary development could proceed.

### What was wrong

Cloud management queries did not provide the same bounded file/check/shell execution interface as junior coding workers, and setup/allocation were incomplete.

### How it was fixed

Added the first cloud setup pass using the ordinary worker protocol, branch selection and optional structured base branch, shared bounded tools for cloud coding, and a cumulative approximately 10% senior/90% junior development allocation excluding setup/management. Relevant coverage remains in `tests/test_setup_tools.py`.

### Design principle enforced or reconstructed

Separate management reasoning from executable coding assignments, but use the same granted tool boundary for every engineer. User Git instructions outrank application defaults.

### Verification

Historical record reports 86 tests and a live Codex branch-and-shell setup check. That revision used private Git; FIX-0040 changed the default repository layout. Do not copy the old private-repository behavior into a new OS requirement.

<a id="fix-0013"></a>

## FIX-0013 — 2026-10-17 — Load saved provider credentials without executing environment files

Status: Implemented.
Source: [Configure OS models](CHAT_HISTORY.md#chat-07)

### Problem

The user had saved an Anthropic key file, but new application launches checked only inherited shell variables and did not load it automatically.

### What was wrong

Credential setup instructions and application startup behavior were inconsistent.

### How it was fixed

Added startup loading of `~/.config/polyinference/anthropic.env` in `cli.py`, with existing environment values taking precedence, and updated README plus `tests/test_saved_credentials.py`. File parsing accepts assignments rather than executing shell code; repository `.env` files are not automatically loaded.

### Design principle enforced or reconstructed

Make credential sourcing explicit, predictable, and separate from project-controlled source. Never put credentials or their pasted values into a fix history.

### Verification

Historical follow-up reports six credential-loading checks passed. This documentation backfill did not read, copy, replace, or revalidate any credential.

<a id="fix-0014"></a>

## FIX-0014 — 2026-10-17 — Capture OS inspection evidence in live and saved views

Status: Implemented; visible layout later superseded by FIX-0037.
Source: [Configure OS models](CHAT_HISTORY.md#chat-07); [Inspect frontend save data](CHAT_HISTORY.md#chat-09)

### Problem

The viewer omitted scheduling, reservations, critical-section ownership, cancellation, and retained execution details; Save needed to preserve the same evidence.

### What was wrong

The original UI exposed process/node output without a complete OS-state projection or shared comprehensive snapshot.

### How it was fixed

Added OS inspection projections for kernel/process/admission/resource/workspace records, durable timing/history data, and comprehensive JSON export/reopen using retained records, events, effects, artifacts, and checkpoints. `ui_os.py` and `snapshots.py` retain these responsibilities.

### Design principle enforced or reconstructed

Inspection must report recorded OS facts and distinguish live, retained, missing, and pruned data. A diagnostic export is not automatically a restorable repository backup.

### Verification

Historical implementation reported 111 tests, lint/JavaScript checks, and browser save/reopen verification. The separate save-data inspection changed no code and explicitly noted capture-time consistency limits and that private Git objects were not embedded.

<a id="fix-0015"></a>

## FIX-0015 — 2026-10-18 — Keep generated projects and runtime history out of version control

Status: Implemented.
Source: [Build LangGraph agent](CHAT_HISTORY.md#chat-06); [Add rolling runtime history](CHAT_HISTORY.md#chat-08)

### Problem

Disposable agent-built projects and automatically generated runtime/history files could clutter staging or enter commits.

### What was wrong

Ignore coverage did not explicitly include the requested testing-project location and custom/nested history archives.

### How it was fixed

Updated `.gitignore` for `/testing/`, runtime state, and rolling-history paths, including custom archive directories. Kept the real `tests/` suite tracked and eligible for changes.

### Design principle enforced or reconstructed

Version source and intentional artifacts, not transient executions, credentials, or disposable generated projects. Ignore rules are version-control hygiene, not an authority boundary for source edits.

### Verification

Historical chats report ignore-rule checks, no history files tracked, and a staging dry run excluding disposable locations. They did not authorize staging or committing later work.

<a id="fix-0016"></a>

## FIX-0016 — 2026-10-18 — Use one serializer for manual save and rolling run archives

Status: Implemented.
Source: [Add rolling runtime history](CHAT_HISTORY.md#chat-08)

### Problem

Persistent runtime databases existed, but there was no automatic rolling diagnostic archive shared with the frontend's Save format.

### What was wrong

Manual export and runtime completion had no common archive lifecycle or 30-day retention cleanup.

### How it was fixed

Added `history.py` archives for UI/CLI completions, failures, and resumes using the same snapshot serializer as manual Save. Completion prunes archive snapshots older than 30 days; recovery databases and manual downloads have independent lifetimes.

### Design principle enforced or reconstructed

Share the serialization path to prevent export drift. Prune only the explicitly managed diagnostic archive, preserving operational recovery state.

### Verification

Historical record reports 118 passing tests plus lint and whitespace checks, with coverage in `tests/test_history.py`. The earlier interrupted request was not counted as a second completed implementation.

<a id="fix-0017"></a>

## FIX-0017 — 2026-10-18 — Relax the existing-directory prerequisite for starting a project

Status: Implemented historically; related startup regression addressed by FIX-0001.
Source: [Add rolling runtime history](CHAT_HISTORY.md#chat-08)

### Problem

Startup already handled Git setup, but required the input directory to exist before the agent could begin. The UI picker also rejected a new directory.

### What was wrong

Filesystem/UI preconditions ran before setup, preventing the setup stage from doing the work it was meant to handle.

### How it was fixed

Allowed nonexistent paths in UI/CLI, created missing directories/parents when setup is enabled, initialized private Git in that revision, and passed the full objective/path to the first setup engineer. Setup completion persists on resume; `prepare_repository: false` is an explicit opt-out.

### Design principle enforced or reconstructed

A setup stage must receive underspecified but recoverable project input instead of demanding all prerequisites first. The responsible agent owns setup policy.

### Verification

Historical record reports 122 regression tests plus four targeted startup/UI checks. This covered missing/plain directories in the legacy private-copy path. It did not cover a later in-place provider discovering an enclosing repository; FIX-0040 introduced that provider and FIX-0001 adds that missing nested-project regression.

<a id="fix-0018"></a>

## FIX-0018 — 2026-10-18 — Make successful and failed launches visible and exportable

Status: Implemented.
Source: [Add rolling runtime history](CHAT_HISTORY.md#chat-08)

### Problem

Clicking Start run appeared to do nothing. A blank check rejected launch, polling erased the error, and failed startup had no useful selected process/run to save.

### What was wrong

UI selection and error lifetime were not tied to launch identity, and diagnostics assumed an agent had initialized.

### How it was fixed

Select a newly started run immediately. Assign run/process IDs to rejected startups, retain submitted inputs and exact errors, keep the failed run selected, and include it in Save even when no agent nodes ran. Changes span `ui.py`, `ui.html`, `history.py`, and `snapshots.py`.

### Design principle enforced or reconstructed

Failure to launch is still an observable execution outcome. Preserve identity and diagnostics independently of how far the application got.

### Verification

Historical record reports 126 tests passed, one skipped, and four JavaScript checks run separately. The blocking check requirement itself was subsequently relaxed in FIX-0019; visibility remains useful for genuine launch failures.

<a id="fix-0019"></a>

## FIX-0019 — 2026-10-18 — Let the coding agent discover an omitted check command

Status: Implemented; policy ownership later clarified by FIX-0032.
Source: [Improve testing context inference](CHAT_HISTORY.md#chat-11)

### Problem

The UI demanded a check command that the AI agent could infer from the user's objective or project, including a new project.

### What was wrong

Launch/configuration treated missing check input as an unrecoverable validation error rather than a setup responsibility.

### How it was fixed

Made the check field optional when setup can discover checks. The setup engineer chooses a meaningful command from user requirements/manifests, registers it, and retains the selection for subsequent verification/resume. Missing checks still cannot establish success.

### Design principle enforced or reconstructed

Ask the agent to resolve recoverable missing information while retaining evidence requirements. Check selection and product acceptance are coding-application policy, not universal OS prerequisites.

### Verification

Historical source reports regression tests and lint passed without an exact count. Existing setup tests cover automatic check selection and refusal to publish success with missing checks. This does not resolve the separate prerequisite-versus-final-acceptance gap listed in the source audit.

<a id="fix-0020"></a>

## FIX-0020 — 2026-10-18 — Report core run and task events in the UI server terminal

Status: Implemented; reporting resilience later strengthened by FIX-0029.
Source: [Show core UI task events](CHAT_HISTORY.md#chat-10)

### Problem

Launching `polyinference ui` gave little terminal indication of task progress or issues.

### What was wrong

Durable lifecycle changes were displayed in the browser but not projected into concise terminal events.

### How it was fixed

Added timestamped run/task starts, completion, interruption, issue, and error messages in `ui.py`, driven by recorded changes rather than a separate task state machine.

### Design principle enforced or reconstructed

Project the same recorded execution facts into each viewing surface. Keep a small reporting feature separate from workflow control.

### Verification

Historical source reports all 16 UI tests and lint passed. The later null-result/reporting incident showed why telemetry must also tolerate partial failure; FIX-0029 records that correction.

<a id="fix-0021"></a>

## FIX-0021 — 2026-10-18 — Deliver accepted artifacts instead of leaving results only in private state

Status: Implemented; default coding delivery later superseded by FIX-0040.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12)

### Problem

Users could not find output in the selected project even when accepted work existed in private run storage.

### What was wrong

Private workspace/commit publication did not itself copy an accepted result to a user-visible destination.

### How it was fixed

Added generic explicit artifact-file delivery with destination/baseline conflict checks, durable intent/receipt, and replay-safe recovery in `runtime/outputs.py`. The coding agent selected only finally accepted output: new projects used their selected folder; existing repositories defaulted to `STATE/result` in that revision.

### Design principle enforced or reconstructed

Execution artifacts and delivered results have separate lifecycles. The OS can deliver explicit files; the agent decides which result is acceptable. Delivery must preserve destination edits and never imply failed/private work was accepted.

### Verification

Historical implementation reported 157 tests passed/one skipped, with five frontend checks passing separately on Node 22. `test_outputs.py` and incident tests cover conflicts, binary/mode preservation, replay, interrupted delivery, and new steering. In-place coding now integrates directly; the delivery capability remains available for other workflows.

<a id="fix-0022"></a>

## FIX-0022 — 2026-10-18 — Allow processes to finish without code, Git, or coding reports

Status: Implemented in the runtime; further separation recorded in FIX-0032.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12)

### Problem

The runtime was intended for future non-coding agents, but coding configuration, cancellation/drain rules, and output expectations were mixed into its normal lifecycle.

### What was wrong

The first bundled application and placeholder runtime evolved together, leaving application assumptions on generic process paths.

### How it was fixed

Separated `RuntimeConfig` from coding `AgentConfig`, supported generic process registration/termination and caller-selected native protocols, and moved coding cancellation-drain policy into the application. Added HTTP/native artifact-only fixtures in `tests/test_runtime_general.py`.

### Design principle enforced or reconstructed

Successful process execution does not require writing code, producing a commit, or satisfying a coding task protocol. An optional workspace must remain optional throughout the call chain.

### Verification

Covered by the historically reported 157-pass suite and non-coding fixtures. This was an initial separation, not a claim that every coupling was already removed; the later audit and FIX-0032 document remaining hard-coded tool/grammar/publication assumptions.

<a id="fix-0023"></a>

## FIX-0023 — 2026-10-18 — Represent phase transitions as current host requests

Status: Implemented.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12); [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

Workers could write a candidate but every first reconciliation request failed with Anthropic HTTP 400.

### What was wrong

Historical assistant `candidate` messages were appended after the pinned current instructions, leaving the request ending with an assistant turn. The provider fixture accepted this unsupported framing, concealing the defect. The incident discarded the original provider error body, so its exact complaint remained inferred.

### How it was fixed

Added an explicit current host request after history for reconciliation/assessment and repair transitions, preserved message roles/trust, and tightened the Anthropic transport/integration fixtures to reject unsupported request shapes.

### Design principle enforced or reconstructed

A workflow state transition must become an explicit current request, rather than relying on stale assistant history. Provider adapters and tests must enforce real wire constraints without reclassifying untrusted data as instructions.

### Verification

Historical implementation's 157-pass suite included strict Anthropic and HTTP integration coverage. The documented incident reconstruction supports the diagnosis; it was not a recovered verbatim provider explanation.

<a id="fix-0024"></a>

## FIX-0024 — 2026-10-18 — Retain structured provider failure facts

Status: Implemented; further fault-scope generalization remains an audit follow-up.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12); [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

The stack reduced distinct provider failures to `Endpoint HTTP 400`, losing the information needed to diagnose them or select a safe recovery.

### What was wrong

Transport exceptions discarded bounded response details/request IDs, and failure paths did not preserve attempted backend identity or useful retry classification.

### How it was fixed

Retained sanitized error messages/categories, HTTP status, request IDs, attempted model/backend, and recovery metadata through inference, kernel settlement, exports, and agent handling.

### Design principle enforced or reconstructed

Adapters report facts and execution certainty; applications interpret them. Do not erase evidence, expose credentials, or infer that a missing successful-backend field means no request was submitted.

### Verification

Historical provider/incident coverage was included in the 157-pass suite. Later generalization analysis warned that a circuit grouping different request errors can block a healthy endpoint; this history does not mark that broader fault-scope redesign complete.

<a id="fix-0025"></a>

## FIX-0025 — 2026-10-18 — Preserve effective authority and full requirements through task handoffs

Status: Implemented; setup authority was further clarified in FIX-0032/FIX-0033.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12); [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

A project-wide game request repeatedly became README-only tasks, and one roadmap drifted from requested 2D gameplay to first-person rendering.

### What was wrong

Planning context exposed an initial path seed without its project-scope meaning, while workers received bounded assignments without the full user objective and correctly ordered updates.

### How it was fixed

Added effective `write_scope`/authority descriptions to planning and setup inputs, the original objective and pinned user amendments to worker requests, and prompts preserving product constraints. Kept individual worker grants bounded.

### Design principle enforced or reconstructed

A narrow assignment must not replace user intent, and a path seed must not masquerade as the full grant. Convey actual authority without weakening the OS's enforcement of that authority.

### Verification

Historical 157-pass suite included application-file creation/delivery and requirement-watermark regressions. Later 317-character interruption analysis found another setup-context gap, addressed by the capability/authority wiring recorded below.

<a id="fix-0026"></a>

## FIX-0026 — 2026-10-18 — Stop non-actionable planning and repeated known failures

Status: Implemented within the recorded basic runtime and agent.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12); [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

Renamed replacement tasks and rewritten memory kept the run cycling after repeated infrastructure failures and empty senior plans.

### What was wrong

The no-progress fingerprint counted narrative memory as progress, and stopped drivers/permanent failures did not reliably close dispatch and terminate the control loop.

### How it was fixed

Excluded rewritten memory from meaningful progress comparison, stopped non-actionable plans, paused on known model failures, drained started workers, detected stopped drivers, and added bounded permanent-failure protection plus queued-cancellation/deadline coverage.

### Design principle enforced or reconstructed

Distinguish new evidence from rewritten narration. Let the application choose recovery work while the OS bounds effects and residency. Respect already started workers' finish paths instead of tearing down their runtime.

### Verification

Historical 157-pass suite covered empty plans despite memory changes, stopped drivers, known-failure drain, queued cancellation, and non-coding deadlines. The later fault-scope audit remains relevant: request-specific errors should not be mistaken for a globally broken endpoint.

<a id="fix-0027"></a>

## FIX-0027 — 2026-10-18 — Recover a known failed model operation with a new linked intent

Status: Implemented.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12); [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

Resuming a failed model step replayed its durable failure; replacement tasks often repeated work instead of continuing the retained private edits.

### What was wrong

Immutable replay correctly deduplicated the old intent, but the application lacked an explicit way to request a distinct corrected attempt with provenance.

### How it was fixed

Added explicit linked `retry-model` recovery after confirmed termination, preserving workspace/trajectory and rebuilding phase state. Kept original requests/results immutable, bounded allowances and program pins, and atomically updated process/task/attempt/run activation. Added output-delivery retry and receipt recovery on its own path.

### Design principle enforced or reconstructed

Retry is a new authorized intent, not alteration of history. Execution certainty gates safe recovery, and idempotent replay must not silently resubmit a remote operation.

### Verification

Historical 157-pass suite covered known versus uncertain failure, retained edits, interruption between checkpoint preparation and activation, receipt recovery, and steering during delivery. Historical runs were not silently migrated.

<a id="fix-0028"></a>

## FIX-0028 — 2026-10-19 — Bound retained native telemetry without aborting healthy generation

Status: Implemented; initial verification limit later superseded.
Source: [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

A senior native job stopped after ordinary streaming traffic exceeded 2,000 events/4 MB before a terminal result.

### What was wrong

The adapter counted disposable text deltas against a fatal job limit alongside tool/lifecycle/terminal evidence and lost useful diagnostics on failure.

### How it was fixed

Bounded retained event data by discarding/coalescing expendable streaming deltas, while preserving final output, usage, callbacks, and terminal state. Added event-count/byte/recent-type diagnostics and transport cleanup coverage in `test_native_events.py` and endpoint tests.

### Design principle enforced or reconstructed

Lossy telemetry retention must not become loss of completion state or cause a healthy execution to fail. Preserve unknown-execution ownership until termination is established.

### Verification

Initial WSL tests were blocked by approval-service capacity; local/browser probes passed. Later output-limit work ran the Linux suite with 178 passed/one skipped, superseding that limitation. The older 'Linux unverified' reply describes the earlier point in time, not the final validation state.

<a id="fix-0029"></a>

## FIX-0029 — 2026-10-19 — Keep reporting failures from replacing execution outcomes

Status: Implemented.
Source: [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

The UI displayed a `NoneType` error as failed even though the durable run was paused for a native execution issue.

### What was wrong

Terminal logging called `.get` on a legitimate null operation result, and reporting exceptions could override the original run outcome/blocker.

### How it was fixed

Made uncertain-result access null-safe, isolated reporting failures, retained reporting diagnostics separately, and preferred durable run status/original errors in UI and exports. Updated logger, snapshot, UI, and browser regressions.

### Design principle enforced or reconstructed

Telemetry observes execution; it must not become a new control-plane failure that rewrites the outcome. Preserve the original diagnostic even if a secondary viewing surface breaks.

### Verification

Historical local logger/adapter probes and six browser checks passed initially. The later 178-pass/one-skipped Linux suite covered these regressions; preserve both stages of evidence rather than rewriting the initial limitation.

<a id="fix-0030"></a>

## FIX-0030 — 2026-10-19 — Recover bounded incomplete model output without executing partial JSON

Status: Implemented for eligible raw model queries.
Source: [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

An 8,000-token Haiku response cutoff paused the whole run and lost usage/stop details before a development write.

### What was wrong

Output exhaustion was treated as a generic terminal provider error rather than a classified, confirmed-stopped generation that the coding agent could adapt.

### How it was fixed

Normalized incomplete-generation facts across HTTP protocols, retained partial visible text/usage/limits without treating it as actionable output, and settled resource accounting. The coding agent creates bounded new linked requests with progressively smaller complete-response guidance, preserving budgets and final-phase reserve. Native jobs and uncertain execution do not inherit this automatic retry rule.

### Design principle enforced or reconstructed

The OS reports resource and completion facts; response decomposition belongs to the application. Valid-looking partial JSON is still incomplete and must never execute.

### Verification

Historical full suite: 178 passed, one skipped; all 11 output-limit cases rerun after the final guidance edit. Coverage includes thinking-only cutoffs, replay, exhaustion, accounting, and no partial tool execution. No live model cutoff was newly induced.

<a id="fix-0031"></a>

## FIX-0031 — 2026-10-19 — Keep tool home/cache housekeeping outside source authority

Status: Implemented; persistent process-owned tool state remains a separate follow-up.
Source: [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

An unsuccessful `npm test` generated `.npm` log/notifier files inside the private source tree, causing a false scope violation and pause.

### What was wrong

The command runner set HOME to the source workspace, then interpreted tool housekeeping as user-source edits.

### How it was fixed

Added `runtime/tool_environment.py` and routed checks/shell commands through isolated temporary home/cache directories outside source. Cleanup covers success, failure, timeout, cancellation, and unavailable executables; source changes still face normal scope enforcement.

### Design principle enforced or reconstructed

Source, execution environment, and disposable scratch have different lifetimes and authority. Isolate runtime housekeeping rather than hiding arbitrary source paths from enforcement.

### Verification

Historical Linux suite: 188 passed, including a real npm-without-manifest regression. Sandbox mount construction was checked, not a live bubblewrap execution. Later audit noted fresh HOME per command loses cross-command config; that process-owned lifetime redesign was not established as implemented.

<a id="fix-0032"></a>

## FIX-0032 — 2026-10-19 — Move coding grammar and policy out of generic OS dispatch

Status: Implemented for the current basic function set.
Source: [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

The earlier general-agent support still exposed fixed coding tools/reply grammar and read coding task/setup/publication records inside generic runtime decisions.

### What was wrong

Mechanisms and the bundled agent's application policy remained coupled at registration, grants, callback replay, publication, and lifecycle handoffs.

### How it was fixed

Added generic typed capability/protocol registration and explicit process/workspace grants. Moved check selection, reply grammar, verdict/publication rules, and management/cancellation policy into the calling agent. Persisted required publication-policy registration across restart, preserved non-workspace callback arguments, and enforced workspace preconditions before custom handlers. See [RUNTIME_BOUNDARY.md](../design-docs/simplified-os/RUNTIME_BOUNDARY.md).

### Design principle enforced or reconstructed

Like an OS syscall boundary, the runtime authenticates and executes granted operations without understanding the calling program's workflow. Other agents must not impersonate coding workers to use tools or finish.

### Verification

Historical full suite: 201 passed; 14 focused boundary/transition/UI cases also passed. Non-coding HTTP/native/custom-tool and workspace-none fixtures were included. Live providers and live bubblewrap were not freshly exercised; new ABI state was required, not silently migrated.

<a id="fix-0033"></a>

## FIX-0033 — 2026-10-19 — Validate agent lifecycle updates and preserve long diagnostic notes

Status: Implemented.
Source: [Explain why the process failed](CHAT_HISTORY.md#chat-13)

### Problem

Setup stored a 317-character explanation in a 256-character `TaskAttempt.stop_reason`; retiring that task later crashed before a valid replacement plan activated.

### What was wrong

Application `model_copy` updates bypassed validation, and prose diagnostics were put into a bounded reason-code field. Generic storage correctly did not validate the coding application's schema.

### How it was fixed

Introduced agent-owned validated attempt transitions, bounded reason codes, and full diagnostic artifacts linked by `polyinference/stop-detail`. Applied the boundary across park, exception, cancellation, retirement, publication, setup, and recovery; normalized old invalid records during retirement. Also exposed effective setup authority.

### Design principle enforced or reconstructed

Validate application state transitions where their semantics are known. Keep generic storage responsible for versions/atomicity and separate machine reason codes from human explanations.

### Verification

Historical 201-pass suite and `tests/test_agent_transitions.py` cover long notes, injected legacy-invalid records, replacement activation, retained diagnostics, and replay without duplicate activation. This fixes a family of writes, not only the observed string.

<a id="fix-0034"></a>

## FIX-0034 — 2026-10-19 — Separate declared build outputs from protected source

Status: Implemented.
Source: [Diagnose early agent pause](CHAT_HISTORY.md#chat-14)

### Problem

A successful Vite build produced `dist/` files that invalidated check evidence and exceeded the setup worker's source grant.

### What was wrong

Scanning used fixed exclusions and treated generated build files as source; project-wide permission did not make every generated file an assigned source edit.

### How it was fixed

Added declared check `output_paths` applied consistently to fingerprints, deltas, scope checks, and commits. Tracked/granted source takes precedence, declarations cannot cover existing source, and genuine source-changing checks remain inconclusive. Scope errors report offending paths/grants and allow bounded application repair.

### Design principle enforced or reconstructed

Distinguish execution output from source authority explicitly. `.gitignore` is not a capability boundary, and granting build output must not hide protected source.

### Verification

Historical full suite: 210 passed, two skipped; final affected tests: 58 passed including previously skipped npm/frontend checks. `tests/test_workspace_outputs.py` covers output exclusion and source precedence. Original paused state was preserved.

<a id="fix-0035"></a>

## FIX-0035 — 2026-10-19 — Preserve dependencies across workspace generations

Status: Implemented.
Source: [Diagnose early agent pause](CHAT_HISTORY.md#chat-14)

### Problem

Adding an authorized file or expanding a workspace view lost `node_modules`, producing later missing-Vite/module errors.

### What was wrong

New generations copied only the source snapshot, although installed dependencies are execution state deliberately excluded from source.

### How it was fixed

Retained private dependency state across grant/closure/setup/integration/abort views only when dependency manifests and locks match. Preserve internal executable links without shared mutable files, account for storage, invalidate on input changes, and retain source/dependency identity across reopening.

### Design principle enforced or reconstructed

Workspace authority changes should not accidentally destroy a compatible execution environment. Source snapshots and dependency environments need distinct identities and lifecycles.

### Verification

Historical 210-pass/two-skipped suite and subsequent 58 affected tests cover environment preservation and invalidation. Later in-place dependency preparation (FIX-0040) addresses fresh worker/review roots; FIX-0003 handles preparation failures as agent observations.

<a id="fix-0036"></a>

## FIX-0036 — 2026-10-19 — Verify native harness permissions and detect unbrokered edits

Status: Implemented.
Source: [Diagnose early agent pause](CHAT_HISTORY.md#chat-14)

### Problem

A native Codex harness could potentially edit files outside the host's recorded tool calls, even though raw inference APIs do not have that executor.

### What was wrong

Read-only policy was requested but not independently confirmed, prompts did not fully explain competing native tools, and there was no complete native-view mutation comparison.

### How it was fixed

Required returned read-only/no-network/never-approval policy before a turn, supplied a separate immutable native input view, required brokered tools in prompts, and checked input and observed source views before callbacks and after completion, including retired generations. Never copy the native view back to source.

### Design principle enforced or reconstructed

Authority depends on effective execution and observed effects, not prompt promises or 'local/cloud' labels. A model's allowed source path does not authorize bypassing the broker.

### Verification

Historical local app-server permission handshake sent no inference turn and confirmed the expected policy. Regression counts were 210 passed/two skipped then 58 affected passes. The incident's 19 callbacks matched 19 child effects, but the notes correctly avoid treating telemetry alone as proof that no direct edits happened.

<a id="fix-0037"></a>

## FIX-0037 — 2026-10-19 — Separate OS monitoring from agent task and review history

Status: Implemented.
Source: [Locate the UI task queue](CHAT_HISTORY.md#chat-15)

### Problem

The UI repeated runtime facts across three panels while hiding the task lifecycle and retained completed/resolved task details.

### What was wrong

Process execution, task verdict, and senior resolution were not projected as distinct concepts; users had to join raw records manually.

### How it was fixed

Added OS and Agents tabs, a persistent task/history table with separate execution/verdict/review state and notes, project acceptance, shared record drawers, and snapshot-aware projections in `ui_agents.py`, `ui_os.py`, `ui-monitor.js`, and `snapshots.py`. Prompt/steering controls were preserved.

### Design principle enforced or reconstructed

Present each layer's actual concepts without conflating process completion, successful assessment, senior acceptance, and project completion. Retained results must remain inspectable.

### Verification

Historical source reports 35 backend tests and 13 frontend checks passed, one skipped, plus browser checks using recorded runs. This was a viewer change, not a change to execution or acceptance policy.

<a id="fix-0038"></a>

## FIX-0038 — 2026-10-19 — Provide generic durable agent-to-user messages

Status: Implemented as an OS capability.
Source: [Add sprint updates and agent output](CHAT_HISTORY.md#chat-17)

### Problem

Agents needed to communicate with the user through both UI and terminal, including future non-coding programs.

### What was wrong

UI task-event logging was not an explicitly granted general message capability with durable delivery/replay semantics.

### How it was fixed

Added generic `user.notify`, persisted plain-text messages, exposed them in UI/snapshots and terminal during UI or CLI runs, and kept delivery replay-safe with terminal-failure handling. Coding progress content remains supplied by the application.

### Design principle enforced or reconstructed

The OS transports granted messages; it must not invent sprint semantics, commit claims, or a coding-only output grammar. Preserve user-visible content and avoid duplicate delivery on replay.

### Verification

Historical focused capability/user-brief/frontend checks and last-failed rerun passed, with lint. The inspected chat also records an initial failed full-suite run; it does not establish a fresh all-green full suite at that point. Later suites provide broader verification.

<a id="fix-0039"></a>

## FIX-0039 — 2026-10-19 — Request evidence-based sprint briefs and working-commit claims

Status: Implemented in the coding agent only.
Source: [Add sprint updates and agent output](CHAT_HISTORY.md#chat-17)

### Problem

Sprint-manager invocations did not consistently give the user progress or identify the latest commit actually vetted as working.

### What was wrong

The senior prompt/proposal/controller path lacked a required brief and an explicit rule separating a provisional commit from a verified working result.

### How it was fixed

Added required senior `user_brief` content, prior-brief context, and delivery through generic `user.notify` on every invocation. Prompts require a vetted commit hash or an explicit statement that none is verified, whether the work came from a junior or senior coder.

### Design principle enforced or reconstructed

The application owns progress meaning and evidence-backed claims; the OS only delivers the supplied message. A recorded commit is not automatically a working product.

### Verification

Historical focused user-brief/capability/frontend tests passed for both launch modes and saved views. See FIX-0038 for the full-suite limitation in that source chat; do not infer a clean complete-suite result from its final prose.

<a id="fix-0040"></a>

## FIX-0040 — 2026-10-19 — Work and integrate in the user's actual repository by default

Status: Implemented; nested-project startup regression corrected by FIX-0001.
Source: [Analyze latest run](CHAT_HISTORY.md#chat-16)

### Problem

Actual writes and commits existed only inside run storage, so the user could not locate ongoing work in the selected project. Replacement workers also struggled to reuse failed private candidates.

### What was wrong

The private bare-repository/copy-back model delayed project-visible integration, and failed-candidate source was not an ordinary reusable task baseline. Fresh independent check environments also lacked reproducible dependency preparation.

### How it was fixed

Added the coding agent's `RepositoryWorkspaces` provider for real integration/task branches and linked worktrees, verified root fast-forward integration, explicit instruction precedence/serial no-branch mode, failed-candidate handoff, dependency preparation, and repository summaries. The OS added generic attached-directory authority/locks and non-destructive scope failure behavior. Legacy isolated mode remains explicit.

### Design principle enforced or reconstructed

Keep the chosen project authoritative while preserving user files and provenance. The agent owns Git workflow; the OS provides optional directory/effect mechanisms that do not require other agent types to use Git.

### Verification

Historical source reports 248 passing tests followed by 27 native/boundary tests after a final guard change, using local fixtures. No live provider/npm-network validation was claimed. New state was required. The original 'choose actual repository root' precondition missed the earlier lax-start invariant; FIX-0017 and FIX-0001 record that recurrence.

<a id="fix-0041"></a>

## FIX-0041 — 2026-10-19 — Record remaining run-quality and generalization findings without calling them fixed

Status: Investigated; several findings remain open or only partly addressed.
Source: [Diagnose 2D Minecraft run](CHAT_HISTORY.md#chat-12); [Explain why the process failed](CHAT_HISTORY.md#chat-13); [Analyze latest run](CHAT_HISTORY.md#chat-16); [Expose Codex usage stats](CHAT_HISTORY.md#chat-18)

### Problem

Past reports combined proposed repairs with completed work, making it easy to assume prerequisite checks proved product completion or every analysis item had been implemented.

### What was wrong

The Minecraft traces exposed multiple independent faults and design gaps. Some were explicitly deferred; similar symptoms later had different causes, and task-specific output could remain unverified.

### How it was fixed

Recorded investigation results and follow-up status in the chat source audit and linked existing issue/run-analysis documents. No implementation was changed by this backfill. In-place integration and dependency preparation address some later-run findings, but do not prove playable gameplay, comprehensive final acceptance, general protocol-output recovery, or correct historical-start accounting.

### Design principle enforced or reconstructed

Separate observation, inference, proposal, implementation, and verification. Preserve unresolved work and changing diagnoses rather than retroactively turning an investigation into a successful fix.

### Verification

Cross-read the source chats and existing investigation documents. No live providers, gameplay run, account-quota implementation, new MCP platform, or shutdown-recovery implementation was performed. The source audit below records the specific unresolved and research-only items.

<a id="fix-0042"></a>

## FIX-0042 — 2026-10-19 — Backfill the fix ledger from past repository chats

Status: Implemented as documentation only.
Source: This chat, documentation backfill requested by the user.

### Problem

The initial ledger covered only the current chat and did not capture earlier fixes, design decisions, or the antecedent of the repeated startup requirement.

### What was wrong

Earlier work was distributed across chat histories and development notes rather than the required maintenance ledger.

### How it was fixed

Reviewed 20 prior repository-path chats and exhausted the older-turn cursors for the two long chats. Added FIX-0005 through FIX-0041, source-chat IDs/titles/dates, historical verification and supersession notes, and a coverage/open-findings audit in `CHAT_HISTORY.md`. Linked the missing-directory startup fix, later in-place migration, and nested-project repair.

### Design principle enforced or reconstructed

Maintenance history must be traceable to evidence and explain recurrence. Backfilled historical work is not newly executed code or newly repeated testing; source limitations and unresolved findings remain visible.

### Verification

Checked entry/index consistency, required sections, relative links/anchors, source coverage, and whitespace. Only documentation changed in this task. The supported recent-thread listing and archive inventory define the reviewed scope; this is not a claim to have searched inaccessible/deleted chats or all account history.

<a id="fix-0043"></a>

## FIX-0043 — 2026-10-19 — Diagnose a completed model response with no visible text

Status: investigated; implementation remains unchanged.
Related history: [FIX-0024](#fix-0024), [FIX-0026](#fix-0026),
[FIX-0027](#fix-0027), [FIX-0030](#fix-0030), [FIX-0041](#fix-0041).
Detailed evidence: [run d434799ad8e4 analysis](run-d434799ad8e4-analysis.md).

### Problem

The Minecraft v10 run paused with `Endpoint returned no text` on its first world
worker's ninth raw model query, after three successful source writes. An earlier
malformed reply had already been repaired successfully through validation feedback.

### What was wrong

The Anthropic adapter's normal-completion path extracted no nonblank text and
raised a plain `EndpointError`, losing the response ID, stop reason, content
summary, and usage. Generic kernel settlement retained only an error and attempted
backend. The coding agent automatically recovers token-cutoff results only, so
this error bypassed its two-recovery allowance and reached run-level pause.
The lost upstream details prevent distinguishing empty content, thinking-only
content, and whitespace; none is established as the original provider response.

### How it was fixed

No implementation changed. Added the linked investigation with the timeline,
owning layers, preserved-work locations, diagnostic limits, and proposed repair.
The snapshot retains three uncommitted files in the worker checkout; only setup
had been committed and build-checked. No world-task or final acceptance was run.

### Design principle enforced or reconstructed

Normalize and retain provider completion/usage facts in the transport and OS;
let the calling agent choose bounded recovery with a new linked intent after
known termination. Reject unusable output without discarding its evidence or
silently replaying a submitted call. FIX-0030 covers explicit output-token stops;
its thinking-only cutoff coverage does not cover an accepted completion with no
visible text. Existing empty-response transport coverage requires rejection, not
diagnostic preservation or agent recovery. This uncovered scope remains open.

### Verification

Parsed the supplied snapshot (1,629 retained events, 58 effects, one failed
effect); inspected contexts, task/run/configuration/repository evidence; matched
the current agent-module hash to its recorded graph digest. Five offline adapter
probes reproduced normal text, empty, thinking-only, whitespace, and token-cutoff
behavior using actual source and an in-memory transport stub. A source-extracted
agent recovery probe confirmed one execution followed by `ModelOperationFailure`
despite two configured recoveries. No live provider, game verification, run resume,
full repository suite, or implementation repair was performed. Documentation
structure, links, and whitespace were checked for these two added records.

<a id="fix-0044"></a>

## FIX-0044 — 2026-10-20 — Retain facts for unusable completed model responses

Status: implemented; focused verification passed; final full-suite review pending.
Related history: [FIX-0024](#fix-0024), [FIX-0030](#fix-0030),
[FIX-0043](#fix-0043). See the [pause audit](pause-retry-audit-2026-10-20.md)
and [handoff](HANDOFF-2026-10-20.md).

### Problem

An empty completed model response paused run d434799ad8e4 with no surviving
provider stop reason, response/request identity, content summary or usage.
Malformed JSON/shape and unexpected response content had similar evidence loss.

### What was wrong

The HTTP adapter raised a plain exception after receiving the response. Kernel
settlement retained rich output/usage only for token cutoffs and structured HTTP
rejections. FIX-0024/FIX-0030 therefore did not cover this completion trigger.

### How it was fixed

`runtime/inference.py` adds `ModelResponseError` with bounded normalized response
facts, IDs, stop/content types and usage, excluding hidden reasoning. It classifies
malformed/empty responses and unexpected content without executing it.
`runtime/kernel.py` retains the failed response, attempted/actual backend and
accounting facts. Unknown usage remains conservatively charged.

### Design principle enforced or reconstructed

The adapter/OS preserves execution facts and privacy independently of application
grammar. Rejecting unusable output must not erase the evidence needed to recover.
The coding agent still decides response decomposition and product acceptance.

### Verification

Included in the final **39-pass** focused run recorded below. New cases cover
four HTTP protocols on both bindings, thinking-only/blank and malformed replies,
unexpected tool content, retained accounting and absent hidden reasoning. No live
provider/original-run reproduction. Lint passed for changed code. Added-document
structure/links and effort-only patch whitespace were checked at handoff. See
FIX-0045 for the incomplete full-suite result.

<a id="fix-0045"></a>

## FIX-0045 — 2026-10-20 — Filter safe one-off model failures with durable OS retries

Status: implemented; focused verification passed; work stopped at user request
before final full-suite verification/review.
Related history: [FIX-0026](#fix-0026), [FIX-0027](#fix-0027),
[FIX-0028](#fix-0028), [FIX-0030](#fix-0030), [FIX-0032](#fix-0032),
[FIX-0036](#fix-0036), [FIX-0043](#fix-0043), [FIX-0044](#fix-0044).
Detailed inventory: [pause audit](pause-retry-audit-2026-10-20.md).
Remaining work: [handoff](HANDOFF-2026-10-20.md).

### Problem

One empty reply, temporary HTTP service/rate-limit failure, full inference queue,
or safe native terminal failure could reach the driver and pause the whole run.
Retryable flags did not provide OS backoff/retry behavior. All HTTP connection
errors also became uncertain, including known pre-submission failures.

### What was wrong

FIX-0026 correctly stopped endless replacement loops, and FIX-0027 added explicit
linked recovery after known termination. FIX-0030 added application adaptation for
token cutoffs. The intervening generic OS strategy for safely retryable one-off
failures was missing. Repeating a mutating/uncertain job would be a different bug.

### How it was fixed

New `runtime/model_retries.py` filters model results before escalation. Defaults
allow one extra safe attempt on either binding, with bounded exponential delay,
Retry-After, durable new identities, per-attempt charging/reservations and retained
outcomes. Concurrent/restarted/replayed calls follow the same recorded chain.
`config.py` exposes retry/wait bounds; `kernel.py` preserves normal authority,
cancellation, limits and finishing reserves and negotiates the retry feature.

`inference.py` distinguishes known-unsubmitted connect/pool/admission failures
from submitted disconnects, settling unsubmitted budget at zero. `codex.py` and
the kernel exclude permission/cancellation/mutation violations and native jobs
with any brokered effect from blind retries, checking native views on known
failure too. `agent/services.py` links an adaptive output retry to the actual
failed attempt after an OS retry. `tests/test_runtime.py` changes the known-stopped
native call-count expectation while preserving unknown-execution retention.
Current RUNTIME_BOUNDARY.md/RUNBOOK.md describe these explicitly requested rules;
core schemas and frozen proposals were not rewritten. New configuration needs
fresh state; no historical runs were migrated/resumed.

### Design principle enforced or reconstructed

The OS may filter transient inference faults using generic known-effect facts;
application grammar, coding work and output decomposition stay with the caller.
Each new submission is a distinct durable intent. Original per-attempt results
remain immutable; public model replay projects the retained effective attempt.
No retry can bypass grants, repeat uncertain/tool-bearing jobs, erase adverse
evidence, reset budgets or consume protected finishing reserves.

### Verification

Final focused run: **39 passed in 9.62 seconds**, covering 36 new retry cases,
the two native known/unknown cases and earlier explicit circuit recovery:
`.venv-linux/bin/python -m pytest tests/test_model_retries.py tests/test_runtime.py::test_native_terminal_failure_releases_resources_but_unknown_retains_them tests/test_incident_fixes.py::test_os_stops_repeated_permanent_failures_and_allows_explicit_recovery -q`.
Coverage includes both bindings/four HTTP protocols, restart during backoff,
exhaustion/replay/concurrency, Retry-After, cancellation/shutdown/deadlines,
token/spend/call/reserve bounds, native effects/policy/unbrokered mutation and
composition with FIX-0030. Lint passed for all changed code/test files.

The first full run reported **280 passed, two skipped, one failed**: the old
single-attempt assertion for a known-stopped native failure. Its corrected
expectation passes the final focused run. The second full run was deliberately
stopped at the user's request; no final full-suite success is claimed. Earlier
focused failures and their corrections are retained in the handoff/audit.
Documentation links/sections and effort-only patch whitespace were checked. No
live provider, game check, network installation, commit, push or run migration.

<a id="fix-0046"></a>

## FIX-0046 — 2026-10-20 — Scope permanent-failure containment to the request being repaired

Status: implemented; focused verification passed; final full-suite review pending.
Related history: [FIX-0024](#fix-0024), [FIX-0026](#fix-0026),
[FIX-0027](#fix-0027), [FIX-0041](#fix-0041), [FIX-0045](#fix-0045).

### Problem

Two different invalid inputs could accumulate in the same role/model/endpoint
bucket and prevent a later healthy request from being submitted.

### What was wrong

FIX-0026's permanent-failure protection scoped its counter to routing/phase/config
but omitted the request intent. The broader fault-scope issue was already noted
in FIX-0024/FIX-0041. Simply adding intent also initially left the old counter
blocked after explicit correction, which the existing regression caught.

### How it was fixed

`runtime/kernel.py` includes the pinned intent fingerprint in the circuit key;
successful explicit recovery clears the repaired original intent's counter.
`inference.py` reports fault scope. New and existing tests verify unrelated-input
independence, repeated-identical-input containment and explicit recovery/reset.

### Design principle enforced or reconstructed

An invalid caller input is not evidence that every operation at that endpoint is
broken. Contain equivalent failures without disabling healthy requests, and clear
only the failure evidence actually repaired. Preserve immutable original failures.

### Verification

The new input-isolation case and existing repeated-permanent-failure/explicit
recovery regression pass in FIX-0045's final 39-case run. Lint and added-record
documentation checks passed. Full-suite and live-provider limits are recorded
there and in the handoff; no global endpoint-health redesign is claimed.

<a id="fix-0047"></a>

## FIX-0047 — 2026-10-20 — Keep OS retries separate from application recovery allowances

Status: implemented and verified with the full local suite and focused regressions.
Related history: [FIX-0027](#fix-0027), [FIX-0030](#fix-0030),
[FIX-0044](#fix-0044), [FIX-0045](#fix-0045), [FIX-0046](#fix-0046).
Detailed inventory: [pause audit](pause-retry-audit-2026-10-20.md).
Resumption record: [handoff](HANDOFF-2026-10-20.md#resumed-work--2026-10-20).

### Problem

After the agent adapted a token-cutoff response, a one-off service error on that
new request could exhaust recovery allowance before the OS submitted its retry.
With a larger allowance, the same sequence succeeded but incorrectly counted an
extra application recovery.

### What was wrong

The OS retry retained the originating request's `polyinference/recovery-of`
provenance. Kernel authorization treated that inherited provenance as a new
application recovery before validating the separately issued OS retry intent.
FIX-0045 tested transient retry followed by output adaptation; it did not test
the reverse order, adaptation followed by transient retry. This was an OS
authorization/accounting composition defect, not an agent response-strategy defect.

### How it was fixed

`runtime/kernel.py` validates a retained OS-issued retry through its OS retry
authorization path. A fresh application recovery still uses its existing separate
authorization/allowance path. Normal scope, process, grant, limits, deadline,
ownership and workspace guards remain in force for both.

`tests/test_model_retries.py` adds the reverse composition with one and two allowed
application recoveries, checking exactly one recovery record, three submissions,
unchanged adapted input on the OS retry, and replay without new submission. A
third test rejects an unissued OS retry carrying recovery provenance, including
when the caller's recovery allowance is zero.

### Design principle enforced or reconstructed

Recovery provenance and the authority to submit a specific new attempt are
distinct. OS transport retries must consume their own bounded retry allowance
and real resource budgets, without consuming or bypassing application recovery
authorization. Retain every attempt and validate its actual issued intent.
This restores the existing boundary guide's documented separation; no new design
rule, schema change or historical-run migration is needed.

### Verification

Reproduced both defects before the correction: the one-recovery case raised
`Model recovery allowance exhausted`; the two-recovery case stored two caller
recovery records instead of one. After correction, **50 focused cases passed**
across `test_model_retries.py`, `test_output_limits.py` and the earlier explicit
permanent-failure recovery regression. That run predates the third authorization
regression; final full-suite verification below includes it.

The resumed pre-correction full suite passed **289 tests, two skipped**, in
297.55 seconds. Windows Node separately passed all **14 frontend checks**; Linux
has Node v12.22.9, below the frontend test's Node 18 minimum. The other Linux skip
needs a supported native Linux Node/npm pair to reproduce npm housekeeping.
Lint passed for the complete changed implementation/test file set.

Final post-correction full suite: **292 passed, two skipped, in 292.39 seconds**
with `.venv-linux/bin/python -m pytest -q -rs`, including all three new regressions.
The two skips are the Linux environment cases described above; the frontend
checks were separately exercised by the 14-pass Windows Node run. Added-record
links, stable IDs, required sections and resumed-patch whitespace were checked.
This completion supersedes the pending verification statements in FIX-0044
through FIX-0046 and the original handoff; their earlier results remain historical
evidence. No live provider, original Minecraft run, native Linux npm reproduction,
network installation, commit or deployment was performed.

<a id="fix-0048"></a>
## FIX-0048 — 2026-10-20 — Document the Codex and serial Haiku tester setup

Status: implemented as documentation only.
Related history: [FIX-0009](#fix-0009), [FIX-0011](#fix-0011),
[FIX-0013](#fix-0013), [FIX-0036](#fix-0036), [FIX-0040](#fix-0040).

### Problem

New testers who start at the README need one concrete setup route for Codex
senior work and Haiku acting as local inference with batch size 1, plus a clear
place to report findings.

### What was wrong

The README contains general setup and provider alternatives, but no dedicated
onboarding guide for this experiment. Calling the cloud path a reverse proxy
could also direct testers to the separate, query-only HTTP adapter. This is a
documentation/discoverability issue, not an established runtime defect.

### How it was fixed

Added root `codex-haiku-setup.md` with installation, same-host Codex login,
Anthropic credentials, an explicit `POLYINFERENCE_LOCAL_BATCH_SIZE=1` launch,
UI smoke testing, project testing, troubleshooting and reporting instructions.
Explained the checked-in `codex_app_server` integration and the separate
`codex_proxy` limitation, and distinguished the local lane from physical hosting
and request concurrency from worker count. Added a visible tester note at the
top of `README.md`. Linked all three existing finding destinations:
`current-iter-issues.md`, `next-iteration.md` and `general-issues.md`.
No implementation, configuration example or test code changed.

### Design principle enforced or reconstructed

Document the effective provider binding and execution path rather than inferring
behavior from lane names or historical proxy research. Keep credentials outside
source, preserve the brokered tool boundary, and make tester evidence discoverable
through the repository's existing issue triage workflow.

### Verification

Cross-read the guide against `ui.py` defaults, `config.py` capacity overrides and
role validation, `cli.py` credential/config loading, the mixed example and README.
Checked official Codex installation/authentication documentation. Checked local
Markdown link targets, required setup/reporting content and patch whitespace.
No live provider requests, package installation, smoke run or implementation test
suite were performed for this documentation-only task. The Git status command
against the WSL checkout was limited by host filesystem interoperability; no
unrelated working-tree changes are claimed.

<a id="fix-0049"></a>
## FIX-0049 — 2026-10-20 — Diagnose context-packing overflow after gameplay recovery

Status: investigated; no implementation changed.
Related history: [FIX-0030](#fix-0030), [FIX-0034](#fix-0034),
[FIX-0040](#fix-0040), [FIX-0041](#fix-0041), [FIX-0044](#fix-0044),
[FIX-0045](#fix-0045), [FIX-0047](#fix-0047).
Detailed evidence: [run 2de3d5c5ab9b analysis](run-2de3d5c5ab9b-analysis.md).

### Problem

Minecraft v11 paused at `worker-3-recover_playable_foundation/model-44` with
`Required context does not fit; no silent pin removal`, immediately after a
passing production build. The first gameplay worker had previously generated
an undeclared test bundle and needed replacement.

### What was wrong

The coding agent packs whole history entries using their canonical byte sizes
plus a fixed 2,000-byte margin. The OS checks the serialized message array, whose
outer escaping/framing is larger. The saved request estimates 93,391 bytes but
measures 96,529 against a 96,000 allowance. Required messages alone are 14,421;
all 44 history entries were included. Omitting the two oldest optional pairs
would reduce the serialized input to 95,719 without removing required pins.
The failed effect records `submitted=false`; this is a local accounting defect,
not an observed provider context-window rejection.

The earlier shell command created `.test-build/foundation.test.mjs` outside its
grant and declared outputs, correctly triggering the attached-workspace block.
The replacement had no candidate commit to resume and reconstructed the modules
from the scaffold. These are separate task-output planning and unfinished-work
handoff gaps, not evidence that the OS should ignore scope violations.

### How it was fixed

No implementation, configuration, tests or generated game files changed.
Added the linked investigation with exact measurements, timeline, owning layers,
preserved-work locations and proposed follow-ups. The replacement's historical
output reports 10 passing gameplay tests and its final explicit build check
passes, but no gameplay commit/publication or final acceptance completes.

### Design principle enforced or reconstructed

The calling agent must pack context against the same representation the OS
actually bounds, retaining mandatory instructions and complete tool pairs.
Known input-size mismatch needs a smaller authorized request, not an identical
transport retry. FIX-0030/FIX-0044 through FIX-0047 address output/transport
failures and did not cover this serialization mismatch. FIX-0034's declared
`dist` output does not cover an undeclared test bundle; FIX-0040's committed
candidate handoff does not cover pre-candidate uncommitted work.

### Verification

Parsed the supplied export (6,601 events, 235 effects, 631 artifacts, two reports),
read relevant source/regressions and matched the current agent-module hash to
the recorded graph digest. An offline Python probe executed the actual extracted
context-builder and canonical-serializer definitions with saved inputs and
in-memory stubs. It reproduced the exact saved messages, overflow and fitting
two-pair omission; assertions passed. Independent JavaScript sizing agreed.
Checked documentation links, stable ID/index/required sections and whitespace.
No live inference, run resume, game playtest, dependency installation or
implementation test suite was performed. Historical game checks are explicitly
separated from these new probes. No implementation fix or new regression coverage
is claimed; unrelated existing working-tree changes were left untouched.

<a id="fix-0050"></a>
## FIX-0050 — 2026-10-20 — Audit input and output cap safeguards across inference adapters

Status: investigated; no implementation changed.
Related history: [FIX-0028](#fix-0028), [FIX-0030](#fix-0030),
[FIX-0044](#fix-0044), [FIX-0045](#fix-0045), [FIX-0047](#fix-0047),
[FIX-0049](#fix-0049).
Detailed evidence: [cap safeguards audit](inference-cap-safeguards-audit-2026-10-20.md).

### Problem

The user asked which issues the Minecraft v11 run exposed and whether input
overflow or truncated output receives proper fallback on both inference lanes.
The run showed a safe local rejection that still ended useful work prematurely.

### What was wrong

Shared input preflight checks configured bounds but does not rebuild oversized
contexts. Raw HTTP output-token stops have structured detection and bounded
application adaptation; native Codex does not receive the configured per-call
output-token limit or use that same cutoff recovery. Reported byte-limit failures
also follow different paths. Chat-compatible responses without a finish reason
are accepted, and endpoint-side silent input/output truncation cannot be reliably
established from the retained completion contract. Anthropic context-window
stops become generic retryable response errors instead of input adaptation.

The existing output adaptation appends feedback without repacking: a fitting
95,719-byte context derived from the saved run becomes 96,327 after feedback,
exceeding the 96,000 cap. This is an offline counterexample, not a claimed run
event. These gaps were outside FIX-0030's raw cutoff handling and FIX-0045's safe
transient retry coverage; binding symmetry does not imply adapter parity.

### How it was fixed

No implementation, configuration, tests or game files changed. Added the linked
audit with a failure-mode inventory, source ownership, observed-versus-probed
distinctions, existing safeguards and proposed repair direction. The original
run's context, output-declaration, unfinished-work handoff and evidence-quality
findings remain recorded in FIX-0049 and its detailed investigation.

### Design principle enforced or reconstructed

The OS owns accurate resource bounds, completion/termination facts and safe
effect handling across endpoints. Calling agents own authorized context reduction
and smaller-response/task strategies. Detection, safe stopping and automatic
recovery are distinct guarantees. Never execute explicitly incomplete output,
discard mandatory constraints, silently move data between inference locations,
or blindly repeat native jobs that may already have effects.

### Verification

Read relevant kernel/adapter/retry/application paths and existing tests. Offline
Python probes executed AST-extracted source to confirm four-protocol cutoff
rejection and the missing finish-reason, context-window classification, reported
output-token overage, native token-parameter and application byte-cap findings.
All six checks completed; the final coroutine harness avoids Windows event-loop
startup, which stalled the first attempts. JavaScript sizing confirmed feedback
can overflow a near-full request. Checked documentation links, stable IDs,
required sections and whitespace. No live inference, run resume, full test suite
or implementation repair was performed; no new regression coverage is claimed.

<a id="fix-0051"></a>
## FIX-0051 — 2026-10-20 — Propose bounded OS recovery for inference overflow

Status: investigated; design proposal only, no implementation changed.
Related history: [FIX-0030](#fix-0030), [FIX-0045](#fix-0045),
[FIX-0047](#fix-0047), [FIX-0049](#fix-0049), [FIX-0050](#fix-0050).
Proposal: [OS overflow safety](inference-overflow-safety-proposal-2026-10-20.md).

### Problem

The user asked how input-too-long and truncated-output recovery should work in
the OS. Existing rejection and selected raw-output recovery do not provide a
uniform continuation path across adapters, particularly when the failing input
cannot itself fit another model invocation.

### What was wrong

FIX-0049/FIX-0050 establish mismatched sizing, missing input adaptation and
different raw/native cap guarantees. A design that sends the full oversized
prompt back for recovery would repeat the original problem; blindly restarting
native work can duplicate effects. These are requirements motivating a proposal,
not additional failures claimed to have occurred in the historical run.

### How it was fixed

No implementation, configuration, tests or game files changed. Recorded a
proposed generic contract for prepared-request measurement, caller-authorized
optional-group reduction, bounded host control events, structured overflow facts,
strict completion handling and linked smaller-output recovery. Required-only
overflow parks with preserved state; uncertain termination requires reconciliation.
The proposal includes a verification matrix but adds no executable regressions.

### Design principle enforced or reconstructed

The OS owns accurate resource/completion/effect guarantees and generic bounded
recovery orchestration. Applications declare what may be omitted and how work
is decomposed or continued. A recovery control event must remain deliverable
without the oversized model prompt. Preserve mandatory constraints, complete
tool pairs, settled effects, authority and real budgets across both bindings.

### Verification

Cross-read the proposal against the existing boundary guide and FIX-0050 audit.
Checked documentation links, stable ID/index, required sections and whitespace.
No implementation checks, live inference, game changes or run resume occurred.
The proposed safeguards and test matrix remain unimplemented and unverified as
runtime behavior; historical probe results are not claimed as new verification.

<a id="fix-0052"></a>
## FIX-0052 — 2026-10-20 — Separate OS overflow guarantees from reusable agent recovery policy

Status: investigated; design proposal only, no implementation changed.
Related history: [FIX-0032](#fix-0032), [FIX-0049](#fix-0049),
[FIX-0050](#fix-0050), [FIX-0051](#fix-0051).
Proposal: [agent/OS responsibility split](agent-os-overflow-responsibility-proposal-2026-10-20.md).

### Problem

The user requested a responsibility split that keeps the OS general and simple
while making agents easy to design. The previous proposal allowed kernel-side
optional context selection and registration of response-recovery strategies,
which could grow the OS's application-policy surface unnecessarily.

### What was wrong

FIX-0051 established execution-safety requirements but left reusable caller policy
too close to the kernel. Duplicating packing/recovery in every agent is also
undesirable. This is a design placement refinement, not a new observed runtime
failure or an implemented correction.

### How it was fixed

No implementation, configuration or tests changed. Added a three-layer proposal:
the OS provides prepared-request measurement/enforcement and normalized durable
outcomes; an optional shared agent library supplies packing and bounded adaptation
defaults; applications supply required inputs, response protocols and semantic
decisions. Added an explicit refinement link to FIX-0051's proposal rather than
rewriting its original design silently. Normal operation results and existing
continuations can carry recovery without a new kernel policy registry.

### Design principle enforced or reconstructed

Keep resource, authority, effect-certainty and replay guarantees mandatory at
the OS boundary. Share useful agent policies in ordinary optional caller-side
code. Agent authors should declare inputs and protocols rather than reimplement
provider-specific recovery; direct and non-coding callers still receive the same
OS guarantees. Coding acceptance, Git handoff and task decomposition remain
application responsibilities.

### Verification

Cross-read the current runtime boundary, public ports and prior overflow analyses/
proposal. Checked stable ID/index, required sections, documentation links and
whitespace. No runtime or implementation tests, live provider requests, generated
game changes or run resume were performed. The proposed responsibility split and
its conformance matrix remain unimplemented and unverified as runtime behavior.

<a id="fix-0053"></a>
## FIX-0053 — 2026-10-20 — Propose agent-controlled OS context handling and optional compaction

Status: investigated; design proposal only, no implementation changed.
Related history: [FIX-0049](#fix-0049), [FIX-0050](#fix-0050),
[FIX-0051](#fix-0051), [FIX-0052](#fix-0052).
Proposal: [optional OS context service](optional-os-context-management-proposal-2026-10-20.md).

### Problem

The user wanted agents to opt into OS handling of long contexts through a setting,
disable it to reveal native agent-design problems, and choose manual memory
management, OS automatic compaction or a mix. They also asked whether automatic
OS compaction already exists.

### What was wrong

The previous responsibility proposal placed common adaptation in a caller-side
library, which did not meet this requested direct OS-service interface. Current
code has coding-agent history selection and senior-written working summaries,
but no implemented general OS automatic compaction or context-policy switch.
Treating every memory/artifact block as implicitly safe to summarize would also
confuse caller-owned semantics with execution authority.

### How it was fixed

No implementation, configuration or tests changed. Recorded a revised proposal
for an optional generic OS context service, process defaults/request overrides,
separate automatic-context and automatic-compaction permissions, and manual,
automatic and hybrid use. Required before/after diagnostics expose successful
interventions; originals stay immutable and summaries are derived input views.
Added an explicit superseding-placement note to FIX-0052's proposal while
preserving that historical document.

### Design principle enforced or reconstructed

Agents own supplied memory, artifacts and semantic transformation permissions.
The OS owns accurate bounds and unconditional execution safety, and may offer
optional generic assistance without taking ownership of an agent's memory store.
Optional automation must be observable and disableable; it cannot weaken grants,
trust, protected inputs, budgets or termination/effect certainty. Compaction
services remain usable by non-coding agents and independent of a shared library.

### Verification

Inspected actual agent memory/context assembly, senior memory updates, context/
memory contracts and runtime/configuration/ports search results. Cross-read the
boundary guide and earlier proposals. Checked documentation links, ID/index,
required sections and whitespace. No implementation tests, inference, actual
compaction or run resume occurred. The settings, OS service, compaction receipts
and conformance matrix are proposed only and remain unimplemented.

<a id="fix-0054"></a>
## FIX-0054 — 2026-10-20 — Defer the shared library and assign current fixes to OS or agent

Status: implemented as planning documentation only; no runtime implementation changed.
Related history: [FIX-0049](#fix-0049), [FIX-0052](#fix-0052),
[FIX-0053](#fix-0053).

### Problem

The user considered a third shared-agent-library layer premature and requested
that it be recorded for the next stage, with current fixes assigned to either
the OS or the agent.

### What was wrong

The earlier three-layer proposal remained visible and could be mistaken for a
current prerequisite. The revised optional-context proposal also needed one
explicit ownership table covering I/O, memory and the other run-exposed issues.
This was plan ambiguity, not an additional observed runtime failure.

### How it was fixed

Recorded the optional shared library in the existing
[next iteration backlog](next-iteration.md#shared-agent-support-library), which
was previously empty. Marked the earlier responsibility proposal historical and
deferred. Updated the [current plan](optional-os-context-management-proposal-2026-10-20.md)
with six OS and five agent items, preserving direct agent-facing automatic-context
and optional-compaction settings. No code, configuration or tests changed.

### Design principle enforced or reconstructed

Keep this stage to OS mechanisms/services and application policy. Optional OS
assistance is directly available to agents, while context semantics, coding
workflow and acceptance remain agent-owned. Defer reusable library extraction
until real reuse justifies the extra surface. Preserve earlier proposals with
explicit supersession rather than silently rewriting design history.

### Verification

Confirmed README identifies `development-docs/next-iteration.md` as the next-stage
backlog and checked the file was empty before adding the deferred idea. Checked
all added/updated plan links, explicit backlog anchor, ownership IDs, stable fix
ID/index, required sections and whitespace. No runtime tests, live inference,
implementation changes or run resume were performed.

<a id="fix-0055"></a>
## FIX-0055 — 2026-10-20 — Implement OS context and output recovery; final verification pending

Status: implemented in working tree; incomplete, stopped at the user's request.
Related history: [FIX-0030](#fix-0030), [FIX-0047](#fix-0047),
[FIX-0049](#fix-0049), [FIX-0050](#fix-0050), [FIX-0053](#fix-0053).
Handoff: [I/O implementation stop point](HANDOFF-2026-10-20-IO.md).

### Problem

Agent-side context estimates could produce an oversized OS request, and output
limits had inconsistent detection and recovery across HTTP/native adapters.
Optional OS context/compaction assistance was unavailable.

### What was wrong

The application and kernel measured different representations. Output recovery
was application-owned and appended unbudgeted feedback; native preparation,
missing completion metadata and complete-but-oversized output had different
handling. Repeated transport submission cannot repair these size mismatches.

### How it was fixed

Added `runtime/context.py`, prepared HTTP/native request construction, context
receipts, caller-selected optional packing/compaction and durable derived views.
Moved bounded smaller-output attempts into `runtime/model_retries.py` with separate
OS-issued identities; original outcomes and caller recovery remain distinct.
Kernel checks final prepared representations, records typed input failure and
rejects oversized complete replies. HTTP completion/context classification was
tightened. Removed conflicting agent history estimates/output adaptation and
exposed memory as a separately compactable block. See the handoff for exact
paths, implementation limits and unfinished coverage/documentation.

### Design principle enforced or reconstructed

OS mechanisms enforce resource/completion/effect guarantees; agents declare
context semantics and optional transformations. Preserve originals, trust,
complete tool groups, authority, real budgets and uncertainty across both lanes.
The optional service requires no shared agent library or coding semantics.

### Verification

The last affected run passed 103 tests in 108.87 seconds; final Ruff passed all
changed modules/tests. Early failures and corrections are recorded in the linked
handoff. The last small additions postdate that test run and have lint coverage
only. Full-suite, native edge cases, documentation consolidation and live-provider
verification remain pending. No original run was resumed and no completion of
the full fix is claimed.

<a id="fix-0056"></a>
## FIX-0056 — 2026-10-20 — Consolidate exported OS settings and coding configuration

Status: implemented in working tree; settings reference and final verification pending.
Related history: [FIX-0032](#fix-0032), [FIX-0053](#fix-0053),
[FIX-0054](#fix-0054), [FIX-0055](#fix-0055).

### Problem

The user required exported OS settings, their documentation and coding-agent
configuration to be located together instead of scattered across layers/files.

### What was wrong

The generic settings class, coding defaults and UI endpoint/resource choices
were mixed across `config.py`, agent behavior and UI construction. New context
and I/O policy would otherwise add more scattered switches.

### How it was fixed

Added `system_settings.py` as the complete OS settings schema location and
`agent/system_settings.py` as the adjacent coding defaults/UI configuration
location. `config.py` retains application policy and compatibility exports.
All five agent example JSON files now use one `system` object; legacy flat input
is accepted and duplicate locations are rejected. UI uses the grouped block.
New context and inference safety fields live together. The final consolidated
reference was not completed before the user requested stopping; its full field
inventory and next steps are in the [handoff](HANDOFF-2026-10-20-IO.md).

### Design principle enforced or reconstructed

Keep the OS's developer-facing configuration discoverable and explicit, with
one schema and nearby application choices. Optional automation must be visible
and configurable without weakening mandatory safety or adding a third layer.

### Verification

Grouped input/default validation and affected UI checks are included in the
103-pass run in FIX-0055. Final Ruff passed. A full exported-settings inventory
was inspected to prepare the reference, but no documentation-completeness check
or final full-suite run is claimed. Stop-point limitations remain open.

<a id="fix-0057"></a>
## FIX-0057 — 2026-10-20 — Preserve interrupted coding edits and improve scope/evidence handling

Status: implemented in working tree; final added regressions not yet run.
Related history: [FIX-0033](#fix-0033), [FIX-0034](#fix-0034),
[FIX-0040](#fix-0040), [FIX-0049](#fix-0049), [FIX-0054](#fix-0054).

### Problem

The run generated an undeclared test bundle, blocked a worker, then reconstructed
its uncommitted modules in a replacement. Malformed replies inflated history and
piped test commands could mask failing exit status.

### What was wrong

Committed-candidate reuse did not cover interruption before a candidate existed.
Task output planning and evidence interpretation needed stronger application
guidance; scope failure facts were not fully returned to the agent.

### How it was fixed

The coding repository provider now snapshots authorized interrupted source into
`coding/interrupted/` references and restores explicitly selected references
with scope/base conflict checks. Agent driver/park paths expose retained source.
OS shell scope outcomes include offending paths/grants; coding opts into a
generic shell fail-fast setting. Agent prompts require declared generated outputs,
full chunked inspection and truthful evidence; worker validation has a bounded
consecutive-correction allowance. No Git workflow was added to the OS.

### Design principle enforced or reconstructed

Preserving source is distinct from accepting or publishing it. Reuse only
authorized retained deltas without copying unexpected files, bypassing scope
guards or fabricating checks. Keep coding policy in the agent and generic
execution facts/settings in the OS.

### Verification

Existing affected repository/UI tests passed in the 103-case run. New explicit
uncommitted-handoff and pipeline regressions were added afterward and have final
lint verification only; they remain first checks for tomorrow. No live game,
original-run resume, full suite, commit or push occurred. See the
[handoff](HANDOFF-2026-10-20-IO.md) for the exact restart point and remaining risks.

<a id="fix-0058"></a>
## FIX-0058 — 2026-10-20 — Complete OS I/O safety and compaction verification

Status: implemented and verified in the working tree.
Related history: [FIX-0055](#fix-0055), [FIX-0056](#fix-0056),
[FIX-0057](#fix-0057); responsibility decisions [FIX-0053](#fix-0053),
[FIX-0054](#fix-0054).

### Problem

The run exposed serialized input overflow, repeated output cutoffs and missing
cross-adapter guarantees. FIX-0055 was deliberately left unfinished at the user's
stop request; its added edge cases and full-suite verification remained open.

### What was wrong

OS preparation, recovery and adapter capability handling needed one consistent
boundary. Resume review found proxy hard-coded limits, missing native terminal
byte-cutoff adaptation, incomplete generation-overage checks and a summary-child
retry path that could not satisfy its durable-child authorization.

### How it was fixed

Completed prepared-payload/limit forwarding for the proxy; native terminal
cutoffs and reported native/Gemini generation overages now enter classified OS
output handling. The native retry guard distinguishes summary children from
actual brokered capability effects. Summary children have no nested recovery tree, uncertain
preparation cannot submit the parent, and receipts link original/derived views
and child calls. Runtime/design ContextPart.compactable definitions and the
generated schema now agree. Main paths: runtime/context.py, runtime/kernel.py,
runtime/model_retries.py, runtime/inference.py, runtime/codex.py, contracts.py
and design-docs/langgraph-agent contracts/schema. See the
[completion report](io-safety-verification-2026-10-20.md).

### Design principle enforced or reconstructed

The OS measures and bounds its known wire input, withholds incomplete output,
owns generic bounded adaptation and preserves effect certainty. Optional context
assistance cannot change authority, routing, canonical memory or finishing
reserves. Native unsupported hard limits must be exposed or rejected, never
silently promised. Coding semantics remain agent-owned.

### Verification

Final full suite: **327 passed, 2 skipped**. The two last corrections were
verified afterward by **73 passing context/recovery cases**. Frontend: **14/14**
with Windows Node; final Ruff and whitespace checks passed. Canonical-LF design
validation passed 35 records/41 invalid combinations. The [completion report](io-safety-verification-2026-10-20.md) records exact final
suite, lint and frontend results, prior failed checks and material limits.
New coverage includes local/cloud manual/assisted input, whole groups, immutable
memory/trust, overrides, unissued child rejection, failed/cancelled/uncertain/
budget-limited compaction, restart without duplicate summaries, remeasured output
feedback, tool-free native compaction, native terminal cutoffs, proxy selected
limits and strict native rejection. This entry supersedes FIX-0055's pending
verification status; it does not claim live provider or original-run validation.

<a id="fix-0059"></a>
## FIX-0059 — 2026-10-20 — Finish the unified OS settings reference and grouped validation

Status: implemented and verified in the working tree.
Related history: [FIX-0055](#fix-0055), [FIX-0056](#fix-0056),
[FIX-0057](#fix-0057); responsibility decisions [FIX-0053](#fix-0053),
[FIX-0054](#fix-0054).

### Problem

Agent developers needed one place to find, document and configure every exported
OS preference. FIX-0056 centralized definitions/defaults but stopped before
finishing the reference. Grouped configuration also had two validation gaps.

### What was wrong

AgentConfig assumed system was a dictionary, and RuntimeConfig's environment
override could inject a duplicate flat local endpoint alongside grouped system
settings. The boundary guide still assigned output adaptation to the agent.

### How it was fixed

Validated non-object system input, applied the environment override within the
selected grouped settings without mutating caller data, and completed
design-docs/simplified-os/AGENT_SETTINGS.md. It inventories RuntimeConfig,
Endpoint, Limits/PhaseReserve, ContextPolicy, InferenceSafety and Check fields,
defaults/units, precedence, coding overrides, context modes, receipts and native
limitations. README, boundary, original proposal and historical handoff link the
current reference. Definitions remain in system_settings.py and coding defaults/
UI choices remain adjacent in agent/system_settings.py; config.py keeps workflow
policy/compatibility exports and examples use one system block.

### Design principle enforced or reconstructed

An OS interface should be discoverable and configured together. Optional
automation must be explicit and observable; disabling it reveals agent input
construction problems while mandatory safety remains active. Keep the current
architecture to OS and agent.

### Verification

Schema-to-reference field coverage and all five grouped examples pass.
Both RuntimeConfig and AgentConfig reject non-object system values and preserve
the local batch-size environment override. Duplicate placements remain rejected.
See the [completion report](io-safety-verification-2026-10-20.md) for exact checks.
This completes FIX-0056's unfinished reference and corrects the old boundary
statement rather than silently changing its historical fix entry.

<a id="fix-0060"></a>
## FIX-0060 — 2026-10-20 — Verify interrupted-source handoff and consecutive correction policy

Status: implemented and verified in the working tree.
Related history: [FIX-0055](#fix-0055), [FIX-0056](#fix-0056),
[FIX-0057](#fix-0057); responsibility decisions [FIX-0053](#fix-0053),
[FIX-0054](#fix-0054).

### Problem

FIX-0057's new source-handoff and fail-fast regressions had not run when the user
stopped. Resume review also found valid tool actions retained an old grammar-error
streak, and unrelated shell capture errors could receive a scope-violation label.

### What was wrong

The agent reset its protocol counter for final replies but returned early for
valid actions without resetting it. Shell scope details were attached by a broad
exception handler even when the failure was unrelated to unauthorized changes.

### How it was fixed

Valid Action replies now reset protocol_errors in agent/worker.py. Shell scope
facts are attached only when offending paths were observed. Verified the retained
authorized-source mechanism in agent/repository.py and driver/park integration:
replacement work uses explicit preserved_source_ref/resume_from, excludes
unauthorized files and rejects insufficient grants or a conflicting integrated
base before copying any retained delta. Prompts/evidence policy and canonical
memory remain in the coding agent.

### Design principle enforced or reconstructed

Consecutive correction limits count consecutive invalid replies. Preserving
unfinished authorized source is distinct from accepting/publishing it, and neither
a generated output nor a recovery attempt expands source authority. Return
truthful generic execution facts while repository workflow stays agent-owned.

### Verification

Pending source handoff, strict-cap and pipeline regressions passed in the resumed
106-test run. Both new grant/base-conflict refusal cases passed, and the
valid-action/error-reset regression passed. The
[completion report](io-safety-verification-2026-10-20.md) records final suite
coverage and limits. This completes FIX-0057's pending verification; no original
Minecraft run, live gameplay, commit or push is claimed.

<a id="fix-0061"></a>
## FIX-0061 — 2026-10-20 — Research concurrent Claude requests for local inference simulation

Status: investigated; no implementation or configuration changed.
Related history: [FIX-0009](#fix-0009), [FIX-0011](#fix-0011),
[FIX-0048](#fix-0048), [FIX-0059](#fix-0059).

### Problem

The user requested research into two Claude API conversations to emulate local
continuous batching, explicitly excluding implementation at this stage.

### What was wrong

No new runtime defect was established. The tester UI deliberately sets both
local.max_inflight and max_workers to 1. Raising only the environment-controlled
inference capacity cannot create a second worker. Message Batches is an offline
bulk API, which is a different mechanism from interactive continuous batching.

### How it was fixed

Research only. HTTPInference already uses httpx.AsyncClient and ordinary
POST /v1/messages with stream:false. Admission permits concurrent requests and
independently releases capacity after known completion. The proposed setup sets
system.max_workers:2 and system.local.max_inflight:2, preserves provider/model
routing and adequate reserved_context_tokens, and uses a fresh run via ui --config.
The mixed example already has two local slots and inherits max_workers:2; its
128000 per-context allowance and 256000 aggregate reservation support two such
allowances. POLYINFERENCE_LOCAL_BATCH_SIZE overrides local.max_inflight only;
remove a lingering value of 1 or set it to 2. Separate conversations keep separate
caller-owned histories. Actual overlap needs independent ready tasks and a Git
policy allowing task worktrees; disabling task branches limits editors to one.
A second key, OS threads and an SDK replacement are unnecessary for this setup.
Only this required history record changed; no implementation, example, test or
launch configuration was edited.

### Design principle enforced or reconstructed

Agents own task readiness and coding/Git policy. The OS owns generic admission
and execution facts. The inference server owns GPU scheduling. Concurrent Claude
calls approximate two active generations and independent slot refill; they do
not reproduce local token-step scheduling, KV memory, contention or throughput.
Streaming changes incremental delivery and is unnecessary for overlapping calls.

### Verification

Read current configuration/environment overrides, UI loading, HTTP adapter,
admission/kernel reservations, controller dispatch, repository worker caps and
mixed example. Inspected the existing two-request overlap regression in
[test_endpoints.py](../tests/test_endpoints.py); it was not rerun in this task.
Consulted official Anthropic documentation for
[stateless Messages](https://platform.claude.com/docs/en/build-with-claude/working-with-messages),
[batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing),
[streaming](https://platform.claude.com/docs/en/build-with-claude/streaming) and
[rate limits](https://platform.claude.com/docs/en/api/rate-limits).
Requests/input/output token limits apply to aggregate organization usage; a second
API key does not provide a separate organization quota. Checked entry/index,
required sections and added-line whitespace. No live request, account-limit
lookup, concurrency benchmark, implementation tests or runtime change occurred.
Existing unrelated working-tree edits are not claimed.

<a id="fix-0062"></a>
## FIX-0062 — 2026-10-20 — Inspect UI memory visibility and propose an OS context drawer

Status: investigated; proposal only, no implementation changed.
Related history: [FIX-0014](#fix-0014), [FIX-0037](#fix-0037),
[FIX-0053](#fix-0053), [FIX-0058](#fix-0058), [FIX-0059](#fix-0059).

### Problem

The user asked whether the UI shows the current agent's memory on the OS side
and requested a simple OS edit if that visibility is missing.

### What was wrong

Visibility is partial. Agents > Shared notes & hazards shows memory/working and
uncovered memory-note/ handoffs. Process execution history exposes node state and
recorded prompts; Inspect records can open retained context and artifact records.
There is no dedicated OS process memory/context view. snapshots.detail normally
reconstructs Prompt from the original effect request's context.parts, rather
than context-prepared/<operation_id>.context. Native userMessage evidence may
override that prompt when retained, but this is not a uniform effective-context
projection. FIX-0037 predates the optional preparation added in FIX-0058; the
current context regressions verify runtime preservation, not this viewer join.
This is an OS inspection gap, not evidence of lost canonical agent memory.

### How it was fixed

No implementation changed. Proposed a read-only Memory / context action in the
OS process drawer in src/polyinference/ui-monitor.js. Reuse existing /api/record
and /api/artifact readers and the savedDocument records/artifacts equivalents;
no new runtime store, agent API, configuration or coding-memory convention is
needed. Let the user choose the process and model operation, defaulting to an
active caller invocation or its latest retained invocation, while identifying
retry attempts and compaction child calls separately.

Show the original ContextView from effect/<operation_id>, the effective prepared
ContextView from context-prepared/<operation_id>, and its context-receipt/ record.
List ordered part IDs, kinds, trust, source, required/compactable flags and
on-demand full artifact content. Display measured bytes/allowance, omitted parts,
summary source/derived links and capture/operation identity. Label preparation
and recorded submission evidence separately: a prepared context or the receipt's
submitted_bytes field alone does not establish provider submission. Missing or
legacy preparation must say unavailable and label original input as such.
For consistency, a follow-up viewer change in snapshots.py should make node
Prompt distinguish original input from effective prepared input as well.

### Design principle enforced or reconstructed

The OS exposes generic retained inputs, transformations and provenance. The
calling agent owns canonical memory and its semantics; an inspector must not
assume memory/working or agent-memory exists for other agents. An invocation's
context is a time-stamped input snapshot, not the provider's hidden reasoning,
native internal session state, or every record the agent might read next.

### Verification

Read fix history, runtime boundary guide, UI/backend/snapshot paths, agent memory
assembly and runtime preparation/submission paths. Ran existing focused checks:
`.venv-linux/bin/python -m pytest tests/test_ui_agents.py tests/test_ui_os.py tests/test_context_safety.py -q`
through WSL: **45 passed in 9.37 seconds**. These confirm existing behavior, not
the proposed drawer. Checked the added history index/ID, required sections, local
source references and whitespace. No live UI/provider inspection, implementation,
new regression tests or run resume occurred. Only this required history entry
and its index row were edited for this task.

<a id="fix-0063"></a>
## FIX-0063 — 2026-10-20 — Design a launch-scoped UI batch simulation flag

Status: investigated; design recorded, implementation deferred by user request.
Related history: [FIX-0061](#fix-0061), [FIX-0048](#fix-0048),
[FIX-0059](#fix-0059).
Design: [SIM-01 in current iteration issues](current-iter-issues.md#sim-batch-ui).

### Problem

The user wants polyinference ui --sim-batch 2 to configure Claude-backed local
inference and worker capacity for that invocation without affecting the next
normal launch, and requested research/design stored for this version only.

### What was wrong

There is no CLI flag/plumbing. Default UI settings cap both workers and local
requests at one. Repeated configuration validation can reapply the legacy
capacity environment override; partial endpoint replacement can lose the model,
URL and credential reference. These are design hazards, not newly reproduced
live startup failures. Existing concurrency support does not supply launch scope.

### How it was fixed

No implementation or configuration changed. Followed README's current-version
tracker link and added SIM-01, covering flag lifetime/range, complete Haiku
endpoint construction, per-instance settings, explicit CLI precedence across
validation, worker/slot/reservation sizing, custom config behavior, credential
and provider startup handling, saved-run evidence and concrete acceptance checks.
The earlier research remains preserved and linked; implementation is deferred.

### Design principle enforced or reconstructed

CLI/UI and the coding agent own this simulation preset. The OS receives ordinary
validated limits and preserves admission, budgets and uncertainty. Provider GPU
scheduling remains remote. Invocation preferences cannot become persistent
settings; saved effective run config is evidence, not a default for new launches.
Preserve complete provider identity and secrets handling across every rebuild.

### Verification

Read the history additions since the earlier research, README tracker mapping,
runtime boundary, CLI/UI/settings/admission/kernel paths and relevant existing
UI, grouped-settings and Anthropic regression sources. Consulted official
Anthropic Messages/authentication/model/rate-limit documentation linked in SIM-01.
Checked new anchors, history ID/index, required sections, local document links,
added-line whitespace and preservation of existing issue/history text. No runtime
tests, live API/model-access checks, implementation, default/config edits or run
resume occurred. Planned test requirements are not claimed as completed checks.

<a id="fix-0064"></a>
## FIX-0064 — 2026-10-20 — Design OS memory and effective-context inspection for this version

Status: investigated; design recorded for this version, implementation remains open.
Related history: [FIX-0062](#fix-0062), [FIX-0037](#fix-0037),
[FIX-0058](#fix-0058), [FIX-0059](#fix-0059).
Design: [MEM-01 in current iteration issues](current-iter-issues.md#os-memory-context-inspector).

### Problem

The user requested implementation research and a concrete design for OS-side
agent-memory visibility, stored in the README-designated current-version tracker.

### What was wrong

FIX-0062 identified partial visibility and original-versus-prepared prompt drift
but left only a short sketch in the history. Research also found that the
operation projection omits retry/compaction relationships, model-node matching
misses retries with changed logical steps, and separate live record reads cannot
claim transaction-wide consistency. Submission and preparation need independent
labels. These are source-established design gaps, not newly reproduced live
provider failures or lost agent memory.

### How it was fixed

No implementation changed. Followed README to current-iter-issues.md and added
MEM-01 with source findings, ownership, exact data mapping, default invocation/
attempt selection, nested retry and compaction handling, original/effective
views, lazy live/saved readers, stale-response invalidation, missing-data states,
unit/submission semantics, snapshot compatibility, node Prompt correction,
affected files, implementation order and an explicit acceptance matrix.
The refined design keeps existing endpoints/storage and uses a small OS
operation-metadata projection; no agent API or memory-store change is needed.

### Design principle enforced or reconstructed

The OS exposes retained input, provenance and preparation facts; agents own
canonical memory and its semantics. An invocation snapshot is not the provider's
hidden state or all future-readable application records. Observers must preserve
operation identity, uncertainty, original evidence and missing-data distinctions
without triggering execution, rewriting history or imposing coding conventions.

### Verification

Reviewed README routing, new history additions, runtime boundary, context
contracts, agent memory assembly, OS preparation/submission and retry code,
UI/cache/readers, shared snapshots and existing regression sources. Consulted
the browser API references linked in MEM-01. Checked new anchors, stable
history/index/sections, relative links, added whitespace and preservation of
prior issue/history text. FIX-0062's earlier 45-test result is identified as
historical; no tests were rerun for this documentation-only follow-up.
No implementation, settings, new regression tests, provider/UI execution or
run resume occurred. Only MEM-01 and this required history/index update changed.

<a id="fix-0065"></a>
## FIX-0065 — 2026-10-20 — Clarify Codex proxy authentication and plan usage

Status: investigated; no implementation changed.
Related history: [FIX-0058](#fix-0058) (proxy prepared payload and output limits).

### Problem

The user asked whether the current PolyInference Codex proxy method uses their
ChatGPT Codex plan and whether its consumption rate matches the 5-hour/weekly
allowances.

### What was wrong

The phrase “Codex proxy” can mean either the repository's optional HTTP adapter
or the native `codex app-server` subscription path. They have different
authentication owners and cannot be treated as interchangeable. The adapter
code does not determine what a separately installed HTTP proxy does with its
upstream credentials.

### How it was fixed

No implementation changed. Established that `codex_proxy` sends a prepared
request through `HTTPInference` to a configured HTTP endpoint, optionally using
the endpoint's `api_key_env` bearer credential. It does not start Codex CLI or
use its ChatGPT login itself. A separate proxy could forward to some Codex
subscription-backed service, but that behavior is outside this repository.
The normal `codex_app_server` integration launches the signed-in Codex CLI.
Recorded the account-usage distinction in this history entry.

### Design principle enforced or reconstructed

Keep transport and authentication claims tied to the code path that owns them.
An HTTP adapter cannot promise subscription-metering behavior from a compatible
third-party service whose implementation and account identity it does not
control.

### Verification

Read the required fix history, `CodexProxy` and `HTTPInference`, the proxy test,
README provider notes, and the Codex/Haiku setup guide. Consulted current
[OpenAI Codex plan usage guidance](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
and [usage credits guidance](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-personal-plans).
No tests were run because no implementation changed. No local proxy endpoint,
credentials, account usage meter, or live request was inspected; actual upstream
metering for a separately installed proxy remains unverified.

<a id="fix-0066"></a>
## FIX-0066 — 2026-10-20 — Audit current memory implementation and management ownership

Status: investigated; no implementation changed.
Related history: [FIX-0026](#fix-0026), [FIX-0053](#fix-0053),
[FIX-0058](#fix-0058), [FIX-0059](#fix-0059), [FIX-0062](#fix-0062),
[FIX-0064](#fix-0064).
Report: [current memory implementation](memory-implementation-report-2026-10-20.md).

### Problem

The user requested a report on implemented memory and who manages it. Shared
agent memory, execution persistence, optional OS compaction and richer memory
contracts can otherwise be mistaken for a single implemented memory subsystem.

### What was wrong

No new runtime defect was established. Current ownership and scope needed a
source-backed explanation: the senior chooses canonical summary text, workers
supply assessment notes, the coding controller/application persists and selects
them, and the OS provides storage and optional derived context preparation.
MemoryQuery/tier/snapshot contracts do not establish an active retrieval service.
The earlier viewer investigations cover visibility rather than this full lifecycle.

### How it was fixed

No implementation or configuration changed. Added the linked report covering
note publication, optional summary replacement and coverage, per-process history,
required/compactable prompt memory, current defaults, compaction role routing,
state-directory storage, absent cross-run/semantic retrieval and viewer limits.
Distinguished canonical senior consolidation from optional OS summary calls and
identified accumulation/required-input limits without claiming a new reproduced
live incident. Only the report and this required history/index update changed.

### Design principle enforced or reconstructed

Agents own canonical memory, relevance and semantic consolidation. The OS owns
durability, immutable evidence, execution bounds and explicitly permitted derived
context transformations. Contracts, proposals and inspection surfaces must not
be represented as implemented memory-management behavior.

### Verification

Read the fix history and runtime boundary, traced current application/runtime/
storage/contracts/settings/viewer paths and inspected existing memory/context
regressions. Offline probes executed actual AST-extracted memory_view, history
and append_history methods with in-memory stubs; empty/populated views, covered
note exclusion with retained originals, paired history and stable-ID deduplication
passed. Source assertions confirmed generic defaults and coding memory flags.
Checked the added report's relative links, stable history/index/sections and
added-text whitespace with UTF-8 Python checks. Windows Git inspection did not
complete reliably against the WSL filesystem (`Function not implemented`); no
completed Git diff check or reliable whole-working-tree status is claimed.
Existing integration/context tests were not rerun; no live
provider, UI execution, run resume or full-suite validation occurred. No unrelated
working-tree changes or historical test outcomes are claimed as this task's work.

<a id="fix-0067"></a>
## FIX-0067 — 2026-10-20 — Trace coding-agent concurrency and OS admission ownership

Status: investigated; no implementation changed.
Related history: [FIX-0009](#fix-0009), [FIX-0032](#fix-0032),
[FIX-0040](#fix-0040), [FIX-0048](#fix-0048), [FIX-0061](#fix-0061),
[FIX-0063](#fix-0063).

### Problem

The user asked whether the current coding agent explicitly programs concurrent
workers or whether the OS independently makes local workers concurrent, and
requested analysis without implementation.

### What was wrong

No new defect was established. Task dispatch, resident worker capacity, endpoint
admission and provider execution are distinct decisions. Treating the OS as an
automatic task parallelizer would conceal the agent's explicit dispatch loop;
treating concurrent workers as guaranteed simultaneous generations would conceal
endpoint limits and serialized application phases.

### How it was fixed

No implementation, configuration or tests changed. Traced agent/controller.py:
ready selects pending tasks whose dependencies have senior keep resolutions;
dispatch fills app.worker_limit while starts remain open; launch supplies a worker
graph continuation to processes.start without awaiting its completion. The controller
waits for FIRST_COMPLETED and can refill available slots. Each worker graph follows
sequential model/tool/phase transitions rather than parallel graph branches.

The OS's runtime/processes.py starts an asyncio driver only when explicitly asked
and enforces resident capacity. runtime/inference.py admits already-requested calls
under endpoint inflight and aggregate reservation limits; it does not interpret the
coding task dependency graph. The agent explicitly acquires verification/project
before integration/reconciliation/checks/assessment/publication and releases it at
the end. Review closes starts and drains active workers before senior review.

The standard UI preset sets max_workers and both endpoint max_inflight values to
one; generic settings default those counts to two. Git policy without task branches
further limits the coding application to one editor. Worker count covers coding
workers across bindings; ordinary juniors bind to local and specialists to cloud.
These are source findings, not measurements of an active run or GPU concurrency.
Only this required history entry and index row were added for this investigation.

### Design principle enforced or reconstructed

The agent owns decomposition, dependencies, start/stop policy and application
serialization. The OS owns explicit process execution, resource admission and
exclusive-resource guarantees. The inference provider owns token/GPU scheduling.
Concurrent execution requires both independently runnable agent continuations
and sufficient runtime/provider capacity; an available inference slot cannot
create a worker or override application dependencies and review barriers.

### Verification

Read the fix history and runtime boundary, traced current controller/worker,
repository policy, service role bindings, process drivers, admission/kernel and
settings paths. Inspected existing two-request admission overlap, four-worker
drain/replan and in-place concurrent/serial repository regression sources; none
were rerun and their historical results are not claimed as new verification.
Checked the new entry's ID/index, required sections, local references and added
whitespace. No live inference, concurrency benchmark, run/config change or
implementation test execution occurred. Existing unrelated working-tree changes
were left untouched.

<a id="fix-0068"></a>
## FIX-0068 — 2026-10-20 — Analyze an interrupted native inventory repair and retained progress

Status: investigated; no implementation changed.
Related history: [FIX-0028](#fix-0028), [FIX-0037](#fix-0037),
[FIX-0040](#fix-0040), [FIX-0041](#fix-0041), [FIX-0049](#fix-0049),
[FIX-0058](#fix-0058), [FIX-0060](#fix-0060).
Detailed evidence: [run eb66fc618354 analysis](run-eb66fc618354-analysis.md).

### Problem

The Minecraft v12 run paused during its fifth sprint's native inventory-transfer
job without a terminal Codex event. The user requested an export/codebase audit
to establish what completed and whether the run exposed bugs.

### What was wrong

The final native operation was active until shortly before its interruption and
retained 30 brokered effects. The runtime applies the endpoint's 180-second
allowance to the entire tool-using native job; its adapter sends an interrupt but
does not drain a terminal acknowledgement. The durable error conflates timeout
and task cancellation. The recorded wall interval is about 174 seconds, so the
whole-job timeout is the leading explanation, not conclusively established as
the original trigger. The safe uncertain pause itself is correct.

Separate findings: 31 malformed raw-worker replies consumed correction effort;
build-only configured checks left final regression execution ad hoc; a dirty
replacement worktree was labelled `merged: true` because its unchanged HEAD was
already an integration ancestor; and senior prompts contain conflicting legacy
and in-place descriptions of uncertain publication. Only the metadata/prompt
inconsistencies and the code/probe timeout behavior are established code findings;
no bad merge, complete-game acceptance, or newly reproduced gameplay defect is
claimed. FIX-0058's context/output safeguards worked in this run, so this is not
a recurrence of FIX-0049's unrecovered input overflow.

### How it was fixed

No implementation, configuration, game files, branches, or run state changed.
Added the linked investigation with task/commit locations, interruption facts,
owner-specific follow-ups and verification limits. Established that setup,
terrain and movement reached `pi-dev`, while inventory remained private and
save/load was pending. A new temporary-copy check passed the preserved final
inventory source's production build and four regression suites after its last
recorded test patch. This new evidence does not publish the uncertain operation.

### Design principle enforced or reconstructed

The OS owns timeout provenance, effect certainty, bounded termination handling,
and immutable execution evidence. Coding agents own reply grammar, task sizing,
Git publication projections, and meaningful product acceptance. Ongoing progress
does not authorize replaying a job with uncertain remote execution. Branch-tip
ancestry, dirty source, passing compilation, accepted increments, and objective
completion must remain distinct. Preserve the previous safeguards instead of
weakening them to avoid a pause.

### Verification

Parsed 395 effects, 1,025 artifacts, 545 checkpoints and 10,000 retained events;
matched the current agent source hash to the recorded graph digest; matched 13
preserved files to saved reads/writes/patches. An offline native stdio probe
reproduced interruption during continuous progress and the absent terminal-drain
path. Temporary-copy `tsc --noEmit`, Vite build and all four game suites passed
with Node v22.17.1. An initial copy-probe dependency lookup was corrected to use
the same ancestor dependencies resolved by the run; it was a harness error.

Focused repository checks: **83 passed in 19.64 seconds**, covering native events,
known/unknown native settlement, model retries, and context safety. Exact command
and probe results are in the investigation. Checked new documentation links,
stable ID/index, required sections, and whitespace. The temporary probe source
was removed. No live inference, run resume/reconciliation, browser playtest,
dependency installation, full suite, implementation fix, commit or push occurred.
Existing unrelated working-tree changes are unclaimed; no new regression coverage
is represented as an implemented repair.

<a id="fix-0069"></a>
## FIX-0069 — 2026-10-20 — Assess single-thread compatibility and find inconsistent worker-cap routing

Status: investigated; no implementation changed; worker-cap routing issue remains open.
Related history: [FIX-0040](#fix-0040), [FIX-0061](#fix-0061),
[FIX-0067](#fix-0067).

### Problem

The user asked whether concurrent coding workers conflict with an OS that has
one local thread. A single coordinator thread, one inference slot, one resident
worker and the single filesystem executor are different constraints.

### What was wrong

Async worker continuations do not inherently require multiple coordinator threads
or simultaneous inference. Process drivers, admission waits and exclusive-lock
waits yield asynchronously. One local inference slot queues requested calls;
the single BlockingIO executor serializes filesystem work off the event loop.
Long synchronous record/artifact operations can still delay that loop, and queued
work consumes wall-time allowance. Neither is a newly measured failure here.

A concrete coding-agent inconsistency was found: controller.tick compares active
workers with app.config.max_workers, but ProjectAgent.dispatch uses app.worker_limit.
Repository policy can reduce the latter to one when task branches are forbidden.
With configured capacity two, effective capacity one, one active worker and another
ready task, tick chooses dispatch even though dispatch immediately does nothing.
This permits repeated unnecessary controller transitions until worker/task state
changes. It is not proof of deadlock or of a failed real run. FIX-0067 traced
ownership and dispatch but did not compare these two capacity predicates. The
existing serial-repository regression checks completion, not absence of no-op
dispatch/checkpoint cycles.

### How it was fixed

No implementation, configuration or tests changed. Established the compatibility
distinctions from runtime/processes.py, inference.py, exclusive.py, blocking.py,
commands.py, shell.py and storage.py. Traced effective worker limits in the
coding services/repository and compared controller tick/dispatch decisions.
An offline probe of the actual AST-extracted tick and dispatch functions reproduced
three consecutive dispatch decisions with unchanged active workers under the
two-versus-one mismatch; setting both limits to one selected wait instead.
The owning layer for aligning those predicates is the coding agent. Only this
required investigation entry and index row were added; the issue remains unfixed.

### Design principle enforced or reconstructed

Agents supply independent continuations without assuming simultaneous execution.
The OS may interleave them on one event-loop thread and admit fewer inference
calls than there are resident workers. Scheduling decisions within an application
must use the same effective capacity as its actual dispatcher, so an intentional
serial policy leads to waiting rather than futile dispatch. Runtime thread/slot
limits do not justify changing coding dependencies, grants or review barriers.

### Verification

Read history additions since FIX-0067 and reused the previously read runtime
boundary. Inspected existing one-slot admission deadline/cancellation/fairness
and filesystem cancellation/nonblocking-loop regressions without rerunning them.
The source-extracted controller probe passed on Windows Python 3.13 and changed
no files or runtime state. It uses in-memory stubs and directly settles these
non-suspending coroutine paths; it does not measure LangGraph scheduling, extra
checkpoint cost, starvation or recursion-limit failure. An attempted separate
Windows asyncio admission/filesystem probe produced no output and was stopped;
no successful concurrency test is claimed from it. Checked the new ID/index,
required sections, referenced paths and added whitespace. No live inference,
full graph/repository tests, benchmark, run resume or implementation repair occurred.
Existing unrelated working-tree changes remain unclaimed.

<a id="fix-0071"></a>
## FIX-0071 — 2026-10-20 — Record a current-version OS concurrency and deadlock audit

Status: investigated; follow-up documented, no implementation changed.
Related history: [FIX-0067](#fix-0067), [FIX-0069](#fix-0069).
Follow-up: [CONC-01](current-iter-issues.md#os-concurrency-audit).

### Problem

The user requested a note in the current-version issue document to double-check
OS deadlocks and related progress issues under multiple workers/thread settings.

### What was wrong

The prior concurrency investigation established asynchronous compatibility and a
coding-agent capacity mismatch, but the current-version tracker had no explicit
OS audit covering resource ordering, admission, starvation and lifecycle waits.
No OS deadlock was established by this documentation task.

### How it was fixed

Followed README's tracker mapping and added open CONC-01 to current-iter-issues.md.
It covers worker/inference capacity combinations, thread/executor distinctions,
lock ordering, native callbacks, compaction/retries, cancellation/deadlines,
drain/shutdown/restart, blocking storage and diagnostic evidence. It requests
bounded progress tests for generic and coding agents, links the existing agent
finding and explicitly leaves implementation and audit verification open.
Only that note and this required history/index update changed.

### Design principle enforced or reconstructed

Record current-version verification work without presenting hypotheses or earlier
test passes as proof. The OS owns resource/lifecycle guarantees; coding-specific
capacity and Git policy remain with the agent. Concurrency recovery must preserve
authority, budgets, durable outcomes and uncertain-effect ownership.

### Verification

Read README's current-version routing, relevant tracker sections and history
updates. Checked the new note/history anchors, IDs, required sections, local links
and added whitespace. Documentation only: no tests, runtime/provider execution,
configuration change or implementation repair occurred. The expanded audit and
the FIX-0069 agent correction remain open; unrelated changes are unclaimed.

<a id="fix-0070"></a>
## FIX-0070 — 2026-10-20 — Measure historical memory pressure and OS context interventions

Status: investigated; no product implementation changed.
Related history: [FIX-0049](#fix-0049), [FIX-0053](#fix-0053),
[FIX-0058](#fix-0058), [FIX-0066](#fix-0066), [FIX-0068](#fix-0068).
Report: [historical memory audit](memory-records-audit-2026-10-20.md).

### Problem

The user requested past-run evidence for memory overwhelming context and how
often the OS compressed it, explicitly excluding agent-written summaries.

### What was wrong

No new implementation defect was established. Shared-memory content, accumulated
conversation/tool history, optional-history omission and OS model summaries need
separate measurements. The earlier implementation report traced ownership but
did not measure historical executions; counting senior memory_update proposals
or every intervened receipt as OS summarization would answer the wrong question.

### How it was fixed

No product implementation, settings or run state changed. Parsed 28 local run
exports/archives and deduplicated them to 15 runs, 13 containing 546 model effects.
Decoded 537 explicit shared-memory views; their peak content was 4,977 bytes.
Independently remeasured v11's confirmed 96,529/96,000-byte local rejection:
shared memory was 1,681 bytes while optional history added 82,108 bytes.
In v12, 32/181 preparations omitted optional history, 31 originals exceeded
their allowance, and no input overflow was recorded. All 32 belonged to one
long-running worker. Zero OS summary calls, cached summaries or applied summaries
were found; v12 explicitly disabled compaction and earlier runs predate it.
Added the linked report, serialized evidence and a link from the implementation
report. A local ignored analysis helper retains the counting method.

### Design principle enforced or reconstructed

Count interventions from retained provenance, distinguish canonical agent memory
from derived prompt views, and preserve execution/version/measurement boundaries.
OS context reduction is not automatically model-based compression. A byte-bound
preflight failure is not evidence that a provider exhausted its physical window;
disabled compaction cannot establish that compaction would never be useful.

### Verification

All 28 snapshots parsed without errors. Checked unique run selection, receipt/
prepared-record equality and bounds for all 181 v12 preparations, optional-only
omissions and complete pairs for all 32 interventions, and absent OS summary
markers. Verified size/digest integrity for 1,025 v12 artifacts, 631 v11 artifacts
and 749 artifacts in the peak-memory run export. Reconstructed saved full/required
message sizes and compared key measurements with earlier investigations.
Checked report/evidence links, history ID/index/sections and added whitespace.
This saved-record sample has incomplete early/provider-internal evidence; no
live inference, run resume, UI execution or product suite was performed. Earlier
test results and unrelated working-tree edits are not claimed as this task's work.


<a id="fix-0072"></a>
## FIX-0072 — 2026-10-20 — Align current OS and agent documentation with justified revisions

Status: implemented as documentation only; verification recorded below.
Related history: [FIX-0032](#fix-0032), [FIX-0040](#fix-0040),
[FIX-0047](#fix-0047), [FIX-0053](#fix-0053), [FIX-0054](#fix-0054),
[FIX-0058](#fix-0058), [FIX-0059](#fix-0059), [FIX-0060](#fix-0060),
[FIX-0061](#fix-0061), [FIX-0065](#fix-0065).
Decision ledger: [current design revisions](../design-docs/simplified-os/DESIGN_REVISIONS.md).

### Problem

The documentation audit found that justified implementation changes still
contradicted active OS/agent prose and launch instructions. In particular,
partial copies, provisional publication of every verdict, sole-parent task
commits, mandatory physical-memory admission and caller-owned output adaptation
could be read as current requirements despite later explicit decisions.
The user requested alignment with reasons marked at strong contradictions.

### What was wrong

Current implementation guidance, historical source contracts and future
interface sketches were interleaved without a consistent precedence/status
notice. FIX-0059 corrected the settings reference and recovery ownership, but
did not reconcile all older workspace, publication, setup and reading-route
claims. Preserving a frozen graph's provenance does not make all of its behavior
a current implementation guarantee. Conversely, ignored process constraints
cannot become approved simplifications just by editing their requirements away.

### How it was fixed

Added DESIGN_REVISIONS.md with fourteen accepted revisions, evidence, ownership
and five explicit open implementation gaps. Aligned the simplified OS and agent
specifications, runbook, implementation decisions, source consolidation, runtime
boundary, settings reference and root/design reading routes. Added dated
"edited because" markers for strong reversals and historical-status notices to
the original audit, implementation notes and static-reader guide.

Current default coding uses full tracked worktrees in the actual project,
integrates only successful verified candidates, preserves real task ancestry and
retains failed/uncertain candidates privately; explicit legacy behavior stays
distinguished. Documented generic process/capability services, bounded OS retries,
optional context preparation, interrupted-source reuse, execution-state/output
classification, provider limits, deferred physical resources/GC/migration,
serial bring-up versus concurrent admission, trust/uncertainty boundaries and
central settings with the shared library deferred.

No implementation, example configuration, schema, generated reader or source
graph changed. Data-policy and hard-allocation enforcement, process-limit
authority, paused-worker residency and generic JSON recovery wording remain
unfixed and visible. The preceding audit's memory-only observations are linked
as prior evidence, not claimed as new runtime fixes or full-suite validation.

### Design principle enforced or reconstructed

Keep current promises tied to accepted behavior and the layer that owns it.
OS execution/resource mechanisms support applications without coding workflow.
Agents retain Git policy, context semantics, canonical memory, grammar and
acceptance. Preserve historical evidence with explicit supersession; distinguish
approved scope reductions from unimplemented hard guarantees.

### Verification

Checked the applied documentation's local paths/anchors, rationale coverage,
balanced code fences and added-line whitespace. All 71 pre-existing fix entries
were preserved; the new index/entry uses the next unused ID. The existing
read-only exported-settings inventory and all five grouped-example validation
check passed. Git diff --check passed for the edited tracked documentation.
SHA-256 comparisons confirmed all 123 baseline implementation/test/example/
schema/graph/reader files unchanged. These are this task's checks; prior audit
probes and historical runtime test counts are not new validation here.

No runtime suite, live provider, hardware benchmark, run migration, commit or
push occurred. Historical FIX-0058–0060 results retain their original timing and
limits.

<a id="fix-0073"></a>
## FIX-0073 — 2026-10-20 — Record automatic and explicit memory management for this version

Status: investigated; current-version implementation work documented only.
Related history: [FIX-0053](#fix-0053), [FIX-0054](#fix-0054),
[FIX-0058](#fix-0058), [FIX-0059](#fix-0059), [FIX-0064](#fix-0064),
[FIX-0066](#fix-0066), [FIX-0070](#fix-0070), [FIX-0072](#fix-0072).
Issue: [MEM-02](current-iter-issues.md#memory-management-modes).

### Problem

After the historical memory audit, the user requested two items in the current
version's to-fix document: OS automatic memory management and explicit agent-side
memory-management support, using C memory management as an analogy. They expressly
requested documentation without implementation.

### What was wrong

Existing context preparation and optional compaction do not constitute a complete
agent memory lifecycle interface. The tracker covered a read-only inspector but
did not capture these two requested deliverables together. History growth, active
memory selection and persistent semantic consolidation require distinct ownership;
turning every omission into a compaction count would misrepresent the evidence.
No additional runtime defect was reproduced during this documentation task.

### How it was fixed

Followed README's current-version tracker mapping and added open MEM-02. It
requests a selectable automatic OS mode with reusable bounded context views and
an explicit agent interface for allocation, versioned updates, selection/paging,
pinning and release. Defined C-inspired ownership/lifetime semantics without
promising a native heap, physical memory scheduling or deletion of retained
evidence. Recorded coding-agent integration, manual/automatic/hybrid behavior,
separate intervention metrics and acceptance work. Existing services/settings
are identified as foundations, and the shared library remains deferred.
Only the tracker entry and this required history/index update changed.

### Design principle enforced or reconstructed

Agent programs own canonical memory meaning and explicit lifetimes; the OS
provides generic scoped handles, durability, bounds and optional authorized
transformations. Releasing active memory must not erase referenced execution
evidence. Planning requirements must remain distinct from implemented guarantees.

### Verification

Read relevant fix history additions, README routing, the updated runtime boundary,
current design revisions and existing MEM-01/context proposals. Reused the prior
audit's measurements as explicitly historical evidence; no snapshots were
reanalyzed and no tests were rerun. Checked new anchors, links, stable ID/index,
required sections and added-text whitespace. No implementation, configuration,
runtime/provider execution, memory API or new regression coverage was added.

<a id="fix-0074"></a>
## FIX-0074 — 2026-10-20 — Confirm the current UI setting for two Claude requests

Status: investigated; no implementation changed.
Related history: [FIX-0061](#fix-0061), [FIX-0063](#fix-0063),
[FIX-0067](#fix-0067).

### Problem

The user asked for the UI flag for two Claude requests, supplied an unrecognized
`--sim-batch 2` error, and requested launch code that does not persist capacity two.

### What was wrong

The CLI still accepts only --port, --config and --state for ui. SIM-01 remains a
design, not an implemented flag. POLYINFERENCE_LOCAL_BATCH_SIZE changes endpoint
admission alone; the normal UI preset still limits coding workers to one.
This confirms the previously documented limitation rather than a new regression.

### How it was fixed

No implementation or saved configuration changed. Established a process-only
Python launch recipe: set the environment override for that child command, wrap
agent.system_settings.ui_system_settings in memory to select max_workers:2 and
local.max_inflight:2, then call ui.serve. greeting_config imports that function
when building each new run, preserving the normal project picker and scope logic.
The existing 256000 reservation supports two 128000 contexts. A subsequent normal
launch retains its original defaults and inherited environment. Only this required
history entry/index changed; SIM-01 remains unimplemented.

### Design principle enforced or reconstructed

Application launch preferences belong to the UI/coding agent. The OS receives
ordinary admission and worker limits; it does not create independent tasks.
Invocation-only overrides must not become source defaults or shell preferences.
Actual overlap still needs independent ready work and task-branch permission.

### Verification

Read current CLI, UI configuration/project-selection paths, settings validators,
mixed example and SIM-01. An offline Windows Python 3 configuration probe used
the actual settings and AgentConfig classes: two workers, two Anthropic slots,
adequate reservation, and repeated validation passed; the original settings
function still returned one worker and one slot. No UI server, inference request,
runtime run or test suite was started. Windows Git status encountered dubious
ownership and WSL status was denied; no global Git setting was changed and no
whole-tree status or unrelated edits are claimed.

<a id="fix-0075"></a>
## FIX-0075 — 2026-10-20 — Raise Haiku generation and OS output limits to 32k

Status: implemented; targeted checks passed.
Related history: [FIX-0011](#fix-0011), [FIX-0030](#fix-0030),
[FIX-0058](#fix-0058), [FIX-0059](#fix-0059).

### Problem

The supplied terminal reported a Haiku response reaching its 8000-token
`max_tokens` limit. The user requested 32k for both Claude generation and OS
enforcement.

### What was wrong

The coding UI preset and mixed-provider example still selected an 8000-token
per-call OS limit. The Anthropic adapter already forwards that allowance directly
as `max_tokens`; there is no separate provider cap to raise in the transport.
The Anthropic-only example inherited a 4000-token allowance and 32000-token total
endpoint contexts. Earlier output-recovery fixes bounded incomplete responses
but intentionally retained the configured ceilings; their 8000-token cutoff
fixtures did not verify this newly requested larger default.

### How it was fixed

Changed `agent/system_settings.py` and `examples/agent.mixed.json` to select
`max_output_tokens_per_call: 32000`. Gave `examples/agent.anthropic.json` the same
96000 input / 32000 output allowances and 128000-token endpoint contexts with
256000-token aggregate reservations. Updated the current settings reference.
The existing API mapping now sends `max_tokens: 32000` from the same OS limit;
no provider-specific constant or generic runtime default was added.

Extended the existing UI/Haiku integration test to check the API payload, exported
configuration and durable operation limits, and accept completed responses
reporting 9000 output tokens. Updated another UI test's transport substitution
to preserve the UI context envelope rather than replace it with a smaller fixture.
Changes apply to fresh runs after relaunch; retained runs/configuration pins and
unrelated working-tree changes were not modified.

### Design principle enforced or reconstructed

Keep provider selection and application resource preferences together in the
coding configuration. The generic OS enforces the declared allowance and its
adapter forwards that same value to Claude. Reserve input plus output within the
endpoint context envelope; raising generation capacity must not bypass completion,
budget, byte-limit or recovery guards. Other agents retain their own OS settings.

### Verification

`.venv-linux/bin/python -m pytest tests/test_ui.py tests/test_anthropic.py tests/test_output_limits.py tests/test_context_safety.py -q`:
**79 passed in 47.89 seconds** under WSL. The initial run had 78 passes and one
failure because the repository-picker test substituted a 32000-total-context
endpoint; preserving the UI envelope corrected that fixture. The final run covers
the new API/OS assertions and existing cutoff, context and recovery behavior.

Ruff passed for both changed Python files. An offline probe validated all five
example configurations and confirmed the UI plus all three example Haiku
endpoints prepare `max_tokens: 32000` with matching OS allowances and adequate
context/reservations. No live provider request, server restart, historical-run
resume, full-suite run, commit or push occurred.

<a id="fix-0076"></a>
## FIX-0076 — 2026-10-20 — Triple the UI and mixed-example sprint allowance

Status: implemented; targeted verification passed.
Related history: [FIX-0011](#fix-0011), [FIX-0075](#fix-0075).
Evidence: [run a1859f8644a5 analysis](run-a1859f8644a5-analysis.md).

### Problem

The two-worker Minecraft v13 run stopped at sprint 9 with `Sprint/query limit`.
The user requested triple the budget while limiting other work to analysis and
issue documentation. It had used 11,138,203 of 64,000,000 run tokens; the token
budget was not the exhausted resource.

### What was wrong

The coding UI and mixed-provider example still used the nine-sprint allowance
established in FIX-0011. The controller stops before another senior review when
sprint reaches max_sprints, or senior_queries reaches three times that value.
This is application workflow configuration, not OS admission failure. Increasing
output limits in FIX-0075 does not change this independent sprint ceiling.

### How it was fixed

Changed max_sprints from 9 to 27 in src/polyinference/ui.py and
examples/agent.mixed.json. The unchanged controller formula raises the associated
senior-query ceiling from 27 to 81. Updated the existing exported-configuration
assertion in tests/test_ui.py and README's budget table. Generic AgentConfig's
eight-sprint default and custom configurations retain their own values. Existing
32k output, token, timeout, worker and inference limits were preserved.
Fresh UI runs after relaunch use the new allowance; retained state/configuration
pins were not edited or resumed.

### Design principle enforced or reconstructed

Raise the resource actually exhausted, at the application layer that owns it.
Explicit workflow budgets must not weaken OS grants, reservations, completion
checks, uncertainty handling or evidence requirements. More sprints permit more
work; they do not correct the separate recovery findings or establish completion.

### Verification

UI and three focused concurrency/integration regressions: **20 passed in 48.70 s**
under WSL. The exact command is in the linked analysis. Ruff passed for both
changed Python files. An AST/configuration probe confirmed UI/mixed max_sprints
27, derived ceiling 81, preserved 32k output/64m run-token allowances, and unchanged
generic default 8. This is targeted default/configuration coverage, not a live
27-sprint workload. No live inference, historical-run mutation, full suite,
commit or push. Existing working-tree changes were inspected before editing
and are not claimed as this task's work.

<a id="fix-0077"></a>
## FIX-0077 — 2026-10-20 — Analyze the first two-slot run and record recovery/concurrency findings

Status: investigated; findings remain open, no concurrency/recovery implementation changed.
Related history: [FIX-0040](#fix-0040), [FIX-0058](#fix-0058),
[FIX-0060](#fix-0060), [FIX-0067](#fix-0067), [FIX-0068](#fix-0068),
[FIX-0069](#fix-0069), [FIX-0071](#fix-0071), [FIX-0075](#fix-0075).
Report: [run analysis](run-a1859f8644a5-analysis.md).
Measurements: [evidence JSON](run-a1859f8644a5-evidence.json).
Follow-ups: [RUN13-01 through RUN13-06](current-iter-issues.md#run-a1859f8644a5-findings).

### Problem

The first two-local-inference-slot test ended before producing accepted gameplay
or user-facing save/load. The user requested concurrency-focused analysis and
current-version issue recording, without implementation beyond the budget increase
recorded separately in FIX-0076.

### What was wrong

No OS deadlock was established. Durable reservations show local concurrency two
for 230.444 s, sub-half-second admission delays and no retained active reservation
or uncertain effect at capture. The contested verification lock cleared in 6.693 s.
The controller's 59 nodes do not show FIX-0069's no-op dispatch pattern.

Agent planning instead omitted a shared test-discovery prerequisite for independent
workers, repeatedly named private commits without selecting explicit resume_from,
and bundled implementation/browser evidence into tasks that did not converge.
Seven candidates stayed private; later sprints started only one worker each.
The senior prompt contradiction and ancestry-only merged label from FIX-0068
remain open. Existing handoff tests cover explicit source reuse, not planner use;
the summary recurrence here involves a clean worker with no new commit.

The retained tail is dominated by installation-wide shell/Git ownership events
(6,960/10,000), while early concurrency journal history was pruned. This proves
serialization/churn, not a measured throughput defect. Sixty-seven malformed
application replies and 21 recovered 8k cutoffs added correction effort during
both concurrent and serial work. No causal history-mixing finding is established.

### How it was fixed

Investigation only: added the detailed analysis and measurement JSON and followed
README's current-version routing to add six open findings in current-iter-issues.md,
with owners and proposed regression requirements. No concurrency, recovery,
prompt, tool, acceptance, generated-game or retained-state implementation changed.
FIX-0076 is the only implementation change made in this task. FIX-0075's existing
32k setting is explicitly separated from the historical export's 8k configuration.

### Design principle enforced or reconstructed

Agents own task dependencies, shared coding prerequisites, source-reuse selection,
grammar and meaningful bounded acceptance. The OS owns admission, exclusive-resource
progress, execution certainty and durable evidence. Distinguish free capacity from
ready work, reservation overlap from GPU concurrency, and uncertain application
verdicts from unknown remote execution. Preserve failed/private source without
silently accepting it. An investigation must separate observed defects, metadata
semantics, historical checks and performance hypotheses.

### Verification

Parsed the 165,672,779-byte export with 790 effects, 396 model calls, 11 reports,
1,175 checkpoints and 10,000 retained events; verified size/SHA-256 for all 1,920
artifacts. Swept complete durable reservation intervals, checked history-reference
ownership, counted correction nodes/output recovery targets, and read task/plan/
assessment/lock evidence and owning source. Substituting the former 8k value into
current agent settings reproduces the recorded agent-source digest exactly.
This is not a complete historical runtime hash match. The first 24,313 journal
events are unavailable, limiting early shell-contention analysis.

The new **20-pass** local-fixture run is shared with FIX-0076; it does not fix or
fully cover these open findings. Lint/configuration checks are recorded there.
Historical project build/browser observations were inspected, not rerun. No live
provider/GPU benchmark, game verification, full suite, run resume, new concurrency
tests, implementation repair, commit or push was performed. Documentation links,
stable IDs/sections, preservation of existing entries, added whitespace and
effort-only implementation scope were checked before handoff.

<a id="fix-0078"></a>
## FIX-0078 — 2026-10-20 — Locate and summarize the current-version implementation tracker

Status: investigated; no implementation changed.
Related history: [FIX-0041](#fix-0041), [FIX-0054](#fix-0054),
[FIX-0063](#fix-0063), [FIX-0064](#fix-0064), [FIX-0069](#fix-0069),
[FIX-0071](#fix-0071), [FIX-0073](#fix-0073), [FIX-0077](#fix-0077).

### Problem

The user requested the current-version fixes/issues file and a brief on its
items, explicitly excluding implementation and the next-version backlog.

### What was wrong

The current tracker combines open implementation designs, investigation work,
completed incident fixes and historical architecture findings. Reading an old
repair direction as an outstanding defect would misstate current status. This
is a navigation/status review, not a newly reproduced runtime defect.

### How it was fixed

No implementation, configuration or tracker content changed. Confirmed README's
mapping to [current-iter-issues.md](current-iter-issues.md), distinct from
next-iteration.md. Reviewed its ten explicitly open IDs: CONC-01, RUN13-01 through
RUN13-06, MEM-01, MEM-02 and SIM-01. MEM-02 has separate automatic and explicit
memory-management deliverables. Identified older open acceptance/accounting work
and residual generalization follow-ups, separating them from completed fixes
and superseded recovery proposals in the user-facing summary.

### Design principle enforced or reconstructed

Distinguish requested work, investigation evidence, implemented behavior and
historical proposals. The OS owns generic execution/resource guarantees and
optional context mechanisms; agents own task planning, canonical memory, Git
policy and product acceptance. Summarizing a backlog does not authorize its
implementation or move deferred library work into this version.

### Verification

Read the fix history, full current tracker, README routing, repository instructions
and runtime boundary. Cross-checked statuses against later history entries,
including completed capability/lifecycle separation and OS I/O recovery.
Confirmed the tracker SHA-256 stayed unchanged. Checked the new index/entry ID,
required sections, local links, preservation of earlier history and patch
whitespace directly. Windows Git inspection reported existing unrelated changes
and filesystem interoperability errors; no reliable whole-tree diff or Git
whitespace result is claimed. WSL launch was denied; no WSL checks are claimed.
No implementation tests, live inference, UI execution, run mutation, commit or
push occurred. Only this required investigation entry/index was added.

<a id="fix-0079"></a>
## FIX-0079 — 2026-10-20 — Assess evidence, implementation readiness and ownership of seven backlog items

Status: investigated; no implementation changed.
Related history: [FIX-0060](#fix-0060), [FIX-0063](#fix-0063),
[FIX-0064](#fix-0064), [FIX-0068](#fix-0068), [FIX-0070](#fix-0070),
[FIX-0073](#fix-0073), [FIX-0077](#fix-0077), [FIX-0078](#fix-0078).

### Problem

The user requested which of RUN13-01/02/04/06, MEM-01/02 and SIM-01 have both
sufficient supporting evidence and a clear implementation scope, including the
agent/OS split. They expressly excluded implementation.

### What was wrong

The selected backlog mixes observed application defects, requested features,
performance investigations and a broader memory lifecycle design. Their common
open status does not establish equal readiness. Current context pressure evidence
shows successful history omission after the earlier overflow fix; it does not
establish that the full proposed memory allocator/lifecycle API is necessary to
repair a remaining overflow. Command-event volume likewise does not establish a
throughput bottleneck. These are assessment findings, not new runtime failures.

### How it was fixed

No implementation, configuration or tracker content changed. Assessed RUN13-01,
RUN13-02's existing explicit handoff, RUN13-06, MEM-01 and SIM-01 as sufficiently
evidenced and scoped. Recorded the concrete change and owning layer in the reply.
RUN13-04 is ready as an audit, not a selected optimization. MEM-02 has clear goals
and acceptance requirements, but its shared automatic/manual ownership, sharing,
versioning and lifetime contract needs design before the whole item is ready.
Arbitrary selective multi-candidate recovery is not implied by RUN13-02's readiness.

### Design principle enforced or reconstructed

Planning dependencies, explicit source reuse and accepted-contribution semantics
belong to the coding agent. Generic context inspection belongs to the OS viewer
and projections, without changing canonical agent memory. Simulation preferences
belong to CLI/UI and coding configuration; a generic settings-precedence mechanism
may need adjustment, but no new OS scheduler or Claude-specific kernel policy is
justified. Separate audit readiness, requested feature value and proven defects.

### Verification

Cross-read the tracker, run-a1859f8644a5 analysis, historical memory audit, relevant
fix history and runtime boundary. Inspected current repository handoff/summary,
senior prompts, command lock, snapshot prompt projection, UI/CLI and settings
validation source, plus the existing explicit-handoff regression source.
Checked the tracker hash remained unchanged, earlier history preservation, new
ID/index/sections/links and added-text whitespace directly. No tests were rerun,
exports reanalyzed, performance measured or live providers invoked. Historical
measurements and test results remain attributed to their original reports.
Only this required investigation entry/index was added; no implementation,
configuration, run state, commit or push changed.


<a id="fix-0080"></a>
## FIX-0080 — 2026-10-20 — Add concise module docs and a complete human/agent navigation tree

Status: implemented; documentation/navigation tooling verified.
Related history: [FIX-0004](#fix-0004), [FIX-0048](#fix-0048),
[FIX-0059](#fix-0059), [FIX-0072](#fix-0072), [FIX-0076](#fix-0076).
Reading route: [developer onboarding](../dev-readme.md),
[documentation index](../docs/README.md), [maintenance contract](../docs/maintenance.md).

### Problem

The README mixed onboarding, operation, architecture and development instructions
in more than 800 lines. Modules lacked concise ownership guides, and no complete
human/agent file map guaranteed that every maintained file could be found from
the README. The existing history rule required FIX entries but did not explicitly
require all affected documentation to accompany every implementation change.

### What was wrong

Repository documentation had no complete inventory, primary-doc ownership contract
or checked navigation projection. Earlier reading-route work in FIX-0072 aligned
current design promises but did not cover all source/research files or prevent
future navigation drift. Several older design links still named moved targets;
FIX-0076 updated the sprint budget but left the tester guide's nine-sprint prose.
These are developer-documentation concerns, not OS execution-policy defects.

### How it was fixed

Reduced README.md to a 15-line introduction and clear routes. Added setup.md,
dev-readme.md, focused operation/setup guides, concise module guides naming every
owned code file, and development/design/reference/test indexes. Offloaded export
and state-layout procedures separately. Preserved detailed historical designs and
evidence at stable paths; repaired their broken links without changing semantics.
The tester checklist now links shared procedures and states the current 27 sprints.

docs/file-tree.json is the authored feature/document hierarchy: every leaf has
one primary Markdown doc plus explicit related files. scripts/project_docs.py
renders docs/file-tree.html with embedded JSON and static links, enhanced by
local search/expand/collapse in docs/tree.js and docs/tree.css. The offline HTML
needs no fetch/server to operate. Validation rejects uncovered/duplicate files,
missing primary docs or code references, broken local Markdown paths/anchors,
unreachable files and stale HTML. .github/workflows/docs.yml runs it on push/PR.
tests/test_project_docs.py covers navigation and invalid-state regressions.

AGENTS.md now installs the documentation completion rule as persistent Codex
project instructions. README, onboarding, module guides, indexes, maintenance
and the HTML tree repeat it: update all affected module/setup/usage/settings/
design/issue docs and navigation in the same task, plus this ledger. The Codex
project reminder uses the repository's supported AGENTS.md mechanism.

### Design principle enforced or reconstructed

Documentation is part of implementing behavior. Give each feature one primary
explanation, make all maintained files reachable through short routes, and derive
human navigation from the same JSON agents consume. Explicit external boundaries
preserve upstream ownership; ignored state/secrets/builds/download sidecars are
not project source. Keep navigation/checking in developer tooling, outside the OS
and coding-agent runtime. Module guides preserve generic process/capability/
storage/resource/effect guarantees while Git policy, canonical memory, grammar
and acceptance remain agent-owned. Historical proposals and open gaps stay marked.

### Verification

Documentation validation/generation passed for **256 files and 116 feature/doc
leaves**, including source references, local Markdown links/anchors, README
reachability and stale-output checks. **20 documentation regressions passed**
with `.venv-linux/bin/python -m pytest tests/test_project_docs.py -q`. Ruff passed
for scripts/project_docs.py and tests/test_project_docs.py; Windows Node's
`node --check docs/tree.js` passed. Browser inspection verified the desktop tree,
filename search, automatic branch opening and the no-match state on loopback.

All **99 pre-existing implementation/test/example files** matched the task-start
SHA-256 baseline. The 56 new/reorganized overview/module guides are at most 80
lines. Task documentation diff and new-file whitespace checks passed. Concurrent
FIX-0078/0079 were read and preserved, not claimed as this task's work; the
pre-append ledger is retained for byte-preservation verification of prior text.
No application/OS behavior changed, so the full runtime suite and live providers
were not run. Code-reference/link checks do not establish semantic correctness
of every prose claim; original runtime validation records retain their own limits.
The historical live-smoke script's isolated-mode assertion is documented as a
limit rather than silently repaired or claimed as newly executed.

<a id="fix-0081"></a>
## FIX-0081 — 2026-10-21 — Reassess unfinished older backlog items against current implementation

Status: investigated; no implementation changed.
Related history: [FIX-0029](#fix-0029), [FIX-0031](#fix-0031),
[FIX-0032](#fix-0032), [FIX-0033](#fix-0033), [FIX-0041](#fix-0041),
[FIX-0046](#fix-0046), [FIX-0058](#fix-0058), [FIX-0069](#fix-0069),
[FIX-0072](#fix-0072), [FIX-0079](#fix-0079), [FIX-0080](#fix-0080).

### Problem

The user extended the backlog-readiness review to older unfinished sections,
retaining the criteria of sufficient evidence and a clear implementation scope.
The earlier instruction to perform no implementation remains in force.

### What was wrong

Historical generalization proposals mix remaining gaps with capability/lifecycle,
provider retry/isolation and output-recovery changes already implemented later.
Current source still reuses setup-selected checks for final acceptance, drops
cancelled started tasks from accounting/allocation, and gives generic output
recovery JSON-specific wording. The separate tick/dispatch worker-cap mismatch
also remains. These findings do not establish an OS deadlock, missing current
cutoff recovery or a need for a new broad fault taxonomy.

### How it was fixed

No implementation, configuration or tracker content changed. Assessed the older
report item 3 (prerequisite/task/final check separation), OSAG-07 (durable started
task accounting) and the remaining audit-item-5/U05 grammar-neutral output
feedback as ready for bounded implementation. Reconfirmed FIX-0069's concrete
agent capacity correction alongside CONC-01; the wider OS audit remains open.
Persistent tool-state lifetimes, broader diagnostic-cause contracts, residual
fault-policy redesign and additional phase-specific output strategies need more
design or evidence before treating their whole proposals as ready fixes.

### Design principle enforced or reconstructed

The coding agent owns check purpose, objective acceptance, task-start accounting
and effective dispatch policy. The OS executes granted checks and preserves
source-bound evidence; generic output assistance must preserve caller grammar.
Existing safeguards and later accepted revisions supersede historical proposals
without erasing their evidence. Readiness of a bounded correction does not imply
readiness of an entire lifecycle or fault-policy redesign.

### Verification

Read the older tracker sections, later fix history, runtime boundary and revision
ledger; used file-tree.json to review workflow, commands, retries and inspection
primary guides. Inspected current check selection/acceptance, allocation/review,
tick/dispatch, command environments, retry feedback, failure-key and summary code.
A new in-memory probe executed the actual routing functions: cancelling a started
specialist changed the reported started count from 1 to 0 and changed the next
role from worker to specialist at a 0.5 fraction. This is a function-level
counterexample, not a full cancellation/dispatch or historical-run replay.
Another source-function probe confirmed tick selects dispatch with configured
capacity two, while actual dispatch starts nothing at effective capacity one.

Checked the new entry/index, links, whitespace and earlier-history preservation;
the ordinary documentation command failed on four Windows-reencoded
Zone.Identifier sidecar names. Generation and check then passed for 256 files
and 116 leaves in an in-memory compatibility wrapper excluding only those four
download-metadata files, consistent with the documented inventory boundary.
The checker source was not changed. The current tracker and navigation contents
remain unchanged. Adjacent module/setup/settings/issue documentation needs no
behavior update because this task changes no interface, setting, path or
implementation status. No runtime suite, live provider, historical export
reanalysis, state mutation, commit or push occurred. Historical verification is
not claimed as new testing. Only this investigation entry/index was added.

<a id="fix-0082"></a>
## FIX-0082 — 2026-10-21 — Preserve a tested current-version checkpoint and schedule sequential fixes

Status: implemented for baseline preservation and scheduling only; the nine
authorized fixes remain queued, not implemented by this entry.
Related history: [FIX-0058](#fix-0058), [FIX-0060](#fix-0060),
[FIX-0079](#fix-0079), [FIX-0080](#fix-0080), [FIX-0081](#fix-0081).
Queue: [authorized current-version work](current-iter-issues.md#authorized-implementation-queue).

### Problem

The user requested a commit of the current tested version before sequential
implementation of every item assessed as sufficiently evidenced and scoped.
They required one commit after each verified fix, the new documentation contract,
preservation of earlier fixes and distinct agent/OS responsibilities. Their final
start time is 2026-10-21 01:55 America/Toronto, superseding the earlier times.

### What was wrong

The current implementation and documentation accumulated after existing HEAD
0f73c5ccd7512b94d99504cbb4ab0a8e8ac15154 on codex/simple-os-v1, with no staged
changes or checkpoint commit for this complete state. A historical passing suite
alone does not establish today's baseline. The earlier ready-only assessments
also needed a durable ordered scope for an unattended, delayed continuation.
This is release/work scheduling preparation, not a newly reproduced runtime bug.

### How it was fixed

Recorded nine sequential items and their owners in current-iter-issues.md:
effective worker capacity, historical starts, grammar-neutral OS feedback,
separate check purposes, RUN13-01/02/06, MEM-01 and SIM-01. Each item must receive
its own regression verification, related documentation and appended FIX entry,
then its own commit before the next item starts. Broader audits, MEM-02 and other
unsettled proposals remain excluded.

Created the native one-time in-chat heartbeat
implement-verified-fixes-at-1-55-a-m for 01:55:00 EDT (05:55:00 UTC), with an explicit
no-early-implementation clock guard, the full queue, baseline requirement and
preservation/verification instructions. Its schedule has a single occurrence;
computer/app availability can delay actual execution, which must be recorded
truthfully. Prepared the current source/docs for a local checkpoint commit named
chore: checkpoint verified simple-os v1 before queued fixes. No queued behavior,
default, provider request or retained run state changed during preparation.

### Design principle enforced or reconstructed

Preserve a verified recovery point before independent changes. Application task,
Git, canonical-memory and acceptance policy stays in the agent; generic authority,
resource, execution-certainty, durability and context/inspection mechanisms stay
in the OS. Every fix includes current documentation and actual checks, preserving
prior entries and recurrence evidence. A requested future start authorizes
preparation now, not early implementation or false claims of exact execution.

### Verification

New baseline full suite under WSL:
.venv-linux/bin/python -m pytest -q -rs — 349 passed, 2 skipped in 284.93 seconds.
The skips require native Linux Node/npm and Node 18+ respectively. Windows Node
separately passed all 14 tests in tests/ui_start.test.cjs; the Linux npm-specific
housekeeping regression was not rerun successfully on that platform.

Ruff passed for src, tests and scripts/project_docs.py. Native Linux documentation
generation/check passed for 256 files and 116 feature/doc leaves; no Windows
metadata compatibility wrapper was needed. The tracked patch's Git diff --check
passed. After staging previously untracked baseline files, the full staged
whitespace check reported existing extra EOF blank lines in docs/architecture.md,
docs/testing.md, setup.md, snapshots.py and system_settings.py. These five
formatting findings were preserved and recorded rather than changing the tested
baseline source before the time gate. Git also reported existing CRLF
normalization notices. SHA-256 checks confirmed all 101 baseline
implementation/test/example files unchanged before the time gate and preserved
all preceding history bytes after removing this entry/index. The queue and this
entry are the only task-authored source-document edits. Existing implementation
changes are checkpointed as prior work, not claimed as new fixes in this task.

Read the latest history, AGENTS.md, developer onboarding, maintenance/testing
guides and existing issue/ownership documents. Reviewed adjacent guides; no
behavior/settings/module documentation update is needed before implementation.
No live inference, run resume, historical-state migration, push or queued fix
implementation occurred. Future work must verify its own changes and outcomes.

<a id="fix-0083"></a>
## FIX-0083 — 2026-10-21 — Wait at the effective coding-worker capacity

Status: implemented; queue item 1.
Related history: [FIX-0040](#fix-0040), [FIX-0069](#fix-0069), [FIX-0082](#fix-0082).

### Problem

With two configured workers but a no-task-branches policy allowing one editor,
the controller repeatedly selected dispatch while the dispatcher started nothing.
The scheduled wakeup actually began at 09:14:29 EDT, not the requested 01:55;
baseline cb02d02 and a clean tree were verified before implementation.

### What was wrong

Agent controller tick compared active workers with config.max_workers, while
dispatch used the lower effective app.worker_limit. Existing serial-repository
coverage established completion, not the wait decision while another task is ready.

### How it was fixed

agent/controller.py now uses app.worker_limit in tick as dispatch already does.
The real-repository regression holds one worker at a model barrier, leaves another
task ready, checks repeated wait decisions, then releases the worker and verifies
both tasks complete on the user's serial checkout. Updated the workflow guide
and current tracker; the wider OS concurrency audit remains open.

### Design principle enforced or reconstructed

Application scheduling and dispatch must agree on effective capacity. Git policy
and task readiness belong to the coding agent; no OS scheduler, grant or resource
limit was changed. Waiting preserves the running worker's finish path.

### Verification

The new regression failed before correction with dispatch instead of wait.
Afterward tests/test_in_place_repository.py and tests/test_regressions.py passed:
38 passed in 82.39 seconds. Documentation generation/check, affected-file Ruff
and patch whitespace checks passed. Reviewed adjacent repository/settings/boundary
guides; no interface/default/navigation change requires further edits. Earlier
history is preserved. Tests use disposable repositories and local transports;
no live provider, historical run mutation, migration or push occurred.

<a id="fix-0084"></a>
## FIX-0084 — 2026-10-21 — Retain cancelled development starts in accounting and allocation

Status: implemented; queue item 2 / OSAG-07.
Related history: [FIX-0041](#fix-0041), [FIX-0081](#fix-0081), [FIX-0083](#fix-0083).

### Problem

Superseding a started task removed its historical start and specialist allocation,
allowing recovery churn to change both displayed work and subsequent role choice.

### What was wrong

Agent routing and senior inputs filtered by current cancellation state. Review
also removed every task being retired before calculating replacement allocation,
even when it had started. Pending quota reservations and executed history were
not distinguished. Prior lifecycle validation preserved valid records but did
not preserve their accounting meaning.

### How it was fixed

Dispatch atomically records started_at. Shared routing helpers retain those
starts, recognize legacy immutable :started specs, and exclude never-started
cancellations. Allocation includes pending reservations separately; reporting
counts only starts. Senior inputs expose started/reserved flags, and retiring
started tasks remain in allocation history. No OS storage schema was changed.
Updated workflow/budget/test guides and tracker status.

### Design principle enforced or reconstructed

Execution history survives later application disposition. Count distinct started
development tasks rather than resumes, and keep future reservations distinct
from executed work. Coding-agent policy owns these definitions; generic OS
records continue to provide atomicity without interpreting tasks.

### Verification

Both new timestamp/legacy-spec cases failed before correction. The final focused
setup, transition, pending-cancellation and agent-UI run passed 28 tests in 55.90
seconds. A complete scripted run parks and retires a started specialist, checks
the replacement is a worker, and verifies two starts after completion/replay.
Existing never-started cancellation and setup-exclusion coverage passed.
Documentation generation/check, changed-file Ruff and patch whitespace passed.
Reviewed inspection and runtime-boundary guides: interfaces remain unchanged.
No historical records were rewritten, live providers called or commits pushed.

<a id="fix-0085"></a>
## FIX-0085 — 2026-10-21 — Preserve caller grammar in generic output recovery

Status: implemented; queue item 3 / U05.
Related history: [FIX-0058](#fix-0058), [FIX-0072](#fix-0072), [FIX-0081](#fix-0081).

### Problem

An ordinary non-coding plain-text caller received OS cutoff-recovery instructions
requesting visible JSON despite retaining its own response protocol.

### What was wrong

The generalized OS recovery moved from the coding agent in FIX-0058 but retained
a JSON-specific phrase. Previous tests covered safety and coding responses, not
the generic feedback's effect on unrelated response grammars.

### How it was fixed

runtime/model_retries.py now requests bounded visible response content under the
same declared protocol. Added raw non-coding fixtures for plain text and JSON on
both bindings, including immutable failed attempts, replay and released admission.
Updated retry/boundary/settings guides, the revision ledger and current queue.

### Design principle enforced or reconstructed

OS assistance may adapt response size without choosing application grammar.
Callers retain semantic strategy; existing linked-intent, effect-certainty,
budget, reserve and context-remeasurement guards remain unchanged.

### Verification

All four new cases failed with the old wording. The final retry/output/context
run passed 88 tests in 20.91 seconds. Documentation generation/check, affected
Ruff and patch whitespace checks passed. No API/default/schema/navigation change
was needed; adjacent provider guides remain accurate. No live inference,
historical-state mutation, migration or push occurred. An unrelated edit in
next-iteration.md remains untouched and excluded from this commit.

<a id="fix-0086"></a>
## FIX-0086 — 2026-10-21 — Separate setup prerequisites from final product acceptance

Status: implemented; focused and full-suite verification passed.
Related history: [FIX-0019](#fix-0019), [FIX-0032](#fix-0032), [FIX-0041](#fix-0041),
[FIX-0081](#fix-0081). Queue item 4 / older report item 3.

### Problem

A setup-discovered environment-only command could satisfy final acceptance even
when the requested product was absent. Distinct product checks were not selected
or run separately from prerequisite/task checks.

### What was wrong

The agent used one setup/checks selection for every phase. Successful execution
of a check was conflated with that check having authority to establish product
completion. The OS correctly retained evidence for the requested commands; the
missing purpose and acceptance policy belonged to the coding application.

### How it was fixed

AgentConfig adds top-level prerequisite_checks and acceptance_checks. Explicit
legacy checks stay combined task/final criteria unless overridden. The agent's
CheckSelection capability adds prerequisite/task/acceptance purpose, pins initial
discovery per purpose and refuses replacement of explicit criteria. Unlabelled
discovery defaults to task and never implicitly acquires final authority.
AgentServices selects setup, task and final criteria independently; senior
assignments cannot use prerequisite-only checks. Final completion refuses missing
criteria and runs only final checks against the reviewed tree. Updated prompts,
module/configuration/boundary guides and tracker. Generic OS Check, registry,
execution/evidence and publication contracts remain unchanged. Fresh state is
required for the changed application capability schema; no old runs are migrated.

### Design principle enforced or reconstructed

The agent chooses what checks mean and what proves the objective. The OS enforces
grants and faithfully binds execution evidence to source/environment identity.
Labels do not make weak checks meaningful; setup must choose real behavior tests.
Preserve explicit user configuration while preventing automatic promotion of
discovered prerequisites into completion authority.

### Verification

Both new regressions failed before correction: an environment-only selection and
a passing syntax check each allowed premature acceptance. The affected setup,
transition and real-repository suites passed 53 tests in 111.13 seconds after
correction, including explicit product failure before implementation and success
afterward, native check selection/replay and refusal to replace pinned commands.
Full suite: 359 passed, 2 environment skips in 343.56 seconds. The additional
brokered purpose-selection/sealing regression was added after collection and
passed separately (1 passed in 1.11 seconds). Full source/test Ruff, all five
example validations and documentation generation/check passed. The skips retain
the baseline Linux Node/npm limitations; frontend coverage was exercised in the
preceding baseline and will be rerun with the later UI work. No live providers, historical-state
mutation or push occurred. Existing unrelated next-iteration edits are excluded.

<a id="fix-0085"></a>
## FIX-0085 — 2026-10-21 — Record future learned routing and quota-aware task scheduling

Status: investigated; future proposals documented, no implementation changed.
Related history: [FIX-0054](#fix-0054), [FIX-0061](#fix-0061),
[FIX-0067](#fix-0067), [FIX-0083](#fix-0083).
Proposals: [learned routing](next-iteration.md#learned-agent-routing) and
[quota-aware scheduling](next-iteration.md#quota-aware-task-scheduler).

### Problem

The user requested two ideas be retained for the next version, explicitly outside
the current version: a fine-tuned agent/settings router and a task scheduler
that submits or delays tasks according to task settings and cloud quotas.

### What was wrong

The future backlog did not capture these ideas. This was a documentation gap,
not evidence of a current runtime defect. Application selection and scheduling
policy must remain distinct from generic OS admission and execution mechanisms.

### How it was fixed

Added two dated proposals to next-iteration.md. Routing takes all agent
descriptions, available settings and the prompt, then selects an agent and its
settings. Scheduling considers all tasks, priority, fidelity, time sensitivity
and provider quota/reset windows, and requests task submission or timed deferral
through the OS. The user's five-hour/weekly Codex example is recorded as a
planning example, not a verified account entitlement. No implementation changed;
training, evaluation, timing, quota and safe interruption contracts remain open.

### Design principle enforced or reconstructed

Future proposals do not expand current-version requirements. Keep task meaning,
agent selection and scheduling policy above the OS; generic authority, resource
admission, timing and execution facts belong to OS mechanisms. Preserve support
for agents with no coding workflow and distinguish deferred starts from stopping
already-running work.

### Verification

Reviewed the future backlog, navigation, documentation maintenance, runtime
boundary, revision ledger and adjacent workflow/inference/provider guides.
Those guides and the current tracker need no edit because current behavior,
interfaces, settings and implementation scope are unchanged. Existing navigation
already owns and links the backlog; no file or feature leaf was added or moved.
Documentation generation/check and scoped whitespace checks passed under WSL.
No runtime tests or live providers were used for these documentation-only ideas.
Concurrent current-version fixes and their history entries are separate work.
