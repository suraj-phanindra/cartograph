"""Cross-species conservation channel + the non-negotiable that the Science CoV-2
data can never enter the frozen benchmark. No network.
"""
import csv
import json

from backend import config
from backend.conservation import conserve
from backend.eval.evaluator import evaluate


# --- data provenance --------------------------------------------------------
def test_committed_edges_match_paper_counts():
    rows = list(csv.DictReader(open(config.COV1_MERS_CSV)))
    from collections import Counter
    by = Counter(r["strain"] for r in rows)
    assert by["SARS-CoV-1"] == 366        # exact canonical number
    assert by["MERS-CoV"] == 296          # exact canonical number
    # the Science SARS-CoV-2 map must NOT be committed (benchmark isolation)
    assert "SARS-CoV-2" not in by


def test_benchmark_isolation_baseline_unchanged():
    # conservation exists, but the locked baseline number is untouched
    m = evaluate()["metrics"]
    assert m["k"][20]["precision"] == 0.45
    assert m["roc_auc"] == 0.8451


def test_conservation_module_reads_only_cov1_mers():
    # the module must not pull in the evaluator / frozen split (check the actual
    # namespace, not source text) and must load only the isolated CoV-1/MERS file
    assert not hasattr(conserve, "evaluate")
    assert not hasattr(conserve, "load_frozen")
    edges, _ = conserve._load()
    assert set(edges) == {"SARS-CoV-1", "MERS-CoV"}
    # every human gene in the committed file is a real symbol; no CoV-2 viral bait leaked in
    rows = list(csv.DictReader(open(config.COV1_MERS_CSV)))
    assert all(r["strain"] in ("SARS-CoV-1", "MERS-CoV") for r in rows)


# --- three states, never collapsed -----------------------------------------
def test_three_states_are_distinct():
    # conserved: the flagship is pan-coronavirus in SARS-CoV-1
    assert conserve.state("Orf6", "RAE1", "SARS-CoV-1") == "conserved"
    # no_ortholog: MERS has NO Orf6 -- this must NOT be rendered as 'not_conserved'
    assert conserve.state("Orf6", "RAE1", "MERS-CoV") == "no_ortholog"
    # not_conserved: Nsp9 ortholog exists in CoV-1 but no such edge is reported
    assert conserve.state("Nsp9", "NUP98", "SARS-CoV-1") == "not_conserved"
    # Orf10 is CoV-2 putative-specific -> no ortholog in either strain
    assert conserve.state("Orf10", "BRD4", "SARS-CoV-1") == "no_ortholog"
    assert conserve.state("Orf10", "BRD4", "MERS-CoV") == "no_ortholog"


def test_no_ortholog_never_collapsed_into_not_conserved():
    # every SARS-CoV-2 accessory ORF is no_ortholog in MERS, never not_conserved
    for orf in ("Orf3a", "Orf6", "Orf7a", "Orf8", "Orf9b", "Orf9c", "Orf10"):
        assert conserve.state(orf, "ANYPREY", "MERS-CoV") == "no_ortholog"
    # conserved core is never no_ortholog (ortholog is universal)
    for core in ("Nsp9", "N", "M", "E", "Spike"):
        assert conserve.state(core, "ANYPREY", "MERS-CoV") != "no_ortholog"


def test_for_edge_summary_and_label():
    fe = conserve.for_edge("Orf6", "RAE1")
    assert fe["is_conserved"] and fe["conserved_in"] == ["SARS-CoV-1"]
    assert fe["per_strain"]["MERS-CoV"] == "no_ortholog"
    assert "conserved" in fe["label"]
    # a no-ortholog-everywhere edge is labelled 'no ortholog', not 'not conserved'
    assert conserve.for_edge("Orf10", "BRD4")["label"] == "no ortholog"


def test_scores_only_boosts_conserved():
    pairs = [("Orf6", "RAE1"), ("Nsp9", "NUP98"), ("Orf10", "BRD4")]
    sc = conserve.scores(pairs, boost=0.5)
    assert sc == {("Orf6", "RAE1"): 0.5}      # only the conserved pair


# --- the channel measurably helps (honest, holds excl-pinned) --------------
def test_conservation_prior_helps_excl_pinned():
    art = json.loads((config.FRONTEND_DATA_DIR / "cartograph_computed.json").read_text())
    cc = art["eval"]["conservation_channel"]
    assert cc["p10_gain_excl_pinned"] > 0        # genuinely helps, not just via the pinned edge
    assert cc["summary"]["shared_any_strain"] > 0
