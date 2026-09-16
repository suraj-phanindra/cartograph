"""The candidate universe: the set of pairs a metric is computed over.

Defined in exactly one place so that no call site can quietly use a different
denominator. Every untested viral-bait to human-prey pair is a candidate, including
the held-out edges, which are untested from the predictor's point of view.

Closed world is the pairs reachable inside the loaded map. Open world is the same
baits against a background proteome, which is the population the tool addresses at
deployment and the honest denominator for a prevalence claim.
"""
from __future__ import annotations


def candidate_universe(graph) -> set[tuple[str, str]]:
    """Every (viral bait, human prey) pair with no edge in `graph`.

    Pass the TRAINING graph, not the full one. Held-out edges are absent from the
    training graph and are therefore candidates, which is what makes them scorable.
    """
    baits = sorted(n for n, d in graph.nodes(data=True) if d["type"] == "viral")
    humans = sorted(n for n, d in graph.nodes(data=True) if d["type"] == "human")
    return {(b, h) for b in baits for h in humans if not graph.has_edge(b, h)}


def prevalence(n_positives: int, n_universe: int) -> float:
    """Base rate of positives in the universe. The denominator of every enrichment."""
    if n_universe <= 0:
        raise ValueError("universe must be non-empty")
    return n_positives / n_universe


def enrichment(value: float, prevalence_: float) -> float | None:
    """How many times better than the base rate. None when prevalence is zero."""
    if not prevalence_:
        return None
    return value / prevalence_


def open_world_size(n_baits: int, n_background: int) -> int:
    """Pair count against a background proteome, for the open-world prevalence."""
    if n_baits < 0 or n_background < 0:
        raise ValueError("counts must be non-negative")
    return n_baits * n_background
