/* OS inspection and explicit operator controls; application recovery stays with its owner. */
let monitorData=null,agentRecords={},agentTexts={},agentTasks=[],taskFilter="all",drawerRestore=null;
let resuming=false,resumePanel=null;
const resumeDrafts=new Map();
const terminalProcess=state=>["completed","failed","cancelled"].includes(state);
const settledOperation=state=>["succeeded","failed","cancelled"].includes(state);
const actionLabel=action=>({keep:"Kept · resolved",revert:"Reverted · resolved",retry:"Retry requested",defer:"Deferred · unresolved"}[action]||"Awaiting review");
const reviewClosed=action=>["keep","revert"].includes(action);
const taskReviewLabel=task=>task.report?.code_location==="private"&&task.resolution?.action==="revert"?"Rejected · resolved":actionLabel(task.resolution?.action);
const compactText=(value,limit=200)=>String(value||"").length>limit?String(value).slice(0,limit-1)+"…":String(value||"");
function readableText(value){try{const parsed=JSON.parse(value);return typeof parsed==="string"?parsed:value}catch{return value}}
function taskTitle(task){const text=task.id.replace(/[_-]\d+$/,"").replace(/[_-]/g," ");return text.charAt(0).toUpperCase()+text.slice(1)}
function buttonLink(label,action){const button=element("button",label,"record-link");button.type="button";button.onclick=action;return button}
function secondary(primary,detail){const box=element("div");box.append(primary instanceof Node?primary:element("span",primary));if(detail)box.append(element("span",detail,"secondary-line"));return box}
function disclosure(parent,title,value){const details=element("details");details.append(element("summary",title),element("pre",pretty(value)));parent.append(details);return details}
function paragraph(parent,title,text){const section=element("section",undefined,"detail-section");section.append(element("h3",title));if(text!=="")section.append(element("p",text??"Not recorded."));parent.append(section);return section}
function resourceName(value){return {"verification/project":"Project verification","shell/installation":"Installation shell","shell":"Installation shell"}[value]||value||"Resource"}
function previewText(value,texts=agentTexts){
 if(typeof value==="string")return readableText(value);
 if(value?.digest)return readableText(texts[value.digest]||"Text not retained; inspect the artifact.");
 return "";
}
function snapshotAgentSource(document){
 if(document.agents)return document.agents;
 const texts={};
 for(const artifact of document.artifacts||[]){
  if(!artifact.data||artifact.error)continue;
  try{texts[artifact.digest]=new TextDecoder().decode(Uint8Array.from(atob(artifact.data),c=>c.charCodeAt(0)))}catch{ /* Raw records remain usable when an artifact is absent. */ }
 }
 return {records:document.records||{},texts};
}
function projectTasks(records,texts={}){
 return Object.entries(records).filter(([key])=>key.startsWith("task/")).map(([key,task])=>{
  const assignment=task.assignment||{},report=records[task.report_ref]||null;
  const resolutionKey=task.report_ref?"resolution/"+task.report_ref:null;
  const resolution=records[resolutionKey]||null,event=records[resolution?.resolution_ref]||null;
  const attempt=records["attempt/"+task.attempt_id]||{};
  return {key,...task,assignment,id:assignment.task_id||key.slice(5),report,resolution,resolutionKey,resolutionEvent:event,attempt,
   resolved:!!report&&reviewClosed(resolution?.action),verdict:report?.verdict||null,
   comment:previewText(report?.assessment_summary,texts),reviewReason:previewText(event?.reason,texts),
   plan:records[task.plan_ref]||{},spec:records[task.spec_ref]||{},
   diagnostic:task.exception||task.stop_reason||previewText(attempt.extensions?.["polyinference/stop-detail"],texts)||attempt.stop_reason||""};
 });
}
function taskMatchesFilter(task,filter){
 if(filter==="active")return task.execution==="in_progress";
 if(filter==="pending")return task.execution==="pending";
 if(filter==="review")return !!task.report&&!task.resolved;
 if(filter==="resolved")return task.resolved;
 if(filter==="interrupted")return ["interrupted","cancelled"].includes(task.execution);
 return true;
}
function taskRank(task){return task.execution==="interrupted"?0:task.report&&!task.resolved?1:task.execution==="in_progress"?2:task.execution==="pending"?3:4}
function pendingReason(task){
 const blocked=(task.assignment.dependencies||[]).filter(id=>{const source=agentRecords["task/"+id];return !source?.report_ref||agentRecords["resolution/"+source.report_ref]?.action!=="keep"});
 if(blocked.length)return "Awaiting kept dependencies: "+blocked.join(", ");
 if(agentRecords["app/run"]?.starts_closed)return "New starts closed for review";
 if(osState?.policy?.max_workers&&(osState.control.active_workers||[]).length>=osState.policy.max_workers)return "Waiting for worker capacity";
 return "Prerequisites satisfied · awaiting dispatch";
}
function inferenceActivity(row){
 const p=row.inference_progress;if(!p)return "model response";
 const labels={waiting_first_output:"waiting for first model output",waiting_buffered_response:"waiting for buffered response",receiving:"receiving model output",terminal:"validating completed output",uncertain:"transport outcome unknown"};
 const elapsed=Math.max(0,Math.round((Date.now()-Date.parse(p.at))/1000+(p.elapsed_seconds||0)));
 const last=p.last_output_seconds==null?"":" · last output "+Math.max(0,Math.round(elapsed-p.last_output_seconds))+"s ago";
 const retry=p.retry?" · "+(p.retry.source||"native")+" retry "+p.retry.attempt:" · initial attempt";
 return (labels[p.state]||p.state)+" · "+elapsed+"s"+last+retry+" · deadline "+stamp(p.deadline);
}
function processWait(process){
 if(!osState)return "";
 const pid=process.process_id,waits=[];
 for(const row of osState.reservations||[])if(row.process_id===pid&&row.state==="waiting")waits.push("Model capacity · "+(row.lane||"ordinary")+" queue · "+duration(row.queued_at));
 for(const row of osState.ownership_waits||[])if(row.process_id===pid&&row.state==="waiting"){
  const owner=(osState.critical_sections||[]).find(item=>item.resource===row.resource)?.process_id;
  waits.push(resourceName(row.resource)+(owner?" · owned by "+owner:"")+" · "+duration(row.queued_at));
 }
 if(!waits.length&&process.status?.wait){
  const wait=process.status.wait;
  if(wait.wait_kind==="operation"){
   const targets=(wait.target_refs||[]).map(ref=>osState.operations.find(row=>row.operation_id===ref||row.key===ref)).filter(Boolean);
   waits.push(targets.length?targets.map(row=>row.state==="uncertain"?"execution outcome unknown":row.kind==="model_query"?inferenceActivity(row)+" · "+(process.endpoint||process.status.binding_ref||"configured")+" endpoint":row.kind==="agent_job"?"native agent job":row.capability||"tool result").join("; "):"operation result");
  }else waits.push(wait.wait_kind.replace(/_/g," ")+(wait.target_refs?.length?": "+wait.target_refs.map(resourceName).join(", "):""));
 }
 return waits.join("; ");
}
function processActivity(process){
 const wait=processWait(process);if(wait)return "Waiting for "+wait;
 const effects=(osState?.operations||[]).filter(row=>row.process_id===process.process_id&&!settledOperation(row.state));
 if(effects.length)return effects.map(row=>(row.state==="uncertain"?"Execution outcome unknown · ":"")+(row.capability||row.kind||"operation")).join("; ");
 return process.status?.phase||"No outstanding operation recorded";
}
function openDrawer(title,meta,refresh=null,back=null){
 ++inspection;drawerRestore=refresh;resumePanel=null;
 $("osInspectorTitle").textContent=title;$("osInspectorMeta").textContent=meta||"";
 $("osInspectorBody").replaceChildren();$("recordBrowser").hidden=true;$("executionDetails").hidden=true;
 $("drawerRefresh").hidden=!refresh||!!savedDocument;$("drawerRefresh").onclick=()=>refresh?.();
 $("drawerBack").hidden=!back;$("drawerBack").onclick=()=>back?.();
 if(!$("osInspector").open)$("osInspector").showModal();
 return $("osInspectorBody");
}
function artifactLinks(parent,value){
 const refs=new Map();
 function visit(item){if(Array.isArray(item)){item.forEach(visit);return}if(!item||typeof item!=="object")return;if(item.digest&&item.artifact_id===item.digest)refs.set(item.digest,item);Object.values(item).forEach(visit)}
 visit(value);
 if(refs.size){const links=element("div",undefined,"record-links");for(const ref of refs.values())links.append(buttonLink("Artifact "+ref.digest.slice(7,19),()=>inspectArtifact(ref)));parent.append(links)}
}
async function inspectArtifact(ref){
 const back=drawerRestore,run=current,request=++inspection,document=savedDocument;
 try{
  const text=await contextArtifact(ref,{run,document});
  if(current!==run||request!==inspection||document!==savedDocument)return;
  const box=openDrawer("Artifact",ref.digest,null,back);box.append(element("pre",text));
 }catch(exc){if(current===run&&request===inspection&&document===savedDocument)error(exc.message)}
}
async function contextRecord(key,source){
 if(source.document){
  if(!Object.hasOwn(source.document.records||{},key))throw Object.assign(Error("Record not retained: "+key),{status:404});
  return {key,value:source.document.records[key],revision:source.document.record_revisions?.[key]};
 }
 return api("/api/record?"+new URLSearchParams({run:source.run,key}));
}
async function contextArtifact(ref,source){
 if(!/^sha256:[0-9a-f]{64}$/.test(ref?.digest||""))throw Error("Invalid artifact reference");
 if(!source.document)return (await api("/api/artifact?"+new URLSearchParams({run:source.run,digest:ref.digest}))).text;
 const row=(source.document.artifacts||[]).find(item=>item.digest===ref.digest);
 if(!row||row.error||typeof row.data!=="string")throw Error(row?.error||"Artifact not retained in this snapshot.");
 return new TextDecoder().decode(Uint8Array.from(atob(row.data),c=>c.charCodeAt(0)));
}
function contextOperations(){
 if(!savedDocument?.records)return osState?.operations||[];
 const records=savedDocument.records;
 return Object.entries(records).filter(([key])=>key.startsWith("effect/")).map(([key,effect])=>{
  const request=effect.request||{},ext=request.extensions||{},id=request.operation_id;
  return {key,operation_id:id,process_id:request.scope?.process_id,state:effect.state,kind:request.payload?.kind,
   created_at:request.created_at,logical_step_id:request.logical_step_id,parent_operation_id:request.causal_parent_ref,
   model_retry:ext["runtime/model-retry"],output_retry:ext["runtime/output-retry"],context_compaction:!!ext["runtime/context-compaction"],
   model_retry_outcome:records["model-retry-outcome/"+id]?.result_operation_id,
   output_retry_outcome:records["output-retry-outcome/"+id]?.operation_id};
 });
}
const modelOperation=row=>["model_query","agent_job"].includes(row.kind);
const contextOrder=(a,b)=>(a.created_at||"").localeCompare(b.created_at||"")||(a.operation_id||"").localeCompare(b.operation_id||"");
function contextInvocations(rows,pid){
 const selected=rows.filter(row=>row.process_id===pid&&modelOperation(row)),map=new Map(selected.map(row=>[row.operation_id,row])),groups=new Map();
 function root(row,visited=new Set()){
  if(visited.has(row.operation_id))throw Error("Retry provenance cycle");
  const next=new Set([...visited,row.operation_id]),roots=new Set();
  for(const marker of [row.model_retry,row.output_retry])if(marker){
   if(typeof marker!=="object"||!marker.root_operation_id||!marker.previous_operation_id)throw Error("Incomplete retry provenance");
   for(const id of [marker.root_operation_id,marker.previous_operation_id]){
    const parent=map.get(id);if(!parent||parent.context_compaction)throw Error("Missing or cross-process retry provenance");
    roots.add(root(parent,next));
   }
  }
  if(roots.size>1)throw Error("Conflicting retry roots");
  return roots.size?[...roots][0]:row.operation_id;
 }
 for(const row of selected){
  let id=row.operation_id,issue=null;
  if(!row.context_compaction)try{id=root(row)}catch(exc){issue=exc.message}
  if(!groups.has(id))groups.set(id,{id,attempts:[],helper:!!row.context_compaction,issue});
  const group=groups.get(id);group.attempts.push(row);if(issue)group.issue=issue;
 }
 for(const group of groups.values()){
  group.attempts.sort(contextOrder);const ids=new Set(group.attempts.map(row=>row.operation_id));
  const outstanding=group.attempts.filter(row=>!settledOperation(row.state));
  let effective=map.get(group.id),visited=new Set(),hasOutcome=false;
  while(effective){
   if(visited.has(effective.operation_id)){group.issue="Retry outcome cycle";effective=null;break}
   visited.add(effective.operation_id);
   const next=effective.output_retry_outcome||effective.model_retry_outcome;
   if(!next||next===effective.operation_id)break;
   hasOutcome=true;
   if(!ids.has(next)){group.issue="Retry outcome unavailable in this invocation";effective=null;break}
   effective=map.get(next);
  }
  group.selected=outstanding.at(-1)||(hasOutcome?effective:null)||group.attempts.at(-1);
  group.outstanding=outstanding.length;group.latest=group.attempts.at(-1);
 }
 return [...groups.values()].sort((a,b)=>contextOrder(a.latest,b.latest));
}
async function showMemory(pid,operationId=null,choice=null,back=drawerRestore){
 const rows=contextOperations(),groups=contextInvocations(rows,pid),ordinary=groups.filter(group=>!group.helper);
 const preferred=ordinary.filter(group=>group.outstanding).at(-1)||ordinary.at(-1);
 const selected=operationId?rows.find(row=>row.operation_id===operationId&&row.process_id===pid&&modelOperation(row)):preferred?.selected;
 const box=openDrawer("Memory / context",pid+" · retained invocation input",()=>showMemory(pid,selected?.operation_id,choice,back),back);
 const source={run:current,document:savedDocument,generation:inspection},valid=()=>source.run===current&&source.document===savedDocument&&source.generation===inspection;
 paragraph(box,"Scope","Retained explicit invocation input, not hidden reasoning, provider KV state or every record the process could read. Completed processes show their last retained invocation.");
 if(!selected){paragraph(box,"Context",groups.length?"No caller invocation retained. Compaction helper calls are separately inspectable.":"No model context recorded for this process.");for(const group of groups)box.append(buttonLink("Compaction helper "+group.id,()=>showMemory(pid,group.id,null,back)));return}
 const chooser=element("select");chooser.setAttribute("aria-label","Invocation and retry attempt");
 for(const group of groups)for(const attempt of group.attempts){const option=element("option",(group.helper?"Compaction helper · ":"Invocation "+group.id+" · ")+attempt.operation_id+" · "+attempt.state);option.value=attempt.operation_id;chooser.append(option)}
 chooser.value=selected.operation_id;chooser.onchange=()=>showMemory(pid,chooser.value,null,back);box.append(chooser);
 const outstanding=ordinary.filter(group=>group.outstanding).length;
 if(outstanding>1)paragraph(box,"Outstanding invocations",outstanding+" invocations have outstanding attempts; select either explicitly.");
 if(preferred?.selected.operation_id!==selected.operation_id)paragraph(box,"Other retained work","A newer or outstanding invocation is available in the selector. Your selected attempt is preserved.");
 const group=groups.find(group=>group.attempts.some(row=>row.operation_id===selected.operation_id));
 if(group?.issue)paragraph(box,"Provenance issue",group.issue+"; this attempt remains separately inspectable.");
 if(selected.context_compaction)paragraph(box,"Helper call","OS context compaction helper, separate from the caller invocation.");
 paragraph(box,"Capture times","OS list: "+stamp(osState?.captured_at)+" · details fetched: "+stamp(new Date().toISOString())+". Separate live reads are not one atomic snapshot.");
 const id=selected.operation_id,keys=[selected.key||"effect/"+id,"context-prepared/"+id,"context-receipt/"+id];
 const results=await Promise.allSettled(keys.map(key=>contextRecord(key,source)));
 if(!valid())return;
 const values=results.map((result,index)=>{if(result.status==="fulfilled")return result.value.value;if(result.reason.status!==404)paragraph(box,"Record load failed: "+keys[index],result.reason.message);return null});
 const [effect,prepared,standalone]=values,request=effect?.request;
 if(!request){paragraph(box,"Context","Selected effect unavailable; refresh details or inspect its raw record.");return}
 if(request.operation_id!==id||request.scope?.process_id!==pid){paragraph(box,"Identity mismatch","Effect identity does not match the selected operation/process. Inspect raw records.");return}
 const original=request.payload?.context,receipt=prepared?.receipt||standalone,effective=prepared?.context;
 const matched=!!effective&&!!receipt&&receipt.context_ref===original?.view_id&&receipt.prepared_context_ref===effective.view_id;
 if(receipt&&receipt.context_ref!==original?.view_id)paragraph(box,"Receipt identity mismatch","Receipt names another original context; inspect raw records.");
 if(effective&&!matched)paragraph(box,"Identity mismatch","Prepared context and embedded receipt do not match this original input; showing original input. Inspect raw records.");
 if(prepared&&standalone&&["context_ref","prepared_context_ref","prepared_digest"].some(key=>prepared.receipt?.[key]!==standalone[key]))paragraph(box,"Receipt discrepancy","Standalone receipt differs from the prepared record's embedded receipt. The embedded receipt identifies that prepared view.");
 const useEffective=matched&&choice!=="original",context=useEffective?effective:original;
 const views=element("div",undefined,"record-links");
 if(matched)views.append(buttonLink("Effective prepared input",()=>showMemory(pid,id,"effective",back)));
 views.append(buttonLink("Original supplied input",()=>showMemory(pid,id,"original",back)));box.append(views);
 paragraph(box,"Selected input",useEffective?"Effective prepared input":"Original supplied input"+(!matched?" · prepared input unavailable or invalid":""));
 paragraph(box,"Operation",id+" · step "+(request.logical_step_id||"unrecorded")+" · "+(effect.state||"unrecorded")+" · created "+stamp(request.created_at));
 const submitted=(effect.result?.extensions?.["polyinference/attempted-backend"]||effect.attempted_backend||{}).submitted;
 paragraph(box,"Submission",submitted===true?"Submission recorded; a dispatch marker does not prove remote receipt":submitted===false?"Recorded as not submitted":"Submission evidence unavailable");
 if(effect.state==="uncertain")paragraph(box,"Execution certainty","Termination remains unknown; preparation and submission do not establish completion.");
 if(receipt){
  paragraph(box,"Measured adapter input",`Original ${receipt.original_bytes??"?"} · prepared ${receipt.submitted_bytes??"?"} · required ${receipt.required_bytes??"?"} · allowance ${receipt.input_allowance??"?"} · ${receipt.unit||"unit unrecorded"}. Byte bound, not provider tokenizer usage. Prepared size does not prove submission.`);
  disclosure(box,"Preparation receipt & policy",receipt);
  for(const summary of receipt.summaries||[]){const section=paragraph(box,"Summary provenance",summary.part_id||"Derived context");artifactLinks(section,summary)}
  for(const helper of receipt.compaction_operations||[]){const row=rows.find(row=>row.operation_id===helper);box.append(row?buttonLink("Compaction helper "+helper,()=>showMemory(row.process_id,helper,null,()=>showMemory(pid,id,choice,back))):recordLink("effect/"+helper,"Compaction helper record "+helper))}
 }else paragraph(box,"Preparation","No preparation receipt retained. Original input remains inspectable.");
 paragraph(box,"Representation limit","Context parts omit some adapter-added tools, schemas, protocol instructions and provider framing. This is not a complete wire dump.");
 if(!context||!Array.isArray(context.parts))paragraph(box,"Parts","No valid ContextView parts retained.");
 for(const [index,part] of (Array.isArray(context?.parts)?context.parts:[]).entries()){
  const section=element("details");section.append(element("summary",(index+1)+" · "+(part.part_id||"unnamed")+" · "+(part.part_kind||"unknown")+(!useEffective&&(receipt?.omitted_refs||[]).includes(part.part_id)?" · omitted by preparation":"")));
  disclosure(section,"Part metadata",{part_id:part.part_id,part_kind:part.part_kind,source_ref:part.source_ref,trust:part.trust,required:part.required,compactable:part.compactable,call_id:part.call_id,artifact:part.content,derived_from:part.derived_from});
  const load=buttonLink("Read full content",async()=>{load.disabled=true;try{const text=await contextArtifact(part.content,source);if(valid())section.append(element("pre",text))}catch(exc){if(valid())section.append(element("p","Content unavailable: "+exc.message))}finally{if(valid())load.disabled=false}});section.append(load);artifactLinks(section,part.content);box.append(section);
  for(const ref of part.derived_from||[])if(typeof ref==="string"&&/^sha256:[0-9a-f]{64}$/.test(ref))section.append(buttonLink("Derived from "+ref,()=>inspectArtifact({digest:ref})));
 }
 const refs=paragraph(box,"Referenced memory snapshots","");
 const index=new Set((osState?.record_index||[]).map(row=>row.key));
 for(const ref of context?.memory_snapshot_refs||[]){const key=typeof ref==="string"?ref:null;refs.append(key&&(source.document?Object.hasOwn(source.document.records||{},key):index.has(key))?recordLink(key):element("pre",pretty(ref)))}
 if(!(context?.memory_snapshot_refs||[]).length)refs.append(element("p","None declared."));
 for(const key of keys)box.append(recordLink(key));
}
function showRecords(){
 if(!osState)return;
 openDrawer("Durable records","Current retained records · "+stamp(osState.captured_at),showRecords);
 $("recordBrowser").hidden=false;renderRecords();
}
function showRunIssue(){
 const box=openDrawer("Run diagnostic","Recorded application blocker and runtime effects",showRunIssue);
 paragraph(box,"Original diagnostic",monitorData?.blocker_detail||monitorData?.blocker||monitorData?.error);
 for(const row of osState?.operations||[])if(row.state==="uncertain")box.append(buttonLink("Unknown execution · "+row.process_id,()=>showOperation(row)));
 if(agentRecords["app/run"])box.append(recordLink("app/run","Run control record"));
 if(monitorData?.reporting_errors?.length)disclosure(box,"Separate observer/reporting errors",monitorData.reporting_errors);
}
function renderExecution(pid){
 $("processes").replaceChildren();$("inspector").replaceChildren(element("p","Select a node for its recorded prompt, response and tool results.","hint"));
 const process=(monitorData?.processes||[]).find(row=>row.id===pid);
 if(!process){$("processes").append(element("p","No process checkpoints were recorded.","hint"));$("executionDetails").hidden=false;return}
 // Consecutive phases stay in order, including a later return to reconciliation.
 let last=null,group=null;
 for(const node of process.nodes||[]){
  const phase=node.phase||"Control flow";
  if(last!==phase){const details=element("details",undefined,"phase-history");details.open=node.status==="running";details.append(element("summary",phase));group=element("div",undefined,"nodes");details.append(group);$("processes").append(details);last=phase}
  const button=element("button",node.name,"node "+node.status+(node.model_call?" model":""));button.type="button";button.dataset.id=node.id;button.title=node.status;
  button.setAttribute("aria-label",phase+": "+node.name+" · "+node.status);button.onclick=()=>selectNode(node.id);group.append(button);
 }
 $("executionDetails").hidden=false;
}
function updateResumePanel(){
 $("resumeRun").disabled=!!savedDocument||resuming||starting;
 const panel=resumePanel;
 if(!panel||panel.run!==current||panel.inspection!==inspection)return;
 const process=osState?.processes.find(row=>row.process_id===panel.pid),options=monitorData?.resume;
 const reason=savedDocument?"Saved snapshots are read-only. Select the retained run to resume.":
  process?.state!=="paused"?"This process is no longer paused.":
  resuming?"Sending resume request…":hasRunningRun?"Wait for the active run to stop before resuming.":
  !options?.allowed?(options?.reason||"Restart the UI server to load resume support, then refresh this page."):null;
 panel.button.disabled=!!reason;panel.text.disabled=resuming||!!savedDocument;
 if(panel.processSelect)panel.processSelect.disabled=resuming;
 panel.hint.textContent=reason||"Optional steering follows the agent's normal review boundary. Existing budgets and saved configuration apply.";
 if(options?.error)panel.status.textContent=options.error;
}
function processResumeControls(box,pid){
 const key=JSON.stringify([current,pid]),section=element("section",undefined,"steering");
 const text=element("textarea"),button=element("button","Resume process"),hint=element("p",undefined,"hint"),status=element("p",undefined,"hint");
 text.rows=3;text.maxLength=16000;text.setAttribute("aria-label","Optional steering for resumed process");
 text.placeholder="Add instructions for the agent (optional)…";text.value=resumeDrafts.get(key)||"";
 text.oninput=()=>resumeDrafts.set(key,text.value);button.type="button";status.setAttribute("role","status");
 section.append(element("h3","Resume paused process"),text,button,hint,status);box.append(section);
 const panel={run:current,pid,inspection,key,text,button,hint,status};resumePanel=panel;updateResumePanel();
 button.onclick=async()=>{
  if(button.disabled||resuming||savedDocument||panel.run!==current||panel.inspection!==inspection)return;
  if(text.value.length>16000){status.textContent="Steering instructions must be at most 16000 characters.";return}
  const run=current,document=savedDocument,version=++viewVersion;resuming=true;updateResumePanel();$("start").disabled=true;
  try{
   await api("/api/resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:run,process_id:pid,text:text.value})});
   resumeDrafts.delete(key);hasRunningRun=true;
   if(current===run&&savedDocument===document&&panel.inspection===inspection&&version===viewVersion){
    text.value="";status.textContent="Resume signal sent. Waiting for the agent to continue.";
   }
  }catch(exc){
   if(current===run&&savedDocument===document&&panel.inspection===inspection&&version===viewVersion)status.textContent=exc.message;
  }finally{
   resuming=false;$("start").disabled=hasRunningRun;updateResumePanel();refresh();
  }
 };
}
function resumeStorage(key,value){
 try{if(typeof localStorage==="undefined")return null;if(value===undefined)return localStorage.getItem(key);
  if(value===null)localStorage.removeItem(key);else localStorage.setItem(key,value)}catch{}return null;
}
function runResumeKey(run=current){return "polyinference.resume."+run}
function runResumeDraft(run=current){
 const key=runResumeKey(run);if(resumeDrafts.has(key))return resumeDrafts.get(key);
 try{const draft=JSON.parse(resumeStorage(key)||"null");if(draft){resumeDrafts.set(key,draft);return draft}}catch{}
 return {text:"",request_id:null};
}
function saveRunResumeDraft(){
 const draft={text:$("resumeText").value,request_id:null},key=runResumeKey();
 resumeDrafts.set(key,draft);resumeStorage(key,JSON.stringify(draft));
}
function renderResumeDraft(data){
 const text=$("resumeText"),draft=runResumeDraft(data.id),key=runResumeKey(data.id);
 // A later poll can acknowledge a POST whose HTTP reply was lost. Retire its
 // identity so the next pause gets a fresh request instead of replaying this one.
 if(draft.request_id&&draft.request_id===data.resume?.request_id){
  resumeDrafts.delete(key);resumeStorage(key,null);if(text.dataset.run===data.id)text.value="";
 }
 if(text.dataset.run!==data.id){text.dataset.run=data.id;text.value=runResumeDraft(data.id).text}
 text.disabled=!!savedDocument||resuming||["accepted","recovering","ready","continuing"].includes(data.resume?.progress);
}
async function showRunResume(){
 if(savedDocument||resuming||starting||hasRunningRun||!current)return;
 const run=current,document=savedDocument,draft=runResumeDraft(run),text=$("resumeText").value;
 if(text.length>16000){$("resumeStatus").textContent="Instructions must be at most 16000 characters.";return}
 if(draft.text!==text){draft.text=text;draft.request_id=null}
 if(!draft.request_id)draft.request_id=typeof crypto!=="undefined"&&crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2);
 const key=runResumeKey(run);resumeDrafts.set(key,draft);resumeStorage(key,JSON.stringify(draft));
 const version=++viewVersion;resuming=true;$("start").disabled=true;$("resumeRun").disabled=true;
 $("resumeRun").textContent="Resuming…";$("resumeText").disabled=true;$("resumeStatus").textContent="Preparing your run to continue…";
 try{
  await api("/api/resume",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:run,text,request_id:draft.request_id})});
  resumeDrafts.delete(key);resumeStorage(key,null);hasRunningRun=true;
  if(current===run&&savedDocument===document&&version===viewVersion){$("resumeText").value="";$("resumeStatus").textContent="Resume requested. Preparing your run…"}
 }catch(exc){
  draft.error=exc.message;resumeDrafts.set(key,draft);resumeStorage(key,JSON.stringify(draft));
  if(current===run&&savedDocument===document&&version===viewVersion)$("resumeStatus").textContent=exc.message;
 }finally{
  resuming=false;$("start").disabled=hasRunningRun;$("resumeRun").disabled=!!savedDocument||starting||hasRunningRun;
  $("resumeText").disabled=!!savedDocument||hasRunningRun;if(!hasRunningRun)$("resumeRun").textContent="Resume";refresh();
 }
}
function showProcess(pid){
 const process=osState?.processes.find(row=>row.process_id===pid);
 const box=openDrawer(pid+" · "+(pid==="controller"?"controller":process?.role||"process"),"Runtime state captured "+stamp(osState?.captured_at),()=>showProcess(pid));
 if(process){
  paragraph(box,"Activity",processActivity(process));const facts=element("div",undefined,"detail-facts");facts.append(stateBadge(process.state),element("span",process.status?.phase||""));box.append(facts);
  if(process.state==="paused")processResumeControls(box,pid);
  const links=element("div",undefined,"record-links");links.append(recordLink(process.key,"Status"),recordLink("process-spec/"+pid,"Specification & limits"),buttonLink("Memory / context",()=>showMemory(pid,null,null,()=>showProcess(pid))));box.append(links);
  const task=agentTasks.find(row=>row.process_id===pid);if(task)box.append(buttonLink("Open task: "+task.id,()=>showTask(task.key)));
  const effects=(osState.operations||[]).filter(row=>row.process_id===pid&&!settledOperation(row.state));for(const effect of effects)box.append(buttonLink((effect.capability||effect.kind)+" · "+effect.state,()=>showOperation(effect)));
  disclosure(box,"Resources, continuation & control",process);
 }
 renderExecution(pid);
}
function showOperation(row,back=drawerRestore){
 const box=openDrawer(row.capability||row.kind||"Operation",row.operation_id,()=>showOperation(row,back),back);
 paragraph(box,"State",row.state==="uncertain"?"Execution outcome unknown. Reservations and conflicting ownership remain retained until the original operation is reconciled.":row.state);
 paragraph(box,"Diagnostic",row.diagnostic||"No failure diagnostic recorded.");
 if(row.isolated_generation)paragraph(box,"Discarded delivery","This generation remains physically uncertain and holds capacity/budget. Its answer cannot be delivered. Independent work may continue; a replacement needs spare capacity.");
 if(row.inference_progress)disclosure(box,"Inference timing and progress",row.inference_progress);
 if(row.transport_failure)disclosure(box,"Transport cause and stage",row.transport_failure);
 if(row.inference_policy)disclosure(box,"Caller retry policy",row.inference_policy);
 if(row.state==="uncertain")paragraph(box,"Recovery","Inspect the original operation, provider/host termination evidence and publication receipts before reconciliation. A timeout or disconnect does not prove termination. Do not remove lock or journal records to force a retry.");
 box.append(buttonLink("Inspect full operation record",()=>inspectRecord(row.key)),element("span"," · "),buttonLink("Open process",()=>showProcess(row.process_id)));
 if(row.parent_operation_id){const parent=osState?.operations.find(item=>item.operation_id===row.parent_operation_id);if(parent)box.append(element("span"," · "),buttonLink("Parent native job",()=>showOperation(parent)))}
 if(row.native_diagnostics)disclosure(box,"Native transport diagnostics",row.native_diagnostics);
 if(modelOperation(row))box.append(buttonLink("Memory / context",()=>showMemory(row.process_id,row.operation_id,null,()=>showOperation(row,back))));
}
function showTask(key){
 const task=agentTasks.find(row=>row.key===key);if(!task)return;
 const box=openDrawer(taskTitle(task),(task.category||"development")+" · "+task.id+" · "+(task.assignment.role||"worker")+" · captured "+stamp(osState?.captured_at),()=>showTask(key));
 const facts=element("div",undefined,"detail-facts");facts.append(stateBadge(task.execution));if(task.verdict)facts.append(stateBadge(task.verdict));if(task.report)facts.append(element("span",taskReviewLabel(task)));box.append(facts);
 const assignment=element("details");assignment.append(element("summary","Assignment, scope & prerequisites"));assignment.open=!task.report&&(task.assignment.objective||"").length<400;box.append(assignment);
 paragraph(assignment,"Assignment",task.assignment.objective);
 paragraph(assignment,"Scope & prerequisites","Writes: "+(task.assignment.write_paths||[]).join(", ")+"\nReads: "+((task.assignment.read_paths||[]).join(", ")||"not recorded")+"\nDepends on: "+((task.assignment.dependencies||[]).join(", ")||"none")+"\nRequired checks: "+((task.assignment.checks||[]).join(", ")||"not recorded"));
 const deps=element("div",undefined,"record-links");for(const id of task.assignment.dependencies||[])deps.append(buttonLink(id,()=>showTask("task/"+id)));assignment.append(deps);
 if(task.diagnostic)paragraph(box,"Interruption / stop diagnostic",task.diagnostic);
 if(task.report){
  const section=paragraph(box,"Verdict & original worker note",task.comment);
  section.append(element("p","Code location: "+(task.report.code_location||"unrecorded")+". Commit: "+(task.report.final_code?.commit_id||task.report.candidate_commit_id||"not recorded"),"secondary-line"));
  if(task.report.assessment_summary)section.append(buttonLink("Full verdict explanation",()=>inspectArtifact(task.report.assessment_summary)));
  const checks=element("div");for(const check of task.report.evidence||[]){const line=element("p");line.append(stateBadge(check.status),element("span"," "+check.criterion_ref+" · "+evidenceFreshness(check,task.report.final_code)));checks.append(line);artifactLinks(checks,[check.invocation,check.output])}section.append(checks);
  paragraph(box,"Senior review",taskReviewLabel(task)+(task.reviewReason?"\n"+task.reviewReason:""));
  const reviewHistory=Object.entries(agentRecords).filter(([id,value])=>id.startsWith("resolution-event/")&&value.report_ref===task.report_ref);
  if(reviewHistory.length){const history=element("details");history.append(element("summary","Review decision history · "+reviewHistory.length));for(const [id,value] of reviewHistory){paragraph(history,value.action,previewText(value.reason));history.append(recordLink(id))}box.append(history)}
 }
 const notes=Object.entries(agentRecords).filter(([id,value])=>id.startsWith("memory-note/")&&(value.provenance_refs||[]).includes(task.report_ref));
 if(notes.length){const section=element("details");section.append(element("summary","Related shared notes · "+notes.length));for(const [id,value] of notes){if(value.content?.digest!==task.report?.assessment_summary?.digest)section.append(element("p",previewText(value.content)));else section.append(element("p","The original verdict explanation is also retained as this shared handoff note.","policy"));section.append(recordLink(id,"Original note · "+(value.author_ref||id)))}box.append(section)}
 const followupRefs=new Set(task.resolutionEvent?.followup_task_refs||[]);
 const followups=agentTasks.filter(row=>followupRefs.has(row.key)||row.attempt.previous_attempt_ref==="attempt/"+task.attempt_id);
 if(followups.length){const section=paragraph(box,"Follow-up assignments","");for(const row of followups)section.append(buttonLink(row.id,()=>showTask(row.key)))}
 const links=element("div",undefined,"record-links");for(const [ref,label] of [[task.key,"Task record"],[task.spec_ref,"Specification"],["attempt/"+task.attempt_id,"Attempt"],[task.report_ref,"Report"],[task.resolutionKey,"Resolution"]])if(ref&&agentRecords[ref])links.append(recordLink(ref,label));links.append(buttonLink("OS process & resources",()=>{selectTab("os");showProcess(task.process_id)}));box.append(links);
 renderExecution(task.process_id);
}
function evidenceFreshness(evidence,code){
 const checked=evidence.checked_code;
 if(!checked||!code)return "revision not recorded";
 return checked.effective_tree_digest===code.effective_tree_digest&&checked.environment_digest===code.environment_digest?"current content & environment":"stale content or environment";
}
function sameRevision(left,right){
 if(!left||!right||!["repository_id","commit_id","effective_tree_digest","environment_digest"].every(key=>left[key]!==undefined&&right[key]!==undefined))return false;
 return [...new Set([...Object.keys(left),...Object.keys(right)])].every(key=>left[key]===right[key]);
}
function acceptanceFacts(records,operations=[]){
 const run=records["app/run"]||{},receipt=records[run.acceptance_ref],head=records["head/provisional"]?.code,reviewed=records["head/reviewed"]?.code;
 const reports=Object.entries(records).filter(([key])=>key.startsWith("report/"));
 const unresolved=reports.filter(([key])=>!reviewClosed(records["resolution/"+key]?.action)).length;
 const unfinished=Object.entries(records).filter(([key,value])=>key.startsWith("task/")&&!["completed","cancelled"].includes(value.execution)).length;
 const matching=sameRevision(head,reviewed);
 const checks=receipt?.evidence||run.acceptance_failure||[];
 const passed=!!checks.length&&checks.every(check=>check.status==="passed"&&evidenceFreshness(check,head)==="current content & environment");
 const accepted=!!receipt&&matching&&sameRevision(receipt.code,head)&&receipt.steering_through===run.steering_received&&receipt.plan_ref===run.plan_ref&&!(run.active_workers||[]).length&&!unfinished&&!unresolved;
 return {run,receipt,accepted,head,reviewed,checks,unresolved,unfinished,items:[
  ["Senior completion proposal",!!run.completion_proposed||!!receipt,receipt?"Recorded in acceptance receipt":run.completion_proposed?"Proposed":"Not yet proposed"],
  ["Started workers settled",Array.isArray(run.active_workers)&&!run.active_workers.length,(run.active_workers||[]).length+" active · "+unfinished+" unfinished tasks"],
  ["Task reports resolved",!!records["app/run"]&&!unresolved,unresolved+" awaiting disposition"],
  ["Reviewed revision matches provisional",matching,matching?"Same accepted content":head?"Review has not caught up":"No project revision recorded"],
  ["Required project checks",passed,passed?"Passing on current content & environment":checks.length?"Failed, inconclusive or stale evidence":"No final check evidence recorded"],
  ["Steering & blocking effects cleared",run.steering_received!==undefined&&run.steering_received===run.steering_applied&&!operations.some(row=>row.state==="uncertain"&&!row.isolated_generation),(run.steering_received||0)-(run.steering_applied||0)+" pending updates · "+operations.filter(row=>row.state==="uncertain").length+" unknown operations"]
 ]};
}
function workflowState(records,processes=[]){
 const run=records["app/run"]||{},tasks=projectTasks(records),setup=tasks.find(row=>row.category==="setup");
 const inPlace=records["repository/setup"]?.isolated===false;
 const senior=processes.find(row=>row.role==="senior"&&row.process_id!=="controller"&&!terminalProcess(row.state));
 let stage="development",summary="Sprint "+(run.sprint||0)+" · development";
 if(!records["app/run"])return {stage:"setup",summary:"No agent run has initialized.",senior};
 if(setup&&!["completed","cancelled"].includes(setup.execution)){stage="setup";summary="Initial setup · "+setup.execution}
 else if(acceptanceFacts(records).accepted||run.completion_proposed){stage="acceptance";summary=acceptanceFacts(records).accepted?"Project accepted · "+(inPlace?"files and commits are in the project repository":run.status==="completed"?"output delivered":"output delivery pending"):"Completion proposed · checking project acceptance"}
 else if(run.starts_closed&&(run.active_workers||[]).length){stage="review";summary="Sprint "+(run.sprint||0)+" · draining "+run.active_workers.length+" started tasks before review. New starts are closed."}
 else if(senior){stage=run.sprint?"review":"planning";summary="Senior "+(senior.status?.phase||"query")+" · "+(processActivity(senior))}
 else if(!run.plan_ref){stage="planning";summary="Initial planning · awaiting a validated senior proposal"}
 else if(run.starts_closed){stage="review";summary="Sprint "+(run.sprint||0)+" · review required. New starts are closed."}
 if(run.blocker)summary+=" · a recorded blocker needs attention";
 return {stage,summary,senior};
}
function renderAgents(data){
 monitorData=data;
 const source=data.agents||(savedDocument?snapshotAgentSource(savedDocument):{records:{},texts:{}});
 agentRecords=source.records||{};agentTexts=source.texts||{};agentTasks=projectTasks(agentRecords,agentTexts);
 const run=agentRecords["app/run"]||{},workflow=workflowState(agentRecords,osState?.processes||[]);
 $("workflowSummary").textContent=(savedDocument?"Saved snapshot · ":osState&&!osState.coordinator_running?"Retained state · ":"")+workflow.summary;
 $("workflowStages").replaceChildren(...[["setup","Setup"],["planning","Planning"],["development","Development"],["review","Sprint review ↔ development"],["acceptance","Acceptance"]].map(([key,label])=>{
  const item=element("span",label,"workflow-step"+(workflow.stage===key?" current":""));if(workflow.stage===key)item.setAttribute("aria-current","step");return item;
 }));
 const plan=agentRecords[run.plan_ref]||{};$("planSummary").textContent=previewText(plan.goal)||"No sprint plan published yet.";
 $("seniorActivity").replaceChildren();
 if(workflow.senior)$("seniorActivity").append(buttonLink("Senior activity · "+(workflow.senior.status?.phase||workflow.senior.state),()=>showProcess(workflow.senior.process_id)));
 else{const queries=(osState?.processes||[]).filter(row=>row.role==="senior"&&row.process_id!=="controller");if(queries.length)$("seniorActivity").append(buttonLink("Inspect latest senior query",()=>showProcess(queries.at(-1).process_id)))}
 $("planDetails").replaceChildren();if(run.plan_ref)$("planDetails").append(recordLink(run.plan_ref,"Current plan "+run.plan_ref));
 const allocation=data.development_allocation;
 if(allocation)$("planDetails").append(element("p",allocation.junior_tasks+" junior / "+allocation.senior_tasks+" specialist started development tasks · specialist target "+Math.round(allocation.target_senior_fraction*100)+"%. Setup and management excluded.","policy"));
 renderTasks();renderNotes();renderAcceptance();
}
function renderTasks(){
 const filters=[["all","All"],["active","Active"],["pending","Pending"],["review","Needs review"],["resolved","Resolved"],["interrupted","Interrupted / cancelled"]];
 $("taskFilters").replaceChildren(...filters.map(([key,label])=>{const count=agentTasks.filter(task=>taskMatchesFilter(task,key)).length,button=element("button",label+" "+count);button.type="button";button.setAttribute("aria-pressed",String(taskFilter===key));button.onclick=()=>{taskFilter=key;renderTasks()};return button}));
 const rows=agentTasks.filter(task=>taskMatchesFilter(task,taskFilter)&&matches([task.id,task.assignment,task.comment,task.reviewReason,task.diagnostic],$("taskSearch").value)).sort((a,b)=>taskRank(a)-taskRank(b)||a.id.localeCompare(b.id));
 table("agentTasks",["Task / assignment","Execution / phase","Verdict","Senior review","Latest note"],rows.map(task=>{
  const process=osState?.processes.find(row=>row.process_id===task.process_id);
  const title=secondary(buttonLink(taskTitle(task),()=>showTask(task.key)),task.id+" · "+(task.assignment.role||"worker")+" · "+(task.category==="setup"?"setup":task.plan_ref||"unplanned"));
  title.append(element("span",compactText(task.assignment.objective,140),"note-preview task-objective"));
  const execution=secondary(stateBadge(task.execution),process?.status?.phase||"");
  if(task.execution==="in_progress"&&process){const wait=processWait(process);if(wait)execution.append(buttonLink("Waiting · "+wait,()=>{selectTab("os");showProcess(process.process_id)}))}
  const progress=agentRecords["worker-progress/"+task.process_id];
  if(progress)execution.append(element("span", "Last progress observation: "+progress.status+" · "+progress.idle_decisions+" idle decisions", "secondary-line"));
  if(task.execution==="pending")execution.append(element("span",pendingReason(task),"secondary-line"));
  const verdict=task.verdict?secondary(stateBadge(task.verdict),task.report.code_location==="private"?"Private candidate":"Provisionally published"):"—";
  const review=task.report?element("span",taskReviewLabel(task),"badge "+(task.resolved?"resolved":"needs-review")):"—";
  const note=element("span",task.reviewReason||task.comment||task.diagnostic||"—","note-preview");
  return [title,execution,verdict,review,note];
 }),agentTasks.length?"No tasks match this filter.":"No tasks have been assigned yet. Planning and review queries appear above.");
 $("taskCount").textContent=rows.length+" of "+agentTasks.length+" tasks · finished and resolved tasks are retained";
}
function renderNotes(){
 $("agentHazards").replaceChildren();$("sharedSummary").replaceChildren();$("agentNotes").replaceChildren();
 for(const [key,value] of Object.entries(agentRecords).filter(([key])=>key.startsWith("hazard/"))){
  if(reviewClosed(agentRecords["resolution/"+value.report_ref]?.action))continue;
  const box=element("div",undefined,"attention");box.append(element("strong",value.verdict+" · "+(value.location||"unrecorded")+" code"),element("p",compactText(value.summary,260)),buttonLink("Open related task",()=>{const task=agentTasks.find(task=>task.report_ref===value.report_ref);if(task)showTask(task.key)}),element("span"," · "),recordLink(key,"Hazard record"));$("agentHazards").append(box);
 }
 const working=agentRecords["memory/working"]||{};
 $("sharedSummary").append(element("p",compactText(working.summary||"No senior summary recorded.",420),"plan-summary"));
 if(working.summary)$("sharedSummary").append(buttonLink("Read full summary",()=>{const box=openDrawer("Shared working summary",working.source_query||"Senior notes");paragraph(box,"Current summary",working.summary);box.append(recordLink("memory/working","Summary provenance"))}));
 if(working.source_query)$("sharedSummary").append(element("p","Consolidated by "+working.source_query+" · original task notes remain retained.","secondary-line"));
 const covered=new Set(working.covered_note_refs||[]);
 const notes=Object.entries(agentRecords).filter(([key])=>key.startsWith("memory-note/")&&!covered.has(key));
 $("newNoteCount").textContent="New worker notes · "+notes.length;
 for(const [key,note] of notes){const box=element("div",undefined,"memory-note");box.append(element("p",previewText(note.content)),recordLink(key,note.author_ref||key));const task=agentTasks.find(task=>(note.provenance_refs||[]).includes(task.report_ref));if(task)box.append(element("span"," · "),buttonLink(task.id,()=>showTask(task.key)));$("agentNotes").append(box)}
}
function renderRepositorySummary(box,summary){
 if(!summary)return;
 for(const worker of summary.workers||[]){
  const row=element("div",undefined,"memory-note");
  row.append(element("strong",worker.task_id||worker.workspace_id||worker.branch||"Retained worktree"));
  paragraph(row,"Tip ancestry",worker.tip_is_ancestor===undefined?"Legacy ancestry-only summary; contribution unverified":worker.tip_is_ancestor?"Ancestor of current HEAD":"Outside current HEAD ancestry");
  paragraph(row,"Task contribution",worker.accepted_contribution===true?"Accepted contribution":worker.publication_recorded?"Published; review: "+(worker.review_action||"unreviewed"):"No recorded task publication");
  paragraph(row,"Source",(worker.code_location||"unrecorded")+" · "+(worker.changes?"uncommitted changes retained":"no recorded uncommitted changes"));
  paragraph(row,"Location",worker.path||"unavailable");
  if(worker.report_ref)row.append(recordLink(worker.report_ref,"Task report"));
  box.append(row);
 }
}
function renderAcceptance(){
 const facts=acceptanceFacts(agentRecords,osState?.operations||[]),run=facts.run,accepted=facts.accepted;
 const inPlace=agentRecords["repository/setup"]?.isolated===false;
 $("acceptanceStatus").textContent=accepted?"Accepted":"Not accepted";$("acceptanceStatus").className="badge "+(accepted?"resolved":"");
 $("acceptanceSummary").textContent=accepted?(inPlace?"Accepted revision is in the project repository.":run.status==="completed"?"Accepted revision and delivered output.":"Project checks accepted; output delivery is pending or blocked."):"Acceptance requires senior review and final evidence on the current project revision.";
 $("acceptanceChecks").replaceChildren(...facts.items.map(([label,passed,detail])=>{
  const row=element("div",undefined,"acceptance-item "+(passed?"passed":"pending"));row.append(element("span",passed?"✓":"○","check-icon"),secondary(label,detail));return row;
 }));
 const box=$("acceptanceDetails");box.replaceChildren();
 box.append(element("p","Provisional: "+(facts.head?.commit_id||"unrecorded")+"\nReviewed: "+(facts.reviewed?.commit_id||"unrecorded"),"policy"));
 for(const check of facts.checks){const line=element("p");line.append(stateBadge(check.status),element("span"," "+check.criterion_ref+" · "+evidenceFreshness(check,facts.head)));box.append(line);artifactLinks(box,[check.invocation,check.output])}
 if(run.acceptance_ref)box.append(recordLink(run.acceptance_ref,"Acceptance receipt"));
 if(run.output)paragraph(box,inPlace?"Project checkout":"Delivered output",typeof run.output==="string"?run.output:run.output.directory||pretty(run.output));
 if(inPlace){paragraph(box,"Integration branch",agentRecords["repository/setup"].base_branch||"detached HEAD");box.append(recordLink("coding/repository-summary","Repository branches and worker paths"));renderRepositorySummary(box,agentRecords["coding/repository-summary"])}
 if(run.output_error||run.output_failure)paragraph(box,"Delivery issue",pretty(run.output_error||run.output_failure));
 if(accepted&&run.status==="paused"&&run.blocker)paragraph(box,"Delivery blocked",monitorData?.blocker_detail||run.blocker);
 if(facts.receipt&&!accepted)paragraph(box,"Earlier acceptance is stale","The recorded acceptance no longer matches the current revision, plan, input watermark or settled work. A new acceptance is required.");
 if(agentRecords["outputs/target"])box.append(recordLink("outputs/target","Output destination"));
}
function renderUserMessages(messages){
 const box=$("userMessages"),previous=box.dataset.messages||"",signature=JSON.stringify(messages);
 if(signature===previous)return;
 box.dataset.messages=signature;const bottom=box.scrollHeight-box.scrollTop-box.clientHeight<40;
 box.replaceChildren();
 if(!messages.length){box.append(element("p","No messages yet."));return}
 for(const message of messages){
  const row=element("div",undefined,"memory-note");
  row.append(element("span",(message.scope?.process_id||"Agent")+" · "+stamp(message.created_at),"subtle"),element("p",message.text));
  box.append(row);
 }
 if(bottom)box.scrollTop=box.scrollHeight;
}
function renderOS(data){
 monitorData=data;if(activityRun!==data.id){activityRun=data.id;activityPage=null;taskFilter="all";$("taskSearch").value="";++inspection;if($("osInspector").open)$("osInspector").close()}
 osState=data.os||null;
 updateResumePanel();
 const targets=["osProcesses","finishedProcesses","admissionLanes","criticalSections","reservationTable","osBudgets","osLimits","osWorkspaces","retainedWorkspaces","osOperations","settledOperations","osActivity","osRecords"];
 if(!osState){$("osCapture").textContent="OS telemetry is unavailable in this snapshot.";for(const id of targets)$(id).replaceChildren();$("snapshotNote").hidden=true;$("osBlocker").hidden=true;return}
 const runtime=osState,run=runtime.control||{},journal=runtime.journal;
 $("osCapture").textContent=(savedDocument?"Saved snapshot":runtime.coordinator_running?"Live coordinator · durable snapshot":"Coordinator stopped · retained state")+" · "+stamp(runtime.captured_at);
 $("kernelVersion").textContent=runtime.kernel?.version||"Kernel version unrecorded";$("osRepository").textContent=data.repository||"Repository unrecorded";
 $("kernelDetails").replaceChildren(recordLink("runtime/kernel","Kernel record"));if(run.program)disclosure($("kernelDetails"),"Pinned agent program",run.program);
 if(data.reporting_errors?.length)disclosure($("kernelDetails"),"Observer/reporting errors",data.reporting_errors);
 const notes=[];
 if(!runtime.coordinator_running)notes.push("States and owners are retained records; they do not prove a host process or provider job is still running.");
 if(journal.pruned_events)notes.push(number(journal.pruned_events)+" earlier transactions expired from the journal retention window.");
 if(journal.legacy_events)notes.push(number(journal.legacy_events)+" legacy transactions lack complete timing or historical values.");
 $("snapshotNote").hidden=!notes.length;$("snapshotNote").textContent=notes.join(" ");
 const unknown=runtime.operations.filter(row=>row.state==="uncertain"),blocker=$("osBlocker");blocker.replaceChildren();blocker.hidden=!data.blocker&&!unknown.length;
 if(!blocker.hidden){blocker.append(element("strong",unknown.length?"Execution outcome unknown":"Recorded blocker"),element("p",compactText(data.blocker_detail||data.blocker||unknown.length+" operations require reconciliation.",240)),buttonLink("Read full diagnostic",showRunIssue));for(const row of unknown)blocker.append(element("span"," · "),buttonLink((row.capability||row.kind)+" · "+row.process_id,()=>showOperation(row)))}
 const active=runtime.processes.filter(row=>!terminalProcess(row.state)),finished=runtime.processes.filter(row=>terminalProcess(row.state));
 $("processCount").textContent=active.length+" active / retained nonterminal";$("finishedProcessCount").textContent="Finished processes · "+finished.length;
 const processRows=rows=>rows.map(row=>{
  const effects=runtime.operations.filter(item=>item.process_id===row.process_id&&!settledOperation(item.state));
  const started=terminalProcess(row.state)?row.started_at:effects[0]?.created_at||row.started_at;
  return [secondary(buttonLink(row.process_id,()=>showProcess(row.process_id)),row.process_id==="controller"?"controller":row.role),secondary(stateBadge(row.state),row.status?.phase||""),secondary(processActivity(row),row.control?.cancel_requested?"Cancellation requested; current effects must settle":""),row.status?.binding_ref||row.endpoint||"—",started&&(!terminalProcess(row.state)||row.finished_at)?duration(started,row.finished_at):"—"];
 });
 table("osProcesses",["Process / role","State / phase","Activity / wait","Endpoint","Elapsed"],processRows(active),"No active processes recorded.");
 table("finishedProcesses",["Process / role","State / phase","Last activity","Endpoint","Recorded duration"],processRows(finished),"No finished processes recorded.");
 const lanes=$("admissionLanes");lanes.replaceChildren();
 for(const lane of runtime.lanes){
  const box=element("div",undefined,"lane"),title=element("div",undefined,"lane-heading");title.append(element("strong",lane.name+" endpoint"),element("span",lane.held+" / "+(lane.limit??"?")+" slots"));box.append(title,element("div",(lane.model||"Model unrecorded")+" · "+(lane.protocol||"protocol unrecorded"),"lane-model"));
  const meter=element("div",undefined,"meter"),fill=element("span");fill.style.width=Math.min(100,lane.held/(lane.limit||1)*100)+"%";meter.append(fill);box.append(meter);
  box.append(element("p",number(lane.reserved_tokens)+" / "+number(lane.token_limit)+" reserved context tokens · "+(lane.ordinary_waiters+lane.finishing_waiters)+" waiting","policy"));lanes.append(box);
 }
 const reservations=runtime.reservations.slice().sort((a,b)=>(a.state==="waiting"?0:1)-(b.state==="waiting"?0:1)||(b.queued_at||"").localeCompare(a.queued_at||""));
 table("reservationTable",["Operation","Endpoint / lane","State","Queue wait","Slot hold"],reservations.slice(0,100).map(row=>[recordLink(row.key,row.operation_id),row.key.split("/")[1]+" / "+(row.lane||"unrecorded"),stateBadge(row.state),row.admitted_at||row.released_at||row.state==="waiting"?duration(row.queued_at,row.admitted_at||row.released_at):"—",row.admitted_at&&(row.released_at||row.state==="held")?duration(row.admitted_at,row.released_at):"—"]));
 $("reservationTable").append(element("p",Math.min(100,reservations.length)+" of "+reservations.length+" reservations. Inspect records or Save for full history.","subtle"));
 const critical=runtime.critical_sections.map(row=>[recordLink(row.key,resourceName(row.resource)),row.process_id?buttonLink(row.process_id,()=>showProcess(row.process_id)):"Available",row.process_id?duration(row.acquired_at):"—",runtime.ownership_waits.filter(item=>item.resource===row.resource&&item.state==="waiting").map(item=>item.process_id+" · "+duration(item.queued_at)).join("; ")||"—"]);
 for(const row of runtime.ownership_waits.filter(row=>row.state==="waiting"&&!runtime.critical_sections.some(item=>item.resource===row.resource)))critical.push([recordLink(row.key,resourceName(row.resource)),"Owner unrecorded","—",row.process_id+" · "+duration(row.queued_at)]);
 table("criticalSections",["Resource","Owner","Hold time","Waiters"],critical,"No exclusive resource records yet.");
 $("workerResidency").textContent=(run.active_workers||[]).length+" / "+(runtime.policy.max_workers??"?")+" resident coding workers. Started waiters count; finished unresolved reports do not. Control and senior queries have separate capacity.";
 table("osBudgets",["Account","Reserved / used"],runtime.budgets.map(row=>[recordLink(row.key),row.reserved_or_used!==undefined?number(row.reserved_or_used)+" tokens":"≈ $"+(Number(row.estimated_microusd||0)/1e6).toFixed(4)]));
 const names={run_token_budget:"Run token allowance",control_token_reserve:"Protected control tokens",run_spend_budget_microusd:"Estimated spend ceiling (micro USD)",max_artifact_bytes:"Artifact storage limit (bytes)",max_workspace_bytes:"Per-workspace limit (bytes)",max_workspace_total_bytes:"Aggregate workspace limit (bytes)",max_queued_operations:"Queued operation limit"};
 $("osLimits").replaceChildren();for(const [key,value] of Object.entries(runtime.limits||{}))if(names[key])$("osLimits").append(element("p",names[key]+": "+(value===0&&key==="run_spend_budget_microusd"?"No enforced ceiling":number(value)),"policy"));
 const workspaceRows=rows=>rows.map(row=>{
  const grant=runtime.workspace_grants?.find(item=>item.workspace_id===row.workspace_id),scope=secondary((row.allowed_write_paths||[]).length+" writable paths",(row.allowed_write_paths||[]).slice(0,3).join(", ")+(row.allowed_write_paths?.length>3?"…":""));
  if(grant?.expandable)scope.append(element("span","May request additional project paths","secondary-line"));
  return [recordLink(row.key,row.workspace_id||row.key),buttonLink(row.process_id||"unrecorded",()=>showProcess(row.process_id)),row.view||"unrecorded",scope,row.generation??"—"];
 });
 const liveIds=new Set(active.map(row=>row.process_id)),live=runtime.workspaces.filter(row=>liveIds.has(row.process_id)),retained=runtime.workspaces.filter(row=>!liveIds.has(row.process_id));
 table("osWorkspaces",["Workspace","Owner","View","Write scope","Generation"],workspaceRows(live),"No active file workspaces.");table("retainedWorkspaces",["Workspace","Owner","View","Write scope","Generation"],workspaceRows(retained));
 $("retainedWorkspaceCount").textContent="Retained workspace history · "+retained.length;
 renderOperations();renderActivity();renderRecords();
 $("journalInfo").textContent=number(journal.count)+" retained transactions · #"+(journal.first_sequence??"—")+"–"+(journal.last_sequence??"—")+". Showing the latest 120 transactions; Older transactions pages through retained history. Save includes the full retained journal.";
}
function renderOperations(){
 if(!osState)return;
 const all=osState.operations.filter(row=>matches(row,$("operationSearch").value)),pending=all.filter(row=>!settledOperation(row.state)).sort((a,b)=>(a.state==="uncertain"?0:1)-(b.state==="uncertain"?0:1)),settled=all.filter(row=>settledOperation(row.state)).sort((a,b)=>(b.created_at||"").localeCompare(a.created_at||""));
 const rows=items=>items.map(row=>[secondary(buttonLink(row.capability||row.kind||"operation",()=>showOperation(row)),row.operation_id),buttonLink(row.process_id||"unrecorded",()=>showProcess(row.process_id)),stateBadge(row.state==="uncertain"?"unknown-execution":row.state),row.state==="uncertain"?"Termination unconfirmed":row.deadline?stamp(row.deadline):"—"]);
 table("osOperations",["Operation / capability","Process","State","Deadline / issue"],rows(pending),"No outstanding operations match.");
 table("settledOperations",["Operation / capability","Process","State","Deadline"],rows(settled.slice(0,100)));
 $("settledOperationCount").textContent="Settled operation history · "+settled.length+ (settled.length>100?" · latest 100 shown; filter to narrow":"");
}
