# Evidence pack review (Cartograph /evidence)

Reviewer pass on the 10-file Science evidence pack, Jul 8. Independent checks run, not a rubber stamp. Verdict: strong and build-ready. Drop it into `/evidence`. One substantive fix, two small verifies.

## What I verified independently
- All 8 JSON files parse cleanly.
- gordon2020_edges.csv: exactly 332 edges, 26 unique baits, 332 unique preys, 0 shared across baits (confirmed by my own cut/uniq, matches counts.json).
- Flagship rests on real data: ORF6-NUP98 (miscore 0.91) and ORF6-RAE1 (0.93) are both present.
- CRISPR consensus: 27 genes hit in 2 or more of 7 screens; SCAP is the only overlap with Gordon prey. That near-zero overlap is correct orthogonal biology (functional screens vs physical AP-MS), not a bug. Framed honestly as Option B corroboration.
- Citations: the pack describes E-utilities esummary PMID-DOI-title co-verification plus a retracted-paper discard, and my own earlier spot-checks (Miorin 33097660, Kovacs L3, Schmidt) all resolved. Trust is high.
- domain.json is a real moat: 12 prey complexes with CORUM/Reactome refs, interaction priors by viral family, 5 CRAPome-style false-positive patterns, 16 sources.
- Shortlist ranks Orf6 and Orf9b top with solved co-structures, matching our flagship choice.

## Substantive fix (do before coding the evaluator/demo)
The flagship is labeled an "L3 recovery" but the described path ORF6 -> NUP98 -> RAE1 is length 2 (two edges), a common-neighbor / complex-completion signal, which is exactly what degree-normalized L3 (length-3 paths) is supposed to beat (Kovacs 2019). Calling an L2 recovery "L3" contradicts our own method thesis and a sharp judge could catch it. This wording is in both worked_example_orf6.json and gordon2020_counts.json.

Why it happens: ORF6's only real preys are NUP98, RAE1, MTCH1. Once ORF6-RAE1 is held out, RAE1 rejoins the graph only through STRING. The single NUP98-RAE1 bridge yields the 2-edge path.

Fix (recommended): when enriching, pull the STRING neighborhood around the nucleoporins so a genuine 3-edge path exists (ORF6 -> NUP98 -> shared nucleoporin -> RAE1). Then confirm the L3 scorer ranks RAE1 highly for ORF6 and report that rank. If the demo shows the 2-edge path, call it complex completion, not L3. (Also note: an earlier design mock used ORF6 -> XPO1 -> NUP98 -> RAE1, but ORF6-XPO1 is not a real Gordon edge; the intermediate must be a genuine STRING node.) CLAUDE.md has been updated with this check.

## Small verifies (low stakes, but be accurate)
1. Biering 2022 Nat Genet: crispr_screens.json lists PMID 35879412 / DOI 10.1038/s41588-022-01131-x. An earlier lookup gave a neighboring PMID (~35879413) and DOI 10.1038/s41588-022-01110-2. Confirm the exact record before citing Biering. It is 1 of 7 screens and Option B only, so not critical.
2. Flagship PDB id: the shortlist gives Orf6-RAE1/NUP98 as 7VPH and 7F90 (SARS-CoV-2). The earlier Design brief said 7VPG (that is the SARS-CoV-1 homolog). Use the SARS-CoV-2 entry (7VPH per the shortlist) for the demo and confirm it resolves in RCSB.

## Housekeeping
- The manifest lists the three edge packs under `edge_packs/` (orf6_nup98.json, orf9b_tom70.json, n_g3bp1.json) but they arrived flat. Put them in `/evidence/edge_packs/` to match the manifest paths, or update the manifest.
- Keep Option A (frozen held-out edges) as the guaranteed number; Option B (CRISPR) is corroboration.

## Bottom line
Ground truth, citations, domain priors, and CRISPR set are trustworthy and ready. Fix the L3-vs-L2 framing so the method and the demo stay honest, confirm the two identifiers, and this pack fully unblocks the build.
