# Maintaining documentation and navigation

[Documentation](README.md) · [Developer onboarding](../dev-readme.md)

**A fix or feature is unfinished until its affected documentation is current.**
Humans and agents follow this contract in the same change:

1. Find the owning feature in [file-tree.json](file-tree.json) or the
   [HTML tree](file-tree.html); read its single primary `doc` and related fixes.
2. Update that guide's purpose, file responsibilities, interfaces, invariants and
   verification pointers when behavior changes. For OS work, read the
   [runtime boundary](../design-docs/simplified-os/RUNTIME_BOUNDARY.md) first.
3. Update affected setup, usage, configuration, design and issue documents.
   State which were reviewed and why no edit was needed when they still apply.
4. Add/move/remove file paths and feature leaves in `file-tree.json`; give each
   leaf exactly one primary doc. Group closely related code files in one leaf.
   Every first-party code file needs a named responsibility in that doc.
5. Append an evidence-based [FIX entry](../development-docs/FIXES.md), then run:

   ```bash
   python scripts/project_docs.py
   python scripts/project_docs.py --check
   ```

6. Include documentation updates/review and actual verification in the handoff.
   Do not leave documentation maintenance to a later task or agent.

When rules, design ownership, setup or automation change, update the
[contributor onboarding procedure](contributor-onboarding.md) and
[project memory checklist](project-memory.md), then refresh retained project notes.

`file-tree.json` is the authored navigation source. The script embeds that exact
JSON in `file-tree.html` and renders working links before JavaScript runs, so the
tree works from `file://` without a server or fetch. Never edit generated HTML.
The check rejects uncovered files, duplicate ownership, missing docs/paths,
broken local Markdown links, unreachable docs and stale HTML. It does not prove
the prose matches runtime semantics; reviewers must check that explicitly.
The same check runs on pushes and pull requests through the
[documentation workflow](../.github/workflows/docs.yml).

Keep new overview/module guides around 80 lines or less. Split long procedures
into focused pages with obvious links. Existing specifications, append-only fix
history and historical evidence retain their stable paths/anchors; concise hubs
lead to them. Preserve earlier decisions and mark supersession explicitly.

The inventory includes repository-owned files and excludes ignored state,
environments, builds, OS download metadata and upstream reference checkouts.
[References](../references/README.md) identifies those external boundaries and
their upstream entry points. Runtime snapshots and private credentials are not
source documentation.

The root [AGENTS.md](../AGENTS.md) is also this repository's persistent Codex
project instruction. Its completion rule applies to future Codex chats opened
in the PolyInference checkout; it travels with the project.
See the [official Codex instruction-loading guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
