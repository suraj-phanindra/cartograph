"""The six-map bake-off. Reproduces docs/Cartograph_multimap_bakeoff.md.

PRIMARY ENDPOINT IS AVERAGE PRECISION, and the reason is a correction. An earlier version
of this module headlined `reach` -- the count of held-out positives a scorer assigns any
non-zero score. That is support-set size, not retrieval: the panel's own `Random` scorer
reaches 100% of positives on every map, and `PrefAttach` reaches more than L3 on every
pathogen map. Every conclusion drawn from it was an artifact. `reach` is still reported,
labelled as a diagnostic, because the gap between support and ranking is itself the finding:
CN and STRING-GBA have IDENTICAL support on all three pathogen maps and average precision
differing by up to 2.9x.

Runs one scorer panel, one split protocol and one set of tie-aware metrics across
every AP-MS map in evidence/multimap/ plus the committed Gordon map, and reports the
paired L3-versus-guilt-by-association comparison that the deployment rule rests on.

Read-only with respect to the locked evaluator: it imports nothing from backend/eval/
except the training-graph builder, and it never reads the frozen split.

    python -m backend.bench.bakeoff            # all maps, 40 seeds, STRING >= 0.700
    python -m backend.bench.bakeoff 20 0.4     # 20 seeds, STRING >= 0.400

The full default run takes about four minutes: the two subsampled human maps have
candidate universes of roughly 380,000 pairs each, against 8,357 for Gordon. Pass a
smaller seed count while iterating.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
from collections import Counter

import networkx as nx

from backend import config
from backend.bench import metrics as bm
from backend.bench import universe as bu
from backend.predict import gba
from backend.predict.cobait import cobait_scores
from backend.predict.l3 import l3_scores

MULTIMAP_DIR = config.EVIDENCE_DIR / "multimap" if hasattr(config, "EVIDENCE_DIR") else None
K_VALUES = (10, 20, 50, 200)  # 200 included so a deployable budget is visible
HELD_FRACTION = 0.17  # matches the frozen Gordon split: 57 of 332


# ---------------------------------------------------------------- loading
def _dir():
    from pathlib import Path
    return Path(__file__).resolve().parents[2] / "evidence"


def load_map(key: str):
    """Return (edges, string_edges) for a map key in evidence/multimap/, or 'gordon'."""
    ev = _dir()
    if key == "gordon":
        rows = list(csv.DictReader(open(ev / "gordon2020_edges.csv")))
        edges = [(r["bait"], r["prey_gene"]) for r in rows]
        string = json.load(open(ev / "string_enrichment.cached.json"))["edges"]
        return edges, string
    rows = list(csv.DictReader(open(ev / "multimap" / f"{key}_edges.csv")))
    edges = [(r["bait"], r["prey_gene"]) for r in rows]
    string = json.load(open(ev / "multimap" / f"{key}_string150.json"))["edges"]
    return edges, string


def build_map_graph(edges, string_edges, threshold: float):
    """Bipartite AP-MS graph plus STRING physical edges among the preys."""
    g = nx.Graph()
    preys = set()
    for bait, prey in edges:
        g.add_node(bait, type="viral")
        g.add_node(prey, type="human")
        g.add_edge(bait, prey, kind="known")
        preys.add(prey)
    for e in string_edges:
        a, b, s = e["a"], e["b"], e["score"]
        if s >= threshold and a != b and a in preys and b in preys:
            g.add_edge(a, b, kind="enrichment", score=s)
    return g


# ---------------------------------------------------------------- scorers
def _l3(train, uni):
    out = {}
    for b in sorted(n for n, d in train.nodes(data=True) if d["type"] == "viral"):
        for c in l3_scores(train, b):
            if (b, c["candidate"]) in uni:
                out[(b, c["candidate"])] = c["l3_score"]
    return out


def _gba(train, uni):
    return {(p["bait"], p["candidate"]): p["score"]
            for p in gba.predict_all(train) if (p["bait"], p["candidate"]) in uni}


def _neighbourhood(train, uni):
    cn, ra, aa = {}, {}, {}
    for (b, p) in uni:
        shared = set(train.neighbors(b)) & set(train.neighbors(p))
        if not shared:
            continue
        cn[(b, p)] = float(len(shared))
        ra[(b, p)] = sum(1.0 / train.degree(z) for z in shared if train.degree(z))
        aa[(b, p)] = sum(1.0 / math.log(train.degree(z)) for z in shared
                         if train.degree(z) > 1)
    return cn, ra, aa


def panel(train, uni, rng):
    cn, ra, aa = _neighbourhood(train, uni)
    return {
        "L3": _l3(train, uni),
        "CN": cn,
        "RA": ra,
        "AA": aa,
        "STRING-GBA": _gba(train, uni),
        "co-bait": cobait_scores(train, uni),
        "PrefAttach": {(b, p): float(train.degree(b) * train.degree(p)) for (b, p) in uni},
        "Random": {pair: rng.random() for pair in uni},
    }


# ---------------------------------------------------------------- one trial
def run_trial(edges, string_edges, threshold, seed, held_frac=HELD_FRACTION):
    """Hold out a fraction of the AP-MS edges, score the panel, return the metrics.

    The training graph is the FULL enriched graph minus the held-out AP-MS edges.
    Rebuilding it from the surviving edge list instead would also strip the held-out
    prey's STRING edges, which silently zeroes every topology scorer.
    """
    rng = random.Random(seed)
    held = set(rng.sample(sorted(edges), round(len(edges) * held_frac)))
    train = build_map_graph(edges, string_edges, threshold)
    train.remove_edges_from(held)

    uni = bu.candidate_universe(train)
    positives = {e for e in held if e in uni}
    if not positives:
        return None

    result = {}
    for name, scores in panel(train, uni, rng).items():
        full = {pair: scores.get(pair, 0.0) for pair in uni}
        ranked = bm.rank(full)
        row = {
            # primary: budget-matched retrieval
            "ap": bm.average_precision(ranked, positives),
            "auc": bm.roc_auc(full, positives),
            # diagnostic only: support-set size. NOT a performance metric. Random scores 1.0.
            "reach_frac": sum(1 for p in positives if scores.get(p, 0.0) > 0) / len(positives),
            "support": len(scores),
        }
        for k in K_VALUES:
            row[f"p@{k}"] = bm.expected_precision_at_k(scores, positives, uni, k)
            row[f"r@{k}"] = bm.recall_at_k(ranked, positives, k)
        result[name] = row
    result["_meta"] = {"universe": len(uni), "positives": len(positives),
                       "prevalence": bu.prevalence(len(positives), len(uni))}
    return result


# ---------------------------------------------------------------- statistics
def sign_test(diffs):
    """Exact two-sided binomial sign test over paired differences."""
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return 1.0, pos, neg
    k = min(pos, neg)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n * 2
    return min(1.0, p), pos, neg


def compare(key, seeds=20, threshold=0.700):
    """Score the whole panel on one map and rank it by average precision.

    Deliberately NOT a two-method advocacy comparison. An earlier version reported only
    L3 versus STRING-GBA, which hid that common neighbours ties or beats L3 on the maps
    where L3 was claimed to win.

    No p-values. A sign test over re-splits of one fixed edge list returns 2^-(n-1)
    whenever one method sweeps, so it reports the seed count rather than the evidence:
    Gordon's effect is stable while that p walks from 2e-03 to 1.4e-40 as seeds go 10
    to 160. Per-seed spread is reported instead.
    """
    edges, string_edges = load_map(key)
    trials = [t for t in (run_trial(edges, string_edges, threshold, s) for s in range(seeds)) if t]
    preys = Counter(p for _, p in edges)
    names = [n for n in trials[0] if n != "_meta"]
    rows = []
    for n in names:
        ap = [t[n]["ap"] for t in trials]
        rows.append({
            "scorer": n,
            "ap": round(statistics.mean(ap), 4),
            "ap_sd": round(statistics.stdev(ap), 4) if len(ap) > 1 else 0.0,
            "r@50": round(statistics.mean(t[n]["r@50"] for t in trials), 4),
            "r@200": round(statistics.mean(t[n]["r@200"] for t in trials), 4),
            "auc": round(statistics.mean(t[n]["auc"] for t in trials), 4),
            "reach_pct": round(100 * statistics.mean(t[n]["reach_frac"] for t in trials), 1),
        })
    rows.sort(key=lambda r: -r["ap"])
    return {
        "map": key,
        "shared_prey_pct": round(100 * sum(1 for c in preys.values() if c > 1) / len(preys), 1),
        "mean_prey_degree": round(sum(preys.values()) / len(preys), 4),
        "positives": round(statistics.mean(t["_meta"]["positives"] for t in trials)),
        "seeds": len(trials),
        "panel": rows,
        "best_by_ap": rows[0]["scorer"],
    }


# Ordered by prey sharing, which is the variable the result turns on. BioPlex is the
# out-of-regime entry: human-human, no pathogen, subsampled to K=200 baits because
# STRING's API rejects more than 2000 identifiers. See evidence/multimap/MANIFEST.json.
MAPS = ("penn2018_mtb", "gordon", "jager2011_hiv", "bioplex3_293t_k200", "haas2023_iav",
        "huri2020_k200_synthbaits")
# huri2020_k200_synthbaits is a SYNTHETIC bipartition of a symmetric two-hybrid network, and
# its STRING-starved preys leave the GBA baseline near its null. It belongs here because it
# shows the mechanism is topological, but its advantage is not a usable effect size.


def main(seeds=20, threshold=0.700):
    results = [compare(k, seeds, threshold) for k in MAPS]
    results.sort(key=lambda r: r["shared_prey_pct"])
    print(f"six-map bakeoff | {seeds} seeds | STRING >= {threshold} | held out {HELD_FRACTION:.0%}")
    print("primary endpoint: average precision. `reach` is a DIAGNOSTIC, not performance.\n")
    for r in results:
        print(f"{r['map']}  ({r['shared_prey_pct']}% shared preys, "
              f"mean prey degree {r['mean_prey_degree']}, ~{r['positives']} positives)")
        print(f"    {'scorer':<12}{'AP':>9}{'+/-sd':>8}{'r@50':>8}{'r@200':>8}{'AUC':>8}{'reach':>8}")
        for row in r["panel"]:
            print(f"    {row['scorer']:<12}{row['ap']:>9.4f}{row['ap_sd']:>8.4f}"
                  f"{row['r@50']:>8.4f}{row['r@200']:>8.4f}{row['auc']:>8.4f}"
                  f"{row['reach_pct']:>7.1f}%")
        print()
    print("best by average precision, per map:")
    for r in results:
        print(f"    {r['map']:<26} {r['best_by_ap']}")
    l3_wins = [r["map"] for r in results if r["best_by_ap"] == "L3"]
    print(f"\nL3 is best on {len(l3_wins)} of {len(results)} maps: {l3_wins or 'none'}")
    print("Random's reach is 100% on every map, which is why reach is not an endpoint.")
    return results


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20,
         float(sys.argv[2]) if len(sys.argv) > 2 else 0.700)
