# Generalization audit

## Generalization audit of this chat's fixes — 2026-10-19

Status: historical architecture/source review with two local probes. The current
implementation status is in the section above; the following describes the code
at the time of the audit, before those changes.
This audit covers the fixes documented below, including the initial provider,
authority, recovery, delivery and process changes, then telemetry, reporting,
output-limit and tool-environment fixes. The long interruption-reason defect
was investigated-only at audit time. Existing unrelated working-tree changes are not attributed
to this chat merely because they appear in Git's diff.

### Use an OS boundary, not an incident-patch boundary

The useful comparison is a computer OS providing mechanisms to applications.
Here the applications are agent programs and expensive execution is inference.
The repository's simplified-OS design already makes this distinction: the kernel
owns processes/effects/admission/ownership, while the task ledger and sprint
decisions belong to the agent. The runtime admits bounded inference operations;
the model server retains responsibility for token/GPU scheduling. A durable agent
continuation is not a copy of hidden reasoning or a conventional CPU register set.

| Computer OS concept | Agent/inference counterpart | Boundary to preserve |
| --- | --- | --- |
| Process and execution context | Agent identity, program version, context references, continuation and outstanding effects | A process must not require a coding task or a Git commit to exist or finish. |
| System call and device driver | Brokered capability invocation and provider adapter | Validate grants/arguments/effect identity; keep coding reply grammar in the calling agent. |
| Address space, filesystem namespace and temporary storage | Private source view, environment/config/cache, artifacts and scratch | Separate source, disposable data and persistent process state, with explicit lifetimes. |
| Resource limits and admission | Tokens/context reservations, model concurrency, bytes, deadlines and spend estimates | Report the exhausted resource; the agent decides how to simplify its work. |
| Error codes and fault containment | Typed failure category, fault scope, termination/effect certainty and causal references | A malformed request, an unavailable endpoint and unknown remote execution need different handling. |
| Journal and recovery | Durable intent/result IDs, receipts, checkpoint references and linked new attempts | Replay preserves the old result; a new execution requires an authorized new identity. |
| Kernel trace buffer and observer processes | Bounded native telemetry and UI/terminal reporters | Dropping diagnostics must not change execution facts or replace the primary failure. |

There are no incident-ID or Minecraft-specific branches in the reviewed `src`
tree. The remaining hard-coding mostly targets the reference coding agent's
workflow, rather than a particular incident. Some constants are legitimate safety
bounds; replacing every literal with configuration would not address the important
architectural coupling.

### Foundations worth retaining

- **Telemetry fix — OS mechanism, broadly applicable.** `NativeEventLog` bounds
  observations while terminal state, final reply and usage survive independently.
  This is the equivalent of a bounded trace buffer, rather than execution depending
  on whether logs fit. The Codex event names belong in that protocol's driver.
- **Request framing — appropriate agent/driver split.** The agent adds an explicit
  current request after historical replies, while the Anthropic adapter checks its
  supported request shape. The final-request fix applies to phase transitions,
  not just the historical Haiku failure. Requiring a final user turn for all
  Anthropic requests is a deliberately restricted common subset, not support for
  every model's possible prefill capabilities.
- **Recovery identities — OS mechanism with agent policy above it.** Original
  effects remain immutable, recovery attempts are linked and bounded, and unknown
  remote execution retains resources until reconciled. The coding agent's choice
  to rebuild reconciliation after a failed assessment belongs in its controller.
  A killed local transport is correctly not proof that remote execution stopped.
- **Process completion and file delivery — useful separation already introduced.**
  `Processes.finish` accepts artifact-only or empty results. `Outputs` delivers
  explicit file artifacts with baseline checks and intent/receipt replay, without
  deciding whether the user's objective is met. The coding agent gates delivery
  on its own acceptance. These are reusable beyond code generation.
- **Source isolation — generalized cause, not a cache-name exemption.** The npm
  fix isolates HOME/XDG/temp paths for both checks and shell. It does not ignore
  arbitrary `.npm` files or weaken source grants. npm/pip environment variables
  are compatibility details appropriate to an execution-environment profile.

### Highest-value places to generalize

1. **Registered capabilities and effective grants — OS/agent boundary.**
   `runtime/tools.py:checks.configure` reads `task/project_setup`, `setup/completed`
   and `plan/`; `configured_checks` resolves `setup/checks`; kernel check grants
   also special-case that record. `Workspaces.extend_setup_scope` uses a
   `polyinference/project-write` flag on an agent TaskSpec. These mechanisms know
   the reference application's lifecycle. An OS should enforce a versioned grant
   for a resource/capability and return its effective authority; the agent should
   decide when setup may select/seal checks or request additional explicit paths.
   Derive prompt-visible authority from that same grant, rather than separately
   reconstructing it. This addresses the latest run's missing setup-authority
   explanation without adding another phase-specific prompt exception. Keep
   explicit-scope restrictions, generation checks and immutable check provenance.

2. **Native brokerage must not prescribe an application's return protocol — OS
   provider adapter and capability ABI.** Protocol registration is generic, but
   `CodexAppServer.generate_job` advertises a fixed coding-tool schema and tells
   every brokered job to finish with `candidate`, `assessment` or `needs_review`.
   The kernel's subordinate-effect allowlist and callback construction likewise
   assume a code workspace and classify just three file tools as reads. Register
   capability schemas/effect classes/resource requirements, then pass the granted
   subset through the adapter. Let the calling agent supply phase grammar and
   instructions. A researcher with a brokered non-file tool should not need a
   TaskSpec, coding response or fake workspace to use the same OS. The current
   non-coding regressions cover HTTP and read-only native fixtures; they do not
   prove arbitrary brokered applications work. This is remaining coupling around
   the generalized registration fix, not a regression caused by event retention.

3. **Fault scope and retry eligibility — OS fault handling, agent recovery policy.**
   HTTP stop reasons are already normalized across four protocols, but kernel
   result handling still checks particular Python exception classes and ad-hoc
   extension keys. The permanent-failure circuit is keyed by role/model/endpoint,
   phase/protocol and configuration, not error category/code or request cause.
   Different request-specific invalid-input failures therefore accumulate in one
   counter. Two unrelated malformed requests can block later healthy requests in
   the same bucket. Like an OS distinguishing a caller's EINVAL from a failed
   device, classify fault scope explicitly: operation/input, credential/account,
   endpoint, resource limit, application, or unknown execution. Endpoint health
   and repeated equivalent bad requests need separate containment policies. Keep
   exact original intents and explicit recovery; do not turn all errors into an
   automatic retry loop. Retry-after metadata is currently retained, not an
   implemented general backoff scheduler.

4. **Tool environment as an owned resource — OS process/environment lifetime.**
   The source-contamination fix creates a fresh HOME/config/cache for each
   invocation and destroys it afterward. That is safe for disposable housekeeping,
   but local tool configuration or user-local installations cannot survive a
   later shell/check invocation. A normal process environment has a defined
   lifetime across child commands. Separate invocation scratch from optional
   process/workspace/run-owned tool state, preserving isolation from source and
   other principals. Account for its disk usage and specify cleanup/restart
   behavior. Current temporary environments sit outside the workspace scanner's
   budgeted tree. Trusted provider authentication, brokered tool homes and
   host-maintenance commands need distinct profiles; applying the same empty
   HOME to the Codex provider would break its authenticated service context.
   Shared subprocess supervision can consolidate group termination, deadlines,
   output draining and lease cleanup while retaining these separate profiles.

5. **Output-limit recovery as an agent strategy using OS resource facts — mostly
   agent policy, with a normalized OS outcome.** `AgentServices.model_result`
   targets 4 KB then 2 KB, repeats the same token cap, and advises scaffolds/file
   patches or a smaller planning increment. This is bounded coding-agent policy,
   not a general inference resource manager. A fixed byte target is not a token
   budget and may not solve a thinking-only cutoff or fit another output schema.
   Give the agent structured limit/usage/completion facts and let its phase/task
   strategy choose a smaller action, decomposition, compact response or an
   authorized budget change. Centralize the strategy's limits instead of repeating
   4,096 in both recovery and `response_budget`. Keep the raw-query-only automatic
   eligibility until stronger effect guarantees exist: a native job may already
   have executed tools, so copying the message that 'none of its actions executed'
   to native retries would be incorrect. The OS should enforce the chosen budget
   and retry identity, not decide to write a scaffold.

6. **Typed lifecycle updates — agent application persistence.** The latest
   317-character `stop_reason` crash exposes a family of writes, not one oversized
   string. The controller's exception path also writes up to 2,000 characters to
   the same 256-character field; settlement uses unbounded reasons, while worker
   parking validates only before `model_copy(update=...)`. Introduce an agent-owned
   validated transition/write boundary with short reason codes and complete
   diagnostics retained separately. Apply it to park, exception, cancellation,
   retirement and recovery, including old invalid records. The OS generic JSON
   store should retain its transaction/version contract, not interpret coding
   attempts. This is analogous to an application validating its own database
   objects, separate from filesystem or storage-driver correctness. This defect
   was diagnosed before this audit; the implementation section above records its fix.

7. **Diagnostic causes as structured references — observer/application boundary.**
   The terminal reporter now cannot replace a runner outcome, which generalizes
   well. The summary still treats `app/run.blocker` as either arbitrary text or
   an operation ID and resolves only `effect/<blocker>`. Keep a structured cause
   with owner/layer, category, operation/resource reference and detail reference,
   and make terminal/UI/export render the same facts. Application task failures
   and observer failures should remain separate from OS process/effect failures.
   Numeric caps on event retention or reporting errors are reasonable defaults;
   they are less important than getting this ownership and causality right.

8. **Business success and semantic progress — agent policy, not kernel policy.**
   Objective propagation is generic, but prompts alone cannot prove feature
   completion. The shared setup/task/final check selection is still a known open
   issue. Separate prerequisite, task and final acceptance contracts in the agent;
   let the OS execute pinned checks and bind evidence to revisions. Likewise,
   excluding memory from the review fingerprint helps, but pending/interrupted
   task metadata can still change without product progress. The agent should
   define useful progress; the OS should enforce budgets/deadlines and report
   consumption. Renaming tasks or checking Node availability must not stand in
   for an implemented product.

### Order and verification

First fix the invalid agent lifecycle records and expose effective authority to
setup. Then establish the capability/grant boundary and fault taxonomy, since both
make subsequent generalization safer. Follow with explicit environment lifetimes
and phase-aware response strategies. The existing scheduler, effect journal and
uncertain-execution rules are foundations to preserve during these changes.

Add cross-application regressions, not just more variants of the original incident:
an artifact-only agent; a native agent with a custom brokered tool and non-coding
schema; two unrelated bad requests versus repeated credential failure; linked
retry after a resource cutoff versus uncertain execution; a two-command tool
setup/check sequence; scratch quotas and restart cleanup; long application
diagnostics across park/retire/replay; and observer failures with stable causes.
Assert these invariants rather than fixing tests to the literal 4 KB retry target.

Verification in this audit: source/design/test review, a search finding no incident
IDs or Minecraft-specific runtime branches, and two read-only Linux probes. The
probes confirmed that different request contexts share the circuit bucket, and
that a HOME `.toolrc` disappears before the next invocation; both temporary
environments were cleaned. The latter demonstrates the current lifetime contract,
not a newly observed production failure. No providers were contacted, no historical
state was changed, and the full regression suite was not rerun for this analysis.
The last full verification at audit time was 188 passed as recorded below. Current
verification is recorded in the implementation section above.
