"""Application bootstrap for an explicit, bounded, artifact-only endpoint warm-up."""
from datetime import timedelta
from pathlib import Path

from ..contracts import ContextPart, ContextView, ModelQuery, OperationRequest, ProcessSpec
from ..primitives import digest, now, operation_fingerprint
from ..runtime.kernel import KernelRuntime


async def probe_endpoint(config, state_directory):
    """Use ordinary OS accounting, with no coding services, tools or workspaces."""
    endpoint = config.local
    if endpoint.protocol not in {"chat", "responses", "anthropic", "gemini"}:
        raise ValueError("Endpoint testing requires a raw generation endpoint on the local lane")
    seconds = endpoint.lifecycle.total_seconds if endpoint.lifecycle else endpoint.timeout_seconds
    limits = config.limits.model_copy(update={"max_steps": 1, "max_model_calls": 1, "max_repairs": 0,
        "max_input_tokens_per_call": 1024, "max_output_tokens_per_call": 64,
        "max_total_tokens": 4096, "max_output_bytes": 4096, "max_wall_time_ms": int(seconds * 1000),
        "final_phase_reserve": None})
    settings = config.system.model_copy(update={"repository": str(Path(state_directory) / "unused"),
        "state_directory": str(state_directory), "local": endpoint, "cloud": endpoint,
        "role_bindings": {"probe": "local"}, "limits": limits, "prepare_repository": False,
        "checks": [], "allowed_write_paths": [], "closure_paths": [], "control_token_reserve": 0,
        "run_token_budget": 4096, "model_call_retries": 0, "max_model_recoveries": 0})
    Path(state_directory).parent.mkdir(parents=True, exist_ok=True)
    (Path(state_directory).parent / "config.json").write_text(settings.model_dump_json(indent=2))
    rt = await KernelRuntime(settings).open()
    try:
        scope = rt.scope.model_copy(update={"process_id": "probe"})
        prompt = rt.artifacts.put(b"Reply with the single word ready.", scope, "text/plain")
        spec = ProcessSpec(record_id="process-spec/probe", revision=1, scope=scope, created_at=now(),
            process_id="probe", parent_process_id=None,
            program={"program_id": "endpoint-probe", "program_version": "1", "graph_digest": digest(b"probe/1"),
                     "state_schema_version": "1", "prompt_bundle_digest": digest(b"ready/1")},
            entry_point="probe", role="probe", input_refs=[prompt], task_spec_ref=None, attempt_id=None,
            workspace_id=None, grant_ref="grant/run", budget_account_ref="budget/run", limits=limits,
            schedule={"priority": {"priority_class": "interactive", "relative_value": 50,
                        "aging_allowed": False, "deadline": None},
                "distribution": {"policy_id": "probe/1", "version": 1, "fidelity": "strict",
                    "rules": [{"rule_id": "probe", "roles": ["probe"], "phases": ["*"],
                        "axis": "inference_location", "eligible_classes": [endpoint.physical_location],
                        "target_weights": {endpoint.physical_location: 1.0}, "enforcement": "hard",
                        "unit": "model_decisions", "accounting_scope": "process", "accounting_group_id": "probe",
                        "window_slots": 1, "max_total_variation": 0, "rounding_slack_slots": 0,
                        "infeasible_action": "reject"}], "max_rebindings": 0, "minimum_residence_ms": 0,
                    "migration_boundaries": ["before_start"]},
                "data_policy": {"policy_ref": "probe/1", "allowed_inference_locations": [endpoint.physical_location],
                    "allowed_destination_classes": ["local", "cloud"], "maximum_classification": "project"},
                "requirements": [], "prerequisites": [], "resource_hints": [], "conflict_keys": [], "locality_refs": []},
            output_schema_ref="text/plain", resume_strategy="portable_context")
        rt.processes.register(spec, "local")
        context = ContextView(view_id="probe", digest=prompt.digest,
            parts=[ContextPart(part_id="prompt", content=prompt, part_kind="data", trust="user",
                               source_ref="probe", required=True)], memory_snapshot_refs=[],
            tool_catalog_digest=digest(b"none"), maximum_input_tokens=1024, omitted_refs=[])
        payload = ModelQuery(role="probe", phase="probe", prompt_template_ref="probe/1", context=context,
            response_schema_ref="text/plain", capability_requirements=[], temperature=0, session_ref=None)
        request = OperationRequest(record_id="request/probe", revision=1, scope=scope, created_at=now(),
            operation_id="probe", logical_step_id="probe", intent_digest=digest(b"pending"),
            causal_parent_ref=None, trace_id=rt.run_id, grant_ref="grant/run", owner_generation=1,
            expected_process_revision=1, expected_binding_generation=1, schedule_ref="probe/1",
            budget_account_ref="budget/run", deadline=spec.created_at + timedelta(seconds=seconds), limits=limits,
            resources=[], conflict_keys=[], safe_boundary="settled_operation", replay_policy="reconcile_before_retry",
            payload=payload)
        request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
        result = await rt.execute(request)
        rt.processes.finish("probe", state="completed" if result.state == "succeeded" else "failed")
        return {"status": result.state, "operation_id": result.operation_id,
                "error": result.error.message if result.error else None,
                "usage": [measure.model_dump(mode="json") for measure in result.usage]}
    finally:
        await rt.close()
