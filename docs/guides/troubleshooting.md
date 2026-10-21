# Troubleshooting

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

| Symptom | What to check |
| --- | --- |
| `polyinference: command not found` | Activate the virtual environment and install this checkout with `python -m pip install -e '.[test]'`. |
| `venv` creation fails on Ubuntu | Install `python3-venv` for the Python version you are using. |
| `codex` executable not found | Run `command -v codex` in the backend's Linux terminal. Fix PATH or set the endpoint's `command[0]` to the absolute Linux executable path. A Windows-only installation is insufficient. |
| Codex is not authenticated | Run `codex login status` and, if needed, `codex login` in that same Linux environment. Check account/workspace access and allowance. |
| Anthropic/OpenAI/Gemini returns 401/403 | Check the configured credential variable exists in the server environment, belongs to the right provider and has the required permissions. Reload it and restart the idle server after a change. |
| Provider rejects the model or returns quota errors | Set an accessible model ID in a custom config and verify the account's quota. Probe that lane before another run. |
| Haiku count/cost remains zero | Confirm `worker` binds to an Anthropic endpoint, and inspect whether any junior model request started. Setup and planning alone use Codex in the default setup. |
| Dirty repository / wrong root / missing branch | Commit or stash source changes, select the actual root and ensure the baseline branch exists locally. Remote-only branch names are not fetched automatically. |
| Check command fails or is unavailable | Use executable arguments rather than shell operators; check dependencies/interpreter paths and set `check_execution` appropriately. A disabled or missing check cannot count as passed evidence. |
| Required files are missing or writes are rejected | Include required read/build/test files in `closure_paths`; grant intended writes explicitly or choose project scope before the run. |
| Run stops early | Read the exact blocker. Sprint/query, process, context, token, artifact and wall-time bounds are separate; increasing one may not resolve another. Change settings only for fresh state. |
| Resume reports configuration/program mismatch | Use the original pinned configuration and code, or start fresh state for the new version. |
| Run has uncertain effects | Inspect the operation and provider outcome. Preserve state; an automatic replacement might duplicate an external effect. |
| UI port is occupied | Use `polyinference ui --port 8766`, or stop the existing idle server. |
| Saved runs appear missing | Launch from the same checkout/working directory or use `polyinference ui --state /absolute/path/to/state`. |
| Code did not change in the selected repository | Inspect task worktrees, candidate verdicts and the repository summary. Default in-place coding advances the selected integration checkout only after successful verification; private candidates or explicit isolated mode do not imply root integration. |
