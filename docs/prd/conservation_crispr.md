# PRD: conservation + CRISPR corroboration channels

Two orthogonal corroboration channels + fixes + one free win. Both channels are
separate corroboration signals; neither blends into a single score; neither touches
the locked benchmark.

## STEP 0 — conservation data (DONE, verified)
- Fetched Gordon 2020 *Science* (PMID 33060197, IMEx IM-28441) via EBI IntAct REST.
- Committed `evidence/gordon2020_science_cov1_mers_edges.csv`: **366 SARS-CoV-1 + 296
  MERS** edges — both exactly the paper's canonical numbers. Provenance in
  `gordon2020_science_cov1_mers_counts.json`.
- **Benchmark isolation:** the 396 Science SARS-CoV-2 edges were fetched but
  deliberately NOT committed, so they cannot touch the frozen Nature-332 split.

## Channel 1: cross-species conservation
- An edge (CoV-2 bait → human prey) is **conserved** if the orthologous viral
  protein in SARS-CoV-1 or MERS binds the SAME human prey.
- **Three states, never collapsed:** `conserved`, `not_conserved` (ortholog
  represented in the strain's screen, no interaction reported), `no_ortholog`
  (no orthologous viral protein in that strain).
- **Orthology model (partial, grounded):** Nsp1-16, N, M, E, Spike → ortholog in
  both strains (universal). Accessory ORFs → ortholog only where that ORF appears
  in the strain's Gordon *Science* screen. MERS has ORF3/4a/4b/5 and NO SARS
  accessory ORF → every CoV-2 accessory ORF is `no_ortholog` in MERS. Orf10 has no
  ortholog in either (CoV-2 putative-specific). Verified: Orf6→RAE1 is conserved
  in SARS-CoV-1; MERS has no Orf6.
- Product: Conserved map layer + edge flag; a real **Compare strains** view (shared
  vs CoV-2-specific with per-strain evidence); worklist column + "conserved only"
  filter; a separate dossier corroboration block; and the locked evaluator run with
  conservation as a candidate prior, reporting honestly whether precision moves.

## Channel 2: CRISPR functional genomics
- **Data reality:** `crispr_screens.json` is metadata-only (no gene lists);
  `crispr_gold_standard.csv` is the verified ≥2-of-7 consensus (27 genes, each with
  its screen set). The per-screen union the spec imagined is NOT in the repo, and it
  cannot be reconstructed cleanly — a full-text symbol match is a *mention*, not a
  screen *hit* (verified: full text names many non-hit prey). Per STEP-0 discipline
  and the spec's own fallback ("if not, present the current set honestly"), the
  channel is built on the verified consensus, **weighted by the real N-of-7 screen
  count**, not on an approximated union.
- Product: worklist "functional evidence" column (N of 7 screens) + "CRISPR-supported
  only" filter; dossier line "host factor in N of 7 genome-wide CRISPR screens" with
  screen names + linked PMIDs; explicit on-screen caveat that hit lists are the
  high-confidence core (abstracts/main text), coverage is sparse because functional
  screens and AP-MS binding are orthogonal, and a hit is NOT evidence of a physical
  interaction. Blank = not established.

## Fixes + free win
- Worklist proposed-experiment text: wrap / hover so it is readable (currently
  truncates).
- Any still-disabled control gets a tooltip explaining why.
- KEEP the line "Every hypothesis Cartograph renders is backed by an openable paper.
  A claim with no citation does not render."
- Free win: surface **recall on the reachable set: 14/14** as a headline stat in the
  evaluator panel (currently buried in held-out transparency).

## Non-negotiables / tests
- Stage 0 core regression passes; baseline evaluator unchanged (0.45 / 0.8451).
- A test asserts the Science data cannot enter the frozen benchmark.
- A "no ortholog" case is asserted (states never collapsed).
- CRISPR screen-count weighting is correct.
- Worklist columns/filters work; offline works with 0 console errors.
- Fresh adversarial review before done.
