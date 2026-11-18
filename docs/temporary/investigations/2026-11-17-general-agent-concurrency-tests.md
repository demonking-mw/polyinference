# General-agent concurrency tests — 17 November 2026

Status: live testing and investigation. No production implementation changed.
Source: feature/simple-agents HEAD 3d39890, including the existing dirty working
tree. Fresh state was used for every invocation. Test artifacts and the full
report are under the Codex task's `outputs/` directory; private journals remain
in its `work/` directory. No historical invocation was resumed.

## Scope and outcomes

The requested cases ran sequentially: Research plus cloud Simple; Research plus
simulated-local Simple; two Research plus two Simple (one per binding). Research
used GPT-6.1 Sol over the ChatGPT Codex subscription for planning/reporting and
remote Haiku 5.5 for extraction. The stand-in is physically cloud inference.
Only the Research graph performed topic analysis for the authorized teacher/router
question and REA (Reverse Engineer Anything); Simple read a synthetic ledger.

| Scenario | Completed | Wall seconds | Peak Cloud holds | Peak Haiku holds |
| --- | --- | --- | --- | --- |
| 1 | 2/2 | 56.27 | 2 | 1 |
| 2 | 2/2 | 58.47 | 1 | 1 |
| 3 | 4/4 | 55.68 | 3 | 2 |

These are concurrent separate `run_v1` kernels, each with fresh state. They are
not a shared-kernel multi-graph integration. All Simple answers matched the
ledger target, and completed cases left no uncertain effects or held/waiting
inference reservations. Times include graph/OS/provider setup and shutdown.

## Admission and optimization findings

Workspace.start rejects a second active invocation. V1AgentIO pins one program
and input at fixed run-level record keys; another graph/input is rejected in
the same kernel. A second coordinator cannot own the same state directory.
Each kernel constructs its own Admission object for each binding. Observed
overlap of multiple one-slot Cloud reservations therefore establishes the lack
of cross-invocation pooling, consistent with FIX-0182 and FIX-0189, rather than
a regression in the kernel-local limit.

The separate single-kernel probe submitted two Cloud and three Haiku effects
with resident capacity explicitly raised to eight. It completed all five,
bounded active reservations to Cloud=1 and
Haiku=2, and exercised endpoint waiters.
Final active/reserved/waiting counts were zero. This proves bounded admission
for those effects, not concurrent full Research/Simple graph hosting.

Role/model selection is fixed by the application. No cost-aware model selector,
cross-kernel endpoint broker, migration or scheduler preemption was exercised.
Provider token/GPU utilization and optimal cost/latency are unmeasured. Successful
workflow overlap alone does not establish endpoint optimization.

## Failures, corrections and research limits

The first pass rejected four Research plans because at least one question
exceeded the adapter's 500-character validator (observed 538–733 characters for
REA, 602/633 for the routing task). The planning prompt states the item count but
not this character limit, and there is no graph-level correction loop. Fresh
diagnostic inputs explicitly requested questions under 150 characters. No agent
prompt or validator implementation was changed.

The first Haiku Simple effects received HTTP 401. After the user's instruction
to retry, fresh calls reading the current saved credential succeeded. The
credential value was never printed or stored in outputs. Known failures settled
their inference reservations; their paused processes retained residency.

An intermediate all-Codex local-role simulation qualified workflow shape only.
One later Haiku stress attempt lost a child before OS startup because the tester
launcher rewrote a shared corpus during child import. The launcher was corrected
to initialize the corpus before child launch, and the fresh four-job rerun above
passed. This was a harness input race, not an OS/provider failure. Intermediate
samples are diagnostic; final peaks use admitted/released journal intervals.
Settled journals were reread after shutdown to avoid transient sampling omissions.

Keyword-only lookup searches supplied documents, returns three bounded excerpts,
and can omit relevant primary documents even when they are present. Some reports
therefore flagged source gaps. Focused follow-ups use only the Research graph
with a smaller, explicitly selected corpus. Topic reports distinguish documented
behavior from proposals; no model training or REA tool/target execution occurred.

## Verification and limits

The focused general-agent/workspace/OS-monitor suite passed 27 tests. Live runs
used actual SQLite checkpoints, journals and provider calls without model mocks.
No browser UI workflow, physical local engine, GPU throughput, provider billing,
generic interrupted Resume or full repository suite was qualified. The complete
10,243-line historic fix ledger was not reviewed; onboarding, current boundary,
owning guides and related scheduler/general-agent/recent provider entries were
reviewed. The project checklist was saved and read back in the task's
`work/polyinference-content.md`, recording checkout/revision/review date.

Adjacent setup, launch, configuration, design, provider and recovery guides need
no behavior edit because implementation and settings are unchanged. The general
agent guide and runtime/provider backlog record these observed limits. The note
uses the existing investigation parent and archive graph group; primary reading
routes, colors and the fixed reading map are unchanged. Documentation generation,
validation, graph and preservation checks are recorded in FIX-0206 and the final
report with their actual results.

## Correction and live rerun — 18 November 2026

The intended topology is one kernel serving all concurrent processes in each
scenario, with scenarios running sequentially. The 17 November harness opened
multiple kernels and did not match that topology. Its overlapping cloud holds
do not motivate a cross-kernel broker for this deployment. Free endpoint choice
under fidelity is prospective and was outside the rerun.

The rerun opened one `KernelRuntime` once. All eight workflows used its SQLite
checkpoint saver, process service, journal and inference admission. The external
test harness provided unique invocation/checkpoint identities and a scope-aware
document handler. It selected the Cloud and simulated-local Simple bindings
using distinct static roles. Research reused the prior bounded prompts and
corpora. Simple used separate ledger values and markers to check corpus isolation.
The test set four resident process slots (the example normally uses two), one
GPT-6.1 Sol Cloud slot and two remote Haiku 5.5 simulated-local slots.

| Case | Completed | Wall seconds | Peak GPT holds | Peak Haiku holds | Peak resident processes |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | 2/2 | 47.74 | 1 | 1 | 2 |
| 2 | 2/2 | 43.47 | 1 | 1 | 2 |
| 3 | 4/4 | 84.35 | 1 | 2 | 4 |

Cloud queue wait peaked at 32.66 seconds. The
journal recorded 12 native GPT jobs, 12
Haiku queries and 12 lookups. All settled successfully
and the next case started only after the prior case was quiescent. All four
Simple answers matched their respective ledgers. Endpoint counts never exceeded
the slot configuration. This supports the OS admission and settlement behavior
under the tested load. The supported workspace/CLI hosting path still needs
application integration. Production implementation and the original launch
settings were not edited. Evidence is `outputs/single-kernel-rerun.json` in the
Codex task workspace. See `development-docs/FIXES.md#fix-0207`.
