# Qualify a small coding workflow

[Reliability](agent-reliability.md) · [Checks](checks.md) · [Implementation record](../../development-docs/reliability-implementation-2026-10-27.md)

Qualification uses fresh disposable projects and independent behavior checks. It
does not resume preserved Minecraft runs or certify a broader product objective.

| File | Responsibility |
| --- | --- |
| [agent/qualification.py](../../src/polyinference/agent/qualification.py) | Physical-attempt/source outcome metrics and the three-success-plus-resume gate. |
| [qualify_workflow.py](../../scripts/qualify_workflow.py) | Pinned short-task corpus, fresh states, independent checks, manifests and a settled interruption/resume trial. |
| [browser_check.mjs](../../scripts/browser_check.mjs) | Real Chromium entry/input/pause/save/reload checks with a command-owned temporary server and cleanup. |
| [test_reliability_plan.py](../../tests/test_reliability_plan.py) | Regressions for OS authority, residency, task-state continuity and error-conditioned response repair. |

## Run and inspect

Use an activated environment with the project/test dependencies. The output path
must be new. Offline scripted-provider qualification:

```bash
python scripts/qualify_workflow.py --fixture --output /tmp/pi-qualification-fixture
```

The fixture provider supports the repair case only. Its successful result proves
controller/tool/check/continuation wiring, not actual model reasoning quality.

An explicitly supplied configuration uses its real providers and allowance:

```bash
python scripts/qualify_workflow.py --config /path/to/profile.json --case repair --output /tmp/pi-qualification-live
```

Cases are `repair` (numeric file repair), `create` (new file then digest-based update),
`save` (JSON state restoration), and
`workflow` (real entry/input/pause/save/reload). The harness narrows writes to the
case's source, supplies trusted independent checks and preserves profile limits.
It never edits the configuration's original repository. Compare the same case,
source/model/profile before varying one parameter. Three completions followed by
one settled interruption/resume must pass independent checks on accepted source.
This is an initial engineering gate, not a statistical reliability claim.

For `workflow`, install Node, Playwright and its Chromium dependency explicitly.
Use the [official installation guide](https://playwright.dev/docs/intro).
Set `QUALIFICATION_BROWSER_TOOLS` to the package directory containing Playwright's
`node_modules`. A browser preflight fails before model work if unavailable. The
runner pins explicit dependency/browser paths in argv and preflights in the OS's
sanitized tool environment; inherited environment alone cannot prove readiness. The
coding agent still has no browser/MCP/persistent-service API: this is a configured
finite check command. Never replace it with a fake DOM to claim browser coverage.

Each trial retains `manifest.json`, state, `independent-check.log` and `result.json`;
source archives/diffs, exact package versions and stable profile/tool pins accompany them.
the root `results.json` records the gate. Pins include source, framework, backends,
commands and original limits. Native jobs and raw generations remain separate.
The interruption happens after a settled edit and clean exception parking, then
uses ordinary run-level resume on the same pinned state/account. It does not
simulate an unknown remote effect or prove recovery from arbitrary power loss.

## Interpretation

Agent monitor/export `quality` projects canonical physical attempts, context
omissions, validation failures, kept source deltas, cloud adjustments and exact
exit causes. It never adds logical usage to physical usage, calls a kept task a
completed product, or interprets a native multi-turn job as one raw generation.
Worker-state records remain bounded views with references to original evidence.
Bounded task metrics retain lineage, actual backends, root counters, dependency
waits and identical read/check shares, including superseded started work. Creation
requires an observed successful update using the digest returned by creation.
Cost output uses the existing dated API-equivalent estimator; missing usage/prices
remain incomplete. Semantic behavior counts and unobserved shell reads are unavailable.

Meaningful regressions include unknown effects retaining capacity, blocked data
policy before submission, source/generation invalidation, repeated repair without
allowance refill, and actual cloud coding with preserved root lineage. Preserve
historical failed evidence and report fixture results separately from live trials.
