# Reference materials

[Documentation](../docs/README.md) · [Current design](../design-docs/README.md) · [File tree](../docs/file-tree.html)

These are research and original artifacts. Current implementation decisions
belong to the [revision ledger](../design-docs/simplified-os/DESIGN_REVISIONS.md).

| Material | Start here |
| --- | --- |
| Agent comparison/repository mapping | [Reference document index](docs/README.md) |
| Codex proxy exploration | [Proxy brief](codex-agent-proxy-brief.md); distinguish from the [current native adapter](../docs/modules/inference.md) |
| Original design exports | [Reference document index](docs/README.md) and [design provenance](../design-docs/polyinference-design/README.md) |

## Upstream checkouts

The following optional checkouts have their own documentation and ownership;
the project tree treats each as one external boundary rather than documenting
third-party modules as PolyInference implementation:

- [Claude Code](claude-code/README.md)
- [Deep Agents](deepagents/README.md)
- [Mini SWE Agent](mini-swe-agent/README.md)

Their contents may depend on separately populated checkouts/submodules. Use each
upstream README to navigate its files. OS download `Zone.Identifier` sidecars
have no project semantics and are excluded from navigation.

After research-driven implementation changes, update affected project guides,
navigation and [FIXES.md](../development-docs/FIXES.md); preserve provenance and
mark superseded conclusions explicitly.
