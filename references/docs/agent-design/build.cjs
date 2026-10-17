// Update the existing graph artifacts. The editor infrastructure stays unchanged.
const fs = require('node:fs');
const path = require('node:path');
const nodes = [];
const edges = [];
function n(id,title,subtitle,pipe,row,kind,body,facts,contract={}) {
  nodes.push({id,title,subtitle,x:96+pipe*560,y:108+row*168,kind,body,facts,contract,links:[]});
}
function e(from,to,label,body,payload,kind='flow') {
  edges.push({id:`${from}--${to}`,from,to,label,body,payload,kind});
}

// Left pipe: the senior's strategic cycle, followed by project acceptance.
n('senior_review','Cloud · senior engineer','CLOUD PIPE / STRATEGY',0,0,'cloud',
  'One cloud-model node owns all senior work. Its prompt changes with the invocation reason, rather than creating a separate node for each prompt. INITIAL: receive the user objective, repository snapshot, acceptance criteria, and run limits; interpret the project and propose a first sprint. SPRINT REVIEW: compare planned work with task reports, commits, and test evidence; explain what went well and wrong, revise assumptions, and assign the next sprint. SPECIALIST TASK: occasionally solve an explicitly assigned difficult problem using the same bounded tool and evidence contracts as the local worker. COMPLETION REVIEW: decide whether project-level verification is justified. The first model inference in a new run is always here.',[
    'Think of this model as the senior engineer and the sprint meeting. It is called at sprint boundaries or concrete exceptions, not after every local action.',
    'A planning response contains a short sprint goal and scoped work items: task ID, dependencies, base revision, allowed tools, instructions, acceptance checks, local/cloud role, and attempt limits.',
    'Review prompts receive a bounded retrospective packet with successful/failed work, observations, tests, checkpoint SHAs, unresolved risks, queue state, and remaining resources; full traces remain retrievable artifacts.',
    'Review, planning, difficult-task execution, and completion use modes of this same node. A single response can review the previous sprint and plan the next.',
    'The common inference gateway enforces context fit, sharing policy, endpoint health, retries, usage accounting, and reserved cloud budget. Required cloud access that is unavailable pauses or stops the run honestly.'
  ],{input:'invocation_reason: initial | sprint_review | plan_correction | specialist_task | specialist_observation | specialist_repair | completion_review; objective; evidence_refs; remaining_budget',
      output:'sprint plan + retrospective | bounded specialist action/candidate | completion_candidate | blocked'});

n('queue','Sprint task queue','CLOUD PIPE / ASSIGNMENTS',0,1,'store',
  'Host code validates the senior plan and atomically publishes a versioned sprint queue. It checks scopes, dependencies, acceptance checks, tools, and budgets before any assignment can run. Dispatch one ready local item without consulting another model. Each dispatch acquires an atomic lease and the writer lock, records a base SHA, prepares an isolated task branch and scoped context, and resets that task\'s mini-agent allowance. Keep the longer-term backlog separate from this short sprint.',[
    'Queue states: queued, ready, leased, passed, failed, blocked, cancelled, and superseded. Dependencies unblock only after host-accepted success.',
    'Start with one active repository writer and one local endpoint serving sequential assignments. Concurrent juniors require isolated worktrees and explicit integration.',
    'A cloud-only difficult assignment is deliberate, leased, and budgeted; it is dispatched to the same senior node in specialist mode.',
    'An empty or stalled queue with no live lease requests a meeting. If a worker is still active, await its result instead.',
    'Reject an invalid plan and request a bounded correction from the senior; do not silently widen tool authority or switch the assigned model role.'
  ],{input:'validated work_items[], sprint_goal, plan_version, review_triggers',
      output:'leased task contract + task_id/attempt_id + branch/base_sha + prepared context, or no-ready-work reason'});

n('event_gate','Sprint coordinator','CLOUD PIPE / HANDOFF',0,2,'host',
  'The host ingests each result, verifies its report and commit against recorded evidence, and integrates only accepted successful work into the sprint branch. Then it makes the cheap routing decision: dispatch another ready task while the sprint remains healthy, or reconvene the senior when the queue is exhausted/stalled, a bounded attempt fails, assumptions change, or integration regresses. This is an event-driven agile cadence, not a weekly timer.',[
    'Ordinary accepted task completion does not call the cloud: update dependencies and return to the queue.',
    'A sprint meeting is a deduplicated event. Assemble what was planned, what passed/failed, causes, commits, checks, remaining work, and resources for the senior to review.',
    'Keep failed checkpoint commits on their task branches. Never promote failed work or release dependent tasks merely because a commit exists.',
    'If integration changes a tested tree, rerun relevant checks before accepting its evidence.',
    'Deterministic rules decide normal handoffs. A reserved, bounded senior call may classify an ambiguous exception; no paid supervisor runs on every worker step.',
    'All states use the durable run/operation ledger. Recover uncertain effects and stale leases before resuming; checkpoints do not undo filesystem or tool effects.'
  ],{input:'result packet + verified commit/tree + integrated revision + queue/dependency state',
      output:'continue_sprint | review(reason, retrospective_packet) | paused/terminal_stop'});

n('final','Project acceptance','CLOUD PIPE / DELIVERY',0,3,'host',
  'After the senior proposes completion, run the independent integration/regression checks required by the project against the integrated tree using the shared guarded tool runtime. Complete the project only when both the senior decision and current host evidence support it. Failed integration returns to the senior with concrete evidence for the next sprint. Also persist truthful blocked, budget_stopped, failed, or cancelled outcomes when the coordinator stops the run; these do not imply project success.',[
    'An exhausted sprint queue triggers a retrospective; it is not project completion.',
    'Task-level success does not prove the combined system works. Unavailable or stale required checks cannot yield completed.',
    'Persist integrated commit references, checks, unresolved backlog/risks, and separate cloud/local resource accounting.',
    'No model call is needed simply to announce a hard budget stop. Resumable interruptions retain their continuation and partial branches.'
  ],{input:'senior completion_candidate + integrated tree + project criteria, OR explicit non-success stop reason',
      output:'completed + final_revision + evidence_refs, OR truthful non-success/paused status'});

// Right pipe: one bounded local agent, tool feedback, checks, and a committed report.
n('local_infer','Local · coding agent','LOCAL PIPE / BOUNDED LOOP',1,0,'local',
  'One local-model node performs each scoped assignment in a mini-swe-agent-style loop. Start with the leased task contract, repository rules, relevant context, and available tools. Propose the next tool action, inspect its returned observation, and repeat for a few bounded steps. A candidate, inability to continue, or exhausted allowance proceeds to host verification. Different task instructions and step prompts are modes of this same worker node, not separate agents.',[
    'Local work includes implementation and tests. It is not restricted to read-only reconnaissance.',
    'Each assignment has a fresh task transcript and explicit step/time/token limits; preserve complete tool-call/result pairs and artifact references when reducing context.',
    'Tool errors and failed checks can be repaired locally while meaningful progress and allowance remain. No cloud review is needed for every ordinary failure.',
    'The worker cannot expand its scope, rewrite sprint dependencies, or grant itself more budget. The host enforces these boundaries.',
    'Malformed outputs receive bounded corrective feedback. Model confidence or a prose success claim never substitutes for check evidence.'
  ],{input:'leased task + scope/base_sha + instructions/tools + observations + remaining task allowance',
      output:'tool proposal | completion_candidate | cannot_complete | budget_exhausted'});

n('execute','Tools & observations','LOCAL PIPE / ACT',1,1,'host',
  'Host code validates the proposed tool and arguments, checks scope/authority and remaining limits, executes approved operations, records their effects and output, and returns a matched observation to the active task model. Use one shared runtime for search, reads, patches, commands, checks, and optional MCP tools. The normal active model is local; an explicitly assigned cloud specialist uses exactly this boundary and receives its own observations.',[
    'Authorization, exact-operation human decisions when required, process/environment isolation, and operation IDs are host responsibilities.',
    'Pair results and denials with their call IDs; spool full output into artifacts and pass a bounded observation to the model.',
    'Record exit codes, timings, usage, mutation metadata, and current tree. Edits invalidate affected evidence.',
    'Tool errors are observations. Repeated errors or no progress close the bounded attempt instead of looping forever.',
    'Inspect ambiguous mutation/timeout outcomes before replay. If effects cannot be established, preserve state and pause.',
    'Task/project verification uses this same guarded runtime internally; it does not need another model call merely to read an exit status.'
  ],{input:'active task/model role + validated tool proposal + operation/input identity',
      output:'paired observation + exit status + output_ref + revision/mutation metadata + updated limits'});

n('verdict','Task verification','LOCAL PIPE / CHECK',1,2,'host',
  'Run the assignment\'s configured acceptance checks through the shared guarded runtime, then compare the recorded evidence with the exact task tree. A meaningful repair may return to the model assigned to this task while its allowance remains. Otherwise close with passed, failed, blocked, or budget_exhausted. This evidence gate is shared by ordinary local tasks and the rare cloud specialist task.',[
    'Record command, availability/status, exit code, output artifact, and checked tree/revision for each test.',
    'No extra reviewer model is required to interpret a configured pass/fail criterion.',
    'Missing required checks, stale evidence, or an unsupported success claim cannot produce passed.',
    'A failed test with repair budget stays inside the task loop; an exhausted or unrecoverable attempt closes and is reported before sprint review.',
    'Retain the assigned model role during repairs. Switching to cloud is a senior assignment decision, not an implicit fallback.'
  ],{input:'candidate or stopping reason + task criteria + exact workspace tree + recorded checks',
      output:'repair observations + remaining allowance, OR verdict + tested_tree_id + evidence_refs'});

n('report','Commit & task report','LOCAL PIPE / RETURN',1,3,'host',
  'Close every finished task attempt with an auditable checkpoint commit and a structured result packet. Commit only scoped changes to the task branch; a no-diff task uses a metadata-only empty commit. This applies to passed, failed, blocked, and budget-exhausted attempts. Record the real SHA before emitting the report, then return it to the sprint coordinator. The model may draft the observation, but host records supply the verdict, test facts, revision, and usage.',[
    'Required packet fields: task/attempt ID, verdict, observation, test results, base SHA, checkpoint SHA, evidence refs, usage, and unresolved issues.',
    'Passed work is only a candidate for integration. Failed or partial work remains reachable on its own branch.',
    'Tie tests to the tested tree ID; a new commit of the identical tree may retain that evidence, while changed content requires new checks.',
    'If Git fails or its outcome is uncertain, reconcile by task/attempt ID and inspect the branch. Do not fabricate a SHA.',
    'A crash before a checkpoint can exist is an interrupted attempt, not a completed task. Resume/reconcile or retain an explicit paused status.'
  ],{input:'closed verdict + scoped tree + tests + task/attempt identity',
      output:'{ task_id, attempt_id, verdict, observation, tests:[{command,status,exit_code,revision,output_ref}], base_sha, commit_sha, evidence_refs, usage, blockers }'});

// Edge bodies are the interaction comments shown by the existing click inspector.
e('senior_review','queue','Sprint planning handoff',
  'The senior turns the objective and retrospective into the next short sprint: a goal, small testable assignments, dependencies, tool scopes, checks, budgets, and explicit meeting triggers. Host code validates the response and atomically replaces or revises the queue. Initial, retrospective, and planning prompts all belong to the same cloud node.',
  'sprint_goal, plan_version, work_items[], review_triggers, remaining cloud reserve');
e('queue','local_infer','Assign the next local task',
  'Like a junior taking the next sprint ticket, the worker receives one ready, leased assignment with a base revision and a clear definition of done. The host acquires the writer lock, prepares the task branch and bounded context, and resets the task allowance. No senior call is needed for ordinary dispatch.',
  'task_id, attempt_id, lease, branch, base_sha, acceptance_checks, tools, scoped prompt, limits');
e('local_infer','execute','Propose a tool action',
  'The local worker chooses its next useful repository action. The host validates the proposal and authority before any effect; model instructions cannot expand the assigned scope. This is one turn of the bounded mini-swe loop, not a new sprint or a new cloud request.',
  'active_role=local, task/attempt ID, call IDs, tool names/arguments, remaining allowance');
e('execute','local_infer','Return the local observation',
  'When the originating task is local, feed matched outputs, errors, exit codes, and revision changes back to that same worker transcript. It can inspect, patch, test, and retry within its small allowance. This is the normal inner loop and does not summon the senior.',
  'paired observations, artifact_refs, workspace tree, mutation flags, usage/counters');
e('local_infer','verdict','Submit candidate or stop attempt',
  'The worker proposes completion, cannot proceed, or reaches its bounded stop condition. Host verification checks the actual task tree even if the model claimed success. Exhaustion records a non-success reason; it does not grant another unbounded model turn.',
  'candidate or stop_reason, task contract, exact tree, prior check records');
e('verdict','local_infer','Repair within the local allowance',
  'A specific failing/missing check can return to the local worker if a justified repair remains within its original task budget. This is a junior fixing their ticket, not a sprint meeting. Exhausted or unrecoverable work instead closes through the checkpoint/report node.',
  'active_role=local, concrete failed-check observations, tree ID, remaining repair/step/time allowance','exception');
e('verdict','report','Close with an evidence-backed verdict',
  'Host checks resolve passed, failed, blocked, or budget_exhausted. Every closed attempt proceeds to the same checkpoint/report contract, regardless of which model performed the work. A failure remains a failure even though its partial work gets a commit.',
  'verdict, tested_tree_id, check records, evidence_refs, blockers, usage');
e('report','event_gate','Return the completed ticket',
  'The worker returns its verdict, observation, test results, and real Git checkpoint SHA to the sprint coordinator. The host verifies the packet, integrates only accepted success, preserves failed branches, updates dependency readiness, and decides whether the sprint can continue. This is the principal return handoff between the two pipes.',
  'task result packet, checkpoint/base SHAs, tested tree, integrated revision or rejection reason');
e('event_gate','queue','Keep the sprint running',
  'After an accepted result, continue with the next ready assignment when the sprint remains healthy. Dependency updates and dispatch are programmatic. The senior remains idle while juniors can productively execute the agreed queue.',
  'accepted task status, updated dependencies/queue, integrated base revision, remaining resources');
e('queue','event_gate','No ready assignment remains',
  'If no task is runnable, inspect live leases before declaring exhaustion. Await any active worker. If no worker is active, distinguish a completed sprint queue from a dependency stall and let the coordinator request the appropriate retrospective. Queue exhaustion alone never means the entire project is complete.',
  'queue_empty | dependency_stall, live leases, pending/finished/failed task IDs');
e('event_gate','senior_review','Reconvene the sprint meeting',
  'Call the senior when the queue runs out or stalls, a task has failed beyond its repair allowance, assumptions are invalidated, or integration regresses. Send one deduplicated retrospective packet: planned versus actual work, what went well/wrong, observations, tests, commits, unresolved work, and resources. The senior adjusts strategy and replenishes the next sprint; ordinary local tool failures do not cause this edge.',
  'mode=sprint_review, review_reason, sprint evidence, task packets, queue state, budget/latency ledger','exception');
e('senior_review','final','Propose project acceptance',
  'After reviewing the latest sprint evidence and remaining backlog, the senior may judge that the user objective is satisfied. The project acceptance node still runs independent checks against the integrated tree. A cloud opinion alone cannot mark the project completed.',
  'mode=completion_review, completion_candidate, rationale, acceptance matrix, integrated revision');
e('final','senior_review','Integration needs another sprint',
  'Independent project checks fail or required acceptance evidence is unavailable. Return the exact integrated revision, failing commands, output artifacts, and unresolved criteria to the senior so the next sprint targets the actual gap. If a required resource or budget prevents review, retain an honest paused/non-success outcome.',
  'mode=sprint_review, reason=integration_failure, project check evidence, final tree, remaining resources','exception');
e('event_gate','final','Record a non-success stop',
  'A hard run limit, cancellation, unrecoverable policy/endpoint problem, or explicit blocked outcome can end or pause the run without another paid model call. This branch records partial work and evidence; it never follows the successful-completion path merely because time or money ran out.',
  'explicit failed | blocked | budget_stopped | cancelled | paused status, partial branches, evidence, continuation','exception');
e('queue','senior_review','Rare senior assignment or plan correction',
  'Normally the queue feeds local work. Exception 1: the senior explicitly reserved a hard ticket for itself; lease it with the same ownership contract and invoke the existing cloud node in specialist_task mode. Exception 2: a proposed plan fails host validation; return structured errors in plan_correction mode under a bounded correction allowance. These reasons select different prompts inside the same cloud node.',
  'invocation_reason=specialist_task with leased task contract, OR plan_correction with validation errors','exception');
e('senior_review','execute','Senior specialist tool action',
  'Only when an explicitly assigned difficult task needs tools, let the senior propose a bounded action through the exact same guarded runtime as the local worker. This is exceptional hands-on senior work, not a second permanent worker or a critic of each local action.',
  'active_role=cloud_specialist, leased task/attempt, tool proposal, reserved step/spend limits','exception');
e('execute','senior_review','Return the specialist observation',
  'If the originating task role is cloud_specialist, return the paired tool result to the same cloud node in specialist_observation mode. Preserve its task identity and tight budget. Local-originated observations instead return exclusively to the local node.',
  'mode=specialist_observation, paired results/artifact refs, tree ID, remaining specialist allowance','exception');
e('senior_review','verdict','Senior specialist candidate',
  'A completed or exhausted senior-only assignment uses the same independent task checks, verdict, commit, and report path as a local assignment. Its result will reach the coordinator rather than being accepted merely because the stronger model produced it.',
  'active_role=cloud_specialist, task candidate or stop reason, exact tree, usage/trace refs','exception');
e('verdict','senior_review','Repair the assigned senior task',
  'Only for an already cloud-assigned specialist task with a justified remaining repair allowance, return concrete check failures to the same senior node in specialist_repair mode. A local task does not take this edge by itself; escalation closes its attempt and goes through sprint review and an explicit new assignment.',
  'mode=specialist_repair, existing task identity, failing-check evidence, remaining reserved budget','exception');

for(const node of nodes) {
  if(['local_infer','execute'].includes(node.id)) node.links.push(['../mini-swe-agent/src/minisweagent/agents/default.py','mini-swe-agent loop']);
  if(['queue','event_gate'].includes(node.id)) node.links.push(['deepagents-agent-handbook.md','Deep Agents study']);
  if(['execute','senior_review'].includes(node.id)) node.links.push(['claude-code-agent-handbook.md','Claude Code study']);
}
const graph={schema:'polyinference.diagram.v2',version:2,documentId:'polyinference-sprint-v1-revision2',title:'Polyinference · two-pipe sprint architecture',description:'Two vertical pipes: cloud strategy and local execution, connected by sprint assignments and evidence-backed reports.',nodes,edges};
const dir=path.resolve(__dirname,'..');
fs.writeFileSync(path.join(dir,'polyinference-agent-structure-v1.json'),JSON.stringify(graph,null,2)+'\n');
const template=fs.readFileSync(path.join(__dirname,'editor.html'),'utf8');
fs.writeFileSync(path.join(dir,'polyinference-agent-v1.html'),template.replace('__GRAPH_DATA__',JSON.stringify(graph).replace(/</g,'\\u003c')));
console.log(`Updated existing graph: ${nodes.length} nodes, ${edges.length} edges.`);
