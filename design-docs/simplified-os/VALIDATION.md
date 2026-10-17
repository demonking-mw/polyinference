# Simple OS v1 validation — 17 October 2026

Branch: `codex/simple-os-v1`, isolated from the agent-testing checkout on `main`.
Host: macOS arm64; Python 3.12.14; pinned `requirements.lock` dependencies.
Codex CLI 0.161.0 with the existing ChatGPT login and `gpt-6.1-sol`.

## Automated validation

* Full behavioral suite: **97 passed in 216.29 seconds**.
* Final OS/contract subset after private-receipt replay hardening and provenance
  refresh: **22 passed in 22.45 seconds**.
* Original agent validator using its documented Pydantic 2.9.2: **35 records,
  41 rejected invalid combinations**, schema/provenance checks passed.
* Original OS validator with Pydantic 2.9.2: **6 views, 3 deltas, 35 rejected
  invalid/unsupported combinations**, schema checks passed.
* Original merged diagram checker: **159 routes passed**.
* Ruff checks/formatting: passed for all source/tests and the live smoke script.
  Python compilation and Python 3.10 syntax parsing passed.
* All five provider example configurations and Git whitespace checks passed.
* Wheel build/install in a separate environment passed. The installed CLI lists
  run/resume, events, cancellation and reconciliation; the wheel contains the
  kernel, process supervision, filesystem executor and UI HTML asset.

The suite includes real local TCP HTTP, stdio RPC, private Git repositories,
shell subprocesses and deterministic providers. No model credentials are needed
for automated pytest runs.

| OS behavior | Coverage |
| --- | --- |
| Four concurrent workers, one assessed failure | Failed private commit excluded from final ancestry; other three complete and publish; fifth task never starts; review rejects private work, schedules repair, and accepts the repaired next sprint. |
| Private receipt crash/replay | Lose operation result after receipt commit, move shared head/owner, reopen runtime; original intent settles from receipt without duplicate publication. |
| Parallel serving and fairness | Two requests overlap at one endpoint; alternating finishing/ordinary admission; context and in-flight limits; one-request cloud substitution. |
| Queue deadline/cancel | Expired queued work produces a known failure without dispatch/charge; cancelled waiters do not obstruct admission. |
| Remote unknown/restart | Occupancy survives restart; replacement is forbidden; explicit termination evidence settles original intent, returns capacity and marks cleanup complete. |
| Budgets and authority | Actual usage and estimated spend settle once; replay does not recharge; process effect exclusion; logical alias, forged verifier and denied-capability rejection. |
| Workspace/files | Literal search, exact digest-checked patch, paged reads, deleted-file non-resurrection, pinned closure/generation, scope and source isolation, delta-preserving abort. |
| Host cancellation and limits | Cooperative cancellation stops at effect boundary and exposes interrupted task; filesystem mutations join on cancellation without blocking loop; command output/deadline bounds. |
| Publication | Requires a broker-minted commit, expected parent/head and actual ownership; final acceptance uses current independent exact-tree checks. |
| Existing application | Setup/branch creation, all verdicts, native callback replay, senior reverts/crash recovery, steering, costs, UI HTTP/export and all provider grammars. |

## Live Codex test

The opt-in [smoke script](../../scripts/smoke_os_codex.py) creates a disposable
source repository whose `greet()` returns `"Hello"`. It runs all three roles through
one cloud lane with `max_inflight=1`. Codex plans, reads/writes through brokered
callbacks, reconciles, runs the trusted Python check, assesses, and reviews the
exact resulting tree for acceptance.

The final smoke run produced:

```json
{
  "status": "completed",
  "reports": [{"verdict": "successful", "reconciliations": 1, "assessments": 1}],
  "native_jobs": 5,
  "broker_callbacks": 7,
  "source_unchanged": true,
  "final_source": "def greet():\n    return \"Hello, OS!\"\n",
  "uncertain": []
}
```

Two full disposable live runs succeeded during this effort. Readiness also
passed after fixing macOS sandbox execution through the resolved Codex binary.
These runs verify the installed CLI's protocol, dynamic host-tool brokerage,
phase/usage handling and complete application path, not general model quality.

## Boundaries

This final OS revision was tested on macOS. The earlier agent-only validation
records Linux/WSL evidence in [implementation/VALIDATION.md](../implementation/VALIDATION.md);
new Linux/WSL deployment runs remain necessary. Native Windows is not supported.
Linux bubblewrap was not exercised on this host. Trusted host scripts/checks are
explicitly enabled capabilities, not a filesystem security boundary.

No live raw OpenAI, Anthropic or Gemini completion was run in this effort; their
wire formats and complete flows have fixture coverage. No physical local model
server or hardware continuous-batching benchmark was available. Application
concurrency is demonstrated; physical GPU/VRAM admission is intentionally deferred.

Unknown provider execution and hard host crashes can require operator evidence.
Automatic remote cancellation, exactly-once remote effects and distributed
failover are not claimed. See [the recovery and retention procedures](RUNBOOK.md).
