"""Prey sharing decides which scorer is worth running on a map.

Measured across four interactomes on 2026-09-15 (docs/Cartograph_multimap_bakeoff.md):
L3 beats a one-line STRING lookup if and only if the AP-MS layer has shared preys,
and the advantage is monotonic in how much sharing there is. Mean prey degree is the
pre-flight statistic that decides it, so it is pinned here.
"""
import networkx as nx
import pytest

from backend.bench import sharing
from backend.eval.evaluator import build_training_graph
from backend.graph.enrich import enriched_graph
from backend.eval.freeze_split import load_frozen


def _star_map(n_baits=3, preys_per_bait=4):
    """Gordon-shaped: every prey belongs to exactly one bait."""
    g = nx.Graph()
    for b in range(n_baits):
        g.add_node(f"B{b}", type="viral")
        for p in range(preys_per_bait):
            name = f"B{b}_P{p}"
            g.add_node(name, type="human")
            g.add_edge(f"B{b}", name, kind="known")
    return g


def _shared_map():
    """Every prey is bound by both baits: mean prey degree 2.0."""
    g = nx.Graph()
    for b in ("B0", "B1"):
        g.add_node(b, type="viral")
    for p in range(4):
        name = f"P{p}"
        g.add_node(name, type="human")
        g.add_edge("B0", name, kind="known")
        g.add_edge("B1", name, kind="known")
    return g


def test_star_map_has_mean_prey_degree_of_one():
    assert sharing.mean_prey_degree(_star_map()) == 1.0


def test_fully_shared_map_has_mean_prey_degree_of_two():
    assert sharing.mean_prey_degree(_shared_map()) == 2.0


def test_string_enrichment_edges_do_not_inflate_prey_degree():
    """The statistic counts bait-prey edges only. Enrichment edges join two preys,
    so counting raw node degree would report sharing where there is none."""
    g = _star_map()
    g.add_edge("B0_P0", "B1_P1", kind="enrichment", score=0.9)
    g.add_edge("B0_P1", "B2_P2", kind="enrichment", score=0.8)
    assert sharing.mean_prey_degree(g) == 1.0


def test_folded_back_edges_count_as_bait_prey_links():
    """A confirmed edge folded back onto the map is a real bait-prey edge."""
    g = _star_map()
    g.add_edge("B1", "B0_P0", kind="confirmed")
    assert sharing.mean_prey_degree(g) > 1.0


def test_gordon_is_a_pure_star_map():
    """The real thing: 332 preys, 332 bait-prey edges, none shared."""
    assert sharing.mean_prey_degree(enriched_graph()) == 1.0


def test_a_training_graph_deflates_the_statistic():
    """The statistic describes the COMPLETE map. Handing it a training graph counts
    the held-out preys at degree 0 and understates sharing, which on a borderline map
    would flip the recommendation. Gordon: 275 surviving edges over 332 preys."""
    train = sharing.mean_prey_degree(build_training_graph(load_frozen()))
    assert train == pytest.approx(275 / 332)
    assert train < sharing.mean_prey_degree(enriched_graph())


def test_star_map_recommends_the_string_lookup():
    rec = sharing.recommended_channel(_star_map())
    assert rec["channel"] == "STRING-GBA"


def test_shared_map_recommends_l3():
    rec = sharing.recommended_channel(_shared_map())
    assert rec["channel"] == "L3"


def test_recommendation_carries_the_evidence_not_just_a_verdict():
    """A bare channel name is unauditable. The record states the measured value, the
    crossover it was compared against, and where that crossover came from."""
    rec = sharing.recommended_channel(_star_map())
    assert rec["mean_prey_degree"] == 1.0
    assert rec["crossover"] == pytest.approx(1.05)
    assert "bakeoff" in rec["basis"].lower() or "shared" in rec["basis"].lower()


def test_map_with_no_preys_raises_rather_than_guessing():
    g = nx.Graph()
    g.add_node("B0", type="viral")
    with pytest.raises(ValueError):
        sharing.mean_prey_degree(g)
