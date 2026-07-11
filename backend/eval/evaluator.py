"""The LOCKED evaluator. Scores a predictor against the frozen held-out set.

This module may import the graph and the predictor (it needs them to run the
prediction it scores). The reverse is forbidden: the predictor and the reasoning
layer must NOT import this module or read heldout.frozen.json. The held-out
truth is revealed only here, at scoring time.

Honest protocol:
  - training graph = enriched interactome with every held-out edge REMOVED, so
    the predictor never sees the answers.
  - run degree-normalized L3 for every bait -> a global ranked list of proposed
    viral->host edges (candidates already known are excluded).
  - a proposed edge is a HIT (green) iff it is in the held-out truth. Everything
    else counts against precision (conservative: we never credit an unlabeled
    edge as correct just because it is plausible).
  - metrics: precision@k, recall@k, ROC-AUC, average precision. Reported with and
    without the disclosed pinned walkthrough edge.
"""

from __future__ import annotations

from backend import config
from backend.graph.enrich import enriched_graph
from backend.predict.l3 import l3_scores
from backend.eval.freeze_split import load_frozen


# --- metric primitives (no sklearn dependency) -----------------------------
def _precision_recall_at_k(labels, k):
    top = labels[:k]
    hits = sum(top)
    total_pos = sum(labels)
    precision = hits / k if k else 0.0
    recall = hits / total_pos if total_pos else 0.0
    return precision, recall, hits


def _roc_auc(labels):
    """ROC-AUC via the Mann-Whitney U statistic over a score-sorted label list.
    `labels` is ordered by predicted score descending; ties already broken
    deterministically upstream, so we use positional ranks."""
    n = len(labels)
    n_pos = sum(labels)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    # rank 1 = lowest score; our list is high->low, so rank = n - index
    sum_ranks_pos = sum((n - i) for i, y in enumerate(labels) if y)
    u = sum_ranks_pos - n_pos * (n_pos + 1) / 2
    return u / (n_pos * n_neg)


def _average_precision(labels):
    total_pos = sum(labels)
    if total_pos == 0:
        return None
    hits = 0
    ap = 0.0
    for i, y in enumerate(labels, 1):
        if y:
            hits += 1
            ap += hits / i
    return ap / total_pos


def build_training_graph(frozen, fold_back=()):
    """Enriched graph with held-out edges removed, plus any fold_back edges
    re-added (the loop round confirms an edge and folds it back in)."""
    g = enriched_graph()
    fold_back = {tuple(e) for e in fold_back}
    for bait, prey in frozen["held_out"]:
        if (bait, prey) in fold_back:
            continue
        if g.has_edge(bait, prey):
            g.remove_edge(bait, prey)
    # mark folded-back edges as confirmed (they are now known to the predictor)
    for bait, prey in fold_back:
        if g.has_node(bait) and g.has_node(prey):
            g.add_edge(bait, prey, kind="confirmed", score=1.0, evidence_ref="loop")
    return g


def predict_all(train_graph, use_prior=False):
    """Run L3 for every viral bait -> a flat list of proposed edges with scores.
    Deterministic ordering (score desc, then bait, then candidate)."""
    baits = [n for n, d in train_graph.nodes(data=True) if d["type"] == "viral"]
    proposals = []
    for bait in sorted(baits):
        for c in l3_scores(train_graph, bait, use_prior=use_prior):
            proposals.append(
                {
                    "bait": bait,
                    "candidate": c["candidate"],
                    "score": c["combined"] if use_prior else c["l3_score"],
                    "path": c["paths"][0] if c["paths"] else None,
                    "via": c.get("via", []),
                }
            )
    key = "score"
    proposals.sort(key=lambda p: (-p[key], p["bait"], p["candidate"]))
    return proposals


def evaluate(fold_back=(), use_prior=False, exclude_pinned=False, target_override=None,
             structure_scores=None, conservation_scores=None):
    """Score the predictor against the frozen held-out set.

    structure_scores / conservation_scores: optional {(bait, prey): boost} — a
    transparent additive corroboration term fused onto the topology score before
    ranking (the L3+structure and L3+conservation channels). Each is an orthogonal
    real signal, evaluated on its own; None = topology only. Neither ever edits the
    frozen split; they only re-rank proposals.

    Returns a dict with precision@k / recall@k / roc_auc / average_precision and
    the per-proposal outcomes (hit/miss) for the in-map green/red display.
    """
    frozen = load_frozen()
    pinned = {tuple(e) for e in frozen["pinned_walkthrough"]}
    fold_back = {tuple(e) for e in fold_back}

    if target_override is not None:
        targets = {tuple(e) for e in target_override}
    else:
        targets = {tuple(e) for e in frozen["held_out"]}
    # folded-back edges are now known, not targets
    targets -= fold_back
    if exclude_pinned:
        targets -= pinned

    train = build_training_graph(frozen, fold_back=fold_back)
    proposals = predict_all(train, use_prior=use_prior)
    prior = structure_scores or conservation_scores
    if prior:
        key = "structure_boost" if structure_scores else "conservation_boost"
        for p in proposals:
            boost = prior.get((p["bait"], p["candidate"]), 0.0)
            if boost:
                p["score"] = p["score"] + boost
                p[key] = boost
        proposals.sort(key=lambda p: (-p["score"], p["bait"], p["candidate"]))

    labels = []
    for p in proposals:
        edge = (p["bait"], p["candidate"])
        hit = edge in targets
        p["outcome"] = "hit" if hit else "miss"
        p["heldout_true"] = hit
        labels.append(1 if hit else 0)

    metrics = {"k": {}}
    for k in config.EVAL_K_VALUES:
        prec, rec, hits = _precision_recall_at_k(labels, k)
        metrics["k"][k] = {"precision": round(prec, 4), "recall": round(rec, 4), "hits": hits}
    metrics["roc_auc"] = round(_roc_auc(labels), 4) if _roc_auc(labels) is not None else None
    ap = _average_precision(labels)
    metrics["average_precision"] = round(ap, 4) if ap is not None else None
    metrics["n_targets"] = len(targets)
    metrics["n_targets_recoverable"] = sum(
        1 for t in targets if any(p["bait"] == t[0] and p["candidate"] == t[1] for p in proposals)
    )
    metrics["n_proposals"] = len(proposals)
    metrics["headline_precision_at_k"] = metrics["k"][config.HEADLINE_K]["precision"]
    metrics["headline_k"] = config.HEADLINE_K

    return {"metrics": metrics, "proposals": proposals, "targets": sorted(targets)}


def per_heldout_recovery(use_prior=False, fold_back=()):
    """For each held-out edge, its rank among its bait's candidates (interpretable
    'how often do we recover a hidden edge' view)."""
    frozen = load_frozen()
    fold_back = {tuple(e) for e in fold_back}
    targets = [tuple(e) for e in frozen["held_out"] if tuple(e) not in fold_back]
    train = build_training_graph(frozen, fold_back=fold_back)

    from backend.predict.l3 import rank_of
    rows = []
    for bait, prey in sorted(targets):
        ranked = l3_scores(train, bait, use_prior=use_prior)
        r = rank_of(ranked, prey)
        rows.append({"bait": bait, "prey": prey, "rank": r, "n_candidates": len(ranked),
                     "recovered": r is not None})
    return rows


if __name__ == "__main__":
    base = evaluate()
    m = base["metrics"]
    print("=== LOCKED EVALUATOR — baseline (L3 topology only, no LLM) ===")
    print(f"held-out targets: {m['n_targets']} ({m['n_targets_recoverable']} recoverable by L3)")
    print(f"proposals ranked: {m['n_proposals']}")
    for k in config.EVAL_K_VALUES:
        kk = m["k"][k]
        print(f"  precision@{k}={kk['precision']:.3f}  recall@{k}={kk['recall']:.3f}  hits={kk['hits']}")
    print(f"  ROC-AUC={m['roc_auc']}  AP={m['average_precision']}")
    print(f"  HEADLINE precision@{m['headline_k']} = {m['headline_precision_at_k']:.3f}")

    rec = per_heldout_recovery()
    recovered = [r for r in rec if r["recovered"]]
    print(f"\nper-held-out recovery: {len(recovered)}/{len(rec)} recovered as candidates")
    ranks = sorted(r["rank"] for r in recovered)
    hits10 = sum(1 for r in recovered if r["rank"] <= 10)
    print(f"  hits@10 (rank<=10 among own bait): {hits10}/{len(rec)}")
    if ranks:
        print(f"  median rank of recovered: {ranks[len(ranks)//2]}")
    orf6 = next((r for r in rec if r["bait"] == "Orf6" and r["prey"] == "RAE1"), None)
    print(f"  flagship Orf6-RAE1: rank {orf6['rank']} of {orf6['n_candidates']}" if orf6 else "  (flagship not in split)")
