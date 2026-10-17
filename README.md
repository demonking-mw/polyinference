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
