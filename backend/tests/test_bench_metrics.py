"""Tie-aware metrics over the full candidate universe.

The locked evaluator ranks by position and documents that ties are broken upstream.
Padding the universe creates one 8,242-member tie block at score 0.0, so positional
ranking manufactures signal out of alphabetical order. These tests pin the honest
values and guard the exact failure mode.
"""
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
