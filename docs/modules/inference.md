# Endpoint admission and provider adapters

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Raw inference and native tool-using jobs have different wire/effect behavior and share bounded admission.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/inference.py](../../src/polyinference/runtime/inference.py) | Async FIFO admission/reservations, prepared HTTP payloads, provider normalization, completion/usage/error facts. |
| [src/polyinference/runtime/codex.py](../../src/polyinference/runtime/codex.py) | Native app-server stdio jobs, broker callbacks, read-only input verification, bounded telemetry and optional query proxy. |

## Interface and ownership

HTTPInference supports chat/Responses/Anthropic/Gemini protocols. CodexAppServer
uses registered application schemas/instructions and explicit brokered tools;
CodexProxy forwards query-only work to a separately installed service.

## Principles to preserve

- Known-unsubmitted, confirmed stopped and unknown execution are distinct facts.
- Incomplete/unusable output must retain diagnostics/usage without executing partial content.
- Native permissions and observed source views matter more than prompt promises.
- Bound streaming telemetry without losing terminal/tool evidence.
- Native hard generation-token caps are unsupported; expose or strictly reject that requirement.
- Provider token/GPU scheduling is outside the OS.

## Verification and related reading

[Endpoints](../../tests/test_endpoints.py), [Anthropic](../../tests/test_anthropic.py),
[native events](../../tests/test_native_events.py) and [output limits](../../tests/test_output_limits.py).

[Provider setup](../guides/providers.md) · [Runtime boundary](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
