# Prompt for Claude Design — Cartograph interactome workbench

Paste everything below into Claude Design.

---

You are designing **Cartograph**, an interactive interactome workbench for host-pathogen biology. Design the product and a clickable prototype of the core flow, then produce a component spec and build plan I can hand directly to Claude Code.

## The user and the job to be done
Design for a named user: a host-pathogen biologist or bioinformatician (think a Gladstone Institutes lab) who has an experimentally-derived protein interaction map (for example an AP-MS interactome such as the SARS-CoV-2 to human map) and needs to decide what to test next. Today, turning one raw interaction hit into a fundable hypothesis takes a team: a network scientist to find what is missing, a structural biologist to model the interface, a literature scholar to find the mechanism, and a pharmacologist to judge druggability. Days to weeks per interaction. Cartograph collapses that into seconds and lets the researcher explore, interrogate, and export.

## The thesis to make visible
Three things that used to be expensive, expert-only, or paywalled are now commodity, and the design should surface all three:
1. A publication-grade 3D molecular viewer in the browser (Mol*, free and embeddable).
2. Prediction of a protein-protein complex structure and its binding affinity, using open models (Boltz-2, MIT-licensed; Chai-1; AlphaFold3), work that used to require crystallography or cryo-EM (months, high cost) or FEP simulation (huge compute).
3. The multi-expert synthesis itself (network plus structure plus literature plus pharmacology), now performed by a team of Claude agents.

## Core concept
An explorable interactome. The left two-thirds is a living network graph. The right third is a dossier that fills in for whatever the researcher selects. Cartograph proposes the edges that should exist but are not yet on the map (deterministic topology, degree-normalized L3), and for any edge, known or predicted, it assembles a structural, cited, testable hypothesis.

## The hero feature: the structural edge dossier (design this first and in the most detail)
When a researcher clicks any edge, or a freshly predicted one, open a dossier containing:
- A 3D structure panel embedding Mol*. If an experimental structure exists, load it from the PDB (for example ORF9b-TOM70 is PDB 7DHG; a SARS Orf6 bound to the Rae1-Nup98 complex is PDB 7VPG, the SARS-CoV-1 homolog, so confirm the SARS-CoV-2 entry). If no structure exists, show a predicted complex from an open folding model, clearly labeled "predicted" with a confidence readout (pLDDT / ipTM), and highlight the predicted interface residues.
- The mechanism, written by Claude, two to three sentences, every clause backed by an openable citation (PubMed / PMC).
- A confidence row that keeps three signals separate and honest: the deterministic topology score, the structure-model confidence, and the strength of literature support.
- A druggability read: is the host protein targetable, and by what (pull from open sources such as Open Targets or ChEMBL), with the interface framed as the potential pocket.
- A proposed wet-lab test: the specific interface residues to mutate and the assay (for example co-immunoprecipitation) to confirm or refute the predicted edge. This is the output the researcher actually acts on.

## Interactions (make it a tool, not a scripted animation)
- Ask anything: a natural-language query box over the map ("what is ORF6 hitting that we have not mapped", "show me the most druggable predicted host factors").
- Confidence slider: raise or lower the prediction threshold and watch predicted edges appear or thin out.
- Layer toggles: known edges, STRING enrichment, predicted, held-out (evaluation), confirmed, and conserved-across-coronaviruses.
- Selection: click a node to see all its edges and their dossiers; click an edge for the structural dossier.
- Run a round: expose the self-improving loop as a control the researcher triggers, not a canned beat. Confirmed hypotheses fold back into the map as annotations, the map densifies, and the evaluator score updates. Keep it bounded and honest.
- Bring your own map: upload or paste an interactome (NDEx or CSV) so the tool works on the researcher's own data, not just the demo. This is what makes it outlast the week and be usable without the builder in the room.
- Compare: SARS-CoV-2 versus SARS-CoV-1 versus MERS, to see which interactions are conserved, since conservation is a strong prior for which predicted edges are real.
- Export: a per-edge report (PDF or JSON) and the annotated map, so the researcher leaves with an artifact.

## The evaluator, shown honestly (not a dashboard)
Keep a locked held-out benchmark, but present it inside the map: hidden true edges snap green as they are predicted, misses flash red, and a precision readout updates. It is the credibility spine. Do not turn it into a bar chart.

## States to design
Empty and upload, exploring the map, node selected, edge dossier open, predicting a brand-new edge (with the length-3 path animating and the structure resolving), evaluation mode, a loop round running, compare mode, and export.

## Visual language
Dark, cinematic, precise, scientific. Viral and human proteins visually distinct. Glowing predicted edges, green for confirmed-against-truth, red for rejected. The 3D structure panel should feel premium. Aim for mission-control for molecular biology, not a SaaS dashboard. I have an existing dark force-directed mock in this style; match and elevate it.

## Integrity rules (non-negotiable, these earn scientist trust)
- The graph proposes edges deterministically. Claude never invents an edge from its weights. Make that boundary visible in the UI.
- Every claim opens to a paper. A hypothesis with no citation does not render.
- Predicted structures are always labeled predicted, with a confidence number. Never present a prediction as experimental fact.
- The evaluator is locked and separate from the agents. Show it as such.

## Technical constraints (so the design hands off cleanly to Claude Code)
- A web app. Network graph via Cytoscape.js (friendly to biology networks). 3D via the Mol* web component, loading structures from PDB, AlphaFold DB, or Model Archive by URL, or from a predicted-structure file. Stream Claude's reasoning to the UI via server-sent events. Druggability from open APIs. Keep it one screen with panels, openable in a browser.

## Prioritization
Design the whole workbench, but make the structural edge dossier the hero and build it out first. Keep one legible flow that also works as a 3-minute demo: ask a question, watch the length-3 prediction, open the dossier with the 3D interface and citations, run the locked evaluation so edges snap green, trigger one loop round. Mark everything else as phase two so the build can scope against seven days.

## Deliverables from you (Claude Design)
A component system, the key screens above, a clickable prototype of the hero flow, and a spec plus plan I can hand directly to Claude Code.
