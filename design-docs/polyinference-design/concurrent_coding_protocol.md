# Concurrent coding protocol

Current design contract, derived from your private-copy/two-critical-section model. This replaces the earlier task-long coding/shell owner gate and shared-editing workspace proposals. It is a design specification, not an implementation.

## Execution model

Each in-progress coding process owns a codebase copy at a recorded base revision `B`. Private edits, context preparation and model reasoning can overlap with other processes. Start with full working trees; partial copies must include the dependency/build/test closure and a reliable mapping back to the full project before publication. Only endpoint/resource admission and the two critical sections below constrain that overlap.

The LLM OS remains an ordinary program operating endpoints and tools. Its coordinator continues scheduling and processing events throughout; no computer-kernel preemption or integration is involved.

## Two separate ownership objects

| Object | Scope and owner lifetime |
| --- | --- |
| `shell_mutex` | One shell/script operation at a time across all managed coding processes, even on different private copies. Acquire before dispatch; release only when the relevant work actually finishes and output/effects are accounted for. Include Git/test/build commands when invoked through the shell. Non-shell private edits do not need this mutex. |
| `verification_gate` | One process at a time in the final reconciliation/development/assessment/commit/publication phase. Acquire before reading the head used for reconciliation; release after the durable completion boundary or a reconciled, explicit abort. It does not cover ordinary private development. |

**Acquisition order:** `verification_gate -> shell_mutex` when both are needed. A shell owner outside the verification phase must finish and release `shell_mutex` before requesting `verification_gate`. Never wait for verification while holding shell ownership. Short coordinator metadata locks/transactions are separate and never span these waits.

A verifier may retain `verification_gate` while waiting for shell access or local inference. Other agents continue private development; their shell commands can run between the verifier's commands, one at a time. FIFO/age-aware shell admission must give the verifier progress; verification ownership does not grant a second shell slot or reserve the shell continuously. A process cannot wait synchronously for another process to enter its held verification gate.

## Per-process sequence

```text
private development at base B
  model reasoning / private non-shell edits may overlap
  each shell operation acquires/releases shell_mutex

request verification_gate with shell_mutex released
  capture current provisional shared head H
  preserve the private delta; merge H into this process's copy
  resolve conflicts without discarding either side silently
  run at least one development/reconciliation LLM loop
    special prompt: inspect incoming changes, assumptions and necessary adaptations
  perform bounded further repairs if needed
  run final one/few testing/examination/assessment LLM loops
    tests/shell commands still acquire shell_mutex individually
  produce verdict: fail | uncertain | successful
  commit attributable change; publish shared head + report boundary
    execution=completed; resolution=unresolved for every verdict
release verification_gate
next waiting process captures this updated head and repeats
```

The development loop after merging is mandatory, even when Git reports no conflict. One iteration is a minimum, not a proof of compatibility. Reserve reconciliation and final-assessment allowances before entry; after any implementation repair, assess the final tree again. If a phase cannot finish, retain interrupted/assessment-pending state rather than invent a verdict or normal completion.

## Shared publication and senior review

The next agent must receive the predecessor's **published shared head**, not just a commit existing in that predecessor's private branch. Keep `provisional_head` distinct from senior review dispositions. Publishing a commit is not accepting its verdict or resolving the task.

**Selected initial policy, matching the proposed sequence:** every normally completed process publishes its identifiable change commit into provisional shared history, including fail and uncertain, with its verdict/hazard attached. Every report remains unresolved until the sprint coordinator reviews it. Later processes must see unresolved/failed/uncertain provenance during reconciliation; affected dependencies may require senior review before continuing. A policy that retains questionable commits privately is a meaningful alternative, but changes which predecessor commits the next process receives and must be selected explicitly.

Preserve the agent's pre-merge private delta/history. Publish one attributable commit `P` whose parent is the captured shared head `H` and whose tree is the final assessed tree. This can be a consolidated task delta; retain internal merge/WIP references as evidence. Then reverting `P` reverses this process's net contribution, including conflict adaptations, without also reversing the preceding agents' incoming changes. If merge commits are published instead, define mainline/revert behavior explicitly; do not leave senior undo ambiguous.

Record `B`, captured `H`, private pre-merge delta/ref, final tree, assessment evidence/environment, published `P`, verdict, changed scope and unresolved hazards. Under the still-held verification gate, ensure Git/evidence objects exist, then atomically compare expected head/plan authority and publish `provisional_head=P` with the immutable report and notification intent in metadata. No external model/Git operation runs inside that short transaction. A convenience Git ref mirrors the metadata authority and is reconciled after a crash. This does not claim one transaction across Git, checkpoints and provider APIs.

Senior keep/revert/retry/defer decisions are separate. A senior revert acquires `verification_gate` and `shell_mutex` for its shell operations, examines later/dependent commits, creates an explicit revert change, checks the resulting tree and publishes the new head before release. Keep the original assessment and review history. Git simplifies undo; it does not eliminate blast-radius analysis or reverse external non-Git effects.

## Isolation, stalls and steering

Each tool call declares a process workspace. Private copies alone do not isolate shared build caches, databases, ports, services or remote destinations. Scope these resources per process or declare additional conflict keys; serialization of command launch is insufficient when background effects outlive a command. All managed shell activity, including compatible cloud-specialist tools, must use the broker. An opaque endpoint that can execute uncontrolled shell work does not satisfy this model's global shell guarantee.

Persist ownership and operation identities. A timeout, disconnection, saved trap frame or expiry does not prove the owner stopped. Retain conflicting exclusion while a relevant command/publication outcome is unknown; reconcile the workspace, effects and journal before a new owner proceeds. If no protected operation remains active, an interrupted owner can explicitly abort, retain its private changes/checkpoint, then release without normal completion. A resumed old owner must not publish without fresh ownership/version validation.

Steering remains delayed: stop new local starts, capture the currently in-progress locals (including those queued for either lock), let those processes finish the sequence above on their existing instructions, then invoke the sprint planner with steering and unresolved reports. Do not wait for unstarted queue tasks or prevent captured waiters from entering the gates needed to finish.

## Verification scenarios for a future implementation

- Two agents develop privately at `B`; A publishes `P1`, then B must merge `P1`, run the reconciliation development loop, assess and publish `P2` before releasing verification ownership.
- Several shell requests across different copies execute one at a time; an outside shell owner releases before waiting for verification. The coordinator keeps handling events.
- A clean Git merge hides a semantic API change; the mandatory development loop catches it or the assessment reports uncertainty/failure honestly.
- A fail/uncertain commit is published unresolved; the next process receives both the code and its hazards, and senior rollback checks downstream effects.
- Crash after private commit, after metadata publication, or during a shell action cannot yield duplicate commits, a lost report or unsafe early lock release.
- Steering with A verifying, B developing and C unstarted lets A/B finish, leaves C pending, then invokes the planner.

The serial phase includes merging, development re-examination, final assessment and publication, so it can be the throughput bottleneck. Measure gate wait/hold time, shell wait time, merge adaptations, re-assessment cost and rollback propagation before relaxing either mutex.
