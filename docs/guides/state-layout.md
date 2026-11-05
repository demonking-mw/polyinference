# Runtime state layout

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

UI data is relative to the directory from which you started the server:

```text
.polyinference/ui/
  fixture/                     # Disposable greeting source project
  runs/<RUN_ID>/
    ui-run.json                # UI run metadata
    config.json                # Effective configuration; environment variable names
    state/
      records.sqlite           # Typed records, reports and operation journal
      checkpoints.sqlite       # LangGraph checkpoints
      artifacts/               # Content-addressed requests/results and other artifacts
      repository.git/          # Legacy isolated mode only
      workspaces/              # Temporary merge/index resources; legacy copies
      snapshots/               # Native-agent snapshots
      result/                  # Legacy isolated mode delivery
```

Custom CLI runs put the equivalent state files directly in `state_directory`.
Start the UI from the same directory later to rediscover its saved runs. Keep the
whole state directory if you need recovery; copying just a SQLite file is not a
complete backup. Prefer patch/Git exports over copying an arbitrary temporary
workspace, which may represent only one task or an intermediate integration view.

Related: [Result locations](results.md) · [Exports](exports.md) · [Archives](archives.md).
