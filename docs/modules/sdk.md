# Contracts and runtime ports

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The packaged boundary between agent programs and replaceable OS implementations.

| File | Responsibility |
| --- | --- |
| [src/polyinference/__init__.py](../../src/polyinference/__init__.py) | Package and graph/wire version identity. |
| [src/polyinference/contracts.py](../../src/polyinference/contracts.py) | Wire records for processes, contexts, effects, tasks and results. |
| [src/polyinference/workspace_contracts.py](../../src/polyinference/workspace_contracts.py) | Workspace/source/grant types and safe relative paths. |
| [src/polyinference/execution_contracts.py](../../src/polyinference/execution_contracts.py) | Optional named command/check resource definitions. |
| [src/polyinference/ports.py](../../src/polyinference/ports.py) | Structural protocols for records, artifacts, processes, workspaces and effects. |
| [src/polyinference/primitives.py](../../src/polyinference/primitives.py) | Canonical serialization, content digests, intent fingerprints and generic limits. |

## Interface and ownership

Applications call `RuntimePorts`; `KernelRuntime` is one implementation. Bootstrap
registers explicit capabilities/protocols. OperationPorts.prepare_resume(request_ref)
is the generic asynchronous execution-preparation boundary; caller-owned workflow
policy consumes its ready state and retained results. InferencePolicy is a generic caller declaration in runtime/inference-policy
(version 1): additional_retries and replace_undelivered. It grants no capacity or
termination proof. OperationPorts.uncertain() reports blocking effects; explicit
include_isolated=True also reports pending generation-only computation. WriteScopeError
belongs to ports; runtime.workspace_state retains a compatibility re-export.
Some shared wire types retain coding
records for compatibility; their presence does not make coding mandatory.

## Principles to preserve

- Stable identity pins the complete intent; changed arguments require a new intent.
- Providers, persistence and scheduling stay outside the port definitions.
- A general process can complete with arbitrary artifacts and no code/check/Git.
- Design fixture copies are provenance, not proof of implemented guarantees.

## Verification and related reading

[Contract tests](../../tests/test_contracts.py), [general-agent fixtures](../../tests/test_runtime_general.py)
and [capability boundary](../../tests/test_capability_boundary.py).

[Runtime boundary](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md) · [Design contracts](../../design-docs/langgraph-agent/README.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
