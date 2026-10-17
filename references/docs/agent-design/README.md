# Polyinference sprint architecture v1

Open `../polyinference-agent-v1.html` directly in a browser. It is a standalone,
offline editor with the complete design embedded. No installation or server is
required. The original architecture study and v0 JSON are preserved.

The same graph file now has eight nodes arranged in two vertical pipes, with
plain text pipe headings and no enclosing group boxes:

- Cloud: senior engineer → sprint task queue → sprint coordinator → project acceptance.
- Local: coding agent → tools and observations → task verification → commit and report.

Initial, review, planning, specialist, and completion prompts are described inside
the single cloud-model node. Worker prompt variations are likewise described
inside the single local-model node. Each interaction arrow contains a detailed
comment and payload in the existing click inspector; its on-canvas text stays
hidden until selection. The editor controls and export formats are unchanged.

The design follows the revised cloud-led sprint direction: the first model call
reviews the objective and plans work; a host-managed queue feeds bounded local
coding loops; each closed task produces a checkpoint commit and a structured
result packet. Queue exhaustion, unrecoverable failure, changed assumptions, and
integration failures reconvene the senior. An occasional explicit hard assignment
uses the cloud in the same execution harness. Project completion requires a senior
decision and independent checks of the integrated tree.

## Using the editor

- Drag states; arrows automatically recompute their boundary ports and routes.
- Click an arrow to reveal its label and transition contract. Other arrows stay
  unlabeled. Select a state to inspect its behavior and related transitions.
- Use Edit in the inspector to change state text, type, contracts, or an arrow's
  endpoints. Add states with `+ State`; Connect takes a source and destination.
- Use focus views, search, pan, zoom, fit, the minimap, and undo/redo to navigate.
- Export JSON for an editable graph, Save HTML for a standalone editable copy, or
  use the more-tools menu to export the current view as SVG.
- Browser autosave preserves a convenience draft. Export for a portable backup.
- Import accepts the old v0/v1 graph JSON and the new v2 schema. Legacy fixed edge
  waypoints are discarded. Reset restores the design embedded in that HTML file
  and can be undone.

Focus views show subsets of the actual states and direct transitions. They do
not invent shortcut edges. Their positions can be edited independently of the
full map. Shared persistence, model adapters, tool policy, leases, and recovery
are described inside the owning nodes; see Design notes for the ownership rules
and source references. The embedded graph's browser-draft key is revised so an
old cached 31-node draft does not hide this in-place update.

## Source and verification

`build.cjs` contains the architecture data; `editor.html` is the editor template.
From the project root, regenerate the two artifacts with:

```text
node references/docs/agent-design/build.cjs
node references/docs/agent-design/verify.cjs
```

Offline checks cover embedded JSON consistency, JavaScript syntax, graph and
reference integrity, obstacle avoidance before/after moving a state, focus views,
selected-only arrow labels, contract edits, connections, undo/redo, old-format
imports, unsafe-link filtering, JSON export, and the persistence adapter. They run
the editor with a minimal DOM test double; they do not prove browser appearance or
native downloads. Browser preview verification was unavailable because the
browser tool rejected access to the local page.
