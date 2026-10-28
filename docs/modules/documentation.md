# Documentation tooling

[Modules](README.md) · [Maintenance contract](../maintenance.md)

| File | Responsibility |
| --- | --- |
| [scripts/project_docs.py](../../scripts/project_docs.py) | Validate the feature tree, file coverage, primary-doc source references, local links/anchors and README reachability; render deterministic HTML. |
| [docs/file-tree.json](../file-tree.json) | Authored feature hierarchy with one primary `doc` and explicit related `files` per leaf. All paths are repository-relative POSIX paths. |
| [docs/tree-template.html](../tree-template.html) | Offline HTML shell with placeholders for JSON and static feature links. |
| [docs/tree.css](../tree.css) | Responsive tree/search presentation and print styling. |
| [docs/tree.js](../tree.js) | Local search, expand/collapse, counts and JSON inspection; no fetch or network dependencies. |
| [docs/file-tree.html](../file-tree.html) | Generated human tree containing the exact JSON and static doc/source links. |
| [tests/test_project_docs.py](../../tests/test_project_docs.py) | Coverage, invalid-tree/link/reachability, generation and offline rendering regressions. |
| [.github/workflows/docs.yml](../../.github/workflows/docs.yml) | Run the dependency-free navigation check on pushes and pull requests. |

Link validation reads maintained Markdown, generated file-tree.html and maintained
documentation HTML/anchors under docs/, design-docs/ and development-docs/.
The unrendered tree template and application UI routes have separate URL bases.
Upstream reference boundaries remain explicit. Source-reference
checks require a link; reviewers must assess the responsibility explanation,
behavior/defaults, regression evidence and concision. These are current tooling
limits, not guarantees supplied by the passing CI check.

Every leaf has exactly one primary Markdown doc. Closely related code files may
share it; each source file must be linked and explained there. Additional reading
lives in the guide's normal links. Branches contain groups, never code-file leaves.
The JSON is the source for both agent navigation and generated human navigation.

The inventory covers maintained checkout files, including new untracked files.
Ignore rules exclude transient local state; explicit external boundaries cover
the upstream repositories listed in [references](../../references/README.md).
Validation does not read credentials or recursively scan upstream code.

Run `python scripts/project_docs.py` to regenerate, then
`python scripts/project_docs.py --check` for read-only validation. The latter
fails if the checked-in HTML no longer represents the authored JSON/template.
Use `python -m pytest tests/test_project_docs.py -q` for tooling regressions.

Update affected docs after every fix/feature; update this guide and
[maintenance](../maintenance.md) whenever navigation behavior changes. Record
the actual result in [FIXES.md](../../development-docs/FIXES.md).
