# Browse and maintain the Obsidian graph

Open the [reading map](reading-map.canvas) for a fixed overview of the main routes.
Open **Graph view** for the complete note tree or **Open local graph** on a module
hub at depth 1–2 to follow its immediate links.

| Group | Color | Look here for |
| --- | --- | --- |
| Root README | Coral `#E05752` | Project entry point |
| Navigation | Gold `#C59122` | Agent instructions, setup, architecture, current work and fix history |
| OS runtime | Blue `#478BD0` | Kernel, processes, capabilities, storage and runtime contracts |
| Coding agent | Green `#4EAD54` | Workflows, assignments, repository policy and recovery |
| Inference | Teal `#269C89` | Providers, admission, context, retries and simulation |
| Scheduler | Violet `#9865CB` | Proposed scheduler policy and OS support |
| Use and operations | Orange `#CB7040` | Launch, configure, inspect, recover and export |
| Verification and tooling | Rose `#BA5990` | Tests, qualification and contributor tools |
| Records and research | Slate `#7A8798` | Implementation records, draft designs and run evidence |

Reserved for future modules: `#5163C7` (indigo), `#8E7047` (bronze) and
`#7EAB29` (lime).

| To find | Enter in Obsidian Search |
| --- | --- |
| Pending work | `path:"development-docs/tasks/"` |
| A fix by ID | `path:"development-docs/FIXES.md" "FIX-0191"` |
| Inference and retry docs | `path:/^docs\/(guides|modules)\// file:(inference OR endpoint OR retry OR fallback)` |
| Scheduler designs and audit | `path:"docs/temporary/" file:scheduler` |
| Run reports | `path:"docs/temporary/investigations/" file:(run OR minecraft)` |

The [shared graph preset](obsidian-graph.json) limits the graph to project notes
and hides unresolved targets, orphans, tags and attachments. It uses shorter
links and more repulsion to keep connected notes close and branches readable.
Obsidian applies forces globally. The reading map uses fixed positions.

When adding, moving or changing ownership of notes, update the parent link and
`docs/file-tree.json`. Review the preset filter and color queries so every note
matches one group. Exclude new module paths from any broad archive query they
previously matched and use the spare colors. Update the reading map and search examples when important routes
change. Keep the README color exclusive to the repository root.

Validate the shared files with `python3 scripts/obsidian_graph.py --check`.
To refresh a local vault, quit Obsidian, run
`python3 scripts/obsidian_graph.py --apply` and reopen the vault. The script
preserves other graph keys and saves the original graph settings once as
`.obsidian/graph.before-polyinference.json`. The workspace and app settings
live separately. Review the graph and map in Obsidian after changing the layout.
