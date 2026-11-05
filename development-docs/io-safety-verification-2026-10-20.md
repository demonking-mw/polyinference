# I/O safety implementation verification — 2026-10-20

The user resumed the [recorded stop-point](HANDOFF-2026-10-20-IO.md).
This completes the current OS/agent work from
[the agreed plan](optional-os-context-management-proposal-2026-10-20.md).
The repository already contained substantial unrelated changes; this work did
not reset, stage or claim those changes. No commit, push, live provider request,
historical-run resume or gameplay validation was performed.

## What was completed after resuming

- Ran the pending affected regressions first: **106 passed in 142.47s**.
- Corrected grouped-system validation for non-object input and the local
  batch-size environment override.
- Finished proxy prepared-request measurement, selected output-limit forwarding
  and transport-response caps. Proxy internal native generation remains opaque.
- Made summary child failures terminal rather than creating a nested retry tree;
  prevented final submission after preparation leaves uncertain effects.
- Added retained original/derived view identities and compaction-call links to
  context receipts.
- Routed native terminal byte-limit stops through OS smaller-response recovery
  with the same mutation/effect checks. Rejected reported native generation
  overages and Gemini generation overages including reported thinking tokens.
- Corrected shell error attribution so unrelated capture failures are not labelled
  write-scope violations.
- Synchronized the optional ContextPart.compactable field in runtime/design
  contracts and regenerated the design JSON schema with installed Pydantic.
  Generator-format changes remove redundant singleton enums and add dictionary
  key constraints; the Python schemas are tested against one another.
- Completed the [central settings reference](../design-docs/simplified-os/AGENT_SETTINGS.md)
  and linked README/boundary/plan/handoff. A regression checks every exported
  field is present and all five grouped example configs validate.
- Confirmed interrupted-source grant/base-conflict refusal before partial copying.
- Corrected valid tool actions to reset the agent's consecutive protocol-error
  count; a valid reply does not increase the correction allowance.
- Distinguished tool-free compaction children from brokered capability effects
  in the native retry guard. A summary child alone does not disable safe output
  adaptation; actual broker callbacks still prevent automatic replay.

## Checks and evidence

- Final repository suite: **327 passed, 2 skipped in 492.24s**:
  .venv-linux/bin/python -m pytest -q --tb=short -ra.
  Skips: WSL Node/npm housekeeping prerequisite and Node 18+ frontend prerequisite.
- That full run was already imported when the final valid-action reset and
  native summary-child retry-guard corrections were made. The final on-disk
  context/recovery implementation was then verified by **73 passed in 25.76s**:
  .venv-linux/bin/python -m pytest tests/test_context_safety.py tests/test_model_retries.py -q --tb=short.
  This includes both corrections and native compaction followed by output cutoff;
  no second full run after those two final corrections is claimed.
- Windows Node: **14/14 frontend tests passed** with node --test tests/ui_start.test.cjs.
  This separately covers the frontend skip, not the Linux npm-housekeeping skip.
- Final Ruff: **passed** for src, tests and design-docs/langgraph-agent/contracts.py.
- git diff --check: **passed**; an existing CRLF conversion notice for
  tests/test_setup_tools.py is not a whitespace failure.
- Consolidated-reference field inventory and all five grouped examples: **passed**.
  README/settings/boundary local-link check: **passed**.
- Standalone design validator in an isolated canonical-LF copy: **35 records and
  41 invalid contract combinations passed**, with schema/source/graph/JSON and
  publication checks. See the checkout line-ending qualification below.

The first full run was **323 passed, 2 skipped, 1 failed in 444.51s**.
Its only failure was runtime/design schema parity for the new optional field.
After synchronizing the design definition, all 10 contract tests passed.
A focused native/context run passed all 31 tests before the later reference/reset
checks. The new source-conflict checks passed both cases. Initial new native and
source-conflict fixtures required corrections to model a tool-free protocol and
a legitimately recorded integrated head; these were fixture corrections, not
relaxations of runtime guards.

WSL test logs (temporary, not committed):
- /tmp/poly-context-resume.log — pending handoff regressions.
- /tmp/poly-context-edges.log — additional boundary checks.
- /tmp/poly-context-native-final.log — native/context focused checks.
- /tmp/poly-io-full.log — first full run and schema mismatch.
- /tmp/poly-io-final.log — final full run.
- /tmp/poly-source-conflicts.log — initial source-conflict fixture diagnostic;
  the corrected two-case check was rerun successfully in the tool output.

## Material limits

- Native app-server/proxy hard generation-token enforcement is unavailable.
  Default mode reports that capability; strict mode rejects before submission.
  Known completed overages/cutoffs are withheld and safely adapted when eligible.
  Hidden native context and unreported server-side truncation cannot be certified.
- Prepared-request sizing is a conservative bound on known UTF-8 payload bytes,
  not an exact provider tokenizer. A provider can reject at a stricter cap;
  that failure is typed and returned without an unchanged input retry loop.
- Automatic compaction is opt-in. It operates on submitted eligible blocks,
  retains original artifacts, and uses bounded chunk summaries. There is no
  background canonical-memory rewriting or recursive summary hierarchy.
- No live local/cloud provider or real native server was invoked. Native coverage
  uses real stdio subprocess fixtures; HTTP coverage uses actual adapter code
  with MockTransport. These do not establish model quality or real server limits.
- Direct standalone design validation stops at its historical source HTML byte
  digest because the checkout has 157 CRLF line endings. The expected digest is
  exactly the Git HEAD blob's digest, and LF-normalized working bytes match HEAD.
  In an isolated temporary copy using those canonical LF bytes, validation passes
  all 35 example records and 41 invalid contract combinations, schema parity,
  graph/JSON counts and publication links. Neither original graph bytes nor the
  historical fingerprint were edited.
- Fresh state is required because configuration/program pins changed. The
  original Minecraft run was not migrated, retried or resumed.
- Shared agent-library work stays deferred in
  [next-iteration.md](next-iteration.md#shared-agent-support-library).

## Where to continue

Current implementation and documentation are complete subject to the limits
above. Use [AGENT_SETTINGS.md](../design-docs/simplified-os/AGENT_SETTINGS.md) for
all exported OS settings and manual/packing/compaction/hybrid usage. Optional next
validation is a fresh-state local/cloud canary or the original application
scenario under an explicit new run; it has not been silently launched.
Direct design-history validation requires canonical LF checkout bytes; its
line-ending behavior is separate from I/O recovery.
Do not repeat the old stop-point checklist or introduce the deferred third layer.
