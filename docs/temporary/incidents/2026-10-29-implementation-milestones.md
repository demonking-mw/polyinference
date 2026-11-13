# OS implementation milestones

## I/O safety implementation completed — 2026-10-20

The OS/agent fixes following run 2de3d5c5ab9b are implemented and locally verified.
See FIX-0058 through FIX-0060 (`development-docs/FIXES.md#fix-0058`) and the
verification report (`development-docs/io-safety-verification-2026-10-20.md`) for checks, capability
limits and fresh-state requirements. The shared agent library remains deferred.
All exported settings are documented in the
central OS reference (`design-docs/simplified-os/AGENT_SETTINGS.md`).


<a id="endpoint-testing-v1"></a>
## Endpoint lifecycle implementation v1 — 2026-10-23

The earlier portable testing proposal (`docs/temporary/incidents/2026-10-23-portable-endpoint-design.md#portable-endpoint-testing`) and
agent/OS split (`docs/temporary/incidents/2026-10-23-portable-endpoint-design.md#endpoint-agent-os-split`) now have an initial implementation.
The current usage/settings guide (`docs/guides/endpoint-testing.md`) is the
behavioral reference; earlier design paragraphs remain evidence of the proposal.
OS-native retries now precede optional caller-authorized retries, with separate
durable counters and one shared original logical deadline. Output adaptation
cannot reset them. The fresh coding agent selects two native retries; the UI adds
one caller retry and a smaller 4096-token raw target inside the 32000 hard ceiling.

SSE Anthropic/chat/Responses assembly, meaningful-output watchdogs, explicit local
and small-cloud timings, cause/stage diagnostics, retained physical holds,
discarded-delivery fencing and a bounded on-click generic probe are implemented.
One-slot endpoints can expose isolated pending computation but cannot submit a
replacement while it holds the slot. A second unknown remains blocking. No native
or tool uncertainty is relabelled safe. New settings are opt-in for old/custom
configurations; saved runs are not automatically migrated.

V1 limits: Gemini has explicit buffered transport; unsupported SSE is not silently
resent. Raw query isolation trusts the built-in adapter only, excluding native
jobs and simulator subclasses. The existing TPS simulator still paces completed
responses and does not prove actual provider streaming/GPU behavior. Probe
admission serializes within one UI manager, not across independent runtimes.
Unsupported status/cancel APIs cannot resolve or reclaim pending computation.
See `development-docs/FIXES.md#fix-0117`, `development-docs/FIXES.md#fix-0118` and
`development-docs/FIXES.md#fix-0119` for actual verification and boundaries.

## Central OS constants/defaults — 29 October 2026

`development-docs/FIXES.md#fix-0161` centralizes generic values and exposes operational
controls under `system.tuning`. See usage (`docs/guides/os-tuning.md`) and the
per-file inventory (`docs/os-config-inventory.md`). Historical state requires
its original frozen source/configuration. The completed Minecraft run's corrected
OS audit and verification receipts are delivered in
`/home/marven/Downloads/polyinference-minecraft-test-2026-10-28/`.
Native-output classification/evidence handoff and gameplay remain outside this fix.
