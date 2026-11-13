# Documentation tooling

| File | Responsibility |
| --- | --- |
| [scripts/project_docs.py](../../scripts/project_docs.py) | Check ownership, paths, anchors and the exact set of note links allowed by the tree. Render offline HTML. |
| [scripts/open_obsidian.sh](../../scripts/open_obsidian.sh) | Install Obsidian on Ubuntu amd64 when requested. Open the existing vault through WSLg with native Wayland when available and an explicit X11 fallback. |
| [docs/file-tree.json](../file-tree.json) | Version 2 note hierarchy rooted at `README.md`. Each node has one primary `doc`, its `files` and optional `children`. Paths are repository-relative POSIX paths. |
| [docs/tree-template.html](../tree-template.html) | Offline HTML shell with placeholders for JSON and static feature links. |
| [docs/tree.css](../tree.css) | Responsive tree/search presentation and print styling. |
| [docs/tree.js](../tree.js) | Local search, expand/collapse, counts and JSON inspection; no fetch or network dependencies. |
| [docs/file-tree.html](../file-tree.html) | Generated human tree containing the exact JSON and static doc/source links. |
| [tests/test_project_docs.py](../../tests/test_project_docs.py) | Regressions for second parents, cycles, missing note links, inventory, heading targets, generation and offline rendering. |
| [.github/workflows/docs.yml](../../.github/workflows/docs.yml) | Run the dependency-free navigation check on pushes and pull requests. |

Each Markdown note links to its direct children. The checker compares those
links to the JSON for every note. An HTML index alone cannot satisfy that test.
Same-note anchors, source links and supporting HTML do not create note-tree
edges. Review descriptions, effective behavior and defaults against the source;
the checker validates structure. Follow `docs/maintenance.md` for the link format.

The inventory covers tracked and unignored first-party files. The checker
validates maintained documentation HTML under `docs/`, `design-docs/` and
`development-docs/`, but skips the unrendered template and application UI URL
base. Upstream checkouts are documented in `references/README.md`.

Run `python scripts/project_docs.py` to regenerate, then
`python scripts/project_docs.py --check` for read-only validation. The latter
fails if the checked-in HTML no longer represents the authored JSON/template.
Use `python -m pytest tests/test_project_docs.py -q` for tooling regressions.
