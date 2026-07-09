# Cartograph

The navigation layer for a protein interaction map. Cartograph predicts the edges that should be there but are not yet drawn, proves each one with the literature and a 3D structure, and measures how often it is right against a locked held-out benchmark.

Built with Claude: Life Sciences (Anthropic x Gladstone). Build track, solo. Due Jul 13, 2026, 9:00 PM ET. Open source (MIT).

## To build
Paste `docs/CLAUDE_CODE_KICKOFF.md` into Claude Code at this repo root. It runs the full autonomous workflow (plan, PRDs, implement, test, adversarial review, iterate). The Claude Design prototype of record is `design/Cartograph.dc.html`; read `design/CARRY_FORWARD.md` before building the frontend.

## Read these first, in order
1. `CLAUDE.md` — operational build context, locked decisions, and the non-negotiable rules. Start here.
2. `docs/Cartograph_7Day_Plan.md` — plan of record: the demo-critical core, the phase-two ladder, and the Day-4 decision gate.
3. `docs/Cartograph_BUILD_SPEC.md` — architecture, data contracts, module interfaces, and the evaluator spec.

## What to build (the demo-critical core)
An interactive SARS-CoV-2 to human interactome. A plain-English query triggers a deterministic prediction of a missing edge; clicking that edge opens a structural dossier (a real 3D structure in Mol*, the interface, a Claude-written mechanism where every clause opens to a paper, and a proposed wet-lab test); a locked evaluator runs in the map so held-out true edges snap green and misses flash red; and one self-improving loop round folds a confirmed edge back in. That is the whole product. Everything else is upside (see the phase-two ladder in the plan).

## Repo map
```
cartograph/
  README.md                 you are here
  CLAUDE.md                 build context + rules (read first)
  LICENSE                   MIT
  .gitignore
  docs/
    Cartograph_BUILD_SPEC.md            architecture, data contracts, evaluator spec
    Cartograph_7Day_Plan.md             plan of record (core vs phase-two, Day-4 gate)
    Cartograph_Day1_Strategy.md         master decision record + differentiation
    Cartograph_Winning_Playbook.md      winner analysis + the visual demo design
    Cartograph_Claude_Design_brief.md   the brief sent to Claude Design
    Cartograph_Science_Evidence_Checklist.md   how the evidence was gathered
    Cartograph_evidence_review.md        review + corrections to the evidence pack
  design/
    wow_moment_mock.html      visual North Star (open in a browser)
    README.md                 Claude Design exports drop here
  evidence/
    EVIDENCE_MANIFEST.json    catalog + provenance + verification status (read first)
    gordon2020_edges.csv      GROUND TRUTH: 332 bait->prey edges (graph + evaluator input)
    gordon2020_counts.json    verified counts + reconciliation
    demo_protein_shortlist.md ranked demo proteins (Orf6, Orf9b, N top)
    worked_example_orf6.json  flagship held-out example + cited chain (see honesty note)
    crispr_gold_standard.csv  27-gene cross-screen consensus (Option B validation)
    crispr_screens.json       per-screen provenance
    cartograph_domain.json    domain priors (the moat): complexes, family priors, FP patterns
    literature_map.md/.csv    subfield landscape (positioning)
    edge_packs/
      orf6_nup98.json         cited evidence pack
      orf9b_tom70.json        cited evidence pack
      n_g3bp1.json            cited evidence pack
```

## Build order (eval first, demo path first)
1. Freeze the held-out split and write the locked evaluator harness against `evidence/gordon2020_edges.csv`. This is the first commit.
2. Load the edge list into networkx. Confirm counts (332 edges, 26 baits).
3. Enrich with STRING among the prey. Implement degree-normalized L3. Get a baseline evaluator number from structure alone, no LLM. That is the honest floor.
4. Literature retrieval, cached, plus Reader / Skeptic / Curator subagents that produce a cited hypothesis (they read from `evidence/edge_packs/`).
5. Close the loop: fold confirmed edges back, re-run the evaluator, capture before and after.
6. Frontend: the living map (Cytoscape.js), the structural dossier (Mol*), the eval-as-green-edges spectacle.
7. Bulletproof the 3-minute demo path. Cache everything on it. Rehearse.
8. Record the video (reserve the last day), write the summary, finalize the repo, submit.

## Data usage
Everything in `evidence/` was gathered and verified during the event (provenance in `EVIDENCE_MANIFEST.json`). Use `gordon2020_edges.csv` as the graph and evaluator ground truth. On the demo path, read from `evidence/`, never from a live network call.

## Design
`design/wow_moment_mock.html` is the visual target. Claude Design exports will be added to `design/`; wire the frontend to match them and the brief.

## Integrity rules (non-negotiable, these earn scientist trust)
- The graph proposes edges deterministically. Claude never invents an edge from its weights.
- Every claim opens to a paper. A hypothesis with no citation does not render.
- Predicted structures are always labeled predicted, with a confidence number. Never present a prediction as experimental fact.
- The evaluator is locked and separate from the agents, committed before any prediction.

## Flagship honesty check (do not skip)
`evidence/worked_example_orf6.json` labels the path ORF6 -> NUP98 -> RAE1 as "L3", but that path is length 2 (a common-neighbor signal, the thing L3 is meant to beat). Recover ORF6-RAE1 via a genuine length-3 path (enrich STRING around the nucleoporins) and report the L3 rank, or call the 2-edge case complex completion. Full detail in `CLAUDE.md` and `docs/Cartograph_evidence_review.md`.

## License
MIT. All work in this repository is produced during the hackathon.
