# Bounded OS model retries

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Generic safe inference retry and smaller-output adaptation filter eligible failures before application escalation.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/model_retries.py](../../src/polyinference/runtime/model_retries.py) | Durable retry chains, delayed attempts, authorization, output feedback and effective-outcome projection. |

## Interface and ownership

Each additional submission has a new linked intent and reservation. Backoff and
Retry-After remain bounded by original deadlines and budgets. The kernel retains
all failed/successful attempts; replay follows the stored effective outcome.

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
