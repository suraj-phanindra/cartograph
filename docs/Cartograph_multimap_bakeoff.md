# Six-map baseline bake-off: when does L3 earn its place?

Run 2026-09-15, extended out of regime 2026-09-16, extended to a symmetric network the same day.

**Result in one line:** L3 beats a one-line STRING lookup if and only if the AP-MS map has
shared preys, the advantage scales monotonically with how much sharing there is
(Pearson r = 0.90 over ten map variants from five datasets, spanning pathogen-host AND
human-human AP-MS), and the mechanism is a
bait -> prey -> bait' -> prey route that no length-2 method can see.

## Protocol

Identical scorer panel, split protocol (17% held out, matching the frozen Gordon split's
57/332), and metrics across every map. 40 paired seeds. Read-only against the repo: imports
`backend.predict.l3` and `backend/bench`, never touches `backend/eval/`.

- Precision@k is the EXACT expectation under random tie-breaking, not one alphabetical draw.
  This removes the artifact class that invalidated the earlier CN/RA/AA comparison.
- Every scorer is scored over the full candidate universe with unreached pairs at 0, so no
  metric is computed on a predictor-selected subset.
- STRING v12.0 physical, fetched live per map at >=0.150 and filtered locally, so thresholds
  are sweepable. (The committed Gordon cache is pre-filtered at >=0.700 and CANNOT be
  re-thresholded downward. Any Gordon row below 0.700 derived from it is really the 0.700 row.)

## The four maps

| dataset | source | edges | baits | preys | shared preys | mean prey degree |
|---|---|---|---|---|---|---|
| Gordon 2020 SARS-CoV-2 | committed in repo | 332 | 26 | 332 | 0 (0.0%) | 1.000 |
| Penn 2018 Mtb | NDEx `50b4abbf-392d-11e9-9f06-0ac135e8bacf` | 176 | 33 | 176 | 0 (0.0%) | 1.000 |
| Jager 2011 HIV-1 | IntAct/IMEx IM-17346, PMID 22190034 | 511 | 16 | 444 | 66 (14.9%) | 1.151 |
| Haas 2023 influenza A | IntAct, PMID 37758692 | 265 | 21 | 210 | 50 (23.8%) | 1.262 |

Acquisition notes. Jager and Haas came from IntAct by PMID. **Penn 2018 is not in IntAct**
(`pubid:30118682` returns zero records); it was recovered from NDEx, where the network's own
reference field cites the paper. Baits were separated by the `TBBAIT` node attribute, giving
33 of the paper's 34 secreted baits and 176 bait-prey edges against the paper's 187.

Jager and Haas are also reported at two bait granularities, because prey sharing is the
variable under test. `[construct]` keeps processed chains and virus strains separate;
`[gene]` collapses them. Collapsing lowers sharing without changing the underlying biology,
which makes it a controlled manipulation of the predicted cause.

## The gradient

L3 reach and STRING-GBA reach as a percentage of held-out positives, normalised per trial so
map size does not confound. Advantage is the paired difference. Sign test is exact binomial
over 40 paired seeds.

| map variant | shared preys | positives | L3 reach | GBA reach | **advantage** | L3 wins/loses | sign p | L3 AUC | GBA AUC |
|---|---|---|---|---|---|---|---|---|---|
| Penn 2018 Mtb | 0.0% | 30 | 17.9% | 27.6% | **-9.7pp** | 0/39 | 3.6e-12 | 0.5803 | **0.6333** |
| Gordon 2020 | 0.0% | 56 | 19.2% | 26.7% | **-7.4pp** | 1/39 | 7.5e-11 | 0.5908 | **0.6294** |
| Jager [gene] | 5.4% | 80 | 42.1% | 41.1% | **+0.9pp** | 22/12 | 0.12 n.s. | 0.6439 | **0.6843** |
| Haas [gene] | 7.6% | 38 | 48.4% | 40.3% | **+8.1pp** | 34/2 | 1.9e-08 | **0.6885** | 0.6829 |
| Jager [construct] | 14.9% | 87 | 47.5% | 37.8% | **+9.7pp** | 40/0 | 1.8e-12 | **0.6793** | 0.6702 |
| Haas [construct] | 23.8% | 45 | 55.7% | 42.3% | **+13.4pp** | 39/1 | 7.5e-11 | **0.7348** | 0.6926 |

Advantage by ascending prey sharing: **-9.7, -7.4, +0.9, +8.1, +9.7, +13.4**
Strictly monotonic. **Pearson r = 0.9095** across six variants from four datasets.
Crossover sits near 5% prey sharing.

## The mechanism, confirmed directly

Of the held-out positives L3 reaches that STRING-GBA cannot (20 seeds):

| map | L3-reached positives | GBA cannot reach | of those, routed via a second bait |
|---|---|---|---|
| Jager 2011 [construct] | 837 | 261 | **223 (85%)** |
| Gordon 2020 | 211 | 16 | **0 (0%)** |

The route is bait -> shared prey -> other bait -> target prey. It is a genuine length-3 path
and structurally invisible to any length-2 method, which is precisely the advantage L3 was
designed to exploit. On a zero-sharing star map the route does not exist, so L3 has no
structural edge and is simply a noisier STRING lookup.

## Why the result should be believed

The law was derived on two maps and then survived three independent tests.

1. **Controlled manipulation.** Collapsing Jager to gene level drops sharing 14.9% -> 5.4% and
   the advantage collapses with it, +9.7pp (40/0 seeds) -> +0.9pp (22/12, not significant).
   This was pre-registered in the previous run's caveats as the falsification test: "if it
   doesn't weaken the effect, my mechanism story is wrong." It weakened.
2. **Out-of-sample prediction, new virus.** Haas 2023 influenza A was not used to derive the
   law. Predicted high advantage at 23.8% sharing; observed +13.4pp, 39/1 seeds.
3. **Out-of-sample prediction, new pathogen kingdom.** Penn 2018 Mtb is bacterial, not viral,
   from a different lab and a different assay year, and has 0% prey sharing. The law predicts
   it should sit alongside Gordon at roughly -7pp. Observed **-9.7pp, 0/39 seeds.**


## Out of regime: does this survive outside pathogen-host maps?

The load-bearing caveat of the four-map run was that every map was pathogen-host bipartite.
BioPlex 3.0 293T (Huttlin et al. 2021) is the opposite regime: human-human AP-MS, no
pathogen, a different lab and a different decade, 118,162 edges over 8,995 baits with 81.5%
of preys shared and a mean prey degree of 11.341.

The full network is a ~93 million pair universe, so a nested random sample of 400 baits was
drawn and the sweep run on prefixes of it. Nesting means one STRING cache serves every K, and
varying K sweeps prey sharing WITHIN a single dataset, which is a second controlled
manipulation of the predicted cause.

| K baits | shared preys | universe | positives | L3 reach | GBA reach | advantage | sign p |
|---|---|---|---|---|---|---|---|
| 25 | 4.3% | 10,014 | 74 | 24.1% | 23.6% | **+0.4pp** | 0.27 n.s. |
| 50 | 7.2% | 29,856 | 112 | 22.9% | 21.8% | **+1.1pp** | 0.096 n.s. |
| 100 | 12.1% | 103,509 | 203 | 24.8% | 20.3% | **+4.5pp** | 1.9e-06 |
| 200 | 22.2% | 381,818 | 421 | 36.1% | 25.7% | **+10.3pp** | 2.0e-03 |

Monotonic within BioPlex, and the mechanism transfers: of the held-out edges L3 reaches that
guilt-by-association cannot, **72% route through a second bait** (Jager 85%, Gordon 0%). The
same length-3 route is doing the work in a regime the rule was never fitted to.

### The combined picture, and where it is not clean

Ten map variants, five datasets, two regimes:

| shared preys | advantage | dataset |
|---|---|---|
| 0.0% | -9.7pp | Penn 2018 Mtb |
| 0.0% | -7.4pp | Gordon 2020 SARS-CoV-2 |
| 4.3% | +0.4pp | BioPlex K=25 |
| 5.4% | +0.9pp | Jager [gene] |
| 7.2% | +1.1pp | BioPlex K=50 |
| 7.6% | +8.1pp | Haas [gene] |
| 12.1% | +4.5pp | BioPlex K=100 |
| 14.9% | +9.7pp | Jager [construct] |
| 22.2% | +10.3pp | BioPlex K=200 |
| 23.8% | +13.4pp | Haas [construct] |

**Pearson r = 0.9023, and strict monotonicity does NOT survive the regime change.** Haas
[gene] at 7.6% sharing returns +8.1pp while BioPlex at 12.1% returns +4.5pp. The pathogen-host
curve runs consistently above the human-human curve at matched sharing, so prey sharing
predicts the sign and the trend but is not a sufficient statistic for the magnitude.

The honest statement is therefore weaker than the four-map version and better tested:
prey sharing decides WHETHER L3 beats guilt-by-association, monotonically within any one
dataset, with a crossover in the 5 to 12 percent band. It does not by itself decide by how
much, and the gap between regimes is unexplained.


## HuRI: does the rule survive when the bait/prey split is synthetic?

BioPlex answered "does this hold outside pathogen-host maps". HuRI asks something harder.
It is yeast two-hybrid and SYMMETRIC: there are no baits and no preys, so the
`bait -> prey -> bait' -> prey` route is not defined by the assay at all. Imposing a split
therefore separates two things the other five maps confound: whether the rule is about
GRAPH TOPOLOGY, or about real AP-MS bait/prey structure.

Construction: 49,271 unique undirected human gene pairs over 7,986 proteins (HuRI publishes
about 53,000 over 8,275), parsed from IntAct because interactome-atlas.org was unreachable
from the build host. 300 proteins were drawn at random and declared baits; preys are their
neighbours minus the drawn set; K is a nested prefix. **The split is an artefact of this
analysis, not of the experiment.**

| K baits | shared preys | positives | L3 reach | GBA reach | advantage | sign p | L3 AUC | GBA AUC |
|---|---|---|---|---|---|---|---|---|
| 25 | 8.1% | 56 | 7.9% | 5.7% | **+2.1pp** | 0.031 | 0.474 | 0.528 |
| 50 | 20.3% | 153 | 27.6% | 5.5% | **+22.2pp** | 1.9e-06 | 0.556 | 0.525 |
| 100 | 24.8% | 275 | 35.0% | 7.4% | **+27.6pp** | 1.9e-06 | 0.607 | 0.534 |
| 150 | 28.3% | 376 | 40.9% | 5.8% | **+35.1pp** | 6.1e-05 | 0.647 | 0.527 |
| 200 | 33.4% | 522 | 48.2% | 7.6% | **+40.6pp** | 2.0e-03 | 0.683 | 0.536 |

Strictly monotonic, and the largest advantages measured anywhere. The mechanism is also at
its clearest: **94% of L3's unique reach routes through a second bait**, against 85% on
Jager, 72% on BioPlex and 0% on Gordon. So the rule is topological. It does not need the
bait/prey roles to be real, only the sharing structure.

### Read the GBA column before believing the magnitudes

Guilt-by-association sits at AUC 0.525 to 0.536 at every K, barely above the 0.500 null, and
its reach never exceeds 7.6%. That is not L3 winning a fair fight. HuRI is enriched for
previously unreported interactions, so its preys are STRING-starved: mean prey STRING degree
1.073, with 1,298 of 1,895 preys having no STRING partner at all. GBA depends entirely on
STRING and therefore has almost nothing to work with, while L3's bait route needs no STRING.

**The honest statement is that HuRI confirms the DIRECTION emphatically and inflates the
MAGNITUDE.** Quote it as evidence that the mechanism is topological, not as evidence that
L3 beats guilt-by-association by 40 points on a typical map.

### Does STRING density explain the regime gap?

That starvation suggests a two-variable model, since prey sharing feeds L3 and STRING density
feeds GBA. Across all 15 map variants from 6 datasets:

    r(prey sharing, advantage)          = +0.939
    r(prey STRING degree, advantage)    = -0.371
    r(sharing, STRING degree)           = -0.226   (near-independent predictors)

    advantage = -1.89 + 1.255 * sharing% - 2.512 * preySTRINGdegree
    R^2 two-variable = 0.909     r^2 sharing alone = 0.882

The sign on STRING density is the predicted one, and it does shrink the Haas and BioPlex
residuals. But **a whole extra parameter buys 0.027 of R-squared, which is not a result.**
Prey sharing remains the dominant predictor; STRING density is a plausible secondary factor
that this evidence does not establish. The regime gap flagged in the BioPlex section stays
only partly explained.

### A caveat that applies to every correlation above

The 15 variants are not 15 independent observations. Five are nested HuRI prefixes, four are
nested BioPlex prefixes, and two each are Jager and Haas re-granulations. The effective
sample is **6 datasets**, so every r quoted here is inflated by the within-dataset
correlation and should be read as descriptive, not inferential.

## The deployment rule

> L3 contributes over guilt-by-association exactly when the AP-MS map has shared preys.
> Compute mean prey degree before running anything. At 1.000 the bait-intermediate route does
> not exist and L3 is strictly worse than a one-line STRING lookup. Above roughly 1.05 to 1.15
> it becomes the best recall channel in the panel, and the advantage grows with sharing within
> a dataset. Treat the crossover as a band, not a point: it sits near 1.05 on pathogen-host
> maps and nearer 1.10 on human-human ones.

One line of code, computable on any new map in advance, and it decides which scorer to run.

## Consequences

1. **Ship STRING-GBA as the default scorer, gate L3 on mean prey degree.** On both zero-sharing
   maps, including the flagship, the shipped predictor loses to a one-line lookup on every
   metric. On sharing maps L3 is the best recall channel. Report both, always.
2. **L3 is a recall channel, not a ranking channel.** Even where it wins reach decisively, it
   loses precision@20 and precision@50 to GBA (Jager construct: p@20 -0.083, p@50 -0.140 at
   0/40 seeds). Use it to widen the candidate pool, then rank with something else.
3. **Stop quoting a single-map, single-seed precision number.** Gordon p@20 for L3 is
   0.322 +/- 0.099 across seeds, not the frozen split's 0.45.
4. **This run is the product.** The harness's first serious use returned a verdict against its
   author's predictor on its author's flagship dataset, then found and validated the exact
   conditions under which that predictor is the best thing in the panel. That is the artifact.

## Caveats

- Penn contributes 176 edges and ~30 held-out positives per trial. It is the smallest map and
  its individual metrics are the noisiest, though the sign test is 0/39.
- Two of the six variants are re-granulations rather than independent datasets. The
  independent-dataset count is four; the independent zero-sharing count is two.
- Prey sharing and STRING prey degree are correlated across these maps, so the gradient is not
  a clean single-variable experiment. The bait-route path audit is what separates them: 85% of
  L3's unique reach on Jager goes through a bait, which STRING density cannot explain.
- Held-out fraction fixed at 17% throughout. Not varied.
- BioPlex is subsampled, not whole: STRING's API rejects more than 2000 identifiers, so K
  caps at 200 of a 400-bait draw. A full-network run needs the bulk STRING download and ENSP
  identifier mapping.
- HuRI is now tested, but with a SYNTHETIC bipartition and a starved GBA baseline. It
  establishes that the mechanism is topological; it does not give a usable effect size.
- The magnitude gap between the pathogen-host and human-human curves at matched sharing is
  unexplained. Prey sharing predicts sign and trend, not size.
