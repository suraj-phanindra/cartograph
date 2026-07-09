"""Degree-normalized L3 link prediction (Kovacs et al. 2019).

The deterministic critical path. The graph PROPOSES candidate edges by counting
length-3 paths, degree-normalized to suppress hub bias. Claude never touches
this; it only reads, adjudicates, and explains the candidates that come out.

score(u, v) = sum over length-3 paths  u - a - b - v  of  1 / sqrt(deg(a)*deg(b))

For a viral bait u and a candidate human prey v (not already linked to u), the
first hop a is a known prey of u, the middle hop a-b is a human-human enrichment
(or known) edge, and b-v closes onto the candidate. This is exactly why the
flagship needs real enrichment: Orf6 -> NUP98 -> NUP214 -> RAE1 is a genuine
length-3 path, not the 2-edge Orf6 -> NUP98 -> RAE1 shortcut (which is an L2
common-neighbor signal, the thing L3 is meant to beat).

The optional domain-prior boost (shared-complex membership) is kept as a SEPARATE,
logged term so the raw topological score is always inspectable on its own.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict

from backend import config


def _load_complexes():
    """Map each human gene -> set of known complex names it belongs to."""
    data = json.loads(config.DOMAIN_JSON.read_text())
    gene_to_complexes = defaultdict(set)
    for cx in data.get("known_prey_complexes", []):
        for m in cx.get("members", []):
            gene_to_complexes[m].add(cx["name"])
    return gene_to_complexes


_COMPLEXES = None


def _prior_boost(g, source, candidate, gene_to_complexes):
    """Transparent prior: does the candidate share a known complex with any
    current prey of the source? Returns a small additive boost + the reason."""
    src_preys = {n for n in g.neighbors(source) if g.nodes[n]["type"] == "human"}
    cand_cx = gene_to_complexes.get(candidate, set())
    if not cand_cx:
        return 0.0, None
    for prey in src_preys:
        shared = cand_cx & gene_to_complexes.get(prey, set())
        if shared:
            return 0.15, f"shares complex '{sorted(shared)[0]}' with prey {prey}"
    return 0.0, None


def l3_scores(g, source, use_prior=False, top_paths=3):
    """Rank candidate human preys for `source` by degree-normalized L3.

    Returns a list of dicts sorted by score desc:
      {candidate, l3_score, prior_boost, combined, n_paths, paths, prior_reason}
    Candidates already adjacent to source are excluded (we predict MISSING edges).
    """
    global _COMPLEXES
    if use_prior and _COMPLEXES is None:
        _COMPLEXES = _load_complexes()

    existing = set(g.neighbors(source)) | {source}
    scores = defaultdict(float)
    paths = defaultdict(list)

    # sorted iteration -> the recorded display path is deterministic across runs
    for a in sorted(g.neighbors(source)):
        deg_a = g.degree(a)
        for b in sorted(g.neighbors(a)):
            if b == source or b == a:
                continue
            deg_b = g.degree(b)
            w = 1.0 / math.sqrt(deg_a * deg_b)
            for v in sorted(g.neighbors(b)):
                if v in existing or v == a or v == b:
                    continue
                if g.nodes[v]["type"] != "human":
                    continue
                scores[v] += w
                paths[v].append([source, a, b, v])

    out = []
    for v, s in scores.items():
        boost, reason = (0.0, None)
        if use_prior:
            boost, reason = _prior_boost(g, source, v, _COMPLEXES)
        vpaths = paths[v]
        out.append(
            {
                "candidate": v,
                "l3_score": round(s, 6),
                "prior_boost": boost,
                "combined": round(s + boost, 6),
                "n_paths": len(vpaths),
                "paths": vpaths[:top_paths],
                "via": sorted({p[2] for p in vpaths}),  # distinct middle nodes
                "prior_reason": reason,
            }
        )
    # deterministic ordering: score desc, then candidate name asc
    key = "combined" if use_prior else "l3_score"
    out.sort(key=lambda d: (-d[key], d["candidate"]))
    return out


def rank_of(candidates, target):
    """1-indexed rank of `target` in a ranked candidate list, or None."""
    for i, c in enumerate(candidates, 1):
        if c["candidate"] == target:
            return i
    return None


def pick_display_path(candidate_entry, preferred=None):
    """Choose a genuine length-3 path to display. Prefers `preferred` (e.g. the
    canonical flagship path) when it is among the candidate's real paths, else the
    first (deterministic) real path. All returned paths are genuine 3-edge paths."""
    paths = candidate_entry.get("paths", [])
    if preferred and preferred in paths:
        return preferred
    return paths[0] if paths else None


if __name__ == "__main__":
    from backend.graph.enrich import enriched_graph

    # Flagship self-check. The predictor stays blind to the evaluator: it does not
    # import the locked split, it just removes the single flagship edge to show the
    # recovery. (The real held-out set lives only in backend/eval/.)
    g = enriched_graph()
    train = g.copy()
    train.remove_edge(*config.FLAGSHIP_HELDOUT_EDGE)

    ranked = l3_scores(train, "Orf6")
    r = rank_of(ranked, "RAE1")
    print(f"Orf6 candidates (RAE1 held out): {len(ranked)} scored")
    print(f"  RAE1 rank for Orf6: {r} of {len(ranked)} (honest floor; topology alone)")
    for c in ranked[:5]:
        print(f"    {c['candidate']:>8}  L3={c['l3_score']:.4f}  via={c['via']}")
    rae1 = next((c for c in ranked if c["candidate"] == "RAE1"), None)
    assert rae1, "RAE1 not recovered at all!"
    # honesty: every recorded path must be a genuine length-3 path (all edges real)
    for p in rae1["paths"]:
        assert len(p) == 4, "not length-3"
        assert all(train.has_edge(p[i], p[i + 1]) for i in range(3)), f"fake edge in {p}"
    disp = pick_display_path(rae1, preferred=config.FLAGSHIP_PATH)
    print(f"  RAE1 display path (genuine, all edges real): {disp}")
    assert disp == config.FLAGSHIP_PATH, "canonical flagship path unavailable"
    print("  flagship honesty: PASS — RAE1 recovered via genuine length-3 paths; "
          "canonical Orf6->NUP98->NUP214->RAE1 confirmed real")
