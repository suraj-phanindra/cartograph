# Cartograph BUILD_SPEC

Architecture, data contracts, and the evaluator spec. This is the "how to build" companion to `CLAUDE.md` (which holds the rules and locked decisions) and `Cartograph_7Day_Plan.md` (the schedule). This document specifies interfaces and contracts, not implementation. Write the code during the event.

## 1. Architecture at a glance
Four layers with one hard boundary.
- Graph layer (deterministic): load the interactome, enrich it, generate candidate edges, score them. Reproducible. Same input, same output.
- Evaluator (locked): a separate process that freezes a held-out edge set and scores predictions. The agents cannot read or edit it.
- Reasoning layer (Claude subagents): Reader, Skeptic, Curator turn a candidate plus retrieved literature into a cited, adjudicated hypothesis. Judgment lives here and only here.
- Presentation layer: the interactive map, the structural dossier (Mol*), and the eval shown as edges snapping green.

The boundary: the graph proposes edges deterministically; Claude reads, judges, and explains. Claude never invents an edge. Structural claims are computed or retrieved, never asserted from model weights.

## 2. Suggested module layout (Claude Code builds this)
```
backend/
  graph/        load edges, STRING enrichment, node/edge model
  predict/      degree-normalized L3 candidate generation
  eval/         LOCKED: frozen split + scoring harness (commit first)
  reason/       Reader / Skeptic / Curator agents; hypothesis assembly
  structure/    PDB / predicted-structure resolution, interface residues
  api/          query, predict, eval, loop endpoints + SSE stream
frontend/
  graph view (Cytoscape.js), dossier panel (Mol*), eval overlay, controls
evidence/       (provided) ground truth + cited packs + domain priors
```

## 3. Data contracts (everything in `evidence/`)
Read `evidence/EVIDENCE_MANIFEST.json` first; it catalogs and dates every file.

### 3.1 Ground-truth edges — `gordon2020_edges.csv`
Columns: `bait,bait_uniprot,prey_gene,prey_uniprot,miscore`. 332 rows. 26 unique baits, 332 unique preys, none shared across baits. `miscore` is the IntAct MI-score (0 to 1). This is the graph and the evaluator ground truth.

### 3.2 Counts — `gordon2020_counts.json`
Verified canonical numbers (26 / 332 / 66 / 69), the bait list, and demo-anchor edge confirmations. Use for assertions in the UI and the video, but re-check against the CSV at load.

### 3.3 Edge packs — `evidence/edge_packs/*.json`
Schema (verified):
```
{
  "edge": "Orf6-NUP98",
  "papers": [ { "pmid", "doi", "one_line_mechanism", "title", "journal", "year" }, ... ],
  "neighbor_edge": "NUP98-RAE1",
  "neighbor_papers": [ { same fields }, ... ],
  "confidence": "high"
}
```
The Reader agent renders `papers` into the dossier; every entry has an openable PMID/DOI. Provided packs: `orf6_nup98`, `orf9b_tom70`, `n_g3bp1`.

### 3.4 Flagship worked example — `worked_example_orf6.json`
Holds `held_out_edge`, `kept_edge`, `bridge_edge`, a cited `chain`, a `mechanism_summary`, and an `Orf9b-TOMM70` backup. NOTE: it calls ORF6 -> NUP98 -> RAE1 an "L3" path; that is length 2. See the honesty check in section 6.

### 3.5 Domain priors — `cartograph_domain.json` (the moat)
Keys: `known_prey_complexes` (12, with CORUM/Reactome refs), `interaction_priors_by_viral_family`, `ap_ms_false_positive_patterns` (5, CRAPome-style), `sources` (16). Inject into candidate scoring and give the Skeptic its false-positive checklist.

### 3.6 CRISPR gold standard — `crispr_gold_standard.csv` + `crispr_screens.json`
27 genes hit in 2 or more of 7 screens; column `in_gordon_prey` marks overlap with AP-MS prey (only SCAP is True). Use for Option B corroboration only. Expect near-zero AP-MS overlap; that is correct orthogonal biology, not a failure.

## 4. Graph layer
- Build a graph from `gordon2020_edges.csv`: viral bait nodes and human prey nodes, edges = interactions, attribute `miscore`.
- Enrich with human-human STRING edges among the prey set. Use the physical/experimental and database channels, not text-mining. Pin the STRING release in config and record it (reproducibility).
- For the flagship to work, enrichment must pull the local neighborhood of the nucleoporins (NUP98, RAE1, and their shared STRING partners), not just the single NUP98-RAE1 edge. See section 6.
- Node model: `{id, type: viral|human, uniprot, degree, annotations[]}`. Edge model: `{source, target, kind: known|enrichment|predicted|confirmed, score, evidence_ref}`.

## 5. Candidate generation (degree-normalized L3)
- Interface: `score_candidates(graph, source_node) -> ranked list of {candidate, l3_score, paths[]}`.
- L3 counts paths of length three between the source and each candidate, degree-normalized to suppress hub bias (Kovacs et al. 2019, `evidence/literature_map`). Deterministic.
- Fold in domain priors from `cartograph_domain.json` (for example, complex-membership boosts) as a transparent, logged term, kept separate from the raw topological score.
- Output feeds both the map (candidate edges to draw) and the reasoning layer (top candidates to adjudicate). The graph proposes; it does not explain.

## 6. Flagship honesty check (do not skip)
The demo recovers held-out ORF6-RAE1. ORF6's only real preys are NUP98, RAE1, MTCH1, so once ORF6-RAE1 is held out, RAE1 rejoins the graph only through STRING. The single NUP98-RAE1 bridge gives ORF6 -> NUP98 -> RAE1, which is length 2 (a common-neighbor signal, the thing L3 is meant to beat). To keep the method and the demo honest:
1. Enrich STRING around the nucleoporins so a genuine length-3 path exists, for example ORF6 -> NUP98 -> [shared nucleoporin] -> RAE1.
2. Confirm the L3 scorer ranks RAE1 highly for ORF6 with ORF6-RAE1 held out, and surface that rank.
3. If the UI shows the 2-edge path, label it complex completion, not L3.
Do not repeat the "L3" label from `worked_example_orf6.json` uncritically.

## 7. Evaluator (LOCKED — first commit)
- Freeze the split before any prediction: hold out 15 to 20 percent of the high-confidence edges with a fixed random seed. Write the held-out set and the seed to a committed file (for example `eval/heldout.frozen.json`). This file and the scoring code live in `backend/eval/` and are never imported or modified by the reasoning layer.
- Metrics: precision at k, recall, and PR-AUC or ROC-AUC against the held-out set. Report a single headline number (precision at k) plus the curve.
- Two runs: baseline (structure and L3 only, no LLM) is the honest floor; full (with the reasoning layer's accept/reject folding back) is the improvement story. Capture both, and the before/after across one loop round.
- Option B (corroboration, optional): score predicted host factors against `crispr_gold_standard.csv`. Present as corroboration, never as the headline. Option A stays the guaranteed number.
- Anti-gaming: the evaluator process is separate and committed first (the Darwin Godel objective-hacking lesson). Say so on screen.

## 8. Reasoning layer (Claude subagents)
- Reader: given a candidate edge, load the matching `edge_packs/*.json`, extract the mechanism and the citations. Output must carry openable PMIDs/DOIs.
- Skeptic: search the packs and domain false-positive patterns for disconfirming evidence. May veto or downgrade. This is the honesty mechanism and the on-screen drama.
- Curator: if the hypothesis survives, write it back to the graph as an annotated, confirmed edge with its citations attached.
- Hypothesis object (contract):
```
{
  "edge": "Orf6-RAE1",
  "mechanism": "two to three sentences",
  "citations": [ { "pmid", "doi", "claim" }, ... ],
  "confidence": { "topology": 0-1, "structure": "pLDDT/ipTM or experimental", "literature": "strong|moderate|weak" },
  "proposed_test": "which interface residues to mutate; which assay",
  "status": "confirmed|downgraded|rejected"
}
```
- Rule: no citation, no render. No invented edges.

## 9. Structural dossier
- Embed the Mol* web component. Load experimental structures by URL from PDB or AlphaFold DB: ORF9b-TOM70 = 7DHG; Orf6 on Rae1-Nup98 = 7VPH (SARS-CoV-2; confirm in RCSB, do not use 7VPG which is the SARS-CoV-1 homolog). Highlight interface residues.
- For an edge with no experimental structure, show a predicted complex from an open model (Boltz-2, MIT; Chai-1; AlphaFold3), clearly labeled predicted with a confidence readout (pLDDT / ipTM). For the demo, pre-compute one predicted complex offline and load the file rather than calling a model live.
- Never present a prediction as experimental fact.

## 10. API surface (suggested)
- `POST /query { question }` -> intent + target node.
- `POST /predict { node }` -> ranked candidates with L3 paths.
- `GET /dossier?edge=` -> hypothesis object + structure ref + druggability.
- `POST /eval/run` -> precision and the per-edge green/red outcomes.
- `POST /loop/step` -> confirm survivors, re-score, return the delta.
- `GET /stream` (SSE) -> reasoning tokens and edge events for the live UI.

## 11. Frontend contract
- Graph payload: `{ nodes: [{id,type,uniprot}], edges: [{source,target,kind,score}] }` for Cytoscape.js.
- Dossier payload: the hypothesis object (section 8) plus a `structure` block `{ source: pdb|predicted, id_or_url, interface_residues[], confidence }`.
- Eval events over SSE: `{ edge, outcome: correct|miss, running_precision }` so held-out edges snap green or red in the map.
- States to support: idle, query, traversal, dossier open, predicting-new-edge, eval, loop round, plus phase-two (upload, compare, export). Match `design/wow_moment_mock.html` and the incoming Claude Design exports.

## 12. Config and environment
- STRING release (pinned), NCBI E-utilities API key (raises the limit to 10 req/s), held-out seed and percentage, list of demo edges to pre-cache. Keep these in one config file so the eval is reproducible.

## 13. Definition of done (core)
Query to a deterministic L3 prediction to a structural dossier (real 3D + cited mechanism + proposed test) to the locked eval snapping edges green to one loop round, all on one screen, reproducible, open-source licensed, and runnable without the builder present. That is the submission. The phase-two ladder in the plan only makes it louder.
