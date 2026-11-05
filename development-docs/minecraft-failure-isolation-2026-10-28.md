# Minecraft live-test failure isolation — 28 October 2026

[Live result](minecraft-live-test-2026-10-28.md) · [Current issues](current-iter-issues.md) · [FIX-0149](FIXES.md#fix-0149)

**The capacity error ended execution after hours of poor local convergence.**
The earlier failures include an effective output cap, unreliable reply grammar,
repeated reading, incomplete diagnostic inputs, two recovery routes with different
outcomes, and a test profile unable to verify browser play. The delivered result
remains a foundation with major gameplay and UI gaps. No implementation was changed
by this analysis, and no provider was relaunched.

The original final REPORT and its evidence remain unchanged. Machine-specific
evidence root, abbreviated **RUN** below:

`/home/marven/Projects/pi/testing/minecraft-v1-live-2026-10-27-2230/`

`RUN/diagnosis-2026-10-28/` contains a reproducible read-only analyzer, physical
attempt metadata, failure counts, check/shell outcomes and two offline reproductions.
It reads the consistent final database and original artifacts. Analysis uses the
frozen runner source, not a guessed reconstruction of the run. Claims below cover
observed failures; unimplemented features and unproven causes are distinguished.

## Measured execution

| Local assignment | Submitted generations | Local provider minutes | Outcome | Cloud follow-up |
| --- | ---: | ---: | --- | --- |
| Browser entry/x-y | 132 | 106.5 | Completed after one operator Resume; focus defect found in review | Separate focus task |
| Focus/input | 44 | 32.2 | Stagnated | Three native jobs, 4.5 minutes, completed |
| Pause/resume | 38 | 24.0 | Stagnated | Three jobs, 4.8 minutes, completed |
| Seed creation | 30 | 8.5 | Reads only; no edit attempt | Three jobs, 6.1 minutes, completed |
| Save copy | 17 | 3.4 | Reads/list/search only; no edit attempt | Three jobs, 11.7 minutes, completed |
| Load saved copy | 19 | 3.7 | Reads/list only; no edit attempt | One job, 5.6 minutes, capacity failure |

These are summed physical generation/job intervals, not task wall times or a
controlled comparison of fresh local/cloud performance. Cloud jobs reused prior
source and include many tool calls; one native job is not one raw generation.
There were 280 raw generations and 46 native jobs overall, including management,
setup and diagnosis. Of the local generations, 37 were rejected: 13 output cutoffs
and 24 response-validation failures. They consumed **46.5 of 178.3 local provider
minutes (26.1%)**. Local action history contains 178 file reads, including 84 exact
repeats with the same arguments and file digest. Novel paged reads are not counted
as repeats. Three read-only tasks consumed 66 generations without attempting edits.

## F01 — Provider capacity stopped an already productive native job

**Confirmed external stop; application continuation limit.** The loading recovery
received a terminal `NativeJobStopped` at 07:12:07Z: selected model at capacity.
Its effects were known and execution confirmed stopped. This does not establish
account quota exhaustion, bad login, local GPU OOM or a deadlock.

The native job had already performed 15 reads, eleven patches, four shell commands
and one configured check. Its checked intermediate tree passed **45 tests at
07:09:01Z**, including one load test. Further test patches and six focused passing
tests followed. There was no final full-tree check/report/reconciliation/assessment
or senior keep after those edits. That private work is retained, not lost, and the
45-test result cannot certify its final tree. It was correctly excluded from the
44-test reviewed delivery.

The exact retry outcome says **native job has brokered effects; caller continuation
required**. [ModelRetries](../src/polyinference/runtime/model_retries.py) deliberately
blocks blind replay of effectful native jobs. [Codex normalization](../src/polyinference/runtime/codex.py)
retains a generic stopped-job error; it does not provide a capacity-specific
continuation policy. The application has explicit settled Resume, but no automatic
policy reconciled this job and waited for verified availability within its remaining
root resources. Such a policy is a follow-up; retrying writes or changing models
inside generic transport retry would violate the boundary. Availability returning
later was never established, so successful continuation is not proven.

## F02 — Clean model failures bypass semantic cloud recovery

**Confirmed application control-flow gap for unattended operation.** At the first
pause, the local output chain was exhausted and fully settled. The pre-resume
database has `model_failure` on the browser task and **zero worker-exception packets**.
It did not reach the mechanism that later recovered all five stagnated tasks.

[AgentServices.model_result](../src/polyinference/agent/services.py) raises
ModelOperationFailure for failed model operations except response-validation and
finishing-reserve cases. [Controller worker failure handling](../src/polyinference/agent/controller.py)
records an interrupted task/model_failure and pauses the run. The normal
[semantic parking path](../src/polyinference/agent/exceptions.py) creates the exception
packet consumed by cloud takeover. These are different paths.

One supported operator Resume at 23:39:26 continued the original stopped worker;
it did not repair the output profile or exercise automatic cloud takeover for that
failure. A clean, exhausted model operation needs an explicit application decision:
bounded changed-approach continuation, eligible cloud handoff, or honest terminal
failure. Unknown effects, cancellation and resource exhaustion must still fence it.
The OS's safe pause was correct; complete autonomous recovery was not implemented.

## F03 — The effective output ceiling was 4096, despite a 16384 hard allowance

**Confirmed profile/response-fit problem; thinking attribution unproven.** All
thirteen cutoff responses report 4096 completion tokens and a length stop. They
consume 20.8 local provider minutes. The configured 16384 ceiling does not enlarge
the actual [raw target](../src/polyinference/agent/services.py), which was pinned
at 4096. High reasoning and a 4096 thinking budget were also pinned. There is no
separate measured thinking-token count establishing which fraction caused a cutoff.

[Output adaptation](../src/polyinference/runtime/model_retries.py) requests smaller
visible UTF-8 responses while retaining the token target, objective and original
resources. Ten of eleven raw cutoff roots eventually recovered; one original plus
both adaptation attempts exhausted and caused the first pause. It is inaccurate
to say all output recovery failed or that no correction was supplied.

The response format includes escaped source edits, and the first cutoff attempted
a whole entry rewrite. Incremental edits were requested but not reliably followed.
Qualify output/thinking/patch sizes together on a new disposable profile; measure
visible response capacity before selecting limits. This evidence does not justify
editing old pins or claiming a larger target alone solves convergence.

## F04 — Valid action generation was unreliable at two boundaries

**Confirmed protocol failures; model/server attribution remains open.** The 24 raw
validation failures comprise 23 invalid-JSON cases (eleven EOF cases and twelve
other syntax/format cases) plus one missing assessment verdict. Responses included
prose, Markdown/XML tool wrappers and incomplete JSON. EOF validation errors are
distinct from the thirteen provider length stops. Two native senior proposals also
failed validation because focused_check was absent from their assignment checks;
bounded repair handled them.

The [chat adapter](../src/polyinference/runtime/inference.py) accepts a response_schema
argument but sends no response_format, JSON schema or tool constraint on this path.
An offline wire preparation reproduces that absence. JSON shape is instructed in
the prompt and validated after generation. This does not establish that the server
supports constrained decoding, nor that switching a flag would solve the problem.
Do not weaken the parser or execute partial/wrapped model text to make a pass.

Five capability effects also failed: one existing-file write with a null digest,
one ambiguous exact patch, one list with unsupported path, and two searches with
unsupported path. Tool schemas and CAS protection rejected them correctly. The
worker failed to follow the supplied interface; prompts alone did not ensure it.
JSON-shape enforcement alone would not correct a stale digest or wrong tool arguments.
Future qualification must exercise actual create/update/search/check/assessment
grammar, including provider-side enforcement only where explicitly supported.

**Correction from the subsequent follow-up:** the original analysis called
offset/max_bytes versus offset/limit a prompt/tool discrepancy. That finding was
incorrect. FileRead accepts both limit and max_bytes, and the handler supports both
(max_bytes takes precedence). Neither spelling is a demonstrated contract defect.

## F05 — The local workflow repeatedly failed to turn inspection into implementation

**Confirmed convergence failure; exact model-quality cause not isolated.** All five
local tasks after entry stagnated at twelve idle decisions. The final three never
attempted an edit or configured check. Earlier tasks also looped on already-read
source and irrelevant experiments. An idle threshold correctly contained each
stall; it did not teach the worker to make progress.

The task contracts were narrower than the old whole-menu/physics assignments, but
still coupled entry code, tests, three documentation paths and several behavioral
invariants. Scalar behavior/focused_check fields validate structure, not actual
model difficulty. The completed cloud repairs show the work was feasible under
the retained grants, not that the local model should necessarily complete it.

Routing continued assigning each new ordinary task to a worker. Automatic cloud
takeovers were real, protected and successful four times; they were not demoted.
The raw senior proposals also chose workers for fresh tasks. Static task-count
[allocation](../src/polyinference/agent/routing.py) and per-lineage recovery do not
adapt task suitability from repeated cross-task failure. Count-based quotas also
include started recoveries; there is no evidence here of a requested cloud task
being overwritten. Follow-up should use measured task difficulty/failure history
and bounded discovery-to-edit checkpoints rather than repeating local-first work
indefinitely or just increasing the idle/call allowance.

## F06 — The model had a fraction of the advertised context, with weak semantic continuity

**Confirmed conservative packing tradeoff; causal contribution plausible.** The
server really served 65536 context. [Context preparation](../src/polyinference/runtime/context.py)
uses a conservative UTF-8 byte bound: min(400000, 65536−16384) = **49152 bytes**,
then leaves recovery headroom. Actual local prompt usage was **4573–13839 tokens,
median 11484**. Server configuration was not secretly reduced to 16K; the host
conservative estimator left most of the actual token window unused.

Optional history was omitted on **214/280** raw calls. Original input reached
395372 bytes; submitted input peaked at 48095 bytes. Auto-compaction was off.
Required input grew to 33733 bytes. The final loading packet's module_context
alone was 13460 bytes, up from 3773 for entry, leaving less room for action history.
The full objective/contracts remained present; there was no required-input overflow.

The required bounded state preserved digests/errors/check refs, but did not retain
source excerpts, a durable implemented-versus-pending checklist or a concrete next
edit. Its next_step was generic. This leaves a plausible rereading cycle when
optional code/result pairs fall out of view. All final worker states show zero
byte-limit evictions, so **8192-byte state eviction is not the demonstrated cause**.
A trusted model-specific tokenizer and better application-owned semantic working
state are testable improvements; neither permits silently dropping mandatory data.
No controlled run isolates packing from model quality, quantization or prompting.

## F07 — An obsolete tool error remains an active next-step instruction

**Reproduced framework defect.** A files.search call with unsupported path fails.
The following schema-correct search uses pattern and has no path. In
[worker_memory.project](../src/polyinference/agent/worker_memory.py), successful tool
calls clear only errors matching both tool and path. The old path-specific search
error therefore survives; next_step keeps saying resolve current error.

The live save task shows exactly this sequence at turns 8/9. Its final state retains
the old error. The first successful entry report also retained a list-argument
error despite passing checks. A memory-only call of the frozen projection reproduces
the search case; no live records were modified. Historical errors should remain
in canonical evidence, while the working view marks superseded errors resolved
and offers an actionable task step. Earlier replay/eviction fixes did not cover
this error-identity mismatch. Its influence on the model's decisions is unproven.

## F08 — The checking agent could not see the files needed for diagnosis

**Confirmed diagnostic input/capability gap.** The one diagnosis concerned a failed
movement assertion in tests/browser-entry.test.js. Its source preview budget was
spent alphabetically on .gitignore, README/docs, index, package and prerequisites;
only 93 bytes remained for src/core.js. It included **neither src/main.js nor the
failing test**. The native job had zero granted capabilities and readonly-query
protocol, so it could not request a current full read through the broker.

[Diagnosis construction](../src/polyinference/agent/diagnostics.py) selects the first
5000 source bytes by sorted path rather than the failing boundary. The returned
diagnosis explicitly says the source/tool was unavailable and classification is
uncertain. Requested worker reads and an unchanged recheck did not establish a
root cause. Its camera-coordinate suggestion was only a hypothesis: the actual
test parsed world-coordinate text. The harness instead restored the real clock
before its simulated frames, so advancing fakeTime did not advance game time.
Turn 90 removed that early restoration; a separate test.ok API error surfaced next.
Focused diagnostic source
ranges or explicit bounded read-only inspection would be useful; giving the OS
coding semantics or granting diagnostic writes is unnecessary.

## F09 — Green tests did not model real browser interaction

**Confirmed test/profile gap, with several separate defects.** Baseline tests passed
25 cases while entry used z against the x/y core and drew no usable terrain.
The first new harness restored performance.now before executing fake frames, then
used nonexistent test.ok. Those produced three movement-check failures (including
the unchanged diagnostic recheck) and one TypeError before repair.
Its focus test dispatched blur to document while real window blur was unhandled;
26 passing cases did not catch that defect. Senior review and the supervisor's
real-window probe did catch it, and the later cloud repair fixed it.

The final 44-case suite still missed editable-element input isolation. Global
document keydown in the delivered `src/main.js`
adds movement keys without checking the focused target. Real Chromium showed
ArrowRight moving the player from both seed and save-name fields. This is an
unresolved integration defect, independent of output limits or capacity.

Only project-checks was registered for the live run: Node tests/basic files, with
no browser check. The earlier narrow qualification had a finite browser runner,
but it was not integrated into this Minecraft profile. Supervisor Chromium checks
were outside the worker feedback loop, and observed defects were deliberately not
injected as steering into the pinned experiment. These are test-design limits;
the absence of a general native browser/MCP capability does not prevent configuring
a bounded real-browser check before a fresh run. Add focus/editing, timing,
create→play→save→load and failure/recovery checks on the actual entry.

## F10 — Most of the requested product was never implemented

**Confirmed unmet scope; no false full acceptance.** The reviewed output is a
264×264 tile-colour view and marker, horizontal movement, pause, seed creation and
named Save copy. It has no browser list/load/restore, no gravity/jumping, and no
functional browser mining/building/inventory/crafting/survival loop. Core movement
is cardinal tile stepping; gravity is disabled and jump is a reserved no-op.

Saved bytes survive reload and repository API loading works, but reload starts
a fresh world. That is persistence infrastructure plus saving, not resumed play.
Most required mobs, dimensions, redstone, fluids, recipes/content, multiplayer and
complete settings/menu flows remain absent. Plain fields/buttons and a white marker
also fail the requested Minecraft-like gameplay UI. The inherited core/repository
primitives predate this run; six delivered path changes do not implement those gaps.

The original objective and strict criteria were preserved, and acceptance was
never attempted. Eleven sprints yielded five nonempty kept increments, four needing
cloud repair. There was no demonstrated effort forecast or milestone path from
that pace to the full inventory. A category checklist is not an exhaustive dated
feature registry. Plan measurable playable milestones and a coverage ledger while
retaining the complete objective; do not redefine partial scaffolding as success.

## F11 — Several investigations tested the wrong execution environment

**Confirmed worker inefficiency and workspace-interface misuse.** The focus worker
made eleven shell calls, including importing the DOM-dependent entry in bare Node
twice (document undefined), scratch module probes with incorrect working directories
and default exports, and experiments whose errors were hidden by `|| true`.
These failed to establish the intended module-instance hypothesis and made no
source changes. A shell effect being succeeded means execution completed, not
that a test or hypothesis succeeded.

Cloud workers also made five failing Git CLI calls in isolated code workspaces
without .git. That absence is expected: the host owns private Git history. One
worker repeated the same failed diff twice and then requested diff --stat. Expose
mode-appropriate host diff/history evidence and reinforce actual workspace facts;
do not create .git or bypass publication to satisfy these probes.

Across canonical effects, 49 configured checks returned 45 passes/four failures;
38 shell calls included nine nonzero exits. All four configured failures were in
the first entry task and were subsequently repaired. Two additional focused pause
tests failed during cloud repair and later passed. These semantic command outcomes
are not the same count as the 19 failed OS effects or 26 response validations.

## F12 — Supervisor/test-environment incidents and qualification limits

**Recovered/inconclusive events, not established live-run root causes.** Sandbox
Node discovery counted two file wrappers, so actual host execution was required
for 25/44-case totals. The first Playwright probe used an implicit context and
could not open another page; only the diagnostic helper was corrected. Headless
tab switching emitted no blur, so native OS focus-loss coverage remains inconclusive;
the explicit real-window blur contract was tested separately.

The first native readiness command was rejected by automatic review for possible
source disclosure, then approved after inspection established fixed text/empty
temporary directory. Authentication and both readiness probes passed. These are
setup/test-environment incidents, not the final capacity failure.

The earlier small gate covered narrow browser workflows and settled Resume; it
did not qualify this local model/profile for growing multi-file coding contracts,
repeated failures or full Minecraft completion. Passing that gate did not promise
this result. Useful next qualification should include the observed failure shapes
and the exact browser check/profile used in the broad run.

## What the evidence does not blame

No observed wrong model, remote Haiku, serving-context reduction, runtime deadlock,
GPU OOM, corrupted source, budget refill, authority expansion, uncertain replay or
unwanted user commit explains this run. GPU samples peaked at 87°C/14446 MiB with
median utilization 100%; no clock/throttling evidence isolates a thermal cause.
IQ1_M quality, thinking allocation, prompts and packing may interact; there was no
controlled comparison to identify one as the sole root cause. Four real cloud
takeovers, immutable history, source conflict checks and honest partial acceptance
boundaries worked and must survive any fixes.

## Repair order and regression criteria

1. **Qualify local execution and autonomy first (F02–F05).** Exercise small real
   edit/check/assessment tasks; select measured output/grammar settings. Route clean
   exhausted operations to an application-owned decision with original resources.
   Unknown work must remain fenced; no blind native-job replay or budget reset.
2. **Repair working state and diagnostics (F06–F08).** Retire obsolete errors,
   preserve concrete implemented/pending facts and select failing source before
   unrelated previews. Reproduce repeated-read stalls and successful correction.
3. **Put real browser checks in the feedback loop (F09/F12).** Test editable input,
   focus, physics and complete saved-world UI on exact source. A broad green Node
   suite must not substitute for those checks.
4. **Adapt routing and product milestones (F05/F10).** Use observed local outcomes,
   preserve cloud takeover authority, and verify a complete playable loop before
   spending more sprints on documentation and adjacent infrastructure.
5. **Handle provider interruption explicitly (F01/F11).** Preserve partial jobs,
   classify terminal causes where supported, and authorize bounded reconciled
   continuation only with a changed/verified condition and original account/deadline.

These are proposed fixes, not implemented or live-validated changes. Verification
for this analysis: canonical count reconstruction, frozen-source control-flow review,
two offline reproductions, source/run preservation audit, documentation generation/
check and whitespace checks. Existing browser/44-test results are retained evidence,
not newly rerun checks. No framework suite, new model run, game edit or commit occurred.

<a id="convergence-context-memory-followup"></a>
## Follow-up — task necessity, exact OS limit and current worker-state bugs

The user requested closer examination of these three points and explicitly said
**do not implement fixes**. This follow-up changes investigation/documentation only.
It does not propose a new memory architecture. Derived evidence and executable
read-only/RAM probes are under `RUN/followup-context-memory-2026-10-28/`.

### All three read-only tasks genuinely needed entry edits

The check used each assignment's actual pinned base, not today's more complete
delivered tree. Complete starting files and every physical reply were inspected.

| Task and pinned base | What already existed | What the actual assignment required but the entry lacked | Logged work |
| --- | --- | --- | --- |
| seeded_world_entry, 43d1937 | Core generate(seed,6), a fixed seed-1 world, movement and pause | World seed input/Create world/status and a handler replacing active state/resetting timing | 28 read replies, one list reply, one malformed read reply; no edit/check/candidate |
| world_save_copy_entry, 41367d4 | Seed creation UI and repository create/serialization APIs | Name input/Save copy/status and a guarded handler persisting the active world | Fourteen reads, one list, two searches; no edit/check/candidate |
| world_load_entry, c24e088 | Save copy UI and repository list/load APIs | Refresh saved worlds, saved-world selector, Load world/status and active-world replacement | Seventeen reads, two lists; no edit/check/candidate |

The load contract names refresh-world-list, saved-world-id, load-world and
world-load-status; none exists at its base. Save's entry has no repository import
or Storage use. Load's entry calls repository.create for saving but never load/list.
Seed's HTML has only the Pause button and canvas. Existing lower-level APIs did
not satisfy the assigned browser behavior; they were meant to be reused.

Every tracked file in each stopped workspace matches its pinned base byte for byte.
Even the rejected seed response requested files.read, not a malformed attempted edit.
Thus the no-edit finding survives this check: these were implementation stalls,
not legitimate inspections concluding that the requested behavior already worked.
The logs do not establish the model's internal reason for rereading.

### The OS imposed a byte bound, not a fixed below-31K token ceiling

The actual call path is [kernel measure](../src/polyinference/runtime/kernel.py)
→ [ContextService.prepare](../src/polyinference/runtime/context.py). The current
files are byte-identical to those frozen for the run. Kernel lines 700–714 build
the HTTP request and measure `len(canonical(prepared))`: serialized UTF-8 bytes,
including JSON framing/escaping, without a model tokenizer. Context lines 67–68
compare that byte count against the conservative allowance below.

| Calculation in this run | Value and meaning |
| --- | --- |
| Endpoint max_context_tokens | 65536, actual configured/served token window |
| Request context maximum / hard input limit | 400000 / 400000 |
| Hard output allowance | 16384 |
| Context cap | min(400000,400000,65536−16384) = **49152**, used as a conservative byte bound |
| Optional-group packing threshold | 49152−min(1024,49152//10) = **48128 bytes** |
| Actual per-call output target | 4096; kernel lines 695–696 enforce the lower target |
| Compaction target | int(49152×0.6) = **29491 bytes**, inactive because auto_compaction=false |

The extra output headroom comes from ContextService reserving the 16384 hard
allowance while the kernel actually sends max_tokens=4096. It therefore reserves
12288 more than that call's chosen output target before the byte comparison.
The conservative byte estimator then reduces effective token usage much further.
This explains underuse of a correctly configured 64K model; it is not evidence
that Strata served a smaller window. No fixed 31K-token input cap applied here.
The near-31K compaction target is not the active limit in these calls.

The generic Endpoint default of 32000 did not apply: the saved endpoint explicitly
sets 65536. The coding control_token_reserve is a run-budget reserve, not this
per-request context calculation. Actual provider prompt usage remained 4573–13839
tokens. Bytes and actual tokenizer tokens must not be presented as the same unit.

A RAM-only replay of worker-10's model-18 request through the **current** code
reproduces its original prepared digest, omission list and receipt exactly:
190900 original bytes → 42126 submitted bytes, 33719 required bytes, allowance
49152, 33 omitted parts. Whole tool groups explain why a particular request can
finish well below the 48128-byte packing threshold. No runtime/configuration,
provider or original receipt was changed by the replay.

### The error belongs to the existing compact worker-state projection

`AgentServices.memory_view()` separately exposes memory/working and memory-note
records. The confirmed problem is in
[worker_memory.project](../src/polyinference/agent/worker_memory.py), which derives
the required 8192-byte worker_state input from action history. It does not establish
corruption of canonical memory, loss of original events or a need for a memory redesign.
The current implementation hash matches the frozen run's file.

**Bug A: corrected unscoped tool calls retain path-shaped errors.** A failed
search/list with an unsupported path is keyed by that path. A schema-correct
success has no path, so lines 42–44 do not retire the old error. The required view
continues to say Resolve current error. In the live save task, turn 8 failed and
turn 9 made the valid search. Model inputs 10–16, seven subsequent submitted calls,
still carried that old error and hint inside required pinned-data. It was not
merely stale text in a final export. The seed and load tasks' error lists were
empty, so this bug cannot explain all three stalls. Causation for save's stall
is also not proven merely by the hint being present.

**Bug B: valid phase replies can retain a protocol error.** Lines 28–29 skip an
entry when observation is not a dict. `append_history` stores observation=None
for candidate/assessment/needs_review replies. That skip occurs before lines 31–32,
which are intended to clear a previous protocol error after a valid reply. Current
RAM probes reproduce stale protocol errors after all three valid non-action forms;
a valid action with a dict observation clears the same error. This is an additional
current defect, not established as a cause of this live run.

The probes validate reply shapes using WorkerReply and use no model, live records
or source writes. Unchanged replay remains idempotent in every case. Existing
test_reliability_plan coverage checks retained digest/error, source invalidation
and byte-eviction replay; it does not test these two resolution paths. Required
regressions would cover corrected search/list and valid non-action error retirement,
while preserving original history and unrelated unresolved errors. They remain
unimplemented under this task's explicit instruction.

### Correction to the earlier read-count sample

The earlier analyzer used the trajectory referenced by worker-state records. That
projection updates before model calls and can trail the final tool when progress
parks the task before another model invocation. This is expected lazy projection,
not evidence that the canonical final tool event was lost. Full effect logs have
182 ordinary local read calls, versus 178 in that projection sample. There are
88 repeated reads when comparing model arguments plus file digest (the earlier
sample had 84); retaining the host-injected generation in the comparison gives
85 exact capability-argument repeats. Diagnostic read-expansion calls are excluded.
This corrects the scope of the earlier counts without changing the no-edit verdict.

Verification: pinned-tree comparisons and all physical reply inspection for three
tasks; exact current context-packing replay; six current in-memory projection
cases and idempotent replay controls; FileRead schema checks confirming both read
argument names; original source/config/report/database/delivery preservation;
documentation generation/check and whitespace checks. No fixes, new model/browser
run, maintained test additions, commits or automatic continuation were performed.
