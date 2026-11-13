# Haiku timeout follow-ups

<a id="run14-findings"></a>
## Run 7086c575ef94 findings — 2026-10-21

Status: investigated; follow-ups open, no implementation changed.
Evidence and limits (`docs/temporary/investigations/2026-10-21-run-7086c575ef94.md`) · `development-docs/FIXES.md#fix-0100`.

- OS/adapter diagnostics: a submitted Haiku call became uncertain after 180.005
  seconds with a 180-second timeout. Preserve timeout origin and chained transport/
  cancellation facts so these causes are distinguishable. The actual trigger is
  strongly consistent with timeout but not conclusively retained. Keep unknown
  execution out of blind retry; timeout tuning alone does not reconcile this call.
- Transport/deadline follow-up (2026-10-23): the official Anthropic guidance and
  source probes (`docs/temporary/investigations/2026-10-21-run-7086c575ef94.md`)
  establish non-streaming large-output requests plus a UI-selected 180-second
  whole-generation limit. Implement internal SSE accumulation and distinguish
  inactivity from total deadlines; SSE alone leaves the kernel cutoff intact.
  Retain typed cause/request/progress diagnostics and explicit durable retry
  accounting. This is an open integration repair, not an implemented change or
  proof that every earlier pause had the same cause.
- Coding planning: one preparation owner received four top-level tests while its
  required runner demanded four different tests/acceptance paths. Check exact
  mandatory-path ownership/grants before dispatch without weakening assertions.
  FIX-0088's owner/dependency validation does not validate this single-owner case.
  The next plan corrected the grant and used an explicit retained-source handoff;
  that handoff worked, but the replacement paused before writing or verification.

Only setup reached pi-dev. Direct 36/36 foundation tests are historical private
worktree evidence; no development contribution or final product was accepted.
This is not a reproduced OS deadlock, context overflow or simulation fault.
