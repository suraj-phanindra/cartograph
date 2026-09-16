"""The reporting contract.

The defect this whole layer exists to fix was a number published without its
denominator. So the harness does not emit bare floats. Every metric is a record
carrying the universe it was computed over, the prevalence of positives in that
universe, the enrichment over that prevalence, and the best value any scorer could
have reached.
"""
from backend.bench import report, universe
from backend.eval.evaluator import build_training_graph, predict_all
from backend.eval.freeze_split import load_frozen


def _report(**kw):
    frozen = load_frozen()
    train = build_training_graph(frozen)
    u = universe.candidate_universe(train)
    positives = {tuple(e) for e in frozen["held_out"]}
    reached = {(p["bait"], p["candidate"]): p["score"] for p in predict_all(train)}
    scores = {pair: reached.get(pair, 0.0) for pair in u}
    return report.full_universe_report(scores, positives, **kw)


def test_report_names_its_candidate_set_and_size():
    r = _report()
    assert r["candidate_set"] == "closed_world"
    assert r["universe_size"] == 8357


def test_report_separates_all_targets_from_reachable_targets():
    """These are different quantities and conflating them is what made a label
    claiming 'recall on the reachable set' silently false."""
    r = _report()
    assert r["n_targets"] == 57
    assert r["n_targets_reachable"] == 14
    assert r["reachable_definition"]


def test_report_carries_prevalence():
    r = _report()
    assert round(r["prevalence"], 6) == round(57 / 8357, 6)


def test_every_metric_is_a_record_never_a_bare_number():
    r = _report()
    assert r["metrics"], "no metrics emitted"
    for name, rec in r["metrics"].items():
        assert isinstance(rec, dict), f"{name} is a bare value"
        assert "value" in rec
        assert "max_attainable" in rec


def test_precision_records_carry_enrichment_over_prevalence():
    r = _report()
    p20 = r["metrics"]["precision_at_20"]
    assert round(p20["value"], 4) == 0.4500
    assert round(p20["enrichment"], 1) == 66.0


def test_rank_metrics_declare_their_null_value_not_an_enrichment():
    """Enrichment over prevalence is meaningless for a rank statistic. A reader
    needs the null instead, or 0.6178 looks like a failing grade."""
    r = _report()
    auc = r["metrics"]["roc_auc"]
    assert round(auc["value"], 4) == 0.6178
    assert auc["null_value"] == 0.5
    assert auc.get("enrichment") is None


def test_recall_record_states_the_attainable_ceiling():
    r = _report()
    rec = r["metrics"]["recall_at_50"]
    assert round(rec["value"], 4) == 0.2281
    assert round(rec["max_attainable"], 4) == 0.8772


def test_report_declares_tie_handling():
    assert _report()["tie_handling"] == "midrank"


def test_open_world_variant_uses_the_pinned_background():
    r = _report(open_world_background=20400, open_world_source="test fixture")
    ow = r["open_world"]
    assert ow["universe_size"] == 26 * 20400
    assert ow["source"] == "test fixture"
    assert ow["prevalence"] < r["prevalence"], "open world must be a rarer population"
