# Limits, steering and recovery

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

The default per-process allowance is 512 model calls, 2,048 steps and a one-hour
wall-clock deadline, with reserved reconciliation, assessment, publication and
cleanup capacity. Context reservations and the parent token allowance also limit
work. Native Codex jobs have their own deadline/event bounds; there is no
provider-enforced dollar or subscription spend cap. Optional token-priced spend
estimates can bound admission; they are not a provider billing guarantee.

> **Edited 2026-10-20 because** the in-place repository change keeps failed and
> unverifiable work out of the user's integration checkout. The old unconditional
> uncertain-publication and private-copy descriptions are superseded by the
> [recorded revisions](../../design-docs/simplified-os/DESIGN_REVISIONS.md).

The execution protocol is:

1. Setup, when enabled, handles the initial objective's prerequisites and Git/branch instructions.
2. Senior planning creates bounded tasks and assigns worker/specialist roles.
3. Each worker develops privately, integrates against the current head, reconciles,
   runs configured checks and assesses. Default in-place mode integrates only
   successful verified candidates. Failed/uncertain candidates stay private and
   close starts for review; verification is released after known effects. With
   task branches forbidden, non-successful edits remain uncommitted. Legacy
   isolated mode still publishes uncertain assessments provisionally.
4. Senior review keeps, reverts, retries or defers reports.
5. Independent final checks guard project completion.

Clean `needs_review` or sustained stagnation can instead park a settled worker
and reach senior exception review. Eligible local failures now get bounded cloud
specialist implementation, even after ordinary replacement depth is spent or a
senior defers/stops/omits them. Actual cloud coding is protected from quota demotion.
Linked replacements retain source evidence, original account/deadline and narrower
grants. Ineligible defer/stop decisions leave an unresolved completion obligation;
unknown effects and exhausted physical budgets remain blockers. See
[agent reliability](agent-reliability.md).

Steering follows the drain-before-review behavior described above. It does not
reset budgets. UI Resume and CLI `resume CONFIG [--text instructions]` record a
run-level intent. The agent clears a recoverable pause through checkpoint/model
recovery, delivery or internal senior review. All stopped workers remain accounted
for. Existing allowances, deadlines, models and completed-run immutability apply.
An exact documented predecessor graph has an explicit compatibility migration;
arbitrary configuration/graph/prompt changes still require a fresh state directory.

The OS accepts intent separately from execution readiness. It automatically settles
known host receipts and retained query responses, or retrieves a Responses result
with a surviving response ID. OS resume-preparation/ records stay separate from
application resume-progress/ and resume-outcome/. Unsupported unknown operations
produce a plain failure, not a routine user resolution workflow. Clicking Resume
never proves that unsettled work ended.

A lost HTTP/RPC connection does not prove that an external job stopped. Uncertain
native/tool/effectful operations stay recorded, retain ownership/capacity and
block runtime dispatch until reconciled. Explicitly consenting generation-only
queries can instead isolate undelivered computation with physical holds retained;
replacement still needs spare capacity. See [endpoint lifecycle policy](endpoint-testing.md). Status and inspection remain available. The runtime can reconcile verifiable host publication
receipts; it does not blindly retry remote requests. Inspect `status` and
`operation`, preserve the state, and establish the provider-side outcome before
attempting recovery. Use the explicit `reconcile --confirm-stopped --evidence`
command only after both provider work and host descendants are known to have
ended. See the [recovery procedure](../../design-docs/simplified-os/RUNBOOK.md#recovery).
Do not delete journal rows to force a retry.
