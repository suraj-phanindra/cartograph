# Cartograph: Claude Science evidence-gathering checklist

Purpose: the exact lookups to run in Claude Science this week so its output drops straight into the Claude Code build. Each item names the goal, a paste-ready Science prompt, and the artifact it produces plus where that artifact lands in the repo.

How to use: keep an `/evidence` folder in the Cartograph repo. Everything Science produces gets saved there as a file (JSON or CSV), and Claude Code reads from `/evidence`, never from a live call on the demo path. Science grounds the biology; Code builds the software; nothing on the demo path waits on the network.

All specific interactions below are grounded in real literature (see Sources), but still ask Science to confirm each against the loaded Gordon 2020 data before you rely on it. Verify, do not assume.

---

## Lookup 1: Lock the ground truth (feeds the graph and the evaluator)
Goal: get the exact Gordon 2020 edge list and confirm the counts you will quote. This is the ground truth the whole evaluator depends on.

Paste into Science:
```
I'm working from Gordon et al. 2020, "A SARS-CoV-2 protein interaction
map reveals targets for drug repurposing" (Nature 583:459-468). Pull the
supplementary high-confidence interaction table. Give me: (1) the exact
count of viral bait proteins, (2) the exact count of high-confidence
virus-human interactions, (3) the count of druggable host proteins and
the drugs, and (4) the full bait-to-prey edge list as a table I can
export. Flag any discrepancy with the commonly cited numbers (26 baits,
332 interactions, 66 druggable proteins, 69 drugs).
```
Output: `/evidence/gordon2020_edges.csv` (the ground-truth edge list) and the confirmed counts. Feeds the graph loader and the frozen held-out split.

---

## Lookup 2: Pick the demo proteins by literature richness (feeds the demo)
Goal: choose the 2 to 3 viral proteins to feature, based on which host interactions have the clearest, best-documented mechanism. Demo strength depends on citation richness.

Paste into Science:
```
For these SARS-CoV-2 viral proteins and their known human interactors,
rank them by how rich and mechanistically clear the published literature
is: Orf6 (Nup98/Rae1), Orf9b (TOM70/TOMM70A), N (G3BP1/G3BP2), E
(BRD2/BRD4), Orf3a (HOPS complex, VPS39). For each, give a one-paragraph
mechanism, the count of strong primary papers, and whether solved
structures exist. I want the two or three with the deepest, cleanest
evidence for a live demo.
```
Output: `/evidence/demo_protein_shortlist.md`. Picks the demo set. Expect Orf6 and Orf9b to top it (both have solved structures and heavy literature).

---

## Lookup 3: Build the evidence pack for the demo edges (feeds the Reader agent and the demo card)
Goal: for each chosen demo edge, cache the specific papers behind it and the neighboring edges, so the on-screen citation card and the Reader subagent pull from a local file.

Paste into Science (repeat per demo edge):
```
For the interaction [Orf6 - Nup98/Rae1], give me the 3 to 5 strongest
primary papers with PMID and DOI, and for each a one-sentence extraction
of the mechanistic claim it supports. Then do the same for the immediate
neighboring host-host edges (e.g., Nup98-Rae1 complex). Return as JSON:
edge, papers[{pmid, doi, one_line_mechanism}], confidence.
```
Output: `/evidence/edge_packs/orf6_nup98.json` and one per demo edge. This is the literature cache. The Reader agent reads it; the demo card renders it.

---

## Lookup 4: The flagship held-out worked example (the money shot)
Goal: script the single prediction the demo hinges on. Hold out one real high-confidence edge and recover it deterministically through a documented complex, then cite the chain.

The candidate: Orf6 binds both Nup98 and Rae1, and Nup98-Rae1 is a well-documented complex. Hold out Orf6-Rae1, keep Orf6-Nup98, and L3 should recover Orf6-Rae1 through the Nup98-Rae1 edge (added by STRING enrichment). The literature chain is deep and the mechanism is airtight.

Paste into Science:
```
Confirm from the literature: (1) are both Orf6-Nup98 and Orf6-Rae1
supported as SARS-CoV-2 Orf6 interactions, (2) is Nup98-Rae1 a documented
human protein complex, and (3) does the mechanism (Orf6 docking on the
Nup98-Rae1 complex at the nuclear pore to block nucleocytoplasmic
transport and interferon signaling) hold up. Give me the papers with
PMIDs for each link in that chain. I want to hold out Orf6-Rae1, predict
it back through Nup98-Rae1, and cite this chain live.
```
Output: `/evidence/worked_example_orf6.json`. This is the scripted demo prediction plus its citation chain. Prepare a second one (Orf9b-TOM70 neighborhood) as backup.

---

## Lookup 5: External CRISPR gold standard (feeds Option B validation, stretch)
Goal: an independent host-factor set the model never saw, to validate predicted host factors against. This is the "and it generalizes to independent ground truth" flourish.

Paste into Science:
```
Find the major genome-wide CRISPR host-factor screens for SARS-CoV-2
(e.g., Wei et al. 2021 Cell; Daniloski et al. 2021 Cell; plus Baggen,
Schneider, Wang, Zhu 2021; Biering et al. 2022 Nat Genet). For each,
extract the top pro-viral host-factor hit genes. Then build a consensus
list of genes that appear as hits in two or more screens, and flag which
of these overlap with the human prey in the Gordon 2020 interactome.
Note that hits are known to be cell-type specific, so I want the
cross-screen consensus, not any single screen.
```
Output: `/evidence/crispr_gold_standard.csv` (consensus hit set + overlap with prey). Feeds the Option B evaluator. Only wire this in if the core is solid by Day 6.

---

## Lookup 6: Distill the domain rules file (your visible moat)
Goal: a small curated JSON of biology priors that improves candidate scoring and hypothesis quality. This is the MaestrIA-style domain file that lifted an eval 74 to 81, and it is the moat a judge cannot say the model supplied on its own.

Paste into Science:
```
From the SARS-CoV-2 interactome literature, give me a compact set of
biology priors useful for scoring candidate viral-host interactions:
(1) known human complexes among the Gordon prey (e.g., Nup98-Rae1, HOPS,
stress-granule G3BP1/G3BP2, mitochondrial import TOM complex), (2)
common interaction types by viral protein family, (3) any documented
false-positive-prone patterns in AP-MS interactome data. Return as JSON
I can inject into candidate scoring and into the Skeptic agent's checks.
```
Output: `/evidence/cartograph_domain.json`. Injected into candidate scoring and the Skeptic agent. Reference it explicitly in the demo and submission as your domain moat.

---

## Sequencing this against the build
- Day 1 to 2: Lookup 1 (ground truth) alongside loading the map. Lookup 2 (pick demo proteins).
- Day 3: Lookups 3 and 4 (evidence packs + the worked example) as you build the Reader/Skeptic/Curator agents.
- Day 4: Lookup 6 (domain JSON) to lift candidate quality before you lock the demo.
- Day 6: Lookup 5 (CRISPR gold standard) only if the core is solid.

## One caveat to respect
CRISPR host-factor hits are cell-type specific, so any single screen is a noisy gold standard. Use the cross-screen consensus, and present Option B as corroboration, not proof. Keep Option A (the frozen held-out edges) as your guaranteed number.

---

## Sources
- Gordon et al. 2020, Nature: https://www.nature.com/articles/s41586-020-2286-9
- Orf6 hijacks Nup98 to block STAT nuclear import (Miorin et al. 2020, PNAS): https://pubmed.ncbi.nlm.nih.gov/33097660/
- Orf6 disrupts nucleocytoplasmic transport via Rae1 and Nup98: https://pmc.ncbi.nlm.nih.gov/articles/PMC8092196/
- Crystal structure of Orf9b in complex with TOM70 (Nat Commun 2021): https://www.nature.com/articles/s41467-021-23118-8
- Orf9b binding to TOM70 prevents HSP90 interaction (2022): https://pubmed.ncbi.nlm.nih.gov/35643212/
- Wei et al. 2021, Genome-wide CRISPR screens reveal host factors critical for SARS-CoV-2 infection (Cell): https://researchgate.net/publication/348848456_Genome-wide_CRISPR_Screens_Reveal_Host_Factors_Critical_for_SARS-CoV-2_Infection
- Bidirectional genome-wide CRISPR screens (Biering et al. 2022, Nat Genet): https://www.nature.com/articles/s41588-022-01110-2
