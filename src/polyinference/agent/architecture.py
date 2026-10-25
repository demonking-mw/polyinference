"""Agent-owned module contracts and pending-plan validation; no runtime policy."""

from __future__ import annotations

from ..domain import Assignment, InterfaceContract


def catalog(app):
    return {
        contract.reference: contract
        for _, _, value in app.ports.records.scan("interface-contract/")
        for contract in [InterfaceContract.model_validate(value)]
    }


def validate_plan(proposal, tasks, contracts):
    """Validate the resulting plan before any disposition or publication side effect."""
    merged = dict(contracts)
    latest = {}
    for contract in contracts.values():
        latest[contract.interface_id] = max(latest.get(contract.interface_id, 0), contract.version)
    revised = set()
    for contract in sorted(proposal.interface_contracts, key=lambda c: (c.interface_id, c.version)):
        existing = merged.get(contract.reference)
        if existing is not None:
            if existing != contract:
                raise ValueError(f"Interface {contract.reference} is immutable; introduce a new version")
            continue
        previous = latest.get(contract.interface_id, 0)
        if contract.version != previous + 1:
            raise ValueError(f"Interface {contract.interface_id} needs version {previous + 1}")
        if previous:
            revised.add(contract.interface_id)
        latest[contract.interface_id] = contract.version
        merged[contract.reference] = contract

    existing = {t["assignment"]["task_id"]: t for t in tasks}
    cancelled = set(proposal.cancel_pending_task_ids)
    for task_id in cancelled:
        if task_id not in existing or existing[task_id]["execution"] != "pending":
            raise ValueError("Only an existing unstarted task may be cancelled")
    if any(t.task_id in existing for t in proposal.tasks):
        raise ValueError("New tasks need new IDs; retry must be a linked new assignment")

    retained = {k: t for k, t in existing.items() if k not in cancelled and t["execution"] != "cancelled"}
    assignments = {k: Assignment.model_validate(t["assignment"]) for k, t in retained.items()}
    assignments.update({t.task_id: t for t in proposal.tasks})
    retained_pending = {k for k, t in retained.items() if t["execution"] == "pending"}
    pending = retained_pending | {t.task_id for t in proposal.tasks}
    unfinished = pending | {k for k, t in retained.items() if t["execution"] == "in_progress"}
    for task_id in pending:
        assignment = assignments[task_id]
        if not set(assignment.dependencies) <= assignments.keys():
            raise ValueError(f"Task {task_id} has an unknown or cancelled dependency")
        for ref in [*assignment.provides, *assignment.consumes]:
            if ref not in merged:
                raise ValueError(f"Task {task_id} references unknown interface {ref}")
            contract = merged[ref]
            if (
                task_id in retained_pending
                and contract.interface_id in revised
                and contract.version != latest[contract.interface_id]
            ):
                raise ValueError(f"Replace pending task {task_id} to use the revised interface contract")

    visiting, ancestors = set(), {}

    def dependencies(task_id):
        if task_id in visiting:
            raise ValueError("Task dependency cycle in resulting plan")
        if task_id not in ancestors:
            visiting.add(task_id)
            result = set()
            for dep in assignments[task_id].dependencies:
                if dep in assignments:
                    result.update({dep} | dependencies(dep))
            visiting.remove(task_id)
            ancestors[task_id] = result
        return ancestors[task_id]

    for task_id in pending:
        assignment = assignments[task_id]
        upstream = dependencies(task_id)
        for ref in assignment.consumes:
            providers = {k for k in unfinished if k != task_id and ref in assignments[k].provides}
            if not providers <= upstream:
                raise ValueError(f"Task {task_id} must depend on unfinished provider(s) of {ref}")
    return merged


def task_context(app, assignment, contracts):
    refs = list(dict.fromkeys([*assignment.provides, *assignment.consumes]))
    if not (refs or assignment.acceptance_criteria or assignment.non_goals):
        return []
    return [
        app.artifact(
            {
                "module_assignment": {
                    "acceptance_criteria": assignment.acceptance_criteria,
                    "non_goals": assignment.non_goals,
                    "provides": assignment.provides,
                    "consumes": assignment.consumes,
                },
                "interface_contracts": [contracts[ref].model_dump(mode="json") for ref in refs],
            }
        )
    ]


def pinned_context(app, spec):
    """Read the task's immutable artifact, never rebind to a newer catalog version."""
    return [app.read(ref) for ref in spec.get("context_refs", [])]
