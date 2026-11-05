# Plan: develop in the user's actual repository

Proposed on 2026-10-19. Implementation is documented in
[the current boundary guide](../design-docs/simplified-os/RUNTIME_BOUNDARY.md#in-place-coding-repositories).
The proposal below preserves the design rationale; it is not itself an execution
record. Shutdown recovery and next-phase MCP integration are outside scope.

## Intended behavior

The supplied project directory becomes the authoritative project, including its real Git object database, local branches, commits, and checked-out integrated files. New coding runs stop cloning a private bare repository and stop waiting for final acceptance to copy code back.

By default, the coding agent creates an integration branch from the currently checked-out commit and checks it out at the supplied directory. Example names: `codex/run-<id>` and separate worker branches `codex/task-<run>-<task>`. The integration branch is the run's logical main; it does not need to be named `main`. These names deliberately avoid making a branch both a ref and a parent directory of another ref.

Workers use linked worktrees under `<project>/.polyinference/worktrees/<run>/<task>/`. Their branches and commits share the actual repository's Git database. A worker's unfinished edits exist in its worktree; integrated work appears at the project root after each successful integration. This is the proposed interpretation of all work happening in the actual repository: parallel workers have separate checkouts inside the supplied directory, with no second authoritative repository elsewhere.

The agent excludes its worktree directory through local Git exclude metadata, preserving existing entries. Workspace scanning must also exclude this internal subtree. Runtime logs/artifacts can remain in the configured state directory; they are evidence, not the only copy of the source or commits.

## Agent and OS boundary

| Concern | Coding agent | OS |
| --- | --- | --- |
| Repository choice | Select the user's project and request an attached workspace | Validate the authorized filesystem resource and canonical root |
| Git defaults | Resolve user instructions; initialize Git when needed; choose/create/select branches | Execute only explicit granted requests; no automatic Git initialization or branch selection |
| Worker layout | Choose task branches/worktrees or serial direct editing | Attach host-approved file roots, enforce owner/grants, protect metadata |
| Source access | Request full tracked project views and bounded write grants | Expose/read/check the requested view without conflating readable source with writable paths |
| Integration | Reconcile branches, interpret tests, choose merge eligibility | Enforce generic resource ownership, expected versions/content, command bounds and retained effect results |
| Dependencies | Decide installation and verification commands and when each worktree needs them | Run granted commands with execution limits and isolated temporary environment resources |
| Completion | Decide objective acceptance; report branch/commit locations and remaining work | Finish processes and deliver explicit artifacts when requested |

Git command construction and Git outcome interpretation should live in an agent-owned repository component registered through the existing capability mechanism. The OS can retain optional Git/snapshot mechanisms already used by current callers; it must not introduce a new default Git workflow for every agent.

## Resolve Git instructions before setup writes

Persist one coding-agent repository plan before starting setup or workers. It records the actual project root, original branch/commit, integration branch or detached-HEAD target, whether any new branches may be created, worker layout, and the user instruction supporting overrides.

User instructions take precedence over the default. Examples:

- No Git-specific instruction: create a unique run branch from current HEAD; allow task branches/worktrees.
- "Create pi-dev and work there": use pi-dev as integration branch; do not additionally create a default run branch.
- "Use existing pi-dev": require that branch and select it safely; do not silently substitute a new branch.
- "Stay on the current branch; do not create branches": create no run or task branches; use serial direct editing in the existing checkout.
- Explicit no-worktree or different merge instructions: select the compatible coding workflow; serialize root editing when independent worktrees are unavailable.

An explicit prohibition applies to internal worker branches as well. Later user steering supersedes earlier branch policy only after active workers have reached safe boundaries. Ambiguous or incompatible instructions need clarification rather than a guessed Git action. Branch plans are application policy records, not OS configuration defaults.

For a fresh directory without Git, the coding agent initializes the real repository at that path. For an unborn repository, it can use the selected run branch for the first setup commit; no artificial private baseline is necessary. With an existing committed repository, branch creation uses the actual current HEAD. Detached HEAD can seed the default new run branch; an explicit request to stay detached must not be converted silently into branch creation.

Before branch changes, inspect staged, unstaged and untracked files, existing worktree registrations and in-progress Git operations. Preserve user changes. The initial bounded version should stop repository setup with a precise diagnostic when unrelated dirty state prevents a safe run, unless the user has already given handling instructions. Do not automatically stash, commit, reset or clean the user's work.

## Worker finish and integration protocol

1. Read the integration branch's current commit and create a task branch/worktree from it. Check out the full tracked tree so build entry files are available. Limit writes separately through the assignment grant.
2. Develop and commit authorized task changes to that real task branch. Commit construction stages the task's allowed source paths, not every file in the repository. Worker commits remain discoverable even when checks fail.
3. When the worker finishes, acquire the integration resource. Capture the latest integration HEAD and merge it into the worker branch if necessary. Resolve conflicts in that worker worktree under the assignment's authority; conflicts requiring other paths go back to the coding manager.
4. Prepare dependencies for the worktree and run configured checks against the exact reconciled candidate. Changes during checking invalidate that evidence. Independent review uses the actual integration checkout or a prepared worktree, never an unprovisioned fresh copy.
5. Revalidate the captured integration HEAD and that the root is still on the intended branch with no unrelated working-tree/index changes. Fast-forward the root checkout to the verified candidate using a normal worktree-aware Git operation. Do not update a checked-out branch ref behind its worktree/index. If the target changed, reconcile and verify again.
6. Record old/new Git HEAD, task branch, merge outcome and check references in the coding report. The manager's next sprint uses the actual integration branch. SQLite head records cache/describe Git state; they do not become a second authority.

Fast-forwarding a reconciled candidate is the default merge strategy: all integration inputs are already in the verified commit. There is no additional unchecked merge commit after verification. Explicit user merge instructions can choose a different strategy; the resulting tree must still be checked.

Worker completion triggers integration handling, not unconditional acceptance. Passing, reconciled tasks merge. Failed, blocked or unverifiable work remains on its named task branch/worktree for inspection or a replacement worker. Replacement tasks explicitly receive that existing branch/commit instead of reconstructing it from a scaffold. An exceptional decision to integrate uncertain work belongs to a recorded manager decision with its limitations visible.

In the no-new-branches mode, use one active editor on the root checkout, verify and commit on the current branch, then let the manager continue from that commit. No merge is needed. Failed edits remain visible with an explicit diagnostic; no destructive automatic rollback. This mode cannot provide the same branch isolation as the default, and that difference must appear in the run status.

## Bounded OS changes

Add an opt-in attached-directory workspace path for the current coding agent. It needs process ownership, canonical root validation, path grants, read/write content checks and declared generated-output handling. Protect `.git` entries and the shared Git directory from ordinary file tools; only explicitly granted repository handlers may mutate Git metadata.

The root integration checkout and worker worktrees share a Git database but need separate file ownership. Use existing generic exclusive resources for each mutating worktree and the shared integration operation. Derive the repository resource identity from the canonical common Git directory so separate runs targeting the same repository do not bypass each other. The coding agent holds the root integration resource while it controls that checkout; it serializes integration/check operations as required. Ordinary external editors do not honor OS leases, so detect branch, index, source and ref drift and stop/reconcile rather than overwrite it. These locks are coordination, not a promise of filesystem atomicity against arbitrary external processes.

Git updates and SQLite reports cannot form one transaction. Record the explicit operation intent with expected Git identity; execute the Git operation; retain observed outcome and then publish the coding report. If result recording fails, stop further mutation and report uncertainty. Do not claim record CAS makes a checkout/merge atomic. This requires only current effect semantics, not a new shutdown-recovery project.

Attached workspaces must not use the current private-copy rollback that deletes/reconstructs an entire directory. Validate file mutations before applying them; use non-destructive per-path updates. Shell commands operate under the existing configured execution backend; preserve the current warning/limits of trusted execution rather than claiming post-command auditing is a sandbox. On a scope violation, retain evidence and stop affected editing instead of deleting the actual checkout or user files. Disposable build/test data stays in declared outputs or temporary storage.

Make repository initialization and selection explicit opt-in resource operations. A general process with workspace mode `none` continues to use inference, artifacts, records and user messages without touching a project directory, Git, checks or coding state. Lazy/optional file and repository services are sufficient. Do not add research workflows, MCP discovery, tool marketplaces or a universal VCS framework.

## Changes to the current code

| Area | Planned change |
| --- | --- |
| `agent/setup.py`, `agent/prompts.py`, `AgentConfig` | Resolve/persist Git policy before setup; choose the actual integration branch; honor user overrides |
| New agent repository component and `agent/services.py` | Register typed coding Git capabilities; own branch/worktree/reconcile/merge policy and explicit candidate handoff |
| `agent/worker.py`, `agent/controller.py`, `agent/runtime_policy.py` | Replace private candidate publication with real task commits and verified integration; manager reads actual integration HEAD |
| `runtime/workspace.py`, `ports.py`, workspace contracts | Add attached-root semantics and optional resource initialization; preserve grants and source-evidence checks |
| `runtime/shell.py`, file mutation paths | Remove destructive private-copy restore from attached workspaces; report scope violations without deleting the user's tree |
| `runtime/kernel.py` | Continue enforcing generic capability/effect/resource rules; replace coding-specific commit assumptions on the new path with registered coding handlers/policy |
| UI/CLI/export and final reporting | Show actual root, original/integration/worker branches, commits, worktree paths and unmerged work; remove "awaiting copy-back" semantics for repository runs |

The existing artifact delivery capability remains available for explicit file/artifact outputs. Successful in-place coding does not require `outputs.deliver`; the actual checkout is already updated after integration.

## End-of-run behavior

Leave the integration branch checked out at the supplied project path by default. Do not automatically merge it into the original branch, push, rewrite history, or switch back. Retain failed/unmerged task branches and their worktrees, including dirty files. Clean worktrees already integrated may be removed through explicit agent cleanup policy; branch/commit provenance must remain inspectable.

On completion, failure or a normal pause, provide a deterministic agent-generated repository summary: project path, original branch/commit, chosen integration branch and why, final HEAD, merged tasks, remaining branches/worktrees and uncommitted paths, check status, and whether any user-requested merge-back/push occurred. If an explicit instruction prevented branches, state that work used the existing branch. The UI should expose this throughout the run; it must not depend on an LLM remembering it in final prose.

## Delivery sequence and acceptance checks

1. Define the agent repository plan and instruction precedence; document the default linked-worktree interpretation and serial override.
2. Implement attached file resources and non-destructive mutation semantics with generic capability/ownership tests.
3. Wire agent setup and worker task branches, real commits and verified integration; remove end-only code delivery on this path.
4. Wire manager review, candidate reuse, dependency preparation, status/export and deterministic final reporting.
5. Validate coding and general-agent regressions, then make in-place execution the default for new coding runs. Version the changed contracts; existing historical runs retain their pinned layout and are not silently migrated.

Required behavioral tests:

- A fresh coding run creates the selected branch/commits in the real repository; integrated files are visible at the given path before final completion.
- Explicit current-branch/no-new-branch instructions create zero branches/worktrees and use serial editing; a named branch override does not create a second integration branch.
- Two workers share one actual Git database and integrate against the latest HEAD; merge conflicts and stale target checks cannot publish unchecked work.
- A failed task remains discoverable and a replacement can continue its branch; normal interruption does not require final artifact delivery for code visibility.
- Dirty initial state and out-of-band ref/index/source changes are preserved; attached-workspace scope failure never removes the project or unrelated files.
- Worker and independent review checks prepare dependencies and identify the exact resulting source revision.
- Final and paused-run status accurately enumerate branches, commits, files and unmerged work.
- A general/storytelling fixture completes with no Git initialization, branches, worktrees, compiler checks, TaskSpecs or coding finalization. Existing artifact-only and native workspace-none tests continue to pass.

No production code, repository branch, current run or existing history is changed by this plan.
