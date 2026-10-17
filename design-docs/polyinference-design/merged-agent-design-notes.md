# Merged agent design

The editable result is `polyinference-agent-design-merged.html`. Its embedded graph is also saved in `polyinference-agent-design-merged.json` for version control and import.

Sources supplied on 2026-10-17:

- `polyinference-agent-design(3).html`: authoritative names, existing node layout, and complete data/memory model.
- `polyinference-modified-agent-graph (1).html`: expanded architecture descriptions, behavioral contracts, and connections.

## Preservation

All 15 original architecture nodes retain their exact IDs, titles, subtitles, kinds, order, and coordinates. In particular, the two `Result Processor` nodes remain distinct by ID and subtitle; neither was renamed.

The entire original `memoryGraph` JSON is embedded verbatim, including its 19 nodes, 21 transitions, contracts, positions, and label positions. The original memory renderer is retained. Its raw JSON SHA-256 is `1ded73e1ab04418c7f203dc495c56f31b74535d5f4853af69579a03715acfba4`.

Names in the original memory view also take priority when a concept is added to the architecture: `Immediate Memory`, `Cloud conductor / loop`, and `Trap frame mechanism`.

## Architecture merge

The result has 23 architecture nodes and 57 transitions. All 19 original transition IDs are retained through their more complete AI counterparts. Where the AI corrected a route, that route replaces the incomplete original: inference returns to the local `Result Processor` before tool execution, and a candidate enters the verification sequence before commit/report.

Five concepts absent from both original views retain their AI titles:

- `Private code copy · base B`
- `Shell mutex · one command`
- `Verification critical section`
- `Merge head / reconciliation dev`
- `Senior resolution / commit undo`

The original two-pipe arrangement stays intact. Added services occupy surrounding gaps: private workspace above the local loop, shell ownership beside local tools, final-phase synchronization below the local result processor, senior resolution below the cloud result processor, and memory/recovery at the perimeter.

The full architecture incorporates the AI's private-development, reconciliation, ownership, provisional-publication, steering, and recovery contracts. Original independent host evidence checks and project acceptance requirements are retained. The separately preserved memory view is deliberately not reconciled with these expanded architecture contracts.

Focus views preserve the original positions and include relevant additional nodes. Design notes describe the merged behavior. Full node titles wrap rather than being truncated in architecture views; the memory view retains its original rendering.

## Verification and reproduction

`merge-agent-graphs.py USER.html AI.html` rebuilds the HTML and JSON, checks exact original names and positions, verifies byte-for-byte memory preservation, and validates unique identifiers and transition endpoints.

`node check-merged-graph.cjs` checks JavaScript syntax and runs the actual routing code across all five views. The 159 visible routes have attached endpoints and orthogonal segments. Architecture/focus views have no overlapping cards or routes through unrelated cards. Original memory geometry is preserved rather than rearranged. Static layout previews were visually inspected; browser-based interaction testing was unavailable because local file URLs were blocked by browser policy.

Both input files are unchanged. The new document has its own browser autosave identity, preventing older drafts from replacing the merged seed.
