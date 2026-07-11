# PRD — virtual PPI-screening workflow (structural channel, pooled-AF3, hypotheses)

Extends the scoring/dossier/worklist/upload layers toward the pooled-AlphaFold3
triage workflow. No change to the locked evaluator's frozen split or seed. Stage-0
regression after every change; the baseline (L3-only) number stays 0.45 / 0.8451.

## Honesty guardrails (non-negotiable)
- Every structural number is **labeled predicted**, **banded**, and **size-corrected**; experimental structures are labeled experimental (a stronger, separate tier), not "predicted".
- **No fabricated ipTM.** We cannot run AlphaFold3/Boltz-2 (no GPU). The ipTM channel ingests values from real sources only: committed pre-computed co-fold files, or the user's uploaded pooled-AF3 matrix. Demo dossiers use the real experimental structures (7VPH, 7DHG) as their structural evidence; where no structure/fold exists we say "no co-fold computed", never a guess.
- Novelty tags are grounded in a real literature check (pre-cached PubMed co-mention counts + Gordon ground-truth membership), never guessed.
- Uploaded pooled-AF3 data **never** enters the locked Gordon benchmark (separate seed, as with the CSV/NDEx upload).

## Build (items 1–4 = core; 5–6 = stretch; then roadmap articulation)

**1. Rounds-run counter.** Restore a plain `rounds run: N` indicator in the loop UI. No sentence.

**2. Structural evidence channel + virtual validation.**
- `backend/structure/cofold.py`: per-pair structural confidence with explicit provenance —
  `experimental` (a deposited PDB complex → confidence from real interface metrics; top tier),
  `predicted` (a co-fold ipTM from a committed file or the uploaded matrix → **size-corrected** and **banded**: >0.80 highly confident, 0.60–0.80 confident, 0.55–0.60 weak, <0.55 no better than random),
  or `none`.
- **Size-correction:** ipTM correlates with summed chain length; for a matrix we de-trend (`iptm ~ a + b·(Lₐ+L_b)`, use the residual) — meaningful at scale; a single value is shown raw + flagged. Chain lengths from UniProt (cached).
- **Fusion + measured gain:** the evaluator reports precision **L3-only vs L3+structure** (structure corroborates candidates with a deposited complex / high size-corrected ipTM). Report the honest delta — if the small Gordon map shows little aggregate change, say so; the per-hypothesis corroboration and the at-scale (virtual-screen) value stand regardless.
- **Dossier:** an "In-silico validation" block showing the structural band beside the topology score and the literature, then the existing physical assay as the confirmation step.

**3. Pooled-AlphaFold3 matrix upload.** A new upload type: a symmetric protein×protein ipTM matrix (the virtual-screen output). Parse → size-correct (de-trend) → threshold to candidate edges → run the same L3-agnostic structural triage + dossier degradation + the user's own eval. Source labeled "virtual screen (pooled-AF3)". Off the guaranteed offline path.

**4. Worklist → ranked testable hypotheses.** Each row: the hypothesis (bait→prey), a **novelty tag** (known / partially known / novel, grounded in the literature check), the **Skeptic verdict**, the **structural ipTM band**, and the **one experiment** to run. Remove global dataset-statistics framing; keep it a short ranked list of specific testable hypotheses.

**5. (stretch) Human-in-the-loop feedback.** Mark a prediction confirmed / refuted / to-test + a note; persisted (localStorage) and exportable; feeds the loop priors.

**6. (stretch) Interoperability export.** NDEx-style + Cytoscape-friendly export of the annotated map, and a clean "Claude Science handoff" hypotheses file (JSON/CSV).

**Roadmap (articulate in README/pitch, do not build):** live pooled-AF3 inside Cartograph, multi-user realtime, active-learning experiment selection by information gain, hyperbolic-embedding topology, chemical/functional-genomics channels, cross-species conservation.

## Tests
Stage-0 unchanged; L3-only vs L3+structure precision computed + reported; a pooled-AF3
matrix upload runs end-to-end; the worklist shows the new columns; size-correction
applied before ranking; upload cannot touch the locked benchmark; offline 0 console errors.

## Adversarial review (fresh)
No structural/novelty claim presented as certain; size-correction before ranking;
pooled-AF3 upload cannot poison the benchmark; no fabricated data; panel-lifecycle intact.
