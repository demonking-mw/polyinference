# Simple OS v1 implementation

Work branch: `codex/simple-os-v1`. The source checkout on `main` remains available
for independent agent testing. This file records the implementation plan and the
latest requirements that supersede historical design defaults.

## Decisions and sources

Use the existing LangGraph agent and RuntimePorts boundary. Reuse the tested
workspace, Git, provider and checkpoint implementation; replace the standalone
placeholder entry point with a kernel that owns durable admission, lifecycle and
recovery. No framework internals or model server scheduler are modified.

Source precedence: the current user request and OS audit answers, then the
simplified OS specification, integration audit A1–A9, agent implementation and
agent audit answers, merged execution/memory graphs, concurrency protocol, five
OS lecture derivations, and reference handbooks. The proxy brief distinguishes
raw inference from complete native jobs; direct Codex app-server is the existing
implemented fallback and must retain real tool brokerage and terminal evidence.

* O01/O05: broker every effect, validate process grants, pinned file closure,
  generation and content; preserve the original delta across abort/restart.
* O02: physical RAM/VRAM management is deferred. Worker, request, token, output,
  artifact and deadline limits still bound the application.
* O03: `POLYINFERENCE_LOCAL_BATCH_SIZE` selects simultaneous local-lane requests;
  the lane may point at a cloud raw API with a batch size of one for testing.
* O04/latest failure example: an assessed **fail** creates an attributable private
  commit and unresolved report without advancing the shared provisional head.
  Close starts atomically, release verification, allow all already-started workers
  to finish and publish, then review/replan. `uncertain` retains the specified
  provisional publication behavior, but also triggers review. Senior cannot accept
  a failed private commit merely by marking it kept; retry/reject is explicit.
* O06: journaled effects and durable checkpoints are the recovery boundary. Never
  infer remote termination from disconnect. Retain unknown reservations/permits,
  reconcile proven host receipts, expose explicit recovery controls and diagnostics.
* O07/O08: support the existing raw API clients and bounded Codex jobs. Opaque
  proxies remain read-only. No MCP platform, migration, general agent framework,
  automatic model placement, distributed coordination or GPU scheduler.

## Work sequence

1. Establish baseline tests and map source requirements to implemented services.
2. Implement kernel entry point, pinned environment configuration, durable
   admission/usage, process status/control, event diagnostics and safe shutdown.
3. Enforce effect identity, grants, queue deadlines, bounded transports/tools and
   recovery semantics, retaining separate shell and verification ownership.
4. Add private failure receipts and drain-before-review to the agent's existing
   protocol with a new program version; preserve successful publication and exact
   tree acceptance.
5. Add deterministic concurrent, crash/replay, provider and CLI integration tests;
   run the full regression suite and contract validators, plus available live
   endpoint smoke tests. Record actual coverage and limitations here.
6. Update launch/configuration/recovery documentation and commit on the OS branch.

## Validation

Implemented and validated; see [the validation record](VALIDATION.md) and
[deployment/recovery guide](RUNBOOK.md). The full suite passes 97 tests, followed
by 22 focused OS/contract tests after the final private-receipt recovery change.
A real Codex coding run completed with five native jobs and seven broker callbacks.

| Requirement | Implementation and evidence |
| --- | --- |
| Kernel authority and bounded process drivers | `runtime/kernel.py`, `processes.py`; principal/grant/budget/generation checks, one active top-level intent per process, cooperative cancellation and durable status. |
| Admission and cloud substitution | `runtime/inference.py`, `config.py`; independent bounded lanes, alternating finishing FIFO, pinned environment override, actual usage settlement and retained unknown occupancy. HTTP/stdio fixtures verify real overlapping requests. |
| Private workspace and tools | `workspace.py`, `tools.py`, `shell.py`, `commands.py`; original delta and manifests, complete integration, read/search/patch, configured checks, bounded process groups and filesystem executor. |
| Shared publication authority | Broker-minted commit and parent validation, expected-head/permit checks and atomic records/events. `test_four_workers_failure_retains_commit_drains_and_replans` covers private failure, other workers draining, deferred starts and the next sprint. |
| Recovery | Durable prepared/submitted/results, provider identities, original-intent replay, known host receipts, explicit attested stop and interrupted-task review. Private failure receipt replay is tested after head/ownership changes and restart. |
| Agent and UI compatibility | Existing public LangGraph graphs/checkpointer, UI and CLI use the kernel. The old adapter import is an alias. All original agent/UI/provider regressions run. |

The new agent program version rejects silent resume of old graph behavior. The
workspace port's `retag_task_spec` is now asynchronous to avoid blocking the
coordinator while copying. Historical wire 2.0 schemas stay unchanged;
`os_contracts.py` adds truthful private-failure reports/receipts instead of claiming
a private candidate was published. Historical all-verdict fixture semantics are
preserved as source-contract evidence; the current user failure rule is tested
by the implementation suite.

The baseline already contained a merged HTML graph whose digest differed from
the examples/program provenance. Its unchanged content matches the checked-in
JSON and all 159 routes. Only the two stale provenance hashes were refreshed;
no graph or contract schema was rewritten.

Explicit v1 boundaries remain physical resource management, model serving,
distributed recovery, guaranteed provider cancellation, migration and automatic
retention/GC. macOS is verified in this OS effort; Linux/WSL share the POSIX
implementation and earlier agent validation, but this final OS revision has not
been rerun on those hosts. The runbook explains trusted command execution and
manual recovery after unknown external effects.
