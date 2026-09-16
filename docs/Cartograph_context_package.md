# Cartograph: context package

What it is, who it is for, what is genuinely differentiated, and what the evidence
does not yet support. Written 2026-09-14.

Every claim below carries a marker. **[verified]** means I ran the code or the query
myself in this repo. **[sourced]** means a citable URL or paper. **[inference]** means
reasoning from the two. Nothing here is asserted without one.

Companion documents: `Cartograph_research_findings.md` (state of the art and the ordered
next steps), `Cartograph_gap_audit.md` (demo-vs-product gaps, with measured appendix),
`cartograph_soa_review.md` (the raw 9,100-word literature review), `Cartograph_agent_onboarding.md`
(bring a coding agent up to speed).

---

## 1. What Cartograph is

Cartograph is an **evidence-and-measurement layer for protein interaction maps**. You give
it an experimentally-derived interactome; it proposes edges that should be there but are
not yet drawn, attaches an auditable evidence dossier to each one, and measures how often
it is right against a benchmark that was frozen before the predictor was written.

The mechanism, concretely, on the shipped SARS-CoV-2 map:

1. **Load** the Gordon et al. 2020 AP-MS interactome — 332 viral-bait to human-prey edges
   across 26 viral baits [verified: `evidence/gordon2020_edges.csv`].
2. **Enrich** it with STRING v12.0 physical edges at score ≥ 700, which adds 159 human-human
   edges and is the only reason length-3 paths exist at all [verified].
3. **Propose** missing edges by degree-normalized L3 (Kovács et al. 2019) — a deterministic
   path count, never a model generating edges from weights [verified: `backend/predict/l3.py`].
4. **Explain** each proposal with a cited dossier where every mechanistic clause must resolve
   to a real PMID or is dropped before render [verified: `backend/reason/hypothesis.py`,
   `backend/agent/verify.py`].
5. **Score** against a held-out split committed as the repo's *first* commit, with an AST test
   proving the predictor cannot import the evaluator [verified: `heldout.frozen.json` in commit
   `41a41ae`, `l3.py` in `89fcc01`, strictly later; `backend/tests/test_core.py:112-127`].

Origin: a 6-day solo hackathon build (Anthropic × Gladstone, 2026-07-08 to 07-13), now being
developed at AI Fund as a Technical Builder project to validate as a possible venture, on a
horizon of roughly one month ending early October 2026.

### The one-sentence version, and why the current one fails

The README says "the navigation layer for a protein interaction map." That phrasing does not
survive contact with a committee. [sourced] Andrew Ng's published selection criterion is an
idea "specified in enough detail that an engineer can build it for a specific target user"
(https://x.com/AndrewYNg/status/1820863062993490137). "Navigation layer" names an abstraction,
not a person with a recurring decision.

A concrete replacement that matches what the code actually does:

> **Software that measures whether a protein-interaction claim is trustworthy — with a
> pre-registered benchmark per map and a paper behind every clause.**

---

## 2. The customer: five candidates, all weak

Five candidate ICPs were stress-tested adversarially against verified evidence. **All five
returned `weak`.** This is the most important finding in this document and it should not be
softened. Each fails for a different, independent reason.

| # | Candidate ICP | Verdict | Why it fails |
|---|---|---|---|
| 1 | Academic virus-host interactomics lab (Krogan, Cristea, Plate, Pichlmair, Varjosalo…) | **weak** | They are triage's *vendors*, not its consumers — MiST, SAINT, CompPASS, CRAPome are all theirs and free. They publicly named a different bottleneck. |
| 2 | Embedded computational biologist / bioinformatics core | **weak** | This person *is* the triage layer. Their job title is the product. No purchase authority; "must justify to a PI" concedes the buyer is elsewhere. |
| 3 | Pharma / biotech host-directed target ID | **weak** | The exact move — expand to network partners to find targets — was formally tested and failed. Segment is contracting. |
| 4 | Benchmark / standards consumer (method developers, assessors) | **weak** | In this field benchmarks are *authored, not bought*. Their incentive is to publish a competitor. Nobody in comp-bio has monetized a harness. |
| 5 | CRO / co-fold screening platform needing a triage layer | **weak** | The buyer loses money when the product works — triage means "buy fewer units." Best-fit account already built its own. |

### The three findings that break every ICP at once

**(a) The pain is not triage.** [verified] When *Cell Systems* asked eleven leading
network-biology groups what the current bottleneck in interaction mapping is, **not one said
candidate triage**. They said assay noise and cross-lab irreproducibility (Skinnider),
completeness (Luck), context-specificity (Mukhtar), scale (van Leeuwen), missing nodes
(Carvunis), isoform resolution (Bulyk) — and Taipale said the inverse of Cartograph's thesis
outright: *"what if we actually need fewer interactions? … p53 … currently has about 2,500
physical interactions … I wager that most of these interactions do not actually happen in
cells."* Krogan — whose lab produced the exact dataset Cartograph runs on — named resolution,
temporal-spatial dynamics, and "people-people interactions." (Skinnider et al., *Cell Systems*
16, 2025, doi:10.1016/j.cels.2025.101295.)

**(b) Revealed behaviour agrees.** [verified — I ran this] Of the 332 Gordon 2020 edges,
**267 (80.4%) have never once co-appeared in a paper title or abstract with their viral bait
in six years.** Median follow-up is 0. Attention concentrates on 13 pairs. And [sourced]
Gordon et al. narrowed the 332 to a test list **by compound availability, not by interaction
confidence** — 66 druggable proteins, 69 compounds. The selection axis is reagent availability,
which Cartograph gets free from Open Targets and does not own. *You cannot sell a decision aid
for a decision that is not being made.*

**(c) The trigger fires once every one to three years.** [verified] Virus-host interactome
papers: ~20-40/yr worldwide, and 824 of 1,031 senior authors in that segment published exactly
once in six years. AP-MS output is flat (462 → 489 papers/yr, 2020-2025) while computational
PPI output nearly doubled (12,841 → 22,029). Supply of predictions is growing far faster than
the wet-lab capacity that would consume triage. A once-per-grant-cycle decision is a consulting
engagement, not a product cadence.

### If forced to name one today

[inference] **ICP #1 narrowed and re-pointed**: the ~65 recurring virus-host interactome labs,
sold not a ranking but **an audit of the map they are about to publish**. It is the only
candidate where the trigger is real (manuscript submission), the pain is the one they named in
print (irreproducibility), and Cartograph's unmatched components are the ones that apply. It is
still weak on willingness to pay — [sourced] Cytoscape (NIH U24 HG012107) and NDEx (U24
CA269436) are free, so academic WTP should be modelled at ~$0.

---

## 3. USP: what is genuinely unmatched

Three things, all verified in the code, all confirmed absent from the prior art.

**1. A locked, pre-registered benchmark reported per map.** The split is frozen and committed
before the predictor exists, with a test proving the predictor cannot import the evaluator
[verified]. [sourced] No product or public resource does this. CAPRI is the closest blinded
assessment but it scores *docking* — given a pair, model the complex — not *which pairs
interact*, and runs ~6-month community rounds rather than per-dataset. Open Targets, the
largest free target-ID platform, concedes the gap in its own literature: *"the lack of
appropriate gold standards across therapeutic areas limits the effectiveness of appropriate
benchmarks."*

**2. A deterministic citation gate — no citation, no render.** A mechanistic clause whose PMID
does not resolve against the verified pack is dropped, not rendered [verified:
`backend/agent/verify.py`]. This is the operational answer to the fabrication problem that makes
reviewers distrust LLM-generated mechanism. [verified] Ran live on TP53|MDM2: 38.8 s, 20
abstracts retrieved, real deposited complex PDB 1YCR, 5 clauses kept, 0 dropped, 4 openable
PMIDs.

**3. Structure-derived interface residues.** Contacts computed from deposited mmCIF coordinates
rather than copied from prose, with predicted models always labelled predicted [verified:
`backend/structure/interface.py`]. The proof this computes rather than copies: the prototype's
wrong ORF9b S55/K46 was repaired to the real S53/R58/E65.

Supporting asset: **`backend/bench`** is the one genuinely dataset- and predictor-agnostic
component in the repo. Every function takes an explicit positives set and a caller-chosen
universe; `roc_auc` uses mid-ranks so a no-preference scorer scores exactly 0.5; every record
carries `value`, `max_attainable` and enrichment over prevalence [verified:
`backend/bench/metrics.py:17-96`].

### What the USP is *not*

**Not the predictor.** [verified, in this repo's own baseline table] A one-line STRING
best-score guilt-by-association lookup — no path machinery at all — beats shipped L3 on every
cut: p@10 **0.80 vs 0.30**, p@20 **0.60 vs 0.45**, p@50 0.36 vs 0.26, AP **0.681 vs 0.373**.
`docs/Cartograph_research_findings.md` states plainly that the null hypothesis "L3 adds nothing
beyond STRING" is *live and not yet refuted*. Every L3 path in this map traverses two STRING
edges. A technical reader finds this in minutes because it is in the repo.

**Not "ranked predictions with evidence."** [sourced] Taken twice over. PrePPI serves ~1.3M
ranked human predictions with structure-plus-evidence at proteome scale (expanded 2026 to yeast
and E. coli — still no viral proteome). P-HIPSTer did 282,528 pan-viral-human structural
predictions in 2019 with a reported ~76% validation rate; it is the closest published prior art
and predates this project by seven years. [verified] Its server today reads "The P-HIPSTer
Database is Being Updated," so benchmarking against it may not currently be executable.

---

## 4. The numbers, stated honestly

Every metric is computed over one stated candidate universe: **8,357** untested viral-bait to
human-prey pairs containing **57** held-out positives, so prevalence is **0.68%** [verified
from the built artifact].

| metric | value | max attainable | vs the floor |
|---|---|---|---|
| precision@20 | 0.45 | 1.00 | 66× prevalence |
| precision@10 | 0.30 | 1.00 | 44× prevalence |
| precision@50 | 0.26 | 1.00 | 38× prevalence |
| recall@50 | 0.23 | 0.88 | 13 of 57 |
| ROC-AUC (tie-aware) | 0.62 | 1.00 | 0.50 null ranker |
| average precision | 0.10 | 1.00 | 0.007 null ranker |

### The headline is a lucky draw, and this must be fixed before any pitch

**[verified — I ran this, 20 seeds, reproducible in under a second]** Resampling the same
56-edge held-out protocol on the same enriched graph with seeds 0-19:

```
values: 0.30 0.30 0.35 0.40 0.55 0.30 0.15 0.25 0.25 0.40
        0.30 0.25 0.45 0.40 0.40 0.30 0.20 0.35 0.15 0.30
mean = 0.3175   median = 0.300   sd = 0.099   range = 0.15 - 0.55
draws reaching 0.45: 2 of 20
reachable of 56: min 7, max 16, mean 10.6
```

**The published 0.45 sits at roughly the 90th percentile of its own sampling distribution.**
The honest headline is **precision@20 ≈ 0.32 ± 0.10 (n = 20 seeds)**, which is still ~47×
prevalence and still a real result. Leading with 0.45 in front of anyone who resamples for a
living is an unrecoverable credibility loss — and it lands directly on the differentiator,
because the entire pitch is measurement honesty. This is gap-audit item C4 and it costs one
second of compute.

### The ceiling is in the data, not the algorithm

[verified] Only 14 of 57 held-out edges are reachable by a length-3 path. Every common-neighbour
variant reaches 20, and the union of *all* local-topology scorers is also 20 — so **37 of 57 are
structurally unrecoverable by any such method on this split.** 28 of the 57 held-out preys have
degree 0 in the training graph, because their only AP-MS edge was the one held out.

This undercuts the standard venture narrative that more model work makes the product better. It
should be pre-empted, not discovered. The lever that does move it is configuration, not
modelling: moving the STRING threshold from 700 to 400 raises reachability 14 → 27, precision@10
0.30 → 0.40, tie-aware AUC 0.618 → 0.711 and AP 0.104 → 0.151, costing 0.05 on precision@20
[verified].

### Split class

[verified] All 57 held-out pairs are class **C2** in the sense of Park & Marcotte 2012 — the
bait is seen in training, the prey is not. Typical random cross-validation is >99% C1, the easy
class, so this split is *harder* than the norm. C3, where neither protein is seen, is unmeasured
and no generalisation to it is claimed. Say this out loud; it converts an unusual split from a
hidden liability into a stated strength.

---

## 5. Where the product cannot currently serve its own ICP

Three verified breaks, all load-bearing, all in the general (non-demo) path.

| break | evidence | consequence |
|---|---|---|
| The Evidence Agent passes **one taxid to both ends** of an edge | `backend/agent/resolve.py:99` — `resolve_edge(bait, prey, taxid="9606")` [verified] | A host-pathogen edge is viral × human by construction, so the flagship capability degrades to topology-only on **every edge shape the project was built for**. Orf6\|RAE1 returns `topology_only` in 1.3 s. |
| Uploads are STRING-enriched against **human regardless of organism** | `config.py:78 STRING_SPECIES = 9606`, used at `graph/enrich.py:35,85` [verified] | A non-human map is silently enriched against the wrong species. |
| `backend/bench` is **never wired to the upload path** | imported only by `build_artifact.py:24-25` [verified] | An uploaded map gets `_own_eval`: `precision@min(20, n_heldout)`, one hardcoded seed, no recall, no AP, no AUC, no universe size, no prevalence [verified: `api/server.py:306-328`]. The single reusable asset is wired to the demo, not the customer. |

Related: a Gordon-shaped map with no STRING enrichment hits returns **zero predictions and
precision 0.0 with `enrich_error` still None** — a wrong answer with no diagnosis, from a
product whose thesis is that you can trust its numbers [verified].

---

## 6. Competitive landscape

| who | what they do | what they do not do |
|---|---|---|
| **PrePPI** (Honig lab, Columbia) | ~1.3M ranked human predictions, structure + evidence, public server; expanded 2026 to yeast and E. coli | No viral proteome. No interactome upload. No per-map held-out evaluation. |
| **P-HIPSTer** (Lasso 2019) | 282,528 pan-viral-human predictions, ~76% reported validation — closest published prior art | Predates SARS-CoV-2. Server currently "Being Updated". Predictions, never ground truth. |
| **Predictomes.org** (Walter lab) | ~16k high-confidence + ~112k lower-confidence AlphaFold-Multimer human PPIs | Human only. No held-out test set, no harness, no per-prediction citations. |
| **STRING / IID / FunCoup / HumanNet** | Ranked association with per-channel evidence, two decades of it | No literature gate, no per-hypothesis provenance, no per-map evaluation. |
| **Open Targets** | 7.8M target-disease associations, per-evidence provenance; the incumbent pharma channel | Free. Concedes its own benchmark gap. |
| **Cytoscape / NDEx** | Store, exchange, visualize | Predict nothing — these are a **distribution channel**, not competitors. Cartograph already exports CX2. |
| **Tamarind Bio** | Sells the upstream Cartograph proposes to triage: FASTA in, ipTM out, ~100 biotech customers incl. 8 of top-20 pharma, $13.6M raised | **No benchmark, no precision number, no citations** — only heuristic ipTM cutoffs. The strongest commercial evidence for the triage thesis and the most obvious design partner. |
| **Causaly / BenchSci** | The "which experiment next" position, already sold to 12-16 of the top 20 pharma | Different method — but they occupy the buyer. |

[verified] **No incumbent locks a pre-registered split per map.** The claim holds.

But the analogues that come closest are all nonprofit or consortium-funded: MLCommons MedPerf,
Open Problems (CZI + Helmholtz), Polaris (Valence/Recursion, no disclosed business model),
DREAM/Sage. The one commercial precedent — Insilico's TargetBench, bundled free with PandaOmics
— [verified] has had an expired TLS certificate on targetbench.org since roughly five months
after launch. **Announcing a benchmark is cheap; operating one is the moat, and the incumbent
is not operating theirs.** This is the central commercial risk in leading with the harness.

[verified] One named, funded buyer exists for exactly this problem: **DARPA's Real-Time
Pathogen-Host Interactome Prediction** program — ranked mechanistic hypotheses, zero-shot on
unseen pathogens, core predictions under 15 minutes, Phase II validation of ≥25 novel
predictions at ≥30% hit rate. Caveats: small-business-only, and solicitation DPA26BZ03-DV014
closed 22 July 2026. Note its zero-shot requirement is Park-Marcotte class **C3** — exactly what
Cartograph explicitly does not measure.

---

## 7. Venture fit

[sourced] AI Fund is a venture studio ($370M+ total, Fund II ~$190M closed May 2025) that
co-founds companies on a stated **3-month idea-to-funded clock**, $500K-$1M pre-seed, with
demand often sourced from corporate LPs — AES, HP, Mitsui, Mitsubishi, QBE, TELUS. Its 40+
portfolio contains **no drug-discovery or computational-biology company**; the health entries
are care-delivery and mental-health apps.

[verified] The EIR pipeline expects ideas that arrive already pressure-tested: "a prototype
built, early feedback from domain experts or potential customers gathered." **Cartograph has
the prototype half and none of the customer half** — no LOI, design partner, pricing test, or
named lab that has run its own map through it.

[inference] Cartograph is **off-thesis by shape rather than by quality**: a research-tooling
venture with a multi-year proof cycle, a buyer outside the LP network, and no corporate partner
supplying demand. The committee's prior should be assumed negative, and the burden is a *named
buyer*, not a better metric.

### The comparable set is unkind

- [sourced] **Rezo Therapeutics** — founded by Nevan Krogan, whose lab produced the exact dataset
  Cartograph runs on, on precisely this thesis. $78M Series A (Nov 2022, SR One, a16z Bio+Health,
  Norwest). **Nothing raised since**; 44 employees as of May 2026. The best-resourced version of
  this thesis has not broken out in four years — and it captured value as a therapeutics
  pipeline, not as software.
- [sourced] **Interline Therapeutics** — $92M (2021, Foresite, ARCH) to "map and correct
  dysfunctional protein communities." Now deadpooled.
- [sourced] **BenevolentAI** — ~$282M raised, BEN-2293 missed Phase IIa, delisted March 2025.
- [sourced] **What does raise**: Chai Discovery, $70M Series A then $130M Series B at $1.3B — on
  **wet-lab hit rates from a frontier model**, not on evaluation rigor.
- [sourced] **The software ceiling**: Schrödinger's 2025 software revenue was $199.5M after ~35
  years as the category leader. A PPI triage layer is a feature inside that envelope.

### Business model options, priced

| model | reality |
|---|---|
| Academic software seats | [sourced] Free incumbents (Cytoscape, NDEx) are NIH-funded. Model WTP at ~$0. |
| Pharma workflow seats | [sourced] Real — Causaly, BenchSci, IPA at ~$32k/seat/yr — but ~150 reachable seats ≈ $4.8M ARR ceiling. |
| Benchmark / standards | [inference] **No one in computational biology has ever monetized a harness.** Central risk. |
| CRO / platform partnership | [inference] Buyer's revenue *falls* when the product works. |
| Data co-generation | [sourced] Capital-intensive and contracting — Ginkgo Q3 2025 revenue $39M, down 56% YoY. |
| Therapeutics co-development | [sourced] Venture-scale, but needs the asset and $78M+. Rezo's path, not a $500K-$1M pre-seed's. |

### The one reframe that fits both the asset and AI Fund's shape

[inference] Not "better PPI prediction" but **the audit layer for AI-generated biological
claims** — locked pre-registered benchmark, no-citation-no-render gate, structure-derived rather
than prose-copied residues. That positions against Causaly/BenchSci (evidence tooling with
pharma budget) rather than against Rezo/Chai (capital-intensive discovery), and it is the only
version where a solo builder with $500K-$1M reaches a first paying user inside a year.

Supporting evidence for that framing, not for the triage one: [sourced] Bayer reviewed 67
in-house projects started from literature reports — data fully reproduced in only **14**,
partially in 10, with 43 showing inconsistencies preventing replication (Prinz et al. 2011).
[sourced] Only **5** SARS-CoV-2 virus-host interactions were reported by every independent AP-MS
study. The market pain is *trust in claims*, and that is what Cartograph's unmatched components
address.

---

## 8. The three questions the evidence cannot answer

These are what a committee asks, and the current answer to each is "we don't know."

1. **Does it generalize?** [verified] Exactly one interactome is loaded. None of the eight
   datasets shortlisted in this project's own research document has been run. All 57 held-out
   pairs are C2; C3 is unmeasured.
2. **Does the method beat a one-line lookup?** [verified] The repo's own table says no — STRING
   best-score wins on every cut. Until that control is refuted, there is no predictor to sell.
3. **Who pays, and for what?** [verified] No customer, design partner, LOI, pricing test, or
   named lab that has run its own map. The single most persuasive missing artifact is one named
   person saying *"we would have tested a different 20 pairs because of this."*

---

## 9. What would change the verdict, ordered by decisiveness

Each is reachable inside the remaining horizon.

1. **Republish the headline as a distribution, not a draw.** mean 0.318, sd 0.099, n=20, above
   the fold, replacing 0.45. One second of compute. Protects the only thing that is actually
   differentiated.
2. **Settle L3 vs STRING in public, and adopt the winner.** If STRING-GBA still wins with
   mid-rank tie handling across ≥3 maps, ship it as the scorer and sell the harness. That is a
   stronger story than a defended L3, not a weaker one.
3. **Fix the two taxids and organism-aware enrichment, then run a second map end to end.**
   Haas 2023 influenza A or Jäger 2011 HIV (Jäger breaks the degree-1 star topology, so it tests
   whether these findings are artifacts). Answers question 1 and proves the ICP's own data shape
   is supported.
4. **Wire `backend/bench` into the upload path.** Universe size, prevalence, precision@k with its
   denominator, recall, AP, tie-aware AUC, per-edge transparency, ≥20 seeds. This is the only
   thing in the repo a competent user cannot rebuild in an afternoon.
5. **Run the retrospective test.** Rebuild the graph from pre-2020 evidence; ask whether eEF1A
   (plitidepsin), eIF4A (zotatifin) or PIKfyve (apilimod) lands in the top 20. Speaks in the
   buyer's currency — a target that entered the clinic — rather than in precision@k.
6. **Get one named artifact.** One recurring lab or one ID-biotech comp-bio lead, on the record,
   with numbers. **If six weeks of outreach produces none, that is itself the answer** — and it
   is a cheaper answer than building for another quarter.

---

## 10. Standing integrity rules

These are enforced by tests and are the credibility floor. Do not trade them for a better number.

- **Deterministic critical path.** The graph proposes; Claude reads, adjudicates, explains.
  Claude never invents an edge from model weights.
- **Eval-first, locked, separate.** Split frozen and committed first, with sha256; a test proves
  the predictor cannot import it.
- **No citation, no render.** A clause whose PMID does not resolve is dropped.
- **Predicted is always labeled predicted.** Experimental structures and predicted models are
  never conflated.
- **Publish the measured zero.** The structure channel's aggregate gain excluding the pinned
  edge is 0.0, and it stays published. That is the strongest integrity signal in the repo — and
  [sourced] it is a *coverage* result (only 3 pairs on this map have a deposited complex), not a
  null result about structure.
