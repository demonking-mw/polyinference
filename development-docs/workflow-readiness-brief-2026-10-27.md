# PolyInference workflow readiness — management brief

27 October 2026 · `codex/simple-os-v1` at `5fe92f3` · About seven minutes to read aloud

Follow-up: [authorized granularity/cloud recovery change](local-task-granularity-and-cloud-recovery-2026-10-27.md)
implements application recovery policy in the uncommitted working tree. This brief
retains the original source/run assessment; fresh live qualification remains required.

**PolyInference has not demonstrated reliable completion of unattended, long-running coding
projects.** The Minecraft runs reviewed from 24, 25 and 26 October all stopped before an accepted
playable application. Some individual tasks completed, including storage and documentation. That is
useful progress, but it does not meet the purpose of the workflow. The wider claim that no
long-running job has ever completed comes from the user's operational experience; this review
establishes the pattern in those saved runs rather than auditing every historical project.

The current branch contains the merged reliability fixes: safer bounded retries, preserved source
and resource accounts, review of clean worker failures, stagnation detection and source-backed
completion checks. The latest run used the requested Qwen3.8-Flash-Next-Coder IQ1_M through Strata
at 64K context and batch one, with native Codex planning and specialist work. Authentication and
generation worked. No additional runtime implementation was changed during that test or this review.
Current new changes are documentation; the game remains uncommitted for review.

The latest test had two distinct failure stages. The first two configurations stopped because
required native review input exceeded the configured input ceiling. Correcting the native ceiling
allowed the third attempt to proceed. That attempt then stopped because physics and menu workers
stalled, each used its one permitted linked recovery, and no runnable work remained. It exited with
code two. A persistent provider outage, GPU out-of-memory error or exhausted total call allowance
was not the recorded final cause. Raising a timeout would not address that stopping condition.

The output evidence is decisive. Across the two development attempts there were 179 local
generations and 13 schema-validation failures. The three physics attempts left no net source change.
Menu recovery retained the same broken three-file delta. A real browser probe could not import the
shell's required mount function, and the delivered browser still mixed incompatible coordinate
systems. Twenty-five unit tests passed, covering core and storage, while the application remained
unplayable. The completed storage milestone came through native specialist recovery after a local
stall.

The word “stall” has a specific meaning here. The agent counts consecutive settled decisions without
new evidence. A new source tree, phase, file listing, previously unread file range or check outcome
can reset that counter. Repeated reads of the same bytes, repeated checks on unchanged code,
narration and model activity cannot. At eight idle decisions it warns; at twelve it parks the worker
and preserves its work. This is not a twelve-second timer and does not kill an active generation.
New evidence can still be irrelevant or incorrect, so this guard detects repetition, not useful
completion. It can stop a loop correctly without supplying a way to finish the task.

The responsibility split matters. The agent includes the model and the Python coding controller: it
owns task size, dependencies, role allocation, useful memory, grammar, repair strategy and product
acceptance. The OS owns generic execution, permissions, durable observations, context packing,
resource accounting and safe retry mechanics. Strata or the provider owns actual generation and GPU
scheduling. The OS cannot infer which feature to implement next or which old observation is
essential to the task.

Context is a likely contributor. The server offered 65,536 tokens, but the agent's local admission
limit was 49,152 UTF-8 bytes under conservative accounting. In 145 of 179 local result receipts,
optional history had been omitted. Originals were saved, but saved history is not the same as
information available to the next model call. The agent already pins instructions, contracts and
shared memory; it lacks a clearly bounded, automatically maintained worker ledger of completed work,
current digests, unresolved errors and the next verified step. Re-reading, growing history and
omission may reinforce each other. This is a supported hypothesis, not an isolated root cause.

Task decomposition and recovery also need work. Earlier plans already used modules; the latest tasks
are not consistently smaller. Physics combined movement, collision, fall damage, save compatibility
and migration across five files. One recovery normally rephrased the same substantial assignment.
The cloud-resolution fixes did survive the merge: all four final-attempt stalls reached cloud
senior review. Cloud review is read-only; it does not itself implement a repair. The senior proposed
local workers for both replacements, and the allocator retained those roles. The ten-percent quota
does not guarantee a cloud repair, but no proposed cloud role was overwritten in those cases.

The separate checking agent was configured for cloud, yet no checking-agent diagnosis ran in the
two development attempts. Automatic stagnation parks directly for senior review, bypassing that
diagnostic trigger. This route already existed before the merge. The gap is between cloud review
and effective corrective execution, rather than a removed cloud handoff. Automatic format retries
did help: nine of eleven unchanged-payload follow-ups became schema-valid, without establishing
task progress.

Output limits require a different response from stagnation. The OS detects confirmed generation
cutoffs, retains evidence, discards incomplete actions and may request a smaller complete response
within bounds. The agent must choose smaller edits and maintain task continuity. Malformed JSON
below the output ceiling is a format failure, not proof of truncation. A disconnect with unknown
execution is different again: the OS preserves ownership until it can establish what happened,
preventing duplicate work.

**The next milestone should be repeatable completion of a small integrated workflow.** First qualify
the local backend on short, concrete coding and tool tasks. Then add a bounded worker task ledger,
smaller observable deliverables, and recovery that chooses a demonstrably changed approach. Give
exceptional specialist routing an explicit, accounted policy. Require real DOM and browser checks
early, before a large dependency chain accumulates. Keep permissions, provenance and
unknown-execution safeguards.

Management should require three consecutive small end-to-end runs and an interrupted run that
resumes correctly, without manual source repair, before another broad game trial. This is an initial
engineering gate, not a statistical reliability claim. Record accepted features, actual application
behavior, retained progress, elapsed cost and exit causes. Larger budgets, more workers or a
different quantization should be tested as controlled changes after that baseline, not assumed to
solve the workflow.

[Engineering analysis, exact rules, ownership and proposed work](workflow-readiness-analysis-2026-10-27.md).
