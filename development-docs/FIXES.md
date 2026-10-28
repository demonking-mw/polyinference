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
| [FIX-0087](#fix-0087) | 2026-10-21 | Record future learned routing and quota-aware task scheduling (ID corrected from duplicate 0085) |
| [FIX-0088](#fix-0088) | 2026-10-21 | Declare shared-check preparation owners before parallel dispatch |
| [FIX-0089](#fix-0089) | 2026-10-21 | Make explicit retained-source handoff actionable during planning |
| [FIX-0090](#fix-0090) | 2026-10-21 | Separate inherited ancestry from accepted task contributions |
| [FIX-0091](#fix-0091) | 2026-10-21 | Inspect retained original and effective OS context with provenance |
| [FIX-0092](#fix-0092) | 2026-10-21 | Add an invocation-only remote Haiku simulation preset |
| [FIX-0093](#fix-0093) | 2026-10-21 | Verify and close the nine-item current-version implementation queue |
| [FIX-0094](#fix-0094) | 2026-10-21 | Recheck queue documentation and correct missed overview/settings references |
| [FIX-0095](#fix-0095) | 2026-10-21 | Propose optional local-inference latency and fault simulation |
| [FIX-0096](#fix-0096) | 2026-10-21 | Add opt-in shared-TPS and fault simulation without changing normal launches |
| [FIX-0097](#fix-0097) | 2026-10-21 | Recover the exact saved Minecraft test prompt |
| [FIX-0098](#fix-0098) | 2026-10-21 | Confirm automatic project documentation instructions and their limits |
| [FIX-0099](#fix-0099) | 2026-10-21 | Create a source-backed illustrated developer onboarding guide |
| [FIX-0100](#fix-0100) | 2026-10-21 | Diagnose a Haiku timeout boundary after a retained foundation handoff |
| [FIX-0101](#fix-0101) | 2026-10-21 | Lead developer onboarding with the project vision and impact |
| [FIX-0102](#fix-0102) | 2026-10-21 | Resume a selected paused process with optional steering from the UI |
| [FIX-0103](#fix-0103) | 2026-10-21 | Verify the implemented scope of endpoint retries and UI recovery |
| [FIX-0104](#fix-0104) | 2026-10-21 | Explain the local-cloud Agent OS premise and shorten developer onboarding |
| [FIX-0105](#fix-0105) | 2026-10-21 | Expose resume beside the selected paused run |
| [FIX-0106](#fix-0106) | 2026-10-22 | Preserve the agent-router distillation tutorial and link both version trackers |
| [FIX-0107](#fix-0107) | 2026-10-22 | Add a navigable HTML learning guide for router distillation and RLAIF |
| [FIX-0108](#fix-0108) | 2026-10-22 | Compare Flash-Next Coder with the earlier coding shortlist |
| [FIX-0109](#fix-0109) | 2026-10-22 | Estimate Coder memory, speed and batching on the reported laptop |
| [FIX-0110](#fix-0110) | 2026-10-23 | Design one-click run resume across frontend, agent and OS |
| [FIX-0111](#fix-0111) | 2026-10-23 | Make Resume run directly through frontend, agent and OS |
| [FIX-0112](#fix-0112) | 2026-10-23 | Count retries and assess the saved Haiku timeout pause |
| [FIX-0113](#fix-0113) | 2026-10-23 | Explain recurring Claude pauses against official transport guidance |
| [FIX-0114](#fix-0114) | 2026-10-23 | Propose portable endpoint resilience and faster failure testing |
| [FIX-0115](#fix-0115) | 2026-10-23 | Split endpoint resilience into agent policy and independent OS mechanisms |
| [FIX-0116](#fix-0116) | 2026-10-23 | Establish shared human and agent onboarding with required project memory |
| [FIX-0117](#fix-0117) | 2026-10-23 | Implement bounded streaming lifecycle and native/caller retry policy |
| [FIX-0118](#fix-0118) | 2026-10-23 | Add explicit endpoint profiles, generic warm-up and timing inspection |
| [FIX-0119](#fix-0119) | 2026-10-23 | Move workspace scope errors to the public agent/OS port |
| [FIX-0127](#fix-0127) | 2026-10-26 | Integrate reliability fixes into the simple OS branch |
| [FIX-0128](#fix-0128) | 2026-10-26 | Establish real local Strata setup and mixed-lane capacity evidence |
| [FIX-0129](#fix-0129) | 2026-10-27 | Correct documentation drift and assess retained workflow reliability |
| [FIX-0130](#fix-0130) | 2026-10-27 | Explain long-run stopping rules and management qualification gates |
| [FIX-0131](#fix-0131) | 2026-10-27 | Verify preserved cloud-resolution fixes and distinguish review from repair |
| [FIX-0132](#fix-0132) | 2026-10-27 | Make local stalls transfer to bounded cloud coding and narrow planner assignments |
| [FIX-0133](#fix-0133) | 2026-10-27 | Plan remaining reliability fixes by ownership and map historical failure coverage |
| [FIX-0134](#fix-0134) | 2026-10-27 | Enforce static process data/allocation policy and uniform limits |
| [FIX-0135](#fix-0135) | 2026-10-27 | Retain paused residency until explicit safe hibernation |
| [FIX-0136](#fix-0136) | 2026-10-27 | Preserve bounded worker state and condition response repair on real errors |
| [FIX-0137](#fix-0137) | 2026-10-27 | Retarget unstarted recovery consumers without new resource accounts |
| [FIX-0138](#fix-0138) | 2026-10-27 | Add reproducible workflow qualification and physical-attempt metrics |
| [FIX-0139](#fix-0139) | 2026-10-27 | Validate maintained HTML/settings and correct smoke/baseline fixtures |
| [FIX-0140](#fix-0140) | 2026-10-27 | Remove conflicting native startup effort from the UI preset |
| [FIX-0141](#fix-0141) | 2026-10-27 | Bound replacement host drivers by the original account deadline |
| [FIX-0142](#fix-0142) | 2026-10-27 | Preflight browser qualification in the actual check environment |
| [FIX-0143](#fix-0143) | 2026-10-27 | Trigger qualification interruption after settled patch operations |
| [FIX-0144](#fix-0144) | 2026-10-27 | Include direct native worker effects in physical job reporting |
| [FIX-0145](#fix-0145) | 2026-10-27 | Keep bounded worker-state eviction replay idempotent |
| [FIX-0146](#fix-0146) | 2026-10-27 | Keep endpoint probing compatible with mandatory placement policy |
| [FIX-0147](#fix-0147) | 2026-10-27 | Prepare the scheduled real-local Minecraft test without early inference |
| [FIX-0148](#fix-0148) | 2026-10-28 | Record the scheduled live result and preserve checked partial delivery |
| [FIX-0149](#fix-0149) | 2026-10-28 | Isolate Minecraft live failures against frozen source and canonical evidence |
| [FIX-0150](#fix-0150) | 2026-10-28 | Verify no-edit task necessity and trace current context and worker-state behavior |


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

<a id="fix-0087"></a>
## FIX-0087 — 2026-10-21 — Record future learned routing and quota-aware task scheduling

ID correction (2026-10-21, FIX-0088): concurrent documentation assigned this
entry FIX-0085 after that ID was already allocated to output recovery. Only this
duplicate identifier/index was corrected to the next unused ID; its findings
and future proposals are preserved. This investigation is separate concurrent work.

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

<a id="fix-0088"></a>
## FIX-0088 — 2026-10-21 — Declare shared-check preparation owners before parallel dispatch

Status: implemented. Related: [FIX-0077](#fix-0077), [FIX-0086](#fix-0086)
and [RUN13-01](current-iter-issues.md#run13-01).

### Problem

Disjoint feature writers could require test discovery supplied only by another
worker's private candidate. Passing direct tests did not establish that the
configured shared runner exercised them.

### What was wrong

Planning received check names without commands/runner previews, and no explicit
shared-check preparation ownership contract. Scope isolation did not express this
dependency. Earlier Git isolation and check evidence fixes could not choose it.

### How it was fixed

AgentServices now prioritizes bounded manifest/check-argv source previews and
includes immutable check definitions in repository_context. Setup/senior prompts
require inspecting discovery, preparing it once or assigning one owner. The
agent-only SeniorProposal.check_preparations declaration names that owner; senior
validation refuses other users of the check without an explicit dependency,
using the existing bounded correction path. Existing keep-gated readiness supplies
the runtime order. Generic OS scheduling/check contracts and grants are unchanged.
Updated worker/workflow guides and tracker; configuration/setup/usage and boundary
guides were reviewed and need no new settings or OS instructions. No files moved.

Explicit history correction: concurrent future-proposal documentation reused
FIX-0085. Its identifier/index alone is corrected to FIX-0087 with a visible note;
its substantive text is retained. It was concurrent work, not this queue's fix.

### Design principle enforced or reconstructed

The coding agent owns dependency and verification policy. Private/unaccepted
infrastructure cannot be an implicit prerequisite. Grant isolation and OS command
success do not prove product behavior or test discovery. Model planning must still
identify preparation honestly; declarations cannot automatically prove arbitrary
runner semantics.

### Verification

Real-repository regression rejects an omitted runner dependency, observes the
actionable correction, accepts preparation before two separate worktrees start,
and verifies the configured runner executes both newly added tests after
integration. Affected repository/transition run: 29 passed and one final assertion
failed because history payloads live in artifacts, not record bodies; corrected
the assertion to inspect the actual model correction, then that regression passed
(1 passed, 6.19 seconds). Ruff and documentation generation/check passed; scoped
whitespace passed. No live model, historical-state mutation or push. Unrelated
next-iteration edits remain outside this commit.

<a id="fix-0089"></a>
## FIX-0089 — 2026-10-21 — Make explicit retained-source handoff actionable during planning

Status: implemented. Related: [FIX-0040](#fix-0040), [FIX-0060](#fix-0060),
[FIX-0068](#fix-0068), [FIX-0077](#fix-0077),
[RUN13-02](current-iter-issues.md#run13-02).

### Problem

Repeated replacement plans named private source in prose but left resume_from
unset; replacements therefore started from shared source without retained edits.
Legacy and in-place prompt paragraphs contradicted each other about uncertainty.

### What was wrong

Earlier coverage proved provider materialization only after manual selection.
Planning lacked actionable changed-path/conflict offers and pre-dispatch source
validation. The legacy provisional-uncertain rule leaked into in-place prompts.

### How it was fixed

RepositoryWorkspaces.source_offer reads retained private candidates or interrupted
snapshots and reports exact references, required grants, conflicts and availability.
Controller review supplies these offers; senior validation rejects unavailable
references and incomplete grants through its existing bounded correction path.
Actual creation retains its independent grant/conflict checks. Prompts require
explicit references and append the actual mode's publication rule; in-place
uncertain candidates remain private. No arbitrary multi-candidate recovery, new
Git tool, automatic reconstruction or OS interface is introduced. Updated primary
repository/worker guides, boundary and tracker. Setup/usage/settings were reviewed
and need no new configuration; navigation ownership is unchanged.

### Design principle enforced or reconstructed

Preservation is distinct from publication. The coding agent chooses source and
replacement scope; the OS enforces ordinary grants and execution certainty. A
planning preflight cannot authorize stale writes, so materialization rechecks the
current head. Unavailable reuse needs an actionable bounded correction or blocker.

### Verification

Affected in-place, agent and recovery suites: 38 passed in 104.57 seconds.
The two new senior-to-replacement cases correct unavailable references or missing
grants once, read the retained implementation through files.read, and complete
without reconstructing it or publishing the original uncertain report. Existing
interrupted-source grant/conflict refusal tests remain passing; added planning
offer assertions passed separately (2 passed, 2.27 seconds). Ruff, scoped
whitespace and documentation generation/check passed. No live provider, run-state
migration or push; unrelated next-iteration edits are excluded.

<a id="fix-0090"></a>
## FIX-0090 — 2026-10-21 — Separate inherited ancestry from accepted task contributions

Status: implemented. Related: [FIX-0068](#fix-0068), [FIX-0077](#fix-0077),
[RUN13-06](current-iter-issues.md#run13-06).

### Problem

An untouched or dirty interrupted worker inherited an integrated HEAD and was
labelled merged:true despite contributing no accepted source. Private, empty and
accepted work could not be distinguished from ancestry alone.

### What was wrong

The coding summary called merge-base ancestry merged and counted it as finished
work. Prior publication safety was correct but did not validate this projection.

### How it was fixed

Repository summaries replace merged with explicit tip/candidate ancestry, dirty
changes, code location, report/review, contribution paths and publication facts.
Publication requires matching report, generic receipt and coding integration
record. Accepted contribution additionally needs keep, current ancestry and a
nonempty candidate delta. Deterministic messages report these distinctions and
inspection needs. The UI renders them separately and labels legacy summaries as
ancestry-only/unverified. Historical records and source are not rewritten.
Updated repository/inspection/boundary guides and tracker. Archive/results/setup
and settings references were reviewed; format-v2 snapshots, commands and settings
are unchanged, so no edits/navigation changes were needed there.

### Design principle enforced or reconstructed

The agent owns Git meaning and task acceptance projections. An inherited commit,
source delta, recorded publication, senior acceptance and product completion are
separate facts. Read-only inspection must preserve that distinction.

### Verification

Five new real-Git cases passed: untouched inherited tip, dirty interrupted source,
private failed candidate, accepted nonempty change and published empty change.
Affected repository/UI projection suites: 38 passed in 79.97 seconds. Windows
Node frontend: 15/15 passed, including cautious legacy rendering. Ruff, scoped
whitespace and native documentation generation/check passed. No live provider,
historical-state rewrite or push; concurrent next-iteration edits are excluded.

<a id="fix-0091"></a>
## FIX-0091 — 2026-10-21 — Inspect retained original and effective OS context with provenance

Status: implemented. Related: [FIX-0037](#fix-0037), [FIX-0058](#fix-0058),
[FIX-0062](#fix-0062), [FIX-0070](#fix-0070),
[MEM-01](current-iter-issues.md#os-memory-context-inspector).

### Problem

The OS exposed no dedicated invocation-context inspector. Node prompts normally
showed original parts and could be silently overridden by native transport text,
even when OS preparation had omitted or summarized input. Newer compaction calls
and retries made a newest-effect heuristic misleading.

### What was wrong

Viewer joins predated context preparation and explicit retry relationships.
Runtime context tests protected originals but did not validate inspection parity.
This was a visibility gap, not canonical-memory loss or a missing memory store.

### How it was fixed

ui_os projects small artifact-free context, retry, outcome and helper metadata.
ui-monitor adds Memory / context from process/model-operation drawers, explicit
attempt selection, transitive same-process retry grouping with cycle/missing-chain
diagnostics, outstanding/outcome selection and separate compaction helpers.
Shared live/saved readers fetch exact effect/prepared/receipt records independently;
embedded matching receipts identify effective views, with explicit original fallback.
Ordered parts, trust, required/compactable flags, omissions, opaque references,
summary/source provenance and byte metrics remain inspectable. Full artifact text
loads on demand. Submission/uncertainty are separately labelled. Generation and
source-identity guards discard stale detail/content/error reads after navigation.

snapshots.detail follows model retry provenance, labels original/effective origin
and selected attempt, retains original messages separately and treats native
messages as observed transport evidence. Missing artifact blocks no longer hide
all node evidence. Live node details, manual Save and archives share this code.
Schema version 2, existing endpoints, validation/host checks and runtime/context
policy are unchanged. No canonical memory manager, agent convention or OS scheduler
was added. Updated README, UI/inspection/context guides, runtime boundary and tracker.
Reviewed settings/setup/archive guides: no new settings, storage or commands.
No files/features moved, so authored navigation remains current.

### Design principle enforced or reconstructed

The OS faithfully inspects retained explicit input and transformations; the agent
owns canonical memory and meaning. Prepared size is not submission, a dispatch
marker is not remote receipt, and neither proves termination or hidden state.
Historical records remain immutable; absent or inconsistent evidence stays visible.

### Verification

Affected UI, OS/agent projection, context, retry and history suites: 115 passed in
58.43 seconds. Windows Node frontend: 19/19 passed. Coverage includes nested
transport/output retries, malformed/cyclic/cross-process provenance, helpers,
omission pairs, prepared/original origin, lazy literal long text, overflow/no
prepared view, unsubmitted/unknown states, unchanged-checkpoint refresh, absent
records, offline saved data and stale responses after close/Back/selection/run/
snapshot changes. Missing prompt artifacts remain local errors. Ruff, scoped
whitespace and native documentation generation/check passed.

A local non-coding fixture without Git/coding records or checkpoints was inspected
through the browser in live and saved JSON modes:
effective summary, receipt/provenance, original Unicode and literal markup were
visible. The disposable loopback server/tab were closed; no provider was contacted.

<a id="fix-0092"></a>
## FIX-0092 — 2026-10-21 — Add an invocation-only remote Haiku simulation preset

Status: implemented. Related: [FIX-0061](#fix-0061), [FIX-0074](#fix-0074),
[FIX-0075](#fix-0075), [FIX-0083](#fix-0083),
[SIM-01](current-iter-issues.md#sim-batch-ui).

### Problem

Testing N overlapping local-stand-in requests required custom JSON/environment
changes. The legacy capacity environment setting changed inference slots only,
not worker capacity, and could undo an explicit selection during revalidation.

### What was wrong

The UI lacked invocation-scoped orchestration of full provider settings, workers
and aggregate context reservations. RuntimeConfig.system revalidated against the
ambient environment instead of providing a view of resolved values. Earlier
provider/admission fixes did not supply this coding UI launch policy.

### How it was fixed

UI-only --sim-batch N validates 1..16 and flows through serve/TestUI. The coding
settings module shares one complete Haiku endpoint factory and applies a pure
validated overlay: worker/local binding, N workers/slots, and reservation at least
N maximum contexts. Complete custom Anthropic fields and other role/provider
settings survive; other local protocols visibly select the full Haiku preset.
No per-call limit, budget, finishing reserve, grant or Git ordering is weakened.

Generic validation context can skip only the legacy capacity environment overlay;
base loading, merged UI validation and resolved system views preserve that choice.
No simulation setting is serialized and os.environ/default files are unchanged.
New runs save effective config; imported history/pins are read unchanged. Opening
the UI makes no billed call. Start checks a nonempty referenced credential and
retains sanitized failures through the normal startup/export path. Launch/UI
labels identify remote model, limits and task-readiness dependence. Generic
admission and Anthropic framing/retry semantics remain unchanged.

Updated README, tester/setup/launch/CLI/configuration guides, settings/UI/CLI
module docs, central settings/boundary references and tracker. Added
test_sim_batch.py to tests/README.md and JSON navigation, regenerated HTML.
Reviewed recovery/archive docs; existing exact-config/pin and read-only history
rules still apply, with conflicting ambient overrides addressed in tester docs.

### Design principle enforced or reconstructed

Provider simulation and coding task readiness belong to the application. The OS
enforces generic slots, context reservations, evidence and execution certainty.
Concurrent remote calls approximate admission/refill, not GPU batching or KV
performance. Invocation preferences cannot silently alter later launches or old runs.

### Verification

Affected simulation/UI/credential/Anthropic/endpoint/context suites: 116 passed in
58.89 seconds. Additional simulation/navigation run (including imported-history
immutability and persisted-config validation) passed 50 tests in 11.37 seconds.
One/two-slot blocking transports prove overlap limits, independent histories and
immediate refill while another slot remains held. A normal two-assignment coding
run completes through the real Anthropic adapter, and effective settings survive
Start/export. CLI 1/2/16, invalid inputs, separate launches, custom/grouped
endpoints, absent/stale/malformed ambient settings, missing/blank credentials
and sanitized 401/404/429 startup errors are covered. Full Ruff, scoped whitespace
and documentation generation/check passed (257 files, 116 leaves). Final broad
integration verification follows the per-fix commit.
Official [Haiku documentation](https://platform.claude.com/docs/en/models/haiku-5-5/overview)
was rechecked. With existing backend credentials, a read-only Models API request
returned 200 and the exact selected ID. Two concurrently issued live requests,
each capped at 16 output tokens, completed (22 and 20 total tokens respectively).
This is bounded provider readiness evidence, not a performance benchmark.

An initial test scaffold incorrectly used the default ignored state path. Its
new creation times and absence of app/effect/report history were verified; only
those new files/directories were retained under the ignored inspector fixture.
Tests now use disposable state throughout. No historical run was modified.

<a id="fix-0093"></a>
## FIX-0093 — 2026-10-21 — Verify and close the nine-item current-version implementation queue

Status: verified and complete; this closing pass changes documentation only.
Related: [FIX-0082](#fix-0082), [authorized queue](current-iter-issues.md#authorized-implementation-queue)
and the implementation entries below.

### Problem

The authorized fixes needed integrated regression verification, preservation of
earlier history, distinct ownership and a closed one-time schedule after completion.

### What was wrong

Per-fix checks alone did not establish that all nine changes worked together.
The heartbeat was still marked active after its single occurrence. No new runtime
defect was found in the closing verification pass.

### How it was fixed

Verified the existing baseline cb02d02704136be0293c4f69f4b7b5a28ab6ff97 on
codex/simple-os-v1, then implemented in the authorized order. Each implementation
received its own regression, related documentation, history entry and local commit:

| Queue item | Commit | Owning layer / implementation record |
| --- | --- | --- |
| Effective worker limit | d2d48aa | Agent control flow, [FIX-0083](#fix-0083) |
| OSAG-07 historical starts | 0ea4750 | Agent allocation/accounting, [FIX-0084](#fix-0084) |
| U05 output feedback | ac08fb2 | Generic OS recovery, [FIX-0085](#fix-0085) |
| Separate check purposes | 82c4e8c | Agent check/acceptance policy, [FIX-0086](#fix-0086) |
| RUN13-01 prerequisites | 06a21b6 | Agent planning/dependencies, [FIX-0088](#fix-0088) |
| RUN13-02 source handoff | 9a21e17 | Agent source/grant planning, [FIX-0089](#fix-0089) |
| RUN13-06 contribution facts | cd9ccd8 | Agent repository/UI projection, [FIX-0090](#fix-0090) |
| MEM-01 inspector | 1810e5d | Read-only OS inspection, [FIX-0091](#fix-0091) |
| SIM-01 launch preset | aa7140b | Agent CLI/UI policy; generic resolved validation, [FIX-0092](#fix-0092) |

Actual wakeup/start clock was 09:14:29 EDT (13:14:29 UTC), after the requested
01:55:00 EDT. No exact-time start is claimed. After verification, the native
automation tool disabled implement-verified-fixes-at-1-55-a-m with status PAUSED;
the saved status was confirmed by 10:34:18 EDT (14:34:18 UTC). No repeat run should
reapply this queue. Updated the durable queue status; no implementation changed
in this closing pass. Adjacent module/setup/usage/settings/design documents were
updated per fix and reviewed again; no further interface/navigation edits needed.

### Design principle enforced or reconstructed

Keep Git workflow, dependencies, grammar, canonical memory and acceptance in the
agent. Keep generic grants, execution certainty, resource bounds, immutable
evidence, optional context preparation and faithful inspection in the OS.
Evidence must distinguish prior tests, current checks, live readiness and limits.
Preserve old fixes and user work instead of hiding regressions or changing scope.

### Verification

Final native WSL .venv-linux suite: 401 passed, 2 skipped in 379.01 seconds.
The two baseline environment skips remain: native Node/npm housekeeping and the
Node 18+ frontend wrapper. Windows Node independently passed all 19 frontend
tests. Full src/tests/scripts Ruff passed. All five example configs validated.
Documentation generation/check passed for 257 files and 116 leaves. The complete
baseline-to-implementation diff passed Git whitespace checks. The five pre-existing
EOF findings recorded in FIX-0082 were preserved, not silently cleaned up.

A direct comparison confirmed all baseline FIX text and entries unchanged after
removing only new index rows/appended entries; current IDs are unique. FIX-0088
explicitly documents the concurrent new duplicate-ID correction, preserving that
entry's findings. The nine commits were inspected in sequence. The unrelated
development-docs/next-iteration.md working-tree edit remains unstaged and untouched.

MEM-01 also received local live/saved browser inspection; SIM-01 received the
bounded live Models API/two-request readiness check recorded in FIX-0092. No
live end-to-end Codex project run or GPU-performance claim is made. No historical
run migration, new thread, parallel agent work, branch cleanup, push, MEM-02,
RUN13-04 optimization or wider CONC-01 audit was performed.

<a id="fix-0094"></a>
## FIX-0094 — 2026-10-21 — Recheck queue documentation and correct missed overview/settings references

Status: documentation corrected; no implementation changed.
Related: [FIX-0085](#fix-0085), [FIX-0086](#fix-0086), [FIX-0093](#fix-0093).

### Problem

The user requested a fresh check that all related documentation, including the
fix history, was updated properly after the nine-item implementation queue.

### What was wrong

All nine implementation entries had the required explanation, ownership and
verification sections, and the primary guides/navigation were updated. However,
the simplified OS overview still described U05's JSON-specific wording as open,
and the central settings reference omitted prerequisite_checks/acceptance_checks
from its coding-field inventory. The design overviews also needed the explicit
check-purpose distinction and provider-correct acceptance-view wording. Link/
inventory checks cannot detect these semantic omissions. This corrects the
overbroad documentation-completeness conclusion in FIX-0093; its historical
verification record and every earlier fix entry remain unchanged.

### How it was fixed

Updated simplified-os/README.md to mark U05 resolved by FIX-0085. Completed the
agent-owned check selection inventory/defaults in simplified-os/AGENT_SETTINGS.md,
including explicit legacy fallback, purpose discovery/sealing and no implicit
promotion of discovered task checks. Aligned the current acceptance descriptions
in simplified-os/README.md and langgraph-agent/README.md with FIX-0086 and the
actual provider views. Dated notes explain these corrections. No frozen diagram,
wire schema, implementation, configuration or historical run changed.

Rechecked all nine changed implementation features through file-tree.json and
their primary module guides. Setup/usage, runtime boundary, current tracker and
other affected module guides already cover the new behavior and need no further
edits. Historical investigation/design proposals remain labelled as historical;
they are not silently rewritten into new implementation claims. Existing files
remain at the same navigation paths; regenerated/checkable HTML stays current.

### Design principle enforced or reconstructed

Documentation correctness includes semantic consistency, not only valid links.
Generic OS commands/evidence do not acquire coding check-purpose or acceptance
policy. Correct current references explicitly while preserving prior fix history
and distinguishing this documentation audit from implementation verification.

### Verification

Fresh documentation generation and --check passed for 257 files and 116 leaves;
all 20 documentation-tool tests passed in 0.26 seconds. Scoped Git whitespace
checks passed. Direct comparison confirmed every earlier FIX entry/text remains
unchanged and all 94 IDs are unique. No runtime tests or live providers were run
for these prose-only corrections; FIX-0093 retains the earlier 401-pass
implementation verification rather than claiming it as new work. The unrelated
next-iteration.md edit remains outside this commit.

<a id="fix-0095"></a>
## FIX-0095 — 2026-10-21 — Propose optional local-inference latency and fault simulation

Status: investigated; proposal only, no implementation or configuration changed.
Related history: [FIX-0061](#fix-0061), [FIX-0063](#fix-0063),
[FIX-0092](#fix-0092), [FIX-0045](#fix-0045), [FIX-0047](#fix-0047).

### Problem

The user finds the Haiku local-inference stand-in too fast and reliable and asks
for three selectable modes: normal, normal and buggy, and slow and buggy, with
TPS, batch capacity and bug rate selected before a run. Implementation is
explicitly deferred.

### What was wrong

The existing invocation-only preset changes worker/slot/context capacity but does
not pace inference or inject faults. HTTPInference sends non-streaming generation
requests and buffers response bytes. Concurrent Haiku calls alone do not model
shared local decoding throughput, variable latency or an intermittently unavailable
server. This is a simulation-fidelity limitation, not a newly established defect
in real local inference or evidence for any particular hardware failure rate.

### How it was fixed

No executable implementation, tests, launch settings or defaults changed. Proposed:

- Normal: preserve the existing provider, latency, concurrency and recovery behavior.
- Normal and buggy: preserve speed, adding configurable fault injection; suggested
  initial bug rate 5% per new inference attempt, an illustrative testing preset.
- Slow and buggy: require positive TPS, batch capacity and a 0..100% bug rate before
  Start; suggested initial values 30 TPS, batch 2 and 5%. Explain that TPS is total
  shared output throughput, not TPS multiplied by batch. Reuse the existing batch
  capacity range/worker-slot-reservation overlay without overriding Git readiness.
- Add an application-installed opt-in provider decorator or simulator transport,
  selected by CLI/UI bootstrap. Keep Haiku choices and simulation scheduling out
  of ordinary OS admission and coding planning. Decorate only the selected local
  lane; actual inference remains remote, with senior/cloud behavior preserved.
- Pace completion using actual output-token usage and an explicit estimated fallback,
  with configurable prefill/startup latency and bounded speed jitter. Target duration
  has a lower bound of startup/prefill plus output_tokens / assigned_TPS, and can
  never beat the actual provider. Share aggregate TPS among active generations,
  reallocating it as requests finish; hold inference capacity until simulated
  completion. Batch 2 at total 30 TPS means approximately 15 TPS each while both
  decode, returning to 30 when one finishes. These are model assumptions, not a
  claim to reproduce GPU continuous batching, KV use or hardware performance.
- The current buffered path can delay delivery and display synthetic progress;
  real incremental token display would require a separate streaming change.
  Use cancellable asynchronous timing, with no sleeping while holding storage locks.
  Keep provider network timeout separate from simulated completion and original
  run deadlines. At 30 TPS, 6000 output tokens take about 200 seconds before
  startup/queuing, exceeding the current 180-second endpoint timeout; merely
  wrapping the existing timeout with a sleep would create unintended failures.
- Choose a weighted fault mix: temporary server unavailable/queue rejection,
  empty or malformed response, and confirmed incomplete output. Add occasional
  endpoint-wide crash/restart episodes with a bounded cooldown so correlated
  failures can survive a retry. Define bug rate as the probability that an eligible
  new attempt starts an incident while healthy; cooldown failures are additional
  consequences, shown separately. Specify fault stage and scope explicitly.
- Inject through existing normalized provider/output outcomes so bounded retries,
  output recovery, budgets and escalation are exercised normally. Do not modify
  files, grants or successful tool results to fabricate bugs. Never execute partial
  output or claim unknown remote work has stopped. Default crash simulation can
  reject before submission; true mid-flight uncertainty is an advanced scenario.
- Record a seed and each operation/attempt's durable fault decision, timing and
  simulator version, distinguishing synthetic evidence from real provider facts.
  Replay uses retained decisions and results; real new retries get new decisions.
  Keep actual API usage/cost even when a received response is discarded or cut off.
  Persist run simulation metadata for inspection/pinning without making it a
  default for later launches or rewriting historical runs.

Reviewed inference/settings/UI/CLI module guides, provider/launch usage, onboarding,
SIM-01 and the runtime boundary. They describe current behavior correctly and need
no edit for an unimplemented proposal. No file/feature paths moved or appeared;
JSON navigation is unchanged. This history entry is the durable design record.

### Design principle enforced or reconstructed

The application selects the test environment; the simulated provider models its
service behavior. The OS retains generic admission, authority, budgets, immutable
outcomes, bounded recovery and execution certainty. Simulation must not become
coding policy or disguise remote inference as measured local performance.

### Verification

Read the existing preset, HTTP buffering/admission/error paths, related fix entries
and primary documentation. No live provider calls, benchmarks or runtime tests
were run. Planned implementation checks: normal-mode parity; shared TPS and refill;
seeded faults with durable replay; retry/cooldown exhaustion; cancellation/deadlines;
real usage versus simulated output; launch isolation and saved-run compatibility.
Documentation generation and --check were attempted using Windows Python with
process-scoped Git safe-directory configuration (no global setting changed). Both
are blocked by four pre-existing Windows-mapped Zone.Identifier paths reported
as uncovered inventory. Native WSL execution is unavailable (E_ACCESSDENIED).
No unrelated files were removed or added to navigation to hide that mismatch.
Verified prior history byte preservation when appending, unique IDs and the five
required entry sections; added-entry whitespace verification passed.

<a id="fix-0096"></a>
## FIX-0096 — 2026-10-21 — Add opt-in shared-TPS and fault simulation without changing normal launches

Status: implemented; final verification results follow below.
Related: [FIX-0095](#fix-0095), [FIX-0092](#fix-0092), [FIX-0061](#fix-0061),
[FIX-0045](#fix-0045), [FIX-0047](#fix-0047),
[SIM-02](current-iter-issues.md#sim-inference-ui).

### Problem

The user authorized implementation of the three-mode proposal, requiring complete
documentation and unchanged behavior when simulation is not enabled. Existing
--sim-batch controls concurrency only; Haiku remained too fast and reliable for
local-serving stress tests.

### What was wrong

The existing application preset deliberately models admission/refill, not latency
or faults. Pacing inside the ordinary 180-second model timeout would introduce
unintended timeouts, and treating cancelled artificial waits as lost remote work
would retain uncertain ownership even after a real response. These are new service
simulation requirements, not a recurrence of the earlier concurrency defect.

### How it was fixed

Added UI-only --sim-inference with hidden-by-default per-run controls: normal,
normal and buggy, slow and buggy; TPS, batch, bug percentage, optional seed and
advanced startup/prompt/jitter/stall/restart timing. Default active selection is
30 shared TPS, batch 2, 5%. Normal uses the original AgentConfig/client/payload;
no default schema/settings field, config pin, environment or historic state changes.

agent/inference_simulation.py owns a separate optional SimulationAgentConfig,
complete Haiku overlay, shared virtual decoder and version/identity-seeded faults.
Explicit saved simulated configs reload their resolved capacity and reinstall the
adapter in CLI execute; later ordinary launches do not inherit them. Custom
Anthropic fields and default cloud seniors survive; roles already bound local
share that lane. Active selected batch overrides --sim-batch; normal retains it.

The adapter emits existing ProviderError/ModelResponseError/IncompleteGeneration
outcomes, exercising bounded OS retry/output adaptation. Preflight unavailable/
restart makes no provider submission. Restart cooldowns affect subsequent attempts,
while actual in-flight work can complete. Output failures preserve actual usage and
retain a full diagnostic response artifact; partial output never executes. Durable
decisions/progress and simulator-version/settings pins distinguish selected/applied
faults from real provider failures. Replay uses immutable OS outcomes, with no new
fault draw, delay or remote call. Live/saved UI shows settings/seed, incidents and
last recorded virtual progress separately from actual cost and generic queue state.

Generic raw HTTP subclasses can implement generate_operation with full request
identity/prepared input under normal OS guards and the original deadline. Only
this opt-in path uses terminal_call to retrieve cancellation outcomes; the adapter
owns the separate network timeout. A focused Python 3.10 cancellation regression
caught wait_for dropping a child's terminal exception during parent cancellation;
explicit cancellation/retrieval fixes this for the new path without changing
ordinary HTTP/native dispatch. Artificial-wait cancellation after terminal evidence
settles as a known nonretryable failure; live provider interruption remains unknown.

Updated owning simulator/CLI/UI/settings/kernel/inference guides; README, setup,
tester/launch/UI/CLI/configuration usage; architecture/runtime boundary and central
settings reference; SIM-02, tests index and JSON/HTML navigation. New concise primary
module and usage guides cover controls, field bounds, record schema and limits.
Reviewed provider/auth, budget, recovery/retry, archive/export, agent services,
context and frozen design docs: existing interfaces/guarantees remain valid, with
new settings/limits/recovery documented in the linked simulator/current references.
No edits there were necessary. Earlier proposal/history/SIM-01 text stays historical.
The unrelated next-iteration.md edit is excluded; no commit or push was requested.

### Design principle enforced or reconstructed

The application chooses the test environment; the provider adapter owns service
simulation. The OS keeps generic admission, grants, budgets, immutable outcomes,
completion safety, bounded recovery and execution certainty. No Haiku-specific
scheduler, Git/task policy or canonical-memory convention enters the kernel.
Buffered virtual timing is not measured GPU/KV performance or model-quality
simulation. Coordinator loss stays conservatively uncertain despite diagnostic
simulator receipts; they do not authorize automatic reconciliation or re-execution.

### Verification

Native WSL affected suites passed 191 tests in 83.58 seconds, including complete
coding runs with/without the installed simulator. The full suite then passed
443 tests, two environment skips, in 388.22 seconds. Skips remain the baseline
native Linux Node/npm housekeeping and Node 18+ frontend wrapper (Linux has older
Node); Windows Node separately passed all 22 frontend checks, including the final
progress-panel placement. No ordinary provider/config path was changed afterward.

Final review added one known-terminal-rejection/cancellation race and a narrow
adapter correction; the final simulator suite passed all 43 cases in 19.32 seconds.
This focused run follows that correction; the 443-pass full run predates it and is
not claimed as a second full verification of the final adapter. Coverage includes
no-flag/normal canonical-config parity, legacy flags, environment/launch isolation,
field validation, shared TPS/refill, preflight versus received faults, actual usage,
retry/output-recovery exhaustion, persisted replay across restart, original deadlines,
known completion/cancellation versus live uncertainty, saved settings/history and
real coding execute/bootstrap. Original default HTTP/native paths retain the earlier
full-suite coverage and their source behavior.

Full src/tests/scripts Ruff passed. Five example configs validated. Documentation
generation and --check passed natively for 261 files and 118 leaves, with no Windows
Zone.Identifier workaround or inventory changes outside the new feature. Scoped Git
whitespace and new-file whitespace checks passed; existing history preservation and
unique stable IDs were checked. The ordinary and flagged launch screens were visually
inspected in temporary loopback fixtures; the controls were absent in normal launch
and displayed the three modes/defaults in the flagged launch. No run was started;
temporary servers and browser tabs were closed. No provider call, hardware benchmark,
old-state migration, commit or push was performed. Haiku quality, GPU/KV behavior and
exact concurrent timing remain outside this buffered simulation's claims.
No live provider request or hardware benchmark is part of this task.

<a id="fix-0097"></a>
## FIX-0097 — 2026-10-21 — Recover the exact saved Minecraft test prompt

Status: investigated; no implementation changed.
Related history: [FIX-0077](#fix-0077).

### Problem

The user requested the exact Minecraft test prompt, rather than a summary of
the game's requirements.

### What was wrong

The run analysis describes the objective but does not reproduce its original
wording. The authoritative evidence for this lookup is the saved application's
config.json objective, not a worker's derived assignment or later interpretation.
No runtime defect was established.

### How it was fixed

Read the saved configurations under .polyinference/ui/runs. All eleven matching
Minecraft game objectives agree, including v13 run a1859f8644a5. Preserved the
original capitalization, spelling and punctuation in the answer:

```text
build me minecraft in 2d. You should implement all features they have until 2020, given that the feature works in 2d. THere should be save/load feature for the world(s) along with your progress. The game itself should have very similiar design to the actual minecraft game, but the menu/other-stuff you should design your own. You are to create a git repo, create a branch called pi-dev, and use that as your working main branch
```

No implementation, saved run or configuration changed. Reviewed the investigation
index, v13 analysis, onboarding and documentation-maintenance/module guides;
their existing behavior descriptions remain accurate and need no edit. No file
or navigation path was added or moved; JSON navigation remains unchanged.

### Design principle enforced or reconstructed

Quote retained user input exactly and distinguish it from agent interpretations.
Reading historical evidence does not authorize executing the quoted objective
or changing the application, OS or saved run.

### Verification

Parsed all twelve saved configurations whose repository names contain minecraft:
eleven contain the identical game prompt; the remaining v8-labelled configuration
contains an unrelated fix-history request and was excluded from that comparison.
No game, provider request or runtime test was run. Exact case-sensitive comparison
confirmed the recorded quote matches v13's saved objective; all 97 fix IDs are
unique and this entry contains the five required sections. Windows Python
documentation generation and --check both failed on the four pre-existing
Windows-mapped Zone.Identifier inventory paths already recorded in FIX-0095.
Native WSL execution returned E_ACCESSDENIED. No unrelated metadata or navigation
was changed to conceal that environment limitation; other working-tree changes
are not this lookup's work.

<a id="fix-0098"></a>
## FIX-0098 — 2026-10-21 — Confirm automatic project documentation instructions and their limits

Status: investigated; no implementation changed.
Related history: [FIX-0004](#fix-0004), [FIX-0080](#fix-0080),
[FIX-0094](#fix-0094), [FIX-0097](#fix-0097).

### Problem

The user asked whether project agents automatically receive rules specifying
which documentation to write or update after implementation.

### What was wrong

No missing instruction was established. The distinction needing clarification
was between automatically supplied project guidance, an agent following it,
and structural checks proving documentation is complete and accurate.

### How it was fixed

Confirmed root [AGENTS.md](../AGENTS.md) was supplied to this Codex chat as
project instructions. It requires affected module/setup/usage/configuration/
design/issue documentation, navigation and this history to be maintained in
the same task, adjacent-doc review with reasons for no edits, and actual checks
in the handoff. Delegation must carry the reading/reporting requirements.
[Maintenance](../docs/maintenance.md) and
[onboarding](../dev-readme.md) provide the detailed completion rules.

The [official instruction-loading guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
confirms Codex discovers AGENTS.md guidance at run startup. This is persistent
project guidance, not a universal system prompt for every agent product.
Other harnesses need to load or otherwise receive it. Instructions do not
by themselves prove compliance. The [CI workflow](../.github/workflows/docs.yml)
runs the navigation check on push/PR; it checks coverage, ownership, paths,
links, reachability and generated HTML, not semantic accuracy or automatic
writing of the required prose.

No implementation or instruction changed. Reviewed AGENTS.md, maintenance,
onboarding, documentation/development indexes, the documentation module guide,
JSON navigation, checker and CI workflow: their existing descriptions cover
these rules and need no edit. No file appeared or moved; navigation is unchanged.

### Design principle enforced or reconstructed

Keep maintenance obligations discoverable through persistent project guidance.
Distinguish instruction delivery, agent compliance and machine-verifiable
structure; accurate prose still requires review. Repository maintenance belongs
to developer tooling and does not impose coding workflow on the runtime OS.

### Verification

Read the current project instructions, related history, owning documentation,
checker/CI paths and fetched official OpenAI documentation. Windows Python
`python scripts/project_docs.py` and `python scripts/project_docs.py --check`
both exited 1 on the same four pre-existing Windows-mapped Zone.Identifier
inventory paths recorded in FIX-0095/FIX-0097. No unrelated metadata or
navigation was altered to conceal that limitation. Checked unique history IDs,
the five required sections, added-text whitespace and byte preservation of all
prior history. No runtime tests, provider calls or alternative-harness startup
were run; other working-tree changes are not this investigation's work.

<a id="fix-0099"></a>
## FIX-0099 — 2026-10-21 — Create a source-backed illustrated developer onboarding guide

Status: implemented as documentation only.
Related history: [FIX-0004](#fix-0004), [FIX-0048](#fix-0048),
[FIX-0072](#fix-0072), [FIX-0080](#fix-0080), [FIX-0094](#fix-0094),
[FIX-0096](#fix-0096), [FIX-0098](#fix-0098).

### Problem

New developers had concise setup/module references but no complete HTML learning
route combining the supplied onboarding recording, its whiteboard, LLM background,
stack selection and the repository's contribution/documentation obligations.
The lecture also contains broader scheduling ideas that could be mistaken for
already implemented behavior when presented without current-code qualification.

### What was wrong

This was a developer-documentation and discoverability gap. The recording and
handwritten resource sketch were not a navigable repository guide, and the original
brief/frozen diagrams do not uniformly describe later runtime changes. The owning
layer is repository onboarding, not the application OS or agent control flow.
Earlier navigation work in FIX-0080 supplied ownership/checking but did not include
this lecture-derived learning artifact.

### How it was fixed

Added [docs/onboarding.html](../docs/onboarding.html), a self-contained offline
field guide with twelve chapters, five accessible SVG diagrams and an interactive
resource-handoff diagram. It covers LLM/token/context/serving basics, actual
agent/OS/provider boundaries, six contribution paths, platform/provider setup,
the greeting fixture, checks and acceptance, security/scope/replay/uncertainty,
settings, evidence inspection and first-contribution reporting. Documentation
coverage includes primary-doc ownership, JSON/generated navigation, all five FIX
sections, recurrence/supersession, investigation-only entries, adjacent-doc review,
actual verification and persistent AGENTS.md guidance.

Preserved the roughly 22:26 lecture as timestamped editorial notes plus all 187
automatically transcribed segments, and embedded the supplied whiteboard image.
Current behavior, teaching examples and proposed scheduler/model-swap/auxiliary
endpoint ideas are labelled separately. Local lane versus physical location,
account-dependent quota examples, synthetic inference timing and unresolved U01–U04
guarantees are explicit. The automated transcript remains labelled source material;
editorial text qualifies informal capability/cost/privacy/uniqueness claims.

Updated README.md, dev-readme.md and docs/README.md with entry links. The existing
developer-onboarding leaf owns the HTML under dev-readme.md in file-tree.json;
regenerated file-tree.html. No new Markdown hub or runtime dependency was added.
The page provides local checklist persistence, glossary filtering, copy controls,
responsive layouts and print styling without analytics or network asset loads.

Reviewed maintenance/documentation tooling, setup/install/provider/configuration/
launch/UI/recovery guides, architecture, agent/OS module guides, current designs,
settings, issues and future backlog. Their behavior, interfaces, defaults and
maintenance rules remain unchanged; they need no edits beyond the three navigation
entry points and primary ownership above. Earlier records and unrelated working-tree
implementation/simulator/future-backlog changes remain separate work.

### Design principle enforced or reconstructed

Onboarding should connect an author's explanation to current source without turning
historical vision or a teaching analogy into an implementation promise. Keep coding
workflow, Git, canonical memory and acceptance in the agent; keep generic authority,
resource/effect guarantees and optional context services in the OS. Scheduler policy
and provider GPU scheduling remain separate. Developer navigation/documentation is
maintained in the same task and does not impose coding prerequisites on general OS
agents. Preserve original evidence and make transcription uncertainty visible.

### Verification

Native WSL documentation generation and --check passed for 262 files and 118 leaves;
all 20 tests/test_project_docs.py checks passed in 0.75 seconds. An additional
HTML-specific standard-library check passed 146 local links/anchors, unique IDs,
five SVG title/description references, the interactive diagram, all 187 transcript
segments, embedded JPEG integrity, no unresolved placeholders and one primary owner.
Extracted inline JavaScript passed Windows Node's node --check.

Browser QA on a temporary loopback server verified desktop (1280 viewport) and
390-pixel phone layouts without document horizontal overflow. All six stack
selections, six resource states/reset/end disablement, glossary match/no-match,
command copy and exact clipboard text, checklist reload persistence/reset, and
photo/transcript disclosures passed. Photo loading and retained segment count were
confirmed; the browser reported no warnings/errors. Preview screenshots were saved
outside source. The initial sandboxed preview could not reach local sockets;
an authorized WSL loopback server returned HTTP 200 and enabled successful QA.
Print styling is included, but no exported PDF was independently rendered.

Final navigation generation/check and scoped Git whitespace passed again for
263 files and 119 leaves after concurrent FIX-0100 added its separate investigation
and navigation leaf. That work is preserved and excluded from this task. Direct
comparison preserved all 98 prior FIX bodies/text bytes, confirmed unique IDs,
the complete source transcript and unchanged adjacent prose/navigation after
excluding only the explicit onboarding and concurrent investigation additions.
All 98 implementation/test/example hashes captured for the final handoff remained
unchanged. New HTML/entry-point whitespace passed; the developer hub stays under
80 lines. The five required FIX sections are present. Git only reported its
existing CRLF-to-LF normalization notices, not whitespace errors.

The supplied audio was transcribed with the user-authorized OpenAI API request.
The transcript is automated, not a manually word-audited recording. No PolyInference
live coding/provider workload or full runtime suite was run for this documentation
change. No runtime implementation, retained run, schema, account setting, commit or
push was changed. Prior history byte preservation and final checks are recorded
by the task's direct comparison; concurrent FIX-0097/FIX-0098 are preserved and
are not this onboarding work.

<a id="fix-0100"></a>
## FIX-0100 — 2026-10-21 — Diagnose a Haiku timeout boundary after a retained foundation handoff

Status: investigated; no implementation changed.
Related: [FIX-0045](#fix-0045), [FIX-0068](#fix-0068), [FIX-0086](#fix-0086),
[FIX-0088](#fix-0088), [FIX-0089](#fix-0089), [FIX-0096](#fix-0096).
Report: [run 7086c575ef94](run-7086c575ef94-analysis.md).

### Problem

Minecraft v14 paused in sprint 2 with Endpoint disconnected; execution requires
reconciliation. The user requested diagnosis of the supplied export, not a repair
or execution of the game-building instructions embedded in that evidence.

### What was wrong

A submitted raw Haiku request became uncertain 180.005032 seconds after activation,
matching its 180-second call timeout. Timeout is the leading explanation, but the
HTTP adapter maps read timeout, transport disconnect and cancellation to the same
UnknownExecution message and the saved effect omits the chained cause. Its exact
original trigger cannot be proven. This is not FIX-0068's native tool-job incident;
that prior investigation does not establish the cause of this raw HTTP failure.
Known-ended retry coverage in FIX-0045 intentionally excludes unknown execution.

Earlier, the single foundation owner lacked the four exact tests/acceptance paths
required by its runner. FIX-0088 covers declared preparation owners/dependencies,
not mandatory filenames versus one owner's grant. The next plan corrected those
paths and explicitly restored all eleven retained foundation paths, demonstrating
FIX-0089's handoff worked. Only setup reached pi-dev; direct private tests passed
36/36 historically, but neither development task produced an accepted contribution.
The export has no inference fault/latency simulation configuration or records.

### How it was fixed

No implementation, configuration, game source, Git or retained run state changed.
Added the linked report, current-version follow-ups, investigation index entry and
JSON/HTML navigation. Established the failure timeline, source preservation and
limits; diagnostics and planning improvements remain open. Reviewed adjacent
inference/retry, worker/workflow, repository, inspection/command, configuration/
recovery and simulator guides plus boundary/revision references. They still
accurately describe current behavior and need no interface/settings edits.
Concurrent FIX-0098/FIX-0099 documentation is preserved as separate work.

### Design principle enforced or reconstructed

The OS/adapter owns accurate transport/timeout facts, immutable evidence and
execution certainty; the coding agent owns feasible task grants, check contracts,
source selection and acceptance. Preserve unknown-effect ownership rather than
silently retrying. A preserved or tested private delta is not an accepted product.
Distinguish measured timing, likely cause, confirmed findings and proposed repairs.

### Verification

Parsed 659 records, 3,600 unpruned events, 119 effects, 326 artifacts and 148
checkpoints. All artifact sizes/SHA-256 digests verified; current agent-module
hash matches the saved graph digest, not a complete historical runtime hash.
Reconstructed the 180.005032-second interval and 0.001052-second admission delay.
A three-case source-derived offline probe confirms ReadTimeout, disconnect and
cancellation share the diagnostic; no network/event loop or live provider was used.
No game/playtest, runtime suite, reconciliation, resume, migration, commit or push.
Windows Python documentation generation and --check each exited 1 on the four
pre-existing Windows-mapped Zone.Identifier paths (FIX-0095). Native WSL execution
returned E_ACCESSDENIED. An in-memory compatibility wrapper excluding exactly those
four metadata paths, consistent with the documented inventory boundary, then
regenerated and checked navigation successfully: 263 files, 119 leaves. Checker
source and metadata files were unchanged; ordinary native verification remains
unavailable here. All 98 implementation/test/script/example baseline files retain
their SHA-256 hashes. All prior history bytes, including concurrent FIX-0099, are
preserved after removing this entry/index row. IDs/required sections and scoped
added-text whitespace checks passed. Historical test results are not new tests.

<a id="fix-0101"></a>
## FIX-0101 — 2026-10-21 — Lead developer onboarding with the project vision and impact

Status: implemented as documentation only.
Related history: [FIX-0099](#fix-0099), [FIX-0080](#fix-0080).

### Problem

The user found that the onboarding HTML reached stack selection and developer
instructions before sufficiently pitching the project, its vision, potential
impact and general background.

### What was wrong

The opening of FIX-0099's guide prioritized contribution mechanics. Its short
purpose explanation did not first establish why the project should exist or what
its integration ambition could enable. This is editorial sequencing owned by
developer onboarding, not a defect in the agent or OS implementation.

### How it was fixed

Rewrote the hero in [docs/onboarding.html](../docs/onboarding.html) around local
compute, cloud intelligence and one usable system. Added a leading Why PolyInference
chapter covering the workflow/resource problem, longer-term vision, potential
economics/control/access benefits, an illustrative coding workflow, systems
integration as the contribution, measurable success criteria and the current
prototype's position. Grounded the pitch in the project brief and supplied lecture,
with aspirations and illustrative uses distinguished from implemented behavior.

Moved the contribution entry cards behind that introduction, added an explicit
transition into onboarding, updated local chapter navigation/metadata, and removed
duplicate research/product summaries from the following architecture introduction.
Updated the primary dev-readme.md description and refreshed the standalone delivery
copy with links to this checkout. Technical chapters from LLM foundations onward,
all diagrams, the whiteboard, transcript, CSS and interaction script are preserved.

Reviewed README/docs-index routes, setup, architecture/module guides, maintenance
and JSON ownership. Their existing links, behavior, interfaces and rules remain
accurate, so no changes were needed there. No file/feature moved or appeared;
file-tree.json remains byte-identical. Generated/checkable navigation is current.

### Design principle enforced or reconstructed

Explain purpose and intended impact before asking readers to learn implementation
details or follow contribution procedures. A stronger project pitch must still
separate aspiration, research questions and measured/current capabilities. Existing
agent/OS/provider boundaries and contribution obligations remain intact.

### Verification

Documentation generation and --check passed for 263 files and 119 leaves. The
HTML-specific check passed 151 local links/anchors, unique IDs, five accessible
SVGs plus the interactive diagram, all 187 transcript segments, embedded image
integrity and primary ownership. Extracted JavaScript passed node --check.
Byte comparison confirmed every technical chapter from foundations onward and
the CSS/script unchanged from this revision's starting file; JSON ownership is
unchanged and the developer Markdown hub remains under 80 lines. New/edited HTML
and primary-guide whitespace checks passed.

Browser QA verified the revised opening at 1280 and 390 pixels, its new navigation
and the pitch-before-onboarding order, with no page horizontal overflow or browser
warnings/errors. Updated desktop/phone preview images were saved outside source.
The delivery copy preserves the same CSS/script and full embedded transcript.
Earlier FIX-0099 test counts are historical; no runtime suite or provider workload
was run for this editorial-only change. The append preserves all earlier history
bytes; unrelated working-tree changes are not this task's work.

<a id="fix-0102"></a>
## FIX-0102 — 2026-10-21 — Resume a selected paused process with optional steering from the UI

Status: implemented; verification recorded below.
Related: [FIX-0027](#fix-0027), [FIX-0032](#fix-0032), [FIX-0045](#fix-0045),
[FIX-0047](#fix-0047), [FIX-0092](#fix-0092), [FIX-0100](#fix-0100).
Feature: [UI-RESUME-01](current-iter-issues.md#ui-process-resume).

### Problem

The frontend could start fresh runs and steer active runs, but selecting a paused
process exposed no control to request continuation, optionally with new instructions.
A plain reopen also cannot clear a paused workflow or safely replay a failed effect.

### What was wrong

There was no frontend/API resume transport or generic durable operator resume
signal. Existing explicit application recovery was reachable only through coding
entry points. UI launch configuration overlays must not replace saved settings,
and starting a new run would discard the user's selected execution identity.
FIX-0027/0045/0047 intentionally preserve original failed/unknown operations; a
button that merely toggled status or resubmitted uncertain work would bypass them.

### How it was fixed

runtime/processes.request_resume validates a paused, noncancelled process and
refuses runtime-wide submitting/active/uncertain effects, then atomically retains
an immutable resume-request and process-control link. It interprets no coding
records or Git policy and does not itself change execution state or grants.

The UI's local-origin POST /api/resume selects the existing run/process, reloads
its exact saved config without new-launch/environment overlays, records the signal
and serializes the background driver with other launches/resumes. An attached
--state can use a matching --config. cli.execute's application adapter validates
program pins and chooses the existing linked model retry, accepted-output recovery
or senior review; optional text enters normal steering. Outcomes and asynchronous
pin/thread failures remain durable/visible, preserving paused state and releasing
the UI's active flag after rejection. Ordinary Start uses the shared driver.

The paused-process drawer supplies optional steering, duplicate-send protection,
per-run/process drafts, visible errors, live eligibility refresh and stale-response
guards. Offline JSON snapshots cannot signal. No configuration schema, agent
module/prompt fingerprint, resource allowance or historical run was changed.
The FIX-0100 run still requires evidence-based reconciliation of its unknown call.

Updated owning UI/inspection/process/CLI guides, UI/recovery/retrying/CLI usage,
the runtime boundary, onboarding feature descriptions, tests index and current
tracker. Reviewed setup, launch, settings, simulator, archive/export, SDK and
agent-workflow/repository guides: existing interfaces/guarantees still apply and
need no additional edits. No file/feature path appeared or moved; JSON ownership
is unchanged and generated navigation is checked below. Concurrent onboarding
FIX-0101 and pre-existing implementation/simulator changes are separate work.

### Design principle enforced or reconstructed

The OS records generic operator intent and enforces execution certainty; the
application owns continuation, coding recovery, steering and acceptance. Resuming
is an explicit new control request, not a change to failed-effect history or proof
of remote termination. Preserve saved authority, source, configuration/program
pins and real budgets; viewing a snapshot cannot authorize execution.

### Verification

Initial new regressions: 8 passed (HTTP controller/worker resume with and without
steering, plus generic non-coding signals). Windows Node passed all 25 frontend
checks, including duplicate sends, drafts, stale replies, live blockers and offline
snapshots. A wider first run had 76 passes and one validation-message failure
caused by Windows default decoding during the UI driver extraction. Restored the
original Unicode; the pre-existing validation test provides the regression check.
Additional coverage retains unknown effects without recording a signal and exposes
program-pin/thread-launch rejection without queuing steering or leaving active UI
ownership behind. No live provider, original-run resume/reconciliation, commit or
push was performed.

Final affected suites passed: 78 tests in 124.62 seconds across test_ui,
test_runtime_general, test_recovery, test_incident_fixes and test_sim_batch.
The final source/test Ruff check passed. The 25-pass Windows Node run exercises
the final frontend source; subsequent changes affected backend failure handling
and documentation only. Native WSL documentation generation and --check passed
for 263 files and 119 leaves without a Windows metadata workaround. Scoped Git
whitespace passed, with only the existing FIXES.md CRLF-normalization notice.

Direct comparison confirms the agent-module fingerprint is unchanged, and all
prior FIX text/bytes (including concurrent FIX-0101) are preserved after removing
this entry/index row. IDs, required sections and task-added whitespace were checked.
Onboarding bytes outside the two UI feature descriptions are preserved. This is
focused recovery/frontend verification, not a full runtime-suite or live-provider
claim. No generated game, real run or provider operation was resumed by these tests.

<a id="fix-0103"></a>
## FIX-0103 — 2026-10-21 — Verify the implemented scope of endpoint retries and UI recovery

Status: investigated; no implementation changed.
Related: [FIX-0045](#fix-0045), [FIX-0047](#fix-0047), [FIX-0058](#fix-0058),
[FIX-0085](#fix-0085), [FIX-0100](#fix-0100), [FIX-0102](#fix-0102).

### Problem

The user asked whether an implemented feature retries endpoint failure for any
reason, requesting a check of both fix history and current source after the UI
resume feature. Automatic retry, explicit recovery and unknown-execution handling
must not be conflated.

### What was wrong

No new runtime defect was established. FIX-0045 implemented selective, bounded
known-ended inference retries, not unconditional retry. The current kernel calls
ModelRetries after a returned operation result; submitted transport failure or
cancellation instead raises UncertainEffect and bypasses that path. The retry
filter also rejects unknown effects, nonretryable errors, stopped/cancelled
processes, native jobs with brokered effects and exhausted safety allowances.
FIX-0102 preserves these conditions rather than broadening retry eligibility.

### How it was fixed

No implementation, configuration, UI or retained run changed. Traced
runtime/model_retries.py, inference.py, kernel.py, processes.py, cli.apply_resume,
settings and existing tests. ProviderError marks rate_limit, service_unavailable,
connection and admission retryable. HTTP rejection maps 429 and 5xx accordingly;
400/401/403 and other permanent rejections are not blind-retried. Received empty/
malformed output uses retryable ModelResponseError. Known-unsubmitted connect/
pool failures can retry, while other transport errors and cancellation become
UnknownExecution. Default model_call_retries is one extra attempt (allowed 1..3),
with 100 ms exponential base delay, Retry-After, a 60-second maximum wait and
original deadlines/budgets. Output-limit recovery separately asks for smaller
complete content, default at most two eligible adaptations. FIX-0047 keeps OS
retries separate from the application's explicit recovery allowance.

Confirmed the UI Resume adapter requests an existing known-model recovery,
accepted-output recovery or senior review. Its generic OS signal refuses unsettled
execution; it does not automatically reconcile the FIX-0100 Haiku request.
Reviewed retry/inference/CLI/process/UI/recovery/settings guides, runtime boundary
and navigation ownership. They already describe this scope accurately and need
no edit. No files/features appeared or moved; authored navigation is unchanged.
Only this required investigation entry and its index row were added.

### Design principle enforced or reconstructed

Adapters retain completion, submission and failure facts; the OS enforces bounded
recovery and effect certainty. Applications own corrected intents, continuation
and acceptance. A known failure, a usable retry and unknown remote termination
are different facts. An operator resume signal cannot erase original outcomes,
reset budgets or authorize blind replay of uncertain/tool-bearing work.

### Verification

Fresh WSL tests/test_model_retries.py: 43 passed in 9.00 seconds. Coverage includes
empty/malformed replies, 429/503/connect versus disconnect/400/401/403, backoff,
restart/replay, budget/cancellation/deadline guards, native-effect restrictions and
output-adaptation composition. Source inspection additionally confirms the full
5xx mapping and configured defaults; the matrix is not a live provider outage.
No provider request, original-run resume/reconciliation, implementation edit,
full-suite run, commit or push was performed. Native documentation generation
and --check passed for 263 files and 119 leaves. Scoped Git whitespace passed
with the existing CRLF-normalization notice only. Unique IDs, required sections,
added-text whitespace and byte preservation of all prior history were verified.

<a id="fix-0104"></a>
## FIX-0104 — 2026-10-21 — Explain the local-cloud Agent OS premise and shorten developer onboarding

Status: implemented as documentation only.
Related: [FIX-0099](#fix-0099), [FIX-0101](#fix-0101),
[FIX-0102](#fix-0102).

### Problem

The onboarding opening did not directly connect the user's core points: costly
cloud capability, local inference without per-token fees but weaker/slower results,
their complementary roles, tools/docs/MCP, and agents running like programs on
shared resources managed by an OS. The whole guide also felt too long and technical.

### What was wrong

FIX-0101 improved purpose-first sequencing but added a long pitch while retaining
the dense technical chapters from FIX-0099. Earlier link/layout checks could not
establish editorial concision or capture this more specific framing. This is an
onboarding explanation problem, not a runtime or model-routing defect.

### How it was fixed

Rewrote [docs/onboarding.html](../docs/onboarding.html) around local/cloud
complementarity, agents as programs, high concurrency and the OS resource bridge,
leading directly into the architecture. Explained the cost premise as no local
per-token provider fee, with hardware/power still counted; concurrency uses spare
capacity rather than accelerating each call. Retained the current remote-Haiku
stand-in and explicit separation of present behavior from the broader vision.

Shortened every main chapter, the lecture recap, stack paths and glossary. Replaced
technical diagram labels/captions and interactive example wording with plain terms.
Preserved five diagrams, the resource example, all setup command blocks, required
reading, safety/ownership restrictions, documentation obligations and FIX rules.
The original whiteboard and complete 187-segment transcript remain unchanged in
the folded source archive. Updated dev-readme.md's description and refreshed the
standalone delivery copy and desktop/phone previews outside tracked source.

Reviewed README, docs index, architecture, setup/provider references, maintenance,
module ownership and runtime boundary, including FIX-0102's paused-process resume.
These retain the same routes, interfaces, behavior and rules, so they need no edits.
No feature/file path appeared or moved; JSON ownership and generated tree HTML
remain byte-identical. Unrelated working-tree changes are separate work.

### Design principle enforced or reconstructed

Explain the project using concrete resources and agent programs before exposing
implementation terms. Keep policy and final acceptance in the agent, generic
execution in the OS and GPU scheduling in the provider. Shortening onboarding must
preserve the contribution contract and source evidence, not weaken obligations or
present future capabilities as implemented guarantees.

### Verification

Main-guide text before the source appendix fell from 9,103 to 5,343 words (41.3%),
using the same counter excluding SVG/style/script content. Documentation generation
and --check passed for 263 files and 119 leaves. The HTML-specific check passed
128 local links/anchors, unique IDs, five accessible SVGs, embedded JPEG integrity,
all 187 transcript segments and one primary owner. Extracted JS passed node --check.

Preservation checks passed for the photo/transcript, seven setup command blocks,
CSS and interaction logic (only resource-story text changed), JSON/generated tree,
edited-line whitespace and the primary guide's under-80-line length. Browser QA
verified desktop (1280px) and phone (390px) openings without horizontal overflow,
architecture navigation, resource transitions through completion/reset, stack
selection and glossary filtering. No browser warnings/errors were observed; the
temporary viewport was reset. Delivery HTML retains the same embedded assets,
CSS/script and links resolved to the checkout. No runtime suite, provider workload,
commit or push was performed for this editorial-only change. Earlier test results
are historical. Appending this entry/index row preserves all prior history bytes.

<a id="fix-0105"></a>
## FIX-0105 — 2026-10-21 — Expose resume beside the selected paused run

Status: implemented.
Related: [FIX-0100](#fix-0100), [FIX-0102](#fix-0102),
[FIX-0103](#fix-0103).
Feature: [UI-RESUME-01](current-iter-issues.md#ui-process-resume).

### Problem

The user selected a paused run but could not see a resume button beside its
status. The screenshot showed the run toolbar and steering panel, while the
ambient tab context named a direct file:// HTML preview rather than the live
loopback API address.

### What was wrong

FIX-0102 exposed Resume process only after discovering OS > Processes and opening
a paused process drawer. Its frontend tests opened that drawer directly, leaving
the run-selection entry point unverified. An old backend without resume metadata
also produced an unhelpful availability message. This was a frontend discovery
problem, not evidence that retry or execution-certainty guards should change.

### How it was fixed

src/polyinference/ui.html now shows Resume run beside a paused status and lets the
run toolbar wrap. src/polyinference/ui-monitor.js opens a paused-process chooser,
preferring the blocking process, a failed worker or the controller, and reuses the
existing Resume process form/API. Optional steering drafts survive process
selection. Opening options sends no signal; submission keeps existing duplicate,
snapshot, active-run and unsettled-execution guards. Blocked runs retain the entry
point so the reason is visible. Missing backend support prompts a server restart.

Updated the UI usage guide, UI/inspection module guides, test inventory and current
feature tracker with the toolbar route and HTTP-versus-file preview distinction.
Reviewed CLI, recovery, launch/settings and runtime-boundary documents: their
interfaces, recovery semantics and ownership remain accurate, so no edits were
needed there. No file or feature path appeared or moved; navigation ownership is
unchanged. Concurrent onboarding FIX-0104 and other working-tree changes are
separate work.

### Design principle enforced or reconstructed

Expose continuation where users select and inspect paused execution, and explain
blocking facts without hiding the action's entry point. Presentation must preserve
the OS's generic signal and certainty guarantees and the application's recovery
policy. A visible resume control cannot prove that remote work stopped or make a
saved snapshot executable.

### Verification

Windows Node tests/ui_start.test.cjs: 27 passed in 3.48 seconds. New coverage opens
the control from the paused-run toolbar, selects the blocking worker, retains
per-process steering drafts and submits the selected run/process/text exactly once.
It also checks visible blocker explanations, missing backend support, read-only
snapshots and hiding the entry for completed runs. Existing resume error, duplicate
and late-reply regressions passed in the same run.

Native documentation generation and --check passed for 263 files and 119 leaves.
Scoped Git whitespace passed with the existing CRLF-normalization notice only.
Prior history bytes, unique IDs, required sections and task-added whitespace were
verified. No backend, agent or runtime implementation changed
in this correction; FIX-0102's backend results are historical. No provider request,
original-run resume/reconciliation, backend-suite run, commit or push was performed.
The browser tool rejected file:// acquisition under its URL policy, so no live
browser visual verification is claimed.

<a id="fix-0106"></a>
## FIX-0106 — 2026-10-22 — Preserve the agent-router distillation tutorial and link both version trackers

Status: implemented as documentation only.
Related history: [FIX-0080](#fix-0080), [FIX-0087](#fix-0087), [FIX-0098](#fix-0098).
Tutorial: [agent-router distillation](router-distillation-tutorial.md).

### Problem

The user's step-by-step tutorial existed only in this chat. They requested a
reasonable repository home with references from both current- and next-version
fix records, so future research could find and reproduce the intended workflow.

### What was wrong

FIX-0087 recorded the next-version learned-router idea, but did not include a
training tutorial. This is a research-documentation/discoverability gap, not a
recurrence of a runtime defect or evidence that learned routing is implemented.

### How it was fixed

Added development-docs/router-distillation-tutorial.md with isolated WSL setup,
task/agent/settings contracts, Opus label collection, a 1.5B LoRA student for the
user's reported 16 GB GPU, saved-adapter inference, held-out evaluation and the
separate later RLAIF stage. Recorded the user's reported written research
permission without copying credentials or asserting independent verification.
Marked starter snippets as unexecuted and explained paid-label interruption,
provenance, length validation, authority and the current role-binding boundary.

Linked the guide from current-iter-issues.md, next-iteration.md's existing routing
proposal, both documentation/development indexes and the authored JSON tree.
Regenerated human navigation. The next-version feature remains proposed; no
application/OS implementation, installed dependencies, configuration or run state
changed. Preserved the completed current-version queue and earlier fix history.

Reviewed setup.md, dev-readme.md, docs/guides/providers.md,
docs/modules/agent-workflow.md, docs/modules/documentation.md, docs/maintenance.md,
and the runtime boundary/revision ledger. Their current setup, allocation,
role-binding, OS and navigation contracts remain accurate; they need no edits
because the new tutorial describes an isolated research experiment, not a shipped
training command or router integration. Existing unrelated working-tree changes
are not this task's work.

### Design principle enforced or reconstructed

Keep research instructions discoverable from current records and future plans
without converting proposals into runtime guarantees. Agent-selection and
settings policy belongs above the OS; predictions do not grant authority or
replace generic admission, budgets and execution-certainty guards. Preserve
traceable experiment inputs and distinguish imitation from measured task success.

### Verification

WSL python3 scripts/project_docs.py and its --check mode both passed for 264
files and 120 feature/doc leaves, including local links, single primary ownership,
README reachability and generated navigation. All nine Python blocks parsed with
ast.parse, and the JSON object plus three JSONL examples parsed successfully;
these checks validate syntax, not imports, API behavior or training results.
Reviewed the task's changes against saved pre-edit copies of all seven existing
documentation files. Earlier fix-history bytes are preserved after removing the
new index row/entry and its separator; fix IDs are unique. Scoped Git whitespace
and the new tutorial's whitespace passed, with existing CRLF-normalization
notices only. Adjacent-document review and reasons for no edits are recorded above.
No teacher request, model download, package installation, GPU training/benchmark,
live agent execution or runtime-suite result is claimed for this documentation task.

<a id="fix-0107"></a>
## FIX-0107 — 2026-10-22 — Add a navigable HTML learning guide for router distillation and RLAIF

Status: implemented as documentation only; verification recorded below.
Related history: [FIX-0080](#fix-0080), [FIX-0087](#fix-0087),
[FIX-0099](#fix-0099), [FIX-0106](#fix-0106).
Guide: [HTML learning guide](router-training-guide.html), owned by the
[Markdown tutorial](router-distillation-tutorial.md).

### Problem

The saved Markdown tutorial assumed training vocabulary, and later chat discussion
added model choices, thinking, synthetic prompts and conversation summarization.
The user requested one HTML teaching document for readers with general AI knowledge
but no training experience, with skippable sections, practical steps near the end
and links from the current/next-version trackers and Markdown companion.

### What was wrong

FIX-0106 preserved the original code walkthrough, not a complete learning route
for newcomers or the subsequent design discussions. This is a teaching and
discoverability gap; no runtime or model-quality defect was established.

### How it was fixed

Added development-docs/router-training-guide.html with fourteen anchored chapters,
three reading paths, responsive contents, optional detail/code disclosures,
semantic process diagrams, an illustrative reward calculator, print support and
primary-source links. Explained tokens/weights, training/inference, SFT/LoRA,
distillation, preferences versus online RLAIF, Opus's roles, current agent/OS
ownership, students/thinking, real/synthetic data, two-pass summaries and evaluation.

Embedded all fourteen code/file-format blocks from Markdown steps 1–7 in Lab A.
Lab B provides controlled data/summary experiments, preference collection, an
optional unexecuted DPO starter recipe and a clearly labelled online-RLAIF
integration procedure/pseudocode. Research status, reported permission, hardware
estimates, example settings and unperformed training remain explicit.

Updated the Markdown owner with the HTML route/responsibilities; linked the HTML
directly from both version trackers and documentation indexes. Assigned the HTML
to the existing primary-doc leaf in docs/file-tree.json and regenerated navigation.
No external assets, network calls or training are triggered by opening the guide.

Reviewed setup, developer onboarding, provider/workflow/documentation module
guides, maintenance and runtime boundary/revision records. Their current commands,
role bindings, allocation, authority and navigation contracts remain accurate;
no edits are needed because this teaches an isolated research workflow rather
than adding a production training interface or changing OS/agent behavior.
Prior fix entries and unrelated working-tree changes are preserved.

### Design principle enforced or reconstructed

Teach prerequisites before procedures while letting experienced readers choose
their entry point. Distinguish demonstrations, proposed experiments, implemented
behavior and measured evidence. Keep task/agent selection and acceptance above
generic OS execution safeguards; a model prediction cannot grant authority.
Evaluate compression and feedback by downstream task outcomes, not fluent prose
or a reward proxy alone. Maintain discoverable ownership and current navigation.

### Verification

WSL documentation generation and --check passed for 265 files and 120 feature/doc
leaves, including ownership, local references, reachability and generated HTML.
HTML-specific checks passed fourteen chapters, 45 unique IDs, 46 local
links/anchors, no remote assets and task-added whitespace. All eleven Python
examples (including labelled architectural pseudocode) parsed with ast.parse;
four JSON objects and three JSONL records parsed successfully. All fourteen Lab A
blocks match Markdown steps 1–7 exactly. Extracted JavaScript passed node --check.

Browser QA verified the desktop opening, chapter navigation, phone layout at
390 x 844, compact/expanding mobile contents with navigation closing it again,
all fifteen lab-code disclosures expanding/collapsing, and the reward slider's
preference change. No page horizontal overflow or browser warnings/errors were
observed; the temporary viewport override was reset. The first preview attempt
could not reach a sandboxed loopback server; a temporary host loopback preview
then succeeded. Printing is supported by styles/events, not a verified PDF export.

Comparison with saved pre-edit copies confirmed all earlier fix-history bytes
are preserved after removing the new index row/entry and separator. IDs remain
unique, and the original Markdown walkthrough is unchanged below its added HTML
reading/ownership route. Task-added whitespace and scoped Git diff --check passed,
with the existing CRLF-normalization notices only. These checks establish
documentation structure, syntax and browser behavior, not model/library execution
or research performance.
No package installation, teacher request, model download, GPU training, agent-run
experiment or production deployment was performed for this documentation change.

<a id="fix-0108"></a>
## FIX-0108 — 2026-10-22 — Compare Flash-Next Coder with the earlier coding shortlist

Status: investigated; published evidence only, no implementation changed.
Related: [chat provenance](CHAT_HISTORY.md), [FIX-0041](#fix-0041).

### Problem

The user requested a coding-only Hugging Face comparison of Qwen3.8 Flash Next
Coder against models previously considered for PolyInference.

### What was wrong

The earlier comparison chat included full Flash-Next but had not assessed the
new compressed Coder build. General intelligence composites do not answer coding
quality, and base-model scores cannot be assigned to arbitrary GGUF files.
This is research evidence maintenance, not a runtime defect.

### How it was fixed

Recovered the shortlist from chat 01a15f3f-2d24-76c1-a62f-398fb2718c05,
"Compare models in inference report", and checked current primary model cards.
The likely requested artifact is [ISTA-DASLab Coder](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF).
Its October 17 update reports SWE-bench Verified 79.20 versus its BF16 baseline
82.80, and LiveCodeBench v6 87.43 for both, at xhigh. It removes half of routed
experts and stores retained weights at 3.5 bpw; effective 1.89 bpw is not a literal
precision for every weight. Total files are 58.4 GB; transformer 29.6 GB plus
28.8 GB disk-offloadable n-gram table. This does not fit wholly in 16 GB VRAM.

[Full Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) versus
[27B](https://huggingface.co/Qwen/Qwen3.8-27B), in Qwen's comparison:
DeepSWE 58.7/42.2; SWE Pro 62.5/61.7; multilingual SWE 81.0/73.8;
NL2Repo 48.1/42.3; LCB v6 91.9/90.3. These full-model numbers do not establish
the pruned Coder's ranking against 27B. Pro uses a corrected benchmark and DeepSWE
uses best-of-harness reporting, so older results cannot form a controlled league.

[Qwen3.6-35B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) reports Verified 73.4,
Terminal 2.0 51.5; [Coder-Next](https://huggingface.co/Qwen/Qwen3-Coder-Next)
reports 70.6/36.2. [Qwen3.5's table](https://huggingface.co/Qwen/Qwen3.5-122B-A10B)
reports Verified/Terminal 2/LCB v6: 122B 72.0/49.4/78.9;
35B 69.2/40.5/74.6; gpt-oss-120b 62.0/18.7/82.7.
Qwen3.6's later table re-evaluates 3.5-35B at 70.0 Verified; retain provenance.
[Next-Instruct](https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct)
reports LCB v6 56.6 and Aider 49.8.
[NVIDIA](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16)
reports Nemotron Super Verified 60.47 (OpenHands), compared with 66.40 for
Qwen3.5-122B and 41.9 for gpt-oss in that setup. Those differences illustrate
harness effects. [GLM-Air](https://huggingface.co/zai-org/GLM-4.5-Air) remains
lower-priority without a matched evaluation; its 59.8 aggregate is not SWE.

Inference: Coder deserves the quality-focused trial against 27B and 3.6; no
controlled exact-quant comparison establishes a universal winner or parity with
the previous chat's proprietary models. No TPS or 64K-input/32K-output result
was measured. Reviewed provider usage, onboarding, maintenance and documentation
module/index/navigation: current bindings/interfaces are unchanged and need no
edit. Only this existing history leaf changes; no new files or navigation paths.

### Design principle enforced or reconstructed

Compare coding task outcomes with evaluation/version/harness provenance.
Distinguish published measurements from deployment inference and unverified
hypotheses. Research recommendations do not change role bindings or OS policy.

### Verification

Read the earlier comparison chat and current Hugging Face primary cards.
No model download, inference, coding benchmark, runtime test, configuration,
retained-run change, commit or push occurred. Windows generation and --check were blocked by Git dubious ownership; no global
Git exception was added. Authorized native WSL generation then passed for 265
files and 120 leaves. Final native --check and prior-history preservation are
verified in the task handoff.

<a id="fix-0109"></a>
## FIX-0109 — 2026-10-22 — Estimate Coder memory, speed and batching on the reported laptop

Status: research and theoretical sizing only; no implementation changed.
Related: [FIX-0108](#fix-0108), [FIX-0061](#fix-0061).

### Problem

The user requested fit, token speed, context and continuous-batching analysis
for Coder on RTX 3080 Laptop 16 GB plus 64 GB DDR4, with 32K input and 16K output.

### What was wrong

FIX-0108 established artifact size, not runtime placement or measured laptop
performance. Adding RAM and VRAM or multiplying single-stream TPS by slots would
misrepresent offloading and shared resources. CPU model, power limit, PCIe link,
RAM channels/speed and SSD remain unspecified. No local defect was established.

### How it was fixed

Checked the [artifact card](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF),
[Strata memory guide](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md),
[engine details](https://github.com/Niko1221/Strata/blob/main/docs/DETAILS.md),
[batching](https://github.com/Niko1221/Strata/blob/main/docs/BATCHING.md) and
[model configuration](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/blob/main/config.json).
Coder has 29.6 GB transformer and 28.8 GB disk-backed lookup shards; Strata says
about 23 GB of experts live in RAM, dense weights and expert cache in VRAM.
64 GB RAM is sufficient in principle without repeatedly paging expert weights.
Estimate 30-45 GiB total system usage including OS/runtime and variable file cache,
not a reservation or measured working set. Allow about 80 GB free NVMe storage
for files, MTP and installation headroom. File cache is reclaimable, not extra
mandatory resident weights. Text-only, one resident engine; no per-worker copy.

32768+16384=49152 tokens per request; use 65536 configured per-sequence context
for templates and growth. Thinking consumes the output allowance. Native context
is 262144. Strata documents 13.7 KB/token INT8 KV and a 0.56 GiB session at 32K:
approximate state at actual 48K is 0.8 GiB/slot, around 1 GiB at configured 64K,
plus draft/graph/checkpoint/prefill state. GDN recurrence is not dense KV per token;
QSA sparse reads do not erase retained KV. Two/four/eight live 48K requests hold
96K/192K/384K total tokens, without violating the per-sequence native limit.
Memory-only extrapolation permits several slots; 8 is a single-GPU implementation
ceiling in the cited docs, not a guaranteed allocatable count on this laptop.

Planning inference with optimized Strata, resident RAM experts, warmed NVMe,
MTP and laptop plugged in: 20-40 generated tokens/s (use 25 as conservative
budget), 300-1000 prompt tokens/s (33-109 seconds for 32K); broad uncertainty,
roughly 10-50 output TPS plausible outside central assumptions. Full 16K generation
at 20-40 TPS is 6.8-13.7 minutes plus prompt processing. These are estimates,
not a measured 16K completion. Engine reference: RTX5070/Ryzen7600/DDR5,
Coder 54.9 TPS at32K, 53.2 at64K, 2177 prompt TPS at32K, only256 generated tokens.
A first-person [3080 Laptop report](https://www.reddit.com/r/LocalLLaMA/comments/1wwwmy1/running_qwen38_flash_next_176b_on_a_16gb_rtx_3080/)
uses 32GB RAM and a different full-model/runtime setup at about10 TPS; it is
not an exact Coder benchmark and illustrates power/offload uncertainty only.

Strata supports shared-weight slots, new-request admission, chunk-interleaved
prefill/decode and slot refill. Single16GB setups default to serial: private
session memory displaces GPU experts and unrelated requests share little expert
work. Batch MTP is opt-in; default slots lose solo speculative drafts. Recommend
one slot for throughput, test two for overlap, four experimental, eight only a
memory/implementation experiment. No laptop multi-stream TPS claim is established.
Illustrative arithmetic at25TPS aggregate with no batching gain and20% overhead:
two/four streams receive10/5TPS each (27.3/54.6 minutes for16K each); further cache
loss can be worse. This is a planning scenario, not a forecast or observed scaling.
Native Windows or Linux is the clearer first test; docs have mixed WSL KV-streaming
notes. No production deployment or change to default bindings is implied.

Reviewed provider/inference module, runtime boundary, maintenance and navigation.
No interfaces, current setup commands or policy changed, so no adjacent guide edits
or new navigation paths are needed. Only this required investigation entry changes.

### Design principle enforced or reconstructed

Provider owns GPU scheduling/batching; application owns worker readiness and
admission requests. Separate per-sequence context, aggregate cache, disk file size,
resident memory, per-stream speed and aggregate throughput. Preserve measurement
provenance and distinguish estimates from hardware validation.

### Verification

Arithmetic and primary-source review only. No download, install, GPU inspection,
model request, runtime test, configuration or saved-run change, commit or push.
Documentation generation/check and prior-history preservation checked in handoff.

<a id="fix-0110"></a>
## FIX-0110 — 2026-10-23 — Design one-click run resume across frontend, agent and OS

Status: design/investigation only; no implementation changed.
Related: [FIX-0100](#fix-0100), [FIX-0102](#fix-0102),
[FIX-0103](#fix-0103), [FIX-0105](#fix-0105).
Proposal: [run-level Resume redesign](current-iter-issues.md#ui-run-resume-design).

### Problem

The user wants optional instructions followed by a simple Resume click, without
having to select internal processes or resolve technical recovery state. They
explicitly requested a design first, split across frontend, agent and OS.

### What was wrong

The frontend currently opens a process chooser; TestUI.resume_options and the
generic request_resume reject unsettled effects before accepting user intent.
cli.apply_resume owns coding continuation choices outside the agent. Earlier
FIX-0102/0105 verified a guarded process-level signal and its discoverability,
not autonomous run-level recovery. This is a broader product requirement, not
evidence that uncertainty can be erased. HTTP remote-status/cancel support and
agent program compatibility are real implementation gaps, not established fixes.

### How it was fixed

No implementation changed. Added a clearly proposed design below UI-RESUME-01:
frontend optional text plus direct run request; agent-owned all-worker continuation
and disposition; OS-owned durable intent and evidence-based effect preparation;
restart/idempotency, provider capability and program migration requirements.
The design separates request acceptance from actual execution and specifies
plain failures rather than a mandatory reconciliation workflow. It does not claim
that every historical/provider interruption is currently recoverable.

Reviewed UI/inspection, agent workflow/services/workers, CLI, process/kernel and
inference module guides, UI/recovery usage, runtime boundary/revision ledger,
runbook, onboarding/setup routes and documentation maintenance/navigation.
These describe unchanged current behavior and need no edits in a design-only
task. The current-iteration proposal and this history record distinguish the
future contract from that behavior. No file/feature appeared or moved, so authored
JSON navigation ownership is unchanged. Pre-existing working-tree edits remain
separate work.

### Design principle enforced or reconstructed

User intent is to continue the objective. The frontend submits and displays it;
the agent chooses continuation and task/source policy; the OS establishes effect
certainty and enforces generic authority/resource guarantees. Accepting intent is
not evidence that an old operation ended. Internal recovery should not become a
routine user task. Preserve prior evidence, saved work and explicit compatibility
rather than silently restarting the objective or weakening execution checks.

### Verification

Source/document review only; no application/OS code, tests, configuration or saved
run was changed. No provider request, reconciliation or resume was executed.
Planned regression cases are listed in the proposal; none are claimed as run.
WSL python3 scripts/project_docs.py and --check both passed: 265 files and
120 feature/doc leaves, including links and README reachability. Byte comparisons
confirmed that removing only the added proposal/index row/entry reproduces the
pre-edit issue/history content exactly. Fix IDs and the new anchors are unique.

<a id="fix-0111"></a>
## FIX-0111 — 2026-10-23 — Make Resume run directly through frontend, agent and OS

Status: implemented; verification below.
Related: [FIX-0027](#fix-0027), [FIX-0100](#fix-0100), [FIX-0102](#fix-0102),
[FIX-0103](#fix-0103), [FIX-0105](#fix-0105), [FIX-0110](#fix-0110).
Feature: [UI-RESUME-01](current-iter-issues.md#ui-process-resume).

### Problem

The user wants optional instructions followed by one Resume click. The process
chooser and requirement to resolve internal recovery state made the UI control
an operator procedure instead of continuation. They approved implementation of
the three-layer design in FIX-0110.

### What was wrong

The frontend chose a paused process. UI and OS validation refused unsettled work
before accepting intent, and cli.apply_resume mixed coding continuation with
transport. Prior FIX-0102/0105 correctly protected execution certainty but tested
process-level submission/discovery, not automatic run-level preparation, durable
request replay or agent continuation across restart. New agent source also changes
graph_digest, requiring a precise compatibility decision for retained runs.

### How it was fixed

Frontend: ui.html/ui-monitor.js expose inline optional instructions and direct
Resume, Resuming progress, persistent drafts/client request identity, replay after
lost acknowledgement and stale-response protection. No mandatory process chooser
or reconciliation form remains. The advanced process drawer stays available.

HTTP/CLI: ui.py accepts run-level requests with optional legacy process_id and
idempotent request_id, reloads saved settings, retains background failures and
restores pending requests after restart, including journal/metadata and activation
crash gaps. CLI resume accepts --text and calls the same agent service;
apply_resume is now only a compatibility wrapper.

Agent: agent/resume.py and controller.py own all-worker continuation, interrupted
source/review, eligible checkpoint reattachment, linked model retry and accepted
output recovery. Plans, steering receipts and outcomes survive interrupted
activation. Ordinary errors leave durable failed progress and a paused run.
Only the exact documented predecessor graph is migrated, with all other program
pins equal; the old/new identity is separately recorded and original manifests,
effects, authority, configuration, budgets, deadlines and cancellation are retained.

OS: runtime/processes.py accepts scoped/unscoped intent independently of unresolved
effects. runtime/resume.py and kernel.py prepare execution under coordinator
ownership, using host receipts, artifact-backed completed raw responses and a
bounded adapter lookup. inference.py retrieves saved HTTP Responses IDs, verifies
identity and terminal status and applies normal completion validation. OS readiness
is separate from application progress; accounting, reservations and callbacks are
restartable. Unknown outcomes remain uncertain and block new dispatch. No native
remote-cancel or host-descendant termination guarantee is claimed, and old
synchronous requests without recovery handles can still fail automatically.

Updated UI/inspection, agent workflow, process/kernel/inference, CLI and SDK module
guides and settings compatibility; UI/CLI/recovery/retrying/results usage; runtime
boundary/revision ledger/runbook and settings reference; onboarding;
current tracker; test inventory and JSON/generated navigation. Reviewed setup,
launch/configuration, provider installation, architecture, agent-service/
worker/repository, archive/export/history and maintenance guides. Their setup,
settings schema, policy, evidence and storage contracts remain unchanged and need
no additional edits. Pre-existing working-tree changes are separate work.

### Design principle enforced or reconstructed

The frontend submits user intent; the agent owns continuation/task/source policy;
the OS owns generic effect certainty and execution authority. Accepting Resume is
not proof of termination. Internal recovery/disposition should be automatic where
evidence permits, with a clear failure where it does not. Preserve immutable
outcomes and saved work, avoid duplicate effects/instructions, and use explicit
compatible-state migration instead of bypassing program pins or resetting limits.

### Verification

WSL integrated suites passed 159 tests with one frontend-wrapper skip in 158.55s
across test_resume, test_ui, test_runtime_general, test_recovery, test_model_retries,
test_inference_simulation, test_saved_credentials, test_ui_frontend, test_endpoints
and test_http_integration. After the final acknowledgement/request-ID changes,
the affected Resume/UI/general-OS suites passed 47 tests in 104.48s. The additional
settlement-crash regression exposed float wire usage being treated conservatively
as unknown integer accounting; integral counts are now restored without rounding.
The final test_resume suite passed all 14 cases after that correction.

Windows Node passed all 29 frontend checks on the final script. The WSL wrapper
skip is because its Node version is below 18; it is not counted as a frontend pass.
Coverage includes direct empty/nonempty-text Resume over real loopback HTTP in
both isolated and actual-project worktree modes, unchanged private edits and saved
settings, duplicate IDs, delayed/lost acknowledgement, post-activation restart,
multi-worker source accounting, atomic steering, exact predecessor/unknown graph
pins, provider/receipt recovery, unsupported/unknown status, bounded waits,
coordinator ownership and recovery accounting after a settlement crash.

Scoped Ruff and Python compilation passed. Documentation generation and --check
passed for 268 files and 120 feature/doc leaves. Prior-history byte preservation,
unique fix IDs/anchors, navigation ownership and task-added whitespace were checked.
Scoped Git whitespace passed with the existing CRLF-normalization notices only.
No browser visual QA, full repository suite or live-provider readiness is claimed.
No live provider, user saved-run execution/reconciliation, commit or push occurred.

<a id="fix-0112"></a>
## FIX-0112 — 2026-10-23 — Count retries and assess the saved Haiku timeout pause

Status: investigated; no implementation changed.
Related: [FIX-0045](#fix-0045), [FIX-0047](#fix-0047), [FIX-0100](#fix-0100),
[FIX-0103](#fix-0103), [FIX-0111](#fix-0111).
Evidence: [run 7086c575ef94 retry audit](run-7086c575ef94-analysis.md#retry-count-audit--2026-10-23).

### Problem

The user asked how many retries preceded the supplied run's pause, whether enough
recovery had been attempted and whether retry logic was faulty. FIX-0100 diagnosed
the same export but did not explicitly separate all retry/correction counts.

### What was wrong

No retry-counter defect was established. The final submitted Haiku call became
uncertain after 180.005032 seconds and bypassed automatic retry by design. The
one-extra-attempt allowance was unused, not exhausted. Across the run there were
zero endpoint retries, output adaptations or explicit linked model recoveries;
six application format corrections (five plus one), and one replacement foundation
task. These are different mechanisms. FIX-0100's confirmed diagnostic conflation
still prevents proving the exact timeout/disconnect/cancellation cause. Current
Resume cannot recover this saved synchronous Anthropic request without a completed
response or supported provider handle. This is an existing recovery-policy/
capability limit, not evidence that all approaches failed.

### How it was fixed

No implementation, configuration, project source or saved run changed. Appended
counts and the assessment to the existing report. Reviewed retry/inference/kernel
and worker/workflow module guides, recovery/retrying usage, runtime boundary and
current issue findings: they describe these guards and outstanding diagnostic/grant
issues accurately, so need no interface/settings/tracker edits. No file or feature
appeared or moved; authored JSON navigation is unchanged. Pre-existing working-tree
changes are separate work.

### Design principle enforced or reconstructed

Count actual durable submissions separately from grammar correction and task
replacement. The OS owns execution certainty, transport evidence, bounded retries
and accounting; the agent owns response grammar, task scope and acceptance. An
intentional uncertainty stop does not establish retry exhaustion or objective
impossibility. Preserve pending effects and original budgets/deadlines in recovery.

### Verification

Fresh export assertions passed: matching whole-file SHA-256, 119 effect outcomes,
absence of retry identities/extensions, five-plus-one correction node outputs,
180.005032-second interval and all 326 artifact sizes/digests. Inspected current
dispatch/classification/retry/Resume source and the existing one-submission
disconnect regression; no runtime suite was rerun. Windows Python lacks pytest;
native WSL returned E_ACCESSDENIED. A supplemental offline async probe was stopped
without a result and supplies no evidence. No provider request, original-run
resume/reconciliation, implementation fix, commit or push occurred.

Ordinary Windows documentation generation and --check each failed on exactly four
pre-existing Windows-mapped Zone.Identifier paths, as in FIX-0100. An in-memory
compatibility wrapper excluding only those four metadata paths then passed both
generation and check: 268 files, 120 feature/doc leaves, links and README
reachability verified. Checker source and metadata files were not edited. Authored
JSON and generated HTML navigation match their pre-task hashes. All prior history
and report bytes are preserved after removing only this task's additions; unique
fix IDs, required sections and added-text whitespace passed. The five inspected
runtime/worker source files retain their pre-task hashes. Historical verification
above remains unchanged.

<a id="fix-0113"></a>
## FIX-0113 — 2026-10-23 — Explain recurring Claude pauses against official transport guidance

Status: investigated; no implementation changed.
Related: [FIX-0068](#fix-0068), [FIX-0100](#fix-0100), [FIX-0103](#fix-0103),
[FIX-0111](#fix-0111), [FIX-0112](#fix-0112).
Evidence and sources: [Anthropic follow-up](run-7086c575ef94-analysis.md#anthropic-documentation-follow-up--2026-10-23).

### Problem

The user requested official Claude documentation research to explain recurring
pauses after the retry-count audit. An intentional uncertainty stop alone does
not explain why the integration repeatedly reaches that state.

### What was wrong

Current Anthropic preparation uses stream=false with a 32,000-token output ceiling
in this run, while the UI Haiku factory selects 180 seconds. The ordinary kernel
also applies that endpoint setting to the whole generation. The HTTP stream context
only buffers response bytes; it does not enable provider SSE. This is a concrete
integration mismatch with Anthropic's long-request/idle-connection guidance.
The application uses custom httpx, so the official SDK's ten-minute default and
two transient/timeout retries are not inherited. Any submitted uncertainty still
halts dispatch before the retry service; raising its counter or enabling SSE alone
would leave other parts of the failure mechanism intact.

All 37 completed Haiku requests took at most 16.470116 seconds and emitted at most
4,582 output tokens; the final request ran 180.005032 seconds without a retained
result. The exact underlying slow generation/provider/network/cancellation cause
is still unproved. A large output allowance does not establish actual output size.
This explains a credible recurring mechanism, not every historical pause or the
separate native Codex incident in FIX-0068.

### How it was fixed

No implementation, configuration or retained run changed. Added the sourced
follow-up to the existing run report, documented current buffering/total-timeout
semantics in the owning inference module guide, and expanded open run14 findings
with the combined transport/deadline/diagnostic repair. Reviewed retry/kernel/
settings/workflow guides, provider/recovery/retrying usage, runtime boundary and
settings reference. They accurately describe unchanged grants, defaults and
uncertainty rules, so need no additional interface or setup edits. No file or
feature appeared or moved; authored navigation ownership is unchanged.

### Design principle enforced or reconstructed

The application chooses generation allowances and task/response sizes. The OS and
adapter provide accurate transport/progress/termination facts and distinct bounded
execution controls. Internal streaming need not expose partial actions to an
agent: require a complete validated response before execution. Each provider
submission remains a charged durable intent. SDK retry convenience does not prove
remote termination or authorize replay of uncertain tool-bearing work.

### Verification

Read current official Anthropic API error/long-request, Python SDK timeout/retry
and streaming/final-message documentation. Two source-derived probes executed the
live prepare method and UI Haiku factory with inert stubs, confirming stream=false,
max_tokens=32000 and timeout_seconds=180. A third executed live KernelRuntime.execute
without an event loop, confirming uncertainty bypasses retries and a returned
known failure reaches the filter. Fresh export measurements established all 37
completed request intervals/output counts. No live inference, outage reproduction,
full runtime suite, source/configuration edit, saved-run resume, commit or push.

Documentation generation and check passed for 268 files and 120 feature/doc
leaves, including new links/anchors and README reachability. Used the previously
verified in-memory Windows compatibility filter for exactly four pre-existing
mapped Zone.Identifier paths; checker source and metadata files were unchanged.
Authored JSON and generated HTML navigation retain their pre-task hashes. Prior
history/report bytes and existing module/tracker text outside the additions are
preserved; unique IDs, required sections and added-text whitespace passed. The
four inspected source/default files retain their pre-task hashes. Existing
working-tree changes and historical test results are not claimed as this work.

<a id="fix-0114"></a>
## FIX-0114 — 2026-10-23 — Propose portable endpoint resilience and faster failure testing

Status: design/proposal only; no implementation changed.
Related: [FIX-0045](#fix-0045), [FIX-0047](#fix-0047), [FIX-0054](#fix-0054),
[FIX-0096](#fix-0096), [FIX-0111](#fix-0111), [FIX-0113](#fix-0113).
Proposal: [portable endpoint lifecycle and testing](current-iter-issues.md#portable-endpoint-testing).

### Problem

The user requested an implementation suggestion for a better testing experience,
with the local lane supporting both small cloud models and actual local inference.
A Claude-only timeout patch or a uniform faster-response assumption would not meet
that requirement.

### What was wrong

The current raw adapter/kernel share one broad endpoint timeout, while submitted
uncertainty blocks all dispatch. Lane names do not encode actual speed, streaming,
retrieval, cancellation or possible effects. The existing optional simulator paces
buffered real responses; that is useful but does not by itself test missing-terminal
SSE and real transport-stall handling. These are established design limits, not a
new runtime reproduction or evidence that local hardware inherently needs a fixed
latency. Unknown compute must remain accounted for even if its output is abandoned.

### How it was fixed

No implementation, saved configuration, launch default or retained run changed.
Added the proposed staged design to current-iter-issues.md: common lifecycle/SSE
normalization, separate editable timing profiles, modest caller response targets,
generation-only recovery with late-output fencing and retained capacity/accounting,
strict effectful uncertainty, tester progress/probes and offline/fixture/live tests.
The proposed narrower query barrier explicitly refines R13 only if implemented;
current boundary/revision guarantees remain unchanged. A one-slot local server
without verified cancellation cannot silently gain spare retry capacity.

Reviewed inference/retry/kernel/settings/inspection and simulator module guides,
simulator/provider/recovery usage, navigation, boundary and revision references.
They remain accurate for unchanged current behavior and need no proposed APIs
presented as implemented. Future stages list their required settings, usage, module,
revision and navigation updates. No files or feature leaves appeared or moved.
Existing working-tree changes remain separate work.

### Design principle enforced or reconstructed

Treat local/cloud as bindings, and configure behavior using trusted adapter facts
and explicit resource preferences. The OS owns transport, deadlines, evidence,
capacity, immutable attempts and safe delivery; the application owns response size,
profile selection, tasks and acceptance; the server owns GPU scheduling. A pure
query's logically abandoned response is not proof that its remote compute ended.
Keep testing fast and deterministic without weakening real-world effect certainty.

### Verification

Reviewed current adapter/admission/kernel/settings/simulator paths and official
Anthropic streaming, llama.cpp server and vLLM serving documentation. Audited the
proposal against no-spare-slot, second-unknown-retry, partial/late output, heartbeat,
restart/replay and original-budget cases. Listed regression cases are requirements,
not tests executed. No runtime test suite, live endpoint, generation, benchmark,
implementation edit, saved-run resume, commit or push occurred.

Documentation generation and check passed for 268 files and 120 feature/doc
leaves, including links/anchors and README reachability. Used the existing
in-memory compatibility filter for exactly four Windows-mapped Zone.Identifier
metadata paths; checker source and metadata files were not changed. Authored JSON
and generated HTML navigation retain their pre-task hashes. Prior tracker/history
bytes are preserved after removing only this task's proposal/entry/index row.
Stable fix IDs, required sections and added-text whitespace passed. Six inspected
implementation/settings files and current boundary/revision guides retain their
pre-task hashes. The 32k-at-5-TPS example was checked arithmetically (106.67 minutes),
not benchmarked. No proposed interface or behavior is claimed as implemented.

<a id="fix-0115"></a>
## FIX-0115 — 2026-10-23 — Split endpoint resilience into agent policy and independent OS mechanisms

Status: design review/investigation only; no implementation changed.
Related: [FIX-0022](#fix-0022), [FIX-0032](#fix-0032), [FIX-0045](#fix-0045),
[FIX-0047](#fix-0047), [FIX-0054](#fix-0054), [FIX-0058](#fix-0058),
[FIX-0085](#fix-0085), [FIX-0114](#fix-0114).
Clarification: [agent/OS separation review](current-iter-issues.md#endpoint-agent-os-split).

### Problem

The user asked to split the endpoint/testing proposal into agent and OS design,
check it against the project's definitions and ensure OS independence.

### What was wrong

The earlier proposal correctly placed transport, limits and durable recovery in
generic services, but left replacement permission and run-level continuation too
implicit. Generation-only execution does not decide whether the caller permits
an answer to be discarded. Similarly, generic resource blocking does not authorize
the OS to choose coding task continuation or application pause policy. These are
design wording/authorization gaps, not implemented regressions. A separate existing
portability dependency was observed: agent/worker.py imports WriteScopeError from
a concrete runtime module. No resulting runtime failure was established.

### How it was fixed

No code, configuration, runtime boundary or saved run changed. Added an explicit
review after the existing proposal, preserving its earlier text and history.
Agent design owns preferences, replacement consent, response semantics and work
continuation. OS design owns provider normalization, generic timer/retry schemas,
admission/accounting, immutable outcomes and delivery fencing. Replacement requires
both caller consent and OS-verified absence of possible effects, plus isolated
delivery/capacity/budget guarantees. It cannot turn uncertain writes into queries.
Preserved existing generic OS output adaptation and the deferred shared library.
Listed separate generic OS conformance and agent/fake-runtime acceptance tests,
and the SDK-owned exception cleanup for future implementation.

Reviewed the primary agent/OS designs, current responsibilities/revisions,
architecture, RuntimePorts, affected service/kernel/inference/retry/process/settings
and SDK guides, and simulator/maintenance references. Their current definitions
remain accurate, so no current interfaces, accepted guarantees or setup/usage need
editing. The new section is explicitly a proposed refinement, including R13;
no file/feature appeared or moved and authored navigation is unchanged.

### Design principle enforced or reconstructed

The agent supplies program meaning and permitted flexibility; an independent OS
provides generic mechanisms and non-waivable guarantees through replaceable ports.
Provider protocols stay inside adapters and GPU scheduling stays in the server.
Automatic runtime assistance can execute declared policy without knowing tasks,
Git, coding grammar or acceptance. Caller permission is necessary but cannot
establish remote termination or weaken grants/resource/effect guards.

### Verification

Cross-read agent/runtime boundary, OS modules/processes and current responsibilities
against the proposed ownership split. A fresh AST import scan of 24 runtime/
settings/ports Python files found no direct imports of polyinference.agent. Four
agent graph/service modules were inspected and the worker exception dependency
was confirmed at worker.py:22 and its catch site. This is static source evidence,
not a dynamic isolation proof or newly executed general-agent runtime suite.
No provider, inference, runtime tests, implementation fix, resume, commit or push.
Proposed conformance cases are requirements, not test results.

Documentation generation and check passed for 268 files and 120 feature/doc
leaves, with links/anchors and README reachability verified. Used the existing
in-memory compatibility filter for exactly four Windows-mapped Zone.Identifier
metadata paths; checker source and metadata files were unchanged. Authored JSON
and generated HTML navigation retain their pre-task hashes. Prior proposal/history
bytes are preserved outside this task's added clarification/entry/index row. Unique
fix IDs, required sections and added-text whitespace passed. Six inspected source/
SDK/settings files and all four primary design/boundary/revision documents retain
their pre-task hashes. This does not claim runtime isolation or implementation.

<a id="fix-0116"></a>
## FIX-0116 — 2026-10-23 — Establish shared human and agent onboarding with required project memory

Status: implemented as documentation only; no application/OS implementation changed.
Related: [FIX-0004](#fix-0004), [FIX-0072](#fix-0072), [FIX-0080](#fix-0080),
[FIX-0098](#fix-0098), [FIX-0099](#fix-0099), [FIX-0104](#fix-0104).
Entry point: [contributor onboarding](../docs/contributor-onboarding.md);
retained knowledge: [project memory checklist](../docs/project-memory.md).

### Problem

The user wants other humans and agents to acquire the same project-rule, design,
preservation and automation awareness by following documentation from README.
They explicitly require an agent to add that information to its memory, project
rules or project-specific content.md, so it informs subsequent requests.

### What was wrong

Existing instructions and the illustrated guide expose maintenance and design
rules, but no shared cross-harness procedure specifies how to initialize retained
contributor knowledge, verify a persistent save and refresh after context loss.
FIX-0098 established Codex instruction delivery and its limits; it did not provide
this broader setup procedure. Reading a page alone cannot establish another
platform's access, persistent memory or automatic compliance. This is a contributor
onboarding gap owned by developer documentation, not an OS memory-service defect.

### How it was fixed

Added docs/contributor-onboarding.md with human setup, required reading through
the tree, agent memory initialization, an every-request/restart/handoff routine
and a reusable onboarding prompt. Added docs/project-memory.md with project
purpose, explicit agent/OS/provider ownership, source/effect/history preservation,
documentation/FIX obligations, real automation and its limits. Both pages and root
AGENTS.md explicitly require agents to add this knowledge to available memory,
project rules or project-specific content.md, verify/report its location and
refresh it. Unavailable persistence must be reported with session-context/reload
fallback; no platform memory capability or background automation is invented.

Linked the procedure directly from README, dev-readme and docs/README, and from
AGENTS. Added maintenance rules for keeping both guides and retained notes current.
Registered two primary-doc leaves in JSON navigation and regenerated HTML.
Reviewed setup/testing, architecture, documentation tooling, the illustrated guide,
agent/OS boundary and revision/design routes, current/future issue indexes:
their environment, behavior, interfaces and existing teaching remain accurate.
They need no further edits because this adds contributor setup, not runtime
features or settings; the field guide already leads through developer onboarding.
No unrelated existing/staged work is claimed, reset, staged, committed or pushed.

### Design principle enforced or reconstructed

Make shared project knowledge inspectable, versioned and reloadable across people
and harnesses. The agent owns canonical memory, workflow, Git and acceptance; the
OS supplies generic execution/resource/effect guarantees. Contributor onboarding
must not impose coding prerequisites on OS programs. Distinguish source guidance,
loaded session context, verified persistent memory and automated structural checks;
preserve history, original evidence, current design status and user work.

### Verification

Native WSL documentation generation and --check passed: 270 maintained files and
122 feature/doc leaves, with links/anchors, primary ownership, README reachability
and current generated HTML. All 20 existing documentation-tool regressions passed
in 0.21 seconds. Both new guides are at most 80 lines; explicit MUST memory/rules/
content.md wording, fallback, task-start source hashes and new-guide whitespace
checks passed. All 109 source/test/tool/example files retain task-start hashes.
Scoped native Git whitespace passed before this entry; final history-preservation,
route/requirement checks and documentation generation/check are recorded at handoff.

Windows sandbox writes were unavailable and ordinary WSL launch returned access
denied; authorized WSL access enabled native authoring/checks without changing
checker source, inventory exclusions or download metadata. No Windows metadata
workaround was needed. Earlier history is preserved with a new stable ID/index.
No runtime suite, browser visual QA, live provider, saved-run execution, platform
memory write, credential change, commit or push occurred. These checks establish
repository guidance/navigation, not another assistant's future compliance.


<a id="fix-0117"></a>
## FIX-0117 — 2026-10-23 — Implement bounded streaming lifecycle and native/caller retry policy

Status: implemented v1; offline checks only, no live provider/local inference validation.
Related: [FIX-0047](#fix-0047), [FIX-0085](#fix-0085), [FIX-0111](#fix-0111),
[FIX-0114](#fix-0114), [FIX-0115](#fix-0115).
Details: [implementation status](current-iter-issues.md#endpoint-testing-v1) and
[current behavior/configuration](../docs/guides/endpoint-testing.md).

### Problem

The exported run stopped after its raw Haiku call exhausted a fixed 180-second
invocation timer. It had no endpoint retry before the uncertainty barrier. The
user requested the proposed repair with more OS-native retry followed by optional
agent policy, supporting small cloud models and actual local serving alike.

### What was wrong

The HTTP adapter requested buffered output and collapsed timeouts/disconnects
into an undifferentiated unknown. Its kernel timer ignored output progress.
FIX-0047 correctly refused blind replay of unknown effects, but lacked explicit
raw-generation delivery consent and physical/logical separation. Output adaptation
also started another transport loop, resetting its allowance. FIX-0085 covered
feedback semantics rather than shared transport counters. These are OS transport,
accounting and retry-composition defects; coding grammar remains agent-owned.

### How it was fixed

Added optional InferenceLifecycle endpoint settings and negotiated InferencePolicy
caller declarations. runtime/inference_stream.py performs bounded incremental
UTF-8/SSE framing and Anthropic/chat/Responses terminal assembly; inference.py
uses first-output/idle/total watchdogs and retains transport cause/stage. Pings
and lifecycle events do not extend meaningful-output deadlines. Hidden reasoning
is not retained; partial JSON/text cannot become an action. Gemini explicitly uses
buffered mode. There is no silent streaming-to-buffered resend.

ModelRetries executes native allowance first, then declared caller retries, records
separate counters/source, and shares root deadline/counters across output adaptation.
Fresh coding configs choose two native retries; bare OS default remains one (now
configurable 0–3). Compaction helper deadlines inherit the parent's effective
logical cutoff. Each new submission retains normal grants, cancellation, budgets,
capacity, finishing reserves and original per-attempt evidence.

Kernel isolation requires explicit consent, built-in raw adapter/tool-free wire
facts and remaining allowance/time. One undelivered generation per lane can be
isolated; its effect stays uncertain and its physical reservations stay held.
A replacement requires spare capacity. Single-slot callers receive an uncertain
logical result without submitting a duplicate; another unknown remains a barrier.
Independent work is permitted without weakening unknown native/tool/effect guards.
Retained delivery_result fences late physical results across replay/restart.
Resume may retrieve isolated status/receipts without requiring their resolution
for unrelated readiness. Native/simulator adapters do not claim this new safety fact.
Optional absent settings preserve old canonical serialization; saved explicit
configurations do not silently acquire the new profile/consent.

Updated inference/retry/kernel/services/settings/SDK guides, complete settings,
boundary/revisions/runbook, investigation status, test inventory and navigation.
Reviewed provider setup, architecture, deployment/implementation, task/acceptance
and repository guides: their provider credentials, broad ownership, host setup and
coding source/acceptance rules remain valid and need no additional edits.

### Design principle enforced or reconstructed

The OS owns generic execution facts, bounded native assistance, accounting and
non-waivable authority/capacity guards. The agent declares additional retry consent,
output targets and semantic recovery. Lost delivery does not prove execution stopped;
logical replacement never fabricates physical capacity or delivers discarded output.
No Git, task graph, reply grammar or acceptance policy is added to generic runtime.

### Verification

Offline lifecycle, retry, resume, simulator and frontend-wrapper selection passed
120 tests with one Linux Node-wrapper skip before final additions; independent
Windows Node checks passed all 30 browser-logic cases. The expanded lifecycle and
probe selection passed 21 cases, and small/large UI output-target cases passed.
Final related Python selection: 270 passed in 174.62 seconds. After final safety
changes, lifecycle/context/retry/resume selection: 113 passed in 32.03 seconds.
All 30 Windows Node browser-logic cases passed; package/affected-test Ruff passed.
All five example configurations validated. The attached historical configuration
retains its exact canonical serialization, native allowance 1 and absent opt-ins.
Documentation generation and --check passed for 274 files / 123 feature/doc leaves.
Initial failures exposed feature negotiation wiring, changed fixture expectations
and nonboolean UI disabled state; these were corrected. No live Claude, local GPU,
production fault injection, browser visual QA or historical-run execution occurred.
The commit is labelled v1 untested as requested; fixture results are not readiness.

<a id="fix-0118"></a>
## FIX-0118 — 2026-10-23 — Add explicit endpoint profiles, generic warm-up and timing inspection

Status: implemented v1; bring-up tooling with offline fixture coverage.
Related: [FIX-0115](#fix-0115), [FIX-0117](#fix-0117).

### Problem

Testing small cloud stand-ins and cold local inference required different timing
budgets and an explicit inexpensive warm-up, with enough diagnostics to distinguish
queueing, first output, active output, backoff and physical uncertainty.

### What was wrong

The local lane name described a routing slot, not endpoint latency/safety. The UI
had no explicit deployment timing choice or bounded generic probe. A separate probe
without serialization/preserved uncertainty could ignore surviving compute and
undercount capacity. This testing workflow belongs to the application, not the OS.

### How it was fixed

agent/system_settings.py owns explicit small-cloud/local-inference/buffered timing
overlays; providers, physical capacity and saved configurations stay explicit.
agent/endpoint_probe.py registers an ordinary artifact-only OS process and submits
one 64-token query, with no tools, Git, workspace, retries or coding services.
It saves its actual RuntimeConfig alongside the journal. UI clicks alone submit
probes; opening/polling/snapshot viewing never warms a model. Probe state serializes
with launches/resumes and remains blocking after uncertainty/server restart until
actual retained terminal reconciliation is observed. There is no cross-runtime
admission claim. UI OS inspection/export retains progress, deadline, transport
cause/stage, caller policy and isolated-computation facts. Fresh UI selects 4096
raw output tokens inside the unchanged hard cap and one additional caller retry.

Added the endpoint-testing guide and updated UI/config/settings/simulator/test
routes and file ownership. Adjacent project selection, credential loading and
accepted-output delivery guides need no change: probes do not select/edit projects,
change credential sources or deliver coding products. The TPS simulator still
paces completed real responses; it does not simulate actual streaming/GPU decoding.

### Design principle enforced or reconstructed

Profiles, warm-up and testing preferences are caller application policy. Generic
OS processes provide grants, admission, budgets, durable facts and termination
rules without requiring coding services. Test convenience cannot waive physical
uncertainty, turn lane names into safety guarantees or claim measured hardware.

### Verification

Generic probe fixtures establish one submitted query, 64-token bound, retained
usage and no repository/workspace/task creation. UI manager fixtures establish
explicit submission, serialization and restart retention. All 30 Node browser-logic
checks passed, including on-click-only probe submission and pending guards.
The final related Python selection passed 270 cases; the final focused safety
selection passed 113. Documentation generation/check passed (274 files, 123 leaves). No live warm-up was submitted.

<a id="fix-0119"></a>
## FIX-0119 — 2026-10-23 — Move workspace scope errors to the public agent/OS port

Status: implemented; backward-compatible exception identity.
Related: [FIX-0054](#fix-0054), [FIX-0115](#fix-0115).

### Problem

The worker imported WriteScopeError from concrete runtime.workspace_state, binding
an otherwise replaceable agent graph to one OS implementation for exception handling.

### What was wrong

The shared boundary omitted a structured failure type that the worker must inspect.
The class was owned by an internal workspace implementation rather than public
ports, contrary to the established agent/OS split. FIX-0054 removed broader policy
coupling but did not cover this remaining exception dependency.

### How it was fixed

Defined WriteScopeError in ports.py; worker.py imports it there. workspace_state.py
re-exports the identical class for existing runtime callers. Structured detail,
message, catch behavior and workspace enforcement remain intact. Updated public
SDK, worker and workspace primary guides. No extra shared strategy library or
OS coding dependency was introduced.

### Design principle enforced or reconstructed

Agents depend on public contracts/ports and own workflow responses to failures.
An OS implementation can be replaced without importing its storage/workspace
internals into the agent graph. Compatibility does not require duplicate classes.

### Verification

The lifecycle fixture confirms public and compatibility imports are identical.
Focused Ruff checks passed after import cleanup. The related 270-case selection included general-agent, capability-boundary,
context, retry, resume, provider and UI suites; all passed. Final focused safety
selection passed 113 cases. Documentation generation/check passed (274 files,
123 leaves), and Git whitespace checks passed.
This changes exception ownership, not scope grants or source mutation semantics.


<a id="fix-0127"></a>
## FIX-0127 — 2026-10-26 — Integrate reliability fixes into the simple OS branch

Status: implemented and verified offline; five unchanged baseline test failures remain.
Related: FIX-0083–0086, FIX-0088–0090, FIX-0115–0119 and the retained
[reliability fix log](../design-docs/implementation/FIXES.md).

### Problem

The runtime reliability branch and codex/simple-os-v1 diverged from main. The user
requested a local merge and push making simple-os-v1 contain both histories.

### What was wrong

The fix branch extended an older monolithic adapter; simple-os-v1 had split generic
kernel/settings/capabilities, in-place Git integration, source/authority safeguards,
streaming recovery and richer shared snapshots. Taking either conflicted side
wholesale would discard independent fixes. Stacking response validation over the
existing transport retries also multiplied the response-repair allowance.

### How it was fixed

Merge the reliability branch into codex/simple-os-v1, adapting generic response
validation, shared recovery accounts and progress observations into the split
KernelRuntime. Preserve the compatibility adapter, registered tool authority,
unknown-execution guards, streaming transport and in-place repository rules.
Retain both check-purpose policy and exact-tree semantic completion, shared-check
preparation, versioned modules, source offers, linked worker exceptions and bounded
stagnation. Keep response exhaustion from refilling through transport retries.
Shared schema-v2 snapshots also project the incoming attempt/recovery/progress
records. Update affected module/configuration/design guides and navigation.
Retained project knowledge is refreshed and read back in AGENTS.md.

Preserve the original query's physical identity and index later response repairs.
Unknown attempts retain admission holds across restart; an older root response
cannot settle a later unknown repair. Explicit reconciliation settles attested
physical attempts, while original-query recovery updates its indexed receipt.
Interruption during the replacement window preserves the settled prior receipt
and accepted replacement instead of copying the logical wait state over it.
Retain operator recovery across the new progress checkpoint, explicit cancellation,
paged reads and isolated tool homes/caches. Do not hide cache-named source paths
from scope checks; the incoming cache fixture now uses the actual tool environment.
The [integration audit](branch-integration-audit-2026-10-26.md) records the full
conflict matrix and verification limits.

### Design principle enforced or reconstructed

Integrate histories without erasing either branch's tested guarantees. Coding
policy stays in the agent; the OS enforces generic grants, resource lineage,
certainty and truthful observations. Retry layering cannot multiply authority or
reset original budgets, and private source is not accepted shared output.

### Verification

The initial complete merged-tree run produced **566 passed, 22 failed, 2 skipped**
(590 cases, 1694.32 seconds); its source/test inputs were unchanged during the run.
All 17 integration failures passed in the corrected-case rerun. The final affected
retry/recovery/progress/runtime/cache/source suite produced **78 passed, 1 skipped,
1 deselected** in 245.71 seconds. It includes all five cross-branch regressions and
the interruption/cache corrections found by the intermediate checks. Separate
critical restart/operator-recovery checks passed all six cases.

Across the complete run and subsequent focused reruns, using the latest result
for each of **592 distinct cases**, results are **585 passed, 5 failed, 2 skipped**.
This is not a single all-green full-suite run. All five remaining failures also
reproduced on untouched `26da7f7`: the short-deadline lifecycle fixture, fixed-time
pacing observation, expired-deadline resume diagnostic and two simulated-worker
output-limit fixtures. Their tests and production defaults remain unchanged; the
[audit](branch-integration-audit-2026-10-26.md#verification-record) lists them.

Ruff, Python source compilation, Node syntax and all **30 frontend tests** passed.
An offline wheel built with cached build tools; its new modules/UI asset, current
retry source and runtime adapter/kernel imports were verified. Documentation
generation/check passed for **297 files / 127 feature/doc leaves**, as did whitespace
checks. The two environment skips require Node/npm in the normal test PATH; the
bundled Node independently ran the frontend tests, but native npm was unavailable.

The command sandbox's async SQLite probe timed out; runtime tests used approved
host execution with disposable fixture state. No live inference or historical
application run was executed. Fresh integrated program/state pins are required;
historical runs remain on their pinned source. Setup/provider credentials, accepted
revisions U01–U04 and future-work proposals require no behavior edit: no new
provider/authentication flow or repair of those unrelated gaps is claimed. Earlier
fix entries and the separate execution-profile worktree remain unchanged.

<a id="fix-0128"></a>
## FIX-0128 — 2026-10-26 — Establish real local Strata setup and mixed-lane capacity evidence

Status: configuration/investigation complete; product test failed; no framework implementation changed.
Related: [FIX-0127](#fix-0127), [FIX-0117](#fix-0117), [FIX-0118](#fix-0118),
and [the live investigation](local-strata-live-test-2026-10-26.md).

### Problem

The user requested one autonomous real local-model Minecraft test after the merge,
with Strata, the installed Qwen IQ1_M, 64K context and batch 1, preserving uncommitted
source for review. Native planning stopped twice before provider submission despite
working authentication and local inference readiness.

### What was wrong

The run's shared input ceiling was initially sized for the local lane. Native
review required 54,085 then 103,227 conservative bytes, exceeding 49,152 then 98,304.
Current native model metadata permits a larger endpoint; this was setup capacity,
not an authentication failure. Local workers also stalled amid repeated reads,
invalid action JSON and conflicting create writes. The observed context omissions
and low-bit model are possible contributors, not isolated proven causes.

### How it was fixed

Configured the actual installed qwen3.8-flash-next-coder-iq1_m at 65,536 server
context with one request/batch group, verified Codex/local readiness, and restored
an exited foreground server through its supported owned-runtime interface.
Fresh attempt 3 uses native 500,000/shared 400,000, below the cached 95% effective
window with 16,384 output headroom. Local input remains 49,152 conservative bytes.
Previous states, source, limits and journals remain unchanged. Isolated repository
mode and conflict/hash-checked provisional export preserve the user's unborn
pi-dev branch without commits. Configuration guidance and this evidence record
are documentation changes; no transport, context or agent implementation fix is
claimed. The final run paused at 19:43:30 Toronto, exit 2, with no runnable tasks
after local locomotion/menu and their bounded recoveries stalled. Private failed
source remains separate. The user target holds only the checked partial export.

### Design principle enforced or reconstructed

Endpoint metadata, configured limits, prepared bytes and actual provider capacity
are distinct facts. New setup cannot rewrite old program pins or replenish linked
recovery allowances. The agent owns task allocation/acceptance and Git policy; the
OS owns generic effects, certainty and admission. A tested partial source milestone
or private runtime commit is not accepted gameplay or a user-branch commit.

### Verification

Real local and Codex probes passed; Strata reports the requested model, 65,536
context, serving/requested concurrency 1 and prompt-and-validate structured output.
No Haiku or simulation was used. Baseline 11 tests passed; the native storage
recovery and final independent exported-tree rerun passed 25. Final prerequisites
and six-file syntax checks passed. Actual browser control checks still show an
unplayable canvas and no menus; a final-private menu snapshot also failed its real
DOM module probe. No game acceptance is claimed. All 179 physical local generations
and 13 validation failures remain accounted, with zero uncertain effects. Linked
recoveries retained original accounts/deadlines and max depth 1. Supported CLI/UI
exports and cumulative/private review diffs preserve partial provenance. Physics
attempts retained no net source delta; menu recovery retained the unchanged private
shell. Owned services were stopped and source remains uncommitted. Documentation
generation/check passed
for 298 files / 128 feature/doc leaves; Git whitespace checks passed. Earlier full
framework-suite results are historical, not rerun for these documentation changes.

<a id="fix-0129"></a>
## FIX-0129 — 2026-10-27 — Correct documentation drift and assess retained workflow reliability

Status: documentation corrected and history investigated; no application/OS implementation changed.
Related: [FIX-0080](#fix-0080), [FIX-0094](#fix-0094), [FIX-0098](#fix-0098),
[FIX-0117](#fix-0117), [FIX-0127](#fix-0127), [FIX-0128](#fix-0128).
Report: [documentation and cross-run reliability audit](documentation-and-reliability-audit-2026-10-27.md).

### Problem

The user requested a documentation compliance/correctness/concision audit and a
manager-level review of retained runs. The tree passed, but module navigation,
settings explanations and verification claims lagged behind the reliability merge.

### What was wrong

Link/ownership checks establish structure, not prose accuracy, responsibility
quality, length or all standalone HTML links. Merge appendices duplicated source
descriptions while module indexes and nested settings remained incomplete.
Guidance confused the 32000 hard output ceiling with the fresh 4096 raw target,
described native startup low effort while turns send medium, and retained stale
resume-overlay and whole-run-pause descriptions. This recurs after FIX-0094:
structural regression coverage still cannot detect semantic overview drift.
These are documentation ownership defects; suspected implementation changes are
separately reported rather than adopted as new design or silently implemented.

### How it was fixed

Updated module ownership/protocol/retry/inspection guides, settings reference,
setup/testing, current configuration/recovery/UI/tester routes and maintenance
limits. Split checks and agent reliability into focused guides with defaults,
bounds and linked invariants/tests. Repaired archived graph reference URLs while
preserving layout, behavior and historical provenance. Updated JSON navigation,
generated HTML and development/issue indexes. Refreshed retained AGENTS knowledge.

Added the linked report comparing earlier Haiku incidents and recent real-Qwen
tests: containment, diagnostics and explicit recovery improved, while task
convergence and browser/product delivery remain unproven. Different models,
baselines/configurations and attempts prevent a controlled overall speed trend.
The report preserves native effort, documentation-checker and legacy-smoke code
follow-ups, existing runtime gaps and baseline failures as unimplemented work.
Original saved runs, historical FIX bodies and pre-existing local work are retained.

### Design principle enforced or reconstructed

Documentation must explain effective behavior and its owning layer, not merely
link every source file. Preserve agent task/Git/memory/acceptance policy, generic
OS authority/accounting/certainty and provider execution boundaries. Distinguish
request targets from ceilings, attempted work from accepted contributions, current
checks from historical evidence, and bounded failure containment from successful
product delivery. Preserve older evidence and explicitly correct later summaries.

### Verification

Documentation generation and --check passed for 303 files / 133 feature/doc leaves;
all 20 existing documentation-tool tests passed. Offline schema/default and five
example-validation checks, archived-link/graph-data preservation, source/test
baseline hashes, earlier FIX-body preservation, focused-guide lengths and task
patch whitespace were checked. The report records reviewed adjacent guides and
remaining tooling/runtime limits. Existing local FIX-0128/configuration/navigation
edits are preserved, not claimed as newly implemented work. Two concurrently added
workflow-readiness reports were registered without claiming their probes/authorship.
No live provider, historical-run execution, game repair, full runtime suite,
commit or push occurred.

<a id="fix-0130"></a>
## FIX-0130 — 2026-10-27 — Explain long-run stopping rules and management qualification gates

Status: investigation/report complete; recommendations proposed; no implementation changed.
Related: [FIX-0127](#fix-0127), [FIX-0128](#fix-0128), [FIX-0129](#fix-0129).
Report: [meeting brief](workflow-readiness-brief-2026-10-27.md) and
[engineering analysis](workflow-readiness-analysis-2026-10-27.md).

### Problem

The user needs a senior meeting report because long-running workflows have not
finished. Literal stopping conditions, likely causes and agent/OS responsibilities
must be clear enough to choose engineering work and a meaningful qualification gate.

### What was wrong

Request success, grammar validity, novelty and product completion can be conflated.
Reviewed October 24–26 Minecraft runs did not reach accepted end-to-end delivery,
despite finite subtask successes. The latest final stop was worker stagnation and
exhausted semantic recovery, after two corrected native input-ceiling stops. Saved
history is not necessarily visible/useful next-call memory. More precise module
contracts did not consistently produce smaller tasks or effective recovery.

### How it was fixed

Produced a read-aloud brief and source-grounded analysis of context/memory,
cutoffs versus malformed JSON and clipped diagnostics, distinct retry/correction/
stall counters, dependency and role policy, resource lineage, unknown execution,
source authority, acceptance and declared U01–U04 OS gaps. Added proposed local
qualification, bounded worker state, evidence-based recovery and integrated gates.
These are recommendations, not implemented or validated repairs. No agent, runtime,
provider, fixture, configuration or game behavior changed; no model was dispatched.
The concurrent FIX-0129 documentation audit and all other edits were preserved,
not claimed as authored here. It also registered these new report paths in the tree.

### Design principle enforced or reconstructed

The agent includes host controller code and owns task semantics, grammar, canonical
memory, progress and recovery strategy. The generic OS owns execution facts,
derived context views, accounting and safe effects; providers own generation.
Failure containment is distinct from productive completion. Improve continuity and
recovery without refilling accounts or weakening source/uncertainty guarantees.

### Verification

Inspected current source at 5fe92f3, saved reports and operation records read-only.
Eleven automatic local schema follow-ups used unchanged payloads and no supplied
replacement; nine became schema-valid and two failed again. This supports format
resampling, not task repair. Original 179-generation/13-validation-failure counts
and empty physics/unchanged menu deltas remain intact. No live run or old state was
resumed. Documentation/navigation checks passed for 303 files / 133 feature/doc
leaves, and whitespace checks passed; exact results are in the review evidence. No full framework
suite or new model result is claimed. Project knowledge remains in AGENTS.md and
was read back. Existing execution guides, setup/authentication and onboarding rules
remain applicable; this report does not change their contracts or claim OS gaps fixed.

<a id="fix-0131"></a>
## FIX-0131 — 2026-10-27 — Verify preserved cloud-resolution fixes and distinguish review from repair

Status: history/source/data investigation; no implementation changed.
Related: [FIX-0127](#fix-0127), [FIX-0130](#fix-0130), FIX-0125/0126 in the
[implementation log](../design-docs/implementation/FIXES.md).

### Problem

The user recalled a cloud-resolution fix for stalls and asked whether it existed
or was overwritten, requesting an enhancement to the management report.

### What was wrong

Cloud senior review, configurable read-only diagnosis and cloud coding recovery
were easy to conflate. The prior report also needed to distinguish a quota's
ability to override roles from proof of an override in this actual run. The saved
final replacements were proposed as local workers by the cloud senior itself.

### How it was fixed

Verified that 309713c (checking agent), 073f523 (FIX-0125 exception review) and
cb2fae5 (FIX-0126 stagnation) are ancestors of 5fe92f3. Diagnosis source is identical
to the fix tip. The pre-merge stagnation graph already bypassed diagnosis and
parked for senior review; default diagnosis role was worker from its introduction.
Recorded all four final stalls reaching cloud senior review, configured cloud
checking agents with zero diagnosis records, and requested/allocated replacement
roles. The earlier storage recovery was proposed and issued as a cloud specialist.
The separate unmerged diagnostic execution profile is unrelated to automatic rescue.

Enhanced both management reports and clarified the worker guide. A new explicit
cloud-first repair policy is proposed, not implemented. No runtime code, model,
configuration, test fixture, historical record, other worktree or budget changed.

### Design principle enforced or reconstructed

Trace actual control flow and pre-allocation intent before attributing a failure
to a merge or allocator. Cloud review is a decision boundary; repair execution
requires an explicit scoped task. New agent recovery policy must preserve provider
constraints, source authority, original accounts/deadlines and known-effect guards.

### Verification

Read-only Git ancestry/blob/graph comparisons and saved SQLite/proposal/backend
inspection support the finding of no overwritten cloud-resolution mechanism.
Machine-local cloud-resolution-audit-2026-10-27.json retains the evidence. Report
links/navigation and whitespace checks cover documentation maintenance; no new
model call, old-run resume, live recovery test or full framework suite is claimed.
The report's proposed cloud-first execution policy remains unverified. Current
project knowledge is refreshed/read back in AGENTS.md; adjacent runtime/context,
provider and recovery contracts remain unchanged.

<a id="fix-0132"></a>
## FIX-0132 — 2026-10-27 — Make local stalls transfer to bounded cloud coding and narrow planner assignments

Status: implemented in the uncommitted working tree; fixture verification complete;
fresh live qualification remains pending. Related: [FIX-0127](#fix-0127),
[FIX-0130](#fix-0130), [FIX-0131](#fix-0131), implementation FIX-0125/0126.

### Problem

The user observed coarse local assignments, repeated local failures without cloud
implementation takeover, excessive stalls and planner assumptions about unsupported
OS tools. The latest Minecraft attempt paused with no runnable tasks despite
43/256 and 87/256 calls used by the failing lineages. Cloud review alone did not
produce cloud coding. The top current-version issue links the combined
[requirements and implementation record](local-task-granularity-and-cloud-recovery-2026-10-27.md).

### What was wrong

The agent bounded semantic depth without a dedicated cloud implementation route.
Normal task-share rounding could demote a proposed specialist repair. A valid
empty/deferred plan could abandon recoverable local work, while broad task and
capability instructions encouraged unsuitable assignments. This is application
policy; generic OS settlement/accounting was not the missing coding decision.

### How it was fixed

Added agent-owned cloud eligibility/normalization before proposal validation,
`max_cloud_recoveries` (default one, range zero to three), lineage counters,
failure/changed-condition/source context and quota protection. Eligible clean local
retry/defer/stop/omitted decisions become actual cloud-specialist coding tasks even
after ordinary semantic depth is spent. Pending ordinary consumers are cloned and
rewired transitively; started contracts stay pinned. Conflicting deltas remain
preserved while automatic repair starts at the current base. Raw model proposals
remain separate from effective decisions/adjustments; final empty-queue blockers
state why cloud recovery is unavailable.

Planner instructions require one behavior/focused check per local task and expose
actual tool inventory: no browser/MCP/persistent service API or native-tool bypass.
Compact task contract/lineage review views avoid repeating dispatch/base/workspace
envelopes while retaining canonical records, specs, source pins and constraints.
Updated primary guides, configuration/design references, historical report pointers,
navigation and project knowledge; the issue is first in current issues and linked
at the top of the README. Preserved unrelated changes and all old live evidence.

### Design principle enforced or reconstructed

Cloud management, diagnosis and coding are distinct. Productive recovery is a
bounded application intent, not permission to weaken OS enforcement. Every linked
attempt inherits original calls/tokens/operations/grants/deadline. Unknown effects,
explicit cancellation, published work, unavailable cloud and depleted physical
resources remain blockers; cloud failure cannot bounce to local or reset counters.
A role rename on the same backend is not a changed condition. Already-linked
pending recovery supersession remains unsupported rather than resetting an account.
Validated local and cloud recovery roles survive allocation and are revalidated
before side effects. New policy uses
fresh program/config/state pins; no preserved run was migrated or resumed.

### Verification

Latest results across 228 selected cases: 227 passed and one unchanged baseline
100 ms provider-resume diagnostic failure. This combines group runs and targeted
reruns; it is not an all-green full-suite claim. The groups returned 57 passes;
49 passes/two UI poll timeouts; and 116 passes/one serial-policy timeout/one known
baseline failure. All three load-sensitive cases passed sequentially in 36.86
seconds without changing their deadlines. Two final role/validation checks and
six allocation/recovery checks passed; the duplicate ten-task case was interrupted
while the main planning group completed that case successfully. Exact coverage,
commands by source group and limits are in the linked implementation record.
Early checks exposed prompt/context overhead and a multi-task review overflow;
the prompt was compressed and task inputs projected without raising the default
context limit. Actual cloud dispatch, shared accounts/deadlines, source handoff,
bounded failure and transitive pending replanning are covered. Ruff, whitespace,
wheel contents and documentation generation/check passed (306 files / 134 leaves).
The initial offline build lacked setuptools; isolated temporary build dependencies
resolved packaging without modifying the active environment. No live model or
Minecraft qualification is claimed. Runtime boundary, endpoint/authentication,
setup and generic context/uncertainty contracts were reviewed; they need no policy
change because tools, grants, source authority and original accounts stay intact.
Project knowledge was saved/read back in AGENTS.md and docs/project-memory.md.

<a id="fix-0133"></a>
## FIX-0133 — 2026-10-27 — Plan remaining reliability fixes by ownership and map historical failure coverage

Status: investigation and proposed implementation report; no fixes implemented.
Related: [FIX-0127](#fix-0127), [FIX-0128](#fix-0128), [FIX-0129](#fix-0129),
[FIX-0130](#fix-0130), [FIX-0131](#fix-0131), [FIX-0132](#fix-0132).
Report: [run reliability implementation plan](run-reliability-implementation-plan-2026-10-27.md).

### Problem

The user requested a scheduled detailed plan for the latest run's executive
directions, explicit OS versus agent implementation ownership, and an assessment
against earlier failure records. The request explicitly excluded implementation.

### What was wrong

Older recommendations and current uncommitted cloud takeover can be conflated.
Cloud review did not imply cloud coding in the saved failing replacements, while
fixture-tested policy does not establish live convergence. Historical provider,
context, planning, source reuse, semantic and acceptance failures need different
owning-layer changes rather than one generalized retry or larger budget.

### How it was fixed

Added a report with direction-to-package traceability, detailed proposed designs,
current status/paths, tests/invariants/limits, staging and qualification gates.
Separated agent ledger/planning/cloud/repair/acceptance from generic OS context,
data-policy/allocation/limit/residency enforcement, provider setup and developer
tooling. Mapped twenty failure/gap families, explicitly identifying prospective
gaps and partial/out-of-scope coverage. Inspected historical reports and current
source, and queried latest attempt-02/03 SQLite records read-only. Reproduced
49+130 local physical attempts, 2+11 schema failures and 38+107 local-result
history omissions; confirmed zero diagnosis records and zero saved uncertain effects,
requested/issued local replacement roles, root account links and 43/87 calls used.
Added navigation, current-issue/investigation pointers and a retained AGENTS note.
All pre-existing implementation/documentation changes remain their original work.

### Design principle enforced or reconstructed

Productive recovery is application policy, including the host controller; the OS
must enforce generic authority, data constraints, accounting, admission and effect
certainty. Source retention, valid grammar, novel evidence and real product
completion are separate. Existing cloud takeover must be qualified rather than
reimplemented from an older report. A plan covering recurring mechanisms is not
proof that most historical failed products would complete. No implementation,
live model call, old-run resume, commit or push is authorized by this report.

### Verification

Documentation generation and `--check` both passed for 307 maintained files /
135 feature/doc leaves; `git diff --check` and the new report's whitespace review
passed. Preservation hashes match for all 133 snapshotted implementation, test,
example and script files, including pre-existing uncommitted work, and all twenty
selected historical database/journal files. AGENTS.md's retained project note was
read back. No framework suite or live workload was rerun; historical test/live
results remain attributed to their original reports. Adjacent execution, setup
and ownership guides require no behavioral edit for a planning report. The report
uses scoped source/history evidence, not an exhaustive revalidation of all prior
fixes or a statistical counterfactual completion estimate.

<a id="fix-0134"></a>
## FIX-0134 — 2026-10-27 — Enforce static process data/allocation policy and uniform limits

Status: implemented; final combined verification recorded in the [stage record](reliability-implementation-2026-10-27.md).
Related: FIX-0072 U01–U03, [FIX-0127](#fix-0127), [FIX-0133](#fix-0133).

### Problem
Registered mandatory data/distribution/limit declarations could differ from actual execution authority.
### What was wrong
Generic registration stored declarations without checking them; dispatch used global limits and role bindings.
### How it was fixed
Added runtime/process_policy.py registration/dispatch checks, optional run-wide data_policy, declared-location/classification/destination validation and static hard-rule rejection. Unequal process/runtime limits reject. Recovery preserves data policy as well as grants/limits. Coding defaults declare a real static harness contract. New runtime pin simple-os/3 requires fresh state.
### Design principle enforced or reconstructed
The OS honors or rejects generic mandatory constraints before effects; lane/URL names do not attest constrained placement. Application cloud staffing remains separate.
### Verification
Five new registration-denial regressions pass; intermediate generic fixtures exposed placeholder destination/role declarations and were corrected, retaining non-coding execution coverage. Combined/final results and limits remain in the stage record; no preserved run is migrated.

<a id="fix-0135"></a>
## FIX-0135 — 2026-10-27 — Retain paused residency until explicit safe hibernation

Status: implemented; final combined verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: U04 in FIX-0072, [FIX-0127](#fix-0127).

### Problem
A completed paused driver silently stopped counting against max_workers.
### What was wrong
Capacity counted unfinished Python tasks rather than durable logical residency.
### How it was fixed
Added durable process-residency admission generations, explicit hibernate after settlement/fencing, release on terminal finish and readmission on start. Clean process parking explicitly hibernates; unsettled effects/permits/reservations prevent release. The ProcessPorts boundary exposes the generic operation.
### Design principle enforced or reconstructed
Logical residency and provider physical holds are separate. A stopped driver or lost connection never proves remote termination or frees unknown capacity.
### Verification
New paused-resident/hibernation/replay regression passes. Generic deadline fixtures now retain uniform authority and explicitly hibernate before starting another worker. Restart/unknown-effect combined checks remain part of final verification.

<a id="fix-0136"></a>
## FIX-0136 — 2026-10-27 — Preserve bounded worker state and condition response repair on real errors

Status: implemented; final combined verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0047](#fix-0047), [FIX-0058](#fix-0058), [FIX-0130](#fix-0130).

### Problem
Optional history omission could remove current digests/errors; immediate schema retries reused input without the new error.
### What was wrong
Shared senior memory was not a bounded automatic worker fact ledger. The awaited response retry window had no production owner feedback builder.
### How it was fixed
Added agent/worker_memory.py with an 8192-byte source/generation-bound projection, trajectory/evidence references, recent digests/errors and next-step guidance. Worker inputs include root resource state/finishing reserves. A generic synchronous response-repair callback offers agent-owned error feedback through the existing guarded window; callback failures remain diagnostics. Agent/state pins advance to agent-7/2.6.
### Design principle enforced or reconstructed
The application owns canonical task semantics; the OS owns physical validation attempts, bounds and immutable pins. No recursive repair allowance or execution of partial output is introduced.
### Verification
New ledger invalidation/idempotence and real error-conditioned two-attempt tests pass. Existing agent/cloud focused cases pass in intermediate runs. Context/retry/native combined checks and live limitations are recorded separately in the stage record.

<a id="fix-0137"></a>
## FIX-0137 — 2026-10-27 — Retarget unstarted recovery consumers without new resource accounts

Status: implemented; final combined verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0088](#fix-0088), [FIX-0089](#fix-0089), [FIX-0132](#fix-0132).

### Problem
Replacing a failed provider could not rewire an already-linked pending recovery consumer safely.
### What was wrong
Blind cloning would drop the consumer's predecessor and mint a fresh allowance; the earlier safe implementation rejected the shape.
### How it was fixed
Review exposes eligible pending recovery lineage. Replanning retargets its original exception to the new pending assignment, preserving contract/source/predecessor and original depth/counts. It rejects an admitted/started consumer or effects, and publication atomically updates retirement/replacement records. Paired behavior/focused_check and declared check required_paths also make task completion closure explicit.
### Design principle enforced or reconstructed
Changing pending dependency identity does not renew authority. Started contracts remain immutable; cloud coding stays an application decision subject to OS data policy.
### Verification
The previous unsafe-clone negative fixture remains applicable. Positive transitive retarget, restart and account-preservation coverage is tracked in the stage record; no live convergence claim follows from planner guidance.

<a id="fix-0138"></a>
## FIX-0138 — 2026-10-27 — Add reproducible workflow qualification and physical-attempt metrics

Status: implemented; narrow offline/live gates passed; exact framework results/limits in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0086](#fix-0086), [FIX-0130](#fix-0130), [FIX-0133](#fix-0133).

### Problem
Unit/build success and generation activity did not demonstrate integrated product completion.
### What was wrong
There was no repeatable short workflow/settled-resume gate with independent checks and identical source/profile pins.
### How it was fixed
Added scripts/qualify_workflow.py corpus/manifests/independent checks and scripts/browser_check.mjs real DOM entry/input/pause/save/reload. Agent qualification metrics feed live/saved monitor data without double-counting logical/physical usage. Four fresh disposable trials include one ordinary settled run-level resume. The fixture provider is explicitly distinct from live inference.
### Design principle enforced or reconstructed
Useful completion needs actual behavior on accepted source. A finite browser check owns its server/process cleanup; it does not invent browser/MCP capabilities for the model.
### Verification
Initial fixture execution exposed a missing disposable Git baseline and retained that failed evidence; the harness now initializes its own disposable baseline. Final offline/live/browser results must be read from the stage record, not inferred from the presence of the harness.

<a id="fix-0139"></a>
## FIX-0139 — 2026-10-27 — Validate maintained HTML/settings and correct smoke/baseline fixtures

Status: implemented; final results in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0080](#fix-0080), [FIX-0129](#fix-0129).

### Problem
Green Markdown/tree checks missed maintained HTML anchors; schema/default drift and legacy fixture assumptions obscured real verification status.
### What was wrong
Validation omitted most rendered documentation HTML; live smoke inherited in-place mode despite asserting unchanged source. Deadline/pacing fixtures raced preparation and simulator assertions expected an obsolete 32000 target.
### How it was fixed
Extended maintained documentation HTML/anchor validation with explicit UI/template/upstream boundaries. Added exact settings-schema/default generation/check. Smoke explicitly selects isolated mode. Fixtures synchronize submitted/provider events, bound lookup independently within a usable deadline and assert the configured 4096 target. Production deadlines and unknown-effect rules are unchanged.
### Design principle enforced or reconstructed
Tooling must test its actual contract and retain adverse evidence; structural/schema checks do not prove prose or product semantics.
### Verification
Documentation generation passes at the current inventory. New HTML/default regressions, original baseline cases and final documentation/package results are recorded in the stage record. No real smoke/model call is claimed merely from repairing its mode.

<a id="fix-0140"></a>
## FIX-0140 — 2026-10-27 — Remove conflicting native startup effort from the UI preset

Status: implemented; verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0129](#fix-0129), [FIX-0133](#fix-0133).

### Problem
UI launcher selected low reasoning effort while the actual native turn used Endpoint.reasoning_effort, default medium.
### What was wrong
Two configuration surfaces implied different effective settings.
### How it was fixed
Removed the UI launcher's low override; explicit endpoint effort remains the native turn authority. Existing user-supplied commands are retained; no best-effort/model-performance result is inferred.
### Design principle enforced or reconstructed
Report configured and actually sent provider settings faithfully. Correcting configuration ambiguity is separate from improving model competence.
### Verification
Source/fixture native turn checks and UI configuration regressions are part of the combined verification. No new reasoning-level benchmark is claimed.

<a id="fix-0141"></a>
## FIX-0141 — 2026-10-27 — Bound replacement host drivers by the original account deadline

Status: implemented; final combined verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0089](#fix-0089), [FIX-0127](#fix-0127), [FIX-0137](#fix-0137).

### Problem
A linked replacement with a newer process start could keep its host driver running after its inherited root deadline, even though new effects were already prohibited.
### What was wrong
The generic driver timer used only the process start and wall limit. Existing account inheritance and dispatch coverage did not test a continuation waiting without submitting an effect.
### How it was fixed
Processes.start takes the earlier of its own cutoff and the durable process-account deadline. The regression uses a long child wall limit and a near-expired inherited deadline with a non-returning continuation.
### Design principle enforced or reconstructed
Recovery keeps the original account and deadline for host execution as well as effects. A new process identity cannot renew time authority.
### Verification
The new regression failed before the change and passed afterward; the selected deadline/restart/unknown-effect tests passed (3 tests). The full suite and final qualification results are recorded in the stage record. No preserved run was resumed or rewritten.

<a id="fix-0142"></a>
## FIX-0142 — 2026-10-27 — Preflight browser qualification in the actual check environment

Status: implemented; qualification results in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0086](#fix-0086), [FIX-0138](#fix-0138).

### Problem
The first live qualification preflight launched Chromium, but its configured worker check could not locate Playwright.
### What was wrong
The verification harness inherited dependency variables that the generic OS correctly removes from command environments. That preflight tested a different environment from actual checks.
### How it was fixed
Browser dependency and Chromium paths are pinned explicitly in command argv. Preflight uses the same runtime tool_environment as configured checks. Cancellation retains a failed qualification result and does not continue new trials. No OS environment filtering or source grants were weakened.
### Design principle enforced or reconstructed
Qualification must exercise the actual execution contract. Infrastructure readiness cannot depend on hidden supervisor state or be inferred from an unrelated successful launch.
### Verification
Through actual OS configured checks, the valid fixture passed and bad-save/missing-export fixtures failed in real Chromium. The aborted live trial remains preserved; its owned service drained with zero pending requests. New live qualification uses fresh state and a separate service instance. Exact results and limits are in the stage record.

<a id="fix-0143"></a>
## FIX-0143 — 2026-10-27 — Trigger qualification interruption after settled patch operations

Status: implemented; live continuation verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0138](#fix-0138), [FIX-0142](#fix-0142).

### Problem
Four live small workflows completed and passed independent Chromium checks, but the intended fourth interruption did not happen.
### What was wrong
The qualification hook recognized only files.write; the actual worker correctly used files.patch. The gate stayed red because there was no verified resume.
### How it was fixed
The hook recognizes successful changed observations from files.write/patch/delete and source-changing shell commands. Reads and failed edits do not trigger interruption. A fresh fifth trial exercises the fault while the four successful ordinary trials remain preserved with identical runtime/model/resource pins.
### Design principle enforced or reconstructed
A successful product check cannot substitute for an unexecuted fault scenario. Test injection must follow actual settled effects and the gate must reject a missing continuation.
### Verification
The retained initial results show four passing product outcomes and a failed qualification gate. Mutation-selector regressions and the additional live settled-resume outcome are recorded in the stage record. No old trial source, accounts or acceptance checks are repaired by the supervisor.

<a id="fix-0144"></a>
## FIX-0144 — 2026-10-27 — Include direct native worker effects in physical job reporting

Status: implemented; final reporting verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0138](#fix-0138), [FIX-0143](#fix-0143).

### Problem
The live resumed cloud task succeeded, but its task summary showed zero native jobs.
### What was wrong
The new summary selected inference-attempt rows only. Effectful native jobs deliberately bypass response retries and retain their physical result directly under effect/, so those jobs were omitted. Runtime execution, original accounts and provider records were intact.
### How it was fixed
Physical reporting selects retry-attempt rows when present, otherwise the direct model/native effect once, and still requires provider-submission evidence. Task lineage and live/saved summaries share that view. Qualification now also retains source archives/diffs, exact dependency versions and full stable profile/tool inventory for reproducibility.
### Design principle enforced or reconstructed
Count canonical physical work once, including jobs that cannot safely be response-replayed. Reporting repairs cannot create charges, change execution or rewrite historical journals.
### Verification
The regression proves direct native jobs are included and adding their retry rows cannot double-count them. Four selected metric regressions passed. The live cloud continuation has three confirmed direct worker jobs on its original account; corrected metrics are projected from retained journals separately from the original qualification results. Final suite/provenance checks are in the stage record.

<a id="fix-0145"></a>
## FIX-0145 — 2026-10-27 — Keep bounded worker-state eviction replay idempotent

Status: implemented; final combined verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0136](#fix-0136).

### Problem
Replaying the same bounded worker projection after byte-limit eviction published an unnecessary new revision.
### What was wrong
The projection reused already-trimmed facts but reset eviction counts to zero. Earlier replay coverage exercised only views that needed no byte eviction.
### How it was fixed
Eviction counts accumulate within the same source/generation view and reset with source invalidation. A regression uses sixteen valid deeply nested paths to force real byte eviction, then requires identical facts and revision on replay.
### Design principle enforced or reconstructed
Derived bounded facts must replay idempotently, including their metadata; packing cannot invent new progress or erase evidence of omitted facts.
### Verification
The regression failed with eviction counts 9→0 before the fix. Focused replay and final-suite results are in the stage record. The previous full run was stopped after 219 passes so the final full run can use the exact corrected source. Live qualification views had zero byte evictions; no grants, budgets or accepted source were changed.

<a id="fix-0146"></a>
## FIX-0146 — 2026-10-27 — Keep endpoint probing compatible with mandatory placement policy

Status: implemented; final affected-suite verification in the [stage record](reliability-implementation-2026-10-27.md).
Related: [FIX-0134](#fix-0134), [FIX-0139](#fix-0139).

### Problem
The explicit artifact-only endpoint probe was rejected when the endpoint had unspecified placement metadata.
### What was wrong
The application probe built a mandatory location rule from endpoint.physical_location, which guesses from a URL. That declaration conflicted with the newly enforced unknown-location policy.
### How it was fixed
The probe declares its actual static protocol class and local binding, leaving placement unrestricted at process level. The copied run-wide DataPolicy remains mandatory and rejects incompatible or unknown location before submission. One-call/no-tools/no-Git bounds remain. Retry fixtures now declare their one-call limit before runtime registration; UI pin and user-brief assertions follow the new version and equivalent compact instructions.
### Design principle enforced or reconstructed
Callers must declare authority they can establish. Lane/URL guesses cannot satisfy mandatory placement, and changing a fixture request cannot alter a registered resource envelope.
### Verification
The full 651-case run returned 646 passes and five integration/compatibility failures. After fixes, all 73 affected lifecycle/retry/brief/UI cases passed, including unspecified/local/cloud probe metadata and two fail-closed constrained cases. The final 655-case inventory is covered by passing results across the full run and affected rerun; see the stage record. This is not presented as a single all-green full run.

<a id="fix-0147"></a>
## FIX-0147 — 2026-10-27 — Prepare the scheduled real-local Minecraft test without early inference

Status: preparation/configuration only; the scheduled live outcome is pending.
Related: [FIX-0128](#fix-0128), [FIX-0138](#fix-0138), [FIX-0146](#fix-0146).

### Problem

The user requested autonomous setup and a fresh Minecraft live test at 22:30
America/Toronto, using the installed local IQ1_M model instead of Haiku and leaving
changes uncommitted for morning review. Preparation started before that time.

### What was wrong

No new framework defect is established. The existing target has unborn pi-dev and
untracked prior source; default in-place publication would conflict with the user's
uncommitted-delivery requirement. Sandbox GPU visibility also differs from the host.

### How it was fixed

No application/OS implementation changed. Created a one-occurrence in-thread app
heartbeat for 22:30 local and read back its saved schedule. Prepared the exact new
prompt, isolated fresh-state agent configuration, real Strata 65536/one-slot/group
configuration, technical check and execution handoff under the ignored local path
`../testing/minecraft-v1-live-2026-10-27-2230/`. Retained 320 framework and twelve
target-source hashes. Verified existing ChatGPT login and installed model component
presence without exposing credentials. Refreshed retained project rules in AGENTS.md.

### Design principle enforced or reconstructed

Future execution authorization permits preparation without claiming an early live
result. Agent Git/source/acceptance policy remains separate from generic OS authority,
accounting and provider GPU scheduling. Preserve prior source, immutable attempts,
original resources/deadlines and uncertain execution. Private isolated history must
not become a commit on the user's branch; exported partial work is not acceptance.

### Verification

Codex login status reports ChatGPT authentication; host GPU inspection finds the
16 GB RTX 3080 Laptop with no inference process. Strata inventory reports requested
IQ1_M components present. Existing Python environment imports current source and
`pip check` passes. Configuration/schema, launch-plan and documentation checks are
recorded in the local preparation receipt. No model readiness request, server,
live run, game change, framework suite, commit or push was performed in preparation.
Setup, provider, configuration/export, lifecycle, reliability and implementation
guides were reviewed; their existing interfaces remain applicable and need no edits.
No maintained file/feature appeared or moved, so authored navigation is unchanged.
Actual start, provider readiness, independent gameplay checks and final outcome
must be recorded after the time gate; earlier qualification results remain historical.

Execution handoff, 2026-10-27 22:38 Toronto: scheduled setup began after the 22:30
wake-up; frozen current-source CLI started at 22:33:26.984356 local. Actual Strata
metadata confirms IQ1_M, context 65536 and one requested/effective slot. Real local
and Codex readiness passed; specialist setup completed successfully and initial
planning is active. The target baseline remains unchanged/uncommitted. Host checks
passed 25 tests; actual baseline Chromium still has zero controls/terrain rectangles
and z=undefined. The finite baseline preview closed. The existing heartbeat now
quietly monitors this already launched run every fifteen minutes, with duplicate
launch forbidden; final export/behavior verification/cleanup and outcome are pending.
Evidence and continuation live in the run's REPORT.md. No framework implementation
or prior runtime state changed; this handoff does not claim product completion.

Continuation handoff, 2026-10-27 23:42 Toronto: the first driver paused at 23:28:06
on confirmed-stopped 4096-token output exhaustion, without uncertain effects or a
development report. Supported exports, a database backup, resource records and
private source were retained before one documented same-state CLI Resume at
23:39:26. The worker's original identity/start/deadline remain; calls 52→55 and
steps 90→95 verify no refill. Configuration/source pins and target hashes remain
unchanged. The live report records the output/thinking-budget limitation and
forbids identical exhausted recovery without a changed condition. This is testing
and bounded continuation, not a framework fix or accepted gameplay claim.


<a id="fix-0148"></a>
## FIX-0148 — 2026-10-28 — Record the scheduled live result and preserve checked partial delivery

Status: investigation/test completed; partial delivery, original product objective unmet.
Related: [FIX-0147](#fix-0147), [FIX-0128](#fix-0128), [FIX-0132](#fix-0132), [FIX-0138](#fix-0138), [FIX-0144](#fix-0144).
Evidence and exact review paths: [scheduled live investigation](minecraft-live-test-2026-10-28.md).

### Problem

The scheduled autonomous test needed a real local IQ1_M lane, actual Codex setup,
long-run evidence and uncommitted morning delivery. Earlier unit/qualification
success did not establish playable Minecraft or full original features through 2018.

### What was wrong

The original browser still used z against the x/y core. The fresh run improved
entry/control/save behavior, but local tasks repeatedly stalled and needed bounded
cloud coding. Its first pause was output exhaustion under the pinned 4096 raw target
and thinking budget; the final loading recovery stopped on provider model capacity.
No single model/quantization/context root cause is established. The application owns
product convergence and browser integration; provider capacity is an external failure.
The earlier small qualification gate covered narrower cases, not this full objective.

### How it was fixed

No framework implementation changed. Ran the exact prompt on a 320-file frozen copy
of the dirty current source with fresh state, real Strata/Qwen 65536/one-slot serving
and existing Codex login; no Haiku/simulation. Retained pre-resume exports, database
and private source before one supported same-state continuation, with original worker
identity/start/deadline and charged counters. Four automatic cloud coding recoveries
completed; loading recovery failed on capacity and remained private/unreviewed.

Supported final CLI/status/patch and full UI exports, exact reviewed/provisional
source, private failed trees/diffs, canonical metrics and independent Chromium
artifacts remain under the local run directory. After twelve original target hashes
and new-path conflict checks, applied exact reviewed tree c24e088 uncommitted on
unborn pi-dev. Six paths changed, including one new browser-entry test. No manual
game implementation, model/config rewrite, budget refill, user commit or push occurred.
Updated the investigation, issue/index/navigation pointers and retained AGENTS note.

### Design principle enforced or reconstructed

Task meaning, source reuse, acceptance and Git policy remain in the agent; generic
execution certainty, grants and accounting remain in the OS; actual serving/capacity
remain in providers. Keep execution, reviewed increments and full product acceptance
distinct. Preserve immutable source/config pins, original root resources and failed
private work. A useful partial delivery must not erase the failed live result.

### Verification

Final host Node checks passed all 44 tests. Real Chromium passed entry/movement,
explicit window-blur, pause/timing, seed validation/determinism and thirteen save/
storage assertions, including bytes surviving page reload. Repository API loading
was a separate diagnostic; browser load/list and restored play are absent. Gravity
and jumping are absent, and both text fields leak arrow input into movement. Native
OS focus switching remains inconclusive in headless Chromium. Most requested
Minecraft gameplay and UI remain unfinished; no final acceptance was attempted.

Canonical final metrics report 280 submitted raw generations, 46 native jobs,
26 response-validation failures and 214 raw context-omission receipts. Native jobs
may contain multiple turns. The final NativeJobStopped effect is confirmed stopped;
zero effects are uncertain. All five linked recoveries preserve predecessor/root,
limits, deadlines and equal/narrower grants. Frozen source/config hashes match.
Owned Strata stopped with exact owner/instance guards; previews/inhibitors ended.
Documentation generation/check and whitespace checks passed. Adjacent setup/provider,
configuration/export, reliability/qualification and boundary guides remain accurate;
no interface change required edits. The full framework suite was not rerun for
this investigation/documentation-only work. The one-time heartbeat was deleted.


<a id="fix-0149"></a>
## FIX-0149 — 2026-10-28 — Isolate Minecraft live failures against frozen source and canonical evidence

Status: investigation complete; repairs proposed, no framework/game implementation changed.
Related: [FIX-0148](#fix-0148), [FIX-0132](#fix-0132), [FIX-0136](#fix-0136), [FIX-0137](#fix-0137), [FIX-0144](#fix-0144).
Detailed findings and proposed repair order: [failure isolation](minecraft-failure-isolation-2026-10-28.md).

### Problem

The final capacity error explained the stop but not the preceding hours of weak
convergence, repeated recovery or the remaining broken gameplay. The user requested
isolation of everything that went wrong using the retained live report.

### What was wrong

Canonical evidence identifies twelve areas with distinct owners/confidence. The raw
4096 target caused thirteen cutoffs despite a 16384 hard allowance; 24 raw responses
failed grammar/schema validation. The chat adapter sends no schema constraint on
this path. Five later local tasks stagnated, including three read-only tasks with
66 generations and no edit attempt. Conservative context packing used a 49152-byte
bound on a real 65536-token server; 214 calls omitted optional history and actual
prompt usage never exceeded 13839 tokens. No state byte eviction is demonstrated.

A corrected search retained an obsolete path-specific tool error in worker memory.
The diagnosis packet omitted the failing entry/test and granted no reads; it could
not identify the harness's early clock restoration. Test.ok misuse and wrong blur
event targets also undermined early integration tests. Final Node tests missed text
field input leakage and did not supply real browser feedback to the workers.

Clean failed model operations take the controller pause path rather than generating
semantic exception packets for cloud takeover. The final native job's brokered
effects correctly blocked generic replay, requiring an application continuation
policy that was not automatic. Capacity, local quality, test coverage and recovery
policy are separate findings; no single quantization/packing root cause is proven.

### How it was fixed

No implementation fix was applied. Added a maintained failure-isolation report and
source/evidence-backed repair order, refreshed issue/index/navigation and retained
AGENTS knowledge. A read-only analyzer and metadata under the original run's new
`diagnosis-2026-10-28/` directory retain exact attempts, local trajectories, check/shell
outcomes and two offline reproductions. The original REPORT, frozen runner, database,
config, delivered/private source and budgets were preserved. No new inference,
Resume, provider setup, game edit, commit or automation was performed.

### Design principle enforced or reconstructed

Separate observed failures, causal mechanisms and hypotheses. The agent owns task
suitability, working memory, diagnosis, semantic continuation, browser-check purpose
and full product acceptance. The OS must keep generic input/output bounds, original
accounts/deadlines, source authority and native side effects safe. A retryable native
terminal message does not authorize blind replay of executed writes. Provider
capacity is external evidence, not proof of exhausted account quota or local OOM.

### Verification

Read-only reconstruction matches 280 raw generations/46 native jobs. The 37 rejected
raw attempts consumed 46.5 of 178.3 local provider minutes (26.1%, not wall-clock
waste). Action history contains 178 local reads, 84 exact repeats. Ten of eleven raw
cutoff chains eventually recovered; one caused the first pause. The pre-resume
snapshot confirms model_failure with zero semantic exception packets. The final
retry reason explicitly requires caller continuation after brokered effects.

Memory-only projection reproduces an obsolete error surviving a schema-correct
search. Offline request preparation confirms no provider schema/JSON constraint for
the chat path. Diagnostic source selection and exact failed check artifacts identify
the clock/test.ok errors; the camera-coordinate suggestion was only an unconfirmed
diagnostic hypothesis. Private loading had a 45-test intermediate pass and further
edits/focused checks, without final report/review; it remains separate from delivery.

Documentation generation/check and whitespace verification passed. Existing browser
and 44-test results were analyzed, not rerun as new evidence. No full framework
suite ran for this documentation/investigation-only task. Worker/retry/context,
reliability/qualification and ownership guides were reviewed; behavior/interfaces
were not changed, so no guide implementation update was needed. The new report
explicitly distinguishes proposed fixes from implemented behavior. Retained project
knowledge in AGENTS.md was read back; original source/run preservation was checked.


<a id="fix-0150"></a>
## FIX-0150 — 2026-10-28 — Verify no-edit task necessity and trace current context and worker-state behavior

Status: investigation complete; current defects reproduced, no fixes implemented by explicit user instruction.
Related: [FIX-0149](#fix-0149), [FIX-0136](#fix-0136), [FIX-0145](#fix-0145).
Evidence and corrections: [focused follow-up](minecraft-failure-isolation-2026-10-28.md#convergence-context-memory-followup).

### Problem

The user asked whether the three local tasks that made no edits actually needed
changes, what OS code restricted context despite a 64K model, and whether the
reported memory error affected the current system. The user explicitly said not
to implement fixes.

### What was wrong

All three tasks needed missing browser integration, despite existing generate and
repository APIs. Their actual starting HTML/entry lacked seeded creation, Save copy
or saved-world refresh/load controls and handlers respectively. All physical replies
were read/list/search actions, including the malformed seed reply; all stopped
workspace source remained byte-identical to each task's pinned base.

The OS does not impose a fixed below-31K-token ceiling in this run. Kernel.measure
counts serialized UTF-8 request bytes. ContextService caps them at
min(400000,400000,65536-16384)=49152, with optional-group packing toward 48128 bytes.
The 29491-byte compaction target is inactive because auto_compaction=false. The
kernel sends a 4096 output target while context preparation reserves the 16384 hard
ceiling. This conservative byte policy explains low actual prompt-token use; it
does not show a smaller Strata window or actual tokenizer-based input counting.

Current worker_memory.project has the path-key mismatch previously identified:
a valid search without path does not retire an earlier invalid path-shaped search
error. Seven live save-task model inputs after the corrected search retained that
hint. Seed/load had no such error, so it cannot explain all three stalls. A second
current defect skips observation=None entries before clearing protocol errors;
valid candidate/assessment/needs_review replies can therefore leave old protocol
errors active. The second defect is reproduced offline, not established as this
run's cause. These are bounded working-state defects, not canonical-memory corruption.

### How it was fixed

No implementation, configuration or maintained test changed. Added a focused
follow-up to the existing failure analysis, issue/history pointers and retained
AGENTS context. Read-only scripts/RAM probes in the original run's new
`followup-context-memory-2026-10-28/` folder retain pinned source comparisons,
physical reply types, exact context replay and current projection cases.

Corrected two earlier analysis claims explicitly: FileRead accepts both limit and
max_bytes; that was not a contract mismatch. The earlier 178 reads/84 repeats came
from worker-state trajectory snapshots that trail final tools at parking. Full
canonical ordinary read effects total 182, with 88 repeats using model arguments
and digest, or 85 including host-injected generation. Original evidence remains
intact; only the earlier analysis's interpretation is corrected.

### Design principle enforced or reconstructed

Investigations must verify that assigned behavior is missing before treating no
edits as failure, and distinguish actual tokens from conservative byte bounds.
Agent working-state error lifecycle belongs to the application. Generic OS context
bounds and original evidence remain authoritative. A stale derived view is not
proof of canonical data loss. Respect the explicit analysis-only scope rather than
expanding memory architecture or silently implementing even small fixes.

### Verification

Compared every tracked source file in all three stopped workspaces with their
pinned Git trees and inspected all 66 physical replies. Current OS context code
matches the frozen source and RAM replay exactly reproduces the saved prepared
digest, omitted refs and byte receipt for worker-10/model-18. Six current projection
cases reproduce the two defects with a successful-action clearing control and
idempotent replay; FileRead accepts both byte-count argument names. Existing replay/
invalidation tests do not cover these resolution cases; no new maintained tests
were added or source fixed. Documentation generation/check and whitespace passed.
Original report/config/database/frozen source and delivered game hashes were checked.
Worker/context guides remain applicable; no behavior/interface changed. AGENTS
retained knowledge was read back. No provider/browser run, Resume, commit or push.

<a id="fix-0151"></a>
## FIX-0151 — 2026-10-28 — Existing browser keyboard isolation and real regression coverage

**Status:** implemented in the uncommitted reviewed game; no new gameplay.

### Problem

The partial Minecraft entry treated text-field arrows/A/D and Escape as gameplay
input. Focusing an editable control could leave prior movement held. FIX-0148–0150
identified this after Node tests and a narrower browser qualification had passed.

### What was wrong

The entry attached keydown to document without checking its target, and cleared
held input on window blur but not when focus moved into an editing control. Stub
coverage lacked these real focus/input transitions. The existing qualification
increment-button fixture did not exercise a game's keyboard behavior.

### How it was fixed

The target game's src/main.js ignores editable keydown targets and clears held
movement on focusin, preserving keyup releases. Two actual-entry Node regressions
cover these transitions. A retained finite tests/browser-real.mjs checks actual
Chromium controls, pause timing, save durability and failure preservation; it
owns/closes its server and browser. Qualification wording now names its narrower
increment fixture. Existing timing, blur and assertion repairs were rechecked.

### Design principle enforced or reconstructed

Application event routing belongs to the product. Test the existing behavior on
its actual entry; a passing stub or unrelated fixture cannot establish browser
playability. Do not add missing loading/physics/features under a bug-fix request.

### Verification

Two regressions failed before repair; 46 Node tests pass after it. Eight actual
Chromium checks pass with no page errors; the screenshot was inspected. Native OS
focus switching, loading/resumed play and full 2018 gameplay remain unverified or
missing. Runner root-path mistakes were harness errors corrected before those
checks. Source/evidence and documentation are retained in the
[implementation record](model-fallback-browser-repair-2026-10-28.md). No commits.

<a id="fix-0152"></a>
## FIX-0152 — 2026-10-28 — Agent-selected provider fallback with durable OS routing

**Status:** implemented for fresh simple-os/4 state; old runs remain frozen.

### Problem

The live run ended on native cloud model capacity after completed brokered tools.
Ordinary retry correctly refused a blind effectful replay, but no alternate-model
continuation existed. The user explicitly authorized this mechanism after the
analysis-only FIX-0149/0150 work and specified agent-selected Terra/high.

### What was wrong

OS retries covered unchanged transport/output attempts, without durable model
selection or a bounded alternate window. The native adapter did not expose trusted
terminal same-thread continuation for this case. An application task replacement
would conflate provider routing with semantic recovery and risk repeating effects.

### How it was fixed

Generic Endpoint.retry_model exposes alternate model/effort and fallback_calls;
seven is the OS default count, overridable by agent input. The OS has no model
default. AgentConfig.default_retry_model selects Terra/high for native cloud,
respecting explicit endpoint overrides/null and stable serialization. The latest
user sequence supersedes the earlier immediate probe: retry the failed logical
request once on alternate, use it for X subsequent invocations, then restore the
configured primary model/effort; a failed primary probe repeats that sequence.

runtime/model_fallback.py persists binding-wide selections/window and OS-issued
intents. It shares original admission, grants, accounts, reserves and logical
deadline without refilling ordinary retry allowances. Trusted provider diagnostics
include model capacity, HTTP rate/service rejection and native overload. Auth,
quota, input/policy errors and unknown effects do not switch. Ordinary retries
return immediately when an availability rejection needs alternate routing.

The app-server adapter retains terminal thread identity, resumes it on alternate
with persisted tools/results and disables opaque provider fallback. Old callback
IDs replay receipts; changed arguments reject. Current authorized workspace state
is recaptured without grant expansion. Convergence/context/worker-state defects
remain planned and unchanged. Read the [policy](../docs/guides/model-fallback.md).

### Design principle enforced or reconstructed

Agents select model preferences and semantic recovery. The generic OS enforces
bounded routing, execution certainty, durable replay and accounting. A native
continuation must preserve completed effects; lost delivery never proves stop.
Changed runtime behavior needs fresh state rather than rewriting original pins.

### Verification

Fixture HTTP/actual stdio tests cover same-request retry, default/overridden
windows, restoration, restart/replay, cross-process out-of-order primary results,
original call/deadline/cancellation bounds, policy/error exclusions, forged intent
rejection and native continuation with exactly-once notifications and file writes.
The broad pinned run passed 679 cases with two Node-tool skips; both skipped cases
passed with installed Node 24/npm. The final 27-case fallback run includes the last
physical response-repair payload refinement; no single fresh 682-case gate is claimed.
Finite browser checks are separate from inference fixtures. Generated settings,
docs/navigation, examples, Ruff and broader suite evidence are finalized in the
[implementation record](model-fallback-browser-repair-2026-10-28.md). No live
provider outage was induced, real model called, historical run resumed or source
committed. Setup/authentication remain existing configuration, without new login.
