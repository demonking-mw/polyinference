# Opt-in live smoke runner

[Modules](README.md) · [Checks](../testing.md)

[scripts/smoke_os_codex.py](../../scripts/smoke_os_codex.py) runs an opt-in real
Codex-backed coding task in a disposable directory and retains its run evidence.
It uses provider allowance and needs same-host Codex authentication and a working
runtime environment. Inspect the script before invoking its CLI; it creates a
temporary directory automatically. Its retained `source_unchanged` assertion
reflects the older isolated workflow and needs review before treating this script
as a current in-place acceptance check. This reorganization did not run or repair it.

The script exercises application/runtime wiring; it is separate from the default
offline suite. Preserve brokered tools, explicit grants, fresh state and actual
acceptance evidence. A small successful run does not prove provider throughput,
Linux sandbox coverage or general product quality.

After changes, update this guide and relevant [provider/setup docs](../guides/providers.md)
and record only checks actually run in [FIXES.md](../../development-docs/FIXES.md).
