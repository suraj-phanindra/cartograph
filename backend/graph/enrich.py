"""STRING human-human enrichment among the Gordon prey.

Fetched ONCE from STRING v12.0 (pinned), physical subnetwork, high-confidence
(score >= 700), then cached to evidence/string_enrichment.cached.json and
committed. The demo reads the cache; it never calls the network. This keeps the
enrichment reproducible and the demo path offline.

Why the physical channel and not text-mining: we want proteins that are part of
the same physical complex (real binding), which is what supports an L3 edge
hypothesis. Text-mining co-mention is not evidence of a physical interaction.
"""

from __future__ import annotations

import json
from datetime import date

import requests

from backend import config
from backend.graph.load import load_graph


def _fetch_string_network(genes):
    """Query STRING for physical interactions among `genes`. Chunked to stay
    within request limits; returns raw edge dicts with STRING preferredNames."""
    url = f"{config.STRING_API}/tsv/network"
    edges = []
    genes = sorted(set(genes))
    # STRING maps the whole identifier list against the network of the set;
    # send all at once (network endpoint handles the full prey set).
    resp = requests.post(
        url,
        data={
            "identifiers": "%0d".join(genes),
            "species": config.STRING_SPECIES,
            "network_type": config.STRING_NETWORK_TYPE,
            "required_score": config.STRING_REQUIRED_SCORE,
            "caller_identity": "cartograph_build",
        },
        timeout=90,
    )
    resp.raise_for_status()
    lines = resp.text.strip().splitlines()
    header = lines[0].split("\t")
    idx = {name: i for i, name in enumerate(header)}
    for line in lines[1:]:
        f = line.split("\t")
        edges.append(
            {
                "a": f[idx["preferredName_A"]],
                "b": f[idx["preferredName_B"]],
                "score": float(f[idx["score"]]),
            }
        )
    return edges


def build_cache(force=False):
    """Fetch STRING enrichment among the prey and write the committed cache."""
    if config.STRING_CACHE.exists() and not force:
        return json.loads(config.STRING_CACHE.read_text()), "exists"

    g = load_graph()
    preys = [n for n, d in g.nodes(data=True) if d["type"] == "human"]
    prey_set = {p.upper() for p in preys}

    raw = _fetch_string_network(preys)
    # keep only edges where BOTH endpoints are Gordon prey (no added nodes)
    kept = []
    seen = set()
    for e in raw:
        a, b = e["a"], e["b"]
        if a.upper() in prey_set and b.upper() in prey_set and a.upper() != b.upper():
            key = tuple(sorted((a.upper(), b.upper())))
            if key in seen:
                continue
            seen.add(key)
            kept.append({"a": a, "b": b, "score": e["score"]})

    cache = {
        "source": "STRING",
        "version": config.STRING_VERSION,
        "network_type": config.STRING_NETWORK_TYPE,
        "required_score": config.STRING_REQUIRED_SCORE,
        "species": config.STRING_SPECIES,
        "retrieved": str(date.today()),
        "n_edges": len(kept),
        "edges": sorted(kept, key=lambda x: (x["a"], x["b"])),
    }
    config.STRING_CACHE.write_text(json.dumps(cache, indent=2))
    return cache, "written"


def load_enrichment():
    """Return cached STRING edges as a list of (geneA, geneB, score)."""
    if not config.STRING_CACHE.exists():
        raise FileNotFoundError(
            "STRING cache missing. Run: python -m backend.graph.enrich  (needs network, once)"
        )
    cache = json.loads(config.STRING_CACHE.read_text())
    return [(e["a"], e["b"], e["score"]) for e in cache["edges"]]


def enriched_graph():
    """The Gordon graph plus cached STRING human-human enrichment edges.

    Enrichment edges only connect nodes that already exist as prey (we do not add
    new human nodes), so the graph stays interpretable as 'the interactome plus
    known human-human links among its prey'.
    """
    g = load_graph()
    present = set(g.nodes)
    # case-insensitive lookup from STRING preferredName -> our node id
    upper_to_id = {n.upper(): n for n in present}
    added = 0
    for a, b, score in load_enrichment():
        na, nb = upper_to_id.get(a.upper()), upper_to_id.get(b.upper())
        if na and nb and not g.has_edge(na, nb):
            g.add_edge(na, nb, kind="enrichment", score=score / 1000.0, evidence_ref="string_v12")
            added += 1
    g.graph["n_enrichment"] = added
    return g


if __name__ == "__main__":
    cache, status = build_cache()
    print(f"STRING cache: {status} — {cache['n_edges']} human-human edges "
          f"(v{cache['version']}, {cache['network_type']}, score>={cache['required_score']})")
    g = enriched_graph()
    print(f"enriched graph: {g.number_of_edges()} edges "
          f"({g.graph['n_enrichment']} enrichment added)")
    # flagship path sanity: are the bridge edges present?
    for a, b in [("NUP98", "NUP214"), ("NUP214", "RAE1"), ("NUP98", "RAE1")]:
        print(f"  bridge {a}-{b}: {'YES' if g.has_edge(a, b) else 'NO'}")
