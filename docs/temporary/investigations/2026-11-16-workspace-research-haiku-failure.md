# Workspace Research run rejected by Haiku

16 November 2026 · Investigation only. The failing path was left unchanged.
Source checkout `feature/simple-agents` at `3d39890` with the workspace
changes in the working tree. Times are Toronto local time.

| Invocation | Agent | Start → end | Outcome |
| --- | --- | --- | --- |
| `6e78c370bded46c8a097e0a30b7cef8c` | Research | 13:49:39.793 → 13:49:57.959 | GPT‑6.1 Sol planned successfully. The first Haiku extraction failed. |
| `d88e4c324e72479e85e3bafec58c9382` | Simple | 13:50:06.101 → 13:50:50.504 | Completed one GPT‑6.1 Sol request through Codex app-server. |

## Confirmed sequence

1. `ga-effect-ga-research-cloud-plan` completed through GPT‑6.1 Sol on
   `codex_app_server`. The provider reported 15,310 tokens for that turn.
2. `ga-effect-ga-research-tool-evidence-0` successfully searched the supplied
   document corpus. The invocation had no attachments and the lookup returned
   zero hits. This agent searches supplied documents and has no web search.
3. `ga-effect-ga-research-local-extract-0` was submitted through the simulated
   local binding to remote Anthropic `claude-haiku-5-5`. Anthropic returned
   HTTP 400, `invalid_request_error`, with the diagnostic
   “`temperature` is deprecated for this model.” The retained `ModelQuery`
   had `temperature: 0.0`. The general-agent adapter sets that field and
   the raw HTTP adapter forwards it into the request.
4. The effect was recorded as failed and non-retryable, with termination
   confirmed. Its inference reservation was released. The journal retains
   a paused process and its residency record, with no evidence of continuing
   provider execution. No cloud report step was registered.
5. The Simple invocation started about eight seconds after Research ended.
   It used only the Codex Cloud route and the provider reported 16,419 tokens.

The confirmed trigger is the rejected request parameter. The zero-hit lookup
also limited the prompt's evidence, but it completed successfully and the
provider diagnostic identifies a different cause. The timestamps show these
were separate, sequential invocations. The successful Simple run provides
evidence about the Codex path, not about a corrected Haiku request.

## Evidence and limits

Read the retained workspace metadata and OS journals under
`.polyinference/haiku-relaunch/workspace-state/invocations/` using the two
IDs above. The failed effect's `polyinference/provider-error` extension and
the digest-verified diagnostic artifact agree. The provider request ID is
`req_011Ch77Fuwqse5mrvyEwdygV`. The lookup artifact was inspected only for
its hit count. Source evidence is in `src/polyinference/general_agents/os_v1.py`
and `src/polyinference/runtime/inference.py`. No prompts or replies are
reproduced. No provider request, retry, reconciliation, or inference code
change was made for this investigation.

Follow-up `development-docs/FIXES.md#fix-0203` records the request fix for
new workspace runs and its offline verification.
