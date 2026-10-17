# Validation record — 17 October 2026

Environment: Ubuntu 22.04 / WSL, Python 3.10.12. Runtime versions are pinned in
`pyproject.toml` and the tested environment is recorded in `requirements.lock`.

* Full behavioral suite, including the test UI: **77 passed**, 74.53 seconds.
* Seven UI tests exercise actual HTTP launches, fresh run state, persisted node
  history, prompt/response artifacts, failure handling, local-origin checks,
  repository switching, full JSON exports and shared CLI/UI steering writes.
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
* All four OpenAI, Gemini, Claude and Codex example configurations pass validation.
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
See [setup and live evidence](PROVIDER_SETUP.md).

Anthropic's real Messages endpoint returned HTTP 401 for the user-supplied
placeholder key, which remains in the private user configuration for replacement.
Live Claude completion remains unverified; native Messages framing and the complete
agent flow passed HTTP fixtures. No raw OpenAI/Gemini completion or hardware
benchmark was performed. Other deployments require their own compatibility checks.
Trusted configured checks are not a sandbox; the optional host-check bubblewrap
path was not exercised. Codex used its bundled bubblewrap implementation.
