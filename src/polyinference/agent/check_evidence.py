"""Source-bound check selection for diagnosis and private exception review."""

from ..contracts import ArtifactRef, CheckEvidence
from ..primitives import canonical


def matching_checks(app, process_id, code, check_names):
    """Keep latest receipt of each verdict per invocation, including conflicting results."""
    definitions = {c.name: c for c in app.check_definitions if c.name in check_names}
    latest = {}
    for _, _, effect in app.ports.records.scan("effect/"):
        request, result = effect["request"], effect.get("result") or {}
        if (request["scope"].get("process_id") != process_id
                or request["payload"].get("capability_id") != "checks.run"
                or result.get("state") != "succeeded" or not result.get("output_refs")):
            continue
        evidence = CheckEvidence.model_validate(app.read(result["output_refs"][0])).model_dump(mode="json")
        checked = evidence["checked_code"]
        if any(checked[key] != code[key] for key in ("repository_id", "effective_tree_digest", "environment_digest")):
            continue
        definition = definitions.get(evidence["criterion_ref"])
        if definition is None:
            continue
        invocation = app.ports.artifacts.read(ArtifactRef.model_validate(evidence["invocation"]))
        if invocation != canonical(definition):
            continue
        key = (evidence["criterion_ref"], evidence["status"])
        if key not in latest or evidence["completed_at"] > latest[key]["completed_at"]:
            latest[key] = evidence
    return [latest[key] for key in sorted(latest)]


def presented_checks(app, evidence, *, cap=1200):
    return [{**app.evidence_view(item, cap=cap), "evidence_id": item["evidence_id"],
             "invocation_ref": item["invocation"], "completed_at": item["completed_at"]}
            for item in evidence]
