# Process lifecycle

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Generic explicitly started process continuations run under durable identities and bounded admission.
request_resume(records, process_id=None, text=None, request_id=None) records an
immutable operator intent under resume-request/. Explicit process signals validate
a paused, noncancelled process and link process-control/. Unscoped signals require
unfinished execution and link resume-control/run. request_id deduplicates accepted
input, including retries after acknowledgement loss. Acceptance is independent of
unsettled effects; KernelRuntime.prepare_resume and ordinary dispatch enforce
certainty before execution. No grants, budgets or coding records are interpreted.
Requests, OS resume-preparation/ and application resume-progress/ and
resume-outcome/ remain exportable.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/processes.py](../../src/polyinference/runtime/processes.py) | Register/start/status/wait/cancel/finish, one driver per process, deadlines and durable state. |

## Interface and ownership

Applications supply ProcessSpec and an async continuation; the OS does not
decompose objectives. Resident worker capacity and model endpoint admission are
independent. Control/management treatment is explicit rather than inferred from roles.

## Principles to preserve

- Cooperative cancellation preserves started effects and their certainty.
- A finished process need not produce source, Git commits, reports or tests.
- Do not hold an exclusive global execution lock while awaiting inference.
- Narrow process-limit authority and paused-worker residency remain open U03/U04 gaps.

## Verification and related reading

[General lifecycle](../../tests/test_runtime_general.py), [runtime](../../tests/test_runtime.py)
and [regressions](../../tests/test_regressions.py).

[Boundary responsibilities](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md#responsibilities).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
