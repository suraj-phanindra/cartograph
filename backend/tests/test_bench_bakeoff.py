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


def _reach(key, seeds=SEEDS):
    edges, string_edges = bakeoff.load_map(key)
    trials = [t for t in (bakeoff.run_trial(edges, string_edges, 0.700, s)
                          for s in range(seeds)) if t]
    assert trials, f"{key} produced no scorable trial"
    l3 = sum(t["L3"]["reach_frac"] for t in trials) / len(trials)
    gba = sum(t["STRING-GBA"]["reach_frac"] for t in trials) / len(trials)
    return l3, gba


def test_on_a_star_map_the_one_line_lookup_reaches_more_than_l3():
    """Gordon has zero shared preys, so the bait-intermediate route does not exist."""
    l3, gba = _reach("gordon")
    assert gba > l3


def test_on_a_shared_prey_map_l3_reaches_more_than_the_lookup():
    """Jager has 14.9% shared preys, which opens bait -> prey -> bait' -> prey."""
    l3, gba = _reach("jager2011_hiv")
    assert l3 > gba


@pytest.mark.parametrize("key,expected", [
    ("gordon", "STRING-GBA"),
    ("penn2018_mtb", "STRING-GBA"),
    ("jager2011_hiv", "L3"),
    ("haas2023_iav", "L3"),
    ("bioplex3_293t_k200", "L3"),   # out of regime: human-human, no pathogen
    ("huri2020_k200_synthbaits", "L3"),   # symmetric network, synthetic bait/prey split
])
def test_preflight_statistic_agrees_with_the_measured_winner(key, expected):
    """The whole point of mean prey degree is that it is computable before scoring.
    If it stops predicting the measured winner, the deployment rule is broken."""
    edges, string_edges = bakeoff.load_map(key)
    g = bakeoff.build_map_graph(edges, string_edges, 0.700)
    assert sharing.recommended_channel(g)["channel"] == expected


def test_held_out_preys_keep_their_string_edges():
    """The training graph removes the AP-MS edge only. Rebuilding from surviving edges
    would strip the held-out prey's STRING edges and silently zero every scorer."""
    edges, string_edges = bakeoff.load_map("gordon")
    trial = bakeoff.run_trial(edges, string_edges, 0.700, seed=0)
    assert trial["L3"]["reach"] > 0, "no held-out edge reachable: STRING layer was lost"
