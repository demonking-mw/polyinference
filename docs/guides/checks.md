# Select checks for setup, tasks and product acceptance

[Configuration](configuration.md) · [Project runs](projects.md) · [Worker protocol](../modules/agent-workers.md)

Check commands run as executable/argument lists, not shell scripts. Configure
named task `checks` in `system`; agent-only `prerequisite_checks` and
`acceptance_checks` belong at top level.

| Selection | Meaning |
| --- | --- |
| `prerequisite_checks: []` | Default. If populated, setup uses these environment checks; they cannot establish product completion. |
| Explicit `checks` | Task criteria; also final criteria when acceptance_checks is omitted/null. |
| `acceptance_checks: null` or omitted | Retain the explicit legacy task/final fallback. |
| `acceptance_checks: []` | Disable that fallback; setup must discover meaningful final criteria. Missing final checks block completion. |

Setup uses prerequisites when present, otherwise available task/product checks.
Development assignments may select task/product checks, not prerequisite-only
checks. Final completion requires passing final checks on the reviewed tree plus
the agent's source-backed semantic assessment of the objective.

For example, use an interpreter with the target project's dependencies:

```json
{
  "name": "tests",
  "argv": ["/absolute/path/to/project-venv/bin/python", "-m", "pytest", "-q"],
  "timeout_seconds": 120,
  "output_paths": []
}
```

Initial setup can discover one combined command per unconfigured purpose through
`checks.configure {name, argv, purpose, timeout_seconds?, output_paths?}`.
Purpose is `prerequisite`, `task` (default) or `acceptance`. Discovered task checks
never automatically become final checks. Explicit criteria cannot be replaced;
discovery closes after setup/planning. Shared names need identical definitions.
This purpose policy belongs to the agent; the OS executes granted commands and
binds their evidence to source and environment identity.

Declare generated directories, for example `"output_paths": ["dist"]` without a
trailing slash, when selecting the command. Tracked or explicitly granted source
always remains source. `.gitignore` cannot hide an unauthorized source change.
Check selection and output declarations remain pinned for the run.

Default in-place workers check their project worktree; independent review/final
checks use the integration checkout. Explicit isolated mode uses private views.
Compatible private dependency state survives workspace generations; changed
manifests/locks invalidate it. Dependency preparation failures reach the agent
for repair, and a failing command cannot become passing evidence.

Planning must inspect the actual runner, required filenames and source closure.
Check `required_paths` explicitly names runner/fixture/entry inputs. A new assignment
must cover them through its read/write/closure paths or an explicit dependency owner.
Use optional assignment `behavior`/`focused_check` for the one behavior being tested.
These structures do not prove semantic task size; planning and review still own it.
Shared runner preparation has one declared owner and explicit dependent tasks;
another worker's private runner is unavailable. Interface contracts and narrow
grants do not prove those exact required files were assigned correctly.

Choose checks that observe requested behavior. A passing syntax/build/storage
test cannot establish rendered gameplay or working menus. The
[retained local test](../../development-docs/local-strata-live-test-2026-10-26.md)
passed 25 narrow tests while the browser remained unplayable. Preserve that
distinction when reporting task milestones and full product acceptance.

The [qualification harness](qualification.md) supplies independently checked short
tasks and a real Chromium entry/input/pause/save/reload command. Browser dependencies
must pass preflight; an unavailable browser is not replaced by a fabricated DOM.
