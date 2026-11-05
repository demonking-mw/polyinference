# Model availability and existing browser repairs — 2026-10-28

[Current issues](current-iter-issues.md) · [Failure analysis](minecraft-failure-isolation-2026-10-28.md) · [Fallback policy](../docs/guides/model-fallback.md)

The user authorized an OS alternate-model retry and repairs to existing tests and
missed browser behavior, with no new gameplay. Earlier analysis-only restrictions
remain historical; convergence, context sizing and worker-memory fixes below are
**plans only**. No old run was resumed, model/config pins changed or account refilled.

The plan below records this earlier batch. The later authorized [scheduled four-repair
implementation](four-repairs-implementation-2026-10-28.md) supersedes its plan-only status;
the original evidence and routing policy remain intact.

## Four-area plan and ownership

| Area | Agent implementation plan | OS implementation plan | Current status |
| --- | --- | --- | --- |
| Local convergence | Keep each task to one missing behavior and meaningful check; explicitly distinguish already-complete behavior from required edits. Give stalled workers the failing entry/test and read capability; escalate repeated identical reads without evidence novelty. All three investigated tasks did need UI edits. | Preserve factual effects, limits and progress; do not require an edit or define semantic completion. | Planned, no policy/prompt changes here. |
| Underused context | Rank current failing source/test, objective and compact facts before repeated history; tune only on fresh comparable trials. | Measure prepared input in tokenizer units where supported; retain honest byte/estimate fallback. Separate input capacity, actual enforced output reserve and prepared bytes; never remove hard bounds. | Planned. The observed cap was 49152 UTF-8 bytes, not 31K tokens; max actual prompt was 13839 tokens. |
| Recovery | Own semantic continuation, scoped private-source reuse, diagnosis and acceptance. Choose alternate model through agent configuration. | Durable availability routing and trusted same-thread native continuation, original authority/accounts/deadline and tool receipt replay. | Availability path implemented; broader semantic recovery unchanged. |
| Memory defect | Retire the old path-specific search error after a corrected successful call; process valid non-action replies before the observation=None early return. Add corrected-search, protocol-clear and replay regressions. | Continue immutable evidence storage; no canonical-memory rewrite or new memory architecture. | Planned; worker_state projection remains unchanged. |

## Implemented model routing

The generic OS exposes Endpoint.retry_model, absent by default. AgentConfig
default_retry_model selects `gpt-6.1-terra`/`high`/7 for native Codex cloud endpoints.
Explicit agent input overrides OS defaults; explicit endpoint configuration wins
over the agent default. Null opt-outs persist on save/reload. Generic OS code has
no model identity or coding-task assumptions; see the linked configuration guide.

Terminal provider availability failure → retry the same logical request once on
the alternate, then seven subsequent alternate invocations and a primary probe.
This is the user's latest sequence, superseding the earlier immediate primary probe.
Seven is the OS default, overridable by agent input; primary model/effort stay pinned.
Count logical invocations, not tasks or physical subattempts.
Selections/window counters persist per binding; replay and older concurrent
primary results cannot corrupt the latest state. Ordinary retry failures route
immediately when availability is discovered, preserving output-adaptation feedback.
Alternate failure does not recurse.

Native post-tool failure continues the same app-server thread on the alternate,
using persisted tools/results and unchanged grants. Repeated old callback IDs
replay receipts; changed arguments reject. Trusted terminal evidence is required;
unknown effects still block. All extra calls share original admission, resource
accounts, finishing reserves and logical deadline. Opaque provider fallback is
disabled on start. Runtime simple-os/4 requires fresh state; agent-7/state 2.6 stay.

Official [app-server guidance](https://learn.chatgpt.com/docs/app-server) and the
installed experimental schema support model override on thread/resume with restored
dynamic tools. [Terra documentation](https://developers.openai.com/api/docs/models/gpt-6.1-terra)
supports high effort. No live provider outage or subscription retry was exercised.

## Existing game/test repair

The kept game already had separate window blur, fresh timing baselines and valid
assertions; these were rechecked rather than reimplemented. Document-level keydown
was still interpreting movement/Escape from editable fields, and focusing an input
left held movement active. The entry now ignores editing targets and clears held
movement on focusin. No loading, gravity, jumping or other gameplay feature was added.
Two regressions failed before repair; all 46 Node tests pass after it.

The retained finite `tests/browser-real.mjs` launches actual Chromium and its own
temporary loopback server. Eight passing checks cover seed creation, movement/key
release, real input isolation, focus clearing, explicit window blur, pause/fresh
resume timing, save bytes after reload and quota failure preserving bytes. No page
errors. Native OS focus switching, browser loading and complete saved play are not
certified. Initial runner root-path errors were harness errors, corrected before
these results. Framework qualification's simpler increment fixture remains distinct.

## Verification and preservation

Evidence and before-change source archives are under
`../testing/fallback-browser-fixes-2026-10-28/` relative to the checkout root.
Final fallback coverage passes 27 fixture cases; the earlier focused runtime run
passed 88. Broad run: 679 passed/two Node-tool skips, with separate exact source pins.
Both skipped cases pass with the installed Node 24/npm. The final physical
response-repair payload refinement is covered by the 27-case run. No single fresh
682-case full rerun is claimed. Final checks and hashes are retained there.
No live inference, historical Resume, commits, pushes or new automation.
Framework/target edits stay uncommitted; target remains unborn pi-dev.
Setup/authentication and endpoint lifecycle guides were reviewed: existing signed-in
auth, provider protocol, admission and execution-backend setup need no new steps.
Onboarding, project memory, settings/boundary/module guides and navigation are updated;
AGENTS retains the reviewed ownership/safety rules. Earlier reports remain unchanged.
