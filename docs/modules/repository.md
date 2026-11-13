# Coding repository policy and retained source

Default coding work uses the selected actual repository, integration branch and linked task worktrees.

| File | Responsibility |
| --- | --- |
| [src/polyinference/agent/repository.py](../../src/polyinference/agent/repository.py) | Git policy/setup, RepositoryWorkspaces, preparation, verified integration, retained candidates and interrupted-source handoff. |
| [src/polyinference/agent/reports.py](../../src/polyinference/agent/reports.py) | Coding reports/commit receipts and commit-free test results. |
| [src/polyinference/os_contracts.py](../../src/polyinference/os_contracts.py) | Compatibility imports of application-owned report extensions. |

## Interface and ownership

The agent installs RepositoryWorkspaces over generic OS attached-directory grants
and leases. In-place is the default; isolated mode is explicit. Failed preparation
reaches engineers as evidence; configured checks still run after known failure.
Senior retained_sources offers describe exact resume_from references, required
write paths and current integration conflicts for private candidates/interrupted
source. Validation corrects unavailable references or incomplete grants before
dispatch; materialization rechecks them. References carry one whole scoped delta,
not arbitrary selective multi-candidate access. Publication rules are mode-specific.
Repository summaries separate tip/candidate ancestry, dirty source, publication
receipts and kept nonempty contributions. An inherited tip or empty publication
does not establish an accepted task contribution; review remains a separate fact.
Test-only reports carry a tested revision and observations instead of a candidate commit.
They appear as `test_result` in repository summaries, with no accepted code contribution;
rejecting the result does not run a Git revert. Source offers skip these non-candidate
reports, preserving normal private-source handoffs when both result kinds coexist.

The repository provider consumes the resolved OS workspace ignore names from
central tuning (`docs/guides/os-tuning.md`); branch/commit/acceptance policy remains
owned by this application.

## Principles to preserve

- The user-selected path is authoritative, including new/nested projects.
- Git choices, retries, dependency commands and acceptance are coding policy.
- Protect root branch/HEAD/index and existing edits before integration.
- Preserve failed/uncertain source privately; reuse needs explicit resume_from, scope and base checks.
- Git mutations and SQLite report publication are separate effects; uncertain outcomes stop mutation.

## Verification and related reading

[In-place repository](../../tests/test_in_place_repository.py), [recovery](../../tests/test_recovery.py)
and [workspace outputs](../../tests/test_workspace_outputs.py).

Boundary: repository guarantees (`design-docs/simplified-os/boundary/repository.md#in-place-coding-repositories`) · `development-docs/FIXES.md#fix-0001` · `development-docs/FIXES.md#fix-0060`.

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in `development-docs/FIXES.md`.
Follow documentation maintenance (`docs/maintenance.md`) in the same task.

## Integrated reliability branch (2026-10-26)

New exception references select a separately validated development delta rather
than masquerading as private commit IDs. Attached handoffs preserve Git control
files, ignored dependencies and original source through materialize_view.
Global active preparation issues exclude completed independent-review workspaces;
their failed check/preparation records remain historical evidence. Current scoped
worker failures are still reported and retried under the original authority.
