# Design atlas

Open either file directly in a browser; no server, package install, network access or external library is required:

- [Agent design](agent-design.html)
- [Simplified OS design](os-design.html)

Each standalone HTML includes its styles, script and design data. Keep both files in this directory for the Agent/OS switch and repository source links. Each file's diagrams, stories and review notes still work independently if it is copied elsewhere.

## Reading the views

- **Architecture:** three focused maps per design. Select components for inputs, outputs, invariants, source links and questions to assess. Arrows show curated principal handoffs, not every graph transition or a separate process per box. On narrow screens the cards reflow and name their outgoing handoffs instead of shrinking a dense diagram.
- **Execution stories:** five illustrative schedules covering normal concurrent work, steering, failed verdict/revert, publication crash recovery and aborted integration. Previous/next and event selection update the state snapshot. Switch lens to see the same event from the other design. Occupancy values are illustrative, not measured deployment capacities or execution logs; intermediate commands/turns may be summarized between snapshots.
- **Shared contracts:** the agent/runtime responsibility boundary, complete verification lifetime, normal verdict handling, independent limits, and core/future scope.
- **Assess the design:** eight questions per design, expandable reasoning, user judgments and notes. Browser local storage retains these when permitted. Export downloads JSON with source fingerprints; nothing is sent to an external service. Judgments do not assert runtime conformance.
- **Source trail:** authoritative current designs, merged diagram, audit, contract artifacts and source consolidation. Source fingerprints identify the document bytes at build time; they are not a live freshness check.

Use the theme switch for light/dark appearance, and **Print this view** for the current section. The review view expands its questions for printing. Links preserve map/component or story/event selection in the URL fragment.

Use **English / 简体中文** in the top bar to switch languages. Both files contain the complete Simplified Chinese translation of the reader: component contracts, maps, execution narratives and snapshots, shared contracts, review questions, and source descriptions. The selection is remembered when browser storage is available and carried in links as `lang=en` or `lang=zh-CN`. Switching preserves the selected component/event, review judgments, and your original notes. Source documents and identifiers remain in their original language.

### Chinese terminology

The translation keeps these distinct design operations separate:

| English | 简体中文 |
| --- | --- |
| Agent | 智能体 |
| Verification / verification gate | 核验 / 核验门控 |
| Assessment | 评估 |
| Senior review | 资深审查 |
| Project acceptance | 项目验收 |
| Code reconciliation | 合并后协调 |
| Effect reconciliation | 核实操作结果 |
| Provisional head | 暂定版本头 |
| Unresolved report | 待处置报告 |
| Continuous batching | 连续批处理 |

Protocol identifiers such as `TaskReport`, `verification_gate`, verdict values and journal-state codes remain identifiable. Displayed review judgments are translated; their stored/exported status codes stay canonical so saved notes work in either language. This is a translation of the visual reader, not a separate revision of the source specifications.

## Regeneration

From the repository root:

```sh
python -B design-docs/visuals/build.py
```

`content.py` is a manually curated projection of the audited source designs, with shared event snapshots so the two lenses cannot drift independently. `template.html`, `atlas.css` and `atlas.js` supply the reader. `build.py` embeds all content and source fingerprints into both output files using only the Python standard library. If a source design changes, review the corresponding content and stories before rebuilding; updating a fingerprint alone does not update the editorial projection.

`zh-CN.json` stores the Chinese design content, interface labels and shared explanatory text as data. Update it alongside the English content when the design changes. Both locales are embedded locally; switching does not call a translation service. There are no Chinese Python source files.

The merged source diagram and original designs are not modified by this build. These are visual design artifacts, not agent, OS, scheduler or backend implementations.
