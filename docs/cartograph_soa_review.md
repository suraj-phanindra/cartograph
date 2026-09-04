# Interactome completion: state of the art, and what it means for Cartograph

## Bottom line

Degree-normalised L3 is still a defensible baseline, and the largest independent benchmark of network-based PPI prediction to date put it in the top tier. What beats it are not GNNs or embeddings but refinements of the same length-3 idea, plus one method that adds sequence — and the best *experimentally validated* method in that benchmark was a topology-plus-sequence hybrid, which is direct evidence for your fusion thesis. So Priority 1 is not where your risk lives.

Your risk lives in Priority 2. Three of your five reported numbers cannot be computed over the same candidate universe — `recall@50 = 0.93` is arithmetically impossible on a global ranking of 57 positives with 50 slots, and `ROC-AUC = 0.845` is hard to reconcile with only 14 of 57 held-out edges being reachable by any length-3 path. A reviewer will find this in about ninety seconds, and it will cost you more credibility than a modest predictor would. Fix the universe before you touch the predictor.

Your Priority 3 hypothesis is supported by the literature but misdiagnosed in your own map: the 14-of-57 ceiling is set by the *STRING enrichment layer*, not by interactome density, and it is measurable and movable today with a threshold sweep.

## Where your framing needs correcting

You asked to be told this first, so:

**Common neighbours is available to you, and it is your most important missing baseline.** In a strictly bipartite bait–prey graph, common neighbours between a bait and a prey is identically zero, because any bait–prey path has odd length. But adding 159 STRING prey–prey edges breaks strict bipartiteness. A path bait → prey′ → prey (AP-MS edge, then one STRING edge) is a length-2 path, and prey′ is a genuine common neighbour. So L2/CN/RA/Adamic–Adar all exist in your enriched graph and score exactly the candidates that are direct STRING partners of one of that bait's known preys. L3 extends the reach to STRING distance 2. If L2 recovers most of your held-out edges, L3 is adding nothing, and you currently cannot tell. This is a sharper ablation than "random vs L3", and it is the one to run first.

**"Zero shared preys" makes every prey degree 1, which determines almost everything else.** With 332 edges over 332 unique preys and no prey hit by two baits, the AP-MS layer is a disjoint union of 26 stars. Two consequences follow. Removing a held-out edge deletes the prey's *only* AP-MS edge, so the prey is AP-MS-isolated at test time. And every length-3 bait→prey path must be AP-MS + STRING + STRING, because the alternative route bait → prey′ → bait′ → prey requires a shared prey, which your map excludes by construction. Reachability is therefore a pure property of the STRING layer.

**Degree normalisation is doing something different in your graph than in the paper it comes from.** L3's degree normalisation assumes a homogeneous network where node degree proxies promiscuity. In your two-layer graph the intermediate nodes' degrees mix AP-MS degree (viral bait promiscuity) with STRING degree (functional hub-ness), which are not the same quantity and are not on the same scale. Worth stating explicitly in the methods, and worth an ablation with and without normalisation.

**There is no Krogan-lab Mpox AP-MS map.** I searched for one specifically and found none. The published mpox "interactomes" are computational predictions rather than affinity-purification experiments — a phylogenomic/host–pathogen interactome analysis ([Kumar et al. 2023](https://doi.org/10.1099/mgen.0.000987)), a computational pathogen–host interactome for in-silico repurposing ([Paul et al. 2024](https://doi.org/10.1038/s41598-024-69617-8)), and the HuPoxNET predicted atlas ([Kataria et al. 2024](https://doi.org/10.3389/fmicb.2024.1399555)). If you had built an "apples-to-apples" comparison on that, the apples would have been predictions.

**Your roadmap is wrong that cross-coronavirus PPI data do not exist.** [Gordon et al. Science 2020](https://doi.org/10.1126/science.abe9403) carried out comparative viral–human interaction mapping for SARS-CoV-2, SARS-CoV-1 *and* MERS-CoV, and [Batra et al. 2026](https://doi.org/10.1016/j.chom.2026.04.015) generated comparative AP-MS maps for SARS-CoV-2 and its bat progenitor RaTG13 in both human and greater horseshoe bat cells. A real conservation column is available; you have been declining to build something you could build.

**The pooled-AlphaFold3 paper is Todor et al.** — authors Todor H, Kim LM, Jänes J, Burkhart HN, Darst SA, Beltrao P, Gross CA ([Mol Syst Biol 2026](https://doi.org/10.1038/s44320-026-00189-7)). There is no author named Anlin; the follow-up preprint on a mycobacterial pathogen does include an author "Na A", which may be where the name came from. Cite it correctly, since you feature it in your positioning.

**On ROC-AUC being "criticised":** the precise modern statement is not that AUROC is invalid but that no single metric is sufficient and that metrics disagree about *which algorithm wins*. See Priority 2 below.

**Your structural channel adding 0.0 aggregate precision is an expected coverage result, not a null result about structure.** Confident structural models exist for a small minority of interactions, so a high-precision/low-recall channel mathematically cannot move an aggregate computed over 57 edges. Report it as coverage-limited and evaluate it where it has coverage.

---

## Topology-only prediction after L3

### The one benchmark that matters

The International Network Medicine Consortium benchmarked 26 network-based methods across six interactomes from four organisms, *A. thaliana*, *C. elegans*, *S. cerevisiae*, and three human networks (HuRI, BioGRID, STRING); with 10-fold cross-validation, four metrics (AUROC, AUPRC, P@500, NDCG), a combined z-score, and then wet-lab Y2H validation of the top-500 predictions from each of the seven best computational methods ([Wang et al. 2023](https://doi.org/10.1038/s41467-023-37079-7)). This is the closest thing the field has to a community standard, and it is the single most useful paper for your decision.

Six methods were consistently strong: RNM, L3, MPS(T), MPS(B&T), RepGSP2 and SEAL. The authors' own summary is that the methods leveraging "specific connectivity properties of PPI networks (i.e., the L3 principle)" displayed the most promising performance, while generic deep-learning approaches (embeddings and GNNs) "performed consistently across different interactomes... with higher robustness, although their performances are not top-ranking." Traditional similarity indices (CN, AA, RA, Jaccard, Katz, preferential attachment) were limited.

The experimental validation is the part worth internalising. Of the top-500 predictions from each method, MPS(B&T) yielded 376 positives and 54 negatives — a precision of 87.4%; MPS(T) reached 75.9% and RNM 69.5%. Computationally the order was different (MPS(T) first, RNM second, MPS(B&T) third), which the authors attribute partly to the metrics differing between the two exercises. RNM had the highest mean rank and lowest variance across all six interactomes, making it the most robust single choice.

So: plain L3 is not the best method, but it is in the top six of 26, and the three that beat it are all L3-derived. RNM combines a diagonal noise model, a spectral noise model and the L3 principle. MPS(T) applies the L3 idea one level up — it scores a pair (i,j) highly when protein i's neighbourhood resembles the neighbourhoods of j's neighbours. MPS(B&T) is MPS(T) plus pairwise sequence similarity, and it is the method that won the wet-lab test. If you want a concrete upgrade path from L3 that is not speculative, it is MPS/RNM, and the sequence term is what bought the extra precision.

Two caveats on this benchmark. It used 10-fold cross-validation over known edges, which is the C1-dominated regime discussed below, so it does not tell you how these methods behave on unseen proteins. And one of its six interactomes is STRING, which is itself an integrated, partly-predicted network — the paper's own predictability analysis (below) shows STRING behaves unlike the five experimental interactomes.

### Cannistraci-Hebb: real, and now peer-reviewed

The CH line is legitimate and you should take it seriously, but the provenance matters for how much weight to give the "beats L3" claim.

The group's account is that they posted a preprint roughly two months after the Kovács et al. preprint in 2018 containing a proof that L3 is the length-3 generalisation of resource allocation (hence their name RA-L3), a framework for length-n local indices, and the CH1/CH2/CH3-Ln family. The CH2-L3 and CH3-L3 indices then circulated as preprints for years, papers as recent as 2024 still cite them as "Muscoloni et al. 2020" preprints. The adaptive framework was finally published as Zhao, Muscoloni, Michieli, Zhang & Cannistraci, "Adaptive Cannistraci-Hebb Network Automata Modelling of Complex Networks for Path-based Link Prediction", NeurIPS 2025. So as of now this is peer-reviewed work, not a preprint; but it took six years, and essentially every head-to-head CH-versus-L3 comparison in the literature comes from the originating group. In the one large independent benchmark, the CH representative (CRA, i.e. CH1) was included and did not reach the top tier ([Wang et al. 2023](https://doi.org/10.1038/s41467-023-37079-7)).

The CHA paper's own most useful finding for you is negative and generalisable: no single path length dominates across network classes. Coauthorship and connectome networks are better captured by L2 structures; PPI and transcription networks favour L3. That is independent-of-provenance support for using L3 on a PPI graph, and it is also an argument for the adaptive approach rather than a fixed choice.

There is an open disagreement here worth knowing about. [Ghasemian et al. 2020](https://doi.org/10.1073/pnas.1914950117) argued that no individual predictor is near-optimal and that stacking ~200 topological predictors approaches the achievable ceiling; the Cannistraci group replied in a preprint ([Muscoloni & Cannistraci 2021](https://doi.org/10.20944/preprints202105.0689.v1)) arguing their adaptive automata match or beat stacking. This is unresolved, and both sides are arguing about the same underlying question of whether the win comes from model selection or model combination.

### The independent test of the core L3 claim

The most important third-party check on "3-hop beats 2-hop" is [Zhou, Lee & Wang 2021](https://doi.org/10.1016/j.physa.2020.125532), who compared 2-hop-based and 3-hop-based similarity indices on 128 real networks and found the 3-hop indices better with a winning rate of about 55.88%. That is a coin flip with a lean. L3's advantage over common-neighbour methods is therefore not a general property of complex networks; it is a property of certain classes, PPI among them. Your regime is the favourable one, but you should stop describing L3 as a general improvement and describe it as a domain-appropriate one.

A useful independent refinement comes from [Yuen & Jansson 2023](https://doi.org/10.1186/s12859-023-05178-3), who argue the L3 principle admits a second interpretation that existing L3 predictors underuse, and propose NormalizedL3 (L3N). They report more true positives among predictions than prior L3 methods on BioGRID, STRING, MINT and HuRI, at higher compute cost. Their other observation is the one you should act on: L3-based and general-purpose predictors rank *different pools* of PPIs. That is the same complementarity Wang et al. found, and it is an argument for a portfolio rather than a champion.

### Subgraph GNNs and embeddings

SEAL learns a heuristic from local enclosing subgraphs rather than assuming one ([Zhang & Chen 2018](https://doi.org/10.48550/arXiv.1802.09691)), and the line continues through labelling-trick theory and scalable variants — Neo-GNN ([Yun et al. 2021](https://doi.org/10.48550/arXiv.2206.04216)), BUDDY/ELPH ([Chamberlain et al. 2023](https://doi.org/10.48550/arXiv.2209.15486)) and NBFNet. On PPI networks specifically, SEAL made the INMC top six but not the top three.

The field's own critique of this literature is the thing to read before adopting any of it. [Li, Shomer et al. 2023](https://doi.org/10.48550/arXiv.2306.10453) identify three pitfalls: baselines reported below their actual performance, no unified splits or metrics across datasets, and, most relevant to you, an unrealistic evaluation setting built on easy negative samples. Their HeaRT protocol samples hard negatives instead, and under it the published ranking of methods changes substantially, with simple heuristics competitive against elaborate architectures.

For embeddings there is a stronger, structural objection: [Menand & Seshadhri 2024](https://doi.org/10.1073/pnas.2312527121) show that low-dimensional node embeddings cannot represent the triangle-rich, heavy-tailed structure that real networks have, which is a measurement-level limitation rather than a tuning problem. Combined with the fact that your graph has 358 nodes and 491 edges, my read is unambiguous: a learned link predictor has nothing to learn here and will overfit. Keep the deterministic predictor; that design choice is defensible on evidence, not just on integrity grounds.

### The bipartite regime

This is the least-served part of the literature and it is your regime, so it is worth knowing what exists. The local-community paradigm was extended to bipartite graphs by [Daminelli, Thomas, Durán & Cannistraci 2015](https://doi.org/10.1088/1367-2630/17/11/113037), which is the natural reference point for bipartite topological prediction. [Özer, Orman & Labatut 2024](https://doi.org/10.1016/j.procs.2024.09.567) then ran an experimental comparison of 19 link-prediction methods able to handle bipartite graphs, some taken from the literature and some adapted by them from unipartite techniques, plus GCN-based recommender methods repurposed for the task — that is the closest thing to a bipartite benchmark and the most directly transferable comparator list for you.

The other body of work you should mine is drug–target interaction prediction, which is bipartite by construction and has been thinking about exactly your evaluation problem for a decade. [Pahikkala et al. 2015](https://doi.org/10.1093/bib/bbu010) lay out four factors that produce dramatically different results — problem formulation, evaluation dataset, nested versus simple cross-validation, and crucially "whether training and test sets share common drugs and targets, only drugs or targets, or neither". That last factor is the bipartite analogue of Park & Marcotte's classes, and the DTI field treats it as mandatory reporting.

### Comparators to add

Given the structure of your graph, the ranked list I would run:

1. **Raw STRING guilt-by-association** — score each candidate prey by its best (and separately, summed) STRING score to the bait's training preys, with no path machinery. This is the control that tells you whether L3 is contributing topology or merely re-expressing STRING.
2. **L2 / CN / RA / Adamic-Adar** on the enriched graph, as described above.
3. **Preferential attachment (degree product)** — in your map prey degree is 1, so this collapses to "rank by bait degree". That makes it a pure degree null, and any pooled metric that PA scores well on is measuring bait promiscuity.
4. **Degree-preserving permutation null** — rewire the STRING layer preserving degree sequence, re-run L3, repeat; this gives you an empirical null distribution for precision@k rather than an analytic one.
5. **Random**, to anchor prevalence.
6. **MPS(T)-style second-order similarity and RNM**, as the two methods with the best independent track record.

---

## Evaluation protocol

### Park & Marcotte, confirmed

Your recollection is right and the paper is worth quoting precisely. The published title is "Flaws in evaluation schemes for pair-input computational predictions" ([Park & Marcotte 2012](https://doi.org/10.1038/nmeth.2259)). The classes are defined by component-level overlap with the training set: C1 is test pairs sharing *both* proteins with the training set, C2 sharing *only one*, and C3 sharing *neither*. Their empirical findings are the load-bearing part: across seven PPI prediction methods spanning SVMs, random forests and heuristics, performance differed significantly and often numerically largely between the three classes; and in a typical random cross-validation, C1 accounted for **more than 99%** of the generated test set. Meanwhile at the population level, using HIPPIE as the reference, C1 is only 19.2% of possible human protein pairs, against 49.2% for C2 and 31.6% for C3. So the standard protocol measures the rarest case and reports it as the general one. They recommend reporting performance separately per class — and note that for pair-input problems with two different object types, four classes are needed.

### Which class your holdout is

Because every prey has degree 1 in the AP-MS layer, holding out edge (bait *b*, prey *p*) removes *p*'s only AP-MS edge. With respect to the assay layer, all 57 of your held-out pairs are therefore **C2**: the bait is seen, the prey has no remaining experimental evidence. On the union graph including STRING, *p* is still a node with prey–prey edges, so it is not literally unseen — but it carries no AP-MS evidence, which is what a topological predictor over the bipartite layer needs.

This is good news, and you should say so explicitly rather than leaving it implicit. Your split is *harder* than the C1-dominated random CV that Park & Marcotte criticise, and it matches your deployment population, where the interesting candidates are proteins with no known viral partner. That is a genuine methodological strength.

The two things it costs you: you have no C1 or C3 stratum at all, so you cannot report the C3 number, and C3 is exactly what a reviewer will ask about when you claim the method generalises to preys outside the map. And the constant-degree prey side means you cannot stratify by prey degree even if you wanted to.

### The candidate-universe problem

This is the finding I would act on first. Your candidate pool is the 332 preys, and every one of them is a validated interactor of some bait — the pool is defined by the union of your training and test edges. Working through the arithmetic on your numbers:

| quantity | value |
|---|---|
| candidate bait × prey pairs (26 × 332 − 275 training edges) | 8,357 |
| held-out positives | 57 |
| prevalence | 0.68% |
| observed precision@20 | 0.45 → ≈66× enrichment over prevalence |
| maximum recall achievable on a *global* top-50 list | 50/57 = 0.877 |
| recall@50 as reported | 0.93 → requires 53 hits in 50 slots |
| maximum recall achievable by L3 alone, given 14/57 reachable | 0.246 |
| implied global ROC-AUC if unreachable positives tie at score 0 | ≈0.49–0.61 |

Three things fall out. The 66× enrichment is real and worth reporting as such; it is a much more informative statement than "precision@20 = 0.45" on its own. But `recall@50 = 0.93` cannot be a global figure; it must be per-bait (26 × 50 = 1,300 slots) or *k* must mean something other than a rank cut, and either way it is not comparable to the precision@20 number unless you say so. And `ROC-AUC = 0.845` is not reconcilable with 14-of-57 reachability under a global ranking where unreachable pairs tie at zero; I get 0.49 to 0.61 depending on how many pairs receive a non-zero L3 score. The likeliest explanation is that the AUC is computed over the L3-generated candidate subset rather than all untested pairs, which is precisely the restricted-negative setting that HeaRT was built to expose ([Li, Shomer et al. 2023](https://doi.org/10.48550/arXiv.2306.10453)).

Separately, the pool itself is closed-world. Against a 5,000-protein background the prevalence would be 0.044%, and against a full ~20,000-protein proteome 0.011% — so an open-world precision@20 is a materially different and much harder number. Nothing forces you to report the open-world version as the headline, but you should compute it, because the claim a triage tool actually makes is "test this pair next", and the real candidate set at deployment is the proteome, not the 332 proteins already known to be in the map.

### Degree and hub bias

The strongest recent result here is [Yılmaz, Yorgancioglu & Koyutürk 2025](https://doi.org/10.1073/pnas.2416646122), and it applies to you directly. Generating test sets by sampling edges uniformly at random introduces a bias toward "rich nodes" (those with higher degree), and, importantly, that bias *persists even when different network snapshots are used*, which is the temporal-holdout protocol the ML community recommends. Their framing of the consequence is worth taking seriously: it creates a research cycle where new algorithms accumulate knowledge about well-studied entities while understudied ones stay overlooked. They propose a weighted validation setting that focuses on low-degree nodes, and AWARE strategies for bias-aware training and evaluation.

For your map: bait degrees vary widely, random edge holdout will draw disproportionately from high-degree baits, and any metric pooled across baits will be dominated by them. Report per-bait precision@k, or weight baits equally, and report the bait-degree distribution of the held-out set.

Two convergent results: [Li et al. 2025](https://doi.org/10.1186/s12915-025-02231-w) show that the scale-free property of biological networks biases both training and evaluation of ML models for molecular interactions, and propose degree-distribution-balanced sampling; and [Lannelongue & Inouye 2024](https://doi.org/10.1093/bioinformatics/btae012) built an explicit benchmarking framework (B4PPI) and found that functional-genomics-based and sequence-based models are complementary, the former best on lone proteins, the latter specialising in interactions involving hubs, and that with functional genomic data, algorithm design has little impact on performance. That last clause should give anyone pause before investing in a fancier predictor.

### Negatives

Your evaluation has no explicit negative set (untested pairs are implicit negatives), which is the standard choice and mostly the right one, but the literature has specific warnings.

[Neumann, Roy, Minhas & Ben-Hur 2022](https://doi.org/10.3389/fbinf.2022.1083292) is the host–pathogen-specific treatment and therefore the most relevant. Their argument: choosing random non-interacting pairs as negatives yields a very small false-negative rate because interactomes are only partially known, *especially* for host–pathogen interactions; whereas the popular fix of selecting negatives with low sequence similarity to the positives makes the problem much easier than it really is and produces over-optimistic accuracy. In other words, your implicit-negative choice is the defensible one; do not "improve" it by filtering.

Two newer approaches if you ever move to a supervised setting: topology-driven negative sampling based on higher-order network characteristics ([Chatterjee et al. 2025](https://doi.org/10.1093/bioinformatics/btaf148)) and degree-distribution-balanced sampling ([Li et al. 2025](https://doi.org/10.1186/s12915-025-02231-w)).

### Leakage

You are largely insulated from this because your predictor has no learned parameters, but two items still bite. First, the general lesson: [Bernett, Blumenthal & List 2024](https://doi.org/10.1093/bib/bbae076) showed that flawed evaluation schemes and test-set leakage had obscured the fact that sequence-based PPI prediction remains an open problem, and the same group's follow-up found that on leakage-reduced data, deep models of varying complexity all plateau at an accuracy of 0.65 regardless of architecture, with ESM-2 embeddings explaining the apparent gains ([Reim et al. 2025](https://doi.org/10.1093/bioinformatics/btaf192)). Their seven guiding questions for detecting leakage in biological ML are a good checklist even for deterministic pipelines ([Bernett et al. 2024](https://doi.org/10.1038/s41592-024-02362-y)). [Dunham & Ganapathiraju 2021](https://doi.org/10.3390/molecules27010041) is the bluntest demonstration: re-implementing published PPI predictors and evaluating them at realistic class balance, several were outperformed by control models built on illogical and random-number features, an effect they attribute to over-characterisation of some proteins in the literature plus the scale-free structure of the network.

Second, the leak that does apply to you: **your node set is derived from the unsplit edge list.** All 332 preys are nodes because all 332 edges define them, including the 57 held out. That is conventional in link prediction, but it is the mechanism behind the closed-world pool above, and it deserves a sentence in your methods rather than silence.

There is also a circularity worth auditing between your enrichment layer and your literature layer. STRING integrates automated text mining of the literature alongside co-expression, conserved genomic context, experimental databases and curated pathways ([Szklarczyk et al. 2023](https://doi.org/10.1093/nar/gkac1000)). If any of your 159 enrichment edges carry text-mining evidence, they are correlated with the same literature your reasoning layer cites and with the PubMed co-mention counts behind your novelty tags — so a "novel" edge could be one that STRING already knew about from text. Rebuilding the enrichment from the experiments and database channels only, and reporting per-channel contributions, would close that loop cleanly and is very much in the spirit of your own no-citation-no-render rule.

### Metric choice

The definitive treatment is [Bi, Jiao, Lee & Zhou 2024](https://doi.org/10.1093/pnasnexus/pgae498): across hundreds of real networks and 26 algorithms, evaluation metrics are significantly inconsistent with one another, different metrics produce remarkably different rankings of algorithms, so no single metric can credibly evaluate performance. Their recommendation is at least two: AUROC, plus one of AUPRC, area under the precision curve, or NDCG; and when negatives greatly outnumber positives, also the area under the generalised ROC curve. They also prove threshold-dependent metrics are essentially equivalent, so if specific thresholds are meaningful in your application, any one of them with those thresholds is fine.

For your use case I would make precision@k primary, because it is the quantity a triage tool is actually judged on, with AUPRC/AP as the required second metric, prevalence stated next to every precision number, and ROC-AUC reported but never alone and never as the headline. The reason AUROC attracts criticism in this task is prevalence: at 0.68% positives, and far lower open-world, the false-positive axis is dominated by the enormous negative class and the curve looks good while the top of the ranking may not be useful.

### Temporal holdout

Temporal holdout, train on an older release, test on edges added later; is the stronger protocol in principle, and it is what protein function prediction settled on. But [Yılmaz et al. 2025](https://doi.org/10.1073/pnas.2416646122) explicitly show the rich-node bias survives the switch to snapshot-based evaluation, so temporal is not automatically unbiased and should be combined with degree-aware weighting.

For your project the good news is that a genuine prospective test is available and cheap. Gordon 2020 is a single release, so there is no later Gordon; but SARS-CoV-2–human interactions curated since 2020 in IntAct/IMEx, plus the independently generated maps in [Gordon et al. Science 2020](https://doi.org/10.1126/science.abe9403) and [Batra et al. 2026](https://doi.org/10.1016/j.chom.2026.04.015), give you edges that were not in your training graph and were not used to build it. Scoring your frozen 2020-derived predictions against post-2020 curated edges is the single most persuasive number you could add, and it is immune to every objection about split construction.

### What a rigorous reviewer would demand

1. One stated candidate universe, with every metric computed on it, and the open-world variant alongside.
2. Baselines: random, degree/preferential attachment, CN/RA/AA at L2, STRING-score-only, and a degree-preserving permutation null.
3. Per-class reporting in the Park & Marcotte sense — at minimum a statement that all held-out pairs are C2 and that C3 is unmeasured.
4. Per-bait stratification and bait-degree-weighted metrics, per Yılmaz et al.
5. At least two metrics per Bi et al., with prevalence stated, and confidence intervals — your median-rank-2 result rests on 14 events and needs an interval, not a point.
6. Multiple seeds. One frozen split is excellent for integrity and insufficient for variance; report the seed-42 split as the pre-registered primary and 20 further seeds as a variance estimate.
7. Explicit statement of which STRING channels contributed, and of the node-set leak.
8. A second and third map, so the claim is about the method and not about Gordon 2020.

---

## The sparsity ceiling

### Published upper bounds

Your hypothesis; that the reachability ceiling reflects map sparsity rather than a flaw in L3; is supported, and there is now a small body of theory to cite for it.

The most quotable result is [Hibshman & Weninger 2023](https://doi.org/10.48550/arXiv.2301.08792), who compute hard upper bounds on how well graph topology alone permits link prediction across many real graphs, and find that "in the sparsest of these graphs the upper bounds are surprisingly low, thereby demonstrating that prediction systems on sparse graph data are inherently limited and require information in addition to the graph topology." That is close to a direct statement of your hypothesis, with the important caveat that it is still a preprint with no journal version I could find, so cite it as such.

The peer-reviewed companion is [Ran, Xu & Jia 2024](https://doi.org/10.1093/pnasnexus/pgae113), who derive the prediction-performance upper bound of a *topological feature*. Two of their results matter to you. The bound depends only on the extent to which the feature is held in missing versus non-existent links — which means it is an empirically measurable quantity in your map, not an abstraction. And because every index built on the same feature shares the same upper bound, the potential of the whole family can be estimated from one member. That has a sharp implication: switching from degree-normalised L3 to CH2-L3 to L3N cannot exceed the length-3-path feature's bound. If you measure that bound and find you are near it, further tuning of L3 variants is wasted effort and the answer must come from a different feature. They verify the pattern on 550 structurally diverse networks and also quantify how much supervised learning lifts the bound, which is a principled way to decide whether to abandon the deterministic predictor.

The INMC benchmark measured interactome predictability directly and the numbers are sobering: structural consistency was above 0.58 for human STRING but below 0.25 for all five other interactomes, "much lower than that of social networks", and both AUPRC and P@500 were small for every interactome except STRING ([Wang et al. 2023](https://doi.org/10.1038/s41467-023-37079-7)). Two lessons. Interactome link prediction is intrinsically low-predictability, so your absolute numbers should not be compared against link-prediction results from social or citation networks. And STRING's anomalous predictability is a warning about using it as ground truth, which I return to under Priority 5.

Finally, [Vlaskin & Altmann 2025](https://doi.org/10.1088/2632-072X/ada07f) built synthetic random graphs incorporating both micro-scale motifs and meso-scale communities and derived theoretical upper bounds for link-prediction performance on them. Their empirical finding; that the performance of all methods correlates with theoretical predictability, that no single method is universally superior, and that different methods exploit different structures, is the cleanest available template for the experiment you actually want to run.

### The mechanism in your map

Where I would push back is on the mechanism. Your 14-of-57 is not a generic sparsity effect; it is a specific and computable consequence of two facts established earlier. Every length-3 bait→prey path in your graph is AP-MS + STRING + STRING, so a held-out prey is L3-reachable if and only if it lies within two STRING steps of another prey of the *same* bait. Your STRING layer has 159 edges over 332 preys, a mean prey STRING degree below 1, so most preys have no STRING partner at all and are unreachable by construction.

That reframes the claim. The lever is not "a denser interactome"; it is a denser *enrichment layer*, and you control it. The prediction "path-based methods get substantially better on denser interactomes" is probably true but you are not currently testing it — you are testing sensitivity to a STRING confidence threshold you chose.

### Experiments that would falsify it

1. **Sweep the STRING threshold** (700 → 400 → 150, and physical-only versus all channels) and plot reachability and precision@k against the resulting prey–prey edge count. If reachability climbs and precision holds, your hypothesis survives in its corrected form. If precision collapses as reachability rises, the ceiling was protecting your precision rather than limiting it — that is the falsification, and it is the most likely single outcome.
2. **Extend the STRING background beyond the 332 preys** to the human proteome. This tests the density hypothesis and fixes the closed-world candidate pool in the same experiment, which is why I would run it first.
3. **Measure the length-3 feature's upper bound** on your map using the Ran et al. framework, and report how far L3 sits below it. If the gap is small, stop optimising the predictor.
4. **Density-matched subsampling** of a dense map. BioPlex 3.0 or HuRI thinned to your density and star-like prey structure, so density varies while assay and organism are held fixed.
5. **Run the pipeline on the other bipartite pathogen maps** (below). If the reachable fraction tracks enrichment-layer density across five maps, that is a real relationship rather than one data point.

One statistical note: 14 reachable edges with a median rank of 2 is a small-sample result. Report a bootstrap interval on that median. As it stands the claim "when L3 can reach a held-out edge, its median rank is 2" is your most attractive finding and your least well-supported one.

---

## Structure, sequence and fusion

### AlphaFold for screening

Your understanding is correct, and the evidence for it got much stronger recently.

The reference point for screening performance is [Bryant, Pozzati & Elofsson 2022](https://doi.org/10.1038/s41467-022-28865-w): with optimised multiple sequence alignments, AlphaFold2 produced acceptable-quality models (DockQ ≥ 0.23) for 63% of heterodimers, and their predicted-DockQ score identified 51% of all interacting pairs at a 1% false-positive rate. That 51%-at-1%-FPR figure is the most concrete screening operating point in the literature and the number to quote. Scaling up degrades it: [Burke et al. 2023](https://doi.org/10.1038/s41594-022-00910-8) modelled 65,484 human protein interactions and obtained only 3,137 high-confidence models, under 5%, of which 1,371 had no homology to a known structure. Coverage, not accuracy, is the binding constraint, and it is quantified independently in [Kosoglu et al. 2023](https://doi.org/10.1093/bib/bbad496).

The approaches that work at proteome scale add a coevolution prefilter rather than folding everything: [Humphreys et al. 2021](https://doi.org/10.1126/science.abm4805) for core eukaryotic complexes, and [Humphreys et al. 2024](https://doi.org/10.1038/s41564-024-01791-x), who searched 78 million protein pairs across 19 human bacterial pathogens with RoseTTAFold2-Lite and identified 1,923 confidently predicted complexes involving essential genes plus 256 involving virulence factors, then tested 12 predictions experimentally and validated half. A ~50% hit rate on a hand-picked dozen is a realistic expectation for well-filtered structural predictions in a pathogen system, and it is the closest published analogue to what Cartograph proposes to do. The current best for human is [Zhang et al. 2025](https://doi.org/10.1126/science.adt1630), which screened 200 million human protein pairs and predicted 17,849 interactions at an expected precision of 90%, of which 3,631 were absent from previous experimental screens; but achieving that required sevenfold-deeper alignments harvested from 30 petabytes of unassembled genomic data plus a network trained on domain-domain interactions from 200 million predicted structures. That is not a pipeline you replicate on a laptop, and its 17,849 predictions over 200 million pairs is a reminder of how conservative a well-calibrated structural screen has to be.

The paper that most directly settles your question, and the one I would put in your README, is [Lambourne et al. 2026](https://doi.org/10.1038/s41467-026-70942-x). They built an experimental framework to assess AI-driven interactome predictions for yeast and human, and found that the quality of high-confidence predictions is on par with established experimental approaches, but that in proteome-wide screening the AI approaches underperform at discovering *strictly novel* interactions: their yeast map identified more than 40-fold more novel PPIs than its AI counterpart. Strikingly, AlphaFold supplied structural models for a substantial number of experimentally identified interactions that the virtual screens had missed. Their conclusion is that at this stage the main contribution of AI prediction is to provide quaternary structure models for experimentally identified interactions.

That sentence is an argument for your architecture. A map that proposes and a structure layer that explains is exactly the division of labour the evidence supports; a structure layer that proposes is not.

### Interface scores and their biases

The core problem is that ipTM and pDockQ are model-*quality* scores being repurposed as interaction *classifiers*, and there was until recently no rigorously benchmarked method for the second task — a point made explicitly by [Mischley et al. 2026](https://doi.org/10.7554/eLife.98179), whose PPIscreenML classifier, trained to separate AlphaFold2 models of real pairs from models of compelling decoys, outperforms both pDockQ and ipTM at it. The same diagnosis motivates SPOC: standard AlphaFold-Multimer confidence metrics "do not reliably separate relevant PPIs from an abundance of false positive predictions", so [Schmid & Walter 2025](https://doi.org/10.1016/j.molcel.2025.01.034) trained an omics-informed classifier and applied it to an all-by-all matrix of nearly 300 human genome-maintenance proteins, releasing ~40,000 scored predictions at predictomes.org where you can also score your own. A third approach converts predicted aligned error into calibrated contact probabilities ([Badonyi & Toth-Petroczy 2026](https://doi.org/10.1002/pro.70760)); their Pinc score is well calibrated against the fraction of native contacts in experimental structures and gives residue-level confidence, which is directly relevant to your interface-residue displays.

On the length bias: confirmed, and now formally documented in exactly the paper you had in mind. [Todor et al. 2026](https://doi.org/10.1038/s44320-026-00189-7) predicted all 113,050 pairwise interactions in *Mycoplasma genitalium* using only 2,027 AlphaFold3 jobs, roughly 100-fold fewer jobs and about twofold faster inference than the paired approach; and report that the resulting unbiased, comprehensive dataset "revealed a previously unappreciated but widespread size bias in AlphaFold interface scores". Note that this is a bacterium, not human, and that the follow-up extending it to a mycobacterial pathogen is still a preprint. Your existing size correction is therefore consistent with the source, but you should describe the bias as summed-chain-length-dependent per that paper rather than as a general "ipTM rises with length" claim, and you should state the functional form you fit.

### Protein language models

The picture here is less encouraging than the headline papers suggest, and the reason is evaluation rather than architecture. After leakage-reduced splits were introduced, deep sequence-based PPI predictors of widely varying complexity, per-protein versus per-token embeddings, self- versus cross-attention; all plateaued at an accuracy of 0.65, with ESM-2 embeddings accounting for the apparent gains irrespective of architecture, and the models demonstrably unable to learn a contact map as an intermediate representation ([Reim et al. 2025](https://doi.org/10.1093/bioinformatics/btaf192)). The authors' inference is that other input types, structure in particular, may be necessary. This follows the same group's demonstration that flawed evaluation and test-set leakage had masked the fact that sequence-based prediction remains open ([Bernett, Blumenthal & List 2024](https://doi.org/10.1093/bib/bbae076)). A recent preprint adds that protein language models exploit species-level taxonomic signal present in negative sets ([Hallee et al. 2025](https://doi.org/10.1101/2025.10.07.681002)), unreviewed, but a plausible mechanism for inflated cross-species numbers.

Read the current state-of-the-art claims against that backdrop: SENSE-PPI for within-, across- and between-species reconstruction ([Volzhenin et al. 2024](https://doi.org/10.1016/j.isci.2024.110371)), the paired-sequence model PPLM ([Liu et al. 2026](https://doi.org/10.1038/s41467-026-70457-5)), and the D-SCRIPT lineage's latest ([Ullanat et al. 2026](https://doi.org/10.1038/s41467-025-67971-3)). These may well be real advances; the field's own benchmarking history says wait for third-party leakage-controlled replication before betting a product on them. For host–pathogen specifically, the difficulties are compounded by tiny positive sets and negative-set artefacts ([Sahni et al. 2025](https://doi.org/10.1016/j.csbj.2025.11.037)), and the older critical assessment of plant–pathogen PPI prediction is a useful methodological precedent for the bipartite inter-species setting ([Yang et al. 2019](https://doi.org/10.1093/bib/bbx123)).

### Fusion: attempted, not solved

This is the most useful answer I can give you on Priority 4, so I will be precise about what exists.

**Fusion of structure with non-structural evidence is solved to the level of a working proteome-scale resource.** PrePPI combines structural and non-structural evidence in a Bayesian framework to compute a likelihood ratio for essentially every possible protein pair, with the structural component derived from template-based modelling and now leveraging AlphaFold structures parsed into domains; the human database holds about 1.3 million predicted interactions behind a web server ([Petrey et al. 2023](https://doi.org/10.1016/j.jmb.2023.168052), updated in [Velez et al. 2026](https://doi.org/10.1016/j.jmb.2026.169735)). The same group's ZEPPI scores interface models by coevolution and conservation restricted to interfacial residues, which lets it work with shallow alignments and run proteome-wide ([Zhao et al. 2024](https://doi.org/10.1073/pnas.2400260121)). If you want to know whether your product thesis has been done, PrePPI has already done the structure-plus-evidence half of it, at proteome scale, with a public server.

**Fusion of topology with sequence is solved and validated experimentally.** Topsy-Turvy synthesises the sequence-based bottom-up view with the network-based top-down view in a single model, using transfer learning at training time so that inference needs only sequence ([Singh et al. 2022](https://doi.org/10.1093/bioinformatics/btac258)); TT3D adds precomputed 3D structure via Foldseek ([Sledzieski et al. 2023](https://doi.org/10.1093/bioinformatics/btad663)); GLIDE combines local indices with diffusion-state embeddings for the same purpose ([Devkota et al. 2020](https://doi.org/10.1093/bioinformatics/btaa459)). And the strongest single datum is the one from Priority 1: in the INMC benchmark the best experimentally validated method, at 87.4% precision on its top 500, was MPS(B&T) — MPS(T) plus pairwise sequence similarity. Fusion of topology and sequence measurably beat topology alone in a blinded wet-lab test.

**Fusion of many topological features is solved in principle.** [Ghasemian et al. 2020](https://doi.org/10.1073/pnas.1914950117) is the reference: stacking large numbers of predictors approaches near-optimal performance, and no individual predictor is close. The natural extension of your architecture is to treat L3, L2, STRING score, structural confidence and literature support as features in a stacked model — with the caveat that stacking requires supervised training data, which puts you back into the split-design problem, and that the Cannistraci group contests the claim.

**Your specific combination is open.** I found no published system that fuses topology, structure-model confidence, sequence and *literature* evidence into a single calibrated ranking with per-source held-out evaluation. The incumbents fuse heterogeneous evidence into a score without a literature channel or per-hypothesis provenance — STRING itself ([Szklarczyk et al. 2023](https://doi.org/10.1093/nar/gkac1000), now [2025](https://doi.org/10.1093/nar/gkae1113)), FunCoup 6 ([Buzzao et al. 2025](https://doi.org/10.1093/nar/gkae1021)), HumanNet v3 ([Kim et al. 2022](https://doi.org/10.1093/nar/gkab1048)) and IID, which now carries over a million experimentally detected human PPIs plus MEGADOCK interface predictions for 53,647 of them ([Kotlyar et al. 2026](https://doi.org/10.1093/nar/gkaf1259)). The closest thing to your per-hypothesis flow is [Trepte et al. 2024](https://doi.org/10.1038/s44320-024-00019-8), which prioritises interactions using quantitative binary-assay data or AlphaFold-Multimer predictions and carries them through to early-stage drug discovery. So: the fusion is attempted and partly solved, the calibrated multi-channel version with literature is open, and the honest framing of your contribution is the *evaluation harness and provenance discipline* around the fusion rather than the fusion itself.

---

## Benchmark datasets

The accompanying `ppi_benchmark_datasets.csv` has the full table with per-row citations and DOIs; scale figures in it are only those I could verify from the cited abstract, and rows where the abstract does not state counts say so rather than guessing.

### Bipartite pathogen–host maps

These are your apples-to-apples comparisons and there are more than you thought. In rough order of usefulness:

[Jäger et al. 2011](https://doi.org/10.1038/nature10719) mapped all 18 HIV-1 proteins and polyproteins against host proteins in HEK293 and Jurkat cells, reporting 497 high-confidence HIV–human interactions involving 435 human proteins; same assay family, same bipartite shape, more preys per bait than Gordon, and two cell lines so you get a reproducibility axis. [Penn et al. 2018](https://doi.org/10.1016/j.molcel.2018.07.010) is the sparsest comparator: 187 Mtb–human interactions involving 34 secreted Mtb proteins, which is close to your regime and would test whether your reachability ceiling generalises. [Shah et al. 2018](https://doi.org/10.1016/j.cell.2018.11.028) compared DENV and ZIKV across human and mosquito hosts, four parallel bipartite maps, which is the natural test bed for a conservation channel. [Davis et al. 2015](https://doi.org/10.1016/j.molcel.2014.11.026) affinity-tagged all 89 KSHV proteins and identified over 500 virus–host interactions, giving you a larger bait set. [Haas et al. 2023](https://doi.org/10.1038/s41467-023-41442-z) mapped 332 influenza A–human interactions across three IAV strains and three human cell types; coincidentally the same edge count as Gordon 2020, which makes it an unusually clean paired comparison.

And the two you dismissed: [Gordon et al. Science 2020](https://doi.org/10.1126/science.abe9403) for SARS-CoV-2, SARS-CoV-1 and MERS-CoV, and [Batra et al. 2026](https://doi.org/10.1016/j.chom.2026.04.015) for SARS-CoV-2 versus RaTG13 in human and bat cells.

For unipartite human comparators, the standard set is HuRI with roughly 53,000 binary interactions from all-by-all Y2H ([Luck et al. 2020](https://doi.org/10.1038/s41586-020-2188-x)); BioPlex 3.0 with 118,162 interactions among 14,586 proteins from affinity purification of 10,128 proteins in 293T cells, plus a second network from 5,522 immunoprecipitations in HCT116 ([Huttlin et al. 2021](https://doi.org/10.1016/j.cell.2021.04.011)) — the dual-cell-line design also makes it the reference for context specificity; hu.MAP 2.0's roughly 7,000 complexes integrated from over 15,000 mass-spectrometry experiments ([Drew et al. 2021](https://doi.org/10.15252/msb.202010016)); and OpenCell ([Cho et al. 2022](https://doi.org/10.1126/science.abi6983)). For direct-versus-indirect contact labels there is now DirectContacts2 ([Claussen et al. 2026](https://doi.org/10.1038/s41467-026-75863-3)).

The field does not have one canonical benchmark, but there are three de facto ones: the INMC six-interactome suite for network-based prediction ([Wang et al. 2023](https://doi.org/10.1038/s41467-023-37079-7)), which is the closest to a standard in your subfield; the OGB link-prediction datasets for the ML community ([Hu et al. 2020](https://doi.org/10.48550/arXiv.2005.00687)); and the leakage-reduced splits from the Bernett/List line for sequence-based methods. A newer graph-level PPI benchmark, PRING, reframes evaluation from pairs to reconstructed graphs and is worth watching, though it is still a preprint ([Zheng et al. 2025](https://doi.org/10.48550/arXiv.2507.05101)).

### What to avoid

**Do not use STRING as ground truth while using STRING as a feature.** This is your most acute circularity risk and it is empirically visible: in the INMC benchmark, human STRING had structural consistency above 0.58 against below 0.25 for the five experimental interactomes, and it was the only interactome on which methods achieved non-trivial AUPRC and P@500 ([Wang et al. 2023](https://doi.org/10.1038/s41467-023-37079-7)). A network that has already been smoothed by integration and prediction looks far more predictable than biology is. Any result you report on a STRING-derived benchmark will be read as an artefact, correctly. This also argues for checking the provenance of the OGB protein datasets before using them as a physical-PPI benchmark, since association is a different label from physical binding.

**Treat literature-curated positives as degree-biased.** [Dunham & Ganapathiraju 2021](https://doi.org/10.3390/molecules27010041) found published PPI predictors beaten by control models on random and illogical features once class balance was realistic, and attributed it to over-characterisation of some proteins in the literature combined with the scale-free network structure. That has a direct implication for your novelty tags: a PubMed co-mention count of zero conflates "genuinely unstudied" with "not yet studied because nobody has looked", and the same study bias that inflates predictor performance will make your novel-versus-known split correlate with protein popularity. Report co-mention counts alongside total publication counts per protein so a reader can see the confound.

**Be careful with AP-MS positives generally.** The CRAPome exists because affinity purification has systematic contaminants ([Mellacheruvu et al. 2013](https://doi.org/10.1038/nmeth.2557)); your frequent-flyer filter is the right instinct and the CRAPome is the citation for it.

### Licensing

I was not able to verify current licence terms for these resources from the literature — licences live on the resource sites and in their terms pages, not in the papers, and I did not retrieve them. Rather than guess at specific licences, the practical pointer is that the OmniPath project maintains per-resource licensing metadata precisely because this is hard: their documentation notes that KEGG data have not been freely available since 2011, and they carry an explicit label for resources whose copyright terms are unclear or where redistribution permission was granted directly. Since you are shipping MIT-licensed code with committed data snapshots, check terms individually before redistribution, and pay particular attention to curated-complex resources such as CORUM ([Steinkamp et al. 2025](https://doi.org/10.1093/nar/gkae1033)) and to attribution requirements for STRING, which you already redistribute in cached form.

---

## Open problems and positioning

### What reviews call unsolved

Recent reviews of the field ([Greenblatt et al. 2024](https://doi.org/10.1016/j.cell.2024.10.038); [Durham et al. 2023](https://doi.org/10.1016/j.tibs.2023.03.003); [Richards et al. 2021](https://doi.org/10.15252/msb.20188792)) converge on a consistent list, and the genuinely open items are:

Coverage remains the dominant problem, and as of 2026 AI screening does not close it; the strongest statement being that an experimental yeast map found over 40-fold more novel interactions than its AI counterpart ([Lambourne et al. 2026](https://doi.org/10.1038/s41467-026-70942-x)). Context specificity is unsolved and increasingly clearly so: interactomes differ between cell lines ([Huttlin et al. 2021](https://doi.org/10.1016/j.cell.2021.04.011)), and both isoform-level and variant-level edge rewiring are active problems ([Guo et al. 2026](https://doi.org/10.1186/s13059-026-04057-3); and, as a preprint, [Stewart et al. 2026](https://doi.org/10.64898/2025.12.20.695738)). Distinguishing direct from indirect association in co-complex data is still being worked out ([Claussen et al. 2026](https://doi.org/10.1038/s41467-026-75863-3)). Structural coverage of the interactome remains low ([Kosoglu et al. 2023](https://doi.org/10.1093/bib/bbad496); [Qi et al. 2026](https://doi.org/10.1038/s41467-026-70884-4)). And the absence of reliable negatives, plus the circularity of the available ground truth, is now recognised as a first-order methodological obstacle rather than a nuisance; that is the through-line of the entire Priority 2 literature.

Worth noting that community-assessment infrastructure exists in adjacent problems and mostly does not exist here: module identification had a DREAM challenge ([Choobdar et al. 2019](https://doi.org/10.1038/s41592-019-0509-5)), and the INMC exercise is the nearest equivalent for PPI link prediction. There is room for a standing, versioned benchmark in this subfield, and that is closer to what you have built than a prediction method is.

### Prior art that already ranks edges

Directly, yes, "rank the missing edges and show the evidence" exists in several forms. STRING has done ranked association with per-channel evidence for two decades. FunCoup 6 and HumanNet v3 do ranked functional coupling with evidence provenance. IID 2025 adds detection types and docking-derived interface predictions for 53,647 PPIs. PrePPI serves ~1.3 million ranked structure-informed human predictions with a query interface, template complexes and per-prediction evidence. Interactome INSIDER provides predicted interface residues across 185,957 interactions ([Meyer et al. 2018](https://doi.org/10.1038/nmeth.4540)). Predictomes.org publishes ~40,000 classifier-scored AlphaFold models and lets users score their own. And in your exact domain, P-HIPSTer predicted about 282,000 pan-viral–human interactions from structural information with a reported experimental validation rate of roughly 76% ([Lasso et al. 2019](https://doi.org/10.1016/j.cell.2019.08.005)); that one you should benchmark against directly, because it is the closest published thing to Cartograph's problem and it predates you by seven years.

The agentic side is separate and moving fast: multi-agent systems for hypothesis generation and experimental design now appear in high-profile venues ([Ghareeb et al. 2026](https://doi.org/10.1038/s41586-026-10652-y); [Swanson et al. 2025](https://doi.org/10.1038/s41586-025-09442-9); [Gao et al. 2024](https://doi.org/10.1016/j.cell.2024.09.022); and as a preprint, [Gottweis et al. 2025](https://doi.org/10.48550/arXiv.2502.18864)). None of these does calibrated PPI ranking against a locked benchmark.

### Where Cartograph is differentiated

Not in the predictor, and not in "ranked predictions with evidence" — both exist. The defensible claims are narrower and, I think, more valuable:

A locked, pre-registered benchmark reported per map, with the split frozen before the predictor was written and a test that the predictor cannot import the evaluator. Nothing in the prior art above does this, and the Priority 2 literature is an extended argument for why it matters. A deterministic citation gate, no citation, no render; which is the operational answer to the fabrication problem that makes reviewers distrust LLM-generated mechanism. Structure-derived interface residues computed from deposited coordinates rather than copied from prose, with predicted models labelled predicted. And the triage framing itself, which is well-timed: pooled-AlphaFold3 makes genome-scale candidate lists cheap ([Todor et al. 2026](https://doi.org/10.1038/s44320-026-00189-7)) at exactly the moment when the experimental assessment says AI cannot yet do the discovery ([Lambourne et al. 2026](https://doi.org/10.1038/s41467-026-70942-x)). Something has to decide what to test first, and that is a benchmarking-and-provenance problem more than a modelling one.

The corollary is a positioning change I would make: lead with the harness, not the predictor. Treat L3 as one channel among several, and let the contribution be that every channel gets scored against the same locked benchmark and every claim carries a verified citation.

---

## Evidence strength of the key claims

You asked me to separate the well-replicated from the single-group from the unscrutinised. The claims this review rests on, tiered:

| claim | tier | basis |
|---|---|---|
| Random CV over known edges measures the rarest case (C1) | **well replicated** | Park & Marcotte 2012, plus the entire DTI evaluation literature and the leakage line 2024-2025 |
| L3-principle methods are top-tier for PPI link prediction | **strong, single large study** | Wang et al. 2023 (26 methods, 6 interactomes, wet-lab validated); consistent with Yuen & Jansson 2023 |
| Metrics disagree about which algorithm wins | **strong** | Bi et al. 2024, hundreds of networks, 26 algorithms |
| Uniform edge sampling biases toward high-degree nodes | **strong, converging** | Yılmaz et al. 2025 (PNAS), Li et al. 2025 (BMC Biol), Lannelongue & Inouye 2024 |
| GNN link-prediction gains shrink under hard negatives | **strong within ML** | Li, Shomer et al. 2023 (NeurIPS D&B); not yet replicated on PPI specifically |
| AlphaFold screening underperforms experiment for novel PPIs | **strong, recent, experimental** | Lambourne et al. 2026; consistent with Burke 2023 coverage and Bryant 2022 operating point |
| ipTM/pDockQ are poor interaction classifiers | **converging, three groups** | Schmid & Walter 2025, Mischley et al. 2026, Badonyi & Toth-Petroczy 2026 |
| Sequence-based PPI prediction plateaus once leakage is removed | **single group, replicated internally** | Bernett et al. 2024 ×2, Reim et al. 2025 — the same lab; awaits third-party confirmation |
| 3-hop beats 2-hop in general | **contested / weak** | Zhou et al. 2021: 55.88% win rate over 128 networks |
| CH2-L3/CH3-L3 beat L3 | **single group** | now peer-reviewed (NeurIPS 2025) but essentially all head-to-head comparisons are from the originating group; CH1 did not top Wang et al. 2023 |
| Stacking approaches the achievable ceiling | **contested** | Ghasemian et al. 2020 (PNAS) versus a Cannistraci-group rebuttal preprint |
| Sparse graphs have low topology-only upper bounds | **preprint** | Hibshman & Weninger 2023, unreviewed; the peer-reviewed neighbour is Ran et al. 2024 |
| AlphaFold interface scores carry a size bias | **single study, bacterium** | Todor et al. 2026; the pathogen follow-up is a preprint |
| pLMs exploit taxonomic signal in negatives | **preprint** | Hallee et al. 2025, unreviewed |

Where the field genuinely disagrees, and I am not picking a winner: whether near-optimal link prediction comes from adaptive selection of one topological model or from stacking many (Cannistraci group versus Clauset group); and whether path-based topological indices have more headroom at all, given that all indices on one feature share an upper bound.

## Three things I would change, in priority order

**1. Fix the candidate universe, then re-report everything.** Define one candidate set explicitly, compute every metric on it, and publish the arithmetic next to the numbers, prevalence, enrichment over prevalence, and the maximum attainable value of each metric. This resolves the `recall@50 = 0.93` impossibility and the ROC-AUC/reachability tension, both of which a reviewer will find immediately. Then add the open-world variant with a proteome-scale background, because that is the population your tool addresses at deployment. Say explicitly that all 57 held-out pairs are class C2 in the sense of [Park & Marcotte 2012](https://doi.org/10.1038/nmeth.2259) and that C3 is unmeasured; that framing turns your unusual split from a hidden liability into a stated strength.

**2. Add the baselines, and stratify by bait degree.** Random, preferential attachment (which in your map collapses to bait degree and is therefore a pure degree null), CN/RA/Adamic-Adar at L2 on the enriched graph, and above all a STRING-score-only guilt-by-association control. Until that control exists you cannot claim topology is contributing anything beyond STRING, and given that every L3 path in your map traverses two STRING edges, the null hypothesis that it is not is quite live. Report per-bait metrics or degree-weighted metrics per [Yılmaz et al. 2025](https://doi.org/10.1073/pnas.2416646122), make precision@k primary with AUPRC as the required second metric per [Bi et al. 2024](https://doi.org/10.1093/pnasnexus/pgae498), and bootstrap the median-rank-2 result.

**3. Test the corrected sparsity hypothesis on more than one map.** Sweep the STRING threshold and plot reachability against precision — that single figure would be the most informative plot in the project, and it is a few hours' work. Extend the STRING background past the 332 preys. Then run the whole pipeline on Jäger 2011 (HIV), Penn 2018 (Mtb) and Haas 2023 (influenza A), and score your frozen Gordon-2020 predictions prospectively against SARS-CoV-2 edges curated since 2020 and against the SARS-CoV-1/MERS and bat/human maps. Five maps and one prospective test would move the claim from "our method got 0.45 on our map" to "path-based triage recovers held-out edges at a rate that tracks enrichment-layer density across five pathogen interactomes", which is a result rather than a demo.

An honourable mention that did not make the top three: replace the plain-L3 predictor with MPS(T)/RNM, which are the methods with the best independent track record ([Wang et al. 2023](https://doi.org/10.1038/s41467-023-37079-7)). I put it fourth deliberately. Given the upper-bound result of [Ran et al. 2024](https://doi.org/10.1093/pnasnexus/pgae113); that all indices built on the same feature share one ceiling; a better length-3 index cannot rescue a map where only 14 of 57 held-out edges are reachable at all. Measure the ceiling first; swap the predictor only if you are not already near it.

