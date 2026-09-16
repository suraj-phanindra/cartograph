# CLAUDE.md: Cartograph

**`AGENTS.md` in this directory is the standing context for this repo. Read it before
writing anything.** It carries the current state, the non-negotiable rules, the environment,
the traps, and what the measurements changed. This file is deliberately a pointer so the two
cannot drift apart. Everything below is duplicated from it only because it is load-bearing
enough that an agent must not miss it.

Last updated 2026-09-16.

## What this is

The navigation layer for a protein interaction map. It loads an experimentally-derived
interactome, deterministically proposes edges that should be there but are not yet drawn,
proves each one with the literature and a 3D structure, and measures how often it is right
against a benchmark frozen before any prediction code existed.

Now developed at AI Fund as a possible venture. The audience for results is technical
diligence, not end users. Credibility of the numbers matters more than features.

## The four rules that are the product

1. **Deterministic critical path.** The graph proposes edges. Claude reads, adjudicates and
   explains. Claude never invents an edge from model weights.
2. **The evaluator is LOCKED.** Never edit `backend/eval/`. Import it read-only. A test proves
   the predictor cannot import it.
3. **No citation, no render.** A clause whose PMID is not in the verified pack is dropped.
4. **Publish the number that beats us.** The benchmark exists to surface unflattering results.

## The correction most likely to mislead you

An earlier version of this file said degree-normalized L3 is "proven to beat common neighbors
on PPI networks." **On this repo's own flagship map that is false, and it was measured here.**
On Gordon 2020, L3 loses to a one-line STRING lookup on every metric (p@10 0.30 vs 0.80,
reach 14 vs 20) and loses to common neighbours on reach.

L3 earns its place only where preys are shared between baits, monotonically, across five interactomes
in two regimes including human-human BioPlex. Check `backend/bench/sharing.py` before choosing a scorer. See
`docs/Cartograph_multimap_bakeoff.md`.

Also: `precision@20 = 0.45` is one favourable draw. Over 20 seeds the mean is 0.32, sd 0.10.
Never quote a single-seed metric as a point estimate, and never quote a precision number
without its candidate universe and prevalence.

## Environment, in one line

Python 3.13 in `./.venv` (system python is 3.9 and cannot run this). Secrets in `.env`; the
live agent needs **two** keys, `ANTHROPIC_API_KEY` and `ANTHROPIC_WORKSPACE_ID`.
`./run.sh build | test | serve | api`.

## Conventions

- Prose and docs: short declarative sentences, no em dashes, proof before claims.
- Cite real papers only. Never fabricate a citation, a count, or a score.
- Audit what exists before building the next thing.
- Tell the human what you intend to change before you change it.

**Now read `AGENTS.md`.**
