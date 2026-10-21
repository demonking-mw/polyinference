# Rolling diagnostic archives

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

Every UI run and CLI `run`/`resume` invocation also automatically saves a diagnostic
JSON snapshot in `.polyinference/history/` under the working directory. Failed
executions are included; each resume gets its own snapshot. UI **Save run · JSON**
and this archive use the same serializer in `src/polyinference/snapshots.py`, so
changes to the saved contents apply to both. Open an archive file with **Open
snapshot** to inspect it.

At each invocation's completion, archive snapshots older than **30 days** are
deleted, using their UTC completion timestamp in the filename. No background
cleanup job runs. Existing run state, private Git stores and manually downloaded
snapshots are retained independently. Archive failures are logged without
changing the agent's result.

Related: [Result locations and exports](results.md) · [Snapshot module](../modules/inspection.md).
