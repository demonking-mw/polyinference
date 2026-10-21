# Proposed split between the OS, shared agent support and applications

20 October 2026. Design only. This refines the placement of mechanisms in
[FIX-0051's overflow proposal](inference-overflow-safety-proposal-2026-10-20.md)
after the user asked how to preserve OS generality and simplicity while making
agents easy to design. No implementation or configuration changed.

Current disposition: the user deferred the shared agent library to the
[next iteration backlog](next-iteration.md#shared-agent-support-library).
For this stage, follow the [two-owner OS/agent plan](optional-os-context-management-proposal-2026-10-20.md).
The three-layer proposal below is retained as historical design material only.

## Recommendation

Use three layers: a small OS execution contract, an optional shared agent library
with reusable recovery defaults, and each agent's application policy. The library
is ordinary caller-side code using the same public runtime boundary. It is not
a privileged component, a compulsory graph framework, or part of the kernel's
understanding of tasks.

Later user-directed refinement:
[optional OS context handling and compaction](optional-os-context-management-proposal-2026-10-20.md)
supersedes the library-only placement of optional packing/compaction. The OS
would expose these as optional generic services controlled by effective agent
policy; the mandatory kernel would remain small. This document remains the
historical earlier proposal, not an implemented design.

FIX-0051 allowed the OS to select caller-authorized optional context groups and
coordinate a registered smaller-response strategy. The refinement here is to put
the selection algorithm and adaptive response loop in the shared library. The OS
supplies authoritative measurements, outcomes, retained effects and bounded
execution. A new kernel recovery-policy registry is unnecessary for this purpose;
normal operation results and existing process continuations suffice.

## Responsibility table

| Concern | OS, including endpoint adapters | Shared agent library | Individual agent |
| --- | --- | --- | --- |
| Endpoint capacity | Expose effective input/output/byte limits, enforcement capabilities and counting certainty for each binding | Use those limits when constructing requests | Choose permitted bindings and requested limits |
| Request sizing | Prepare the complete adapter request; measure and enforce the same prepared representation that will execute | Pack optional groups using the OS sizing service, including recovery feedback | Identify required inputs, optional groups and allowed omission priorities |
| Input overflow | Return bounded typed facts without submitting; retain the full request by reference | Drop permitted whole groups, re-prepare, and retry a fitting request; retain omission provenance | Summarize semantically, page required data, split work or authorize another binding when ordinary packing cannot fit |
| Output cutoff | Normalize completion/cutoff facts; retain bounded diagnostics; prevent incomplete replies from being successful actionable results | Validate the declared response protocol and issue bounded smaller-response attempts where effects and termination allow | Define the response grammar, useful output unit and any domain-specific decomposition |
| Known transient service fault | Perform safe bounded transport retries with durable identities and resource accounting | Consume the effective recorded result | Choose whether persistent endpoint trouble warrants replanning or an authorized alternate binding |
| Effects and uncertain termination | Track tool effects, grants, ownership and termination; prevent unsafe replay and retain resources when necessary | Wait for reconciliation or resume from recorded settled effects | Reconcile domain-specific external effects and choose semantic continuation |
| Failure delivery | Return bounded control results/notifications to host code, independent of whether a model prompt fits | Handle those results without crashing the agent driver; preserve continuation state | Decide whether to decompose, defer, seek input or stop the objective |
| Source scope and generated output | Enforce explicit authority and output/scratch lifetimes; preserve unexpected attached-directory writes | Offer explicit scratch/output helpers and checkpoint/handoff utilities over OS records/artifacts | Select test commands, declare generated outputs, choose Git workflow and judge acceptance |

## Keep the OS surface small

The conceptual additions are limited to reliable endpoint-limit discovery or
declaration, prepared-request measurement/execution, and normalized resource
outcomes. Existing operation identity, records, artifacts, grants, cancellation
and process continuation remain the foundations.

Preparation must bind the selected endpoint, adapter-added instructions/schemas,
content and relevant configuration. Execution uses that prepared object or
revalidates it before submission. Otherwise a shared library can still measure
one representation and send a different one, reproducing FIX-0049. Neither a
declared endpoint capacity nor a conservative estimate should be represented as
verified exact token usage. Unsupported hard output-limit enforcement must be
explicit rather than hidden behind a reservation number.

Normalize generic outcomes such as input overflow, output cutoff, received-byte
overflow, unverified completion and unknown termination. Attach limit/measurement
units, submission/termination facts, effect references and bounded diagnostics.
The OS does not attach coding repair steps or decide that the whole project
failed. Its host result path must not embed the oversized original prompt.

The OS must not need to understand user objectives, source code, summaries,
coding candidates, task decomposition or a particular response grammar in order
to reject an oversized request or preserve execution certainty. Provider
completion and application semantic completeness are distinct.

## Make common agent design declarative

For the ordinary case an author supplies required input blocks, ordered optional
context groups, a response schema/protocol, allowed bindings/capabilities and
recovery limits. The shared library handles provider-independent packing, complete
group preservation, bounded feedback, linked attempts, replay and default parking.
The same utilities can serve a research or artifact-only agent without Git,
workspaces, tests or coding task records.

Semantic summarization and task splitting are optional application hooks. Authors
need them only when dropping declared optional context or asking for a smaller
complete response cannot solve the problem. The shared library never silently
summarizes mandatory constraints or interprets the business objective.

Persist every chosen replacement intent and continuation through existing OS
records and effects so restarts do not reset adaptation allowance or repeat a
submission. The library's retry policy does not bypass OS authorization, resource
budgets, deadlines or finishing reserves. Direct callers that bypass the library
still receive the same OS bounds and completion/termination safeguards.

## Concrete input-overflow sequence

1. The library constructs context from the author's required and optional groups.
2. OS preparation returns the actual size and effective allowance, without model
   submission. If the complete request fits, execute that prepared request.
3. Otherwise the library removes only permitted whole groups, records omissions,
   and prepares again. Recovery feedback participates in this same packing step.
4. If required context cannot fit, the library invokes the application's host-side
   paging/decomposition hook or returns a bounded blocked result. This step does
   not require a model to ingest the original oversized prompt. If a planning
   model is useful, the application supplies a new fitting control context with
   retained-data references.
5. The OS validates any new request under the original authority and real budgets.
   Binding changes require existing authorization, including inference-location
   restrictions. Only the affected process is parked unless shared effects or
   application policy require a broader stop.

In run 2de3d5c5ab9b, the default packing loop could have removed the two oldest
optional pairs and reached a fitting next request; no semantic summarizer was
needed to address the demonstrated accounting problem. This is a proposed
behavior, not a resumed-run result.

## Concrete truncated-output sequence

1. The OS adapter recognizes a cutoff or unverified completion, retains evidence
   and withholds successful actionable output. A syntactically valid JSON value
   does not override an explicit cutoff signal.
2. With known termination and no prior effects, the library invokes the declared
   protocol's generic smaller-response strategy and creates a linked new request.
   A useful default is at most two adapted attempts, subject to the OS budgets.
3. Every replacement input is re-packed and re-measured. Partial JSON is never
   concatenated into an executable tool call. An explicitly declared chunk
   protocol may advance from a fully accepted unit.
4. With recorded native tool effects, the library uses a registered continuation
   from settled state; it does not blindly restart the native job. Semantic
   reconciliation, when needed, belongs to the agent.
5. With unknown termination, the OS retains ownership/capacity until cancellation
   is confirmed or reconciliation establishes the outcome. No adaptation loop
   can bypass that condition. Exhausted safe adaptation returns a bounded result
   to the agent rather than causing an incidental unhandled exception.

The OS cannot infer that valid-looking content was secretly shortened by an
endpoint that reports success. Adapters must expose their completion/enforcement
capabilities; endpoint deployments must disable silent prompt truncation.
Equivalent safety contracts across local/cloud do not require pretending that
all adapters expose the same token controls.

## Relationship to the other run findings

Generated test-output declarations are coding-agent policy. Generic output and
scratch mechanisms can make correct declarations easier, but the OS must not
automatically grant paths because a command claims they are generated files.
Likewise, the OS can retain opaque process checkpoints, artifacts and deltas;
the coding agent decides how unfinished edits become a replacement's valid Git
baseline. A general agent need not create candidate commits to preserve state.

Provider completion/size faults are OS facts. Malformed application replies,
test exit-status interpretation, final evidence and product acceptance belong
to the library's declared protocol or the individual application. A provider
`completed` status does not establish that Minecraft is playable.

## Validation and limits of this proposal

Use separate conformance suites for OS/adapters, shared library policies and
individual agents. OS tests require no coding concepts; library tests cover
near-limit packing, feedback headroom, complete groups, bounded adaptation,
replay and native effects. Application tests cover semantic requirements and
acceptance. Repeat the generic safety scenarios on both bindings, including an
artifact-only or workspace-none agent and a direct caller without the library.

Cross-read the current boundary guide, public ports and FIX-0049 through FIX-0051
before writing this proposal. Checked documentation structure, links and whitespace
only. No implementation tests, live inference or run resume were performed, and
no implementation or test code was changed.
