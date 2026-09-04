# Onboarding prompt for a new coding agent

Paste everything in the fenced block below as the first message to a fresh coding agent
working on this repo. It is written to be self-contained.

Keep it current. If the measured numbers or priorities change, update this file in the same
commit as the change.

---

```
You are picking up Cartograph, a Python + vanilla-JS research tool. Read this whole message
before running anything, then read the three docs named at the end before proposing changes.

WHAT IT IS
Cartograph is a navigation and triage layer for protein interaction maps. It loads an
experimentally-derived interactome, deterministically proposes edges that should exist but are
not yet drawn, justifies each with retrieved literature and a 3D structure, and measures how
often it is right against a benchmark split that was frozen before any prediction code existed.

Origin: a 6-day hackathon build (2026-07-08 to 07-13, Anthropic x Gladstone). It is now being
developed as a possible venture, so the audience for results is technical diligence, not end
users. Credibility of the numbers matters more than features.

NON-NEGOTIABLE INTEGRITY RULES. These are the product, not preferences.
1. The critical path is deterministic. The graph proposes edges via degree-normalized L3 in
   backend/predict/l3.py. An LLM never invents an edge. It reads, adjudicates and explains.
2. The evaluator is LOCKED. backend/eval/ holds a held-out split frozen as the first commit
   with a sha256 checksum. A test proves the predictor cannot import it. Never edit
   backend/eval/. You may import and call its functions read-only.
3. No citation, no render. Every mechanistic clause must reference a PMID present in the
   verified edge pack, or the clause is dropped.
4. Predicted is always labelled predicted. Experimental structures and predicted models are
   never conflated.
5. Interface residues are computed from deposited coordinates, never copied from prose.
6. Docs and prose use short declarative sentences and NO em dashes. Match this.

ENVIRONMENT
- Python 3.13 in ./.venv. The system python is 3.9 and CANNOT run this project; the pins need
  3.11+. Always use ./.venv/bin/python.
- Secrets live in .env at the repo root, which backend/config.py loads at import time via a
  dependency-free loader. It does not override real environment variables.
  Two keys are required for the live agent, not one:
    ANTHROPIC_API_KEY
    ANTHROPIC_WORKSPACE_ID     (the key is identity-linked; every endpoint 400s without it)
- Commands:
    ./run.sh build   rebuild the computed artifact
    ./run.sh test    92 tests, about 23 seconds
    ./run.sh serve   offline static demo on 127.0.0.1:8791
    ./run.sh api     the same demo plus the live /api/* routes and the Evidence Agent
- Anything under /tmp or a scratch dir is fine for experiments. Do not write experiment
  scripts into the repo.

ARCHITECTURE, SHORT VERSION
  evidence/gordon2020_edges.csv          332 edges, 26 viral baits, 332 human preys, 0 shared
    -> backend/graph/load.py             networkx, nodes typed viral|human
    -> backend/graph/enrich.py           + 159 STRING v12.0 physical edges, score >= 700
    -> backend/predict/l3.py             degree-normalized L3, 1/sqrt(deg(a)*deg(b)) per path
    -> backend/eval/evaluator.py         LOCKED. precision@k, recall, ROC-AUC, AP
    -> backend/reason/, backend/structure/, backend/agent/
    -> backend/build_artifact.py         freezes everything into
                                         frontend/data/cartograph_computed.json
    -> frontend/                         index.html + app.js + style.css, Cytoscape + Mol*

The Evidence Agent (backend/agent/pipeline.py) is a six-stage drop-only funnel: resolve,
retrieve, read, skeptic, VERIFY (deterministic), review. After the read stage the model can
only ever REMOVE claims. Every failure path lands on topology-only. Stage 5 re-checks every
citation against a closed PMID set. This architecture is the most defensible thing in the repo.

NUMBERS THAT ARE TRUE, MEASURED 2026-09-03
The candidate universe is 8,357 untested bait-human pairs containing 57 positives, a prevalence
of 0.68%.
- precision@10/20/50 = 0.300 / 0.450 / 0.260. These are honest and survive full-universe
  evaluation unchanged, because precision@k is invariant to expanding the negative set when the
  top-k is unchanged. Enrichment over prevalence is 44x / 66x / 38x.
- Tie-aware ROC-AUC over the full universe is 0.6178, against a null ranker at 0.5000.
- 14 of 57 held-out edges are reachable by L3. Every common-neighbour variant reaches 20.
  The union of all topology scorers is also 20, so 37 of 57 are structurally unrecoverable by
  any local-topology method on this split.

NUMBERS IN THE README THAT ARE WRONG. Do not repeat them.
- "recall@50 = 0.93 on 57 held-out edges" is 13 of 14 REACHABLE edges. The global value is
  0.2281. Maximum attainable recall@50 against 57 positives is 0.8772, so 0.93 was provably
  not global.
- "ROC-AUC = 0.845 on all candidate edges" was computed over the 115 pairs L3 reaches, which is
  1.4% of the universe. This is the restricted-negative setting. Honest value 0.6178.
- "24 tests" is stale. There are 92.
- "zero live network calls" is false in the literal sense: index.html loads Google Fonts in both
  modes. The DATA claim is true, nothing is fetched live at demo time.

TRAPS THAT WILL COST YOU AN HOUR EACH
- backend/eval/evaluator.py imports l3_scores directly and calls enriched_graph() internally,
  so evaluate() is hardwired to the Gordon dataset and to one predictor. To benchmark another
  scorer, do NOT refactor the evaluator. Import build_training_graph(load_frozen()) and the
  metric helpers _precision_recall_at_k / _roc_auc / _average_precision and write a standalone
  script. Six baselines were run this way in about 40 lines.
- The metric helpers assume ties are already broken upstream, and the pooling tie-break is
  alphabetical. Coarse scorers such as common neighbours have very few distinct scores, so the
  alphabet decides their top-k and inflates precision@k. Always recompute with mid-rank tie
  handling before quoting a comparison.
- evidence/string_enrichment.cached.json contains only 159 edges ALREADY filtered at
  required_score >= 700. Lower thresholds cannot be derived from it and need a fresh fetch.
- The Evidence Agent dossier cache is an in-memory dict, wiped on every restart. A cold run
  takes about 45 seconds; a cached one is instant.
- /api/eval/run calls evaluate() with no arguments, so it cannot fold back confirmed edges even
  though evaluate() accepts fold_back.
- Human-in-the-loop verdicts are localStorage only. "Confirmed edges fold into the map" means a
  CSS recolor. Nothing re-ranks.
- The four cited dossiers are a hardcoded list in config.DEMO_EDGES. Only one of them appears
  in the 40-row worklist.
- "Ask the map" is a regex keyword matcher in app.js, not natural language understanding.

WHAT NOT TO DO
- Do not edit backend/eval/.
- Do not replace L3 or adopt a learned predictor. 358 nodes and 491 edges have nothing to learn,
  and all indices on the same feature share one ceiling, so a better index cannot rescue a map
  where only 14 of 57 are reachable.
- Do not build auth, tenancy, billing or multi-user storage. Explicitly out of scope.
- Do not use STRING as ground truth. It is already used as a feature, so that is circular.
- Do not quote a precision number without stating the candidate universe and prevalence
  next to it.

READ THESE THREE DOCS BEFORE PROPOSING CHANGES
  docs/Cartograph_research_findings.md   state of the art, prior art, and the ordered next
                                         steps. Start here.
  docs/Cartograph_gap_audit.md           where the demo overpromises, what is demo-path-only,
                                         what needs more data, plus a measured-results appendix.
  docs/cartograph_soa_review.md          the full 9,100-word literature review, 88 verified DOIs.

CURRENT PRIORITY
Item 1 of the next-steps list in Cartograph_research_findings.md: define one candidate universe,
recompute every metric on it, and publish prevalence, enrichment and maximum attainable value
next to each number.

Before writing code, tell me what you intend to change and wait for my confirmation.
```
