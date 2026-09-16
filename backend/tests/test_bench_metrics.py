"""Tie-aware metrics over the full candidate universe.

The locked evaluator ranks by position and documents that ties are broken upstream.
Padding the universe creates one 8,242-member tie block at score 0.0, so positional
ranking manufactures signal out of alphabetical order. These tests pin the honest
values and guard the exact failure mode.
"""
import pytest
from backend.bench import metrics, universe
from backend.eval.evaluator import build_training_graph, predict_all
from backend.eval.freeze_split import load_frozen


def _setup():
    frozen = load_frozen()
    train = build_training_graph(frozen)
    u = universe.candidate_universe(train)
    positives = {tuple(e) for e in frozen["held_out"]}
    reached = {(p["bait"], p["candidate"]): p["score"] for p in predict_all(train)}
    scores = {pair: reached.get(pair, 0.0) for pair in u}
    return scores, positives, u


def test_all_zeros_scorer_scores_exactly_one_half():
    """The guard. A scorer expressing no preference must not earn credit from
    the order its ties happen to fall in."""
    _, positives, u = _setup()
    flat = {pair: 0.0 for pair in u}
    assert metrics.roc_auc(flat, positives) == 0.5


def test_perfect_scorer_scores_one():
    _, positives, u = _setup()
    perfect = {pair: (1.0 if pair in positives else 0.0) for pair in u}
    assert metrics.roc_auc(perfect, positives) == 1.0


def test_roc_auc_is_tie_aware_not_positional():
    scores, positives, _ = _setup()
    assert round(metrics.roc_auc(scores, positives), 4) == 0.6178


def test_precision_at_k_is_unchanged_by_the_larger_universe():
    """Precision@k is invariant to expanding the negative set when the top-k is
    unchanged. This is why the 45% headline survives and the others do not."""
    scores, positives, _ = _setup()
    ranked = metrics.rank(scores)
    assert round(metrics.precision_at_k(ranked, positives, 10), 4) == 0.3000
    assert round(metrics.precision_at_k(ranked, positives, 20), 4) == 0.4500
    assert round(metrics.precision_at_k(ranked, positives, 50), 4) == 0.2600


def test_recall_denominator_is_all_positives_not_the_reachable_subset():
    scores, positives, _ = _setup()
    ranked = metrics.rank(scores)
    assert round(metrics.recall_at_k(ranked, positives, 50), 4) == 0.2281


def test_average_precision_over_the_full_universe():
    scores, positives, _ = _setup()
    ranked = metrics.rank(scores)
    assert round(metrics.average_precision(ranked, positives), 4) == 0.1039


def test_max_attainable_recall_is_capped_by_k_over_positives():
    """57 positives into 50 slots caps recall@50 at 0.8772, which is why a
    reported 0.9286 was provably not a global figure."""
    assert round(metrics.max_recall_at_k(50, 57), 4) == 0.8772
    assert metrics.max_recall_at_k(100, 57) == 1.0


def test_max_attainable_precision_is_capped_by_positives_over_k():
    assert metrics.max_precision_at_k(10, 57) == 1.0
    assert round(metrics.max_precision_at_k(100, 57), 4) == 0.5700


def test_ranking_is_deterministic():
    scores, _, _ = _setup()
    assert metrics.rank(scores) == metrics.rank(scores)


# --- expected precision under random tie-breaking -------------------------------
# rank() breaks ties alphabetically, which lets a coarse scorer (few distinct scores)
# have the alphabet decide its top-k. Measured on Gordon: common neighbours has 4
# distinct scores over 92 pairs, and its published precision@10 of 0.600 sat at the
# 97.9th percentile of tie-break outcomes against an expectation of 0.464.

def test_expected_precision_matches_plain_precision_when_there_are_no_ties():
    scores = {("b", "p1"): 0.9, ("b", "p2"): 0.8, ("b", "p3"): 0.7, ("b", "p4"): 0.6}
    positives = {("b", "p1"), ("b", "p3")}
    universe = set(scores)
    ranked = metrics.rank(scores)
    assert metrics.expected_precision_at_k(scores, positives, universe, 2) == \
        metrics.precision_at_k(ranked, positives, 2)


def test_a_scorer_with_no_preference_scores_exactly_the_prevalence():
    """The precision analogue of the all-zeros AUC test. If every pair ties, no
    ordering is expressed, so expected precision@k must equal the base rate."""
    universe = {("b", f"p{i}") for i in range(10)}
    scores = {p: 0.0 for p in universe}
    positives = {("b", "p0"), ("b", "p1")}
    assert metrics.expected_precision_at_k(scores, positives, universe, 5) == 0.2


def test_a_partially_consumed_tie_group_contributes_its_share():
    """Two slots left, a tie group of 4 holding 2 positives: expect 2 * 2/4 = 1 hit."""
    universe = {("b", f"p{i}") for i in range(5)}
    scores = {("b", "p0"): 1.0, ("b", "p1"): 0.5, ("b", "p2"): 0.5,
              ("b", "p3"): 0.5, ("b", "p4"): 0.5}
    positives = {("b", "p0"), ("b", "p1"), ("b", "p2")}
    # k=3: p0 taken outright (1 hit), then 2 of the 4 tied -> 2 * (2/4) = 1.0
    assert metrics.expected_precision_at_k(scores, positives, universe, 3) == \
        pytest.approx(2.0 / 3.0)


def test_pairs_the_scorer_never_reached_are_ranked_last_not_dropped():
    """Unreached pairs score 0 and sit in the final tie group, so the metric is never
    computed on a predictor-selected subset."""
    universe = {("b", f"p{i}") for i in range(4)}
    scores = {("b", "p0"): 0.9}            # the scorer reached exactly one pair
    positives = {("b", "p0"), ("b", "p3")}
    assert metrics.expected_precision_at_k(scores, positives, universe, 1) == 1.0
    # k=2: p0 outright, then 1 of the 3 unreached, which hold 1 positive -> 1/3
    assert metrics.expected_precision_at_k(scores, positives, universe, 2) == \
        pytest.approx((1 + 1 / 3) / 2)


def test_k_beyond_the_universe_still_divides_by_k():
    universe = {("b", "p0"), ("b", "p1")}
    scores = {("b", "p0"): 1.0, ("b", "p1"): 0.5}
    assert metrics.expected_precision_at_k(scores, {("b", "p0")}, universe, 4) == 0.25
