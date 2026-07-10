# Cartograph: UI refinement to a professional workbench

Direction: make Cartograph look and feel like an instrument a scientist uses daily, not a guided demo. Strip the tutorial and self-describing copy. Let integrity show through behavior and functional labels, not through paragraphs that explain the product. Restore the central "Ask the map" search as the primary action.

## A. Restore the central "Ask the map" search (primary interaction)
- Replace the three hardcoded buttons in the top-left "ASK THE MAP" panel (screenshot 1: "What interaction is Orf6 missing?", "Show the Orf9b-TOM70 dossier", "Show the N-G3BP1 dossier") with the central search bar from the workbench design (screenshot 2): a single prominent "Ask the map ..." input at the top of the canvas.
- Keep a few suggestion chips under the bar as examples, not as the only path (screenshot 2 has "ORF6's unmapped targets", "Most druggable predicted", "Run locked evaluation"). Chips are affordances, not a script.
- The bar accepts free text and maps it to a graph action via a deterministic intent parser (which viral protein to probe, "most druggable", "run evaluation"), so it works offline. In API mode it can use live NLU. Never fabricate; if a query is not understood, say so plainly.
- Placeholder should be terse, e.g. "Ask the map ..." not a full sentence tutorial.

## B. Remove the demo scaffolding and self-describing copy
Remove these entirely:
- The right-panel onboarding block (screenshot 1): the heading "An AP-MS hit becomes a structural, cited, testable hypothesis", the paragraph under it, the numbered steps 1 to 5, and "Start with 'What interaction is Orf6 missing?' on the left." This is a tutorial; a workbench does not ship one on the main canvas.
- The left "INTEGRITY" caption block (screenshot 1: "The graph proposes edges via degree-normalized L3. Claude never invents an edge ...", "Every mechanistic clause opens to a real PubMed paper", etc.).
- The bottom-of-canvas integrity captions from the design (screenshot 2): "Edges are proposed by deterministic L3 topology ... it only shows what the graph proposes" and "Every hypothesis Cartograph renders is backed by an openable paper. A claim with no citation does not render."
- Any instructional placeholder or helper text that explains what the product is or what order to do things in.

Replace the right panel's default (when nothing is selected) with a clean, terse empty state like the workbench (screenshot 2): "Select a node to see its edges, or an edge for its structural dossier." Nothing more.

## C. Keep integrity as functional labels only (do NOT remove these)
These are how a real tool signals state; they are not marketing:
- The dossier badges: "PREDICTED EDGE" / "KNOWN EDGE", and on the structure "EXPERIMENTAL · PDB 7VPH" or "PREDICTED · AlphaFold ... (pLDDT ...)".
- The locked-evaluator lock icon and label.
- The dossier provenance footer line ("proposed by deterministic L3 · explained by Claude ... · scored by locked held-out benchmark").
- Citations rendered inline and openable; predicted structures always labeled with confidence.
The integrity story now lives in the product's behavior and in the demo narration, not in on-screen prose.

## D. Bug 1 — dossier header vs structure badge overlap on scroll (screenshot 3)
When the dossier is scrolled, the "EXPERIMENTAL · PDB 7VPH" badge (absolutely positioned over the Mol* viewport) scrolls up and overlaps the sticky dossier header ("Orf6 -> RAE1 / deterministic ... L3 ..."), making both unreadable. Fix: the structure badge must be clipped inside the structure panel (its positioning container should be the viewport with overflow hidden), and the sticky dossier header must have an opaque background and a higher z-index than the scrolling content so nothing bleeds over or under it. Verify by scrolling the dossier slowly from top to bottom: the header stays clean, the badge stays inside the structure panel.

## E. Bug 2 — selected node label is black and invisible (screenshot 4)
When a node is clicked/selected (e.g. ORF6), its label renders in near-black on the dark hexagon and disappears. Fix the selected and active node label style to stay high-contrast (light text with a dark halo, or a contrasting label chip), matching the unselected state. This is on the hero node, so it must be correct. Keep the hover tooltip that already works ("Orf6 · viral bait · P0DTC6 · deg 3 · click for dossier").

## F. Unify to one workbench frontend
The offline page (screenshot 1) and the workbench design (screenshot 2) have diverged, which is why the search bar disappeared and the tutorial copy crept in. Consolidate onto one frontend that both serving modes use. Live-only features (Bring your own map / upload, live NLU, live druggability) are present but disabled with a quiet tooltip when running offline, not a separate simpler page. Adopt the workbench chrome from screenshot 2: the product name plus "interactome workbench", the strain selector ("SARS-CoV-2 · Gordon 2020"), and the top-right actions (Compare strains, Bring your own map, Export). Keep it calm and dense, like an instrument.

## G. Tone
Labels terse and technical. No exclamation, no "let's", no coaching. Assume the user is a domain expert. Every word on screen should be a label, a value, a control, or a citation. If a sentence explains the product rather than the data, cut it.

---

## Claude Code prompt (paste at the repo root)

Refine Cartograph's UI into a professional scientific workbench. It should read as an instrument a structural or systems biologist uses, not a guided demo. Same autonomous loop: plan, PRD, implement, test, fresh red-team review, iterate. Do not regress the demo-critical core or change any data, prediction, evaluator, or citation logic; this is a UI and copy pass. Run the Stage 0 regression after every change.

Read first: CLAUDE.md, docs/REPORT.md, the current frontend(s), and docs/Cartograph_UI_refinement_spec.md (this spec, with annotated screenshots described).

Changes:
1. Restore the central "Ask the map" search as the primary action, replacing the three hardcoded query buttons. Free-text input plus a few example suggestion chips (not a fixed script). Back it with a deterministic intent parser so it works offline (map text to: probe a named viral protein, most-druggable predicted, run evaluation); live NLU in API mode. Terse placeholder "Ask the map ...". If a query is not understood, say so; never fabricate.
2. Remove all tutorial and self-describing copy: the right-panel onboarding heading + paragraph + numbered steps + "Start with ..." line; the left INTEGRITY caption block; and the bottom-of-canvas integrity captions. Replace the right panel default with a terse empty state: "Select a node to see its edges, or an edge for its structural dossier."
3. Keep integrity as functional labels only: the PREDICTED/KNOWN and EXPERIMENTAL/PREDICTED-structure badges, the locked-evaluator lock, the dossier provenance footer, and inline openable citations. Do not add any explanatory prose.
4. Fix the dossier scroll bug: the structure "EXPERIMENTAL · PDB ..." badge must stay clipped inside the structure viewport, and the sticky dossier header must have an opaque background and higher z-index so nothing overlaps it while scrolling. Verify by scrolling a dossier top to bottom.
5. Fix the selected-node label: it renders near-black and invisible when a node is clicked (e.g. ORF6). Make selected/active node labels high-contrast (light text with a dark halo). Keep the working hover tooltip.
6. Unify onto one workbench frontend for both serving modes (offline and API); live-only features are disabled with a quiet tooltip offline, not a separate simpler page. Adopt the workbench chrome (name + "interactome workbench", strain selector, top-right Compare strains / Bring your own map / Export).
7. Tone pass: every on-screen string is a label, value, control, or citation. Cut anything that explains the product rather than the data.

Test: the Stage 0 core regression still passes and the evaluator number is unchanged; the demo path still works from the search bar; scroll a dossier and confirm no header/badge overlap; select nodes and confirm labels are readable; offline mode shows the same workbench with live-only controls disabled and no console errors.

Adversarial review (fresh subagent): confirm no fabricated query answers; the functional integrity labels (badges, provenance, lock, citations) are all still present and correct; predicted structures still labeled; no tutorial/marketing copy remains; the panel-lifecycle and overlap rules from the prior pass still hold; and the two serving modes render the identical unified frontend.

Done: the app reads as a professional workbench, the central Ask-the-map search is back, all demo/tutorial and integrity-marketing copy is gone while functional labels remain, the three bugs are fixed, both modes use one frontend, tests pass, the core did not regress, and docs/REPORT.md is updated.
