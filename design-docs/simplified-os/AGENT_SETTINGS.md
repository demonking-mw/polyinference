# OS settings for agent developers

This is the consolidated reference for OS settings exported to agents.
The schema and generic defaults live in
[system_settings.py](../../src/polyinference/system_settings.py).
Wire resource types remain in [contracts.py](../../src/polyinference/contracts.py)
and command definitions in [execution_contracts.py](../../src/polyinference/execution_contracts.py);
the central schema uses those types, rather than separate configuration stores.

The bundled coding agent selects its OS defaults and UI preferences together in
[agent/system_settings.py](../../src/polyinference/agent/system_settings.py).
Workflow settings remain in [AgentConfig](../../src/polyinference/config.py).
There is no shared agent library. See the [runtime boundary](RUNTIME_BOUNDARY.md)
and [FIX-0058](../../development-docs/FIXES.md#fix-0058) for ownership and verification.

## Configure one system block

> **Edited 2026-10-20 because** accepted changes need one current authoring
> contract, while unresolved code behavior must remain visible. The
> [revision ledger](DESIGN_REVISIONS.md) explains optional services, static
> routing, capability limits and the deferred shared library. In particular,
> process-declared routing/classification/hard allocation, narrower process limits
> and paused-worker residency are not fully enforced today (U01–U04). A stored
> declaration is not proof that those constraints were validated.

Keep OS choices in one adjacent **system** block and workflow fields outside it.
All [agent examples](../../examples/agent.mixed.json) use this layout.
Python callers can pass the same dictionary as RuntimeConfig(system=...) or
AgentConfig(system=..., objective=...). The config.system property returns a
validated OS-only view.

~~~json
{
  "system": {
    "repository": "/absolute/path/to/project",
    "state_directory": "/absolute/path/to/fresh-state",
    "local": {"model": "served-model"},
    "cloud": {"model": "served-model"},
    "allowed_write_paths": ["example.py"],
    "context_policy": {
      "auto_deal_context": true,
      "auto_compaction": false
    },
    "inference_safety": {
      "output_recoveries": 2,
      "require_output_token_enforcement": false
    }
  },
  "objective": "Implement and verify the requested change."
}
~~~

This illustrates grouping, not provider installation or complete task setup.
A general agent supplies its own roles/protocols and uses bare RuntimeConfig
without requiring coding workflows, checks or Git.

Precedence is generic defaults, coding defaults when using AgentConfig, explicit
configuration, then **POLYINFERENCE_LOCAL_BATCH_SIZE** for local.max_inflight.
That environment override accepts 1–32 and is pinned at startup. Nested settings
objects are validated with their own defaults: an explicit object replaces the
application's default object rather than recursively merging its preferences.

Legacy flat input is accepted. A field cannot appear both in system and at top
level. Unknown fields and non-object system values fail validation. Persisted
model dumps remain flat for compatibility. The CLI resolves repository, state
and output paths relative to the JSON file's parent; direct Python callers use
their working directory.

Configuration, programs and prompts are pinned for a run. Use fresh state for
these changes; historical runs are not migrated by this implementation.

## RuntimeConfig: complete OS field inventory

These are **generic OS defaults**. Coding/UI overrides are listed below.
Counts and capacities are positive unless stated otherwise.

| Field | Default | Meaning / units |
| --- | --- | --- |
| repository | required | Workspace root; an artifact agent need not invoke repository operations. |
| state_directory | .polyinference | Durable records, artifacts, checkpoints and workspaces. |
| allowed_write_paths | [] | Exact repository-relative source grants, using POSIX paths. |
| closure_paths | [] | Additional relative inputs for workspace views. |
| checks | [] | Optional named command resources, defined below; acceptance stays agent policy. |
| local | required | Endpoint lane using the Endpoint fields below. |
| cloud | required | Second endpoint lane; names do not determine physical inference location. |
| role_bindings | {"default":"local"} | Agent role to lane; at least one role is required. |
| prepare_repository | false | Optional repository-provider preference; the coding agent implements setup. |
| output_directory | null | Optional output destination used by the coding application. |
| base_branch | null | Optional repository-provider baseline selection. |
| write_scope | explicit | explicit grants or project-wide grant selection with project; operations still need granted paths. |
| shell_execution | disabled | disabled, trusted or bubblewrap shell backend. |
| shell_fail_fast | false | Prefix shell scripts with Bash set -e -o pipefail to expose failing commands/pipelines. |
| max_workers | 2 | Active ordinary-driver cap, 1–16; separate from inference concurrency. Paused-worker residency remains open U04, not an implemented hibernation guarantee. |
| limits | defaults below | Pinned RuntimeConfig operation envelope. A narrower registered ProcessSpec limit is not independently enforced today; see U03. |
| run_token_budget | 64000000 | Parent token reservation/usage allowance. |
| control_token_reserve | 0 | Nonnegative token allowance protected for management processes; less than run budget. |
| run_spend_budget_microusd | null | Optional estimated run ceiling in millionths of a US dollar. |
| max_artifact_bytes | 134217728 (128 MiB) | Run artifact storage cap. |
| max_workspace_bytes | 67108864 (64 MiB) | Per-workspace storage cap. |
| max_workspace_total_bytes | 1073741824 (1 GiB) | Aggregate workspace storage cap. |
| max_queued_operations | 128 | Inference admission waiters per endpoint, 1–4096. |
| max_command_seconds | 300 | Repository/workspace helper timeout, at most 3600 seconds. Shell/check operations have their own bounded timeout arguments. |
| max_model_response_bytes | 4194304 (4 MiB) | HTTP transport-body cap and native terminal-message cap; transport cutoff without termination proof remains uncertain. |
| context_policy | defaults below | Optional input preparation/compaction preferences. |
| inference_safety | defaults below | Output recovery and capability requirements. |
| max_repeated_model_failures | 2 | Permanent-failure circuit threshold for the same pinned model intent. |
| max_model_recoveries | 2 | Nonnegative upper bound for caller recovery and, independently, OS output adaptation; separate counters. |
| model_call_retries | 1 | Extra settled transient-response/transport attempts, 1–3; excludes output cutoffs and uncertain work. |
| model_retry_delay_ms | 100 | Initial exponential retry delay, 0–60000 milliseconds. |
| model_retry_max_delay_ms | 60000 | Maximum retry wait, 0–3600000 milliseconds; original deadline also applies. |
| check_execution | disabled | Independently enables checks with trusted or bubblewrap. |

The former review_token_reserve spelling is an input alias for
control_token_reserve. New code should use the generic name.
Trusted execution runs host commands. Bubblewrap requires a compatible installed
Linux sandbox. Neither backend grants additional source paths.

## Endpoint: same schema on both lanes

| Field | Default | Meaning / units |
| --- | --- | --- |
| protocol | chat | chat, responses, gemini, anthropic, codex_app_server or codex_proxy. |
| base_url | http://127.0.0.1:8000/v1 | HTTP base including API prefix; direct app-server uses command. |
| model | required | Exact served model identifier. |
| api_key_env | null | Credential variable name, never the secret value. |
| command | ["codex","app-server"] | Native adapter executable and arguments. |
| max_inflight | 2 | Admitted concurrent requests/jobs, 1–32. |
| max_context_tokens | 32000 | Configured total input/output context allowance per request. |
| reserved_context_tokens | 64000 | Aggregate context capacity; must fit one maximum-size context. |
| readonly_snapshot_root | null | Proxy's separately configured exact read-only snapshot root. |
| brokered_tools | false | Native endpoint supports explicitly granted host callbacks. |
| inference_location | null | Explicit local/cloud physical location. Otherwise localhost chat/Responses is inferred local; other cases cloud. |
| timeout_seconds | 180 | Provider/job timeout, at most 1800 seconds and bounded by operation deadline. |
| estimated_microusd_per_token | null | Nonnegative token-price estimate for cloud spend admission; required for a configured spend bound on that cloud lane. |

Packing and compaction never reroute to another lane. Native app-server and proxy
cannot enforce a hard generation-token ceiling. Direct native preparation sends
size guidance, rejects detectable completed overages and reports the limitation.
The proxy passes the chosen output limit through HTTP but cannot certify native
internal work. **require_output_token_enforcement=true** rejects these adapters
before submission. HTTP token parameters rely on server enforcement; reported
overages are rejected.

## Limits and optional final reserve

These wire settings are referenced by system.limits. An explicit limits object
requires all non-optional fields; its default factory supplies this full envelope.

| Field | Generic default | Meaning / units |
| --- | --- | --- |
| max_steps | 2048 | Process operation count, including OS child/recovery operations. |
| max_model_calls | 512 | Process inference operation count, including compaction/recovery. |
| max_repairs | 0 | Application repair allowance; interpreted by the coding agent. |
| max_input_tokens_per_call | 24000 | Input allowance; current adapters conservatively account prepared UTF-8 bytes against it. |
| max_output_tokens_per_call | 4000 | Requested generation ceiling; see adapter limitations above. |
| max_total_tokens | 16000000 | Process token reservation/usage allowance. |
| max_output_bytes | 262144 (256 KiB) | Visible model/tool output bound; cut model output cannot become actionable success. |
| max_wall_time_ms | 3600000 | Process lifetime allowance in milliseconds. |
| max_api_spend_microusd | 0 | Estimated process spend ceiling; zero means no additional process spend ceiling. |
| cost_guarantee | estimate | enforced is rejected: adapters cannot certify provider-enforced dollar quotas. |
| final_phase_reserve | null | Optional finishing reserve with the fields below; must fit within totals. |

| PhaseReserve field | Coding default | Meaning |
| --- | --- | --- |
| reconciliation_model_calls | 2 | Calls protected for reconciliation. |
| assessment_model_calls | 2 | Calls protected for assessment. |
| publication_steps | 2 | Operations protected for publication. |
| cleanup_steps | 1 | Operations protected for cleanup. |

All four reserve counts are positive when supplied. Ordinary OS compaction and
recovery preserve finishing reserves; they gain no new calls, deadlines, grants
or token credit.

## Optional context policy

| ContextPolicy field | Generic default | Meaning / units |
| --- | --- | --- |
| auto_deal_context | false | Permit OS input transformations; off means measure/report/reject unchanged input. |
| auto_compaction | false | Also permit model summaries of explicitly compactable blocks; requires automatic handling too. |
| compaction_trigger | 0.8 | Proactive trigger fraction of input allowance, greater than 0 and at most 1. |
| compaction_target | 0.6 | Best-effort target fraction, greater than 0 and below trigger. |
| max_compaction_calls | 8 | Child inference intent allowance per parent, 0–32; zero prevents new summary calls. |
| compaction_output_tokens | 1024 | Requested tokens per child, capped by parent output allowance. |
| compaction_summary_bytes | 4096 | Maximum accepted UTF-8 bytes per chunk summary; joined summaries must be smaller than source. |
| recovery_headroom | 1024 | Desired conservative input headroom. Packing reserves at most 10% of cap; compaction targets this and its target fraction. |

Effective policy merges runtime defaults, then partial
ProcessSpec.extensions["runtime/context-policy"], then partial
OperationRequest.extensions["runtime/context-policy"]. These are host-agent
choices, not model-tool grants. Overrides cannot change routing, hard limits,
source authority or completion requirements.

| Mode | Configuration / agent responsibility |
| --- | --- |
| Manual | Both switches false. Agent manages memory, paging and decomposition; OS always checks overflow. |
| Packing | auto_deal_context=true, auto_compaction=false. OS omits eligible complete optional groups, oldest supplied groups first. |
| Assisted compaction | Both true. OS may also derive summaries above the pressure trigger. |
| Hybrid | Agent manages its own summaries/protected blocks and opts selected other blocks or requests into assistance. |

The service handles submitted ContextViews; it does not scan arbitrary memory
records in the background. Manual agents can opt particular requests into
assistance. There is no mandatory canonical-memory compactor.

Agents define each ContextPart:
- required=true, compactable=false: retain verbatim.
- required=true, compactable=true: retain representation; eligible data, summary
  or message blocks may be replaced with a derived summary.
- required=false: permit whole-block omission.
- call_id: keep tool-call/result groups together; a required member protects the
  group. Instructions and tool pairs are never summarized.

Compaction uses the same process, binding, grants and deadline with no tools.
Each child is a durable accounted intent. A summary-call failure is terminal for
that child, without a nested transport/output retry tree. Preparation can omit
eligible inputs or return overflow. Unknown effects stop submissions until
reconciliation. Large sources use fitting chunks within the call bound; there is
no recursive summary-of-summaries loop. If protected input still cannot fit, the
parent fails before provider submission.

Sources remain immutable artifacts. Summaries retain classification, source
lineage and data trust; retrieved data never becomes an instruction. Lossy
summaries do not prove semantic equivalence or task acceptance. Canonical memory
changes remain explicit agent decisions.

## Mandatory I/O safety and receipts

Effective input allowance is the minimum of ContextView.maximum_input_tokens,
Limits.max_input_tokens_per_call, and endpoint.max_context_tokens minus the
parent output reservation. Sizing covers the known final adapter payload,
including schemas, serialized messages, native instructions and recovery feedback.
It uses a conservative UTF-8 byte bound, not an exact provider tokenizer or proof
of hidden native-harness context. A stricter provider rejection becomes typed
input-overflow evidence instead of an identical retry loop.

Preparation records context-receipt/<operation_id>. Dispatched results expose
extensions["runtime/context-receipt"]:
- context_ref, prepared_context_ref, prepared_digest identify original/derived
  views and the adapter input fingerprint.
- policy, original_bytes, submitted_bytes, required_bytes, input_allowance,
  unit and pressure expose effective settings and measurements.
- omitted_refs, summaries, compaction_operations and intervened expose every
  intervention, source/summary links and charged child operations.

Records under context-prepared/, context-summary/ and context-call/ retain exact
derived views, reusable summary artifacts and child intents for inspection/replay.
Unfitting input returns a failed OperationResult with
extensions["runtime/io-error"]["category"] equal to input_overflow, its receipt,
and attempted-backend.submitted=false. Provider context rejection uses that
category with provider facts and submitted status. Host code receives the failure
independently of the oversized prompt. The agent can page evidence, select less
data, revise memory or decompose work before a new intent; protected constraints
are not silently deleted.

| InferenceSafety field | Default | Meaning |
| --- | --- | --- |
| output_recoveries | 2 | Smaller-response attempts, 0–3, also bounded by max_model_recoveries; zero returns the classified failure directly. |
| smaller_response_bytes | 4096 | Initial visible response size guidance, capped by max_output_bytes; next attempt halves it. |
| require_output_token_enforcement | false | Reject native adapters without a hard generation-token parameter before submission. |
| require_completion_metadata | true | Fixed true; cannot disable completion proof/cutoff rejection. |

Confirmed cutoffs, reported generation overages and completed oversized replies
remain failed observations. Their text is never an executed action or concatenated
result. Safe bounded recovery adds smaller-response feedback under the same
declared protocol, remeasures input, creates a new durable intent and charges
normal budgets. Original failures stay immutable; execute/replay projects the
effective result. Current generic feedback nevertheless mentions visible JSON
for arbitrary raw callers; U05 tracks that grammar leak. Disable output_recoveries
when that assistance is unsuitable; incomplete-output rejection still applies. Output-retry records expose lineage; an exhausted cutoff
exposes polyinference/incomplete-generation.

Missing completion metadata/unusable responses cannot become success; eligible
known-ended response failures use separate bounded response/transport retry.
Disconnects, timeouts or HTTP transport-body overflow without termination proof
retain uncertainty and occupied capacity. They need reconciliation, not blind
retry. Native jobs with brokered effects cannot use automatic smaller-response
replay. Grammar correction, meaningful output units and task acceptance stay
agent responsibilities.

## Optional command resources and coding preferences

Each checks entry has these fields:

| Check field | Default | Meaning |
| --- | --- | --- |
| name | required | Unique command resource name. |
| argv | required | Nonempty executable/argument list, without shell interpolation. |
| timeout_seconds | 60 | Positive timeout, at most 600 seconds. |
| output_paths | [] | Declared relative generated-output directories; tracked/granted source retains source authority. |

The coding agent's adjacent defaults select senior/cloud, worker/local and
specialist/cloud; enable repository preparation, shell fail-fast and automatic
packing; disable compaction; reserve 32000 control tokens; and use the envelope
above with max_repairs=2 and the finishing reserve above.
UI preferences in the same module select endpoints, grants, checks, one worker,
96000 input / 32000 output allowances and trusted shell/check backends. The Haiku
examples use the same allowances with 128000-token endpoint context envelopes.
The Anthropic adapter sends the OS output allowance as the Messages API's
`max_tokens`, so Claude generation and OS enforcement use the same 32000 ceiling.
Examples override these choices in their single system block.

Coding-only fields remain outside system: objective, repository_mode, git_policy,
dependency_prepare, senior_development_fraction, max_sprints,
max_senior_corrections and max_protocol_corrections. The last defaults to 3
consecutive malformed-reply corrections (0–16); valid replies reset the count.
The agent owns full evidence inspection, canonical memory and repository-aware
reuse of interrupted work through preserved_source_ref / resume_from.
Preservation never makes unfinished source an accepted commit.
