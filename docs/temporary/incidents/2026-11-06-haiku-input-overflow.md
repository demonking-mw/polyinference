# Haiku input overflow and missing cloud handoff

<a id="run-dd20b7d98b80"></a>
## Haiku input overflow and absent cloud handoff — 6 November 2026

Status: Haiku preset updated; escalation investigated only, no recovery implementation changed.
`development-docs/FIXES.md#fix-0179` records verification and preservation limits.

The supplied run export reports a paused first database worker after setup was kept.
Its first request measured 37790 serialized bytes. Optional focused-source removal
left 29240 required bytes against a saved 24000-input allowance; no provider counter
was configured, so measurement used a disclosed conservative byte/token bound.
The runtime rejected before provider submission. An earlier setup diagnostic also
failed with 26794 required bytes. Both exact receipts replay offline on main's
unchanged context/prompt implementation. The status-missing-db patch is unrelated.
Setup ultimately passed; product tests/acceptance still failed on missing tests/entry.
The database worker submitted no generation and retained no source changes.

The run configured two native retries plus one caller retry and one cloud recovery.
These are not a blanket escalation chain. InputOverflow has no retryable flag;
ModelRetries._blocked rejects it. park_model_failure accepts only eligible retryable
IncompleteGeneration, ModelResponseError and NativeJobStopped output failures.
Consequently no worker-exception packet was created for cloud_recovery.offer/prepare,
and the controller paused with the original blocker. Provider model fallback is a
separate same-provider availability path; the Haiku endpoint has no retry_model.
Cloud senior planning had already succeeded, but no Codex repair assignment existed.

Only fresh bundled Haiku settings change to 96000 input/32000 output. Existing
remote Anthropic explicit configurations, real-local preferences and historical
source/accounts/deadlines remain preserved. Generalizing input-failure escalation,
changing prompt construction or enabling provider token counting remains unimplemented
and outside this authorization. Retry counters alone cannot make this failure eligible.
