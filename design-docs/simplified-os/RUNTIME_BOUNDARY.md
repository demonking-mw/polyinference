# Runtime and agent boundary

Read this before changing the coding agent or OS. These rules apply through the
public runtime ports; general programs can use them without the coding application.

## Responsibilities

| Function | OS responsibility | Calling agent responsibility |
| --- | --- | --- |
| Process lifecycle | Register identity, enforce uniform limits/resident admission/deadlines, start/wait/cancel/finish, release settled residency through hibernation and retain outputs/unfinished effects | Supply the program/continuation and decide what work to do; explicitly identify control processes |
| Inference | Admission, context/output bounds, provider transport, usage, durable results and uncertainty | Supply context, role binding and response grammar; interpret the result |
| Brokered tools | Check capability grants, input schema, effect class, identity and workspace preconditions; invoke the installed handler | Choose which existing capabilities to grant; supply application-specific handlers/instructions where needed |
| Workspaces and commands | Optional private file views, scoped edits, shell exclusion, source evidence and temporary tool environments | Select paths, read/build closure and checks; request authorized scope changes |
| Records and publication | Atomic compare-and-swap, immutable objects, ownership and receipt replay | Validate application objects and install any program-specific publication policy |
| Artifacts and delivery | Store/read artifacts; deliver explicit files with baseline conflict protection | Decide which artifacts constitute the result and when it is acceptable to deliver them |
| User messages | Persist and display plain text in the UI and terminal with operation replay protection | Grant `user.notify`, decide when to speak, and supply the message content |

The OS does not require a TaskSpec, coding verdict, source edit, test or commit for
a general process to complete. A process may return artifacts or no output. The
bundled agent still requires its reconciliation, assessment and acceptance flow.

The runtime schedules bounded model operations. Token/GPU scheduling remains in
the inference server; agent continuation does not expose hidden reasoning state.

### Proposed standalone scheduler boundary

V1 scheduler authority is limited to individual-process admission (`run`), deferral
(`wait`) and requesting preemption from the running set. Its observations are
read-only. The OS distributes resources among eligible processes: destination
selection within original permissions, capacity/quota allocation, physical dispatch,
safe suspension/readmission and settlement. An admitted process can still wait for
OS resources. The scheduler cannot claim a resource vector, choose an endpoint/model,
submit an operation, settle usage or attest resource release. A preemption request
remains pending while the OS drains protected effects; it grants no cancellation,
new budget or deadline. This is a clarified proposed interface, not new runtime
behavior. See the scheduler design (`docs/temporary/proposals/2026-11-08-standalone-scheduler-design.md`)
and `development-docs/FIXES.md#fix-0183`.

The OS resolves the declared local token pair and enforces it alongside generic
resource, authority and effect guarantees. Cloud per-call token limits belong to
the provider. The coding agent owns one-file local edit contracts, required cloud
placement, semantic recovery and source-backed acceptance. Private passing or
failing check receipts can inform review without granting permission to publish.

- [Repository integration and retained source](boundary/repository.md)
- [Capability registration and model calls](boundary/capabilities.md)
- [Workspace authority and publication](boundary/workspaces.md)
- [Operator Resume, replay and compatibility](boundary/continuation.md)
- [Context preparation and output recovery](boundary/inference.md)
- [Inference retry and model fallback](boundary/retries.md)
