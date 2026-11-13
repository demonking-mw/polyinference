# Workspace authority and publication

## Workspace grants and coding setup

Workspace creation requires a registered owner and atomically installs its
`workspace-grant/<id>` with the authoritative manifest. That grant narrows the
process capability set, specifies allowed check names, and explicitly permits or
forbids adding project-relative paths. Expansion is rejected under an explicit
filesystem scope. Current-generation, path, digest and final-delta checks remain.
An empty copied view or a read-only grant is valid; the calling agent supplies
the read/build closure it actually needs.

The coding worker's `load` passes its bounded tool/check grant to `create`.
Only project-mode setup opts into expansion. `workspaces.authority(id)` supplies
the prompt's `write_authority`, so the model sees the same permission that the
broker enforces. The OS no longer reads a TaskSpec's project-write extension.
The old wire field `task_spec_ref` and `retag_task_spec` method remain opaque
provenance references; the runtime does not interpret the referenced task.

`AgentServices` installs `checks.configure` from `agent/runtime_policy.py`.
That handler owns the initial-setup-only rule and immutable per-purpose
`setup/checks/<purpose>` selection. Its application-owned CheckSelection schema
distinguishes prerequisite, task and final acceptance checks. It registers ordinary
commands through `tools.register_check`, grants selected names to setup, and lets
`sync_setup` update the agent ledger/spec.
The OS stores immutable command definitions under `runtime/check/<name>` and
runs only granted names against the current source revision. It does not read
`task/project_setup`, `setup/completed` or `plan/`.

The agent now separates prerequisite, task and final acceptance policy (FIX-0086).
Explicit legacy config.checks remains combined task/final policy unless overridden;
setup-discovered task checks never silently authorize final completion. These
agent fields and criteria do not add coding-purpose interpretation to the OS.

## Publication and lifecycle data

`records.publish` requires a process capability grant and a currently owned
resource permit. `OperationRequest.conflict_keys` checks the actual named resources,
not an assumed coding lock. Atomicity and immutable receipts remain OS mechanisms.
Record names such as `app/run`, `report/` or `head/provisional` have no special
meaning in generic publication.

The coding agent installs a publication policy keyed by its program ID. That
policy checks the coding verification permit, broker-minted commit provenance,
expected shared head, report ownership and private-failure rules. Its updates
close starts and capture other workers when a verdict requires review, in the
same transaction as the publication. This preserves the four-worker drain path.

Publication policies must be reinstalled before new publication after restart.
A program that previously required a policy must not silently fall back to
generic publication while its handler is absent. Already committed receipts
remain replayable independently of retired permits.
`register_publication_policy` pins the requirement under
`runtime/publication-policy/<program_id>`. Missing code produces a known failed
new publication without changing the batch. Installing the handler afterward does
not rewrite that operation's failure: retry with a new operation/logical identity.

The agent also owns `TaskAttempt` validation. `task_attempt` validates the updated
value for park, publish, retirement, recovery and setup transitions. Human notes
are retained as artifacts through `polyinference/stop-detail`; `stop_reason`
contains a bounded code. Existing invalid long notes can be retained while the
attempt is retired. Generic OS storage does not validate this application schema.

Role names do not confer OS privileges. Management/reserve treatment is explicit;
`control_token_reserve` is an OS resource setting. `AgentConfig` accepts the former
`review_token_reserve` spelling as an alias and preserves coding defaults. Bare
`RuntimeConfig` has no coding phase reserve or predefined senior/worker roles.
