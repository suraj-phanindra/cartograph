"""Load the Gordon 2020 interactome into a networkx graph.

Deterministic. Same CSV in, same graph out. This is the graph layer's front
door; the evaluator, the predictor, and the artifact exporter all build on the
graph produced here. Canonical counts are asserted at load so a corrupted or
swapped CSV fails loudly instead of silently changing the headline number.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field

import networkx as nx

from backend import config


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    kind: str  # known | enrichment | predicted | confirmed
    score: float
    evidence_ref: str = ""


def _read_edges_csv(path=config.EDGES_CSV):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(
                {
                    "bait": r["bait"].strip(),
                    "bait_uniprot": r["bait_uniprot"].strip(),
                    "prey_gene": r["prey_gene"].strip(),
                    "prey_uniprot": r["prey_uniprot"].strip(),
                    "miscore": float(r["miscore"]),
                }
            )
    return rows


def load_graph(path=config.EDGES_CSV, assert_counts=True) -> nx.Graph:
    """Build the viral-bait / human-prey graph from the ground-truth CSV.

    Nodes carry: type (viral|human), uniprot, and (later) annotations.
    Known edges carry kind='known' and the IntAct MI-score.
    """
    rows = _read_edges_csv(path)
    g = nx.Graph()

    baits, preys = set(), set()
    for r in rows:
        bait, prey = r["bait"], r["prey_gene"]
        baits.add(bait)
        preys.add(prey)
        if bait not in g:
            g.add_node(bait, type="viral", uniprot=r["bait_uniprot"], annotations=[])
        if prey not in g:
            g.add_node(prey, type="human", uniprot=r["prey_uniprot"], annotations=[])
        g.add_edge(bait, prey, kind="known", score=r["miscore"], evidence_ref="gordon2020")

    if assert_counts:
        n_known = sum(1 for _, _, d in g.edges(data=True) if d["kind"] == "known")
        assert n_known == config.N_EDGES, f"expected {config.N_EDGES} known edges, got {n_known}"
        assert len(baits) == config.N_BAITS, f"expected {config.N_BAITS} baits, got {len(baits)}"
        assert len(preys) == config.N_PREYS, f"expected {config.N_PREYS} preys, got {len(preys)}"
        # Gordon preys are unique per bait: no human prey shared across baits.
        assert not (baits & preys), "bait/prey name collision"

    g.graph["baits"] = sorted(baits)
    g.graph["preys"] = sorted(preys)
    return g


def known_edges(g: nx.Graph):
    """Return the set of known viral->host edges as (bait, prey) tuples."""
    out = set()
    for u, v, d in g.edges(data=True):
        if d.get("kind") != "known":
            continue
        # orient viral -> human
        if g.nodes[u]["type"] == "viral":
            out.add((u, v))
        else:
            out.add((v, u))
    return out


if __name__ == "__main__":
    G = load_graph()
    print(f"loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"baits ({len(G.graph['baits'])}): {', '.join(G.graph['baits'])}")
    ke = known_edges(G)
    print(f"known viral->host edges: {len(ke)}")
    assert ("Orf6", "RAE1") in ke and ("Orf6", "NUP98") in ke
    assert ("Orf9b", "TOMM70") in ke and ("N", "G3BP1") in ke
    print("flagship anchor edges present: Orf6-RAE1, Orf6-NUP98, Orf9b-TOMM70, N-G3BP1")
