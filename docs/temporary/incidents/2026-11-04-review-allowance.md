# Senior review allowance incident

<a id="run-917e45c4b40a"></a>
## Review allowance visibility — 4 November 2026

Run `917e45c4b40a` completed setup and paused during initial senior review with no development tasks
started. Its first proposal requested eight source ranges against `max_review_reads=4`. No reads were
performed: whole-batch validation rejected it. The configured total and remaining allowance were absent
from the planner input, although the response schema allowed eight ranges per proposal. The correction
used descriptive sentences as task `focused_check` values; response validation required configured check
names. Its physical response repair requested eight ranges again, ending the bounded review correction
loop. The terminal message described an exhausted allowance despite zero successful reads.

Independent review also reproduced missing dependencies: plain `npm ci` failed with `npm: command not
found`; checks using the local runtime helper then failed with `tsc: not found` and `playwright: not
found`. Earlier setup-specific TypeScript/build/Chromium smoke evidence passed in the worker workspace.
This investigation distinguishes setup verification, independent environment preparation and planning
validation; the exported Minecraft objective is retained evidence.

`development-docs/FIXES.md#fix-0175` raises the fresh-configuration default to 16 and supplies current
`review_limits`, `planning_limits`, process `resource_limits`, `resources`, finishing reserve and
response budget to the planner. Numeric rejection feedback now states requested and remaining ranges.
The eight-range proposal and 4000-byte range schema bounds remain. Explicit lower/zero settings still
apply. Dependencies and invalid focused-check generation remain separate follow-ups; these changes do
not establish live planner convergence. Historical source, configuration, accounts and run state are
preserved; no Resume or new model inference was performed for this repair.
