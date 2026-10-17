"""Editorial projection of the audited designs; illustrative, not runtime state."""

AGENT = "../langgraph-agent/README.md"
OS = "../simplified-os/README.md"
AUDIT = "../INTEGRATION_AUDIT.md"


def node(title, brief, purpose, inputs, outputs, rules, question, source, tag="Application", tone="neutral"):
    if not all(isinstance(items, list) for items in (inputs, outputs, rules)):
        raise TypeError(f"{title}: inputs, outputs and rules must be lists")
    if tone not in {"neutral", "cloud", "local", "gate"} or not source.startswith("../"):
        raise ValueError(f"{title}: invalid visual category or source reference")
    return dict(title=title, brief=brief, purpose=purpose, inputs=inputs, outputs=outputs,
                rules=rules, question=question, source=source, tag=tag, tone=tone)


def edge(a, b, label="", **kwargs):
    return dict(a=a, b=b, label=label, **kwargs)


def diagram(label, title, description, positions, edges, initial, footnote):
    return dict(label=label, title=title, description=description,
                positions=[dict(id=i, row=r, col=c) for i, r, c in positions],
                edges=edges, initial=initial, footnote=footnote)


def question(qid, title, why, inspect, source):
    return dict(id=qid, title=title, why=why, inspect=inspect, source=source)


AGENT_NODES = {
    "input": node("Objective & steering", "Ordered user input", "Persist the objective and later instructions without silently rewriting a running assignment.",
        ["User objective, acceptance criteria and run limits", "Later steering with a monotonic input sequence"],
        ["Pinned objective and criteria", "Durable steering barrier and captured worker set"],
        ["Receipt closes new coding starts atomically with worker claiming.", "Captured started workers keep their original instructions; pending unstarted tasks stay pending.", "A later message stays pending until a planner actually consumes its input range."],
        "Can a message arrive during review without being lost or acknowledged early?", AGENT + "#11-steering-and-recovery"),
    "controller": node("Sprint controller", "Deterministic control flow", "Host code coordinates sprints, dispatch, review barriers and project acceptance. Ordinary routing does not spend a model call.",
        ["Run/plan versions and durable events", "Reports, dependency states, steering and remaining budget"],
        ["Worker claims and senior queries", "Validated plan activation or guarded project outcome"],
        ["The default first model call is senior initial planning.", "Ordinary review closes starts and drains existing workers before pinning its packet.", "Keep receiving input, status and completion events while a query or worker waits."],
        "Are all branches driven by authoritative records rather than model prose?", AGENT + "#41-sprint-controller", "Host control"),
    "senior": node("Senior-query graph", "Plan, review, correct", "One reusable senior role changes prompt mode for initial planning, sprint review, corrections and completion review.",
        ["Pinned head, reports, steering range and expected plan", "Bounded context, output schema and query budget"],
        ["Typed proposal for a plan, dispositions or completion", "A separately recorded blocked/invalid response when necessary"],
        ["The reference binding is cloud; another feasible static map may be pinned before an experiment.", "A proposal cannot directly mutate authoritative state.", "A stale result cannot acknowledge unseen input or retarget a revert."],
        "Is senior review based on a stable, complete packet with explicit version checks?", AGENT + "#43-senior-queries-and-specialists", "Cloud default", "cloud"),
    "ledger": node("Task ledger", "Claims, dependencies, attempts", "The application stores scoped immutable assignments and tracks execution independently of senior acceptance.",
        ["Validated plan and TaskSpecs", "Dependency dispositions, concrete inputs and immutable base B"],
        ["One atomic claim per attempt", "Bounded worker process and private workspace setup"],
        ["A claim counts against W from setup onward.", "Resolve prerequisites before starting; publication alone does not satisfy a kept/reviewed dependency.", "Changed base or scope needs a superseding spec and linked attempt."],
        "Can two claimants or a steering race create an unauthorized duplicate worker?", AGENT + "#41-sprint-controller"),
    "worker": node("Coding-worker graph", "Bounded private implementation", "Independent invocations reuse one worker graph. Each has its own context, assignment, budget and private scoped code copy.",
        ["Immutable TaskSpec, original B and allowed writes", "Pinned context, model binding and final-phase reserve"],
        ["Scoped actions and paired observations", "Candidate for verification or a parked exception"],
        ["Ordinary workers use local inference in the reference map; specialists use the same protocol.", "Every shell command takes the global shell permit.", "The three phases are development, reconciliation and assessment."],
        "Can the worker stop honestly when scope, evidence or allowance is insufficient?", AGENT + "#42-coding-worker", "Local default", "local"),
    "publication": node("Commit & unresolved report", "Publish before releasing the gate", "Every normal assessed verdict publishes an attributable commit and immutable unresolved report into provisional history.",
        ["Current verification owner, captured H and final assessed tree", "Real commit P, verdict, evidence, hazards and expected versions"],
        ["Provisional head = P, with sole parent H", "Visible report + durable receipt + event intents, atomically"],
        ["successful, fail and uncertain all publish; publication is not senior acceptance.", "A private Git commit alone is insufficient. Read the committed receipt before normal closure.", "Unfinished assessment is retained as interrupted work, without an invented verdict."],
        "Does the next verifier see the actual published predecessor and its hazards?", AGENT + "#10-publication-and-review", "Protected phase", "gate"),
    "context": node("Context & documentation", "Pinned, attributed continuity", "Keep per-process histories, versioned notes/hazards and a durable documentation backlog without a shared mutable transcript.",
        ["Source-linked notes, actions, observations and report/disposition events", "Pinned memory/doc versions and bounded retrieval needs"],
        ["A bounded ContextView with complete ordered tool pairs", "Documentation tasks and atomic doc-version/cursor publication"],
        ["A summary is derived continuity, not acceptance evidence or a new user instruction.", "Exact criteria, current diff and unresolved effects remain available.", "Rich tiers, vector retrieval and autonomous consolidation are future extensions."],
        "Can you trace a claim to its code revision and source without trusting a summary?", AGENT + "#8-multi-stage-memory-and-documentation"),
    "resolution": node("Senior resolution", "Keep · revert · retry · defer", "Apply senior decisions separately from worker verdicts. Acceptance concerns the resulting combined revision.",
        ["Senior proposal against a pinned report/head range", "Original commits, later dependencies and blast-radius evidence"],
        ["Immutable resolution records and follow-up assignments", "Serialized inverse commits when code must be removed"],
        ["Keep accepts already-published code; retry/defer do not remove it.", "Revert acquires verification, checks the resulting tree and journals its own head update.", "A partial disposition batch recovers one receipt at a time before activating the next plan."],
        "Could a revert break later work, or wrongly advance review past unresolved ancestors?", AGENT + "#10-publication-and-review", "Senior decision", "cloud"),
    "acceptance": node("Project acceptance", "Independent final judgment", "Record completed only for the current accepted project revision, backed by senior intent and independent project checks.",
        ["Matching reviewed/provisional revision and senior completion proposal", "No active coding workers, unresolved contributors, pending steering or relevant uncertain effects"],
        ["A guarded project outcome tied to exact content/environment", "Concrete review issues if checks fail or authority changes"],
        ["Close starts and settle captured workers before taking verification.", "Run required project checks on a complete private view; take shell per command.", "Compare heads, plan, input watermarks and owner when recording completion. New steering invalidates the snapshot."],
        "Can completion race a new message, publication or still-running effect?", AGENT + "#10-publication-and-review", "Protected phase", "gate"),
    "assignment": node("Load assignment", "Private scoped copy at B", "Start only after a tracked claim and successful workspace setup.",
        ["TaskSpec, allowed paths and immutable B"], ["Manifest, generation 1, per-process context"],
        ["Copy assigned files plus necessary read/build/test closure.", "An omitted path is not a deletion and does not prove absence in B."],
        "Is the dependency closure enough for useful private development?", OS + "#6-each-agents-private-part-of-the-code"),
    "development": node("Develop privately", "Reason → act → observe", "Use a bounded local model/tool loop while other workers can do the same.",
        ["Current context and paired observations"], ["Explicit B-relative private delta", "Candidate or needs_review exception"],
        ["One active top-level effect per process; no shared transcript.", "Shell ownership is per command, never across model reasoning.", "Protect the final-phase reserve from ordinary development spending."],
        "Is progress bounded without stealing the allowance needed to close honestly?", AGENT + "#42-coding-worker", "Local reasoning", "local"),
    "gate": node("Acquire verification", "Release outside shell first", "Queue for the project permit only after relevant tool effects are settled and final-phase allowances are viable.",
        ["Preserved development delta and no held outside shell permit"], ["Current fenced project ownership"],
        ["The acquisition order is verification, then shell.", "No metadata lock spans this wait.", "Other eligible inference and control work can keep running."],
        "Can any worker wait for verification while still holding shell?", OS + "#7-mergetestcommit-is-one-critical-section", "Protected phase", "gate"),
    "reconcile": node("Capture H & reconcile", "Complete private integration view", "Materialize the latest provisional H and merge the original B-relative private delta into it.",
        ["Current provisional H, original B and preserved delta"], ["New workspace generation and integrated final-phase tree"],
        ["At least one reconciliation-development turn is mandatory even after a clean merge.", "The full view expands visibility, not write authority.", "Abort retires this view; resume captures fresh H and rebuilds from the original private delta."],
        "Does this worker adapt to incoming semantic changes rather than just clean Git merges?", OS + "#62-delta-and-complete-integration-view", "Protected phase", "gate"),
    "checks": node("Run required checks", "Exact content + environment", "Host tools collect independent evidence for the integrated tree under the worker's assignment.",
        ["Integrated content identity and configured criteria"], ["Passed/failed/unavailable/inconclusive check records"],
        ["Shell is acquired separately for each command.", "A test, formatter or hook changing assessed inputs invalidates affected evidence.", "Partial-copy checks are development feedback, not full-project integration evidence."],
        "Were all required criteria actually checked on the final inputs?", AGENT + "#42-coding-worker", "Protected phase", "gate"),
    "assess": node("Final model assessment", "fail · uncertain · successful", "The assigned model examines the final tree and evidence; host validation constrains the verdict.",
        ["Current check records, exact tree and assessment-mode prompt"], ["Completed assessment with a truthful verdict"],
        ["Definite failed criteria imply fail; missing or inconclusive required evidence implies uncertain.", "A repair returns to reconciliation/development and requires final assessment again.", "Absent assessment means interrupted/assessment-pending, not normal completion."],
        "Can a model explanation override a failed required check? It must not.", AGENT + "#42-coding-worker", "Protected model turn", "gate"),
    "release": node("Release & finish", "Completed, still unresolved", "Close the worker protocol only after reading the durable publication receipt and settling protected work.",
        ["Validated receipt, known-ended effects and cleanup state"], ["Released verification/worker occupancy", "Retained report and recovery artifacts"],
        ["Report acceptance remains unresolved until senior review.", "Retained records use storage limits, not worker execution slots.", "Unknown publication/command outcome retains conflicting ownership."],
        "Is ownership released because the effect ended, rather than because a timer expired?", OS + "#failure-and-abort"),
    "barrier": node("Close new starts", "Review or steering boundary", "Atomically close coding starts and capture workers already claimed, including setup and gate waiters.",
        ["Review trigger or ordered steering receipt"], ["Stable captured set; pending work stays unstarted"],
        ["Ordinary review uses the same conservative sprint boundary.", "Later steering unions still-started workers into the outstanding set."],
        "Does closing starts accidentally prevent captured workers from finishing?", AGENT + "#11-steering-and-recovery"),
    "drain": node("Drain captured workers", "Keep their finish paths open", "Await existing work on its original assignment without holding the gate needed for it to complete.",
        ["Captured process IDs and their durable states"], ["Settled worker outcomes or an explicit interrupted blocker"],
        ["Do not wait for pending unstarted tasks.", "Do not silently cancel a stuck worker or manufacture a report.", "Exception review does not falsely complete the ordinary steering drain."],
        "Can the barrier explain exactly what it is waiting for?", AGENT + "#41-sprint-controller"),
    "plan": node("Activate next plan", "Acknowledge only consumed input", "Activate an immutable validated plan after its review effects are known.",
        ["Reconciled dispositions, expected versions and consumed steering range"], ["New plan pointer and exact acknowledgements"],
        ["Later input remains pending and keeps starts closed.", "Never mutate an executing TaskSpec in place.", "A completion candidate goes through independent project acceptance."],
        "Do plan activation and acknowledgement cover exactly the reviewed range?", AGENT + "#41-sprint-controller"),
}

OS_NODES = {
    "programs": node("LangGraph application", "Controller, workers, senior queries", "A portable application calls explicit runtime ports. LangGraph owns graph transitions and public checkpoint semantics.",
        ["Pinned graph/state/prompt versions and process inputs"], ["ProcessSpecs, bounded model/tool requests and publication intents"],
        ["One current driver per invocation; nodes are not independent processes.", "Runtime clients stay in live context, outside serialized graph state.", "No private LangGraph/Pregel patch is required."],
        "Are all effects explicit and recoverable at public adapter boundaries?", OS + "#9-agent-cooperation-and-additive-langgraph-integration"),
    "kernel": node("Kernel / control plane", "Identity, admission, journal, events", "One small asynchronous coordinator is the authority for operations, reservations, ownership and durable event publication.",
        ["Authenticated caller, grants, pinned versions and bounded intents"], ["Admitted operations or explicit waits/denials", "Durable process/effect state and targeted wakeups"],
        ["Persist intent and fingerprint before dispatch; replay lookup precedes new-dispatch checks.", "Short metadata transactions never span model/tool waits.", "Reserve controller/recovery/senior capacity separately from W."],
        "Can a saturated worker pool or an uncertain effect freeze the control plane?", OS + "#4-processes-and-operations", "Host control"),
    "gateway": node("Inference gateway", "Local + one selected cloud protocol", "Validate binding, data policy, context fit and capacity, then submit/track/cancel/reconcile bounded work.",
        ["ModelQuery or supported AgentJob, context and role policy"], ["Actual backend result, effect certainty and honest usage"],
        ["Role bindings are fixed per run; no automatic provider overflow or model migration.", "Several independent local requests may coexist; the server owns token batching.", "Raw inference and native agent-job execution are different protocols."],
        "Does the selected endpoint enforce the guarantees the adapter advertises?", OS + "#5-scheduling-local-continuous-batching-and-cloud-work"),
    "broker": node("Workspace & tool broker", "Private files, tools, two gates", "Mediate source access, scoped mutations, foreground commands and exact-tree evidence for every managed coding effect.",
        ["Workspace ID, manifest, generation, content preconditions and grant"], ["Scoped observation/change evidence", "Complete integration view and attributable Git objects"],
        ["CWD alone is not isolation; the execution backend must enforce scope.", "Reject escape, Git control access and unauthorized final H-to-P writes.", "Commands and relevant descendants remain owned until known ended."],
        "Can a shell, hook, cache or native job bypass the declared authority?", OS + "#6-each-agents-private-part-of-the-code"),
    "endpoints": node("Shared execution services", "One local model + cloud endpoint", "Reuse model/serving implementations. Local weights are loaded once, not once per agent.",
        ["Admitted bounded generations or compatible native jobs"], ["Independent results, provider/host handles and usage evidence"],
        ["The serving engine controls sequences, prefill/decode and GPU token scheduling.", "Cloud sessions serialize when mutable; account allowance is separate from local capacity.", "Unknown termination retains reservations; closing a transport is not proof of cancellation."],
        "Are capacity and cancellation claims measured or truly enforced?", OS + "#53-cloud-execution"),
    "persistence": node("Persistence & projections", "SQLite · artifacts · Git · saver", "Store authoritative metadata, immutable evidence and graph continuations while keeping their separate consistency domains explicit.",
        ["Claims, effect intents/results, retained artifacts and real Git objects"], ["Atomic metadata heads/reports/receipts/event intents", "Recoverable Git refs, notifications and graph continuation"],
        ["Immutable Git/evidence objects exist before authoritative pointer publication.", "No transaction spans SQLite, Git, the graph saver and a provider.", "A convenient Git ref is a repairable projection; metadata publication is the authority."],
        "Can recovery distinguish a private commit from a committed shared-head receipt?", OS + "#8-minimal-storage-and-state"),
    "ownership": node("Shell & verification ownership", "Independent, ordered permits", "Serialize one shell command installation-wide and one final project phase, without monopolizing all inference.",
        ["Resource key, owner generation, FIFO waiters and protected operations"], ["Fenced ownership, visible wait or reconciled release"],
        ["Order: verification before shell. Never queue for verification while holding outside shell.", "Verification spans capture/merge/reconcile/check/assess/commit/publication.", "Timeout, exception and lease expiry do not establish safe release."],
        "Could a finally block release a gate while a writer is still alive?", OS + "#7-mergetestcommit-is-one-critical-section", "Protected phase", "gate"),
    "workers": node("W · worker residency", "Setup through required cleanup", "Bound resident coding invocations and their host/private-workspace allowance independently of model concurrency.",
        ["Claimed workers, setup, waits and cleanup"], ["Bounded resident work or queued new starts"],
        ["Model/gate waiters still count against W.", "Finished published workers free W even while their reports remain unresolved.", "Controller, recovery and one senior query have separately bounded capacity."],
        "Does retained unresolved history accidentally hold every worker slot?", OS + "#4-processes-and-operations"),
    "local": node("L / E / T · local admission", "Requests, engine sequences, context", "Admit independent local generations while respecting request and conservative context capacity.",
        ["Input tokens + reserved maximum output", "In-flight L, engine capacity E, reserved context T"],
        ["Admitted independent local request or explicit capacity wait"],
        ["Require in-flight < L and total reserved context + request <= T; each sequence must fit.", "This core keeps L <= E; queued-in-engine requests still count.", "Alternate verifier finishing and ordinary lanes when both wait. Do not wait to fill a batch."],
        "Can at least two independent requests overlap without exceeding measured fit?", OS + "#51-independent-limits", "Shared local model", "local"),
    "cloud": node("C · cloud occupancy", "Account, endpoint, session", "Reserve cloud operations independently of local model resources and track real selected-endpoint limits.",
        ["Eligible static binding, account budget and bounded query/job"], ["Admitted cloud call or bounded wait/stop"],
        ["A strict senior call waits when required cloud access is unavailable.", "A native job remains active while brokered subordinate callbacks execute.", "An estimated subscription percentage is not an exact enforced token reservation."],
        "Can the account limit and true cost bound be known or enforced?", OS + "#53-cloud-execution", "Cloud endpoint", "cloud"),
    "shell": node("Shell · capacity 1", "One command + relevant descendants", "Protect every managed shell/script command, including Git, tests and compatible native-job tools.",
        ["Authorized foreground command and current workspace generation"], ["Paired output/effects and confirmed completion, or uncertainty"],
        ["Take the permit separately per command.", "Do not hold shell during model reasoning.", "No unmanaged background services or undeclared shared mutations."],
        "Are descendants and shared caches accounted for beyond command launch?", OS + "#7-mergetestcommit-is-one-critical-section", "Protected effect", "gate"),
    "verification": node("Verification · capacity 1", "The complete final phase", "Own the project from before capturing provisional H through durable publication, or a reconciled explicit abort.",
        ["No pending conflicting tool effects, saved delta, viable final-phase reserve"], ["Serialized final tree, evidence, P and publication receipt"],
        ["Retain during inference waits, but do not reserve the whole local model.", "Senior revert and final project acceptance also use this gate.", "Never wait for another worker's entry or senior review while holding it."],
        "Are gate hold time and final-phase feasibility bounded?", OS + "#7-mergetestcommit-is-one-critical-section", "Protected phase", "gate"),
    "memory": node("Memory & bounded storage", "Per physical domain", "Fit the service, active inference/KV, host state, tools and headroom without double counting.",
        ["Measured RAM/VRAM domains and conservative backend/token capacity", "Bounded prompt/output/workspace/artifact sizes"],
        ["Admitted vector of simultaneous resource needs", "Pinned live inputs and retained recovery evidence"],
        ["Count shared model residency once; do not add discrete VRAM to RAM.", "Token admission is approximate unless the backend enforces the reservation.", "Retained evidence/storage limits are separate from execution-slot limits."],
        "What measured capacity basis supports the selected W/L/context limits?", OS + "#51-independent-limits"),
    "intent": node("Prepare stable intent", "Process + logical step → operation", "Map a logical effect to one stable identity and semantic fingerprint before dispatch.",
        ["Authenticated process/step, request and expected versions"], ["Durable PREPARED intent and simultaneous reservations"],
        ["A retried node reuses this mapping.", "Changed intent under the same ID is rejected.", "A deliberate repair advances the logical step."],
        "Can an interrupted node mint a second ID for the same intended action?", OS + "#4-processes-and-operations"),
    "submitting": node("Mark submitting", "Persist before sending", "Record the dispatch boundary before contacting a tool/provider.",
        ["Prepared intent and current new-dispatch authority"], ["Submitted handle, result or visibly ambiguous outcome"],
        ["There is no atomic transaction across a provider and metadata.", "A crash after send may be ambiguous before a provider ID is known."],
        "What can you prove after a disconnect immediately following send?", AGENT + "#11-steering-and-recovery"),
    "active": node("Track active effect", "Waiting still consumes resources", "Yield graph control while retaining resources that the external operation still uses.",
        ["Host/provider IDs and actual progress"], ["Known result or uncertainty requiring reconciliation"],
        ["Progress is not completion.", "Cancellation is a request until termination is confirmed.", "Top-level jobs retain cloud occupancy through subordinate callbacks."],
        "Does waiting release only the host coroutine, or incorrectly release an active resource?", OS + "#4-processes-and-operations"),
    "uncertain": node("Retain uncertainty", "Keep conflicting exclusion", "Do not guess that a timed-out effect stopped, failed or never happened.",
        ["Disconnect/timeout/crash and retained original intent"], ["Visible uncertain state, owners, reservations and diagnostics"],
        ["No automatic blind retry of ambiguous mutations.", "Do not unlock because a permit expired or the graph raised.", "Preserve partial evidence without inventing an assessed verdict."],
        "Can the system expose the blocker and still accept status/cancel/input?", OS + "#failure-and-abort", "Retained ownership", "gate"),
    "recover": node("Reconcile & restore", "One current coordinator / driver", "Fence stale writers, inspect the journal and external evidence, then choose a known continuation.",
        ["Durable journal, descendants, Git objects and publication receipt"], ["Original retained result, safe continued supervision or explicit reconciled abort"],
        ["A found publication receipt returns the original commit, never a second undo unit.", "After abort, retire the integration generation and rebuild at fresh H from the original private delta.", "Pinned incompatible program versions do not silently resume."],
        "Can old and restarted drivers both keep writing?", OS + "#10-steering-recovery-and-progress"),
    "settled": node("Settle once", "Known effects, honest usage", "Commit a reconciled result and release only resources known to be unused.",
        ["Confirmed terminal outcome and measured/estimated/unknown usage"], ["Retained original result and deduplicated journal settlement"],
        ["Duplicate delivery settles journal accounting once.", "Actual provider executions remain billable; no exactly-once billing promise.", "Replay returns this result even after old workspace/permit generations change."],
        "Can settlement lose usage or rerun an effect because the current view changed?", OS + "#4-processes-and-operations"),
}

for component in OS_NODES.values():
    if component["tag"] == "Application":
        component["tag"] = "Runtime component"
OS_NODES["programs"]["tag"] = "Application"
OS_NODES["endpoints"]["tag"] = "Execution backend"

AGENT_MAPS = [
    diagram("Whole agent", "A sprint loop with three reusable graphs", "Senior queries propose. The controller validates. Independent workers implement and return evidence.",
        [("input",0,0),("controller",0,1),("senior",0,2),("ledger",1,0),("worker",1,1),("publication",1,2),("context",2,0),("resolution",2,1),("acceptance",2,2)],
        [edge("input","controller"),edge("controller","senior",both=True),edge("controller","ledger","validated plan"),edge("ledger","worker"),edge("worker","publication"),edge("publication","resolution","unresolved report",data=True),edge("resolution","acceptance"),edge("context","worker","pinned context",data=True,targetOffset=-0.28)], "controller",
        "Arrows show principal handoffs, not every control transition. Review returns through the controller and senior-query graph."),
    diagram("Worker phases", "From a private delta to a durable shared result", "Read left → right, then follow the next row back. Verification stays held from acquisition through publication, including model assessment.",
        [("assignment",0,0),("development",0,1),("gate",0,2),("reconcile",1,2),("checks",1,1),("assess",1,0),("publication",2,0),("release",2,1)],
        [edge("assignment","development"),edge("development","gate"),edge("gate","reconcile"),edge("reconcile","checks"),edge("checks","assess"),edge("assess","publication"),edge("publication","release")], "reconcile",
        "Repairs repeat reconciliation/checks/assessment. needs_review parks a bounded exception after safe effect settlement; it does not fabricate a report."),
    diagram("Review boundary", "Finish existing work before changing its instructions", "The barrier closes starts, not the finish paths of workers already captured. Review holds no worker verification gate.",
        [("barrier",0,0),("drain",0,1),("senior",0,2),("resolution",1,2),("plan",1,1),("acceptance",1,0)],
        [edge("barrier","drain"),edge("drain","senior"),edge("senior","resolution"),edge("resolution","plan"),edge("resolution","acceptance","completion path",route="below")], "barrier",
        "Either activate a next plan or pursue guarded project acceptance. Later steering stays pending; an exception review cannot falsely acknowledge a blocked drain."),
]

OS_MAPS = [
    diagram("Four modules", "A small runtime between the agent and effects", "The application uses portable ports. The OS admits and journals effects; existing backends execute them.",
        [("programs",0,1),("kernel",1,1),("gateway",1,0),("endpoints",2,0),("broker",1,2),("ownership",2,2),("persistence",2,1)],
        [edge("programs","kernel"),edge("kernel","gateway"),edge("kernel","broker"),edge("gateway","endpoints"),edge("kernel","persistence","journal",data=True),edge("broker","ownership")], "kernel",
        "Persistence is shared by kernel and broker. The shell and verification permits are application ownership, not long database locks."),
    diagram("Independent limits", "Worker count is not model concurrency", "Inspect each limit separately. W, L/E/T, C and the two permits constrain different lifetimes.",
        [("workers",0,0),("local",0,1),("cloud",0,2),("verification",1,0),("shell",1,1),("memory",1,2)], [], "local",
        "These are independent constraints, not a linear pipeline. Example capacities in execution stories are illustrative, not deployment recommendations."),
    diagram("Effects & recovery", "Durable intent surrounds every external effect", "Normal work reaches a known result. Ambiguous work keeps ownership and enters explicit reconciliation.",
        [("intent",0,0),("submitting",0,1),("active",0,2),("uncertain",1,1),("recover",1,0),("settled",1,2)],
        [edge("intent","submitting"),edge("submitting","active"),edge("active","settled"),edge("active","uncertain","ambiguous"),edge("uncertain","recover"),edge("recover","settled","known outcome",route="below")], "uncertain",
        "No exactly-once guarantee is assumed at arbitrary providers. Recovery preserves the original operation, receipt and actual billable usage."),
]

AGENT_REVIEW = [
    question("A01","Is the controller deterministic where it should be?","Ordinary routing should not need an extra supervisory inference after every tool result.","Trace initial planning, ready dispatch, a blocked dependency and an exhausted queue. Each branch should use records/policy and reserve senior calls for actual planning/review.",AGENT+"#41-sprint-controller"),
    question("A02","Can every worker finish honestly within its grant?","A worker may consume its allowance before the mandatory final phases, or confuse interrupted work with assessed failure.","Check final-phase reserves, maximum repair loops, scope exceptions and the needs_review exit. No final assessment means no normal TaskReport.",AGENT+"#42-coding-worker"),
    question("A03","Does reconciliation inspect semantic changes?","A clean merge can still break assumptions across workers.","Require a development turn after capturing H. Check full integration evidence, incoming hazards and renewed checks after any repair.",OS+"#62-delta-and-complete-integration-view"),
    question("A04","Are verdict, publication and acceptance separate?","A successful local verdict is not senior acceptance, and fail/uncertain code still enters provisional history under this design.","Follow all three assessed verdicts to a real commit, unresolved report and durable receipt. Verify dependency gating and senior dispositions.",AGENT+"#10-publication-and-review"),
    question("A05","Can steering and review coexist without revoking workers?","Changing a plan while captured workers run can invalidate their authority or strand the drain.","Inject input during setup, gate wait, senior query and acceptance. The captured set finishes original instructions; only consumed input is acknowledged.",AGENT+"#11-steering-and-recovery"),
    question("A06","Can senior undo preserve later work?","A Git inverse may conflict with semantic/build dependencies created by later commits.","Inspect blast-radius analysis, resulting-tree checks and independent head-update receipts. retry/defer must not silently remove already-published code.",AUDIT),
    question("A07","Can project completion race anything?","A passing old snapshot is insufficient when input, workers or provisional history changes.","Inspect the atomic completion guard: equal reviewed/provisional heads, no active coding work or uncertain effects, no unresolved contributors/pending input, current owner and exact required checks.",AGENT+"#10-publication-and-review"),
    question("A08","Does the experiment isolate model placement from harness changes?","A lower cloud token count can hide extra repairs, latency or a different harness.","Keep objectives/trees/criteria and harness comparable. Confirm feasible static role policies, and measure accepted outcomes, total usage, latency, merge cost and assessment calibration.",AGENT+"#12-evolution-and-first-build"),
]

OS_REVIEW = [
    question("O01","Is runtime authority impossible to bypass?","A prompt or path label cannot enforce filesystem, account or tool authority.","Trace every model/tool/Git/native-job effect through authentication, grant, current generation and content checks. Test source writes, Git metadata, hooks and shared caches.",OS+"#6-each-agents-private-part-of-the-code"),
    question("O02","Do separate resource limits match actual lifetimes?","Worker residency, queued-in-engine requests, cloud sessions and model weights consume different resources.","Check W/L/E/T/C plus shell/verification. Require measured per-domain fit and conservative token accounting. Waiting must retain genuinely occupied resources.",OS+"#51-independent-limits"),
    question("O03","Does concurrency actually reach one shared model?","A global graph/client lock can serialize requests despite a configured worker pool.","Demonstrate two independent bounded local requests in flight on one resident service, independent result delivery and no batch-fill barrier.",OS+"#52-dispatch-policy"),
    question("O04","Can the two gates deadlock or release early?","Shell-to-verification inversion and unknown descendants can invalidate both liveness and exclusion.","Force verification → shell order, bounded phase work, FIFO queues and owner progress. Keep control/senior capacity usable. No timeout/finally-only unlock.",OS+"#7-mergetestcommit-is-one-critical-section"),
    question("O05","Are partial workspaces faithfully attributed?","Omitted files, conflicting renames or stale views can delete or overwrite unrelated work.","Prove absence in B for adds/rename destinations, authorize both rename endpoints, preserve the original delta, validate H-to-P scope and reject retired generations.",OS+"#62-delta-and-complete-integration-view"),
    question("O06","Is recovery safe at every dispatch/publication boundary?","Graph checkpoints do not atomically persist provider effects, Git and metadata.","Crash before send, after send, after Git commit and after record publication. Recover the original operation/receipt or retain visible uncertainty. Rebuild aborted integration at fresh H.",OS+"#failure-and-abort"),
    question("O07","Does the cloud adapter implement the real protocol?","API-compatible text does not prove native tool execution, bounded jobs or confirmed cancellation.","Pin the actual raw-inference or native-job adapter. Check phase control, callback ancestry, workspace brokerage, output schema and cost/cancellation guarantees. Reject opaque coding jobs.",OS+"#53-cloud-execution"),
    question("O08","Will the first build remain small and measurable?","Optional interface fields can accidentally turn the core into a general platform before the main guarantees work.","Keep the four modules, one local service, one cloud protocol, direct tools and plain records. Defer MCP lifecycle, weighted routing, tiered memory, migration and distributed coordination.",OS+"#1-scope-and-authority"),
]

def story(title, source, definitions, **initial):
    state = dict(controller="Ready", A="Not started", B="Not started", C="Not started", w=0, l=0, cloud=0,
                 shell="—", verifier="—", provisional="H0", reviewed="H0", starts="Open", reports="None",
                 journal="—", received=0, applied=0)
    state.update(initial)
    frames = []
    for item in definitions:
        state.update(item.get("state", {}))
        frames.append(dict(item, state=dict(state)))
    return dict(title=title, source=source, frames=frames)


def event(title, agent, os, rule, **state):
    return dict(title=title, agent=agent, os=os, rule=rule, state=state)


STORIES = {
    "normal": story("Two workers → reviewed project", OS+"#7-mergetestcommit-is-one-critical-section", [
        event("Senior planning is the first inference","The controller asks the senior for a scoped first sprint. The response is a proposal, not direct task authority.","The gateway admits one cloud query. No worker slot or local inference slot is consumed by planning.","The controller stays responsive while senior inference waits.",controller="Awaiting initial senior proposal",cloud=1,journal="active"),
        event("Claim two private workers","A validated plan creates A and B with separate assignments, context and private scoped copies at immutable B = H0.","Atomic claims reserve two worker slots. Workspace setup is tracked before either invocation becomes ready.","A worker is in progress from claim/setup, not just when its model starts.",controller="Dispatching eligible work",A="Development · scoped view at H0",B="Development · scoped view at H0",w=2,cloud=0,journal="settled"),
        event("Both local generations overlap","The independent worker graphs each await their own model result. Their histories remain separate.","Two bounded requests coexist on one shared local model service. The engine batches tokens; the OS reserves request/context capacity.","W and L are different limits; never hold a global graph/client lock across generation.",A="Local generation active",B="Local generation active",l=2,journal="active"),
        event("A captures H0; B keeps working","A preserves its private delta, takes verification, builds the complete H0 view and starts mandatory reconciliation. B can continue private development.","Verification belongs to A. One A generation uses L; B's private edit needs neither model capacity nor the global shell permit.","Verification protects the final phase, not exclusive use of all inference.",A="Reconciliation · full view of H0",B="Private scoped edit",l=1,verifier="A",journal="active"),
        event("A runs integrated checks","The worker checks the integrated tree through guarded tools. Earlier partial-copy checks are only development feedback.","A takes shell for this check while retaining verification. Local request occupancy is zero after its generation ended.","Shell is per command and is never held across model reasoning.",A="Required integrated check active",B="Private search / read",l=0,shell="A",journal="active"),
        event("A completes final assessment","After checks, the assigned model assesses the final exact tree. Host validation accepts a successful verdict only with current sufficient evidence.","The assessment generation has ended and shell is free. A retains verification until commit and durable publication finish.","Any repair or assessed-input change requires renewed checks and final assessment.",A="Assessment complete · successful",shell="—",journal="settled"),
        event("P1 publishes unresolved","A creates real P1 with sole parent H0, then atomically publishes P1 plus its report, receipt and event intents. Senior acceptance has not happened.","Git/evidence objects precede the metadata transaction. A still owns verification until it validates the committed receipt.","Every normal assessed verdict publishes provisionally, including fail and uncertain.",A="Published P1 · unresolved",provisional="P1",reports="A unresolved",journal="settled"),
        event("B receives P1, not H0","After A's receipt and release, B acquires verification and reconciles against the updated provisional head P1, with A's unresolved provenance.","A's worker slot is released after known cleanup. B now owns verification and a bounded local reconciliation request.","Unresolved reports retain storage, not completed workers' execution slots.",A="Finished · report retained",B="Reconciliation · full view of P1",w=1,l=1,verifier="B",journal="active"),
        event("B publishes P2 after its final phases","B has completed its own reconciliation, checks and assessment. P2 is parented on P1 and the second report remains unresolved.","The second Git/evidence preparation and atomic publication have ended. B validates the receipt before releasing its permit.","Publication is a serialized chain H0 → P1 → P2; task verdicts remain separate from review.",B="Published P2 · unresolved",l=0,provisional="P2",reports="A + B unresolved",journal="settled"),
        event("Drain, then senior review","Both workers have finished and starts are closed. The senior sees a pinned P2 packet and proposes dispositions and whether completion checks are justified.","No worker or verification slot is held. The separately bounded senior query uses one cloud operation.","Never await senior review while holding the worker's verification permit.",controller="Review barrier · pinned P2 packet",B="Finished · report retained",w=0,cloud=1,verifier="—",starts="Closed",journal="active"),
        event("Accept only the checked resulting revision","The senior keeps the contributions. Independent project checks have completed at P2; the final comparison confirms no active worker, pending input or uncertain effect before recording completed.","Reviewed and provisional both identify P2. Verification protects the acceptance comparison; shell/check effects are already settled. The owner releases after the committed outcome.","A senior completion proposal and task-level success cannot replace current project evidence.",controller="Guarded project completion at P2",cloud=0,verifier="Acceptance",reviewed="P2",reports="A + B kept",journal="settled"),
    ]),
    "steering": story("Steering during work and review", AGENT+"#11-steering-and-recovery", [
        event("Receive S1 and capture started workers","Steering S1 closes starts and captures A and B. A is reconciling; B is waiting for verification. C has not started and remains pending.","Receipt and claims share the short transaction. Gate/model waiters count as started, but pending C consumes no W slot.","Closing starts must leave the captured workers' final-phase paths open.",controller="Drain captured {A, B} for S1",A="Reconciliation on original spec",B="Waiting for verification · original spec",C="Pending · not captured",w=2,l=1,verifier="A",starts="Closed",received=1),
        event("A publishes and releases","A finishes its original assignment, publishes P1 unresolved and releases after known completion. S1 has not changed its instructions.","A's permits and residency end after receipt/cleanup. B remains resident while waiting.","Steering receipt is not grant revocation or silent cancellation.",A="Finished · P1 unresolved",l=0,verifier="—",w=1,provisional="P1",reports="A unresolved"),
        event("B is allowed into verification","B captures P1 and runs the mandatory reconciliation/final phases on its original instructions. C still does not start.","The verification queue admits captured B despite the new-start barrier. Its local request is eligible normally.","The drain waits for started work, not for an emptied pending queue.",B="Reconciliation against P1",verifier="B",l=1),
        event("Drain reaches a real boundary","B's checks, assessment, P2 publication and release finish. The controller can now pin the drained worker reports with S1.","Both worker slots and conflicting permits are free; retained reports remain durable.","A stuck or interrupted worker would expose a blocker, not an invented completion.",B="Finished · P2 unresolved",w=0,l=0,verifier="—",provisional="P2",reports="A + B unresolved",controller="Drain complete · ready to pin S1"),
        event("Senior query pins S1","The senior query consumes a packet ending at S1, with expected head P2 and the captured reports.","Cloud admission is independent of worker capacity. New starts remain closed.","A query records its exact input range and expected authority versions.",controller="Senior review · snapshot through S1",cloud=1),
        event("S2 arrives during the query","The controller records S2 immediately. The active senior query still covers only S1; its response must not pretend to have consumed S2.","Ingress remains responsive during the cloud wait. Received advances to 2; applied stays 0.","Later input stays pending and keeps new coding starts closed.",received=2),
        event("Apply only the consumed range","Assuming its head/plan/report comparisons still hold, the S1 proposal resolves the reviewed reports and acknowledges S1. S2 is still pending, so starts stay closed.","The application publishes only its exact acknowledgement range. A separate new review handles S2; no stale payload acknowledges it.","applied ≤ planner snapshot ≤ received; on a relevant version conflict retain and refresh the proposal.",controller="S1 applied · S2 still pending",cloud=0,applied=1,reviewed="P2",reports="A + B resolved"),
        event("Review S2 before reopening","A further senior query pins S2. After its own validated plan publication, applied reaches 2 and starts can reopen under the new immutable plan.","This snapshot is after that bounded query and publication have ended. A new claim would reserve W again.","The old pending queue is not automatically executed just to complete a steering drain.",controller="New plan active · consumed through S2",starts="Open",applied=2,C="Eligible only under the new plan"),
    ]),
    "failed": story("Failed verdict → senior revert", AGENT+"#10-publication-and-review", [
        event("Assessment finds a definite failure","A has reconciled and assessed its final tree. A required criterion fails, so the normal verdict is fail.","A still holds verification. Final assessment is complete; relevant tool/model effects have ended.","Definite failed criteria cannot be converted to successful by model prose.",A="Assessed fail",w=1,verifier="A"),
        event("Failed code still publishes provisionally","The selected policy publishes real P1 plus the unresolved failed report and attributable hazard. It does not hide the code privately.","Commit/evidence exist before atomic P1/report/receipt publication. A retains verification while validating the receipt.","provisional_all applies to successful, fail and uncertain normal assessed outcomes.",A="P1 published · fail · hazard attached",provisional="P1",reports="A fail · unresolved"),
        event("Senior reviews after the worker finishes","A releases and the review barrier pins P1. The senior examines the failed contribution, later/dependent work and the blast radius before proposing a revert.","The worker slot and verification are free; one cloud query is active.","Keep/revert/retry/defer are separate from the original worker verdict.",controller="Senior reviewing failed P1",A="Finished · failed report retained",w=0,verifier="—",starts="Closed",cloud=1),
        event("Revert uses its own protected intent","The senior revert is an authorized generic head-update capability. The inverse is checked against the captured current head; it is not a fabricated worker TaskReport.","The resolution operation owns verification and takes shell for its inverse/check command. Stable intent and expected head are journaled.","Reconcile each revert receipt before applying the next disposition or activating a new plan.",controller="Applying authorized revert",cloud=0,verifier="Senior revert",shell="Senior revert",journal="active"),
        event("Publish the inverse and resolution","A real inverse commit R1, parented on P1, becomes provisional head with resolution/evidence/receipt. The original failed report and commit remain history.","The command has ended; the metadata head/resolution publication settles once under the current owner.","Git undo does not reverse unrelated remote effects; dependency checks remain necessary.",shell="—",provisional="R1",reports="A reverted · original report retained",journal="settled"),
        event("Reviewed result is still not project completion","The accepted resulting revision is R1 after dispositions/checks. Verification is released; completion still needs a matching senior proposal and independent project checks.","No worker, shell or verification occupancy remains in this snapshot. The original report is retained separately from the reviewed head.","retry/defer alone would have left the published code in place; an explicit inverse removed it.",controller="Ready for further planning or completion review",verifier="—",reviewed="R1"),
    ]),
    "crash": story("Crash around head publication", OS+"#failure-and-abort", [
        event("A owns an assessed candidate","A completed reconciliation, checks and assessment. It still owns verification and has not yet published the candidate.","The original private delta, final tree, owner and phase state are durable. No active command remains.","Only a completed final assessment can enter normal commit/report publication.",A="Assessed candidate · publication pending",w=1,verifier="A",journal="prepared"),
        event("Private P1 exists; shared H0 remains","Trusted Git preparation creates P1. Merely finding this commit would not prove a completed worker or a shared-head handoff.","Git/evidence objects are immutable prerequisites. The authoritative metadata head has not advanced yet.","Private commit existence is distinct from durable head/report/receipt publication.",A="Private P1 · no committed receipt yet",journal="prepared"),
        event("Crash leaves the publication uncertain","A publication response is lost around the metadata commit. The worker cannot decide whether P1 is shared and must not retry with a new intent.","Retain original publication ID and conflicting verification ownership. The recovery view has not yet read authoritative outcome.","Timeout or exception does not prove that publication failed or that releasing the gate is safe.",controller="Recovery required",A="Publication outcome unknown",provisional="Not yet reconciled",journal="uncertain",starts="Closed"),
        event("Restart fences the old writer","Recovery first establishes that the previous coordinator/driver cannot keep writing, then inspects the original journal and receipt.","One current driver is restored only after effect reconciliation. Status/input handling stays available while the blocker is visible.","A saved checkpoint is not a transaction with a provider, Git or the metadata journal.",controller="Inspecting original intent and receipt",A="Supervised recovery · ownership retained"),
        event("The original receipt proves P1 published","Recovery finds P1 plus the original report/receipt already committed. It returns that original result rather than making another commit.","The authoritative head is P1. Journal settlement is deduplicated; real incurred provider usage remains accounted for.","Replay lookup returns retained success even after an old workspace/permit generation changes.",controller="Original publication recovered",A="P1 receipt validated · unresolved",provisional="P1",reports="A unresolved",journal="settled"),
        event("Finish the original attempt","The worker finishes known cleanup and releases. Senior review is still separate; no duplicate undo unit was created.","Verification and worker occupancy are now reusable. The report, receipt and recovery artifacts remain retained.","If no receipt existed, recovery would establish the actual outcome before continuing or recording a reconciled abort.",controller="Ready for review",A="Finished original attempt",w=0,verifier="—"),
    ]),
    "abort": story("Abort integration → rebuild at fresh H", OS+"#failure-and-abort", [
        event("B integrated predecessor P1","B's original private delta was based on H0. Under verification it built a complete P1 integration view, including predecessor A's changes.","Original B-relative delta and the integrated generation remain separately attributable.","The whole integration tree is not a private delta against the original base.",B="Integration at P1 · original base H0",w=1,verifier="B",provisional="P1",reports="A unresolved"),
        event("Explicitly abort after effects settle","B cannot finish this final phase. It retains partial work, aborts without a normal report and retires the integration generation/check authority.","Relevant commands/publication effects are known ended before release. Paused B retains W unless explicitly hibernated safely.","No completed assessment means no fabricated fail/uncertain normal report.",B="Paused · abandoned integration retained",verifier="—",journal="settled"),
        event("Another worker publishes P2","While B is paused and holds no verification, C completes its own protected sequence and publishes P2. The shared head has moved.","This snapshot is after C's publication/cleanup. B is still resident; its original private delta is pinned.","Resuming B cannot publish against the head captured by its abandoned generation.",C="Finished · P2 unresolved",provisional="P2",reports="A + C unresolved"),
        event("Reacquire and rebuild at P2","B takes fresh verification, materializes P2 and reapplies only its preserved original H0-to-development delta. Abandoned repairs are available for explicit reapplication.","A new integration generation prevents stale tool/assessment dispatch from targeting the switched view.","Never diff the abandoned whole tree against H0: that would reattribute incoming predecessor code.",B="New integration generation · captured P2",verifier="B",journal="prepared"),
        event("Repeat reconciliation and final phases","B starts the mandatory new reconciliation turn. It must rerun relevant checks and final assessment before any normal publication.","A new logical step and bounded local request are admitted; retired evidence grants no publication authority.","A clean merge or earlier assessment does not waive the fresh final-phase requirements.",B="Fresh reconciliation active · checks/assessment still required",l=1,journal="active"),
        event("Publish only the newly assessed result","After renewed checks/assessment and scope validation, B publishes P3 with sole parent P2, validates the receipt and releases after cleanup.","The original operations are settled; the new P3/report receipt is durable. No predecessor contribution was relabeled as B's private delta.","A recovered existing publication receipt would instead finish the original attempt, not rebuild a second publication.",B="Finished · P3 unresolved",w=0,l=0,verifier="—",provisional="P3",reports="A + C + B unresolved",journal="settled"),
    ]),
}

CONTENT = {
    "agent": dict(title="Agent design", eyebrow="THE APPLICATION · PORTABLE LANGGRAPH GRAPHS",
        headline="The agent decides what happens next.",
        description="A deterministic sprint controller coordinates senior planning, bounded coding workers and evidence-based review. The runtime supplies the effects and guarantees underneath.",
        nodes=AGENT_NODES, maps=AGENT_MAPS, review=AGENT_REVIEW,
        takeaway="A worker can finish successfully while its report remains unresolved. Only senior review and independent project checks can support project acceptance."),
    "os": dict(title="Simplified OS design", eyebrow="THE RUNTIME · AUTHORITY, RESOURCES & EFFECTS",
        headline="The OS makes each effect accountable.",
        description="Four small modules admit work, isolate code, preserve ownership and recover external effects. One shared local model serves concurrent requests; the engine controls token batching.",
        nodes=OS_NODES, maps=OS_MAPS, review=OS_REVIEW,
        takeaway="Verification is serial; reasoning need not be. The current verifier holds the project permit through publication while other eligible private work and model requests can progress."),
    "stories": STORIES,
    "sources": [
        dict(title="Audited agent design",category="CURRENT DESIGN",href=AGENT,description="Graphs, portable ports, task/verdict/review semantics and application-owned state."),
        dict(title="Simplified OS specification",category="CURRENT DESIGN",href=OS,description="Four implementation modules, independent limits, private copies, two gates and recovery."),
        dict(title="Merged agent graph",category="BEHAVIORAL BASELINE",href="../polyinference-design/polyinference-agent-design-merged.html",description="Original editable diagram: 23 execution nodes and the preserved 19-node memory view."),
        dict(title="Joint integration audit",category="CORRECTIONS & OPEN CHECKS",href=AUDIT,description="Nine findings across the two designs, their corrections and implementation acceptance schedules."),
        dict(title="Agent wire contract",category="STRUCTURAL + SELECTED SEMANTIC CHECKS",href="../langgraph-agent/contracts.py",description="Wire 2.0 records. Models validate shapes and some invariants; they do not implement a runtime."),
        dict(title="Core workspace/profile contract",category="STRUCTURAL + SELECTED SEMANTIC CHECKS",href="../simplified-os/contracts.py",description="Static role profile, scoped manifests, explicit deltas and integration-generation links."),
        dict(title="Source consolidation",category="RESEARCH & PRECEDENCE",href="../simplified-os/SOURCES.md",description="How the five lecture derivations and earlier agent studies support the current build boundary."),
        dict(title="Reader build notes",category="THIS VISUAL PROJECTION",href="README.md",description="Offline files, regeneration instructions, diagram conventions and review-note behavior."),
    ],
    "boundary": [
        ["ProcessSpec / TaskSpec","Agent declares role, immutable assignment/base, limits, scope and dependencies.","Runtime authenticates, negotiates and claims bounded residency before setup."],
        ["ModelQuery / AgentJob","Agent supplies context, phase, grammar and required execution guarantees.","Runtime enforces static eligibility, context/data policy, admission and actual endpoint protocol."],
        ["CapabilityCall","Agent proposes a scoped action; it does not grant itself authority.","Runtime validates arguments/current view/content, journals and executes with required permits."],
        ["TaskReport + PublicationReceipt","Agent proposes assessed verdict and preserves evidence/provenance.","Runtime publishes actual H → P, unresolved report, receipt and event intents atomically in metadata."],
        ["Review resolution / head update","Senior proposes keep/revert/retry/defer; controller validates application meaning.","Revert is a separate journaled capability call and protected head update, without a fake worker report."],
        ["Continuation + event cursor","Agent retains pinned graph/phase/context/workspace references.","Runtime reconciles effects/ownership and advances one compatible current driver."],
    ],
    "capacity": [
        ["W","Resident coding workers","Setup through execution and necessary cleanup, including model/gate waits."],
        ["L","Submitted local requests","Queued-in-engine requests count until confirmed ended."],
        ["E","Backend sequence limit","Engine configuration; this core keeps L ≤ E."],
        ["T","Reserved local context","Input plus reserved output across admitted local requests; conservative unless backend-enforced."],
        ["C","Cloud operations","Independent account/endpoint capacity; also serialize mutable sessions."],
        ["Shell / verification","One / one","Per-command installation exclusion versus complete final-phase project ownership."],
    ],
}
