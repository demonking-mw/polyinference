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

async function ui({monitoring = false} = {}) {
  const html = fs.readFileSync(path.join(__dirname, '../src/polyinference/ui.html'), 'utf8');
  const elements = new Map([...html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"/g)]
    .map(([, tag, id]) => [id, new Element(tag)]));
  let handler = async url => response(url === '/api/runs' ? listing([view('old')]) : view('old'));
  const context = vm.createContext({
    document: {getElementById: id => elements.get(id), createElement: tag => new Element(tag),
      createTextNode: text => Object.assign(new Element('#text'), {textContent: text}), querySelectorAll: () => []},
    Node: Element, URL, URLSearchParams, Blob,
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
  app.context.snapshot = {records:fixture.records, artifacts:[{digest:'note-kept',data:Buffer.from(JSON.stringify(content)).toString('base64')}]};
  assert.equal(vm.runInContext('projectTasks(snapshotAgentSource(snapshot).records,snapshotAgentSource(snapshot).texts)[0].comment', app.context), content);
  app.context.runtime = osFixture();
  app.context.snapshot.os = app.context.runtime; app.context.snapshot.processes = [];
  vm.runInContext('savedDocument=snapshot;current="snapshot:fixture";render({id:current,status:"paused",processes:[],os:runtime,agents:snapshotAgentSource(snapshot),cost:{}});', app.context);
  app.setHandler(() => {throw Error('Offline inspector must not fetch');});
  await vm.runInContext('inspectRecord("report/kept")', app.context);
  assert.match(textOf(app.elements.get('osInspectorBody')), /unresolved/);
  await vm.runInContext('inspectArtifact({digest:"note-kept"})', app.context);
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
