# PolyInference agent

A portable LangGraph coding agent implementing the audited sprint/worker/senior
design. The bundled standalone runtime is a placeholder OS: static endpoint
routing, direct tools, SQLite records, private workspaces, and two ownership gates.
It does not implement a model server or the future OS scheduler.

The implementation incorporates the [user's review answers](design-docs/implementation/user-agent-review.json).
See [implementation and adapter notes](design-docs/implementation/README.md) and
[the validation record](design-docs/implementation/VALIDATION.md).

## Install and test

Use Linux or WSL, Python 3.10+, and Git. Put runtime state on a Linux filesystem.

```bash
python3 -m venv .venv-linux
. .venv-linux/bin/activate
pip install -e '.[test]'
pytest -q
ruff check src tests
```

Direct dependencies are pinned in `pyproject.toml`; `requirements.lock` captures
the tested complete environment. LangGraph source is unchanged.

## Simple test UI

From the project directory in WSL:

```bash
source .venv-linux/bin/activate
polyinference ui
```

Open **http://localhost:8765** and click **Run test**. The default is a tiny Codex
greeting task using your existing subscription. Each click creates fresh state.
After the run, processes and executed nodes appear in order. Click a blue model
node to see its prompt and response. Other nodes show their input, output and
recorded tool results. The run selector keeps previous tests available.

The extra controls are deliberately small:

* **Root repository**: enter a WSL/Linux Git root or click **Browse…**. Commit or
  stash local changes first. The agent develops in a private copy of committed
  HEAD. For another repository, enter its objective and inspect **Check command**;
  Python and npm test commands are suggested when available. Without `--config`,
  all committed regular files are in scope. With `--config`, its explicit file
  grants, endpoint bindings and checks remain in force.
* **Export JSON**: download the selected run's processes, full node input/output,
  prompts, responses, operation artifacts, reports, steering and cost estimates.
* **Costs**: per-run Codex/Haiku estimates and the total across saved runs update
  automatically. Missing prices or usage produce a `+` and an explanation under
  **About cost estimates**. Codex shows an API-equivalent estimate, not the cost
  charged to your subscription. Rates are recorded with their date and source
  links in the export; no billing API is required.
* **Steering**: while a run is active, expand the steering panel, enter updated
  instructions and click **Send update**. The panel tracks received and pending
  instructions. Started workers finish before the senior reviews the update;
  it does not stop workers immediately.

To use your own configured task or inspect an existing run:

```bash
polyinference ui --config path/to/agent.json
polyinference ui --state path/to/state-directory
```

The UI reads the real LangGraph checkpoints and operation artifacts. It also
shows failed/interrupted runs, and binds only to the local machine. UI run state
is stored under `.polyinference/ui/`. Use `--port 8766` if needed.

## Configure endpoints

Copy [the example](examples/agent.openai.json) and replace the repository, objective,
exact writable file paths, read/build/test closure, configured checks, and model
names. Paths are relative to the configuration file. Credential values come only
from the named environment variables.

* OpenAI: `responses` or `chat`, normally with `OPENAI_API_KEY`.
* Gemini: `gemini`, `https://generativelanguage.googleapis.com/v1beta`,
  with `GEMINI_API_KEY`.
* Anthropic Claude: `anthropic`, `https://api.anthropic.com/v1`, with
  `ANTHROPIC_API_KEY`. See [the Claude example](examples/agent.anthropic.json).
* Local servers: OpenAI-compatible `chat` or `responses`.
* Codex subscription agent: `codex_app_server`, authenticated separately with
  the official Codex CLI. Enable `brokered_tools` for coding roles. See
  [the Codex example](examples/agent.codex.json).
* A separately installed mehdic-compatible proxy: `codex_proxy`, for read-only
  senior queries with an explicitly pinned snapshot directory. Opaque proxy coding
  jobs are rejected. The direct app-server adapter is the functional native coding
  path; no third-party proxy is installed automatically.

The endpoint called `local` is the worker lane; it can point at another cloud API
for v1 tests. Physical inference location is recorded separately. Pin role bindings
before starting a run. All-local, all-cloud, and mixed configurations use the same
worker/publication protocol.

Check commands are administrator-configured argv lists. The model can request a
configured name and cannot supply shell text. `check_execution` defaults to
`disabled`, yielding unavailable evidence. Select `trusted` for checks you trust
to run on the host, or `bubblewrap` for a restricted Linux environment when bwrap
is installed. Trusted checks are executable code, not an OS sandbox. Background
services and remote mutations are outside this placeholder's tool profile.

## Run

```bash
export OPENAI_API_KEY='...'  # Or the credential for your configured provider.
polyinference validate-config path/to/agent.json
polyinference probe path/to/agent.json --endpoint cloud
polyinference run path/to/agent.json
polyinference status path/to/state-directory
polyinference steer path/to/state-directory 'Updated instructions'
polyinference resume path/to/agent.json
```

Steering closes new starts immediately. Started workers, including gate and model
waiters, finish on their original assignment before senior planning consumes the
input. Superseded unstarted tasks can be explicitly cancelled by the next plan.

The runtime clones the configured repository's committed HEAD into its own Git
store. It never edits the source checkout. Start from a clean committed revision;
dirty/untracked source inputs are rejected. Every assessed verdict publishes a real
commit to provisional history, with an unresolved immutable report. Senior review
is a separate record, and independent final checks guard project completion.
Use `polyinference export STATE OUTPUT.patch` to export the initial-to-provisional
patch for inspection. State also contains the actual Git objects and commit IDs.

Each report keeps its verdict explanation. Shared notes remain visible to workers
until a senior `memory_update` records a source-linked refinement; original notes
and reports remain available afterward.

## Bounds and recovery

Defaults permit 512 model calls and 2,048 steps per worker, with reserved final
phases and a one-hour deadline. Process and parent token reservations are enforced
conservatively. Dollar/subscription cost is explicitly an estimate: the placeholder
does not promise a provider-enforced spend cap.

Checkpoints, operations, prepared requests, workspaces, original deltas, ownership,
and publication receipts are persisted separately. Resume uses the pinned program,
configuration and prompt hashes. A retained receipt settles its original operation;
it does not create another commit. Review disposition batches resume individually.

A lost HTTP/RPC connection does not prove cancellation. Unknown external effects
remain visible in `status` and `operation`, retain conflicting ownership, and block
replacement dispatch. The placeholder automatically reconciles verifiable host
commit/publication receipts. Remote unknowns need provider reconciliation; it does
not guess that they stopped. Deliberate scope/allowance blockers pause without a
fabricated completed task report.

Tests use disposable real Git repositories, actual TCP/stdio fixtures, and adversarial
schedules. A complete coding run passed using Codex CLI 0.163.0 and the configured
ChatGPT subscription. Claude protocol tests pass; the supplied placeholder key
returned HTTP 401, so live Claude completion remains unverified. See
[provider setup and live evidence](design-docs/implementation/PROVIDER_SETUP.md).
These checks do not establish model quality or compatibility with other deployments.
