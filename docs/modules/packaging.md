# Packaging and repository hygiene

[Modules](README.md) · [Setup](../../setup.md)

| File | Responsibility |
| --- | --- |
| [pyproject.toml](../../pyproject.toml) | Python version/dependency pins, setuptools packages/UI assets, CLI entry point, pytest and Ruff configuration. |
| [requirements.lock](../../requirements.lock) | Recorded tested transitive Python environment. |
| [.gitignore](../../.gitignore) | Exclude credentials, caches, builds, generated projects and runtime/history data. |

The wheel packages `src/polyinference`, including `ui.html` and `ui-monitor.js`.
Documentation/navigation tooling runs from the checkout and is not a runtime
service or dependency. No frontend build is required for the local UI.

Version intentional source and evidence. Keep generated project experiments in
`testing/`, implementation checks in `tests/`, and runtime state in ignored
`.polyinference/`. Ignore rules do not establish source authority or override
tracked/granted file protection.

Use the [installation guide](../guides/install.md) for environment reproduction
and [checks](../testing.md) for wheel validation. After dependency, asset or
packaging changes, update setup, this guide, related settings docs, navigation
and [FIXES.md](../../development-docs/FIXES.md) in the same task.
