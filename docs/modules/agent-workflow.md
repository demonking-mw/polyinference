# Coding controller, setup and task allocation

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The application chooses ready work, starts independent workers, drains before review and decides final acceptance.

| File | Responsibility |
| --- | --- |
| [src/polyinference/agent/controller.py](../../src/polyinference/agent/controller.py) | ProjectAgent lifecycle, dispatch, review, steering, recovery, delivery and controller graph. |
| [src/polyinference/agent/resume.py](../../src/polyinference/agent/resume.py) | Run continuation, all-worker disposition, checkpoint/model/output recovery and exact predecessor compatibility. |
| [src/polyinference/agent/setup.py](../../src/polyinference/agent/setup.py) | Initial specialist setup using the normal worker protocol. |
| [src/polyinference/agent/tasks.py](../../src/polyinference/agent/tasks.py) | Task/attempt envelopes and explicit coding capability grants. |
| [src/polyinference/agent/routing.py](../../src/polyinference/agent/routing.py) | Stable senior/junior development allocation by task count. |

## Interface and ownership

ProjectAgent uses AgentServices/RuntimePorts and LangGraph continuations.
ProjectAgent.resume consumes UI/CLI intents after generic OS preparation. It
reattaches eligible checkpoints, retries a known model failure or reopens senior
review/output delivery. Every stopped worker remains represented; retained source
and interrupted tasks reach review. Instructions have an atomic steering receipt,
so interrupted activation cannot apply them twice. Plans/outcomes survive restart;
ordinary failures leave a paused run with a durable error. Exact prior graph
50fa4c43...dc9b2ca8 is migrated only when all other program pins match; old manifests
and effects remain unchanged, with a separate migration record. Unknown graph or
prompt/schema changes are rejected. Grants, budgets and deadlines are preserved.
Dependencies become ready after senior keep resolutions. Verification/integration
is serialized by an explicit resource permit; starts close while review drains.
Shared runner preparation has one declared owner and explicit dependent tasks;
private source cannot satisfy that dependency. Planning sees commands/source previews.
Dispatch records started_at atomically with task admission. Historical development
counts retain cancelled/superseded starts; legacy :started specs remain evidence.
Role allocation uses those same starts plus pending quota reservations, which are
labelled separately in senior inputs and never counted as executed work.
Setup checks prerequisites when present. Assignments use task/product checks;
final completion requires its separate acceptance selection. Explicit legacy
checks remain combined task/final criteria when no acceptance override is supplied.

## Principles to preserve

- Planning, Git/check policy and acceptance belong to this application.
- Requested work and started work differ; OS slots cannot invent ready tasks.
- Keep setup/management outside development allocation counts.
- Preserve user amendments and retained failure evidence across handoffs.
- Tick and dispatch use the same effective worker limit, including one-editor Git policy (FIX-0083).

## Verification and related reading

[Agent](../../tests/test_agent.py), [drain/regressions](../../tests/test_regressions.py),
[setup](../../tests/test_setup_tools.py) and [user briefs](../../tests/test_user_briefs.py).

[Agent design](../../design-docs/langgraph-agent/README.md) · [Current issues](../../development-docs/current-iter-issues.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
