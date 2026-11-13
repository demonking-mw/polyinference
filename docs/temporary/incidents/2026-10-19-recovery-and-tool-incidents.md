# Agent recovery and tool incidents

## Agent interruption bookkeeping breaks senior recovery — 2026-10-19

Status: investigation preserved below; the attempt-validation and prompt-authority
fixes are now implemented in the boundary refactor documented above.
Incident: run `e94b7049eeda`, repository
`/home/mawa/projects/testing/mincraft-6`.

### Ownership: agent implementation, not a demonstrated OS defect

Here, "agent" includes the Python controller/worker workflow and its prompt
assembly, not just the model's decisions. The design explicitly assigns task
ledgers and sprint decisions to the agent (`design-docs/simplified-os/README.md`,
section 3). `TaskAttempt` is an agent application contract. Its invalid update is
written by `agent/worker.py` and later rejected by `agent/controller.py`.

The OS record service intentionally stores generic application JSON with
compare-and-swap/atomicity guarantees; it does not interpret or validate each
agent's task schema. Persisting the payload supplied by the agent is not evidence
of a storage bug. Schema validation for this record belongs at the agent's write
boundary. Likewise, omitting already-supported setup authority from the model's
inputs belongs to agent prompt/context assembly.

The observed OS behavior was sound: model/tool operations settled, check failures
were recorded against the correct source revision, temporary caches stayed outside
source, leases/capacity were released, and the uncommitted replacement plan was
not partially activated. The controller's decision to pause after its own exception
is agent policy. No new OS scheduling, isolation, grant-enforcement, or transactional
storage defect is demonstrated by this run.

### What stopped the run

The visible blocker is an agent-side `TaskAttempt.stop_reason` validation failure,
not a failed model operation. `contracts.py` types this field as `Identifier`,
whose maximum length is 256 characters. The setup worker returned a valid
`needs_review` reply with a 317-character explanation. `agent/worker.py:park`
first validates the previous attempt, then uses `model_copy(update=...)` to put
that explanation into `stop_reason`. Pydantic does not validate those updates.
The generic record store consequently persisted an invalid attempt at
`attempt/setup-project` revision 4. Its complete explanation is also retained
in the task's `exception` field and model history.

The worker parked successfully at `05:48:19Z`, released its verification permit,
and allowed senior review to continue. Senior inference completed successfully at
`05:48:38Z`: the proposal retired `project_setup` and created
`bootstrap_game_project`, with explicit paths for `package.json`, a lockfile,
HTML, JavaScript, styles and README. The proposal was durably staged in
`review-batch/active`, state `applying`.

`ProjectAgent._apply_review` then tried to validate the old attempt before
replacing its reason with the valid short code `superseded_by_plan`. That read
rejected the already-persisted 317-character value. The controller paused the
run and exposed the Pydantic exception as the blocker. The atomic plan activation
had not happened: no `task/bootstrap_game_project` or `plan/1` was committed.
There were no uncertain effects; both model lanes and both critical sections
were released. This is a recoverable agent application-data/schema defect,
rather than evidence of unfinished provider execution.

### Why setup asked for review

Setup selected `production-build` (`npm run build`) while the source contained
only `.gitignore`. All six recorded check invocations returned a normal failed
check, exit 254, because `package.json` did not exist. Reconciliation/assessment
repeated without creating the scaffold, including two assessment replies asking
for repair. The worker eventually asked to expand its `.gitignore`-only scope.

That authority diagnosis was misleading. The run used `write_scope=project`,
and its setup task specs already contained `polyinference/project-write=true`.
`Tools.run` and `Workspaces.extend_setup_scope` can extend the setup grant when
new explicit project paths are written; the existing setup regression exercises
this through a new file created by shell. No rejected scaffold-write attempt is
present in this export. However, setup's pinned inputs expose the initial
`assignment.write_paths` without the project-write policy or an explanation of
automatic extension. The bootstrap prompt asks for prerequisites without making
that authority explicit. This is an agent context/prompt defect, not
proof that the runtime forbade those files. The previously documented distinction
between setup checks and final product acceptance remains a separate policy issue.

The previous housekeeping fix is working: npm logs point to
`state/tool-environment-*/cache/npm`, the source digest stays stable across the
checks, and no cache-related write-scope violation occurred.

### Repair direction and verification

- Keep `stop_reason` consistent with its contract: use a bounded reason code and
  retain the complete human explanation separately, or deliberately introduce a
  bounded diagnostic-text contract. Do not silently write arbitrary prose into
  an identifier field. Audit other interruption/exception writers, including
  the controller path that currently allows up to 2,000 characters.
- Validate updated task-attempt records at the agent's write boundary before
  persistence, not just their old values. Do not add task-specific validation to
  the generic OS record store. Include recovery/retirement of already-invalid
  persisted attempts; fixing only new writes will not unblock this staged review.
- Supply setup with its effective write authority and explain when new project
  paths may extend the seed scope. Preserve explicit-scope restrictions.
- Add an integration regression with a long valid `needs_review.reason`, senior
  replacement/retirement, and restart/replay of the staged review. Check that
  the full explanation survives and the replacement is activated exactly once.

A read-only probe using the installed Linux dependencies and this export
reproduced the mismatch: `model_copy` accepted 317 characters, then
`TaskAttempt.model_validate` rejected the serialized copy with
`string_too_long`, maximum 256. The export confirms `review-batch/active=applying`
and the absent replacement task. No code changes or historical-state edits were
made for this investigation; the regression suite was not rerun.

## Tool housekeeping caused a false write-scope pause — 2026-10-19

Status: OS fix implemented and verified. Incident: run `667b821fa4b0`, repository
`/home/mawa/projects/testing/minecraft-5`. This is separate from the provider
output-limit and native-event incidents below.

### Failure sequence and ownership

The run was still in automatic setup. The setup workspace's write grant contained
only `.gitignore`; senior planning and development had not started. Setup selected
`npm test` as its check before a `package.json` existed. The command returned 254
with an ENOENT error for that missing manifest.

The OS launched the check with `HOME` set to the private source root. npm therefore
created `.npm/_logs/2026-10-19T05_24_02_715Z-debug-0.log` and
`.npm/_update-notifier-last-checked` inside the workspace. The workspace scanner
uses fixed exclusions rather than `.gitignore`; `.npm` was not excluded. The check
first became inconclusive because it appeared to modify source. At the following
worker `acquire`, `Workspaces.preserve_delta` rejected those extra files with
`Private changes exceed write scope`, before issuing a verification permit.

That host exception paused the task/process, and the controller closed further
starts and durably paused the run. The driver then exited. This was not a model
operation waiting for a reply: all eight recorded OS effects had succeeded, no
effect was uncertain, and no execution lane or lock remained held. The failed
npm subprocess was represented in check evidence. The private workspace survived,
but there was no publication, final report or automatic retry of the host node.

The primary stack bug was placing ordinary tool housekeeping in assessed source.
The scope guard correctly rejected files outside the setup grant. Selecting a
product check before its manifest existed is a separate agent/setup-policy issue;
this change does not make that command pass or weaken acceptance.

### Implemented fix

- `runtime/tool_environment.py` supplies one temporary environment per check or
  shell invocation, under runtime state and outside the workspace tree. `HOME`,
  XDG cache/config/data/state, temporary-file paths, npm cache and pip cache all
  point into it. Commands retain their source working directory and existing
  bounded execution/output policy. They do not inherit the operator's home.
- `runtime/tools.py` and `runtime/shell.py` share this environment. Bubblewrap
  receives an explicit writable `/tool-environment` bind separate from
  `/workspace`. Cleanup completes before releasing the installation-wide shell
  lease, including failure, timeout, cancellation and process-start failure.
- `runtime/workspace.py` versions the environment policy in the execution
  environment digest as `isolated-tool-environment-v1`.
- Source scanning, evidence invalidation and write grants are unchanged. There
  is no new `.npm` ignore exemption: an actual unauthorized `.npm/source.js`
  written in the source root must still invalidate evidence and fail preservation.

### Verification and operational limits

`tests/test_tool_environment.py` covers successful, failed, timed-out, unavailable
and cancelled checks; shell housekeeping; sandbox mount/path mapping; and genuine
out-of-scope source changes. A real native Linux Node/npm regression runs
`npm test` without a manifest: it remains a failed check, its source revision stays
unchanged, and delta preservation succeeds. Temporary directories and shell leases
are checked after cleanup. The sandbox test verifies mount construction; it does
not execute bubblewrap.

The full Linux suite passed: **188 passed** in 201 seconds, including the native
npm regression and browser-script checks with Linux Node 22. Ruff passed for
`src` and `tests`; whitespace checks passed for the changed files.

The historical paused run and contaminated workspace were not rewritten or
resumed. Restart the backend to load the fix for new invocations. A missing
`package.json` still needs a suitable check or the project files it requires.

## Output-token cutoff paused a recoverable worker — 2026-10-19

Status: implemented and verified. Incident: run `f5bcd770dbe6`, repository
`/home/mawa/projects/testing/minecraft4`, worker `worker-1-content_registry`.

### What happened

Setup completed, reconciled, passed assessment and published. The senior planning
call also completed successfully. The first development worker listed its files,
then its next model query (`model-1`, operation
`sha256:ff05b9c0014897bef89fb917e4897446f2131565d4481de428b10c42f4c2e32a`)
stopped at `2026-10-19T04:56:11Z` with `Anthropic did not complete: max_tokens`.
The configured per-call output budget was 8,000 tokens. No development file write
had executed; the only development tool observation was `files.list`.

The assignment was a substantial content registry. The stop reason confirms an
output-token cutoff, but the old adapter discarded the partial reply and usage,
so the export cannot establish how much of the budget was thinking versus visible
JSON. Haiku 5.5 thinking is enabled by default and counts toward `max_tokens`;
see the official [migration guide](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide).
This was a confirmed stopped generation, not an unknown transport failure.

The host correctly refused to execute incomplete JSON. The stack defects were
treating this cutoff as a generic terminal provider failure, pausing the whole
agent without a smaller-response recovery, and losing provider usage/stop metadata.
The export's unpriced call and missing actual-backend fields reflect that loss.

The previous incident's fixes were working: the senior native call retained 20
events while discarding 1,212 text deltas, and the UI reported the durable paused
state with the original blocker and no terminal-reporting errors.

### Fix

- `runtime/inference.py`: output-token stops produce a typed `IncompleteGeneration`
  observation, with partial visible text, provider/model ID, normalized usage,
  stop reason and the requested output limit. Thinking text is excluded. Equivalent
  chat `length`, Responses `max_output_tokens`, and Gemini `MAX_TOKENS` stops receive
  the same classification. The adapter never returns partial text as a completed
  actionable response, even if that text happens to be syntactically valid JSON.
- `runtime/kernel.py`: keep the original operation failed/confirmed stopped, retain
  its incomplete-output artifact and classification, record the actual backend and
  provider-reported token usage, and settle budgets using that usage. Output limits
  do not count as permanent authentication/request failures in the circuit breaker.
- `agent/services.py`: recover only classified, known-stopped HTTP model queries.
  Use new, durably linked operation IDs within `max_model_recoveries` (default two),
  preserving the original request/result. Each new request adds trusted feedback
  asking for a smaller complete response, with progressively lower visible-JSON
  targets (normally 4 KB, then 2 KB). It never executes or continues the partial JSON.
  Scaffolds and subsequent small patches replace large whole-file responses.
- The actual configured output-token cap stays unchanged. The original objective,
  workspace grant, phase, model-call limits, recovery allowance, process deadline
  and final-phase reserve still apply. Unknown execution and other provider failures
  do not take this automatic recovery path. Exhaustion still pauses safely.
- Recovery requests/results are replayable without another provider submission,
  including after the recovery allowance is exhausted. Workers count actual durable
  model operations so recovery calls cannot silently consume the final-phase reserve.
- Worker prompts and pinned `response_budget` inputs now encourage small actions
  from the first call, before a cutoff occurs.

### Verification

`tests/test_output_limits.py` adds 11 cases covering visible and thinking-only
cutoffs, other supported HTTP protocols, recovery after one/two failures, immutable
replay, no partial tool execution, usage/budget settlement, finite exhaustion, and
the mandatory-phase reserve. The tests use local fixture transports, not live models.

The full Linux suite passed: **178 passed, 1 skipped** in 202 seconds. This includes
the earlier native-event, reporting, recovery and export regressions. The final
progressive response-size guidance was additionally verified by rerunning all
11 output-limit tests. Ruff passed for `src` and `tests`; whitespace checks passed.
The historical run and its failure records were not rewritten.

## Native event overflow and reporting failure — 2026-10-19

Status: fixes implemented; Linux regressions verified in the output-limit follow-up
above, superseding the initial verification limitation. This section concerns
run `daec3ddd8884`, distinct from the historical HTTP 400 incident below.

### Failure sequence

Setup completed and published successfully. The first senior planning operation,
`senior-1/model-0` (`sha256:a1bd9134b8ddbd719f11ff2745a978803a9d5ed58212fb30b6baee5a60afe8db`),
stopped at `2026-10-19T04:19:38Z` with `Native event limit exceeded`. The adapter
counted all native notifications, including text deltas, against a 2,000-event /
4 MB execution limit. The export did not retain the failed stream or identify which
threshold fired. The OS correctly kept the submitted operation uncertain and paused
the run. No development assignments had started.

The terminal reporter then evaluated `value.get("result", {}).get("error")` on
an uncertain effect containing `"result": null`. The resulting `AttributeError`
(`'NoneType' object has no attribute 'get'`) replaced the visible execution error.
The summary gave the reporter's error precedence over the durable paused state.

### Implemented changes

- `runtime/codex.py`: event retention is now a bounded rolling buffer, independent
  of execution. Streaming deltas are counted but discarded. Receiving more than
  2,000 notifications or 4 MB no longer ends a healthy call. Final assistant text,
  latest usage and terminal state are tracked independently, including notifications
  arriving before the turn-start RPC response. Tool callbacks still execute through
  the broker; their effects retain the existing durable audit trail. The buffer's
  bounds, transport line bound, reply bound and execution deadlines remain enforced.
- Native success results include retention counters. Failures carry bounded native
  diagnostics: received event/byte counts, retained/dropped counts, bounded method
  counts, and the last 24 event types/sizes. Failure summaries omit prompt text,
  response text and tool arguments. The kernel preserves these through native
  exception wrapping, in uncertain effect records or known-failure result extensions.
  The OS view and JSON export expose them.
- `ui.py`: terminal reporting handles null results. Printing, event parsing and
  reporting reads cannot replace a runner result or exception. Reporting failures
  are deduplicated and bounded in a separate `reporting_errors` metadata list, which
  is included in saved/exported run metadata.
- `snapshots.py` / `ui.html`: summaries preserve a durable paused state and resolve
  operation-ID blockers to their original diagnostics. The blocker ID remains
  available separately; the user-facing status displays `blocker_detail`.

### Regression coverage and verification

- `tests/test_native_events.py`: noisy stdio server emits over 4 MB of deltas and
  more than 4,000 notifications; reply, usage and callbacks must survive retention
  eviction. Disconnect and confirmed failure preserve bounded payload-free
  diagnostics. Separate checks bound retained bytes and method cardinality.
- `tests/test_runtime.py`: known and uncertain native failures retain diagnostics
  through the kernel; existing assertions still enforce the distinction between
  released and retained admission reservations.
- `tests/test_ui.py`: null-result reporting, broken terminal output, original runner
  exceptions, durable pause summaries, and exports with separate reporting errors.
- `tests/ui_start.test.cjs`: paused runs display their original operation diagnostic
  instead of an opaque hash. All **6 browser-script tests passed**.
- Python syntax checks passed. Local probes executed the actual adapter definitions
  with an in-memory transport, exercising normal and early terminal delivery after
  4,204 events, disconnect, confirmed failure and transport cleanup. Event-retention,
  logger and summary probes also passed. These probes do not replace Linux pytest
  or exercise real subprocess timing. `git diff --check` passed for tracked changes.
- Initially the Linux regression command could not execute: automatic approval review rejected
  WSL launches because its selected reviewer model was at capacity. This was an
  approval-service failure, not a test failure or a finding that the command was
  unsafe. It was subsequently covered by the full Linux run above. Focused rerun:

  ```bash
  .venv-linux/bin/python -m pytest -q tests/test_native_events.py tests/test_endpoints.py tests/test_runtime.py tests/test_ui.py tests/test_ui_os.py tests/test_history.py
  ```

The historical run and its uncertain operation were not modified. An interrupted
local session is not automatically treated as proof of provider termination;
existing reconciliation requirements and retained-capacity safeguards remain intact.
