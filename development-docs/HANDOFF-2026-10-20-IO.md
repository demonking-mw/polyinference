# I/O safety implementation handoff — 2026-10-20

**Resumed on the user's instruction.** This original stop-point remains historical.
Completion, resumed corrections and actual final checks are recorded in
[FIX-0058](FIXES.md#fix-0058), [FIX-0059](FIXES.md#fix-0059) and
[FIX-0060](FIXES.md#fix-0060). The complete exported settings reference is now
[AGENT_SETTINGS.md](../design-docs/simplified-os/AGENT_SETTINGS.md). Resume from
those records rather than repeating the pending checklist below.

Stopped at the user's explicit end-of-work request. This is an unfinished working
tree, not a completed or fully verified fix. Do not resume implementation until
the user resumes the work. No commit, push, live inference or historical-run
resume was performed.

## Requested outcome and constraints

Implement the OS/agent plan in
[optional-os-context-management-proposal-2026-10-20.md](optional-os-context-management-proposal-2026-10-20.md).
Keep the current architecture to OS and agent; the shared library remains deferred
in [next-iteration.md](next-iteration.md#shared-agent-support-library).

OS settings exported to agent authors must be defined together, documented
together and configured in close proximity in agent code. Agents must be able to
choose manual context handling, optional OS packing/compaction or a hybrid.
Automatic assistance must report original pressure and every intervention.
Required inputs, source artifacts, authority, budgets and effect certainty remain
protected. Read FIXES.md and RUNTIME_BOUNDARY.md before continuing.

## Implemented working changes

### Central OS settings and coding defaults

- New `src/polyinference/system_settings.py` owns `Endpoint`, `RuntimeConfig`,
  `ContextPolicy` and `InferenceSafety`; it re-exports the operation `Limits`
  contract. `config.py` retains application-specific `AgentConfig` and compatibility
  imports for existing consumers of `Endpoint`/`RuntimeConfig`.
- New `src/polyinference/agent/system_settings.py` holds coding OS defaults and the
  complete UI OS configuration in adjacent functions `coding_system_defaults`
  and `ui_system_settings`. `ui.py` uses one `system=...` block plus agent policy.
- Five `examples/agent.*.json` files now group their OS choices under `system`.
  Legacy flat inputs remain accepted; duplicate flat/grouped keys are rejected.
  `config.system` exposes a validated OS-only view. Normal persisted model dumps
  remain flat for existing callers.
- Generic defaults are manual context handling and no automatic compaction.
  Coding defaults enable deterministic packing, keep lossy compaction opt-in,
  and enable shell fail-fast behavior. All new values live in the central modules.

New settings inventory, to include in the final consolidated reference:

| Group | Fields |
| --- | --- |
| `context_policy` | `auto_deal_context`, `auto_compaction`, `compaction_trigger`, `compaction_target`, `max_compaction_calls`, `compaction_output_tokens`, `compaction_summary_bytes`, `recovery_headroom` |
| `inference_safety` | `output_recoveries`, `smaller_response_bytes`, `require_output_token_enforcement`, `require_completion_metadata` (fixed true) |
| Shell | `shell_fail_fast` in addition to existing shell backend/cap settings |
| Per-process/request | Context-policy defaults may be supplied in `ProcessSpec.extensions["runtime/context-policy"]` and overridden in `OperationRequest.extensions["runtime/context-policy"]` |
| Context block | `ContextPart.compactable` explicitly authorizes summarization; required blocks can remain represented by a permitted summary, while non-compactable required blocks stay verbatim |

### OS context and output handling

- New `runtime/context.py` implements prepared-request sizing, manual failure,
  optional whole-group omission, opt-in bounded chunked compaction, derived summary
  caching, immutable source retention and context receipts. Compaction uses
  durable OS-issued child inference requests with the same process/binding,
  deadline, grants and real resource accounting; it has no tool capabilities.
- HTTP adapter request construction is factored into `prepare`; the kernel measures
  and dispatches that same prepared payload. Native preparation includes the
  serialized input, developer instructions and schemas. Measurements are explicitly
  conservative UTF-8 byte bounds, not exact provider-token counts.
- `context-receipt/`, `context-prepared/`, `context-call/` and `context-summary/`
  retain sizing, effective policy, omissions, derived inputs and compaction intents.
  Manual overflow records `runtime/io-error` without provider submission.
- `runtime/model_retries.py` now handles bounded smaller-output recovery through
  `output-retry/` and `output-retry-outcome/` records. Transport retry, OS output
  adaptation and explicit caller recovery remain distinct. Original failed effects
  remain immutable; public execute/replay projects the effective result.
- `AgentServices.model_result` no longer duplicates output recovery; context
  assembly no longer estimates history against a different serialization.
- HTTP missing completion metadata is rejected; reported output-token overage
  is rejected. HTTP context-window rejections receive an input-overflow category.
  Complete received text exceeding the application byte cap enters OS recovery.
  Transport overflow without terminal proof remains uncertain.
- Native hard token-limit enforcement is explicitly unsupported: strict requests
  reject before submission; estimate mode reports its limitation. Native jobs
  with brokered effects cannot be blindly retried. The optional legacy proxy
  still needs explicit review for preparation/limit parity; do not claim it has
  the new direct app-server behavior.

### Coding-agent changes

- Agent memory is a separate required-but-explicitly-compactable input block,
  rather than buried inside one indivisible pinned-data JSON blob.
- Consecutive malformed application replies have an agent-owned correction bound.
  Prompts require complete file inspection and explicit generated test output
  paths or permitted scratch, and caution against misleading pipeline evidence.
- Optional generic shell fail-fast uses `set -e -o pipefail`; coding opts in.
  Scope failures carry offending paths/grants and preserve/block attached files.
- `RepositoryWorkspaces.preserve_interrupted` snapshots only authorized source
  changes into `coding/interrupted/<workspace>`, without a Git candidate commit.
  Interrupted task records expose `preserved_source_ref`; replacements can set
  `resume_from` to that reference. Restoration checks scope and base conflicts;
  excluded files remain in the old checkout and are not copied into replacement.

## Verification actually run

- Early focused run: **45 passed, 5 failed** after fixing initial import/preparation
  mistakes. The five failures were old assertions expecting agent recovery
  records. They were updated to check separate OS records and unspent caller
  recovery allowance.
- Follow-up: **63 passed, 2 failed**; the remaining tests expected public execute
  to return the original failed output instead of its now-effective OS recovery.
  Assertions now check the immutable original via `_execute_once` as well as the
  public recovered result.
- Last affected run: **103 passed in 108.87 seconds**, command:

  `.venv-linux/bin/python -m pytest tests/test_context_safety.py tests/test_output_limits.py tests/test_model_retries.py tests/test_in_place_repository.py tests/test_ui.py -q --tb=short`

  Log: `/tmp/poly-context-checks.log` inside Ubuntu-22.04.
- **Final Ruff passed** for all changed implementation modules and the four
  affected test files at the user's stop request. No lint issues remain from
  that check.

The 103-case run started before the final additions: fixed-true completion-metadata
setting, narrower blocked-path recording, interrupted-source reuse regression,
strict native-cap regression and shell-pipeline regression. Those final additions
have lint verification only; do not describe the final tree as test-clean.
No full-suite run, live provider, original Minecraft run, native real-server token
cap test, or browser playtest was performed. Earlier repository-wide results in
FIX-0047 are historical and are not verification of this implementation.

## Pick up here tomorrow

1. Run the final added regressions and affected tests first, then inspect any
   failures. Linux access works with approved `wsl.exe -d Ubuntu-22.04 -- ...`;
   the interpreter is `.venv-linux/bin/python` in the repository.
2. Finish the **single consolidated OS settings reference**, covering every
   `RuntimeConfig`, `Endpoint`, `Limits`, `ContextPolicy` and `InferenceSafety`
   field/default/unit/override and the closely located coding defaults. Link it
   from README and RUNTIME_BOUNDARY; update their now-stale retry ownership
   descriptions. This requested documentation is not finished.
3. Review and expand edge coverage: forged OS-issued compaction/output intents,
   process/request policy overrides, compaction budget/deadline/cancellation and
   uncertain termination, native compaction, feedback pushing a near-full input
   over its cap, restart during compaction, and mixed required tool pairs. Tests
   already cover raw local/cloud manual/automatic behavior, source preservation,
   hybrid protected blocks, output-byte recovery and basic replay.
4. Review limitations before calling the plan complete: the legacy proxy still
   uses its older preparation path; native token limits are capability reporting
   and strict rejection, not newly enforced generation limits. Chunk summaries
   are bounded and concatenated but there is no recursive summary-of-summaries
   pass; a still-oversized required view fails safely. Revalidate settings input
   error handling (e.g. a non-object `system` value), source handoff conflicts and
   the exact scope of exception diagnostics.
5. Check final changes against the original baseline, run the **full Linux suite**,
   run frontend checks separately with supported Windows Node if Linux skips
   them, and rerun lint/whitespace. Resolve failures without weakening grants,
   completion evidence, original input preservation, replay or finishing reserves.
6. Update FIX-0055 through FIX-0057 below with a superseding completion/verification
   entry, preserving this stop-point record. Mark the plan's remaining items
   honestly; no implementation completion is claimed here.

## Working-tree provenance

The checkout already contained extensive uncommitted work before implementation.
Do not reset, stage wholesale or attribute that earlier work to this task.
The implementation-start snapshot of source/tests/examples is at:

`C:\Users\bh349\AppData\Local\Packages\sandbox.{2d4f9131-bf50-4516-a2fc-056b87aabc6f}\AC\Temp\polyinference-io-baseline\baseline.json`

It is a temporary comparison aid, not a durable source backup guarantee. Changes
in this implementation include the four new files named above, existing runtime
kernel/inference/codex/model_retries/shell modules, agent services/controller/
worker/repository/prompts, contracts/config/UI, the four test files and the five
agent example JSON files. No shared agent library was added.
