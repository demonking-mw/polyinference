# Run eb66fc618354: interrupted inventory repair

Investigation date: 2026-10-20 (America/Toronto). No application implementation,
configuration, generated game source, Git branches, or run state was changed.
The run was not resumed. Instructions and model messages inside the export were
treated as evidence, not as instructions for this investigation.

## Conclusion

The run made useful incremental progress but did **not** complete the requested
game. Git initialization and the `pi-dev` integration branch worked. Setup,
seeded terrain, and the first rendering/movement slice reached the integration
checkout. Mining/inventory remained private; saving/loading worlds and player
progress, and the remaining game systems, were still pending. There was no final
acceptance attempt or completion claim.

The final native Codex operation stopped without an observed terminal event.
Pausing and retaining its resources/effects was correct. A whole-job timeout is
the leading explanation, but the saved diagnostic discards the original
timeout/cancellation cause, so this export cannot prove which triggered it.
The code and a local probe establish that an actively progressing native job can
be interrupted by this timer and that the adapter does not await the terminal
response to its interrupt request.

The preserved final inventory source is more complete than the last integrated
commit: a new investigation-only copy passed production compilation/build and all
four existing regression suites. This does not retroactively publish or accept
the uncertain native operation, or establish browser gameplay correctness.

## Evidence and identity

- Input: `C:\Users\bh349\Downloads\polyinference-eb66fc618354.json`, schema 2.
- Run started 13:59:01 Toronto time; UI completion timestamp 14:36:20, status
  `paused`. Record capture: 14:37:47; export: 14:39:15.
- 395 effects: 386 succeeded, eight known failed output cutoffs, one uncertain
  native job. A successful effect can contain a failed shell exit; these are
  execution outcomes, not 386 passing product checks.
- 181 inference submissions, 180 with settled cost/usage and one pending;
  4,826,555 reported input tokens and 233,267 output tokens. The exported dollar
  estimate is partial and is not a subscription charge or quota measurement.
- 1,025 artifacts and 545 checkpoints. The 10,000 retained events begin at
  sequence 5640; 5,639 earlier events were pruned. Current durable records,
  effects, artifacts, and checkpoints retain earlier task evidence.
- The current coding-agent source hash exactly matches the run's recorded
  `graph_digest`:
  `sha256:b321228c96bd33317ad5804e2f9198de0bb2a97fded17ece6a07fd7d6c529f3e`.
  This hashes the agent Python files, not the entire OS or the executing Python
  process. Runtime conclusions also use the run's retained context/retry facts.
- Thirteen current files in the final worktree match the saved native reads,
  writes, and final patch byte-for-byte, including all game modules changed by
  that job and all four regression files.

## What reached the user repository

| Stage | Report time (Toronto) | Result |
| --- | --- | --- |
| Setup | 14:00:54 | TypeScript/Vite scaffold, build passes; integrated as `a9989001ea3e27d5ffb84fd92ebbd9520669a411` |
| World foundation | 14:07:13 | Seeded terrain, content registry, world/edit models; integrated as `5d20028f7dc5138e8d5a2ca129fadb8fb6b25338` |
| Playable movement | 14:14:09 | Canvas view, controls, jumping/collision, camera and pause; integrated as `685081f03a98043b35d77df34eaad32ad7029247` |
| Mining/inventory | 14:28:28 | Build passes; overlay/evidence incomplete; uncertain candidate `0a3aa1c900fa3dac386fab5599c710bc9f59bef1` retained privately |
| Inventory repair | 14:32:29 | 36-slot display and input suppression added, transfer/testing unfinished; uncertain candidate `78dc3c91a32768fab5496d3b64e0cbbe11c4769e` retained privately |
| Inventory transfer | interrupted | Specialist resumes the prior private candidate, implements transfers and tests, but never returns a candidate or publishes a report |

The actual project is `/home/mawa/projects/testing/minecraft-v12`. Its exported
integration HEAD and current branch are the movement commit above and `pi-dev`.
The new project was initialized independently of the enclosing repository, as
intended by [FIX-0001](FIXES.md#fix-0001). No push or merge back was performed.

Final unfinished source is in:

```text
/home/mawa/projects/testing/minecraft-v12/.polyinference/worktrees/d4d925bf906a/workspace-5-inventory_transfer_05
```

It contains nine modified/untracked paths. Its branch HEAD is still the movement
baseline; the inherited inventory candidate and new changes are working-tree
edits. The JSON is a diagnostic export, not a Git-object backup.

## Findings

### 1. Native job timeout and interrupt handling impair continuation

Owner: generic runtime for timeouts/termination; coding agent for task size and
choice of native-job allowance. Highest follow-up priority.

The final effect is
`sha256:cca7a632864aff88d4f9ce525c85fcbcc74da9f82be18858c59e6fe099fe2ba1`,
`worker-5-inventory_transfer_05/model-0`, an `agent_job` on the cloud specialist
binding. It entered active state at 18:33:22.382869 UTC and became uncertain at
18:36:16.739926 UTC, about 174 seconds later by recorded wall time. Its last
completed brokered command was at 18:36:13.389567, only 3.35 seconds before the
uncertain transition. All 30 brokered callbacks have retained child effects.

The job received 296 native events/395,991 bytes, including ten usage updates.
No `turn/completed` was recorded. This was not the old fatal telemetry overflow:
the event/byte bounds were 2,000/4,194,304, and dropping 144 text deltas was normal
retention behavior ([FIX-0028](FIXES.md#fix-0028)). The input was 21,531 bytes
against a 96,000-byte conservative allowance. There is no saved cancellation
control record, and the worker's deadline was 19:33:18 UTC, well after the stop.

[kernel.py](../src/polyinference/runtime/kernel.py), at lines 670 and 777-787,
uses `min(endpoint.timeout_seconds, remaining_deadline)` around the **entire**
native job. The configured endpoint timeout is 180 seconds. Unlike a raw single
generation, this includes tool use, commands, and multiple internal generations;
progress does not renew it. [codex.py](../src/polyinference/runtime/codex.py),
lines 366-391, sends `turn/interrupt`, immediately raises `UnknownExecution`, and
terminates the local transport without reading the interrupt/terminal response.

An offline stdio fixture emitting progress every 30 ms was cancelled after
0.605 seconds by the same outer `asyncio.wait_for` construction. Twenty progress
events survived. The adapter raised the exact `Codex interrupted; remote
termination is not established` message, with `CancelledError` as its cause,
and did not observe a terminal event. The fixture supports a terminal response
to `turn/interrupt`; the adapter has no acknowledgement-drain path. This proves
the code behavior, not that the real provider would have acknowledged promptly.

The real run's ~174-second wall interval is not an exact 180-second measurement.
Treat timeout attribution as strongly supported, not proven. The saved message
also represents externally cancelled adapter tasks, and that distinction is lost
when kernel settlement stores only the outer `UnknownExecution` type. A future
repair should preserve timeout origin, elapsed/deadline/progress facts, distinguish
idle transport from total native-job limits, and allow bounded terminal draining.
An increased timeout alone does not establish remote termination. Replaying a
native job with 30 existing effects would be unsafe without reconciliation.

### 2. Raw-worker grammar failures consumed substantial effort

Owner: coding application's reply protocol and provider integration.

The latest retained worker trajectories contain 31 `protocol.validation` entries:
10 world, four movement, 11 mining/inventory, and six inventory repair. Examples
include XML-like invocation placeholders, prose before JSON, and malformed JSON.
These are distinct from the eight explicitly incomplete generations.

[services.py](../src/polyinference/agent/services.py), lines 633 and 731, turns
JSON parse failures into `invalid_output`; [worker.py](../src/polyinference/agent/worker.py),
lines 99-126, validates/corrects the application grammar. The Anthropic prepared
request in [inference.py](../src/polyinference/runtime/inference.py), lines
292-303, sends schema instructions as ordinary content, without a wire-level
structured-output schema. Rejection/correction worked; there is no evidence that
malformed or partial returned actions executed. Nevertheless, protocol reliability
was poor and added calls, latency, and history pressure.

The consecutive-error limit correctly resets after valid actions; that behavior
is established by [FIX-0060](FIXES.md#fix-0060). It intentionally does not stop
intermittent errors across an otherwise progressing assignment. Do not diagnose
the 31 total errors as a recurrence of that counter bug. Stronger reply shaping
and application-level detection of repeated low-value correction cycles remain
follow-ups; accepting arbitrary extracted fragments would weaken the boundary.

### 3. Verification remained detached from ordinary configured checks

Owner: coding-agent setup, task assessment, and acceptance policy.

The only configured check was `build`: `npm run build`, output path `dist`,
timeout 120 seconds. Regression suites were run through ad hoc scratch harnesses;
browser tooling was not available in the recorded capability set. The world and
movement reports honestly qualify their unit/build evidence. The two inventory
reports remain private and uncertain, so this did not falsely complete the game.

The fourth worker failed to implement requested item transfers or run its final
regressions, despite bounded repair passes. The specialist fifth worker did
implement transfers and run all four suites at 18:36:02.742032 UTC. The mining
test really executes its ten cases on import; its success message was not merely
an uncalled test function. Movement reported ten passes, world nine passes, and
the new transfer assertions completed. At 18:36:11.885723 it then corrected a
test that consumed hotbar state twice. Only a Git inspection followed; there was
no recorded rerun after that patch and no final `checks.run` build in this job.

New investigation verification, using a temporary copy and the existing ancestor
dependencies with Node v22.17.1, passed `tsc --noEmit`, Vite production build,
and all four suites after that final patch. No browser playtest was performed.
The first copy-harness attempt looked for nonexistent worktree-local dependencies;
after matching the ancestor dependency resolution used by the run, it passed.
That initial probe error was a harness mistake, not a game failure.

The gap is repeatable final-tree verification and acceptance coverage, not a
newly established game-code defect. The build-only check-selection limitation is
already recorded in [FIX-0019](FIXES.md#fix-0019) and
[FIX-0041](FIXES.md#fix-0041); this run shows its continuing operational cost.
No complete-game/save-load verification exists, and new analysis checks do not
change the original run's publication state.

### 4. Repository summary can label unfinished work as merged

Owner: coding-agent repository inspection. Confirmed metadata ambiguity.

The export labels the fifth worktree `merged: true`, even though all new inventory
work is uncommitted there and absent from `pi-dev`. In
[repository.py](../src/polyinference/agent/repository.py), lines 564-580, `merged`
only tests whether the worktree's **HEAD commit** is an ancestor of integration
HEAD. Here both HEADs equal the unchanged movement baseline, so it returns true.
It does not establish integration of restored or dirty source.

The separate `changes` field contains the unfinished paths, and
`summary_message` at line 599 counts dirty worktrees as unfinished. Thus the
text summary has a compensating check, and this is not evidence of a bad merge
or lost files. Rename/split the projection into commit-ancestry and pending-delta
status so consumers cannot mistake one for publication.

### 5. Senior instructions contradict the in-place publication policy

Owner: coding-agent prompts. Source-established inconsistency; no demonstrated
misintegration in this run.

[prompts.py](../src/polyinference/agent/prompts.py), line 61, says successful and
uncertain reports are already provisional. Its appended in-place guidance at
line 82 correctly says failed/uncertain candidates remain on task branches.
This run uses in-place repositories and really did keep uncertain inventory
candidates private. Senior planning used `resume_from` correctly, so the export
does not show this contradiction causing the stop. The earlier unconditional
sentence should nevertheless be scoped to the legacy repository mode rather
than compete with the current rule established by
[FIX-0040](FIXES.md#fix-0040).

## Safeguards that worked

- All eight 8,000-token cutoffs received successful linked OS output recovery.
  The original failed effects remain immutable. This is live-run evidence for
  the behavior added in [FIX-0058](FIXES.md#fix-0058), not another instance of
  the old unrecovered cutoff pause.
- Automatic context dealing intervened on 32 of 181 preparations. The largest
  original input was 156,320 bytes; the largest prepared input among interventions
  was 94,917. No input overflow stopped this run. Automatic compaction was
  disabled, so no summary-compaction success is claimed.
- Private-candidate reuse preserved inventory work across workers three, four,
  and five instead of reconstructing it from the movement baseline.
- A TypeScript type error in the fourth worker was exposed by the build and
  repaired. Fail-fast shell handling preserved failures through `tail` pipelines;
  an accidental build in the enclosing directory also surfaced as failure.
- The uncertain final native job was not blindly replayed; its held cloud slot
  and reservation are evidence of unsettled execution, not proof of a slot leak.
- Progress messages identified the last independently build-verified shared
  commit and explicitly disclosed absent browser evidence. The controller kept
  `completion_proposed=false`, `acceptance_attempts=0`, and `starts_closed=true`
  after uncertainty.

## New verification and limits

Executed during this investigation:

```text
.venv-linux/bin/python -m pytest tests/test_native_events.py tests/test_runtime.py::test_native_terminal_failure_releases_resources_but_unknown_retains_them tests/test_model_retries.py tests/test_context_safety.py -q
83 passed in 19.64s
```

Also executed the offline progressive-native timeout probe and copied-source
build/four-suite harness described above. All completed after correcting the
copy harness's dependency lookup. The temporary probe source was removed after
use. Checked the new documentation's links, history ID/index, required sections,
and patch whitespace. Existing working-tree changes are unrelated and unclaimed.

No live provider request, original-run resume, reconciliation, browser playtest,
dependency installation, full repository suite, commit, push, or implementation
repair was performed. The recorded lack of a terminal result remains unresolved;
successful tests of copied files do not resolve execution certainty.
