# Export code and diagnostic evidence

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

There are two separate exports:

- **UI Save run · JSON** downloads the selected run's OS overview, full durable
  records and revisions, retained event journal, raw checkpoints, exact artifact
  bytes, processes, nodes, prompts,
  responses, tool/operation artifacts, reports, steering, setup information,
  configuration metadata, allocation and cost estimates. It is for debugging;
  it is not a code patch. It can contain project source and task text, so review
  it before sharing.
- **CLI patch export** writes the difference between the stored initial and
  provisional heads, including binary diffs. It does not depend on a model's
  description of its edits.

To export a UI run, replace `RUN_ID` with the selected run's ID:

```bash
polyinference status .polyinference/ui/runs/RUN_ID/state
polyinference export .polyinference/ui/runs/RUN_ID/state /tmp/polyinference-result.patch
```

For the custom CLI configuration in the [configuration guide](configuration.md):

```bash
polyinference export .polyinference/my-project-state /tmp/polyinference-result.patch
```

Inspect the run status, reviewed/provisional heads and unresolved reports first.
In-place runs merge successful, verified candidates. Failed or uncertain candidates
remain on task branches. A partial export can include integrated work that has not
passed project-level acceptance. Legacy isolated runs may also provisionally retain
uncertain work. Do not reapply a patch to the same checkout that already contains it.

Apply a reviewed patch in a clean checkout at the **same baseline revision and
branch used by that run**:

```bash
cd /absolute/path/to/target-repository
git apply --stat /tmp/polyinference-result.patch
git apply --check /tmp/polyinference-result.patch
git apply /tmp/polyinference-result.patch
```

Then run your checks, review the diff and commit it yourself. If setup selected a
different baseline branch, switch your receiving checkout to that baseline first.
A patch is a content diff; it does not recreate branch names or commit history.

You can extract a resulting tree into a separate,
empty output directory instead. Replace `COMMIT_ID` with the desired commit ID
from the provisional/reviewed head in `polyinference status STATE`, and use the
absolute path to that run's state directory:

```bash
mkdir -p /absolute/path/to/new-output
git -C /absolute/path/to/project archive COMMIT_ID \
  | tar -x -C /absolute/path/to/new-output
```

This uses `tar` and exports files without Git metadata. In-place commits remain
in the project's Git database. For a historical isolated run, use
`git --git-dir=STATE/repository.git archive COMMIT_ID` instead. Retain state for
execution evidence and retain unfinished worktrees for their uncommitted files.

Related: [Result locations](results.md) · [State layout](state-layout.md).
