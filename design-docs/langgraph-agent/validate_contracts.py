"""Validate the design examples and important invalid contract combinations.

This checks schemas/selected invariants, not an implemented agent or scheduler.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from pydantic import ValidationError

from contracts import ContractBundle


def publication_links(records: list[dict], protocol: dict) -> None:
    """Example-level checks; a real adapter performs these in its publication path."""
    by_id = {record["record_id"]: record for record in records}
    operations = {record["operation_id"]: record for record in records
                  if record["kind"] == "operation_request"}
    reports = [record for record in records if record["kind"] == "task_report"]
    assert {report["verdict"] for report in reports} == {"successful", "fail", "uncertain"}
    for report in reports:
        receipt = by_id[report["publication_receipt_ref"]]
        request = operations[receipt["publication_operation_id"]]
        publication = request["payload"]
        assert receipt["kind"] == "publication_receipt"
        assert publication["kind"] == "publication"
        assert receipt["report_ref"] == publication["report_ref"] == report["record_id"]
        assert receipt["published_head"] == publication["final_code"] == report["final_code"]
        assert receipt["previous_head"] == publication["expected_head"] == report["captured_head"]
        assert receipt["verification_permit_ref"] == publication["verification_permit_ref"] == report["verification_permit_ref"]
        assert publication["receipt_ref"] == receipt["record_id"]
        assert publication["policy"] == receipt["publication_policy"] == report["publication_policy"] == "provisional_all"
        assert report["resolution"] == "unresolved"
        assert len(report["reconciliation_turn_refs"]) >= protocol["post_merge_development_turns_min"]
        assert len(report["assessment_turn_refs"]) >= protocol["final_assessment_turns_min"]
    # Explicit H -> P1 -> P2(fail) -> P3(uncertain) handoff.
    assert by_id["report-2"]["captured_head"] == by_id["report-1"]["final_code"]
    assert by_id["report-3"]["captured_head"] == by_id["report-2"]["final_code"]


def main() -> None:
    directory = Path(__file__).resolve().parent
    examples = json.loads(directory.joinpath("examples.json").read_text(encoding="utf-8"))
    validated = ContractBundle.model_validate_json(json.dumps(examples))
    actual_schema = json.loads(directory.joinpath("contract.schema.json").read_text(encoding="utf-8"))
    expected_schema = ContractBundle.model_json_schema()
    expected_schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert actual_schema == expected_schema, "Schema export is stale"

    by_id = {record["record_id"]: record for record in examples["records"]}
    assert len(by_id) == len(examples["records"]), "Duplicate example identity"

    manifest = by_id["program-1"]
    basis = manifest["design_basis"]
    source = directory.parent.parent.joinpath(basis["source_path"])
    source_bytes = source.read_bytes()
    assert basis["html_digest"] == "sha256:" + hashlib.sha256(source_bytes).hexdigest(), "Source design changed"
    def graph(path: Path) -> dict:
        html = path.read_text(encoding="utf-8")
        seed = re.search(r'<script[^>]*id="graph-seed"[^>]*>([\s\S]*?)</script>', html)
        assert seed, "Missing embedded graph"
        return json.loads(seed.group(1))
    merged = graph(source)
    assert merged == json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
    assert merged["memoryGraph"] == graph(source.with_name("polyinference-agent-graph.html"))["memoryGraph"]
    assert basis["document_id"] == merged["documentId"]
    assert (basis["execution_node_count"], basis["execution_edge_count"], basis["memory_node_count"], basis["memory_edge_count"]) == (
        len(merged["nodes"]), len(merged["edges"]), len(merged["memoryGraph"]["nodes"]), len(merged["memoryGraph"]["edges"]))
    publication_links(examples["records"], manifest["worker_protocol"])

    rejected: list[str] = []

    def invalid(label: str, record_id: str, change) -> None:
        candidate = copy.deepcopy(by_id[record_id])
        change(candidate)
        try:
            ContractBundle.model_validate_json(json.dumps({"records": [candidate]}))
        except ValidationError:
            rejected.append(label)
        else:
            raise AssertionError(f"Accepted invalid contract: {label}")

    invalid("unknown core field", "process-spec-worker-1",
            lambda r: r.update(arbitrary_authority=True))
    invalid("priority outside contract", "process-spec-worker-1",
            lambda r: r["schedule"]["priority"].update(relative_value=101))
    invalid("allocation weights do not sum to one", "process-spec-flex-example",
            lambda r: r["schedule"]["distribution"]["rules"][0].update(
                target_weights={"local": 0.8, "cloud": 0.8}))
    invalid("flexible allocation cannot secretly be hard", "process-spec-flex-example",
            lambda r: r["schedule"]["distribution"]["rules"][0].update(enforcement="hard"))
    invalid("overlapping allocation rules", "process-spec-worker-1",
            lambda r: r["schedule"]["distribution"]["rules"].append(
                dict(r["schedule"]["distribution"]["rules"][1], rule_id="duplicate-selector")))
    invalid("assessment reserve exceeds allowance", "process-spec-worker-1",
            lambda r: r["limits"].update(max_model_calls=1))

    def break_pair(record: dict) -> None:
        part = record["payload"]["context"]["parts"][0]
        part.update(part_kind="tool_call", call_id="call-without-result")

    invalid("incomplete provider context tool pair", "query-record-1", break_pair)

    def ordered_pair(record: dict) -> None:
        call = copy.deepcopy(record["payload"]["context"]["parts"][0])
        call.update(part_id="part-call", part_kind="tool_call", call_id="call-ordered")
        result = dict(call, part_id="part-result", part_kind="tool_result")
        record["payload"]["context"]["parts"] = [call, result]

    def reversed_pair(record: dict) -> None:
        ordered_pair(record)
        record["payload"]["context"]["parts"].reverse()

    def duplicate_context_part(record: dict) -> None:
        ordered_pair(record)
        record["payload"]["context"]["parts"][1]["part_id"] = "part-call"

    invalid("result cannot precede its tool call", "query-record-1", reversed_pair)
    invalid("context parts cannot alias identities", "query-record-1", duplicate_context_part)
    valid_pair = copy.deepcopy(by_id["query-record-1"])
    ordered_pair(valid_pair)
    ContractBundle.model_validate_json(json.dumps({"records": [valid_pair]}))
    invalid("expired request at creation", "query-record-1",
            lambda r: r.update(deadline="2026-10-17T13:59:00Z"))
    invalid("operation missing process scope", "query-record-1",
            lambda r: r["scope"].update(process_id=None))
    invalid("unknown usage represented as zero", "query-result-1",
            lambda r: r["usage"][0].update(value=0, provenance="unknown"))
    invalid("terminal result with unknown termination", "query-result-1",
            lambda r: r.update(execution_termination="unknown"))
    invalid("terminal result with unknown effects", "query-result-1",
            lambda r: r.update(effects="unknown"))
    invalid("success with failed evidence", "report-1",
            lambda r: r["evidence"][0].update(status="failed", exit_code=1))
    invalid("success with stale environment", "report-1",
            lambda r: r["evidence"][0]["checked_code"].update(
                environment_digest="sha256:" + "0" * 64))
    invalid("private-only normal completion", "report-1",
            lambda r: r.update(code_location="private"))
    invalid("unknown pressure represented as zero", "pressure-1",
            lambda r: r["signals"][0].update(value=0))
    invalid("old wire version cannot silently resume", "report-1",
            lambda r: r.update(contract_version="1.0"))
    invalid("reviewed-only is not the merged program", "run-demo",
            lambda r: r.update(publication_policy="reviewed_only"))
    invalid("missing post-merge development turn", "report-1",
            lambda r: r.update(reconciliation_turn_refs=[]))
    invalid("missing durable publication reference", "report-1",
            lambda r: r.pop("publication_receipt_ref"))
    invalid("undo unit parent is not captured head", "report-1",
            lambda r: r.update(candidate_parent_commit_id="unrelated-commit"))
    invalid("reported final commit differs from candidate", "report-1",
            lambda r: r["final_code"].update(commit_id="another-candidate"))
    invalid("publication omitted verifier ownership", "publication-request-1",
            lambda r: r["payload"].update(permit_refs=[]))
    invalid("receipt has wrong predecessor", "publication-receipt-1",
            lambda r: r.update(candidate_parent_commit_id="unrelated-commit"))
    invalid("private commit did not advance shared head", "publication-receipt-1",
            lambda r: r.update(published_head=copy.deepcopy(r["previous_head"])))
    invalid("completed attempt lacks published assessment report", "attempt-1",
            lambda r: r.update(report_ref=None))
    invalid("published failed code lacks hazard notice", "report-2",
            lambda r: r.update(hazard_refs=[]))
    invalid("uncertain publication lost verification owner", "continuation-1",
            lambda r: r.update(publication_state="uncertain", publication_operation_id="op-publication-1", verification_permit_ref=None))
    invalid("named verification owner missing from retained permits", "continuation-1",
            lambda r: r.update(publication_state="uncertain", publication_operation_id="op-publication-1", verification_permit_ref="permit-verification-1"))
    invalid("run cannot acknowledge unseen steering", "run-demo",
            lambda r: r.update(steering_applied_through=1))
    invalid("completed run cannot leave pending steering", "run-demo",
            lambda r: r.update(outcome="completed", steering_received_through=1))
    invalid("completed run cannot ignore provisional work", "run-demo",
            lambda r: r.update(outcome="completed", provisional_revision=copy.deepcopy(by_id["report-1"]["final_code"])))
    invalid("run heads cannot switch repositories", "run-demo",
            lambda r: r["provisional_revision"].update(repository_id="other-repository"))
    invalid("pending steering cannot reopen worker starts", "steering-barrier-1",
            lambda r: r.update(starts_closed=False))
    invalid("barrier cannot acknowledge unseen input", "steering-barrier-1",
            lambda r: r.update(steering_applied_through=2))
    invalid("planner cannot capture unseen input", "steering-barrier-1",
            lambda r: r.update(planner_input_through=2))
    invalid("planner cannot move behind acknowledged input", "steering-barrier-1",
            lambda r: r.update(steering_applied_through=1, planner_input_through=0))
    invalid("drain set cannot duplicate workers", "steering-barrier-1",
            lambda r: r["captured_worker_process_ids"].append("worker-1"))

    # Shape validation permits an accepted snapshot; runtime still checks live
    # workers/effects, senior authority and complete project-criteria coverage.
    accepted = copy.deepcopy(by_id["run-demo"])
    accepted.update(outcome="completed")
    ContractBundle.model_validate_json(json.dumps({"records": [accepted]}))
    retained_owner = copy.deepcopy(by_id["continuation-1"])
    retained_owner.update(publication_state="uncertain", publication_operation_id="op-publication-1",
                          verification_permit_ref="permit-verification-1", permit_refs=["permit-verification-1"])
    ContractBundle.model_validate_json(json.dumps({"records": [retained_owner]}))

    # A commit of identical content retains test evidence from the pre-commit tree.
    report = by_id["report-1"]
    assert report["final_code"]["commit_id"] != report["evidence"][0]["checked_code"]["commit_id"]
    assert report["final_code"]["effective_tree_digest"] == report["evidence"][0]["checked_code"]["effective_tree_digest"]

    # Unknown execution is retainable, but must remain visibly nonterminal.
    uncertain = copy.deepcopy(by_id["query-result-1"])
    uncertain.update(state="uncertain", execution_termination="unknown", effects="unknown", finished_at=None)
    ContractBundle.model_validate_json(json.dumps({"records": [uncertain]}))

    # Failed/uncertain normal completions are published, unresolved and attributable.
    for record_id in ["report-2", "report-3"]:
        ContractBundle.model_validate_json(json.dumps({"records": [by_id[record_id]]}))

    bad_links = copy.deepcopy(examples["records"])
    next(r for r in bad_links if r["record_id"] == "report-1")["publication_receipt_ref"] = "publication-receipt-2"
    try:
        publication_links(bad_links, manifest["worker_protocol"])
    except AssertionError:
        rejected.append("receipt for a different report cannot establish publication")
    else:
        raise AssertionError("Accepted mismatched publication receipt")

    print(f"Validated {len(validated.records)} illustrative records and current JSON Schema export.")
    print(f"Rejected {len(rejected)} invalid contract combinations; retained identical-tree evidence and explicit uncertainty.")
    print("Matched merged source digest/counts/JSON; verified all three verdicts publish along the receipt/head chain.")
    print("No agent, OS adapter, provider execution or scheduling performance was tested.")


if __name__ == "__main__":
    main()
