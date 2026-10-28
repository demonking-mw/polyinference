# Worker/senior graphs and reply grammar

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Reusable application graphs turn model replies into development, reconciliation and assessment decisions.

| File | Responsibility |
| --- | --- |
| [src/polyinference/agent/worker.py](../../src/polyinference/agent/worker.py) | Worker phase transitions, actions, checks, validated task attempts and bounded grammar correction. |
| [src/polyinference/agent/senior.py](../../src/polyinference/agent/senior.py) | Senior submit/validate graph for structured planning and review proposals. |
| [src/polyinference/agent/prompts.py](../../src/polyinference/agent/prompts.py) | Application instructions, role grammar, constraints and truthful evidence rules. |
| [src/polyinference/domain.py](../../src/polyinference/domain.py) | Git policy, assignments, senior proposals and typed worker replies. |
| [src/polyinference/agent/architecture.py](../../src/polyinference/agent/architecture.py) | Immutable versioned interfaces, resulting-plan dependencies and pinned task contracts. |
| [src/polyinference/agent/review.py](../../src/polyinference/agent/review.py) | Source/diff/check packets, bounded review reads and exact-tree semantic completion. |
| [src/polyinference/agent/diagnostics.py](../../src/polyinference/agent/diagnostics.py) | Bounded read-only checking-agent diagnosis under the worker's resource account. |
| [src/polyinference/agent/schema.py](../../src/polyinference/agent/schema.py) | Compact displayed response schemas while retaining validation constraints. |
| [src/polyinference/agent/worker_memory.py](../../src/polyinference/agent/worker_memory.py) | Bounded source-backed worker facts and deterministic validation-error feedback within existing retry bounds. |

## Interface and ownership

WorkerReply accepts actions, candidates, assessments or review requests. The application validates it and
issues explicit brokered operations. Native and raw models receive application-owned schemas/instructions
through the same OS boundary. Worker scope recovery catches the public ports.WriteScopeError; it imports no
concrete workspace-state implementation merely to recognize the typed error. Senior inputs include check
commands, bounded source previews and task contract/ lineage views with durable record/spec refs; full
workspace envelopes stay in records. When a shared check needs preparation, check_preparations names its new
owner; every other assignment using that check must explicitly depend on that owner. Invalid
ownership/dependencies receive the existing bounded proposal correction. An already prepared contract needs
no extra task. Dependencies start only after keep. Senior publication instructions distinguish in-place
private uncertain candidates from isolated provisional ones. Retained-source offers drive explicit
resume_from and bounded corrections for unavailable source or incomplete replacement grants.

Assignments can pin `acceptance_criteria`, `non_goals`, `provides` and `consumes`. Optional `behavior` and
`focused_check` are paired; the check must be assigned. Declared check `required_paths` need readable
closure or declared dependency owners, including retained providers. The required 8192-byte worker-state view retains recent CAS
digests/errors/evidence and original trajectory references. Source/generation changes invalidate digest
facts. Interface references use `interface_id@version`; revisions must be sequential and existing versions
are immutable. Pending consumers must depend on unfinished providers; changing an interface requires
replacing affected pending tasks. Started tasks retain their original contract artifacts.
Byte-eviction counts persist within the same source/generation so replay keeps the same ledger revision.

Senior review separates worker claims from actual diffs, source and check evidence. Bounded `read_requests`
retrieve more source. Completion must assess the reserved `objective` criterion and configured criteria
against the exact reviewed tree; missing, uncertain or stale evidence cannot establish completion. Diagnosis
can request bounded read expansion or advise continuation/review, without write tools or a new resource
allowance. See [configuration](../guides/agent-reliability.md).

Automatic stagnation parks directly for senior review, bypassing read-only diagnosis. Eligible local
exceptions now get a bounded cloud coding takeover protected from normal allocation. The senior graph
validates this effective plan and retains raw model decisions separately. Workers receive predecessor
failure/source context. Planner instructions require one behavior/check per local task and pin actual
capabilities: no browser/MCP/persistent service API. See [recovery](../guides/agent-reliability.md).

## Principles to preserve

- Consecutive invalid replies consume a bounded correction streak; valid actions reset it.
- Partial/incomplete model output must never become executable actions.
- Product acceptance needs meaningful evidence; a build or candidate alone is insufficient.
- Preserve the full objective, declared outputs and write authority in worker inputs.

## Verification and related reading

[Transitions](../../tests/test_agent_transitions.py), [native worker](../../tests/test_native_worker.py),
[HTTP integration](../../tests/test_http_integration.py) and [incident
fixes](../../tests/test_incident_fixes.py). Module/review/diagnosis coverage:
[planning](../../tests/test_module_planning.py), [semantic review](../../tests/test_semantic_review.py),
[diagnosis](../../tests/test_check_diagnosis.py) and [feedback](../../tests/test_validation_feedback.py).

[Agent design](../../design-docs/langgraph-agent/README.md) · [Repository guide](repository.md).

After a fix/feature, update this guide and all affected docs/settings/navigation, then record actual
verification in [FIXES.md](../../development-docs/FIXES.md). Follow [documentation
maintenance](../maintenance.md) in the same task.

See [worker recovery](../../design-docs/implementation/WORKER_RECOVERY.md) and [progress
monitoring](../../design-docs/implementation/PROGRESS_MONITORING.md). Private in-place reports remain
private until verified publication; a successful fixture response is not live product verification.
