"""Prey sharing: the pre-flight statistic that decides which scorer to run.

Measured 2026-09-15 across four pathogen-host interactomes -- Gordon 2020 SARS-CoV-2,
Penn 2018 Mtb, Jager 2011 HIV-1 and Haas 2023 influenza A, six map variants in all
(docs/Cartograph_multimap_bakeoff.md). Degree-normalized L3 beats a one-line STRING
guilt-by-association lookup if and only if the AP-MS layer has SHARED PREYS, and the
advantage is monotonic in how much sharing there is (Pearson r = 0.91).

    mean prey degree   shared preys   L3 reach advantage over GBA
    1.000 (Penn)              0.0%    -9.7 pp   (0/39 seeds)
    1.000 (Gordon)            0.0%    -7.4 pp   (1/39 seeds)
    1.054 (Jager, gene)       5.4%    +0.9 pp   (not significant)
    1.076 (Haas, gene)        7.6%    +8.1 pp   (34/2 seeds)
    1.151 (Jager, construct) 14.9%    +9.7 pp   (40/0 seeds)
    1.262 (Haas, construct)  23.8%   +13.4 pp   (39/1 seeds)

The mechanism is direct, not correlational: prey sharing opens a
bait -> shared prey -> other bait -> target prey route, which is length 3 and therefore
invisible to any length-2 method. Of the held-out edges L3 reaches that GBA cannot on
Jager, 85% travel exactly that route. On Gordon the same count is zero.

So the statistic is causal, one line to compute, and available BEFORE any scoring run.
"""

from __future__ import annotations

# Crossover sits between the 5.4% and 7.6% sharing variants, where the advantage turns
# from "not significant" to "+8.1 pp at 34/2 seeds". Stated as mean prey degree.
CROSSOVER = 1.05


def mean_prey_degree(graph) -> float:
    """Average number of viral baits each human prey is bound by.

    Counts viral neighbours only, which is what makes this the AP-MS layer's property.
    Raw node degree would include the STRING enrichment edges between two preys and
    report sharing on a map that has none.
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


def recommended_channel(graph, crossover: float = CROSSOVER) -> dict:
    """Which scorer is worth running on this map, with the evidence for the verdict.

    Returns a record rather than a bare channel name: a recommendation whose basis is
    not inspectable is not auditable, which is the rule the rest of this repo runs on.
    """
    measured = mean_prey_degree(graph)
    use_l3 = measured >= crossover
    return {
        "channel": "L3" if use_l3 else "STRING-GBA",
        "l3_applicable": use_l3,
        "mean_prey_degree": round(measured, 4),
        "crossover": crossover,
        "basis": (
            "Four-map bakeoff, 2026-09-15: L3 beats STRING guilt-by-association only "
            "where preys are shared between baits, monotonically in the amount of "
            "sharing (r = 0.91, 6 variants). See docs/Cartograph_multimap_bakeoff.md."
        ),
    }
