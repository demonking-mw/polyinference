# Standalone scheduler for PolyInference

Research and design report · 8 November 2026 · authority corrected 9 November 2026
· **Standalone scheduler proposed**

**V1 authority rule:** the standalone scheduler controls only whether an individual
OS process may run, must wait, or must be preempted from the running set. **The OS
distributes resources.** It selects authorized execution destinations, allocates
capacity, enforces account/quota limits, dispatches operations and establishes safe
resource release. A scheduler admission decision grants no resource entitlement.

This clarification supersedes the earlier draft's operation-level scheduling,
endpoint-selection and resource-claim powers, and the same ambiguity in the first
OS impact audit. Earlier investigation/verification receipts remain historical in
`development-docs/FIXES.md#fix-0180` and `development-docs/FIXES.md#fix-0182`; the correction is
recorded in `development-docs/FIXES.md#fix-0183`. The existing runtime is not changed here.

Implementation preparation: the [9 November OS impact audit](../investigations/2026-11-09-scheduler-os-impact.md)
traces Part 1 against current source and the fix history. Read its physical-attempt,
binding-fence, deferral/resume and provider-ownership requirements before implementing
OS support. It adds no scheduler or runtime behavior and preserves this proposal.

Source baseline: checkout `ae58af5b35f31a722d98a19837f1974a4feb8769`, branch
`fix/status-missing-db`, including the pre-existing uncommitted Haiku preset and
documentation changes. This report develops the supplied scheduler research and
the existing next-iteration proposal (`development-docs/next-iteration.md#quota-aware-task-scheduler`).
Source findings below describe this checkout; proposed interfaces and numeric
policy defaults describe work still to implement. No saved run is migrated.

The 13 November implementation audit in Part 1 identifies the OS mechanisms
already in code and the remaining scheduler integration work.

**Recommendation:** build one replaceable process-admission/preemption service
above the OS. It ranks already-submitted individual processes using importance,
time sensitivity and aging, then issues process eligibility decisions. The OS
independently manages a shared resource broker across all managed runs and all
their operations. Start with cooperative process preemption at safe boundaries.
Only the OS may use an adapter's verified interruption/checkpoint capability.

**Fidelity: future feature.** Version 1 does not optimize fidelity or change model
quality, reasoning effort, execution distribution or harness to improve a score.
PolyInference currently defines fidelity as adherence to a declared execution
distribution, independently of model quality. Existing hard distribution, data,
capability and cloud-only constraints still apply. A future fidelity preference
can be displayed as inactive metadata; an unsupported *required* fidelity policy
must be rejected. See the agent design (`design-docs/langgraph-agent/README.md#7-distribution-and-fidelity`).


- [Proposed OS support for process scheduling](2026-11-08-scheduler-os-support.md)
- [Proposed scheduler process policy](2026-11-08-scheduler-process-policy.md)
