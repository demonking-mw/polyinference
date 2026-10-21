# Developer onboarding

[Project](README.md) · [Documentation](docs/README.md) · [HTML tree](docs/file-tree.html) · [JSON tree](docs/file-tree.json)

**Update all affected documentation after implementing any fix or feature, in the
same change.** This applies to humans and agents; documentation is part of completion.

## Before changing anything

1. Read [AGENTS.md](AGENTS.md) and the complete [fix history](development-docs/FIXES.md),
   including related entries and design principles.
2. Find the owning [module guide](docs/modules/README.md) through the tree. For OS
   or agent work, also read the [runtime boundary](design-docs/simplified-os/RUNTIME_BOUNDARY.md)
   and [accepted design revisions/open gaps](design-docs/simplified-os/DESIGN_REVISIONS.md).
3. [Set up the environment](setup.md). Install the test extra and run the
   [checks relevant to your change](docs/testing.md). Keep generated test projects
   in ignored `testing/`; the maintained suite is `tests/`.

## Reading routes

| Area | Start here |
| --- | --- |
| Source layout and ownership | [Architecture](docs/architecture.md), [modules](docs/modules/README.md) |
| Agent workflows and protocols | [Agent design](design-docs/langgraph-agent/README.md) |
| OS mechanisms and guarantees | [OS design](design-docs/simplified-os/README.md), [runbook](design-docs/simplified-os/RUNBOOK.md) |
| All exported OS settings | [Settings reference](design-docs/simplified-os/AGENT_SETTINGS.md) |
| Current implementation/provider notes | [Implementation index](design-docs/implementation/README.md) |
| Current defects and implementation work | [Current iteration](development-docs/current-iter-issues.md) |
| Future work | [Next iteration](development-docs/next-iteration.md) |
| Unsorted questions | [General issues](development-docs/general-issues.md); triage into current/next |
| Investigations, audits and historical decisions | [Development index](development-docs/README.md), [design index](design-docs/README.md) |
| Original briefs and implementation plan | [Brief](PROJECT_BRIEF.md), [plan](IMPLEMENTATION_PLAN.md) |
| Upstream research and original diagrams | [References](references/README.md) |

## Completion checklist

- Update the owning module guide, and all affected setup, usage, settings,
  architecture and issue docs. Explain reviewed docs that need no change.
- Update [file-tree.json](docs/file-tree.json) when files/features move or change;
  every leaf has exactly one primary doc and an explicit list of related files.
- Update [FIXES.md](development-docs/FIXES.md) with problem, owning root cause,
  implementation, design principle and actual verification. Preserve past entries.
- Follow [documentation maintenance](docs/maintenance.md), regenerate the HTML
  tree, run `python scripts/project_docs.py --check`, and report checks and limits.

The root `AGENTS.md` supplies persistent Codex project instructions for this
checkout. Keep its documentation reminder current alongside this guide.
