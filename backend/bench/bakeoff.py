"""The five-map bake-off. Reproduces docs/Cartograph_multimap_bakeoff.md.

Runs one scorer panel, one split protocol and one set of tie-aware metrics across
every AP-MS map in evidence/multimap/ plus the committed Gordon map, and reports the
paired L3-versus-guilt-by-association comparison that the deployment rule rests on.

Read-only with respect to the locked evaluator: it imports nothing from backend/eval/
except the training-graph builder, and it never reads the frozen split.

    python -m backend.bench.bakeoff            # all maps, 40 seeds, STRING >= 0.700
    python -m backend.bench.bakeoff 20 0.4     # 20 seeds, STRING >= 0.400
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
from backend.bench import sharing
from backend.bench import universe as bu
from backend.predict import gba
from backend.predict.l3 import l3_scores

MULTIMAP_DIR = config.EVIDENCE_DIR / "multimap" if hasattr(config, "EVIDENCE_DIR") else None
K_VALUES = (10, 20, 50)
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
        row = {
            "reach": sum(1 for p in positives if scores.get(p, 0.0) > 0),
            "reach_frac": sum(1 for p in positives if scores.get(p, 0.0) > 0) / len(positives),
            "auc": bm.roc_auc(full, positives),
        }
        for k in K_VALUES:
            row[f"p@{k}"] = bm.expected_precision_at_k(scores, positives, uni, k)
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


def compare(key, seeds=40, threshold=0.700):
    """L3 versus STRING-GBA on one map, paired across seeds."""
    edges, string_edges = load_map(key)
    trials = [t for t in (run_trial(edges, string_edges, threshold, s) for s in range(seeds)) if t]
    preys = Counter(p for _, p in edges)
    shared_pct = 100 * sum(1 for c in preys.values() if c > 1) / len(preys)
    lr = [t["L3"]["reach_frac"] for t in trials]
    gr = [t["STRING-GBA"]["reach_frac"] for t in trials]
    diffs = [a - b for a, b in zip(lr, gr)]
    p, wins, losses = sign_test(diffs)
    return {
        "map": key,
        "shared_prey_pct": round(shared_pct, 1),
        "mean_prey_degree": round(sum(preys.values()) / len(preys), 4),
        "positives": round(statistics.mean(t["_meta"]["positives"] for t in trials)),
        "l3_reach_pct": round(100 * statistics.mean(lr), 1),
        "gba_reach_pct": round(100 * statistics.mean(gr), 1),
        "advantage_pp": round(100 * statistics.mean(diffs), 1),
        "l3_wins": wins, "l3_losses": losses, "sign_p": p,
        "l3_auc": round(statistics.mean(t["L3"]["auc"] for t in trials), 4),
        "gba_auc": round(statistics.mean(t["STRING-GBA"]["auc"] for t in trials), 4),
        "recommended": sharing.recommended_channel(
            build_map_graph(edges, string_edges, threshold))["channel"],
    }


# Ordered by prey sharing, which is the variable the result turns on. BioPlex is the
# out-of-regime entry: human-human, no pathogen, subsampled to K=200 baits because
# STRING's API rejects more than 2000 identifiers. See evidence/multimap/MANIFEST.json.
MAPS = ("penn2018_mtb", "gordon", "jager2011_hiv", "haas2023_iav", "bioplex3_293t_k200")


def main(seeds=40, threshold=0.700):
    rows = sorted((compare(k, seeds, threshold) for k in MAPS),
                  key=lambda r: r["shared_prey_pct"])
    print(f"four-map bakeoff | {seeds} seeds | STRING >= {threshold} | held out {HELD_FRACTION:.0%}\n")
    head = f"{'map':<16}{'shared':>8}{'pos':>5}{'L3 rch':>8}{'GBA rch':>9}{'adv':>9}{'W/L':>8}{'sign p':>10}{'run':>12}"
    print(head + "\n" + "-" * len(head))
    for r in rows:
        print(f"{r['map']:<16}{r['shared_prey_pct']:>7.1f}%{r['positives']:>5}"
              f"{r['l3_reach_pct']:>7.1f}%{r['gba_reach_pct']:>8.1f}%"
              f"{r['advantage_pp']:>+8.1f}pp{str(r['l3_wins'])+'/'+str(r['l3_losses']):>8}"
              f"{r['sign_p']:>10.1e}{r['recommended']:>12}")
    adv = [r["advantage_pp"] for r in rows]
    mono = all(adv[i] <= adv[i + 1] for i in range(len(adv) - 1))
    print(f"\nadvantage by ascending prey sharing: {adv}")
    print(f"monotonic: {mono}")
    return rows


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40,
         float(sys.argv[2]) if len(sys.argv) > 2 else 0.700)
