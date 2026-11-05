# Artifact delivery and user messages

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Optional OS capabilities deliver explicit files and durable plain-text notifications for any agent.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/outputs.py](../../src/polyinference/runtime/outputs.py) | Destination baseline/conflict checks, file delivery intents/receipts and replay-safe recovery. |
| [src/polyinference/runtime/messages.py](../../src/polyinference/runtime/messages.py) | Typed user.notify arguments, durable messages and terminal delivery. |

## Interface and ownership

The caller chooses acceptable artifacts, destinations and message content.
Default in-place coding does not copy back with outputs.deliver; explicit legacy
isolated coding and other applications may use it. user.notify requires a grant.

## Principles to preserve

- Preserve destination edits and immutable failed operations on delivery retry.
- Replaying a notification must not duplicate terminal output.
- Delivery/reporting failure cannot rewrite primary execution facts.
- The OS never invents sprint semantics, commit claims or acceptance.

## Verification and related reading

[Outputs](../../tests/test_outputs.py), [user briefs](../../tests/test_user_briefs.py),
[history](../../tests/test_history.py) and [recovery](../../tests/test_recovery.py).

[Results](../guides/results.md) · [Explicit recovery](../guides/retrying.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
