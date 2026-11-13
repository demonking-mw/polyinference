# Inference simulation design

<a id="sim-inference-ui"></a>
## SIM-02 — Opt-in inference pacing and fault modes — 2026-10-21

Status: implemented; verification recorded in `development-docs/FIXES.md#fix-0096`.
Implements FIX-0095's proposal (`development-docs/FIXES.md#fix-0095`) under the user's later explicit
implementation request. SIM-01 below remains the concurrency-only launch preset.

UI --sim-inference reveals normal, normal and buggy, and slow and buggy modes before
Start. The default selection is 30 shared output TPS, batch 2, bug rate 5%, with an
optional seed and advanced timing controls. Normal/no flag retain the original
AgentConfig/client path. Buggy/slow configs explicitly pin settings in the optional
application config subclass and reinstall only the local-lane adapter on recovery.
The selected batch beats legacy/environment capacity without altering defaults,
later launches, custom Anthropic fields, old state or ordinary default config pins.

The application adapter supplies virtual shared decoding, startup/prompt latency,
seeded speed/stalls, normalized transient/output failures and endpoint restart
cooldowns. The OS retains admission, budgets, grants, completion bounds, recovery
and uncertainty; its only addition is a generic operation-aware HTTP adapter hook
and cancellation-safe terminal invocation. Actual usage survives discarded output;
diagnostics distinguish decisions, applied faults, real provider facts and progress.

This is a buffered service approximation, not a GPU/KV/model-quality emulator.
Only new calls during cooldown fail; already submitted calls can finish. A seed
repeats decisions for the same operation IDs, not all concurrent wall timing. A
coordinator crash stays conservatively uncertain even if a simulator diagnostic
receipt exists. Full provider responses are retained as diagnostic artifacts with
the existing snapshot/storage limits; partial actions never execute.

Ownership/record schema: module guide (`docs/modules/inference-simulation.md`).
Controls/limits/recovery: usage (`docs/guides/sim-inference.md`) and
settings reference (`design-docs/simplified-os/AGENT_SETTINGS.md#optional-application-inference-simulation`).
Regression checks are in test_inference_simulation.py and the real UI script tests;
actual final counts and environment limits belong in FIX-0096.

<a id="sim-batch-ui"></a>
## SIM-01 — Launch-scoped Claude batch simulation — 2026-10-20

Status: implemented in `development-docs/FIXES.md#fix-0092` under the authorized queue.
The original design/required checks below are retained; actual fixture/live
verification is in that entry. Related research: `development-docs/FIXES.md#fix-0061`.
README identifies this file as the current-version issue tracker.

### Requested behavior and scope

`polyinference ui --sim-batch 2` should launch the usual UI with Claude Haiku as
the local inference stand-in, two local inference slots and capacity for two
workers. No custom JSON or environment export should be needed. The existing
Start run interaction remains; this flag does not invent an objective or bypass
project selection. The override belongs to this UI invocation: new runs created
by that server use it, while a later `polyinference ui` uses its normal config and
inherited environment. Do not write the flag into source defaults, user settings,
credential files, shell profiles or os.environ. Existing environment values remain
unchanged; absent the flag, their existing behavior remains supported.

Persist each created run's effective config in its existing config.json/export,
so diagnostics and exact-config recovery remain possible. This is historical
run evidence, not a preference to load for future launches. Opening old history
or --state must not rewrite its saved configuration or change old runtime pins.

### Findings and owning layers

- `cli.py:main` currently accepts ui --port/--config/--state, but no batch flag.
  `serve` constructs TestUI, whose configuration() reloads either a JSON config or
  greeting_config(); configure_run() then validates another merged dictionary.
- `agent/system_settings.py:ui_system_settings` supplies the complete default
  Haiku endpoint, max_inflight:1 and max_workers:1. `system_settings.py` defines
  Endpoint and generic limits. Its environment_capacity validator can overwrite
  local.max_inflight on every validation, including RuntimeConfig.system.
- `runtime/inference.py` already implements async HTTP and bounded Admission;
  kernel.open builds admission from endpoint limits. No GPU scheduler, Python
  thread pool, second API key or Message Batches integration is needed.
- Agent readiness and repository task-branch policy determine useful parallel
  tasks. Disabling task branches retains its one-editor rule. Setup, dependencies,
  senior queries, verification and acceptance retain their current ordering.

Place the flag/preset in CLI/UI and the coding application's adjacent settings
module. The OS continues to receive ordinary validated Endpoint/max_workers
values. Keep Claude defaults and coding workflow out of generic OS admission.

### Implementation design

1. Add optional ui-only `--sim-batch N` (default None). Accept integers 1..16,
   matching the smaller of max_workers' 16 and Endpoint.max_inflight's 32 limits.
   Reject zero, negatives, fractions and larger values with an argparse error.
   Thread the optional value through serve and TestUI as an instance attribute;
   preserve existing call signatures by adding an optional keyword parameter.
2. Reuse/extract a complete Haiku Endpoint factory next to ui_system_settings,
   used by both default UI configuration and the simulation preset. Default fields:
   protocol anthropic, base_url https://api.anthropic.com/v1, model currently
   claude-haiku-5-5, api_key_env ANTHROPIC_API_KEY, timeout_seconds 180,
   max_context_tokens 128000 and inference_location cloud. Recheck model support
   when implementing; no model/credential access has been tested in this task.
3. Resolve a fresh base configuration, then apply a pure, validated simulation
   overlay: worker binding local, max_workers=N, local.max_inflight=N and
   local.reserved_context_tokens=max(existing reservation,
   N * local.max_context_tokens). Preserve per-call input/output limits, real
   budgets, finishing reserves and configured senior/cloud provider behavior.
   For --config with an Anthropic local endpoint, clone its complete fields,
   preserving custom model, URL, credential reference, timeout and prices. For a
   non-Anthropic local endpoint, the explicit simulation flag selects the complete
   default Haiku factory instead. Announce the effective provider/model and slots
   so this replacement is visible. Respect other role bindings; a non-worker role
   already bound local will share that lane. Preserve relative-path resolution.
4. Explicit CLI selection must beat POLYINFERENCE_LOCAL_BATCH_SIZE, including a
   stale value of 1. Do not temporarily mutate the environment or edit config JSON.
   Use validation context to suppress only the legacy capacity environment overlay
   when resolving an explicit simulation preset, then validate the complete merged
   configuration. Thread this context through initial JSON/default construction
   and configure_run revalidation. Never pass local={max_inflight:N} as an endpoint:
   it loses required model and provider fields. Revalidate after complete-field
   updates rather than relying on model_copy(update=...) to perform validation.
   Treat RuntimeConfig.system as a view of resolved values; if that property is
   used, it must not reread the ambient capacity override and undo the selection.
   No serialized simulation flag or new generic runtime setting is required.
5. Apply the overlay consistently whenever that TestUI instance builds a fresh
   config: UI defaults, repository selection, Start run, effective-config display
   and per-run config persistence. Keep the unmodified base independent of the
   result. A second TestUI instance without the flag must have normal defaults.
   Show a concise launch message with simulated slots, worker cap and the remote
   nature of Haiku; two slots mean a maximum, not guaranteed two active requests.
6. Validate the complete effective config and a nonempty referenced API credential
   before starting a simulation run, with a sanitized actionable error if missing.
   Keep startup failure observable through the existing UI launch-error/export
   path; do not let an unhandled credential exception kill the server. Continue
   using load_saved_credentials before UI bootstrap (existing environment wins).
   Retain native Anthropic framing: POST /v1/messages, x-api-key,
   anthropic-version:2023-06-01, system outside messages, final user turn,
   model and max_tokens. stream:false permits concurrent requests. Keep the
   existing response classification, retries and credential redaction. No automatic
   billed generation is needed merely to open the UI. Valid config/credential
   presence cannot guarantee network, billing balance or account model access.

### Required acceptance and verification at implementation time

- CLI parsing and plumbing: omitted flag preserves behavior; 1, 2 and 16 reach
  TestUI; invalid inputs fail; --port/--config/--state continue to work.
- Launch isolation: construct a simulated manager and then a normal manager in
  the same interpreter; only the first has the override. Check no environment,
  input JSON, global defaults or old saved runs changed. Also exercise separate
  CLI launches. Preserve deliberate pre-existing environment settings.
- Precedence through the full startup path: with environment batch size 1,
  --sim-batch 2 must produce max_workers:2, local.max_inflight:2 and sufficient
  reservation in configuration(), configure_run(), saved config and kernel
  Admission. Cover absent/malformed stale environment values with an explicit
  valid flag, grouped JSON, complete Endpoint preservation and resolved system
  views; do not accidentally weaken ordinary no-flag environment validation.
- Provider startup regression: default flag path must construct the real
  HTTPInference adapter with mock transport while preserving its actual headers.
  Assert full URL, model, headers, payload and physical location; assert senior
  Codex settings survive. Cover custom Anthropic settings and non-Anthropic
  replacement. Missing/blank credentials and fixture 401/404/429 responses yield
  visible sanitized diagnostics, without treating retries as new worker capacity.
- Meaningful concurrency: use two independent scripted worker tasks and the real
  adapter/admission path with a blocking mock or local TCP fixture. Demonstrate
  two overlapping requests, no third concurrent request, independent histories,
  and a waiting third request admitted when either slot completes. Check token
  reservation release and existing uncertainty retention; do not require paired
  completion. Repeat the baseline with one slot. The greeting demo intentionally
  requests one small worker, so it cannot prove two-slot occupancy.
- Preserve Git no-task-branch serialization and dependency/verification ordering.
  Verify history/export records retain effective settings. Use existing focused
  UI, saved-credential, Anthropic, endpoint/admission and grouped-settings suites,
  add regressions for this behavior, and run the required checks for the actual
  patch. If credentials/network are available, verify the selected model with
  the Models API and run a bounded live two-request smoke check; report separately
  from fixture evidence. A 429 still means shared account limits, not bad wiring.
- Update README, codex-haiku-setup.md, the central settings reference and fix history
  with usage, precedence, invocation scope and simulated-versus-real batching.

### Research sources and limits

Official Anthropic references: [Messages](https://platform.claude.com/docs/en/api/messages/create),
[authentication](https://platform.claude.com/docs/en/manage-claude/authentication),
[Models API](https://platform.claude.com/docs/en/api/models/list),
[rate limits](https://platform.claude.com/docs/en/api/rate-limits) and
[batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing).
Messages are stateless, so histories remain caller-owned. Organization limits
are shared. Concurrent calls emulate admission/slot refill; they do not reproduce
local GPU contention, token-step batching, KV memory use, latency or throughput.

This task inspected the current CLI/UI/settings, provider and kernel paths and
existing regression sources. No implementation/configuration changed, no tests
were run, no credentials were read and no live provider calls were made. The
checks above are planned requirements, not completed verification.
