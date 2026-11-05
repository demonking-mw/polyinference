# Input and output cap safeguards: current behavior

Implementation update: this audit describes the pre-change baseline. Current
behavior, verification and remaining limits are in
[the completion report](io-safety-verification-2026-10-20.md) and
[the OS settings reference](../design-docs/simplified-os/AGENT_SETTINGS.md).

20 October 2026. Analysis-only follow-up to
[run 2de3d5c5ab9b](run-2de3d5c5ab9b-analysis.md). No implementation or
configuration changed. The user asked whether the OS detects and recovers from
input overflow and output truncation equally on local and cloud endpoints.

## Answer

There are shared bounds, failure records and safe-stopping paths, plus useful
recovery for explicitly reported raw HTTP output-token cutoffs. There is not a
complete uniform automatic recovery path for all input/output cap failures.
The run's local lane used Anthropic HTTP, while cloud used Codex app-server;
lane names alone do not determine adapter behavior or physical hosting.

## Issues demonstrated by the run

1. Agent history packing and runtime serialized-message sizing disagree. The
   93,391-byte estimate produced 96,529 bytes against a 96,000 allowance. Mandatory
   messages would fit, so this was an avoidable optional-history overflow.
2. Known local input rejection has no automatic context-rebuild path. It pauses
   the driver even when a smaller valid context is available.
3. An ad hoc test bundle was absent from both the task grant and declared outputs.
   The scope guard correctly blocked that worker. The resulting pre-candidate
   uncommitted modules were retained but not handed to the replacement, which
   reconstructed them from the scaffold.
4. The replacement accumulated eleven malformed-response feedback turns and
   substantial source-write history. Worker validation increments logical steps
   and calls, but has no separate small invalid-response budget; the overall
   call/step limits still bound the run.
5. Evidence needs careful interpretation: piped test commands initially returned
   exit 0 while reporting test failures; the later final summary reports ten
   passing tests. Build success does not establish product completeness. The
   feature inventory remained uncertain after an incomplete read, and gameplay
   edits never completed publication or project acceptance.

## Current behavior by failure mode

### Input too large under configured limits

[KernelRuntime._dispatch](../src/polyinference/runtime/kernel.py) constructs
messages and measures `len(canonical(messages))` as a conservative token bound.
It rejects input exceeding the smaller of the context and operation input caps,
and rejects input plus requested output allowance exceeding the selected
endpoint's configured `max_context_tokens`. These checks run for both bindings
and both `ModelQuery` and `AgentJob`.

Rejection happens before provider submission. No user constraints are silently
removed. The failure is a plain non-retryable `EndpointError`, not a structured
input-overflow result with measured/required/optional sizes. The OS does not
compact or summarize context, split assignments, select a larger model, or
switch bindings. The calling agent's current partial history packing does not
rebuild after the rejection, so the bundled coding run pauses.

Configured limits are not discovered backend capacity. There is no backend
tokenizer or acknowledgement proving which full prompt was consumed. Native
Codex additionally adds protocol instructions, schema/tool declarations and
wrapping after the kernel's message sizing. A server that silently drops input
cannot be reliably detected from these preflight checks alone.

### Endpoint rejects input despite local preflight

[HTTPInference.rejected](../src/polyinference/runtime/inference.py) retains
bounded error facts. HTTP 400 is generic non-retryable `invalid_request`; there
is no context-size adaptation based on the provider error. An Anthropic
`model_context_window_exceeded` completion stop is rejected, but is classified as
a generic retryable `ModelResponseError` with reason `stop_reason`. The OS may
retry the same input once by default, then escalate; it does not shrink it.

This classification gap is distinct from a failure actually observed in the run:
the run's final rejected request was never submitted.

### Raw HTTP output-token cutoff

[HTTPInference.normalize](../src/polyinference/runtime/inference.py) recognizes
Anthropic `max_tokens`, chat `length`, Responses `incomplete` with
`max_output_tokens`, and Gemini `MAX_TOKENS`. It raises `IncompleteGeneration`
even when partial visible text happens to be valid action JSON. The OS retains
partial visible output, usage and stop facts as failed-response evidence, settles
known-stopped resources and never delivers that partial output as an executable
successful reply.

[ModelRetries](../src/polyinference/runtime/model_retries.py) deliberately avoids
unchanged OS retries for that classification. The bundled coding application's
[AgentServices.model_result](../src/polyinference/agent/services.py) issues up to
two linked replacement requests by default, asking for smaller complete JSON
(first below 4,096 bytes, then 2,048), with the same output-token limit. Budgets,
deadlines, recovery allowance and finishing reserves still apply. Exhaustion
escalates to pause. This applies to any role using raw `ModelQuery`, on either
binding, not to native `AgentJob`. This run's three raw output cutoffs successfully
used this recovery.

The replacement request appends feedback to the original context without
repacking it. A near-full input can therefore overflow during output recovery:
the prior investigation's fitting 95,719-byte message set becomes 96,327 bytes
when the actual first-recovery feedback is appended, against the same 96,000
allowance. This is an offline counterexample, not an event claimed in the run.

### Silent or incorrectly signalled output truncation

The chat-compatible adapter accepts `finish_reason=None` as well as `stop`.
If the endpoint omits a cutoff signal but returns nonempty text, normalization
can accept it. Application JSON/schema checks reject malformed replies and feed
errors back, but cannot establish completeness of silently cut content that still
matches the grammar. Likewise, `normalize` does not independently reject reported
`output_tokens` above the requested maximum; it relies on endpoint enforcement.

There is no universal way to infer a semantic cutoff from valid-looking text.
Reliable endpoint completion metadata and refusal to silently truncate input
are prerequisites for a strong end-to-end guarantee.

### Response byte caps

The caps have different meanings and paths:

- `max_model_response_bytes` defaults to 4 MiB. HTTP transport aborts reading an
  oversized body with `UnknownExecution`; it cannot establish termination merely
  from stopping the read. The kernel records uncertainty and retains ownership/
  capacity pending reconciliation rather than resubmitting blindly.
- `limits.max_output_bytes` is 256 KiB in the supplied run. After a successful
  model operation, `AgentServices.model_result` rejects oversized visible text
  with plain `ValueError("Model output exceeds cap")`. This check is in the
  coding application, not a universal kernel model-result check. It has no
  smaller-output recovery and can leave the OS effect successful while the
  application driver pauses.
- File/tool output truncation is separate. `files.read` returns `truncated`,
  byte offsets and `next_offset`; the agent can request subsequent chunks.
  Shell output has a truncation flag. Neither automatically proves a task's
  inspection or verification was complete.

### Cloud Codex app-server differences

[CodexAppServer.generate_job](../src/polyinference/runtime/codex.py) receives no
per-call output-token limit argument. Its `turn/start` request sends no such
limit; the kernel's 8,000-token accounting/reservation is therefore not an
adapter-enforced Codex generation cap. It does not normalize an output-token
stop into the same `IncompleteGeneration` recovery path.

The adapter requires a terminal turn and rejects missing messages or invalid
wrapped envelopes. A final reply over its byte cap produces known-stopped
`NativeJobStopped`; the generic OS may retry once only if no brokered effects
ran and other safety/budget conditions permit it. That repeats the job rather
than asking for a smaller reply. With brokered effects it does not retry blindly.
An exit/disconnect/timeout without terminal proof remains uncertain. The
subprocess also has a 1 MiB line-reader limit; an oversized notification can
interrupt reception before terminal proof. These byte/native protections are not
equivalent to the raw HTTP output-token fallback.

These are source findings and offline probes, not new native failures observed
in run 2de3d5c5ab9b. No claim is made about which output-limiting controls an
external Codex server might support beyond what this adapter currently sends.

## Ownership and repair direction, not implemented

The OS should report normalized size/termination facts consistently across
bindings and distinguish input overflow, output cutoff, complete-but-oversized
response and unknown termination. Final request preparation must account for
adapter-added context and expose the effective enforced generation limits.
The caller owns removal/summarization of optional history, task decomposition
and a smaller complete-response strategy, with bounded new intents and preserved
mandatory pins. Native continuation must respect already executed effects.
Changing the OS to understand coding assignments is unnecessary.

Genuinely oversized required inputs should produce a clear unsatisfiable request
instead of silent instruction loss. Neither blind retry nor silently moving
local work to a cloud endpoint is a general fallback. Both bindings need the
same contract and equivalent scenario coverage, with adapter-specific mechanisms.

## Verification

Read the actual kernel, HTTP/native adapters, retry manager, application context/
model-result paths, worker/senior validation, configuration and relevant tests.
Existing tests cover four raw cutoff formats, non-execution of partial JSON,
bounded recovery/replay and safe versus unsafe native retries. Their historical
pass counts were not rerun or claimed for this audit.

Ran a standard-library Python probe against AST-extracted actual source. It
confirmed rejection of reported cutoffs for all four HTTP formats; acceptance
of chat output lacking a finish reason; generic retryable classification of an
Anthropic context-window stop; acceptance when reported output-token usage
exceeds the requested cap; absence of a native output-token parameter in the
function and outgoing RPC; and the plain application byte-cap exception. All
six checks completed successfully. The first harness attempts stalled creating
a Windows event loop and were interrupted; the final in-memory coroutine probe
avoided event-loop creation and passed without network or tools.

A JavaScript reconstruction using the saved run messages and actual recovery
feedback established the 95,719 to 96,327-byte counterexample. This is new offline
analysis, separate from historical runtime outcomes. No live provider request,
run resume, repository implementation test suite, game change or repair was
performed. Documentation links, required fix-history sections and whitespace
were checked. Existing unrelated working-tree changes were left untouched.
