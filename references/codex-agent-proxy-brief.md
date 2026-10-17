# Codex agent proxies: build brief

Research date: 2026-10-16. Documentation review only; these proxies have not been installed, audited, or tested in this repository. Recheck the selected project's current README and pin its commit before implementing.

## Decision

For a prototype where a LangGraph node submits a task and receives the result of a complete Codex execution, first evaluate **[mehdic/codex-proxy](https://github.com/mehdic/codex-proxy)**. Keep the **[official Codex SDK](https://learn.chatgpt.com/docs/codex-sdk)** as the comparison baseline and fallback. Use the SDK directly if a compatible HTTP interface adds no value.

The desired operation is: give Codex an objective, let its runtime choose and execute tools over multiple steps, and return the outcome. A proxy that only forwards model requests does not supply that execution loop.

This fits the `agent_job` backend described in [the project design](../design-docs/project-design.md), section 5.2. It does not replace the separate `model_inference` interface used when Polyinference owns the action/observation loop. This brief adds an implementation candidate; it does not change the project's architecture or select a production dependency.

## Third-party candidates

| Project | Documented approach | Use in this project |
| --- | --- | --- |
| [mehdic/codex-proxy](https://github.com/mehdic/codex-proxy) | Wraps `codex app-server` over stdio; exposes Chat Completions and Responses-shaped endpoints. Codex owns authentication. Native Codex tools remain available. | First candidate for a Codex agent behind an HTTP interface. |
| [CIVITAS-John/codex-app-server-to-proxy](https://github.com/CIVITAS-John/codex-app-server-to-proxy) | Prerelease app-server wrapper with Chat Completions, continuation, activity reporting, and per-request working-directory, sandbox, and search controls. | Alternative when explicit execution controls and activity reporting are priorities. |
| [starhunt/star-cliproxy](https://github.com/starhunt/star-cliproxy) | Runs installed CLIs behind compatible APIs; documents Codex CLI and persistent app-server modes, session reuse, and a dashboard. | Consider if several agent runtimes must share one endpoint. Select an agent execution mode explicitly. |
| [router-for-me/CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) | Codex OAuth and other providers behind compatible model APIs, with streaming, function calling, and routing. | Candidate for model access when LangGraph owns the agent loop. Its documented gateway features do not establish full Codex CLI execution. |
| [RayBytes/ChatMock](https://github.com/RayBytes/chatmock) | OpenAI/Ollama-compatible model access with ChatGPT authentication; documents function calling, images, reasoning controls, and web search. | Candidate for model access. Do not assume its function-call support means it executes local coding tasks internally. |

These are capability comparisons based on project documentation, not reliability rankings or confirmation of access for a particular subscription.

### Limits that affect the choice

- **mehdic:** normal requests create fresh threads; continuity is opt-in. Its README documents incomplete multimodal transport, no durable Responses state, and no approval UI bridge. The default sandbox is read-only. [Runtime and caveats](https://github.com/mehdic/codex-proxy#caveats)
- **CIVITAS:** built-in shell/filesystem access and search are disabled by default. Set its `x_codex` policy deliberately. Client system messages replace Codex's base instructions; project/runtime instructions still apply. Subagents require a process-level opt-in. Its API is not full Responses compatibility. [Policy](https://github.com/CIVITAS-John/codex-app-server-to-proxy#select-codex-policy), [instructions](https://github.com/CIVITAS-John/codex-app-server-to-proxy#instruction-configuration)
- **All candidates:** an OpenAI-compatible response shape does not prove identical ChatGPT desktop behavior, native tool execution, complete event visibility, or safe cancellation. Verify the capabilities the adapter promises.

## Integration boundary

```text
LangGraph / kernel coordinator
  -> CloudProcessSpec and bounded execution grant
  -> agent_job adapter
  -> local proxy
  -> Codex app-server: model + tools + observations + continuation
  -> terminal result and evidence artifacts
  -> Cloud Result Processor / verification gate
```

Use one owner for each loop. LangGraph controls task dispatch and transitions; Codex controls the steps inside its assigned job. Avoid putting a LangGraph tool loop around every internal Codex action.

There are two tool paths to distinguish:

1. **Native tools:** Codex executes tools configured in its runtime and continues reasoning internally.
2. **Client-defined functions:** a compatibility wrapper may return `tool_calls` for the caller to execute. Those require another request with the observations. They are not evidence of an internally completed task.

The mehdic wrapper documents this distinction explicitly in its [tool bridge](https://github.com/mehdic/codex-proxy#tool-calling). For the first agent-job experiment, use native tools and leave client-defined functions out of the request.

## First build sequence

1. **Establish the baseline.** Authenticate with `codex login` and run a small task directly through Codex. Record the CLI version, selected model, permissions, working directory, and available tools. ChatGPT sign-in and API-key billing are separate access paths; verify which is active. [Official authentication](https://learn.chatgpt.com/docs/auth)
2. **Install the selected proxy separately from the target workspace.** For mehdic, the documented build is below. Select and record a reviewed commit before installing dependencies. Do not let the agent's working directory accidentally become the proxy's source checkout.

   ```bash
   git clone https://github.com/mehdic/codex-proxy.git
   cd codex-proxy
   # Check out the reviewed revision, then record it:
   git rev-parse HEAD
   npm install
   npm run build
   npm start
   ```

   Its documented default base URL is `http://127.0.0.1:3466/v1`. Confirm the effective target directory and sandbox in the proof run before allowing writes. [Setup](https://github.com/mehdic/codex-proxy#install-and-run)

3. **Prove native execution before integrating LangGraph.** Submit a task requiring several observable actions: run `pwd`, list the target repository, read `PROJECT_BRIEF.md`, then summarize its requirements. Supply no client-defined tools. Inspect the execution trace; correct-looking prose alone is insufficient proof.
4. **Prove a bounded edit.** In a disposable workspace, ask for one small file change and a configured check. Verify the actual file, command exit status, and resulting diff independently. Confirm that the agent cannot write outside its authorized scope.
5. **Build one adapter.** Expose `submit`, `status/events`, `cancel`, and `collect_result` as internal concepts. Declare unsupported operations honestly; a Chat Completions endpoint alone may not implement all four. Use direct app-server/SDK integration if necessary.
6. **Add one LangGraph node.** Submit a complete bounded task, await terminal completion, store artifact references, and return a typed outcome. Keep the proxy and Codex process alive outside the node's transient state.
7. **Add recovery only after the basic path works.** Exercise timeout, disconnect, process restart, quota rejection, and continuation. Persist operation identity before dispatch. Reconcile uncertain execution before submitting a replacement.

The install commands above are upstream instructions, not actions already performed here. Run them in the environment that will host the agent. For this WSL-based project, a Linux-hosted prototype is a reasonable first experiment; Windows/WSL interoperability has not been validated.

## Adapter contract and sessions

Keep the provider-specific HTTP payload behind a small adapter. Suggested normalized fields:

| Input | Output |
| --- | --- |
| Operation/process/attempt IDs; mode and objective | `completed`, `failed`, `blocked`, `budget_exhausted`, `cancelled`, or `interrupted` |
| Exact base revision and isolated workspace | Provider session/turn IDs when actually exposed |
| Instructions, context/artifact references, expected result schema | Actual runtime/model; bounded answer or typed proposal |
| Tool/permission grant; finite deadline and execution limits | Tool/evidence references; candidate diff and tested revision |
| Explicit continuation policy | Reported usage, errors, and certainty that execution has stopped |

These are proposed host-level fields, not claims that every proxy accepts or returns them. Map each field to a real provider feature or enforce it in the host; otherwise mark it unsupported. A prompt asking for a budget limit is not an enforced limit.

Start with one active attempt and a fresh agent session. Add continuity only for related steps in that attempt. Key sessions by project, attempt, runtime configuration, and instruction version; serialize access. A different task, workspace, or incompatible instruction set starts a fresh session. Store artifacts and explicit context for cross-runtime handoffs rather than assuming hidden Codex state can transfer to a local model.

Disable automatic transport retries for mutating tasks until replay behavior is understood. A disconnected request may still be running. Closing an HTTP connection must not be recorded as confirmed cancellation without evidence that the agent and its commands stopped.

## Acceptance checks before relying on it

- Native tools execute within one submitted task; observed actions match workspace changes.
- Working directory, write scope, network access, and permission behavior match the grant.
- Internal activity is recorded separately from client tool calls; observational events are never executed again by LangGraph.
- Related requests continue the intended session, while unrelated attempts remain separate.
- Failure, quota exhaustion, timeout, and interrupted streams cannot become successful task outcomes.
- Cancellation/restart tests establish whether execution stopped, persisted, or remains uncertain.
- Required output schemas are validated by host code; malformed proposals cannot publish plans or accept work.
- Independent checks run against the exact candidate tree. Agent prose and a successful HTTP status are not acceptance evidence.

Keep the prototype bound to loopback, preserve the scoped sandbox, and keep credentials out of repository artifacts. Enable writes only in the intended task workspace. These controls matter because this endpoint can initiate real commands and edits.

## Evaluation and next decision

Compare the direct Codex baseline with the proxy using the same task, revision, tools, instructions where possible, and permissions. Measure completion quality, latency, usage, tool visibility, continuation, and recovery. Record any proxy-injected prompt changes or event loss.

Label these runs as **agent-job experiments**. Comparing a Codex agent job with a local model under a different harness changes both the model and the execution loop; it cannot isolate model-routing quality. Keep model-inference experiments under a common harness when that is the question being measured.

Adopt the proxy for the prototype only after the checks above pass. Prefer the official SDK/app-server path when compatibility translation prevents reliable permissions, evidence collection, or lifecycle management. No proxy was installed and no subscription inference was consumed for this brief.
