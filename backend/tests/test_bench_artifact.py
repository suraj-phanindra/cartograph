"""The artifact must publish the full-universe numbers alongside the restricted ones.

Augment, never replace. eval.baseline stays byte-identical so the locked evaluator's
own numbers remain reproducible and the loop honesty check keeps its teeth. The new
eval.full_universe block is what a reader should quote.
"""
import pytest

from backend.build_artifact import build


@pytest.fixture(scope="module")
def art():
    a, _ = build()
    return a


def test_restricted_baseline_is_left_intact(art):
    """The old numbers stay, labelled, so the correction is auditable rather than
    a silent overwrite."""
    b = art["eval"]["baseline"]
    assert b["roc_auc"] == 0.8451
    assert b["headline_precision_at_k"] == 0.45
    assert b["candidate_set"] == "restricted"


def test_full_universe_block_exists_with_its_denominator(art):
    fu = art["eval"]["full_universe"]
    assert fu["candidate_set"] == "closed_world"
    assert fu["universe_size"] == 8357
    assert fu["n_targets"] == 57
    assert fu["n_targets_reachable"] == 14


def test_full_universe_corrects_the_three_wrong_numbers(art):
    m = art["eval"]["full_universe"]["metrics"]
    assert m["roc_auc"]["value"] == 0.6178
    assert m["recall_at_50"]["value"] == 0.2281
    assert m["average_precision"]["value"] == 0.1039


def test_precision_headline_survives_the_correction(art):
    m = art["eval"]["full_universe"]["metrics"]
    assert m["precision_at_20"]["value"] == 0.45
    assert round(m["precision_at_20"]["enrichment"], 1) == 66.0


def test_open_world_background_is_pinned_to_a_real_release(art):
    ow = art["eval"]["full_universe"]["open_world"]
    assert ow["background"] == 20431
    assert "UniProt" in ow["source"]
    assert "2026_03" in ow["source"]


def test_split_class_is_stated_in_the_integrity_block(art):
    """All 57 held-out pairs are class C2 in the Park and Marcotte sense. Saying so
    turns an unusual split into a stated strength, and C3 stays unmeasured."""
    s = art["integrity"]["split_class"]
    assert "C2" in s and "C3" in s


def test_conservation_channel_scores_the_whole_universe(art):
    """The boost was computed over the pairs L3 reaches, so conserved pairs L3 never
    reached were silently unscored."""
    assert art["eval"]["conservation_channel"]["n_conserved_candidates"] == 51
