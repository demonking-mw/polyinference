# First run

[Documentation](../README.md) · [Setup](../../setup.md) · [Developer guide](../../dev-readme.md)

Start with the built-in task before selecting a real project:

1. Launch `polyinference ui` without `--config` and open the page.
2. Keep the default root repository, objective and check command.
3. Click **Start run**. This makes real provider requests and consumes API/subscription allowance.
4. Wait for setup, planning, development, review and acceptance to settle.
5. Open **Agents**, select a task or senior query, and expand its execution history. Click a blue model node
   for its prompt and response; other nodes show inputs, outputs and tool results.
6. Use **Save run · JSON** to retain a diagnostic snapshot; **Open snapshot** reopens it in the viewer.

The fixture is a tiny committed Python project generated under
`.polyinference/ui/fixture/`. The goal is to change `greeting("Codex")` from
`Hello Codex` to exactly `Hello, Codex!`, with only `greeting.py` writable and a
read-only unittest checking the result. Successful completion requires the check
to pass against the accepted integrated tree. With default in-place coding the
fixture's actual checkout receives verified work on the selected integration
branch; unfinished or non-successful candidates remain in task worktrees.

Each **Start run** click creates a fresh run and state directory. The UI permits
one active test at a time and retains previous runs in its run selector. A run
can stop with a blocker or exhausted allowance; a recorded worker response alone
does not mean the project completed.

The configured defaults are `claude-haiku-5-5` and `gpt-6.1-sol`. These are model
IDs pinned by this project, not a promise that every account can access them.
If a provider rejects an ID, use a configuration with an available model as
explained below.
