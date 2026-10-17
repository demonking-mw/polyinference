"""Validate the design examples and important invalid contract combinations.

This checks schemas/selected invariants, not an implemented agent or scheduler.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from pydantic import ValidationError

from contracts import ContractBundle


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
    invalid("private policy with provisional code", "report-1",
            lambda r: r.update(code_location="provisional"))
    invalid("unknown pressure represented as zero", "pressure-1",
            lambda r: r["signals"][0].update(value=0))

    # A commit of identical content retains test evidence from the pre-commit tree.
    report = by_id["report-1"]
    assert report["final_code"]["commit_id"] != report["evidence"][0]["checked_code"]["commit_id"]
    assert report["final_code"]["effective_tree_digest"] == report["evidence"][0]["checked_code"]["effective_tree_digest"]

    # Unknown execution is retainable, but must remain visibly nonterminal.
    uncertain = copy.deepcopy(by_id["query-result-1"])
    uncertain.update(state="uncertain", execution_termination="unknown", effects="unknown", finished_at=None)
    ContractBundle.model_validate_json(json.dumps({"records": [uncertain]}))

    # Explicit provisional-all is supported independently of task success.
    provisional = copy.deepcopy(report)
    provisional.update(publication_policy="provisional_all", code_location="provisional", verdict="uncertain")
    ContractBundle.model_validate_json(json.dumps({"records": [provisional]}))

    print(f"Validated {len(validated.records)} illustrative records and current JSON Schema export.")
    print(f"Rejected {len(rejected)} invalid contract combinations; accepted 3 intended edge cases.")
    print("No agent, OS adapter, provider execution or scheduling performance was tested.")


if __name__ == "__main__":
    main()
