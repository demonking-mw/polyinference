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
