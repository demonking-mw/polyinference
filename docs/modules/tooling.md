# Developer tooling

Choose a task group before running a tool from the repository root.

| Task group | When to use it |
| --- | --- |
| Documentation and schema checks | Run `python scripts/project_docs.py` after changing the tree, then rerun with `--check`. Run `python scripts/settings_docs.py --check` when changing settings. |
| Offline design checks | Run the design contract validators or graph verifier when editing those artifacts. Use the associated guide for rebuild commands. |
| Workflow qualification | Run `python scripts/qualify_workflow.py --fixture --output <new-directory>` for the offline gate. The browser runner is part of qualification. See `docs/guides/qualification.md`. |
| Live smoke | Use `scripts/smoke_os_codex.py` only for an authorized real Codex check. It uses provider allowance and a disposable project. |
| Packaging | Verify the wheel with the commands in `docs/testing.md`. |

- [Documentation and tree tooling](documentation.md)
- [Design contract, graph and reader tools](design-tools.md)
- [Packaging and repository hygiene](packaging.md)
- [Opt-in live smoke runner](live-smoke.md)
