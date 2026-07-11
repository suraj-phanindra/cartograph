"""CRISPR functional-genomics corroboration channel.

If a human protein Cartograph's map contains is ALSO a dependency hit in
independent genome-wide CRISPR screens, that is orthogonal FUNCTIONAL evidence for
its role in infection. It is NOT evidence of a physical interaction — functional
screens and AP-MS binding capture different biology (a knockout can matter without
the protein ever touching a viral bait). This channel never claims otherwise.

Data: evidence/crispr_screen_hits.json — 433 hits across 7 published genome-wide
screens, every hit traceable to a specific supplementary table / figure (curated
by a Claude Science run; see docs/completeness_note.md). We count PROVIRAL hits
(knockout REDUCES infection = dependency factor), which are knockout-comparable
across all 7 screens; a gene's weight is the number of screens it is a proviral hit
in. Antiviral/restriction hits are tracked but not counted in the dependency weight
(Biering's antiviral set is CRISPR-activation/GOF, not knockout-comparable).

Two of the seven screens (Wei, Baggen) lack a reproducible genome-wide FDR hit
list, so we also report every count EXCLUDING them (soft-provenance sensitivity,
per the source's own recommendation). Blank = not established, never fabricated.
"""
import functools
import json

from backend import config

# screens whose hit list is paper-curated top-N rather than a reproducible
# genome-wide FDR list (treat with most caution for overlap analysis)
SOFT_PROVENANCE = {"Wei et al. (Cell 2021)", "Baggen et al. (Nat Genet 2021)"}
N_SCREENS = 7


@functools.lru_cache(maxsize=1)
def _load():
    """gene -> {'proviral': [screen names], 'antiviral': [screen names]} and a
    screen->pmid map."""
    data = json.loads(config.CRISPR_HITS.read_text())
    genes, pmids = {}, {}
    for name, blk in data.items():
        if name.startswith("_"):
            continue
        pmids[name] = str(blk.get("pmid", ""))
        for h in blk["hits"]:
            g = h["gene"]
            rec = genes.setdefault(g, {"proviral": [], "antiviral": []})
            d = h.get("direction", "proviral")
            if name not in rec[d]:
                rec[d].append(name)
    return genes, pmids


def for_gene(gene):
    """Functional-evidence read for one human protein, or None if not a hit.

    n_screens = number of PROVIRAL (dependency) screens; screens carry name + pmid
    + a soft-provenance flag. n_screens_excl_soft drops Wei/Baggen. Also surfaces
    whether the gene is a restriction (antiviral) hit, labelled separately."""
    genes, pmids = _load()
    rec = genes.get(gene)
    if not rec or not rec["proviral"]:
        return None
    pro = rec["proviral"]
    screens = [{"name": s, "pmid": pmids.get(s, ""), "soft": s in SOFT_PROVENANCE} for s in pro]
    return {
        "n_screens": len(pro),
        "n_screens_excl_soft": sum(1 for s in pro if s not in SOFT_PROVENANCE),
        "of_total": N_SCREENS,
        "screens": screens,
        "direction": "proviral (dependency)",
        "also_restriction_hit": bool(rec["antiviral"]),
        "note": "functional dependency evidence — NOT evidence of a physical interaction",
    }


def map_summary(preys):
    """Option B corroboration over a set of host proteins in the map: how many are
    independent CRISPR dependency hits, with the soft-provenance sensitivity."""
    supported = []
    for g in sorted(set(preys)):
        fe = for_gene(g)
        if fe:
            supported.append({"gene": g, "n_screens": fe["n_screens"],
                              "n_screens_excl_soft": fe["n_screens_excl_soft"],
                              "screens": [s["name"] for s in fe["screens"]]})
    supported.sort(key=lambda x: (-x["n_screens"], x["gene"]))
    return {
        "n_host_factors": len(set(preys)),
        "n_crispr_supported": len(supported),
        "n_crispr_supported_excl_soft": sum(1 for s in supported if s["n_screens_excl_soft"] > 0),
        "n_screens_total": N_SCREENS,
        "supported": supported,
        "caveat": ("Functional-dependency hits from 7 genome-wide CRISPR screens (the high-confidence "
                   "core from each paper's own hit table/figure; Wei & Baggen lack a reproducible "
                   "genome-wide FDR list, so counts are also shown excluding them). A CRISPR hit is "
                   "orthogonal functional evidence, NOT proof of a physical interaction. Sparse overlap "
                   "with AP-MS prey is expected — dependency screens and binding assays capture different "
                   "biology. Blank means not established, never absent from biology."),
    }


if __name__ == "__main__":
    # demo self-check: union + screen-count weighting are correct and honest
    fe = for_gene("RAB7A")
    assert fe and fe["n_screens"] == 2, fe
    assert set(s["name"].split()[0] for s in fe["screens"]) == {"Daniloski", "Zhu"}
    assert for_gene("CEP350")["n_screens_excl_soft"] == 0            # Baggen-only -> drops without soft
    assert for_gene("RAE1") is None                                  # not a hit -> blank, not fabricated
    import csv as _csv
    preys = {r["prey_gene"] for r in _csv.DictReader(open(config.EDGES_CSV))}
    s = map_summary(preys)
    assert s["n_crispr_supported"] == 11 and s["n_crispr_supported_excl_soft"] == 9, s
    print(f"crispr ok: {s['n_crispr_supported']} of {s['n_host_factors']} host factors are CRISPR hits "
          f"({s['n_crispr_supported_excl_soft']} excl. soft-provenance)")
