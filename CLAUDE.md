# CLAUDE.md: Cartograph build context

Drop this at the repo root. It is the seed context for Claude Code. Read it before writing anything. Update it as decisions land.

## Mission
Build Cartograph: a navigation layer for a protein interaction map. It loads an experimentally-derived interactome, proposes the missing edges deterministically from graph structure, and has Claude read the literature behind the neighboring edges to produce a mechanistic, cited hypothesis. A locked evaluator hides a fraction of the known edges and measures how often we predict them back. The map fills itself in on screen, with a paper behind every edge.

Event: Built with Claude Life Sciences (Anthropic x Gladstone). Build track. Solo. Due Jul 13, 9PM ET. Open source (MIT or Apache-2.0), all work done during the event.

## The user we build for
A host-pathogen biologist (Gladstone style) who has an experimental interaction map and needs to know what edge is likely missing and where to look next, with evidence they can audit. Working software they could use without us in the room.

## Non-negotiable design rule: deterministic critical path, LLM for reasoning only
- The graph layer is deterministic and reproducible. Traversal, candidate generation, and edge scoring are computed, not invented. Same question returns the same answer twice.
- Claude never predicts an edge from its own weights. The graph proposes candidates; Claude reads, adjudicates, and explains with retrieved literature.
- Every hypothesis ships with its evidence trail. A claim with no openable paper does not ship.
- The evaluator is a separate, locked process. Agents may not read or edit it. This is the Darwin Godel objective-hacking lesson: an unlocked evaluator gets gamed.

## Architecture
1. Graph layer (deterministic, networkx): load the network, enrich it, run neighborhood queries and candidate generation.
2. Literature layer (retrieval): NCBI E-utilities (esearch then efetch) for PubMed abstracts, PMC Open Access for full text where available. Cache aggressively.
3. Reasoning layer (Claude subagents): Reader pulls and reads the papers behind neighboring edges; Skeptic hunts for disconfirming literature and can veto a hypothesis; Curator writes confirmed edges back as annotations.
4. Evaluator (locked): frozen held-out edge split, automatic scoring, committed before any prediction.
5. Frontend (the demo): a dark force-directed graph that animates traversal, draws candidate edges, streams reasoning, and shows the eval as edges snapping green.

The loop: graph proposes a missing edge, Reader and Skeptic adjudicate with literature, Curator folds confirmed edges back as annotations, the denser graph proposes better candidates next round, the evaluator number rises. Keep the loop bounded to the frozen held-out set. No open-ended self-modification.

## Locked technical decisions
- Data: SARS-CoV-2 to human map, Gordon et al. 2020. Ground truth lives in /evidence/gordon2020_edges.csv (332 edges, 26 baits, 332 unique preys, 0 shared), verified against IntAct/IMEx record IM-27814; the 26 baits were recovered from the pp1ab polyprotein via UniProt chain ids. Druggability (66 proteins / 69 compounds, 29 FDA-approved) is a separate curated annotation, not part of the PPI edge record. NDEx CX is an alternative source.
- Graph tooling: networkx, in-memory. Neo4j only as an optional stretch for persisting annotations.
- Enrichment: STRING human PPIs among the prey, physical and experimental subset, high-confidence only. Not the text-mining channel. BioGRID PSI-MITAB is the fallback.
- Candidate generation: degree-normalized L3 (paths of length three). Proven to beat common neighbors on PPI networks and works on bipartite graphs. Deterministic.
- FLAGSHIP HONESTY CHECK (do not skip): the held-out ORF6-RAE1 recovery must ride a genuine length-3 path (for example ORF6 -> NUP98 -> a shared nucleoporin -> RAE1), not the 2-edge ORF6 -> NUP98 -> RAE1 shortcut, which is a common-neighbor (L2) signal, exactly the thing L3 is supposed to beat. ORF6's only real preys are NUP98, RAE1, MTCH1, and RAE1 attaches to the graph only through STRING once ORF6-RAE1 is held out. So enrich STRING around the nucleoporins until a true 3-edge path exists, then confirm the L3 scorer ranks RAE1 highly for ORF6 and report that rank. If the demo shows the 2-edge path, call it complex completion, not L3. The evidence pack's worked_example_orf6.json and gordon2020_counts.json both call this path "L3"; that label is wrong and must not propagate into the code or the demo script.
- Literature: NCBI E-utilities plus PMC OA. Get a free NCBI API key to raise the rate limit from 3 to 10 requests per second.
- Evaluator: hold out 15 to 20 percent of high-confidence edges with a fixed seed, committed as the first commit. Metrics: precision at k, recall, PR-AUC or ROC-AUC.
- Frontend: web app, force-directed graph (Cytoscape.js preferred for biology networks; sigma.js or D3-force as alternatives), server-sent events or websockets to stream reasoning and edge events. Pre-cache literature for demo proteins so the demo path never waits on the network.

## Build order (eval first, demo path first)
1. Freeze the held-out split and write the locked evaluator harness. First commit.
2. Load the NDEx map into networkx. Confirm it loads clean.
3. Enrich with STRING among the prey. Implement normalized L3. Get a baseline eval number from structure alone, no LLM. This is the honest floor.
4. Literature retrieval, cached. Reader, Skeptic, Curator subagents produce a cited hypothesis for a candidate.
5. Close the loop: fold confirmed edges back, re-run eval, capture before and after.
6. Frontend: the living map with traversal animation, cited-hypothesis card, and the eval-as-green-edges spectacle.
7. Bulletproof the 3-minute demo path. Hard-code and cache everything not on it. Rehearse.
8. Record the video (reserve the whole last day). Write the 100 to 200 word summary. Finalize the open-source repo and license. Submit.

## Demo path (the product until it works)
One network loaded. One plain-English query to a graph-traversal animation to a cited hypothesis. The eval shown as the map filling in green against hidden truth. One visible Skeptic drop. If a feature is not on this path, it waits.

## Cut list
Multi-network, cross-species (MERS, SARS-CoV-1), Neo4j persistence, polished settings UI, external CRISPR-screen validation (stretch only), anything off the query-to-hypothesis-to-map path.

## Conventions
- Prose and docs: short declarative sentences, no em dashes, proof before claims.
- Commit the eval and the frozen split before any prediction code.
- Ask Claude to audit what exists before building the next thing. That loop is underrated.
- Cite real papers only. Never fabricate a citation, a count, or a score.
