"""Cross-species conservation: is a SARS-CoV-2 bait->prey edge also seen in
SARS-CoV-1 or MERS? An orthogonal corroboration signal, kept SEPARATE from
topology / structure / literature (never blended into one score).

Three states, NEVER collapsed (rendering 'no ortholog' as 'not conserved' is a
fabrication):
  - conserved      the orthologous viral protein binds the SAME human prey in
                   that strain.
  - not_conserved  the ortholog is represented in that strain's Gordon Science
                   screen, but no interaction with this prey is reported.
  - no_ortholog    no orthologous viral protein for this bait in that strain.

Orthology is PARTIAL and grounded in the data + comparative genomics:
  - Nsp1-16, N, M, E, Spike have clear orthologs in both strains (conserved core;
    Gordon screened the full ORFeome of each virus, so absence = 'no interaction').
  - Accessory ORFs: an ortholog is counted only where that ORF is represented in
    the strain's Gordon Science screen. MERS encodes lineage-specific ORF3/4a/4b/5
    and has NO ortholog of any SARS accessory ORF -> every CoV-2 accessory ORF is
    no_ortholog in MERS. Orf10 has no ortholog in either (CoV-2 putative-specific).
    This matches the well-established SARS/MERS comparative genomics.

Benchmark isolation: this reads ONLY the committed CoV-1 + MERS edges. The Science
SARS-CoV-2 map is not in the repo and never enters here.
"""
import csv
import functools

from backend import config

STRAINS = ("SARS-CoV-1", "MERS-CoV")
CONSERVED_CORE = {f"Nsp{i}" for i in range(1, 17)} | {"N", "M", "E", "Spike"}


@functools.lru_cache(maxsize=1)
def _load():
    """Return (edges_by_strain, viral_proteins_by_strain).

    edges_by_strain[strain] = set of (viral_protein, human_gene)
    viral_proteins_by_strain[strain] = set of canonical viral proteins represented.
    """
    edges = {s: set() for s in STRAINS}
    vprots = {s: set() for s in STRAINS}
    with open(config.COV1_MERS_CSV) as f:
        for r in csv.DictReader(f):
            s = r["strain"]
            if s not in edges:
                continue
            edges[s].add((r["viral_protein"], r["human_gene"]))
            vprots[s].add(r["viral_protein"])
    return edges, vprots


def _ortholog_exists(bait, strain):
    """True if bait has an orthologous viral protein in `strain`. Conserved-core
    proteins always do; accessory ORFs only where represented in the strain's screen
    (which matches SARS/MERS comparative genomics for every in-scope bait)."""
    if bait in CONSERVED_CORE:
        return True
    _, vprots = _load()
    return bait in vprots[strain]


def state(bait, prey, strain):
    """One of 'conserved' | 'not_conserved' | 'no_ortholog' for one strain."""
    if not _ortholog_exists(bait, strain):
        return "no_ortholog"
    edges, _ = _load()
    if (bait, prey) in edges[strain]:
        return "conserved"
    return "not_conserved"


def for_edge(bait, prey):
    """Full conservation read for a CoV-2 edge: per-strain state + a summary.
    `conserved_in` lists strains where the same edge is seen; `is_conserved` is
    True if conserved in at least one strain (the corroboration signal)."""
    per = {s: state(bait, prey, s) for s in STRAINS}
    conserved_in = [s for s, st in per.items() if st == "conserved"]
    return {
        "per_strain": per,
        "conserved_in": conserved_in,
        "is_conserved": bool(conserved_in),
        # a compact, honest label for the worklist column
        "label": _label(per, conserved_in),
    }


def _label(per, conserved_in):
    if conserved_in:
        return "conserved: " + ", ".join(s.replace("SARS-CoV-", "CoV-").replace("MERS-CoV", "MERS")
                                         for s in conserved_in)
    if all(v == "no_ortholog" for v in per.values()):
        return "no ortholog"
    return "not conserved"


def scores(edges, boost=0.5):
    """{(bait, prey): boost} for every edge conserved in >=1 strain -- the evaluator
    prior. Additive and transparent, exactly like the structural channel; never
    edits the frozen split."""
    out = {}
    for bait, prey in edges:
        if for_edge(bait, prey)["is_conserved"]:
            out[(bait, prey)] = boost
    return out


def compare_strains_rows(cov2_edges):
    """For the 'Compare strains' view: each CoV-2 edge with its conservation across
    strains, split into shared (conserved in >=1) vs CoV-2-specific."""
    rows = []
    for bait, prey in cov2_edges:
        c = for_edge(bait, prey)
        rows.append({"bait": bait, "prey": prey, "per_strain": c["per_strain"],
                     "conserved_in": c["conserved_in"], "shared": c["is_conserved"]})
    return rows


if __name__ == "__main__":
    # demo self-check: the three states are real and never collapsed
    assert state("Orf6", "RAE1", "SARS-CoV-1") == "conserved"          # flagship is pan-coronavirus
    assert state("Orf6", "RAE1", "MERS-CoV") == "no_ortholog"          # MERS has no Orf6 (NOT 'not conserved')
    assert state("Nsp9", "NUP98", "SARS-CoV-1") == "not_conserved"     # Nsp9 ortholog exists, no such edge
    assert state("Orf10", "BRD4", "SARS-CoV-1") == "no_ortholog"       # Orf10 is CoV-2-specific
    fe = for_edge("Orf6", "RAE1")
    assert fe["is_conserved"] and fe["conserved_in"] == ["SARS-CoV-1"]
    assert fe["per_strain"]["MERS-CoV"] == "no_ortholog"
    print("conservation states ok:", fe["label"])
