# Launch the local UI

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

From the PolyInference checkout, with the virtual environment active and credentials
loaded:

```bash
polyinference ui
```

The coding UI cloud agent uses a 1800-second warning threshold and inherits
cloud_agent_timeout_interrupt=false; presets and endpoint profiles do not enable
interruption. Explicit caller configuration may still select true.

Plain `polyinference ui` reads optional machine preferences from
`$XDG_CONFIG_HOME/polyinference/ui-defaults.json` (default
`~/.config/polyinference/ui-defaults.json`). The JSON object accepts only `local`
(a complete endpoint), `local_token_limits`, `max_workers`, `local_strata_config` and `local_strata_profile`.
The endpoint replaces the Haiku preset, including its credentials. Strata paths
resolve relative to this preference file. This machine's 128K coding preset uses
114688 input (112K) plus 16384 output (16K) tokens, with local.max_inflight and
max_workers both 1. Output includes reasoning. This prioritizes repository/tool
context while retaining room for edits; it is a starting preference, not a measured optimum. Set local_strata_profile to a saved Strata profile name to start its
engine automatically before the UI opens. Its launch JSON must use the matching
context and parallel=1, batch_groups=1. Machine preferences retain the project picker and grants.
Explicit `ui --config` bypasses them; saved-run Resume retains its saved settings.
`--sim-batch` applies afterward and selects remote Haiku for a declared local endpoint,
even when Strata uses the Anthropic wire protocol. Invalid preferences fail visibly.
These are coding-application preferences; generic OS defaults remain unchanged.
With local_strata_profile and a declared loopback local endpoint, UI startup reuses
a ready engine or starts a stopped profile and waits for generation readiness.
Strata is found on PATH or at ~/.local/bin/strata. The UI checks live model/context/
slots, reports failures, and never restarts a mismatched or failed engine. A startup
already in progress is awaited. A changed live launch config requires stopping that
profile first. Without this setting, start Strata separately. Explicit remote
simulation skips automatic startup. Preparation precedes saved-run restoration;
Resume still retains saved settings. A runtime started by this UI is tied to its
process with Strata's --die-with-pid watcher. Normal exit, Ctrl+C, SIGTERM and
terminal SIGHUP also stop the captured owner/instance; startup failures clean up
before opening HTTP. SIGKILL cannot run Python cleanup, so Strata detects process
death and stops its server/engine tree. New instances use a 10-second drain budget,
followed by Strata's bounded termination handling; release need not be immediate.
A ready/starting runtime reused from another launch is not adopted or stopped;
reuse does not extend the original owner's lifetime.
Cleanup failures are printed; guarded stops never fall back to killing a port or
profile replacement. A later UI launch starts its stopped profile again.

Open **[http://localhost:8765](http://localhost:8765)** in your browser. On Windows,
the browser can connect to the backend running inside WSL. Keep the terminal open.
The server binds to `127.0.0.1`; it is intended for use on your own machine.
For this server's new runs, `polyinference ui --sim-batch 2` selects two workers
and remote Haiku inference slots, with matching context reservation. N is 1..16.
It overrides the legacy capacity environment variable for this invocation only.
The launch/UI label names the effective model and limits; Start run still requires
an objective/project and a nonempty referenced credential. See
[simulation details](../../codex-haiku-setup.md) before interpreting concurrency.
To add opt-in latency/fault controls before Start, use `polyinference ui
--sim-inference`; see [the three modes and their limits](sim-inference.md).
Without this flag, ordinary launches retain their existing behavior and UI.

For later launches:

```bash
cd ~/projects/polyinference
source .venv-linux/bin/activate
polyinference ui
```

Use `polyinference ui --port 8766` and open `http://localhost:8766` if the default
port is occupied. After the active run settles, **Ctrl+C** stops the foreground
server. Closing the browser tab does not stop the server or its run. Stopping the
backend during work is an interruption, not a graceful pause/cancel feature.

Next: [First run](first-run.md) · [Project runs](projects.md).
