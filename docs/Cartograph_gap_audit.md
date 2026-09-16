# Cartograph: demo vs product gap audit

Audited 2026-09-03 against commit `HEAD` on the live API build. Every row below was
verified by running the code or reading the built artifact, not by reading the README.

Method: queried `frontend/data/cartograph_computed.json` directly, ran
`backend.eval.evaluator.evaluate()`, exercised `/api/evidence` end to end with a live
key, and read the cited source lines. File and line references are given so each claim
can be rechecked.

## Claims that hold exactly

These were tested and found accurate. They are the credibility floor of the project.

| claim | evidence |
|---|---|
| Held-out transparency shows all 57 edges | `per_heldout_recovery` has 57 rows, 14 recovered, 43 missed, paths shown only for the 14 |
| Structure channel gain is 0.0 excluding the pinned edge | `eval.structure_channel.aggregate_gain_excl_pinned = 0.0`, both variants published |
| Upload eval uses a separate seed | `UPLOAD_SEED = 1234` in `api/server.py:57` vs `HELDOUT_SEED = 42` in `config.py:55` |
| ipTM is size-corrected | `structure/cofold.py:35-68` regresses against summed chain length and flags `size_corrected: false` when it cannot |
| SSE streams a live agent trace | `frontend/app.js:798` opens `EventSource('/api/stream?...')` |
| Novelty tags come from real co-mention counts | 27 rows at 0 co-mentions, 12 recovered held-out, 1 at a single co-mention |
| CX2, Claude Science handoff, self-contained HTML report | all three implemented (`app.js:1279`, `app.js:99`) |
| Evidence Agent degrades to topology-only without a key | verified live on 2026-09-02 |
| Determinism of the frozen split | sha256 recompute check passes on every build |

Publishing a measured zero for the project's own structure channel is the strongest
integrity signal in the repo. It should not be removed.

## A. Overpromises without lying

Each claim below is literally true and practically much thinner than it reads.

| id | claim | reality | one-line build to close it |
|---|---|---|---|
| A1 | Each hypothesis carries "the single next experiment" | 39 of 40 rows share one identical string | Derive the experiment per edge from the dossier's interface residues and assay type, or drop the column until it can vary |
| A2 | Worklist hypotheses carry a cited mechanism | 1 of 40 | Batch-run the Evidence Agent over the top 40 and bake results into the artifact |
| A3 | "Every hypothesis Cartograph renders is backed by an openable paper" (`app.js:1140`) | 40 rendered, 1 cited | Gate worklist rows on having a citation, or restate the rule as applying to dossier clauses only |
| A4 | A structural band appears "only where a real structure exists" | 0 of 40 | Run structure resolution across all 40 worklist edges at build time |
| A5 | Real druggability, with repurposing leads flagged | 1 of 40 has an approved drug | Extend the Open Targets precache from demo genes to all 40 prey |
| A6 | Skeptic verdict as an AP-MS frequent-flyer filter | 39 pass, 1 veto, so it fires on 2.5% | Run the Skeptic over every worklist row, not just dossier edges, and report its rejection rate |
| A7 | "Confirmed edges fold into the map" | CSS recolor only (`app.js:133-138`), nothing re-ranks | POST verdicts to the server, fold into the uploaded graph, re-run L3, reorder the list |
| A8 | One loop round improves precision@20 from 0.30 to 0.35 | Real at build time (`build_artifact.py:284-286`), replayed from stored JSON in the UI (`app.js:628`) | Make `/api/eval/run` accept `fold_back` so the loop recomputes live |
| A9 | "recall@50 = 0.93 on 57 real held-out edges" | Denominator is the 14 reachable edges, not 57. True recall@50 over all 57 is 0.23 | Report recall over reachable and recall over all held-out side by side |
| A10 | "Claude reads, adjudicates, and explains" | The offline demo runs nothing. Four dossiers are baked from `config.DEMO_EDGES` | Label baked dossiers as precomputed, and run the agent live when API mode is on |

## B. Works on the demo path only

| id | thing | why it does not generalize | one-line build to close it |
|---|---|---|---|
| B1 | The locked evaluator | `evaluate()` calls `enriched_graph()` internally and imports `l3_scores` directly (`eval/evaluator.py:23-24`), so it is hardwired to Gordon and to one predictor | Parameterize the evaluator over `(graph, frozen_split, predictor)` so any dataset and any method can be benchmarked |
| B2 | "Ask the map" natural language input | `parseIntent` (`app.js:466`) is a regex keyword matcher. It finds a bait name or one of three keywords and ignores the rest of the sentence | Replace with an intent parser that handles arbitrary phrasing and echoes back what it understood |
| B3 | The four dossiers | `DEMO_EDGES` in `config.py:96` is a hardcoded four-item list | Let the artifact builder generate dossiers for any N edges passed in |
| B4 | `/api/dossier` | Returns 404 unless the edge is in a pre-cached pack | Fall back to the live Evidence Agent when no pack exists |
| B5 | Loop round | Explicitly disabled for uploaded maps (`app.js:457`) | Generalize fold-back to run against any map's own held-out split |
| B6 | Held-out transparency view | SARS-CoV-2 only, disabled for uploads | Drive the same view from the upload's own split |
| B7 | Conservation and CRISPR columns | Coronavirus-only reference data, permanently "not applicable" on any other organism | Hide the columns for non-CoV maps rather than rendering dead cells |
| B8 | Graph loader | `load_graph(assert_counts=True)` asserts 332 edges and 26 baits (`graph/load.py:45`) | Move count assertions into per-dataset config instead of literals |
| B9 | Druggability | Committed snapshots cover demo genes only | Same precache expansion as A5 |

B1 is the keystone. It is the same refactor that unblocks the comparator suite and the
multi-dataset benchmark, and it gates C4, C5, C6 and C10 below.

## C. Exists already, needs to run on more data

| id | what exists | experiment to run |
|---|---|---|
| C1 | Evidence Agent, verified working end to end | Run across all 40 worklist edges, then all 115 proposals, and bake into the artifact |
| C2 | Full pipeline | Run on other pathogen-host AP-MS maps with the same bipartite shape (Mpox, HIV, Dengue/Zika, M. tuberculosis) |
| C3 | Full pipeline | Run on a dense human map (BioPlex 3.0, HuRI) to test whether the 14 of 57 reachability ceiling is a sparsity artifact |
| C4 | Evaluator | Repeat over 20 or more seeds to get confidence intervals on precision@20, currently a single draw on 14 positives |
| C5 | Evaluator | Temporal holdout: train on an older STRING or IntAct release, test on edges added since |
| C6 | Evaluator | Compare globally pooled ranking against per-bait ranking. They are different claims and only one is reported |
| C7 | Structure channel | The honest 0.0 gain rests on n=3 pairs. Rerun on a map with more deposited complexes before treating it as a finding |
| C8 | Conservation channel | Currently CoV-1 and MERS only. Extend to more strains to see if the signal holds |
| C9 | ipTM screen (`structure/cofold.py`) | Has never run on real data. Only synthetic test fixtures exist. Run it on one real pooled-AF3 matrix |
| C10 | Baselines | Random, L2 common-neighbor, degree-product and raw STRING score across every dataset above. Requires B1 first |

## Measured context for the headline numbers

CORRECTED 2026-09-03. An earlier version of this section used 115 pairs as the prevalence
denominator and reported lift of 2.1x to 3.7x. That was wrong by roughly 18x, and wrong in
the pessimistic direction. 115 is the predictor's own output, not a candidate universe, so
using it scores L3 against a pool L3 selected.

The real universe is 26 baits x 332 preys minus 275 training AP-MS edges = 8,357 pairs
containing 57 positives, a prevalence of 0.6821%. An empirical random baseline over that
universe (2,000 draws of 20, seed 0) gives mean precision@20 = 0.0066.

| metric | value | enrichment over prevalence |
|---|---|---|
| precision@10 | 0.300 | 44x |
| precision@20 | 0.450 | 66x |
| precision@50 | 0.260 | 38x |
| ROC-AUC (tie-aware, full universe) | 0.6178 | null ranker = 0.5000 |

The 66x figure was independently derived by the Claude Science review and reproduced here to
one decimal. Against an open-world proteome background of about 20,000 proteins the
prevalence falls to 0.011%, so the open-world enrichment is far larger again. Always state
the universe definition next to the number.

## Sequencing

CORRECTED 2026-09-03. This section previously called B1 the keystone that gates C4, C5, C6
and C10, and sequenced it first. That was wrong. `build_training_graph(frozen)` already
returns the training graph and the metric helpers are importable, so any scorer can be
benchmarked against the frozen split today with a read-only import. Six baselines were run
that way in one scratch script. B1 remains a cleanliness win but it is not a blocker, and
treating it as one delayed the most important experiment in the project.

The current ordering lives in `Cartograph_research_findings.md` under "Next steps". In short:
fix the candidate universe and re-report, then baselines and per-bait stratification, then
run on more maps. B1 is hygiene, done alongside, not first.

Retained from the original ordering:

1. A9, A3 and the reporting corrections are documentation edits measured in minutes.
4. C1 has the highest ratio of demonstrable value to effort. It is about 30 minutes of
   compute plus API spend, and it moves the product surface from 1 of 40 populated to
   something a reader can scroll.
5. C2 and C3 are the generalization evidence. They are the answer to "does this work on
   anything other than the dataset you built it on".

## Appendix: measured results, 2026-09-03

Three experiments were run against the frozen split, each adversarially verified by two
independent agents (a leakage lens and an arithmetic lens). Where a verifier recomputed a
number, the corrected value is the one given here. No repo file was modified by any
experiment, and no leakage was found in any of them.

### What survives an honest evaluation, and what does not

The candidate universe is 8,357 untested bait-human pairs. The published numbers were
computed over the 115 pairs L3 reaches, which is 1.4% of that universe. This is the
restricted-negative setting.

| metric | published | honest full universe | status |
|---|---|---|---|
| precision@10 | 0.300 | 0.300 | survives unchanged |
| precision@20 | 0.450 | 0.450 | survives unchanged |
| precision@50 | 0.260 | 0.260 | survives unchanged |
| recall@50 | 0.9286 | 0.2281 | does not survive. 0.9286 is 13 of 14 reachable, not 57 |
| ROC-AUC | 0.8451 | 0.6178 tie-aware | does not survive. Null ranker scores 0.5000 |
| average precision | 0.3733 | 0.1039 | does not survive |

Precision@k is mathematically invariant to expanding the negative set when the top-k is
unchanged, which is why it holds. Maximum achievable recall@50 against 57 positives is
0.8772, so the published 0.9286 was provably not a global figure.

### L2 versus L3

All four common-neighbour variants reach 20 of 57 held-out edges. L3 reaches 14.

| result | finding | statistical support |
|---|---|---|
| CN reaches more held-out edges than L3 | 20 of 57 vs 14 of 57, 6 discordant to 0 | McNemar exact p = 0.0312, robust |
| CN beats L3 on precision@20 | 10 hits vs 9, one discordant pair | McNemar exact p = 1.000, no support |
| CN doubles L3 at precision@10 | artifact. CN has 4 distinct scores over 92 pairs, so alphabetical tie-breaking decides its top-k. Published 0.600 sits at the 97.9th percentile of tie-break outcomes, expectation 0.464 | not a real 2x. Honest ratio 1.55x |
| Adamic-Adar and RA tie L3 at k=20 | wrong. Expectation 0.387 versus L3's 0.450, so they lose | reported value sat at the 94.7th percentile |
| Degree product (hub-bias null) | below chance | held-out edges attach to lower-degree nodes than average, so hub bias is not inflating our numbers |

The load-bearing finding is the ceiling, not the ranking. 28 of the 57 held-out preys have
degree 0 in the training graph, because their only Gordon edge was the one held out. The
union of all five topology scorers reaches 20 of 57, so 37 of 57 positives are structurally
unrecoverable by any local-topology method on this split.

### The reachability ceiling and the STRING threshold

The mechanism is confirmed exactly. Mean prey STRING degree at score>=700 is 0.958, and 196
of 332 preys have no STRING partner at all. An offline predicate, "the held-out prey sits at
STRING distance exactly 2 from a surviving prey of the same bait", predicts L3's actual
reachability perfectly at every threshold tested: 14, 17, 21, 27, 48.

| STRING threshold | enrichment edges | reachable of 57 | p@10 | p@20 | AUC tie-aware | AP |
|---|---|---|---|---|---|---|
| 700 (current) | 159 | 14 | 0.30 | 0.45 | 0.6178 | 0.1039 |
| 600 | 189 | 17 | | | 0.6420 | 0.1068 |
| 500 | 238 | 21 | | | 0.6713 | 0.1185 |
| 400 | 347 | 27 | 0.40 | 0.40 | 0.7107 | 0.1509 |
| 150 | 1232 | 48 | 0.50 | 0.35 | 0.7876 | 0.1287 |

Reachable sets are strictly nested, so loosening only ever adds. The first run of this
experiment concluded that loosening costs AUC and AP, but a verifier showed that was an
artifact of a denominator that shrinks with the threshold: the locked evaluator scores only
the proposal list, so at 700 it silently drops 43 of the 57 positives before computing AUC.
Holding the universe fixed at 8,357 pairs reverses both metrics. AUC rises monotonically as
the threshold loosens, and AP peaks at threshold 400 with the current 700 the worst of the five.

Score 700 is therefore not the optimal operating point. Threshold 400 improves reachability,
precision@10, AUC and AP simultaneously, and costs 0.05 on precision@20.

Nine of the 57 remain unreachable even at threshold 150, so a residual ceiling exists that
no enrichment setting removes.
