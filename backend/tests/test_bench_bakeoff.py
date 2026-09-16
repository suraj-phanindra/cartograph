"""The four-map result, regression-protected.

docs/Cartograph_multimap_bakeoff.md makes one claim the product now depends on: L3
beats STRING guilt-by-association if and only if the map has shared preys. These tests
pin the direction of that result on the two extremes, and pin that the cheap pre-flight
statistic agrees with the expensive measurement.

Kept to a few seeds so it stays in the normal suite. The published table uses 40.
"""
import pytest

from backend.bench import bakeoff, sharing

SEEDS = 5


def _panel(key, seeds=3):
    edges, string_edges = bakeoff.load_map(key)
    trials = [t for t in (bakeoff.run_trial(edges, string_edges, 0.700, s)
                          for s in range(seeds)) if t]
    assert trials, f"{key} produced no scorable trial"
    names = [n for n in trials[0] if n != "_meta"]
    return {n: {m: sum(t[n][m] for t in trials) / len(trials)
                for m in ("ap", "reach_frac")} for n in names}


def test_reach_is_not_a_performance_metric():
    """THE regression test for the error this module was built on.

    An earlier version headlined `reach` -- positives given any non-zero score -- and drew
    a six-map law from it. A uniform random scorer assigns every pair a non-zero score, so
    it reaches 100% of positives while ranking at chance. If this ever passes with Random
    below 1.0, someone has changed what reach means; if a conclusion is ever drawn from
    reach again, this test is the reason not to."""
    p = _panel("gordon")
    assert p["Random"]["reach_frac"] == 1.0
    assert p["Random"]["ap"] < 0.02, "random should rank at chance while reaching everything"
    assert p["PrefAttach"]["reach_frac"] > p["L3"]["reach_frac"], \
        "a degree product reaches more positives than L3 and ranks far worse"


def test_on_a_star_map_the_one_hop_lookup_beats_l3_on_retrieval():
    """The result that survived re-derivation. Gordon and Penn have no shared preys, so
    L3 has no bait at the middle hop and degenerates to a two-hop STRING walk."""
    for key in ("gordon", "penn2018_mtb"):
        p = _panel(key)
        assert p["STRING-GBA"]["ap"] > p["L3"]["ap"], f"{key}: L3 should lose on AP"


def test_the_bait_route_alone_carries_almost_no_ranking_signal():
    """co-bait isolates the bait-intermediate route that the retracted claim rested on.
    If that route carried the signal it would rival L3. It does not."""
    p = _panel("jager2011_hiv")
    assert p["co-bait"]["ap"] < p["L3"]["ap"] / 3


def test_l3_is_not_the_best_scorer_on_gordon():
    """Stated plainly so it cannot be quietly un-stated: on this repo's flagship map the
    shipped predictor is beaten by several simpler methods on average precision."""
    p = _panel("gordon")
    better = [n for n, v in p.items() if v["ap"] > p["L3"]["ap"]]
    assert "STRING-GBA" in better and "CN" in better


def test_held_out_preys_keep_their_string_edges():
    """The training graph removes the AP-MS edge only. Rebuilding from surviving edges
    would strip the held-out prey's STRING edges and silently zero every scorer."""
    edges, string_edges = bakeoff.load_map("gordon")
    trial = bakeoff.run_trial(edges, string_edges, 0.700, seed=0)
    assert trial["L3"]["reach_frac"] > 0, "no held-out edge reachable: STRING layer was lost"
