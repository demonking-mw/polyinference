# File tools, checks and foreground commands

[Module index](README.md) · [Architecture](../architecture.md) · [File tree](../file-tree.html)

The broker executes explicitly granted file/command operations and records truthful bounded outcomes.

| File | Responsibility |
| --- | --- |
| [src/polyinference/runtime/tools.py](../../src/polyinference/runtime/tools.py) | Scoped file operations, named configured checks and source-bound evidence. |
| [src/polyinference/runtime/shell.py](../../src/polyinference/runtime/shell.py) | Enabled foreground shell scripts, scope auditing and shared shell gate. |
| [src/polyinference/runtime/commands.py](../../src/polyinference/runtime/commands.py) | Bounded trusted argv execution for Git and merge helpers. |
| [src/polyinference/runtime/tool_environment.py](../../src/polyinference/runtime/tool_environment.py) | Invocation-private HOME/cache directories outside assessed source. |

## Interface and ownership

Commands select disabled, trusted or optional Linux bubblewrap execution.
Applications choose checks/dependency commands and declared outputs. Check argv
is not a shell script. Tool environment does not inherit provider credentials.

## Principles to preserve

- Trusted execution has host privileges; scope auditing is not a sandbox.
- Timeouts/cancellation must preserve process/effect certainty.
- Generated output must be declared without obscuring source changes.
- Failed setup/check output is evidence for agent repair, never manufactured success.
- Tool home/cache cleanup cannot become source mutation or extra write authority.

## Verification and related reading

[Tool environment](../../tests/test_tool_environment.py), [setup tools](../../tests/test_setup_tools.py),
[workspace outputs](../../tests/test_workspace_outputs.py) and [runtime](../../tests/test_runtime.py).

[Budgets/execution](../guides/budgets.md) · [Runtime boundary](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md).

After a fix/feature, update this guide and all affected docs/settings/navigation,
then record actual verification in [FIXES.md](../../development-docs/FIXES.md).
Follow [documentation maintenance](../maintenance.md) in the same task.

## Integrated reliability branch (2026-10-26)

files.read accepts bounded offset/max_bytes for progress-aware read coverage,
retaining the existing limit alias, check grants, generation binding and source
authority. Its public FileRead schema advertises the new bound to native brokers.

Read results retain next_offset for existing paged readers as well as returned-byte
coverage. Cache-like names such as .npm remain source during checks/scope auditing;
real tool caches stay in the separate invocation environment.
