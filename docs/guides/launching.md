# Launch the local UI

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

From the PolyInference checkout, with the virtual environment active and credentials
loaded:

```bash
polyinference ui
```

Open **[http://localhost:8765](http://localhost:8765)** in your browser. On Windows,
the browser can connect to the backend running inside WSL. Keep the terminal open.
The server binds to `127.0.0.1`; it is intended for use on your own machine.
For this server's new runs, `polyinference ui --sim-batch 2` selects two workers
and remote Haiku inference slots, with matching context reservation. N is 1..16.
It overrides the legacy capacity environment variable for this invocation only.
The launch/UI label names the effective model and limits; Start run still requires
an objective/project and a nonempty referenced credential. See
[simulation details](../../codex-haiku-setup.md) before interpreting concurrency.

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
