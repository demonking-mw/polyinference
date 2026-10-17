(() => {
  'use strict';
  const BUNDLE = JSON.parse(document.getElementById('atlas-data').textContent);
  const PAGE = BUNDLE.page;
  let language = 'en';
  try { language = localStorage.getItem('polyinference-atlas-language') || 'en'; } catch { /* URL remains available. */ }
  const requestedLanguage = new URLSearchParams((location.hash.split('?')[1] || '')).get('lang');
  if (requestedLanguage) language = requestedLanguage;
  if (!['en','zh-CN'].includes(language)) language = 'en';
  let DATA = language === 'zh-CN' ? BUNDLE.locales['zh-CN'] : BUNDLE;
  let design = DATA[PAGE];
  const $ = id => document.getElementById(id);
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const list = items => `<ul>${items.map(item => `<li>${esc(item)}</li>`).join('')}</ul>`;
  const views = ['architecture', 'walkthrough', 'contracts', 'review', 'sources'];
  const originalText = new WeakMap(), originalAttributes = new WeakMap();
  const t = text => language === 'zh-CN' ? (BUNDLE.ui_zh[text] ?? text) : text;
  function translateUi() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (node.parentElement?.closest('script,style,textarea,code,pre,#language-select,[contenteditable]')) continue;
      if (!originalText.has(node)) originalText.set(node,node.nodeValue);
      const original = originalText.get(node), trimmed = original.trim();
      if (trimmed) node.nodeValue = original.replace(trimmed,t(trimmed));
    }
    document.querySelectorAll('[aria-label],[placeholder]').forEach(el => {
      if (el.id === 'language-select') return;
      if (!originalAttributes.has(el)) originalAttributes.set(el,{});
      const saved = originalAttributes.get(el);
      for (const name of ['aria-label','placeholder']) {
        if (!el.hasAttribute(name)) continue;
        if (!(name in saved)) saved[name] = el.getAttribute(name);
        el.setAttribute(name,t(saved[name]));
      }
    });
  }
  function updateLanguageLinks() {
    document.querySelectorAll('[data-design]').forEach(link => {
      const params = new URLSearchParams({lang:language});
      if (state.view === 'walkthrough') {params.set('scenario',state.scenario);params.set('step',String(state.step));}
      link.href = `${link.dataset.design}-design.html#${state.view}?${params}`;
    });
    document.querySelector('.brand').href = `agent-design.html#architecture?lang=${language}`;
  }
  function renderHeader() {
    document.documentElement.lang = language;
    document.title = `${design.title} · PolyInference ${t('design atlas')}`;
    $('language-select').value = language;
    $('eyebrow').textContent = design.eyebrow;
    $('page-title').textContent = design.headline;
    $('page-description').textContent = design.description;
    $('breadcrumb').textContent = language === 'zh-CN' ? `设计图谱 / ${PAGE === 'agent' ? '智能体' : '简化 OS'}` : `Design atlas / ${PAGE === 'agent' ? 'Agent' : 'Simplified OS'}`;
    $('design-takeaway').innerHTML = `<strong>${t('Keep in mind')}</strong><p>${esc(design.takeaway)}</p>`;
    updateLanguageLinks();
  }
  const reviewKey = `polyinference-design-review-v1-${PAGE}`;
  const state = {view:'architecture', map:0, node:design.maps[0].initial, scenario:'normal', step:0};
  let notes = {};
  let storageAvailable = true;
  try {
    const saved = JSON.parse(localStorage.getItem(reviewKey) || '{}');
    if (saved && typeof saved === 'object' && !Array.isArray(saved)) notes = saved;
  } catch { storageAvailable = false; }
  const statuses = ['Unreviewed','Satisfied','Concern','Open question'];
  let theme = '';
  try { theme = localStorage.getItem('polyinference-atlas-theme') || ''; } catch { /* Optional. */ }
  if (!['light','dark'].includes(theme)) theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  function setTheme(value) {
    document.documentElement.dataset.theme = value;
    $('theme-toggle').textContent = t(value === 'dark' ? 'Light theme' : 'Dark theme');
    $('theme-toggle').setAttribute('aria-label', t(`Switch to ${value === 'dark' ? 'light' : 'dark'} theme`));
    originalAttributes.delete($('theme-toggle'));
  }
  setTheme(theme);
  $('theme-toggle').addEventListener('click', () => {
    const value = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(value);
    try { localStorage.setItem('polyinference-atlas-theme', value); } catch { /* Optional. */ }
  });

  document.querySelector(`[data-design="${PAGE}"]`).setAttribute('aria-current','page');

  function route(replace = false) {
    const params = new URLSearchParams({lang:language});
    if (state.view === 'architecture') { params.set('map', String(state.map)); params.set('node', state.node); }
    if (state.view === 'walkthrough') { params.set('scenario', state.scenario); params.set('step', String(state.step)); }
    const hash = `#${state.view}${params.size ? '?' + params : ''}`;
    if (location.hash !== hash) history[replace ? 'replaceState' : 'pushState'](null, '', hash);
  }
  function readRoute() {
    const [view, query = ''] = location.hash.slice(1).split('?');
    state.view = views.includes(view) ? view : 'architecture';
    const params = new URLSearchParams(query);
    const targetLanguage = params.get('lang');
    if (['en','zh-CN'].includes(targetLanguage) && targetLanguage !== language) changeLanguage(targetLanguage,false);
    if (state.view === 'architecture') {
      const number = Number(params.get('map') || 0);
      state.map = Number.isInteger(number) && design.maps[number] ? number : 0;
      const node = params.get('node');
      state.node = design.maps[state.map].positions.some(p => p.id === node) ? node : design.maps[state.map].initial;
    }
    if (state.view === 'walkthrough') {
      const scenario = params.get('scenario');
      state.scenario = Object.hasOwn(DATA.stories, scenario) ? scenario : 'normal';
      const number = Number(params.get('step') || 0);
      state.step = Number.isInteger(number) ? Math.min(Math.max(0, number), DATA.stories[state.scenario].frames.length - 1) : 0;
    }
    showView();
  }
  function showView() {
    document.body.dataset.view = state.view;
    views.forEach(id => { $(id).hidden = state.view !== id; });
    document.querySelectorAll('[data-view]').forEach(link => {
      if (link.dataset.view === state.view) link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    });
    if (state.view === 'architecture') renderMap();
    if (state.view === 'walkthrough') renderStory();
    updateLanguageLinks();
  }
  document.querySelectorAll('[data-view]').forEach(link => link.addEventListener('click', e => {
    e.preventDefault(); state.view = link.dataset.view; route(); showView(); window.scrollTo(0,0);
  }));
  window.addEventListener('hashchange', readRoute);
  window.addEventListener('popstate', readRoute);

  function renderMap() {
    const map = design.maps[state.map];
    $('map-tabs').innerHTML = design.maps.map((item, i) => `<button type="button" data-map="${i}" aria-pressed="${i === state.map}">${esc(item.label)}</button>`).join('');
    $('map-title').textContent = map.title;
    $('map-description').textContent = map.description;
    $('map-footnote').textContent = map.footnote;
    $('diagram').style.paddingBottom = map.edges.some(e => e.route === 'below') ? '58px' : '';
    $('nodes').innerHTML = map.positions.map(p => {
      const n = design.nodes[p.id];
      const next = map.edges.filter(e => e.a === p.id).map(e => design.nodes[e.b].title);
      return `<button type="button" class="node" data-node="${esc(p.id)}" data-tone="${esc(n.tone)}" aria-pressed="${state.node === p.id}" aria-controls="inspector" style="grid-column:${p.col + 1};grid-row:${p.row + 1}"><span class="node-tag">${esc(n.tag)}</span><span class="node-title">${esc(n.title)}</span><span class="node-description">${esc(n.brief)}</span>${next.length ? `<span class="node-next">→ ${next.map(esc).join(' / ')}</span>` : ''}</button>`;
    }).join('');
    $('nodes').setAttribute('aria-label', map.title + t('. Select a component for its contract.'));
    originalAttributes.delete($('nodes'));
    $('map-tabs').querySelectorAll('[data-map]').forEach(button => button.addEventListener('click', () => {
      state.map = Number(button.dataset.map); state.node = design.maps[state.map].initial; route(true); renderMap();
    }));
    $('nodes').querySelectorAll('[data-node]').forEach(button => button.addEventListener('click', () => {
      state.node = button.dataset.node;
      $('nodes').querySelectorAll('[data-node]').forEach(node => node.setAttribute('aria-pressed', String(node.dataset.node === state.node)));
      route(true); renderInspector();
      if (matchMedia('(max-width:1220px)').matches) $('inspector').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block:'start'});
    }));
    renderInspector();
    requestAnimationFrame(drawConnections);
  }
  function renderInspector() {
    const n = design.nodes[state.node];
    $('inspector').innerHTML = `<p class="eyebrow">SELECTED COMPONENT · ${esc(n.tag)}</p><h3 id="inspector-title">${esc(n.title)}</h3><p class="purpose">${esc(n.purpose)}</p><div class="detail-section"><h4>RECEIVES</h4>${list(n.inputs)}</div><div class="detail-section"><h4>PRODUCES</h4>${list(n.outputs)}</div><div class="detail-section"><h4>NON-NEGOTIABLE RULES</h4>${list(n.rules)}</div><div class="detail-check"><strong>QUESTION TO ASSESS</strong>${esc(n.question)}</div><a class="source-link" href="${esc(n.source)}">Inspect the source contract ↗</a>`;
    $('inspector').querySelector('.eyebrow').textContent = `${t('SELECTED COMPONENT')} · ${n.tag}`;
    translateUi();
  }
  function drawConnections() {
    if (state.view !== 'architecture') return;
    const host = $('diagram').getBoundingClientRect();
    if (!host.width) return;
    const svg = $('connections');
    svg.setAttribute('viewBox', `0 0 ${host.width} ${host.height}`);
    const rectangles = {};
    $('nodes').querySelectorAll('[data-node]').forEach(button => {
      const r = button.getBoundingClientRect();
      rectangles[button.dataset.node] = {left:r.left-host.left, right:r.right-host.left, top:r.top-host.top, bottom:r.bottom-host.top, x:(r.left+r.right)/2-host.left, y:(r.top+r.bottom)/2-host.top};
    });
    if (matchMedia('(max-width:440px)').matches) { svg.innerHTML = ''; return; }
    const maxBottom = Math.max(...Object.values(rectangles).map(r => r.bottom));
    const paths = design.maps[state.map].edges.map(e => {
      const a = rectangles[e.a], b = rectangles[e.b];
      if (!a || !b) return '';
      let path, labelX, labelY;
      if (e.route === 'below') {
        const y = maxBottom + 29;
        path = `M${a.x},${a.bottom + 3} V${y} H${b.x} V${b.bottom + 4}`;
        labelX = (a.x + b.x)/2; labelY = y + 16;
      } else if (Math.abs(a.top-b.top) < 8) {
        const right = b.x > a.x;
        const x1 = right ? a.right + 4 : a.left - 4;
        const x2 = right ? b.left - 5 : b.right + 5;
        const x = (x1+x2)/2;
        path = `M${x1},${a.y} H${x} V${b.y} H${x2}`;
        labelX = x; labelY = Math.min(a.y,b.y) - 9;
      } else {
        const down = b.top > a.top;
        const y1 = down ? a.bottom + 3 : a.top - 3;
        const y2 = down ? b.top - 5 : b.bottom + 5;
        const y = (y1+y2)/2;
        const targetX = b.x + (e.targetOffset || 0) * (b.right-b.left);
        path = `M${a.x},${y1} V${y} H${targetX} V${y2}`;
        labelX = (a.x+targetX)/2; labelY = y - 8;
      }
      return `<path class="connection-path${e.data ? ' data' : ''}" d="${path}" marker-end="url(#arrow)"${e.both ? ' marker-start="url(#arrow)"' : ''}/>${e.label ? `<text class="edge-label" x="${labelX}" y="${labelY}">${esc(e.label)}</text>` : ''}`;
    }).join('');
    svg.innerHTML = `<defs><marker id="arrow" viewBox="0 0 8 8" refX="6" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M1 1 L6 4 L1 7" fill="none" stroke="var(--muted)" stroke-width="1.1"/></marker></defs>${paths}`;
  }
  new ResizeObserver(() => requestAnimationFrame(drawConnections)).observe($('nodes'));

  function renderScenarioOptions() { $('scenario').innerHTML = Object.entries(DATA.stories).map(([id, s]) => `<option value="${id}">${esc(s.title)}</option>`).join(''); }
  $('scenario').addEventListener('change', () => {state.scenario = $('scenario').value; state.step = 0; route(true); renderStory();});
  $('previous').addEventListener('click', () => { if (state.step > 0) { state.step--; route(true); renderStory(); } });
  $('next').addEventListener('click', () => { if (state.step < DATA.stories[state.scenario].frames.length - 1) { state.step++; route(true); renderStory(); } });
  function resource(label, value, used, capacity) {
    return `<div class="resource"><span class="resource-label">${esc(t(label))}</span><span class="resource-value">${esc(value)}</span>${capacity ? `<div class="resource-track" aria-label="${language === 'zh-CN' ? `${capacity} 个名额中已占用 ${used} 个` : `${used} of ${capacity} occupied`}">${Array.from({length:capacity}, (_,i) => `<span class="resource-slot${i < used ? ' used' : ''}"></span>`).join('')}</div>` : ''}</div>`;
  }
  function renderStory() {
    const scenario = DATA.stories[state.scenario], frame = scenario.frames[state.step], s = frame.state;
    $('scenario').value = state.scenario;
    $('step-counter').textContent = `${t('EVENT')} ${String(state.step + 1).padStart(2,'0')} / ${String(scenario.frames.length).padStart(2,'0')}`;
    $('previous').disabled = state.step === 0;
    $('next').disabled = state.step === scenario.frames.length - 1;
    $('next').textContent = state.step === scenario.frames.length - 1 ? 'Story complete' : 'Next event →';
    const other = PAGE === 'agent' ? 'os' : 'agent';
    $('other-lens').href = `${other}-design.html#walkthrough?scenario=${encodeURIComponent(state.scenario)}&step=${state.step}&lang=${language}`;
    $('other-lens').textContent = t(`See this through the ${other === 'os' ? 'OS' : 'agent'} lens ↗`);
    $('story-steps').innerHTML = scenario.frames.map((f,i) => `<li><button type="button" data-step="${i}"${i === state.step ? ' aria-current="step"' : ''}><span class="story-index">${i + 1}</span><span>${esc(f.title)}</span></button></li>`).join('');
    $('story-steps').querySelectorAll('[data-step]').forEach(b => b.addEventListener('click', () => { state.step = Number(b.dataset.step); route(true); renderStory(); }));
    requestAnimationFrame(() => {
      const steps = $('story-steps'), current = steps.querySelector('[aria-current="step"]');
      if (current && steps.scrollWidth > steps.clientWidth) {
        const box = current.getBoundingClientRect(), parent = steps.getBoundingClientRect();
        steps.scrollLeft += box.left - parent.left - (parent.width-box.width)/2;
      }
    });
    $('story-event').innerHTML = `<p class="eyebrow">${PAGE === 'agent' ? 'APPLICATION PERSPECTIVE' : 'RUNTIME PERSPECTIVE'}</p><h3 class="story-event-title">${esc(frame.title)}</h3><p class="story-event-description">${esc(frame[PAGE])}</p>`;
    const heads = `<div class="head-strip"><span class="head-item">Provisional <strong>${esc(s.provisional)}</strong></span><span class="head-item">Reviewed <strong>${esc(s.reviewed)}</strong></span><span class="status">${esc(s.reports)}</span></div>`;
    const control = `<div class="actor-row"><span class="actor-name">Controller</span><span class="actor-state">${esc(s.controller)}</span></div>`;
    const permits = `<div class="resource-grid">${resource('Verification owner',s.verifier)}${resource('Shell owner',s.shell)}${resource('New coding starts',s.starts)}</div>`;
    if (PAGE === 'agent') {
      const canonicalState = BUNDLE.stories[state.scenario].frames[state.step].state;
      const workers = ['A','B','C'].filter(key => canonicalState[key] !== 'Not started').map(key => `<div class="actor-row"><span class="actor-name">${t('Worker')} ${key}</span><span class="actor-state">${esc(s[key])}</span></div>`).join('');
      $('story-state').innerHTML = `<div class="actor-lanes">${control}${workers}</div><p class="state-title">SHARED HISTORY & REVIEW</p>${heads}${permits}<p class="small muted">Steering received / applied: <strong>${s.received} / ${s.applied}</strong></p>`;
    } else {
      const journal = ['prepared','submitting','active','uncertain','settled'].map(label => `<span${s.journal === label ? ' class="active"' : ''}>${t(label)}</span>`).join('');
      $('story-state').innerHTML = `<div class="resource-grid">${resource('W · resident workers',`${s.w} / 4`,s.w,4)}${resource('L · local in flight',`${s.l} / 2`,s.l,2)}${resource('C · cloud in flight',`${s.cloud} / 1`,s.cloud,1)}</div>${permits}<p class="state-title">FOCUSED EFFECT JOURNAL · ${esc(s.journal === '—' ? 'NO SINGLE EFFECT SELECTED' : s.journal.toUpperCase())}</p><div class="journal" aria-label="Focused effect state">${journal}</div>${heads}<div class="actor-lanes">${control}</div><p class="small muted">Steering received / applied: <strong>${s.received} / ${s.applied}</strong>. Other effects may have separate journal states.</p>`;
      $('story-state').querySelector('.state-title').textContent = `${t('FOCUSED EFFECT JOURNAL')} · ${s.journal === '—' ? t('NO SINGLE EFFECT SELECTED') : t(s.journal)}`;
    }
    $('story-rule').textContent = frame.rule;
    $('story-source').href = scenario.source;
    updateLanguageLinks(); translateUi();
  }

  function renderContracts() {
    const header = `<div class="contract-grid"><div class="contract-panel"><p class="eyebrow">AGENT OWNS MEANING</p><h3>What should be done?</h3>${list(['Objective, task criteria and dependency meaning','Sprint plans, prompt modes and repair decisions','Verdict proposals, review decisions and doc batching','Logical context, provenance and required evidence'])}</div><div class="contract-panel"><p class="eyebrow">OS OWNS MECHANISMS</p><h3>May this effect happen safely?</h3>${list(['Authentication, grants, quotas and atomic admission','Actual model/tool execution and workspace enforcement','Fenced ownership, journaled intent and reconciliation','Durable records, artifacts, publication and events'])}</div></div>`;
    const table = `<div class="table-wrap"><table><caption class="sr-only">Agent to OS boundary</caption><thead><tr><th>Contract</th><th>Application responsibility</th><th>Runtime guarantee</th></tr></thead><tbody>${DATA.boundary.map(row => `<tr>${row.map(cell => `<td>${esc(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    const gates = `<p class="section-kicker">ONE PROJECT VERIFIER, ONE SHELL COMMAND</p><div class="contract-panel"><h3>Verification holds through the entire final phase</h3><div class="gate-sequence">${['Capture H','Merge delta','Reconcile turn','Checks','Assessment','Real commit','Atomic publication','Release'].map((s,i) => `${i ? '<span class="sequence-arrow" aria-hidden="true">→</span>' : ''}<span class="gate-step">${esc(s)}</span>`).join('')}</div><p style="margin-top:16px">Acquire verification before shell. Shell is taken separately per command; it is free during model reasoning. Other private work and eligible inference can progress. Unknown effects retain conflicting ownership.</p></div>`;
    const verdicts = `<p class="section-kicker">NORMAL ASSESSED OUTCOMES ALL ENTER PROVISIONAL HISTORY</p><div class="verdicts">${[['successful','Current sufficient passing evidence.'],['fail','A definite required criterion failed.'],['uncertain','Required evidence is missing or inconclusive.']].map(([v,d]) => `<div class="verdict"><strong>${v}</strong><p>${d}</p><small>Real commit → provisional + unresolved</small></div>`).join('')}</div><p class="small muted" style="margin-top:12px">Interrupted or assessment-pending work has no invented verdict or normal TaskReport. Senior review remains separate from every normal worker verdict.</p>`;
    const capacity = `<p class="section-kicker">INDEPENDENT ADMISSION CONSTRAINTS</p><div class="table-wrap"><table><thead><tr><th>Limit</th><th>Bounds</th><th>Lifetime / interpretation</th></tr></thead><tbody>${DATA.capacity.map(row => `<tr>${row.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    const scope = `<p class="section-kicker">IMPLEMENTATION BOUNDARY</p><div class="contract-panel scope-list"><div><h3>Build in this core</h3>${list(['One project, one shared local model, one cloud protocol','Bounded workers, direct tools and scoped code copies','Complete private integration and exact-tree evidence','Two permits, durable journal, versioned notes and records'])}</div><div><h3>Future negotiated extensions</h3>${list(['Weighted distribution and running-process model migration','MCP discovery/lifecycle and rich tiered memory','Autonomous consolidation or general subagent APIs','Distributed coordinators, broad snapshots or custom GPU scheduling'])}</div></div>`;
    $('contract-content').innerHTML = header + table + (PAGE === 'os' ? capacity + gates + verdicts : gates + verdicts + capacity) + scope;
    translateUi();
  }

  function reviewEntry(id) {
    const item = notes[id];
    return {status:statuses.includes(item?.status) ? item.status : 'Unreviewed', note:typeof item?.note === 'string' ? item.note : ''};
  }
  function saveNotes() {
    try {localStorage.setItem(reviewKey, JSON.stringify(notes));} catch {storageAvailable = false;}
    updateReviewSummary();
  }
  function updateReviewSummary() {
    const judged = design.review.filter(q => reviewEntry(q.id).status !== 'Unreviewed').length;
    const concerns = design.review.filter(q => reviewEntry(q.id).status === 'Concern').length;
    $('review-count').textContent = language === 'zh-CN' ? `已记录 ${judged} / ${design.review.length} 项判断${concerns ? ` · ${concerns} 项疑虑` : ''}` : `${judged} of ${design.review.length} judgments recorded${concerns ? ` · ${concerns} concern${concerns === 1 ? '' : 's'}` : ''}`;
    $('review-dot').hidden = !design.review.some(q => reviewEntry(q.id).status !== 'Unreviewed' || reviewEntry(q.id).note);
    $('storage-note').textContent = storageAvailable ? 'Notes save in this browser. Export a copy to keep or share.' : 'Browser storage is unavailable. Export notes before closing.';
    translateUi();
  }
  function renderReview() {
    $('review-list').innerHTML = design.review.map((q,i) => {
      const saved = reviewEntry(q.id);
      return `<article class="review-item"><div class="review-header"><details${i === 0 ? ' open' : ''}><summary id="question-${q.id}"><span class="review-id">${q.id}</span>${esc(q.title)}</summary><div class="review-body"><p><strong>Why it matters.</strong> ${esc(q.why)}</p><p><strong>What to inspect.</strong> ${esc(q.inspect)}</p><a class="source-link" href="${esc(q.source)}">Inspect supporting design ↗</a><label class="note-label" for="note-${q.id}">YOUR NOTES</label><textarea id="note-${q.id}" data-note="${q.id}" placeholder="Record your reasoning, questions or required changes.">${esc(saved.note)}</textarea></div></details><select class="review-select" data-judgment="${q.id}" aria-labelledby="question-${q.id}">${statuses.map(status => `<option value="${status}"${saved.status === status ? ' selected' : ''}>${status}</option>`).join('')}</select></div></article>`;
    }).join('');
    $('review-list').querySelectorAll('[data-note]').forEach(input => input.addEventListener('input', () => {notes[input.dataset.note] = {...reviewEntry(input.dataset.note), note:input.value}; saveNotes();}));
    $('review-list').querySelectorAll('[data-judgment]').forEach(select => select.addEventListener('change', () => {notes[select.dataset.judgment] = {...reviewEntry(select.dataset.judgment), status:select.value}; saveNotes();}));
    updateReviewSummary();
  }
  $('export-notes').addEventListener('click', () => {
    const review = {design:PAGE, language, program_version:'proposal-4-audited-core', source_provenance:DATA.provenance,
      exported_at:new Date().toISOString(), judgments:design.review.map(q => ({id:q.id, question:q.title, ...reviewEntry(q.id), source:q.source}))};
    const url = URL.createObjectURL(new Blob([JSON.stringify(review,null,2) + '\n'], {type:'application/json'}));
    const link = document.createElement('a'); link.href = url; link.download = `polyinference-${PAGE}-review.json`; document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  function renderSources() {
    $('source-content').innerHTML = `<div class="source-grid">${DATA.sources.map(s => `<a class="source-card" href="${esc(s.href)}"><span class="source-category">${esc(s.category)}</span><h3>${esc(s.title)} ↗</h3><p>${esc(s.description)}</p></a>`).join('')}</div><div class="provenance"><h3>A dated, inspectable design snapshot</h3><p class="muted small">The audited READMEs and joint integration audit supply the current contracts. The merged graph supplies the behavioral baseline; its preserved memory view yields where its old prose conflicts with expanded execution contracts. The reader adds illustrative schedules and assessment questions, not new runtime guarantees.</p><p class="muted small">Wire 2.0 · state 2.1 · program proposal-4-audited-core. This reader runs offline; source links resolve when these files remain in the repository. No performance or implementation result is implied.</p><details><summary>Source fingerprints at build time</summary>${DATA.provenance.map(p => `<div class="hash-row">${esc(p.path)}<code>sha256:${esc(p.digest)}</code></div>`).join('')}</details></div>`;
    translateUi();
  }
  function changeLanguage(value, updateRoute = true) {
    if (!['en','zh-CN'].includes(value)) return;
    const opened = [...document.querySelectorAll('#review details[open]')].map(d => d.querySelector('summary').id);
    language = value; DATA = language === 'zh-CN' ? BUNDLE.locales['zh-CN'] : BUNDLE; design = DATA[PAGE];
    try {localStorage.setItem('polyinference-atlas-language',language);} catch { /* Fragment links preserve selection. */ }
    renderHeader(); setTheme(document.documentElement.dataset.theme);
    renderScenarioOptions(); renderContracts(); renderReview(); renderSources(); renderMap(); renderStory(); showView();
    document.querySelectorAll('#review details').forEach(d => {d.open = opened.includes(d.querySelector('summary').id);});
    translateUi(); if (updateRoute) route(true);
  }
  $('language-select').addEventListener('change', () => changeLanguage($('language-select').value));
  $('print').addEventListener('click', () => window.print());
  let priorDetails = [];
  window.addEventListener('beforeprint', () => {priorDetails = [...document.querySelectorAll('#review details')].map(d => [d,d.open]); if (state.view === 'review') priorDetails.forEach(([d]) => {d.open = true;}); drawConnections();});
  window.addEventListener('afterprint', () => {priorDetails.forEach(([d,open]) => {d.open = open;}); requestAnimationFrame(drawConnections);});
  renderHeader(); renderScenarioOptions(); renderContracts(); renderReview(); renderSources(); readRoute(); translateUi();
})();
