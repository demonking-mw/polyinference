# Next iteration backlog

Ideas recorded here are deferred, not requirements for the current implementation.

<a id="shared-agent-support-library"></a>
## Shared agent support library — deferred on 2026-10-20

Status: proposed for the next stage; explicitly excluded from the current fix.
Source: the user's request to keep the current system split between OS and agent.
Earlier design: [three-layer responsibility proposal](agent-os-overflow-responsibility-proposal-2026-10-20.md).
Current plan: [optional OS context handling](optional-os-context-management-proposal-2026-10-20.md).

Consider an optional caller-side library once several real agent implementations
show which patterns are worth sharing. Candidate helpers include declarative
context construction, response-schema validation, application recovery loops,
checkpoint/handoff utilities and convenience wrappers over OS context services.

The motivation is to reduce duplicated agent code without adding coding workflow
to the OS. The cost is a third architectural surface, versioning and lifecycle
complexity. The user considers that premature for the current stage.

Do not introduce this library, require it, or route the current fix through it.
For now, generic execution safety and optional automatic context/compaction
services belong to the OS; coding-specific choices and semantic recovery belong
directly to the coding agent. Future evaluation should preserve direct OS access,
support non-coding agents and derive the library from demonstrated reuse.
