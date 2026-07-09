# design -> code carry-forward

The Claude Design prototype (`Cartograph.dc.html` + its JS) is the visual and interaction spec of record. It is faithful and on-spec. Before and during the real build, the items below must move from "illustrative design data" to "real." They are fine in a prototype; they are not fine in the submission.

## Verified good (preserve these)
- The flagship recovery path is a genuine length-3 path: ORF6 -> NUP98 -> NUP214 -> RAE1, and all three edges exist in the data. Keep it length-3. Never collapse to the 2-edge ORF6 -> NUP98 -> RAE1 shortcut (that is a common-neighbor / L2 signal, the thing L3 is meant to beat).
- Mol* is real: PDBe Mol* component loads experimental structures by PDB id (7DHG confirmed in-browser). Keep this.
- The eval math is honest: 4 held-out-true predictions + 1 false = 80 percent. Keep the green/red-in-the-map presentation (not a bar chart).
- Integrity boundary is visible; predicted vs experimental is labeled; ipTM/pLDDT confidence is shown; flagship citations are real (Miorin 2020 PMID 33097660; Addetia 2021 PMC8092196).

## Must fix in the real build
1. Held-out set must be REAL Gordon edges. In the prototype only ORF6-RAE1 is a real Gordon AP-MS edge; ORF6-STAT1, ORF9b-HSP90AA1, and E-MARK2 are functional or indirect relationships (0 matches each in `evidence/gordon2020_edges.csv`). The locked evaluator must draw its held-out set from `gordon2020_edges.csv`. Until the precision is computed on real held-out edges, label it "illustrative," not measured.
2. No placeholder citations. `cartograph-data.js` N|G3BP1 citation 2 ("Yang et al. 2023 / PMC review / https://pmc.ncbi.nlm.nih.gov/") does not resolve. Replace with verified citations from `evidence/edge_packs/n_g3bp1.json`. Enforce the rule everywhere: no citation, no render.
3. Verify interface residues against the cited structures. M58 (ORF6) and S53 (ORF9b, the phospho-regulated residue) are correct; confirm or repair E55 and D61 (ORF6), S55 and K46 (ORF9b), and R95/G99/R107 (N-G3BP1), using the residues named in the cited structure papers (ORF6: PMID 35970938 / PDB 7VPH; ORF9b: PDB 7DHG).
4. Predicted-complex 3D: wire the mmCIF output of an open folding model (Boltz-2 MIT, or AlphaFold3 / Chai-1) into the same Mol* panel, labeled predicted with ipTM/pLDDT. Pre-compute one predicted complex offline for the demo so the demo path makes no live GPU call.

Minor: deep-link Open Targets per target (RAE1 is deep-linked; do the same for TOMM70 and G3BP1). Node degree currently counts predicted edges; fine, just know it reflects current map state.

## Files in this folder
- `Cartograph.dc.html` — the clickable Claude Design prototype. Open in a browser.
- `support.js` — the Claude Design prototype runtime.
- `cartograph-data.js` — reference dataset (real flagship names; directly reusable in the build).
- `cartograph-spec.js` — in-app spec / config.
- `wow_moment_mock.html` — the earlier visual North Star.
- `README.md` — this folder's guide.
