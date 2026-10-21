# Run on your project

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

1. Choose a project path on the host filesystem (inside Linux for WSL). The folder
   may be new: startup creates it and any missing parents and initializes Git there.
   For an existing Git checkout, commit or stash changes, including untracked files you want to keep.
   The coding agent preserves existing edits and requires a clean integration checkout.
2. In **Project path**, enter the absolute host path or use **Browse…**.
   Select the intended project directory. A folder inside another repository gets
   its own Git repository; the enclosing checkout is not used as its baseline.
   A new project folder is also supported; enter its path in the main field or folder picker even if it
   does not exist yet. The picker indicates that setup will create it at run start.
3. Enter a specific objective: expected behavior, files or areas to change,
   acceptance criteria, setup chores and branch instructions.
4. Expand **Check command** and inspect the command. The UI suggests a pytest
   command for Python projects or `npm test` when `package.json` defines it.
   Otherwise enter one or let setup discover it. Missing checks cannot establish
   success. Install the required tools and dependencies.
5. Optionally enter an existing local **Base branch** in that same panel. If you
   need a new branch, explicitly request its creation in the initial objective.
6. Click **Start run** and inspect the selected project and recorded integration
   branch. Integrated work appears in that folder throughout the run.

An example objective:

> Use the existing `feature/search` branch as the baseline for this development.
> Inspect the project setup and run any required preparation. Add case-insensitive
> filtering to the search endpoint, preserve pagination behavior, and add tests
> for mixed-case queries. Completion requires the configured test command to pass.

The coding agent resolves Git instructions before editing the actual repository.
By default it creates and checks out `codex/run-<id>` from current HEAD. Workers
use branches and linked worktrees under `PROJECT/.polyinference/worktrees/`;
passing work merges into the integration branch and updates the project root.
Explicit instructions take precedence: a named branch replaces the default, and
"create no branches" disables task branches too and serializes root editing.
The agent inspects available local branches and resolves setup errors before development.
For a new project, the agent
initializes Git at the supplied path. Nothing is pushed or merged back by default.

Recoverable Git setup errors are sent back to the agent with the available branches
for correction. Startup notes reach the setup engineer instead of rejecting local
development. Dependency preparation failures also reach the agent as observations;
the configured checks still run and provide evidence for repair and acceptance.
This recovery policy belongs to the coding agent; runtime permissions, workspace
grants and execution guarantees remain enforced by the OS.

The check field is parsed as **an executable and arguments**, not as a shell
script. For example, use `python -m pytest -q` or `npm test`; shell operators such
as `&&` and pipes are not interpreted there. For more involved verification,
provide a committed script and configure its interpreter and arguments.
Worker checks execute in their full project worktree; independent review and
acceptance use the root integration checkout. The coding agent prepares locked
npm dependencies with `npm ci --ignore-scripts` before checks. Other projects can
set `dependency_prepare` to an explicit argv, or prepare their tools during setup.
These commands require enabled shell execution. An absolute interpreter can
select an existing Python environment. The OS does not choose package managers.

Without `--config`, selecting another project grants the selected directory as
the development scope, including new files; each task still has its own explicit
write set. With `--config`, the configured grants, closure, endpoints and checks
remain in force when you change roots. Adjust those grants for the target project
before starting.

For disposable projects inside this checkout, use **`testing/`**, which Git ignores.
The real implementation test suite is **`tests/`** and remains tracked.
