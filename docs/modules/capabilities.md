# Capability registration and tool ABI

Explicit typed descriptors connect trusted host handlers to process-granted operations.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/capabilities.py](../../src/polyinference/runtime/capabilities.py) | Pinned descriptor/schema/effect registry and granted native tool projections. |
| [src/polyinference/runtime/tool_contracts.py](../../src/polyinference/runtime/tool_contracts.py) | Argument schemas for optional file, check, shell and branch capabilities. |

## Interface and ownership

Trusted bootstrap registers a handler, input type, effect class and workspace
requirement. Direct calls carry the installed schema digest. Native callbacks
use the same grants and journaled subordinate effects.

## Principles to preserve

- Registration alone does not grant a process permission.
- Validate effect class, schema, typed arguments and workspace generation before handlers.
- A non-workspace capability must not receive invented file-view metadata.
- Pin descriptors across restart and reject changed definitions under the same identity.

## Verification and related reading

[Capability boundary](../../tests/test_capability_boundary.py) and [setup tools](../../tests/test_setup_tools.py).

Bootstrap guide (`design-docs/simplified-os/boundary/capabilities.md#bootstrap-and-the-capability-boundary`).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in `development-docs/FIXES.md`.
Follow documentation maintenance (`docs/maintenance.md`) in the same task.
