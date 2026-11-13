# Operator Resume, replay and compatibility

## Explicit operator resume signals

> Updated 2026-10-23 (FIX-0111): run-level Resume separates request acceptance
> from execution readiness; the former process-only frontend flow is superseded.

runtime/processes.request_resume records generic scoped or unscoped operator intent
and optional text. request_id deduplicates identical input. Explicit process
signals validate a paused noncancelled principal; unscoped signals need unfinished
execution. Acceptance can occur with unsettled effects and grants no execution
permission. It never interprets tasks, Git or coding acceptance.

KernelRuntime.prepare_resume runs under coordinator ownership. runtime/resume.py
uses existing host receipts, retained completed query artifacts and adapter-specific
result retrieval. HTTP Responses lookup requires its saved response ID and validates
identity, terminal state and output. Readiness lives under resume-preparation/;
unknown effects keep ownership/capacity; the isolated generation-only exception
is defined below under bounded inference retries. Unsupported
synchronous/native recovery fails without asserting termination. No generic OS
Git, task selection, canonical-memory or acceptance policy is introduced.

ProjectAgent.resume in agent/resume.py chooses checkpoint/model recovery, internal
senior review or accepted-output delivery for the run. All stopped workers and
retained source remain represented. Instructions have an atomic application receipt;
plans and activation can recover after a coordinator restart without applying them
twice. Application resume-progress/ and resume-outcome/ link the original intent,
while the HTTP layer serializes drivers and projects their progress. CLI Resume
uses the same service. Offline snapshots cannot signal or execute.

The exact predecessor graph documented in agent/resume.py is compatible only when
its other program pins match. The agent records the old/new identity and updates
its current run pointer, preserving original manifests, effects, config, authority,
budgets, deadlines and cancellation. Unknown graph/prompt/schema versions remain
rejected; there is no blanket historical migration or allowance reset.


## Diagnosing a boundary failure

| Observation | Owner and next inspection |
| --- | --- |
| Capability exceeds process/workspace grant | OS rejected the requested authority. Compare the process capability list, `workspace-grant/<id>` and `workspaces.authority(id)` with the calling agent's request. Registration alone grants no process permission. |
| Schema/effect mismatch or strict argument error | OS rejected an invocation before the handler ran. Use the installed descriptor/digest; inspect the request's argument artifact. The provider's JSON acceptance does not override this check. |
| Stale workspace generation/content | OS rejected a stale view. Inspect the manifest and request binding; the agent must build a new intent from its current view rather than alter an old operation. |
| Reinstall publication policy | Bootstrap is incomplete after restart. Recreate the owning application's services before new publication; settled receipt replay remains available. |
| Coding commit/report invariant rejected | The application publication hook rejected the candidate. Inspect the verification permit, expected head and minted commit/report provenance; generic record publication does not impose this coding policy. |
| Long review/exception note | Agent lifecycle data. Inspect `polyinference/stop-detail` on the attempt and the task's diagnostic/history. The note is not a permission grant or an OS error code. |
| `UncertainEffect` / unknown execution | OS cannot prove the effects ended. Inspect the original effect and reconciliation evidence before new work; a missing local connection is insufficient. |

An application `needs_review` reply is a request to its controller. An OS process
may be parked/paused while the application reviews it. The run's `app/run.status`
and blocker are coding-application state; they are not a universal OS verdict that
the requested objective failed. Generic agents define their own completion policy.

## Failure, replay and compatibility

The basic execution rules are unchanged: stable IDs do not execute twice; source
scope checks remain; observer failures do not replace primary failures; and a
disconnect or local transport kill does not establish remote termination. An
exception during an external-write handler or result recording is uncertain,
so it cannot be silently repeated as a known failed tool invocation.

The kernel compatibility marker is `simple-os/6`, with coding program
`agent-9-local-contracts` and state schema `2.8`. These pins include context
measurement/retention contracts and agent semantic-failure/error-lifecycle changes
within the current basic function set. It does not
introduce the planned next-version integration platform. Use new run/state
directories for incompatible implementations. Updated 2026-10-23: older runs
retain their original records; the explicit Resume section documents the sole
exact graph-only compatibility migration, without broader historical conversion.

The existing function set has the following regression evidence:

| Function | General-agent coverage | Coding-agent coverage |
| --- | --- | --- |
| Process start/wait/cancel/finish | `test_runtime_general.py`: artifact-only completion, terminal state, cancellation and driver deadline; `test_capability_boundary.py`: role names grant no management authority | `test_os.py`, `test_regressions.py`: bounded workers, cancellation, drain and terminal records |
| Inference and native output | `test_runtime_general.py`: raw/native non-coding output; `test_capability_boundary.py`: real stdio with app-owned schema/instructions and no code workspace | `test_native_worker.py`, `test_endpoints.py`, `test_http_integration.py`: coding phases and provider transport paths |
| Tool dispatch | `test_capability_boundary.py`: custom typed tool, denied grants/schema/effect/arguments, callback replay, ordinary `generation` data, workspace source preconditions and external-write uncertainty | `test_setup_tools.py`, `test_runtime.py`: file/shell/check calls, stale requests, scope and setup handoffs |
| Atomic publication | `test_capability_boundary.py`: unrelated application record names and resource permit, policy missing after restart, reinstallation and immutable failed outcomes | `test_os.py`, `test_recovery.py`, `test_regressions.py`: commit provenance, private failure, shared heads, receipts and replay |
| Artifacts and file delivery | `test_outputs.py`: explicit arbitrary file artifacts, baseline conflicts and interrupted delivery | `test_recovery.py`, `test_ui.py`: accepted-tree delivery, receipt recovery and exported evidence |
| Application lifecycle data | No coding task/attempt/report records are required by the general fixtures | `test_agent_transitions.py`: long review notes, old invalid attempts, setup retirement, replacement and replay; `test_setup_tools.py`: setup/check policy |

These tests use local transports and disposable repositories. The native fixture
exercises the actual adapter wire code, but does not claim fresh live-provider or
live-bubblewrap validation. Find historical test results in
`development-docs/implementation-records.md` and remaining work in
`development-docs/current-iter-issues.md`.
