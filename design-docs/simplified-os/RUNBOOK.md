# Simple OS v1: deployment and recovery

> **Edited 2026-10-20 because** later repository and I/O fixes supersede the
> original publication, private-copy and caller-recovery defaults. The
> [revision ledger](DESIGN_REVISIONS.md) records the reasons and unresolved
> contract gaps; this guide describes the current default and explicit legacy mode.

The CLI and existing test UI now use `KernelRuntime`. `StandaloneRuntime` remains
an import alias for agent integrations. The OS branch is `codex/simple-os-v1`;
main is reserved for the separate agent testing effort. Historical source graphs
and proposal fixtures remain preserved; later optional contract fields and their
synchronized schemas are recorded explicitly in the fix history. [Implementation decisions](IMPLEMENTATION.md) record the
audit answers and the newer private-failure policy.

## OS boundary and non-coding agents

`RuntimeConfig` configures the OS independently of the bundled coding agent's
`AgentConfig`. It accepts arbitrary role names bound to the available endpoint
lanes, and does not require an objective, acceptance checks, writable files or Git
initialization. `repository` supplies project identity and an optional file-capability
root; opening the OS does not import or initialize it.

An agent registers its own `ProcessSpec` with `runtime.processes.register(spec,
binding_ref, management=False)`, submits `ModelQuery` operations, and can finish
with artifact references using `runtime.processes.finish(process_id,
output_refs=[...])`. An empty result is also valid. It can use `start`/`wait` for
bounded drivers and terminal status. Neither file delivery nor the coding agent's
candidate/reconciliation/assessment protocol is required by the OS.

Native agents register their own output schema and workspace mode with
`runtime.register_agent_protocol(name, schema, workspace="snapshot", brokered=False)`.
The coding application's schemas are registered by `AgentServices`; the kernel
does not import or impose them. Optional file/Git/check capabilities remain available
to agents that need them. Cancellation and resource termination are OS operations;
closing a coding sprint's starts is policy installed by the coding application.
Use `runtime.workspaces.prepare_artifact_snapshot(snapshot_id, files)` to create
an immutable native input directory from file artifact references without a Git
revision. Native snapshot roots are issued by the host.

`Outputs` is an optional artifact-file delivery service. It records a destination
and baseline before work, validates every affected path before writing, preserves
binary data and executable modes, detects external changes, and records a durable
intent and receipt. Legacy isolated coding invokes it only after final acceptance. Default in-place
coding records its integrated output directly and does not need copy-back.
Other agents may return artifacts without invoking this service at all.

Known model failures can be recovered with `runtime.recover_model(failed_id,
new_request, reason)`. The OS requires a new identity, the same process scope,
confirmed termination, explicit provenance and remaining recovery allowance. It
rejects new operations after process termination, and cancellation while queued
prevents provider submission. Program-specific recovery after reconciliation is
an installed callback; the kernel does not interpret other agents' `app/run` data.

Regression coverage: `tests/test_runtime_general.py` executes HTTP and native
research agents through the OS and terminates them without coding tasks, checks,
file workspaces or a Git store. `tests/test_outputs.py` covers optional delivery,
conflicts and interrupted-write recovery.

### Automatic inference retry

The bare OS has one native extra attempt; fresh coding-agent configs choose two.
model_call_retries accepts 0–3; InferencePolicy.additional_retries (0–3) follows
that allowance with separate counters. Backoff/Retry-After, the root deadline,
budgets, finishing reserves, cancellation and grants remain binding. Output
adaptation cannot reset the shared counters/deadline. Grammar and semantic
correction remain application policy. Inspect model-retry/, its outcomes and
inference-progress/ alongside immutable effect records.

Optional endpoint.lifecycle enables explicit SSE timings and generation-only
replacement consent. A missing terminal never proves remote termination. An
isolated generation keeps capacity/budget and discards delivery; replacing it
requires spare capacity. Native jobs/tools/external writes remain strict. Old
saved endpoints without lifecycle preserve their legacy policy. See
[endpoint testing](../../docs/guides/endpoint-testing.md) and the
[settings reference](AGENT_SETTINGS.md) for current configuration and v1 limits.

## Deployment

Use Python 3.10+, Git and Bash on macOS, Linux or WSL. Install the pinned Python
environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install -e .
polyinference --help
```

On WSL, keep state and sources on the Linux filesystem and install Codex there.
Native Windows is outside this POSIX implementation (`flock`, process groups,
Bash). Linux may use `bubblewrap` for configured checks/scripts. On macOS those
commands require explicit `trusted` execution; trusted commands have host access.
The native Codex process uses its own read-only platform sandbox; writes and
commands go through the host broker. Dependency installation and model serving
remain deployment responsibilities.

Choose an existing provider example under `examples/`, then set the repository,
fresh state directory, objective, write grants, closure and check command. Paths
in configuration resolve relative to that JSON file. Existing source repositories
must be clean. New coding runs use the actual repository by default: the coding
agent resolves Git instructions and creates/selects the integration branch and
linked task worktrees. The OS attaches authorized directories and enforces grants;
it does not choose branches. See the [current boundary guide](RUNTIME_BOUNDARY.md#in-place-coding-repositories).

```bash
polyinference validate-config /absolute/path/to/agent.json
polyinference probe /absolute/path/to/agent.json --endpoint cloud
polyinference run /absolute/path/to/agent.json
# Or the existing test/inspection UI:
polyinference ui --config /absolute/path/to/agent.json
```

Raw API protocols are `chat`, `responses`, `anthropic` and `gemini`. Credentials
are environment-variable references, never tokens embedded in configuration.
For Codex, install and authenticate its CLI on the backend host (`codex login`),
then use `codex_app_server`, `command: ["codex", "app-server"]`. Coding bindings
require `brokered_tools: true`. Direct app-server is the proxy brief's supported
native fallback. Optional `codex_proxy` is restricted to read-only senior queries;
an opaque proxy is not accepted as a coding backend.

For a subscription-only bring-up, `examples/agent.codex.json` requires no raw API
key. A complete disposable live test is available as
`PYTHONPATH=src python scripts/smoke_os_codex.py --model YOUR_CODEX_MODEL`.
This makes real provider requests and retains its temporary source/state for
inspection. The model name must be available to the signed-in account.

## Concurrency and limits

Configured limits and capability grants do not implement every rich wire-contract
promise. Current conflicting process data policies/hard allocations, narrower
process limits, paused-worker residency and JSON-specific recovery feedback remain
[open implementation gaps](DESIGN_REVISIONS.md#open-implementation-gaps).
Documentation alignment does not approve ignoring those constraints.

`local` and `cloud` are routing lanes; either can represent a cloud endpoint.
They are independent only when they represent independently provisioned capacity.
If all roles share one limited endpoint/account, bind them to one lane so they
share its admission counter.

```bash
export POLYINFERENCE_LOCAL_BATCH_SIZE=4
polyinference run /absolute/path/to/agent.json
```

The environment override accepts 1–32 and pins `local.max_inflight` for the run.
For cloud API substitution in the worker lane, set its URL/model/protocol/key and
use `POLYINFERENCE_LOCAL_BATCH_SIZE=1`. A request is sent as soon as it fits; the
OS never waits to fill a batch. The model server owns actual continuous batching.

| Setting | Bound and lifetime |
| --- | --- |
| `max_workers` | Resident ordinary agent drivers; explicitly marked management processes remain independent. |
| `max_inflight` per endpoint | Submitted requests/native jobs until known termination; unknown work retains occupancy across restart. |
| `max_context_tokens` / `reserved_context_tokens` | Per-call input+output and aggregate active reservations; UTF-8 bytes conservatively bound input tokens. |
| `max_queued_operations` | Endpoint waiters (default 128), bounded also by each operation deadline. |
| `limits` | Per-process model calls, steps, wall time, output and mandatory final-phase allowances. |
| `run_token_budget` / `control_token_reserve` | Parent admission allowance and protected control-process portion (coding default 32,000 tokens; bare runtime default zero). `AgentConfig` also accepts the former `review_token_reserve` input spelling. |
| `run_spend_budget_microusd` | Optional estimated spend; requires explicit `estimated_microusd_per_token` for cloud bindings. |
| `max_model_response_bytes` | Transport/native-event output cap (default 4 MiB). |
| `max_artifact_bytes` | Retained content-addressed artifacts (default 128 MiB). |
| `max_workspace_bytes` / `max_workspace_total_bytes` | Individual code copies (64 MiB) and aggregate workspace/snapshot files (1 GiB). |
| `max_command_seconds` | Trusted Git/merge command deadline (default 300 seconds). Checks/scripts have their own finite bounds. |

Actual provider-reported tokens replace reserved estimates once, atomically with
estimated spend settlement. Missing/unknown usage retains the conservative charge.
This is internal admission accounting, not an enforceable provider bill or
subscription quota. No automatic second provider is used on quota failure.
Physical RAM/VRAM placement and memory management are deferred by audit O02.

The verifier's mandatory model requests alternate with ordinary FIFO requests
when both wait. Verification spans merge, reconciliation, checks, assessment and
publication. The independent installation shell gate spans individual commands,
not direct Codex reasoning. A single bounded filesystem worker performs scans
and copies while the event loop continues handling model results and control.

## Failure and cancellation

An assessed failure creates a private commit parented on the captured shared
head, plus an immutable private report/receipt. It does not advance that head.
The same transaction closes new starts and captures every started worker.
Verification is released; the other workers finish their original assignments and
publish normally. Sprint review starts only after that drain. The senior can
reject the private candidate or schedule repair; it cannot accept it with `keep`.
> **Edited 2026-10-20 because** FIX-0040's real-repository integration must not
> fast-forward failed or unverifiable work into the user's checkout. The previous
> unconditional uncertain-publication statement applied to the older isolated path.

Default in-place mode also retains **uncertain assessments privately** and closes
starts for review. With task branches forbidden, non-successful edits remain
uncommitted in the current checkout. Legacy isolated mode still publishes an
uncertain assessment provisionally. An uncertain *execution* is different:
termination/effects are unknown, so reconciliation is required.

```bash
polyinference status /absolute/path/to/state
polyinference events /absolute/path/to/state --after 0
polyinference operation /absolute/path/to/state OPERATION_ID
polyinference cancel /absolute/path/to/state PROCESS_ID --reason 'Stop this assignment'
polyinference steer /absolute/path/to/state 'Replan with the revised requirement'
```

Cancellation is cooperative: finish the current effect, issue no subsequent
worker action, preserve attributable work, release proven-safe ownership, and
send the interrupted assignment to review. Cancelling the senior/controller uses
steering instead. It does not imply that a remote request has stopped.
Events are monotonic metadata changes committed with records, capped at the last
10,000 entries. Full evidence remains in the journal/artifacts. Polling status
and events is read-only; neither starts a model request.

## Recovery

The [runtime/agent wiring guide](RUNTIME_BOUNDARY.md) documents the current
capability and publication-policy registration order. New runs use kernel ABI
`simple-os/2`; existing run directories are not automatically migrated. Reinstall
the owning application's handlers and policy before issuing new effects after a
supported restart. Generic processes do not require the coding application.

One coordinator holds each state directory. Configuration and agent/program
identity remain pinned. The coding agent now has one exact predecessor migration
for run-level Resume, recorded under coding/resume-program-migration/; original
manifests/effects are preserved. This is not general historical-state migration.

Ordinary UI Resume or CLI resume CONFIG [--text instructions] first accepts a
durable intent, then automatically prepares recoverable execution under that
coordinator lease. Host receipts and completed query artifacts settle known work;
HTTP Responses can retrieve a result when its response ID survived. Native unknown
effects and synchronous HTTP work without recovery handles remain unsupported.
OS resume-preparation/ and application resume-progress/outcome records are separate.
Requests restore across server restart and instructions are applied once. A plain
failure is retained when automatic recovery cannot establish an outcome. The expert
procedure below remains for externally established termination evidence.

On restart, settled effects replay before checking transient workspace/permit
state. Durable publication and commit receipts settle recognized host outcomes.
Other submitted effects become `uncertain`; they retain reservations and logical
ownership. Unknown effectful/native/tool work blocks runtime dispatch until
reconciled. Explicitly isolated generation-only work instead retains physical
holds with discarded delivery; independent work can proceed within capacity.
Use uncertain(include_isolated=True) to include it in generic inspection.
Status and inspection remain usable. This
single-project safety boundary does not promise isolation between arbitrary hosted
programs or automatic remote cancellation. A disconnect or elapsed deadline alone never proves termination.

1. Stop the coordinator and preserve the whole state directory.
2. Inspect `status` and `operation`. Native journals include observed thread/turn
   identifiers. Establish provider termination and the absence of surviving host
   commands/descendants using provider and host evidence.
3. Save that evidence in a bounded text file, then explicitly attest:

   ```bash
   polyinference reconcile /absolute/path/to/agent.json OPERATION_ID \
     --confirm-stopped --evidence /absolute/path/to/termination.txt
   polyinference resume /absolute/path/to/agent.json
   ```

Reconciliation records a failed terminal result and evidence; it never repeats
the remote request. Once all unknown effects of the process are settled, it
releases capacity/ownership, restores the preserved development delta, marks the
attempt interrupted and returns the run to review. The original abandoned
integration generation remains attributable. Senior reviews interrupted work and
creates new assignments when needed. Never remove journal rows or lock records
to force redispatch.

Hard host crashes and arbitrary trusted background commands are not guaranteed
to be recoverable automatically. An unknown process may require manual provider
and host inspection. Avoid starting another run against the same external effects
until they are resolved. There is no distributed coordinator or automatic remote
cancel guarantee. Local command deadlines normally kill and join their process
groups; cancellation of an admitted filesystem mutation joins the I/O first.

## Retention and export

Keep complete state (records, checkpoints, artifacts and snapshots) together with
the actual project and its retained task worktrees. In-place Git history lives in
that project; legacy isolated state additionally owns private Git/copies.
No automatic pruning can
discard live/recovery evidence. After completion and reviewed export, archive or
remove the whole stopped run directory explicitly. Git objects and SQLite history
are retained for the finite run; workspace/artifact quotas do not bound Git's
entire historical store. Use an external disk quota when a total physical cap is
required.

`polyinference export STATE result.patch` exports initial-to-provisional changes.
Check completion/review status before applying it. Failed private candidates are
excluded; their report's `final_code.commit_id` can be inspected with
`git -C PROJECT show COMMIT` in an in-place run. Failed candidates have real
task branches/worktrees; inspect `coding/repository-summary` or CLI status for
their paths. Historical isolated runs instead use
`git --git-dir=STATE/repository.git show COMMIT`. Retain state for execution
evidence and worker worktrees for their uncommitted edits.
