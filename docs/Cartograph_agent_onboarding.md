# Onboarding prompt for a new coding agent

Paste everything in the fenced block below as the first message to a fresh coding agent
working on this repo. It is written to be self-contained and to work for Codex, Claude Code
or any other agent.

Keep it current. If the measured numbers or priorities change, update this file in the same
commit as the change. Last updated 2026-09-14.

Note for Codex specifically: `AGENTS.md` at the repo root is auto-read and is STALE. It is the
July hackathon seed. The prompt below overrides it explicitly.

---

```
You are picking up Cartograph, a Python + vanilla-JS research tool. Read this whole message
before running anything, then read the docs named at the end before proposing changes.

FIRST: AGENTS.md and CLAUDE.md at the repo root are STALE. They are the July hackathon seed
context. Their mission statement, cut list and "user we build for" are all superseded by this
message and by docs/Cartograph_context_package.md. Where they conflict with this message, this
message wins. Do not act on their cut list; it says conservation is cut, and conservation is
fully built.

WHAT IT IS
Cartograph is an evidence-and-measurement layer for protein interaction maps. It loads an
experimentally-derived interactome, deterministically proposes edges that should exist but are
not yet drawn, justifies each with retrieved literature and a 3D structure, and measures how
often it is right against a benchmark split frozen before any prediction code existed.

Origin: a 6-day solo hackathon build (2026-07-08 to 07-13, Anthropic x Gladstone). It is now
being developed at AI Fund as a possible venture, so the audience for results is technical
diligence, not end users. Credibility of the numbers matters more than features.

CURRENT STATE, 2026-09-14
- Branch `bench/candidate-universe`, PR #1 OPEN and unmerged against `main`, 3 commits,
  +1784 -26 across 22 files. `main` is unprotected.
- 123 tests pass in about 40 seconds.
- The candidate-universe work is DONE and shipped in that PR. Every metric is now computed over
  one stated universe with prevalence, enrichment and maximum attainable value published next
  to it. `backend/bench/` is the new home for that machinery.
- Exactly one interactome has ever been loaded. Zero second datasets have been run.

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
6. Never quote a precision number without stating the candidate universe and prevalence next
   to it, and never quote a single-seed metric as a point estimate. See NUMBERS below.
7. Docs and prose use short declarative sentences and NO em dashes. Match this.

ENVIRONMENT
- Python 3.13 in ./.venv. The system python is 3.9 and CANNOT run this project. Always use
  ./.venv/bin/python.
- Secrets live in .env at the repo root, loaded by backend/config.py at import time. Two keys
  are required for the live agent, not one:
    ANTHROPIC_API_KEY
    ANTHROPIC_WORKSPACE_ID     (the key is identity-linked; every endpoint 400s without it)
- Commands:
    ./run.sh build   rebuild the computed artifact
    ./run.sh test    123 tests, about 40 seconds
    ./run.sh serve   offline static demo on 127.0.0.1:8791
    ./run.sh api     the same demo plus the live /api/* routes and the Evidence Agent
- Write experiment scripts to a scratch directory, never into the repo.

ARCHITECTURE, SHORT VERSION
  evidence/gordon2020_edges.csv          332 edges, 26 viral baits, 332 human preys, 0 shared
    -> backend/graph/load.py             networkx, nodes typed viral|human
    -> backend/graph/enrich.py           + 159 STRING v12.0 physical edges, score >= 700
    -> backend/predict/l3.py             degree-normalized L3, 1/sqrt(deg(a)*deg(b)) per path
    -> backend/eval/evaluator.py         LOCKED. precision@k, recall, ROC-AUC, AP
    -> backend/bench/                    candidate universe, tie-aware metrics, metric records
                                         that always carry their denominator. Dataset- and
                                         predictor-agnostic. The most reusable code here.
    -> backend/reason/, backend/structure/, backend/agent/
    -> backend/build_artifact.py         freezes everything into
                                         frontend/data/cartograph_computed.json
    -> frontend/                         index.html + app.js + style.css, Cytoscape + Mol*

The Evidence Agent (backend/agent/pipeline.py) is a six-stage drop-only funnel: resolve,
retrieve, read, skeptic, VERIFY (deterministic), review. After the read stage the model can
only ever REMOVE claims. Every failure path lands on topology-only. Stage 5 re-checks every
citation against a closed PMID set. This architecture is the most defensible thing in the repo.

NUMBERS THAT ARE TRUE
The candidate universe is 8,357 untested bait-human pairs containing 57 positives, a prevalence
of 0.68%. Measured from the built artifact.
- precision@10/20/50 = 0.300 / 0.450 / 0.260 on the frozen split. Enrichment 44x / 66x / 38x.
- Tie-aware ROC-AUC over the full universe is 0.6178 against a null ranker at 0.5000.
- recall@50 is 0.2281, with a maximum attainable of 0.8772.
- 14 of 57 held-out edges are reachable by L3. Every common-neighbour variant reaches 20, and
  the union of all local-topology scorers is also 20, so 37 of 57 are structurally unrecoverable
  by any such method on this split.
- All 57 held-out pairs are Park-Marcotte class C2. C3 is unmeasured and no generalisation to
  it is claimed.

THE HEADLINE IS A SINGLE-SEED DRAW. Measured 2026-09-14, reproducible in under a second.
Resampling the same 56-edge protocol on the same enriched graph with seeds 0-19 gives
mean 0.3175, median 0.300, sd 0.099, range 0.15 to 0.55. Only 2 of 20 draws reach 0.45, so the
published 0.45 sits near the 90th percentile of its own sampling distribution. The honest
figure is precision@20 about 0.32 +/- 0.10 at n=20, which is still roughly 47x prevalence.
Reachability swings 7 to 16 of 56 over the same seeds. Do not quote 0.45 bare.

Reproduce it like this:
    from backend.graph.enrich import enriched_graph
    from backend.eval.evaluator import predict_all
    # sample 56 AP-MS edges per seed, remove them, predict_all, score precision@20

THE STRATEGIC VERDICT, from docs/Cartograph_context_package.md
- The USP is real and it is NOT the predictor. The three unmatched things are the locked
  pre-registered benchmark reported per map, the deterministic no-citation-no-render gate, and
  structure-derived interface residues. Prior art already owns "ranked predictions with
  evidence" (PrePPI, P-HIPSTer).
- A one-line STRING best-score guilt-by-association lookup beats shipped L3 on every precision
  cut and on AP (0.681 vs 0.373). The null hypothesis that L3 adds nothing beyond STRING is
  live and not yet refuted. Every L3 path in this map traverses two STRING edges.
- Five candidate customer profiles were stress-tested on 2026-09-14 and all five came back
  weak. The pain the field names in print is irreproducibility, not triage. Do not build
  toward a triage pitch without saying so explicitly.

TRAPS THAT WILL COST YOU AN HOUR EACH
- backend/eval/evaluator.py imports l3_scores directly and calls enriched_graph() internally,
  so evaluate() is hardwired to the Gordon dataset and to one predictor. To benchmark another
  scorer, do NOT refactor the evaluator. Import build_training_graph(load_frozen()) and use
  backend/bench for the metrics. Six baselines were run that way in about 40 lines.
- backend/agent/resolve.py:99 is `resolve_edge(bait, prey, taxid="9606")`. ONE taxid is passed
  to BOTH ends. A host-pathogen edge is viral x human by construction, so the Evidence Agent
  degrades to topology-only on every edge shape this project was built for. Orf6|RAE1 returns
  topology_only in 1.3 seconds. It works fine on same-organism pairs: TP53|MDM2 runs end to end
  in 38.8 seconds with real PDB 1YCR and 0 clauses dropped.
- config.py:78 pins STRING_SPECIES = 9606, used at graph/enrich.py:35 and :85. Every upload is
  STRING-enriched against human regardless of the organism the user selected.
- backend/bench is imported only by build_artifact.py. An uploaded map gets _own_eval at
  api/server.py:306-328, which returns precision@min(20, n_heldout) on one hardcoded seed and
  nothing else. No recall, no AP, no AUC, no universe size, no prevalence.
- A Gordon-shaped map with no STRING enrichment hits returns zero predictions and precision 0.0
  with enrich_error still None. Silent wrong answer.
- Tie handling. The locked evaluator's helpers assume ties are broken upstream and the pooling
  tie-break is alphabetical. Coarse scorers such as common neighbours have very few distinct
  scores, so the alphabet decides their top-k and inflates precision@k. Use backend/bench, which
  is mid-rank tie-aware, for any comparison.
- evidence/string_enrichment.cached.json contains only 159 edges ALREADY filtered at
  required_score >= 700. Lower thresholds cannot be derived from it and need a fresh fetch.
- The Evidence Agent dossier cache is an in-memory dict, wiped on every restart.
- /api/eval/run calls evaluate() with no arguments, so it cannot fold back confirmed edges even
  though evaluate() accepts fold_back.
- Human-in-the-loop verdicts are localStorage only. "Confirmed edges fold into the map" is a CSS
  recolor. Nothing re-ranks.
- The in-map evaluator and loop animations replay baked artifact JSON. They do not compute.
- The four cited dossiers are a hardcoded list in config.DEMO_EDGES.
- "Ask the map" is a regex keyword matcher in app.js, not natural language understanding.
- README.md line 152 still says "59 tests". It is 123.

WHAT NOT TO DO
- Do not edit backend/eval/.
- Do not replace L3 or adopt a learned predictor. 358 nodes and 491 edges have nothing to learn,
  and all indices on the same feature share one ceiling, so a better index cannot rescue a map
  where only 14 of 57 are reachable. Settle L3 versus STRING first.
- Do not build auth, tenancy, billing or multi-user storage. Explicitly out of scope.
- Do not use STRING as ground truth. It is already a feature, so that is circular.
- Do not add UI polish. Generalization evidence is the binding constraint, not product surface.

READ THESE DOCS BEFORE PROPOSING CHANGES
  docs/Cartograph_context_package.md     what it is, the customer, USP, the honest numbers, and
                                         what would change the verdict. Start here.
  docs/Cartograph_research_findings.md   state of the art, prior art, ordered next steps.
  docs/Cartograph_gap_audit.md           demo-vs-product gaps plus a measured-results appendix.
  docs/cartograph_soa_review.md          the full 9,100-word literature review, 88 verified DOIs.

CURRENT PRIORITY, ordered by decisiveness
1. Republish the headline as a distribution, not a draw. mean 0.318, sd 0.099, n=20, replacing
   the bare 0.45 in README.md, the built artifact and the frontend eval panel.
2. Settle L3 versus STRING best-score in public with mid-rank tie handling across at least
   three maps. If STRING wins, ship it as the scorer and sell the harness.
3. Fix the two taxids in agent/resolve.py and make STRING species organism-aware, then run a
   second map end to end. Haas 2023 influenza A or Jager 2011 HIV. Jager breaks the degree-1
   star topology, so it tests whether these findings are artifacts of this map's shape.
4. Wire backend/bench into the upload path so an uploaded map returns universe size, prevalence,
   precision@k with its denominator, recall, AP, tie-aware AUC, per-edge transparency and at
   least 20 resampled seeds.
5. Run the retrospective test. Rebuild the graph from pre-2020 evidence and ask whether eEF1A
   (plitidepsin), eIF4A (zotatifin) or PIKfyve (apilimod) lands in the top 20.

Before writing code, tell me what you intend to change and wait for my confirmation.
```
