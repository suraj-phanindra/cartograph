"""CRISPR functional-genomics channel: the union is correct, weighted by real
screen count, honest about soft provenance, and never claims physical validation.
"""
import json

from backend import config
from backend.crispr import crispr


def test_union_and_screen_count_weighting():
    # RAB7A is a proviral dependency hit in exactly two screens (Daniloski + Zhu)
    fe = crispr.for_gene("RAB7A")
    assert fe["n_screens"] == 2
    assert {s["name"].split()[0] for s in fe["screens"]} == {"Daniloski", "Zhu"}
    assert fe["of_total"] == 7
    # a non-hit returns None (blank = not established, never fabricated)
    assert crispr.for_gene("RAE1") is None
    assert crispr.for_gene("NUP98") is None


def test_soft_provenance_sensitivity():
    # CEP350 is a Baggen-only hit -> drops to 0 when the two soft screens are excluded
    fe = crispr.for_gene("CEP350")
    assert fe["n_screens"] == 1 and fe["n_screens_excl_soft"] == 0
    # a hit from a hard-provenance screen keeps its count
    assert crispr.for_gene("RAB7A")["n_screens_excl_soft"] == 2


def test_never_claims_physical_interaction():
    fe = crispr.for_gene("SCAP")
    assert "not evidence of a physical" in fe["note"].lower()
    s = crispr.map_summary(["SCAP", "RAB7A"])
    assert "not proof of a physical interaction" in s["caveat"].lower()


def test_map_summary_option_b():
    import csv
    preys = {r["prey_gene"] for r in csv.DictReader(open(config.EDGES_CSV))}
    s = crispr.map_summary(preys)
    assert s["n_host_factors"] == 332
    assert s["n_crispr_supported"] == 11            # real overlap, not the 1-gene consensus
    assert s["n_crispr_supported_excl_soft"] == 9   # sensitivity to the soft screens
    # every supported gene is a real Gordon prey and a real hit
    for row in s["supported"]:
        assert row["gene"] in preys and crispr.for_gene(row["gene"])


def test_only_proviral_counted_not_gof_antiviral():
    # Biering's antiviral set is CRISPR-activation (GOF), NOT knockout-comparable;
    # it must not inflate a gene's dependency screen count. Pick a mucin (GOF antiviral).
    data = json.loads(config.CRISPR_HITS.read_text())
    biering = data["Biering et al. (Nat Genet 2022)"]
    muc = next(h["gene"] for h in biering["hits"] if h["gene"].startswith("MUC") and h["direction"] == "antiviral")
    fe = crispr.for_gene(muc)
    # a GOF-only antiviral gene is not a dependency (proviral) hit -> None
    assert fe is None


def test_artifact_crispr_channel_present():
    art = json.loads((config.FRONTEND_DATA_DIR / "cartograph_computed.json").read_text())
    cc = art["eval"]["crispr_channel"]
    assert cc["n_crispr_supported"] == 11 and cc["n_crispr_supported_excl_soft"] == 9
    assert "not proof of a physical interaction" in cc["caveat"].lower()
