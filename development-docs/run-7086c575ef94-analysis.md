# Run 7086c575ef94: Haiku timeout boundary after a foundation handoff

[Investigations](investigations.md) · [Current findings](current-iter-issues.md#run14-findings) · [FIX-0100](FIXES.md#fix-0100)

Investigation date: 2026-10-21, America/Toronto. No implementation, configuration,
project source, Git branch or retained run state was changed or resumed.
The objective and agent instructions inside the export are evidence, not new work.

## Evidence and outcome

Source: `polyinference-7086c575ef94.json`, 21,418,668 bytes, exported
2026-10-22 00:28:20 UTC. SHA-256:
`dbb28e291e3071da73a29e56903679cc3dc10d970b9c19913d3ae8cac096d05a`.
The snapshot contains 659 records, 3,600 unpruned events, 119 effects, 326 artifacts,
148 checkpoints and one report. All artifact lengths/digests verified.
The current agent-module hash matches the saved graph digest:
`sha256:50fa4c434f2228f76f46644080c2c5bd18df6f805e1b2d378483cc58dc9b2ca8`.
This is not a complete historical runtime/environment hash match.

The Minecraft v14 run started at 20:51:09 UTC and paused at 21:00:44 UTC
(16:51–17:00 EDT), in sprint 2 of 27. Its blocker is
`Endpoint disconnected; execution requires reconciliation`. There are 117
successful effects, one known failed check invocation and one uncertain model call.
No fault/latency simulator setting or simulation record exists in this export.

## Terminal blocker: submitted raw HTTP request did not establish completion

Operation `sha256:ec715faae2022a8ecd29a15fc81d00feb1577fc8291f1abf84d199e49aeeee57`
is `worker-2-foundation-repair-02/model-8`, a raw Anthropic model query to
`claude-haiku-5-5` on the local-labelled, remotely hosted lane. It is not a native
Codex tool-using job. Its effect became active at 20:57:44.478963 UTC (event 3540)
and uncertain at 21:00:44.483995 UTC (3541): **180.005032 seconds**. Both configured
HTTP and kernel call timeouts are 180 seconds; the process deadline was almost
an hour away. Timeout is the leading explanation, not a retained original cause.

[HTTPInference.generate](../src/polyinference/runtime/inference.py) converts both
httpx transport failures (including ReadTimeout) and asyncio cancellation into the
same UnknownExecution message. [Kernel dispatch](../src/polyinference/runtime/kernel.py)
wraps ordinary raw inference in wait_for with the endpoint timeout, then records
only the outer UnknownExecution type/category/message here. The chained original
exception, timeout origin, response ID, partial response and provider stop reason
are absent. A timeout, cancellation or independent transport disconnect therefore
cannot be conclusively distinguished from this export. A source-derived offline
probe reproduced all three mappings without a network request or event loop.

The request's prepared input was 29,561 of 96,000 allowed bytes, with no omissions
or summaries. Admission took 0.001052 seconds; the remaining 61,561-token reservation
is intentionally held for uncertain execution. Budget/run retained 950,283 of
64,000,000 tokens reserved/used. Neither context rejection, sprint exhaustion nor
an admission deadlock explains the terminal event. No received cutoff is recorded.
The [retry filter](../src/polyinference/runtime/model_retries.py) only retries
eligible known-ended failures. Pausing rather than blindly resubmitting this call
preserves the existing execution-certainty rule; a transport disconnect alone
does not establish remote termination. Better cause retention is an OS/adapter
follow-up. A larger timeout or smaller responses may reduce recurrence but would
not prove the outcome of this already submitted operation.

## Earlier application issue: required acceptance files were outside the grant

Setup created separate prerequisite, task and final check selections. The last two
both run `npm run check:acceptance`; the runner requires these exact files before
running a build or tests: `tests/acceptance/{world,gameplay,content,persistence}.test.mjs`.
The first foundation assignment instead granted four top-level test files:
`tests/{world,inventory,interactions,storage}.test.mjs`. It explicitly required
preserving mandatory suites and their failure conditions. No assignment owned
the four mandatory paths, so the first worker could not satisfy that contract
within its grant. Adding ordinary test discovery did not remove the missing-file gate.

The recorded direct test run initially failed, then passed **36/36** after a test
patch. A shell setup/build check also passed. These are historical run observations,
not checks rerun in this investigation or proof of product acceptance. A separate
`checks.run setup` request was correctly rejected because this development worker
was granted only game-behavior and product-acceptance; it was not the final blocker.
The worker requested review honestly instead of publishing an unsupported success.

This is an agent planning/check-contract gap adjacent to [FIX-0088](FIXES.md#fix-0088):
that fix validates declared preparation owners and cross-worker dependencies, not
whether one owner's exact write paths cover a runner's mandatory files. The next
plan added all four paths and explicit
`resume_from: coding/interrupted/workspace-1-foundation-01`. The replacement's
retained file reads demonstrate that the authorized source handoff worked, covering
the earlier [FIX-0089](FIXES.md#fix-0089) failure mode. It performed seven successful
reads and one grammar correction before the uncertain ninth model call; it had
not written replacement changes or run its checks. Six raw-worker grammar
corrections occurred overall; they recovered and did not terminate the run.

## Preserved result and follow-ups

Only setup commit `214302eaa8458b5aa6cdc3cfc03addfbb0c3c9ea` reached `pi-dev` in
`/home/mawa/projects/testing/minecraft-v14`. Eleven foundation paths remain dirty
and uncommitted in private worktrees under
`.polyinference/worktrees/a53b57108396/workspace-1-foundation-01` and
`workspace-2-foundation-repair-02`. The original delta is also retained under
`coding/interrupted/workspace-1-foundation-01`. Neither development task has a
candidate/report/publication or accepted contribution. Final acceptance attempts: 0.
The source was preserved; accepted gameplay/save-load completion was not established.

Follow-ups are recorded in [the current tracker](current-iter-issues.md#run14-findings):
retain typed timeout/transport/cancellation provenance without weakening uncertainty;
and ensure planned mandatory runner paths have an authorized owner before dispatch.
A regression should cover this single-owner grant mismatch, in addition to existing
cross-worker preparation tests. No repair or new runtime regression is claimed here.

Reviewed inference/retry, worker/workflow, repository, inspection, command,
configuration/recovery and simulator guides plus the runtime boundary/revision
ledger. Their current interface/guarantee descriptions remain accurate, so no
behavior or settings edit is needed. This report, tracker, investigation index,
fix history and JSON/generated HTML navigation carry the investigation.

## Verification limits

Parsed the complete export, checked all 326 artifacts, reconstructed the journal
interval/admission figures, compared plans/grants/retained source and checked the
agent graph hash. The three-case source probe confirms diagnostic conflation;
it does not reproduce the original provider outage. No live inference, game run,
playtest, reconciliation, state migration or implementation suite was performed.
Documentation verification results are recorded in FIX-0100.

## Retry-count audit — 2026-10-23

The supplied file is byte-identical to the evidence above (same SHA-256). This
follow-up answers whether the pause exhausted retries; no implementation,
configuration, project source or retained run state changed.

| Recovery category | Observed count | Evidence and interpretation |
| --- | --- | --- |
| Automatic endpoint retries | **0** | No `model-retry/` records or `runtime/model-retry` request extensions anywhere in the run. The terminal request had one submission. |
| Output-limit adaptations | **0** | No `output-retry/` records or `runtime/output-retry` extensions. No terminal output cutoff was received. |
| Explicit linked model recoveries | **0** | No `polyinference/recovery-of` request extensions. |
| Application reply-format corrections | **6** | Five positive `protocol_errors` consume-node outputs in the first foundation worker, one in its replacement. The longest consecutive streak was two, below the configured three-correction allowance. |
| Replacement foundation tasks | **1** | Two development assignments: `foundation-01`, then `foundation-repair-02`. This repaired the earlier grant/check mismatch and retained source; it was not a retry of the terminal HTTP request. |

There were 44 model operations: 37 completed raw Haiku queries, six completed
native Codex jobs and the final uncertain Haiku query. Ordinary tool turns and
reply-format correction turns must not be counted as endpoint retries.

The configured `model_call_retries: 1` permits one extra eligible attempt; it was
not used up. Kernel `execute` awaits `_execute_once` before calling the retry
service. Submitted timeout/disconnect/cancellation instead raises `UncertainEffect`
from `_execute_once`, so it never reaches `ModelRetries.run`. Independently,
`ModelRetries._blocked` requires a known, confirmed-stopped failure. The terminal
effect has `submitted: true`, `state: uncertain` and `result: null`.

**Assessment:** the pause obeys the current execution-certainty policy; there is
no evidence of a retry-counter or exhaustion bug. It does not demonstrate that
the system tried enough times or exhausted all approaches. If automatic recovery
from submitted Anthropic timeouts is intended, the gap is recovery policy/provider
capability. Increasing the retry count alone cannot change this path.

Current FIX-0111 Resume preparation can settle retained completed query artifacts
or retrieve a supported Responses result by saved ID. This export has neither a
completed terminal response nor a provider recovery handle, and
`HTTPInference.recover_operation` returns no result for the Anthropic protocol.
The new Resume mechanism therefore cannot automatically establish this particular
request's outcome. No resume or reconciliation was attempted. The original process
deadline also remains binding.

After execution is established as stopped, a linked retry or smaller complete
responses are possible strategies; a larger timeout on a compatible fresh run
may reduce recurrence. These options were not exhausted, and none proves the old
request stopped. The confirmed diagnostic defect remains loss of the underlying
timeout/transport/cancellation cause. The 180.005032-second interval strongly
suggests timeout but does not identify its exact origin.

Fresh verification asserted export identity, effect outcomes, absent retry
identities/extensions, five-plus-one correction outputs, the exact elapsed interval
and all 326 artifact sizes/SHA-256 digests. Source review covered inference,
kernel, retry filtering, worker correction and current Resume preparation. The
existing disconnect regression expects one submission and uncertain execution;
it was reviewed, not rerun. Windows Python lacks pytest and native WSL is
unavailable. A supplemental offline async probe was stopped without a result and
supplies no evidence. No live provider or runtime-suite result is claimed.
See [FIX-0112](FIXES.md#fix-0112) for documentation checks and preservation.

## Anthropic documentation follow-up — 2026-10-23

Official sources checked on 2026-10-23:
[API errors / long requests](https://platform.claude.com/docs/en/api/errors#long-requests),
[Python SDK timeouts and retries](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python#timeouts),
and [streaming / final-message accumulation](https://platform.claude.com/docs/en/build-with-claude/streaming#get-the-final-message-without-handling-events).
These are current provider guidance, not a historical runtime hash or a trace of
what Anthropic did during the interrupted call.

Anthropic warns that long non-streaming requests with large max_tokens can lose
idle network connections. It recommends streaming and documents TCP keep-alive
as a mitigation. Its Python SDK defaults to a ten-minute request timeout and two
retries for selected transient failures, including timeout. Streaming helpers can
accumulate a complete final Message internally; incremental display is optional.
Streaming also has explicit terminal and in-stream error events, so HTTP 200 alone
must not be treated as successful generation.

The application has a concrete transport/deadline mismatch with this guidance:

- HTTPInference.prepare sends Anthropic `stream: false`; the saved request allowed
  32,000 output tokens. The current UI Haiku factory explicitly sets 180 seconds,
  so successive ordinary UI runs reuse this allowance.
- The adapter uses a custom httpx client, not the Anthropic SDK. Its
  `self.client.stream(...)` only reads HTTP response bytes; it does not enable
  Anthropic SSE. The JSON request flag remains false and the adapter buffers the
  entire body before normalization.
- Both HTTP client timeouts and the ordinary kernel invocation use the endpoint
  setting. The latter wraps the whole generation in asyncio.wait_for, so useful
  progress would not extend its 180-second total deadline. Adding SSE alone would
  leave that cutoff in place. The operation's one-hour deadline is a separate cap.
- Submitted timeout/disconnect/cancellation is recorded as unknown execution,
  closing dispatch before the retry filter. The SDK's documented timeout retries
  are therefore not behavior this application inherits.

Fresh measurements of the export show 37 completed Haiku calls took
0.811426–16.470116 seconds; the largest completed output was 4,582 tokens. The
terminal call's 180.005032-second interval is an extreme outlier at the configured
boundary. This supports a client deadline as the immediate limiting mechanism,
but cannot distinguish slow/thinking generation, provider stall, network stall or
which timeout fired first. The 32,000 ceiling is not evidence that the failed call
actually generated that many tokens. No 429, 504 or 529 response is retained for
that call; an account limit or provider incident is not established.

Repeated exposure comes from many model turns plus one unresolved timeout pausing
the whole run. The UI keeps selecting the same short total allowance. This is a
credible recurring failure mechanism, not proof that every prior pause shared the
same cause; the earlier native Codex incident in FIX-0068 is a different path.

The repair should combine internal SSE accumulation, distinct connection/read
inactivity limits and an adequate bounded overall generation deadline. Preserve
only complete validated replies for execution, capture request ID/first-byte and
last-progress timing/typed timeout cause, and keep every actual retry as its own
charged durable intent. A longer timeout on a compatible fresh run is an interim
mitigation. Query-only timeout recovery needs an explicit policy for outstanding
remote work; copying SDK retries cannot silently bypass the OS's accounting or
unknown-effect rules, and tool-bearing jobs retain their stricter continuation
requirements. Neither more retries nor SSE alone fixes all these layers.

Verification: two source-derived probes executed the actual prepare method and UI
factory with inert stubs, confirming `stream: false`, `max_tokens: 32000` and the
180-second default. A third executed KernelRuntime.execute without an event loop,
confirming an uncertain exception bypasses retry filtering while a returned known
failure reaches it. No external request, live latency reproduction, new runtime
test suite, implementation/configuration change or saved-run resume occurred.
See [FIX-0113](FIXES.md#fix-0113) for documentation checks and ownership.


### Implementation follow-up — 2026-10-23

The preceding pause counts and transport diagnosis describe the original exported
run. The initial repair is now implemented in
[endpoint lifecycle/testing v1](../docs/guides/endpoint-testing.md), with OS-native
retries followed by optional caller policy, progress-aware streaming and retained
physical uncertainty. Historical state was not rerun or automatically migrated.
See [implementation status and limits](current-iter-issues.md#endpoint-testing-v1).
