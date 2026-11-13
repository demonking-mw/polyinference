# Capability registration and model calls

## Bootstrap and the capability boundary

Static registration/dispatch now enforce mandatory data policy and supported hard
class constraints; unsupported weights and unequal process/runtime limits reject.
Paused residency persists until explicit safe hibernation/readmission. See the
gap history (`design-docs/simplified-os/DESIGN_REVISIONS.md#open-implementation-gaps`) and
current verification (`development-docs/reliability-implementation-2026-10-27.md`).
RuntimeConfig.limits remains the uniform supported envelope; arbitrary narrower
per-process limits are rejected rather than silently widened.

Trusted application code opens `KernelRuntime`, installs its handlers/protocols,
and registers processes before issuing effects. Registration is a local Python
API, not a model-accessible operation. It does not discover tools or create MCP
servers. `src/polyinference/ports.py` defines the boundary.

A capability consists of a name, argument type, handler, effect class and whether
it requires a file workspace. Pydantic supplies the argument schema. The wire
descriptor is pinned under `runtime/capability/<name>`; changing it requires a new
state directory. Handler code is installed again on restart and is governed by
the caller's program/version pin, not serialized Python function addresses.
Native protocol definitions (schema, instructions, brokerage and workspace mode)
are likewise pinned under `runtime/agent-protocol/<name>`. Reinstalling the same
definition is valid; changing it under the same identity is rejected after restart.

For example, with an open runtime and an application-owned `ProcessSpec`:

```python
from polyinference.contracts import Wire

class Lookup(Wire):
    topic: str

async def lookup(request, arguments):
    return {"finding": arguments["topic"]}

runtime.register_capability("example.lookup", lookup, input_type=Lookup)
runtime.processes.register(spec, "local", capabilities=["example.lookup"])
runtime.register_agent_protocol(
    "example/1",
    {"type": "object", "properties": {"summary": {"type": "string"}}},
    workspace="none", brokered=True,
    instructions="Use the granted tool and return the supplied summary schema.",
)
```

The caller still constructs the existing `AgentJob` and stable `OperationRequest`.
An executable end-to-end example, including the complete spec/context/request and
real stdio transport, is `tests/test_capability_boundary.py`. A raw `ModelQuery`
does not need native protocol registration. The existing raw/native artifact-only
paths are covered by `tests/test_runtime_general.py`.

Register a process once. On restart, restore its persisted spec and continuation;
reinstall handlers and native protocols before new dispatch. Replaying a settled
operation returns its retained result before checking transient ownership. For a
model invocation with OS-selected retries, `execute(original)` projects the
effective retained attempt; every individual failed/successful effect remains
immutable. Replay follows that durable chain without another provider submission.

The bundled application's wiring is explicit:

| Handoff | Code and persisted authority |
| --- | --- |
| Bootstrap | `AgentServices.__init__` installs its two native protocols, `checks.configure`, publication policy, cancellation policy and reconciliation callback. Required registration is not skipped through optional `hasattr` checks. |
| Process creation | `AgentServices.process` builds the coding `ProcessSpec` and calls `processes.register`, supplying the capability maximum and management flag. The OS atomically writes the process, spec and mutable initial status. |
| Worker load | `agent/worker.py:load` supplies the workspace's narrower tool/check grant, paths and expansion flag. The OS atomically writes the workspace manifest and grant after materializing the private view. |
| Model input | `AgentServices.model` reads `workspaces.authority` for `write_authority`; the native adapter receives only the job's explicitly selected registered descriptors and the application's instructions. |
| Tool request | `AgentServices.capability` uses the registry's schema digest and binds workspace generation/content only for workspace capabilities. Native callbacks construct the same operation payload at the OS boundary. |
| Publication | The OS verifies capability/resource ownership, calls the installed program policy, then commits its returned batch with the receipt in one record transaction. |
| Recovery | The OS establishes effect certainty and invokes the installed reconciliation callback. The coding application changes its own task/run records; settled operations retain their original results. |

General agents use these same existing services, choosing only what they need.
The built-in `user.notify` capability takes `{"text": "Message for the user"}`
(1–16000 characters, nonblank), has effect class `shared_write`, and requires no
workspace, Git repository or coding records. Grant it in process registration and,
for native jobs, in `AgentJob.allowed_capabilities`. Direct callers use an ordinary
`CapabilityCall`. Each notification is retained under `user-message/<operation_id>`
and shown in the UI's **Messages from agents** panel, including saved snapshots.
The runtime also prints the full message immediately in the launch terminal for
both CLI and UI runs. Replay/recovery retains one message without printing it again;
a terminal failure leaves the durable UI message available. The OS does not infer
progress or verification claims. The coding sprint manager supplies its own
`user_brief` on each planning/review invocation and sends it through this capability.

They do not instantiate `AgentServices` merely to obtain OS functionality. Python
handlers and policies are trusted application bootstrap code; registration is not
a sandbox for untrusted Python plugins.

## Direct and native calls use the same authority

Direct `CapabilityCall` payloads carry the registered capability's `schema_digest`
and `effect_class`, plus an argument artifact. Use
`runtime.capabilities.get(name).schema_digest`; hashing the name is not the ABI.
The kernel rejects absent grants, changed schemas and forged effect classes before
calling the handler. Strict argument validation applies even if a provider emitted
JSON that passed its own schema check.

For native jobs, the installed protocol selects the output schema, optional
instructions and working view:

- `snapshot`: a prepared read-only Git or artifact snapshot.
- `workspace`: an existing process-owned file workspace.
- `none`: an empty private native working directory; no code workspace or Git is
  created. The historical `AgentJob.workspace_id` wire field remains present but
  is unused by this mode.

Only `AgentJob.allowed_capabilities`, checked against the process grant, are
advertised through the existing `polyinference_tool` transport envelope. Its
argument schemas come from those registered capabilities. The adapter supplies
no coding phase instructions. The bundled agent installs its own
`candidate`/`assessment`/`needs_review` instructions.

Native callbacks become ordinary journaled subordinate effects. The kernel derives
their effect class and schema digest from the capability, not model text. A stable
parent/call ID replays the original observation; changed arguments under the same
ID are rejected. A non-workspace tool does not get a fabricated file view. A
workspace tool receives the current host-issued generation/content binding.
The kernel checks generation and any supplied expected content before invoking
every registered workspace handler, including application-owned ones such as
`checks.configure`. Validation is not limited to the built-in file-tool handler.
The agent helper fills a missing host generation, but preserves an explicitly
supplied generation so stale-intent checks cannot be bypassed by refreshing it.
`generation` is host metadata only for workspace capabilities; for a capability
without a workspace it is an ordinary typed argument and participates in replay
comparison unchanged.
