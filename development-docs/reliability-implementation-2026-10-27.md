# Reliability implementation and verification — 27 October 2026

[Approved plan](run-reliability-implementation-plan-2026-10-27.md) · [Current issues](current-iter-issues.md) · [Qualification](../docs/guides/qualification.md)

The user authorized implementation after reviewing FIX-0133. The prior report's
analysis-only restriction described that original task. Work preserves HEAD
`5fe92f3` and the pre-existing uncommitted FIX-0132 tree; no old run is migrated.
The baseline archive/hashes are `/tmp/pi-reliability-implementation-start.*`.

The scoped plan is implemented, including actual cloud coding takeover, bounded
worker continuity, error-conditioned repair and OS authority/residency enforcement.
The small live gate passed with four ordinary completions plus a settled resumed
cloud-worker completion. This establishes the narrow tested workflow; broad
Minecraft convergence remains unqualified. Final framework verification follows.

## Implemented mechanisms

| Package | Implementation and ownership |
| --- | --- |
| O2/O3 | Generic registration/dispatch validates mandatory data constraints, classifications, static hard distribution and identical process/runtime limits. Unknown placement cannot satisfy local-only/cloud-only requirements; unrestricted placement accepts unspecified metadata. |
| O4 | Durable resident admissions survive paused drivers. Explicit settled hibernation releases logical residency; readmission preserves identity/accounts. Clean fenced parking performs that transition; unknown physical effects and waiting/held reservations block release. Replacement host execution also respects its inherited root deadline. |
| A1/A5 | Agent worker-state projection pins source/generation, recent file digests, unresolved errors, evidence references and next step within 8192 bytes. Existing remaining-call input now includes root operations/tokens/deadline and finishing reserves. |
| A4 | A synchronous optional owner callback conditions the existing bounded response retry on the real validation error. Required pins/role/schema/grants remain immutable and retry counts are not refilled. |
| A2/A3 | Optional behavior/focused-check contracts and declared check-source closure supplement planner guidance. Pending linked recovery consumers can be retargeted only while unstarted, preserving predecessor/root and contract; raw model plans remain distinct from host normalization. |
| Q1/A6/T1 | A fresh-state qualification corpus, command-owned real Chromium gate, source/profile manifests, independent checks, physical-attempt metrics and settled interruption/resume harness. Existing exact-tree semantic acceptance remains required. |
| O1/T2 | Removed the contradictory UI low-effort launcher override; native turn effort remains endpoint-controlled. Maintained documentation HTML/anchors and exported settings/default schema drift are checked. The legacy unchanged-source smoke explicitly uses isolated mode. |

The runtime pin is `simple-os/3`; the agent pin is
`agent-7-bounded-worker-state`, state schema `2.6`. Changed enforcement and state
semantics require fresh state. Old runs use their original source/configuration.
No general migration, automatic fan-out recovery or new browser/MCP OS API is added.

### Ownership, compatibility and limits

The OS owns data/distribution checks, uniform limits, logical residency and physical
effect/account settlement. The coding application owns behavior/check contracts,
worker facts, error meaning, cloud implementation selection and final acceptance.
Verification owns the disposable corpus and Chromium command. Provider context,
sampling and native turn settings remain explicit configuration; this work changes
no saved provider profile or model weights. New qualification configuration uses
the existing installed models on a separate owned localhost service.

Data checks enforce declared artifact classification/location/destination metadata;
they cannot certify opaque content or a provider's honesty. Static hard classes
are supported, weighted dynamic schedules are rejected and soft preferences remain
advisory. Hibernation is a settled logical transition, not GPU migration. Finishing
reserves protect calls/steps, not remote availability. Bounded state may evict facts
and require rereads; it does not turn model claims into verified memory.

Task metrics include original lineage/deadline/counters, actual backends, started
and superseded work, source deltas, identical read/check shares, dependency blockers
and bounded-state size. Full behavior counts, shell-read coverage and unrecorded wait
duration remain unavailable. The corpus adds a separately checked create/update
case; its evaluator requires a second successful edit with creation's returned
digest. Dated API-equivalent cost estimates remain separate from billing/unknowns.

Fixture policy success, one small live gate and browser-runner fixtures cannot
establish broad Minecraft convergence. Retained historical objectives and failed
source remain unchanged. No thresholds, model/quantization or original-run resource
allowances were tuned to manufacture qualification.

## Verification log

The first focused run returned 31 passes and three rejected generic fixtures
whose template destination did not name their actual binding. Those fixtures now
declare a real non-coding static contract rather than bypass policy enforcement.
A later run returned 68 passes, one remaining mismatched-role fixture and the
known 100 ms resume diagnostic baseline failure; both received focused repairs.
These intermediate results are retained, not presented as an all-green run.

The legacy baseline fixtures were made deterministic without weakening
production guards: a submitted-request event replaces startup races; resume
lookup has its own short configured timeout inside a usable original deadline;
simulated output assertions follow the 4096 configured target. Real provider and
browser qualification remain separately reported from offline fixture checks.

The full 651-case run finished with 646 passes and five compatibility failures;
all 73 affected cases passed after the fixes. No preserved run was resumed, no
receiving Minecraft source was changed, and no prior
changes are claimed as new.

Resource review reproduced a separate inherited-deadline defect: a replacement
driver waiting without a new effect outlived its root deadline. The regression
failed before the fix and passed after it; selected deadline/restart/unknown-effect
checks returned 3 passes. Hibernation checks now use the admission implementation's
actual `waiting` and `held` reservation states, with negative/release regressions.

A broader interrupted run returned 177 passes and three in-place workflow failures:
the two-worker review packet exceeded 24 KB, source evidence was omitted from a
serial review, and completed publication left a resident admission behind. Senior
instructions were compacted without increasing authority or dropping constraints.
Publication now uses OS finish atomically; returned terminal drivers also settle
resident state. The three affected workflows passed targeted reruns. A larger
two-exception transaction fixture explicitly configures a sufficient review packet,
and both CAS-conflict and post-publication restart cases pass with original account
and deadline checks. Missing check-source tests also cover multiple/retained owners.

Metrics were run against disposable copies of the two latest historical databases
and WALs, never their original runtime: 179 raw generations, 13 raw validation
failures, 25 native jobs with one additional validation failure, and 145 raw context
omissions. The initial retry-row-only projection showed 16 native jobs; FIX-0144
adds nine direct jobs without double-counting retries. Raw/native denominators stay
separate. Evidence: `/tmp/pi-reliability-historical-metrics/result-canonical-physical.json`.

### Fresh live qualification

Artifacts: `/home/marven/Projects/pi/testing/reliability-qualification-2026-10-27/`.
Qwen3.8-Flash-Next-Coder IQ1_M ran through the existing Strata installation; cloud
senior/specialist jobs used the existing gpt-6.1-sol Codex connection. Fresh copied
profiles used one worker, 32 calls and a 600000 ms original process ceiling, with
one cloud recovery. Installed weights/effort were unchanged. Each disposable task
could write only app.js; actual entry/input/pause/save/reload checks stayed fixed.

| Trial | Result | Raw generations | Native jobs | Seconds |
| --- | --- | --- | --- | --- |
| workflow-02/trial-1 | Completed; independent Chromium passed | 7 | 4 | 171.5 |
| workflow-02/trial-2 | Completed; independent Chromium passed | 8 | 4 | 196.3 |
| workflow-02/trial-3 | Completed; independent Chromium passed | 7 | 5 | 228.4 |
| workflow-02/trial-4 | Completed; independent Chromium passed | 6 | 5 | 193.2 |
| workflow-02/trial-5-resumed | Completed after settled interruption/resume; Chromium passed | 3 | 11 | 325.0 |

The fifth trial dispatched three actual specialist worker jobs, beyond cloud review.
It retained account `worker-1-persist_saved_value` and deadline
`2026-10-27T23:10:52.489398+00:00`: remaining calls 28→25, operations 121→101,
tokens 1953626→1702430 across resume. No account or deadline was renewed. All five
trials have the same execution-profile digest, unchanged framework/check pins and
zero uncertain effects. `workflow-02/results.json` records the passing gate.

Two verification defects remain visible as adverse evidence. The first `workflow/`
attempt found that inherited browser paths disappeared in the real OS tool
environment; it was aborted and its owned service drained (FIX-0142). The first
four workflow-02 trials passed product checks but missed the intended interruption
because the worker patched instead of writing. Their red gate is preserved in
`results-before-resume.json`; the corrected mutation trigger ran a fresh fifth
trial without editing any earlier source or relaxing acceptance (FIX-0143).

The original result files remain unchanged after the reporting-only native counter
fix. `corrected-physical-accounting.json` projects the table above from database
copies; three direct worker jobs and repository-policy jobs were absent from the
initial counters. Raw/provider usage and native multi-turn jobs remain distinct.
The executed source, dirty patch, dependency versions and both actual qualifier
versions are retained under `qualified-framework-*`, `dependency-versions.json`
and `workflow-02-qualifier-*.py`. Later provenance/reporting additions and the
eviction-metadata replay fix were requalified offline. All recorded live worker
views had zero byte evictions, so that replay fix leaves their input facts unchanged.

### Other observed checks

- Final offline scripted-provider gate: `/tmp/pi-reliability-qualification-fixture-07/results.json`, three completions plus settled resume passed. Source archives, exact package/profile/tool pins are retained; final provenance verification is recorded below.
- Real configured OS browser checks: valid fixture passed; bad-save and missing-export failed. Logs: `browser-os-environment-03/` under the live artifact root. This tests the actual sanitized command environment, without model calls.
- Ruff, Node syntax checks and the Node UI test file passed. Final wheel verification and exact output are recorded with the framework results below.
- Documentation generation/check passed: 317 maintained files, 137 feature/doc leaves. Exact settings/default export check passed. The only remaining length advisory is the pre-existing endpoint-testing guide.
- All 20 selected historical database/WAL hashes still match the pre-task preservation record. The original FIX history bodies are preserved. Final preservation/whitespace checks repeat after verification completes.

The next full run was stopped after 219 passes with no failures because a valid
deep-path replay probe exposed eviction counts resetting 9→0. FIX-0145 preserves
those counts within one source/generation; the regression failed before and both
focused ledger checks passed afterward. The final full suite restarts on that
exact corrected source. No live view in the five recorded trials had byte eviction.

### Complete framework run and final compatibility follow-up

The complete run took 1869.20 seconds: 646 passed, five failed, no skips.
JUnit: `/tmp/pi-reliability-full-suite-final4.xml`. Its remaining failures were:
the endpoint probe guessed location from a URL; one backoff fixture changed limits
after registration; one UI export assertion expected simple-os/2; two brief-delivery
variants required the old literal prompt prefix. The actual brief delivery,
exported behavior and fixed runtime enforcement remained covered by the assertions.

FIX-0146 makes probe allocation protocol-based while preserving the run-wide data
ceiling. Positive unknown/local/cloud metadata and constrained fail-closed cases
are included in its rerun. The one-call retry envelope is declared before opening
the runtime; the UI expects the new pin and brief tests require the equivalent
EVERY-invocation/user_brief instruction plus actual delivered notifications.
These final changes are isolated call-site/fixture compatibility fixes. All affected
lifecycle, retry and brief modules and related UI probe/export cases passed:
**73 passed in 79.24 seconds**, JUnit `/tmp/pi-reliability-affected-final.xml`.
The five parameterized probe cases replace the original single case, bringing
the current inventory to 655. A test-ID comparison confirms all 655 current cases
have passing results across the full run and affected rerun, with none missing:
`/tmp/pi-reliability-final-case-coverage.json`. This is not a single all-green full
run on the final tree; the full suite was not repeated after the isolated fixes.

### Final handoff checks

- Ruff passed for src, tests and the changed tooling scripts; Node syntax and the Node UI test file passed.
- Wheel build passed. All 73 packaged Python/JS/HTML files match the final workspace bytes. Artifact: `/tmp/pi-reliability-wheels-final4/polyinference-0.1.0-py3-none-any.whl`, SHA256 `4e6a0748e34e7ee35c249b4dcd267fc8d234975b5772d6ce9a8ef73df204a1fa`.
- Documentation generation/check passed at 317 maintained files/137 leaves; settings schemas/defaults and git whitespace checks passed. The endpoint-testing guide's existing length advisory remains advisory.
- Source archives for all four final offline trials contain 76 files each, all matching their manifest hashes. No live models were rerun merely for reporting/provenance or isolated probe compatibility changes.
- Final historical database/WAL and original FIX-body preservation checks passed. Project HEAD remains `5fe92f3e2122dbb19e12d3152644a32f2979f40b`; no project commit/push, old-run resume or runtime setting rewrite occurred.
- Both owned Strata service instances drained and stopped. Qualification projects, failed evidence, private deltas and all original accounting remain retained.
- Retained project knowledge was refreshed and read back in the checkout's `AGENTS.md`; it installs no hooks or automation.

## Documentation maintenance

Owning kernel/process, worker/controller, retry/port, settings/check/qualification
and tooling guides describe the new interfaces and limits. Current design gaps
are marked resolved only for the implemented static profile, retaining their
historical symptoms and links. Setup/onboarding/project memory, configuration,
navigation and FIX history must agree before completion. Provider authentication,
workspace source authority, physical unknown-effect accounting and the agent/OS
ownership boundary remain enforced; adjacent guides are reviewed for consistency.

Credential/login, provider installation, Git export/conflict and underlying budget
guides were reviewed without edits: their authentication, installation, source
handoff and accounting contracts are unchanged. Existing endpoint-testing edits
were preserved; its length advisory is not a new guide rewrite. Current-iteration
status and the historical plan's follow-up link distinguish implemented mechanisms
from the earlier report's proposed state. No project commit or push is performed.
