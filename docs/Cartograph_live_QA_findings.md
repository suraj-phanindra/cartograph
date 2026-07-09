# Cartograph: live QA findings (independent pass via Chrome)

I drove the running app at 127.0.0.1:8791 end to end: initial map, the Orf6 hero flow, the Orf6-RAE1 dossier, the locked evaluator, one loop round, the N-G3BP1 and Orf9b-TOM70 dossiers, and a layer toggle. Zero console errors across the entire session. This is a strong, honest build. Below: what passed, then a prioritized fix list.

## Passed (verified live)
- Loads clean, no console errors on load or during any interaction.
- Hero flow: "What interaction is Orf6 missing?" animates the genuine length-3 path Orf6 -> NUP98 -> NUP214 -> RAE1 and proposes Orf6 -> RAE1 (toast: "L3 rank 7/8"). The bug the red team caught (hero edge dropped by a cap) is gone; the edge draws.
- Orf6-RAE1 dossier: real experimental structure 7VPH in Mol* (ORF6 C-terminal tail + RAE1 + NUP98), interface residues E55/Q56/M58/E59/D61 computed from <=3.0A contacts, mechanism with inline citations 1/2/3 and the honest line that topology proposed the edge and the structure confirms the contact, three unblended confidence gauges (topology 0.64 / structure 2.8A / literature strong), Skeptic PASS, druggability labeled "curated prior, not computed/cited," three real PMIDs (33097660, 35970938, 33849972), and a full provenance line.
- Locked evaluator: honest panel. precision@10/20/50 = 30/45/26, ROC-AUC 0.8451, AP 0.3733, recall@50 93%, "on 57 real held-out Gordon edges (14 reachable by L3)," "without pinned edge: @20 45% (pinning does not inflate it)," "frozen seed 42, committed before prediction." Held-out edges snap green, misses red on the map.
- Loop round: honest. "30% -> 35% on remaining held-out; confirmed 4 edges, folded back as known; reachable set unchanged (10 -> 10); the gain is honest re-ranking on the same remaining hidden edges."
- N-G3BP1 dossier: the placeholder citation is fixed. Real citations now (PMID 40936503 Virus Evol 2025; 33495715 Sci Bull 2021; 35652658 J Virol 2022). Structure honestly labeled "AlphaFold DB (AF-Q13283, G3BP1)."
- Orf9b-TOM70 dossier: known edge, structure 7DHG, four real citations (33990585, 35643212, 32728199, 34502139), druggability MODERATE.
- Carry-forward fixes confirmed live: real held-out edges, citation placeholder replaced, predicted structures labeled with source.

## Fix list (prioritized)

### P0 — demo-breaker (reproduced in the expanded structure viewer; fix first)
I missed this on the first pass because I did not open the expanded (fullscreen) structure viewer. Reproduced now, end to end:
1. Open a dossier (e.g. Orf6-RAE1), then click the Mol* "Toggle Expanded Viewport" control. The 3D structure expands to fill most of the screen.
2. In this expanded state the app's own overlay panels render on top of the viewer at their fixed positions:
   - The "PREDICTED EDGE" dossier header panel (top-right) sits directly over the Mol* control column. The reset/refresh icon is above the panel, but the collapse / exit-expanded-viewport button and the toggle-controls button are behind the panel. Only a bottom control peeks out.
   - The loop-round / evaluator info panel (top-center) overlays and covers part of the protein structure.
3. Exit is broken. Clicking where the collapse control sits does nothing (the dossier panel is on top and intercepts it), and pressing Escape does not exit either. The only way out is a full page reload. A user, and a judge watching the demo, gets trapped in the expanded viewer.

Fix: when the viewer is expanded, either (a) hide or reflow the app overlay panels (dossier header, loop/eval panels) so they never cover the viewer or its controls, or (b) render a large, always-on-top Close / Exit-fullscreen button that is not under any panel, and wire Escape to collapse. Verify the collapse control is reachable by an actual mouse click, not just present in the DOM. Re-test with a dossier open AND after running the evaluator and a loop round (both panels present), since that is when the occlusion is worst (see the user's screenshots).

Broader lesson for the QA pass: every overlay panel must be tested against the expanded/fullscreen viewer state and must never occlude a control. Add "expanded viewer + each panel visible" as an explicit case in the test matrix.

### P1 — worth fixing, and one is on the hero path
1. Dense-cluster node and label overlap. The nuclear-pore cluster (NUP98, NUP88, NUP54, NUP58, NUP62, NUP214) has overlapping nodes and colliding labels; it reads as clutter. This is exactly where the hero edge terminates (RAE1 sits in this cluster), so it is on camera during the money moment. Fix: increase node repulsion / spacing in that region, add label collision avoidance (halos or offset, hide-on-overlap with zoom-to-reveal), or nudge preset positions so no two labels touch. Make the hero neighborhood legible at the default zoom.
2. Loop fold-back is invisible in the counts. After the loop confirms 4 edges "folded back as known," the "Confirmed (loop)" layer still reads 0 and "Known (AP-MS)" still reads 35. The self-improvement beat has no visible trace in the legend or counts. Fix: increment the counter (Confirmed 0 -> 4, or Known 35 -> 39) and recolor the 4 confirmed edges so the map visibly densifies. Right now the loop's effect only shows in the transient panel.

### P2 — minor polish
3. Info panels persist and can overlap. The evaluator and loop panels sit over the top-center of the graph and stay; the loop toast (top-left) was partially occluded by the eval panel. Add a dismiss or auto-fade, and make sure panels and toasts never stack over each other.
4. Layer toggle confirmation. Toggling "Predicted (L3)" changed the control state, but predicted edges were hard to confirm as hidden because the eval green held-out edges occupy the same region. Verify the toggle truly hides the predicted layer, and consider a toggle (or clear visual separation) for the held-out eval overlay too.
5. Bait label legibility. Single-letter viral labels (for example "N") are a dark glyph on the amber hexagon and are hard to read. Give baits a readable label treatment, especially single letters (N, E, M).
6. Mol* viewport has a small control/box artifact in the top-left corner. Confirm it is an intended control, not a stray element.

### Not bugs (checked and cleared)
- Labels I first read as garbled ("E1P4M", "8TF7F7") are screenshot-resolution artifacts; the real labels (EIF4H, GTF2F2) render correctly.

## Exhaustive pass — coverage matrix (every button, toggle, screen)
Driven live via Chrome. Zero console errors across the entire sweep (~18 interaction batches, checked after each).

Query buttons: Orf6 (animates the length-3 path + toast + opens dossier) PASS. Orf9b-TOM70 (opens known-edge dossier, real 7DHG) PASS. N-G3BP1 (opens predicted-edge dossier) PASS.
Layer toggles: Known (hides/shows AP-MS edges) PASS. STRING (hides/shows enrichment) PASS. Predicted L3 (hides/shows predicted) PASS. Confirmed (loop) — same mechanism, but nothing to show because of P1.2.
Evaluator: honest panel with all metrics + disclosures, green/red snap on map PASS. Loop: honest 30 to 35, and it is one-shot (the button disables after one round, so no runaway or >100%) PASS.
Dossiers: Orf6-RAE1 (experimental 7VPH, interface E55/Q56/M58/E59/D61, mechanism with inline citations, three unblended gauges, Skeptic PASS, druggability labeled "curated prior", real PMIDs, provenance) PASS. Orf9b-TOM70 (experimental 7DHG, interface I44/S53/R58/E65, four real citations) PASS. N-G3BP1 (predicted AlphaFold monomer, pLDDT 66.8, explicitly declines to show contact residues since the complex is not deposited) PASS and exemplary on honesty.
Graph: node click on a prey (MTCH1) opens a node panel (UniProt, degree, incident edges) PASS. Node click on a bait (ORF6) opens the dossier PASS. Mouse-wheel zoom PASS.
Links: "7DHG on RCSB" href verified real. Keyboard: Tab focuses the five DOM buttons with a visible focus ring.

## Additional findings from the exhaustive pass

### P2 (continued)
7. Panels never dismiss. The node panel, the evaluator panel, and the loop panel all persist. Clicking empty background does not deselect, and there are no close buttons; a stale panel (e.g. the MTCH1 node panel) stays on screen through running the evaluator and the loop. Add a close affordance and click-background-to-dismiss, and clear the right panel when context changes.
8. Raw Mol* controls are exposed. The "Toggle Controls Panel" button opens the full Mol* "Structure Tools" developer panel (Quick Styles, Model type, "Nothing Focused") crammed inside the small viewer, covering the structure. Animation, Screenshot, Settings, and Selection Mode are power-user controls that do not belong in the embedded biologist view. Trim to a minimal custom set (spin, reset, expand, and a safe screenshot) and hide the rest via the pdbe-molstar hideControls options.
9. Accessibility gaps. Only the five DOM buttons are keyboard-focusable; the layer toggles and the graph canvas are not reachable or operable by keyboard. Nodes do not show a pointer cursor or a hover tooltip, so their clickability is not discoverable. Add keyboard operability for the toggles, a focus path for graph selection or an equivalent, and a hover state / pointer cursor on nodes.
10. Responsive not verified. The layout is a fixed three-column desktop layout; at a narrow width the capture did not confirm a clean reflow. Verify below ~1100px that the three columns stack or hide gracefully with no overlap.

### Scope note (not a bug)
The Claude Design prototype's in-app Spec (Cmd) screen was not carried into the build; there is no spec/command screen in the running app. Fine, it was never demo-critical, but noting the delta.

## Framing notes for the video (not bugs)
- The hero edge is L3 rank 7 of 8. Own it: "even a mid-ranked topological candidate is mechanistically real and structurally confirmed by 7VPH." Or, if you want a punchier rank on camera, feature a higher-ranked recovered edge as the opener and keep Orf6-RAE1 as the deep example. The Orf6-RAE1 biology plus the real structure is worth keeping.
- The eval panel shows precision@50 = 26% alongside the stronger numbers. On camera, say ROC-AUC 0.8451 and recall@50 93% first. Keeping the full curve visible on screen is good for trust; just do not narrate the 26% as the headline.

## Bottom line
The underlying engine and honesty are strong and verified. But the UI is not demo-clean yet: the expanded-viewer trap (P0) can strand a viewer, and the hero-cluster overlap (P1.1) lands on camera. Fix order: P0 (expanded-viewer occlusion + exit), then P1.1 (hero-cluster legibility), then P1.2 (make the loop fold-back visible), then the P2 polish. These are UI/interaction defects on top of a sound core, not science problems.
