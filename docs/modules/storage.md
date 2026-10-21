# Persistence, exclusive resources and blocking I/O

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

Durable generic records/artifacts and bounded host resource ownership underpin replay and inspection.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/storage.py](../../src/polyinference/runtime/storage.py) | SQLite versioned records, atomic compare-and-publish, retained journal and immutable artifact bytes. |
| [src/polyinference/runtime/exclusive.py](../../src/polyinference/runtime/exclusive.py) | Durable permits, async ownership waits and advisory filesystem locks. |
| [src/polyinference/runtime/blocking.py](../../src/polyinference/runtime/blocking.py) | Single bounded filesystem executor; cancellation joins submitted mutations. |

## Interface and ownership

Records own versions and atomic batches; applications validate their own record
semantics. Artifacts are content-addressed. Exclusive resource keys coordinate
cooperating runtimes; filesystem work is serialized off the event loop.

## Principles to preserve

- SQLite atomicity does not make an external filesystem/Git mutation atomic.
- Stable immutable keys cannot be reused for different content.
- External editors need not honor advisory locks; detect drift before publication.
- Join mutating work after cancellation rather than asserting it never ran.

## Verification and related reading

[OS/storage](../../tests/test_os.py), [runtime](../../tests/test_runtime.py),
[recovery](../../tests/test_recovery.py) and [workspace output](../../tests/test_workspace_outputs.py) checks.

[Concurrency audit scope](../../development-docs/current-iter-issues.md#os-concurrency-audit).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.
