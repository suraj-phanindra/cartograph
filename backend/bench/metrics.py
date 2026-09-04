"""Metrics computed over an explicit candidate universe, with tie-aware ranking.

Why this exists rather than reusing backend/eval/evaluator.py: that module is locked,
and its ROC-AUC ranks by list position with the docstring note that ties are broken
deterministically upstream. That assumption holds for a 115-item proposal list where
scores are nearly all distinct. It fails on a full universe, where most pairs are tied
at zero and alphabetical order would decide the result. Fed the padded universe the
positional implementation returns 0.6497 against a tie-aware 0.6178, an inflation of
0.0319 manufactured entirely by the tiebreak.

Every function here takes the positive set explicitly, so no metric can be computed
against a denominator the caller did not choose.
"""
from __future__ import annotations


def rank(scores: dict[tuple[str, str], float]) -> list[tuple[str, str]]:
    """Deterministic ordering: score descending, then bait, then candidate.

    Matches the locked evaluator's tiebreak so top-k comparisons stay comparable.
    Ordering within a tie block is arbitrary by construction, which is exactly why
    roc_auc below does not use position.
    """
    return sorted(scores, key=lambda p: (-scores[p], p[0], p[1]))


def precision_at_k(ranked: list, positives: set, k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    return sum(1 for p in ranked[:k] if p in positives) / k


def recall_at_k(ranked: list, positives: set, k: int) -> float:
    """Denominator is every positive, never the subset the scorer happened to reach."""
    if not positives:
        raise ValueError("no positives")
    return sum(1 for p in ranked[:k] if p in positives) / len(positives)


def average_precision(ranked: list, positives: set) -> float:
    if not positives:
        raise ValueError("no positives")
    hits = 0
    total = 0.0
    for i, pair in enumerate(ranked, 1):
        if pair in positives:
            hits += 1
            total += hits / i
    return total / len(positives)


def roc_auc(scores: dict[tuple[str, str], float], positives: set) -> float:
    """Mann-Whitney U with mid-ranks, so tied pairs contribute 0.5 each.

    A scorer that expresses no preference scores exactly 0.5, which a positional
    implementation does not guarantee.
    """
    pos = [s for p, s in scores.items() if p in positives]
    neg = [s for p, s in scores.items() if p not in positives]
    if not pos or not neg:
        raise ValueError("need both positives and negatives in the universe")

    ordered = sorted(neg)
    concordant = 0.0
    for s in pos:
        lower = _count_lt(ordered, s)
        equal = _count_lt(ordered, s, inclusive=True) - lower
        concordant += lower + 0.5 * equal
    return concordant / (len(pos) * len(neg))


def _count_lt(ordered: list[float], value: float, inclusive: bool = False) -> int:
    """Index of the first element not less than (or not less than or equal to) value."""
    lo, hi = 0, len(ordered)
    while lo < hi:
        mid = (lo + hi) // 2
        below = ordered[mid] <= value if inclusive else ordered[mid] < value
        if below:
            lo = mid + 1
        else:
            hi = mid
    return lo


def max_precision_at_k(k: int, n_positives: int) -> float:
    """Best precision@k any scorer could reach given how many positives exist."""
    if k <= 0:
        raise ValueError("k must be positive")
    return min(1.0, n_positives / k)


def max_recall_at_k(k: int, n_positives: int) -> float:
    """Best recall@k any scorer could reach. k slots cannot hold more than k positives."""
    if n_positives <= 0:
        raise ValueError("no positives")
    return min(1.0, k / n_positives)
