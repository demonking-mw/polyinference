# Design contracts, graph merge and reader tools

[Modules](README.md) · [Design index](../../design-docs/README.md)

These offline tools maintain design artifacts. They do not implement the running
OS or establish conformance to every proposed guarantee.

| File | Responsibility |
| --- | --- |
| [langgraph-agent/contracts.py](../../design-docs/langgraph-agent/contracts.py) | Preserved proposal wire models; runtime types are packaged separately. |
| [langgraph-agent/validate_contracts.py](../../design-docs/langgraph-agent/validate_contracts.py) | Example/schema and selected invalid-combination checks. |
| [simplified-os/contracts.py](../../design-docs/simplified-os/contracts.py) | Design OS/workspace extension models. |
| [simplified-os/validate_contracts.py](../../design-docs/simplified-os/validate_contracts.py) | Core fixtures and cross-document consistency checks. |
| [merge-agent-graphs.py](../../design-docs/polyinference-design/merge-agent-graphs.py) | Merge supplied user/AI exports while preserving the chosen memory model. |
| [check-merged-graph.cjs](../../design-docs/polyinference-design/check-merged-graph.cjs) | Offline merged-graph routes, structure and layout checks. |
| [visuals/build.py](../../design-docs/visuals/build.py) | Embed editorial content, locales, styles/scripts and fingerprints in standalone readers. |
| [visuals/content.py](../../design-docs/visuals/content.py) | Curated design stories, components and illustrative execution snapshots. |
| [visuals/template.html](../../design-docs/visuals/template.html) | Reader document template. |
| [visuals/atlas.js](../../design-docs/visuals/atlas.js) | Reader navigation, scenarios, notes and locale behavior. |
| [visuals/atlas.css](../../design-docs/visuals/atlas.css) | Responsive, theme and print presentation. |
| [visuals/zh-CN.json](../../design-docs/visuals/zh-CN.json) | Translation data shared by the reader implementation. |
| [agent-design/build.cjs](../../references/docs/agent-design/build.cjs) | Update early agent graph exports while preserving their editor infrastructure. |
| [agent-design/verify.cjs](../../references/docs/agent-design/verify.cjs) | Offline graph data, source-link and editor behavior checks. |

Keep current runtime promises in the [revision ledger](../../design-docs/simplified-os/DESIGN_REVISIONS.md)
and [boundary guide](../../design-docs/simplified-os/RUNTIME_BOUNDARY.md). Preserve
historical graph/layout/memory provenance. Updating a fingerprint alone does not
update a reader's curated semantics; update content and translations deliberately.

Verification commands, run from the repository root with the test environment:

```bash
python design-docs/langgraph-agent/validate_contracts.py
python design-docs/simplified-os/validate_contracts.py
node design-docs/polyinference-design/check-merged-graph.cjs
```

Only rebuild readers when editing them intentionally; follow their
[regeneration/status guide](../../design-docs/visuals/README.md). Historical fixture
checks do not substitute for [runtime tests](../testing.md).

After design-tool fixes/features, update this guide, affected design/status docs,
navigation and [FIXES.md](../../development-docs/FIXES.md) in the same change.
