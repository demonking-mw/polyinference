"""Validate core design fixtures and cross-document interface consistency.

These checks do not execute a scheduler, copy files or run model/tool backends.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from pydantic import ValidationError

import contracts as core


def require_features(profile: core.CoreProfile, required: list[dict]) -> None:
    available = {(f.feature_id, f.version) for f in profile.supported_features}
    if any((f["feature_id"], f["version"]) not in available for f in required):
        raise ValueError("Unsupported required runtime feature")


def distribution_supported(policy: dict) -> None:
    if any(rule["enforcement"] == "hard" and len(rule["eligible_classes"]) > 1
           and rule["target_weights"] for rule in policy["rules"]):
        raise ValueError("Weighted hard allocation needs a feature outside this core")


def main() -> None:
    folder = Path(__file__).resolve().parent
    raw = json.loads((folder / "core-examples.json").read_text(encoding="utf-8"))
    examples = core.CoreExamples.model_validate_json(json.dumps(raw))
    expected = core.CoreExamples.model_json_schema()
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert json.loads((folder / "core.schema.json").read_text(encoding="utf-8")) == expected

    agent_data = json.loads((folder.parent / "langgraph-agent/examples.json").read_text(encoding="utf-8"))
    core.agent.ContractBundle.model_validate_json(json.dumps(agent_data))
    by_id = {r["record_id"]: r for r in agent_data["records"]}
    require_features(examples.profile, [f for f in by_id["program-1"]["required_runtime_features"]
                                        if f["necessity"] == "required"])
    distribution_supported(by_id["process-spec-worker-1"]["schedule"]["distribution"])
    manifests = {w.manifest_id: w for w in examples.workspaces}
    for report_id in ["report-1", "report-2", "report-3"]:
        report = by_id[report_id]
        request = by_id["publication-request-" + report_id.rsplit("-", 1)[1]]
        require_features(examples.profile, request["required_features"])
        requirement = core.ViewRequirement.model_validate(request["extensions"]["polyinference/workspace-view"])
        manifest = manifests[requirement.manifest_ref]
        assert manifest.workspace_id == requirement.workspace_id
        assert manifest.generation == requirement.generation
        assert manifest.view == requirement.view == "integration"
        assert manifest.effective_code.model_dump(mode="json") == report["final_code"]
        assert manifest.captured_head.model_dump(mode="json") == report["captured_head"]
    assert examples.profile.local_inflight_limit >= 2
    assert examples.profile.max_workers >= 2

    rejected: list[str] = []
    def invalid(label: str, change) -> None:
        candidate = copy.deepcopy(raw)
        change(candidate)
        try:
            core.CoreExamples.model_validate_json(json.dumps(candidate))
        except ValidationError:
            rejected.append(label)
        else:
            raise AssertionError(f"Accepted invalid core data: {label}")

    invalid("local backlog exceeds engine cap", lambda d: d["profile"].update(local_inflight_limit=3))
    invalid("maximum context cannot fit token reservation", lambda d: d["profile"].update(local_reserved_context_tokens=1))
    invalid("global shell cannot have two owners", lambda d: d["profile"].update(shell_capacity=2))
    invalid("verification cannot have two owners", lambda d: d["profile"].update(verification_capacity=2))
    invalid("core shares one model service", lambda d: d["profile"].update(local_model_services=2))
    invalid("framework patch is not the integration contract", lambda d: d["profile"].update(langgraph_integration="patch_pregel"))
    invalid("new effect with wrong generation", lambda d: d["view_requirements"][0].update(generation=1))
    invalid("retired view cannot be used for new dispatch", lambda d: d["view_requirements"][0].update(
        manifest_ref="workspace-1/development/1", generation=1, view="development"))
    invalid("workers cannot share a writable root", lambda d: d["workspaces"][2].update(
        private_root_ref=d["workspaces"][0]["private_root_ref"]))
    invalid("partial tree cannot be final integration", lambda d: d["workspaces"][1].update(materialization="scoped"))
    invalid("integration must capture current predecessor", lambda d: d["workspaces"][1].update(captured_head=None))
    invalid("integration must preserve private delta", lambda d: d["workspaces"][1].update(preserved_delta_ref=None))
    invalid("omission is not deletion", lambda d: d["deltas"][0].update(absence_is_deletion=True))
    invalid("delta cannot write outside assigned paths", lambda d: d["deltas"][0]["changes"][0].update(path="other/file.py"))
    invalid("delta needs original copied hash", lambda d: d["deltas"][0]["changes"][0].update(expected_base_digest="sha256:" + "0" * 64))
    invalid("read closure is not write authority", lambda d: d["workspaces"][0]["copied_files"][1].update(writable=True))
    invalid("integration cannot expand write authority", lambda d: d["workspaces"][1]["allowed_write_paths"].append("src/untouched.py"))
    invalid("integration cannot use another worker's delta", lambda d: d["workspaces"][1].update(preserved_delta_ref="delta-2"))
    invalid("integration must retain a known delta", lambda d: d["workspaces"][1].update(preserved_delta_ref="missing-delta"))
    invalid("integration cannot change task ownership", lambda d: d["workspaces"][1].update(task_spec_ref="task-spec-2"))
    invalid("integration must follow expanded development generation", lambda d: d["workspaces"][0].update(generation=2))
    invalid("delta identity cannot collide", lambda d: d["deltas"][1].update(delta_id="delta-1"))
    invalid("add cannot overwrite a copied base file", lambda d: d["deltas"][0]["changes"][0].update(action="add", expected_base_digest=None))
    invalid("write paths cannot alias by duplication", lambda d: d["workspaces"][0]["allowed_write_paths"].append("src/feature.py"))
    invalid("static map must bind senior", lambda d: d["profile"]["role_backend_refs"].pop("senior"))
    invalid("relative path cannot escape copy", lambda d: d["deltas"][0]["changes"][0].update(path="../other.py"))
    invalid("absolute path cannot escape copy", lambda d: d["deltas"][0]["changes"][0].update(path="C:/other.py"))
    invalid("agent cannot edit Git control files", lambda d: d["workspaces"][0]["allowed_write_paths"].append(".git/config"))

    def rename_delta(d: dict) -> None:
        d["deltas"][0]["changes"][0].update(
            action="rename", source_path="src/feature.py", path="tests/test_feature.py", content=None)

    def double_source(d: dict) -> None:
        rename_delta(d)
        d["deltas"][0]["changes"].append(copy.deepcopy(raw["deltas"][0]["changes"][0]))

    def rename_over_existing(d: dict) -> None:
        rename_delta(d)
        for index in (0, 1):
            d["workspaces"][index]["allowed_write_paths"].append("pyproject.toml")
        d["deltas"][0]["changes"][0]["path"] = "pyproject.toml"

    invalid("rename source cannot also be modified", double_source)
    invalid("rename cannot clobber existing destination", rename_over_existing)

    # Static alternative experiments do not require running-process migration.
    for backend in (examples.profile.local_backend_descriptor_ref, examples.profile.cloud_backend_descriptor_ref):
        alternative = copy.deepcopy(raw)
        alternative["profile"]["role_backend_refs"] = {role: backend for role in ("worker", "senior", "specialist")}
        core.CoreExamples.model_validate_json(json.dumps(alternative))
    # Non-overwriting rename, explicit add and delete remain representable.
    for action in ("rename", "add", "delete"):
        candidate = copy.deepcopy(raw)
        change = candidate["deltas"][0]["changes"][0]
        if action == "rename":
            rename_delta(candidate)
        elif action == "add":
            change.update(action="add", path="tests/test_feature.py", expected_base_digest=None)
        else:
            change.update(action="delete", content=None)
        core.CoreExamples.model_validate_json(json.dumps(candidate))

    def delete_unseen(d: dict) -> None:
        d["workspaces"][0]["allowed_write_paths"].append("src/untouched.py")
        d["deltas"][0]["changes"] = [dict(action="delete", path="src/untouched.py",
                                              expected_base_digest="sha256:" + "0" * 64, content=None)]
    invalid("unseen file needs explicit copied-base preconditions before deletion", delete_unseen)

    for feature in ["runtime/mcp-lifecycle", "runtime/memory-tiers", "runtime/weighted-distribution"]:
        try:
            require_features(examples.profile, [dict(feature_id=feature, version="1")])
        except ValueError:
            rejected.append(feature)
        else:
            raise AssertionError("Core unexpectedly requires a future subsystem")

    try:
        distribution_supported(by_id["process-spec-bounded-example"]["schedule"]["distribution"])
    except ValueError:
        rejected.append("semantic hard-allocation requirement cannot bypass feature negotiation")
    else:
        raise AssertionError("Core silently accepted mandatory weighted allocation")

    # The unrelated fixture file is absent in development and present unchanged
    # in every complete integration view; it never appears in the task delta.
    for delta in examples.deltas:
        development = manifests[delta.development_manifest_ref]
        integration = next(w for w in examples.workspaces
                           if w.workspace_id == delta.workspace_id and w.view == "integration")
        assert "src/untouched.py" not in {f.path for f in development.copied_files}
        assert "src/untouched.py" in {f.path for f in integration.copied_files}
        assert "src/untouched.py" not in {change.path for change in delta.changes}

    print(f"Validated {len(examples.workspaces)} workspace views, {len(examples.deltas)} explicit deltas and the core profile/schema.")
    print(f"Rejected {len(rejected)} invalid or unsupported combinations; matched agent publication/workspace extensions.")
    print("No OS scheduler, copy/merge implementation, LangGraph runtime or inference backend was executed.")


if __name__ == "__main__":
    main()
