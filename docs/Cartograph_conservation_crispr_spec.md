# Cartograph: conservation + CRISPR corroboration channels (spec + prompt)

Two orthogonal evidence channels, plus the leftover cosmetics. Both channels corroborate hypotheses; neither is allowed to touch the locked benchmark.

## Does Claude Code already have what it needs?
- CRISPR channel: YES. `evidence/crispr_gold_standard.csv` (27-gene cross-screen consensus) and `evidence/crispr_screens.json` (7 screens with PMIDs) are already in the repo.
- Conservation: NO. The SARS-CoV-1 and MERS interactomes are NOT in the repo. They come from a different paper: Gordon et al. 2020, Science, "Comparative host-coronavirus protein interaction networks reveal pan-viral disease mechanisms" (PMID 33060197, DOI 10.1126/science.abe9403, free full text at PMC7808408). It reports 366 human-SARS-CoV-1 interactions and 296 for MERS-CoV. Claude Code must fetch this first.

Fetch route (use the same method that already worked for the Nature paper): query IntAct/IMEx through EBI PSICQUIC by publication id (PMID 33060197) to get the MITAB records for the SARS-CoV-1 and MERS maps. Fall back to the PMC7808408 supplementary tables, or the Krogan lab NDEx networkset, if IntAct is incomplete. Commit the result to `evidence/gordon2020_science_cov1_mers_edges.csv` with a counts/provenance JSON alongside it, exactly like the existing ground-truth files.

---

## Channel 1: cross-species conservation ("Compare strains")

What it is: an edge is conserved if the orthologous viral protein in SARS-CoV-1 or MERS interacts with the SAME human protein. Human preys are the same species, so no mapping is needed on the host side. This is the Science paper's core finding (pan-viral mechanisms), and it is a genuine prior: a pan-coronavirus interaction is more likely to be real.

Non-negotiable caveat (viral orthology is partial):
- Nsp1 to Nsp16, N, M, E, and S have clear orthologs across the three viruses.
- Accessory ORFs do not. MERS has Orf3, Orf4a, Orf4b, Orf5, and has NO Orf6. SARS-CoV-1 and SARS-CoV-2 ORFs align better but are not identical.
- So the three states must be distinguished, and never collapsed: "conserved", "not conserved (ortholog exists, no interaction reported)", and "no ortholog in this strain". Rendering "no ortholog" as "not conserved" would be a fabrication. Blank is not the same as absent.

What it does in the product:
1. A "Conserved" layer and an edge flag on the map (the UI already reserves this layer).
2. "Compare strains" (currently greyed out) becomes a real view: show which edges are shared across coronaviruses vs SARS-CoV-2 specific, with the per-strain evidence.
3. A conservation column in the triage worklist, filterable ("conserved only"), because a conserved predicted edge is a better experiment.
4. Conservation as an orthogonal corroboration signal in the dossier, alongside topology, structure, and literature. Keep the signals separate; never blend them into one score.
5. Run the locked evaluator with conservation as a candidate-scoring prior and report honestly whether precision improves. It may genuinely help (unlike the structural channel, which honestly reported no aggregate gain). If it does not help, say so.

Benchmark isolation: the Science paper's SARS-CoV-2 map is a slightly different, larger set (~400 PPIs) than the Nature 332 that the frozen benchmark is built on. Use the Science data ONLY for the CoV-1 / MERS comparison. Do not let it modify, extend, or contaminate the frozen held-out split or the ground-truth edge list. Assert this with a test.

---

## Channel 2: chemical / functional-genomics (CRISPR) corroboration

What it is: if a host protein Cartograph predicts is also a hit in independent genome-wide CRISPR screens, that is orthogonal functional evidence for its role in infection. This is the Option B story that was always planned.

Honest caveat you must design around (this is the whole risk of this feature):
- Functional screens and physical AP-MS binding capture different biology. In our own data, only SCAP overlaps between the 27-gene consensus and the Gordon prey. So a corroboration channel built on the strict consensus will light up almost never, and a channel that lights up once is not a feature.
- Fix: use the UNION of top hits across the 7 screens (in `crispr_screens.json`), not just the 2-or-more consensus, and carry the number of screens as the confidence weight (hit in 4 screens is stronger than hit in 1). That widens coverage substantially while staying honest.
- Also note in the manifest caveat: our hit lists are the high-confidence core taken from abstracts and main text, not the full genome-wide supplementary tables. State that on screen. If you have time, pull the fuller hit tables from the papers' supplements; if not, present the current set honestly.

What it does in the product:
1. A CRISPR column in the triage worklist ("functional evidence"), showing the number of screens the host protein is a hit in, filterable ("CRISPR-supported only"). Blank means "not established", never "absent from biology", exactly like the existing druggability convention.
2. A line in the dossier: "Independent functional evidence: host factor in N of 7 genome-wide CRISPR screens", with the screen names and PMIDs linked, plus the explicit note that a functional hit is not evidence of a direct physical interaction.
3. Option B corroboration in the evaluator view: of the host factors Cartograph predicts, how many are independent CRISPR hits. Present as corroboration, never as the headline; Option A (the frozen held-out edges) stays the guaranteed number.

Never claim a CRISPR hit validates a physical interaction. The evidence manifest already states these are orthogonal; keep that wording.

---

## Cosmetics and one free win
- Worklist: the proposed-experiment text truncates ("co-fol..."). Wrap it, or add a hover or expand so the experiment is readable. It is the most useful cell in the table.
- "Compare strains": it is currently disabled with no explanation. This build enables it, so the issue resolves itself. If any control remains disabled, give it a tooltip saying why.
- KEEP the line "Every hypothesis Cartograph renders is backed by an openable paper. A claim with no citation does not render." The user has decided to keep it. Do not remove it.
- Free win: the held-out transparency screen shows 14 recovered of 14 reachable, i.e. L3 recovered every held-out edge that a length-3 path can even reach. Surface that as a headline stat in the evaluator panel too ("recall on the reachable set: 14/14"). It is the strongest honest number in the product and it is currently buried one click deep.

---

## Claude Code prompt (paste at the repo root)

Add two orthogonal corroboration channels to Cartograph, plus small fixes. Same autonomous loop: plan, PRD, implement, test, fresh red-team review, iterate. Do not regress the demo-critical core; run the Stage 0 regression after every change; do not touch the locked evaluator's frozen split or seed.

Read first: CLAUDE.md, docs/REPORT.md, docs/Cartograph_BUILD_SPEC.md, docs/Cartograph_conservation_crispr_spec.md (this spec), evidence/EVIDENCE_MANIFEST.json, evidence/crispr_gold_standard.csv, evidence/crispr_screens.json, and the current scoring, dossier, worklist, and evaluator code.

STEP 0 — fetch the conservation data (you do not have it). The SARS-CoV-1 and MERS interactomes come from Gordon et al. 2020, Science (PMID 33060197, DOI 10.1126/science.abe9403; free full text PMC7808408; 366 SARS-CoV-1 and 296 MERS interactions). Fetch via IntAct/IMEx through EBI PSICQUIC by PMID 33060197 — the same route that worked for the Nature paper. Fall back to the PMC supplementary tables or the Krogan lab NDEx networkset. Commit to evidence/gordon2020_science_cov1_mers_edges.csv plus a provenance/counts JSON, verified the same way as the existing ground truth. If the data cannot be obtained cleanly, stop and tell me rather than approximating it.

1. Conservation channel. An edge is conserved if the orthologous viral protein in SARS-CoV-1 or MERS binds the SAME human protein. Viral orthology is PARTIAL: Nsp1-16, N, M, E, S map across strains; accessory ORFs do not (MERS has Orf3/4a/4b/5 and NO Orf6). You must distinguish three states and never collapse them: "conserved", "not conserved (ortholog exists, no interaction reported)", and "no ortholog in this strain". Rendering "no ortholog" as "not conserved" is a fabrication. Then: light up the Conserved layer and edge flag on the map; make the greyed-out "Compare strains" control a real view (shared vs SARS-CoV-2-specific, with per-strain evidence); add a conservation column + "conserved only" filter to the worklist; show conservation as a separate corroboration signal in the dossier (never blended into one score); and run the locked evaluator with conservation as a candidate prior and report honestly whether precision improves or not.
   BENCHMARK ISOLATION: the Science paper's SARS-CoV-2 map (~400 PPIs) differs from the Nature 332 the frozen benchmark uses. Use the Science data ONLY for CoV-1/MERS comparison. It must not modify, extend, or contaminate the frozen split or ground truth. Assert this with a test.

2. CRISPR functional-genomics channel. Use the UNION of top hits across the 7 screens in crispr_screens.json (not just the 2-or-more consensus, which overlaps our prey only at SCAP and would light up almost never), weighted by the number of screens a gene is a hit in. Add a "functional evidence" column + "CRISPR-supported only" filter to the worklist; add a dossier line "host factor in N of 7 genome-wide CRISPR screens" with screen names and PMIDs linked. State on screen that our hit lists are the high-confidence core from abstracts/main text, not full genome-wide tables. Never claim a CRISPR hit validates a physical interaction — functional screens and AP-MS binding are orthogonal; keep the manifest's wording. Blank means "not established", never fabricated.

3. Fixes: the worklist's proposed-experiment text truncates — wrap it or add hover/expand so it is readable. Give any still-disabled control a tooltip explaining why. KEEP the line "Every hypothesis Cartograph renders is backed by an openable paper. A claim with no citation does not render." (the user has decided to keep it).

4. Free win: surface "recall on the reachable set: 14/14" as a headline stat in the evaluator panel (it is currently only visible one click deep in held-out transparency). It is the strongest honest number in the product.

Test: Stage 0 core regression passes and the baseline evaluator number is unchanged; a test asserts the Science data cannot enter the frozen benchmark; conservation states are never collapsed (a "no ortholog" case is asserted); the CRISPR union and screen-count weighting are correct; the worklist columns and filters work; offline still works with zero console errors.

Adversarial review (fresh subagent): confirm no fabricated conservation or CRISPR claims; "no ortholog" is never shown as "not conserved"; no CRISPR hit is presented as validating a physical interaction; the frozen benchmark is untouched; the panel-lifecycle and overlap rules still hold.

Done: both channels work and are honest, Compare strains is live, the evaluator reports whether conservation helps (either way), the fixes land, the core did not regress, and docs/REPORT.md is updated with the new data provenance and the honest accuracy result.
