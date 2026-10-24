# Test suite

[Developer onboarding](../dev-readme.md) · [Check commands](../docs/testing.md) · [Modules](../docs/modules/README.md)

Offline fixtures use disposable repositories and transports. Tests are evidence
for specific guarantees; live providers, physical scheduling and sandbox behavior
need separately stated checks. Update affected docs and FIXES.md with every fix.

| Module | Coverage responsibility |
| --- | --- |
| [conftest.py](conftest.py) | Shared runtime/agent configs, repositories and transport fixtures. |
| [test_agent.py](test_agent.py) | Coding orchestration and acceptance. |
| [test_agent_transitions.py](test_agent_transitions.py) | Validated attempts, retained long notes and replacement/replay. |
| [test_anthropic.py](test_anthropic.py) | Anthropic wire framing, payload limits and response handling. |
| [test_capability_boundary.py](test_capability_boundary.py) | Typed grants/ABI, native callbacks and non-coding programs. |
| [test_context_safety.py](test_context_safety.py) | Prepared bounds, context modes, compaction and grouped settings. |
| [test_contracts.py](test_contracts.py) | Packaged wire/schema invariants. |
| [test_costs.py](test_costs.py) | Usage/pricing estimates and aggregation. |
| [test_endpoints.py](test_endpoints.py) | Endpoint transport, admission, routing and concurrency. |
| [test_history.py](test_history.py) | Shared snapshot archives, retention and failure isolation. |
| [test_http_integration.py](test_http_integration.py) | Complete coding workflow over real local HTTP fixtures. |
| [test_in_place_repository.py](test_in_place_repository.py) | Git setup, verified integration, concurrent/serial worktrees and source reuse. |
| [test_inference_simulation.py](test_inference_simulation.py) | Opt-in/normal parity, TPS sharing, faults/cooldowns, usage, durable replay, cancellation/deadlines and real coding runs. |
| [test_incident_fixes.py](test_incident_fixes.py) | Incident-derived lifecycle, provider and recovery regressions. |
| [test_inference_lifecycle.py](test_inference_lifecycle.py) | Split UTF-8/SSE terminals, heartbeat/idle/total deadlines, native/caller quotas, shared adaptation allowance, physical holds, late-result fencing, generic probes and real loopback streaming. |
| [test_model_retries.py](test_model_retries.py) | Durable bounded retries, accounting and recovery composition. |
| [test_native_events.py](test_native_events.py) | Bounded native telemetry and terminal evidence. |
| [test_native_worker.py](test_native_worker.py) | Native brokered coding phases and source authority. |
| [test_os.py](test_os.py) | Kernel resources, effects, publication and replay. |
| [test_output_limits.py](test_output_limits.py) | Completion/cutoff classification and bounded smaller-output recovery. |
| [test_outputs.py](test_outputs.py) | Explicit artifact delivery, conflicts and interrupted recovery. |
| [test_resume.py](test_resume.py) | Generic automatic preparation, Responses/receipt recovery, predecessor compatibility, exactly-once steering, multi-worker source and restart activation. |
| [test_recovery.py](test_recovery.py) | Persistent restart, known/uncertain effects and explicit recovery. |
| [test_regressions.py](test_regressions.py) | Adversarial workflow, drain/replan and incident schedules. |
| [test_runtime.py](test_runtime.py) | Runtime tools, scopes, cancellation and effect settlement. |
| [test_runtime_general.py](test_runtime_general.py) | Non-coding/artifact-only HTTP/native lifecycles and generic operator resume signals. |
| [test_saved_credentials.py](test_saved_credentials.py) | Data-only private key loading and environment precedence. |
| [test_setup_tools.py](test_setup_tools.py) | Setup/check selection, durable task-start/quota accounting and bounded coding tool behavior. |
| [test_sim_batch.py](test_sim_batch.py) | Invocation-only UI simulation, CLI/precedence, provider framing, admission/refill, saved settings and startup failures. |
| [test_tool_environment.py](test_tool_environment.py) | Private homes/caches and command cleanup. |
| [test_ui.py](test_ui.py) | UI launch/project picker/API/export/default settings and run-level Resume with both repository providers and durable recovery rejection. |
| [test_ui_agents.py](test_ui_agents.py) | Coding task/review/history projections. |
| [test_ui_frontend.py](test_ui_frontend.py) | Python wrapper invoking supported Node frontend checks. |
| [test_ui_os.py](test_ui_os.py) | Generic OS snapshot/inspection projections. |
| [test_user_briefs.py](test_user_briefs.py) | Durable notifications and evidence-based senior briefs. |
| [test_workspace_outputs.py](test_workspace_outputs.py) | Declared output/source precedence and dependency environments. |
| [ui_start.test.cjs](ui_start.test.cjs) | UI JavaScript launch/snapshot/inspection, direct Resume, optional persistent instructions, request replay, progress, guards and stale replies. |

Documentation-tool regressions have their own feature guide:
[test_project_docs.py](test_project_docs.py), described in
[documentation tooling](../docs/modules/documentation.md).

Run only appropriate checks, record actual results/limits, and keep historical
results separate. Follow [documentation maintenance](../docs/maintenance.md)
before finishing, including affected guide/settings/navigation updates.
