# SARS-CoV-2 CRISPR screen hit lists — completeness note

**7 genome-wide screens, 433 sourced hits (302 proviral, 131 antiviral).** Every hit traces to a
specific supplementary table or main figure; none inferred from abstract/discussion. Gene symbols
normalized to current HGNC (rest.genenames.org). 6 supplements obtained via PubMed Central /
Europe PMC open-access; Baggen via Springer publisher supplement (no PMC OA copy).

| # | Screen | Cell line | n hits | Direction(s) | Threshold | Provenance |
|---|--------|-----------|-------:|--------------|-----------|------------|
| 1 | Wei 2021 Cell | Vero-E6 | 50 | 25 pro + 25 anti | Fig 2B top-25/direction by mean Cas9-v2 z (paper's FDR not in supp) | Table S1 |
| 2 | Daniloski 2021 Cell | A549-ACE2 | 28 | proviral only | MAGeCK FDR<0.05 (union of 2 MOIs) | Table S1 |
| 3 | Schneider 2021 Cell | Huh-7.5 | 147 | 84 pro + 63 anti | FDR<0.05, paper's own 'Sig' flag | Table S1A |
| 4 | Wang 2021 Cell | Huh7.5.1 | 21 | proviral only | Fig 1B line, MAGeCK pos ES<=1e-4 | Table S1 |
| 5 | Baggen 2021 Nat Genet | Huh7 | 52 | proviral only | authors' curated top-50+ (only TMEM106B formally sig.) | Suppl Table 2 |
| 6 | Zhu 2021 Nat Commun | HeLa-ACE2 | 32 | proviral only | top 32 at FDR<0.15 (paper's validated set) | Suppl Data 1 |
| 7 | Biering 2022 Nat Genet | Calu-3 | 103 | 60 pro (LOF) + 43 anti (GOF) | FDR<0.05 | Suppl Tables 1 & 3 |

## Per-screen notes

**Wei et al. (Cell 2021)** (PMID 33147444) — Complete for the paper's displayed hit set. The supplement (Table S1) provides only per-condition z-scores for all ~21,672 genes, not the gene-level FDR the paper uses to formally call hits, so a fully reproducible genome-wide FDR list is not extractable. The reported set is the paper's own Fig 2B hit set: top 25 resistance (proviral) + top 25 sensitization (antiviral) ranked by mean Cas9-v2 z-score. Key anchors (ACE2, SMARCA4, CTSL, DYRK1A up; HIRA, CABIN1 down) reproduce exactly. Three monkey (Chlorocebus) LOC gene models in the proviral top-25 have no clean human ortholog and are flagged.

**Daniloski et al. (Cell 2021)** (PMID 33147445) — Complete and reproducible. Full genome-wide MAGeCK hit list extracted at the stringent FDR<0.05 in either MOI condition (28 unique genes after merging a duplicate CTSL/CTSL1 library row). Positive-selection screen, so all hits are proviral; there is no antiviral arm. Paper also discusses looser sets (top-50 overlap, RRA p<0.05 ~1000 genes) available in the same table if a broader cut is wanted.

**Schneider et al. (Cell 2021)** (PMID 33382968) — Complete and fully reproducible. The supplement carries the paper's own 'Sig' hit flag; 147 flagged genes in the primary Huh-7.5 37C SARS-CoV-2 screen (84 proviral z>0, 63 antiviral z<0) at FDR<0.05. Matches the paper's stated 146 (84+62) within one boundary antiviral gene at FDR~0.048. TMEM41B and GAG/SREBP pathway hits present as expected.

**Wang et al. (Cell 2021)** (PMID 33333024) — Partial by design. FDR<0.05 yields only 4 genes; the reproducible reported set is the 21 genes above the paper's own Fig 1B display line (MAGeCK pos enrichment score <=1e-4). Positive-selection screen, all proviral. Full unthresholded MAGeCK scores for all ~20,915 genes are in the same sheet for any alternative cutoff (e.g. the ES<=0.005 / ~431-gene set the paper used as GO-analysis input).

**Baggen et al. (Nat Genet 2021)** (PMID 33686287) — Partial — this is the weakest-provenance screen and the paper itself provides no genome-wide significance-thresholded hit list. Gene-level p-values in the supplement are unadjusted for multiple testing, and the high-stringency SARS-CoV-2 screen yielded exactly ONE formally significant enriched gene, TMEM106B (the paper's title hit). The reported 52-gene list is the authors' own curated 'top 50+' enriched (proviral) set from the low-stringency Huh7 screen (Suppl Table 2), all confirmed positive-log2FC/enriched. Supplement was fetched from the publisher (Springer) as there is no PMC open-access copy.

**Zhu et al. (Nat Commun 2021)** (PMID 33574281) — Complete for the paper's defined hit set. Reported the paper's explicit 'top 32 genes at FDR<0.15' that were carried to validation (Supplementary Data 1, MAGeCK positive-selection). Positive-selection screen, all proviral; Retromer/CCC/Commander complex dominates as in the paper. Note the genome-wide screen used the Sdel spike-deletion clone (endosomal entry route) in HeLa-ACE2. Two further genes (SHOX2, CCDC53) also fall under FDR<0.15 but sit outside the paper's stated top-32 set.

**Biering et al. (Nat Genet 2022)** (PMID 35879412) — Complete and reproducible, with an important direction caveat. This is a BIDIRECTIONAL study (CRISPR knockout LOF + CRISPR-activation GOF) in Calu-3 at FDR<0.05. The 60 proviral hits come from the knockout (LOF) screen (Suppl Table 1), directly comparable to the other six knockout screens. The paper reports no knockout-defined antiviral hit table; the 43 antiviral hits reported here come from the CRISPRa (GOF) enriched screen (Suppl Table 3) — these are activation-defined restriction factors (incl. the mucins MUC1/MUC4/MUC13/MUC21 headline) and are flagged as NOT direction-equivalent to knockout-defined antiviral hits.

## Provenance / completeness caveats (ranked by confidence)
- **Fully reproducible from a thresholded supplement:** Schneider (own Sig flag), Daniloski (MAGeCK FDR), Biering (MAGeCK FDR, both directions), Zhu (paper's stated top-32).
- **Reproducible but display-threshold-defined (positive-selection, proviral only):** Wang (Fig 1B ES line — strict FDR<0.05 gives only 4 genes).
- **Paper-curated top-N, no genome-wide FDR list exists:** Wei (supp has z-scores not FDR → Fig 2B top-25/direction) and Baggen (unadjusted p-values; only TMEM106B formally significant → authors' curated top-50+). These two are the lists to treat with most caution for any set-overlap / reproducibility analysis.

## Direction caveats
- Wei, Schneider, Biering-LOF report BOTH proviral and antiviral (knockout) hits.
- Daniloski, Wang, Zhu, Baggen are positive-selection (survival) screens → **proviral/dependency only**, no antiviral arm.
- Biering's 43 antiviral hits are **CRISPR-activation (GOF)** defined (overexpression restricts) — NOT knockout-defined, so not direction-equivalent to the other screens' antiviral calls.

## HGNC normalization
28 hit records had a previous/alias symbol updated to the current HGNC symbol (original retained in
`original_symbol`), e.g. KIAA0196→WASHC5, C16orf62→VPS35L, KIAA1033→WASHC4, TMEM30A→CDC50A,
INADL→PATJ, HIST3H3→H3-4. Separately, Daniloski's duplicate CTSL/CTSL1 library rows were merged to
one CTSL hit (hgnc_note only, no `original_symbol`). 3 Chlorocebus (Vero-E6) LOC gene models in Wei's
proviral top-25 have no clean human ortholog (flagged). SPHAR (Schneider) is a withdrawn HGNC entry
(retained as reported).
