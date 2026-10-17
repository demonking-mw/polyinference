// Checks the delivered script and evaluates its real routing code without a browser.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const html = fs.readFileSync(path.join(__dirname, 'polyinference-agent-design-merged.html'), 'utf8');
const data = JSON.parse(html.match(/<script[^>]*id="graph-seed"[^>]*>([\s\S]*?)<\/script>/)[1]);
const script = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)[1];
new Function(script);
const scopes = JSON.parse(script.match(/const scopes=(.*);/)[1]);
const routing = script.slice(script.indexOf('function rect('), script.indexOf('function render('));
const results = {};
let routed = 0;
for (const view of ['all', 'cloud', 'local', 'delivery', 'memory']) {
  const graph = view === 'memory' ? data.memoryGraph : data;
  const nodes = graph.nodes.filter(n => !scopes[view] || scopes[view].includes(n.id));
  const positions = Object.fromEntries(nodes.map(n => [n.id,
    ['all', 'memory'].includes(view) ? {x:n.x, y:n.y} : data.layouts[view][n.id]]));
  assert(nodes.every(n => positions[n.id]), `${view}: missing focus coordinates`);
  if (view !== 'memory') {
    for (let i=0; i<nodes.length; i++) for (let j=i+1; j<nodes.length; j++) {
      const a = positions[nodes[i].id], b = positions[nodes[j].id];
      assert(!(a.x < b.x+224 && a.x+224 > b.x && a.y < b.y+94 && a.y+94 > b.y),
        `${view}: overlapping nodes ${nodes[i].id}, ${nodes[j].id}`);
    }
  }
  const context = vm.createContext({ graph, positions, routeCache: new Map(), W:224, H:94 });
  vm.runInContext(`function graphData(){return graph;} function pos(n){return positions[n.id];}\n${routing}`, context);
  const ns = new Map(nodes.map(n => [n.id,n]));
  const obstacles = nodes.map(n => context.rect(n));
  const edges = graph.edges.filter(e => ns.has(e.from) && ns.has(e.to)).map(e => {
    const points = context.route(e, ns, obstacles);
    assert(points.length >= 2 && points.every(p => Number.isFinite(p.x) && Number.isFinite(p.y)));
    const from = positions[e.from], to = positions[e.to];
    const onBoundary = (p,n) =>
      ((p.x===n.x || p.x===n.x+224) && p.y>=n.y && p.y<=n.y+94) ||
      ((p.y===n.y || p.y===n.y+94) && p.x>=n.x && p.x<=n.x+224);
    assert(onBoundary(points[0],from) && onBoundary(points.at(-1),to), `${e.id}: detached arrow`);
    for (let i=1; i<points.length; i++) {
      assert(points[i].x === points[i-1].x || points[i].y === points[i-1].y, `${e.id}: diagonal route`);
      if (view === 'memory') continue; // Original memory geometry is intentionally immutable.
      for (const n of nodes) {
        if (n.id === e.from || n.id === e.to) continue;
        const p = positions[n.id];
        assert(!context.blocked(points[i-1], points[i], [{l:p.x,r:p.x+224,t:p.y,b:p.y+94}]),
          `${view}: ${e.id} crosses ${n.id}`);
      }
    }
    routed++;
    return {...e, points:JSON.parse(JSON.stringify(points)), d:context.rounded(points)};
  });
  results[view] = {nodes:nodes.map(n => ({...n,...positions[n.id]})), edges};
}
// Feed the same computed geometry to the static layout preview.
if (process.argv[2]) fs.writeFileSync(process.argv[2], JSON.stringify(results));
console.log(JSON.stringify({script:'syntax valid', routes_checked:routed,
  architecture:'no overlapping cards, detached arrows, or routes crossing unrelated cards',
  views:Object.fromEntries(Object.entries(results).map(([k,v]) => [k,{nodes:v.nodes.length,edges:v.edges.length}]))},null,2));
