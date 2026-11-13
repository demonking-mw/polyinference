# Repository integration and retained source

## In-place coding repositories

The agent also supports `kind: test` assignments that run existing checks without
source edits or result files. Their tested revision, observations and receipts are
agent records, not coding publications. They reuse existing processes, workspaces,
checks, permits, artifacts and atomic records. The only shared SDK change is allowing
`TaskSpec.allowed_change_scope: []` to express no source-write authority; edit tasks
still require a target in agent validation. No OS implementation or task semantics
were added. See `development-docs/FIXES.md#fix-0178`.

New coding runs use the actual supplied repository. `AgentConfig.repository_mode`
defaults to `in_place`; bare `RuntimeConfig` has no such workflow setting.
`agent/repository.py` implements Git policy and the application's workspace provider.
The coding app installs it with the OS's trusted `install_workspaces` bootstrap
method. No OS module imports it. The legacy private-copy provider remains available
through explicit `repository_mode: "isolated"` for existing consumers and fixtures.

Before setup edits, a read-only senior process resolves the user's Git instructions
into `coding/repository-policy`. Structured `git_policy`/`base_branch` configuration
can pin the decision. The application creates/selects a real integration branch
from current HEAD; the default is `codex/run-<state-id>`. "No new branches" also
disables worker branches and uses one editor on the current checkout. The coding
agent sends recoverable branch/policy errors back to its senior process for a
corrected decision. Attention notes reach setup without rejecting ordinary local
development; they do not authorize ignoring explicit user constraints.

Startup recovery is application policy in `agent/repository.py`, with observations
and prompts assembled by `agent/services.py` and `agent/prompts.py`. Nested project
initialization, Git selection retries and dependency preparation decisions use the
existing generic capability and record interfaces. Their diagnostics live under
`coding/` records. No OS hook, configuration field, wire contract or protocol rule
is added for this recovery flow. Other agents need no Git policy, setup task,
dependency preparation or coding acceptance checks to run or finish.

Workers check out full tracked source into linked task worktrees under the supplied
project's `.polyinference/worktrees/`. They share its actual common Git database.
The OS's `attach` method validates directory authority, ownership and write grants;
it does not infer Git branches, task policy or acceptance. Ordinary file tools cannot
address `.git` or runtime control data. The attached source view remains stable across
phase-generation changes; it is not recopied over user files.

The agent registers `coding.prepare`, `coding.commit` and `coding.publish` handlers
through the existing typed capability/effect mechanism. They own repository policy,
commit provenance, candidate scope and verified integration. Publication checks the
current root branch, HEAD, source/index cleanliness and task index before changing
the actual checkout. A candidate includes the captured integration commit and its
previous task tip; the root fast-forwards to the checked candidate. Failed/uncertain
candidates remain on real task branches. A replacement's explicit `resume_from`
names a retained candidate and receives its scoped edits with conflict checks.
The agent supplies read-only retained-source planning offers and validates exact
references/grants before dispatch; materialization rechecks current conflicts.
This adds no OS Git/source-reading capability or automatic publication authority.

Git and SQLite are separate resources: intent/outcome records and retained effects
do not make a filesystem merge atomic with report publication. A completed merge
whose report cannot be recorded is uncertain and stops further mutation.

> **Edited 2026-10-20 because** real task history and the user's actual checkout
> supersede sole-parent/provisional-all assumptions: retain the prior task tip
> when needed, integrate only successful verified candidates, and preserve
> failed/uncertain candidates for explicit repair/review (FIX-0040, R03/R04).

Generic
OS `filesystem/<canonical-resource-digest>` leases also hold advisory file locks
across independent runtimes. The agent derives the shared Git-directory identity
and owns the integration checkout for the run. External editors do not honor those
leases; detected edits or index/ref drift stop integration without overwriting them.

Attached workspaces never use private-copy directory rollback. A shell scope failure
preserves files and blocks further mutations on that workspace. Trusted shell still
has host privileges; after-command auditing is not a sandbox. The selected sandbox
or trusted execution backend retains its existing meaning.

The coding agent prepares dependencies before brokered checks. Locked npm projects
use `npm ci --ignore-scripts`; `dependency_prepare` supplies other explicit argv.
Commands still require the shell capability and its configured backend. Review and
acceptance check the root integration checkout, with source identity tied to evidence.
The OS executes commands and stores evidence; it does not select package managers.
The coding agent retains failed preparation output as an observation and continues
to configured checks so its engineers can repair and recheck prerequisites. Unknown
execution termination still stops mutation under the existing OS guarantees.

Completion updates the in-place output record without `outputs.deliver`. The agent
retains `coding/repository-summary` and sends a deterministic user message on normal
completion/failure/pause. UI, CLI status and exports include branch/commit/worktree
locations. The root stays on the integration branch; there is no automatic push,
merge-back or branch cleanup. The artifact delivery service remains optional for
other workflows.
The coding summary distinguishes ancestry, dirty/private source, publication and
kept nonempty contributions; it never interprets inherited ancestry as new work.

The current coding marker is `agent-9-local-contracts`, state schema `2.8`.
New runs require fresh state. Older layouts are not migrated. Updated 2026-10-23:
the exact graph-only Resume compatibility path below preserves layout and prior outcomes.
Context measurement separates input tokens/provenance, serialized bytes and output reservation; caller
priorities are generic hints. Relevance, frozen-source diagnosis and semantic recovery of clean unusable
output remain agent policy. See the context contract (`docs/guides/context-measurement.md`).
The OS marker is `simple-os/6`; an artifact-only or workspace-none process still
requires no Git, coding task, check or code-writing finalization. MCP and shutdown
recovery are not expanded by this change. The sections below describe shared
mechanisms; private-copy details apply to the legacy optional provider.

The current agent negotiates `runtime/attached-workspace` for this layout.
Git-specific report extensions live in `agent/reports.py`; `os_contracts.py` is a
compatibility import. Git steering changes wait for started workers to drain.
An existing branch at a different commit needs a new run, preserving current
task/evidence identities.
