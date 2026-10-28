"""Read-only application records for the agent monitor, separate from OS state."""

from __future__ import annotations


def agent_snapshot(records, read_text):
    """Keep task history and resolution events; expand only small explanatory text.

    Live views and saved snapshots use the same browser-side projection. Full
    evidence and model/tool artifacts are fetched only when the user inspects them.
    """
    prefixes = (
        "task/", "task-spec/", "attempt/", "report/", "resolution/", "resolution-event/",
        "plan/", "proposal/", "head/", "memory/", "memory-note/", "hazard/", "setup/",
        "worker-exception/", "exception-queue/", "worker-progress/", "worker-state/", "progress-event/", "progress-observer-error/", "interface-contract/",
        "acceptance-receipt/", "outputs/", "output-delivery/", "review-batch/", "coding/", "repository/",
    )
    selected = {key: value for key, value in records.items()
                if key == "app/run" or key.startswith(prefixes)}
    texts = {}
    for value in selected.values():
        if not isinstance(value, dict):
            continue
        refs = [value.get(name) for name in ("assessment_summary", "reason", "goal", "content")]
        refs.append((value.get("extensions") or {}).get("polyinference/stop-detail"))
        for ref in refs:
            if not isinstance(ref, dict) or not ref.get("digest") or ref["digest"] in texts:
                continue
            try:
                content = read_text(ref)
                texts[ref["digest"]] = content[:12000] + (
                    "\n[Preview truncated; inspect the artifact for full text.]" if len(content) > 12000 else ""
                )
            except (OSError, ValueError) as exc:
                texts[ref["digest"]] = "Artifact unavailable: " + str(exc)
    from .agent.qualification import quality

    return {"records": selected, "texts": texts, "quality": quality(records)}
