# Provider setup on this machine

Codex CLI **0.163.0** is installed in Ubuntu-22.04 at
`/home/mawa/.local/bin/codex`. WSL login shells include that directory in PATH.
It uses the existing ChatGPT subscription login and `gpt-6.1-sol`.
Credentials stay in the private user authentication cache, outside this repository.

From WSL:

```bash
cd /home/mawa/projects/polyinference
. .venv-linux/bin/activate
codex --version
codex login status
polyinference probe examples/agent.codex.json
```

The probe makes one small readiness request without starting an application run.
The example has the tested endpoint settings; set its repository, objective,
allowed files, closure and check commands before starting a real project run.
Paths are relative to the configuration file.

The direct subscription adapter was tested through a complete disposable coding
task: senior plan, native development with brokered file/check calls, mandatory
reconciliation, assessment, publication, senior keep and independent acceptance.
The accepted change produced `Hello, Codex!`; the source checkout retained its
original `Hello Codex`. There were five native phase jobs and nine brokered
callbacks. One reconciliation turn and one assessment turn were retained in the
successful report. The configured unittest passed against the published tree.

Local evidence remains in:

* `.polyinference/codex-smoke/state-2/` — successful run, typed records, artifacts and Git objects.
* `.polyinference/codex-smoke/agent-2.json` — exact disposable run configuration.
* `.polyinference/codex-setup/coding-report.json` — concise nonsecret evidence.
* Earlier diagnostic runs remain in separate state directories.

The adapter defines its scoped read-only permission profile through app-server
startup overrides so ChatGPT workspace routing reloads retain it. Native commands
have no filesystem write grant or network access. File writes and configured
checks go through the host broker. Strict output-schema translation and the phase
reply envelope stay at the adapter boundary; canonical OS records are unchanged.
Reported native token totals are recorded, and known usage above the initial
reservation is charged before further dispatch. Native internal loops are bounded
by the job deadline and event limits, not a provider-enforced token/spend quota.

## Claude

[The Anthropic example](../../examples/agent.anthropic.json) uses the native
Messages API at `https://api.anthropic.com/v1/messages`, API version
`2023-06-01`, and the requested `claude-haiku-5-5` model.

The supplied placeholder remains at
`/home/mawa/.config/polyinference/anthropic.env` (mode 0600), outside Git.
Replace only its `ANTHROPIC_API_KEY` value. New WSL login shells load this file.
For an existing shell, source it before probing:

```bash
. "$HOME/.config/polyinference/anthropic.env"
.venv-linux/bin/polyinference probe examples/agent.anthropic.json
```

The real endpoint returned HTTP 401 for the placeholder, as expected. A live Claude
completion has not been verified. Automated tests cover actual TCP Messages
requests through the full agent, credential/version headers, separate system
instructions, assistant history, text/thinking blocks, cached token accounting,
truncation, refusals, tool requests, authentication/quota errors and disconnections.
The adapter does not retry uncertain requests.

Protocol references:
[Codex app-server](https://learn.chatgpt.com/docs/app-server),
[Codex authentication](https://learn.chatgpt.com/docs/authentication),
[Codex permissions](https://learn.chatgpt.com/docs/permissions),
[Anthropic API overview](https://platform.claude.com/docs/en/api/overview),
[Claude models](https://platform.claude.com/docs/en/models/overview),
[Claude stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons).
