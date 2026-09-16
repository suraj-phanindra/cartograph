# Six-map baseline bake-off, and a retraction

Run 2026-09-15, extended 2026-09-16, **substantially retracted and re-derived 2026-09-16.**

## What was claimed, and why it was wrong

An earlier version of this document claimed:

> L3 beats a one-line STRING guilt-by-association lookup if and only if the AP-MS map has
> shared preys, the advantage is monotonic in how much sharing there is (r = 0.94 over
> fifteen map variants), and mean prey degree is a pre-flight statistic that predicts which
> scorer to run.

**That claim was an artifact of the endpoint.** It was measured on `reach`: the count of
held-out positives to which a scorer assigns any non-zero score. `reach` is support-set
size, not retrieval quality. Measured on Gordon:

| scorer | reach | average precision |
|---|---|---|
| Random | **100.0%** | 0.0071 |
| PrefAttach | 41.4% | 0.0059 |
| STRING-GBA | 26.5% | **0.1848** |
| L3 | 18.8% | 0.0718 |

A uniform random number generator reaches every positive, because it assigns every pair a
non-zero score. A degree product reaches more than twice what L3 reaches and ranks at
chance. Any quantity a random scorer maximises cannot be a performance metric, and the
"advantage rises with prey sharing" gradient largely restated that sharing gives L3 more
pairs to assign non-zero scores to. That is arithmetic, not a law.

The disconfirming evidence was already in this file and was not acted on: it said "L3 is a
recall channel, not a ranking channel," and reported precision@20 of -0.083 and
precision@50 of -0.140 on Jager, then headlined the coverage number anyway.

## The corrected result

Primary endpoint is average precision. Twenty seeds, 17% held out, every metric over an
explicit candidate universe with unreached pairs scored 0. Full panel, not a two-method
comparison. Reproduce with `python -m backend.bench.bakeoff`.

| map | shared preys | best by AP | AP | L3's AP | L3 placing |
|---|---|---|---|---|---|
| Penn 2018 Mtb | 0.0% | **STRING-GBA** | 0.2772 | 0.0787 | 5th of 8 |
| Gordon 2020 SARS-CoV-2 | 0.0% | **STRING-GBA** | 0.1848 | 0.0718 | 5th of 8 |
| Jager 2011 HIV-1 | 14.9% | **Adamic-Adar** | 0.1514 | 0.1264 | 5th of 8 |
| BioPlex 3.0 293T | 22.2% | **Adamic-Adar** | 0.0630 | 0.0498 | 4th of 8 |
| Haas 2023 influenza A | 23.8% | **Resource allocation** | 0.1462 | 0.1439 | 2nd, a tie |
| HuRI (synthetic split) | 33.4% | **L3** | 0.0237 | 0.0237 | 1st |

**L3 is best on one of six maps, and that one is the weakest evidence in the set.** HuRI's
preys are STRING-starved (mean prey STRING degree 1.073, 68% with no partner at all), so
every STRING-dependent scorer sits near the 0.50 AUC null there and L3 wins by default. On
Haas, L3's 0.1439 sits inside the seed spread of RA's 0.1462 and CN's 0.1436 (sd 0.028 to
0.037), so that is a tie, not a win.

The simple neighbourhood indices dominate. Adamic-Adar is best on two maps and top three on
four. A one-hop STRING lookup is best on both star maps by a factor of 2.6 to 3.5 on AP.

## What survives, and it is a negative result

**On AP-MS maps where no prey is shared between baits, degree-normalized L3 is beaten by
simpler methods on every metric tested** -- reach, recall@50, recall@200, average precision
and tie-aware AUC alike. Penn AP 0.079 against 0.277; Gordon 0.072 against 0.185.

The mechanism is a degeneracy, and it is worth stating plainly because it is not a
measurement but a graph-theoretic fact. L3 scores a `source -> a -> b -> v` path. On a
bipartite map with no shared prey, `b` can never be a bait, so both middle hops lie in the
STRING side-information layer and L3 IS a two-hop STRING walk, while guilt-by-association is
a one-hop STRING lookup. **Two hops of side information are noisier than one.** That is the
whole result on star maps.

## The mechanism story also failed

The retracted claim held that L3's advantage on shared-prey maps came from a
`bait -> shared prey -> other bait -> target prey` route invisible to length-2 methods. That
route is real and the path audit confirmed it carries most of L3's *extra reach* (94% on
HuRI, 85% on Jager, 72% on BioPlex, 0% on Gordon).

`backend/predict/cobait.py` isolates it: three lines, no STRING, no degree normalisation, no
length-3 machinery, scoring only how many other baits bind the candidate while sharing a
prey with this bait. If the route carried ranking signal, this counter would rival L3.

| map | co-bait AP | L3 AP |
|---|---|---|
| Gordon | 0.0075 | 0.0718 |
| Jager | 0.0248 | 0.1264 |
| Haas | 0.0286 | 0.1439 |
| HuRI | 0.0094 | 0.0237 |

It does not come close. **The bait route produces candidate coverage and almost no ranking
signal**, which is exactly why a coverage endpoint made it look decisive.

## The finding that is actually interesting

Support and ranking are close to orthogonal here. On all three pathogen maps, CN, RA,
Adamic-Adar and STRING-GBA have **identical reach to the digit** (Penn 28.7%, Gordon 26.5%,
Jager 38.6%) because on a bipartite graph whose only prey-prey edges are STRING, a common
neighbour of a bait and a candidate is precisely a prey of that bait STRING-linked to the
candidate. Same support set, every time.

Their average precision over that identical support ranges from 0.0969 to 0.2772 on Penn, a
2.9-fold spread. Everything separating these methods is in how they weight a support set
they share, and nothing at all is in which pairs they can see. A coverage metric is blind to
100% of the difference between them.

## Prior art, checked after the fact

Three of the four moves in the retracted claim had published precedent, two of them in this
repo's own bibliography:

- **Zhou, Lee & Wang 2021** (10.1016/j.physa.2020.125532) already published the claim shape:
  which of 2-hop or 3-hop wins is predictable in advance from structural statistics. It is
  row 84 of `ppi_prediction_bibliography.csv` and is cited at line 59 of
  `cartograph_soa_review.md`.
- **Cannistraci et al. 2013** (10.1038/srep01613) published a network statistic with an
  explicit threshold band selecting a predictor family, on protein interactomes, in 2013.
- **Kunegis et al. 2010** (arXiv:1006.5367) states the bipartite fact the mechanism rests
  on: even-length path methods do not apply to bipartite graphs.
- The `bait -> prey -> bait' -> prey` route is user-based collaborative filtering, and the
  zero-sharing regime is its cold-start case.

One inversion is worth recording. Prey degree across baits is the **specificity** term of
MiST, the scorer that built both Gordon 2020 and Jager 2011, and of CompPASS and the
CRAPome, where a high value flags a **contaminant**. The retracted claim made the same
quantity an enabling condition.

## Statistics, corrected

- **No p-values.** A sign test over re-splits of one fixed edge list returns 2^-(n-1)
  whenever one method sweeps, so it reports the seed budget, not the evidence: Gordon's
  effect is stable while that p walks from 2e-03 to 1.4e-40 as seeds go 10 to 160. Per-seed
  standard deviation is reported instead.
- **r = 0.939 is withdrawn.** Nine of the fifteen variants were nested prefixes in which
  prey sharing is a monotone function of the prefix length K, so the pooled correlation
  largely measured K correlating with itself.
- **The two-variable fit is withdrawn.** Leave-one-dataset-out cross-validation collapses it
  (CV-R^2 0.609 to 0.095).
- The effective sample was never fifteen. It is **six datasets**.

## Reproducibility debt, disclosed

Nine of the fifteen rows in the retracted table cannot be regenerated from this repo. The
gene-level collapses of Jager and Haas, and the BioPlex and HuRI sub-prefixes, were computed
from intermediate files that were never committed. Both "controlled manipulations" the
retracted claim rested on are among them. The six maps in `evidence/multimap/` do reproduce.

## Standing limits

- Six datasets, all bipartite or made bipartite. Two are subsampled because STRING's API
  rejects more than 2000 identifiers.
- HuRI's bait/prey split is synthetic and its STRING layer is starved. It is the weakest map
  in the set and it is the only one L3 wins.
- Only one enrichment source (STRING physical, >= 0.700) and one held-out fraction (17%).
- The negative result on star maps rests on two datasets, Penn and Gordon.
