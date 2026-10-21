# Tester checklist: Codex + serial Haiku

[Setup](setup.md) · [Documentation](docs/README.md) · [Developer onboarding](dev-readme.md)

Use the requested testing branch. Record `git branch --show-current` and
`git rev-parse HEAD` with your findings. Reuse or create the Linux/macOS test
environment using [installation](docs/guides/install.md); install the lockfile
before the editable package when reproducing the recorded environment.

| Lane / role | Pinned UI preset |
| --- | --- |
| `local` / `worker` | Anthropic `claude-haiku-5-5`, one in-flight request |
| `cloud` / `senior`, `specialist` | `codex_app_server`, `gpt-6.1-sol`, low effort, brokered tools, one request |

The lane names do not describe physical hosting. Haiku is a paid cloud stand-in
for serial local admission; this is neither Anthropic's Batch API nor a hardware
performance model. One worker and one inference slot are separate limits. Model
IDs require account access; record rejections and agree on replacements before
comparing results.

1. Install and authenticate [Codex on the backend host](docs/guides/codex-login.md).
   WSL needs its own Linux Codex installation/login. The backend launches stdio
   app-server automatically; no HTTP proxy or `OPENAI_API_KEY` is needed here.
2. Supply [Anthropic credentials](docs/guides/anthropic-key.md) in that host's
   environment or private saved file. Existing exported values override the file;
   use `unset ANTHROPIC_API_KEY` to let a later launch read the saved value.
3. Launch **without `--config`** from the activated checkout:

   ```bash
   POLYINFERENCE_LOCAL_BATCH_SIZE=1 polyinference ui
   ```

   The variable applies only to this launch. The default UI has one worker,
   trusted shell/check execution, 27 sprints and 32k output. Copying the mixed
   JSON example selects different concurrency settings.
4. Follow the [greeting smoke test](docs/guides/first-run.md). Inspect worker
   calls on `local` and senior/specialist calls on `cloud`; the saved config must
   show `max_workers:1` and both `max_inflight:1`. Require final acceptance/check
   evidence, then **Save run · JSON**.
5. Follow the [project run guide](docs/guides/projects.md) for a disposable task
   under ignored `testing/`. Record its integration branch, commit and worktree
   paths. Keep state/evidence if a run pauses; see [troubleshooting](docs/guides/troubleshooting.md).

For later launches, reactivate the checkout environment and repeat step 3.
[Launch controls](docs/guides/launching.md) cover ports and stopping the idle server.
Snapshots are diagnostic evidence, not complete Git backups or resumable state.
See [provider distinctions](docs/guides/providers.md) before selecting `codex_proxy`.

Report each finding in [current iteration](development-docs/current-iter-issues.md),
[next iteration](development-docs/next-iteration.md), or [general issues](development-docs/general-issues.md)
for later triage. Include branch/commit, OS/Python/Codex versions, objective/check,
run ID, models, batch size, reproduction, expected/actual behavior, exact errors
and snapshot location. Separate observations from suspected causes; include UX
and setup friction. Review sensitive project content before sharing evidence.

When implementing a fix/feature, update all related docs and navigation plus
[FIXES.md](development-docs/FIXES.md) in the same task. Follow [maintenance](docs/maintenance.md).
