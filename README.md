# PolyInference agent and simple OS

PolyInference is a LangGraph coding agent with a small local test UI. Give it a
repository, an objective and a command that verifies the result. A senior agent
plans and reviews the work, junior agents implement most tasks, and the runtime
records the processes, prompts, responses, tool results and Git history.

The default UI uses **Anthropic Haiku for junior workers** and **Codex through your
ChatGPT login for setup, planning, review and senior development**. Other supported
backends include OpenAI, Gemini and compatible local model servers.

The bundled **simple OS v1** runs the existing LangGraph agent on macOS, Linux
and WSL. It owns bounded inference admission, process lifecycle, brokered tools,
private workspaces, publication and persistent recovery. It connects to an existing
model server or cloud API; physical RAM/VRAM management is deferred. See the
[OS deployment and recovery guide](design-docs/simplified-os/RUNBOOK.md).

## Contents

- [Requirements](#requirements)
- [Install and launch](#install-and-launch)
- [Run the first test](#run-the-first-test)
- [Work on your own project](#work-on-your-own-project)
- [Use the UI](#use-the-ui)
- [Configure providers and models](#configure-providers-and-models)
- [Configure a repeatable run](#configure-a-repeatable-run)
- [Use the command line](#use-the-command-line)
- [Retrieve code and debugging data](#retrieve-code-and-debugging-data)
- [Limits, steering and recovery](#limits-steering-and-recovery)
- [Troubleshooting](#troubleshooting)
- [Test the implementation](#test-the-implementation)
- [Project structure and design](#project-structure-and-design)

## Requirements

| Requirement | Details |
| --- | --- |
| Operating system | macOS, Linux, or Linux inside WSL. Native Windows is not supported by the POSIX runtime. |
| Python | Python 3.10 or later, including `venv` and `pip`. |
| System tools | Git and Bash; `curl` for the Codex installation below. |
| Default junior provider | An Anthropic API key with access to the configured model. |
| Default senior provider | Codex CLI installed and signed in on the same macOS/Linux/WSL host as PolyInference. |
| Project tools | Any compiler, interpreter, package manager and dependencies required by your target project's checks. |

The implementation has been exercised on Ubuntu 22.04 in WSL with Python 3.10.12
and Codex CLI 0.163.0. Keep the repository and runtime state on the Linux
filesystem, for example `~/projects/polyinference`, rather than `/mnt/c/...`.
Use Linux paths in the UI, such as `/home/yourname/projects/my-app`.

The UI is packaged with the Python application. It needs no frontend build,
JavaScript package installation or separate development server. Node/npm are only
needed if your target project uses them.

## Install and launch

Run the commands in **Bash** on macOS, Linux or WSL. On macOS, install Python 3.10+
and Git using your preferred package manager; skip the Ubuntu package commands.
`bubblewrap` execution requires Linux; use explicitly enabled `trusted` commands
on macOS. Codex uses its own platform sandbox for native jobs.

### 1. Install the application

On Ubuntu/Debian, install the system prerequisites if needed:

```bash
sudo apt update
sudo apt install -y git bash curl python3 python3-venv python3-pip
```

Clone and install:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/demonking-mw/polyinference.git
cd polyinference
python3 -m venv .venv-linux
source .venv-linux/bin/activate
python -m pip install -e '.[test]'
polyinference --help
```

The `test` extra includes pytest and Ruff, useful for testing the implementation
and for the UI's suggested Python check. A runtime-only installation can use
`python -m pip install -e .` instead. Direct dependencies are pinned in
[pyproject.toml](pyproject.toml); [requirements.lock](requirements.lock) records the
complete tested environment. To reproduce those transitive versions, install
`python -m pip install -r requirements.lock` before the editable installation.

### 2. Install Codex and sign in

Install Codex in the **same macOS/Linux/WSL environment as the backend**. WSL
needs its own Linux installation even if you use the Windows desktop app. Skip the installation command if `codex --version` already works there.
The official Linux installer is documented in the
[Codex CLI quickstart](https://learn.chatgpt.com/docs/codex/cli):

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Follow the installer's PATH instructions, reopening your terminal if necessary.
Then activate the PolyInference virtual environment again and sign in:

```bash
codex --version
codex login
codex login status
```

Use the ChatGPT account you intend to use for Codex. The default integration
launches `codex app-server` automatically; you do not start an app-server manually
or paste a subscription token into a PolyInference JSON file. Subscription access
and available models depend on your account/workspace.
[Official authentication guidance](https://learn.chatgpt.com/docs/auth).

If the browser callback cannot complete in WSL or on a remote machine, try:

```bash
codex login --device-auth
```

Device login must be enabled for your account/workspace; follow the URL and code
shown by the CLI. Run `codex login status` afterward to confirm the authentication
method. For the default mixed setup, an `OPENAI_API_KEY` is not required.
[Device authentication instructions](https://learn.chatgpt.com/docs/auth#login-on-headless-devices).

### 3. Supply the Anthropic API key

Get an API key for your own Anthropic account. Set `ANTHROPIC_API_KEY` in the
**same terminal that will launch the backend**. This Bash prompt avoids putting
the value directly in shell history:

```bash
read -rsp 'Anthropic API key: ' ANTHROPIC_API_KEY
printf '\n'
export ANTHROPIC_API_KEY
```

For reuse, you can put the following line in a private file outside the repository,
for example `~/.config/polyinference/anthropic.env`, using your editor:

```bash
export ANTHROPIC_API_KEY='replace-with-your-real-key'
```

Create the parent directory with `mkdir -p ~/.config/polyinference` before saving
the file. Restrict the file and explicitly load it before launching the app:

```bash
chmod 600 ~/.config/polyinference/anthropic.env
source ~/.config/polyinference/anthropic.env
```

PolyInference does **not** automatically load a `.env` file. A server that is
already running keeps its previous environment; after replacing a key, restart
the server when its active run has finished. Credential values belong in your
environment, while configurations contain only environment variable names.

### 4. Launch the UI

From the PolyInference checkout, with the virtual environment active and credentials
loaded:

```bash
polyinference ui
```

Open **[http://localhost:8765](http://localhost:8765)** in your browser. On Windows,
the browser can connect to the backend running inside WSL. Keep the terminal open.
The server binds to `127.0.0.1`; it is intended for use on your own machine.

For later launches:

```bash
cd ~/projects/polyinference
source .venv-linux/bin/activate
source ~/.config/polyinference/anthropic.env  # If you saved the key this way.
polyinference ui
```

Use `polyinference ui --port 8766` and open `http://localhost:8766` if the default
port is occupied. After the active run settles, **Ctrl+C** stops the foreground
server. Closing the browser tab does not stop the server or its run. Stopping the
backend during work is an interruption, not a graceful pause/cancel feature.

## Run the first test

Start with the built-in task before selecting a real project:

1. Launch `polyinference ui` without `--config` and open the page.
2. Keep the default root repository, objective and check command.
3. Click **Run test**. This makes real provider requests and consumes API/subscription allowance.
4. Wait for setup, planning, development, review and acceptance to settle.
5. Select processes and nodes to inspect what happened. Click a blue model node
   for its prompt and response; other nodes show inputs, outputs and tool results.
6. Use **Export JSON** if you want to retain a debugging report.

The fixture is a tiny committed Python project generated under
`.polyinference/ui/fixture/`. The goal is to change `greeting("Codex")` from
`Hello Codex` to exactly `Hello, Codex!`, with only `greeting.py` writable and a
read-only unittest checking the result. Successful completion requires the check
to pass against the accepted private tree. The fixture's source checkout stays
unchanged; use the export instructions below to retrieve the code.

Each **Run test** click creates a fresh run and state directory. The UI permits
one active test at a time and retains previous runs in its run selector. A run
can stop with a blocker or exhausted allowance; a recorded worker response alone
does not mean the project completed.

The configured defaults are `claude-haiku-5-5` and `gpt-6.1-sol`. These are model
IDs pinned by this project, not a promise that every account can access them.
If a provider rejects an ID, use a configuration with an available model as
explained below.

## Work on your own project

1. Prepare a project directory on the host filesystem (inside Linux for WSL). For an existing Git
   checkout, commit or stash changes, including untracked files you want to keep.
   The runtime imports committed content and rejects a dirty source checkout.
2. In **Root repository**, enter the absolute host path or use **Browse…**.
   Select the repository root, not a `src/` subdirectory. A new project folder is
   also supported; create the directory before selecting it.
3. Enter a specific objective: expected behavior, files or areas to change,
   acceptance criteria, setup chores and branch instructions.
4. Expand **Check command** and inspect the command. The UI suggests a pytest
   command for Python projects or `npm test` when `package.json` defines it.
   Otherwise you must enter one. Install the required tools and dependencies.
5. Optionally enter an existing local **Base branch** in that same panel. If you
   need a new branch, explicitly request its creation in the initial objective.
6. Click **Run test**, inspect the outcome and export the changes for review.

An example objective:

> Use the existing `feature/search` branch as the baseline for this development.
> Inspect the project setup and run any required preparation. Add case-insensitive
> filtering to the search endpoint, preserve pagination behavior, and add tests
> for mixed-case queries. Completion requires the configured test command to pass.

Branch selection happens in the private repository. The source checkout is not
switched or renamed, and nothing is pushed. Existing named branches must be
available locally; a missing branch is a blocker. For a folder without a committed
Git baseline, the runtime creates one privately rather than initializing or
committing the original directory.

The check field is parsed as **an executable and arguments**, not as a shell
script. For example, use `python -m pytest -q` or `npm test`; shell operators such
as `&&` and pipes are not interpreted there. For more involved verification,
provide a committed script and configure its interpreter and arguments.
Checks execute in the private integrated workspace, not the source checkout.
Ignored virtual environments and `node_modules` from the source are not copied;
do not assume project-local installed dependencies will be present there. An
absolute interpreter path can select an existing Python environment. Setup shell
commands are available, but the OS has no dependency-cache manager.

Without `--config`, selecting another project grants the selected directory as
the development scope, including new files; each task still has its own explicit
write set. With `--config`, the configured grants, closure, endpoints and checks
remain in force when you change roots. Adjust those grants for the target project
before starting.

For disposable projects inside this checkout, use **`testing/`**, which Git ignores.
The real implementation test suite is **`tests/`** and remains tracked.

## Use the UI

| Control or display | Behavior |
| --- | --- |
| Run selector | Reopen saved runs, including failed or interrupted runs. |
| Process/node list | Inspect the recorded execution order and individual node details. |
| Blue model node | Read the model's prompt and response. |
| Other nodes | Inspect state transitions, inputs, outputs and recorded operations. |
| Steering | Send new instructions while the selected run is active. |
| Export JSON | Download the selected run's detailed debugging data. |
| Costs | View provider estimates for the run and totals across saved runs. |

Steering closes new task starts immediately. Workers that have already started,
including workers waiting for a gate or model slot, finish their original
assignment before the senior consumes the update. The panel shows received and
pending instructions. Steering is not an immediate worker interrupt.

Development allocation targets **10% senior / 90% junior by task count** over the
run. Setup, sprint planning and management calls do not count toward that split.
Rounding matters for small runs; it does not promise 10% of tokens, calls, elapsed
time or money. Exports include actual started-task allocation separately.

Cost reporting is approximate. Codex shows an **API-equivalent estimate**, not
an amount charged to your subscription or its remaining allowance. Missing usage
or unknown prices produce an incomplete estimate, marked with `+`; expand
**About cost estimates** for the explanation. The export retains rate dates and
source links. A zero Haiku count can be valid if no Haiku request has started;
check the endpoint bindings and recorded model operations before assuming a bug.

## Configure providers and models

`local` and `cloud` are the names of two endpoint **lanes**. They do not guarantee
where inference happens: the default `local` lane points to Anthropic's cloud API.
Physical inference location is recorded separately.

The default bindings are:

| Role | Purpose | Lane / default backend |
| --- | --- | --- |
| `worker` | Junior development tasks | `local` / Anthropic Haiku |
| `senior` | Planning and review | `cloud` / Codex |
| `specialist` | Initial setup and senior development tasks | `cloud` / Codex |

All three bindings must be present in a custom configuration. They are pinned
for a run. To change models, providers or bindings, start a fresh state directory.

| Backend | Endpoint configuration | Authentication / example |
| --- | --- | --- |
| Anthropic | `protocol: "anthropic"`, `base_url: "https://api.anthropic.com/v1"` | `api_key_env: "ANTHROPIC_API_KEY"`; [Claude example](examples/agent.anthropic.json) |
| OpenAI API | `protocol: "responses"` or `"chat"`, `base_url: "https://api.openai.com/v1"` | `api_key_env: "OPENAI_API_KEY"`; [OpenAI example](examples/agent.openai.json) |
| Gemini | `protocol: "gemini"`, `base_url: "https://generativelanguage.googleapis.com/v1beta"` | `api_key_env: "GEMINI_API_KEY"`; [Gemini example](examples/agent.gemini.json) |
| Local compatible server | `protocol: "chat"` or `"responses"`, URL of your running server | Set its served model ID and any required credential variable. |
| Codex subscription | `protocol: "codex_app_server"`, `command: ["codex", "app-server"]` | Codex CLI login; [Codex example](examples/agent.codex.json) |
| Default mixed setup | Haiku `local` lane and Codex `cloud` lane | [Mixed example](examples/agent.mixed.json) |

Export the corresponding API credential before launching the CLI or UI. Set the
`model` field to the exact ID your endpoint serves. A ChatGPT login authenticates
Codex; raw OpenAI API calls use a separately configured API key. Local inference
requires you to install and run a compatible server yourself.

Coding roles using `codex_app_server` require **`brokered_tools: true`** so their
file, shell and check operations use the same host broker as raw LLM workers.
Planning/review queries remain read-only. Setup and senior development have file
and enabled shell/check tools through the worker protocol.

There is also an optional `codex_proxy` adapter for a separately installed,
compatible proxy with a pinned read-only snapshot. It supports senior queries;
opaque proxy coding jobs are rejected. No third-party proxy is installed by this
project. Use the native app-server path for Codex development.

## Configure a repeatable run

The UI defaults are useful for a first test. Use a JSON configuration to pin your
own project, permissions, checks and endpoint settings:

```bash
mkdir -p .polyinference
cp examples/agent.mixed.json .polyinference/agent.json
```

Edit `.polyinference/agent.json` before running it. The example's repository,
objective and file names are placeholders. At minimum, update these fields:

| Field | What to set |
| --- | --- |
| `repository` | Absolute host path to the target root, e.g. `/home/yourname/projects/my-app`. |
| `state_directory` | A fresh directory, e.g. `"./my-project-state"`. In this copied config that resolves to `.polyinference/my-project-state/`. |
| `objective` | The full development request and acceptance criteria. |
| `allowed_write_paths` | Exact project-relative writable file names, including intended new files, when using the default `write_scope: "explicit"`. |
| `closure_paths` | Additional project-relative source, manifests, scripts and test files needed in the initial worker view. |
| `checks` | Named executable/argument lists that verify the project, with suitable timeouts. |
| `local`, `cloud` | Provider protocols, URLs, accessible model IDs, credential variable names and concurrency/context settings. |

For example, replace the check with this object inside the `checks` list, using
an interpreter that has your project's dependencies installed:

```json
{
  "name": "tests",
  "argv": ["/absolute/path/to/project-venv/bin/python", "-m", "pytest", "-q"],
  "timeout_seconds": 120
}
```

`repository` and `state_directory` resolve relative to the **configuration file's
parent directory**, not your terminal's working directory. Source file grants
and closure paths resolve relative to the target repository; use POSIX paths
such as `src/example.py`, not Windows paths or absolute file paths. The check
executable runs from the private workspace, so use an absolute executable path
when you need a particular virtual environment.

Additional settings worth reviewing:

| Setting | Effect |
| --- | --- |
| `prepare_repository: true` | Run a specialist setup task before planning; enables private initialization and branch/setup handling. Default UI and mixed example enable it; generic configs default to false. |
| `base_branch` | Select an existing local branch as the private baseline. Omit/null to start from the source HEAD. |
| `write_scope` | `explicit` restricts development to file grants; `project` allows task grants anywhere in the selected project directory, including new files. |
| `shell_execution` | `disabled`, `trusted` or `bubblewrap`. Default UI and mixed example use `trusted`. |
| `check_execution` | Independently enables configured checks using `trusted` or `bubblewrap`. Generic default is `disabled`, which yields unavailable check evidence. |
| `senior_development_fraction` | Default `0.1`: target share of development tasks assigned to the specialist. |
| `max_workers` | Concurrent started workers; UI default is 1, generic config default is 2. |
| `POLYINFERENCE_LOCAL_BATCH_SIZE` | Environment override for local-lane `max_inflight` (1–32); pinned at startup. Use 1 for a cloud API substitution experiment. |
| `review_token_reserve` | Parent token allowance reserved for planning/review; default 32,000. |
| `run_spend_budget_microusd` | Optional estimated run cost bound; requires an explicit endpoint token-price estimate. |
| `max_sprints` | UI/mixed example use 9 sprints and up to 27 senior queries; generic config default is 8 sprints. |
| `limits` / `run_token_budget` | Per-process allowances, final-phase reserves and parent token allowance. Set them before starting. |

**`trusted` shell/check execution runs code on your host.** Workspace-relative
working directories and post-run scope checks are not an OS security sandbox.
Use it for projects and commands you trust. The optional `bubblewrap` mode needs
`bwrap` installed and a compatible Linux environment; this backend has not been
validated by the live-provider checks. Shell scripts run in a bounded foreground
process group with captured output and a timeout; background services are outside
this placeholder's tool profile. Shell tools receive a minimal environment rather
than inheriting provider credential variables.

Validate, optionally probe both providers, then launch the UI with your config:

```bash
polyinference validate-config .polyinference/agent.json
polyinference probe .polyinference/agent.json --endpoint local
polyinference probe .polyinference/agent.json --endpoint cloud
polyinference ui --config .polyinference/agent.json
```

Validation checks the schema, not authentication, model availability or the
project's test environment. Each probe sends one small real request without
starting a project run; it does not prove the entire coding/tool workflow works.
The UI uses your configuration as its template, but still gives every **Run test**
click a new state directory under `.polyinference/ui/runs/`.

## Use the command line

You can run without the UI using the same configuration and environment:

```bash
polyinference run .polyinference/agent.json
polyinference status .polyinference/my-project-state
```

Run status is printed as JSON. `run` and `resume` exit with status 2 when the run
has not reached `completed`; inspect its blocker and evidence rather than treating
any saved commit as final success.

| Command | Purpose |
| --- | --- |
| `polyinference validate-config CONFIG` | Validate configuration structure. |
| `polyinference probe CONFIG --endpoint local` | Make one readiness request to the worker lane. Use `cloud` for the other lane. |
| `polyinference run CONFIG` | Start/drive a run in the configured state directory. Use fresh state for a new run. |
| `polyinference status STATE` | Inspect application status, task reports, heads and uncertain effects. |
| `polyinference steer STATE 'Updated instructions'` | Record steering for the running coordinator to consume. |
| `polyinference resume CONFIG` | Reopen persisted execution with its pinned configuration and implementation. |
| `polyinference operation STATE OPERATION_ID` | Inspect one journaled operation. |
| `polyinference export STATE OUTPUT.patch` | Export the initial-to-provisional code diff. |
| `polyinference ui --state STATE` | View a persisted run in the UI. |

Run `polyinference --help` or `polyinference COMMAND --help` for argument syntax.
`ui --state` imports an existing run for inspection; **Run test** still creates a
new run rather than resuming that imported run.

## Retrieve code and debugging data

The runtime works in isolated copies and its own Git object store. **It never
applies the result to your selected source checkout automatically.**

There are two separate exports:

- **UI Export JSON** downloads the selected run's processes, nodes, prompts,
  responses, tool/operation artifacts, reports, steering, setup information,
  configuration metadata, allocation and cost estimates. It is for debugging;
  it is not a code patch. It can contain project source and task text, so review
  it before sharing.
- **CLI patch export** writes the difference between the stored initial and
  provisional heads, including binary diffs. It does not depend on a model's
  description of its edits.

To export a UI run, replace `RUN_ID` with the selected run's ID:

```bash
polyinference status .polyinference/ui/runs/RUN_ID/state
polyinference export .polyinference/ui/runs/RUN_ID/state /tmp/polyinference-result.patch
```

For the custom CLI configuration above:

```bash
polyinference export .polyinference/my-project-state /tmp/polyinference-result.patch
```

Inspect the run status, reviewed/provisional heads and unresolved reports first.
Every assessed worker verdict, including `uncertain` and `fail`, can publish a
provisional commit; exporting an incomplete run can therefore include work that
has not been accepted.

Apply a reviewed patch in a clean checkout at the **same baseline revision and
branch used by that run**:

```bash
cd /absolute/path/to/target-repository
git apply --stat /tmp/polyinference-result.patch
git apply --check /tmp/polyinference-result.patch
git apply /tmp/polyinference-result.patch
```

Then run your checks, review the diff and commit it yourself. If setup selected a
different baseline branch, switch your receiving checkout to that baseline first.
A patch is a content diff; it does not recreate branch names or commit history.

For a new project, you can extract the entire resulting tree into a separate,
empty output directory instead. Replace `COMMIT_ID` with the desired commit ID
from the provisional/reviewed head in `polyinference status STATE`, and use the
absolute path to that run's state directory:

```bash
mkdir -p /absolute/path/to/new-output
git --git-dir=/absolute/path/to/state/repository.git archive COMMIT_ID \
  | tar -x -C /absolute/path/to/new-output
```

This uses `tar` and exports the files without a `.git` directory. Initialize a new
repository there if desired. The original commits remain in the state's private
Git store, so retain the state if you need its history or execution evidence.

UI data is relative to the directory from which you started the server:

```text
.polyinference/ui/
  fixture/                     # Disposable greeting source project
  runs/<RUN_ID>/
    ui-run.json                # UI run metadata
    config.json                # Effective configuration; environment variable names
    state/
      records.sqlite           # Typed records, reports and operation journal
      checkpoints.sqlite       # LangGraph checkpoints
      artifacts/               # Content-addressed requests/results and other artifacts
      repository.git/          # Private Git objects and commits
      workspaces/              # Scoped development and integrated working copies
      snapshots/               # Native-agent snapshots
```

Custom CLI runs put the equivalent state files directly in `state_directory`.
Start the UI from the same directory later to rediscover its saved runs. Keep the
whole state directory if you need recovery; copying just a SQLite file is not a
complete backup. Prefer patch/Git exports over copying an arbitrary temporary
workspace, which may represent only one task or an intermediate integration view.

## Limits, steering and recovery

The default per-process allowance is 512 model calls, 2,048 steps and a one-hour
wall-clock deadline, with reserved reconciliation, assessment, publication and
cleanup capacity. Context reservations and the parent token allowance also limit
work. Native Codex jobs have their own deadline/event bounds; there is no
provider-enforced dollar or subscription spend cap. Optional token-priced spend
estimates can bound admission; they are not a provider billing guarantee.

The execution protocol is:

1. Setup, when enabled, handles the initial objective's prerequisites and Git/branch instructions.
2. Senior planning creates bounded tasks and assigns worker/specialist roles.
3. Each worker develops privately, integrates against the current head, reconciles,
   runs configured checks and assesses. Successful/uncertain commits may advance
   the provisional head. A failed commit stays private, closes new starts and
   releases verification while already-started workers finish publishing.
4. Senior review keeps, reverts, retries or defers reports.
5. Independent final checks guard project completion.

Steering follows the drain-before-review behavior described above. It does not
reset budgets. `resume` restores saved execution; it does not automatically clear
`paused` or `budget_stopped`, raise allowances, change models or restart a
completed run. Changed configuration, graph or prompt fingerprints are rejected
for existing state. Use a fresh state directory for a changed setup or budget.

A lost HTTP/RPC connection does not prove that an external job stopped. Uncertain
operations stay recorded, retain conflicting ownership and block replacement
dispatch until reconciled. The runtime can reconcile verifiable host publication
receipts; it does not blindly retry remote requests. Inspect `status` and
`operation`, preserve the state, and establish the provider-side outcome before
attempting recovery. Use the explicit `reconcile --confirm-stopped --evidence`
command only after both provider work and host descendants are known to have
ended. See the [recovery procedure](design-docs/simplified-os/RUNBOOK.md#recovery).
Do not delete journal rows to force a retry.

## Troubleshooting

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
| Code did not change in the selected repository | Expected: development is private. Export and review the patch or private Git commits. |

## Test the implementation

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
[OS validation record](design-docs/simplified-os/VALIDATION.md). Earlier agent-only
WSL evidence remains in the [agent validation record](design-docs/implementation/VALIDATION.md).

## Project structure and design

| Path | Purpose |
| --- | --- |
| `src/polyinference/agent/` | Controller, independent worker graphs, senior review, setup, routing and prompts. |
| `src/polyinference/runtime/` | Simple OS kernel, admission, process supervision, provider clients and workspace/tool broker. |
| `src/polyinference/contracts.py` / `workspace_contracts.py` | Packaged SDK wire and workspace types. |
| `src/polyinference/ports.py` | Runtime service interfaces implemented by the bundled kernel. |
| `src/polyinference/ui.py` / `ui.html` | Local testing backend and frontend. |
| `examples/` | Editable provider/task configurations. |
| `tests/` | Implementation tests. |
| `testing/` | Ignored disposable projects created while testing the agent. |
| `.polyinference/` | Ignored local state, fixtures, artifacts and private Git stores. |

Start with the [design documentation index](design-docs/README.md),
[LangGraph agent design](design-docs/langgraph-agent/README.md),
[simplified OS design](design-docs/simplified-os/README.md),
[implementation/adapter notes](design-docs/implementation/README.md) and
[implementation plan](IMPLEMENTATION_PLAN.md). The implementation incorporates
[the user's agent-review answers](design-docs/implementation/user-agent-review.json).
The canonical wire/workspace data structures remain the integration boundary for
the future OS; provider transport details stay inside the standalone adapter.
