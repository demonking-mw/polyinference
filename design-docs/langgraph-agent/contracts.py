"""Proposed PolyInference wire contracts, not an agent/runtime implementation.

Requires Pydantic 2 to validate examples or export JSON Schema. Cross-record,
authorization, resource-accounting and effect guarantees remain runtime duties.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, JsonValue,
    model_validator,
)


Identifier = Annotated[str, Field(min_length=1, max_length=256)]
Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
Count = Annotated[int, Field(ge=0)]
PositiveCount = Annotated[int, Field(gt=0)]
Fraction = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]


def extension_names(value: dict[str, JsonValue]) -> dict[str, JsonValue]:
    if any("/" not in key for key in value):
        raise ValueError("Extension keys require a namespace/name")
    return value


Extensions = Annotated[dict[str, JsonValue], AfterValidator(extension_names)]


class Wire(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False,
        protected_namespaces=("model_validate", "model_dump"),
    )


class Scope(Wire):
    tenant_id: Identifier
    project_id: Identifier
    run_id: Identifier | None = None
    process_id: Identifier | None = None


class Feature(Wire):
    feature_id: Identifier
    version: Identifier


class Record(Wire):
    contract_version: Literal["1.0"] = "1.0"
    record_id: Identifier
    revision: PositiveCount
    scope: Scope
    created_at: AwareDatetime
    required_features: list[Feature] = Field(default_factory=list)
    extensions: Extensions = Field(default_factory=dict)


class ArtifactRef(Wire):
    artifact_id: Identifier
    digest: Digest
    media_type: Identifier
    size_bytes: Count
    classification: Literal["public", "project", "restricted"]
    scope: Scope


class CodeRevision(Wire):
    repository_id: Identifier
    commit_id: Identifier | None
    effective_tree_digest: Digest
    environment_digest: Digest
    includes_uncommitted_inputs: bool


class PhaseReserve(Wire):
    reconciliation_model_calls: PositiveCount
    assessment_model_calls: PositiveCount
    publication_steps: PositiveCount
    cleanup_steps: PositiveCount


class Limits(Wire):
    max_steps: PositiveCount
    max_model_calls: PositiveCount
    max_repairs: Count
    max_input_tokens_per_call: PositiveCount
    max_output_tokens_per_call: PositiveCount
    max_total_tokens: PositiveCount
    max_output_bytes: PositiveCount
    max_wall_time_ms: PositiveCount
    max_api_spend_microusd: Count
    cost_guarantee: Literal["enforced", "estimate"]
    final_phase_reserve: PhaseReserve | None = None

    @model_validator(mode="after")
    def reserve_fits(self) -> Limits:
        if self.final_phase_reserve:
            reserve = self.final_phase_reserve
            if (reserve.reconciliation_model_calls + reserve.assessment_model_calls
                    > self.max_model_calls):
                raise ValueError("Final model-call reserve exceeds total")
            if reserve.publication_steps + reserve.cleanup_steps > self.max_steps:
                raise ValueError("Final step reserve exceeds total")
        return self


class Priority(Wire):
    priority_class: Literal["interactive", "critical", "normal", "background"]
    relative_value: Annotated[int, Field(ge=0, le=100)]
    aging_allowed: bool
    deadline: AwareDatetime | None


class DistributionRule(Wire):
    rule_id: Identifier
    roles: Annotated[list[Identifier], Field(min_length=1)]
    phases: Annotated[list[Identifier], Field(min_length=1)]
    axis: Literal["inference_location", "harness_class"]
    eligible_classes: Annotated[list[Identifier], Field(min_length=1)]
    target_weights: dict[Identifier, Fraction] = Field(default_factory=dict)
    enforcement: Literal["hard", "soft"]
    unit: Literal["model_decisions", "agent_jobs"]
    accounting_scope: Literal["process", "run", "group"]
    accounting_group_id: Identifier
    window_slots: PositiveCount
    max_total_variation: Fraction
    rounding_slack_slots: Count
    infeasible_action: Literal["wait_until_deadline", "reject"]

    @model_validator(mode="after")
    def weights_and_selectors(self) -> DistributionRule:
        if len(set(self.eligible_classes)) != len(self.eligible_classes):
            raise ValueError("Duplicate eligible class")
        if self.target_weights:
            if set(self.target_weights) != set(self.eligible_classes):
                raise ValueError("Targets must cover exactly the eligible classes")
            if abs(sum(self.target_weights.values()) - 1) > 1e-9:
                raise ValueError("Target weights must sum to one")
        return self


class DistributionPolicy(Wire):
    policy_id: Identifier
    version: PositiveCount
    fidelity: Literal["strict", "bounded", "flexible"]
    rules: Annotated[list[DistributionRule], Field(min_length=1)]
    on_unmatched: Literal["reject"] = "reject"
    max_rebindings: Count
    minimum_residence_ms: Count
    migration_boundaries: list[Literal["before_start", "settled_operation", "new_attempt"]]

    @model_validator(mode="after")
    def fidelity_and_overlap(self) -> DistributionPolicy:
        if self.fidelity == "flexible" and any(r.enforcement != "soft" for r in self.rules):
            raise ValueError("Flexible allocation rules must be soft")
        if self.fidelity == "strict" and any(r.enforcement != "hard" for r in self.rules):
            raise ValueError("Strict allocation rules must be hard")
        ids = [r.rule_id for r in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("Rule IDs must be unique")
        for index, left in enumerate(self.rules):
            for right in self.rules[index + 1:]:
                roles_overlap = "*" in left.roles + right.roles or bool(set(left.roles) & set(right.roles))
                phases_overlap = "*" in left.phases + right.phases or bool(set(left.phases) & set(right.phases))
                if left.axis == right.axis and roles_overlap and phases_overlap:
                    raise ValueError("Same-axis rules must match uniquely")
        return self


class DataPolicy(Wire):
    policy_ref: Identifier
    allowed_inference_locations: Annotated[list[Identifier], Field(min_length=1)]
    allowed_destination_classes: Annotated[list[Identifier], Field(min_length=1)]
    maximum_classification: Literal["public", "project", "restricted"]


class Requirement(Wire):
    feature_id: Identifier
    version: Identifier
    necessity: Literal["required", "preferred"]


class ResourceQuantity(Wire):
    resource_id: Identifier
    domain_id: Identifier
    unit: Identifier
    amount: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    guarantee: Literal["estimate", "enforced"]
    lifetime: Literal["operation", "session", "process", "service"]


class Prerequisite(Wire):
    record_ref: Identifier
    required_state: Literal["settled", "completed", "kept", "reviewed", "available"]
    expected_revision: PositiveCount | None = None


class ScheduleContract(Wire):
    priority: Priority
    distribution: DistributionPolicy
    data_policy: DataPolicy
    capability_floor_ref: Identifier | None = None
    requirements: list[Requirement]
    prerequisites: list[Prerequisite]
    resource_hints: list[ResourceQuantity]
    conflict_keys: list[Identifier]
    locality_refs: list[Identifier]


class ProgramRef(Wire):
    program_id: Identifier
    program_version: Identifier
    graph_digest: Digest
    state_schema_version: Identifier
    prompt_bundle_digest: Digest


class AgentProgram(Record):
    kind: Literal["agent_program"] = "agent_program"
    program: ProgramRef
    entry_points: Annotated[list[Identifier], Field(min_length=1)]
    required_runtime_features: list[Requirement]
    optional_runtime_features: list[Requirement]
    migration_registry_ref: Identifier | None


class ProjectRun(Record):
    kind: Literal["project_run"] = "project_run"
    program: ProgramRef
    objective: ArtifactRef
    acceptance_spec: ArtifactRef
    catalog_ref: Identifier
    budget_account_ref: Identifier
    grant_ref: Identifier
    limits: Limits
    publication_policy: Literal["reviewed_only", "provisional_all"]
    reviewed_revision: CodeRevision
    provisional_revision: CodeRevision | None
    plan_ref: Identifier | None
    steering_received_through: Count
    steering_applied_through: Count
    outcome: Literal["active", "paused", "completed", "failed", "cancelled", "budget_stopped"]


class ProcessSpec(Record):
    kind: Literal["process_spec"] = "process_spec"
    process_id: Identifier
    parent_process_id: Identifier | None
    program: ProgramRef
    entry_point: Identifier
    role: Identifier
    input_refs: Annotated[list[ArtifactRef], Field(min_length=1)]
    task_spec_ref: Identifier | None
    attempt_id: Identifier | None
    workspace_id: Identifier | None
    grant_ref: Identifier
    budget_account_ref: Identifier
    limits: Limits
    schedule: ScheduleContract
    output_schema_ref: Identifier
    resume_strategy: Literal["portable_context", "native_session", "new_attempt"]


class WaitReason(Wire):
    wait_kind: Literal["operation", "dependency", "resource", "steering_drain", "human", "reconciliation"]
    target_refs: list[Identifier]
    holder_refs: list[Identifier]
    since: AwareDatetime
    deadline: AwareDatetime | None
    diagnostic_ref: Identifier | None


class ProcessStatus(Record):
    kind: Literal["process_status"] = "process_status"
    process_spec_ref: Identifier
    state: Literal["created", "ready", "running", "waiting", "paused", "completed", "failed", "cancelled"]
    phase: Identifier
    owner_generation: PositiveCount
    binding_generation: Count
    binding_ref: Identifier | None
    wait: WaitReason | None
    pending_operations: list[Identifier]
    reservation_refs: list[Identifier]
    permit_refs: list[Identifier]
    continuation_ref: Identifier | None
    terminal_result_ref: Identifier | None
    cancellation_requested: bool
    cleanup_state: Literal["none", "pending", "complete", "uncertain"] = "none"
    last_progress_at: AwareDatetime | None = None


class TaskSpec(Record):
    kind: Literal["task_spec"] = "task_spec"
    task_id: Identifier
    plan_ref: Identifier
    objective: ArtifactRef
    allowed_change_scope: Annotated[list[Identifier], Field(min_length=1)]
    prerequisites: list[Prerequisite]
    base: CodeRevision
    acceptance_spec: ArtifactRef
    context_refs: list[ArtifactRef]
    memory_snapshot_refs: list[Identifier]
    allowed_capabilities: list[Identifier]
    worker_process_spec_ref: Identifier
    report_schema_ref: Identifier


class ContextPart(Wire):
    part_id: Identifier
    content: ArtifactRef
    part_kind: Literal["instruction", "data", "message", "tool_call", "tool_result", "summary"]
    trust: Literal["user", "application", "model", "external_tool", "retrieved"]
    source_ref: Identifier
    required: bool
    call_id: Identifier | None = None
    derived_from: list[Identifier] = Field(default_factory=list)


class ContextView(Wire):
    view_id: Identifier
    digest: Digest
    parts: list[ContextPart]
    memory_snapshot_refs: list[Identifier]
    tool_catalog_digest: Digest
    maximum_input_tokens: PositiveCount
    omitted_refs: list[Identifier]

    @model_validator(mode="after")
    def complete_tool_pairs(self) -> ContextView:
        calls: list[str] = []
        results: list[str] = []
        for part in self.parts:
            if part.part_kind in {"tool_call", "tool_result"}:
                if part.call_id is None:
                    raise ValueError("Tool context parts need a call ID")
                (calls if part.part_kind == "tool_call" else results).append(part.call_id)
        if sorted(calls) != sorted(results) or len(calls) != len(set(calls)):
            raise ValueError("Context requires one complete pair per tool call")
        return self


class ModelQuery(Wire):
    kind: Literal["model_query"] = "model_query"
    role: Identifier
    phase: Identifier
    prompt_template_ref: Identifier
    context: ContextView
    response_schema_ref: Identifier
    capability_requirements: list[Requirement]
    temperature: Annotated[float, Field(ge=0, le=2)]
    session_ref: Identifier | None


class AgentJob(Wire):
    kind: Literal["agent_job"] = "agent_job"
    role: Identifier
    objective: ArtifactRef
    context: ContextView
    workspace_id: Identifier
    allowed_capabilities: list[Identifier]
    required_phase_protocol: Identifier
    required_guarantees: list[Requirement]
    response_schema_ref: Identifier
    session_ref: Identifier | None


class CapabilityCall(Wire):
    kind: Literal["capability_call"] = "capability_call"
    capability_id: Identifier
    schema_digest: Digest
    arguments: ArtifactRef
    model_call_id: Identifier | None
    workspace_id: Identifier | None
    expected_code: CodeRevision | None
    effect_class: Literal["read", "private_write", "shared_write", "external_write"]
    reconciliation_strategy_ref: Identifier | None


class MemoryQuery(Wire):
    kind: Literal["memory_query"] = "memory_query"
    query: ArtifactRef
    namespace_refs: list[Identifier]
    semantic_kinds: list[Identifier]
    snapshot_ref: Identifier | None
    maximum_age_ms: Count | None
    applicable_code: CodeRevision | None
    required_item_refs: list[Identifier]
    permitted_tiers: list[Identifier]
    max_items: PositiveCount
    max_bytes: PositiveCount
    max_tokens: PositiveCount


class ExpectedVersion(Wire):
    record_ref: Identifier
    revision: PositiveCount


class Publication(Wire):
    kind: Literal["publication"] = "publication"
    expected_versions: Annotated[list[ExpectedVersion], Field(min_length=1)]
    expected_head: CodeRevision
    candidate_commit_id: Identifier
    report_ref: Identifier
    evidence_refs: list[Identifier]
    policy: Literal["reviewed_only", "provisional_all"]
    permit_refs: Annotated[list[Identifier], Field(min_length=1)]
    event_intent_refs: list[Identifier]


Payload = Annotated[
    ModelQuery | AgentJob | CapabilityCall | MemoryQuery | Publication,
    Field(discriminator="kind"),
]


class OperationRequest(Record):
    kind: Literal["operation_request"] = "operation_request"
    operation_id: Identifier
    logical_step_id: Identifier
    intent_digest: Digest
    causal_parent_ref: Identifier | None
    trace_id: Identifier
    grant_ref: Identifier
    owner_generation: PositiveCount
    expected_process_revision: PositiveCount
    expected_binding_generation: Count
    schedule_ref: Identifier
    priority_hint: Priority | None = None
    budget_account_ref: Identifier
    deadline: AwareDatetime
    limits: Limits
    resources: list[ResourceQuantity]
    conflict_keys: list[Identifier]
    safe_boundary: Literal["before_start", "settled_operation", "protected_phase"]
    replay_policy: Literal["deduplicated", "reconcile_before_retry", "never_automatic"]
    payload: Payload

    @model_validator(mode="after")
    def valid_deadline(self) -> OperationRequest:
        if self.deadline <= self.created_at:
            raise ValueError("Deadline must follow request creation")
        if self.scope.process_id is None or self.scope.run_id is None:
            raise ValueError("Operation needs authenticated run/process scope")
        return self


class UsageMeasure(Wire):
    metric: Identifier
    unit: Identifier
    value: Annotated[float, Field(ge=0)] | None
    provenance: Literal["measured", "provider_reported", "estimated", "unknown"]
    account_scope_ref: Identifier

    @model_validator(mode="after")
    def unknown_is_not_zero(self) -> UsageMeasure:
        if (self.value is None) != (self.provenance == "unknown"):
            raise ValueError("Unknown usage must have null value, and only unknown may")
        return self


class ActualBackend(Wire):
    catalog_ref: Identifier
    backend_id: Identifier
    model_version: Identifier
    harness_version: Identifier
    inference_location: Identifier
    harness_location: Identifier
    provider_session_ref: Identifier | None


class ErrorDetail(Wire):
    code: Identifier
    message: Annotated[str, Field(max_length=4000)]
    retryable_after_reconciliation: bool
    retry_after_ms: Count | None


class OperationResult(Record):
    kind: Literal["operation_result"] = "operation_result"
    operation_id: Identifier
    logical_step_id: Identifier
    state: Literal["prepared", "submitting", "active", "uncertain", "succeeded", "failed", "cancelled", "denied"]
    output_refs: list[ArtifactRef]
    paired_call_id: Identifier | None
    binding_ref: Identifier | None
    binding_generation: Count
    actual_backend: ActualBackend | None
    usage: list[UsageMeasure]
    execution_termination: Literal["not_started", "active", "confirmed_stopped", "unknown"]
    effects: Literal["none", "known", "unknown"]
    started_at: AwareDatetime | None
    finished_at: AwareDatetime | None
    error: ErrorDetail | None
    continuation_ref: Identifier | None

    @model_validator(mode="after")
    def terminal_certainty(self) -> OperationResult:
        terminal = self.state in {"succeeded", "failed", "cancelled", "denied"}
        if terminal and self.execution_termination not in {"not_started", "confirmed_stopped"}:
            raise ValueError("Active/unknown termination cannot be a terminal operation")
        if terminal and self.effects == "unknown":
            raise ValueError("Unknown effects require reconciliation")
        if self.state == "succeeded" and self.error is not None:
            raise ValueError("Success cannot carry an error")
        return self


class BindingDecision(Record):
    kind: Literal["binding_decision"] = "binding_decision"
    process_id: Identifier
    operation_id: Identifier
    generation: PositiveCount
    policy_id: Identifier
    policy_version: PositiveCount
    rule_ids: Annotated[list[Identifier], Field(min_length=1)]
    selected_backend_classes: dict[Identifier, Identifier]
    actual_backend: ActualBackend
    reason: Literal["default", "pressure", "deadline", "availability", "manual", "capability_fit"]
    distribution_before: dict[Identifier, Count]
    distribution_after: dict[Identifier, Count]
    total_variation_by_rule: dict[Identifier, Fraction]
    pressure_snapshot_ref: Identifier | None
    capability_evaluation_ref: Identifier | None = None
    safe_point_ref: Identifier
    rebuild_context: bool


class CheckEvidence(Wire):
    evidence_id: Identifier
    criterion_ref: Identifier
    checked_code: CodeRevision
    status: Literal["passed", "failed", "unavailable", "inconclusive"]
    exit_code: int | None
    invocation: ArtifactRef
    output: ArtifactRef
    completed_at: AwareDatetime


class TaskReport(Record):
    kind: Literal["task_report"] = "task_report"
    task_spec_ref: Identifier
    attempt_id: Identifier
    process_id: Identifier
    plan_ref: Identifier
    execution: Literal["completed"] = "completed"
    resolution: Literal["unresolved"] = "unresolved"
    verdict: Literal["fail", "uncertain", "successful"]
    stop_reason: Identifier | None
    assessment_turn_refs: Annotated[list[Identifier], Field(min_length=1)]
    assessment_summary: ArtifactRef
    original_base: CodeRevision
    captured_head: CodeRevision
    final_code: CodeRevision
    candidate_commit_id: Identifier
    preserved_private_delta_ref: Identifier
    publication_policy: Literal["reviewed_only", "provisional_all"]
    code_location: Literal["private", "provisional"]
    evidence: list[CheckEvidence]
    hazard_refs: list[Identifier]
    usage: list[UsageMeasure]

    @model_validator(mode="after")
    def evidence_and_policy(self) -> TaskReport:
        if self.publication_policy == "reviewed_only" and self.code_location != "private":
            raise ValueError("Reviewed-only completion retains a private candidate")
        if self.publication_policy == "provisional_all" and self.code_location != "provisional":
            raise ValueError("Provisional-all completion must publish provisional code")
        if self.verdict == "successful":
            if not self.evidence or any(e.status != "passed" for e in self.evidence):
                raise ValueError("Success needs passed evidence")
            def content_identity(code: CodeRevision) -> tuple[str, str, str]:
                return (code.repository_id, code.effective_tree_digest, code.environment_digest)
            if any(content_identity(e.checked_code) != content_identity(self.final_code)
                   for e in self.evidence):
                raise ValueError("Success evidence must describe the final code/environment")
        return self


class ReviewResolution(Record):
    kind: Literal["review_resolution"] = "review_resolution"
    report_ref: Identifier
    senior_query_ref: Identifier
    action: Literal["keep", "revert", "retry", "defer"]
    reason: ArtifactRef
    reviewed_resulting_code: CodeRevision | None
    revert_commit_id: Identifier | None
    followup_task_refs: list[Identifier]
    evidence_refs: list[Identifier]


class MemoryItem(Record):
    kind: Literal["memory_item"] = "memory_item"
    memory_id: Identifier
    semantic_kind: Literal["objective", "user_instruction", "steering", "working_summary", "episode", "project_fact", "hazard", "procedure", "documentation"]
    content: ArtifactRef
    author_ref: Identifier
    trust: Literal["user", "application", "model", "external_tool", "retrieved"]
    provenance_refs: list[Identifier]
    applicable_code: CodeRevision | None
    valid_until: AwareDatetime | None
    supersedes_ref: Identifier | None
    tombstone: bool
    access_policy_ref: Identifier
    retention_policy_ref: Identifier
    tier_preference: Identifier
    pinned_by_refs: list[Identifier]
    hazard_code_location: Literal["private", "provisional", "reviewed", "reverted"] | None = None


class Continuation(Record):
    kind: Literal["continuation"] = "continuation"
    process_spec_ref: Identifier
    program: ProgramRef
    thread_id: Identifier
    checkpoint_namespace: str
    checkpoint_id: Identifier
    owner_generation: PositiveCount
    binding_generation: Count
    logical_step_id: Identifier
    phase: Identifier
    pinned_record_versions: list[ExpectedVersion]
    workspace_id: Identifier | None
    code: CodeRevision | None
    trajectory_ref: Identifier
    context_view_ref: Identifier
    pending_operations: list[Identifier]
    permit_refs: list[Identifier]
    reservation_refs: list[Identifier]
    budget_ledger_ref: Identifier
    memory_snapshot_refs: list[Identifier]
    event_cursor: Count
    pause_reason: Identifier


class SprintPlan(Record):
    kind: Literal["sprint_plan"] = "sprint_plan"
    parent_plan_ref: Identifier | None
    senior_query_ref: Identifier
    goal: ArtifactRef
    task_spec_refs: list[Identifier]
    resolution_refs: list[Identifier]
    input_report_refs: list[Identifier]
    steering_from: Count
    steering_through: Count
    expected_head: CodeRevision


class TaskAttempt(Record):
    kind: Literal["task_attempt"] = "task_attempt"
    task_spec_ref: Identifier
    process_spec_ref: Identifier
    workspace_id: Identifier
    original_base: CodeRevision
    previous_attempt_ref: Identifier | None
    execution: Literal["pending", "in_progress", "completed", "interrupted", "cancelled"]
    report_ref: Identifier | None
    stop_reason: Identifier | None


class CapabilityDescriptor(Record):
    kind: Literal["capability_descriptor"] = "capability_descriptor"
    capability_id: Identifier
    capability_version: Identifier
    transport_class: Literal["direct", "mcp", "other"]
    input_schema_digest: Digest
    output_schema_digest: Digest
    effect_class: Literal["read", "private_write", "shared_write", "external_write"]
    conflict_key_template_refs: list[Identifier]
    resource_hints: list[ResourceQuantity]
    access_policy_ref: Identifier
    replay_guarantee: Literal["deduplicated", "read_repeatable", "reconcile", "none"]
    cancellation_guarantee: Literal["confirmed", "request_only", "unsupported"]
    server_class_ref: Identifier | None
    negotiated_protocol_version: Identifier | None
    negotiated_features: list[Feature]


class BackendDescriptor(Record):
    kind: Literal["backend_descriptor"] = "backend_descriptor"
    backend_id: Identifier
    backend_classes: list[Identifier]
    execution_kind: Literal["model_query", "agent_job"]
    inference_location: Identifier
    harness_location: Identifier
    model_version: Identifier
    harness_version: Identifier
    max_context_tokens: PositiveCount
    max_output_tokens: PositiveCount
    requirements_satisfied: list[Requirement]
    account_scope_ref: Identifier
    tool_brokerage: Literal["host_brokered", "equivalent_verified", "opaque", "none"]
    enforced_limit_names: list[Identifier]
    observed_usage_metrics: list[Identifier]
    cancellation_guarantee: Literal["confirmed", "request_only", "unsupported"]
    reconciliation_strategy_ref: Identifier | None
    resume_modes: list[Literal["portable_context", "native_session", "new_attempt"]]
    migration_compatibility_ref: Identifier | None
    mutable_session_concurrency: PositiveCount


class PressureSignal(Wire):
    metric: Identifier
    domain_ref: Identifier
    value: Annotated[float, Field(ge=0)] | None
    unit: Identifier
    observation: Literal["measured", "provider_reported", "estimated", "unknown"]
    retry_at: AwareDatetime | None

    @model_validator(mode="after")
    def unknown_value(self) -> PressureSignal:
        if (self.value is None) != (self.observation == "unknown"):
            raise ValueError("Unknown pressure must have null value")
        return self


class PressureSnapshot(Record):
    kind: Literal["pressure_snapshot"] = "pressure_snapshot"
    source_ref: Identifier
    observed_at: AwareDatetime
    stale_after_ms: PositiveCount
    signals: list[PressureSignal]
    reservation_snapshot_ref: Identifier


class RetrievedItem(Wire):
    item_ref: Identifier
    item_revision: PositiveCount
    score: Annotated[float, Field(allow_inf_nan=False)] | None
    reason: Annotated[str, Field(max_length=1000)]


class MemorySnapshot(Record):
    kind: Literal["memory_snapshot"] = "memory_snapshot"
    query_operation_ref: Identifier
    index_version_ref: Identifier | None
    items: list[RetrievedItem]
    omitted_refs: list[Identifier]
    missing_required_refs: list[Identifier]
    truncated: bool
    content_bytes: Count
    estimated_tokens: Count


class SteeringBarrier(Record):
    kind: Literal["steering_barrier"] = "steering_barrier"
    starts_closed: bool
    steering_received_through: Count
    steering_applied_through: Count
    captured_worker_process_ids: list[Identifier]
    captured_plan_ref: Identifier
    planner_input_through: Count | None


class DocumentationBatch(Record):
    kind: Literal["documentation_batch"] = "documentation_batch"
    from_cursor_exclusive: Count
    through_cursor_inclusive: Count
    input_event_refs: list[Identifier]
    captured_code: CodeRevision
    previous_doc_ref: Identifier
    update_task_ref: Identifier | None
    state: Literal["pending", "active", "published", "failed"]
    published_doc_ref: Identifier | None


ContractRecord = Annotated[
    AgentProgram | ProjectRun | ProcessSpec | ProcessStatus | TaskSpec
    | OperationRequest | OperationResult | BindingDecision | TaskReport
    | ReviewResolution | MemoryItem | Continuation | SprintPlan | TaskAttempt
    | CapabilityDescriptor | BackendDescriptor | PressureSnapshot | MemorySnapshot
    | SteeringBarrier | DocumentationBatch,
    # More application/service records use the same versioned reference boundary.
    Field(discriminator="kind"),
]


class ContractBundle(Wire):
    contract_version: Literal["1.0"] = "1.0"
    records: list[ContractRecord]


if __name__ == "__main__":
    # Explicit invocation only: export the proposed wire shape beside this file.
    destination = Path(__file__).with_name("contract.schema.json")
    schema = ContractBundle.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    destination.write_text(
        json.dumps(schema, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported {destination.name}")
