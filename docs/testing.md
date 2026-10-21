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

The OS validation includes the full agent/UI/provider regression suite, the
four-worker failure/drain/replan scenario, restart recovery and a real complete
Codex coding run on macOS. Results and platform limits are recorded in the
[historical OS validation record](../design-docs/simplified-os/VALIDATION.md). Later
Linux/WSL I/O, settings and source-handoff checks are recorded in the
[I/O completion report](../development-docs/io-safety-verification-2026-10-20.md),
with the ordering and limits of its full/focused runs. Neither record proves
physical local-serving performance. Earlier agent-only WSL evidence remains in
the [agent validation record](../design-docs/implementation/VALIDATION.md).

## Documentation checks

```bash
python scripts/project_docs.py --check
python -m pytest tests/test_project_docs.py -q
ruff check scripts/project_docs.py tests/test_project_docs.py
```

Run `python scripts/project_docs.py` after editing the JSON tree, before `--check`.
Add meaningful behavioral regressions when changing runtime guarantees. Choose
focused checks for the affected layer and record limits; historical results do
not count as today's verification. Update related module, settings, design and
usage docs plus FIXES.md in the same task. See [maintenance](maintenance.md).

