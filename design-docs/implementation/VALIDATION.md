# Validation record — 17 October 2026

Environment: Ubuntu 22.04 / WSL, Python 3.10.12. Runtime versions are pinned in
`pyproject.toml` and the tested environment is recorded in `requirements.lock`.

* Full behavioral suite, including the test UI: **86 passed**, 100.77 seconds.
* Eight UI tests exercise actual HTTP launches, fresh run state, persisted node
  history, prompt/response artifacts, failure handling, local-origin checks,
  repository switching, full JSON exports and shared CLI/UI steering writes.
* The default UI uses Haiku juniors and Codex setup/senior engineers with a
  nine-sprint limit and approximately 10% of development assignments on the senior.
  A mixed-provider regression exercises the real Anthropic Messages adapter with
  a fixture transport and a simulated Codex senior. It completes after four
  senior reviews, beyond the former three-sprint cap, and verifies nonzero costs
  for both providers. No new live Anthropic authentication test was performed.
* Eight setup/tool tests cover cloud-first preparation, existing/new/empty Git
  baselines, requested-branch selection, source isolation, callback replay,
  shell timeout/output/cwd/scope handling, and cumulative development allocation.
* A complete ten-task run routes one nominated development task to the cloud
  senior and nine to juniors. A strengthened replay check also passed separately
  (15.50 seconds): a shell edit during native assessment forces reconciliation,
  fresh checks and a second assessment, including settled model-result replay.
* A new live Codex setup check passed with the installed CLI and subscription:
  three native phase jobs selected a new private branch, ran a brokered shell
  script, checked the resulting file and published a successful setup report.
  Seven subordinate callbacks included branch selection, shell, reads and checks.
  This was a setup-only check, not full project acceptance or a live Haiku run.
* Browser verification found the optional Base branch control, preserved saved
  runs and no JavaScript errors after restarting the UI with the new defaults.
* Six cost tests cover mixed Codex/Haiku totals, cached and cache-write usage,
  long prompts, native usage recovery, deduplication and missing usage/prices.
* Browser checks verified the repository picker, expanded steering panel, saved
  run totals and a real JSON download containing four processes and 25 nodes.
  The browser reported no JavaScript errors.
* A live Codex test started through the UI completed successfully: four processes,
  25 executed graph nodes, successful worker verdict, and passed check evidence.
  Browser interaction verified node selection and actual prompt/response display.
* Native failure tests distinguish confirmed termination from unknown execution;
  unknown execution retains its slot/tokens.
* Final Codex endpoint/native-worker/runtime regression checks: **22 passed**,
  7.69 seconds, including early host callbacks with colliding RPC IDs.
* Ruff lint and formatting checks passed; Python compilation and Git whitespace
  checks passed.
* All five OpenAI, Gemini, Claude, Codex and mixed-provider example configurations
  pass validation.
* Package wheel builds successfully and includes the UI HTML asset and server.
  UI JavaScript syntax and browser rendering checks passed.
* Original agent validator: 35 illustrative records, 41 invalid combinations.
* Original workspace validator: six views, three deltas, 35 invalid combinations.
* Original diagram checker: all 159 visible routes passed using Node 20.18.0.
* The original JSON-schema equality checks were run with the design's documented
  Pydantic 2.9.2 in an isolated `.polyinference/contract-validation` folder.
  The runtime remains on Pydantic 2.14.1. Runtime contract tests separately compare
  SDK and original Python schemas under the same installed Pydantic version.

The tests use disposable real Git repositories, actual TCP HTTP and stdio RPC,
and deterministic scripted provider outputs. They exercise concurrent private work,
all three verdicts, mandatory reconciliation and assessment, current-tree evidence,
source isolation, read-only omission, stale generations, effect replay, unknown
execution, admission, shell exclusion/order, independent sprint/project checks,
steering during workers/query/acceptance, cancellation of pending assignments,
verdict notes/refinement, typed SDK records, native callback ancestry, coordinator
exclusion, abort/rebuild, publication receipt recovery, senior revert replay, and
a crash between two senior reverts.

A real Codex CLI 0.163.0 run using the existing ChatGPT subscription and
gpt-6.1-sol completed a disposable coding task. Five native phase jobs and nine
brokered callbacks produced a successful report, required reconciliation and
assessment turns, a real publication, senior keep and independent acceptance.
The source checkout remained unchanged. The native profile, dynamic tool schema,
strict output grammar and token usage events were verified against this CLI.
The new shell/branch callback schema was also exercised by the live setup check.
See [setup and live evidence](PROVIDER_SETUP.md).

Anthropic's real Messages endpoint returned HTTP 401 for the user-supplied
placeholder key, which remains in the private user configuration for replacement.
Live Claude completion remains unverified; native Messages framing and the complete
agent flow passed HTTP fixtures. No raw OpenAI/Gemini completion or hardware
benchmark was performed. Other deployments require their own compatibility checks.
Trusted configured checks are not a sandbox; the optional host-check bubblewrap
path was not exercised. Codex used its bundled bubblewrap implementation.
