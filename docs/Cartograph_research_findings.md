# Research findings: state of the art, prior art, and what changes

Source: a Claude Science literature review commissioned 2026-09-03, delivered as
`docs/cartograph_soa_review.md` (about 9,100 words), `docs/ppi_prediction_bibliography.csv`
(88 records) and `docs/ppi_benchmark_datasets.csv` (18 datasets). Every DOI in the review was
retrieved from PubMed, arXiv or Crossref and checked against the retrieved record.

This file records what the review found, what it got wrong about our own code, and the
resulting plan. Measured numbers live in the appendix of `Cartograph_gap_audit.md`. The two
files are meant to be read together.

## Bottom line

The predictor is not where the risk is. The evaluation is.

Degree-normalized L3 is a defensible, domain-appropriate baseline. It placed in the top six
of 26 methods in the one large independent benchmark, run by the International Network
Medicine Consortium across six interactomes, where L3-principle methods were top-tier and
generic deep learning was robust but not top-ranking. The three methods that beat plain L3
are all L3 derivatives, and the best wet-lab-validated one, at 87.4% precision on its top 500,
was L3 plus a sequence term. That is direct support for a fusion architecture.

The reportable errors are all in evaluation, and a reviewer finds them in about ninety seconds.

## Corrections to our framing

Eight assumptions we were operating on turned out to be wrong. The first two are the
consequential ones.

1. **Common neighbours is available to us, and was our most important missing baseline.**
   A strictly bipartite bait-prey graph has no common neighbours, because every bait-prey path
   has odd length. Adding 159 STRING prey-prey edges breaks that. The path bait to prey' to
   prey is length 2 and prey' is a genuine common neighbour. So CN, RA and Adamic-Adar all
   exist in our enriched graph. We had been asserting they did not.

2. **Zero shared preys makes every prey degree 1, and that determines almost everything.**
   The AP-MS layer is a disjoint union of 26 stars. Removing a held-out edge deletes that
   prey's only AP-MS edge, so the prey is orphaned at test time. Every length-3 path must be
   AP-MS then STRING then STRING, because the alternative route through a shared prey does not
   exist. Reachability is therefore a pure property of the STRING layer.

3. **Degree normalization means something different in our graph than in the paper it comes
   from.** L3 assumes a homogeneous network where degree proxies promiscuity. Our intermediate
   nodes mix AP-MS degree (viral bait promiscuity) with STRING degree (functional hubness).
   These are different quantities on different scales. Needs an ablation with and without.

4. **There is no Krogan-lab Mpox AP-MS map.** Published mpox interactomes are computational
   predictions: Kumar et al. 2023, Paul et al. 2024, and the HuPoxNET predicted atlas
   (Kataria et al. 2024). An earlier roadmap item named Mpox as an apples-to-apples comparison.
   The apples would have been predictions. Item dropped.

5. **Cross-coronavirus data exists and we already have it.** Gordon et al. Science 2020 covers
   SARS-CoV-2, SARS-CoV-1 and MERS-CoV. Batra et al. 2026 covers SARS-CoV-2 against its bat
   progenitor RaTG13 in both human and bat cells. See the conservation section below, where the
   review is itself wrong about what we have built.

6. **The pooled-AlphaFold3 paper is Todor et al. 2026, Mol Syst Biol, DOI
   10.1038/s44320-026-00189-7.** We had been citing an author name that does not exist on it.
   We feature this paper in positioning, so the wrong name is a visible credibility hit.

7. **ROC-AUC is not "criticised" or invalid.** The precise modern statement, from Bi, Jiao, Lee
   and Zhou 2024 across hundreds of real networks and 26 algorithms, is that no single metric is
   sufficient and that metrics disagree about which algorithm wins. Report at least two. Keep
   AUC, never alone, never as headline.

8. **Our structure channel's 0.0 aggregate gain is a coverage result, not a null result about
   structure.** Only 3 pairs on this map have a deposited complex. The honest statement is that
   the channel could not be tested at this coverage, not that structure does not help.

## Where the review is wrong about us

The review states we have been "declining to build" a conservation column. That is aimed at
`CLAUDE.md`'s cut list, which is stale. The column is fully built.

`backend/conservation/conserve.py` reads `evidence/gordon2020_science_cov1_mers_edges.csv`,
which holds 662 rows: 366 SARS-CoV-1 edges over 24 viral proteins and 296 MERS-CoV edges over
22 viral proteins. It resolves four never-collapsed states (conserved, not_conserved,
no_ortholog, not_screened) and is wired into `build_artifact.py` in seven places, including a
scored evaluator channel. Measured over all 332 CoV-2 edges: SARS-CoV-1 gives 111 conserved,
209 not conserved, 9 no ortholog, 3 not screened; MERS gives 30, 175, 107, 20. 118 of 332
CoV-2 edges are conserved in at least one strain.

The fix is to `CLAUDE.md`, which misled the reviewer, not to the code.

What is genuinely missing from that channel is more interesting than what the review asked for:

- It cannot move recall. `conserve.scores(pairs, boost=0.5)` only re-ranks inside L3's existing
  pool. `n_targets_recoverable` stays at 14 and `n_proposals` stays at 115. 20 of the 57
  held-out edges are conserved and would be boosted, but only those already reachable benefit.
- **Conservation transfer used as a candidate GENERATOR reaches 20 of 57 held-out edges against
  L3's 14, with only 9 shared.** This is an unexploited channel that raises the ceiling rather
  than reordering beneath it.
- The CoV-1/MERS edges are never used as an independent prospective target set.
- No Batra 2026 RaTG13 data, which would add a fourth strain and a host axis.

Two smaller notes: orthology is a hand-maintained table, not sequence-derived, and 101 of the
662 rows can never match a CoV-2 bait name, correctly, since MERS has no SARS accessory ORF
orthologs.

## Baselines, measured

Run against the frozen split. Read the tie-breaking caveat below before quoting any of it.

| scorer | pool | reaches of 57 | p@10 | p@20 | p@50 | AP |
|---|---|---|---|---|---|---|
| L3 (shipped) | 115 | 14 | 0.30 | 0.45 | 0.26 | 0.373 |
| CN (common neighbours) | 92 | 20 | 0.60 | 0.50 | 0.30 | 0.458 |
| Resource allocation | 92 | 20 | 0.50 | 0.45 | 0.34 | 0.467 |
| Adamic-Adar | 92 | 20 | 0.50 | 0.45 | 0.34 | 0.456 |
| **STRING best-score guilt-by-association** | | | **0.80** | **0.60** | **0.36** | **0.681** |
| Preferential attachment (degree null) | 8357 | 57 | 0.00 | 0.00 | | 0.008 |

Two findings and one caveat.

**The finding that matters most: a one-line STRING score lookup, with no path machinery at
all, beats L3 on every precision cut and on average precision.** Given that every L3 path in
our map traverses two STRING edges, the null hypothesis that L3 contributes nothing beyond
STRING is live and is not yet refuted. This is the single result most likely to be found by a
reviewer in minutes.

**The reachability finding is robust and the precision findings are not.** Every CN variant
reaches 20 of 57 and the L3-only set is empty: every edge L3 reaches, CN also reaches, plus six
more (M-ETFA, M-PMPCB, Nsp10-AP2A2, Nsp7-RAB8A, Nsp8-MEPCE, Orf8-SIL1). McNemar exact on
reachability gives p = 0.0312. McNemar exact on the precision@20 difference gives p = 1.000.

**Caveat, from adversarial verification:** CN has only four distinct scores across 92 pairs, so
alphabetical tie-breaking decides its entire top-k. The published CN precision@10 of 0.600 sits
at the 97.9th percentile of tie-break outcomes; its expectation is 0.464. The Adamic-Adar and RA
rows reported as tying L3 at k=20 lose to it in expectation. The STRING-GBA row has continuous
scores and is less exposed to this, but it has not been separately tie-audited. Treat every
precision number in this table as provisional until recomputed with mid-rank tie handling.

Preferential attachment scoring below chance is a genuinely useful defensive result: held-out
edges attach to lower-degree nodes than average, so the standard hub-bias objection to PPI link
prediction does not land on us.

## Evaluation methodology

- **All 57 held-out pairs are class C2** in the sense of Park and Marcotte 2012, which defines
  classes by how much of a test pair was seen in training: C1 shares both proteins, C2 shares
  one, C3 shares neither. Because every prey has AP-MS degree 1, holding out a pair removes the
  prey's only AP-MS edge. Typical random cross-validation is more than 99% C1, which is the easy
  class, while at population level C1 is only 19.2% of possible human pairs. **Our split is
  harder than the norm and matches our deployment population. Say so.** The cost is that we have
  no C1 or C3 stratum, so we cannot claim generalisation to preys outside the map.
- **Pooled metrics measure bait promiscuity.** Yilmaz et al. 2025 show uniform random edge
  sampling biases test sets toward high-degree nodes and that the bias survives temporal
  holdout. Report per-bait or bait-degree-weighted metrics and publish the bait-degree
  distribution of the held-out set.
- **Metric policy:** precision@k primary, AUPRC as a required second, prevalence printed next to
  every precision number, and the maximum attainable value of each metric stated.
- **Keep implicit negatives.** Do not "improve" the negative set by filtering it.
- **The one leak that applies to us:** the node set is derived from the unsplit edge list, so
  every answer is guaranteed to sit inside a 332-protein pool. This inflates precision@k
  uniformly and means 0.45 is not a proteome-scale number.
- **STRING text-mining creates circularity** between our enrichment layer and our literature
  layer, and the committed cache cannot answer whether it bites, because it stores only
  post-filter edges without channel breakdown.

## Prior art, and the positioning change

Two systems already occupy parts of the space we were claiming:

- **PrePPI** has done the structure-plus-evidence half at proteome scale: roughly 1.3 million
  ranked human predictions on a public server.
- **P-HIPSTer** did about 282,000 pan-viral-human structural predictions in 2019 with a reported
  76% validation rate. It predates this project by seven years and is the closest published
  thing to our problem. It must be a comparator, and it must never be used as ground truth.

So "we predict missing PPIs" and "ranked predictions with evidence" are both taken. What is not
in the prior art:

1. A locked, pre-registered benchmark reported per map, with the split frozen before the
   predictor was written and a test proving the predictor cannot import the evaluator.
2. A deterministic citation gate: no citation, no render.
3. Structure-derived interface residues computed from deposited coordinates rather than copied
   from prose, with predicted models always labelled predicted.
4. The triage framing, which is well timed: pooled AlphaFold3 makes genome-scale candidate lists
   cheap (Todor et al. 2026) exactly when the experimental assessment says AI cannot yet do the
   discovery (Lambourne et al. 2026, whose yeast map found over 40-fold more novel PPIs than its
   AI counterpart, while AlphaFold supplied structures for interactions the screens missed).

The review also notes that community-assessment infrastructure barely exists in this subfield,
so there is room for a standing, versioned benchmark, and that is closer to what we have built
than a prediction method is.

**The positioning change: lead with the harness, not the predictor.** Treat L3 as one channel
among several and let the contribution be that every channel is scored against the same locked
benchmark and every claim carries a verified citation.

## Datasets

Ranked shortlist, from the review and the CSV:

1. **Gordon 2020 Science (SARS-CoV-1 + MERS-CoV)** already committed to the repo. Run first.
2. **Haas 2023 influenza A** the cleanest paired second map.
3. **Jager 2011 HIV** the one that breaks the degree-1 pathology, so it tests whether our
   findings are artifacts of the star topology.
4. **Shah 2018 flavivirus (DENV/ZIKV, human and mosquito)** conservation test bed.
5. **Batra 2026 SARS-CoV-2 vs RaTG13 (human and bat cells)** conservation with a host axis.
6. **Penn 2018 Mtb** sparsity stress test.
7. **Davis 2015 KSHV** largest bait set among the bipartite maps.
8. **HuRI, then BioPlex 3.0** the dense human-human comparators.

Avoid or handle with care:

- **STRING as ground truth.** Acute circularity, since we use it as a feature. The INMC
  benchmark also shows it is the only interactome on which methods score non-trivially.
- **OGB, BioGRID, HIPPIE, IID, hu.MAP, CORUM** each carry a different silent label mismatch.
- **P-HIPSTer** is the mpox trap at scale: predictions, not measurements. Comparator only.
- The INMC six-interactome suite is the de facto standard and is missing from the CSV.

Licensing could not be verified from the literature, because licences live on resource sites
rather than in papers. CORUM and STRING attribution are the specific exposures, given that we
redistribute a cached STRING subset.

## Predictor guidance

- **Do not adopt a learned link predictor.** 358 nodes and 491 edges have nothing to learn.
- **Do not upgrade L3 yet.** Ran et al. 2024 show all indices built on the same feature share
  one ceiling, so a better length-3 index cannot rescue a map where only 14 of 57 held-out edges
  are reachable. Measure the ceiling first, swap only if not already near it.
- If a swap is eventually justified, MPS(T) and RNM have the best independent track record
  (Wang et al. 2023). Cannistraci-Hebb variants are real and peer-reviewed, but the "beats L3"
  claim is single-group.
- L3-based and general-purpose predictors rank different pools, which argues for a portfolio of
  channels rather than a single champion. That is the same conclusion the positioning reaches.
- **ipTM and pDockQ are model-quality scores being misused as interaction classifiers.** Well
  replicated. Our size correction should be described as summed-chain-length dependent, with the
  fitted functional form stated.
- **Do not bet the product on protein language models yet.**

## Next steps

Ordered. This supersedes the sequencing section of `Cartograph_gap_audit.md`.

**1. Fix the candidate universe and re-report everything.** Define one candidate set explicitly,
compute every metric on it, and publish the arithmetic next to each number: prevalence,
enrichment over prevalence, and the maximum attainable value. This resolves both the
recall@50 = 0.93 impossibility and the ROC-AUC tension. Add an open-world variant against a
proteome-scale background, because that is the deployment population. State explicitly that all
57 held-out pairs are class C2 and that C3 is unmeasured.

**2. Add the baselines and stratify by bait degree.** Random, preferential attachment, CN, RA
and Adamic-Adar at L2, and above all the STRING-score-only guilt-by-association control, which
gates our central claim. Recompute every precision number with mid-rank tie handling, since the
current baseline table is tie-inflated. Report per-bait or degree-weighted metrics. Make
precision@k primary with AUPRC required. Bootstrap the median-rank-2 result, which rests on 14
events.

**3. Run on more than one map.** Ship the reachability-versus-precision threshold sweep as a
figure, which is a few hours of work and is the most informative plot in the project. Extend the
STRING background past the 332 preys. Then run the full pipeline on HIV (Jager 2011), Mtb
(Penn 2018) and influenza A (Haas 2023).

**4. Build the prospective test.** Score the frozen 2020-derived predictions against SARS-CoV-2
edges curated since 2020 in IntAct/IMEx, plus the Gordon Science 2020 CoV-1/MERS maps and Batra
2026. These edges were not in the training graph and were not used to build it. The review calls
this "the single most persuasive number you could add, and it is immune to every objection about
split construction." Pair it with degree-aware weighting.

**5. Make conservation a candidate generator.** It reaches 20 of 57 against L3's 14 with only 9
shared, so it raises the ceiling instead of reordering beneath it. Also state plainly in the eval
panel that the L3-plus-conservation gain comes from an external dataset containing some of the
answers. That is legitimate corroboration rather than leakage from the frozen split, but a
reviewer will ask.

**6. Move the STRING threshold from 700 to 400.** Measured: reachability 14 to 27, precision@10
0.30 to 0.40, tie-aware AUC 0.618 to 0.711, AP 0.104 to 0.151, costing 0.05 on precision@20.
One line of config with evidence behind it.

**7. Hygiene, alongside rather than first.** Parameterize the evaluator over graph, split and
predictor. This was previously sequenced first as a blocker. It is not one: the training graph
builder and metric helpers are already importable, and six baselines were run without touching
the evaluator.

Deliberately not on this list: replacing L3, adopting a learned predictor, protein language
models, and any auth, tenancy or billing work.
