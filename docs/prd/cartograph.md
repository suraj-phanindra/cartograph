# Cartograph — consolidated component PRD

One document instead of seven ceremonial files (the build is done and tested; a
single spec of record is more useful than scattered stubs). Each component lists:
goal · data contract · acceptance criteria · tests · role in the 3-minute demo.
Data contracts are the ones in `docs/Cartograph_BUILD_SPEC.md`.

---

## 1. eval (LOCKED — first commit) · `backend/eval/`
**Goal.** Freeze a held-out set of real Gordon edges before any prediction exists, and score any predictor against it. The anti-objective-hacking spine.
**Contract.** `heldout.frozen.json` = `{seed, fraction, held_out:[[bait,prey]], pinned_walkthrough, sha256}`. `evaluate()` → `{metrics:{k:{precision,recall,hits}, roc_auc, average_precision, ...}, proposals, targets}`.
**Acceptance.** Split frozen & committed before predict code; reproducible sha256; predictor never imports this module; precision identical across runs; headline is computed (not 0.80).
**Tests.** `test_frozen_split_deterministic`, `test_frozen_file_integrity`, `test_evaluator_precision_identical_across_runs`, `test_no_import_of_locked_evaluator`, `test_evaluator_number_is_real_not_illustrative`.
**Demo role.** The precision chip: 45% precision@20, ROC-AUC 0.845, "frozen seed 42, committed before prediction."

## 2. graph · `backend/graph/`
**Goal.** Load the interactome deterministically; enrich with STRING among the prey.
**Contract.** `load_graph()` → networkx graph, nodes `{type:viral|human, uniprot}`, known edges `{kind:known, score:miscore}`. `enriched_graph()` adds `{kind:enrichment, score}` STRING edges. Counts asserted: 332 edges / 26 baits / 332 preys.
**Acceptance.** Loads clean; flagship anchors present; STRING pinned (v12.0, physical, ≥700) and cached offline; the three flagship bridges (NUP98–NUP214, NUP214–RAE1, NUP98–RAE1) exist.
**Tests.** `test_graph_counts`, `test_flagship_anchor_edges_present`, `test_enrichment_flagship_bridges`.
**Demo role.** The map itself; the enrichment edges that make the length-3 path possible.

## 3. predict (L3) · `backend/predict/l3.py`
**Goal.** Degree-normalized L3 candidate generation. Deterministic. The graph proposes; it never explains.
**Contract.** `l3_scores(g, source)` → ranked `[{candidate, l3_score, prior_boost, combined, paths, via}]`. `score = Σ 1/√(deg(a)·deg(b))` over length-3 paths.
**Acceptance.** Reproducible ranking; flagship RAE1 recovered via a genuine length-3 path (all edges real); never the 2-edge shortcut; domain prior kept as a separate logged term.
**Tests.** `test_l3_reproducible`, `test_flagship_recovered_via_genuine_length3_path`.
**Demo role.** The animated `Orf6 → NUP98 → NUP214 → RAE1` path and the proposed `Orf6 → RAE1` edge.

## 4. reason · `backend/reason/hypothesis.py`
**Goal.** Reader assembles a cited mechanism from the verified packs; Skeptic applies AP-MS false-positive patterns; Curator confirms survivors.
**Contract.** `read_edge(key)` → `{mechanism:[{text,cites}], citations:[{n,pmid,doi,title,url,...}], dropped}`. `skeptic_review(prey,...)` → `{verdict:pass|downgrade|veto, reason, caveat}`.
**Acceptance.** Every mechanistic clause cites a PMID present in the pack or is dropped; all citations openable; N–G3BP1 placeholder replaced; Skeptic vetoes sticky proteins.
**Tests.** `test_every_mechanistic_clause_is_cited`, `test_all_citations_are_openable_and_resolve`, `test_no_placeholder_citation_survives`, `test_skeptic_vetoes_sticky_proteins`.
**Demo role.** The dossier's cited mechanism, the visible Skeptic verdict.

## 5. structure · `backend/structure/`
**Goal.** Resolve a dossier's structure block; compute interface residues from real coordinates; label predicted vs experimental.
**Contract.** `resolve.build_structure_facts()` → per-edge `{kind, source, url, method, confidence:{type,value}, interface_residues, note}`. `interface.interface_residues(cif, a, b)` → heavy-atom contacts ≤ 3.0 Å.
**Acceptance.** 7VPH/7DHG are the real SARS-CoV-2 complexes; residues structure-derived (E55/M58/D61 kept; S55/K46 repaired); predicted labeled with real pLDDT and no fabricated residues.
**Tests.** `test_structure_predicted_is_labeled_predicted`, `test_experimental_residues_are_structure_verified`.
**Demo role.** The Mol\* 3D panel, the interface-residue chips, the EXPERIMENTAL/PREDICTED badge.

## 6. artifact + api · `backend/build_artifact.py` (+ optional `backend/api/`)
**Goal.** Run the whole engine to one reproducible JSON the frontend loads; optional thin FastAPI wrapper is upside, off the demo path.
**Contract.** `frontend/data/cartograph_computed.json` = `{meta, integrity, eval:{baseline, loop}, graph:{nodes,edges,predicted}, flagship, dossiers, ...}`.
**Acceptance.** Byte-identical across runs (hash-seed independent); loop before/after fair on the same target set; every dossier field populated.
**Tests.** `test_artifact_is_byte_identical_across_runs`.
**Demo role.** The single offline data source for the whole app.

## 7. frontend · `frontend/`
**Goal.** The one screen: map + dossier + evaluator + loop, matching the Claude Design tokens.
**Contract.** Consumes `cartograph_computed.json`; Cytoscape graph payload `{nodes,edges}`; dossier payload = the hypothesis object; eval reveals green/red in-map.
**Acceptance.** Ask → path → dossier → eval → loop runs without crashing; Mol\* loads offline; predicted always labeled; no live network on the demo path.
**Verification.** Driven end-to-end in a headless browser (screenshots in `docs/`); only console error is a missing favicon.
**Demo role.** Everything the viewer sees.

---

### Assumptions recorded during the build
- Reasoning prose is composed by Claude at build time (grounded in packs), not via a live API, so the demo needs no key and cannot fabricate citations.
- Enrichment uses the STRING physical channel (real complex membership), not text-mining co-mention.
- The flagship walkthrough edge is pinned into the held-out set and **disclosed**; precision is reported so pinning cannot hide behind the headline.
- N–G3BP1 shows a predicted G3BP1 monomer (no deposited complex) rather than a fabricated complex — honesty over spectacle.
