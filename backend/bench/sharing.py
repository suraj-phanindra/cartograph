"""Prey sharing: the pre-flight statistic that decides which scorer to run.

Measured across five AP-MS interactomes, ten map variants, in two regimes
(docs/Cartograph_multimap_bakeoff.md): pathogen-host (Gordon 2020 SARS-CoV-2, Penn 2018
Mtb, Jager 2011 HIV-1, Haas 2023 influenza A) and human-human (BioPlex 3.0 293T).
Degree-normalized L3 beats a one-line STRING guilt-by-association lookup if and only if
the AP-MS layer has SHARED PREYS, and the advantage rises with how much sharing there is
(Pearson r = 0.90 overall, monotonic within every single dataset).

    mean prey degree   shared preys   L3 reach advantage over GBA
    1.000 (Penn)              0.0%    -9.7 pp   (0/39 seeds)
    1.000 (Gordon)            0.0%    -7.4 pp   (1/39 seeds)
    1.054 (Jager, gene)       5.4%    +0.9 pp   (not significant)
    1.076 (Haas, gene)        7.6%    +8.1 pp   (34/2 seeds)
    1.151 (Jager, construct) 14.9%    +9.7 pp   (40/0 seeds)
    1.262 (Haas, construct)  23.8%   +13.4 pp   (39/1 seeds)

and out of regime, on human-human BioPlex 3.0 subsamples:

    1.048 (BioPlex K=25)      4.3%    +0.4 pp   (not significant)
    1.143 (BioPlex K=100)    12.1%    +4.5 pp   (20/0 seeds)
    1.283 (BioPlex K=200)    22.2%   +10.3 pp   (10/0 seeds)

and on HuRI, where the bait/prey split is SYNTHETIC (the assay is symmetric two-hybrid):

    1.107 (HuRI K=25)         8.1%    +2.1 pp   (14/4 seeds)
    1.620 (HuRI K=200)       33.4%   +40.6 pp   (10/0 seeds)

Strict monotonicity holds WITHIN each dataset but not across regimes: the pathogen-host
curve runs above the human-human one at matched sharing. So this statistic predicts the
sign and the trend, not the magnitude. Two caveats on the magnitudes:

  - HuRI's huge advantages are partly a starved baseline. Its preys have mean STRING degree
    1.073 and 68% have no STRING partner at all, so guilt-by-association sits near the 0.50
    AUC null at every K. HuRI establishes that the mechanism is TOPOLOGICAL (it does not
    need real bait/prey roles); it does not give a usable effect size.
  - A two-variable fit adding prey STRING degree reaches R^2 = 0.909 against 0.882 for
    sharing alone. The sign is right, the gain is not worth a parameter, and the 15 map
    variants are only 6 independent datasets. Treat every correlation as descriptive.

The mechanism is direct, not correlational: prey sharing opens a
bait -> shared prey -> other bait -> target prey route, which is length 3 and therefore
invisible to any length-2 method. Of the held-out edges L3 reaches that GBA cannot,
94% travel exactly that route on HuRI, 85% on Jager and 72% on BioPlex. On Gordon, where no
prey is shared, the count is zero.

So the statistic is causal, one line to compute, and available BEFORE any scoring run.
"""

from __future__ import annotations

# Crossover is a BAND, not a point: near 1.05 on pathogen-host maps (between the 5.4% and
# 7.6% variants) and nearer 1.10 on human-human ones (BioPlex is still not significant at
# 1.079). Held at the conservative end, since the cost of running L3 unnecessarily is one
# extra channel while the cost of skipping it is unreachable candidates.
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
