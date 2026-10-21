# Kernel and durable effect execution

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

KernelRuntime composes OS services and settles stable operation intents with retained execution evidence.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/kernel.py](../../src/polyinference/runtime/kernel.py) | Bootstrap, effect dispatch, authority/budget checks, settlement, publication and reconciliation. |
| [src/polyinference/runtime/adapter.py](../../src/polyinference/runtime/adapter.py) | Historical StandaloneRuntime compatibility alias. |
| [src/polyinference/runtime/__init__.py](../../src/polyinference/runtime/__init__.py) | Runtime package boundary; sprint policy stays in the agent. |

## Interface and ownership

Open KernelRuntime, install trusted application handlers/protocols and register
processes before dispatch. execute(original) follows retained OS retry outcomes;
individual attempts remain immutable. Generic publication invokes installed policy.

## Principles to preserve

- Replay returns settled evidence without duplicate execution.
- Unknown execution retains ownership/capacity and blocks new dispatch until reconciled.
- Every actual submission consumes its own real resource reservation.
- No coding-record names, verdict grammar or Git prerequisites enter generic policy.
- Open process/data-policy guarantees remain documented gaps, not claimed enforcement.

## Verification and related reading

[OS](../../tests/test_os.py), [runtime](../../tests/test_runtime.py), [recovery](../../tests/test_recovery.py)
and [general-agent](../../tests/test_runtime_general.py) fixtures.

[Runtime boundary](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md) · [Open gaps](../../design-docs/simplified-os/DESIGN_REVISIONS.md#open-implementation-gaps).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
