// Exercise the shipped UI script with controlled HTTP timing, using Node's stdlib.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.children = []; this.dataset = {}; this.attributes = {};
    this.textContent = ''; this.disabled = false; this.hidden = false; this._value = '';
    this.classList = {toggle() {}};
    this.style = {};
  }
  get options() { return this.children; }
  get value() { return this._value; }
  set value(value) {
    this._value = this.tag === 'select' && !this.options.some(option => option.value === value) ? '' : value;
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) {
    this.children = nodes;
    if (this.tag === 'select') this._value = nodes[0]?.value || '';
  }
  setAttribute(key, value) { this.attributes[key] = value; }
  removeAttribute(key) { delete this.attributes[key]; }
  focus() { this.focused = true; }
  querySelector(selector) {
    const found = this.children.find(child => child instanceof Element &&
      (selector.startsWith('.') ? (child.className || '').split(' ').includes(selector.slice(1)) : child.tag === selector));
    return found || this.children.map(child => child instanceof Element ? child.querySelector(selector) : null).find(Boolean) || null;
  }
  showModal() { this.open = true; }
  close() { this.open = false; }
}

const response = (data, status = 200) => ({ok: status < 400, json: async () => data});
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return {promise, resolve}; };
const flush = () => new Promise(resolve => setImmediate(resolve));
const view = (id, status = 'completed', error = null) => ({
  id, status, error, state: '/state/' + id, repository: '/project', processes: [],
  cost: {}, steering_received: 0, steering_applied: 0,
});
const listing = runs => ({
  runs, repository: '/project', objective: 'Old objective', check_command: 'python -m pytest',
  total_cost: {estimated_usd: 0}, configuration: 'Fixture', browse_root: '/',
});

function pausedProcess(app) {
  vm.runInContext(`current="old";hasRunningRun=false;
    osState={processes:[{process_id:"worker",state:"paused",key:"process-status/worker"},
      {process_id:"controller",state:"paused",key:"process-status/controller"}],operations:[]};
    monitorData={id:"old",processes:[],resume:{allowed:true}};showProcess("worker");`, app.context);
  return vm.runInContext('resumePanel', app.context);
}

test('paused process sends one resume signal with optional steering to its selected run', async () => {
  for (const text of ['', 'Preserve <existing> source.']) {
    const app = await ui(), panel = pausedProcess(app), post = deferred();
    let requests = 0, submitted;
    panel.text.value = text; panel.text.oninput();
    app.setHandler(async (url, options) => {
      if (options?.method === 'POST') {
        assert.equal(url, '/api/resume'); requests++; submitted = JSON.parse(options.body); return post.promise;
      }
      return response(url === '/api/runs' ? listing([view('old', 'running')]) : view('old', 'running'));
    });
    const sending = panel.button.onclick();
    assert.equal(panel.button.disabled, true);
    await panel.button.onclick();
    assert.equal(requests, 1);
    assert.deepEqual(submitted, {id: 'old', process_id: 'worker', text});
    assert.equal(panel.text.value, text); // Keep instructions until acknowledgement.
    post.resolve(response({id: 'old', process_id: 'worker', request_ref: 'resume-request/one'}, 202));
    await sending; await flush();
    assert.equal(panel.text.value, '');
    assert.match(panel.status.textContent, /Resume signal sent/);
    assert.equal(app.elements.get('runs').value, 'old');
  }
});

test('resume errors retain drafts and late replies cannot affect another process drawer', async () => {
  const app = await ui(), panel = pausedProcess(app);
  panel.text.value = 'Keep my instructions'; panel.text.oninput();
  app.setHandler(async (url, options) => options?.method === 'POST'
    ? response({error: 'Reconcile unsettled operations first'}, 400)
    : response(url === '/api/runs' ? listing([view('old', 'paused')]) : view('old', 'paused')));
  await panel.button.onclick(); await flush();
  assert.equal(panel.text.value, 'Keep my instructions');
  assert.match(panel.status.textContent, /Reconcile unsettled/);
  assert.equal(panel.button.disabled, false);
  const post = deferred();
  app.setHandler(async (url, options) => options?.method === 'POST' ? post.promise
    : response(url === '/api/runs' ? listing([view('old', 'paused')]) : view('old', 'paused')));
  const sending = panel.button.onclick();
  vm.runInContext('showProcess("controller")', app.context);
  const next = vm.runInContext('resumePanel', app.context);
  next.text.value = 'Different process instructions';
  post.resolve(response({error: 'old request failed'}, 400));
  await sending; await flush();
  assert.equal(next.status.textContent, '');
  assert.equal(next.text.value, 'Different process instructions');
  vm.runInContext('showProcess("worker")', app.context);
  assert.equal(vm.runInContext('resumePanel.text.value', app.context), 'Keep my instructions');
});

test('resume controls respect saved snapshots, blockers, active runs and refreshed process status', async () => {
  const app = await ui();
  pausedProcess(app);
  vm.runInContext('savedDocument={};updateResumePanel()', app.context);
  assert.equal(vm.runInContext('resumePanel.button.disabled', app.context), true);
  assert.match(vm.runInContext('resumePanel.hint.textContent', app.context), /read-only/);
  vm.runInContext('savedDocument=null;monitorData.resume={allowed:false,reason:"Reconcile unknown execution"};updateResumePanel()', app.context);
  assert.equal(vm.runInContext('resumePanel.button.disabled', app.context), true);
  assert.match(vm.runInContext('resumePanel.hint.textContent', app.context), /Reconcile/);
  vm.runInContext('monitorData.resume={allowed:true};hasRunningRun=true;updateResumePanel()', app.context);
  assert.equal(vm.runInContext('resumePanel.button.disabled', app.context), true);
  vm.runInContext('hasRunningRun=false;osState.processes[0].state="running";updateResumePanel()', app.context);
  assert.match(vm.runInContext('resumePanel.hint.textContent', app.context), /no longer paused/);
});

test('Resume click immediately starts the selected run with optional inline instructions and no process choice', async () => {
  for (const text of ['', 'Keep my worker changes']) {
    const app = await ui(), $ = id => app.elements.get(id), post = deferred();
    let posts = 0, submitted;
    app.setHandler(async (url, options) => {
      if (options?.method === 'POST') {posts++; submitted = JSON.parse(options.body); return post.promise;}
      return response(url === '/api/runs' ? listing([view('old', 'running')]) : view('old', 'running'));
    });
    vm.runInContext('render({id:"old",status:"paused",processes:[],cost:{},resume:{allowed:true}})', app.context);
    assert.equal($('resumeFields').hidden, false);
    $('resumeText').value=text; $('resumeText').oninput();
    const sending=$('resumeRun').onclick();
    assert.equal(posts, 1);
    assert.equal(submitted.id, 'old'); assert.equal(submitted.text, text);
    assert.equal(typeof submitted.request_id, 'string'); assert.ok(submitted.request_id.length);
    assert.equal('process_id' in submitted, false);
    assert.equal($('osInspector').open, undefined);
    assert.equal($('resumeRun').disabled, true); assert.equal($('resumeRun').textContent, 'Resuming…');
    await $('resumeRun').onclick(); assert.equal(posts,1);
    post.resolve(response({id:'old',request_ref:'resume-request/one'},202));
    await sending; await flush();
    assert.equal($('resumeText').value, '');
  }
});

test('Resume shows background recovery and respects read-only snapshots', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  app.context.pending={id:'old',status:'running',processes:[],cost:{},resume:{allowed:true,progress:'recovering'}};
  vm.runInContext('render(pending)',app.context);
  assert.equal($('resumeRun').hidden,false); assert.equal($('resumeRun').disabled,true);
  assert.equal($('status').textContent,'resuming');
  assert.match($('resumeStatus').textContent,/Preparing/);
  assert.equal($('sendSteering').disabled,true);
  vm.runInContext('savedDocument={};render({...pending,status:"paused",resume:{}})',app.context);
  assert.equal($('resumeRun').disabled,true); assert.equal($('resumeText').disabled,true);
  vm.runInContext('savedDocument=null;render({...pending,status:"completed",resume:{}})',app.context);
  assert.equal($('resumeRun').hidden,true);
});

test('Resume retains instructions and request identity after a lost acknowledgement and page restart', async () => {
  const storage=new Map(), app=await ui({storage}), $=id=>app.elements.get(id);
  vm.runInContext('render({id:"old",status:"paused",processes:[],cost:{},resume:{allowed:true}})',app.context);
  $('resumeText').value='Preserve this'; $('resumeText').oninput();
  let first;
  app.setHandler(async (url,options)=> {
    if(options?.method==='POST'){first=JSON.parse(options.body);throw new Error('Connection lost');}
    return response(url==='/api/runs'?listing([view('old','paused')]):view('old','paused'));
  });
  await $('resumeRun').onclick(); await flush();
  assert.equal($('resumeText').value,'Preserve this'); assert.match($('resumeStatus').textContent,/Connection lost/);
  const next=await ui({storage}), $next=id=>next.elements.get(id);
  vm.runInContext('render({id:"old",status:"paused",processes:[],cost:{},resume:{allowed:true}})',next.context);
  assert.equal($next('resumeText').value,'Preserve this');
  let retried;
  next.setHandler(async (url,options)=> {
    if(options?.method==='POST'){retried=JSON.parse(options.body);return response({id:'old'},202);}
    return response(url==='/api/runs'?listing([view('old','running')]):view('old','running'));
  });
  await $next('resumeRun').onclick(); await flush(); assert.deepEqual(retried,first);
  assert.equal(storage.size,0);
});

test('a later poll acknowledges a lost Resume reply and the next pause creates a new request', async () => {
  const app=await ui(), $=id=>app.elements.get(id);let first,next;
  vm.runInContext('render({id:"old",status:"paused",processes:[],cost:{}})',app.context);
  $('resumeText').value='Keep this';$('resumeText').oninput();
  app.setHandler(async (url,options)=> {
    if(options?.method==='POST'){first=JSON.parse(options.body);throw new Error('Lost reply');}
    return response(url==='/api/runs'?listing([view('old','paused')]):view('old','paused'));
  });
  await $('resumeRun').onclick();await flush();
  app.context.ack={...view('old','running'),resume:{request_id:first.request_id,progress:'running'}};
  vm.runInContext('render(ack)',app.context);
  assert.equal($('resumeText').value,'');
  vm.runInContext('hasRunningRun=false;render({...ack,status:"paused"})',app.context);
  app.setHandler(async (url,options)=> {
    if(options?.method==='POST'){next=JSON.parse(options.body);return response({id:'old'},202);}
    return response(url==='/api/runs'?listing([view('old','running')]):view('old','running'));
  });
  await $('resumeRun').onclick();await flush();
  assert.notEqual(next.request_id,first.request_id);assert.equal(next.text,'');
});

test('simulation controls and launch payload remain absent without the flag', async () => {
  const app = await ui();
  assert.equal(app.elements.get('inferenceSetup').hidden, true);
  assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(simulationOptions())', app.context)), {});
  assert.equal(app.elements.get('inferenceStatus').hidden, true);
});

test('enabled simulation exposes three modes and preserves edited settings across polling', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  vm.runInContext('setupSimulation({batch:3})', app.context);
  assert.equal($('inferenceSetup').hidden, false);
  assert.equal($('simMode').options.length, 3);
  const fields = {simTPS:'30',simBatch:'2',simBugRate:'5',simSeed:'123',simPrefill:'1.5',simPromptTPS:'2000',
    simJitter:'0.2',simStallRate:'5',simStallSeconds:'3',simRestart:'15'};
  for(const [id,value] of Object.entries(fields))$(id).value=value;
  vm.runInContext('setupSimulation({batch:9})', app.context);
  let selected = JSON.parse(vm.runInContext('JSON.stringify(simulationOptions())', app.context));
  assert.deepEqual(selected.simulation, {mode:'slow-buggy',tps:30,batch:2,bug_rate:5,seed:123,prefill_seconds:1.5,
    prefill_tps:2000,jitter:0.2,stall_rate:5,stall_seconds:3,restart_seconds:15});
  $('simMode').value='buggy';$('simMode').onchange();
  selected = JSON.parse(vm.runInContext('JSON.stringify(simulationOptions())', app.context));
  assert.deepEqual(selected, {simulation:{mode:'buggy',batch:2,bug_rate:5,restart_seconds:15,seed:123}});
  assert.equal($('simTPS').disabled, true);
  $('simMode').value='normal';$('simMode').onchange();
  assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(simulationOptions())', app.context)), {simulation:{mode:'normal'}});
  assert.equal($('simBatch').disabled, true);
});

test('simulation inspection renders saved and live facts as plain text', async () => {
  const app = await ui(), box=app.elements.get('inferenceStatus');
  vm.runInContext(`savedDocument={configuration:{inference_simulation:{mode:'slow-buggy',tps:30,batch:2,bug_rate:5,seed:7}},records:{
    'simulation/inference/attempt/a':{process_id:'<img src=x>',phase:'decoding',elapsed_seconds:5,output_tokens:100,simulated_tokens:30,injected:false,incident_started:false},
    'simulation/inference/attempt/b':{phase:'failed',injected:true,incident_started:true}}};renderSimulation(savedSimulation());`, app.context);
  assert.equal(box.hidden, false);
  assert.match(box.children[0].textContent, /30 shared TPS.*seed 7/);
  assert.match(box.children[1].textContent, /incidents: 1.*affected attempts: 1/);
  assert.match(box.children[2].textContent, /^<img src=x>.*virtual tokens 30 \/ 100/);
  vm.runInContext('renderSimulation(null)', app.context);
  assert.equal(box.hidden, true);
});

test('agent messages render full plain text across polling and run changes', async () => {
  const app = await ui(), box = app.elements.get('userMessages');
  const text = '<img src=x onerror=alert(1)>\n' + 'Progress. '.repeat(100);
  app.context.notifications = [{key: 'user-message/one', text, scope: {process_id: 'researcher'}, created_at: '2026-10-19T12:00:00Z'}];
  vm.runInContext('renderUserMessages(notifications)', app.context);
  assert.equal(box.children.length, 1);
  assert.equal(box.children[0].children[1].textContent, text);
  assert.match(box.children[0].children[0].textContent, /researcher/);
  const row = box.children[0];
  vm.runInContext('renderUserMessages(notifications)', app.context);
  assert.equal(box.children[0], row); // Unchanged polls do not repeat live announcements.
  vm.runInContext('renderUserMessages([])', app.context);
  assert.equal(box.children.length, 1);
  assert.equal(box.children[0].textContent, 'No messages yet.');
});

async function ui({monitoring = false, storage = new Map()} = {}) {
  const html = fs.readFileSync(path.join(__dirname, '../src/polyinference/ui.html'), 'utf8');
  const elements = new Map([...html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"/g)]
    .map(([, tag, id]) => [id, new Element(tag)]));
  let handler = async url => response(url === '/api/runs' ? listing([view('old')]) : view('old'));
  const context = vm.createContext({
    document: {getElementById: id => elements.get(id), createElement: tag => new Element(tag),
      createTextNode: text => Object.assign(new Element('#text'), {textContent: text}), querySelectorAll: () => []},
    Node: Element, URL, URLSearchParams, Blob,
    localStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value),removeItem:key=>storage.delete(key)},
    Option: function(text, value) { const option = new Element('option'); option.textContent = text; option.value = value; return option; },
    fetch: (...args) => handler(...args), setInterval() {}, matchMedia: () => ({matches: false}), TextDecoder, atob,
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../src/polyinference/ui-monitor.js'), 'utf8'), context);
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  // Keep the real launch, polling, selection and error rendering. Unrelated OS
  // tables and provider cost formatting are covered by the Python HTTP tests.
  vm.runInContext((monitoring ? '' : 'renderOS=()=>{};') + 'showCost=()=>{};', context);
  await flush();
  return {elements, context, setHandler: value => { handler = value; }};
}

test('accepted start selects its run immediately, despite a stale poll and repeated click', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  const oldPoll = deferred(), post = deferred();
  let posts = 0, lists = 0;
  app.setHandler(async (url, options) => {
    if (options?.method === 'POST') { posts++; return post.promise; }
    if (url === '/api/runs') return ++lists === 1 ? oldPoll.promise : response(listing([view('new', 'running'), view('old')]));
    return response(view('new', 'running'));
  });
  const polling = vm.runInContext('refresh()', app.context);
  const starting = $('start').onclick();
  assert.equal($('start').textContent, 'Starting…');
  assert.equal($('start').disabled, true);
  await $('start').onclick();
  assert.equal(posts, 1);
  post.resolve(response({id: 'new'}, 202));
  await starting;
  assert.equal($('runs').value, 'new');
  assert.equal($('status').textContent, 'running');
  assert.equal($('export').attributes['aria-disabled'], 'false');
  oldPoll.resolve(response(listing([view('old')])));
  await polling; await flush();
  assert.equal($('runs').value, 'new');
  assert.equal($('start').disabled, true);
});

test('rejected start selects the saved failed attempt and keeps its exact error across polls', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  const message = 'Enter a test objective of 1–16000 characters';
  let posted;
  $('checkCommand').value = '';
  app.setHandler(async (url, options) => {
    if (options?.method === 'POST') {
      posted = JSON.parse(options.body);
      return response({id: 'rejected', process_id: 'startup-rejected', status: 'failed', error: message}, 400);
    }
    return response(url === '/api/runs' ? listing([view('rejected', 'failed', message), view('old')]) : view('rejected', 'failed', message));
  });
  await $('start').onclick(); await flush();
  assert.equal(posted.check_command, ''); // Validation still creates a server-side attempt.
  assert.notEqual($('checkCommand').focused, true);
  assert.equal($('runs').value, 'rejected');
  assert.equal($('status').textContent, 'failed');
  assert.equal($('export').attributes['aria-disabled'], 'false');
  assert.match($('export').href, /id=rejected/);
  assert.equal($('launchError').hidden, false);
  assert.equal($('launchError').textContent, 'Could not start run rejected: ' + message);
  await vm.runInContext('refresh()', app.context);
  assert.equal($('launchError').textContent, 'Could not start run rejected: ' + message);
  assert.equal($('start').disabled, false);
});

test('network error stays visible while the old run refreshes; a successful retry clears it', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  app.setHandler(async (url, options) => {
    if (options?.method === 'POST') throw Error('Failed to fetch');
    return response(url === '/api/runs' ? listing([view('old')]) : view('old'));
  });
  await $('start').onclick(); await flush();
  assert.equal($('runs').value, 'old');
  assert.match($('launchError').textContent, /Failed to fetch/);
  await vm.runInContext('refresh()', app.context);
  assert.match($('launchError').textContent, /Failed to fetch/);
  app.setHandler(async (url, options) => response(options?.method === 'POST' ? {id: 'retry'} : url === '/api/runs' ? listing([view('retry', 'running')]) : view('retry', 'running')));
  await $('start').onclick(); await flush();
  assert.equal($('runs').value, 'retry');
  assert.equal($('launchError').hidden, true);
  assert.equal($('launchStatus').textContent, 'Started run retry.');
});

test('starting from a snapshot returns to live view and exposes an immediate initialization error', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  vm.runInContext('savedDocument={};current="snapshot:old";', app.context);
  $('runs').disabled = true;
  app.setHandler(async (url, options) => {
    const failed = {...view('early', 'failed', 'Provider credentials missing'), failure_stage: 'startup', process_id: 'startup-early'};
    return response(options?.method === 'POST' ? {id: 'early'} : url === '/api/runs' ? listing([failed]) : failed);
  });
  await $('start').onclick(); await flush();
  assert.equal(vm.runInContext('savedDocument', app.context), null);
  assert.equal($('runs').disabled, false);
  assert.equal($('runs').value, 'early');
  assert.equal($('status').textContent, 'failed');
  assert.equal($('error').textContent, 'Provider credentials missing');
  assert.match($('message').textContent, /startup-early/);
  assert.match($('export').href, /id=early/);
  assert.equal($('export').attributes['aria-disabled'], 'false');
});


test('blank check command starts automatically without opening settings or stealing focus', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  $('checkCommand').value = '';
  $('checkSettings').open = false;
  let posted;
  app.setHandler(async (url, options) => {
    if (options?.method === 'POST') { posted = JSON.parse(options.body); return response({id: 'auto'}, 202); }
    return response(url === '/api/runs' ? listing([view('auto', 'running')]) : view('auto', 'running'));
  });
  await $('start').onclick(); await flush();
  assert.equal(posted.check_command, '');
  assert.equal($('checkSettings').open, false);
  assert.notEqual($('checkCommand').focused, true);
  assert.equal($('runs').value, 'auto');
  assert.equal($('status').textContent, 'running');
});

test('paused run shows its original operation diagnostic instead of an opaque blocker id', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  const diagnostic = 'Codex app-server exited without a terminal turn';
  const paused = {...view('old', 'paused', diagnostic), blocker: 'sha256:operation', blocker_detail: diagnostic,
    reporting_errors: ['BrokenPipeError: closed terminal']};
  app.setHandler(async url => response(url === '/api/runs' ? listing([paused]) : paused));
  await vm.runInContext('refresh()', app.context);
  assert.equal($('status').textContent, 'paused');
  assert.equal($('error').textContent, diagnostic);
  assert.equal($('message').textContent, 'Stopped: ' + diagnostic);
  assert.equal($('start').disabled, false);
});

const textOf = element => [element.textContent, ...element.children.map(textOf)].join(' ');
const descendants = element => [element,...element.children.flatMap(descendants)];

function contextFixture() {
  const artifacts=[];
  function part(id,kind,text,extra={}) {
    const digest='sha256:'+require('node:crypto').createHash('sha256').update(text).digest('hex');
    artifacts.push({digest,data:Buffer.from(text).toString('base64')});
    return {part_id:id,part_kind:kind,trust:'user',required:false,compactable:true,
      content:{artifact_id:digest,digest,size_bytes:Buffer.byteLength(text)},...extra};
  }
  const instruction=part('instruction','instruction','Literal <img onerror=evil> café / 中文',{required:true,trust:'application'});
  const call=part('call','tool_call','tool invocation',{call_id:'pair'}), result=part('result','tool_result','tool result',{call_id:'pair'});
  const memory=part('notes','memory','Original memory '.repeat(1500));
  const summary=part('notes','summary','Effective summary',{trust:'model',derived_from:[memory.content.digest]});
  const original={view_id:'original',parts:[instruction,call,result,memory],memory_snapshot_refs:['opaque-handle','memory/generic']};
  const effective={view_id:'prepared',parts:[instruction,summary],memory_snapshot_refs:original.memory_snapshot_refs};
  const receipt={context_ref:'original',prepared_context_ref:'prepared',original_bytes:40000,submitted_bytes:900,
    required_bytes:500,input_allowance:1000,unit:'utf8_bytes_conservative_token_bound',omitted_refs:['call','result'],
    summaries:[{part_id:'notes',source:memory.content,summary:summary.content}],compaction_operations:['helper'],prepared_digest:'wire'};
  const records={'memory/generic':{summary:'Agent-owned memory'}};
  for(const [index,id] of ['root','output','transport','helper'].entries()) {
    const extensions={};
    if(['output','transport'].includes(id))extensions['runtime/output-retry']={root_operation_id:'root',previous_operation_id:'root'};
    if(id==='transport')extensions['runtime/model-retry']={root_operation_id:'output',previous_operation_id:'output'};
    if(id==='helper')extensions['runtime/context-compaction']=true;
    records['effect/'+id]={state:id==='transport'||id==='helper'?'succeeded':'failed',request:{operation_id:id,
      scope:{process_id:'generic'},logical_step_id:'model-'+index,created_at:'2026-10-21T12:00:0'+index+'Z',extensions,
      payload:{kind:'model_query',context:original}}};
  }
  records['effect/root'].attempted_backend={submitted:false};
  records['effect/transport'].result={extensions:{'polyinference/attempted-backend':{submitted:true}}};
  records['context-prepared/transport']={context:effective,receipt};
  records['context-receipt/transport']=receipt;
  records['context-receipt/root']={...receipt,submitted_bytes:40000,compaction_operations:[],summaries:[],omitted_refs:[]};
  records['output-retry-outcome/root']={operation_id:'transport'};
  records['model-retry-outcome/output']={result_operation_id:'transport'};
  return {records,artifacts,processes:[]};
}

test('context selection follows nested retries, excludes helpers and isolates malformed provenance', async () => {
  const app=await ui(); app.context.snapshot=contextFixture();
  const groups=vm.runInContext('savedDocument=snapshot;contextInvocations(contextOperations(),"generic")',app.context);
  assert.equal(groups.length,2); assert.equal(groups[0].selected.operation_id,'transport');
  assert.equal(groups[1].helper,true);
  vm.runInContext('delete snapshot.records["output-retry-outcome/root"];delete snapshot.records["model-retry-outcome/output"];',app.context);
  const noOutcome=vm.runInContext('contextInvocations(contextOperations(),"generic")',app.context);
  assert.equal(noOutcome[0].selected.operation_id,'transport');
  app.context.rows=JSON.parse(JSON.stringify(vm.runInContext('contextOperations()',app.context)));
  app.context.rows.push({operation_id:'other',process_id:'different',kind:'model_query',state:'active',created_at:'9'});
  app.context.rows.push({operation_id:'bad',process_id:'generic',kind:'model_query',state:'uncertain',created_at:'8',model_retry:{root_operation_id:'other',previous_operation_id:'other'}});
  let projected=vm.runInContext('contextInvocations(rows,"generic")',app.context);
  assert.equal(projected.at(-1).id,'bad'); assert.match(projected.at(-1).issue,/cross-process/);
  app.context.rows[0].model_retry={root_operation_id:'transport',previous_operation_id:'transport'};
  projected=vm.runInContext('contextInvocations(rows,"generic")',app.context);
  assert.ok(projected.some(group=>/cycle/.test(group.issue)));
});

test('saved context drawer is lazy, literal, provenance-aware and offline with original fallback', async () => {
  const app=await ui(); app.context.snapshot=contextFixture(); app.context.runtime=osFixture();
  vm.runInContext('savedDocument=snapshot;current="snapshot:generic";osState=runtime;',app.context);
  app.setHandler(()=>{throw Error('Saved context must stay offline')});
  await vm.runInContext('showMemory("generic")',app.context);
  let body=app.elements.get('osInspectorBody'), text=textOf(body);
  assert.match(text,/Effective prepared input/); assert.match(text,/Submission recorded/);
  assert.match(text,/prepared 900/); assert.doesNotMatch(text,/Original memory Original/);
  assert.match(text,/Summary provenance/); assert.match(text,/opaque-handle/);
  let load=descendants(body).find(node=>node.textContent==='Read full content'); await load.onclick();
  assert.match(textOf(body),/Literal <img onerror=evil> café \/ 中文/);
  await vm.runInContext('showMemory("generic","transport","original")',app.context);
  body=app.elements.get('osInspectorBody'); assert.match(textOf(body),/omitted by preparation/);
  const loads=descendants(body).filter(node=>node.textContent==='Read full content'); await loads.at(-1).onclick();
  assert.match(textOf(body),new RegExp('Original memory '.repeat(100)));
  await vm.runInContext('showMemory("generic","root")',app.context);
  text=textOf(app.elements.get('osInspectorBody'));
  assert.match(text,/Original supplied input · prepared input unavailable/); assert.match(text,/Recorded as not submitted/);
  assert.doesNotMatch(text,/Selected input Effective prepared input/);
  await vm.runInContext('showMemory("empty")',app.context);
  assert.match(textOf(app.elements.get('osInspectorBody')),/No model context recorded/);
});

test('live context refresh preserves attempt, distinguishes absent preparation and keeps errors local', async () => {
  const app=await ui(); const snapshot=contextFixture(); app.context.snapshot=snapshot; app.context.runtime=osFixture();
  const rows=vm.runInContext('savedDocument=snapshot;contextOperations()',app.context); app.context.rows=rows;
  vm.runInContext('savedDocument=null;current="live";osState=runtime;osState.operations=rows;',app.context);
  let artifacts=0;
  app.setHandler(url=>{const parsed=new URL(url,'http://fixture');
    if(parsed.pathname==='/api/artifact'){artifacts++;return response({text:'Downloaded content'})}
    const key=parsed.searchParams.get('key'); return response(snapshot.records[key]?{value:snapshot.records[key]}:{error:'Absent'},snapshot.records[key]?200:404);
  });
  await vm.runInContext('showMemory("generic","root")',app.context);
  assert.equal(artifacts,0); assert.match(textOf(app.elements.get('osInspectorBody')),/Recorded as not submitted/);
  snapshot.records['context-prepared/root']={context:snapshot.records['effect/root'].request.payload.context,
    receipt:{context_ref:'original',prepared_context_ref:'original',submitted_bytes:40000}};
  await app.elements.get('drawerRefresh').onclick();
  assert.match(textOf(app.elements.get('osInspectorBody')),/Effective prepared input/);
  assert.match(app.elements.get('osInspectorMeta').textContent,/generic/);
  snapshot.records['effect/root'].state='uncertain'; delete snapshot.records['effect/root'].attempted_backend;
  snapshot.records['context-prepared/root'].receipt.context_ref='mismatch';
  await app.elements.get('drawerRefresh').onclick();
  const text=textOf(app.elements.get('osInspectorBody'));
  assert.match(text,/Identity mismatch/); assert.match(text,/Submission evidence unavailable/); assert.match(text,/Termination remains unknown/);
  app.setHandler(()=>response({error:'Read failed'},500));
  await vm.runInContext('showMemory("generic","transport")',app.context);
  assert.match(textOf(app.elements.get('osInspectorBody')),/Record load failed/);
});

test('late context records and errors cannot replace drawers after close, Back, selection, run or snapshot changes', async () => {
  for(const steer of ['close','back','selection','run','snapshot']) {
    const app=await ui(); app.context.snapshot=contextFixture(); app.context.runtime=osFixture();
    app.context.rows=vm.runInContext('savedDocument=snapshot;contextOperations()',app.context);
    vm.runInContext('savedDocument=null;current="live";osState=runtime;osState.operations=rows;',app.context);
    const pending=deferred(); app.setHandler(()=>pending.promise);
    const loading=vm.runInContext('showMemory("generic","transport",null,()=>openDrawer("Back target",""))',app.context);
    if(steer==='close')app.elements.get('closeOSInspector').onclick();
    if(steer==='back')app.elements.get('drawerBack').onclick();
    if(steer==='run')vm.runInContext('current="another";openDrawer("New run","")',app.context);
    if(steer==='snapshot')vm.runInContext('savedDocument=snapshot;openDrawer("Snapshot","")',app.context);
    if(steer==='selection'){
      app.setHandler(url=>{const key=new URL(url,'http://fixture').searchParams.get('key');return response({value:app.context.snapshot.records[key]},app.context.snapshot.records[key]?200:404)});
      await vm.runInContext('showMemory("generic","root")',app.context);
    }
    const before=textOf(app.elements.get('osInspectorBody'));
    pending.resolve(response({error:'Stale error'},500)); await loading;
    assert.equal(textOf(app.elements.get('osInspectorBody')),before);
    assert.doesNotMatch(app.elements.get('error').textContent,/Stale error/);
    if(steer==='close')assert.equal(app.elements.get('osInspector').open,false);
  }
});

test('repository facts keep inherited ancestry, private source and accepted contribution distinct', async () => {
  const app = await ui();
  app.context.summary = {workers:[
    {task_id:'parked',tip_is_ancestor:true,code_location:'unreported',changes:' M a.py',path:'/private'},
    {task_id:'done',tip_is_ancestor:true,publication_recorded:true,accepted_contribution:true,code_location:'provisional',path:'/done'},
    {task_id:'old',merged:true,path:'/legacy'},
  ]};
  vm.runInContext('document.getElementById("acceptanceDetails").replaceChildren();renderRepositorySummary(document.getElementById("acceptanceDetails"),summary)', app.context);
  const rows = app.elements.get('acceptanceDetails').children;
  assert.match(textOf(rows[0]), /Ancestor of current HEAD/);
  assert.match(textOf(rows[0]), /No recorded task publication/);
  assert.match(textOf(rows[0]), /uncommitted changes retained/);
  assert.doesNotMatch(textOf(rows[0]), /Accepted contribution/);
  assert.match(textOf(rows[1]), /Accepted contribution/);
  assert.match(textOf(rows[2]), /Legacy ancestry-only summary; contribution unverified/);
  assert.doesNotMatch(textOf(rows[2]), /Accepted contribution/);
});
function monitorFixture() {
  const code = {repository_id:'repo', commit_id:'commit', effective_tree_digest:'tree', environment_digest:'env'};
  const records = {
    'app/run':{status:'active', sprint:2, plan_ref:'plan/2', starts_closed:true, active_workers:[],
      steering_received:0, steering_applied:0, completion_proposed:true, acceptance_ref:'acceptance-receipt/1'},
    'head/provisional':{code}, 'head/reviewed':{code:{...code}},
    'plan/2':{goal:'Deliver the accepted fix'},
    'acceptance-receipt/1':{code, steering_through:0, plan_ref:'plan/2',
      evidence:[{criterion_ref:'tests', status:'passed', checked_code:code}]},
    'memory/working':{summary:'Shared summary', covered_note_refs:['memory-note/kept']},
    'process/controller':{state:'waiting'},
  };
  for (const [id, action, verdict] of [['kept','keep','successful'],['rejected','revert','fail'],['retry','retry','uncertain'],['defer','defer','uncertain']]) {
    records['task/'+id] = {assignment:{task_id:id, objective:'A lengthy objective for '+id, role:'worker', checks:['tests']},
      category:'development', execution:'completed', process_id:'worker-'+id, attempt_id:id,
      plan_ref:'plan/2', spec_ref:'task-spec/'+id, report_ref:'report/'+id};
    records['report/'+id] = {execution:'completed', resolution:'unresolved', verdict,
      code_location:verdict==='fail'?'private':'provisional', final_code:code, assessment_summary:{digest:'note-'+id}};
    records['resolution/report/'+id] = {action, resolution_ref:'resolution-event/'+id};
    records['resolution-event/'+id] = {report_ref:'report/'+id, action, reason:{digest:'review-'+id}};
    records['memory-note/'+id] = {author_ref:'worker-'+id, content:{digest:'note-'+id}, provenance_refs:['report/'+id]};
  }
  records['task/parked'] = {assignment:{task_id:'parked', objective:'Needs a scope decision'}, execution:'interrupted', attempt_id:'parked'};
  const texts = Object.fromEntries(['kept','rejected','retry','defer'].flatMap(id => [
    ['note-'+id, JSON.stringify('Original worker note: '+id)], ['review-'+id, 'Senior reason: '+id]]));
  return {records, texts, code};
}
function osFixture() {
  return {captured_at:'2026-10-19T12:00:00Z', coordinator_running:false, kernel:{version:'simple-os/2'},
    control:{active_workers:[]}, policy:{max_workers:2}, processes:[], operations:[], lanes:[], reservations:[],
    critical_sections:[], ownership_waits:[], budgets:[], workspaces:[], record_index:[], activity:[],
    journal:{count:0, first_sequence:null, last_sequence:null, pruned_events:0, legacy_events:0}};
}

test('completed task review joins immutable reports without inventing verdicts or closing retry/defer', async () => {
  const app = await ui(); app.context.fixture = monitorFixture();
  const projected = JSON.parse(vm.runInContext('JSON.stringify(projectTasks(fixture.records,fixture.texts))', app.context));
  assert.deepEqual(projected.filter(task => task.resolved).map(task => task.id), ['kept','rejected']);
  assert.deepEqual(projected.filter(task => task.report && !task.resolved).map(task => task.id), ['retry','defer']);
  assert.equal(projected.find(task => task.id === 'parked').verdict, null);
  assert.equal(projected.find(task => task.id === 'kept').comment, 'Original worker note: kept');
  assert.equal(projected.find(task => task.id === 'kept').report.resolution, 'unresolved');
  assert.equal(vm.runInContext('taskReviewLabel(projectTasks(fixture.records)[1])', app.context), 'Rejected · resolved');
});

test('acceptance is tied to exact content, environment and steering, independent of object property order', async () => {
  const app = await ui(); app.context.fixture = monitorFixture();
  vm.runInContext('fixture.records["resolution/report/retry"].action="keep";fixture.records["resolution/report/defer"].action="keep";delete fixture.records["task/parked"];', app.context);
  vm.runInContext('fixture.records["head/reviewed"].code={environment_digest:"env",effective_tree_digest:"tree",commit_id:"commit",repository_id:"repo"};', app.context);
  assert.equal(vm.runInContext('acceptanceFacts(fixture.records).accepted', app.context), true);
  vm.runInContext('fixture.records["app/run"].active_workers=["started"];', app.context);
  assert.equal(vm.runInContext('acceptanceFacts(fixture.records).accepted', app.context), false);
  vm.runInContext('fixture.records["app/run"].active_workers=[];', app.context);
  vm.runInContext('fixture.records["app/run"].steering_received=1;', app.context);
  assert.equal(vm.runInContext('acceptanceFacts(fixture.records).accepted', app.context), false);
  vm.runInContext('fixture.records["app/run"].steering_received=0;fixture.records["head/provisional"].code={...fixture.code,environment_digest:"changed"};', app.context);
  assert.equal(vm.runInContext('acceptanceFacts(fixture.records).accepted', app.context), false);
  assert.equal(vm.runInContext('acceptanceFacts(fixture.records).items[4][1]', app.context), false);
});

test('two-tab monitor renders all tasks, filters resolved history and opens task notes with original execution', async () => {
  const app = await ui({monitoring:true}), $ = id => app.elements.get(id);
  app.context.fixture = monitorFixture(); app.context.runtime = osFixture();
  vm.runInContext('render({...monitorData,id:"fixture",status:"paused",processes:[],os:runtime,agents:fixture,cost:{}})', app.context);
  assert.match(textOf($('agentTasks')), /Kept/);
  assert.match(textOf($('agentTasks')), /Original worker note|Senior reason/);
  assert.match($('taskCount').textContent, /5 of 5/);
  const resolved = $('taskFilters').children.find(button => button.textContent.startsWith('Resolved'));
  resolved.onclick();
  assert.match($('taskCount').textContent, /2 of 5/);
  vm.runInContext('showTask("task/kept")', app.context);
  assert.equal($('osInspector').open, true);
  assert.match(textOf($('osInspectorBody')), /Original worker note: kept/);
  assert.match(textOf($('osInspectorBody')), /Senior reason: kept/);
  assert.equal($('executionDetails').hidden, false);
  assert.equal(app.elements.has('tab-records'), false);
  $('tab-os').onclick();
  assert.equal($('view-os').hidden, false);
  assert.equal($('view-agent').hidden, true);
  $('tab-agent').onkeydown({key:'Home', preventDefault(){}});
  assert.equal($('tab-os').focused, true);
});

test('legacy saved snapshots retain Unicode notes and require no live record or artifact requests', async () => {
  const app = await ui({monitoring:true}), fixture = monitorFixture();
  const content = 'Durable note: café / 中文';
  const digest = 'sha256:'+require('node:crypto').createHash('sha256').update(JSON.stringify(content)).digest('hex');
  fixture.records['report/kept'].assessment_summary = {digest};
  app.context.snapshot = {records:fixture.records, artifacts:[{digest,data:Buffer.from(JSON.stringify(content)).toString('base64')}]};
  assert.equal(vm.runInContext('projectTasks(snapshotAgentSource(snapshot).records,snapshotAgentSource(snapshot).texts)[0].comment', app.context), content);
  app.context.runtime = osFixture();
  app.context.snapshot.os = app.context.runtime; app.context.snapshot.processes = [];
  vm.runInContext('savedDocument=snapshot;current="snapshot:fixture";render({id:current,status:"paused",processes:[],os:runtime,agents:snapshotAgentSource(snapshot),cost:{}});', app.context);
  app.setHandler(() => {throw Error('Offline inspector must not fetch');});
  await vm.runInContext('inspectRecord("report/kept")', app.context);
  assert.match(textOf(app.elements.get('osInspectorBody')), /unresolved/);
  app.context.artifactDigest = digest;
  await vm.runInContext('inspectArtifact({digest:artifactDigest})', app.context);
  assert.match(textOf(app.elements.get('osInspectorBody')), /café \/ 中文/);
});

test('OS highlights unknown execution with causal ownership details and keeps settled operations in history', async () => {
  const app = await ui({monitoring:true}), $ = id => app.elements.get(id);
  const runtime = osFixture();
  runtime.operations = [{key:'effect/unknown',operation_id:'unknown',process_id:'worker',kind:'agent_job',state:'uncertain',diagnostic:'Lost terminal response',conflict_keys:[]},
    {key:'effect/old',operation_id:'old',process_id:'worker',kind:'model_query',state:'succeeded',conflict_keys:[]}];
  runtime.processes = [{key:'process/worker',process_id:'worker',role:'worker',state:'waiting',status:{phase:'assessment'}}];
  runtime.critical_sections = [{key:'permit/verification/project',resource:'verification/project',process_id:'worker'}];
  app.context.runtime = runtime; app.context.fixture = monitorFixture();
  vm.runInContext('render({id:"fixture",status:"paused",processes:[],os:runtime,agents:fixture,cost:{}})', app.context);
  assert.match(textOf($('osBlocker')), /Execution outcome unknown/);
  assert.match(textOf($('osOperations')), /Execution unknown/);
  assert.doesNotMatch(textOf($('osOperations')), /model_query/);
  assert.match(textOf($('settledOperations')), /model_query/);
  vm.runInContext('showOperation(runtime.operations[0])', app.context);
  assert.match(textOf($('osInspectorBody')), /timeout or disconnect does not prove termination/);
  assert.match(textOf($('osInspectorBody')), /Lost terminal response/);
});

test('controller is not displayed as a senior query and long task objectives stay out of row titles', async () => {
  const app = await ui({monitoring:true}); app.context.fixture = monitorFixture(); app.context.runtime = osFixture();
  app.context.runtime.processes = [{process_id:'controller',role:'senior',state:'ready',status:{phase:'controller'}}];
  vm.runInContext('render({id:"fixture",status:"paused",processes:[],os:runtime,agents:fixture,cost:{}})', app.context);
  assert.equal(vm.runInContext('workflowState(fixture.records,runtime.processes).senior', app.context), undefined);
  const links = app.elements.get('agentTasks').querySelector('tbody').children.map(row => row.children[0].children[0].children[0]);
  assert.ok(links.every(link => link.textContent.length < 80));
  assert.match(app.elements.get('workflowSummary').textContent, /Retained state/);
});

test('pending tasks require kept dependencies and model waits use readable operation names', async () => {
  const app = await ui({monitoring:true}); app.context.fixture = monitorFixture(); app.context.runtime = osFixture();
  app.context.runtime.operations = [{key:'effect/sha256:opaque',operation_id:'sha256:opaque',state:'active',kind:'model_query'}];
  app.context.runtime.processes = [{process_id:'worker',role:'worker',endpoint:'local',state:'waiting',
    status:{wait:{wait_kind:'operation',target_refs:['sha256:opaque']}}}];
  vm.runInContext('render({id:"fixture",status:"paused",processes:[],os:runtime,agents:fixture,cost:{}})', app.context);
  assert.equal(vm.runInContext('processWait(runtime.processes[0])', app.context), 'model response · local endpoint');
  assert.equal(vm.runInContext('pendingReason({assignment:{dependencies:["retry"]}})', app.context), 'Awaiting kept dependencies: retry');
  assert.equal(vm.runInContext('pendingReason({assignment:{dependencies:["kept"]}})', app.context), 'New starts closed for review');
});


test('endpoint testing submits only on click and projects pending probe guards', async () => {
  const app = await ui(), $ = id => app.elements.get(id);
  let posts = 0;
  $('endpointProfile').append(new app.context.Option('Local inference','local-inference'));
  $('endpointProfile').value = 'local-inference';
  app.setHandler(async (url, options) => {
    if (options?.method === 'POST') {
      assert.equal(url, '/api/endpoint-test');
      assert.equal(JSON.parse(options.body).endpoint_profile, 'local-inference');
      posts++;
      return response({id:'probe'},202);
    }
    return response(url === '/api/runs' ? {...listing([]),endpoint_probe:{status:'running',state:'/probe/state',progress:{state:'waiting_first_output',elapsed_seconds:2}}} : view('old'));
  });
  await vm.runInContext('refresh()', app.context);
  assert.equal(posts,0);
  await $('testEndpoint').onclick();
  assert.equal(posts,1);
  assert.equal($('testEndpoint').disabled,true);
  assert.equal($('start').disabled,true);
  assert.match($('endpointTestStatus').textContent,/waiting_first_output/);
});
