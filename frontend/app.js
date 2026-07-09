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

let DATA=null, cy=null, molViewer=null;
const state = { evalDone:false, loopDone:false, layers:{known:true,enrichment:true,predicted:true,confirmed:true} };

async function boot(){
  DATA = await (await fetch('data/cartograph_computed.json')).json();
  buildGraph();
  buildControls();
  buildLegend();
  renderIdle();
  document.getElementById('pill-data').textContent =
    `Gordon 2020 · ${DATA.meta.n_edges} edges · ${DATA.meta.n_baits} baits`;
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
      'text-outline-color':'#3a2a10','color':'#1a1206' } },
    { selector:'node[type="human"]', style:{
      'shape':'ellipse','background-color':'#16233f','border-color':COL.human,'color':COL.ink } },
    { selector:'node.dim', style:{ 'opacity':0.22 } },
    { selector:'node.pathlit', style:{ 'border-color':COL.predicted,'border-width':4,
      'background-color':'#123', 'shadow-blur':24,'shadow-color':COL.predicted,'shadow-opacity':0.9 } },
    { selector:'node.dossier-target', style:{ 'border-color':COL.predicted,'border-width':3 } },

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
    row.innerHTML=`<span class="sw"></span><span class="dot" style="background:${c}"></span>${label}<span class="cnt">${cnt(k)}</span>`;
    row.onclick=()=>toggleLayer(k,row);
    wrap.appendChild(row);
  }
  document.querySelectorAll('.ask-preset').forEach(b=> b.onclick=()=>runQuery(b.dataset.q));
  document.getElementById('btn-eval').onclick=runEval;
  document.getElementById('btn-loop').onclick=runLoop;
  document.getElementById('btn-reset').onclick=()=>location.reload();

  const il=document.getElementById('integrity-list'); il.innerHTML='';
  const items=[DATA.integrity.deterministic_path, DATA.integrity.no_citation_no_render,
    DATA.integrity.predicted_labeled, DATA.integrity.locked_evaluator];
  for(const t of items){ const li=document.createElement('li'); li.textContent=t; il.appendChild(li); }
}

function toggleLayer(k,row){
  state.layers[k]=!state.layers[k]; row.classList.toggle('on',state.layers[k]);
  const sel = k==='confirmed' ? 'edge.confirmed'
    : k==='predicted' ? 'edge[kind="predicted"]'
    : `edge[kind="${k}"]`;
  cy.edges(sel).forEach(e=>{
    if(e.hasClass('hiddenEdge')) return;
    e.style('display', state.layers[k]?'element':'none');
  });
}

function buildLegend(){
  const L=document.getElementById('legend');
  const rows=[['known','#3a4a6e','Known'],['enrich','#26324e','STRING'],['pred',COL.predicted,'Predicted L3'],
    ['hit',COL.confirmed,'Held-out ✓'],['miss',COL.rejected,'Miss']];
  L.innerHTML=rows.map(([_,c,t])=>`<span><i class="g" style="background:${c}"></i>${t}</span>`).join('');
}

/* ---------- ask / flagship animation ---------- */
function runQuery(q){
  if(q==='orf9b'){ revealPredictedFor('Orf9b'); openDossier('Orf9b|TOMM70'); return; }
  if(q==='n'){ revealPredictedFor('N'); openDossier('N|G3BP1'); return; }
  // flagship: Orf6 -> RAE1 via the length-3 path
  const path = DATA.flagship.path;               // ['Orf6','NUP98','NUP214','RAE1']
  toast(`<span class="k">Deterministic L3</span> asks: what edge is Orf6 missing? Walking the length-3 path <span class="k">${path.join(' → ')}</span> …`);
  cy.elements().addClass('dim');
  let i=0;
  const step=()=>{
    if(i<path.length){
      const n=cy.getElementById(path[i]); n.removeClass('dim').addClass('pathlit');
      if(i>0){ const e=cy.getElementById(KEY(path[i-1],path[i])) ; if(e.nonempty()){ e.removeClass('dim hiddenEdge').addClass('pathlit'); } }
      i++; setTimeout(step,650);
    } else {
      // reveal the predicted Orf6-RAE1 edge
      const pe=cy.getElementById(KEY('Orf6','RAE1'));
      pe.removeClass('hiddenEdge dim').addClass('pathlit');
      toast(`Graph proposes the missing edge <span class="k">Orf6 → RAE1</span> (L3 rank ${DATA.flagship.l3_rank}/${DATA.flagship.n_candidates}). Opening the structural dossier…`);
      setTimeout(()=>{ cy.elements().removeClass('dim'); openDossier('Orf6|RAE1'); }, 900);
    }
  };
  step();
}
function revealPredictedFor(bait){
  cy.edges('edge[kind="predicted"]').forEach(e=>{ if(e.source().id()===bait){ e.removeClass('hiddenEdge'); e.style('display','element'); } });
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
  const chip=document.getElementById('precision-chip'); chip.classList.remove('hidden');
  chip.innerHTML=`<div class="lbl">Locked evaluator · precision@${b.headline_k}</div>
    <div class="big">${Math.round(b.headline_precision_at_k*100)}%</div>
    <div class="sub">on <b>${b.n_targets}</b> real held-out Gordon edges (${b.n_recoverable} reachable by L3)<br>
    ROC-AUC <b>${b.roc_auc}</b> · recall@50 <b>${Math.round(b.recall_at_k['50']*100)}%</b><br>
    <span style="color:${COL.mut}">frozen seed ${DATA.eval.seed}, committed before prediction</span></div>`;
  const r=document.getElementById('eval-readout');
  r.innerHTML=`held-out <b>${b.n_targets}</b> · precision@${b.headline_k} <b>${(b.headline_precision_at_k*100).toFixed(0)}%</b><br>ROC-AUC <b>${b.roc_auc}</b> · recall@50 <b>${(b.recall_at_k['50']*100).toFixed(0)}%</b>`;
}

/* ---------- loop round ---------- */
function runLoop(){
  if(state.loopDone) return; state.loopDone=true;
  const lp=DATA.eval.loop;
  // confirm the recovered-true greens -> turn confirmed, densify
  cy.edges('edge.hit').addClass('confirmed');
  for(const [s,t] of lp.confirmed_edges){
    const e=cy.getElementById(KEY(s,t)); if(e.nonempty()) e.addClass('confirmed');
  }
  toast(`<span class="k">Loop round</span>: confirm ${lp.confirmed_edges.length} recovered-true edges (each a real Gordon edge, each L3-rank #1), fold them back as known, re-score the still-hidden edges.`);
  const chip=document.getElementById('precision-chip');
  const before=Math.round(lp.before_precision_at_20*100), after=Math.round(lp.after_precision_at_20*100);
  chip.innerHTML=`<div class="lbl">Loop round · precision@20 on remaining held-out</div>
    <div class="big">${before}% → ${after}%</div>
    <div class="sub">confirmed <b>${lp.confirmed_edges.length}</b> edges, folded back as known<br>
    recoverable ${lp.before_recoverable} → <b>${lp.after_recoverable}</b><br>
    <span style="color:${COL.mut}">measured on the remaining hidden edges (fair before/after)</span></div>`;
  document.getElementById('btn-loop').disabled=true;
}

/* ---------- dossier ---------- */
function selectNode(id){
  const dz=DATA.dossiers; // if a node has a single dossier'd incident edge, show it
  const inc=Object.keys(dz).filter(k=>k.split('|').includes(id));
  if(inc.length) openDossier(inc[0]); else renderNodePanel(id);
}

function openDossier(key){
  const d=DATA.dossiers[key]; if(!d) return;
  cy.nodes().removeClass('dossier-target');
  cy.getElementById(d.source).addClass('dossier-target');
  cy.getElementById(d.target).addClass('dossier-target');
  const badge = d.status==='predicted'?['PREDICTED EDGE',COL.predicted]
    : d.status==='confirmed'?['CONFIRMED EDGE',COL.confirmed]:['KNOWN EDGE',COL.human];
  const st=d.structure, cf=d.confidence;
  const html=`
  <div class="dz-head">
    <span class="dz-badge" style="background:${hex2(badge[1],.16)};color:${badge[1]}">${badge[0]}</span>
    <div class="dz-title">${d.source}<span class="arrow">→</span>${d.target}</div>
    <div class="dz-sub">${d.provenance.proposed_by} · Claude explained · ${d.provenance.evaluator}</div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Structure</div>
    <div id="molstar-wrap"><div class="struct-chip" style="background:${st.kind==='experimental'?hex2(COL.human,.9):hex2(COL.predicted,.9)};color:#05121a">
      ${st.kind==='experimental'?'EXPERIMENTAL · '+st.source:'PREDICTED · '+st.source}</div></div>
    <div class="struct-meta">
      <span class="lbl">method</span> ${st.method}
      &nbsp;·&nbsp; <span class="lbl">${st.confidence.type}</span> ${st.confidence.value} ${st.confidence.unit||''}<br>
      <span class="lbl">chains</span> ${st.chains}
    </div>
    ${st.interface_residues.length?`<div class="struct-resid">${st.interface_residues.map(r=>`<span class="r">${r}</span>`).join('')}</div>
      <div class="struct-note">interface residues ${st.interface_source}</div>`
      :`<div class="struct-note">${st.interface_source}</div>`}
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Mechanism <span style="color:${COL.mut};font-weight:400;text-transform:none;letter-spacing:0"> — every clause opens to a paper</span></div>
    <div class="mech">${renderMechanism(d.mechanism)}</div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Confidence <span style="color:${COL.mut};font-weight:400;text-transform:none;letter-spacing:0"> — three signals, never blended</span></div>
    <div class="conf-row">
      ${gauge('Topology', cf.topology, COL.topology, cf.topology!=null?cf.topology.toFixed(2):'—', cf.topology_rank?`L3 rank ${cf.topology_rank}`:'')}
      ${gauge('Structure', structVal(st), COL.predicted, `${st.confidence.value}`, st.confidence.type)}
      ${gauge('Literature', cf.literature_count>=2?0.9:(cf.literature_count===1?0.5:0.15), COL.confirmed, cf.literature, `${cf.literature_count} papers`)}
    </div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Skeptic</div>
    <div class="skeptic sk-${d.skeptic.verdict}">
      <span class="badge">${d.skeptic.verdict}</span>
      <div>${d.skeptic.reason}${d.skeptic.caveat?`<br><span style="color:${COL.mut}">${d.skeptic.caveat}</span>`:''}</div>
    </div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Proposed wet-lab test</div>
    <div class="test-box">
      <div class="muts">${d.proposed_test.residues.map(r=>`<span class="mut">${r}</span>`).join('')}</div>
      ${d.proposed_test.text}
    </div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Druggability <span style="color:${COL.mut};font-weight:400;text-transform:none;letter-spacing:0"> — Open Targets</span></div>
    <div class="kv"><b>${d.druggability.target}</b> · tractability <b style="color:${drugColor(d.druggability.level)}">${d.druggability.level}</b>
    <div class="drug-bar"><i style="width:${drugPct(d.druggability.level)}%;background:${drugColor(d.druggability.level)}"></i></div>
    ${d.druggability.note}
    ${d.druggability.ensembl?`<br><a href="https://platform.opentargets.org/target/${d.druggability.ensembl}" target="_blank" style="color:${COL.predicted};font-family:JetBrains Mono,monospace;font-size:11px">open in Open Targets →</a>`:''}</div>
  </div>

  <div class="dz-sec">
    <div class="dz-sec-h">Citations</div>
    <div class="cites">${d.citations.map(c=>`<div class="cite-item"><span class="n">${c.n}</span>
      <div><a href="${c.url}" target="_blank">${c.title}</a><br>
      <span class="id">PMID ${c.pmid}${c.journal?` · ${c.journal} ${c.year}`:''}</span></div></div>`).join('')}</div>
  </div>

  <div class="integrity-foot">
    <b>proposed by</b> ${d.provenance.proposed_by}<br>
    <b>explained by</b> ${d.provenance.evidence_by}<br>
    <b>structure</b> ${d.provenance.structure_by} · <b>scored by</b> ${d.provenance.evaluator}
  </div>`;
  document.getElementById('dossier-body').innerHTML=html;
  mountStructure(st);
}

function renderMechanism(mech){
  return mech.map(cl=>{
    const cites=cl.cites.map(n=>`<sup class="cite">${n}</sup>`).join('');
    return cl.text+cites;
  }).join('');
}

function gauge(cap,v,color,val,sub){
  const pct=Math.max(0,Math.min(1,v||0))*360;
  return `<div class="gauge"><div class="ring" style="background:conic-gradient(from -90deg,${color} 0 ${pct}deg,#182238 ${pct}deg 360deg)">
    <span class="val" style="color:${color}">${val}</span></div>
    <div class="cap">${cap}<br><span style="color:${COL.mut}">${sub||''}</span></div></div>`;
}
function structVal(st){ return st.confidence.type==='pLDDT'? st.confidence.value/100 : (st.confidence.type==='resolution'? 0.85 : 0.7); }
function drugColor(l){ return l==='LOW'?COL.viral:(l==='MODERATE'?COL.topology:COL.confirmed); }
function drugPct(l){ return l==='LOW'?30:(l==='MODERATE'?55:80); }
function hex2(hex,a){ const n=parseInt(hex.slice(1),16); return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`; }

/* ---------- Mol* ---------- */
function mountStructure(st){
  const wrap=document.getElementById('molstar-wrap'); if(!wrap) return;
  const el=document.createElement('pdbe-molstar');
  el.setAttribute('custom-data-url', st.url);
  el.setAttribute('custom-data-format','cif');
  el.setAttribute('hide-controls','true');
  el.setAttribute('hide-water','true');
  el.setAttribute('bg-color-r','5'); el.setAttribute('bg-color-g','7'); el.setAttribute('bg-color-b','14');
  el.setAttribute('landscape','true');
  if(st.kind==='predicted') el.setAttribute('alphafold-view','true');
  wrap.appendChild(el);
}

/* ---------- panels ---------- */
function renderNodePanel(id){
  const n=DATA.graph.nodes.find(x=>x.id===id)||{};
  const partners=DATA.graph.edges.filter(e=>e.source===id||e.target===id);
  document.getElementById('dossier-body').innerHTML=`
    <div class="dz-head"><div class="dz-title">${id}</div>
    <div class="dz-sub">${n.type==='viral'?'SARS-CoV-2 viral bait':'human prey'} · ${n.uniprot||''} · degree ${n.degree||0}</div></div>
    <div class="dz-sec"><div class="dz-sec-h">Incident edges</div>
    <div class="kv">${partners.map(e=>`${e.source} → ${e.target} <span style="color:${COL.mut}">(${e.kind})</span>`).join('<br>')||'—'}</div></div>`;
}

function renderIdle(){
  const f=DATA.flagship, b=DATA.eval.baseline;
  document.getElementById('dossier-body').innerHTML=`
    <div class="dz-idle">
      <h2>An AP-MS hit becomes a structural, cited, testable hypothesis.</h2>
      <p>The graph proposes missing edges deterministically. Claude reads the literature and explains. A locked evaluator measures how often the hidden true edges come back.</p>
      <div class="step s1"><b>Ask the map</b> — "what interaction is Orf6 missing?"</div>
      <div class="step s2"><b>Length-3 path</b> — ${f.path.join(' → ')} (genuine L3, never the 2-edge shortcut)</div>
      <div class="step s3"><b>Structural dossier</b> — real 3D, interface residues, a mechanism where every clause opens to a paper, a proposed wet-lab test</div>
      <div class="step s4"><b>Locked evaluator</b> — held-out Gordon edges snap green; precision@${b.headline_k} = ${Math.round(b.headline_precision_at_k*100)}%, ROC-AUC ${b.roc_auc}</div>
      <div class="step s5"><b>One loop round</b> — confirm recovered edges, fold back, re-score</div>
      <p style="margin-top:20px;color:${COL.mut};font-size:11px">Start with <b style="color:${COL.predicted}">"What interaction is Orf6 missing?"</b> on the left.</p>
    </div>`;
}

boot();
