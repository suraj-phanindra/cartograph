"""Prey sharing: a descriptive property of an AP-MS map.

RETRACTION, 2026-09-16. This module previously exported `recommended_channel`, which
claimed that mean prey degree predicts whether degree-normalized L3 beats a one-hop STRING
guilt-by-association lookup, with a crossover near 1.05. That claim was measured on `reach`
-- the count of held-out positives a scorer assigns any non-zero score. `reach` is
support-set size, not retrieval quality: the bake-off panel's own `Random` scorer reaches
100% of positives on every map. Re-derived on average precision, the claim does not hold.

What the corrected measurement says (docs/Cartograph_multimap_bakeoff.md, 20 seeds,
average precision as primary endpoint, six maps):

    map                  best by AP     L3's placing
    Penn 2018 Mtb        STRING-GBA     5th of 8
    Gordon 2020          STRING-GBA     5th of 8
    Jager 2011 HIV-1     STRING-GBA     4th of 8
    BioPlex 3.0 293T     Adamic-Adar    close behind
    Haas 2023 IAV        L3 / CN        a tie
    HuRI (synthetic)     L3             STRING layer is starved

L3 is never clearly best. The co-bait counter in backend/predict/cobait.py, which isolates
the bait-intermediate route the old claim rested on, scores AP 0.003 to 0.029. So that route
produces candidate coverage and almost no ranking signal, and the mechanism story explained
an artifact.

`recommended_channel` is deliberately NOT replaced by a corrected rule. There is no rule in
this evidence worth shipping: run the panel and report all of it.

`mean_prey_degree` survives because it is a real and useful descriptor of a bipartite AP-MS
map -- it says whether the bait layer is a disjoint union of stars -- and because the
star-map result does hold: where no prey is shared, L3 is beaten by simpler methods on every
metric tested. Just do not use it to pick a scorer.
"""

from __future__ import annotations


def mean_prey_degree(graph) -> float:
    """Average number of baits each prey is bound by. 1.0 means a disjoint union of stars.

    Counts viral neighbours only, which is what makes this the AP-MS layer's property.
    Raw node degree would include the STRING enrichment edges between two preys and report
    sharing on a map that has none.

    Describes the COMPLETE map. Handing it a training graph counts held-out preys at
    degree 0 and understates sharing.
    """
    preys = [n for n, d in graph.nodes(data=True) if d.get("type") == "human"]
    if not preys:
        raise ValueError("map has no human preys, so prey sharing is undefined")
    bait_links = sum(
        1
        for p in preys
        for nb in graph.neighbors(p)
        if graph.nodes[nb].get("type") == "viral"
    )
    return bait_links / len(preys)


def is_star_map(graph) -> bool:
    """True when no prey is shared between baits, so the bait layer is disjoint stars.

    The one structural fact from the bake-off that survived re-derivation on average
    precision: on star maps L3 has no bait available at the middle hop, degenerates into a
    two-hop walk in the STRING side-information layer, and loses to the one-hop lookup on
    reach, recall@k, average precision and tie-aware AUC alike.
    """
    return mean_prey_degree(graph) == 1.0
