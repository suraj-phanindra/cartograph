# Cartograph: virtual PPI screening, accuracy, and the ICP workflow

Synthesis of the Silas session, the collaboration feedback, verified research, and Claude Science's own patterns, into a prioritized plan. The through-line: the bottleneck in this field is no longer generating an interactome, it is reading one. Cartograph is the layer that reads it.

## 1. The strategic unlock: a judge just described Cartograph's exact job
Sukrit Silas is one of the hackathon judges, and his talk is Cartograph's thesis stated by a scientist:
- Pooled-AlphaFold3 (his and Todor's method, now published in Molecular Systems Biology, 2026) makes a genome-wide PPI map cheap and fully in-silico. It predicts all ~113,000 pairwise interactions in a bacterium with ~2,000 AlphaFold3 jobs, with far fewer false positives than folding pairs.
- But it produces a "protein hairball" that a scientist cannot act on. His words: the field "died 15 years ago" because nobody could go through the hairball at scale; the real bottleneck is triage plus literature review plus turning the hairball into ranked, novel, testable hypotheses; other tools produce junk that "sounds like an overconfident undergraduate."
- That triage-to-cited-testable-hypothesis layer is exactly Cartograph.

The reposition: Cartograph is the navigation, triage, and hypothesis layer for any interactome, experimental (AP-MS, like Gordon 2020) or virtual (pooled-AlphaFold3). Same deterministic-plus-cited-plus-measured value, a much bigger surface, and it plugs directly into a judge's own workflow.

## 2. Increasing precision and accuracy (the honest levers)
Verified from the literature: network topology and structural prediction are orthogonal signals, and combining them beats either alone. Network "shape" methods can even beat AlphaFold at raw yes/no PPI prediction, while ipTM is a reliable interface-quality score (roughly: >0.8 highly confident, 0.6 to 0.8 confident, <0.55 no better than random). So:

- Fuse two channels. Keep degree-normalized L3 as the deterministic topology channel; add a structural-confidence channel from a co-fold (AlphaFold3 / Boltz-2) ipTM for the candidate pair. A candidate that scores high on BOTH is a strong lead; disagreement is flagged, not hidden. This is the single biggest, most defensible accuracy lever, and it is fully on-thesis (deterministic topology proposes, structure corroborates, Claude explains, the locked evaluator measures).
- Show the gain honestly. Report the locked-evaluator precision for L3-only versus L3-plus-structure. If it goes up, that is a real, measured accuracy improvement to state on camera; if it does not on this small map, say so.
- Calibrate and label. Show the ipTM band, never a bare number, and always labeled predicted.
- Size-correction caveat (from the session): ipTM correlates with the summed size of the pair, so any structural channel must size-correct before ranking. Bake that in.

Roadmap-only accuracy ideas (name in the pitch, do not build now): hyperbolic graph embeddings for host-pathogen interactomes, cross-coronavirus conservation as a prior, and integrating functional or chemical genomics screens as extra evidence channels.

## 3. Virtual wet-lab: the co-fold IS the in-silico experiment
Sukrit's whole point is that AlphaFold folding is the virtual experiment. So reframe Cartograph's "proposed wet-lab test":
- Virtual validation first: for a predicted edge, show the co-fold ipTM (pre-computed with Boltz-2 or AlphaFold3, labeled predicted, size-corrected) as an in-silico assay result, next to the topology score and the literature.
- Then the physical assay to confirm (the existing co-IP / mutagenesis suggestion).
This makes the dossier read as predict, validate in-silico, then test at the bench, which is the exact loop the ICP now runs. Pre-compute the folds for the demo edges so the offline demo shows real structures with no live GPU.

## 4. Improve the self-improving loop, and add sibling loops
Today the loop folds confirmed edges back and re-ranks (a closed AI loop). Two upgrades, both feasible and both address the collaboration feedback:
- Human-in-the-loop feedback (this is Patryk's point, and Ricardo's "persistent trust bar" question from the session). Let the scientist mark a prediction confirmed, refuted, or worth testing, with a note. That feedback updates the priors, persists across sessions as project memory, and is exportable to share with a collaborator. This is a real feedback loop (human plus AI), not just the model talking to itself, and it is the honest answer to "collaboration, not just context."
- Active triage ("what to test next" by value, not just score). Rank the worklist by which single experiment would most sharpen the map, not only by raw L3 score. Even a simple version (prefer high-confidence, high-druggability, low-literature-coverage edges) reads as a decision tool a PI would use.
- Restore the rounds-run counter in the new UI (it was dropped). Keep it as a plain counter ("rounds run: N") with no explanatory sentence, consistent with the professional-tone pass.

## 5. Connect with the tools the ICP already uses (interoperability)
Scientists in this space live in a small set of standards. Meeting them there is high-value and low-cost:
- NDEx import and export. NDEx is the standard interactome exchange, and Gordon 2020 is hosted there. Import any NDEx network, export the annotated Cartograph map back. This is the concrete "connect with their tools."
- Cytoscape export. Cytoscape is the standard desktop network viewer; export the map and annotations in a Cytoscape-friendly format.
- Claude Science handoff. Export the ranked hypotheses as a clean file a scientist drops straight into Claude Science for the deeper multi-agent analysis Sukrit demoed. Cartograph triages and cites; Claude Science goes deep. Cartograph feeds it.
- The standard databases are already wired (STRING, UniProt, PDB, AlphaFold DB, Open Targets).

## 6. Adopt Claude Science's design principles (from the session)
The session is a free spec for what a scientist trusts. Bring these patterns into Cartograph:
- Ranked, specific, testable hypotheses, not global dataset statistics. Sukrit: "I don't want global insights, I want specific hypotheses, don't b------t me." Reframe the worklist as exactly that: a short ranked list of testable hypotheses, each with a novelty flag, the literature check, and the one experiment to run. No dataset-summary fluff.
- Skepticism made visible. The Skeptic agent that can veto or downgrade is the antidote to "overconfident undergraduate" output. Surface it on every hypothesis.
- Novelty as a first-class signal. For each hypothesis, say whether the literature already knows it (Sukrit graded hypotheses partly on novelty). A "known / partially known / novel" tag is high-value.
- Project memory and a trust bar. Persist the scientist's cutoffs, confirmations, and preferences across sessions, so they are not re-teaching it every time (Ricardo's question).
- Honest "I do not have X, let me go find it" behavior, never global filler.

## 7. The ICP tooling gaps this closes (from the judge and the literature)
- Hairball triage at scale: unsolved enough that the field abandoned large PPI maps; Cartograph makes them navigable.
- Literature-review bottleneck: weeks of a PhD's time synthesizing papers, collapsed into cited hypotheses.
- Junk-hypothesis problem: other tools overclaim; Cartograph is deterministic-proposed, cited, Skeptic-checked, and measured.
- No persistent method or trust bar; no easy way to fold in a scientist's own judgment or a collaborator's: the human-in-the-loop feedback closes this.
- No bridge between a cheap virtual screen and a fundable, testable lead: Cartograph is that bridge.

## 8. What to build now vs what to put on the roadmap (honest about the deadline)
Build now, in priority order (each extends something that already exists, so it is feasible):
1. Restore the rounds-run counter. Trivial; fold into the current UI pass.
2. Structural-evidence channel plus virtual-validation reframe. Add the co-fold ipTM (pre-computed, size-corrected, labeled) to candidate scoring and the dossier; report L3-only vs L3-plus-structure precision from the locked evaluator. Biggest accuracy and virtual-wet-lab win.
3. Accept a pooled-AlphaFold3 score matrix as an upload type. Extend the existing upload to take a score matrix (the virtual-screen output), threshold and size-correct it, run the same triage. Biggest judge-alignment win.
4. Reframe the worklist as ranked testable hypotheses with a novelty tag and the Skeptic verdict visible. Cheap, high-credibility.
5. Human-in-the-loop feedback: mark confirmed / refuted / to-test plus a note, persisted, feeding the loop and exportable. Addresses the collaboration feedback.
6. NDEx and Cytoscape export, plus the Claude Science hypotheses handoff export. Interoperability.

Roadmap (articulate in the README and the pitch, do not build): running pooled-AlphaFold3 live inside Cartograph; multi-user real-time collaboration; active-learning experiment selection by information gain; hyperbolic-embedding topology; chemical and functional genomics integration; cross-species conservation.

Recommended minimum for this submission: 1, 2, and 3, plus the framing of 4. Those three make the accuracy story real and land the method squarely in a judge's own workflow. Treat 5 and 6 as stretch, and the rest as the roadmap slide.

## Claude Code prompt (recommended minimum bundle: items 1 to 4)

Extend Cartograph toward the virtual-PPI-screening workflow. Same autonomous loop: plan, PRD, implement, test, fresh red-team, iterate. Do not regress the demo-critical core; run the Stage 0 regression after every change; do not touch the locked evaluator's frozen split or seed.

Read first: CLAUDE.md, docs/REPORT.md, docs/Cartograph_BUILD_SPEC.md, docs/Cartograph_PPI_screening_strategy.md (this doc), and the current scoring, dossier, worklist, and upload code.

Build:
1. Restore the rounds-run counter in the self-improving-loop UI as a plain "rounds run: N" indicator, no explanatory sentence (keep the professional tone).
2. Structural evidence channel + virtual validation. Add a second, orthogonal candidate signal: a co-fold interface confidence (ipTM) for the predicted pair, from a pre-computed AlphaFold3 / Boltz-2 model, size-corrected (ipTM correlates with summed chain size, so correct before ranking) and shown as a calibrated band (>0.8 highly confident, 0.6 to 0.8 confident, <0.55 no better than random), always labeled predicted. In the dossier, show it as an in-silico validation result beside the topology score and the literature, then keep the physical assay as the confirmation step. In the evaluator, report precision for L3-only vs L3-plus-structure so any accuracy gain is measured, not asserted. Pre-compute the folds for the demo edges so the offline demo needs no live GPU.
3. Accept a pooled-AlphaFold3 score matrix as an upload type (in addition to the edge-list CSV / NDEx). Parse a symmetric protein-by-protein ipTM matrix, size-correct, threshold to candidate edges, and run the same deterministic triage, dossier, and evaluator. Label the source as a virtual screen. Never fabricate; if annotations are missing, fetch or say so. Keep this off the guaranteed offline demo path (it is a live/upload feature).
4. Reframe the worklist as ranked testable hypotheses: a short ranked list, each row showing the hypothesis, a novelty tag (known / partially known / novel, grounded in the literature check), the Skeptic verdict, the structural ipTM band, and the one experiment to run. Remove any global dataset-statistics framing.

Honesty (non-negotiable): every structural number is labeled predicted, banded, and size-corrected; novelty tags are grounded in real literature, never guessed; no fabricated drugs, edges, structures, or citations; the locked evaluator is untouched; the offline demo uses only pre-cached data.

Test: Stage 0 core regression passes and the baseline evaluator number is unchanged; L3-plus-structure precision is computed and reported; a pooled-AF3 matrix upload runs end to end; the worklist shows the new columns; offline works with no console errors.

Adversarial review (fresh subagent): confirm no structural or novelty claim is presented as certain; size-correction is applied before ranking; the pooled-AF3 upload cannot poison the locked benchmark; no fabricated data; panel-lifecycle and overlap rules still hold.

Stretch (only if the above is solid, in order): human-in-the-loop feedback (mark a prediction confirmed / refuted / to-test with a note, persisted and exportable, feeding the loop); NDEx and Cytoscape export; a Claude Science hypotheses handoff export.

Done: the structural channel and the pooled-AF3 input work and are honest; the worklist reads as ranked testable hypotheses; the rounds-run counter is back; the core did not regress; docs/REPORT.md is updated with the accuracy comparison and the new inputs.

## Sources
- Pooled-AlphaFold3 (Todor, Silas et al.), Molecular Systems Biology 2026: https://link.springer.com/article/10.1038/s44320-026-00189-7
- Pooled-AlphaFold3 preprint, bioRxiv 2025: https://www.biorxiv.org/content/10.1101/2025.07.01.662654v2.full
- Network topology plus AlphaFold-Multimer for PPI discovery: https://www.biorxiv.org/content/10.1101/2024.02.19.580970.full.pdf
- Network shape intelligence vs AlphaFold2 for PPI prediction: https://www.biorxiv.org/content/10.1101/2023.08.10.552825.full.pdf
- AlphaFold3 benchmarking (ipTM reliability), Briefings in Bioinformatics 2025: https://academic.oup.com/bib/article/26/6/bbaf616/8351050
