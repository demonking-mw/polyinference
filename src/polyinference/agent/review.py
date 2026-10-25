"""Agent-owned review evidence selection and semantic completion policy."""

from __future__ import annotations

import difflib
from copy import deepcopy

from ..contracts import CodeRevision
from ..domain import canonical, digest
from .architecture import pinned_context


def code_identity(code):
    return {key: code[key] for key in ("commit_id", "effective_tree_digest", "environment_digest")}


def brief_ref(app, ref):
    """Full scoped reference remains durable; avoid repeating its wire envelope."""
    if hasattr(ref, "model_dump"):
        ref = ref.model_dump(mode="json")
    key = "review-artifact/" + digest(canonical(ref))[7:]
    if not app.ports.records.get(key):
        app.ports.records.compare_and_publish({}, {}, {key: ref})
    return {"record_ref": key, "digest": ref["digest"], "size_bytes": ref["size_bytes"]}


def check_view(app, evidence, cap=1200):
    view = app.evidence_view(evidence, cap=cap)
    return {
        **view,
        "checked_code": code_identity(view["checked_code"]),
        "output_ref": brief_ref(app, view["output_ref"]),
    }


def contract(app, head):
    return {
        "reviewed_tree_digest": head["effective_tree_digest"],
        "criteria": [
            {
                "criterion_id": "objective",
                "description": app.config.objective,
                "required_checks": [c.name for c in app.config.checks],
            },
            *[c.model_dump(mode="json") for c in app.config.acceptance_criteria],
        ],
    }


def source_view(app, head, path, content, *, offset=0, cap=1500):
    raw = content[offset : offset + cap] if content is not None else b""
    binary = content is not None and b"\0" in content
    source_ref = (
        brief_ref(
            app,
            app.ports.artifacts.put(
                content, app.scope(), "application/octet-stream" if binary else "text/plain"
            ),
        )
        if content is not None
        else None
    )
    return {
        "evidence_id": "source/" + digest(canonical([head, path, offset, len(raw)]))[7:],
        "path": path,
        "source_code": code_identity(head),
        "source_ref": source_ref,
        "exists": content is not None,
        "offset": offset,
        "content": raw.decode(errors="replace") if not binary else "",
        "binary": binary,
        "truncated": content is not None and (offset > 0 or offset + len(raw) < len(content)),
        "total_bytes": len(content) if content is not None else 0,
    }


async def repository_context(app, head, changed_paths=()):
    tree = await app.ports.workspaces.tree(CodeRevision.model_validate(head).commit_id)
    selected = list(
        dict.fromkeys([*changed_paths, *app.config.allowed_write_paths, *app.config.closure_paths])
    )
    remaining, contents = 4500, []
    for path in selected:
        if remaining <= 0:
            break
        content = tree[path][1] if path in tree else None
        view = source_view(app, head, path, content, cap=min(1500, remaining))
        contents.append(view)
        remaining -= len(view["content"].encode()) + 150
    return {
        "paths": sorted(tree)[:100],
        "omitted_path_count": max(0, len(tree) - 100),
        "contents": contents,
        "omitted_content_paths": selected[len(contents) :],
        "source_code": head,
    }


async def report_view(app, report):
    before = await app.ports.workspaces.tree(report["captured_head"]["commit_id"])
    after = await app.ports.workspaces.tree(report["final_code"]["commit_id"])
    paths = [p for p in sorted(set(before) | set(after)) if before.get(p) != after.get(p)]
    # Full delta retained independently of a bounded presentation. This is actual
    # integrated code, not the worker's summary or original development delta.
    delta = []
    for path in paths:
        old = before.get(path, (None, b""))[1].decode(errors="replace").splitlines(keepends=True)
        new = after.get(path, (None, b""))[1].decode(errors="replace").splitlines(keepends=True)
        delta.append(
            f"path: {path}; mode: {before.get(path, (None,))[0]} -> {after.get(path, (None,))[0]}\n"
            + "".join(difflib.unified_diff(old, new, fromfile="before/" + path, tofile="after/" + path))
        )
    raw = "\n".join(delta).encode()
    full_ref = app.ports.artifacts.put(raw, app.scope(), "text/plain")
    spec = app.get(report["task_spec_ref"])
    return {
        **{
            key: report[key]
            for key in (
                "record_id",
                "task_spec_ref",
                "verdict",
                "resolution",
                "candidate_commit_id",
                "hazard_refs",
            )
        },
        "captured_head": code_identity(report["captured_head"]),
        "final_code": code_identity(report["final_code"]),
        "worker_claim": {
            "summary": app.read(report["assessment_summary"]),
            "source_ref": brief_ref(app, report["assessment_summary"]),
            "trust": "model_claim",
        },
        "task_contract": {
            "objective": app.read(spec["objective"]),
            "allowed_change_scope": spec["allowed_change_scope"],
            "acceptance_spec": app.read(spec["acceptance_spec"]),
            "source_ref": spec["record_id"],
            "module_context": pinned_context(app, spec),
        },
        "changed_paths": paths[:100],
        "omitted_changed_path_count": max(0, len(paths) - 100),
        "integrated_diff": {
            "source_ref": brief_ref(app, full_ref),
            "preview": raw[:2500].decode(errors="replace"),
            "truncated": len(raw) > 2500,
            "before_commit": report["captured_head"]["commit_id"],
            "after_commit": report["final_code"]["commit_id"],
        },
        "task_check_evidence": [check_view(app, e) for e in report["evidence"]],
        "publication_status": "provisional; task verdict does not certify the project objective",
    }


def evidence_catalog(snapshot):
    """Only presented current-tree source and independent checks are citable."""
    head = snapshot["head"]
    sources = snapshot["repository_context"]["contents"] + snapshot.get("review_reads", [])
    catalog = [
        {"evidence_id": s["evidence_id"], "kind": "source", "path": s["path"]}
        for s in sources
        if s["source_code"] == code_identity(head)
        and not s.get("presentation_omitted")
        and not s.get("binary")
        and (s["content"] or s["total_bytes"] == 0)
    ]
    catalog += [
        {"evidence_id": e["evidence_id"], "kind": "independent_check", "criterion": e["criterion_ref"]}
        for e in snapshot.get("independent_review_evidence", [])
        if e["status"] == "passed"
        and e["checked_code"]["effective_tree_digest"] == head["effective_tree_digest"]
        and e["checked_code"]["environment_digest"] == head["environment_digest"]
    ]
    return catalog


def validate_completion(proposal, snapshot):
    assessment = proposal.completion_assessment
    if not proposal.complete:
        return
    if assessment is None:
        raise ValueError("Completion requires a source-backed completion_assessment")
    expected = snapshot["acceptance_contract"]
    if assessment.reviewed_tree_digest != expected["reviewed_tree_digest"]:
        raise ValueError("Completion assessment belongs to another tree")
    ids = [c.criterion_id for c in assessment.criteria]
    if len(ids) != len(set(ids)) or set(ids) != {c["criterion_id"] for c in expected["criteria"]}:
        raise ValueError("Assess every declared criterion, including the full objective, exactly once")
    valid = {e["evidence_id"] for e in snapshot.get("review_evidence_catalog", [])}
    source_ids = {
        e["evidence_id"] for e in snapshot.get("review_evidence_catalog", []) if e["kind"] == "source"
    }
    for item in assessment.criteria:
        if item.verdict != "met":
            raise ValueError("Unmet/uncertain semantic criteria cannot complete the project")
        if not item.evidence_refs or not set(item.evidence_refs) <= valid:
            raise ValueError("Completion requires presented current-tree source/independent evidence")
        if not set(item.evidence_refs) & source_ids:
            raise ValueError("Semantic completion requires source review, not only technical checks")
    required = {name for c in expected["criteria"] for name in c["required_checks"]}
    passing = {
        e["criterion_ref"]
        for e in snapshot.get("independent_review_evidence", [])
        if e["status"] == "passed"
        and e["checked_code"]["effective_tree_digest"] == snapshot["head"]["effective_tree_digest"]
        and e["checked_code"]["environment_digest"] == snapshot["head"]["environment_digest"]
    }
    if not required <= passing:
        raise ValueError("Required project checks lack passing evidence on the reviewed tree")


async def retrieve(app, snapshot, requests):
    head = snapshot["head"]
    tree = await app.ports.workspaces.tree(CodeRevision.model_validate(head).commit_id)
    views = []
    for request in requests:
        content = tree[request.path][1] if request.path in tree else None
        views.append(
            source_view(app, head, request.path, content, offset=request.offset, cap=request.max_bytes)
        )
    return views


def fit_snapshot(app, snapshot):
    """Bound optional previews, never trim objective/criteria/grants or provenance."""
    import json

    from ..domain import SeniorProposal
    from .prompts import SENIOR

    result = deepcopy(snapshot)
    result["memory"] = {
        "senior_summary": result.get("memory", {}).get("senior_summary"),
        "notes": [
            {"source_ref": note.get("source_ref", note.get("record_id")), "comment": note["comment"]}
            for note in result.get("memory", {}).get("notes", [])
        ],
    }
    omitted = list(result.get("omitted_review_material", []))
    instruction = (
        SENIOR + "\nReturn JSON matching this schema: " + json.dumps(SeniorProposal.model_json_schema())
    )

    def size():
        return (
            len(
                canonical(
                    [
                        {"role": "system", "content": instruction},
                        {"role": "user", "content": "Pinned application inputs:\n" + json.dumps(result)},
                    ]
                )
            )
            + 2000
        )

    optional = []
    memory = result["memory"]
    if isinstance(memory["senior_summary"], str):
        optional.append((memory, "senior_summary", "memory/summary"))
    for note in memory["notes"]:
        if not isinstance(note["comment"], str):
            note["comment"] = canonical(note["comment"]).decode()
        optional.append((note, "comment", "memory/" + str(note["source_ref"])))
    for report in result["reports"]:
        optional.append((report["integrated_diff"], "preview", "diff/" + report["record_id"]))
        for e in report["task_check_evidence"]:
            optional.append((e, "output_preview", "task-check/" + report["record_id"]))
        claim = report["worker_claim"]
        claim["summary"] = (
            canonical(claim["summary"]).decode()
            if not isinstance(claim["summary"], str)
            else claim["summary"]
        )
        optional.append((claim, "summary", "claim/" + report["record_id"]))
    for source in result["repository_context"]["contents"]:
        optional.append((source, "content", "source/" + source["path"]))
    # Requested ranges take priority over automatic previews.
    for e in result.get("independent_check_diagnostics", []):
        optional.append((e, "output_preview", "independent-check/" + e["criterion"]))
    for source in result.get("review_reads", []):
        optional.append((source, "content", "requested-source/" + source["path"]))
    result["review_evidence_catalog"] = evidence_catalog(result)
    while size() > app.config.limits.max_input_tokens_per_call:
        candidates = [(obj, key, label) for obj, key, label in optional if obj[key]]
        if not candidates:
            raise ValueError(
                f"Required review contracts exceed context bound ({size()} > {app.config.limits.max_input_tokens_per_call}); "
                "split work or configure a larger context"
            )
        automatic = [item for item in candidates if not item[2].startswith("requested-source/")]
        obj, key, label = max(automatic or candidates, key=lambda item: len(item[0][item[1]]))
        value = obj[key]
        obj[key] = value[: len(value) // 2] if len(value) > 200 else ""
        obj["truncated"] = True
        if key == "content" and not obj[key]:
            obj["presentation_omitted"] = True
        if label not in omitted:
            omitted.append(label)
        result["omitted_review_material"] = omitted
        result["review_evidence_catalog"] = evidence_catalog(result)
    return result
