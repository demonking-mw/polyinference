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
| [src/polyinference/agent/cloud_recovery.py](../../src/polyinference/agent/cloud_recovery.py) | Eligible cloud takeover, capability inventory and pending-consumer rewiring before plan validation. |

## Interface and ownership

ProjectAgent uses AgentServices/RuntimePorts and LangGraph continuations.
ProjectAgent.resume consumes UI/CLI intents after generic OS preparation. It
reattaches eligible checkpoints, retries a known model failure or reopens senior
review/output delivery. Every stopped worker remains represented; retained source
and interrupted tasks reach review. Instructions have an atomic steering receipt,
so interrupted activation cannot apply them twice. Plans/outcomes survive restart;
ordinary failures leave a paused run with a durable error. The documented exact
predecessor migration does not apply to changed recovery policy. Old manifests/
effects remain unchanged. Unknown graph/prompt/schema changes are rejected. Grants,
budgets and deadlines are preserved.
Dependencies become ready after senior keep resolutions. Verification/integration
is serialized by an explicit resource permit; starts close while review drains.
Shared runner preparation has one declared owner and explicit dependent tasks;
private source cannot satisfy that dependency. Planning sees commands/source previews.
Dispatch records started_at atomically with task admission. Historical development
counts retain cancelled/superseded starts; legacy :started specs remain evidence.
Role allocation uses those same starts plus pending quota reservations, which are
labelled separately in senior inputs and never counted as executed work.
Eligible local exceptions get bounded specialist/cloud coding outside normal
quota, including after ordinary depth exhaustion. Empty/defer/stop plans cannot
abandon that route. Model proposals and effective adjustments are retained;
pending consumers are rewired and started contracts remain pinned. An unstarted
linked recovery is retargeted through its original exception/predecessor, retaining
its root/depth/grants; an admitted consumer cannot be cloned into a fresh account.
Cloud retries share the original physical envelope; see [reliability](../guides/agent-reliability.md).
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
[setup](../../tests/test_setup_tools.py), [cloud recovery](../../tests/test_cloud_recovery.py)
and [user briefs](../../tests/test_user_briefs.py).

[Agent design](../../design-docs/langgraph-agent/README.md) · [Current issues](../../development-docs/current-iter-issues.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.

## Integrated reliability branch (2026-10-26)

Review includes independent current-tree checks, bounded source retrieval, versioned
module contracts and explicit semantic completion criteria. Clean fenced worker
exceptions become review obligations; linked replacements share original resource
accounts/deadlines. Existing steering, check-preparation dependencies, historical
started-task allocation and retained private-source offers remain authoritative.
These combined graph/schema changes use fresh program/state pins; old live runs
must use their original pinned source.

Operator-prepared model recovery may resume at the progress node inserted before
the model node, retaining its linked recovery identity and original allowance.
Explicit cancellation remains cancelled rather than becoming a semantic exception.
