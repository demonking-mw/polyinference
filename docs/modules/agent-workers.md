# Worker/senior graphs and reply grammar

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Reusable application graphs turn model replies into development, reconciliation and assessment decisions.

| File | Responsibility |
| --- | --- |
| [src/polyinference/agent/worker.py](../../src/polyinference/agent/worker.py) | Worker phase transitions, actions, checks, validated task attempts and bounded grammar correction. |
| [src/polyinference/agent/senior.py](../../src/polyinference/agent/senior.py) | Senior submit/validate graph for structured planning and review proposals. |
| [src/polyinference/agent/prompts.py](../../src/polyinference/agent/prompts.py) | Application instructions, role grammar, constraints and truthful evidence rules. |
| [src/polyinference/domain.py](../../src/polyinference/domain.py) | Git policy, assignments, senior proposals and typed worker replies. |

## Interface and ownership

WorkerReply accepts actions, candidates, assessments or review requests. The
application validates it and issues explicit brokered operations. Native and raw
models receive application-owned schemas/instructions through the same OS boundary.
Worker scope recovery catches the public ports.WriteScopeError; it imports no
concrete workspace-state implementation merely to recognize the typed error.
Senior inputs include immutable check commands and bounded manifest/runner previews.
When a shared check needs preparation, check_preparations names its new owner;
every other assignment using that check must explicitly depend on that owner.
Invalid ownership/dependencies receive the existing bounded proposal correction.
An already prepared contract needs no extra task. Dependencies start only after keep.
Senior publication instructions distinguish in-place private uncertain candidates
from isolated provisional ones. Retained-source offers drive explicit resume_from
and bounded corrections for unavailable source or incomplete replacement grants.

## Principles to preserve

- Consecutive invalid replies consume a bounded correction streak; valid actions reset it.
- Partial/incomplete model output must never become executable actions.
- Product acceptance needs meaningful evidence; a build or candidate alone is insufficient.
- Preserve the full objective, declared outputs and write authority in worker inputs.

## Verification and related reading

[Transitions](../../tests/test_agent_transitions.py), [native worker](../../tests/test_native_worker.py),
[HTTP integration](../../tests/test_http_integration.py) and [incident fixes](../../tests/test_incident_fixes.py).

[Agent design](../../design-docs/langgraph-agent/README.md) · [Repository guide](repository.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.

## Integrated reliability branch (2026-10-26)

The integrated worker/senior protocol retains scope recovery and check-preparation
ownership, adds bounded diagnosis and exact-tree semantic completion, and pins
versioned module interfaces. Related implementation files:

- `agent/architecture.py` validates immutable interfaces and resulting dependency plans.
- `agent/review.py` supplies source/diff/check evidence and validates completion criteria.
- `agent/diagnostics.py` runs a bounded, read-only checking agent sharing the worker account.
- `agent/schema.py` compacts displayed schemas without changing their constraints.

See [worker recovery](../../design-docs/implementation/WORKER_RECOVERY.md) and
[progress monitoring](../../design-docs/implementation/PROGRESS_MONITORING.md).
Private in-place reports remain private until verified publication; a successful
fixture response is not live product verification.

Integrated source responsibilities:

- [src/polyinference/agent/architecture.py](../../src/polyinference/agent/architecture.py) implements versioned module contracts and dependency validation.
- [src/polyinference/agent/review.py](../../src/polyinference/agent/review.py) implements source-backed review and exact-tree semantic completion.
- [src/polyinference/agent/diagnostics.py](../../src/polyinference/agent/diagnostics.py) implements bounded read-only check diagnosis.
- [src/polyinference/agent/schema.py](../../src/polyinference/agent/schema.py) implements compact response schema presentation.
