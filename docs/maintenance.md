# Maintain the documentation

Find the feature in the [JSON tree](file-tree.json). Read its primary `doc` and
the relevant FIX entries before changes. In the same task, update affected
module, setup, usage, settings, design and task docs. A primary guide names each
owned source file, its interface, invariants and meaningful checks. Group related
files under one guide when their responsibilities belong together.

## Add or move a note

1. Give the note one purpose: a tutorial, a procedure, a reference or an
   explanation. Keep entry pages short; split unrelated topics. A coherent
   specification or append-only ledger may be longer.
2. Add a relative Markdown link from its single parent, such as
   `[Configuration](guides/configuration.md)`. Use `/` in paths, explicit `.md`
   and percent encoding for spaces. Same-page heading links can use the heading
   text, e.g. `[Example](#Add%20or%20move%20a%20note)`.
3. Match the parent/child relationship in `docs/file-tree.json`. Use inline
   code for citations across branches: `development-docs/FIXES.md#fix-0080`.
   Use Quick Switcher to open a cited path and Find to locate the section or
   FIX ID. Source code, external sites and supporting HTML/data can stay
   clickable. Cite upstream Markdown by path so it stays outside the vault's
   note tree. The offline file map is generated from the same JSON.
4. Put working notes in `docs/temporary/` and name them `YYYY-MM-DD-short-topic.md`.
   Record date, source and status. When decisions land, update the maintained
   guide and mark the temporary note. Preserve unique evidence linked by a FIX.
   Before removing a script, check references, callers, CI and reusable tests.

## Finish the change

Append a FIX entry in `development-docs/FIXES.md`. Keep stable IDs, preserve
earlier text and report symptoms, ownership, the change, design and actual checks.
Mark investigation-only work and later corrections explicitly. Check adjacent
docs and explain those that need no change. Refresh `docs/contributor-onboarding.md`
and `docs/project-memory.md` when rules, ownership, setup or automation change.

```bash
python scripts/project_docs.py
python scripts/project_docs.py --check
```

CI verifies file ownership, source links, note-tree structure, maintained HTML
links and generated output. It does not prove prose accuracy. For changed settings
schemas/defaults also run `python scripts/settings_docs.py` and
`python scripts/settings_docs.py --check` in the project environment.
Keep ignored state, local Obsidian preferences, private logs and upstream
checkouts outside the first-party doc tree.

In Obsidian, open this checkout as a vault and start at the root `README.md`.
For a WSL checkout, run Linux Obsidian through WSLg so the file watcher uses
the Linux filesystem directly. From the repository root in Ubuntu, run
`bash scripts/open_obsidian.sh --install`. This downloads the official Debian
package and uses `sudo` to install it if needed. In the vault picker, select
**Open folder as vault** and choose this checkout's Linux path. After that,
`bash scripts/open_obsidian.sh` opens `README.md` in the registered vault.

If Obsidian looks blurry, quit it completely and relaunch with the script.
It selects native Wayland when the display socket is available. Use
`bash scripts/open_obsidian.sh --x11` if the Wayland window fails to open.

Set **New link format** to **Relative path to file** and disable **Use Wikilinks**.
In Graph view, turn off Tags and Attachments, and turn on Existing files only.
If the vault also contains local state or upstream repositories, exclude
`testing/`, `references/claude-code/`, `references/deepagents/`,
`references/mini-swe-agent/` and other local output folders in **Files and links
→ Excluded files**. Keep `docs/temporary/` visible.
