# Recent literature map: host–pathogen PPI networks & interactome link prediction

*Scope: the subfield surrounding **Cartograph** — predicting missing edges in an
experimentally-derived interactome and generating literature-cited mechanistic
hypotheses, benchmarked on the SARS-CoV-2–human map. Built from an OpenAlex
sweep (2018–2026, citation- and recency-sorted) across seven threads, curated
down to 40 anchor papers. Full table: `cartograph_literature_map.csv`.*

![Literature landscape]({{artifact:d90b2857-ce75-48cd-b503-46a826935abb}})

*Marker area ∝ citation count. Rows in bold (link-prediction methods; AI/LLM over
PPI) are Cartograph's methodological core. The visual story: the biology threads
(interactome, CRISPR, network medicine) are dense and heavily cited but front-loaded
in 2020–2022; the AI/LLM-over-PPI thread is recent and thinly cited — an open lane.*

---

## The one-paragraph picture

The SARS-CoV-2 interactome is one of the most intensively mapped host–pathogen
systems in biology. The foundational layer — the AP-MS interactome, the
genome-wide CRISPR host-factor screens, and the network-medicine repurposing
analyses — was largely laid down in a ~24-month burst (2020–2022) and is now
mature and highly cited. Two threads that Cartograph depends on are, by
contrast, still moving: **network-based link prediction** (the degree-normalized
L3 lineage) matured in 2018–2022 but has not been systematically applied to the
COVID interactome for hypothesis generation; and **LLM-driven synthesis over PPI
literature** is nascent (papers from 2023–2025, citation counts in the single
digits). Cartograph sits precisely at the intersection of those two live
threads, on top of the mature biology.

---

## Thread 1 — The SARS-CoV-2 interactome (the substrate)

- **Gordon et al. 2020, *Nature*** — *A SARS-CoV-2 protein interaction map reveals
  targets for drug repurposing* (doi:10.1038/s41586-020-2286-9). The demo dataset:
  26 viral baits, 332 high-confidence AP-MS interactions in HEK293T, mined for
  druggable host targets. This is Cartograph's ground-truth graph.
- **Gordon et al. 2020, *Science*** — *Comparative host-coronavirus protein
  interaction networks reveal pan-viral disease mechanisms*
  (doi:10.1126/science.abe9403). Extends the map to SARS-CoV-1 and MERS; the
  cross-viral conservation of interactions is a strong prior for which held-out
  edges *should* be recoverable.
- **Complementary interactome maps** extend the substrate beyond protein–protein
  AP-MS: Schmidt et al. 2020 (*Nat Microbiol*) and follow-ups map the SARS-CoV-2
  **RNA–protein** interactome in infected cells, and Horlacher et al. 2023 give a
  computational human–SARS-CoV-2 protein–RNA map. These are orthogonal edge types
  Cartograph could fold in later, but they are not the AP-MS benchmark graph.

**Read for Cartograph:** the interactome is small, sparse, and bipartite
(viral→human) at its core — which is exactly why enriching with human–human
STRING edges (to create length-3 paths) is necessary for L3 to have signal.

## Thread 2 — CRISPR host-factor screens (your external validation set)

Four genome-wide screens published within weeks of each other in late 2020
(*Cell*), plus two 2021 follow-ups, are the canonical independent host-factor
evidence. These are the **strongest candidates for external validation** — genes
that score as SARS-CoV-2 host factors by loss-of-function but were *not* AP-MS
baits/preys are exactly the "missing edges" a good predictor should enrich for.

| Screen | Cell line | Notable hits | DOI |
|---|---|---|---|
| **Wei et al. 2020** | Vero E6 | *SMARCA4*, Golgi/HOPS, *TMEM41B* | 10.1016/j.cell.2020.10.028 |
| **Daniloski et al. 2020** | A549^ACE2 | *ACE2*, *RAB7A*, retromer, *SEC61* | 10.1016/j.cell.2020.10.030 |
| **Wang et al. 2020** | Huh7.5.1 | *ACE2*, *CTSL*, *TMEM106B*, RAB GTPases | 10.1016/j.cell.2020.12.004 |
| **Schneider et al. 2020** | multiple | pan-coronavirus factors, *TMEM41B* | 10.1016/j.cell.2020.12.006 |
| **Zhu et al. 2021, *Nat Commun*** | — | entry-regulating host factors | 10.1038/s41467-021-21213-4 |
| **Baggen et al. 2021, *Nat Genet*** | — | *TMEM106B* as proviral factor | 10.1038/s41588-021-00805-2 |

**Recommended primary external-validation set:** Wei, Daniloski, Wang, Schneider
(the four *Cell* screens). They use different cell lines, so the intersection is
a high-confidence host-factor core; the union is a recall ceiling. A predicted
edge landing on a screen hit absent from Gordon is a genuine independent hit.

## Thread 3 — Host–pathogen PPI network analysis (the method context)

A focused, methods-oriented literature on computationally predicting
host–pathogen protein interactions — network-based classifiers, feature-extended
predictors, and controllability/topology analyses of virus–host graphs (Ackermann
2019 on influenza; Mahapatra 2020; Kösesoy 2021; Tahir 2023 Deep-HPI-pred; Hu
2025 HPInet). Notably, this is a **low-citation, long-tail thread**: the genuine
methodology papers are cited in the low tens, not the thousands — the heavily
cited "host-pathogen" hits from a naive search are pandemic clinical/omics reviews,
not interaction-prediction methods, and were excluded during curation. The
practical read: cross-species HPI prediction is an active but non-crowded niche,
and Cartograph's degree-normalized L3 approach is more principled than most of
these ad hoc feature pipelines.

## Thread 4 — Network medicine / drug repurposing (the application precedent)

- **Zhou et al. 2020, *Cell Discovery*** — *Network-based drug repurposing for
  novel coronavirus 2019-nCoV/SARS-CoV-2* (doi:10.1038/s41421-020-0153-3).
  The proximity-based repurposing template: measure network distance between drug
  targets and viral-host modules. Precedent for turning predicted edges into
  actionable hypotheses — the downstream half of Cartograph's value proposition.

## Thread 5 — PPI link-prediction methods (Cartograph's engine)

- **Kovács et al. 2019, *Nature Communications*** — *Network-based prediction of
  protein interactions* (doi:10.1038/s41467-019-09177-y). The paper that
  establishes **L3 (paths of length three)** as the right topological signal for
  PPIs — proteins are linked not because they share partners (L2/triadic closure)
  but because they sit at the ends of complementary L3 paths. Degree normalization
  (the exact variant Cartograph uses) is introduced here to suppress hub bias.
  **This is the methodological anchor of the whole project.**
- Supporting GNN-based PPI predictors (Jha 2022; Lv 2021; Zhou 2022) represent the
  learned alternative to L3's deterministic topology. Useful as benchmark
  comparators; note they need more training signal than a 332-edge graph provides,
  which is an argument *for* Cartograph's L3 choice on this dataset.

## Thread 6 — AI/LLM over PPI & literature (the open frontier)

This is the thinnest and newest thread — and the one Cartograph most directly
advances. Papers appear only from 2022 onward with citation counts still in the
single-to-low-double digits:

- LLM-based biomedical **relation/PPI extraction** from text (Tang 2022; Arsenyan
  2023–2024 on LLM knowledge-graph construction).
- **Explainable biomedical hypothesis generation** via retrieval-augmented LLMs
  (Pelletier 2024–2025) and **multi-agent LLM** hypothesis systems (Xu 2025).

**Read for Cartograph:** nobody has yet combined *deterministic topological link
prediction* with *LLM literature-grounded mechanistic explanation* for a viral
interactome. The separation-of-concerns design (graph math ≠ LLM synthesis) is
well-aligned with where this field is cautiously heading — grounding LLM output
in retrieved evidence rather than free generation.

## Thread 7 — Resources / databases

STRING (v11 / 2021 / 2023 releases; Szklarczyk) for the human–human enrichment
edges, and BioGRID for orthogonal experimental PPI evidence. Version choice
matters for reproducibility of the held-out benchmark — pin the STRING release.

---

## Gaps & opportunities the map surfaces

1. **No topology-based rediscovery benchmark on the COVID interactome exists.**
   The L3 method (2019) and the Gordon map (2020) have not been formally married
   in a held-out edge-recovery study. Cartograph's benchmark would be novel.
2. **CRISPR screens are underused as PPI validation.** They're cited as
   host-factor catalogs, rarely as an independent gold standard for *interaction*
   prediction. Using the four *Cell* screens this way is a defensible, and fairly
   original, external-validation design.
3. **LLM hypothesis generation lacks grounding standards.** The 2024–2025 work
   flags hallucination as the central risk; Cartograph's PubMed/PMC-cited output
   with deterministic-graph separation is a timely, publishable answer.
4. **Recency caveat:** the field's citation mass is 2020–2022. New 2024–2026 work
   is scattered and lower-profile — genuine white space for a well-benchmarked
   methods contribution, not a crowded race.

---

*Method note: OpenAlex, queried across seven threads by both citation count and
recency (2018–2026). OpenAlex's `search` relevance over-weights raw citations, so
the first-pass buckets pulled in generic high-cite pandemic reviews (sepsis
guidelines, gut-microbiota reviews, etc.) that are not about PPI networks. Every
thematic bucket was therefore re-curated with precise `title.search` queries and
the off-topic reviews dropped; the result is 40 genuinely on-topic anchor papers.
One consequence worth noting: for the host–pathogen-methods and interactome
threads, the honestly-curated set is **lower-citation** than the polluted
first pass — the real methodology papers are cited in the tens, and the thousands-cited
"hits" were reviews, not methods. All 40 rows with DOIs are in
`cartograph_literature_map.csv`.*
