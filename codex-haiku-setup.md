# Tester checklist: Codex + Haiku

[Setup](setup.md) · [Documentation](docs/README.md) · [Developer onboarding](dev-readme.md)

Record the requested testing branch and HEAD with `git branch --show-current`
and `git rev-parse HEAD`. Follow [installation](docs/guides/install.md), including
the lockfile recipe when reproducing a recorded Linux/macOS environment.

| Lane / role | Pinned UI preset |
| --- | --- |
| `local` / `worker` | Anthropic `claude-haiku-5-5`, one in-flight request |
| `cloud` / `senior`, `specialist` | `codex_app_server`, `gpt-6.1-sol`, medium turn effort, brokered tools, one request |

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
   trusted shell/check execution and 27 sprints. Raw queries target 4096 tokens
   inside a 32k hard ceiling. The mixed JSON example has different concurrency.
4. Follow the [greeting smoke test](docs/guides/first-run.md). Inspect worker
   calls on `local` and senior/specialist calls on `cloud`; the saved config must
   show `max_workers:1` and both `max_inflight:1`. Require final acceptance/check
   evidence, then **Save run · JSON**.
5. Follow the [project run guide](docs/guides/projects.md) for a disposable task
   under ignored `testing/`. Record its integration branch, commit and worktree
   paths. Keep state/evidence if a run pauses; see [troubleshooting](docs/guides/troubleshooting.md).

For later launches, reactivate the checkout environment and repeat step 3.
For concurrent remote simulation, use:

```bash
polyinference ui --sim-batch 2
```

N accepts 1..16: N workers/local slots and at least N full-context reservations.
It overrides ambient capacity for this server's new runs without changing the
environment or later launches. Custom Anthropic settings survive; another local
protocol selects the full Haiku preset. Senior/cloud settings remain explicit.
Opening the UI makes no billed request. New runs save effective configuration;
Resume uses saved settings and suppresses ambient capacity overlays. See
[configuration](docs/guides/configuration.md) and [recovery](docs/guides/recovery.md).

Slots are maximums, not guaranteed occupancy. Use independent tasks to exercise
overlap; the greeting asks for one. No-task-branch Git policy still permits only
one editor. This simulates request admission/refill, not GPU token-step batching,
KV memory, latency/throughput or Anthropic's Message Batches API. Shared account
quotas still apply. Model availability was rechecked against the
[official Haiku overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview);
account access requires its own readiness evidence.

For pacing/fault controls, use `polyinference ui --sim-inference`. Its active
mode's batch takes precedence over --sim-batch; normal mode retains it. The
[simulation guide](docs/guides/sim-inference.md) covers defaults, fault decisions,
timing and recovery. Actual Haiku usage remains recorded.

[Launch controls](docs/guides/launching.md) cover ports and stopping the idle server.
Snapshots are diagnostic evidence, not complete Git backups or resumable state.
See [provider distinctions](docs/guides/providers.md) before selecting `codex_proxy`.

Report each finding in [current iteration](development-docs/current-iter-issues.md),
[next iteration](development-docs/next-iteration.md), or [general issues](development-docs/general-issues.md)
for triage. Include branch/commit, OS/Python/Codex versions, objective/check, run ID,
models/batch, reproduction, expected/actual behavior, errors and snapshot location.
Separate observations from suspected causes; include setup/UX friction and review
sensitive content before sharing evidence.

When implementing a fix/feature, update all related docs and navigation plus
[FIXES.md](development-docs/FIXES.md) in the same task. Follow [maintenance](docs/maintenance.md).
