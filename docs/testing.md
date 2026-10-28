# Checks and verification

[Documentation](README.md) · [Setup](../setup.md) · [Developer guide](../dev-readme.md)

From the checkout with the virtual environment activated:

```bash
python -m pip install -e '.[test]'
pytest -q
ruff check src tests
python -m pip wheel --no-deps --wheel-dir .polyinference/wheels .
```

The automated suite uses disposable Git repositories, real TCP/stdio fixtures
and adversarial execution schedules. It covers provider protocols, workspace
contracts, setup/branch handling, brokered tools, publication/replay, steering,
UI exports and cost accounting without requiring live provider credentials.

Historical OS validation includes agent/UI/provider regressions, the four-worker
drain/replan scenario, restart recovery and a small Codex coding run on macOS.
Those results and platform limits are recorded in the
[historical OS validation record](../design-docs/simplified-os/VALIDATION.md). Later
Linux/WSL I/O, settings and source-handoff checks are recorded in the
[I/O completion report](../development-docs/io-safety-verification-2026-10-20.md),
with the ordering and limits of its full/focused runs. Neither record proves
physical local-serving performance. Earlier agent-only WSL evidence remains in
the [agent validation record](../design-docs/implementation/VALIDATION.md).

The [four-repair record](../development-docs/four-repairs-implementation-2026-10-28.md)
contains current framework checks and source limits; the [27 October record](../development-docs/reliability-implementation-2026-10-27.md)
retains the earlier qualification evidence.
The historical [26 October integrated-tree audit](../development-docs/branch-integration-audit-2026-10-26.md#verification-record)
recorded 585 passed, 5 baseline failures and 2 skips
across a full run plus focused reruns, not one all-green suite. The separate
[local Strata test](../development-docs/local-strata-live-test-2026-10-26.md) passed
25 project tests but failed browser/product verification. Neither fixture counts
nor historical live checks establish current end-to-end readiness.

[Cloud recovery regressions](../tests/test_cloud_recovery.py) exercise actual
controller dispatch to a fixture cloud worker, quota immunity, shared accounts/
deadlines, transitive pending-plan rewiring, finite attempts and hard blockers.
They establish policy behavior, not live model convergence or product acceptance.

## Documentation checks

```bash
python scripts/project_docs.py --check
python scripts/settings_docs.py --check
python -m pytest tests/test_project_docs.py -q
ruff check scripts/project_docs.py tests/test_project_docs.py
```

Run `python scripts/project_docs.py` after editing the JSON tree, before `--check`.
Add meaningful behavioral regressions when changing runtime guarantees. Choose
focused checks for the affected layer and record limits; historical results do
not count as today's verification. Update related module, settings, design and
usage docs plus FIXES.md in the same task. See [maintenance](maintenance.md).

Use the [qualification harness](guides/qualification.md) for three fresh small
workflows plus a settled interruption/resume. Scripted fixture results and real
model/browser qualification must be reported separately, with source/profile pins.

