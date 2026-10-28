# Scheduled real-local Minecraft test — 27/28 October 2026

[Development records](README.md) · [FIX-0148](FIXES.md#fix-0148) · [Earlier test](local-strata-live-test-2026-10-26.md)

**Finished: paused/exit 2; useful partial output, no product acceptance.**
Setup began at the authorized 22:30 Toronto wake-up on 27 October. Frozen CLI
execution began at 22:33:26 and finally stopped at 03:12:16 on 28 October.
The last cloud job reported `Selected model is at capacity`; execution was
confirmed stopped with zero uncertain effects. This is a provider capacity
failure, not evidence of exhausted account quota or of completed gameplay.
No PolyInference implementation changed during this investigation.

[Subsequent failure isolation](minecraft-failure-isolation-2026-10-28.md) traces
the distinct application, context, grammar, test and provider failures against
canonical records and frozen source; its repair recommendations are unimplemented.

The machine-specific review entry point and complete evidence are:

`/home/marven/Projects/pi/testing/minecraft-v1-live-2026-10-27-2230/REPORT.md`

## Actual configuration and preserved authority

- Frozen dirty framework at HEAD `5fe92f3`, 320 files; fresh simple-os/3,
  agent-7/state 2.6. Existing implementation edits and historical runs remain.
- Real `qwen3.8-flash-next-coder-iq1_m` through owned Strata on localhost:8099;
  actual context 65536, one requested/effective slot, parallel/group count one,
  int8 KV, high/4096 thinking, temperature zero. No Haiku or simulation.
- Existing ChatGPT login; real Codex `gpt-6.1-sol` seniors/specialists. Both
  readiness probes passed. Credentials were neither copied nor exposed.
- One worker, 27 sprints, eight hours and 256 calls per original process/root;
  original grants, accounts and deadlines remain authoritative. The 4096 raw
  target and 16384 hard output ceiling differ; no model/config pin was changed.
- Isolated runtime Git history protected the target's unborn `pi-dev` branch.
  Frozen source and agent hashes match. No user/framework commit or push occurred.

## Observed execution and limits

The first worker paused at 23:28:06 on bounded output exhaustion. Supported
exports, database/private-source backups and accounting preceded one documented
same-state Resume at 23:39:26. Its original start/deadline remained unchanged;
calls 52→55 and steps 90→95 established no refill. This did not alter the profile.

The first browser-entry task completed after 132 submitted raw generations.
Five later local tasks stalled at the twelve-idle-decision threshold. Automatic
cloud coding recovered focus handling, pause, seeded creation and saving, using
three native jobs per recovery and each original root's resources. The fifth,
loading recovery, stopped on its first native job with the capacity error.
Its private source is retained separately and was not delivered.

Canonical metrics: **280 submitted raw generations, 46 native jobs**, 26 response
validation failures (24 raw/two native), 214 raw context-omission receipts, five
nonempty kept publications and zero uncertain effects. Native jobs contain
multiple turns. Local stalls, output/thinking interaction and context omission
coincided; this run does not isolate quantization, prompting or packing as a cause.
The narrow earlier qualification gate did not demonstrate this broader objective.

## Independently checked partial delivery

Reviewed/provisional tree `c24e088bc1d54df2a4d175bd4d092e955c72223c` passed
**44 actual host Node tests**. Real Chromium verified terrain/player rendering,
horizontal movement/key release, explicit window-blur handling, pause/Escape and
timing, seeded creation, actual named saves and storage errors. Saved bytes
survived page reload; repository API loading succeeded as a separate diagnostic.
Headless tab switching emitted no native blur and remains inconclusive.

There is **no browser load/list UI or restored play after reload**. Gravity and
jumping are absent; arrow keys in both text fields move the player. The picture
is a small block-colour canvas and white marker. Most gameplay through 2018 and
out-of-game UI remain missing. Tests and kept increments are not product acceptance.

All twelve target baseline hashes and new-path conflicts were checked before
applying this exact thirteen-file tree uncommitted. Six paths differ, including
one new browser-entry test. CLI patch/status, full UI export (24 processes),
exact trees, original/failed source and review manifests remain under the run.
Owned Strata stopped with owner/instance guards; previews and inhibitors ended.
The one-time heartbeat was deleted after final verification.

Setup/provider/configuration, export/reliability/qualification and boundary guides
were reviewed; their interfaces remain accurate and need no edits. Navigation,
current issue pointers, FIX history and retained AGENTS knowledge were refreshed.
Documentation generation/check and whitespace checks passed; the full framework
suite was not rerun for this investigation/documentation-only change.
