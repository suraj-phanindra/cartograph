"""STRING best-score guilt-by-association.

The control that gates the project's central claim. Measured 2026-09-15: on both
zero-sharing maps (Gordon, Penn) this one-line lookup beats degree-normalized L3 on
every metric, so it ships as a real channel rather than a scratch-script baseline.
"""
import networkx as nx
import pytest

from backend.predict import gba


def _map():
    """One bait with two known preys, plus three unbound humans reachable by STRING.

        B0 -- KNOWN_A        KNOWN_A ~0.9~ CAND_HI
        B0 -- KNOWN_B        KNOWN_B ~0.4~ CAND_LO
                             CAND_HI ~0.8~ CAND_ORPHAN   (no link to any prey of B0)
    """
    g = nx.Graph()
    g.add_node("B0", type="viral")
    for n in ("KNOWN_A", "KNOWN_B", "CAND_HI", "CAND_LO", "CAND_ORPHAN"):
        g.add_node(n, type="human")
    g.add_edge("B0", "KNOWN_A", kind="known")
    g.add_edge("B0", "KNOWN_B", kind="known")
    g.add_edge("KNOWN_A", "CAND_HI", kind="enrichment", score=0.9)
    g.add_edge("KNOWN_B", "CAND_LO", kind="enrichment", score=0.4)
    g.add_edge("CAND_HI", "CAND_ORPHAN", kind="enrichment", score=0.8)
    return g


def test_scores_a_candidate_by_its_best_string_link_to_a_known_prey():
    out = {c["candidate"]: c["gba_score"] for c in gba.gba_scores(_map(), "B0")}
    assert out["CAND_HI"] == pytest.approx(0.9)
    assert out["CAND_LO"] == pytest.approx(0.4)


def test_candidate_with_no_link_to_any_prey_of_the_bait_is_not_scored():
    """CAND_ORPHAN is STRING-adjacent to CAND_HI, but CAND_HI is not a prey of B0.
    Guilt by association is one hop from a KNOWN prey, never two."""
    names = {c["candidate"] for c in gba.gba_scores(_map(), "B0")}
    assert "CAND_ORPHAN" not in names


def test_known_preys_are_never_proposed_as_candidates():
    names = {c["candidate"] for c in gba.gba_scores(_map(), "B0")}
    assert "KNOWN_A" not in names and "KNOWN_B" not in names


def test_takes_the_best_link_when_a_candidate_touches_several_preys():
    g = _map()
    g.add_edge("KNOWN_B", "CAND_HI", kind="enrichment", score=0.99)
    out = {c["candidate"]: c["gba_score"] for c in gba.gba_scores(g, "B0")}
    assert out["CAND_HI"] == pytest.approx(0.99)


def test_names_the_prey_that_supplied_the_best_link():
    """Provenance: a score with no stated support is not renderable under the
    repo's evidence rules."""
    g = _map()
    g.add_edge("KNOWN_B", "CAND_HI", kind="enrichment", score=0.99)
    hi = next(c for c in gba.gba_scores(g, "B0") if c["candidate"] == "CAND_HI")
    assert hi["via"] == "KNOWN_B"


def test_viral_nodes_are_never_candidates():
    g = _map()
    g.add_node("B1", type="viral")
    g.add_edge("KNOWN_A", "B1", kind="known")
    names = {c["candidate"] for c in gba.gba_scores(g, "B0")}
    assert "B1" not in names


def test_ordering_is_deterministic_score_desc_then_name():
    g = _map()
    g.add_edge("KNOWN_A", "CAND_LO", kind="enrichment", score=0.9)
    ranked = [c["candidate"] for c in gba.gba_scores(g, "B0")]
    assert ranked == ["CAND_HI", "CAND_LO"]


def test_bait_with_no_known_preys_returns_nothing():
    g = _map()
    g.add_node("B_EMPTY", type="viral")
    assert gba.gba_scores(g, "B_EMPTY") == []
