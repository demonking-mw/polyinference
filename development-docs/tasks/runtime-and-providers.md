# Runtime and provider tasks

The OS owns physical execution, resource facts, replay and durable evidence.
Provider serving behavior belongs to the provider; escalation policy belongs
to the calling agent.

| ID or trigger | Open work and completion evidence |
| --- | --- |
| Native interruption | Distinguish timeout from cancellation and drain for matching terminal evidence after requesting interruption. Preserve uncertainty when termination cannot be proved. See FIX-0068, FIX-0170 and FIX-0171. |
| Haiku input overflow | Review required-only input overflow separately from retryable output failure. The updated 96K/32K preset shipped; safe recovery routing is unimplemented. Reproduce rejection without provider submission before changing policy. See FIX-0179. |
| P1-09 | Archive long campaign history before bounded pruning. Verify rotation and visible gaps for a run beyond the retained journal limit. Old pruned events stay unavailable. |
| CONC-01 / RUN13-04 | Audit command serialization, stalled progress and journal churn with measured workloads. The effective worker-capacity fix shipped; the wider audit was not closed by it. |
| MEM-02 | Reassess the proposed automatic context and explicit agent memory lifecycle against current packing and optional compaction. Keep canonical memory with the agent; test lifetime and retained evidence before expanding any generic OS interface. |
| MCP design review | Review native inference release, shared endpoint admission scope, staged dispatch receipts and optional task/input support in `docs/temporary/proposals/2026-11-13-mcp-support-design.md`. Owner decisions D2/D3/D5/D8/D11 and acceptance scenarios define the next review; this is not implementation authorization. |

Read the native setup, Haiku overflow and concurrency evidence under
`docs/temporary/incidents/` before changing these paths. The runtime boundary
and open design gaps are under `design-docs/simplified-os/`. The original MEM-02
scope is in `docs/temporary/incidents/2026-10-20-memory-management-modes.md`.
