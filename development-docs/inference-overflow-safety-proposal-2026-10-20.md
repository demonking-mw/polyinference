# Proposed OS input/output overflow safety

20 October 2026. Design proposal only, answering the user's implementation
question after [the cap audit](inference-cap-safeguards-audit-2026-10-20.md).
No implementation, configuration, tests or generated game files changed.
This proposal is not evidence that the safeguards below already exist.

Placement refinement: the later
[agent/OS responsibility proposal](agent-os-overflow-responsibility-proposal-2026-10-20.md)
places optional-context selection and adaptive response loops in an optional
shared agent library. Its minimal OS contract supersedes the placement of those
algorithms in the OS described here; the execution-safety requirements remain.

## Contract and ownership

Use one generic overflow contract for raw and native inference on both bindings.
The OS prepares and bounds requests, normalizes completion/size/termination facts,
retains evidence and coordinates bounded recovery. It does not decide coding
scope, invent product success criteria or choose which user requirements matter.
An application registers its permitted context-reduction policy and a small host
recovery handler using the ordinary generic process boundary.

The recovery handler is host code, not another invocation containing the oversized
prompt. It receives a bounded control event with references to the retained
request, phase/state, work and failure. It can return a smaller authorized request,
park the affected process or request a higher-level decision. The original large
input need not fit a model in order for the OS to report the failure.

Proposed outcomes distinguish `input_overflow`, `output_truncated`,
`response_too_large`, `completion_unverified` and `termination_unknown`. Include
the effective endpoint limits, measured size/unit or counting uncertainty,
required/optional contribution, whether submission occurred, termination/effect
certainty, and artifact references. These are proposed application-independent
resource facts, not coding-specific error messages.

## Input overflow flow

1. **Prepare before measuring.** The selected adapter constructs the complete
   immutable request, including protocol instructions, schemas and tool
   descriptors. Measure that prepared representation using backend-aware token
   counting where available, otherwise an explicit conservative bound including
   adapter overhead. Dispatch the same prepared request. Never silently describe
   a byte estimate as exact provider-token usage.
2. **Reserve headroom.** Fit input plus output allowance, request framing and
   recovery-feedback allowance within the endpoint's effective context window.
   Check request-byte and operation limits independently. Expose effective
   capacity to the caller; configured capacity is not automatically verified
   backend capacity.
3. **Reduce authorized optional context.** Under a caller-registered policy,
   the OS can drop whole optional groups deterministically, retaining tool
   call/result pairs and mandatory constraints. The policy identifies protected
   current-phase data, priorities and permitted omission. Store the omission
   manifest; do not silently truncate text or summarize mandatory instructions.
   Semantic summaries or task decomposition come from the caller's handler.
4. **Re-measure.** Submit only after the final request fits. Recovery feedback
   must participate in this same packing path rather than being appended later.
5. **Report an unsatisfiable request.** If required context alone cannot fit,
   submit nothing. Deliver the small control result to the host handler/supervisor.
   Preserve the original inputs and process state for paging, decomposition or an
   explicitly authorized larger endpoint. Do not silently move local data to
   cloud inference. Affect only the process/operation whose request cannot fit,
   unless shared-effect uncertainty requires a broader stop.

An actual provider context-length rejection follows this same classified flow.
Do not repeatedly submit unchanged oversized input. Require deployments to disable
silent prompt truncation; if consumption/completion cannot be verified, expose
that limitation rather than claiming an end-to-end guarantee.

## Output truncation flow

1. **Enforce the declared generation limit.** Each adapter declares whether it
   can enforce the requested per-call output limit and supplies its actual native
   parameter. If it cannot, reject requests requiring that guarantee before
   dispatch or expose an explicitly selected estimate-only mode. Do not claim
   the native adapter enforces the raw HTTP cap when it does not send one.
2. **Require completion evidence.** Normalize provider/native cutoff signals.
   Missing/contradictory completion metadata is unverified completion, not a
   successful executable reply. JSON/schema validation is also required, but
   valid JSON alone is not proof that a signalled cutoff completed.
3. **Reject the incomplete unit.** Retain bounded partial visible text and usage
   as evidence, but do not execute actions or publish a result from it. Previously
   completed brokered effects remain recorded and must not be repeated.
4. **Run bounded recovery.** For known-stopped, effect-free raw calls, invoke the
   caller's registered smaller-response strategy and submit a new linked intent.
   Default to at most two adapted attempts, subject to the same budgets, deadline
   and finishing reserves. Keep the hard output cap; ask for a smaller complete
   unit or use an application-declared chunk protocol. Repack the entire input
   including feedback. Never splice arbitrary truncated JSON into a tool call.
5. **Resume native work only from settled effects.** A native job that already
   ran tools needs a caller continuation from its retained state, not a blind
   restart. A known-stopped failure before effects can use the effect-free path.
   Exhausted adaptation parks the affected process with an actionable reason;
   it does not erase work or fabricate success.
6. **Treat byte overflow separately.** A fully received, confirmed-complete but
   oversized reply can use a smaller-response recovery classification without
   executing its content. If stopping the stream/read does not prove provider
   termination, classify uncertainty, attempt cancellation and await confirmation.
   Retain capacity/ownership until reconciliation; do not resubmit blindly.

## Verification required before calling this implemented

Exercise the same behavioral matrix on both bindings and every supported raw/
native adapter: exact-fit and near-limit prepared inputs; quote/newline-heavy
history; required-only overflow; provider context rejection; missing/false
completion metadata; valid-looking JSON with a cutoff; oversized received text;
transport overflow without terminal proof; output feedback pushing input over its
cap; native failure before and after brokered effects; recovery exhaustion,
cancellation, restart and replay. Assert no mandatory input loss, no partial action
execution, no duplicated effects and no budget/reserve reset.

This design was checked against the current
[runtime/agent boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md) and
the prior audit. Only documentation structure, links and whitespace were checked
for this proposal. No code, provider behavior, tests or run were executed to
validate implementation of the proposed contract.
