/* Cartograph frontend. Loads the computed artifact (real numbers, real citations,
   real structures) and drives the 3-minute demo: ask -> length-3 path -> dossier
   -> locked evaluator snapping held-out edges green -> one loop round.
   Nothing here fabricates data; it only renders backend/build_artifact.py output. */
'use strict';

const COL = {
  void:'#05070e', viral:'#ffb454', human:'#6c9ffb', predicted:'#22e0dd',
  confirmed:'#42e08a', rejected:'#ff5c6a', topology:'#ffd166', conserved:'#b98bff',
  known:'#3a4a6e', enrich:'#26324e', ink:'#e8edf6', mut:'#8a97ad',
};
const KEY = (s,t)=>`${s}|${t}`;

// --- safety helpers: escape all interpolated strings, validate every URL.
// Today the data is our own build-time artifact, but the product's purpose is to
// load user-supplied interactomes, so the trust boundary is closed here up front. ---
const ESC = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'};
const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c=>ESC[c]);
const safeUrl = u => (typeof u==='string' && /^https?:\/\//i.test(u)) ? u : null;
const safeEnsembl = e => (typeof e==='string' && /^ENSG[0-9]+$/.test(e)) ? e : null;
const edgeBetween = (a,b) => cy.getElementById(KEY(a,b)).union(cy.getElementById(KEY(b,a)));

let DATA=null, cy=null, molViewer=null;
const state = { evalDone:false, loopRound:0, layers:{known:true,enrichment:true,predicted:true,confirmed:true} };

async function boot(){
  try {
    const resp = await fetch('data/cartograph_computed.json');
    if(!resp.ok) throw new Error(`HTTP ${resp.status} fetching the computed artifact`);
    DATA = await resp.json();
  } catch(err) {
    document.getElementById('dossier-body').innerHTML =
      `<div class="dz-idle"><h2>Could not load the demo data.</h2>
       <p>${esc(String(err))}</p>
       <p style="color:#8a97ad">Serve the folder over HTTP (not file://). From <code>frontend/</code>:
       <br><b style="color:#22e0dd">python3 -m http.server 8791 --bind 127.0.0.1</b><br>
       then open <b>http://127.0.0.1:8791/index.html</b>. Or run <b>./run.sh</b> from the repo root.</p></div>`;
    return;
  }
  buildGraph();
  buildControls();
  buildLegend();
  buildSearch();
  wireTopActions();
  renderIdle();
  detectMode();
}

let MODE = 'offline';
async function detectMode(){
  try {
    const r = await fetch('/api/health');
    const j = await r.json();
    MODE = (j && j.mode === 'online') ? 'online' : 'offline';
  } catch { MODE = 'offline'; }
  const pill=document.getElementById('mode-pill');
  pill.textContent = MODE==='online' ? 'live · api' : 'offline';
  pill.classList.toggle('online', MODE==='online');
  // gate live-only controls; leave a quiet tooltip when disabled
  document.querySelectorAll('[data-live]').forEach(el=>{
    const feature=el.dataset.live;
    const enabled = MODE==='online' && feature!=='compare';   // compare = phase two, not built
    el.disabled = !enabled;
    el.title = enabled ? '' :
      (feature==='compare' ? 'Cross-coronavirus comparison — not in this build'
       : 'Requires the API server (./run.sh api)');
  });
}

function wireTopActions(){
  document.getElementById('act-upload').onclick=()=>{ if(MODE==='online') openUpload(); };
  document.getElementById('act-export').onclick=exportCurrent;
  // compare stays disabled (phase two)
}

// Export: current dossier -> self-contained report, else the worklist -> CSV
let _currentDossierKey=null;
function exportCurrent(){
  if(_currentDossierKey && DATA.dossiers[_currentDossierKey]) exportDossierReport(_currentDossierKey);
  else exportWorklistCsv();
}

/* ---------- graph ---------- */
function buildGraph(){
  const els=[];
  for(const n of DATA.graph.nodes){
    els.push({ data:{ id:n.id, label:n.id, type:n.type, cluster:n.cluster,
      uniprot:n.uniprot, degree:n.degree }, position:{ x:n.x, y:n.y } });
  }
  const seen=new Set();
  for(const e of DATA.graph.edges){
    if(e.held_out) continue;               // held-out truths are hidden until eval
    const id=KEY(e.source,e.target);
    if(seen.has(id)) continue; seen.add(id);
    els.push({ data:{ id, source:e.source, target:e.target, kind:e.kind, score:e.score,
      hasDossier: !!DATA.dossiers[id] } });
  }
  // predicted (missing) edges — hidden until revealed
  for(const p of DATA.graph.predicted){
    const id=KEY(p.source,p.target);
    if(seen.has(id)) continue; seen.add(id);
    els.push({ data:{ id, source:p.source, target:p.target, kind:'predicted',
      l3:p.l3_score, rank:p.rank, heldTrue:p.held_out_true, path:JSON.stringify(p.path||[]),
      hasDossier: !!DATA.dossiers[id] }, classes:'predicted hiddenEdge' });
  }

  cy = cytoscape({
    container: document.getElementById('cy'),
    elements: els,
    layout:{ name:'preset' },
    minZoom:0.35, maxZoom:2.5, wheelSensitivity:0.25,
    style: cyStyle(),
  });
  cy.fit(undefined, 60);
  cy.on('tap','node', evt=> selectNode(evt.target.id()));
  cy.on('tap','edge', evt=>{ const id=evt.target.id(); if(DATA.dossiers[id]) openDossier(id); });

  // hover: pointer cursor + tooltip so clickability is discoverable (a11y)
  const tip=document.getElementById('cy-tip');
  const container=cy.container();
  cy.on('mouseover','node', evt=>{
    container.style.cursor='pointer';
    const n=evt.target.data();
    tip.innerHTML=`<b>${esc(n.id)}</b> · ${n.type==='viral'?'viral bait':'human prey'}`
      +(n.uniprot?`<br>${esc(n.uniprot)} · deg ${esc(n.degree)}`:'')
      +`<br><span style="color:#8a97ad">click for ${DATA.dossiers && Object.keys(DATA.dossiers).some(k=>k.split('|').includes(n.id))?'dossier':'node details'}</span>`;
    tip.classList.remove('hidden');
  });
  cy.on('mouseover','edge', evt=>{ container.style.cursor = DATA.dossiers[evt.target.id()]?'pointer':'default'; });
  cy.on('mousemove', evt=>{
    if(tip.classList.contains('hidden')) return;
    const oe=evt.originalEvent; tip.style.left=(oe.clientX+14)+'px'; tip.style.top=(oe.clientY+14)+'px';
  });
  cy.on('mouseout','node', ()=>{ container.style.cursor='default'; tip.classList.add('hidden'); });
  cy.on('mouseout','edge', ()=>{ container.style.cursor='default'; });
}

function cyStyle(){
  return [
    { selector:'node', style:{
      'label':'data(label)','color':COL.ink,'font-family':'JetBrains Mono, monospace',
      'font-size':'11px','font-weight':600,'text-valign':'center','text-halign':'center',
      'text-margin-y':0,'width':'mapData(degree,1,20,26,52)','height':'mapData(degree,1,20,26,52)',
      'text-outline-width':2,'text-outline-color':COL.void,'border-width':2 } },
    { selector:'node[type="viral"]', style:{
      'shape':'hexagon','background-color':COL.viral,'border-color':'#ffd9a8',
      'font-size':'13px','font-weight':800,'text-outline-width':0,'color':'#231400',
      'width':'mapData(degree,1,20,34,58)','height':'mapData(degree,1,20,34,58)' } },
    { selector:'node[type="human"]', style:{
      'shape':'ellipse','background-color':'#16233f','border-color':COL.human,'color':COL.ink } },
    { selector:'node.dim', style:{ 'opacity':0.22 } },
    { selector:'node.pathlit', style:{ 'border-color':COL.predicted,'border-width':4,
      'background-color':'#0c2230', 'shadow-blur':24,'shadow-color':COL.predicted,'shadow-opacity':0.9 } },
    { selector:'node.dossier-target', style:{ 'border-color':COL.predicted,'border-width':3 } },
    // selected/active nodes get a dark box behind the label so it stays readable
    // even on a light hexagon or a darkened (path-lit) fill (bug: black label on ORF6)
    { selector:'node.pathlit, node.dossier-target', style:{
      'color':'#eafcff','text-outline-width':3,'text-outline-color':'#04121a',
      'text-outline-opacity':1,'font-weight':800 } },

    { selector:'edge', style:{ 'curve-style':'straight','width':2,'line-color':COL.known,
      'target-arrow-shape':'none','opacity':0.85 } },
    { selector:'edge[kind="known"]', style:{ 'line-color':COL.known,'width':2 } },
    { selector:'edge[kind="enrichment"]', style:{ 'line-color':COL.enrich,'line-style':'dashed','width':1.5,'opacity':0.6 } },
    { selector:'edge[kind="predicted"]', style:{ 'line-color':COL.predicted,'width':2.5,'line-style':'dashed',
      'shadow-blur':10,'shadow-color':COL.predicted,'shadow-opacity':0.7 } },
    { selector:'edge.hiddenEdge', style:{ 'display':'none' } },
    { selector:'edge.pathlit', style:{ 'line-color':COL.predicted,'width':4,'opacity':1,'line-style':'solid',
      'shadow-blur':18,'shadow-color':COL.predicted,'shadow-opacity':1 } },
    { selector:'edge.hit', style:{ 'line-color':COL.confirmed,'width':4,'line-style':'solid','opacity':1,
      'shadow-blur':16,'shadow-color':COL.confirmed,'shadow-opacity':1 } },
    { selector:'edge.miss', style:{ 'line-color':COL.rejected,'width':2.5,'line-style':'dashed','opacity':0.9 } },
    { selector:'edge.confirmed', style:{ 'line-color':COL.confirmed,'width':3.5,'line-style':'solid','opacity':1 } },
    { selector:'edge.dim', style:{ 'opacity':0.12 } },
    { selector:'.hl', style:{ 'opacity':1 } },
  ];
}

/* ---------- controls ---------- */
function buildControls(){
  const defs=[['known','Known (AP-MS)',COL.known],['enrichment','STRING enrichment',COL.enrich],
    ['predicted','Predicted (L3)',COL.predicted],['confirmed','Confirmed (loop)',COL.confirmed]];
  const cnt=k=> k==='predicted'? DATA.graph.predicted.length
    : DATA.graph.edges.filter(e=>!e.held_out && e.kind===k).length;
  const wrap=document.getElementById('layer-toggles'); wrap.innerHTML='';
  for(const [k,label,c] of defs){
    const row=document.createElement('div'); row.className='layer-row on'; row.dataset.k=k;
    row.setAttribute('role','switch'); row.setAttribute('aria-checked','true');
    row.setAttribute('tabindex','0'); row.setAttribute('aria-label',`${label} layer`);
    row.innerHTML=`<span class="sw"></span><span class="dot" style="background:${c}"></span>${label}<span class="cnt">${cnt(k)}</span>`;
    row.onclick=()=>toggleLayer(k,row);
    row.onkeydown=(e)=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); toggleLayer(k,row); } };
    wrap.appendChild(row);
  }
  document.getElementById('btn-eval').onclick=runEval;
  document.getElementById('btn-loop').onclick=runLoop;
  document.getElementById('btn-reset').onclick=()=>location.reload();
  document.getElementById('btn-worklist').onclick=openWorklist;
  document.getElementById('btn-evaltrans').onclick=openEvalTransparency;
}

function toggleLayer(k,row){
  state.layers[k]=!state.layers[k];
  row.classList.toggle('on',state.layers[k]);
  row.setAttribute('aria-checked', state.layers[k]?'true':'false');
  const sel = k==='confirmed' ? 'edge.confirmed'
    : k==='predicted' ? 'edge[kind="predicted"]'
    : `edge[kind="${k}"]`;
  cy.edges(sel).forEach(e=>{
    if(e.hasClass('hiddenEdge')) return;
    e.style('display', state.layers[k]?'element':'none');
  });
}

function updateLayerCount(k, n){
  const row=document.querySelector(`.layer-row[data-k="${k}"] .cnt`);
  if(row) row.textContent=n;
}

function buildLegend(){
  const L=document.getElementById('legend');
  const rows=[['known','#3a4a6e','Known'],['enrich','#26324e','STRING'],['pred',COL.predicted,'Predicted L3'],
    ['hit',COL.confirmed,'Held-out ✓'],['miss',COL.rejected,'Miss']];
  L.innerHTML=rows.map(([_,c,t])=>`<span><i class="g" style="background:${c}"></i>${t}</span>`).join('');
}

/* ---------- Ask the map: deterministic intent parser + dispatch ---------- */
let queryToken=0;
const BAIT_ALIAS = { nucleocapsid:'N', envelope:'E', membrane:'M', spike:'Spike' };

function buildSearch(){
  const input=document.getElementById('ask-input');
  input.addEventListener('keydown', e=>{ if(e.key==='Enter'){ runSearch(input.value); } });
  document.getElementById('ask-go').onclick=()=>runSearch(input.value);
  const chips=[['ORF6’s unmapped targets','orf6 unmapped targets'],
    ['Most druggable predicted','most druggable predicted'],
    ['Run locked evaluation','run locked evaluation']];
  const wrap=document.getElementById('ask-chips'); wrap.innerHTML='';
  for(const [label,q] of chips){
    const b=document.createElement('button'); b.type='button'; b.className='ask-chip'; b.textContent=label;
    b.onclick=()=>{ input.value=q; runSearch(q); };
    wrap.appendChild(b);
  }
}

function graphBaits(){ return DATA.graph.nodes.filter(n=>n.type==='viral').map(n=>n.id); }
function allBaits(){ return [...new Set(DATA.worklist.map(r=>r.bait))]; }

function parseIntent(text){
  const t=(text||'').toLowerCase().trim();
  if(!t) return {type:'none'};
  if(/\b(loop)\b/.test(t)) return {type:'loop'};
  if(/(evaluat|precision|\brun\b.*\beval|benchmark|held.?out)/.test(t)) return {type:'eval'};
  if(/(druggab|repurpos|approved drug|most.drugg)/.test(t)) return {type:'druggable'};
  const rx=s=>String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');  // escape ids from (possibly uploaded) data
  const g=graphBaits();
  for(const b of g){ if(new RegExp(`\\b${rx(b.toLowerCase())}\\b`).test(t)) return {type:'probe', bait:b}; }
  for(const [alias,b] of Object.entries(BAIT_ALIAS)){ if(t.includes(alias)) return {type:'probe', bait:b}; }
  for(const b of allBaits()){ if(new RegExp(`\\b${rx(b.toLowerCase())}\\b`).test(t)) return {type:'probe_offscreen', bait:b}; }
  return {type:'unknown'};
}

function runSearch(text){
  const it=parseIntent(text);
  switch(it.type){
    case 'none': return;
    case 'eval': runEval(); return;
    case 'loop':
      if(!state.evalDone){ runEval(); toast('Ran the locked evaluator — <span class="k">run loop</span> again for the fold-back round.'); }
      else runLoop();
      return;
    case 'druggable':
      wlState.onlyRepurpose=true; wlState.sort='approved_drug'; wlState.dir=-1;
      openWorklist();
      toast('Most-druggable predicted targets — worklist filtered to <span class="k">repurposing leads</span> (approved drug on the host target).');
      return;
    case 'probe': probeBait(it.bait); return;
    case 'probe_offscreen':
      wlState.bait=it.bait; wlState.onlyRepurpose=false; openWorklist();
      toast(`<span class="k">${esc(it.bait)}</span> is a bait in the interactome; its predicted edges are listed in the worklist (outside the current neighbourhood view).`);
      return;
    default:
      toast('Query not understood — try a viral protein (e.g. <span class="k">ORF6</span>), <span class="k">most druggable predicted</span>, or <span class="k">run evaluation</span>.');
  }
}

function probeBait(bait){
  if(bait===DATA.flagship.path[0]){ flagshipOrf6(); return; }   // flagship walkthrough
  const dz=Object.keys(DATA.dossiers).find(k=>k.split('|')[0]===bait);
  const n=revealPredictedFor(bait);
  if(dz){ openDossier(dz); }
  else { selectNode(bait); cy.animate({center:{eles:cy.getElementById(bait)}},{duration:300}); }
  toast(n ? `<span class="k">${esc(bait)}</span> — revealed ${esc(n)} deterministic L3 prediction${n===1?'':'s'}.`
          : `<span class="k">${esc(bait)}</span> has no L3 predictions in this neighbourhood view.`);
}

function flagshipOrf6(){
  const my=++queryToken;                          // cancel any in-flight animation
  cy.elements().removeClass('dim pathlit');
  const path = DATA.flagship.path;               // ['Orf6','NUP98','NUP214','RAE1']
  toast(`Length-3 path <span class="k">${esc(path.join(' → '))}</span> — deterministic L3.`);
  cy.elements().addClass('dim');
  let i=0;
  const step=()=>{
    if(my!==queryToken) return;                   // superseded by a newer query
    if(i<path.length){
      const n=cy.getElementById(path[i]); n.removeClass('dim').addClass('pathlit');
      if(i>0){ const e=edgeBetween(path[i-1],path[i]); if(e.nonempty()){ e.removeClass('dim hiddenEdge').addClass('pathlit'); e.style('display','element'); } }
      i++; setTimeout(step,650);
    } else {
      const pe=edgeBetween('Orf6','RAE1');
      pe.removeClass('hiddenEdge dim').addClass('pathlit'); pe.style('display','element');
      toast(`Predicted edge <span class="k">Orf6 → RAE1</span> · L3 rank ${esc(DATA.flagship.l3_rank)}/${esc(DATA.flagship.n_candidates)}.`);
      setTimeout(()=>{ if(my!==queryToken) return; cy.elements().removeClass('dim'); openDossier('Orf6|RAE1'); }, 900);
    }
  };
  step();
}
function revealPredictedFor(bait){
  let n=0;
  cy.edges('edge[kind="predicted"]').forEach(e=>{ if(e.source().id()===bait){ e.removeClass('hiddenEdge'); e.style('display','element'); n++; } });
  return n;
}

function toast(html){ const t=document.getElementById('ask-toast'); t.innerHTML=html; t.classList.remove('hidden');
  clearTimeout(toast._t); toast._t=setTimeout(()=>t.classList.add('hidden'), 6000); }

/* ---------- evaluator ---------- */
function runEval(){
  if(state.evalDone) return; state.evalDone=true;
  // reveal every predicted edge and snap green (held-out true) / red (miss)
  const preds=cy.edges('edge[kind="predicted"]');
  preds.removeClass('hiddenEdge'); preds.forEach(e=>e.style('display','element'));
  let idx=0;
  const arr=preds.toArray().sort((a,b)=> (b.data('l3')||0)-(a.data('l3')||0));
  const step=()=>{
    if(idx<arr.length){
      const e=arr[idx++];
      e.removeClass('pathlit');
      e.addClass(e.data('heldTrue')?'hit':'miss');
      setTimeout(step,180);
    } else showPrecision();
  };
  step();
  document.getElementById('btn-loop').disabled=false;
}

function showPrecision(){
  const b=DATA.eval.baseline;
  const pk=b.precision_at_k, np=b.without_pinned;
  const pct=v=>Math.round(v*100)+'%';
  const chip=document.getElementById('precision-chip'); chip.classList.remove('hidden');
  chip.innerHTML=`<button class="panel-close" aria-label="Dismiss evaluator panel" onclick="hideChip()">✕</button>
    <div class="lbl">Locked evaluator · precision@${esc(b.headline_k)}</div>
    <div class="big">${pct(b.headline_precision_at_k)}</div>
    <div class="sub">precision@10 <b>${pct(pk['10'])}</b> · @20 <b>${pct(pk['20'])}</b> · @50 <b>${pct(pk['50'])}</b><br>
    ROC-AUC <b>${esc(b.roc_auc)}</b> · AP <b>${esc(b.average_precision)}</b> · recall@50 <b>${pct(b.recall_at_k['50'])}</b><br>
    on <b>${esc(b.n_targets)}</b> real held-out Gordon edges (${esc(b.n_recoverable)} reachable by L3)<br>
    <span style="color:${COL.mut}">without pinned edge: @20 ${pct(np.precision_at_k['20'])} (pinning does not inflate it)<br>
    frozen seed ${esc(DATA.eval.seed)}, committed before prediction</span></div>`;
  const r=document.getElementById('eval-readout');
  r.innerHTML=`held-out <b>${esc(b.n_targets)}</b> · P@10/20/50 <b>${pct(pk['10'])}/${pct(pk['20'])}/${pct(pk['50'])}</b><br>ROC-AUC <b>${esc(b.roc_auc)}</b> · AP <b>${esc(b.average_precision)}</b>`;
}

/* ---------- loop round ---------- */
function runLoop(){
  const rounds=(DATA.eval.loop.rounds)||[];
  if(state.loopRound>=rounds.length) return;
  const rd=rounds[state.loopRound];
  state.loopRound++;
  // round 1 also confirms the eval greens on the map (the densification beat)
  if(state.loopRound===1) cy.edges('edge.hit').addClass('confirmed');
  for(const [s,t] of rd.confirmed){ const e=edgeBetween(s,t); if(e.nonempty()) e.addClass('confirmed'); }
  updateLayerCount('confirmed', cy.edges('edge.confirmed').length);
  const confRow=document.querySelector('.layer-row[data-k="confirmed"]');
  if(confRow && !state.layers.confirmed){ state.layers.confirmed=true; confRow.classList.add('on'); confRow.setAttribute('aria-checked','true'); }
  document.getElementById('loop-rounds').textContent=`rounds run: ${state.loopRound}`;
  const before=Math.round(rd.before_precision_at_20*100), after=Math.round(rd.after_precision_at_20*100);
  const chip=document.getElementById('precision-chip'); chip.classList.remove('hidden');
  chip.innerHTML=`<button class="panel-close" aria-label="Dismiss loop panel" onclick="hideChip()">✕</button>
    <div class="lbl">Loop round ${esc(rd.round)} · precision@20 on remaining held-out</div>
    <div class="big">${before}% → ${after}%</div>
    <div class="sub">confirmed <b>${esc(rd.confirmed.length)}</b> edges this round (<b>${esc(rd.cumulative_confirmed)}</b> total)<br>
    reachable ${esc(rd.before_recoverable)} → <b>${esc(rd.after_recoverable)}</b> · ${esc(rd.n_remaining)} still hidden<br>
    <span style="color:${COL.mut}">fair before/after on the same target set</span></div>`;
  toast(`<span class="k">Loop round ${esc(rd.round)}</span>: confirm ${esc(rd.confirmed.length)} recovered-true edges (real Gordon edges, L3-rank #1), fold back, re-score the still-hidden edges.`);
  const btn=document.getElementById('btn-loop');
  if(state.loopRound>=rounds.length){ btn.disabled=true; btn.textContent='Loop complete'; }
  else btn.textContent=`Run loop round ${state.loopRound+1}`;
}

/* ---------- dossier ---------- */
function selectNode(id){
  const dz=DATA.dossiers; // if a node has a single dossier'd incident edge, show it
  const inc=Object.keys(dz).filter(k=>k.split('|').includes(id));
  if(inc.length) openDossier(inc[0]); else renderNodePanel(id);
}

function openDossier(key){
  const d=DATA.dossiers[key]; if(!d) return;
  _currentDossierKey=key;
  cy.nodes().removeClass('dossier-target');
  cy.getElementById(d.source).addClass('dossier-target');
  cy.getElementById(d.target).addClass('dossier-target');
  const badge = d.status==='predicted'?['PREDICTED EDGE',COL.predicted]
    : d.status==='confirmed'?['CONFIRMED EDGE',COL.confirmed]:['KNOWN EDGE',COL.human];
  const st=d.structure, cf=d.confidence;
  const rcsb=safeUrl(st.rcsb_url);
  const ens=safeEnsembl(d.druggability.ensembl);
  const skClass = ['pass','downgrade','veto'].includes(d.skeptic.verdict)?d.skeptic.verdict:'pass';
  const html=`
  <div class="dz-head">
    <button class="panel-close" aria-label="Close dossier" onclick="closeDossier()">✕</button>
    <span class="dz-badge" style="background:${hex2(badge[1],.16)};color:${badge[1]}">${esc(badge[0])}</span>
    <div class="dz-title">${esc(d.source)}<span class="arrow">→</span>${esc(d.target)}</div>
    <div class="dz-sub">${esc(d.provenance.proposed_by)} · Claude explained · ${esc(d.provenance.evaluator)}</div>
    <button class="dz-report" id="dz-report-btn" title="Download a self-contained report">⤓ Report</button>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Structure</div>
    <div id="molstar-wrap"></div>
    <div class="struct-meta">
      <span class="lbl">method</span> ${esc(st.method)}
      &nbsp;·&nbsp; <span class="lbl">${esc(st.confidence.type)}</span> ${esc(st.confidence.value)} ${esc(st.confidence.unit||'')}
      ${rcsb?`&nbsp;·&nbsp; <a href="${esc(rcsb)}" target="_blank" rel="noopener noreferrer" style="color:${COL.predicted};font-family:var(--mono);font-size:11px">${esc(st.pdb)} on RCSB →</a>`:''}<br>
      <span class="lbl">chains</span> ${esc(st.chains)}
    </div>
    ${st.interface_residues.length?`<div class="struct-resid">${st.interface_residues.map(r=>`<span class="r">${esc(r)}</span>`).join('')}</div>
      <div class="struct-note">interface residues ${esc(st.interface_source)}</div>`
      :`<div class="struct-note">${esc(st.interface_source)}</div>`}
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Mechanism</div>
    <div class="mech">${renderMechanism(d.mechanism)}</div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Confidence</div>
    <div class="conf-row">
      ${gauge('Topology', cf.topology, COL.topology, cf.topology!=null?cf.topology.toFixed(2):'—', cf.topology_rank?`L3 rank ${esc(cf.topology_rank)}`:'')}
      ${gauge('Structure', structVal(st), COL.predicted, `${esc(st.confidence.value)}`, esc(st.confidence.type))}
      ${gauge('Literature', cf.literature_count>=2?0.9:(cf.literature_count===1?0.5:0.15), COL.confirmed, esc(cf.literature), `${esc(cf.literature_count)} papers`)}
    </div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Skeptic</div>
    <div class="skeptic sk-${skClass}">
      <span class="badge">${esc(d.skeptic.verdict)}</span>
      <div>${esc(d.skeptic.reason)}${d.skeptic.caveat?`<br><span style="color:${COL.mut}">${esc(d.skeptic.caveat)}</span>`:''}</div>
    </div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Proposed wet-lab test</div>
    <div class="test-box">
      <div class="muts">${d.proposed_test.residues.map(r=>`<span class="mut">${esc(r)}</span>`).join('')}</div>
      ${esc(d.proposed_test.text)}
    </div>
  </div>

  ${renderDruggability(d.druggability)}

  <div class="dz-sec">
    <div class="dz-sec-h">Citations</div>
    <div class="cites">${d.citations.map(c=>{ const u=safeUrl(c.url); const label=`${esc(c.title)}`;
      return `<div class="cite-item"><span class="n">${esc(c.n)}</span>
      <div>${u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${label}</a>`:label}<br>
      <span class="id">PMID ${esc(c.pmid)}${c.journal?` · ${esc(c.journal)} ${esc(c.year)}`:''}</span></div></div>`;}).join('')}</div>
  </div>

  <div class="integrity-foot">
    <b>proposed by</b> ${esc(d.provenance.proposed_by)}<br>
    <b>explained by</b> ${esc(d.provenance.evidence_by)}<br>
    <b>structure</b> ${esc(d.provenance.structure_by)} · <b>scored by</b> ${esc(d.provenance.evaluator)}
  </div>`;
  document.getElementById('dossier-body').innerHTML=html;
  // wire handlers in JS (no interpolated data in inline onclick -> no JS-context XSS)
  const rb=document.getElementById('dz-report-btn'); if(rb) rb.onclick=()=>exportDossierReport(key);
  mountStructure(st);
}

function renderMechanism(mech){
  return mech.map(cl=>{
    const cites=cl.cites.map(n=>`<sup class="cite">${esc(n)}</sup>`).join('');
    return esc(cl.text)+cites;
  }).join('');
}

function gauge(cap,v,color,val,sub){
  const pct=Math.max(0,Math.min(1,v||0))*360;
  return `<div class="gauge"><div class="ring" style="background:conic-gradient(from -90deg,${color} 0 ${pct}deg,#182238 ${pct}deg 360deg)">
    <span class="val" style="color:${color}">${val}</span></div>
    <div class="cap">${cap}<br><span style="color:${COL.mut}">${sub||''}</span></div></div>`;
}
function renderDruggability(dr){
  const live=dr.live;
  const ens=safeEnsembl(dr.ensembl);
  const otTarget = ens ? `https://platform.opentargets.org/target/${ens}` : null;
  const head=`<div class="dz-sec-h">Druggability &amp; repurposing</div>`;

  if(!live || live.unavailable){
    // honest fallback: no live/cached data -> the curated prior, clearly labeled
    return `<div class="dz-sec">${head}
      <div class="kv"><b>${esc(dr.target)}</b> · <span style="color:${COL.mut}">live druggability ${live?esc(live.reason):'not cached'}</span><br>
      curated prior (not from a live source): tractability <b style="color:${drugColor(dr.curated_level)}">${esc(dr.curated_level)}</b> — ${esc(dr.curated_note)}
      ${otTarget?`<br><a href="${esc(otTarget)}" target="_blank" rel="noopener noreferrer" style="color:${COL.predicted};font-family:var(--mono);font-size:11px">open in Open Targets →</a>`:''}</div></div>`;
  }

  const t=live.tractability||{};
  const drugs=live.drugs||[];
  const badge = live.repurposing_lead
    ? `<span class="repurpose-badge">★ Repurposing lead</span>` : '';
  const drugRows = drugs.slice(0,6).map(x=>{
    const u=safeUrl(x.ot_url);
    const stage = x.approved ? `<span class="wl-badge wl-yes">Approved</span>` : `<span class="drug-stage">${esc(x.stage_label)}</span>`;
    return `<div class="drug-row">${stage}
      <div><b>${u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(x.name)}</a>`:esc(x.name)}</b>
      <span style="color:${COL.mut}">${x.mechanism?'· '+esc(x.mechanism):''}</span></div></div>`;
  }).join('');
  const more = drugs.length>6 ? `<div style="color:${COL.mut};font-size:11px;margin-top:4px">+${drugs.length-6} more in Open Targets</div>`:'';
  const drugBlock = drugs.length
    ? `<div class="drug-list">${drugRows}${more}</div>`
    : `<div class="kv" style="color:${COL.mut}">No known drugs against this target in Open Targets.</div>`;

  return `<div class="dz-sec">${head}
    <div class="kv"><b>${esc(live.gene)}</b> · small-molecule tractability <b style="color:${COL.predicted}">${esc(t.small_molecule||'none reported')}</b>
      ${t.antibody?` · antibody <b>${esc(t.antibody)}</b>`:''} ${badge}
    </div>
    ${drugBlock}
    ${live.repurposing_lead?`<div class="repurpose-note">Existing drugs against this host target are <b>repurposing hypotheses</b> — not validated for antiviral use, and no drug here treats the infection.</div>`:''}
    <div class="drug-src">source: ${esc(live.source)}, data ${esc(live.data_version)}, fetched ${esc(live.fetched)}
      ${otTarget?` · <a href="${esc(otTarget)}" target="_blank" rel="noopener noreferrer" style="color:${COL.predicted}">Open Targets →</a>`:''}</div>
  </div>`;
}

function structVal(st){ return st.confidence.type==='pLDDT'? st.confidence.value/100 : (st.confidence.type==='resolution'? 0.85 : 0.7); }
function drugColor(l){ return l==='LOW'?COL.viral:(l==='MODERATE'?COL.topology:COL.confirmed); }
function drugPct(l){ return l==='LOW'?30:(l==='MODERATE'?55:80); }
function hex2(hex,a){ const n=parseInt(hex.slice(1),16); return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`; }

/* ---------- Mol* : trimmed controls + app-owned fullscreen (P0 fix) ---------- */
let currentStruct=null, fsReturnFocus=null;

function makeMolstar(st){
  const el=document.createElement('pdbe-molstar');
  el.setAttribute('custom-data-url', st.url);
  el.setAttribute('custom-data-format','cif');
  el.setAttribute('hide-controls','true');
  el.setAttribute('hide-water','true');
  el.setAttribute('bg-color-r','5'); el.setAttribute('bg-color-g','7'); el.setAttribute('bg-color-b','14');
  el.setAttribute('landscape','true');
  if(st.kind==='predicted') el.setAttribute('alphafold-view','true');
  return el;
}
// call an instance method safely once the viewer has initialised
function molCall(el, fn){
  try { const v=el && el.viewerInstance; if(v) fn(v); } catch(e){ /* viewer not ready or API changed */ }
}
function molControlBar(getEl, onExpand){
  const bar=document.createElement('div'); bar.className='mol-controls';
  const mk=(label,title,handler)=>{ const b=document.createElement('button'); b.type='button';
    b.textContent=label; b.title=title; b.setAttribute('aria-label',title); b.onclick=handler; return b; };
  bar.append(
    mk('⟳','Toggle spin', ()=>molCall(getEl(), v=>v.visual.toggleSpin && v.visual.toggleSpin())),
    mk('⤢','Reset view', ()=>molCall(getEl(), v=>v.visual.reset && v.visual.reset({camera:true}))),
    mk('⛶','Expand (fullscreen)', onExpand),
  );
  return bar;
}

function mountStructure(st){
  const wrap=document.getElementById('molstar-wrap'); if(!wrap) return;
  currentStruct=st;
  wrap.innerHTML=`<div class="struct-chip" style="background:${st.kind==='experimental'?hex2(COL.human,.9):hex2(COL.predicted,.9)};color:#05121a">${st.kind==='experimental'?'EXPERIMENTAL · '+esc(st.source):'PREDICTED · '+esc(st.source)}</div><div class="dz-loading" style="padding:16px"><span class="spin"></span>loading structure…</div>`;
  const el=makeMolstar(st);
  el.addEventListener('load', ()=>{ const l=wrap.querySelector('.dz-loading'); if(l) l.remove(); }, {once:true});
  wrap.appendChild(el);
  wrap.appendChild(molControlBar(()=>el, ()=>openFullscreen(st)));
  // safety: remove the loading placeholder even if the load event never fires
  setTimeout(()=>{ const l=wrap.querySelector('.dz-loading'); if(l) l.remove(); }, 4000);
}

function openFullscreen(st){
  const ov=document.getElementById('struct-fullscreen');
  document.getElementById('fs-title').textContent =
    `${st.kind==='experimental'?'Experimental':'Predicted'} · ${st.source}`;
  const resid=document.getElementById('fs-resid');
  resid.innerHTML = st.interface_residues && st.interface_residues.length
    ? 'interface residues: '+st.interface_residues.map(r=>`<span class="r">${esc(r)}</span>`).join('')
    : esc(st.interface_source||'');
  const mount=document.getElementById('fs-mount'); mount.innerHTML='';
  const el=makeMolstar(st); mount.appendChild(el);
  document.getElementById('fs-spin').onclick=()=>molCall(el, v=>v.visual.toggleSpin && v.visual.toggleSpin());
  document.getElementById('fs-reset').onclick=()=>molCall(el, v=>v.visual.reset && v.visual.reset({camera:true}));
  fsReturnFocus=document.activeElement;
  ov.classList.remove('hidden');
  refreshInert();  // trap focus: background inert while any dialog is open
  document.body.style.overflow='hidden';
  document.getElementById('fs-close').focus();
}
function closeFullscreen(){
  const ov=document.getElementById('struct-fullscreen');
  if(ov.classList.contains('hidden')) return false;
  ov.classList.add('hidden');
  document.getElementById('fs-mount').innerHTML='';   // dispose the viewer
  refreshInert();
  document.body.style.overflow='';
  if(fsReturnFocus && fsReturnFocus.focus) fsReturnFocus.focus();
  return true;
}
// make the rest of the app inert (out of tab + a11y tree) while ANY dialog is open.
// Derived from state (not a boolean toggle) so nested/overlapping dialogs can never
// leave the background stuck-inert.
function refreshInert(){
  const on = fsOpen() || modalOpen();
  for(const id of ['topbar','main']){ const el=document.getElementById(id); if(el) el.inert=on; }
}
function fsOpen(){ return !document.getElementById('struct-fullscreen').classList.contains('hidden'); }

/* ---------- panels ---------- */
function renderNodePanel(id){
  _currentDossierKey=null;   // a node panel is not a dossier -> Export falls back to worklist CSV
  const n=DATA.graph.nodes.find(x=>x.id===id)||{};
  const partners=DATA.graph.edges.filter(e=>e.source===id||e.target===id);
  document.getElementById('dossier-body').innerHTML=`
    <div class="dz-head"><button class="panel-close" aria-label="Close panel" onclick="closeDossier()">✕</button>
    <div class="dz-title">${esc(id)}</div>
    <div class="dz-sub">${n.type==='viral'?'SARS-CoV-2 viral bait':'human prey'} · ${esc(n.uniprot||'')} · degree ${esc(n.degree||0)}</div></div>
    <div class="dz-sec"><div class="dz-sec-h">Incident edges</div>
    <div class="kv">${partners.map(e=>`${esc(e.source)} → ${esc(e.target)} <span style="color:${COL.mut}">(${esc(e.kind)})</span>`).join('<br>')||'—'}</div></div>`;
}

function renderIdle(){
  document.getElementById('dossier-body').innerHTML=`
    <div class="dz-empty-wrap">
      <div class="dz-panel-head">Dossier</div>
      <div class="dz-empty-center">
        <div class="dz-ring" aria-hidden="true"></div>
        <div class="dz-empty-prompt">Select a <b>node</b> to see its edges, or an <b>edge</b> for its structural dossier.</div>
        <button class="dz-cta" id="dz-predict"><span class="sp" aria-hidden="true">&#10022;</span> Predict the ORF6 gap</button>
      </div>
      <div class="dz-empty-foot">Every hypothesis Cartograph renders is backed by an openable paper. A claim with no citation does not render.</div>
    </div>`;
  const btn=document.getElementById('dz-predict');
  if(btn) btn.onclick=()=>{ document.getElementById('ask-input').value=''; probeBait(DATA.flagship.path[0]); };
}

/* ---------- modal (worklist / eval transparency / upload) ---------- */
function openModal(title, actionsHtml, bodyHtml){
  document.getElementById('modal-title').innerHTML=title;
  document.getElementById('modal-actions').innerHTML=actionsHtml||'';
  document.getElementById('modal-body').innerHTML=bodyHtml||'';
  modalReturnFocus=document.activeElement;
  const m=document.getElementById('modal'); m.classList.remove('hidden');
  refreshInert();
  document.getElementById('modal-close').focus();
  return m;
}
let modalReturnFocus=null;
function closeModal(){
  const m=document.getElementById('modal');
  if(m.classList.contains('hidden')) return false;
  m.classList.add('hidden');
  document.getElementById('modal-body').innerHTML='';
  refreshInert();
  if(modalReturnFocus && modalReturnFocus.focus) modalReturnFocus.focus();
  return true;
}
function modalOpen(){ return !document.getElementById('modal').classList.contains('hidden'); }

/* ---------- worklist: ranked "what to test next" ---------- */
const wlState = { sort:'l3_score', dir:-1, bait:'all', onlyDossier:false, onlyRecovered:false, onlyRepurpose:false };

function openWorklist(){
  const dm=DATA.druggability_meta;
  const src = dm ? ` · druggability: ${esc(dm.source.replace(' Platform GraphQL',''))} ${esc(dm.data_version)}` : '';
  openModal(`What to test next <small>top ${DATA.worklist.length} graph-proposed edges · deterministic L3${src}</small>`,
    `<button class="fs-btn" id="wl-csv">Export CSV</button>`, '');
  document.getElementById('wl-csv').onclick=exportWorklistCsv;
  renderWorklist();
}
function wlRows(){
  let rows=DATA.worklist.slice();
  if(wlState.bait!=='all') rows=rows.filter(r=>r.bait===wlState.bait);
  if(wlState.onlyDossier) rows=rows.filter(r=>r.has_dossier);
  if(wlState.onlyRecovered) rows=rows.filter(r=>r.recovered);
  if(wlState.onlyRepurpose) rows=rows.filter(r=>r.approved_drug);
  const k=wlState.sort, d=wlState.dir;
  const norm=v=> v==null ? null : (typeof v==='boolean' ? (v?1:0) : v);
  rows.sort((a,b)=>{ let x=norm(a[k]), y=norm(b[k]);
    // nulls always sort last regardless of direction
    if(x==null && y==null) return 0;
    if(x==null) return 1;
    if(y==null) return -1;
    if(typeof x==='number' && typeof y==='number') return d*(x-y);
    return d*String(x).localeCompare(String(y)); });
  return rows;
}
function renderWorklist(){
  const baits=[...new Set(DATA.worklist.map(r=>r.bait))].sort();
  const cols=[['edge','Edge'],['l3_score','L3'],['rank','Rank'],['recovered','Recovered'],
    ['structure','Structure'],['has_mechanism','Mechanism'],['tractability','Tractability'],['approved_drug','Repurposing'],['','']];
  const arr=k=> wlState.sort===k?`<span class="arr">${wlState.dir<0?'▼':'▲'}</span>`:'';
  const rows=wlRows();
  const badge=(on,txt,cls)=> on?`<span class="wl-badge ${cls}">${txt}</span>`:'<span class="wl-no">—</span>';
  const body=`
    <div class="wl-filters">
      <label>Bait <select id="wl-bait">${['all',...baits].map(b=>`<option ${b===wlState.bait?'selected':''}>${esc(b)}</option>`).join('')}</select></label>
      <label><input type="checkbox" id="wl-dos" ${wlState.onlyDossier?'checked':''}> has dossier</label>
      <label><input type="checkbox" id="wl-rec" ${wlState.onlyRecovered?'checked':''}> recovered held-out only</label>
      <label><input type="checkbox" id="wl-rep" ${wlState.onlyRepurpose?'checked':''}> repurposing leads only</label>
      <span style="margin-left:auto;color:var(--mut2);font-family:var(--mono);font-size:11px">${rows.length} edges</span>
    </div>
    <table class="wl-table"><thead><tr>${cols.map(([k,l])=>l?`<th data-k="${k}">${esc(l)} ${arr(k)}</th>`:'<th></th>').join('')}</tr></thead>
    <tbody>${rows.map(r=>`
      <tr class="${r.has_dossier?'clickable':''}" data-edge="${esc(r.edge)}">
        <td class="wl-edge">${esc(r.bait)} → ${esc(r.prey)}</td>
        <td class="wl-num">${r.l3_score.toFixed(3)}</td>
        <td class="wl-num">${esc(r.rank)}</td>
        <td>${badge(r.recovered,'held-out ✓','wl-yes')}</td>
        <td>${r.structure==='experimental'?'<span class="wl-badge wl-exp">experimental</span>':(r.structure==='predicted'?'<span class="wl-badge wl-pred">predicted</span>':'<span class="wl-no">—</span>')}</td>
        <td>${badge(r.has_mechanism,'cited','wl-yes')}</td>
        <td>${r.tractability?`${esc(r.tractability)}<span style="color:var(--mut2);font-size:10px">${r.n_drugs?` · ${esc(r.n_drugs)} drugs`:''}</span>`:(()=>{const u=safeUrl(r.opentargets);return u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer" style="color:var(--mut2);font-size:11px" onclick="event.stopPropagation()">Open Targets ↗</a>`:'<span class="wl-no">—</span>';})()}</td>
        <td>${r.approved_drug?'<span class="wl-badge wl-yes">★ lead</span>':'<span class="wl-no">—</span>'}</td>
        <td>${r.has_dossier?'<span style="color:var(--predicted);font-size:11px">open dossier →</span>':''}</td>
      </tr>`).join('')}</tbody></table>
    <div class="wl-note">L3 score and rank are computed on the blind training graph (held-out edges removed). <b>Tractability</b>/<b>Repurposing</b> are real Open Targets data (${DATA.druggability_meta?esc(DATA.druggability_meta.source)+', '+esc(DATA.druggability_meta.data_version)+', fetched '+esc(DATA.druggability_meta.fetched):'cached'}); a <b>★ lead</b> means the host target has an approved drug — a repurposing <i>hypothesis</i>, not a validated antiviral. Blanks mean "not established", never fabricated. Rows with a dossier are clickable.</div>`;
  document.getElementById('modal-body').innerHTML=body;
  document.getElementById('wl-bait').onchange=e=>{ wlState.bait=e.target.value; renderWorklist(); };
  document.getElementById('wl-dos').onchange=e=>{ wlState.onlyDossier=e.target.checked; renderWorklist(); };
  document.getElementById('wl-rec').onchange=e=>{ wlState.onlyRecovered=e.target.checked; renderWorklist(); };
  document.getElementById('wl-rep').onchange=e=>{ wlState.onlyRepurpose=e.target.checked; renderWorklist(); };
  document.querySelectorAll('.wl-table th[data-k]').forEach(th=>{ const k=th.dataset.k; if(!k) return;
    th.onclick=()=>{ if(wlState.sort===k) wlState.dir*=-1; else { wlState.sort=k; wlState.dir=-1; } renderWorklist(); }; });
  document.querySelectorAll('.wl-table tr.clickable').forEach(tr=>{
    tr.onclick=()=>{ const e=tr.dataset.edge; closeModal(); openDossier(e); }; });
}
function exportDossierReport(key){
  const d=DATA.dossiers[key]; if(!d) return;
  const st=d.structure, cf=d.confidence;
  const mech=d.mechanism.map(cl=>esc(cl.text)+cl.cites.map(n=>`<sup>[${esc(n)}]</sup>`).join('')).join('');
  const cites=d.citations.map(c=>{ const u=safeUrl(c.url);
    return `<li>[${esc(c.n)}] ${u?`<a href="${esc(u)}">${esc(c.title)}</a>`:esc(c.title)} — PMID ${esc(c.pmid)}${c.journal?`, ${esc(c.journal)} ${esc(c.year)}`:''}</li>`;}).join('');
  const rcsb=safeUrl(st.rcsb_url);
  const html=`<!doctype html><html><head><meta charset="utf-8"><title>Cartograph — ${esc(d.source)}→${esc(d.target)}</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#111;line-height:1.6}
h1{margin:0 0 4px}.sub{color:#666;font-size:13px;font-family:monospace}.badge{display:inline-block;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:700;background:#e6f0ff}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:#555;border-bottom:1px solid #ddd;padding-bottom:4px;margin-top:28px}
.r{display:inline-block;font-family:monospace;font-weight:600;background:#e9f9f2;padding:3px 6px;border-radius:4px;margin:2px}
.mut{color:#555;font-size:13px}.foot{margin-top:32px;padding-top:12px;border-top:1px solid #ddd;color:#888;font-size:11px;font-family:monospace}
sup{color:#0a7}a{color:#0a7}</style></head><body>
<div class="badge">${esc(d.status.toUpperCase())} EDGE</div>
<h1>${esc(d.source)} → ${esc(d.target)}</h1>
<div class="sub">Proposed by ${esc(d.provenance.proposed_by)} · explained by Claude · scored by ${esc(d.provenance.evaluator)}</div>
<h2>Structure</h2>
<p><b>${st.kind==='experimental'?'Experimental':'Predicted'}</b> · ${esc(st.source)} · ${esc(st.method)} · ${esc(st.confidence.type)} ${esc(st.confidence.value)} ${esc(st.confidence.unit||'')}${rcsb?` · <a href="${esc(rcsb)}">${esc(st.pdb)} on RCSB</a>`:''}<br>
<span class="mut">chains: ${esc(st.chains)}</span></p>
${st.interface_residues.length?`<p>Interface residues (${esc(st.interface_source)}):<br>${st.interface_residues.map(r=>`<span class="r">${esc(r)}</span>`).join('')}</p>`:`<p class="mut">${esc(st.interface_source)}</p>`}
<h2>Mechanism</h2><p>${mech}</p>
<h2>Confidence</h2><p class="mut">topology ${cf.topology!=null?esc(cf.topology.toFixed(2)):'—'}${cf.topology_rank?` (L3 rank ${esc(cf.topology_rank)})`:''} · structure ${esc(st.confidence.value)} ${esc(st.confidence.type)} · literature ${esc(cf.literature)} (${esc(cf.literature_count)} papers)</p>
<h2>Proposed wet-lab test</h2><p>Mutations: ${d.proposed_test.residues.map(r=>`<span class="r">${esc(r)}</span>`).join('')}<br>${esc(d.proposed_test.text)}</p>
<h2>Druggability &amp; repurposing</h2>${(()=>{ const L=d.druggability.live;
  if(L && !L.unavailable){
    const drugs=(L.drugs||[]).slice(0,8).map(x=>`<li>${esc(x.name)} — ${x.approved?'<b>Approved</b>':esc(x.stage_label)}${x.mechanism?' · '+esc(x.mechanism):''}</li>`).join('');
    return `<p>${esc(L.gene)} — small-molecule tractability <b>${esc((L.tractability||{}).small_molecule||'none reported')}</b>${L.repurposing_lead?' · <b>Repurposing lead</b> (has an approved drug — a hypothesis, not a validated antiviral)':''}.</p>`
      +(drugs?`<ol>${drugs}</ol>`:'<p class="mut">No known drugs against this target.</p>')
      +`<p class="mut">Source: ${esc(L.source)}, data ${esc(L.data_version)}, fetched ${esc(L.fetched)}.</p>`;
  }
  return `<p>${esc(d.druggability.target)} — curated prior (not from a live source): tractability ${esc(d.druggability.curated_level)}. ${esc(d.druggability.curated_note)}</p>`;
})()}
<h2>Citations</h2><ol>${cites}</ol>
<div class="foot">Generated by Cartograph. Every mechanistic clause opens to a real paper; predicted structures are labelled with a confidence number; the graph proposes edges deterministically and Claude only explains and cites. Ground truth: Gordon et al. 2020 (PMID 32353859).</div>
</body></html>`;
  const blob=new Blob([html],{type:'text/html'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download=`cartograph_${d.source}_${d.target}.html`; a.click(); URL.revokeObjectURL(a.href);
}

function exportWorklistCsv(){
  const cols=['bait','prey','l3_score','rank','recovered','structure','structure_source','has_mechanism','tractability','n_drugs','approved_drug','opentargets'];
  const esc2=v=>{ let s=String(v==null?'':v);
    if(/^[=+\-@\t\r]/.test(s)) s="'"+s;                // block CSV formula injection (incl. tab/CR lead-ins)
    return /[",\n\r]/.test(s)?`"${s.replace(/"/g,'""')}"`:s; };
  const lines=[cols.join(',')].concat(wlRows().map(r=>cols.map(c=>esc2(r[c])).join(',')));
  const blob=new Blob([lines.join('\n')],{type:'text/csv'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='cartograph_worklist.csv'; a.click(); URL.revokeObjectURL(a.href);
}

/* ---------- eval transparency: recovered vs missed held-out edges ---------- */
function openEvalTransparency(){
  const b=DATA.eval.baseline;
  const rec=(DATA.per_heldout_recovery||[]).slice()
    .sort((a,x)=> (x.recovered-a.recovered) || ((a.rank||1e9)-(x.rank||1e9)) || a.bait.localeCompare(x.bait));
  const nrec=rec.filter(r=>r.recovered).length;
  const pct=v=>Math.round(v*100)+'%';
  const body=`
    <div class="wl-filters" style="gap:18px">
      <span><b style="color:var(--ink)">${esc(b.n_targets)}</b> held-out Gordon edges</span>
      <span><b style="color:var(--confirmed)">${esc(nrec)}</b> recovered by L3</span>
      <span><b style="color:var(--ink)">${esc(b.n_recoverable)}</b> reachable ceiling (a length-3 path exists)</span>
      <span>precision@20 <b style="color:var(--confirmed)">${pct(b.precision_at_k['20'])}</b> · ROC-AUC <b>${esc(b.roc_auc)}</b></span>
    </div>
    <table class="wl-table"><thead><tr><th>Held-out edge</th><th>Outcome</th><th>L3 rank (in bait)</th><th>Length-3 path</th></tr></thead>
    <tbody>${rec.map(r=>`<tr>
      <td class="wl-edge">${esc(r.bait)} → ${esc(r.prey)}</td>
      <td>${r.recovered?'<span class="wl-badge wl-yes">recovered ✓</span>':'<span class="wl-badge" style="color:var(--rejected);background:rgba(255,92,106,.12)">missed</span>'}</td>
      <td class="wl-num">${r.recovered?esc(r.rank)+' / '+esc(r.n_candidates):'—'}</td>
      <td class="mono" style="font-size:11px;color:var(--mut)">${r.path?esc(r.path.join(' → ')):'no length-3 path exists (unreachable)'}</td>
    </tr>`).join('')}</tbody></table>
    <div class="wl-note">The evaluator was frozen (seed ${esc(DATA.eval.seed)}) and committed before any prediction code, in a module the predictor cannot import. Precision is reported with and without the disclosed pinned walkthrough edge (@20 ${pct(b.without_pinned.precision_at_k['20'])} without). "Missed" edges mostly have no length-3 path back to a co-prey — the honest topology ceiling, not a scoring error.</div>`;
  openModal(`Held-out transparency <small>every held-out edge: recovered or missed, and why</small>`, '', body);
}

/* ---------- upload: bring your own interactome (via the API) ---------- */
function openUpload(){
  const body=`
    <div class="up-form">
      <div class="up-msg info">Your edges &rarr; STRING enrichment &rarr; L3. Not added to the locked benchmark; edges with no cached evidence show topology only, never a fabricated mechanism or citation.</div>
      <label>Edge list (one <span class="mono">bait,prey</span> per line; a header row is optional)</label>
      <textarea id="up-edges" placeholder="ORF6,NUP98&#10;ORF6,RAE1&#10;N,G3BP1&#10;N,G3BP2"></textarea>
      <label>Held-out fraction for your own eval (0 to skip)</label>
      <input type="number" id="up-frac" min="0" max="0.5" step="0.05" value="0.2">
      <div style="display:flex;gap:10px;align-items:center">
        <button class="fs-btn" id="up-run" style="background:var(--panel2)">Enrich + run L3</button>
        <span id="up-status" style="font:500 12px/1 var(--mono);color:var(--mut)"></span>
      </div>
      <div id="up-result"></div>
    </div>`;
  openModal(`Upload interactome <small>your edges → STRING enrichment → deterministic L3</small>`, '', body);
  document.getElementById('up-run').onclick=runUpload;
}

async function runUpload(){
  const status=document.getElementById('up-status');
  const result=document.getElementById('up-result');
  const edges=document.getElementById('up-edges').value.trim();
  const frac=parseFloat(document.getElementById('up-frac').value)||0;
  result.innerHTML='';
  if(!edges){ status.textContent='paste an edge list first.'; return; }
  status.innerHTML='<span class="spin"></span> validating + enriching (STRING)…';
  try{
    const resp=await fetch('/api/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({edges, heldout_fraction:frac})});
    if(!resp.ok){ const e=await resp.json().catch(()=>({detail:`HTTP ${resp.status}`}));
      throw new Error(e.detail||`HTTP ${resp.status}`); }
    const d=await resp.json();
    status.textContent='';
    renderUploadResult(d);
  }catch(err){
    status.textContent='';
    result.innerHTML=`<div class="up-msg err">${esc(String(err.message||err))}<br><br>
      Upload needs the Cartograph API server. Start it: <b class="mono">./run.sh api</b> (the static demo runs without it).</div>`;
  }
}

function renderUploadResult(d){
  const preds=(d.predictions||[]);
  const ev=d.eval;
  const rows=preds.slice(0,25).map(p=>`<tr>
    <td class="wl-edge">${esc(p.bait)} → ${esc(p.prey)}</td>
    <td class="wl-num">${(p.l3_score||0).toFixed(3)}</td>
    <td class="mono" style="font-size:11px;color:var(--mut)">${p.path?esc(p.path.join(' → ')):'—'}</td>
    <td><span class="wl-no">no cached evidence — topology only</span></td></tr>`).join('');
  document.getElementById('up-result').innerHTML=`
    <div class="up-msg ok">Loaded ${esc(d.n_baits)} baits, ${esc(d.n_prey)} prey, ${esc(d.n_edges)} edges; added ${esc(d.n_enrichment)} STRING enrichment edges.
    ${ev?` Your own held-out eval: precision@${esc(ev.k)} <b>${Math.round(ev.precision*100)}%</b> on ${esc(ev.n_heldout)} held-out edges (seed ${esc(ev.seed)}).`:''}</div>
    <table class="wl-table" style="margin-top:12px"><thead><tr><th>Predicted edge</th><th>L3</th><th>Length-3 path</th><th>Evidence</th></tr></thead>
    <tbody>${rows||'<tr><td colspan=4 class="wl-no">no length-3 predictions</td></tr>'}</tbody></table>
    <div class="wl-note">These predictions are pure topology on your network. Cartograph shows no mechanism, structure, or citation here because none is cached for your edges — it will not fabricate one. Your data was not added to the locked Gordon benchmark.</div>`;
}

/* ---------- panel lifecycle: one system for every transient panel ---------- */
function closeDossier(){
  _currentDossierKey=null;
  if(cy){ cy.nodes().removeClass('dossier-target'); }
  renderIdle();
}
function hideChip(){ document.getElementById('precision-chip').classList.add('hidden'); }
function hideToast(){ document.getElementById('ask-toast').classList.add('hidden'); }

function wireGlobalHandlers(){
  document.getElementById('fs-close').onclick=closeFullscreen;
  document.getElementById('modal-close').onclick=closeModal;
  // click the modal backdrop (not the card) to dismiss
  document.getElementById('modal').addEventListener('mousedown', (e)=>{ if(e.target.id==='modal') closeModal(); });
  // Escape closes, in priority order: fullscreen > modal > chip > toast > dossier
  document.addEventListener('keydown', (e)=>{
    if(e.key!=='Escape') return;
    if(closeFullscreen()) return;
    if(closeModal()) return;
    const chip=document.getElementById('precision-chip');
    if(!chip.classList.contains('hidden')){ hideChip(); return; }
    if(!document.getElementById('ask-toast').classList.contains('hidden')){ hideToast(); return; }
    closeDossier();
  });
  // click empty graph background -> dismiss dossier + chip (click-away)
  cy.on('tap', (evt)=>{ if(evt.target===cy){ closeDossier(); hideChip(); hideToast(); } });
}

boot().then(()=>{ if(cy) wireGlobalHandlers(); });
