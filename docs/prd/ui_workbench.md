# PRD — UI refinement to a professional workbench

**Goal.** Cartograph reads as an instrument a structural/systems biologist uses,
not a guided demo. UI + copy only — no change to data, prediction, evaluator, or
citation logic. Stage-0 regression after every change; evaluator number unchanged.

**A. Central "Ask the map" search (primary action).** Replace the three hardcoded
query buttons with a prominent `Ask the map …` input at the top of the canvas + a
few example chips (affordances, not a script: "ORF6's unmapped targets", "Most
druggable predicted", "Run locked evaluation"). A **deterministic intent parser**
(works offline) maps free text to a graph action:
- a named viral protein (ORF6/ORF9b/N/… any of the 26 baits) → probe it (reveal its
  L3 predictions; open its dossier if one exists; ORF6 runs the length-3 flagship).
- "most druggable / druggable / repurpos*" → open the worklist filtered to leads.
- "run evaluation / evaluate / precision" → run the locked evaluator; "loop" → loop round.
- unrecognized → a plain "Query not understood — try a viral protein, 'most druggable
  predicted', or 'run evaluation'." **Never fabricate an answer.**
Live NLU is an API-mode enhancement; the deterministic parser is the shipped impl.

**B. Remove tutorial / self-describing copy.** Delete the right-panel onboarding
(heading + paragraph + numbered steps + "Start with…"), the left INTEGRITY caption
block, and any bottom-of-canvas integrity prose. Right-panel default becomes a terse
empty state: **"Select a node to see its edges, or an edge for its structural dossier."**

**C. Keep integrity as functional labels only.** PREDICTED/KNOWN + EXPERIMENTAL/
PREDICTED-structure badges, a locked-evaluator **lock** icon, the dossier provenance
footer, inline openable citations. No explanatory prose added.

**D. Bug — dossier scroll overlap.** The structure "EXPERIMENTAL · PDB …" badge must
stay clipped inside the structure viewport (positioning container = `#molstar-wrap`,
`overflow:hidden`); the sticky dossier header gets an **opaque** background + higher
`z-index` than scrolling content. Verify by scrolling a dossier top→bottom.

**E. Bug — selected node label invisible.** A selected/path-lit node (e.g. ORF6) gets
a dark background but keeps its dark label → invisible. Fix: selected/active/path-lit
labels are high-contrast (light text + dark halo). Keep the hover tooltip.

**F. One workbench frontend, both modes.** A single frontend for offline and API.
Workbench chrome: name + "interactome workbench", a strain selector ("SARS-CoV-2 ·
Gordon 2020"), top-right actions **Compare strains** / **Bring your own map** /
**Export**. Mode is detected via `/api/health` (the offline static server answers it
too, so there is no console error). Live-only controls (Bring your own map; Compare
strains is phase-two/not built) are **disabled with a quiet tooltip** offline, not a
separate page. Export = current dossier → report, else worklist → CSV.

**G. Tone.** Every string is a label, value, control, or citation. No coaching.

**Acceptance / tests.** Stage-0 passes + evaluator unchanged; the demo path works from
the search bar; scrolling a dossier shows no header/badge overlap; selected labels
readable; offline shows the same workbench with live-only controls disabled and zero
console errors; fresh red-team confirms no fabricated answers, functional integrity
labels intact, no tutorial/marketing copy, panel-lifecycle intact, both modes identical.
