# Cartograph Demo — Candidate Protein Shortlist by Literature Richness

Five SARS-CoV-2 viral-protein / human-interactor pairs from the Gordon 2020 AP-MS map, ranked by depth and mechanistic clarity of the **published primary literature** and by the existence of **experimentally solved structures of the interaction**. Every PMID and DOI below was verified against NCBI E-utilities (esummary) and CrossRef; every PDB ID against the RCSB PDB data API.

## Ranking (best → weakest evidence)

| Rank | Interaction | Primary papers | Solved complex structure? | Key PDB IDs |
|------|-------------|----------------|---------------------------|-------------|
| 1 | Orf6 (NUP98/RAE1) | 6 | Yes — of the complex | 7VPH, 7F90, 9A8Y |
| 2 | Orf9b (TOMM70/TOM70) | 6 | Yes — of the complex | 7DHG, 7KDT, 6Z4U |
| 3 | N (G3BP1/G3BP2) | 5 | Yes — of the complex | 7SUO, 8TH1 |
| 4 | E (BRD2/BRD4) | 4 | Yes — of the complex | 7TUQ, 7TV0 |
| 5 | Orf3a (HOPS / VPS39) | 4 | Partner complex: **No** (apo channel only) | 6XDC, 7KJR |

## Recommended demo set

**Orf6 (NUP98/RAE1)**, **Orf9b (TOMM70/TOM70)**, **N (G3BP1/G3BP2)** — the three with the deepest, cleanest published evidence. Orf6 and Orf9b both pair a textbook-clean immune-evasion mechanism with a solved co-structure of the viral protein bound to its human partner; N–G3BP adds a high-profile phase-separation story with a domain–peptide co-crystal. Orf3a is scientifically compelling but lacks a solved structure of the specific PPI (VPS39/HOPS), and E–BRD has a thinner primary-literature base.

## Orf6 (NUP98/RAE1)

SARS-CoV-2 Orf6 is the virus's most potent interferon antagonist and its mechanism is resolved to the residue level. Its C-terminal acidic tail docks onto the RAE1–NUP98 heterodimer at the nuclear pore, and this same interface sequesters the mRNA-export machinery and blocks STAT1/STAT2 nuclear import, shutting down ISG transcription (Miorin 2020 PNAS, PMID 33097660; Lei/Xia in Evasion of Type I IFN, PMID 32979938). Kato 2021 (PMID 35096974) and Li 2024 (PMID 38507240) dissect how Orf6 is positioned in the pore by Rae1, and Addetia 2021 (PMID 33849972) shows bidirectional nucleocytoplasmic-transport disruption. The Orf6-CTD•RAE1•NUP98 interface is captured in crystal structures (PDB 7VPH, 7F90), and an integrative/NMR model of full-length Orf6 in a membrane exists (9A8Y). Literature is the deepest of the five candidates and the mechanism is textbook-clean.

**Strong primary papers: 6** (representative, all verified):

- PMID **33097660** — SARS-CoV-2 Orf6 hijacks Nup98 to block STAT nuclear import and antagonize interferon signaling. *Proceedings of the National Academy of Sciences of the United States of America* (2020). DOI: 10.1073/pnas.2016650117
- PMID **32979938** — Evasion of Type I Interferon by SARS-CoV-2. *Cell reports* (2020). DOI: 10.1016/j.celrep.2020.108234
- PMID **35096974** — Molecular Mechanism of SARS-CoVs Orf6 Targeting the Rae1-Nup98 Complex to Compete With mRNA Nuclear Export. *Frontiers in molecular biosciences* (2021). DOI: 10.3389/fmolb.2021.813248
- PMID **38507240** — SARS-CoV-2 Orf6 is positioned in the nuclear pore complex by Rae1 to inhibit nucleocytoplasmic transport. *Molecular biology of the cell* (2024). DOI: 10.1091/mbc.E23-10-0386
- PMID **33849972** — SARS-CoV-2 ORF6 Disrupts Bidirectional Nucleocytoplasmic Transport through Interactions with Rae1 and Nup98. *mBio* (2021). DOI: 10.1128/mBio.00065-21
- PMID **39480836** — The SARS-CoV-2 ORF6 protein inhibits nuclear export of mRNA and spliceosomal U snRNA. *PloS one* (2024). DOI: 10.1371/journal.pone.0312098

**Solved structures (RCSB PDB, verified):**
- **7VPH** (X-ray) — Orf6 CTD–RAE1/NUP98 (SARS-CoV-2)
- **7F90** (X-ray) — Orf6–RAE1/NUP98 nuclear-pore complex
- **9A8Y** (Integrative/NMR) — Orf6 in liposomes

## Orf9b (TOMM70/TOM70)

Orf9b binds the mitochondrial import receptor TOM70 (TOMM70) in its cytosolic TPR domain, displacing the HSP90 C-terminal EEVD peptide that TOM70 normally uses to recruit the antiviral adaptor MAVS — thereby suppressing RIG-I/MAVS-driven type I/III interferon (Jiang 2020, PMID 32728199; Gao 2021 structure, PMID 33990585; Gordon 2020 Science). The binary complex is solved by both X-ray crystallography (PDB 7DHG) and cryo-EM (7KDT), giving the cleanest single-interface structural picture of the set; apo Orf9b is also solved (6Z4U). Phosphorylation switches Orf9b between its TOM70-binding and lipid-binding states (Chen 2021, PMID 34502139), and the interaction reshapes mitochondrial protein biogenesis (Gordon-adjacent, PMID 37682539). A crisp, single binary PPI ideal for a demo.

**Strong primary papers: 6** (representative, all verified):

- PMID **33990585** — Crystal structure of SARS-CoV-2 Orf9b in complex with human TOM70 suggests unusual virus-host interactions. *Nature communications* (2021). DOI: 10.1038/s41467-021-23118-8
- PMID **32728199** — SARS-CoV-2 Orf9b suppresses type I interferon responses by targeting TOM70. *Cellular & molecular immunology* (2020). DOI: 10.1038/s41423-020-0514-8
- PMID **35643212** — Binding of SARS-CoV-2 protein ORF9b to mitochondrial translocase TOM70 prevents its interaction with chaperone HSP90. *Biochimie* (2022). DOI: 10.1016/j.biochi.2022.05.016
- PMID **33913550** — SARS-CoV-2 ORF9b antagonizes type I and III interferons by targeting multiple components of the RIG-I/MDA-5-MAVS, TLR3-TRIF, and cGAS-STING signaling pathways. *Journal of medical virology* (2021). DOI: 10.1002/jmv.27050
- PMID **34502139** — Phosphorylation of SARS-CoV-2 Orf9b Regulates Its Targeting to Two Binding Sites in TOM70 and Recruitment of Hsp90. *International journal of molecular sciences* (2021). DOI: 10.3390/ijms22179233
- PMID **37682539** — The Orf9b protein of SARS-CoV-2 modulates mitochondrial protein biogenesis. *The Journal of cell biology* (2023). DOI: 10.1083/jcb.202303002

**Solved structures (RCSB PDB, verified):**
- **7DHG** (X-ray) — Orf9b–human TOM70 complex
- **7KDT** (EM) — Human TOM70–Orf9b
- **6Z4U** (X-ray) — Orf9b apo (SARS-CoV-2)

## N (G3BP1/G3BP2)

The nucleocapsid (N) protein's intrinsically disordered region 1 binds the NTF2-like domain of the stress-granule nucleators G3BP1/G3BP2, out-competing G3BP's normal partners to dismantle stress granules and rewire phase separation in the virus's favour (Luo/Yang 2021 Cell Discovery, PMID 34400613; Zheng 2021 Science Bulletin, PMID 33495715). A short N-IDR1 peptide bound to the G3BP1 NTF2 domain is co-crystallised (PDB 7SUO, 8TH1). Downstream work ties the interaction to innate-immune / cGAS-STING suppression (PMID 37100798) and shows G3BP1/2 redundancy (PMID 40733530, 38492217). Mechanistically rich and structurally anchored, though the co-structure is a domain–peptide fragment rather than a full complex.

**Strong primary papers: 5** (representative, all verified):

- PMID **34400613** — Molecular determinants for regulation of G3BP1/2 phase separation by the SARS-CoV-2 nucleocapsid protein. *Cell discovery* (2021). DOI: 10.1038/s41421-021-00306-w
- PMID **33495715** — SARS-CoV-2 nucleocapsid protein phase separates with G3BPs to disassemble stress granules and facilitate viral production. *Science bulletin* (2021). DOI: 10.1016/j.scib.2021.01.013
- PMID **38492217** — Interaction between host G3BP and viral nucleocapsid protein regulates SARS-CoV-2 replication and pathogenicity. *Cell reports* (2024). DOI: 10.1016/j.celrep.2024.113965
- PMID **37100798** — Phase-separated nucleocapsid protein of SARS-CoV-2 suppresses cGAS-DNA recognition by disrupting cGAS-G3BP1 complex. *Signal transduction and targeted therapy* (2023). DOI: 10.1038/s41392-023-01420-9
- PMID **40733530** — Beyond Stress Granules: G3BP1 and G3BP2 Redundantly Suppress SARS-CoV-2 Infection. *Viruses* (2025). DOI: 10.3390/v17070912

**Solved structures (RCSB PDB, verified):**
- **7SUO** (X-ray) — G3BP1 NTF2 domain–N IDR1 peptide
- **8TH1** (X-ray) — G3BP1 NTF2–N IDR1

## E (BRD2/BRD4)

The envelope (E) protein carries a C-terminal acetyl-lysine mimic that engages the bromodomains of the BET proteins BRD2 and BRD4, and the interaction is required for efficient infection (Gordon 2020 Nature). Crystal structures of BRD4 bromodomain-1 bound to mono- and di-acetylated E peptides (PDB 7TUQ, 7TV0) reveal the histone-mimicry interface (Wei/Nichols 2022 Structure, PMID 35716662). Functionally, E neutralises BET-mediated post-entry antagonism (Gilmore/Barrado-Gil 2022 Cell Reports, PMID 35839775) and binds the BRD2/BRD4 SEED domains to alter host transcription (PMID 39066826). Clean structural story but a thinner primary-literature base (18 PubMed hits) than Orf6/Orf9b/N.

**Strong primary papers: 4** (representative, all verified):

- PMID **35716662** — Binding of the SARS-CoV-2 envelope E protein to human BRD4 is essential for infection. *Structure (London, England : 1993)* (2022). DOI: 10.1016/j.str.2022.05.020
- PMID **35839775** — Viral E protein neutralizes BET protein-mediated post-entry antagonism of SARS-CoV-2. *Cell reports* (2022). DOI: 10.1016/j.celrep.2022.111088
- PMID **39066826** — SARS-CoV-2 E protein interacts with BRD2 and BRD4 SEED domains and alters transcription in a different way than BET inhibition. *Cellular and molecular life sciences : CMLS* (2024). DOI: 10.1007/s00018-024-05343-8
- PMID **36595918** — Characterization of multiple interactions between the envelope E protein of SARS-CoV-2 and human BRD4. *STAR protocols* (2022). DOI: 10.1016/j.xpro.2022.101853

**Solved structures (RCSB PDB, verified):**
- **7TUQ** (X-ray) — BRD4 BD1–monoacetylated E peptide
- **7TV0** (X-ray) — BRD4 BD1–diacetylated E peptide

## Orf3a (HOPS / VPS39)

Orf3a blocks autophagosome–lysosome fusion by sequestering VPS39, a subunit of the HOPS tethering complex, preventing HOPS-mediated assembly of the STX17–SNAP29–VAMP8 SNARE complex and trapping autolysosome maturation (Miao 2021 Developmental Cell, PMID 33422265; Chen 2021 Cell Discovery, PMID 33947832). Orf3a also disrupts lysosome function via BORC/ARL8b and lysosomal cholesterol egress (PMID 38448435; PMID 42287635). The functional mechanism is well documented and biologically compelling, but — unlike the other four — there is no experimentally solved co-structure of Orf3a with VPS39/HOPS; only apo cryo-EM structures of the Orf3a channel exist (PDB 6XDC, 7KJR). Structurally the weakest for showcasing a solved interaction interface.

**Strong primary papers: 4** (representative, all verified):

- PMID **33422265** — ORF3a of the COVID-19 virus SARS-CoV-2 blocks HOPS complex-mediated assembly of the SNARE complex required for autolysosome formation. *Developmental cell* (2021). DOI: 10.1016/j.devcel.2020.12.010
- PMID **33947832** — The SARS-CoV-2 protein ORF3a inhibits fusion of autophagosomes with lysosomes. *Cell discovery* (2021). DOI: 10.1038/s41421-021-00268-z
- PMID **38448435** — SARS-CoV-2 virulence factor ORF3a blocks lysosome function by modulating TBC1D5-dependent Rab7 GTPase cycle. *Nature communications* (2024). DOI: 10.1038/s41467-024-46417-2
- PMID **42287635** — SARS-CoV-2 ORF3a blocks lysosomal cholesterol egress by disrupting VPS39-regulated NPC2 trafficking and BMP metabolism. *Cell reports* (2026). DOI: 10.1016/j.celrep.2026.117544

**Solved structures (RCSB PDB, verified):**
- **6XDC** (EM) — ORF3a apo channel (no HOPS co-structure)
- **7KJR** (EM) — ORF3a apo channel

---
*Verification: PMIDs confirmed via NCBI E-utilities esummary; DOIs confirmed to resolve to the exact claimed title via CrossRef; PDB IDs confirmed via RCSB data API (title + experimental method). Seed papers PMID 33097660 (Miorin Orf6–NUP98/STAT) and PMID 35643212 (Orf9b–TOM70–HSP90) both verified. Note: several DOIs initially recalled from memory resolved to unrelated papers and were discarded — all identifiers here derive from live PubMed records.*
