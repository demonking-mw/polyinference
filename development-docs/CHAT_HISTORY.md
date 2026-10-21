# Past chat audit and fix-history sources

Reviewed on 2026-10-19 (America/Toronto). This is a provenance/coverage companion
to [FIXES.md](FIXES.md), not a second implementation backlog or a raw transcript
archive. It records what was inspected and what must not be mistaken for a fix.

## Scope and evidence rules

- Reviewed **20 prior chats, 85 retained turns**, associated with the repository
  path or its local project. Both older-turn pages were read for the two chats
  with pagination; all returned per-chat cursors were exhausted.
- The supported recent-thread inventory returned 50 non-pinned chats plus pinned
  chats. The archived Codex inventory returned four unrelated chats and no further
  cursor. This audit covers the relevant chats accessible through those listings;
  it does not claim access to deleted chats, unlisted older chats, or every chat
  in a separate cloud project/account.
- Titles below reproduce the app's source titles. Chat IDs permit retrieval even
  if sidebar placement changes. Dates are Toronto dates of retained turns.
- Used user requests, completed assistant reports, visible change/command records,
  and repository documents/source for corroboration. Quoted test counts are
  **historical reports**, not tests rerun while backfilling. A chat's task request
  alone is not evidence that it was implemented.
- Interrupted turns, plans, pure inspection, research, and unverified limits stay
  distinct. No credentials, full prompts, private output dumps, or transient quota
  values are reproduced here.
- The current chat (`01a15743-81b6-7b10-a26f-4f44cc1e70e7`) already supplied
  FIX-0001 through FIX-0004 and now FIX-0042. It is not counted among the 20 prior
  chats or 85 turns.

## Reading the recurrence

The earlier missing-folder relaxation is [FIX-0017](FIXES.md#fix-0017), implemented
in the legacy private-copy path. [FIX-0040](FIXES.md#fix-0040) later made the user's
actual repository authoritative and introduced a different repository provider.
Its enclosing-root rejection exposed a gap in startup coverage.
[FIX-0001](FIXES.md#fix-0001) fixes that later trigger and tests nested projects.
Thus the earlier request to relax startup is confirmed; the exact earlier fix
was narrower than the latest nested-directory failure. Check both providers when
changing startup semantics and preserve this invariant across layout migrations.

## Open or only partly resolved findings

These are findings from the reviewed records, not newly implemented fixes:

| Finding | Historical evidence and current limit |
| --- | --- |
| Prerequisites versus final product acceptance | CHAT-12 explicitly deferred report item 3. Passing Node/npm/ignore checks does not establish a game exists. The present immutable check selection must not be described as comprehensive product-acceptance layering. |
| Started-then-cancelled task accounting | CHAT-12 deferred report item 8/OSAG-07; CHAT-16 again observed four starts but only three counted. No reviewed implementation establishes the correction. |
| Fault-scope-aware circuits | CHAT-13's generalization audit found request-specific failures grouped as endpoint failures. Generic capability separation does not by itself implement the broader taxonomy. |
| Persistent process tool state | CHAT-13 fixed source-contaminating caches, then observed fresh HOME per command loses cross-command configuration. Process-owned lifetime/quotas remain separate from disposable scratch. |
| Protocol errors, no-progress escalation, and staffing overrides | CHAT-16 found malformed replies/output-limit waste and no deliberate senior escalation for repeatedly failing tasks. Bounded token-cutoff recovery and the 10% staffing ratio do not establish a complete protocol/escalation strategy. |
| Exact path closure and current blocker reporting | CHAT-16 found omitted index.html, literal directory-path selection, and a stale top-level blocker. Full in-place worktrees address the main default-layout missing-file trigger, but no reviewed change establishes general directory expansion semantics or a complete blocker-lifecycle fix. |
| Test wiring and playable product | CHAT-16 found the final engine/tests unverified, the runner still selecting world tests, and a failing isolated landing assertion. No implemented stack change proves the captured product became playable. |
| Account quota exposure | CHAT-18 researched rate-limit read/update interfaces only. No account-quota UI or scheduling feature was implemented there. |
| MCP/research-agent platform and shutdown recovery | Explicitly outside the reviewed implementation scope. General-agent fixtures establish generic mechanisms, not a new agent product, MCP stack, or expanded shutdown recovery. |

Some later changes address portions of these findings: in-place worktrees,
private-candidate handoff, and dependency preparation are recorded in FIX-0040;
preparation-error recovery is FIX-0003. Do not mark the rest complete by association.

## Source chats

<a id="chat-01"></a>

### CHAT-01 — Refine polyinference agent graph

- Chat ID: `01a142a9-aa88-7863-b99e-1688e1f53527` (local).
- Retained turns reviewed: 6; dates: 2026-10-15, 2026-10-16; no unread returned pages.
- Fix-history coverage: [FIX-0005](FIXES.md#fix-0005).

Design/editor revisions only. The user's edited full architecture was preserved while derived views, memory-view editing, and label behavior changed. No runtime was built here.

<a id="chat-02"></a>

### CHAT-02 — Connect LangGraph to ChatGPT

- Chat ID: `01a14794-8a43-7e02-a212-20d5f47c7e23` (local).
- Retained turns reviewed: 5; dates: 2026-10-16; no unread returned pages.
- Fix-history coverage: [FIX-0009](FIXES.md#fix-0009).

Research plus `references/codex-agent-proxy-brief.md`. No third-party proxy was installed or tested in this chat. Recommendations and external product claims are historical, not current advice.

<a id="chat-03"></a>

### CHAT-03 — Design OS-independent LangGraph

- Chat ID: `01a14a59-019a-7e11-9fd9-618086b84eaf` (local).
- Retained turns reviewed: 4; dates: 2026-10-17; no unread returned pages.
- Fix-history coverage: [FIX-0007](FIXES.md#fix-0007).

Portable agent/OS designs and contract validators. The merged graph explicitly superseded an earlier proposal for failed-work publication. Contract checks were not runtime tests.

<a id="chat-04"></a>

### CHAT-04 — Merge agent graph designs

- Chat ID: `01a14a76-68ff-7c52-a7ba-eafb252f2246` (local).
- Retained turns reviewed: 1; dates: 2026-10-17; no unread returned pages.
- Fix-history coverage: [FIX-0006](FIXES.md#fix-0006).

Merged graph artifact with preserved user layout and memory model. The original output was a visualization artifact; repository merge notes and mirrored HTML/JSON corroborate the result.

<a id="chat-05"></a>

### CHAT-05 — Audit OS and agent designs

- Chat ID: `01a14aa5-b078-75c3-816f-abfb60269f48` (local).
- Retained turns reviewed: 4; dates: 2026-10-17; no unread returned pages.
- Fix-history coverage: [FIX-0007](FIXES.md#fix-0007), [FIX-0008](FIXES.md#fix-0008).

Joint design audit and interactive readers, followed by bilingual content and removal of duplicated Chinese Python files. Runtime fixes were not claimed.

<a id="chat-06"></a>

### CHAT-06 — Build LangGraph agent

- Chat ID: `01a14b3c-a7c6-7220-81f8-c9e055007cea` (local).
- Retained turns reviewed: 15; dates: 2026-10-17; no unread returned pages.
- Fix-history coverage: [FIX-0009](FIXES.md#fix-0009), [FIX-0010](FIXES.md#fix-0010), [FIX-0011](FIXES.md#fix-0011), [FIX-0012](FIXES.md#fix-0012), [FIX-0015](FIXES.md#fix-0015).

Initial executable agent/provider work, test UI, project/export/cost/steering controls, worker routing/budget correction, first cloud setup/tool parity, role allocation, and setup documentation. Both available pages were read; operational launch/stop replies were not treated as separate code fixes.

<a id="chat-07"></a>

### CHAT-07 — Configure OS models

- Chat ID: `01a14c36-482e-74e3-a1be-e91fa1669070` (local).
- Retained turns reviewed: 5; dates: 2026-10-17; no unread returned pages.
- Fix-history coverage: [FIX-0011](FIXES.md#fix-0011), [FIX-0013](FIXES.md#fix-0013), [FIX-0014](FIXES.md#fix-0014).

Mixed provider configuration, automatic external credential loading, comprehensive OS viewer/save data, and the requested medium-to-low reasoning setting. No key value was copied into this audit.

<a id="chat-08"></a>

### CHAT-08 — Add rolling runtime history

- Chat ID: `01a14fda-495a-7d83-b4da-9c0a06d5d950` (local).
- Retained turns reviewed: 6; dates: 2026-10-18; no unread returned pages.
- Fix-history coverage: [FIX-0015](FIXES.md#fix-0015), [FIX-0016](FIXES.md#fix-0016), [FIX-0017](FIXES.md#fix-0017), [FIX-0018](FIXES.md#fix-0018).

Rolling archive, generated-history ignore rules, relaxed missing-folder startup, and visible/exportable startup failures. The interrupted first archive request was not counted as another implemented feature.

<a id="chat-09"></a>

### CHAT-09 — Inspect frontend save data

- Chat ID: `01a14fde-f6c8-7891-9b08-32f08bc69aac` (local).
- Retained turns reviewed: 1; dates: 2026-10-18; no unread returned pages.
- Fix-history coverage: [FIX-0014](FIXES.md#fix-0014).

Inspection only: described Save's retained data, no-redaction behavior, capture consistency limits, and inability to restore private Git from JSON. No implementation change.

<a id="chat-10"></a>

### CHAT-10 — Show core UI task events

- Chat ID: `01a14ffc-b293-7283-bbb1-6dab5fae03c4` (local).
- Retained turns reviewed: 1; dates: 2026-10-18; no unread returned pages.
- Fix-history coverage: [FIX-0020](FIXES.md#fix-0020).

Small terminal projection of core lifecycle events. Subsequent reporting hardening is linked separately.

<a id="chat-11"></a>

### CHAT-11 — Improve testing context inference

- Chat ID: `01a15145-640f-7d72-a6d3-748c4476b548` (local).
- Retained turns reviewed: 1; dates: 2026-10-18; no unread returned pages.
- Fix-history coverage: [FIX-0019](FIXES.md#fix-0019).

Made check input optional and delegated meaningful check discovery to setup; omitted checks cannot justify success.

<a id="chat-12"></a>

### CHAT-12 — Diagnose 2D Minecraft run

- Chat ID: `01a15196-5534-7c02-8c15-16008382cb7d` (local).
- Retained turns reviewed: 6; dates: 2026-10-18, 2026-10-19; no unread returned pages.
- Fix-history coverage: [FIX-0021](FIXES.md#fix-0021), [FIX-0022](FIXES.md#fix-0022), [FIX-0023](FIXES.md#fix-0023), [FIX-0024](FIXES.md#fix-0024), [FIX-0025](FIXES.md#fix-0025), [FIX-0026](FIXES.md#fix-0026), [FIX-0027](FIXES.md#fix-0027), [FIX-0041](FIXES.md#fix-0041).

Investigated the absent Minecraft product and then implemented the user's selected issue items, output delivery, and basic non-coding process support. Final-acceptance layering and historical-start accounting were explicitly deferred.

<a id="chat-13"></a>

### CHAT-13 — Explain why the process failed

- Chat ID: `01a15157-6226-7ec0-a460-b07c22883b44` (local).
- Retained turns reviewed: 13; dates: 2026-10-18, 2026-10-19; no unread returned pages.
- Fix-history coverage: [FIX-0023](FIXES.md#fix-0023), [FIX-0024](FIXES.md#fix-0024), [FIX-0025](FIXES.md#fix-0025), [FIX-0026](FIXES.md#fix-0026), [FIX-0027](FIXES.md#fix-0027), [FIX-0028](FIXES.md#fix-0028), [FIX-0029](FIXES.md#fix-0029), [FIX-0030](FIXES.md#fix-0030), [FIX-0031](FIXES.md#fix-0031), [FIX-0032](FIXES.md#fix-0032), [FIX-0033](FIXES.md#fix-0033), [FIX-0041](FIXES.md#fix-0041).

Thirteen turns across both available pages: phase-framing/diagnostic investigation, native-event/reporting fixes, output-limit recovery, tool-home isolation, long-note diagnosis, generalization audit, and implemented capability/lifecycle separation. Initial verification restrictions were later superseded by recorded Linux runs.

<a id="chat-14"></a>

### CHAT-14 — Diagnose early agent pause

- Chat ID: `01a154cb-dd9d-7441-be8f-5e1d544cba63` (local).
- Retained turns reviewed: 3; dates: 2026-10-19; no unread returned pages.
- Fix-history coverage: [FIX-0034](FIXES.md#fix-0034), [FIX-0035](FIXES.md#fix-0035), [FIX-0036](FIXES.md#fix-0036).

Separated ordinary generated build output from source, preserved dependencies, and implemented native permission/tamper checks after an actual early pause. Analysis and proposal turns preceded the implementation.

<a id="chat-15"></a>

### CHAT-15 — Locate the UI task queue

- Chat ID: `01a154f7-2a4e-7d81-86b9-3d8b5b066eeb` (local).
- Retained turns reviewed: 4; dates: 2026-10-19; no unread returned pages.
- Fix-history coverage: [FIX-0037](FIXES.md#fix-0037).

Inspected missing task-lifecycle UI, proposed the OS/Agents layout, then implemented it. Layout proposals are not additional runtime changes.

<a id="chat-16"></a>

### CHAT-16 — Analyze latest run

- Chat ID: `01a15524-ea89-7f42-b927-b0c9a4149408` (local).
- Retained turns reviewed: 6; dates: 2026-10-19; no unread returned pages.
- Fix-history coverage: [FIX-0040](FIXES.md#fix-0040), [FIX-0041](FIXES.md#fix-0041).

Analyzed the interrupted run without implementing shutdown recovery, confirmed private writes/commits, proposed in-place work, then implemented that plan. The last empty interrupted turn is not evidence of another completed fix.

<a id="chat-17"></a>

### CHAT-17 — Add sprint updates and agent output

- Chat ID: `01a156d0-37a8-7253-8255-7314249dd97e` (local).
- Retained turns reviewed: 1; dates: 2026-10-19; no unread returned pages.
- Fix-history coverage: [FIX-0038](FIXES.md#fix-0038), [FIX-0039](FIXES.md#fix-0039).

Kept sprint briefs in the coding agent and generic user.notify in the OS. Focused tests and a last-failed rerun were green; an earlier complete-suite command failed, so this audit does not invent an all-green full-suite result for this chat.

<a id="chat-18"></a>

### CHAT-18 — Expose Codex usage stats

- Chat ID: `01a154fd-fdc1-7683-8241-0c19c4b1ba28` (local).
- Retained turns reviewed: 1; dates: 2026-10-19; no unread returned pages.
- Fix-history coverage: [FIX-0041](FIXES.md#fix-0041).

Research/inspection only: found an account rate-limit RPC and update notification, tested a read without inference, and proposed exposure. No project files changed. Account quota display/scheduler integration was not implemented, and historical percentages are not current quota.

<a id="chat-19"></a>

### CHAT-19 — Find open-source computer use models

- Chat ID: `01a15148-33a4-76c2-be9d-e7f42b43ce2e` (local).
- Retained turns reviewed: 1; dates: 2026-10-18; no unread returned pages.
- Fix-history coverage: no repository implementation fix claimed.

Model-comparison research only. No repository fix or model deployment is established. External rankings/specifications were not refreshed for this documentation task.

<a id="chat-20"></a>

### CHAT-20 — Set up Qwen3.6-35B inference

- Chat ID: `01a14229-5be6-7300-8a29-c7a6ba0b46dc` (local).
- Retained turns reviewed: 1; dates: 2026-10-15; no unread returned pages.
- Fix-history coverage: no repository implementation fix claimed.

Native Windows inference setup outside this repository. The chat reports a model checksum/loading check and launch command, with no generation requested. It is not a PolyInference runtime integration or an implemented OS inference scheduler.

## Repository corroboration

The chat audit was cross-read against [current iteration issues](current-iter-issues.md),
[the run analysis](run-analysis-8e83ed155ae2.md),
[the workspace/native-boundary investigation](workspace-output-and-native-boundary.md),
[the in-place implementation plan](in-place-repository-plan.md),
[the current runtime boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md),
[the design integration audit](../design-docs/INTEGRATION_AUDIT.md), and
[the merge provenance](../design-docs/polyinference-design/merged-agent-design-notes.md).
Relevant source and regression files were checked for the recorded mechanisms;
no application behavior was changed and no historical suite was rerun.
