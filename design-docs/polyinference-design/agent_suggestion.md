# Agent suggestions

The HTML remains the agent design, including OS-handled responsibilities. The [concurrency contract](concurrent_coding_protocol.md) and [graph](modified_agent_graph.html) now use your private-copy/two-mutex model.

- **S1 — Give each in-progress agent a private code copy.** Record its base and tool workspace. **Why:** development can overlap without mixing edits.
- **S2 — Show serialized reconciliation before final assessment.** Acquire verification ownership, merge the latest head, run at least one specially prompted development loop, then final assessment. **Why:** clean merges can still change assumptions.
- **S3 — Show two distinct mutexes.** Every shell command uses the shell mutex; reconciliation through commit/publication uses the verification gate. Acquire verification before shell when both are needed. **Why:** mutual exclusion must not create a lock cycle.
- **S4 — Publish before releasing verification.** Record the agent commit, provisional head and unresolved report together. **Why:** the next process must merge published work, not an inaccessible private commit.
- **S5 — Preserve delayed steering.** Finish the captured currently-running locals, including lock waiters, before planning; leave unstarted tasks pending. **Why:** steering neither interrupts current work nor waits for the entire queue.
- **S6 — Retain verdicts, hazards and senior undo.** All completed reports stay unresolved; publish fail/uncertain provenance and record original/revert commits. **Why:** shared-head publication is not senior approval, and undo requires blast-radius review.
- **S7 — Recover ownership with effects.** Save phase, workspace, both tokens and publication/operation references. **Why:** a timeout or crash does not prove protected work stopped.
