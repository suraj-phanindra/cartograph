# AGENTS.md: Cartograph

Standing context for any coding agent working in this repo. Read it before writing
anything. It is auto-loaded, so it stays short and points at the docs for depth.

**Keep it current.** If a measured number or a priority changes, update this file in the
same commit as the change. This is not a formality: the "Current state" block below went
stale within a day of being written, because a merged PR and a new dataset both changed it.
If you are touching a number anywhere in this repo, check whether it also appears here.
Last updated 2026-09-16.

## What this is

The navigation layer for a protein interaction map. Cartograph loads an
experimentally-derived interactome, deterministically proposes edges that should be there
but are not yet drawn, proves each one with the literature and a 3D structure, and measures
how often it is right against a benchmark frozen before any prediction code existed.

Origin: a 6-day solo hackathon build (2026-07-08 to 07-13, Anthropic x Gladstone). It is now
being developed at AI Fund as a possible venture. **The audience for results is technical
diligence, not end users.** Credibility of the numbers matters more than features. A change
that adds product surface without adding evidence is the wrong change.

## Current state, 2026-09-16

- PR #1 and PR #2 both merged to `main`. `main` is unprotected, so nothing gates a red merge.
- 154 tests, about 23 seconds.
- Shipped: the explicit candidate universe with every metric carrying its denominator
  (`backend/bench/`), the STRING guilt-by-association control (`backend/predict/gba.py`),
  the pre-flight statistic (`backend/bench/sharing.py`), and the bake-off
  (`backend/bench/bakeoff.py`).
- Six interactomes loaded: Gordon 2020 SARS-CoV-2, Penn 2018 Mtb, Jager 2011 HIV-1,
  Haas 2023 influenza A, BioPlex 3.0 293T (human-human) and HuRI (two-hybrid, symmetric,
  synthetic bait/prey split).
  See `evidence/multimap/MANIFEST.json` for provenance on each.
- Reproduce the whole comparison with `python -m backend.bench.bakeoff` (about 100 seconds
  at the default 40 seeds).

## Non-negotiable integrity rules. These are the product, not preferences.

1. **Deterministic critical path.** The graph proposes edges. An LLM never invents one; it
   reads, adjudicates and explains. Same question returns the same answer twice.
2. **The evaluator is LOCKED.** `backend/eval/` holds a split frozen as the first commit with
   a sha256 checksum, and a test proves the predictor cannot import it. Never edit
   `backend/eval/`. Import and call it read-only.
3. **No citation, no render.** A mechanistic clause whose PMID is not in the verified pack is
   dropped, not rendered.
4. **Predicted is always labelled predicted.** Experimental structures and predicted models
   are never conflated.
5. **Interface residues are computed from deposited coordinates**, never copied from prose.
6. **Never quote a precision number without its candidate universe and prevalence, and never
   quote a single-seed metric as a point estimate.**
7. **Publish the number that beats us.** The benchmark exists to surface unflattering
   results. Burying one makes it decorative.

## Environment

- Python 3.13 in `./.venv`. The system python is 3.9 and cannot run this project.
- Secrets in `.env` at the repo root, loaded by `backend/config.py`. The live agent needs
  **two** keys: `ANTHROPIC_API_KEY` and `ANTHROPIC_WORKSPACE_ID` (the key is identity-linked
  and every endpoint 400s without the workspace header).
- `./run.sh build | test | serve | api`. Serve is offline on 8791; api adds `/api/*` on 8792.
- Write experiment scripts to a scratch directory, never into the repo.

## What the measurements say. This changes what you should build.

- **On both zero-sharing maps, degree-normalized L3 loses to a one-line STRING lookup on
  every metric.** Gordon: p@10 0.30 vs 0.80, p@20 0.45 vs 0.60, AUC 0.618 vs 0.672, reach 14
  vs 20. An older version of this file claimed L3 is "proven to beat common neighbors." On
  this map that is false, and it was measured here.
- **L3 earns its place only where preys are shared between baits.** Advantage over
  guilt-by-association rises with prey sharing across fifteen map variants from six datasets,
  r = 0.94, because sharing opens a `bait -> prey -> bait' -> prey` route that no length-2
  method can see. It is TOPOLOGICAL: it holds on HuRI, where the bait/prey split is synthetic
  because two-hybrid data is symmetric, with 94% of L3's unique reach routed through a second
  bait. What does NOT hold is magnitude: strict monotonicity fails across regimes, HuRI's
  +40.6pp is inflated by a STRING-starved baseline, and the fifteen variants are only six
  independent datasets. Check `backend/bench/sharing.py` BEFORE choosing a scorer. Gordon
  is 1.000.
- **`precision@20 = 0.45` is a favourable draw.** Over 20 seeds: mean 0.32, sd 0.10,
  range 0.15 to 0.55. Quote the distribution.
- **The ceiling is in the data.** 37 of 57 Gordon held-out edges are unrecoverable by any
  local-topology scorer. More model work does not fix that; enrichment threshold does.
- All 57 Gordon held-out pairs are Park-Marcotte class **C2**. C3 is unmeasured and no
  generalisation to it is claimed.

## Traps that cost an hour each

- `backend/eval/evaluator.py` imports `l3_scores` and calls `enriched_graph()` internally, so
  `evaluate()` is hardwired to Gordon and to one predictor. To benchmark another scorer do NOT
  refactor it: use `build_training_graph(load_frozen())` plus `backend/bench`.
- **The training graph removes the AP-MS edge only.** Rebuilding it from the surviving edge
  list also strips the held-out prey's STRING edges and silently zeroes every topology scorer.
- **Mean prey degree describes the COMPLETE map.** Handing it a training graph counts held-out
  preys at degree 0 and understates sharing.
- `rank()` in `backend/bench/metrics.py` breaks ties alphabetically. For any comparison
  BETWEEN scorers use `expected_precision_at_k` in the same module, since the tie-break
  artifact scales with how coarse a scorer is.
- `evidence/string_enrichment.cached.json` is pre-filtered at `>=700` and **cannot** be
  re-thresholded downward. The `evidence/multimap/*_string150.json` caches can.
- `backend/agent/resolve.py` passes ONE taxid to both ends of an edge, so the Evidence Agent
  degrades to topology-only on every host-pathogen edge. `config.STRING_SPECIES` is pinned to
  human for every upload regardless of organism. Both are known, both are unfixed.
- `backend/bench` is wired only into `build_artifact.py`. Uploaded maps get `_own_eval`:
  precision@min(20, n) on one seed, nothing else.
- The in-map evaluator and loop animations replay baked artifact JSON. They do not compute.
- "Ask the map" is a regex keyword matcher, not language understanding.

## Flagship honesty check (do not skip)

The held-out `Orf6-RAE1` recovery must ride a genuine length-3 path
(`Orf6 -> NUP98 -> NUP214 -> RAE1`), never the 2-edge `Orf6 -> NUP98 -> RAE1` shortcut, which
is a common-neighbour signal and exactly what L3 is supposed to beat. `evidence/`'s
`worked_example_orf6.json` and `gordon2020_counts.json` both mislabel that shortcut as "L3";
that label is wrong and must not propagate into code or demo copy. `backend/predict/l3.py`
asserts the real path under `__main__`.

## Do not

- Edit `backend/eval/`.
- Replace L3 or adopt a learned predictor. 358 nodes and 491 edges have nothing to learn, and
  all indices on one feature share a ceiling. Settle L3 versus STRING on more maps first.
- Build auth, tenancy, billing or multi-user storage. Explicitly out of scope.
- Use STRING as ground truth. It is already a feature, so that is circular.
- Add UI polish. Generalization evidence is the binding constraint, not product surface.

## Read before proposing changes

- `docs/Cartograph_context_package.md` - what this is, the customer, the USP, what the
  evidence does not support. Start here.
- `docs/Cartograph_multimap_bakeoff.md` - the six-map result, why it should be believed, and
  which parts of it should not be quoted as an effect size.
- `docs/Cartograph_research_findings.md` - state of the art, prior art, ordered next steps.
- `docs/Cartograph_gap_audit.md` - demo-vs-product gaps with a measured appendix.

## Conventions

- Prose and docs: short declarative sentences, no em dashes, proof before claims.
- Cite real papers only. Never fabricate a citation, a count, or a score.
- Audit what exists before building the next thing. That loop is underrated.
- Tell the human what you intend to change before you change it.
