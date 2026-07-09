# Cartograph: Day 1 Strategy and Demo-Path Lock

Built with Claude: Life Sciences (Anthropic x Gladstone). Build track, solo. Jul 7 to Jul 13, 2026.
Role of this doc: the decision record that ends Day 1. It locks the idea, resolves the technical forks, and freezes the 3-minute demo path. Everything here is grounded in verified sources (see end).

---

## 1. Verdict after research

The core idea in your seed context survives contact with the facts, and two research findings make it stronger and safer to ship.

1. The data checks out. Gordon et al. 2020 expressed 26 of 29 SARS-CoV-2 proteins in human cells, mapped 332 high-confidence virus-human interactions by AP-MS, and flagged 66 druggable human proteins hit by 69 drugs. It is on NDEx in machine-readable CX format. You are not parsing a PDF to start.
2. The sparse-bipartite crux is solved. Your seed doc flagged that pure topological link prediction is weak on a sparse bipartite graph. The literature answer is L3: link prediction over paths of length three beats common-neighbor methods on protein interaction networks, and a degree-normalized L3 works on bipartite graphs specifically. This is your deterministic candidate generator. The worry is retired.
3. There is one close piece of direct prior art, and it leaves your wedge open. GraPPI (arXiv Jan 2025) is a GraphRAG pipeline that explores and explains known PPI pathways at scale for drug target ID. It validates the demand (drug-discovery researchers said they want cited PPI reasoning) but it does not predict missing edges, it has no locked held-out evaluator, it has no self-improving loop, and it runs over canonical knowledge graphs, not a specific experimental map. Adjacent hypothesis-generation agents exist too (for example BioDisco, StatefulDiscovery), but none pair held-out edge prediction with cited mechanism on a context-specific experimental map. Your build is prediction-first, measured, auditable, and context-specific. Different product. If a judge names one of these, concede it and reframe to the measured held-out wedge.

Bottom line: proceed with Cartograph. Do not change the thesis. Sharpen the wedge, add the visible loop, and lead with the number.

---

## 2. The lock (put this everywhere: README, demo, submission)

Name: Cartograph (keep it; it encodes the product in one word, mapmaking over a map you navigate blind).

One-sentence metaphor: Cartograph is the navigation layer for a protein interaction map. It reads the map, predicts the roads that should be there but are not yet drawn, and shows you the paper behind every turn.

One-paragraph pitch: An interactome is a map, and researchers navigate it blind. Every edge is an assertion with a paper behind it, but the graph strips that context away, and the edges that matter most are the ones not yet on the map. Cartograph loads an experimentally-derived interaction map, proposes the missing edges deterministically from graph structure, and has Claude read the literature behind the neighboring edges to produce a mechanistic, cited hypothesis you can audit line by line. Underneath runs a locked evaluator: hide a fifth of the known edges, predict them from the rest, report the hit rate. Not a hypothesis generator that sounds confident. A method with a measured number.

The thesis that must survive: AI capability is not the bottleneck, context is. An interactome is that thesis in pure form. The graph is easy to compute and hard to read, because the context connecting each edge to a mechanism has been stripped out. That gap is the product.

---

## 3. Differentiation (you will be asked; concede, then reframe)

Against STRING and BioGRID: they serve the canonical, aggregated interactome and are built for retrieval. A Krogan map is specific, experimentally-derived, and context-specific, and its value is in the edges not in the canonical set. Exactly there, reference databases are silent or low-confidence by construction. STRING's text channel is statistical co-occurrence, which gives association, not mechanism. Cartograph targets a mechanistic hypothesis for a specific edge, with a literature chain you can open.

Against GraPPI (the one close prior art): GraPPI explores and explains edges that already exist, over a large canonical KG. Cartograph predicts edges that do not exist yet, on a specific experimental map, and proves its hit rate against a locked held-out set. Explanation versus prediction plus measurement. Concede that GraPPI proved researchers want cited PPI reasoning, then say Cartograph answers the harder question: not what does this known edge mean, but what edge is missing, and how often are you right.

The benchmark bar (state it before a judge sets it for you): the bar is not beating STRING at re-deriving interactions it already scores. That is their home turf. The bar is narrower and more useful: on held-out or uncharacterized edges, produce a mechanistic cited hypothesis and be right at a measurable rate against ground truth.

### Independent corroboration (Claude Science literature map, Jul 7)
A 40-paper OpenAlex sweep of the subfield confirms the wedge from the outside. The heavily-cited mass of this field is 2020 to 2022 (the AP-MS interactome, the CRISPR screens, network-medicine repurposing). The two threads Cartograph joins are still live and thinly cited: degree-normalized L3 link prediction (Kovacs et al. 2019, verified real) and LLM literature-grounded synthesis over PPI (2023 to 2025, single-digit citation counts). No group has married deterministic topological link prediction with LLM literature-grounded mechanistic explanation on a viral interactome. Three gaps the map surfaced, each a ready pitch line:
1. No topology-based held-out rediscovery benchmark on the COVID interactome exists. Cartograph's number is novel, not a re-run.
2. CRISPR screens are used as host-factor catalogs, rarely as an independent gold standard for interaction prediction. Option B is an original validation design, not a borrowed one.
3. LLM hypothesis generation still lacks grounding standards, and the 2024 to 2025 work names hallucination as the central risk. Cartograph's cited-plus-deterministic design is a timely, publishable answer.

One modeling nudge from the same map: cross-coronavirus conservation (Gordon et al. 2020, Science, extends the map to SARS-CoV-1 and MERS) is a strong prior for which held-out edges should be recoverable. Consider using conservation when you pick or analyze the held-out split.

---

## 4. Rubric pressure-test

Judging is 4 axes. Impact 25, Claude Use 25, Depth and Execution 20, Demo 30. Here is where Cartograph stands and what to do about it.

Demo (30%, your biggest lever). Strong fit if and only if the wow moment is early and the number is live. Risk: burning the first 60 seconds on setup. Fix: metaphor in one sentence, then a query-to-cited-hypothesis inside 15 seconds, then the number. Script is in section 8. This axis is where the grand prize is won or lost, so the demo path is the product until it works.

Claude Use (25%, your special-prize lever). This is the axis most builds underplay and the one that catches the "creative use of Claude" attention. A basic app would have one LLM call that explains an edge. Go past that: a deterministic graph proposes, then a small team of Claude subagents adjudicates, and one of them is a Skeptic whose job is to find disconfirming evidence before any hypothesis is allowed to stand. Claude authors its own per-protein-family reasoning skills as it goes. The self-improving loop (section 6) is the headline creative move. Design notes in section 5 and 6.

Impact (25%). Real therapeutic relevance is built in: druggable host factors, a pandemic-era map, a method that generalizes to any Krogan map. Name the user out loud in the demo and summary: a Gladstone-style host-pathogen biologist who has an experimental map and needs to know what is missing and where to look next. Say the tool works without you in the room and outlasts the week (Build-track language, straight from the brief).

Depth and Execution (20%). The deterministic-versus-LLM separation is the craft signal. Structural claims are computed and reproducible, judgment is the only thing the model does, and the evaluator is locked. Show that boundary explicitly. It reads as engineering taste, not a quick hack.

Weakest axis to defend: Claude Use, only because most teams stop at a single explanatory call. Your fix is already on-thesis: the multi-agent adjudication plus the self-improving loop turns a retrieval demo into a system that visibly gets better. That is the difference between placing and winning a special mention.

---

## 5. The moat and the creative-Claude-use design

Two things the model cannot supply on its own, and that you encode visibly:

1. Systems taste: the deterministic-versus-reasoning boundary. The graph proposes candidates deterministically (same question, same answer, twice). Claude never invents an edge from its weights. Claude reads, synthesizes across papers, and explains, and it sits only where correctness is not required to be guaranteed. Make this boundary a slide and a sentence.

2. Biology grounding: every hypothesis ships with its evidence trail. A claim you cannot open the paper for does not ship.

The Claude subagent cast (keep it legible, three named roles):
- Reader: pulls the papers behind the neighboring edges and extracts the mechanistic claim.
- Skeptic: actively searches for disconfirming literature. If it finds a contradiction, the hypothesis is downgraded, not shipped. This is the honesty mechanism and it reads as rigorous to scientist judges.
- Curator: writes the confirmed hypothesis back into the graph as an annotated edge with its citations attached.

Creative Claude Code beats worth showing: Claude authoring its own reasoning skill per protein family and reusing it; subagents running in parallel; the deterministic layer and the reasoning layer cleanly separated so the same query is reproducible. These are the "went beyond a basic application" signals the Claude Use axis rewards.

---

## 6. The self-improving loop (the headline move, keep it bounded)

The loop, in one breath: the graph proposes a missing edge, Reader and Skeptic adjudicate it with literature, the Curator folds confirmed edges back into the graph as annotations, and the enriched graph proposes better candidates next round. As annotations accumulate, the evaluator number climbs. The map improves itself, under a locked ruler.

Why this wins here: it is the most legible possible proof of "a system that learns from its own outputs," it maps directly onto Anthropic's own "AI builds itself" narrative that the judges live in, and it is the creative-Claude-use headline. It is the transferable core of your prior RSI research, applied to biology.

Keep it honest and bounded (this matters, do not skip): the loop runs over the frozen held-out set only. The "self-improvement" is annotations accumulating and the score rising toward the hidden truth, not open-ended self-modification. The evaluator is a separate locked process the agents cannot touch. This is the Darwin Godel lesson: an unlocked evaluator gets gamed. Lock it, and the climbing number is trustworthy rather than a party trick.

---

## 7. Resolved technical forks

All five "decide on day one" forks, resolved for speed to the demo.

1. Graph tooling: networkx (in-memory, Python). A single network of a few thousand edges does not need Neo4j, and networkx is fastest to a demo and plays with everything. Keep Neo4j as an optional stretch only if you want the annotations layer to persist and look production-grade on stage. Do not start there.

2. Enrichment source for human-human PPIs among the prey: STRING, physical and experimental subset, high-confidence only. Rationale: STRING is the easiest single bulk source, it already integrates BioGRID, IntAct, and MINT for its experiments channel, and it gives a combined confidence score. Filter to the ~332 prey proteins plus their neighbors, and use the experimental and database channels, not the text-mining channel, to keep candidate generation mechanistic and honest. BioGRID (PSI-MITAB bulk) is the fallback if you want strictly physical curated edges.

3. Literature retrieval: NCBI E-utilities (esearch then efetch) for PubMed abstracts, plus PMC Open Access for full text where available. Free. Get a free NCBI API key to raise the limit from 3 to 10 requests per second. This is your concrete citation API. Pre-fetch and cache literature for the demo proteins so the stage path never waits on a network call.

4. Candidate generation: degree-normalized L3 (paths of length three) over the enriched graph. Proven to beat common neighbors on PPI networks and validated on bipartite graphs. Deterministic. It ranks candidate host factors per viral bait. Claude adjudicates and explains the top candidates. It does not generate them.

5. Evaluator metric and split: freeze the held-out split and the metric before predicting anything. Hold out 15 to 20 percent of the 332 high-confidence edges with a fixed random seed, committed to git as the first commit. Metrics: precision at k, recall, and PR-AUC or ROC-AUC against the held-out set. The harness scores automatically and lives in a separate locked file the agents may not edit (the Karpathy pattern: a locked prepare.py evaluator, an editable reasoning layer).

---

## 8. The locked evaluator (your signature move, get it working first)

This is what turns a demo into a result and earns scientist trust. Build it before the reasoning layer.

Option A (the floor, do this first, fully in your control): randomly hold out 15 to 20 percent of the high-confidence edges. Predict them from the remaining graph plus literature. Report precision at k, recall, PR-AUC or ROC-AUC. The split is frozen before any prediction. The harness scores automatically. State the number live in the demo.

Option B (the reach, add only if the core is solid): validate host-factor predictions against an independent published genome-wide CRISPR host-factor screen for SARS-CoV-2 that the model never saw (for example Daniloski et al. 2021 Cell, or Wei et al. 2021 Cell; confirm the exact reference and access at build time). Predict host factors, check hits against the screen. Harder to game, more compelling. This is the "and it generalizes to independent ground truth" flourish.

Ship A as the guaranteed number. Add B as the flourish. Either way, the number goes on screen.

---

## 9. The 3-minute demo (visual-first; the map fills itself in)

This is the biggest change from the first draft, and it comes straight from what the winners actually did. The winning demos never showed a dashboard. They made the domain artifact itself the spectacle. Wrench Board (2nd, Opus 4.7) won the room when "the boardview lit up step by step, arrows appearing, components getting pointed at, names surfacing." Tekton (1st, Opus 4.8) won on a 3D model with an evidence chain to every documented source. MaestrIA "streams its reasoning in real time with animated bounding boxes over the photos." Cartograph's interactome is the same class of object: a living map that lights up, proposes, and completes itself, with a paper behind every edge. Full analysis and the visual spec are in the companion doc "Cartograph Winning Playbook."

Design rule: the eval is the credibility spine, but you show it as an event inside the map, never as a line chart. The number ticks in a corner. The eye is on the map.

The screen: a dark, cinematic force-directed graph of the SARS-CoV-2 to human map. Viral proteins one color, human host proteins another, edges are known interactions. It looks real because it is real data.

0:00 to 0:20, metaphor and problem, spoken over the live map.
"This is a map of how SARS-CoV-2 hijacks a human cell. 332 known contacts, and every edge is a paper. But the map is full of holes, and finding what is missing today means a scientist reading for weeks. Cartograph is the navigation layer."

0:20 to 0:55, the wow: ask, then watch the graph move.
Type a plain-English question. Claude's reasoning streams. A neighborhood of the graph highlights, the path of length three is walked visibly, and a candidate edge is drawn as a glowing dashed arrow. A mechanism card slides in with its citations. "Twelve seconds. Click the edge, open the paper." This is the query-to-cited-hypothesis moment, now visual instead of textual.

0:55 to 1:50, the eval as spectacle (this replaces the boring number).
"Is this just a confident story? We hid a fifth of the real edges before any prediction. Watch the map find them." Predicted edges snap into place. Correct ones flash and lock green against the hidden truth, misses flash red and fade. A small precision-at-k counter climbs in the corner, but the map completing itself is the show. This is the honest evaluator, made watchable.

1:50 to 2:25, the Skeptic and the loop (creative Claude use).
A candidate edge flickers. The Skeptic agent surfaces a contradicting paper on screen, and the edge dims and drops. The survivors lock in, the map gets denser, and the next query is better for it. "The map improves itself, and a locked ruler proves it is real, not the model marking its own homework."

2:25 to 2:50, architecture and honesty in one line.
"The design: the graph proposes deterministically, Claude adjudicates and cites, a locked evaluator scores. Claude never invents an edge. Every claim opens to a paper."

2:50 to 3:00, close.
"Cartograph. Point it at any Krogan map. It tells you what is missing, and it proves how often it is right."

Rules for the recording: one network loaded, one query, the eval shown as the map filling in, one visible Skeptic drop. If a beat is not on this list, cut it. Reserve the entire last day for recording the video. Multiple winners warned that a 3-minute video takes far longer to produce than you expect.

---

## 10. Seven-day plan (demo-path-first, eval as the first commit)

Note: this section is superseded by the standalone doc "Cartograph 7-Day Plan" (elevated scope: structural interactome workbench, with a demo-critical core, a phase-two ladder, and a Day-4 decision gate). The lighter outline below is kept for reference.

Day 1, Tue Jul 7 (today): scope locked (this doc). Freeze the held-out split and write the locked evaluator harness. That is the first commit. Load the SARS-CoV-2 map from NDEx into networkx and confirm it loads clean. Attend the 12PM kickoff.

Day 2, Wed Jul 8: enrich with STRING human-human PPIs among the prey. Implement normalized L3 candidate generation. Produce a baseline evaluator number from structure alone, no LLM. That is your honest floor. Attend the 12PM Claude Science session with Alexander Tarashansky.

Day 3, Thu Jul 9: literature retrieval (E-utilities plus PMC OA, cached). Build the reasoning layer: Reader, Skeptic, Curator subagents produce a cited hypothesis for a candidate. Wire the deterministic-versus-LLM boundary so the critical path is reproducible.

Day 4, Fri Jul 10: close the loop. Confirmed hypotheses fold back as annotations, re-run the evaluator, capture the before-and-after number. Build the minimal live view: the query-to-hypothesis panel and the climbing chart. Attend the 12PM Gladstone session on virtual genome-wide PPI screening (Sukrit Silas). This one is directly on your topic. Do not miss it.

Day 5, Sat Jul 11: bulletproof the 3-minute path. Cache all literature for the demo proteins. Hard-code anything not on the path. Rehearse against a clock.

Day 6, Sun Jul 12: Option B external CRISPR-screen validation only if the core is solid, otherwise polish and record a backup demo take. Confirm the repo is clean and open-source licensed.

Day 7, Mon Jul 13 (due 9PM ET): record the final 3-minute video, write the 100 to 200 word summary, finalize the public repo with an approved open-source license (MIT or Apache-2.0), submit on the CV platform.

Office hours run 5 to 6PM ET daily. Use them to sanity-check the biology with the Anthropic and Gladstone people who will influence judging.

---

## 11. Risks and the cut list

Risks and mitigations:
- Sparse bipartite graph: mitigated by STRING enrichment plus L3.
- Weak literature for some proteins: pre-select demo proteins with rich literature and cache their evidence.
- Loop overscoping: keep it bounded to the frozen held-out set, annotations only, no open-ended self-modification.
- Evaluator gaming (the Darwin Godel cautionary tale): the evaluator is locked, separate, and committed before any prediction.
- Time: the demo path is the product. If a day slips, cut scope, not the demo.

Cut for now, not forever: multi-network support, cross-species comparison (MERS, SARS-CoV-1), a polished UI, Neo4j persistence, Option B, and anything off the query-to-cited-hypothesis-to-number path.

---

## 12. What is settled versus open

Settled: Life Sciences, Build track, solo. SARS-CoV-2 Krogan map as demo data. networkx, STRING enrichment, E-utilities plus PMC, normalized L3, locked held-out evaluator. The metaphor, the differentiation, the loop, and the demo script above.

Open, decide as you build: exact held-out percentage and random seed (pick and freeze Day 1), which two or three demo proteins to feature (pick for literature richness Day 3 to 5), whether to attempt Option B (decide Day 6 based on core stability), final project name if you want to move off Cartograph.

---

## Sources
- Gordon et al. 2020, A SARS-CoV-2 protein interaction map reveals targets for drug repurposing, Nature: https://www.nature.com/articles/s41586-020-2286-9
- Krogan Lab network maps (NDEx links): https://kroganlab.ucsf.edu/network-maps
- Normalized L3-based link prediction in PPI networks, BMC Bioinformatics: https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-023-05178-3
- Neighbor-Enhanced Link Prediction in Bipartite Networks, PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC12192312/
- STRING API help: https://string-db.org/help/api/
- NCBI E-utilities general intro (rate limits, API keys): https://www.ncbi.nlm.nih.gov/books/NBK25497/
- GraPPI, Retrieve-Divide-Solve GraphRAG for PPI exploration, arXiv Jan 2025: https://arxiv.org/abs/2501.16382
- Judging criteria and schedule: Built with Claude Life Sciences participant guide (project doc "Hackathon Details").
