# Router tutorial history

<a id="router-distillation-tutorial"></a>
## Agent-router distillation research tutorial — 2026-10-22

Status: documented; research instructions only, outside the current runtime fixes.
The [HTML learning guide](../../../development-docs/router-training-guide.html) explains training fundamentals,
distillation, RLAIF, model/thinking choices, synthetic data and two-pass summaries;
its labs include the step-by-step distillation walkthrough and later feedback work.
The Markdown tutorial (`development-docs/router-distillation-tutorial.md`) covers Opus labels,
a small LoRA student on the user's reported 16 GB GPU, validation, inference and
evaluation, with RLAIF as a later stage. The user reports written Anthropic
permission for this research project. Recording the tutorial does not implement
a learned router, change process settings or reopen the completed fix queue.
Next-version work remains in the routing proposal (`development-docs/next-iteration.md#learned-agent-routing`).
Documentation verification and limits: `development-docs/FIXES.md#fix-0106`.
Expanded learning-guide verification: `development-docs/FIXES.md#fix-0107`.
