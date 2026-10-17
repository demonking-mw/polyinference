const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const dir = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(dir, 'polyinference-agent-v1.html'), 'utf8');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 2);
const graph = JSON.parse(scripts[0][1]);
new vm.Script(scripts[1][1]);
assert.deepEqual(graph, JSON.parse(fs.readFileSync(path.join(dir,'polyinference-agent-structure-v1.json'),'utf8')));
assert.equal(new Set(graph.nodes.map(n => n.id)).size, graph.nodes.length);
assert.equal(new Set(graph.edges.map(e => e.id)).size, graph.edges.length);
const ids = new Set(graph.nodes.map(n=>n.id));
assert(graph.edges.every(e=>ids.has(e.from)&&ids.has(e.to)));
assert(graph.edges.every(e=>!e.via));
assert.equal(graph.nodes.length,8,'The simplified graph has eight nodes');
assert.equal(graph.nodes.filter(n=>n.kind==='cloud').length,1,'Use one cloud model node for every prompt mode');
assert.equal(graph.nodes.filter(n=>n.kind==='local').length,1,'Use one local model node for every worker prompt');
for(const pipe of [['senior_review','queue','event_gate','final'],['local_infer','execute','verdict','report']]){
  const members=pipe.map(id=>graph.nodes.find(n=>n.id===id));
  assert(members.every(n=>n.x===members[0].x),'Each pipe is a vertical column');
  assert(members.slice(1).every((n,i)=>n.y>members[i].y),'Read each pipe top to bottom');
}
assert(graph.edges.every(e=>e.body.length>100&&e.payload),'Every interaction has an explanatory comment and payload');
assert(!/<script[^>]+src=|@import|fonts\.googleapis|<link[^>]+stylesheet/.test(html));
const byId = new Map(graph.nodes.map(n=>[n.id,n]));
for (const n of graph.nodes) {
  assert(n.body && n.facts.length && n.contract);
  for (const [url] of n.links) if (!/^https?:/.test(url)) assert(fs.existsSync(path.resolve(dir, url)), `Missing link: ${url}`);
}
console.log('Graph structure, embedded JSON, JavaScript syntax, offline assets: PASS');

// Exercise the editor in a deliberately small, browser-free DOM test double.
class Element {
  constructor(tag='div'){this.tagName=tag;this.children=[];this.attrs={};this.style={};this.dataset={};this.listeners={};this.value='';this.textContent='';this.hidden=false;this.className='';this.classList={add:(...c)=>this.classes(c,true),remove:(...c)=>this.classes(c,false),toggle:(c,on)=>{const has=this.className.split(' ').includes(c);this.classes([c],on===undefined?!has:on);},contains:c=>this.className.split(' ').includes(c)};}
  classes(cs,on){const list=new Set(this.className.split(' ').filter(Boolean));for(const c of cs)on?list.add(c):list.delete(c);this.className=[...list].join(' ');}
  setAttribute(k,v){this.attrs[k]=String(v);if(k==='class')this.className=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5)]=String(v);if(k==='value')this.value=String(v);}
  getAttribute(k){return k==='class'?this.className:this.attrs[k];}
  removeAttribute(k){delete this.attrs[k];}
  append(...items){this.children.push(...items);for(const item of items)if(item&&typeof item==='object')item.parent=this;}
  prepend(item){this.children.unshift(item);}
  replaceChildren(...items){this.children=[];this.append(...items);}
  addEventListener(name,fn){this.listeners[name]=fn;}
  get lastElementChild(){return this.children[this.children.length-1];}
  getBoundingClientRect(){return{left:0,top:0,width:1280,height:680};}
  closest(selector){if(selector==='[data-node]'&&this.dataset.node)return this;if(selector==='[data-edge]'&&this.dataset.edge)return this;return this.parent?.closest(selector)||null;}
  click(){this.onclick?.({target:this});}
  showModal(){this.attrs.open='';}
  close(){delete this.attrs.open;}
  remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}
  setPointerCapture(){}
  releasePointerCapture(){}
}
const elements=new Map();
for(const match of html.matchAll(/\bid="([^"]+)"/g))elements.set(match[1],new Element());
elements.get('graph-seed').textContent=scripts[0][1];
elements.get('save-state').append(new Element(),new Element());
const viewButtons=['all','cloud','local','delivery'].map(v=>{const b=new Element('button');b.dataset.view=v;return b;});
const body=new Element('body'),eventListeners={};
const document={getElementById:id=>elements.get(id),createElement:tag=>new Element(tag),createElementNS:(ns,tag)=>new Element(tag),createTextNode:text=>({textContent:text}),querySelectorAll:selector=>selector==='[data-view]'?viewButtons:[],querySelector:()=>null,body,addEventListener:(n,fn)=>eventListeners[n]=fn};
const saved=new Map(),downloads=[];
const context={document,localStorage:{getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v)},setTimeout:fn=>{fn();return 1;},clearTimeout(){},requestAnimationFrame:fn=>{fn();return 1;},cancelAnimationFrame(){},ResizeObserver:class{observe(){}},innerWidth:1600,console,Blob,URL:{createObjectURL:blob=>{downloads.push(blob);return'blob:test';},revokeObjectURL(){}},Date,Math,Set,Map,JSON,Number,String,Object,Array,Infinity};
const source=scripts[1][1].replace("if(innerWidth<=760)document.body.classList.add('hide-panel');preparePositions();", "globalThis.testApi={get data(){return data},get selection(){return selection},get camera(){return camera},setView,render,select,route,rect,pos,visibleNodes,routeCache,blocked,validate,addNode,connectNode,deleteSelection,travel,centerNode,exportSVG,exportHTML,get connectSource(){return connectSource}};\nif(innerWidth<=760)document.body.classList.add('hide-panel');preparePositions();");
vm.createContext(context);
const start=Date.now();vm.runInContext(source,context,{timeout:30000});
console.log(`Editor boot and complete map render: PASS (${Date.now()-start} ms)`);
const api=context.testApi;
assert.equal(elements.get('nodes').children.length,graph.nodes.length);
assert.equal(elements.get('edges').children.length,graph.edges.length);
assert(elements.get('lanes').children.every(n=>n.tagName==='text'),'Pipe headings have no enclosing boxes');
assert.equal(elements.get('edge-labels').children.length,0,'No arrow text before selection');
api.select('edge',graph.edges[0].id);
assert.equal(elements.get('edge-labels').children.length,1);
api.select('node','local_infer');
assert.equal(elements.get('edge-labels').children.length,0);
for(const scope of ['cloud','local','delivery','all']){api.setView(scope);assert(elements.get('nodes').children.length>0);}
console.log('Focus views, selected-only edge labels, inspector: PASS');
function checkRoutes(){const ns=new Map(api.visibleNodes().map(n=>[n.id,n])),obs=[...ns.values()].map(api.rect);let checked=0,collisions=[];for(const edge of api.data.edges){if(!ns.has(edge.from)||!ns.has(edge.to))continue;const points=api.route(edge,ns,obs);assert(points.length>=2);const others=obs.filter(r=>r.id!==edge.from&&r.id!==edge.to);for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i];assert(a.x===b.x||a.y===b.y,`Nonorthogonal: ${edge.id}`);if(api.blocked(a,b,others))collisions.push(edge.id);}checked++;}return {checked,collisions:[...new Set(collisions)]};}
let routes=checkRoutes();assert.deepEqual(routes.collisions,[]);console.log(`Obstacle-aware routing: PASS (${routes.checked} transitions)`);
const moved=api.data.nodes.find(n=>n.id==='local_infer'),before=JSON.stringify(api.routeCache.get('local_infer--execute'));moved.x+=106;moved.y+=49;api.routeCache.clear();api.render();assert.notEqual(JSON.stringify(api.routeCache.get('local_infer--execute')),before);routes=checkRoutes();assert.deepEqual(routes.collisions,[]);console.log('Connections follow moved nodes and avoid card interiors: PASS');
const v0=JSON.parse(fs.readFileSync(path.join(dir,'polyinference-agent-structure-v0.json'),'utf8'));const imported=api.validate(v0);assert.equal(imported.nodes.length,v0.nodes.length);assert(imported.edges.every(e=>!e.via));assert.throws(()=>api.validate({nodes:graph.nodes,edges:[{id:'bad',from:'missing',to:'context'}]}));const malicious=JSON.parse(JSON.stringify(graph));malicious.nodes[0].links=[['javascript:alert(1)','unsafe'],['https://example.com','safe']];assert.equal(api.validate(malicious).nodes[0].links.length,1);console.log('v0 JSON import, invalid endpoints, unsafe reference filtering: PASS');
const count=api.data.nodes.length;api.addNode();assert.equal(api.data.nodes.length,count+1);api.deleteSelection();assert.equal(api.data.nodes.length,count);api.travel('undo');assert.equal(api.data.nodes.length,count+1);api.travel('redo');assert.equal(api.data.nodes.length,count);console.log('Add/delete and undo/redo: PASS');
api.connectNode('local_infer');api.connectNode('final');assert.equal(api.data.edges.length,graph.edges.length+1);api.deleteSelection();assert.equal(api.data.edges.length,graph.edges.length);
api.select('node','local_infer');elements.get('edit-btn').click();const form=elements.get('inspector-body').children[0],titleField=form.children[0].children[1];titleField.value='Edited local task';form.onsubmit({preventDefault(){}});assert.equal(api.data.nodes.find(n=>n.id==='local_infer').title,'Edited local task');console.log('Connect and edit state contract: PASS');
elements.get('export-btn').click();assert.equal(downloads.length,1);assert(saved.size>0);console.log('JSON export and browser-draft persistence adapter: PASS');
console.log('All offline checks passed. Browser appearance and native downloads still require a browser check.');
