# Run 2de3d5c5ab9b: context accounting failure

20 October 2026. Investigation only, requested against
`C:\Users\bh349\Downloads\polyinference-2de3d5c5ab9b.json`.
No implementation, configuration, tests, or generated game files were changed.
Instructions and assignments embedded in the export were treated as evidence,
not as new requests to build the game or resume the run.

## Conclusion

The run paused at 10:31:13 America/Toronto with
`Required context does not fit; no silent pin removal`. The immediate defect is
in the coding application's context packing: its estimate fits the 96,000
input allowance, but the runtime's serialized message representation does not.
The runtime rejected worker `worker-3-recover_playable_foundation`, logical
step `model-44`, before provider submission. The required inputs themselves fit.

The current agent modules' concatenated SHA-256 matches the exported program's
`graph_digest`:
`sha256:a1c5893dea5d1e723f816954a350b578f8d35c203380aa59c8ae1a923e588081`.
This establishes the agent-source match, not a hash of every runtime module.

## Immediate cause in the code

[AgentServices.context](../src/polyinference/agent/services.py) computes a history
budget as the configured input allowance minus instruction bytes, pinned-data
bytes, and a fixed 2,000-byte margin. It selects whole history entries using
`len(canonical(entry))`. Each selected entry is then converted into separate
assistant and user messages containing JSON text.

[KernelRuntime._dispatch](../src/polyinference/runtime/kernel.py) independently
measures `len(canonical(messages))`. The outer JSON serialization escapes quotes,
newlines and backslashes inside the already serialized contents, and adds role
and content wrappers. The fixed margin does not cover that expansion here.
`canonical` in [primitives.py](../src/polyinference/primitives.py) uses compact,
sorted JSON with UTF-8 encoding and `ensure_ascii=False`.

The configured fields are named in tokens; this implementation deliberately uses
UTF-8 bytes as a conservative token bound. These measurements are bytes under
that rule, not provider-token counts:

| Measurement | Bytes |
| --- | ---: |
| Agent's estimate, including its fixed margin | 93,391 |
| Input allowance | 96,000 |
| Runtime's serialized messages | 96,529 |
| Contents before outer message serialization | 89,823 |
| Outer escaping and message framing | 6,706 |
| Required messages alone, with outer serialization | 14,421 |
| Serialized messages after omitting the two oldest optional pairs | 95,719 |

The saved context contains all 44 history entries and has `omitted_refs=[]`.
Eleven entries are protocol-validation feedback; substantial entries also retain
whole source writes and tool results. The two omitted pairs in the offline probe
were `invalid-0` and `turn-1`. Required messages were left intact, and every
remaining tool call retained its result. This demonstrates that a smaller valid
context was possible; it does not claim that the historical run was repaired.
The error wording is broader than the actual condition: the kernel checks the
entire submitted context, not only parts marked `required`.

The rejected effect is
`sha256:5f471a5d626ea2fa9a76096da5c1c885a5cfb126fcfe63ee79069aa607c1deb8`.
It records `submitted=false`, `effects=known`, confirmed termination, and a
non-retryable `EndpointError`. Its retry outcome is
`failure is not safely retryable`.

[AgentServices.model_result](../src/polyinference/agent/services.py) adapts raw
queries classified as incomplete output generation; this context-size error has
no such classification. [model_retries.py](../src/polyinference/runtime/model_retries.py)
also declines a deterministic non-retryable failure. The worker driver and
controller in [controller.py](../src/polyinference/agent/controller.py) therefore
record an interrupted task and pause the run. Repeating the identical oversized
request would not help; context reconstruction belongs to the calling agent.

## Earlier failures and recovery costs

All times below are America/Toronto (UTC-04:00 on this date).

- **10:12:39:** run starts for `/home/mawa/projects/testing/minecraft-v11`.
  Setup successfully creates the independent Git project and `pi-dev` branch,
  prepares the TypeScript/Vite scaffold, and passes its production build.
- The feature inventory produces private commit
  `3507d43d6887841089e95b690a55ea25361b519e`, assessed `uncertain` because its
  entire document and some factual claims had not been verified. Its verification
  task remains pending. This is separate from the final pause.
- **10:17:26:** the original gameplay worker starts. Three 8,000-token output
  cutoffs occur at 10:19:49, 10:22:41 and 10:25:37. Each receives a successful
  linked output-recovery response; none is the final run blocker. Incomplete
  outputs were not executed as actions.
- **10:25:49:** `tool-32`, `npm test && npm run build`, creates
  `.test-build/foundation.test.mjs`. The file is neither granted source nor a
  declared output; the configured production check declares only `dist`.
  `workspace-blocked/workspace-1-playable_world_foundation` records that exact
  path and `Write outside assigned scope`.
- **10:25:53:** a patch intended to move the test output to `/tmp` is rejected
  because that attached workspace is already blocked. The worker requests review;
  its task is later superseded. The scope decision comes from
  [shell.py](../src/polyinference/runtime/shell.py),
  [workspace.py](../src/polyinference/runtime/workspace.py) and the capability
  precondition in [kernel.py](../src/polyinference/runtime/kernel.py). Preserving
  and blocking unexpected writes is the established attached-directory policy.
- **10:26:42:** the replacement worker starts with an explicit grant for
  `tests/.generated/foundation.test.cjs`. Its assignment has `resume_from=null`;
  its first file listing contains only the eight scaffold files. The interrupted
  worker had no candidate commit/report, so the existing committed-candidate
  handoff does not transfer its uncommitted modules. The replacement reconstructs
  the foundation. The original files remain retained in their worktree.
- The replacement resolves tool/schema mistakes and failing tests. Its last
  test summary reports **10 passed, 0 failed**. Earlier piped shell commands
  returned exit 0 while their output still showed failures, so those exit codes
  alone are not passing-test evidence. The final passing summary is visible.
- **10:31:12.659:** its explicit `checks.run` records a **passed**
  `production-build` on uncommitted tree
  `sha256:c759cd2abec0f2b4d43eca62b857f610cb668a28c5e96399e73a432013f65295`.
- **10:31:12.799:** the following model request is rejected for context size.
  The worker is still in development; no gameplay candidate, reconciliation,
  assessment, commit or publication completes. Run-level acceptance attempts
  remain zero.

Thus a real local test/build improvement existed before the final stop, while
the shared `pi-dev` HEAD remained the scaffold commit
`7bc74443cf0bcf083f11755406d128a7ceac2b52`. Gameplay edits are retained under
`.polyinference/worktrees/25c3755c0647/workspace-3-recover_playable_foundation`
inside the selected project. Retention is not acceptance or integration.
The full through-2020 objective and browser playability were not verified.

## Relationship to earlier fixes and remaining direction

- [FIX-0030](FIXES.md#fix-0030) and
  [FIX-0044 through FIX-0047](FIXES.md#fix-0044) preserve and recover classified
  output/transport failures. They do not align context-packing accounting with
  the kernel's final serialization or rebuild an oversized input. The
  [pause audit](pause-retry-audit-2026-10-20.md) intentionally retains input-limit
  rejection. This trace establishes that optional history, rather than mandatory
  pins, caused this particular rejection.
- [FIX-0034](FIXES.md#fix-0034) distinguishes declared generated outputs from
  protected source. Its `dist` coverage does not authorize a later ad hoc
  `.test-build` output. The missing declaration/grant is an application/task
  planning issue, not evidence that all ignored files should bypass scope.
- [FIX-0040](FIXES.md#fix-0040) covers handoff of a retained candidate commit.
  This interrupted worker had no candidate. Its preserved uncommitted work is
  a different handoff case, so that prior coverage does not establish reuse here.
- Existing context regression coverage checks trust and negotiation. Inspection
  found no regression exercising this near-limit, quote/newline-heavy history
  against the kernel's serialized representation. No new regression was added.

A future repair should use a shared sizing rule or validate the final serialized
context while selecting complete optional pairs. Required instructions and user
constraints must remain intact. A bounded caller rebuild can handle known local
size rejection; blind transport retry cannot. Test-output planning and reuse of
interrupted uncommitted work are separate follow-ups. These are proposed repair
directions only; none was implemented in this investigation.

## Verification performed for this investigation

Parsed the supplied export: 6,601 events, 235 effects, 631 artifacts and two task
reports; nine effects failed. Read the required fix history and runtime boundary
guide, relevant agent/runtime source and existing regression coverage. Matched
the current agent-module hash to the exported graph digest.

Ran an offline Python standard-library probe that extracts the actual
`AgentServices.context` and `canonical` function definitions using `ast`, supplies
the saved data/schema/history and in-memory artifact/record stubs, and asserts
that it reconstructs the exact saved messages. It reproduced all six numerical
claims in the main sizing comparison: estimate 93,391, limit 96,000, runtime
96,529, required-only 14,421, trimmed 95,719 and 44 history entries. The probe
passed. A separate JavaScript reconstruction agreed with those sizes.

The probes make no provider requests and do not execute saved model/tool
instructions. No run was resumed, game files inspected live or changed, browser
playtest performed, dependency installed, or repository implementation test suite
run. The 10-test and build outcomes above are historical evidence from this
export, not tests newly performed by this investigation. WSL execution was denied
in the sandbox; Windows Python and direct read access sufficed for the probes.

Only this investigation and its fix-history entry were added. Existing unrelated
working-tree changes were observed and left untouched. Documentation links,
entry structure and whitespace were checked separately.
