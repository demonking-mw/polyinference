# Development records

[Developer onboarding](../dev-readme.md) · [Documentation](../docs/README.md) · [File tree](../docs/file-tree.html)

Read [FIXES.md](FIXES.md) before repository work and update it before handing off.
After every fix/feature, update all affected module, setup, usage, settings,
design and issue docs in the same change; follow [maintenance](../docs/maintenance.md).

| Need | Record |
| --- | --- |
| Current four-repair implementation and verification | [28 October scheduled batch](four-repairs-implementation-2026-10-28.md) |
| Committed model fallback/browser repair and original four-area plan | [28 October implementation](model-fallback-browser-repair-2026-10-28.md) |
| Authorized reliability implementation and checks | [27 October implementation record](reliability-implementation-2026-10-27.md) |
| Latest broad real-local product test | [27/28 October Minecraft result and limits](minecraft-live-test-2026-10-28.md) |
| Causes and proposed repairs for that test | [28 October failure isolation](minecraft-failure-isolation-2026-10-28.md) |
| Highest-priority current fix | [Local task granularity and cloud recovery](local-task-granularity-and-cloud-recovery-2026-10-27.md) |
| Proposed implementation sequence and past-failure coverage | [Run reliability plan](run-reliability-implementation-plan-2026-10-27.md) — report only; no fixes implemented by this plan |
| Durable fixes and design principles | [Fix history](FIXES.md) |
| Work/defects for this version | [Current iteration](current-iter-issues.md) |
| Next-stage features | [Next iteration](next-iteration.md) |
| Learn to train an agent/settings router | [HTML learning guide](router-training-guide.html), [Markdown walkthrough](router-distillation-tutorial.md) |
| Questions awaiting triage | [General issues](general-issues.md) |
| Past-run evidence and audits | [Investigations](investigations.md) |
| Documentation compliance and workflow trend | [27 October audit](documentation-and-reliability-audit-2026-10-27.md) |
| Detailed workflow-readiness review (separate work) | [Management brief](workflow-readiness-brief-2026-10-27.md), [engineering analysis](workflow-readiness-analysis-2026-10-27.md) |
| Proposals and historical handoffs | [Planning archive](proposals.md) |
| Source chats used for historical backfill | [Chat audit](CHAT_HISTORY.md) |

Current behavior is defined by the [runtime boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md),
[accepted revisions/open gaps](../design-docs/simplified-os/DESIGN_REVISIONS.md)
and [module guides](../docs/modules/README.md). Investigation/proposal status must
not be mistaken for implemented behavior. Preserve older entries and stable IDs;
mark corrections/supersession explicitly. Long append-only evidence remains at
its original paths; use these short indexes to choose what to read.

[2026-10-26 reliability/simple OS compatibility audit](branch-integration-audit-2026-10-26.md) records the merge conflicts, owning layers and integration decisions.

[2026-10-26 local Strata live test](local-strata-live-test-2026-10-26.md) records real
Qwen setup, mixed-lane context limits, bounded recovery and product-check limits.

[Workflow readiness meeting brief](workflow-readiness-brief-2026-10-27.md) and
[engineering analysis](workflow-readiness-analysis-2026-10-27.md) explain completion
failures, stopping rules, agent/OS responsibilities and proposed qualification gates.
