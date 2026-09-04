"""Metric records: a value never travels without its denominator.

The published defect was "ROC-AUC = 0.845 on all candidate edges" where the candidate
set was in fact the 115 pairs the predictor reached, about 1.4% of the untested pairs.
A reader could not detect that from the number. So the harness emits records, and a
record that cannot state its universe is a bug rather than a rounding difference.

Enrichment over prevalence is reported for precision, where it is meaningful. Rank
statistics report their null value instead, because 0.6178 read against a 0.5 null is
a modest positive result while 0.6178 read against nothing looks like a failure.
"""
from __future__ import annotations

from backend import config
from backend.bench import metrics as M
from backend.bench import universe as U


def _precision_record(ranked, positives, k, prevalence):
    value = M.precision_at_k(ranked, positives, k)
    return {
        "value": round(value, 4),
        "max_attainable": round(M.max_precision_at_k(k, len(positives)), 4),
        "enrichment": round(U.enrichment(value, prevalence), 2) if prevalence else None,
    }


def _recall_record(ranked, positives, k):
    return {
        "value": round(M.recall_at_k(ranked, positives, k), 4),
        "max_attainable": round(M.max_recall_at_k(k, len(positives)), 4),
        "enrichment": None,
    }


def full_universe_report(scores, positives, candidate_set="closed_world",
                         k_values=None, open_world_background=None,
                         open_world_source=None):
    """Score a pair-to-score mapping over the universe those pairs define.

    `scores` must already cover the whole universe, with unreached pairs at 0.0.
    Padding is the caller's job because only the caller knows which universe applies.
    """
    k_values = list(k_values or config.EVAL_K_VALUES)
    positives = {tuple(p) for p in positives}
    n_universe = len(scores)
    prevalence = U.prevalence(len(positives), n_universe)
    ranked = M.rank(scores)

    out = {
        "candidate_set": candidate_set,
        "universe_size": n_universe,
        "n_targets": len(positives),
        "n_targets_reachable": sum(1 for p in positives if scores.get(p, 0.0) > 0.0),
        "reachable_definition": "the scorer assigns a nonzero score",
        "prevalence": prevalence,
        "tie_handling": "midrank",
        "metrics": {},
    }

    for k in k_values:
        out["metrics"][f"precision_at_{k}"] = _precision_record(ranked, positives, k, prevalence)
        out["metrics"][f"recall_at_{k}"] = _recall_record(ranked, positives, k)

    out["metrics"]["roc_auc"] = {
        "value": round(M.roc_auc(scores, positives), 4),
        "max_attainable": 1.0,
        "null_value": 0.5,
        "enrichment": None,
    }
    out["metrics"]["average_precision"] = {
        "value": round(M.average_precision(ranked, positives), 4),
        "max_attainable": 1.0,
        "null_value": round(prevalence, 6),
        "enrichment": None,
    }

    if open_world_background:
        n_baits = len({b for b, _ in scores})
        size = U.open_world_size(n_baits, open_world_background)
        out["open_world"] = {
            "universe_size": size,
            "n_baits": n_baits,
            "background": open_world_background,
            "source": open_world_source,
            "prevalence": U.prevalence(len(positives), size),
            "note": ("Precision@k is unchanged by the wider background. Prevalence and "
                     "therefore enrichment are not."),
        }
    return out
