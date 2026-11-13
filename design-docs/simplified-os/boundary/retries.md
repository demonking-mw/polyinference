# Inference retry and model fallback

## Bounded inference retries

Updated 2026-10-23: implementation of the endpoint-testing split, superseding
blanket unknown-execution wording only for explicitly isolated generation-only work.
The OS executes generic transport retries and preserves facts; the agent chooses
semantic correction, decomposition, continuation and permitted extra retries.

model_call_retries is the native extra-attempt allowance (0–3, bare OS default 1;
fresh coding agent default 2). A caller may declare InferencePolicy through
runtime/inference-policy at version 1: additional_retries (0–3, default 0) and
replace_undelivered (default false). Native attempts precede caller-authorized
ones. Configured backoff/Retry-After, cancellation, finishing reserves, grants,
step/call/token/spend limits and the root deadline apply to every new intent.
Output adaptation shares the native/caller counters and root deadline; it does
not restart them. Explicit application recovery/grammar correction remain separate.

Received unusable output, transient service/rate-limit failures and proven
unsubmitted connection/admission failures qualify. Permanent input/auth/grant
failures do not. Native jobs require known termination and no brokered effects.
For unknown raw generation, caller consent alone is insufficient: the trusted
adapter must establish generation-only behavior. One undelivered generation per
lane may then be isolated. Its effect stays uncertain, holds physical capacity and
conservative token/spend allocations, and its logical delivery is discarded.
A replacement needs a free slot/reservation and remaining allowance/deadline;
a single-slot endpoint cannot manufacture capacity. A second unknown remains a
blocking barrier. Independent safe work can continue around isolated computation.
Tool/native/effectful unknowns keep the strict global barrier. Public uncertain()
returns blockers; include_isolated=True also exposes pending computation.

A late retrieved response or explicit termination evidence can settle physical
accounting, but never deliver a discarded answer. Resume attempts supported
receipt/status recovery for isolated queries without requiring it for unrelated
execution readiness. No partial streamed text or JSON can execute an action.

Endpoint.lifecycle explicitly selects SSE/buffered transport and connect, first
meaningful output, output-idle and total timings. Pings do not count as output.
The total logical budget includes preparation, queueing, retries and backoff,
capped by the original process deadline. Without lifecycle, legacy timeout_seconds
and strict uncertainty behavior remain. Cloud AgentJob endpoint timeouts follow the generic OS boolean
cloud_agent_timeout_interrupt (default false): false logs once and continues the
same physical job; true interrupts. Direct stdio reads and proxy HTTP transport
follow this policy. Original deadlines/cancellation, grants, holds and terminal
evidence remain authoritative. Raw queries and local agents keep their timeouts.
Profiles and bounded on-click warm-up belong to the testing application, with no
Git/check/coding prerequisite. GPU/token scheduling remains backend-owned.

model-retry/<root>/<attempt> retains its issued intent, absolute delay, source and
budget root; model-retry-outcome records native/caller counts and effective result.
inference-progress/<operation> exposes bounded elapsed/last-output/deadline facts.
Old physical results are never rewritten as proof of termination. Optional settings
are omitted when absent, preserving old canonical serialization; saved pins and
old runs are not silently opted into new behavior. See the
endpoint testing guide (`docs/guides/endpoint-testing.md`) for profiles,
configuration, fixture coverage and v1 limits.

## Availability model selection

Endpoint.retry_model is a generic caller-supplied OS option, absent by default.
The coding agent chooses its native-cloud default through default_retry_model;
no model identity or coding role is hard-coded into the kernel. Explicit agent
configuration supplies/overrides the OS preference. One confirmed provider availability
failure gets the same logical request retried once on the alternate, then X subsequent
invocations use it before primary is probed again. X defaults to seven in the OS and
agent input can override it. The original primary model/effort stay pinned. Selection,
counts and linked intents are durable per binding and share original authority,
admission, accounts and deadlines. This separate availability attempt does not
refill ordinary retries. See policy/configuration (`docs/guides/model-fallback.md`).

Terminal app-server model failure may retain a trusted same-thread continuation,
including completed tool results. The OS can resume that thread on the alternate,
deduplicating old callback IDs; it cannot blindly replay effectful work or infer
termination from lost transport. Task replacement, diagnosis, canonical memory,
source reuse and acceptance remain agent policy. Fresh simple-os/6 state is
required; original frozen runs remain on their original source/configuration.
