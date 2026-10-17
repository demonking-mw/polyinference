# Simple OS v1: deployment and recovery

The CLI and existing test UI now use `KernelRuntime`. `StandaloneRuntime` remains
an import alias for agent integrations. The OS branch is `codex/simple-os-v1`;
main is reserved for the separate agent testing effort. Source design schemas and
graphs remain frozen. [Implementation decisions](IMPLEMENTATION.md) record the
audit answers and the newer private-failure policy.

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
must be clean. The OS imports their baseline into an isolated Git store; it does
not change source files, branches or refs.

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
| `max_workers` | Started coding drivers, including setup and waiters; senior control remains independent. |
| `max_inflight` per endpoint | Submitted requests/native jobs until known termination; unknown work retains occupancy across restart. |
| `max_context_tokens` / `reserved_context_tokens` | Per-call input+output and aggregate active reservations; UTF-8 bytes conservatively bound input tokens. |
| `max_queued_operations` | Endpoint waiters (default 128), bounded also by each operation deadline. |
| `limits` | Per-process model calls, steps, wall time, output and mandatory final-phase allowances. |
| `run_token_budget` / `review_token_reserve` | Parent admission allowance and protected planning/review portion (default 32,000 tokens). |
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
An uncertain assessed verdict still publishes provisionally, closes starts and
requires review. Uncertain *execution* is a different condition: termination is
unknown and recovery is required.

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

One coordinator holds each state directory. The effective configuration and
agent/program version are pinned; older placeholder runs require their original
implementation. There is no state migration in v1.

On restart, settled effects replay before checking transient workspace/permit
state. Durable publication and commit receipts settle recognized host outcomes.
Other submitted effects become `uncertain`; they retain reservations and logical
ownership. A disconnect or elapsed deadline alone never proves termination.

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

Keep complete state (records, checkpoints, artifacts, workspaces, snapshots and
private Git) for active, unresolved or recoverable runs. No automatic pruning can
discard live/recovery evidence. After completion and reviewed export, archive or
remove the whole stopped run directory explicitly. Git objects and SQLite history
are retained for the finite run; workspace/artifact quotas do not bound Git's
entire historical store. Use an external disk quota when a total physical cap is
required.

`polyinference export STATE result.patch` exports initial-to-provisional changes.
Check completion/review status before applying it. Failed private candidates are
excluded; their report's `final_code.commit_id` can be inspected with
`git --git-dir=STATE/repository.git show COMMIT`. Retain the state if you need
private commits or recovery evidence.
