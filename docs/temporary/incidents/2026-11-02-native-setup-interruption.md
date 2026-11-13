# Native setup interruption

<a id="run-20739a315d3f"></a>
## Native setup interruption — 2 November 2026

**Historical investigation only; no implementation, configuration or saved-run change
in that investigation.** Subsequent `development-docs/FIXES.md#fix-0171` adds a default
warning-only cloud agent timeout policy for fresh configurations; the retained run
remains unchanged and still requires evidence-based recovery. Terminal drain and
precise interruption-cause reporting remain follow-ups.
Run `20739a315d3f` reproduces the unresolved whole-native-job timeout and
missing terminal drain documented in `development-docs/FIXES.md#fix-0068`.
The screenshot's Minecraft objective is retained evidence, not an instruction
for this investigation to build the game or resume its campaign.

### Evidence and trigger

The saved configuration selects cloud `gpt-6.1-sol`/medium via
`codex_app_server`, with `timeout_seconds=180`. Local Qwen/Strata is configured
for 1800 seconds, but no local model operation was submitted before this pause.
The initial repository-policy job completed; the setup specialist then started.
Times below are Toronto local time on 2 November:

| Event | Time |
| --- | --- |
| Run created | 16:04:09.084600 |
| Setup effect active | 16:04:15.975450 |
| Native turn started | 16:04:16.331309 |
| Last completed broker callback | 16:06:11.815 |
| Native rollout records `turn_aborted`, reason `interrupted` | 16:07:16.002 |
| Effect marked uncertain | 16:07:16.017413 |

Activation to uncertainty is **180.041963 seconds**, matching the whole-call
limit. This strongly supports kernel timeout as the interruption trigger; the
saved failure does not retain the original exception type, so it cannot exclude
an independently coincident cancellation. The rollout corroborates interruption,
not successful completion or proof that every descendant effect ended.

### Owning cause and retained work

`agent/system_settings.py:ui_system_settings` explicitly chooses the 180-second
cloud timeout. `runtime/kernel.py` bounds the entire `generate_job` call with
that timeout, including reasoning and brokered tools. Incoming activity does not
extend it. `runtime/codex.py` groups timeout and cancellation into one
UnknownExecution, sends `turn/interrupt`, then terminates the local transport
without draining a matching terminal acknowledgement. The OS therefore correctly
keeps the effect uncertain and pauses dispatch. This is not evidence of Qwen
failure, context exhaustion, malformed JSON or a provider availability rejection.
Terra fallback applies to confirmed availability failures, not this uncertainty.

All 19 issued broker callbacks have successful host receipts: 12 file writes,
two patches, four shell calls and one file listing. Shell receipt success does
not establish every command succeeded: these were environment/network probes.
The worker encountered missing Node/npm and wrote a runtime bootstrap helper.
Twelve untracked scaffold files remain in the recorded private setup worktree
under `testing/minecraft-v2/.polyinference/worktrees/b9fb1d95b397/`.
No `checks.run`, candidate commit, accepted contribution or gameplay completion
is recorded. The integration branch is `pi-dev`; private files are not delivered
accepted output. The subsequent repository-summary error is a consequence of
the uncertainty barrier, not another original failure.

### Follow-up and verification limits

Application policy should budget native setup work separately from short queries;
a longer cloud timeout in a **fresh** configuration reduces this trigger but does
not repair terminal handling. Generic runtime follow-up should preserve timeout
versus cancellation provenance, await a bounded matching interrupt terminal and
retain uncertainty if termination cannot be established. Never convert transport
shutdown or a generic rollout abort into blanket proof of stopped host work.
Resume retains saved pins, timeout and original resources; changing new-run
preferences cannot repair this saved effect. Reconcile remote work and descendants
before any explicit continuation; do not delete state or blindly replay setup.

Read-only evidence: the run's `ui-run.json`, `config.json`, retained records and
history export `20261102T210716260250Z-f9403892b84b4ae3833e758f62e11ac0.json`,
plus the matching local Codex rollout for thread
`01a19e13-bd55-7532-824e-aca475968f46`. No live generation, Resume, reconciliation,
game execution or framework tests were performed. Documentation navigation is
verified separately; source-level inspection and saved evidence are not a fresh
live timeout reproduction. Existing kernel/inference/UI/recovery guides remain
accurate; no protocol or settings behavior changed.
Documentation generation passed (336 files, 148 leaves); all 66 hashed run,
history and rollout evidence files remained unchanged. Retained project knowledge
was appended to AGENTS.md and read back.
