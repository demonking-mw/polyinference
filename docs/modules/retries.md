# Bounded OS model retries

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Generic safe inference retry and smaller-output adaptation filter eligible failures before application escalation.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/model_retries.py](../../src/polyinference/runtime/model_retries.py) | Durable retry chains, delayed attempts, authorization, output feedback and effective-outcome projection. |
| [src/polyinference/runtime/retry.py](../../src/polyinference/runtime/retry.py) | Registered response validation, physical attempt records and bounded caller replacement windows. |

## Interface and ownership

Each additional submission has a new linked intent and reservation. Backoff and
Retry-After remain bounded by original deadlines and budgets. The kernel retains
all failed/successful attempts; replay follows the stored effective outcome.
The OS-native allowance precedes InferencePolicy.additional_retries. Durable
source/counters distinguish native from caller permission. Both share the root
logical deadline and retry allowance across output adaptation. A new application
recovery still has its separate existing authorization; it cannot alter old intents.
One consenting generation-only unknown may be isolated with its physical holds;
replacement requires free capacity and another unknown stops the chain. See
[profiles and limits](../guides/endpoint-testing.md).

## Principles to preserve

- Never blindly retry uncertain execution or native jobs with brokered effects.
- OS retry allowance is distinct from explicit application recovery allowance.
- Remeasure feedback; preserve routing, grants, trust, limits and finishing reserves.
- Grammar repair/task decomposition remain caller policy. Generic smaller-output
  feedback limits visible response bytes while preserving the caller's declared protocol (FIX-0085).

## Verification and related reading

[Retry regressions](../../tests/test_model_retries.py), [output limits](../../tests/test_output_limits.py)
and [incident recovery](../../tests/test_incident_fixes.py).

[FIX-0047](../../development-docs/FIXES.md#fix-0047) · [Boundary retries](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md#bounded-inference-retries).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.

## Integrated reliability branch (2026-10-26)

`runtime/retry.py` adds caller-registered response validation, durable physical
attempts and an optional owning-agent replacement window. `inference_retry` is
coding-app configuration; bare RuntimeConfig processes retain their existing
transport retry flow. Confirmed malformed replies consume this response allowance;
exhaustion does not restart it through ModelRetries. Transport/output recovery
retains its separate existing guards. Unknown effects are never blindly retried.
Physical attempts share model-call, token and inherited recovery accounts.

Physical-attempt indexes retain admission ownership across restart. Prepared
bookkeeping is not termination evidence. If a later response-repair attempt is
unknown, an older completed root response cannot settle it; explicit provider/host
reconciliation is required and releases only attested physical holds.

Interruption while waiting for a response replacement preserves the prior settled
physical receipt and any accepted replacement. Replay can continue that bounded
repair without resubmitting the completed attempt or charging it again.

Inspect `inference-attempt/<operation>/<index>` for physical outcomes and
`retry/<operation>` for the replacement window. `offer_retry` accepts only the
owning process, preserves required context pins, role/phase/schema/grants and
cannot expand context authority. Without an accepted replacement, the bounded
retry uses the original request. This response policy is distinct from transport
retry and worker grammar correction; see [agent settings](../guides/agent-reliability.md).

`register_response_repair(schema_ref, callback)` optionally installs a synchronous
owning-application feedback builder. The waiting record is durable before it runs;
the existing deadline/window and `offer_retry` authority checks still apply.
Callback errors are separate diagnostics and cannot change an execution outcome.
The coding agent pins bounded validation feedback and the current phase, retaining
all required inputs. No extra model call or recursive repair allowance is added.
