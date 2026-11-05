# OS constants audit inventory

[Central configuration](guides/os-tuning.md) · [Runtime boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md)

The audit read every file in `src/polyinference/runtime/`, then the shared contracts,
configuration, ports, execution definitions, primitives and inspection/entry-point
consumers. This inventory distinguishes operational settings from protocol data;
ordinary numeric literals are not automatically safe deployment controls.
All generic values below have their canonical definitions in
[os_config.py](../src/polyinference/os_config.py); exported operational overrides
are under `system.tuning`. Existing public settings retain their names.

| File(s), relative to `src/polyinference/` | Audited result / setting ownership |
| --- | --- |
| `system_settings.py` | Existing runtime, endpoint, context, lifecycle, retry-model and inference-safety defaults and validation bounds reference the canonical file; resolved `tuning` is pinned. |
| `primitives.py` | Generic Limits defaults use canonical `DEFAULTS`; hash/JSON encoding and selected fingerprint fields are protocol. |
| `contracts.py`, `execution_contracts.py` | Caller retry/context defaults, distribution tolerance, diagnostic bounds and check timeout default/ceiling centralized. Wire enum tags, identifier scales and coding-only records remain contract/application semantics. |
| `workspace_contracts.py`, `ports.py`, `os_contracts.py` | Path/manifest/grant invariants and protocol signatures; coding compatibility exports are application-owned. No independent operational timers/buffers. |
| `runtime/storage.py` | Retention, event page default/max and SQLite busy timeout configurable; saved tuning inherited by independent writers. WAL/FULL, atomic transactions, digest paths and immutable keys are fixed durability/identity rules. |
| `runtime/exclusive.py` | Optional ownership-wait cap, standalone fallback default and lock poll interval centralized; omitted cap preserves runtime process wall-time. Lease keys, depth arithmetic and lock ordering are invariants. |
| `runtime/blocking.py` | Single serialized filesystem worker/gate protects copy and aggregate accounting; not a parallelism knob. Cancellation still joins mutation. |
| `runtime/commands.py` | Command read chunk and subprocess stream size centralized; total output/time bounds still supplied by caller. SIGKILL/process-group cleanup remains fixed. |
| `runtime/tools.py`, `runtime/shell.py` | List default/max, search pattern/line/match caps, shell length/default/max/argv, output chunks and sandbox system paths configurable. Source authority, expected hashes and replacement cardinality remain fixed. |
| `runtime/tool_environment.py` | Non-path tool environment defaults configurable; private paths, directory permissions, mount names and cleanup are host-issued invariants. |
| `runtime/tool_contracts.py`, `runtime/messages.py` | Shared shell schema ceiling and notification length centralized; tool IDs, effect classes and required schema fields remain ABI. |
| `runtime/processes.py` | Resume text/request-ID limits centralized and shared with CLI/UI. Initial counters, state names, deduplication, deadlines and one-driver rule remain structural. |
| `runtime/process_policy.py` | Classification ordering and static allocation enforcement are mandatory policy, not tuning. Actual limits already come from runtime config. |
| `runtime/progress.py` | Recent effect window configurable; observer/source identifiers and state projections remain protocol. |
| `runtime/context.py` | Headroom divisor, compaction reserve/chunk divisor/minimum and temperature configurable; existing compaction flags/ratios/call/token bounds remain public settings. UTF-8 repair and whole-group/trust rules are invariant. |
| `runtime/inference.py` | Queue/output and HTTP pool/keepalive/environment defaults unified; error/counter body caps, sanitized preview, Retry-After maximum, recovery polling, progress interval/precision, block-type count and Anthropic version configurable. HTTP statuses, token keys, credential redaction, no redirects/implicit transport retries and terminal semantics remain protocol/safety. |
| `runtime/inference_stream.py` | SSE framing, message tags and terminal facts; no operational default outside runtime config. |
| `runtime/codex.py` | Output/token defaults unified; event/recent/method/line buffers, error preview and shutdown grace configurable. Client identity centralized. RPC IDs, permission fences, telemetry filtering and provider usage parsing remain protocol. |
| `runtime/kernel.py` | cloud_agent_timeout_interrupt selects warning-only versus interrupting cloud AgentJob timeouts, preserving original deadlines, cancellation and resource ownership. Passes resolved tuning to record/checkpoint connections, primary/fallback clients and services; error/excerpt limits configurable. Diagnostic and pin version use one identity constant. Accounting, native overage classification and reconciliation logic unchanged. |
| `runtime/model_retries.py` | Backoff and shrinking factors configurable; retry allowances remain public settings. Original deadline, effectful-native no-blind-retry and alternate routing rules unchanged. |
| `runtime/model_fallback.py` | Existing endpoint fallback allowance/effort settings already explicit; no hidden operational limits. Native session/authority transfer rules fixed. |
| `runtime/retry.py`, `runtime/resume.py` | Error preview and response status-recovery timeout configurable; original request/resource/termination rules preserved. No retry unit-logic repair included. |
| `runtime/lifecycle.py` | Settled/fenced account lineage and hibernation rules; no additional operational default. |
| `runtime/outputs.py` | Existing configured output destination/storage bounds; modes/hashes/baseline conflicts and atomic publication invariants. |
| `runtime/workspace.py` | Ignore/exclusion rules, empty baseline, setup/publication Git identity, dependency/environment classification, command chunks and error preview centralized. Namespaces, generation IDs, Git modes and merge exit-code range are protocol. |
| `runtime/workspace_state.py` | Environment names, dependency filenames and requirements prefix/suffix configurable. Protected source wins; storage roots and safe link handling fixed. Historical constant imports remain views of canonical defaults. |
| `runtime/__init__.py`, `runtime/adapter.py` | Package/compatibility boundary only. |
| `ui_os.py`, `snapshots.py`, `ui.py`, `ui-monitor.js`, `ui.html`, `cli.py` | Inspector retention/activity/live-offline paging uses resolved tuning; control limits and check default use canonical values; resume text has no independent client cap. Application UI server defaults, fixture objectives, presentation constants and control retry policy stay application-owned. |
| `history.py`, `costs.py`, `ui_repository.py` | Archive retention, approximate price tables and project-picker limits belong to the test/viewer application, not OS execution. Reviewed, excluded from OS tuning. |
| `config.py`, `agent/system_settings.py`, `agent/repository.py` | Coding presets/workflow remain application-owned. Repository provider now consumes the resolved OS ignore rule rather than importing a frozen default set. |

The complete field/default/range catalog is generated in
[settings-schema.json](settings-schema.json). This change centralizes configuration;
it does not fix native cumulative-output failure classification, missing diagnostic
check evidence, agent stagnation, game defects or historical journal loss.
