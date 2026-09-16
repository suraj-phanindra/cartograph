# Four-map baseline bake-off: when does L3 earn its place?

Run 2026-09-15. The first multi-dataset experiment in this project.

**Result in one line:** L3 beats a one-line STRING lookup if and only if the AP-MS map has
shared preys, the advantage scales monotonically with how much sharing there is
(Pearson r = 0.91 over six map variants from four datasets), and the mechanism is a
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

## The deployment rule

> L3 contributes over guilt-by-association exactly when the AP-MS map has shared preys.
> Compute mean prey degree before running anything. At 1.000 the bait-intermediate route does
> not exist and L3 is strictly worse than a one-line STRING lookup. Above roughly 1.05 it
> becomes the best recall channel in the panel, and the advantage grows with sharing.

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
- All four maps are pathogen-host bipartite. No dense human-human map (HuRI, BioPlex) tested,
  so nothing here generalises to that regime.
