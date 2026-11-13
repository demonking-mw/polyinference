# Central OS configuration

Configuration (`docs/guides/configuration.md`) · Settings module (`docs/modules/settings.md`) · [Audit inventory](../os-config-inventory.md)

[src/polyinference/os_config.py](../../src/polyinference/os_config.py) is the single
source of generic OS defaults and operational validation ceilings. `DEFAULTS`
contains the existing endpoint/resource/context defaults; `BOUNDS` contains their
operational schema ceilings; `OSTuning` exposes the formerly embedded controls.
`system_settings.py` validates and composes these values without defining another
set of defaults. Helpers used without a runtime use the same canonical defaults.

Set preferences together in the run JSON before starting:

```json
{
  "system": {
    "tuning": {
      "journal_retention_events": 50000,
      "events_page_size": 100,
      "events_page_max": 1000,
      "file_list_default": 250,
      "file_list_max": 2000,
      "native_event_limit": 4000,
      "response_recovery_seconds": 20
    }
  }
}
```

This is a fragment to merge with the required endpoint/project settings, not a
complete launch file. Omitted tuning fields keep their canonical defaults.

For native cloud jobs, see [cloud agent endpoint timeouts](cloud-agent-timeouts.md).

Resolved nested paths/collections and the environment mapping are immutable, including aliases from the
system view. HTTP environment trust also controls proxy routing. Inspection readers inherit saved SQLite
timeouts; a standalone database needs a default-timeout metadata lookup before its policy is known.
Unknown keys, invalid ranges, default pages larger than maximum pages and default
shell timeouts above their maximum reject. Environment overrides cannot replace
host-issued private HOME/cache/temp paths. Sandbox paths and ignored names remain
trusted deployment policy; changing them grants no source authority.

All resolved fields appear in the saved configuration and its immutable digest.
`runtime/os-tuning` retains the effective operational settings for independent
record writers and inspectors. CLI/UI writers reopening that database inherit its
retention/page policy instead of resetting to library defaults. Journal pruning
removes historical events only; canonical records remain. `null` retention keeps
all future events; it cannot restore previously pruned events. An omitted exclusive
wait cap keeps the process wall-time bound; standalone helpers retain their prior fallback. Larger retention,
buffers and excerpts consume more disk/memory/context.

The constants refactor preserved previous defaults; simple-os/6 additionally introduces
one local token pair and provider-owned cloud limits (`docs/guides/local-token-limits.md`). One corrected duplicate is the kernel
version display: diagnostics and the durable kernel pin now read the same constant.
Changing source defaults or run configuration requires fresh state; use the frozen
original source/configuration for historical runs. No budget/deadline/grant is
rewritten, and this change does not resume any run.

Coding-agent presets remain explicit application choices in
[agent/system_settings.py](../../src/polyinference/agent/system_settings.py).
They may intentionally override generic defaults; workflow, model selection,
semantic recovery and acceptance policy remain outside the OS configuration.
Wire tags/versions, path traversal restrictions, hashes, units, index arithmetic,
one-driver/one-effect rules, serialized filesystem mutation, mandatory completion
metadata and confirmed-termination rules are protocol or safety invariants.
SQLite WAL/FULL durability remains a fixed policy, centralized for maintenance.
Native event-name preview length affects diagnostics, while delta filtering uses the original wire method.

Inspect every field/default/range in the generated [settings schema](../settings-schema.json)
or print the complete operational section without starting services:

```bash
python -c 'from polyinference.os_config import OSTuning; print(OSTuning().model_dump_json(indent=2))'
python scripts/settings_docs.py --check
```

[tests/test_os_config.py](../../tests/test_os_config.py) verifies nondefault retention,
independent writers, paging, telemetry, environments, dependency classification,
combined command output limits and changed-configuration rejection. Existing OS,
context, native, recovery, capability, workspace and UI suites cover preserved guards.
