# Optional context preparation

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The OS measures prepared adapter input and can derive a smaller view under caller-declared permissions.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/context.py](../../src/polyinference/runtime/context.py) | ContextService policy resolution, whole-group omission, compaction children, durable prepared views and receipts. |

## Interface and ownership

ContextPolicy resolves defaults, process preferences and request overrides. Async or
synchronous adapter measurements separate input tokens/provenance from serialized
bytes. Raw output reservation uses the enforced submitted cap; native hidden context
remains unmeasured. An opt-in same-provider counter never generates output; failure
retains a labeled conservative bound. See [measurement and configuration](../guides/context-measurement.md).
`auto_deal_context` permits optional-group omission; `auto_compaction` separately
permits eligible summaries. Hard bounds always apply, including manual mode.
The OS Memory / context inspector exposes retained originals, prepared views,
receipts and helper provenance without changing this service or canonical memory.

Summary helpers inherit the effective parent lifecycle cutoff, including queue/
preparation time; they cannot extend a logical call by receiving a fresh timer.

## Principles to preserve

- Preserve required inputs, trust, whole tool groups and immutable originals.
- Omit optional groups by caller retention_priority, oldest on ties; do not rank task meaning.
- Enforce independent token and byte ceilings; admission reserves measured/bounded tokens.
- Replayed preparations must retain both their wire digest and measurement provenance.
- Canonical memory semantics and compaction eligibility belong to the agent.
- Summary children use the same binding/grants/budgets and no recursive recovery tree.
- Prepared bytes do not prove provider submission; receipts retain provenance.
- Required-only overflow stops safely with retained state.

## Verification and related reading

[Context safety](../../tests/test_context_safety.py), [four-repair regressions](../../tests/test_four_repairs.py)
and [model retries](../../tests/test_model_retries.py).

[Settings/modes](../../design-docs/simplified-os/AGENT_SETTINGS.md) · [Memory report](../../development-docs/memory-implementation-report-2026-10-20.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
