# Build outputs and native harness boundary — 19 October 2026

Incident: run `8b5eb9df2646`, source project `minecraft-7`. The setup worker
returned a candidate after about 73 seconds. The final Vite build exited zero,
but generated `dist/index.html` and two assets. They were outside the source
write grant. The check became inconclusive, then preserving the private delta
raised `Private changes exceed write scope` before verification ownership.

The run already used project scope and an expandable setup grant. Its source
grants were correct for the scaffold. `.gitignore` included `dist/`, but source
scanning used fixed exclusions. Separately, expanding a grant rematerialized
only scanned source, dropping installed `node_modules` and causing the missing
Vite error. Reinstalling dependencies in `prebuild` worked around that symptom.

## Runtime changes

- Checks declare `output_paths`, selected and retained with their command.
  Generated output is excluded consistently from source identities, deltas and
  commits. Tracked and granted source take precedence; `.gitignore` is not an
  authority boundary. Setup rejects output declarations covering existing source.
- Installed dependencies are private execution state. Copies across write-grant,
  read-closure, setup-spec, integration and abort generations retain dependencies
  only when the recorded dependency inputs match. Source changes to dependency
  manifests/locks invalidate that state before commands. Copies preserve internal
  executable links, do not share mutable files, and count against storage limits.
  Tracked source inside a dependency-named directory is never discarded as cache.
- Source paths and dependency identities survive reopening runtime state.
- Scope failures include paths, grant and phase. A development handoff returns
  the error to the worker for at most `max_repairs` correction attempts, preserving
  its files. Exhaustion parks the worker. Real check source mutations still
  invalidate evidence, with changed paths in the check output.

## Codex audit

The adapter already requested the named `polyinference_readonly` filesystem
profile, disabled native shell, denied escalation, and advertised host callbacks.
The worker prompt preferred host tools but did not explicitly explain competing
native tools or stale filesystem generations. There was no independent comparison
of the native view after a job.

Codex now receives a separate input copy. The native developer instructions and
worker prompt require host tools for current reads, edits and commands. Before
callbacks and after terminal replies, the runtime compares the exact input copy
and observed broker source views, including retired generations. Direct mutations
are rejected even when the path is in the source grant. A violation before a
terminal response preserves unknown-execution semantics; a returned terminal job
with detected mutations is a known failure. An input copy is never copied back
into the writable workspace.

An ephemeral session against the installed Codex CLI 0.163.0 confirmed the actual
effective policy: `sandbox.type=readOnly`, `networkAccess=false`, and
`approvalPolicy=never`, with `polyinference_readonly` active. No model turn was
sent. The adapter now verifies the returned policy before starting any turn and
rejects missing or broader permissions. The installed experimental protocol schema
also confirms support for named permissions and `developerInstructions`.

The incident export contains 19 `polyinference_tool` requests and 19 corresponding
child effects, with no recorded native command-execution or file-change items.
That telemetry is consistent with brokered execution; it is not independent
proof of the absence of direct writes. The observed pause is explained by the
declared check producing ordinary build files.

Raw chat/Responses/Anthropic requests have no native filesystem executor. This
distinction is about the harness, not local versus cloud inference. Trusted host
commands retain their existing execution trust model.

The original incident state and export are retained. Existing runs pin program,
graph and prompt identities; the updated implementation does not silently migrate
or resume an old run under different semantics.

Regression coverage: `test_workspace_outputs.py`, native worker stdio and tamper
tests, existing setup/tool-environment/capability/recovery tests, repository lint,
and the full regression suite.
