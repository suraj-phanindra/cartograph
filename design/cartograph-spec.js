/* Cartograph — in-app spec & build plan (rendered into the Spec overlay) */
window.CartographSpecHTML = `
<div style="font-family:'Hanken Grotesk',system-ui,sans-serif;color:#e8edf6;">
  <!-- header -->
  <div style="padding:26px 34px 20px;border-bottom:1px solid #16203a;background:linear-gradient(180deg,#0c1424,#0a0f1e);position:sticky;top:0;z-index:2;backdrop-filter:blur(8px);">
    <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">
      <span style="font-weight:800;font-size:23px;letter-spacing:-.01em;">Cartograph</span>
      <span style="font-size:13px;color:#8a97ad;">component system · screen map · build plan for Claude Code</span>
      <span style="margin-left:auto;font:600 10px/1 'JetBrains Mono',monospace;color:#22e0dd;border:1px solid rgba(34,224,221,.4);padding:6px 10px;border-radius:999px;letter-spacing:.06em;">SCOPED FOR 7 DAYS</span>
    </div>
    <div style="font-size:13px;color:#aab6cc;margin-top:10px;line-height:1.6;max-width:88ch;">An explorable interactome. Left two-thirds is a living network graph; right third is a dossier that fills in for whatever is selected. The graph proposes missing edges deterministically (degree-normalized L3); for any edge Claude assembles a structural, cited, testable hypothesis. Build the <b style="color:#22e0dd;">structural edge dossier</b> first — it is the hero and the whole 3-minute demo turns on it.</div>
  </div>

  <div style="padding:26px 34px 40px;display:flex;flex-direction:column;gap:30px;">

  <!-- ============ 1. DESIGN TOKENS ============ -->
  <section>
    <div style="font:700 11px/1 'JetBrains Mono',monospace;letter-spacing:.16em;color:#22e0dd;text-transform:uppercase;margin-bottom:14px;">01 · Design tokens</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
      <div style="background:#0c1322;border:1px solid #1e2a44;border-radius:11px;padding:15px 17px;">
        <div style="font-weight:700;font-size:14px;margin-bottom:11px;">Color</div>
        <div style="display:flex;flex-direction:column;gap:7px;font:500 11.5px/1.4 'JetBrains Mono',monospace;">
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#05070e;border:1px solid #1e2a44;"></span>void &nbsp;<span style="color:#7d8aa3;">#05070e</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#0a0f1e;border:1px solid #1e2a44;"></span>panel &nbsp;<span style="color:#7d8aa3;">#0a0f1e</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#ffb454;"></span>viral &nbsp;<span style="color:#7d8aa3;">#ffb454 · hexagon</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#6c9ffb;"></span>human &nbsp;<span style="color:#7d8aa3;">#6c9ffb · circle</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#22e0dd;"></span>predicted &nbsp;<span style="color:#7d8aa3;">#22e0dd · glow</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#42e08a;"></span>confirmed &nbsp;<span style="color:#7d8aa3;">#42e08a</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#ff5c6a;"></span>rejected &nbsp;<span style="color:#7d8aa3;">#ff5c6a</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#ffd166;"></span>topology / L3 &nbsp;<span style="color:#7d8aa3;">#ffd166</span></div>
          <div style="display:flex;align-items:center;gap:9px;"><span style="width:16px;height:16px;border-radius:4px;background:#b98bff;"></span>conserved &nbsp;<span style="color:#7d8aa3;">#b98bff</span></div>
        </div>
      </div>
      <div style="background:#0c1322;border:1px solid #1e2a44;border-radius:11px;padding:15px 17px;">
        <div style="font-weight:700;font-size:14px;margin-bottom:11px;">Type &amp; rules</div>
        <div style="font-size:12.5px;line-height:1.7;color:#c6d0e2;">
          <b>Hanken Grotesk</b> — prose, UI, headings.<br>
          <b style="font-family:'JetBrains Mono',monospace;">JetBrains Mono</b> — all data: residues, scores, PDB IDs, PMIDs.<br>
          <span style="color:#8a97ad;">Numbers, units and identifiers are always mono. Prose is never mono.</span>
        </div>
        <div style="height:1px;background:#16203a;margin:13px 0;"></div>
        <div style="font-size:12px;line-height:1.7;color:#aab6cc;">
          <b style="color:#e8edf6;">Confidence is three signals, never blended</b> into one number: topology (gold), structure (teal), literature (green). Each keeps its own gauge and unit color.
        </div>
      </div>
    </div>
  </section>

  <!-- ============ 2. COMPONENT SYSTEM ============ -->
  <section>
    <div style="font:700 11px/1 'JetBrains Mono',monospace;letter-spacing:.16em;color:#22e0dd;text-transform:uppercase;margin-bottom:14px;">02 · Component system</div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
      ${[
        ['&lt;Workbench&gt;','Top bar + left ControlStrip + GraphStage + DossierPanel. Owns global state (layers, confidence, mode, selection).','shell'],
        ['&lt;GraphStage&gt;','Cytoscape.js mount. Node/edge stylesheet from tokens. Emits select-node / select-edge. Hosts AskBox, EvaluatorChip, CompareLegend as absolute overlays.','graph'],
        ['&lt;EdgeDossier&gt;','THE HERO. StructurePanel + Mechanism + ConfidenceRow + Druggability + WetLabTest + Citations + IntegrityFooter. Driven by one dossier object.','hero'],
        ['&lt;StructurePanel&gt;','Mol* web component. Experimental → load PDB by id (7DHG). Predicted → predicted-model file + "PREDICTED" chip + ipTM/pLDDT + interface residues pinned.','hero'],
        ['&lt;ConfidenceRow&gt;','Three radial gauges (topology/structure/literature). Value + color + unit per gauge. Never a single blended score.','hero'],
        ['&lt;WetLabTest&gt;','Interface residues → point mutations + assay + readout. The output the scientist acts on. Titled "Proposed Wet Lab Test".','hero'],
        ['&lt;NodePanel&gt;','Node identity + degree + list of incident edges, each a row that opens its dossier.','panel'],
        ['&lt;ControlStrip&gt;','LayerToggles · ConfidenceSlider · EvaluatorControl · LoopControl · IntegrityCaption.','shell'],
        ['&lt;AskBox&gt;','NL query over the map. Streams Claude reasoning (SSE) as a toast while the graph animates.','graph'],
        ['&lt;EvaluatorChip&gt; / snap','Locked held-out precision, shown IN the map: truths snap green, misses flash red. Never a bar chart.','eval'],
        ['&lt;UploadModal&gt;','CSV / NDEx bring-your-own-map. Re-runs L3 + agents on the user’s network.','p2'],
        ['&lt;CompareMode&gt;','SARS-CoV-2 vs SARS-1 vs MERS. Conserved edges recolor violet as a reality prior.','p2']
      ].map(([n,d,tag])=>{
        const c = tag==='hero'?'#22e0dd':(tag==='eval'?'#42e08a':(tag==='p2'?'#b98bff':'#6c9ffb'));
        return `<div style="background:#0c1322;border:1px solid #1e2a44;border-left:2px solid ${c};border-radius:9px;padding:12px 14px;">
          <div style="font:700 12.5px/1 'JetBrains Mono',monospace;color:#e8edf6;margin-bottom:6px;">${n}</div>
          <div style="font-size:11.5px;line-height:1.5;color:#aab6cc;">${d}</div></div>`;
      }).join('')}
    </div>
  </section>

  <!-- ============ 3. DATA CONTRACT ============ -->
  <section>
    <div style="font:700 11px/1 'JetBrains Mono',monospace;letter-spacing:.16em;color:#22e0dd;text-transform:uppercase;margin-bottom:14px;">03 · Data contract (the dossier object)</div>
    <div style="background:#080d18;border:1px solid #1e2a44;border-radius:11px;padding:16px 18px;overflow:auto;">
      <pre style="margin:0;font:500 11.5px/1.65 'JetBrains Mono',monospace;color:#c6d0e2;white-space:pre;">{
  <span style="color:#7fb0ff;">edge</span>:      { source:"ORF6", target:"RAE1", status:"predicted|known|confirmed" },
  <span style="color:#7fb0ff;">structure</span>: { kind:"experimental|predicted",
              pdb:"7DHG"|null, url:<span style="color:#8a97ad;">// PDB / AlphaFold DB / Model Archive / Boltz-2 file</span>,
              iptm:0.72, plddt:78, interface:["E55","M58","D61"] },
  <span style="color:#7fb0ff;">confidence</span>:{ topology:0.83,          <span style="color:#ffd166;">// deterministic L3 — the graph</span>
              structure:0.72,         <span style="color:#22e0dd;">// ipTM / resolution — the model</span>
              literature:"Strong", litCount:2 },   <span style="color:#42e08a;">// the evidence</span>
  <span style="color:#7fb0ff;">druggability</span>:{ target:"RAE1", level:"LOW", pct:0.32, source:"Open Targets", url },
  <span style="color:#7fb0ff;">proposed_test</span>:{ residues:["E55A","M58R","D61A"],
                  assay:"co-immunoprecipitation", readout:"STAT1 nuclear import" },
  <span style="color:#7fb0ff;">citations</span>:[ { n:1, id:"PMID 33097660", url } ],   <span style="color:#ff5c6a;">// no citation ⇒ clause does not render</span>
  <span style="color:#7fb0ff;">provenance</span>:{ proposed_by:"deterministic L3", evidence_by:"Claude agents",
               evaluator:"locked held-out benchmark" }
}</pre>
    </div>
    <div style="font-size:11.5px;color:#7d8aa3;margin-top:9px;line-height:1.6;">This is exactly what the <b style="color:#aab6cc;">Export</b> button emits per edge (JSON), and the schema Claude Code should target for the SSE dossier stream. The prototype ships a working reference in <span style="font-family:'JetBrains Mono',monospace;color:#c6d0e2;">cartograph-data.js</span>.</div>
  </section>

  <!-- ============ 4. ARCHITECTURE ============ -->
  <section>
    <div style="font:700 11px/1 'JetBrains Mono',monospace;letter-spacing:.16em;color:#22e0dd;text-transform:uppercase;margin-bottom:14px;">04 · Architecture</div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
      ${[
        ['Graph','Cytoscape.js','Biology-friendly. Preset positions for a crafted demo; fcose for uploaded maps. Node/edge classes map 1:1 to layers. Glow via underlay-color/opacity.'],
        ['3D','Mol* web component','&lt;pdbe-molstar&gt; loads by PDB id, or any URL (AlphaFold DB, Model Archive, or a local Boltz-2 mmCIF). Highlight interface residues via the viewer selection API.'],
        ['Prediction','Deterministic L3','Degree-normalized length-3 path score over the adjacency matrix. Pure topology, reproducible, no model weights. Runs client- or server-side.'],
        ['Structure','Boltz-2 / Chai-1 / AF3','Open folding models predict the complex + binding affinity. Output mmCIF + confidence handed to Mol*. Labeled predicted, always.'],
        ['Synthesis','Claude agents (SSE)','network · structure · literature · pharmacology agents. Reasoning streamed to the UI over server-sent events. Claude explains edges — it never invents them.'],
        ['Druggability','Open Targets / ChEMBL','Open APIs. Target tractability + known modalities; interface framed as the candidate pocket.']
      ].map(([k,v,d])=>`<div style="background:#0c1322;border:1px solid #1e2a44;border-radius:9px;padding:12px 14px;">
        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:5px;"><span style="font:600 9.5px/1 'JetBrains Mono',monospace;letter-spacing:.08em;color:#7d8aa3;text-transform:uppercase;">${k}</span><span style="font-weight:700;font-size:13px;color:#e8edf6;">${v}</span></div>
        <div style="font-size:11.5px;line-height:1.5;color:#aab6cc;">${d}</div></div>`).join('')}
    </div>
  </section>

  <!-- ============ 5. BUILD PLAN ============ -->
  <section>
    <div style="font:700 11px/1 'JetBrains Mono',monospace;letter-spacing:.16em;color:#22e0dd;text-transform:uppercase;margin-bottom:14px;">05 · Build plan · 7 days</div>

    <div style="display:flex;flex-direction:column;gap:10px;">
      <div style="background:linear-gradient(180deg,rgba(34,224,221,.06),transparent);border:1px solid rgba(34,224,221,.3);border-radius:11px;padding:15px 17px;">
        <div style="display:flex;align-items:center;gap:9px;margin-bottom:10px;"><span style="font:700 10px/1 'JetBrains Mono',monospace;color:#04202a;background:#22e0dd;padding:4px 8px;border-radius:5px;">PHASE 1 · HERO</span><span style="font-size:12px;color:#8a97ad;">days 1–4 · the 3-minute demo must run end-to-end</span></div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px 20px;font-size:12.5px;line-height:1.5;color:#d3dcec;">
          <div><b style="color:#22e0dd;font-family:'JetBrains Mono',monospace;">D1</b> · Mol* embed de-risked: load 7DHG live, then a predicted mmCIF by URL with ipTM/pLDDT + interface highlight.</div>
          <div><b style="color:#22e0dd;font-family:'JetBrains Mono',monospace;">D2</b> · Cytoscape map + layers + selection. Wire the <b>EdgeDossier</b> shell to the data contract.</div>
          <div><b style="color:#22e0dd;font-family:'JetBrains Mono',monospace;">D3</b> · L3 predictor + the ask→animate→reveal→open-dossier flow. Claude SSE into Mechanism + Test.</div>
          <div><b style="color:#22e0dd;font-family:'JetBrains Mono',monospace;">D4</b> · Locked evaluator in-map (snap green / flash red + precision) and one bounded loop round. Export JSON.</div>
        </div>
      </div>

      <div style="background:#0c1322;border:1px solid #1e2a44;border-radius:11px;padding:15px 17px;">
        <div style="display:flex;align-items:center;gap:9px;margin-bottom:10px;"><span style="font:700 10px/1 'JetBrains Mono',monospace;color:#e8edf6;background:#2a2140;border:1px solid #4a3a6e;padding:4px 8px;border-radius:5px;">PHASE 2</span><span style="font-size:12px;color:#8a97ad;">days 5–7 · makes it outlast the week</span></div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px 20px;font-size:12.5px;line-height:1.5;color:#c6d0e2;">
          <div><b style="color:#b98bff;font-family:'JetBrains Mono',monospace;">·</b> Bring-your-own-map (CSV / NDEx) → predictor + agents on user data.</div>
          <div><b style="color:#b98bff;font-family:'JetBrains Mono',monospace;">·</b> Compare mode: SARS-CoV-2 / SARS-1 / MERS conservation prior.</div>
          <div><b style="color:#b98bff;font-family:'JetBrains Mono',monospace;">·</b> STRING enrichment layer + full NL query grammar.</div>
          <div><b style="color:#b98bff;font-family:'JetBrains Mono',monospace;">·</b> Multi-round loop history + per-map benchmark authoring.</div>
          <div><b style="color:#b98bff;font-family:'JetBrains Mono',monospace;">·</b> PDF export of the annotated map + per-edge report.</div>
          <div><b style="color:#b98bff;font-family:'JetBrains Mono',monospace;">·</b> ChEMBL modality detail; pocket rendering in Mol*.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ============ 6. INTEGRITY ============ -->
  <section>
    <div style="font:700 11px/1 'JetBrains Mono',monospace;letter-spacing:.16em;color:#ff5c6a;text-transform:uppercase;margin-bottom:14px;">06 · Integrity rules · non-negotiable</div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;">
      ${[
        ['The graph proposes edges deterministically','Claude never invents an edge from its weights. The provenance line is visible on every dossier: graph proposed · Claude explained.'],
        ['Every claim opens to a paper','A hypothesis clause with no citation does not render. Citations are first-class objects, not footnotes.'],
        ['Predictions are labeled predicted','Always with a confidence number (ipTM / pLDDT). A prediction is never shown as experimental fact.'],
        ['The evaluator is locked & separate','Held-out truth is hidden from the agents. Shown inside the map as green snaps / red misses — the credibility spine, not a dashboard.']
      ].map(([t,d])=>`<div style="background:#0c1322;border:1px solid rgba(255,92,106,.25);border-radius:9px;padding:12px 14px;">
        <div style="display:flex;gap:8px;align-items:flex-start;"><span style="color:#ff5c6a;font-size:13px;line-height:1.3;">✓</span><div><div style="font-weight:700;font-size:12.5px;margin-bottom:4px;">${t}</div><div style="font-size:11.5px;line-height:1.5;color:#aab6cc;">${d}</div></div></div></div>`).join('')}
    </div>
    <div style="margin-top:16px;font-size:11.5px;color:#7d8aa3;line-height:1.6;">Full spec, data contract, and phased tasks are also delivered as a standalone <b style="color:#aab6cc;font-family:'JetBrains Mono',monospace;">Cartograph — Build Plan.md</b> you can hand directly to Claude Code alongside this prototype and <span style="font-family:'JetBrains Mono',monospace;color:#c6d0e2;">cartograph-data.js</span>.</div>
  </section>

  </div>
</div>`;
