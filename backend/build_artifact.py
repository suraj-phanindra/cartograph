"""Build the computed artifact the frontend loads.

Runs the whole deterministic engine once, computes the honest evaluator numbers
and the honest loop delta, assembles the four dossiers (deterministic graph +
verified structure + cited reasoning), and writes everything to
frontend/data/cartograph_computed.json. Nothing here is illustrative: every
number is computed, every citation resolves, every predicted structure is
labelled predicted.

The demo renders a real induced subgraph over the flagship neighbourhoods (for
legibility); the headline metrics are computed on the FULL held-out set.
"""

from __future__ import annotations

import json

import networkx as nx

from backend import config
from backend.graph.enrich import enriched_graph
from backend.predict.l3 import l3_scores, rank_of, pick_display_path
from backend.eval.evaluator import evaluate, per_heldout_recovery
from backend.eval.freeze_split import load_frozen
from backend.reason.hypothesis import read_edge, skeptic_review, DOSSIER
from backend.structure.resolve import build_structure_facts

# Real baits whose neighbourhoods form the three hero clusters. The induced
# subgraph over these is real data, curated only for on-screen legibility.
DEMO_BAITS = ["Orf6", "Nsp9", "Orf9b", "N"]
CLUSTER = {
    "Orf6": "nuclear-pore", "Nsp9": "nuclear-pore",
    "Orf9b": "mitochondria", "N": "stress-granule",
}
DEMO_EDGES = ["Orf6|RAE1", "Orf9b|TOMM70", "N|G3BP1", "Orf6|NUP98"]


def _literature_word(n):
    return "Strong" if n >= 2 else ("Moderate" if n == 1 else "Weak")


def _subgraph(g, frozen):
    """Induced subgraph over demo baits + their preys + enrichment among them.

    Built with a SORTED node order so the layout (and thus the whole artifact) is
    byte-identical across runs, independent of Python's set/hash iteration order.
    """
    node_ids = set(DEMO_BAITS)
    for b in DEMO_BAITS:
        node_ids |= {n for n in g.neighbors(b) if g.nodes[n]["type"] == "human"}
    node_ids = sorted(node_ids)  # deterministic order, hash-independent

    sub = nx.Graph()
    for n in node_ids:
        sub.add_node(n, **g.nodes[n])
    for u, v, d in g.edges(data=True):
        if u in sub and v in sub:
            sub.add_edge(u, v, **d)

    # seeded layout on the sorted node order -> deterministic, reproducible positions.
    # Higher k = more repulsion so the dense nuclear-pore cluster does not pile up.
    pos = nx.spring_layout(sub, seed=config.HELDOUT_SEED, k=2.4, iterations=400)
    order = sorted(pos)
    xs = [pos[n][0] for n in order]
    ys = [pos[n][1] for n in order]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    W, H, PADX, PADY = 1180, 720, 90, 80

    px = {n: (PADX + (pos[n][0] - minx) / (maxx - minx) * W,
              PADY + (pos[n][1] - miny) / (maxy - miny) * H) for n in order}
    px = _deoverlap(px, order, min_dist=78.0, iters=140, bounds=(PADX, PADY, PADX + W, PADY + H))

    held = {tuple(e) for e in frozen["held_out"]}
    out_nodes = []
    for n, d in sub.nodes(data=True):
        cluster = CLUSTER.get(n)
        if cluster is None:
            for b in DEMO_BAITS:
                if g.has_edge(b, n):
                    cluster = CLUSTER[b]
                    break
        out_nodes.append({
            "id": n, "type": d["type"], "uniprot": d.get("uniprot", ""),
            "degree": g.degree(n), "cluster": cluster or "other",
            "x": round(px[n][0], 1), "y": round(px[n][1], 1),
        })
    return sub, out_nodes, held


def _deoverlap(px, order, min_dist, iters, bounds):
    """Deterministic pairwise de-overlap: push apart any two nodes closer than
    min_dist. Keeps the hero cluster (dense nucleoporins) legible. Pure geometry,
    seeded input -> reproducible output."""
    import math
    x0, y0, x1, y1 = bounds
    p = {n: [px[n][0], px[n][1]] for n in order}
    for _ in range(iters):
        moved = False
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                a, b = order[i], order[j]
                dx = p[b][0] - p[a][0]
                dy = p[b][1] - p[a][1]
                dist = math.hypot(dx, dy) or 0.01
                if dist < min_dist:
                    push = (min_dist - dist) / 2.0
                    ux, uy = dx / dist, dy / dist
                    p[a][0] -= ux * push; p[a][1] -= uy * push
                    p[b][0] += ux * push; p[b][1] += uy * push
                    moved = True
        # clamp to bounds
        for n in order:
            p[n][0] = min(max(p[n][0], x0), x1)
            p[n][1] = min(max(p[n][1], y0), y1)
        if not moved:
            break
    return {n: (p[n][0], p[n][1]) for n in order}


def _build_dossier(edge_key, ranked_by_bait, structure_facts, frozen):
    bait, prey = edge_key.split("|")
    r = read_edge(edge_key)
    struct = structure_facts[edge_key]
    spec = DOSSIER[edge_key]

    # topology confidence = L3 score of this candidate (normalised to 0-1 by the
    # max candidate score for its bait), plus its rank
    ranked = ranked_by_bait.get(bait, [])
    entry = next((c for c in ranked if c["candidate"] == prey), None)
    maxscore = ranked[0]["l3_score"] if ranked else 1.0
    topo = round(entry["l3_score"] / maxscore, 2) if entry else None
    rank = rank_of(ranked, prey) if entry else None
    path = pick_display_path(entry, preferred=config.FLAGSHIP_PATH) if entry else None

    held = {tuple(e) for e in frozen["held_out"]}
    is_heldout = (bait, prey) in held
    lit_n = len(r["citations"])
    sk = skeptic_review(prey, has_structure=(struct["kind"] == "experimental"), literature_count=lit_n)

    status = "predicted" if is_heldout else "known"
    return {
        "edge": edge_key, "source": bait, "target": prey, "status": status,
        "mechanism": r["mechanism"], "citations": r["citations"],
        "structure": struct,
        "confidence": {
            "topology": topo, "topology_rank": rank,
            "structure": struct["confidence"],
            "literature": _literature_word(lit_n), "literature_count": lit_n,
        },
        "proposed_test": spec["test"],
        "druggability": spec["drug"],
        "skeptic": sk,
        "l3_path": path,
        "held_out": is_heldout,
        "provenance": {
            "proposed_by": "deterministic degree-normalized L3",
            "evidence_by": "Claude reasoning layer (Reader/Skeptic), grounded in verified edge packs",
            "structure_by": struct["source"],
            "evaluator": "locked held-out benchmark (frozen before prediction)",
        },
    }


def _build_worklist(ranked_all, held_set, structure_facts, top_n=40):
    """The ranked 'what to test next' triage list over the WHOLE map.

    Only honestly-known columns: L3 score/rank, whether the edge is a recovered
    held-out true edge, whether we hold a structure and a cited mechanism, and a
    druggability read. Conservation is intentionally omitted — we have no
    cross-coronavirus PPI data, so a conservation column would be fabricated.
    """
    rows = []
    for bait, ranked in ranked_all.items():
        for i, c in enumerate(ranked, 1):
            edge = f"{bait}|{c['candidate']}"
            has_dossier = edge in DOSSIER
            struct = structure_facts.get(edge)
            rows.append({
                "bait": bait, "prey": c["candidate"], "edge": edge,
                "l3_score": c["l3_score"], "rank": i,
                "recovered": (bait, c["candidate"]) in held_set,
                "structure": struct["kind"] if struct else "none",
                "structure_source": (struct.get("pdb") or struct.get("source")) if struct else None,
                "has_mechanism": has_dossier,
                "druggability": DOSSIER[edge]["drug"]["level"] if has_dossier else None,
                "opentargets": f"https://platform.opentargets.org/search?q={c['candidate']}",
                "has_dossier": has_dossier,
                "path": pick_display_path(c, preferred=config.FLAGSHIP_PATH),
            })
    rows.sort(key=lambda r: (-r["l3_score"], r["bait"], r["prey"]))
    return rows[:top_n]


def build():
    g = enriched_graph()
    frozen = load_frozen()

    # --- evaluator: baseline (topology only) --------------------------------
    base = evaluate()
    m = base["metrics"]
    # disclosed anti-gaming check: precision WITHOUT the pinned walkthrough edge
    m_np = evaluate(exclude_pinned=True)["metrics"]

    # --- honest loop: confirm the #1-ranked recovered-true edges, fold back --
    rec = per_heldout_recovery()
    top1_greens = [(r["bait"], r["prey"]) for r in rec if r["recovered"] and r["rank"] == 1]
    held = [tuple(e) for e in frozen["held_out"]]
    remaining = [h for h in held if h not in set(top1_greens)]
    loop_before = evaluate(target_override=remaining)["metrics"]
    loop_after = evaluate(fold_back=top1_greens, target_override=remaining)["metrics"]

    # --- demo subgraph ------------------------------------------------------
    sub, nodes, held_set = _subgraph(g, frozen)

    # rank L3 candidates for every bait once (blind training graph); reuse for the
    # demo subgraph and the whole-map worklist.
    train = _train_graph(g, frozen)
    all_baits = sorted(n for n, d in g.nodes(data=True) if d["type"] == "viral")
    ranked_all = {b: l3_scores(train, b) for b in all_baits}
    ranked_by_bait = {b: ranked_all[b] for b in DEMO_BAITS}

    # enrich held-out recovery rows with the L3 path behind each recovered edge
    # (for the eval-transparency view). Deterministic; derived from ranked_all.
    for r in rec:
        ent = next((c for c in ranked_all.get(r["bait"], []) if c["candidate"] == r["prey"]), None)
        r["path"] = pick_display_path(ent, preferred=config.FLAGSHIP_PATH) if ent else None

    # visible edges
    edges = []
    for u, v, d in sub.edges(data=True):
        # orient viral -> human where relevant
        s, t = (u, v)
        if sub.nodes[v]["type"] == "viral":
            s, t = v, u
        kind = d.get("kind", "enrichment")
        # a known viral->host edge that is actually held out is hidden until eval
        heldout_true = (s, t) in held_set and sub.nodes[s]["type"] == "viral"
        edges.append({
            "source": s, "target": t, "kind": kind,
            "score": round(d.get("score", 0.0), 3),
            "held_out": heldout_true,
        })
    edges.sort(key=lambda e: (e["source"], e["target"]))  # deterministic order

    # visible L3 predictions (missing edges the graph proposes among visible nodes).
    # A candidate is shown when it is a top-6 proposal OR it is a held-out-true edge
    # OR it has a dossier — so the flagship Orf6->RAE1 (L3 rank 7) is never dropped.
    visible = {n["id"] for n in nodes}
    predicted = []
    for bait in DEMO_BAITS:
        for i, c in enumerate(ranked_by_bait[bait], 1):
            if c["candidate"] not in visible:
                continue
            edge = (bait, c["candidate"])
            keep = i <= 6 or edge in held_set or f"{bait}|{c['candidate']}" in DOSSIER
            if not keep:
                continue
            predicted.append({
                "source": bait, "target": c["candidate"],
                "l3_score": c["l3_score"],
                "path": pick_display_path(c, preferred=config.FLAGSHIP_PATH),
                "rank": i,
                "held_out_true": edge in held_set,
                "has_dossier": f"{bait}|{c['candidate']}" in DOSSIER,
            })
    # de-dup and sort by score
    seen = set()
    uniq = []
    for p in sorted(predicted, key=lambda x: -x["l3_score"]):
        key = (p["source"], p["target"])
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    predicted = uniq

    # --- dossiers -----------------------------------------------------------
    structure_facts = build_structure_facts()
    dossiers = {e: _build_dossier(e, ranked_by_bait, structure_facts, frozen) for e in DEMO_EDGES}

    # --- worklist: ranked "what to test next" over the whole map ------------
    worklist = _build_worklist(ranked_all, held_set, structure_facts)

    # --- flagship detail ----------------------------------------------------
    flag_bait, flag_prey = config.FLAGSHIP_HELDOUT_EDGE
    flag_entry = next((c for c in ranked_by_bait[flag_bait] if c["candidate"] == flag_prey), None)
    flagship = {
        "edge": f"{flag_bait}|{flag_prey}",
        "path": config.FLAGSHIP_PATH,
        "l3_rank": rank_of(ranked_by_bait[flag_bait], flag_prey),
        "n_candidates": len(ranked_by_bait[flag_bait]),
        "l3_score": flag_entry["l3_score"] if flag_entry else None,
        "note": ("Recovered via a genuine length-3 path (Orf6->NUP98->NUP214->RAE1). "
                 "Topology ranks it inside Orf6's nuclear-pore candidate set; the structure "
                 "(PDB 7VPH) and literature identify it as the biologically correct edge."),
    }

    artifact = {
        "meta": {
            "title": "Cartograph — computed artifact",
            "ground_truth": "Gordon et al. 2020 (PMID 32353859), IntAct IM-27814",
            "n_edges": config.N_EDGES, "n_baits": config.N_BAITS,
            "string_version": config.STRING_VERSION,
            "string_params": f"physical channel, score>={config.STRING_REQUIRED_SCORE}",
            "n_enrichment_edges": g.graph.get("n_enrichment"),
            "reproducible": True,
        },
        "integrity": {
            "deterministic_path": "The graph proposes edges via degree-normalized L3. "
                                  "Claude reads, adjudicates, explains. Claude never invents an edge.",
            "no_citation_no_render": "Every mechanistic clause opens to a real PubMed paper.",
            "predicted_labeled": "Predicted structures are always labelled predicted with a "
                                 "confidence number (pLDDT/ipTM). Never shown as experimental fact.",
            "locked_evaluator": "The held-out split was frozen and committed BEFORE any prediction "
                                "code, in a module the reasoning layer cannot import.",
            "headline_is_honest": "Precision is computed on real held-out Gordon edges, not the "
                                  "prototype's illustrative 80%.",
        },
        "eval": {
            "seed": frozen["seed"], "fraction": frozen["fraction"],
            "n_held_out": frozen["n_held_out"],
            "n_random_sampled": frozen["n_random_sampled"],
            "pinned_walkthrough": frozen["pinned_walkthrough"],
            "protocol": frozen["protocol"],
            "baseline": {
                "precision_at_k": {str(k): m["k"][k]["precision"] for k in config.EVAL_K_VALUES},
                "recall_at_k": {str(k): m["k"][k]["recall"] for k in config.EVAL_K_VALUES},
                "roc_auc": m["roc_auc"], "average_precision": m["average_precision"],
                "headline_precision_at_k": m["headline_precision_at_k"],
                "headline_k": m["headline_k"],
                "n_targets": m["n_targets"], "n_recoverable": m["n_targets_recoverable"],
                # disclosed: pinning the walkthrough edge does not inflate the headline
                "without_pinned": {
                    "precision_at_k": {str(k): m_np["k"][k]["precision"] for k in config.EVAL_K_VALUES},
                    "roc_auc": m_np["roc_auc"], "n_targets": m_np["n_targets"],
                },
            },
            "loop": {
                "confirmed_edges": [list(e) for e in top1_greens],
                "confirmed_in_view": [list(e) for e in top1_greens
                                      if e[0] in DEMO_BAITS and e[1] in {n["id"] for n in nodes}],
                "measured_on": "the remaining held-out edges (fair before/after, same target set)",
                "before_precision_at_20": loop_before["k"][20]["precision"],
                "after_precision_at_20": loop_after["k"][20]["precision"],
                "before_recoverable": loop_before["n_targets_recoverable"],
                "after_recoverable": loop_after["n_targets_recoverable"],
                "story": ("Confirm the high-confidence recovered-true edges (each L3-rank #1, each a "
                          "real Gordon edge), fold them back as known, and re-score the still-hidden "
                          "edges on the same target set. Folding them back re-ranks the still-hidden "
                          "edges — one climbs into the top 20 — lifting precision@20 from "
                          f"{loop_before['k'][20]['precision']} to {loop_after['k'][20]['precision']}. "
                          "Reachability is unchanged this round; the gain is honest re-ranking, not "
                          "newly-unlocked edges."),
            },
        },
        "graph": {"nodes": nodes, "edges": edges, "predicted": predicted,
                  "clusters": sorted(set(CLUSTER.values()))},
        "flagship": flagship,
        "dossiers": dossiers,
        "worklist": worklist,
        "held_out_in_view": sorted([[s, t] for (s, t) in held_set
                                    if s in DEMO_BAITS and t in visible]),
        "per_heldout_recovery": rec,
    }

    # guard: the narrated flagship path must not drift from the computed path
    arrow = "→".join(config.FLAGSHIP_PATH)
    assert flagship["path"] == config.FLAGSHIP_PATH, "flagship path drifted from config"
    orf6_mech = " ".join(cl["text"] for cl in dossiers["Orf6|RAE1"]["mechanism"])
    assert arrow in orf6_mech, f"narrated path drifted; expected '{arrow}' in the Orf6-RAE1 mechanism"

    out = config.FRONTEND_DATA_DIR / "cartograph_computed.json"
    out.write_text(json.dumps(artifact, indent=2))
    return artifact, out


def _train_graph(g, frozen):
    train = g.copy()
    for bait, prey in frozen["held_out"]:
        if train.has_edge(bait, prey):
            train.remove_edge(bait, prey)
    return train


if __name__ == "__main__":
    art, out = build()
    e = art["eval"]
    print(f"wrote {out}")
    print(f"nodes={len(art['graph']['nodes'])} edges={len(art['graph']['edges'])} "
          f"predicted={len(art['graph']['predicted'])} dossiers={len(art['dossiers'])}")
    b = e["baseline"]
    print(f"BASELINE precision@{b['headline_k']}={b['headline_precision_at_k']} "
          f"ROC-AUC={b['roc_auc']} (on {b['n_targets']} held-out, {b['n_recoverable']} recoverable)")
    lp = e["loop"]
    print(f"LOOP confirm {len(lp['confirmed_edges'])} edges -> P@20 "
          f"{lp['before_precision_at_20']} -> {lp['after_precision_at_20']}, "
          f"recoverable {lp['before_recoverable']} -> {lp['after_recoverable']}")
    print(f"FLAGSHIP {art['flagship']['edge']} rank {art['flagship']['l3_rank']}/"
          f"{art['flagship']['n_candidates']} via {art['flagship']['path']}")
