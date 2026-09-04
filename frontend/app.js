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
const state = { evalDone:false, loopRound:0, uploaded:null, layers:{known:true,enrichment:true,predicted:true,confirmed:true,conserved:false} };

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
    const enabled = MODE==='online';
    el.disabled = !enabled;
    // any control still disabled explains why on hover (no silent dead buttons)
    el.title = enabled ? '' : 'Requires the API server — run ./run.sh api';
  });
}

function wireTopActions(){
  document.getElementById('act-upload').onclick=()=>{ if(MODE!=='online') return;
    state.uploaded ? openUploadedPredictions() : openUpload(); };
  document.getElementById('act-export').onclick=exportCurrent;
  document.getElementById('act-compare').onclick=()=> isUploaded()?compareUploaded():openCompareStrains();
}

// Export: whatever you're looking at. A live agent dossier -> HTML report; a demo
// dossier -> its report; an uploaded map -> its predictions CSV; else the worklist.
let _currentDossierKey=null;
function exportCurrent(){
  if(state.liveDossier){ exportLiveDossierReport(state.liveDossier); return; }
  if(_currentDossierKey && DATA.dossiers[_currentDossierKey]){ exportDossierReport(_currentDossierKey); return; }
  if(state.viewingUploaded && state.uploaded){ exportUploadedCsv(); return; }
  exportWorklistCsv();
}
function exportUploadedCsv(){
  const cols=['bait','prey','l3_score','path'];
  const esc2=v=>{ let s=String(v==null?'':v); if(/^[=+\-@\t\r]/.test(s)) s="'"+s;
    return /[",\n\r]/.test(s)?`"${s.replace(/"/g,'""')}"`:s; };
  const lines=[cols.join(',')].concat((state.uploaded.predictions||[]).map(p=>
    [p.bait,p.prey,p.l3_score,(p.path||[]).join(' -> ')].map(esc2).join(',')));
  const blob=new Blob([lines.join('\n')],{type:'text/csv'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='cartograph_uploaded_predictions.csv'; a.click(); URL.revokeObjectURL(a.href);
  toast('Exported your <span class="k">predicted edges</span> as CSV.');
}
function exportLiveDossierReport(d){
  const st=d.structure||{};
  const cites=(d.citations||[]).map(c=>`<li>[${esc(c.n)}] ${esc(c.title)} — PMID ${esc(c.pmid)}${c.journal?`, ${esc(c.journal)} ${esc(c.year)}`:''} · <a href="https://pubmed.ncbi.nlm.nih.gov/${esc(c.pmid)}/">open</a></li>`).join('');
  const mech=(d.mechanism||[]).map(cl=>`<p>${esc(cl.text)} ${(cl.cites||[]).map(n=>`<sup>[${esc(n)}]</sup>`).join('')}</p>`).join('') || `<p><i>${esc(d.mechanism_status||'no cited mechanism')}</i></p>`;
  const html=`<!doctype html><meta charset="utf-8"><title>Cartograph — ${esc(d.source)}→${esc(d.target)}</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#111;line-height:1.6}
h1{margin:0}h2{font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:#555;border-bottom:1px solid #ddd;padding-bottom:4px;margin-top:26px}
.mut{color:#666;font-size:13px}sup,a{color:#0a7}</style>
<h1>${esc(d.source)} → ${esc(d.target)}</h1>
<div class="mut">Live Evidence Agent · every citation verified against the retrieved set · not on the locked benchmark</div>
<h2>Structure</h2><p>${st.source?`${esc(st.kind)} · ${esc(st.source)}${st.interface_residues&&st.interface_residues.length?` · interface ${st.interface_residues.map(esc).join(', ')}`:''}`:'no structure found'}</p>
<h2>Mechanism</h2>${mech}
<h2>Skeptic</h2><p>${esc((d.skeptic||{}).verdict||'')} — ${esc((d.skeptic||{}).reason||'')}</p>
<h2>Citations</h2><ol>${cites||'<li>none</li>'}</ol>
<h2>Provenance</h2><p class="mut">${esc((d.provenance||{}).evidence_by||'')}</p>`;
  const blob=new Blob([html],{type:'text/html'}); const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download=`cartograph_${d.source}_${d.target}.html`; a.click(); URL.revokeObjectURL(a.href);
  toast('Exported the <span class="k">live dossier</span> as a report.');
}

/* ---------- human-in-the-loop feedback (local, exportable, feeds the map) ----
   A wet-lab scientist's verdicts live in localStorage on THIS machine only. They
   are the human half of the loop: confirmed edges fold into the map as real
   green edges; refuted ones are struck out. Never touches the locked benchmark. */
const FB_KEY='cartograph.feedback.v1';
const FB_VERDICTS=['confirmed','to-test','refuted'];
function fbAll(){ try{ return JSON.parse(localStorage.getItem(FB_KEY))||{}; }catch{ return {}; } }
function fbGet(edge){ return fbAll()[edge]||null; }
function fbSet(edge, verdict, note){
  const a=fbAll();
  if(!verdict && !note){ delete a[edge]; }
  else { a[edge]={ verdict:verdict||null, note:(note||'').slice(0,600), ts:Date.now() }; }
  localStorage.setItem(FB_KEY, JSON.stringify(a));
  applyFeedbackToMap(); updateFbCount();
}
function applyFeedbackToMap(){
  if(!window.cy) return;
  cy.edges().removeClass('fb-confirmed fb-refuted fb-totest');
  for(const [edge,v] of Object.entries(fbAll())){
    const [s,t]=edge.split('|'); const e=edgeBetween(s,t);
    if(!e.length) continue;
    if(v.verdict==='confirmed'){ e.removeClass('hiddenEdge').style('display','element').addClass('fb-confirmed'); }
    else if(v.verdict==='refuted'){ e.addClass('fb-refuted'); }
    else if(v.verdict==='to-test'){ e.removeClass('hiddenEdge').style('display','element').addClass('fb-totest'); }
  }
}
function updateFbCount(){
  const n=Object.values(fbAll()).filter(v=>v.verdict).length;
  const el=document.getElementById('fb-count'); if(el){ el.textContent=n?`${n} marked`:''; }
}
function exportFeedbackJson(){
  const a=fbAll();
  const payload={ tool:'Cartograph', kind:'human-in-the-loop-feedback', exported:new Date().toISOString(),
    note:'Local wet-lab verdicts on L3-proposed edges. Not part of the locked benchmark.', feedback:a };
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
  const link=document.createElement('a'); link.href=URL.createObjectURL(blob);
  link.download='cartograph_feedback.json'; link.click(); URL.revokeObjectURL(link.href);
}
/* ---------- item 6: NDEx/Cytoscape (CX2) + Claude Science handoff ---------- */
function _dl(name, text, mime){
  const blob=new Blob([text],{type:mime}); const link=document.createElement('a');
  link.href=URL.createObjectURL(blob); link.download=name; link.click(); URL.revokeObjectURL(link.href);
}
// CX2 is the NDEx / Cytoscape exchange format: a JSON array of aspect objects.
function buildCX2(nodes, edges){
  const idx=new Map(nodes.map((n,i)=>[n.id,i]));
  const cxNodes=nodes.map((n,i)=>({ id:i, v:{ name:n.id, type:n.type||'', uniprot:n.uniprot||'', cluster:n.cluster||'' },
    ...(n.x!=null?{ x:Number(n.x), y:Number(n.y) }:{}) }));
  const cxEdges=edges.filter(e=>idx.has(e.source)&&idx.has(e.target)).map((e,i)=>({ id:i,
    s:idx.get(e.source), t:idx.get(e.target),
    v:{ interaction:e.kind||'interacts-with',
        ...(e.l3_score!=null?{ l3_score:Math.round(e.l3_score*1000)/1000 }:{}),
        ...(e.held_out?{ held_out_truth:true }:{}),
        ...(e.conserved?{ conserved_in_cov1_or_mers:true }:{}),
        ...(e.verdict?{ reviewer_verdict:e.verdict }:{}) } }));
  return [
    { CXVersion:"2.0", hasFragments:false },
    { metaData:[ {name:"networkAttributes",elementCount:1}, {name:"nodes",elementCount:cxNodes.length},
                 {name:"edges",elementCount:cxEdges.length} ] },
    { networkAttributes:[ { name:"Cartograph — SARS-CoV-2 → human interactome",
        description:"Gordon 2020 AP-MS edges + STRING v12 physical enrichment + deterministic degree-normalized L3 predictions + reviewer verdicts. Predicted edges carry interaction='predicted' and an l3_score; they are hypotheses, not measured interactions." } ] },
    { nodes:cxNodes },
    { edges:cxEdges },
    { status:[ { success:true } ] },
  ];
}
function exportNetworkCX2(){
  const nodes=DATA.graph.nodes;
  const seen=new Set(), edges=[];
  for(const e of DATA.graph.edges){ const k=KEY(e.source,e.target); if(seen.has(k))continue; seen.add(k);
    edges.push({ source:e.source, target:e.target, kind:e.kind, held_out:e.held_out, conserved:e.conserved }); }
  for(const p of DATA.graph.predicted){ const k=KEY(p.source,p.target); if(seen.has(k))continue; seen.add(k);
    edges.push({ source:p.source, target:p.target, kind:'predicted', l3_score:p.l3_score, held_out:p.held_out_true, conserved:p.conserved }); }
  const fb=fbAll();
  for(const e of edges){ const v=fb[KEY(e.source,e.target)]; if(v&&v.verdict) e.verdict=v.verdict; }
  _dl('cartograph_network.cx2', JSON.stringify(buildCX2(nodes, edges), null, 2), 'application/json');
  toast('Exported <span class="k">CX2</span> — open in Cytoscape or upload to NDEx.');
}
// Structured hypotheses handoff for a downstream Claude Science analysis.
function exportHypothesesJson(){
  const fb=fbAll();
  const b=DATA.eval.baseline;
  const hyps=DATA.worklist.map(r=>{
    const d=DATA.dossiers[r.edge];
    const v=fb[r.edge];
    return {
      hypothesis:r.hypothesis, bait:r.bait, prey:r.prey,
      l3_score:r.l3_score, l3_rank_in_bait:r.rank,
      novelty:r.novelty, skeptic_verdict:r.skeptic,
      conservation:r.conservation, crispr_functional_evidence:r.crispr, structure_band:r.structure_band, recovered_held_out:r.recovered,
      proposed_experiment:r.experiment,
      druggability:{ tractability:r.tractability, n_drugs:r.n_drugs, approved_drug_repurposing_hypothesis:r.approved_drug, open_targets:r.opentargets },
      mechanism: d?d.mechanism.map(c=>c.text):null,
      citations: d?d.citations.map(c=>({pmid:c.pmid, title:c.title, journal:c.journal, year:c.year})):null,
      reviewer_verdict: v?{verdict:v.verdict, note:v.note}:null,
    };
  });
  const payload={
    tool:"Cartograph", kind:"ranked-hypotheses-handoff", generated:new Date().toISOString(),
    provenance:{ proposed_by:"deterministic degree-normalized L3 (Kovács 2019)",
      explained_by:"Claude reasoning layer (Reader/Skeptic), grounded in verified edge packs",
      evaluator:"locked held-out benchmark, frozen before prediction",
      baseline:{ precision_at_20:b.precision_at_k['20'], roc_auc:b.roc_auc, average_precision:b.average_precision } },
    data_sources:{ interactome:"Gordon et al. 2020 SARS-CoV-2→human AP-MS (332 edges, 26 baits)",
      enrichment:"STRING v12.0 physical channel, score>=700",
      druggability: DATA.druggability_meta?`${DATA.druggability_meta.source} ${DATA.druggability_meta.data_version}`:"Open Targets",
      novelty:"NCBI PubMed co-mention counts (SARS-CoV-2 context)" },
    honesty:"Predicted edges are hypotheses, not measured interactions. Structural bands appear only where a real structure exists; no ipTM is fabricated. Repurposing flags are hypotheses, not validated antivirals. Reviewer verdicts and this handoff are NOT part of the locked benchmark.",
    hypotheses:hyps,
  };
  _dl('cartograph_hypotheses.json', JSON.stringify(payload, null, 2), 'application/json');
  toast(`Exported <span class="k">${hyps.length}</span> ranked hypotheses for Claude Science.`);
}
function importFeedbackJson(file){
  const rd=new FileReader();
  rd.onload=()=>{ try{
      const p=JSON.parse(rd.result); const fb=p.feedback||p;
      const cur=fbAll(); let n=0;
      for(const [edge,v] of Object.entries(fb)){
        if(typeof edge!=='string' || !/^[A-Za-z0-9_.\-]+\|[A-Za-z0-9_.\-]+$/.test(edge)) continue;   // trust boundary
        if(v && (FB_VERDICTS.includes(v.verdict) || v.verdict==null)){
          cur[edge]={ verdict:v.verdict||null, note:String(v.note||'').slice(0,600), ts:v.ts||Date.now() }; n++; }
      }
      localStorage.setItem(FB_KEY, JSON.stringify(cur));
      applyFeedbackToMap(); updateFbCount(); toast(`Imported <span class="k">${n}</span> feedback marks.`);
    }catch(e){ toast('Could not parse that feedback file.'); } };
  rd.readAsText(file);
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
      hasDossier: !!DATA.dossiers[id], conserved: !!e.conserved },
      classes: e.conserved?'isConserved':'' });
  }
  // predicted (missing) edges — hidden until revealed
  for(const p of DATA.graph.predicted){
    const id=KEY(p.source,p.target);
    if(seen.has(id)) continue; seen.add(id);
    els.push({ data:{ id, source:p.source, target:p.target, kind:'predicted',
      l3:p.l3_score, rank:p.rank, heldTrue:p.held_out_true, path:JSON.stringify(p.path||[]),
      hasDossier: !!DATA.dossiers[id], conserved: !!p.conserved },
      classes: 'predicted hiddenEdge' + (p.conserved?' isConserved':'') });
  }

  cy = cytoscape({
    container: document.getElementById('cy'),
    elements: els,
    layout:{ name:'preset' },
    minZoom:0.35, maxZoom:2.5, wheelSensitivity:0.25,
    style: cyStyle(),
  });
  cy.fit(undefined, 60);
  state.demoEls = cy.elements().jsons();   // snapshot so we can switch back from an uploaded map
  cy.on('tap','node', evt=>{ if(isUploaded()){ renderUploadedNodePanel(evt.target.id()); return; } selectNode(evt.target.id()); });
  cy.on('tap','edge', evt=>{ const e=evt.target;
    if(e.data('uploadedPred')){ openLiveDossier(e.data('source'), e.data('target'), e.data('l3')); return; }
    if(DATA.dossiers[e.id()]) openDossier(e.id()); });

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
  applyFeedbackToMap();   // restore any saved verdicts onto the fresh graph
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
    // human-in-the-loop verdicts fold back onto the map
    { selector:'edge.fb-confirmed', style:{ 'line-color':COL.confirmed,'width':4,'line-style':'solid','opacity':1,
      'shadow-blur':14,'shadow-color':COL.confirmed,'shadow-opacity':0.9 } },
    { selector:'edge.fb-totest', style:{ 'line-color':COL.topology,'width':3,'line-style':'dashed','opacity':1 } },
    { selector:'edge.fb-refuted', style:{ 'line-color':COL.rejected,'width':2,'line-style':'dotted','opacity':0.7 } },
    // cross-species conservation highlight (pan-coronavirus edges)
    { selector:'edge.conserved-hl', style:{ 'line-color':COL.conserved,'width':4,'opacity':1,
      'shadow-blur':14,'shadow-color':COL.conserved,'shadow-opacity':0.85 } },
    { selector:'edge.dim', style:{ 'opacity':0.12 } },
    { selector:'.hl', style:{ 'opacity':1 } },
  ];
}

/* ---------- controls ---------- */
function buildControls(){
  const defs=[['known','Known (AP-MS)',COL.known],['enrichment','STRING enrichment',COL.enrich],
    ['predicted','Predicted (L3)',COL.predicted],['confirmed','Confirmed (loop)',COL.confirmed],
    ['conserved','Conserved (CoV-1/MERS)',COL.conserved]];
  const nConserved=()=> DATA.graph.edges.filter(e=>!e.held_out && e.conserved).length
    + DATA.graph.predicted.filter(p=>p.conserved).length;
  const cnt=k=> k==='predicted'? DATA.graph.predicted.length
    : k==='conserved'? nConserved()
    : DATA.graph.edges.filter(e=>!e.held_out && e.kind===k).length;
  const wrap=document.getElementById('layer-toggles'); wrap.innerHTML='';
  for(const [k,label,c] of defs){
    const on = state.layers[k]!==false;
    const row=document.createElement('div'); row.className='layer-row'+(on?' on':''); row.dataset.k=k;
    row.setAttribute('role','switch'); row.setAttribute('aria-checked',on?'true':'false');
    row.setAttribute('tabindex','0'); row.setAttribute('aria-label',`${label} layer`);
    if(k==='conserved') row.title='Highlights edges the orthologous viral protein also makes in SARS-CoV-1 or MERS (pan-coronavirus).';
    row.innerHTML=`<span class="sw"></span><span class="dot" style="background:${c}"></span>${label}<span class="cnt">${cnt(k)}</span>`;
    row.onclick=()=>toggleLayer(k,row);
    row.onkeydown=(e)=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); toggleLayer(k,row); } };
    wrap.appendChild(row);
  }
  document.getElementById('btn-eval').onclick=()=> isUploaded()?showUploadedEval():runEval();
  document.getElementById('btn-loop').onclick=()=>{ if(!isUploaded()) runLoop(); };
  document.getElementById('btn-reset').onclick=()=> isUploaded()?cy.fit(undefined,55):location.reload();
  document.getElementById('btn-worklist').onclick=()=> isUploaded()?openUploadedPredictions():openWorklist();
  document.getElementById('btn-evaltrans').onclick=()=>{ if(!isUploaded()) openEvalTransparency(); };
}

function toggleLayer(k,row){
  state.layers[k]=!state.layers[k];
  row.classList.toggle('on',state.layers[k]);
  row.setAttribute('aria-checked', state.layers[k]?'true':'false');
  if(k==='conserved'){   // a highlight overlay, not a visibility layer
    cy.edges('.isConserved').forEach(e=>{
      if(e.hasClass('hiddenEdge')) return;
      e.toggleClass('conserved-hl', state.layers.conserved);
    });
    return;
  }
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

function isUploaded(){ return !!(state.viewingUploaded && state.uploaded); }

function buildSearch(){
  const input=document.getElementById('ask-input');
  input.addEventListener('keydown', e=>{ if(e.key==='Enter'){ runSearch(input.value); } });
  document.getElementById('ask-go').onclick=()=>runSearch(input.value);
  buildChips();
}
function buildChips(){
  const input=document.getElementById('ask-input');
  const up=isUploaded();
  const chips = up
    ? [[`What is ${uploadedBaits()[0]||'CDK2'} hitting?`, `what is ${uploadedBaits()[0]||'CDK2'} hitting`],
       ['My predictions','my predictions'],
       ['Run my eval','run my eval']]
    : [['ORF6’s unmapped targets','orf6 unmapped targets'],
       ['Most druggable predicted','most druggable predicted'],
       ['Run locked evaluation','run locked evaluation']];
  const wrap=document.getElementById('ask-chips'); wrap.innerHTML='';
  for(const [label,q] of chips){
    const b=document.createElement('button'); b.type='button'; b.className='ask-chip'; b.textContent=label;
    b.onclick=()=>{ input.value=q; runSearch(q); };
    wrap.appendChild(b);
  }
}

// Reconfigure every demo-bound surface for the active map (demo vs uploaded).
function applyMode(){
  const up=isUploaded();
  const input=document.getElementById('ask-input');
  if(input) input.placeholder = up ? 'Ask your map — e.g. what is CDK2 hitting, or run my eval'
                                   : 'Ask the map — what is ORF6 hitting that we haven’t mapped?';
  buildChips();
  // demo-only signal layers hidden on an uploaded map (no loop/conservation there)
  ['confirmed','conserved'].forEach(k=>{ const r=document.querySelector(`.layer-row[data-k="${k}"]`); if(r) r.style.display=up?'none':''; });
  const setBtn=(id,txt,dis,tip)=>{ const b=document.getElementById(id); if(!b)return;
    if(txt!=null) b.textContent=txt; b.disabled=!!dis; b.title=tip||''; };
  setBtn('btn-eval', up?'Run my eval':'Run evaluator', false);
  setBtn('btn-loop', up?'Loop round':null, up, up?'The fold-back loop runs on the SARS-CoV-2 locked benchmark':'');
  setBtn('btn-evaltrans', up?'Held-out (SARS-CoV-2)':null, up, up?'Held-out transparency is for the SARS-CoV-2 benchmark; your map has its own upload eval':'');
  setBtn('btn-worklist', up?'Your predictions':'What to test next', false);
}

function uploadedBaits(){ return state.uploaded ? [...new Set((state.uploaded.predictions||[]).map(p=>p.bait))] : []; }
function graphBaits(){ return DATA.graph.nodes.filter(n=>n.type==='viral').map(n=>n.id); }
function allBaits(){ return [...new Set(DATA.worklist.map(r=>r.bait))]; }

function parseIntent(text){
  const t=(text||'').toLowerCase().trim();
  if(!t) return {type:'none'};
  const rxq=s=>String(s).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  if(isUploaded()){
    if(/(prediction|what to test|worklist|to test)/.test(t)) return {type:'my_preds'};
    if(/(eval|precision|benchmark|held.?out|accuracy)/.test(t)) return {type:'my_eval'};
    for(const n of uploadedNodeIds()){ if(new RegExp(`\\b${rxq(n.toLowerCase())}\\b`).test(t)) return {type:'probe_uploaded', node:n}; }
    return {type:'unknown_uploaded'};
  }
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

function uploadedNodeIds(){ return state.uploaded ? state.uploaded.graph.nodes.map(n=>n.id) : []; }

function runSearch(text){
  const it=parseIntent(text);
  switch(it.type){
    case 'none': return;
    case 'my_preds': openUploadedPredictions(); return;
    case 'my_eval': showUploadedEval(); return;
    case 'probe_uploaded': probeUploaded(it.node); return;
    case 'unknown_uploaded':
      toast(`Try a protein in your map (e.g. <span class="k">${esc(uploadedBaits()[0]||'a bait')}</span>), <span class="k">my predictions</span>, or <span class="k">run my eval</span>.`);
      return;
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

function probeUploaded(node){
  const n=cy.getElementById(node); if(!n.length) return;
  cy.elements().removeClass('pathlit');
  n.addClass('pathlit');
  const preds=cy.edges().filter(e=>e.data('uploadedPred') && (e.data('source')===node||e.data('target')===node));
  preds.addClass('pathlit');
  cy.animate({center:{eles:n}, zoom: Math.max(cy.zoom(),0.8)},{duration:350});
  const np=preds.length;
  toast(np ? `<span class="k">${esc(node)}</span> — ${np} predicted edge${np===1?'':'s'} (dashed). Click one to run the Evidence Agent.`
           : `<span class="k">${esc(node)}</span> has no L3 predictions in your map.`);
}
function showUploadedEval(){
  const ev=state.uploaded && state.uploaded.eval;
  if(!ev){ toast('No held-out eval for this upload. Re-open <span class="k">Bring your own map</span> → <span class="k">＋ new edge list</span> and set a held-out fraction > 0 to benchmark your own network.'); return; }
  const chip=document.getElementById('precision-chip'); chip.classList.remove('hidden');
  chip.innerHTML=`<button class="panel-close" aria-label="Dismiss" onclick="hideChip()">✕</button>
    <div class="lbl">Your map · precision@${esc(ev.k)}</div>
    <div class="big">${Math.round(ev.precision*100)}%</div>
    <div class="sub">on <b>${esc(ev.n_heldout)}</b> of your own edges held out (seed ${esc(ev.seed)})<br>
    <span style="color:${COL.mut}">computed on YOUR network — never the locked Gordon benchmark. L3 topology only.</span></div>`;
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

function evalArithmeticRows(fu){
  const order=['precision_at_10','precision_at_20','precision_at_50',
               'recall_at_10','recall_at_20','recall_at_50','roc_auc','average_precision'];
  const pretty={precision_at_10:'precision@10',precision_at_20:'precision@20',
                precision_at_50:'precision@50',recall_at_10:'recall@10',
                recall_at_20:'recall@20',recall_at_50:'recall@50',
                roc_auc:'ROC-AUC',average_precision:'avg precision'};
  return order.filter(k=>fu.metrics[k]).map(k=>{
    const m=fu.metrics[k];
    const floor = m.enrichment!=null ? esc(m.enrichment.toFixed(0))+'x'
                : (m.null_value!=null ? esc(m.null_value) : '—');
    return `<tr><td>${esc(pretty[k]||k)}</td><td class="num">${esc(m.value)}</td>`
         + `<td class="num">${esc(m.max_attainable)}</td><td class="num">${floor}</td></tr>`;
  }).join('');
}

function toggleEvalDetail(){
  const d=document.getElementById('eval-detail');
  const b=document.getElementById('eval-detail-btn');
  if(!d) return;
  const on=d.classList.toggle('on');
  d.setAttribute('aria-hidden', on?'false':'true');
  if(b){ b.textContent = on ? 'hide arithmetic ▲' : 'show arithmetic ▼';
         b.setAttribute('aria-expanded', on?'true':'false'); }
}

function showPrecision(){
  const b=DATA.eval.baseline;
  const fu=DATA.eval.full_universe;
  const pk=b.precision_at_k, np=b.without_pinned;
  const pct=v=>Math.round(v*100)+'%';
  // Every number below is quoted against the full candidate universe. The restricted
  // figures stay in the artifact under eval.baseline so the correction is auditable.
  const head = fu ? fu.metrics['precision_at_'+b.headline_k] : null;
  const chip=document.getElementById('precision-chip'); chip.classList.remove('hidden');
  chip.innerHTML=`<button class="panel-close" aria-label="Dismiss evaluator panel" onclick="hideChip()">✕</button>
    <div class="lbl">Locked evaluator · precision@${esc(b.headline_k)}</div>
    <div class="big">${pct(b.headline_precision_at_k)}</div>
    ${fu?`<div class="sub"><span style="color:${COL.mut}">prevalence <b>${esc((fu.prevalence*100).toFixed(2))}%</b> on <b>${esc(fu.universe_size.toLocaleString())}</b> untested pairs</span>${head&&head.enrichment?` · <b style="color:${COL.confirmed}">${esc(head.enrichment.toFixed(0))}x</b> the floor`:''}<br>
    <button id="eval-detail-btn" class="fs-btn eval-detail-btn" aria-expanded="false"
            aria-controls="eval-detail" onclick="toggleEvalDetail()">show arithmetic ▼</button></div>
    <div id="eval-detail" class="eval-detail" aria-hidden="true">
      <table class="eval-table"><thead><tr><th>metric</th><th class="num">value</th><th class="num">max</th><th class="num">floor</th></tr></thead>
      <tbody>${evalArithmeticRows(fu)}</tbody></table>
      <div class="eval-note">universe <b>${esc(fu.candidate_set)}</b>, ${esc(fu.universe_size.toLocaleString())} pairs, ${esc(fu.n_targets)} held out · ties ${esc(fu.tie_handling)}${fu.open_world?`<br>open world: ${esc(fu.open_world.universe_size.toLocaleString())} pairs, prevalence ${esc((fu.open_world.prevalence*100).toFixed(3))}%`:''}</div>
    </div>`:''}
    <div class="sub">${(()=>{ const rr=b.reachable_recall; if(!rr||!fu) return '';
      return `<b style="color:${COL.confirmed}">on the reachable subset: ${esc(rr.recovered)}/${esc(rr.reachable)}</b> <span style="color:${COL.mut}">— L3 recovers every held-out edge a length-3 path can reach. Across all ${esc(fu.n_targets)}, recall@50 is ${esc(fu.metrics.recall_at_50.value)}.</span><br>`; })()}
    ${(()=>{ const cc=DATA.eval.conservation_channel; if(!cc) return '';
      const a=cc.l3_only_excl_pinned, x=cc.l3_plus_conservation_excl_pinned;
      return `<span style="color:${COL.conserved}">L3 + conservation (SARS-CoV-1/MERS): precision@10 ${pct(a.p10)}→<b>${pct(x.p10)}</b>, @20 ${pct(a.p20)}→<b>${pct(x.p20)}</b> excl. pinned — a real orthogonal gain</span><br>`; })()}
    ${(()=>{ const sc=DATA.eval.structure_channel; if(!sc) return '';
      return `<span style="color:${COL.mut}">L3 + structure (${esc(sc.n_pairs_with_structure)} pairs w/ a deposited complex): aggregate @20 <b>${pct(sc.l3_plus_structure_excl_pinned_p20)}</b> excl. pinned — unchanged; corroborates per-hypothesis</span><br>`; })()}
    ${(()=>{ const cr=DATA.eval.crispr_channel; if(!cr) return '';
      return `<a onclick="openCrisprPanel()" style="cursor:pointer;color:${COL.topology}">Option B · functional: ${esc(cr.n_crispr_supported)}/${esc(cr.n_host_factors)} host factors are independent CRISPR hits →</a><br>`; })()}
    <span style="color:${COL.mut}">without pinned edge: @20 ${pct(np.precision_at_k['20'])} (pinning does not inflate it)<br>
    frozen seed ${esc(DATA.eval.seed)}, committed before prediction</span></div>`;
  const r=document.getElementById('eval-readout');
  r.innerHTML = fu
    ? `held-out <b>${esc(fu.n_targets)}</b> · P@10/20/50 <b>${pct(pk['10'])}/${pct(pk['20'])}/${pct(pk['50'])}</b><br>prevalence <b>${esc((fu.prevalence*100).toFixed(2))}%</b> · ROC-AUC <b>${esc(fu.metrics.roc_auc.value)}</b> · AP <b>${esc(fu.metrics.average_precision.value)}</b>`
    : `held-out <b>${esc(b.n_targets)}</b> · P@10/20/50 <b>${pct(pk['10'])}/${pct(pk['20'])}/${pct(pk['50'])}</b>`;
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

  ${renderInSilico(d.structural_validation)}

  ${renderConservation(d.conservation)}

  ${renderCrispr(d.crispr)}

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

  <div class="dz-sec">
    <div class="dz-sec-h">Your verdict <span class="dz-sec-note">local · exportable · confirmed edges fold into the map</span></div>
    <div class="fb-box">
      <div class="fb-btns" id="fb-btns">
        <button class="fb-btn" data-v="confirmed">✓ Confirmed</button>
        <button class="fb-btn" data-v="to-test">◔ To test</button>
        <button class="fb-btn" data-v="refuted">✕ Refuted</button>
      </div>
      <textarea class="fb-note" id="fb-note" placeholder="Lab note (optional): assay, result, caveat…"></textarea>
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
  wireFeedback(key);
  mountStructure(st);
}

function wireFeedback(key){
  const cur=fbGet(key);
  const note=document.getElementById('fb-note');
  const btns=[...document.querySelectorAll('#fb-btns .fb-btn')];
  const paint=v=> btns.forEach(b=> b.classList.toggle('on', b.dataset.v===v));
  if(cur){ paint(cur.verdict); if(note) note.value=cur.note||''; }
  btns.forEach(b=> b.onclick=()=>{
    const v = fbGet(key)?.verdict===b.dataset.v ? null : b.dataset.v;   // click again to clear
    paint(v); fbSet(key, v, note?note.value:'');
  });
  if(note) note.onchange=()=> fbSet(key, fbGet(key)?.verdict||null, note.value);
}

/* ---------- live Evidence Agent: on-demand dossier for an uploaded edge ---------- */
function openLiveDossier(bait, prey, l3_score){
  const edge = bait+'|'+prey;
  _currentDossierKey = null;                 // not a cached dossier
  if(cy){ cy.nodes().removeClass('dossier-target'); }
  document.getElementById('dossier-body').innerHTML = `
    <div class="dz-head">
      <button class="panel-close" aria-label="Close dossier" onclick="closeDossier()">✕</button>
      <span class="dz-badge" style="background:${hex2(COL.predicted,.16)};color:${COL.predicted}">LIVE · EVIDENCE AGENT</span>
      <div class="dz-title">${esc(bait)}<span class="arrow">→</span>${esc(prey)}</div>
      <div class="dz-sub">deterministic retrieval · Claude reads · code-verified citations${state.uploaded?' · <a onclick="openUploadedPredictions()" style="cursor:pointer;color:var(--predicted)">← predictions</a>':''}</div>
    </div>
    <div class="dz-sec"><div class="dz-sec-h">Agent trace</div><div id="agent-trace" class="agent-trace"></div></div>
    <div id="live-dossier"></div>`;
  const trace=document.getElementById('agent-trace');
  const step=(html,cls='')=>{ const el=document.createElement('div'); el.className='trace-step '+cls; el.innerHTML=html; trace.appendChild(el); return el; };
  let last=null, finished=false;
  const spin=(html)=>{ if(last) last.classList.remove('run'); last=step('<span class="spin"></span> '+html,'run'); };
  const taxid=(state.uploaded&&state.uploaded.taxid)||'9606';
  const es=new EventSource(`/api/stream?edge=${encodeURIComponent(edge)}&taxid=${encodeURIComponent(taxid)}`);
  es.addEventListener('start', e=>{ const d=JSON.parse(e.data);
    step(`resolving <b>${esc(bait)} → ${esc(prey)}</b>${d.reasoning?'':' · <span style="color:var(--mut2)">reasoning layer not configured — deterministic facts only</span>'}`); });
  es.addEventListener('cached', ()=>step('loaded from cache (already computed this session)','ok'));
  es.addEventListener('resolving', ()=>spin('resolving identifiers (UniProt)'));
  es.addEventListener('retrieving', ()=>spin('retrieving literature, structure, druggability'));
  es.addEventListener('retrieved', e=>{ const d=JSON.parse(e.data); if(last)last.classList.remove('run');
    step(`retrieved <b>${esc(d.papers)}</b> papers · ${esc(d.comention_count)} co-mentions · structure: ${esc(d.structure)}`,'ok'); });
  es.addEventListener('reading', ()=>spin('Reader drafting a cited mechanism'));
  es.addEventListener('skeptic', ()=>spin('Skeptic: adversarial check'));
  es.addEventListener('vetoed', e=>{ if(last)last.classList.remove('run'); step('Skeptic <b>veto</b> — '+esc(JSON.parse(e.data).reason),'veto'); });
  es.addEventListener('verifying', ()=>spin('Verify gate: re-checking every citation'));
  es.addEventListener('verified', e=>{ const d=JSON.parse(e.data); if(last)last.classList.remove('run');
    step(`verify gate: kept <b>${esc(d.kept)}</b>, dropped <b>${esc(d.dropped)}</b> · structure ${d.structure_ok?'confirmed':'not used'}`,'ok'); });
  es.addEventListener('reviewing', ()=>spin('final adversarial review (drop-only)'));
  es.addEventListener('topology_only', e=>{ if(last)last.classList.remove('run'); step('topology-only — '+esc(JSON.parse(e.data).reason),'warn'); });
  es.addEventListener('result', e=>{ finished=true; if(last)last.classList.remove('run'); es.close(); renderLiveDossier(JSON.parse(e.data)); });
  es.addEventListener('error', e=>{ if(e.data){ if(last)last.classList.remove('run'); step('agent error — '+esc(JSON.parse(e.data).reason||'failed'),'veto'); } });
  es.addEventListener('done', ()=>{ es.close(); });
  es.onerror=()=>{ if(!finished){ if(last)last.classList.remove('run'); } es.close(); };
}

function _structureBlock(st){
  if(!st) return `<div class="dz-sec"><div class="dz-sec-h">Structure</div>
    <div class="struct-note">No deposited complex found for this pair and no confident model — no structure is shown (none is invented).</div></div>`;
  const rcsb=safeUrl(st.rcsb_url);
  const c=st.confidence||{};
  return `<div class="dz-sec"><div class="dz-sec-h">Structure ${st.kind==='predicted'?'<span class="wl-badge wl-pred">PREDICTED</span>':'<span class="wl-badge wl-exp">EXPERIMENTAL</span>'}</div>
    <div id="molstar-wrap"></div>
    <div class="struct-meta"><span class="lbl">method</span> ${esc(st.method)} &nbsp;·&nbsp;
      <span class="lbl">${esc(c.type||'')}</span> ${esc(c.value)} ${esc(c.unit||'')}
      ${rcsb?`&nbsp;·&nbsp; <a href="${esc(rcsb)}" target="_blank" rel="noopener noreferrer" style="color:${COL.predicted};font-family:var(--mono);font-size:11px">${esc(st.pdb)} on RCSB →</a>`:''}<br>
      <span class="lbl">chains</span> ${esc(st.chains)}</div>
    ${(st.interface_residues&&st.interface_residues.length)?`<div class="struct-resid">${st.interface_residues.map(r=>`<span class="r">${esc(r)}</span>`).join('')}</div>
      <div class="struct-note">interface residues ${esc(st.interface_source)}</div>`
      :`<div class="struct-note">${esc(st.interface_source||'')}</div>`}</div>`;
}

function renderLiveDossier(d){
  state.liveDossier = d;                 // so Export knows what you're looking at
  const st=d.structure, cf=d.confidence||{};
  const skClass=['pass','downgrade','veto'].includes((d.skeptic||{}).verdict)?d.skeptic.verdict:'pass';
  const mech = d.mechanism&&d.mechanism.length
    ? `<div class="mech">${renderMechanism(d.mechanism)}</div>`
    : `<div class="struct-note"><b>No cited mechanism.</b> ${esc(d.mechanism_status||'no mechanism supported by retrieved literature')} — the deterministic facts below are still real.</div>`;
  const cites = (d.citations||[]).map(c=>{ const u=safeUrl(c.url);
    return `<div class="cite-item"><span class="n">${esc(c.n)}</span><div>${u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">${esc(c.title)}</a>`:esc(c.title)}<br>
      <span class="id">PMID ${esc(c.pmid)}${c.journal?` · ${esc(c.journal)} ${esc(c.year)}`:''}</span></div></div>`;}).join('');
  document.getElementById('live-dossier').innerHTML=`
    ${_structureBlock(st)}
    <div class="dz-sec"><div class="dz-sec-h">Mechanism</div>${mech}</div>
    <div class="dz-sec"><div class="dz-sec-h">Confidence</div><div class="conf-row">
      ${gauge('Topology', null, COL.topology, '—', cf.topology_note||'L3')}
      ${st?gauge('Structure', st.kind==='experimental'?0.95:0.6, COL.predicted, esc((st.confidence||{}).value), esc((st.confidence||{}).type)):''}
      ${gauge('Literature', cf.literature_count>=2?0.9:(cf.literature_count===1?0.5:0.15), COL.confirmed, esc(cf.literature), `${esc(cf.literature_count)} cited`)}
    </div></div>
    ${renderConservation(d.conservation)}
    ${renderCrispr(d.crispr)}
    <div class="dz-sec"><div class="dz-sec-h">Skeptic</div>
      <div class="skeptic sk-${skClass}"><span class="badge">${esc((d.skeptic||{}).verdict)}</span>
      <div>${esc((d.skeptic||{}).reason||'')}${(d.skeptic||{}).caveat?`<br><span style="color:${COL.mut}">${esc(d.skeptic.caveat)}</span>`:''}</div></div></div>
    ${(d.proposed_test&&(d.proposed_test.text||d.proposed_test.residues.length))?`<div class="dz-sec"><div class="dz-sec-h">Proposed wet-lab test</div>
      <div class="test-box"><div class="muts">${d.proposed_test.residues.map(r=>`<span class="mut">${esc(r)}</span>`).join('')}</div>${esc(d.proposed_test.text)}</div></div>`:''}
    <div class="dz-sec">
      <div class="dz-sec-h">Your verdict <span class="dz-sec-note">local · exportable · confirmed edges fold into the map</span></div>
      <div class="fb-box">
        <div class="fb-btns" id="fb-btns">
          <button class="fb-btn" data-v="confirmed">✓ Confirmed</button>
          <button class="fb-btn" data-v="to-test">◔ To test</button>
          <button class="fb-btn" data-v="refuted">✕ Refuted</button>
        </div>
        <textarea class="fb-note" id="fb-note" placeholder="Lab note (optional): assay, result, caveat…"></textarea>
      </div>
    </div>
    ${renderDruggability(d.druggability)}
    ${cites?`<div class="dz-sec"><div class="dz-sec-h">Citations <span class="dz-sec-note">every one re-verified by code</span></div><div class="cites">${cites}</div></div>`:''}
    ${_agentReport(d.agent_report, d.queries)}
    <div class="integrity-foot"><b>proposed by</b> ${esc(d.provenance.proposed_by)}<br>
      <b>evidence by</b> ${esc(d.provenance.evidence_by)}<br>
      <b>structure</b> ${esc(d.provenance.structure_by)} · <b>${esc(d.provenance.evaluator)}</b></div>`;
  wireFeedback(`${d.source}|${d.target}`);
  if(st && st.url) mountStructure(st);
}

function _agentReport(rep, queries){
  const q = (rep&&rep.queries)||queries||[];
  if(!rep && !q.length) return '';
  const dropped=(rep&&rep.clauses_dropped_by_verify)||[];
  return `<div class="dz-sec"><div class="dz-sec-h">Agent provenance <span class="dz-sec-note">what was queried, retrieved, dropped</span></div>
    <div class="agent-report">
      ${rep?`<div>papers retrieved <b>${esc(rep.papers_retrieved)}</b> · co-mentions <b>${esc(rep.comention_count)}</b> · Skeptic <b>${esc(rep.skeptic_verdict)}</b></div>`:''}
      ${dropped.length?`<div class="drop">verify gate dropped ${dropped.length}: ${dropped.map(x=>`<span title="${esc(x.reason)}">PMID ${esc(x.pmid)}</span>`).join(', ')}</div>`:''}
      ${(rep&&rep.reviewer_flags&&rep.reviewer_flags.length)?`<div class="drop">reviewer flags: ${rep.reviewer_flags.map(f=>esc(f)).join('; ')}</div>`:''}
      <details><summary>${q.length} queries run</summary><div class="qlog">${q.map(x=>`<div>${esc(x.source)}: ${esc(x.query)} <span style="color:var(--mut2)">${esc(x.fetched_at||'')}</span></div>`).join('')}</div></details>
    </div></div>`;
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
function renderConservation(c){
  if(!c) return '';
  if(c.not_applicable) return `<div class="dz-sec">
    <div class="dz-sec-h">Cross-species conservation <span class="dz-sec-note">reference data</span></div>
    <div class="cons-verdict"><b>Not applicable</b> — ${esc(c.reason||'no reference data for this organism')}. The SARS-CoV-1/MERS comparison is coronavirus-specific; this is a distinct state, not an absence of conservation.</div></div>`;
  const strainRow=(name,st)=>`<div class="cons-row"><span class="cons-strain">${name}</span>${consStateChip(st)}</div>`;
  const verdict = c.is_conserved
    ? `<b style="color:${COL.conserved}">Corroborated across coronaviruses.</b> The orthologous viral protein binds the same human prey in ${esc(c.conserved_in.map(s=>s.replace('MERS-CoV','MERS')).join(' and '))}. A pan-coronavirus interaction is a stronger candidate to test.`
    : (c.label==='no ortholog'
        ? `No orthologous viral protein in SARS-CoV-1 or MERS, so conservation cannot be assessed. This is <b>not</b> evidence against the edge — it is a distinct state, never counted as "not conserved".`
    : (c.label==='not assessed'
        ? `The ortholog exists but was not represented in the SARS-CoV-1/MERS Gordon screen, so conservation cannot be assessed here — we do <b>not</b> claim the interaction was tested and absent.`
        : `SARS-CoV-2-specific in this data: the ortholog is in the SARS-CoV-1/MERS screen but no interaction with this prey is reported there.`));
  return `<div class="dz-sec">
    <div class="dz-sec-h">Cross-species conservation <span class="dz-sec-note">separate signal · not blended into the score</span></div>
    ${strainRow('SARS-CoV-1', c.per_strain['SARS-CoV-1'])}
    ${strainRow('MERS', c.per_strain['MERS-CoV'])}
    <div class="cons-verdict">${verdict}</div>
    <div class="struct-note">Gordon 2020 <i>Science</i> (SARS-CoV-1 + MERS); benchmark-isolated from the locked evaluator.</div>
  </div>`;
}
function renderCrispr(c){
  if(!c) return '';
  if(c.not_applicable) return `<div class="dz-sec">
    <div class="dz-sec-h">Independent functional evidence <span class="dz-sec-note">CRISPR</span></div>
    <div class="cons-verdict"><b>Not applicable</b> — ${esc(c.reason||'CRISPR reference data is SARS-CoV-2-specific')}. No dependency-screen reference set for this organism (never a blank implying absence).</div></div>`;
  const screens=c.screens.map(s=>{ const u=`https://pubmed.ncbi.nlm.nih.gov/${esc(s.pmid)}/`;
    return `<a href="${u}" target="_blank" rel="noopener noreferrer">${esc(s.name)}${s.soft?' *':''}</a>`; }).join(', ');
  const soft=c.n_screens>c.n_screens_excl_soft?` (${esc(c.n_screens_excl_soft)} excluding the soft-provenance screens *)`:'';
  return `<div class="dz-sec">
    <div class="dz-sec-h">Independent functional evidence <span class="dz-sec-note">CRISPR · orthogonal to binding</span></div>
    <div class="cons-verdict">Host factor in <b style="color:${COL.topology}">${esc(c.n_screens)} of ${esc(c.of_total)}</b> genome-wide CRISPR screens${soft}: ${screens}.${c.also_restriction_hit?' Also a knockout-defined restriction (antiviral) factor.':''}${c.also_gof_restriction?' Also restricts on overexpression (CRISPR-activation / GOF — not knockout-comparable).':''}</div>
    <div class="struct-note">A functional dependency hit is <b>not</b> evidence of a direct physical interaction — CRISPR screens and AP-MS binding capture different biology.${c.n_screens>c.n_screens_excl_soft?' * Wei / Baggen lack a reproducible genome-wide FDR list.':''}</div>
  </div>`;
}
function renderInSilico(sv){
  if(!sv) return '';
  const band = sv.band==='experimental'
    ? `<span class="wl-badge wl-exp">EXPERIMENTAL</span>`
    : (sv.iptm!=null
        ? `<span class="isilico-band tier${sv.tier}">${esc(sv.band)}</span>`
        : `<span class="wl-no">${esc(sv.band||'no model')}</span>`);
  let val='';
  if(sv.iptm!=null){
    val = `co-fold ipTM <b>${esc(sv.iptm)}</b>`
      + (sv.iptm_size_corrected!=null && sv.size_corrected ? ` · size-corrected <b>${esc(sv.iptm_size_corrected)}</b>` : ` · <span style="color:${COL.mut}">size-correction needs a population</span>`)
      + ` · <span style="color:${COL.predicted}">predicted</span>`;
  } else if(sv.provenance==='experimental'){
    val = `${esc(sv.label)}${sv.interface_contacts?` · <b>${esc(sv.interface_contacts)}</b> interface residues`:''}${sv.resolution_A?` · ${esc(sv.resolution_A)} Å`:''}`;
  } else {
    val = esc(sv.label||'');
  }
  return `<div class="dz-sec">
    <div class="dz-sec-h">In-silico validation</div>
    <div class="kv">${band} ${val}<br><span style="color:${COL.mut};font-size:11px">${esc(sv.note||'')}</span></div>
  </div>`;
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

function renderUploadedNodePanel(id){
  _currentDossierKey=null; state.liveDossier=null;
  const n=cy.getElementById(id); if(!n.length) return;
  cy.nodes().removeClass('dossier-target'); n.addClass('dossier-target');
  const inc=n.connectedEdges().map(e=>({s:e.data('source'),t:e.data('target'),k:e.data('kind'),
    l3:e.data('l3'), pred:!!e.data('uploadedPred')}));
  const known=inc.filter(e=>!e.pred);
  const preds=inc.filter(e=>e.pred);
  const rows=preds.map(e=>`<div class="up-node-pred" data-b="${esc(e.s)}" data-p="${esc(e.t)}" data-l="${e.l3||0}">
    <span>${esc(e.s)} → ${esc(e.t)} <span style="color:var(--mut2);font-size:11px">L3 ${(e.l3||0).toFixed(2)}</span></span>
    <button class="ev-run">▶ agent</button></div>`).join('');
  document.getElementById('dossier-body').innerHTML=`
    <div class="dz-head"><button class="panel-close" aria-label="Close panel" onclick="closeDossier()">✕</button>
      <div class="dz-title">${esc(id)}</div>
      <div class="dz-sub">${esc(n.data('type')==='viral'?'bait (column 1)':'prey (column 2)')} · degree ${esc(n.degree())} · your uploaded map</div></div>
    <div class="dz-sec"><div class="dz-sec-h">Known / enrichment edges</div>
      <div class="kv">${known.map(e=>`${esc(e.s)} → ${esc(e.t)} <span style="color:${COL.mut}">(${esc(e.k)})</span>`).join('<br>')||'—'}</div></div>
    ${preds.length?`<div class="dz-sec"><div class="dz-sec-h">Predicted edges · run the Evidence Agent</div>
      <div class="up-node-preds">${rows}</div></div>`:''}`;
  document.querySelectorAll('.up-node-pred').forEach(el=> el.querySelector('.ev-run').onclick=()=>
    openLiveDossier(el.dataset.b, el.dataset.p, parseFloat(el.dataset.l)));
}
function renderIdle(){
  const up=isUploaded();
  const prompt = up ? 'Select a <b>node</b> for its edges, or a dashed <b>predicted edge</b> to run the live Evidence Agent.'
                    : 'Select a <b>node</b> to see its edges, or an <b>edge</b> for its structural dossier.';
  const cta = up ? '<span class="sp" aria-hidden="true">&#10022;</span> Your predictions'
                 : '<span class="sp" aria-hidden="true">&#10022;</span> Predict the ORF6 gap';
  document.getElementById('dossier-body').innerHTML=`
    <div class="dz-empty-wrap">
      <div class="dz-panel-head">Dossier</div>
      <div class="dz-empty-center">
        <div class="dz-ring" aria-hidden="true"></div>
        <div class="dz-empty-prompt">${prompt}</div>
        <button class="dz-cta" id="dz-predict">${cta}</button>
      </div>
      <div class="dz-empty-foot">Every hypothesis Cartograph renders is backed by an openable paper. A claim with no citation does not render.</div>
    </div>`;
  const btn=document.getElementById('dz-predict');
  if(btn) btn.onclick=()=>{ if(isUploaded()){ openUploadedPredictions(); return; }
    document.getElementById('ask-input').value=''; probeBait(DATA.flagship.path[0]); };
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
const wlState = { sort:'l3_score', dir:-1, bait:'all', onlyDossier:false, onlyRecovered:false, onlyRepurpose:false, onlyNovel:false, onlyConserved:false, onlyCrispr:false };

function openWorklist(){
  const dm=DATA.druggability_meta;
  const src = dm ? ` · druggability: ${esc(dm.source.replace(' Platform GraphQL',''))} ${esc(dm.data_version)}` : '';
  openModal(`Testable hypotheses <small>${DATA.worklist.length} L3-proposed interactions, ranked · novelty grounded in PubMed${src}</small>`,
    `<span id="fb-count" class="fb-count"></span>
     <label class="fs-btn fs-file" title="Import feedback JSON">⤒ Import<input type="file" id="fb-imp" accept="application/json" hidden></label>
     <button class="fs-btn" id="fb-exp" title="Export your verdicts (JSON)">⤓ Feedback</button>
     <button class="fs-btn" id="wl-cx2" title="Network for Cytoscape / NDEx (CX2)">⤓ CX2</button>
     <button class="fs-btn" id="wl-hyp" title="Ranked hypotheses for Claude Science (JSON)">⤓ Hypotheses</button>
     <button class="fs-btn" id="wl-csv" title="Worklist as CSV">⤓ CSV</button>`, '');
  document.getElementById('wl-csv').onclick=exportWorklistCsv;
  document.getElementById('wl-cx2').onclick=exportNetworkCX2;
  document.getElementById('wl-hyp').onclick=exportHypothesesJson;
  document.getElementById('fb-exp').onclick=exportFeedbackJson;
  document.getElementById('fb-imp').onchange=e=>{ if(e.target.files[0]){ importFeedbackJson(e.target.files[0]); renderWorklist(); } };
  updateFbCount();
  renderWorklist();
}
function wlRows(){
  let rows=DATA.worklist.slice();
  if(wlState.bait!=='all') rows=rows.filter(r=>r.bait===wlState.bait);
  if(wlState.onlyDossier) rows=rows.filter(r=>r.has_dossier);
  if(wlState.onlyRecovered) rows=rows.filter(r=>r.recovered);
  if(wlState.onlyRepurpose) rows=rows.filter(r=>r.approved_drug);
  if(wlState.onlyNovel) rows=rows.filter(r=>r.novelty && r.novelty.tag==='novel');
  if(wlState.onlyConserved) rows=rows.filter(r=>r.conservation && r.conservation.is_conserved);
  if(wlState.onlyCrispr) rows=rows.filter(r=>r.crispr);
  const k=wlState.sort, d=wlState.dir;
  const NVORD={ 'novel':0,'partially known':1,'known':2,'unassessed':3 };
  const norm=v=> v==null ? null
    : (v && typeof v==='object' && v.tag!==undefined ? NVORD[v.tag]  // novelty -> tag order
    : (v && typeof v==='object' && v.is_conserved!==undefined ? (v.is_conserved?0:1)  // conservation -> conserved first
    : (typeof v==='boolean' ? (v?1:0) : v)));
  rows.sort((a,b)=>{ let x=norm(a[k]), y=norm(b[k]);
    // nulls always sort last regardless of direction
    if(x==null && y==null) return 0;
    if(x==null) return 1;
    if(y==null) return -1;
    if(typeof x==='number' && typeof y==='number') return d*(x-y);
    return d*String(x).localeCompare(String(y)); });
  return rows;
}
const NV = { 'known':['nv-known','known'], 'partially known':['nv-partial','partially known'],
  'novel':['nv-novel','novel'], 'unassessed':['nv-un','unassessed'] };
const SK = { 'pass':['sk-pass','passes Skeptic'], 'downgrade':['sk-down','downgraded'], 'veto':['sk-veto','vetoed'] };
function novChip(n){ if(!n) return '<span class="wl-no">—</span>';
  const [cls,lbl]=NV[n.tag]||['nv-un',n.tag]; return `<span class="wl-badge ${cls}" title="${esc(n.basis)}">${esc(lbl)}</span>`; }
function skChip(v){ const [cls,lbl]=SK[v]||['sk-pass',v]; return `<span class="wl-badge ${cls}">${esc(lbl)}</span>`; }
function consWlChip(c){ if(!c) return '<span class="wl-no">—</span>';
  if(c.is_conserved) return `<span class="wl-badge cons-yes" title="orthologous viral protein binds the same prey in ${esc(c.conserved_in.join(', '))}">✦ ${esc(c.label.replace('conserved: ',''))}</span>`;
  if(c.label==='no ortholog') return '<span class="wl-badge cons-na" title="no orthologous viral protein in SARS-CoV-1 or MERS (not the same as \'not conserved\')">no ortholog</span>';
  if(c.label==='not assessed') return '<span class="wl-badge cons-na" title="the ortholog exists but was not in the CoV-1/MERS Gordon screen — conservation cannot be assessed">not assessed</span>';
  return '<span class="wl-no" title="ortholog is in the CoV-1/MERS screen but no interaction with this prey is reported">not conserved</span>'; }
function crisprWlChip(c){ if(!c) return '<span class="wl-no">—</span>';
  const soft=c.n_screens>c.n_screens_excl_soft?` (${c.n_screens_excl_soft} excl. soft)`:'';
  return `<span class="wl-badge cr-yes" title="dependency hit in ${c.n_screens} of ${c.of_total} CRISPR screens${soft} — functional evidence, not a physical interaction">${c.n_screens}/${c.of_total} screens</span>`; }
function renderWorklist(){
  const baits=[...new Set(DATA.worklist.map(r=>r.bait))].sort();
  const cols=[['edge','Hypothesis'],['l3_score','L3'],['novelty','Novelty'],['skeptic','Skeptic'],
    ['conservation','Conservation'],['structure_band','Structure'],['crispr','Functional'],['tractability','Druggability'],['you','You'],['','']];
  const arr=k=> wlState.sort===k?`<span class="arr">${wlState.dir<0?'▼':'▲'}</span>`:'';
  const rows=wlRows();
  const body=`
    <div class="wl-filters">
      <label>Bait <select id="wl-bait">${['all',...baits].map(b=>`<option ${b===wlState.bait?'selected':''}>${esc(b)}</option>`).join('')}</select></label>
      <label><input type="checkbox" id="wl-nov" ${wlState.onlyNovel?'checked':''}> novel only</label>
      <label><input type="checkbox" id="wl-cons" ${wlState.onlyConserved?'checked':''}> conserved only</label>
      <label><input type="checkbox" id="wl-cr" ${wlState.onlyCrispr?'checked':''}> CRISPR-supported only</label>
      <label><input type="checkbox" id="wl-dos" ${wlState.onlyDossier?'checked':''}> has dossier</label>
      <label><input type="checkbox" id="wl-rec" ${wlState.onlyRecovered?'checked':''}> recovered held-out only</label>
      <label><input type="checkbox" id="wl-rep" ${wlState.onlyRepurpose?'checked':''}> repurposing leads only</label>
      <span style="margin-left:auto;color:var(--mut2);font-family:var(--mono);font-size:11px">${rows.length} hypotheses</span>
    </div>
    <table class="wl-table"><thead><tr>${cols.map(([k,l])=>l?`<th data-k="${k}">${esc(l)} ${arr(k)}</th>`:'<th></th>').join('')}</tr></thead>
    <tbody>${rows.map(r=>`
      <tr class="${r.has_dossier?'clickable':''}" data-edge="${esc(r.edge)}">
        <td class="wl-hyp">
          <div class="wl-edge">${esc(r.bait)} → ${esc(r.prey)}${r.recovered?' <span class="wl-badge wl-yes" title="a held-out Gordon edge L3 re-found blind">held-out ✓</span>':''}</div>
          <div class="wl-test" title="${esc(r.experiment)}">🧪 ${esc(r.experiment)}</div>
        </td>
        <td class="wl-num" title="rank ${esc(r.rank)} for ${esc(r.bait)} on the blind training graph">${r.l3_score.toFixed(3)}</td>
        <td>${novChip(r.novelty)}</td>
        <td>${skChip(r.skeptic)}</td>
        <td>${consWlChip(r.conservation)}</td>
        <td>${r.structure_band?`<span class="wl-badge wl-exp">${esc(r.structure_band)}</span>`:'<span class="wl-no" title="not yet folded — run a pooled-AF3 screen to get an ipTM band">no model</span>'}</td>
        <td>${crisprWlChip(r.crispr)}</td>
        <td>${r.tractability?`${esc(r.tractability)}${r.approved_drug?' <span class="wl-badge wl-yes">★ lead</span>':''}<span style="color:var(--mut2);font-size:10px">${r.n_drugs?` · ${esc(r.n_drugs)} drugs`:''}</span>`:(()=>{const u=safeUrl(r.opentargets);return u?`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer" style="color:var(--mut2);font-size:11px" onclick="event.stopPropagation()">Open Targets ↗</a>`:'<span class="wl-no">—</span>';})()}</td>
        <td>${(()=>{const f=fbGet(r.edge); if(!f||!f.verdict) return '<span class="wl-no">—</span>';
          const m={'confirmed':['fb-c','✓ confirmed'],'to-test':['fb-t','◔ to test'],'refuted':['fb-r','✕ refuted']}[f.verdict];
          return `<span class="wl-badge ${m[0]}"${f.note?` title="${esc(f.note)}"`:''}>${m[1]}</span>`;})()}</td>
        <td>${r.has_dossier?'<span style="color:var(--predicted);font-size:11px">open dossier →</span>':''}</td>
      </tr>`).join('')||`<tr><td colspan="10" class="wl-empty">No hypotheses match this filter.${wlState.onlyCrispr?' None of the top L3 predictions target a known CRISPR dependency factor — binding partners and functional hits are different biology (see Option B in the evaluator panel for the map-wide overlap).':''}</td></tr>`}</tbody></table>
    <div class="wl-note">Each row is one testable interaction the deterministic L3 layer proposes, ranked by L3 score (computed on the blind training graph). <b>Novelty</b> is grounded in a real PubMed co-mention count under SARS-CoV-2 context — <i>novel</i> means 0 co-mentions, a genuinely new prediction; <i>known</i> means a recovered Gordon edge or a cited edge pack; hover for the basis. <b>Skeptic</b> is the AP-MS frequent-flyer filter (a veto is a likely co-purification artifact). <b>Structure</b> shows a band only where a real structure exists; "no model" means nothing has been folded yet — no ipTM is invented. <b>Functional</b> shows how many of 7 genome-wide CRISPR screens call the host protein a dependency hit — orthogonal <i>functional</i> evidence, <b>not</b> proof of a physical interaction; it is expected to be sparse on these top predictions (binding partners and dependency hits are different biology), and the map-wide overlap is in the evaluator panel's Option B. <b>Druggability</b> is real Open Targets data (${DATA.druggability_meta?esc(DATA.druggability_meta.source)+', '+esc(DATA.druggability_meta.data_version):'cached'}); a <b>★ lead</b> is a repurposing <i>hypothesis</i>, not a validated antiviral. Blanks mean "not established", never fabricated. Rows with a dossier are clickable.</div>`;
  document.getElementById('modal-body').innerHTML=body;
  document.getElementById('wl-bait').onchange=e=>{ wlState.bait=e.target.value; renderWorklist(); };
  document.getElementById('wl-nov').onchange=e=>{ wlState.onlyNovel=e.target.checked; renderWorklist(); };
  document.getElementById('wl-cons').onchange=e=>{ wlState.onlyConserved=e.target.checked; renderWorklist(); };
  document.getElementById('wl-cr').onchange=e=>{ wlState.onlyCrispr=e.target.checked; renderWorklist(); };
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
${(()=>{ const f=fbGet(key); if(!f||!f.verdict) return '';
  return `<h2>Your verdict</h2><p><b>${esc(f.verdict)}</b>${f.note?`<br><span class="mut">${esc(f.note)}</span>`:''}<br><span class="mut">recorded locally by the reviewer; not part of the locked benchmark</span></p>`; })()}
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
  const cols=['bait','prey','hypothesis','l3_score','rank','novelty_tag','novelty_basis','skeptic',
    'conservation','conserved_in','crispr_n_screens','recovered','structure','structure_band','structure_source','has_mechanism','experiment',
    'tractability','n_drugs','approved_drug','opentargets'];
  const flat=r=>({...r, novelty_tag:r.novelty&&r.novelty.tag, novelty_basis:r.novelty&&r.novelty.basis,
    conservation:r.conservation&&r.conservation.label, conserved_in:r.conservation&&r.conservation.conserved_in.join(';'),
    crispr_n_screens:r.crispr&&r.crispr.n_screens});
  const esc2=v=>{ let s=String(v==null?'':v);
    if(/^[=+\-@\t\r]/.test(s)) s="'"+s;                // block CSV formula injection (incl. tab/CR lead-ins)
    return /[",\n\r]/.test(s)?`"${s.replace(/"/g,'""')}"`:s; };
  const lines=[cols.join(',')].concat(wlRows().map(flat).map(r=>cols.map(c=>esc2(r[c])).join(',')));
  const blob=new Blob([lines.join('\n')],{type:'text/csv'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='cartograph_worklist.csv'; a.click(); URL.revokeObjectURL(a.href);
}

/* ---------- Compare strains: cross-species conservation view ---------- */
const CONS_STATE = {
  conserved:['cons-yes','conserved'], not_conserved:['cons-no','not conserved'],
  no_ortholog:['cons-na','no ortholog'], not_screened:['cons-na','not screened'],
};
function consStateChip(st){ const [cls,lbl]=CONS_STATE[st]||['cons-no',st];
  const tip=st==='no_ortholog'?'no orthologous viral protein in this strain (distinct from not-conserved)'
    :st==='not_screened'?'ortholog exists but is absent from this strain’s Gordon screen — conservation cannot be assessed'
    :st==='not_conserved'?'ortholog is in this strain’s screen, but no interaction with this prey is reported'
    :'the ortholog binds the same human prey';
  return `<span class="wl-badge ${cls}" title="${tip}">${esc(lbl)}</span>`; }
const csState = { filter:'all' };
function openCompareStrains(){
  openModal(`Compare strains <small>SARS-CoV-2 vs SARS-CoV-1 + MERS · conservation from Gordon 2020 Science · benchmark-isolated</small>`, '', '');
  renderCompareStrains();
}
function renderCompareStrains(){
  const cs=DATA.eval.compare_strains, s=cs.summary;
  let rows=cs.rows.slice();
  if(csState.filter==='shared') rows=rows.filter(r=>r.shared);
  else if(csState.filter==='specific') rows=rows.filter(r=>!r.shared);
  const pct=n=>Math.round(100*n/s.n_gordon_edges);
  const fbtn=(k,l)=>`<button class="cmp-fbtn ${csState.filter===k?'on':''}" data-f="${k}">${l}</button>`;
  const body=`
    <div class="cmp-summary">
      <div class="cmp-stat"><b>${s.shared_any_strain}</b><span>of ${s.n_gordon_edges} CoV-2 edges are pan-coronavirus (${pct(s.shared_any_strain)}%)</span></div>
      <div class="cmp-stat"><b>${s.conserved_in_cov1}</b><span>conserved in SARS-CoV-1</span></div>
      <div class="cmp-stat"><b>${s.conserved_in_mers}</b><span>conserved in MERS</span></div>
      <div class="cmp-stat"><b>${s.cov2_specific}</b><span>SARS-CoV-2-specific</span></div>
      <div class="cmp-stat"><b>${s.no_ortholog_mers}</b><span>no MERS ortholog (accessory ORFs)</span></div>
    </div>
    <div class="wl-filters" style="gap:8px">
      ${fbtn('all','all map edges')}${fbtn('shared','shared only')}${fbtn('specific','CoV-2-specific only')}
      <span style="margin-left:auto;color:var(--mut2);font-family:var(--mono);font-size:11px">${rows.length} edges shown</span>
    </div>
    <table class="wl-table"><thead><tr><th>Edge</th><th>SARS-CoV-1</th><th>MERS</th><th>conservation</th></tr></thead>
    <tbody>${rows.map(r=>`<tr class="${DATA.dossiers[r.bait+'|'+r.prey]?'clickable':''}" data-edge="${esc(r.bait+'|'+r.prey)}">
      <td class="wl-edge">${esc(r.bait)} → ${esc(r.prey)}${r.predicted?' <span class="wl-badge wl-pred">predicted</span>':''}</td>
      <td>${consStateChip(r.per_strain['SARS-CoV-1'])}</td>
      <td>${consStateChip(r.per_strain['MERS-CoV'])}</td>
      <td>${r.shared?'<span class="wl-badge cons-yes">✦ shared</span>':'<span class="wl-no">CoV-2-specific</span>'}</td>
    </tr>`).join('')}</tbody></table>
    <div class="wl-note">An edge is <b>conserved</b> when the orthologous viral protein binds the <b>same</b> human prey in that strain (Gordon 2020 <i>Science</i>, SARS-CoV-1 366 + MERS 296 interactions; the Science SARS-CoV-2 map is deliberately excluded so it cannot touch the locked benchmark). Viral orthology is partial: Nsp1-16, N, M, E, Spike are conserved across all three; MERS encodes lineage-specific ORF3/4a/4b/5 and has <b>no ortholog</b> of any SARS accessory ORF. <b>“No ortholog” is not “not conserved”</b> — a missing ortholog is shown as its own state, never as a failed conservation. Conservation is a separate corroboration signal, never blended into the L3 score; measured as an evaluator prior it improves precision (see the evaluator panel).</div>`;
  document.getElementById('modal-body').innerHTML=body;
  document.querySelectorAll('.cmp-fbtn').forEach(b=> b.onclick=()=>{ csState.filter=b.dataset.f; renderCompareStrains(); });
  document.querySelectorAll('.wl-table tr.clickable').forEach(tr=>{
    tr.onclick=()=>{ closeModal(); openDossier(tr.dataset.edge); }; });
}

/* ---------- Functional genomics (CRISPR) — Option B corroboration ---------- */
function openCrisprPanel(){
  const c=DATA.eval.crispr_channel; if(!c) return;
  openModal(`Functional genomics corroboration <small>7 genome-wide CRISPR screens · Option B · orthogonal to physical binding</small>`, '', '');
  const rows=c.supported.map(s=>`<tr>
    <td class="wl-edge">${esc(s.gene)}</td>
    <td><span class="wl-badge cr-yes">${esc(s.n_screens)}/${esc(c.n_screens_total)} screens</span>${s.n_screens_excl_soft<s.n_screens?` <span class="wl-no" style="font-size:10px">(${esc(s.n_screens_excl_soft)} excl. soft)</span>`:''}</td>
    <td class="mono" style="font-size:11px;color:var(--mut)">${s.screens.map(x=>esc(x.split(' ')[0])).join(', ')}</td></tr>`).join('');
  document.getElementById('modal-body').innerHTML=`
    <div class="cmp-summary">
      <div class="cmp-stat"><b>${esc(c.n_crispr_supported)}</b><span>of ${esc(c.n_host_factors)} host factors in the map are independent CRISPR dependency hits</span></div>
      <div class="cmp-stat"><b>${esc(c.n_crispr_supported_excl_soft)}</b><span>excluding the two soft-provenance screens (Wei, Baggen)</span></div>
      <div class="cmp-stat"><b>${esc(c.n_screens_total)}</b><span>genome-wide screens · 433 sourced hits</span></div>
    </div>
    <table class="wl-table"><thead><tr><th>Host factor</th><th>Dependency hit in</th><th>screens</th></tr></thead><tbody>${rows}</tbody></table>
    <div class="wl-note">${esc(c.caveat)} Option A (the frozen held-out benchmark) remains the guaranteed number; this is corroboration, never the headline.</div>`;
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
let upMode='edges';
function openUpload(){
  openModal(`Bring your own map <small>your data → deterministic triage · not added to the locked benchmark</small>`,
    `<div class="up-tabs"><button class="up-tab" data-m="edges">Edge list</button><button class="up-tab" data-m="matrix">Pooled-AF3 ipTM matrix</button></div>`, '');
  document.querySelectorAll('.up-tab').forEach(b=> b.onclick=()=>setUpMode(b.dataset.m));
  setUpMode('edges');
}
function setUpMode(m){
  upMode=m;
  document.querySelectorAll('.up-tab').forEach(b=> b.classList.toggle('on', b.dataset.m===m));
  document.getElementById('modal-body').innerHTML = m==='edges' ? uploadEdgesForm() : uploadMatrixForm();
  document.getElementById('up-run').onclick = m==='edges' ? runUpload : runScreen;
}
function uploadEdgesForm(){
  return `<div class="up-form">
    <div class="up-msg info">Your edges → STRING enrichment → L3. Not added to the locked benchmark; edges with no cached evidence show topology only, never a fabricated mechanism or citation.</div>
    <label>Edge list (one <span class="mono">bait,prey</span> per line; a header row is optional)</label>
    <textarea id="up-edges" placeholder="MDM2,TP53&#10;CDK2,CCNA2&#10;RB1,E2F1&#10;BCL2,BAX"></textarea>
    <div style="display:flex;gap:16px;flex-wrap:wrap">
      <div style="flex:1;min-width:150px"><label>Held-out fraction for your own eval (0 to skip)</label>
        <input type="number" id="up-frac" min="0" max="0.5" step="0.05" value="0.2" style="width:100%"></div>
      <div style="flex:1;min-width:150px"><label>Organism (UniProt taxid) <span style="color:var(--mut2)">— the Evidence Agent resolves genes here</span></label>
        <input type="text" id="up-taxid" value="9606" placeholder="9606 = human" style="width:100%"></div>
    </div>
    <div style="display:flex;gap:10px;align-items:center">
      <button class="fs-btn" id="up-run" style="background:var(--panel2)">Enrich + run L3</button>
      <span id="up-status" style="font:500 12px/1 var(--mono);color:var(--mut)"></span>
    </div><div id="up-result"></div></div>`;
}
function uploadMatrixForm(){
  return `<div class="up-form">
    <div class="up-msg info">A pooled-AlphaFold3 virtual screen: a symmetric protein×protein ipTM matrix. Cartograph size-corrects ipTM (it rises with summed chain length), thresholds to candidate edges, bands each, and runs the L3 topology channel. Every ipTM is labelled predicted; nothing is fabricated; not added to the locked benchmark.</div>
    <label>ipTM matrix (CSV/TSV; header row of protein names, first column = names)</label>
    <textarea id="up-matrix" placeholder="prot,NUP98,RAE1,NUP214,G3BP1&#10;NUP98,1,0.88,0.72,0.15&#10;RAE1,0.88,1,0.65,0.10&#10;NUP214,0.72,0.65,1,0.14&#10;G3BP1,0.15,0.10,0.14,1"></textarea>
    <label>Keep pairs with (size-corrected) ipTM ≥</label>
    <input type="number" id="up-thr" min="0" max="1" step="0.05" value="0.55">
    <div style="display:flex;gap:10px;align-items:center">
      <button class="fs-btn" id="up-run" style="background:var(--panel2)">Size-correct + triage</button>
      <span id="up-status" style="font:500 12px/1 var(--mono);color:var(--mut)"></span>
    </div><div id="up-result"></div></div>`;
}

async function runScreen(){
  const status=document.getElementById('up-status'), result=document.getElementById('up-result');
  const matrix=document.getElementById('up-matrix').value.trim();
  const threshold=parseFloat(document.getElementById('up-thr').value)||0.55;
  result.innerHTML='';
  if(!matrix){ status.textContent='paste an ipTM matrix first.'; return; }
  status.innerHTML='<span class="spin"></span> size-correcting + triaging…';
  try{
    const resp=await fetch('/api/screen',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({matrix, threshold})});
    if(!resp.ok){ const e=await resp.json().catch(()=>({detail:`HTTP ${resp.status}`})); throw new Error(e.detail||`HTTP ${resp.status}`); }
    status.textContent=''; renderScreenResult(await resp.json());
  }catch(err){
    status.textContent='';
    result.innerHTML=`<div class="up-msg err">${esc(String(err.message||err))}<br><br>Needs the API server: <b class="mono">./run.sh api</b>.</div>`;
  }
}
function bandChip(b){ const t={'highly confident':3,'confident':2,'weak':1,'no better than random':0}[b];
  return `<span class="isilico-band tier${t==null?0:t}">${esc(b)}</span>`; }
function renderScreenResult(d){
  const rows=(d.top||[]).map(r=>`<tr>
    <td class="wl-edge">${esc(r.a)} — ${esc(r.b)}</td>
    <td class="wl-num">${esc(r.iptm)}</td>
    <td class="wl-num">${r.size_corrected?esc(r.iptm_size_corrected):'<span class="wl-no">—</span>'}</td>
    <td>${bandChip(r.band)}</td></tr>`).join('');
  const l3=(d.l3_proposals||[]).map(p=>`<tr><td class="wl-edge">${esc(p.a)} — ${esc(p.b)}</td>
    <td class="wl-num">${(p.l3_score||0).toFixed(3)}</td><td class="mono" style="font-size:11px;color:var(--mut)">${p.path?esc(p.path.join(' → ')):'—'}</td></tr>`).join('');
  document.getElementById('up-result').innerHTML=`
    <div class="up-msg ok">${esc(d.source)}: ${esc(d.n_proteins)} proteins, ${esc(d.n_pairs)} pairs; ${esc(d.n_kept)} above threshold ${esc(d.threshold)}. Size-correction ${d.size_corrected?`applied (${esc(d.n_lengths_resolved)} lengths from UniProt)`:'skipped (no lengths resolved)'}.</div>
    <table class="wl-table" style="margin-top:12px"><thead><tr><th>Candidate edge</th><th>ipTM</th><th>size-corrected</th><th>band</th></tr></thead><tbody>${rows||'<tr><td colspan=4 class="wl-no">none above threshold</td></tr>'}</tbody></table>
    ${l3?`<div style="margin-top:12px;font:600 10px/1 var(--mono);letter-spacing:.1em;color:var(--mut2);text-transform:uppercase">L3 topology channel · edges the folds may have missed</div>
    <table class="wl-table"><thead><tr><th>Proposed edge</th><th>L3</th><th>path</th></tr></thead><tbody>${l3}</tbody></table>`:''}
    <div class="wl-note">Bands are the AF3 ipTM calibration (≥0.80 highly confident · 0.60–0.80 confident · 0.55–0.60 weak · &lt;0.55 no better than random) applied to the <b>size-corrected</b> ipTM where correction ran (≥3 pairs with both chain lengths resolved), else the raw ipTM. Every value is predicted; a pair with an unresolved chain length is left uncorrected, never assigned an invented length. ${esc(d.note)}</div>`;
}

async function runUpload(){
  const status=document.getElementById('up-status');
  const result=document.getElementById('up-result');
  const edges=document.getElementById('up-edges').value.trim();
  const frac=parseFloat(document.getElementById('up-frac').value)||0;
  const taxid=(document.getElementById('up-taxid').value||'9606').trim().replace(/[^0-9]/g,'')||'9606';
  result.innerHTML='';
  if(!edges){ status.textContent='paste an edge list first.'; return; }
  status.innerHTML='<span class="spin"></span> validating + enriching (STRING)…';
  try{
    const resp=await fetch('/api/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({edges, heldout_fraction:frac})});
    if(!resp.ok){ const e=await resp.json().catch(()=>({detail:`HTTP ${resp.status}`}));
      throw new Error(e.detail||`HTTP ${resp.status}`); }
    const d=await resp.json();
    d.taxid=taxid;                      // the Evidence Agent resolves genes in this organism
    status.textContent='';
    renderUploadResult(d);
  }catch(err){
    status.textContent='';
    result.innerHTML=`<div class="up-msg err">${esc(String(err.message||err))}<br><br>
      Upload needs the Cartograph API server. Start it: <b class="mono">./run.sh api</b> (the static demo runs without it).</div>`;
  }
}

function renderUploadResult(d){
  state.uploaded = d;                 // persist so predictions/map survive closing the modal
  state.viewingUploaded = true;
  renderUploadedMap(d);               // the central map now shows YOUR interactome
  setStrainDropdown();                // the selector reflects what you're viewing
  applyMode();                        // reconfigure search/layers/eval/worklist for your map
  const ev=d.eval;
  document.getElementById('up-result').innerHTML=`
    <div class="up-msg ok">Loaded ${esc(d.n_baits)} baits, ${esc(d.n_prey)} prey, ${esc(d.n_edges)} edges; added ${esc(d.n_enrichment)} STRING enrichment edges.
    ${ev?` Your own held-out eval: precision@${esc(ev.k)} <b>${Math.round(ev.precision*100)}%</b> on ${esc(ev.n_heldout)} held-out (seed ${esc(ev.seed)}).`:''}
    <br><b>Your interactome is now on the map.</b> Predicted edges are clickable there; reopen this list anytime from the <b>map selector</b> (top-left).</div>
    <div class="up-actions">
      <button class="fs-btn" id="run-all-ev" style="background:#0e1526;color:var(--predicted);border-color:rgba(34,224,221,.4)">▶ Run Evidence Agent on top ${Math.min((d.predictions||[]).length,10)}</button>
      <button class="fs-btn" id="up-view-map">Explore the map ↗</button>
    </div>
    <div id="preds-wrap">${predictionsTable(d.predictions)}</div>
    <div class="wl-note">L3 is pure topology on your network. <b>Run Evidence Agent</b> fetches a live, verified dossier for a predicted edge: identifiers resolved (UniProt), literature + structure + druggability retrieved (NCBI/RCSB/AlphaFold/Open Targets), Claude reads, and a deterministic gate re-checks every citation — nothing is fabricated. Not added to the locked Gordon benchmark.</div>`;
  wirePredictions(document.getElementById('preds-wrap'));
  document.getElementById('run-all-ev').onclick=()=>runAllEvidence(document.getElementById('preds-wrap'));
  document.getElementById('up-view-map').onclick=closeModal;
}

/* ---------- uploaded-map workbench: map, selector, predictions, batch ---------- */
function predictionsTable(preds){
  const rows=(preds||[]).slice(0,25).map((p,i)=>`<tr data-b="${esc(p.bait)}" data-p="${esc(p.prey)}" data-l="${p.l3_score||0}">
    <td class="wl-edge">${esc(p.bait)} → ${esc(p.prey)}</td>
    <td class="wl-num">${(p.l3_score||0).toFixed(3)}</td>
    <td class="mono" style="font-size:11px;color:var(--mut)">${p.path?esc(p.path.join(' → ')):'—'}</td>
    <td class="pred-ev"><button class="ev-run">▶ run Evidence Agent</button></td></tr>`).join('');
  return `<table class="wl-table" style="margin-top:10px"><thead><tr><th>Predicted edge</th><th>L3</th><th>Length-3 path</th><th>Evidence Agent</th></tr></thead>
    <tbody>${rows||'<tr><td colspan=4 class="wl-no">no length-3 predictions</td></tr>'}</tbody></table>`;
}
function wirePredictions(root){
  root.querySelectorAll('tr[data-b]').forEach(tr=>{
    const btn=tr.querySelector('.ev-run'); if(!btn) return;
    btn.onclick=()=>{ closeModal(); openLiveDossier(tr.dataset.b, tr.dataset.p, parseFloat(tr.dataset.l)); };
  });
}
async function runAllEvidence(root){
  const rows=[...root.querySelectorAll('tr[data-b]')].slice(0,10);
  const runBtn=document.getElementById('run-all-ev'); if(runBtn){ runBtn.disabled=true; runBtn.textContent='running…'; }
  for(const tr of rows){
    const cell=tr.querySelector('.pred-ev');
    cell.innerHTML='<span class="spin"></span> running…';
    try{
      const r=await fetch('/api/evidence',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({bait:tr.dataset.b, prey:tr.dataset.p, l3_score:parseFloat(tr.dataset.l),
          taxid:(state.uploaded&&state.uploaded.taxid)||'9606'})});
      const d=await r.json();
      const nmech=(d.mechanism||[]).length, st=d.structure?(d.structure.pdb||'model'):'';
      cell.innerHTML=`<button class="ev-run">view →</button> <span style="font-size:10px;color:var(--mut2)">${nmech?nmech+' clauses':'no mechanism'}${st?' · '+esc(st):''}</span>`;
      cell.querySelector('.ev-run').onclick=()=>{ closeModal(); openLiveDossier(tr.dataset.b, tr.dataset.p, parseFloat(tr.dataset.l)); };
    }catch(e){ cell.innerHTML='<span class="wl-no">failed — needs the API</span>'; }
  }
  if(runBtn){ runBtn.disabled=false; runBtn.textContent='✓ all done — click any “view →”'; }
}
function renderUploadedMap(result){
  const g=result.graph; if(!g||!window.cy) return;
  const els=[], seen=new Set();
  for(const n of g.nodes) els.push({data:{id:n.id,label:n.id,type:n.type,degree:n.degree||1}});
  for(const e of g.edges){ const id=KEY(e.source,e.target); if(seen.has(id))continue; seen.add(id);
    els.push({data:{id,source:e.source,target:e.target,kind:e.kind}}); }
  for(const p of g.predicted){ const id=KEY(p.source,p.target); if(seen.has(id))continue; seen.add(id);
    els.push({data:{id,source:p.source,target:p.target,kind:'predicted',l3:p.l3_score,uploadedPred:true,
      path:JSON.stringify(p.path||[])}, classes:'predicted'}); }
  cy.stop(); closeDossier(); cy.elements().remove(); cy.add(els);
  cy.layout({name:'cose', animate:false, nodeRepulsion:9000, idealEdgeLength:78, padding:50, randomize:true}).run();
  cy.fit(undefined,55);
  updateLayerCountsUploaded(g);
}
function updateLayerCountsUploaded(g){
  updateLayerCount('known', g.edges.filter(e=>e.kind==='known').length);
  updateLayerCount('enrichment', g.edges.filter(e=>e.kind==='enrichment').length);
  updateLayerCount('predicted', g.predicted.length);
}
function setStrainDropdown(){
  const sel=document.getElementById('strain-select');
  const demo='SARS-CoV-2 · Gordon 2020';
  const mine = state.uploaded ? `Your uploaded map · ${state.uploaded.n_baits}×${state.uploaded.n_prey}` : null;
  const cur = state.viewingUploaded ? mine : demo;
  sel.innerHTML = [mine, demo].filter(Boolean).map(o=>`<option ${o===cur?'selected':''}>${esc(o)}</option>`).join('');
  sel.onchange=e=>{ if(e.target.value===demo) switchToDemo(); else switchToUploaded(); };
}
function switchToUploaded(){
  if(!state.uploaded) return;
  state.viewingUploaded=true; renderUploadedMap(state.uploaded); setStrainDropdown(); applyMode();
  toast('Viewing <span class="k">your uploaded map</span>. Click a predicted edge to run the Evidence Agent, or reopen the list from “Bring your own map”.');
}
function switchToDemo(){
  state.viewingUploaded=false; closeDossier();
  cy.stop(); cy.elements().remove(); cy.add(state.demoEls); cy.fit(undefined,60);
  ['known','enrichment','predicted','confirmed'].forEach(k=>{ const on=state.layers[k]!==false;
    const row=document.querySelector(`.layer-row[data-k="${k}"]`); if(row) row.classList.toggle('on',on); });
  buildLegend(); setStrainDropdown(); applyMode();
}
function compareUploaded(){
  openModal(`Compare strains <small>cross-species conservation</small>`, '', '');
  document.getElementById('modal-body').innerHTML=`
    <div class="wl-note" style="margin:20px;line-height:1.7">
      <b>Not applicable to your uploaded map.</b> Cross-species conservation needs a reference interactome for the orthologous species. Cartograph ships SARS-CoV-1 + MERS as the reference for the SARS-CoV-2 demo (Gordon 2020 <i>Science</i>); there is no built-in reference for your organism(s).<br><br>
      To compare across species, upload a second interactome for the orthologous species (open <b>Bring your own map → ＋ new edge list</b>) — automatic alignment is on the roadmap. Until then, each live dossier honestly shows conservation as <b>“not applicable”</b>, never a blank implying the interaction is absent elsewhere.
    </div>`;
}
// reopen the persisted predictions list (so running the agent never loses your data)
function openUploadedPredictions(){
  const d=state.uploaded; if(!d){ openUpload(); return; }
  if(!state.viewingUploaded) switchToUploaded();
  openModal(`Your uploaded map <small>${esc(d.n_baits)} baits · ${esc(d.n_prey)} prey · ${esc(d.n_edges)} edges · not on the locked benchmark</small>`,
    `<button class="fs-btn" id="up-new">＋ new edge list</button>`, '');
  document.getElementById('modal-body').innerHTML=`
    <div class="up-actions" style="padding:14px 20px 0">
      <button class="fs-btn" id="run-all-ev" style="background:#0e1526;color:var(--predicted);border-color:rgba(34,224,221,.4)">▶ Run Evidence Agent on top ${Math.min((d.predictions||[]).length,10)}</button>
    </div>
    <div id="preds-wrap" style="padding:8px 20px 20px">${predictionsTable(d.predictions)}</div>`;
  wirePredictions(document.getElementById('preds-wrap'));
  document.getElementById('run-all-ev').onclick=()=>runAllEvidence(document.getElementById('preds-wrap'));
  document.getElementById('up-new').onclick=openUpload;
}

/* ---------- panel lifecycle: one system for every transient panel ---------- */
function closeDossier(){
  _currentDossierKey=null; state.liveDossier=null;
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
