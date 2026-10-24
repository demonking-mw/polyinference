# Locate code and export evidence

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

New coding runs default to `repository_mode: "in_place"`. Source, commits and
branches live in the supplied actual repository. Inspect them with ordinary
`git log --all` and `git show COMMIT`. The root stays on the integration branch;
failed candidates and unfinished edits remain in named worker branches/worktrees.
The UI, CLI status and JSON export record the original branch, integration branch,
commit and worker paths. Final reporting describes the branch arrangement even
when the run stops early. No final copy-back is needed.

Git behavior is coding-agent policy. `git_policy` can explicitly select
`{"mode":"current","task_branches":false}` or a named `new`/`existing` branch;
otherwise a read-only senior policy step resolves the user's objective before
repository mutation. Contradictory or unsupported actions stop setup with a
diagnostic. `repository_mode: "isolated"` retains the old private-copy workflow
for explicit use and legacy fixtures; only that mode uses end-of-run delivery and
`output_directory`. Historical runs need a compatible implementation; Resume has
one exact graph-only migration documented in the [workflow guide](../modules/agent-workflow.md).

Choose [export procedures](exports.md) for patches and archive extraction, or
[state layout](state-layout.md) for database/artifact locations. See
[explicit recovery](retrying.md) and [rolling archives](archives.md) for failures.
