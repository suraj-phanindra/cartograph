# Cartograph: the 7-day build plan (elevated scope)

Supersedes Section 10 of the Day-1 strategy doc. This is the authoritative plan for the structural interactome workbench. Solo. Tue Jul 7 to Mon Jul 13 (submissions due Jul 13, 9:00 PM ET).

The governing rule: build the demo-critical core first, prove it end to end by the Day-4 gate, then add phase-two only from a solid base. Ambition is fine because the core is small and the phase-two ladder is optional. You never bet the submission on a stretch.

---

## The demo-critical core (must ship — this alone is a winning submission)
If only these work, you have a complete, honest, winning 3-minute demo:
1. The SARS-CoV-2 to human interactome renders as an interactive graph (real data).
2. A plain-English query triggers a deterministic L3 prediction of a missing edge, with the length-3 path shown.
3. Clicking that edge opens the structural dossier: a real 3D structure in Mol* (experimental PDB), the interface, a Claude-written mechanism where every clause opens to a paper, and a proposed wet-lab test.
4. The locked evaluator runs in-map: held-out true edges snap green, misses flash red, a precision number shows.
5. One self-improving loop round: a confirmed edge folds back, the map densifies, the score updates.

That is the whole product. Everything below is upside.

## The phase-two ladder (add only from a solid core, in this order)
1. Druggability read on the host protein (Open Targets / ChEMBL). Cheap, high value, promote early if time.
2. Live interface prediction for a NOVEL edge with no experimental structure (Boltz-2 / Chai-1 / AlphaFold3), labeled predicted with a confidence number. The jaw-drop. See the pre-compute trick under Risks.
3. Bring-your-own-interactome: upload NDEx / CSV. Biggest "outlasts the week" story, but the riskiest surface. Only if the core is rock solid.
4. Compare across coronaviruses (SARS-CoV-2 / SARS-CoV-1 / MERS) using conservation.
5. Export a per-edge report (PDF / JSON) and the annotated map.

---

## Parallel tracks
Three tools run at once so Code is never blocked. Front-load Science and Design.
- Claude Science: produces `/evidence` files (ground-truth edges, per-edge packs, CRISPR set, domain rules). Days 1 to 4.
- Claude Design: produces the component system and hero-dossier prototype, then hands to Code. Days 1 to 2.
- Claude Code: builds backend then frontend. Days 2 to 6.
- Cowork (me): plan, review, demo script, verification. Ongoing.

---

## Day by day

### Day 1 — Tue Jul 7 — Foundations and eval-first
Focus: skeleton that can grow, and the honest number's harness before anything else.
- Attend the 12:00 PM ET kickoff.
- Scaffold the repo. Add an open-source license (MIT). Create `/evidence`.
- FIRST COMMIT: freeze the held-out split (fixed seed, 15 to 20 percent of high-confidence edges) and write the locked evaluator harness. Before any prediction code.
- Load the SARS-CoV-2 map from NDEx into networkx. Confirm it loads clean.
- Start Science: Lookup 1 (Gordon ground-truth edges) and Lookup 4 (flagship worked example evidence).
- Start Claude Design with the brief. Get first screens.
- Done when: repo + license + committed locked evaluator + map loads + Design returning screens.

### Day 2 — Wed Jul 8 — Deterministic engine and the honest floor
Focus: the reproducible critical path and a real baseline number.
- Attend the 12:00 PM ET Claude Science session (Tarashansky).
- Enrich with STRING human-human PPIs among the prey (pin the STRING release).
- Implement degree-normalized L3 candidate generation.
- Produce a baseline evaluator number from structure alone, no LLM. That is your honest floor.
- Science: Lookup 3 (edge evidence packs for ORF6-RAE1/NUP98 and ORF9b-TOM70) into `/evidence`.
- Design: finalize the hero dossier layout, hand off to Code.
- Done when: L3 returns ranked candidates; evaluator prints a real precision number; demo-edge evidence cached.

### Day 3 — Thu Jul 9 — The hero begins (reasoning + structure)
Focus: the structural dossier skeleton, the part that makes this a tool.
- Build the reasoning layer: Reader, Skeptic, Curator subagents produce a cited hypothesis for a candidate, reading only from `/evidence`.
- Frontend: Cytoscape.js renders the real map; clicking an edge opens the dossier panel.
- Embed the Mol* web component in the dossier. Load a real structure by PDB URL: ORF9b-TOM70 is 7DHG. Confirm it renders in the browser.
- Done when: clicking the ORF9b-TOM70 edge opens a dossier showing the real 3D structure plus a cited mechanism.

### Day 4 — Fri Jul 10 — Close the core loop. DECISION GATE.
Focus: the flagship path, end to end, live.
- Attend the 12:00 PM ET Gladstone session (Silas, virtual PPI screening). On-topic, worth the hour.
- Wire the full flagship path: query, L3 traversal to RAE1, dossier with the Orf6 on Rae1-Nup98 structure (7VPG, confirm the SARS-CoV-2 entry), interface residues, cited mechanism, proposed test.
- Show the eval in-map: held-out edges snap green or red, precision readout updates.
- One loop round: confirm an edge, fold it back, re-run the evaluator.
- GATE: if the 3-minute core path does not run end to end tonight, freeze scope, cut the entire phase-two ladder, and spend Day 5 stabilizing. No exceptions.
- Done when: the full core demo path runs live on the flagship edge.

### Day 5 — Sat Jul 11 — Bulletproof the core, then one stretch
Focus: make the demo path unbreakable before adding anything.
- Cache all demo literature and structures locally. Handle every failure on the path gracefully. Pre-load the demo state so nothing waits on a network call.
- Rehearse the 3-minute path against a clock.
- Only if the core is solid: add the top phase-two item. Druggability (cheap) or the live/pre-computed novel-edge prediction (the jaw-drop). One, not both.
- Done when: the core is demo-stable and rehearsed, with at most one stretch integrated.

### Day 6 — Sun Jul 12 — Polish, maybe a second stretch, start the video
Focus: make it look like the cinematic mock, and de-risk the video.
- Visual polish, copy, legends, and the honesty labels (predicted vs experimental, confidence numbers, deterministic vs LLM boundary).
- At most one more phase-two item, only if everything is solid: pick the cheapest-highest-value of upload, compare, or export.
- Start recording demo takes. Draft the 100 to 200 word summary. Clean the repo and write the README.
- Done when: the build is frozen and submission-ready, and a first full video take exists.

### Day 7 — Mon Jul 13 (due 9:00 PM ET) — Video and submit. No new features.
Focus: ship.
- Record the final 3-minute video: metaphor, query, L3 prediction, structural dossier with 3D and citations, eval edges snapping green, one loop round, close.
- Finalize the public repo (open-source license, README, `/evidence`, a reproducible evaluator), and the 100 to 200 word summary.
- Submit on the CV platform with a comfortable buffer before 9:00 PM ET.
- Done when: submitted.

---

## Cut lines (drop in this order when behind)
Compare mode, then export, then upload-your-own-map, then druggability, then live folding prediction. Never cut: the locked evaluator, the cited mechanism, the real-structure dossier, or the Day-7 video time.

## Risks and fallbacks
- Mol* wiring eats Day 3: it is well documented and loads by URL, but if it slips, fall back to a pre-rendered structure image with the interface highlighted. Still shows structure. Do not let it block the graph.
- Live folding (Boltz-2 / Chai-1 / AF3) is too heavy for the timeline or compute: pre-compute one predicted complex for a single novel edge before the demo, save the structure file, and load it into Mol* labeled predicted with its confidence. You get the jaw-drop with zero fragile live GPU calls, and it is honest because Cartograph genuinely produced it.
- Literature or structure gaps: avoided by choosing flagship edges that already have real structures and deep literature (ORF9b-TOM70 7DHG, Orf6-Rae1-Nup98 7VPG).
- Time slips: the Day-4 gate plus the cut lines are the release valve. Protect the core.
- Objective-hacking suspicion from judges: the evaluator is locked, separate, and committed before predictions. Say so on screen.

## Submission checklist (Day 7)
- 3-minute demo video (YouTube or Loom).
- Public GitHub repo, open-source license, README, `/evidence`, reproducible evaluator.
- 100 to 200 word written summary naming the user, the problem, and what Claude did.
- Submitted on the CV platform before 9:00 PM ET.

## Definition of the win
A researcher watches an AP-MS hit become a structural, cited, testable hypothesis in seconds, and watches the map prove itself against hidden truth under a locked ruler. That is useful, legible, honest, and on-theme. The core delivers it. The phase-two ladder only makes it louder.
