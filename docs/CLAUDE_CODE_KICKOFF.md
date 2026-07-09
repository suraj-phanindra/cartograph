# Claude Code kickoff — build Cartograph autonomously

Paste the block below into Claude Code at the repo root. Everything it references is already in the repo.

---

You are building Cartograph end to end, autonomously. This repo contains the full context, the verified data, and the Claude Design prototype. Plan, write PRDs, implement, test, adversarially review, and iterate in dynamic loops until the demo-critical core runs and is honest. Work in phases. Keep going on sensible defaults. Only stop for a decision that changes the product, not the implementation.

## Read first, in this order, then restate the plan and the demo path back to me
1. README.md
2. CLAUDE.md — rules and locked decisions (non-negotiable)
3. docs/Cartograph_BUILD_SPEC.md — architecture, data contracts, evaluator spec, API surface, frontend contract
4. docs/Cartograph_7Day_Plan.md — the demo-critical core vs the phase-two ladder, and the Day-4 gate
5. design/CARRY_FORWARD.md — what to preserve and the four things to fix
6. design/Cartograph.dc.html and design/cartograph-data.js — the visual and interaction spec, and the reusable dataset
7. evidence/ — start at EVIDENCE_MANIFEST.json; gordon2020_edges.csv is ground truth; edge_packs/ hold cited evidence; cartograph_domain.json is the moat

## Non-negotiables (a build that violates any of these has failed)
- Deterministic critical path. The graph proposes edges with degree-normalized L3; Claude only reads, adjudicates, and explains. Claude never invents an edge from its weights.
- Eval-first. Your FIRST commit is the locked evaluator computing precision on a frozen, seeded held-out split of REAL edges from evidence/gordon2020_edges.csv, in a separate process the reasoning agents cannot import or edit.
- No citation, no render. Every mechanistic claim must open to a real PubMed / PMC / DOI / PDB link. Fail closed.
- Predicted structures are always labeled predicted with a confidence number (ipTM / pLDDT). Never present a prediction as experimental fact.
- Demo-path-first. Build the 3-minute path before anything off it. Phase two only after the core is green and the Day-4 gate passes.
- Honest headline number. The precision you show is computed on real held-out Gordon edges. Do not ship the prototype's illustrative 80 percent.

## The workflow to run (a loop; use parallel subagents)
For each component in this order — eval (first), graph, predict (L3), reason (Reader / Skeptic / Curator), structure (Mol*), api, frontend:
1. PLAN + PRD. Write docs/prd/<component>.md: goal, the exact data contract from BUILD_SPEC, acceptance criteria, the test list, and how it serves the 3-minute demo. One page.
2. IMPLEMENT to the contract.
3. TEST. Unit tests for deterministic pieces (graph loads 332 edges / 26 baits; L3 ranking is reproducible; evaluator precision@k is identical across runs with the frozen seed). Integration tests for the API. A scripted run of the demo path. All green before moving on.
4. ADVERSARIAL REVIEW. Spawn a fresh red-team subagent; the author never grades itself.
   - Code red-team: edge cases, error handling, input and upload safety (injection / XSS), and that the demo path cannot crash.
   - Science-honesty auditor: is any rendered claim uncited? any predicted structure unlabeled? is the held-out set real Gordon edges? is the flagship path genuinely length-3? any fabricated residue or citation? does the deterministic-versus-LLM boundary hold? File every finding as an issue.
5. ITERATE. Fix findings, re-run tests and the evaluator. Use keep-or-revert against the evaluator number (improve, run, eval, keep or revert) and log before / after.
6. INTEGRATE and update the demo path. Then audit the whole system before building the next component ("audit what you built before building more"). Repeat.

## Apply the carry-forward fixes (design/CARRY_FORWARD.md)
1. Evaluator on real held-out Gordon edges, not the prototype's illustrative set (ORF6-STAT1, ORF9b-HSP90AA1, E-MARK2 are not real Gordon edges; only ORF6-RAE1 is).
2. Replace the N-G3BP1 placeholder citation with verified ones from evidence/edge_packs/n_g3bp1.json, and enforce no-citation-no-render everywhere.
3. Verify or repair interface residues against the cited structures (M58 / S53 are anchored; check the rest).
4. Wire an open folding model's mmCIF (Boltz-2 / AF3 / Chai-1) into the Mol* panel, labeled and with confidence; pre-compute one predicted complex offline for the demo.

## Phase 1 — the demo-critical core (must ship)
Interactive SARS-CoV-2 to human map (Cytoscape.js) -> plain-English query -> deterministic L3 prediction of a missing edge with the length-3 path shown -> structural edge dossier (real Mol* for experimental structures such as 7DHG and 7VPH; a labeled predicted model otherwise; interface residues; a cited mechanism; a proposed wet-lab test) -> the locked evaluator running in the map so real held-out edges snap green and misses flash red with a computed precision -> one self-improving loop round that folds a confirmed edge back and updates the score. Reproducible, open-source (MIT), runnable without you present.

## Phase 2 — only after the core is green and the Day-4 gate passes (priority order)
Druggability read (Open Targets / ChEMBL) -> live or pre-computed novel-edge structure prediction -> bring-your-own-interactome upload -> compare across coronaviruses -> export. Cut from the bottom if time is short. Never cut: the locked evaluator, the cited mechanism, the real-structure dossier, or the demo-video time.

## Definition of done, and what to hand back
- The Phase-1 core runs end to end on one screen, reproducibly.
- Tests are green and the science-honesty audit is clean: zero uncited claims, zero unlabeled predictions, the held-out set is real, the flagship path is length-3.
- A report: the computed precision (baseline structure-only vs with the loop, before and after one round), the test summary, the adversarial findings and how each was resolved, and a 3-minute demo-path checklist.
- README updated with run instructions; repo open-source and reproducible.

## How to work
Move fast on defaults and record assumptions in the PRDs. Prefer small, tested commits. Use parallel subagents for independent components and for every red-team pass. If a decision would change the product (not just the implementation), state it, choose the best default, and keep building. The evaluator is your source of truth: when unsure, run it.

---
