# Cartograph

The navigation layer for a protein interaction map. Cartograph loads an
experimentally-derived interactome, **deterministically proposes the edges that
should be there but are not yet drawn**, proves each one with the literature and
a 3D structure, and **measures how often it is right against a locked held-out
benchmark of real edges**.

Built with Claude: Life Sciences (Anthropic x Gladstone). Build track, solo. Open source (MIT).

![the flagship dossier: Orf6 -> RAE1, recovered by topology, confirmed by the experimental 7VPH structure](docs/demo_dossier.png)

## The one-screen demo (runs offline, reproducibly)

```bash
./run.sh            # builds the computed artifact, then serves the demo
# open http://127.0.0.1:8791/index.html
```

`run.sh` creates the venv, installs `requirements.txt`, freezes the locked
evaluator split, loads the cached STRING enrichment, computes the artifact, and
serves the single-page app. The demo makes **zero live network calls** — every
structure, citation, and number is baked in at build time.

The 3-minute path:
1. **Ask the map** — "what interaction is Orf6 missing?"
2. **Deterministic L3** walks a genuine length-3 path `Orf6 → NUP98 → NUP214 → RAE1` and proposes the missing edge `Orf6 → RAE1`.
3. **Structural dossier** opens: the real experimental structure (PDB **7VPH**) in Mol\*, structure-derived interface residues (E55 / M58 / D61), a mechanism where **every clause opens to a real PubMed paper**, and a proposed wet-lab test.
4. **Locked evaluator** runs in-map: real held-out Gordon edges snap green, misses flash red, and the honest precision shows — **precision@20 = 45%** against a prevalence of 0.68% on 8,357 untested pairs, a 66x enrichment. (That is one split. Over 20 seeds the mean is 0.32; and on this map a one-line STRING lookup beats it. Both facts are below.)
5. **One loop round**: confirm the recovered-true edges, fold them back, re-score the still-hidden edges — **precision@20 0.30 → 0.35** on the remainder.

![the locked evaluator running in-map: held-out Gordon edges snap green, misses flash red, and every metric opens to its own arithmetic: value, maximum attainable, and the prevalence floor it is measured against](docs/demo_evaluator.png)

## The honest headline numbers (computed, not illustrative)

Every metric is computed over one stated candidate universe: the **8,357** untested
viral-bait to human-prey pairs, containing **57** held-out positives. Prevalence is
therefore **0.68%**, and that is the floor each number below is measured against.

| metric | L3 | STRING-GBA | max attainable | vs the floor |
|---|---|---|---|---|
| precision@10 | 0.30 | **0.80** | 1.00 | 44x / **117x** prevalence |
| precision@20 | 0.45 | **0.60** | 1.00 | 66x / **88x** prevalence |
| precision@50 | 0.26 | **0.36** | 1.00 | 38x / **53x** prevalence |
| recall@50 | 0.23 | **0.32** | 0.88 | 13 / 18 of 57 |
| ROC-AUC (tie-aware) | 0.62 | **0.67** | 1.00 | 0.50 null ranker |
| average precision | 0.10 | **0.25** | 1.00 | 0.007 null ranker |
| held-out edges reached | 14 | **20** | 57 | of 57 |
| flagship `Orf6–RAE1` | recovered, L3 rank 7/8 | | | via genuine length-3 path |

**Read that table again: on this map the deterministic L3 predictor loses to a one-line
STRING lookup on every single metric.** STRING-GBA scores a candidate by the best STRING
score linking it to a prey the bait already binds. No path machinery at all
(`backend/predict/gba.py`). That result is published here rather than buried because the
benchmark exists to surface it.

**And the single number is a favourable draw.** `precision@20 = 0.45` is one split. Resampling
the same 17% held-out protocol over 20 seeds gives **mean 0.32, sd 0.10, range 0.15 to 0.55**,
with only 2 of 20 draws reaching 0.45. Quote the distribution, not the draw.

### When is L3 worth running at all?

Measured across five AP-MS interactomes, ten map variants, in two regimes
(`docs/Cartograph_multimap_bakeoff.md`, reproduce with `python -m backend.bench.bakeoff`):

| map | shared preys | L3 reach | STRING-GBA reach | advantage | 40 paired seeds |
|---|---|---|---|---|---|
| Penn 2018 Mtb | 0.0% | 17.9% | 27.6% | **-9.7pp** | L3 wins 0/39 |
| Gordon 2020 SARS-CoV-2 | 0.0% | 19.2% | 26.7% | **-7.4pp** | L3 wins 1/39 |
| Jager 2011 HIV-1 | 14.9% | 47.5% | 37.8% | **+9.7pp** | L3 wins 40/0 |
| Haas 2023 influenza A | 23.8% | 55.7% | 42.3% | **+13.4pp** | L3 wins 39/1 |

And out of regime, on human-human BioPlex 3.0 293T subsamples (no pathogen at all):
4.3% sharing gives +0.4pp (not significant), 12.1% gives +4.5pp, 22.2% gives **+10.3pp**.

Pearson r = 0.90 over all ten variants, monotonic within every dataset. Strict monotonicity
does not survive the regime change: the pathogen-host curve runs above the human-human one at
matched sharing, so prey sharing predicts the sign and the trend, not the magnitude. The mechanism is direct: shared preys
open a `bait → prey → bait' → prey` route that is length-3 and therefore invisible to any
length-2 method. Of the held-out edges L3 reaches that STRING-GBA cannot on Jager, **85%
travel exactly that route**, and 72% on BioPlex. On Gordon the count is **zero**.

So the deployment rule is a one-line pre-flight check (`backend/bench/sharing.py`): compute
**mean prey degree** before scoring anything. At 1.000 the route does not exist and the
STRING lookup wins. Above about 1.05 to 1.15, L3 becomes the best recall channel in the panel. Gordon
sits at exactly 1.000, which is why this repo's flagship map is the one topology helps least
on, and the built artifact says so in `eval.channel`.

Against an open-world background of the reviewed human proteome (UniProt release
2026_03, 20,431 proteins) the universe is 531,206 pairs and prevalence falls to
0.011%, so the enrichment is far larger again. Precision@k is unchanged by that
widening; prevalence and enrichment are not.

**Two earlier figures were wrong and are corrected above.** A previously published
recall@50 of 0.93 used a denominator of the 14 reachable edges rather than all 57;
the global value is 0.23, and 57 positives into 50 slots caps recall@50 at 0.88 in
any case. A previously published ROC-AUC of 0.845 was computed over the 115 pairs L3
reaches, which is 1.4% of the untested universe, and is a restricted-negative
setting. Both restricted figures are still published in the artifact under
`eval.baseline` so the correction can be audited rather than taken on trust.

Only 14 of 57 held-out edges are reachable by a length-3 path at all. Every
common-neighbour variant reaches 20, and the union of all local-topology scorers is
also 20, so 37 of 57 are unrecoverable by any such method on this split. When L3 can
reach a held-out edge, its median rank among its bait's candidates is **2**.

All 57 held-out pairs are class **C2** in the sense of Park and Marcotte 2012: the
bait is seen in training, the prey is not. Typical random cross-validation is over
99% C1, the easy class, so this split is harder than the norm. C3, where neither
protein is seen, is unmeasured and no generalisation to it is claimed.

## Integrity rules (non-negotiable, and enforced by tests)

- **Deterministic critical path.** The graph proposes edges via degree-normalized L3 (`backend/predict/l3.py`). Claude reads, adjudicates, explains. Claude never invents an edge from model weights.
- **Eval-first, locked, separate.** The held-out split was frozen and committed as the **first commit**, in `backend/eval/`, with a sha256 checksum. A test (`test_no_import_of_locked_evaluator`) proves the predictor and reasoning layers cannot import it.
- **No citation, no render.** Every mechanistic clause references a PMID that must exist in the verified edge pack; if it does not, the clause is dropped (`backend/reason/hypothesis.py`).
- **Predicted is always labeled predicted.** Experimental structures (7VPH, 7DHG) and predicted models (AlphaFold, with a real pLDDT) are never conflated.
- **Interface residues are structure-derived**, computed from the deposited coordinates (`backend/structure/interface.py`), not copied from prose. The prototype's wrong ORF9b S55/K46 were repaired to the real contacts S53/R58/E65.

## Architecture

One deterministic engine, exposed as a computed artifact the frontend loads.

```
backend/
  config.py         single source of truth (seed, STRING pin, demo edges)
  graph/            load.py (332 edges/26 baits), enrich.py (STRING v12.0, cached)
  predict/          l3.py — degree-normalized L3 (Kovacs 2019), deterministic
  eval/             LOCKED: freeze_split.py + heldout.frozen.json (committed first),
                    evaluator.py (precision@k / recall / ROC-AUC / AP)
  reason/           hypothesis.py — Reader / Skeptic / Curator, no-citation-no-render
  structure/        interface.py (contacts from coords), resolve.py (dossier blocks)
  bench/            candidate universe, tie-aware metrics, metric records that always
                    carry their denominator, sharing.py (the pre-flight statistic) and
                    bakeoff.py (the four-map comparison). Predictor- and dataset-agnostic.
  predict/gba.py    STRING best-score guilt-by-association: the control that wins here
  build_artifact.py runs the whole engine -> frontend/data/cartograph_computed.json
  tests/            153 tests: counts, determinism, L3, eval, boundary, honesty
frontend/           index.html + app.js + style.css (Cytoscape + Mol*), vendored libs
evidence/           (provided) ground truth + cited packs + domain priors
```

Data flow: `gordon2020_edges.csv` → networkx graph → STRING enrichment → L3
candidates → locked evaluator scores them → reasoning layer assembles cited
dossiers → `build_artifact.py` freezes it all into one JSON → the frontend
animates the demo.

## Beyond the core (Phase 2)

All optional, none on the critical path; the offline static demo is the guaranteed fallback.
- **Ranked testable hypotheses** — the worklist is a triage of the top predicted edges, each a testable interaction with a **novelty tag grounded in a real PubMed co-mention count** (novel = 0 co-mentions; known = a recovered Gordon edge or cited pack), the **Skeptic verdict** (AP-MS frequent-flyer filter), a **structural band only where a real structure exists** (no fabricated ipTM), real druggability, and the single next experiment. Sortable/filterable, CSV export.
- **Held-out transparency** — every one of the 57 held-out edges as recovered/missed with its L3 rank and length-3 path, and the reachability ceiling.
- **Bring-your-own-interactome upload** (needs the API) — your edge-list → STRING enrichment → L3 → optional **own** held-out eval on a **separate seed**; uploaded data never touches the locked benchmark.
- **Evidence Agent** (needs the API) — for any predicted edge on an uploaded map, a live, cited, **code-verified** dossier: identifiers resolved (UniProt), literature + a real deposited structure + druggability retrieved (NCBI / RCSB / AlphaFold / Open Targets), Claude reads, and a **deterministic Stage-4 gate re-checks every citation** (closed-set + resolve + title-match; a PDB must actually contain both accessions). Streamed over SSE as a live trace; degrades honestly to topology-only on any failure or without a Claude key; **no citation, structure, residue, or drug is ever fabricated**. Conservation/CRISPR read "not applicable" for non-coronavirus organisms.
- **Pooled-AlphaFold3 virtual screen** (needs the API) — upload a symmetric protein×protein **ipTM matrix**; Cartograph **size-corrects** ipTM (it rises with summed chain length), thresholds to candidate edges, bands each (predicted, labelled), and runs the L3 topology channel to catch edges the folds may have missed. Every ipTM is labelled predicted; nothing is fabricated; not added to the locked benchmark.
- **Structural evidence channel** — deposited complexes (7VPH, 7DHG) fuse into the evaluator as a transparent additive boost. Reported **honestly**: excluding the self-referential pinned edge, the aggregate precision gain is **0.0** on this small map — the channel corroborates individual hypotheses, it does not inflate the headline (see below).
- **Human-in-the-loop feedback** — record confirmed / to-test / refuted + a lab note per dossier; verdicts persist locally, **fold back onto the map** (confirmed → green edge), and export/import as JSON. The human half of the loop; never touches the benchmark.
- **Live druggability + repurposing** — real Open Targets (data 26.06) tractability + known drugs per host target; a target with an approved drug is flagged a **repurposing lead** (a *hypothesis*, not a validated antiviral). Committed snapshots make the offline demo show real, dated data with no live call; `/api/druggability` fetches uncached targets live.
- **Interoperable export** — the whole map as **CX2** (open in Cytoscape / upload to NDEx), and the ranked hypotheses as a structured **Claude Science handoff** JSON (mechanism, citations, novelty, Skeptic, experiment, provenance).
- **FastAPI + SSE** wrapper over the engine; **dossier → self-contained HTML report** export.

## Where this is going: the triage layer for cheap PPI maps

Pooled-AlphaFold3 (Anlin/Todor, *Mol Syst Biol* 2026) makes genome-wide PPI maps
cheap to generate — but a screen that proposes thousands of pairs needs a triage
layer that decides **what to test first**, with the evidence to justify it.
Cartograph is that layer: deterministic topology proposes, Claude explains with
real literature, a locked benchmark keeps everyone honest, and now a structural
channel ingests real fold confidence (never fabricated). The honest finding on
this 332-edge map: **structure corroborates per-hypothesis but does not raise
aggregate precision** — exactly the kind of result the locked evaluator exists to
surface rather than hide.

### Roadmap (not built — deliberately scoped out of the hackathon)

Honest about what is *not* here yet, and why each is a real next step, not vapor:
- **Live pooled-AlphaFold3 folding** — Cartograph ingests an ipTM matrix today; the next step is to *drive* the fold jobs for the top-ranked candidate pairs on a GPU and stream ipTM back into the same channel. The size-correction and banding are already in place for it.
- **Active-learning loop** — use the locked evaluator + reviewer verdicts to choose which pairs to fold/test next (expected-information-gain ranking), instead of folding the whole matrix. The human-in-the-loop feedback is the first half of this.
- **Multi-user realtime** — several biologists annotating one map at once (verdicts are local-only today); needs a shared store and presence.
- **Cross-species conservation** — a real conservation column would need cross-coronavirus (SARS-CoV-1, MERS) PPI data we do not have; it is intentionally omitted rather than fabricated.
- **Hyperbolic / learned embeddings** — L3 is a strong deterministic baseline; a learned link-predictor (kept deterministic at inference) could raise recall on the long tail, scored against the same locked benchmark.
- **Chemical & functional genomics** — fold in CRISPR-screen hits and compound-perturbation data as additional orthogonal channels behind the same evaluator.

Each stays behind the same non-negotiable: the graph proposes, Claude explains with real literature, and a locked benchmark keeps the number honest.

## Commands

```bash
./run.sh            # build + serve the OFFLINE static demo (no API)
./run.sh api        # build + serve the demo WITH the live API (adds upload)
./run.sh build      # just rebuild frontend/data/cartograph_computed.json
./run.sh test       # run the test suite (153 tests)
```

Reproducibility: the STRING enrichment is pinned to v12.0 (physical channel,
score ≥ 700) and cached in `evidence/`; the held-out seed is 42; the computed
artifact is **byte-identical across runs** regardless of Python's hash seed.
Network is needed exactly once (STRING + the three structures) and the results
are committed so the demo runs offline forever after.

## What is real vs. what is a disclosed simplification

- **Real:** the graph, the STRING enrichment, the L3 predictor, the locked evaluator and every number it reports, the two experimental structures (7VPH, 7DHG) and their computed interface residues, every citation (verified against NCBI), the AlphaFold-predicted G3BP1 model and its pLDDT, the worklist **novelty tags** (grounded in real NCBI PubMed co-mention counts, cached), the **size-correction** of any uploaded ipTM matrix, and the Open Targets druggability snapshots (data 26.06).
- **Disclosed simplification:** the reasoning-layer mechanism prose is Claude-authored at build time, grounded strictly in the verified packs (no live API on the demo path). The N–G3BP1 3D is the predicted G3BP1 *monomer* (the complex is not deposited), labeled predicted, with no fabricated contact residues. The map renders a real induced subgraph of the flagship neighborhoods for legibility; the headline metrics are computed on the full held-out set.

## License

MIT. All work produced during the hackathon.
