"""STRING best-score guilt-by-association. The control that gates the central claim.

For a viral bait u and a candidate human prey v, the score is the best STRING score
linking v to any prey u is ALREADY known to bind. There is no path machinery: one hop
from a known prey, and that is the whole method.

It ships as a real channel because it wins. Measured 2026-09-15 across four
interactomes (docs/Cartograph_multimap_bakeoff.md), on both maps whose preys are not
shared between baits -- Gordon 2020 and Penn 2018 -- this lookup beats degree-normalized
L3 on reach, precision@10/20/50 and tie-aware AUC, at p < 1e-7 over 40 paired seeds.
L3 overtakes it only once the AP-MS layer has shared preys; see backend/bench/sharing.py
for the pre-flight statistic that decides which channel to run.

Note what this is NOT: it is one hop from a known prey, never two. A candidate that is
STRING-adjacent to another candidate is not guilty by association with the bait.
"""

from __future__ import annotations


def gba_scores(g, source):
    """Rank candidate human preys for `source` by best STRING link to a known prey.

    Returns a list of dicts sorted by score desc, then candidate name asc:
      {candidate, gba_score, via, n_links}
    `via` names the prey that supplied the winning link, so the score is auditable.
    Candidates already adjacent to source are excluded (we predict MISSING edges).
    """
    known_preys = {n for n in g.neighbors(source) if g.nodes[n].get("type") == "human"}
    if not known_preys:
        return []

    existing = set(g.neighbors(source)) | {source}
    best: dict[str, tuple[float, str]] = {}
    n_links: dict[str, int] = {}

    # sorted iteration -> the recorded `via` is deterministic across runs
    for prey in sorted(known_preys):
        for cand in sorted(g.neighbors(prey)):
            if cand in existing or cand == prey:
                continue
            if g.nodes[cand].get("type") != "human":
                continue
            edge = g.edges[prey, cand]
            if edge.get("kind") != "enrichment":
                continue
            score = float(edge.get("score") or 0.0)
            n_links[cand] = n_links.get(cand, 0) + 1
            current = best.get(cand)
            if current is None or score > current[0]:
                best[cand] = (score, prey)

    out = [
        {
            "candidate": cand,
            "gba_score": round(score, 6),
            "via": via,
            "n_links": n_links[cand],
        }
        for cand, (score, via) in best.items()
    ]
    out.sort(key=lambda d: (-d["gba_score"], d["candidate"]))
    return out


def predict_all(train_graph):
    """Run GBA for every viral bait -> a flat, deterministically ordered proposal list.

    Mirrors the shape of backend.eval.evaluator.predict_all so the two channels are
    interchangeable at a call site.
    """
    baits = sorted(n for n, d in train_graph.nodes(data=True) if d.get("type") == "viral")
    proposals = []
    for bait in baits:
        for c in gba_scores(train_graph, bait):
            proposals.append(
                {
                    "bait": bait,
                    "candidate": c["candidate"],
                    "score": c["gba_score"],
                    "via": [c["via"]],
                }
            )
    proposals.sort(key=lambda p: (-p["score"], p["bait"], p["candidate"]))
    return proposals
