# Kernel and durable effect execution

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

KernelRuntime composes OS services and settles stable operation intents with retained execution evidence.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/kernel.py](../../src/polyinference/runtime/kernel.py) | Bootstrap, effect dispatch, authority/budget checks, settlement, publication and reconciliation. |
| [src/polyinference/runtime/resume.py](../../src/polyinference/runtime/resume.py) | Durable resume preparation/progress, completed response recovery and adapter recovery coordination without coding policy. |
| [src/polyinference/runtime/adapter.py](../../src/polyinference/runtime/adapter.py) | Historical StandaloneRuntime compatibility alias. |
| [src/polyinference/runtime/__init__.py](../../src/polyinference/runtime/__init__.py) | Runtime package boundary; sprint policy stays in the agent. |

## Interface and ownership

Open KernelRuntime, install trusted application handlers/protocols and register
processes before dispatch. execute(original) follows retained OS retry outcomes;
individual attempts remain immutable. Generic publication invokes installed policy.
prepare_resume accepts a retained intent under the runtime coordinator lease,
recovers host receipts/completed query artifacts or an adapter-retrievable response,
and records OS-owned resume-preparation/ readiness separately from agent progress.
Completion receipts store artifact references, not duplicate response bodies. Unknown work keeps reservations; strict effects block dispatch, while explicitly isolated query-only computation is separately accounted for;
unsupported recovery is a bounded failure, never an inferred remote stop.
Recovered accounting and application notification are restartable. Explicit Resume
also attempts status/receipt recovery for isolated generations without making them
blocking. Their original delivery remains discarded after physical settlement. Native jobs with
possible broker/host effects do not use the query-only recovery shortcut.
Trusted HTTPInference subclasses may implement generate_operation(request,
messages, max_output, prepared=...). This optional adapter owns its transport
timeout/service pacing inside the original operation deadline; normal clients retain
their old call path. Admission/grants/budgets/completion bounds still surround it.
terminal_call retrieves cancellation outcomes before settlement. The
[application simulator](inference-simulation.md) is one caller; the kernel imports
no simulation settings or provider-specific pacing policy.

## Principles to preserve

- Replay returns settled evidence without duplicate execution.
- Unknown tools/native/effectful execution retains ownership/capacity and blocks dispatch.
- Explicit caller consent can isolate one undelivered generation-only call per lane;
  physical holds remain, late delivery is fenced, and replacements need spare capacity.
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

## Integrated reliability branch (2026-10-26)

The kernel composes generic settlement/account lineage and read-only execution
observations through `runtime/lifecycle.py` and `runtime/progress.py`. The historical
adapter remains an import alias. No new OS dependency on coding-agent grammar or
Git policy is introduced. See [recovery](../../design-docs/implementation/WORKER_RECOVERY.md)
and [observations](../../design-docs/implementation/PROGRESS_MONITORING.md).
