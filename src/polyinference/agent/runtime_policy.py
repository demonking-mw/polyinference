"""Coding application policy installed over generic runtime capabilities."""

from __future__ import annotations

from typing import Literal

from ..domain import Check


class CheckSelection(Check):
    purpose: Literal["prerequisite", "task", "acceptance"] = "task"


def purpose_checks(config, records, purpose):
    declared = {"prerequisite": config.prerequisite_checks, "task": config.checks,
                "acceptance": config.checks if config.acceptance_checks is None else config.acceptance_checks}[purpose]
    if declared:
        return declared
    selected = records.get("setup/checks/" + purpose)
    if not selected and purpose == "task":
        legacy = records.get("setup/checks")
        if legacy and legacy[1].get("purpose", "task") == "task":
            selected = legacy  # Legacy discovery never acquires final-acceptance authority.
    return [Check.model_validate(check) for check in selected[1]["checks"]] if selected else []


def configured_checks(config, records):
    checks = {}
    for purpose in ("prerequisite", "task", "acceptance"):
        for check in purpose_checks(config, records, purpose):
            checks[check.name] = check
    return list(checks.values())


class CodingRuntimePolicy:
    def __init__(self, app):
        self.app = app

    async def configure_checks(self, request, arguments):
        app, ports = self.app, self.app.ports
        manifest = ports.workspaces.current(request.payload.workspace_id)
        task = ports.records.get("task/project_setup")
        if (manifest.view != "development" or not task
                or task[1]["workspace_id"] != manifest.workspace_id
                or ports.records.get("setup/completed") or ports.records.scan("plan/")):
            raise ValueError("Check selection requires the initial setup task before planning")
        selected = CheckSelection.model_validate({key: value for key, value in arguments.items() if key != "generation"})
        purpose = selected.purpose
        declared = {"prerequisite": app.config.prerequisite_checks, "task": app.config.checks,
                    "acceptance": app.config.checks if app.config.acceptance_checks is None
                    else app.config.acceptance_checks}[purpose]
        if declared:
            raise ValueError("Cannot replace explicitly configured checks for this purpose")
        check = Check.model_validate(selected.model_dump(exclude={"purpose"}))
        if not check.name.strip() or not check.argv[0].strip() or any("\x00" in arg for arg in check.argv):
            raise ValueError("Supply a check name and nonempty executable arguments")
        source = set(await ports.workspaces.scan_async(ports.workspaces.root_for(manifest)))
        source.update(manifest.allowed_write_paths)
        source.update(ports.workspaces.source_paths)
        if any(path == output or path.startswith(output + "/")
               for output in check.output_paths for path in source):
            raise ValueError("Build output paths overlap existing or granted source files")
        selection = {"workspace_id": manifest.workspace_id, "checks": [check.model_dump(mode="json")],
                     "purpose": purpose}
        key = "setup/checks/" + purpose
        retained = ports.records.get(key)
        if retained and retained[1] != selection:
            raise ValueError("Acceptance checks have already been selected for this run")
        ports.tools.register_check(check)
        ports.records.put_once(key, selection)
        if not ports.records.get("setup/checks"):
            ports.records.put_once("setup/checks", selection)  # Diagnostic compatibility alias for the first choice.
        ports.workspaces.configure_grant(manifest.workspace_id,
                                        check_names=[c.name for c in app.check_definitions])
        return selection

    def publication(self, arguments, process_id, *, require_integration=True):
        app = self.app
        if not app.ports.exclusive.owns(arguments["permit_ref"], "verification/project", process_id):
            raise ValueError("Coding publication requires current verification permit")
        expected, updates = dict(arguments["expected"]), dict(arguments["updates"])
        reports = [v for k, v in arguments["immutable"].items() if k.startswith("report/")]
        candidate = reports[0]["final_code"] if reports else (updates.get("head/provisional") or {}).get("code")
        if "head/provisional" in updates and updates["head/provisional"]["code"] != candidate:
            raise ValueError("Published head must match the reported candidate")
        if app.repository and "head/provisional" in updates and require_integration:
            integrated = app.ports.records.get("coding/integrated/" + arguments["receipt_ref"])
            if not integrated or integrated[1] != {"code": candidate, "process_id": process_id}:
                raise ValueError("Coding publication requires a recorded real-repository integration")
        if candidate:
            head = app.ports.records.get("head/provisional")
            if expected.get("head/provisional") != head[0]:
                raise ValueError("Code publication requires expected shared head")
            minted = [value for _, _, value in app.ports.records.scan("commit-info/")
                      if value["code"] == candidate and value["process_id"] == process_id]
            if not minted or minted[0]["parent"] != head[1]["code"]:
                raise ValueError("Candidate must be a broker commit parented on the current shared head")
        for report in reports:
            if report["process_id"] != process_id:
                raise ValueError("Report belongs to another process")
            if report.get("code_location") == "private" and "head/provisional" in updates:
                raise ValueError("Private failed commit must not advance the shared head")
            if report["verdict"] != "successful":
                version, run = app.ports.records.get("app/run")
                expected["app/run"] = version
                updates["app/run"] = {
                    **run, "starts_closed": True, "completion_proposed": False,
                    "review_reason": "worker_" + report["verdict"],
                    "captured_workers": sorted(set(run["captured_workers"]) | set(run["active_workers"])),
                }
        return {**arguments, "expected": expected, "updates": updates}
