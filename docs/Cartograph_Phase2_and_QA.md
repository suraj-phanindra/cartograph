# Cartograph Phase 2 + full QA: plan and Claude Code prompt

Four build days (Jul 9 to Jul 12), then video and submit Jul 13 (deadline 9 PM ET / 6 PM PDT). The core is already a green, honest, tested submission. Phase 2 makes it genuinely more useful for the host-pathogen biologist, without ever regressing the core.

## The one rule above all
The demo-critical core (query to L3 prediction to structural dossier to locked eval to loop) must stay green and honest after every change. Regression-test it after each feature. If a Phase-2 item threatens the core, revert it and keep the core. A clean core beats a feature-rich broken one, every time.

## Guardrails carried forward (do not weaken)
- Deterministic graph proposes; Claude explains and cites; the evaluator is locked and separate. Uploaded data never leaks into the frozen held-out split.
- No citation, no render. Predicted structures labeled predicted with confidence. No fabricated residues, citations, drugs, or edges.
- Honest numbers only. The headline stays the computed metrics on real held-out edges.

## Priority stack

### P0 — the four you asked for
1. UX-debt fix pass (do this FIRST, it is the clean foundation). Fix the reported clutter, overlap, and clunk: labels covering menu items (z-index and layout), cramped menus, inconsistent spacing and type. Adopt the design tokens from the brief (neo-grotesk body + mono for data, cool-clinical palette). Add real empty, loading, and error states. This makes every later feature land on a clean base.
2. FastAPI + SSE wrapper. Turn the existing engine functions (evaluate(), l3_scores(), read_edge()) into real endpoints, and stream the reasoning over SSE. Keep the static offline artifact as the guaranteed demo fallback; the API is the "it is a real system" upgrade and the backbone for upload.
3. Bring-your-own-interactome upload. Accept an edge-list CSV (bait,prey minimal) or an NDEx network id. Validate, enrich with STRING among the new prey, run L3, and let the user pick a held-out fraction to get their own eval number. Honesty rule: uploaded networks have no cached evidence packs, so the dossier degrades honestly. Show topology and, if you run live retrieval, label it; if not, show "no cached literature for this edge" rather than inventing one. This is what makes Cartograph outlast the week and work for any lab.
4. Graph layout and visual polish. Readable at the current 23 nodes and when an uploaded network is larger. Better default layout, hover and focus states, legible labels that never collide, and the cinematic dark style from the mock held consistently.

### P1 — the gaps I would close to make it genuinely more useful (cut from the bottom if time is short)
5. Ranked "what to test next" worklist. The researcher's real job is triage. Add a sortable, filterable table of the top predicted missing edges across the whole map: L3 score, conservation, structure available (yes/predicted/no), druggability, and whether a cited mechanism exists. This turns Cartograph from a one-edge explorer into a decision tool. Highest usefulness-per-hour of anything here.
6. Export. One click to take the worklist as CSV and any dossier as a self-contained report (HTML or PDF with the structure image, mechanism, citations, and proposed test). Researchers live in grants and slide decks; give them something to carry out. Cheap, high utility.
7. Deepened druggability and repurposing. This is the dataset's own thesis (Gordon: "targets for drug repurposing"). For each host target, pull real Open Targets / ChEMBL tractability and existing drugs, deep-linked, labeled. A predicted edge whose host target already has an approved drug is a repurposing lead, and that is a direct line to the Impact axis and to Gladstone judges.
8. Eval transparency. Let anyone click into the evaluator: which held-out edges were recovered vs missed, which are reachable by topology (the 14 of 57 ceiling), and for any prediction, the actual L3 paths and their contribution. Trust is a feature; make the honesty inspectable.

## Four-day sequence
- Day 1 (Jul 9): P0.1 UX-debt fix pass + P0.2 FastAPI/SSE wrapper. End with the core green on the new backend and a visibly cleaner UI.
- Day 2 (Jul 10): P0.3 upload (with honest degradation) + P0.4 graph/visual polish. Regression-test the core.
- Day 3 (Jul 11): P1.5 worklist + P1.6 export + P1.7 druggability/repurposing as far as time allows. Regression-test.
- Day 4 (Jul 12): P1.8 eval transparency if reached, then FREEZE. Full exhaustive QA pass (matrix below), accessibility pass, fix everything, re-run all tests and the eval. Record the video against the frozen build.
- Jul 13: buffer, any re-record, submit before 6 PM PDT.

## UX audit dimensions (apply to every screen)
- Layout and z-index: nothing overlaps, no label covers a control, panels do not collide at any window size.
- Information architecture: each panel has one job; hide advanced controls until needed; reduce simultaneous choices.
- Hierarchy and type: one type scale, consistent spacing, data in mono, prose in sans; the eye knows where to look first.
- States: every view has a designed empty, loading, error, and populated state.
- Feedback: hovers, focus rings, active states, and clear affordances on every clickable thing.
- Accessibility (WCAG AA): color contrast, keyboard navigation and focus order, hit-target size, and that color is never the only signal (green/red also carry a label or icon).
- Consistency: one palette, one icon set, one button system, one set of tokens.
- Performance: interactions feel instant; large uploaded graphs do not freeze the UI.

## Exhaustive functional test matrix
For every screen and control below, test: default render, primary interaction, edge cases (empty, invalid, very large), error handling, keyboard-only path, small-window layout, console is clean (0 errors), and honesty holds (labels present, no uncited claim, no fabricated data).

Screens and controls to cover:
- Map: load, pan/zoom, node click, edge click, layer toggles, confidence slider, compare mode, layout with 23 nodes and with a large uploaded network.
- Query: valid query, empty query, nonsense query, an entity not in the map; the length-3 path animation orientation and the predicted edge draw (the hero must always draw and snap green, the bug the red team caught).
- Edge dossier: experimental structure (7VPH, 7DHG), predicted structure (labeled + confidence), interface residues, mechanism with every citation opening, druggability, proposed test, Skeptic verdict; an edge with no cached evidence (graceful).
- Evaluator: run, green/red snapping, the precision and AUC readout, the transparency drill-down, reproducibility across runs.
- Loop: one round, fold-back, re-score, and the claim shown is not overstated.
- Upload: valid CSV, malformed CSV, huge CSV, NDEx id (valid and invalid), an uploaded network with unknown gene names, and the honest dossier degradation.
- Worklist and export: sort, filter, CSV export opens in a spreadsheet, report export renders standalone.
- API: each endpoint (happy path, bad input, large input), SSE stream starts and ends cleanly, and the static offline demo still works with the server off.
- Global: keyboard nav across the whole app, focus management when panels open and close, and no layout breakage from ~1280px down.

---

## Claude Code Phase-2 prompt (paste at the repo root)

Continue building Cartograph. The green, honest core is committed; do not regress it. Extend it into a more useful tool for a host-pathogen biologist, then run a full QA pass, using the same autonomous loop as before (plan, PRD, implement, test, adversarial review, iterate) with fresh red-team subagents that never grade their own work.

Read first: README.md, CLAUDE.md, docs/REPORT.md, docs/Cartograph_BUILD_SPEC.md, docs/Cartograph_7Day_Plan.md, design/CARRY_FORWARD.md, and the current app. Restate the plan back to me.

Hard rule: after every change, regression-test the demo-critical core (query to L3 to structural dossier to locked eval to loop). It must stay green and honest. If a feature threatens it, revert the feature, keep the core.

Guardrails (unchanged): deterministic graph proposes, Claude explains and cites, evaluator stays locked and separate, uploaded data never enters the frozen split. No citation, no render. Predicted structures labeled with confidence. No fabricated residues, citations, drugs, or edges. Headline number stays the computed metric on real held-out edges.

Build in this order, each as its own plan -> PRD (docs/prd/<feature>.md) -> implement -> test -> adversarial review (code red-team + science-honesty auditor) -> iterate -> regression-test the core:
1. UX-debt fix pass FIRST: fix overlap and z-index (labels covering controls), declutter menus, adopt the design tokens (neo-grotesk + mono, cool-clinical palette), and add empty/loading/error states.
2. FastAPI + SSE wrapper over evaluate(), l3_scores(), read_edge(); keep the static offline artifact as the guaranteed fallback.
3. Bring-your-own-interactome upload (edge-list CSV or NDEx id): validate, enrich with STRING, run L3, optional user-chosen held-out fraction for their own eval. Dossiers degrade honestly when no cached evidence exists.
4. Graph layout and visual polish, readable at 23 nodes and at upload scale.
5. Ranked "what to test next" worklist: sortable, filterable table of top predicted edges (L3 score, conservation, structure availability, druggability, has-cited-mechanism).
6. Export: worklist to CSV, any dossier to a self-contained report.
7. Deepened druggability and repurposing from real Open Targets / ChEMBL, deep-linked and labeled.
8. Eval transparency: recovered vs missed held-out edges, reachability, and the L3 paths behind any prediction.

Then FREEZE and run one exhaustive QA pass across every screen and control: default render, primary interaction, edge cases (empty, invalid, very large), error handling, keyboard-only navigation, small-window layout, zero console errors, and honesty (labels present, no uncited claim, no fabricated data). Fix everything found. Re-run all tests and the evaluator.

Definition of done: the core is still green and honest; the new features work and are tested; the science-honesty audit is clean; every screen passes the QA matrix with zero console errors and no overlap or clutter; the app runs offline from run.sh and with the FastAPI server. Hand back an updated docs/REPORT.md: what was added, the test summary, every adversarial finding and its resolution, the confirmation that the core did not regress, and any assumptions you made on defaults.

Cut policy if time runs short: keep P0 (items 1 to 4) and the core; drop items 8, then 7, then 6, then 5. Never cut the core, the locked evaluator, honesty, or the video-day buffer.
