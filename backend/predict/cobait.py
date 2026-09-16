"""The co-bait counter: the trivial method that isolates the bait-intermediate route.

Score(bait, candidate) = how many OTHER baits bind the candidate while also sharing at
least one prey with this bait. That is common neighbours on the bait-projected graph. It
sees exactly the `bait -> shared prey -> other bait -> target prey` route and nothing
else: no STRING, no degree normalisation, no length-3 machinery.

It exists to answer one question. An earlier version of this repo claimed L3's advantage
on shared-prey maps came from that route. If the route carried the signal, this three-line
counter would match L3. Measured 2026-09-16, it does not come close: average precision
0.003 to 0.029 against L3's 0.024 to 0.144 across six maps. The route produces candidate
COVERAGE and almost no ranking signal, which is why the earlier claim was an artifact of
measuring coverage rather than retrieval.

Keep it in the panel. A baseline that fails is still the thing that showed the claim was
wrong, and removing it would make the correction unauditable.
"""

from __future__ import annotations


def cobait_scores(train, universe):
    """{(bait, candidate): n_shared_baits} for pairs the route reaches."""
    preys = {b: {n for n in train.neighbors(b) if train.nodes[n].get("type") == "human"}
             for b, d in train.nodes(data=True) if d.get("type") == "viral"}
    baits_of: dict[str, set] = {}
    for b, pp in preys.items():
        for q in pp:
            baits_of.setdefault(q, set()).add(b)
    # bait-bait projection, computed once: which baits share at least one prey
    shares = {b: set() for b in preys}
    for bs in baits_of.values():
        for b in bs:
            shares[b] |= bs
    for b in shares:
        shares[b].discard(b)

    out = {}
    for (b, p) in universe:
        n = len(baits_of.get(p, set()) & shares.get(b, set()))
        if n:
            out[(b, p)] = float(n)
    return out
