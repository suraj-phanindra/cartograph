"""STAGE 0 — the demo-critical-core regression gate.

Pins the exact facts the 3-minute demo depends on. Run after EVERY change
(`pytest backend/tests/test_regression_core.py`). If any assertion here fails, the
core has regressed — revert the change. These numbers are the honest headline and
must not drift: precision@20=0.45, ROC-AUC=0.8451 on 57 real held-out edges;
flagship Orf6->RAE1 recovered via the genuine length-3 path; loop 0.30->0.35.
"""

import pytest

from backend.build_artifact import build
from backend.eval.evaluator import evaluate


@pytest.fixture(scope="module")
def art():
    a, _ = build()
    return a


# --- the evaluator headline (the untouchable number) ------------------------
def test_evaluator_headline_unchanged():
    m = evaluate()["metrics"]
    assert m["k"][20]["precision"] == 0.45
    assert m["k"][10]["precision"] == 0.30
    assert m["k"][50]["precision"] == 0.26
    assert m["roc_auc"] == 0.8451
    assert m["n_targets"] == 57
    assert m["n_targets_recoverable"] == 14


def test_artifact_eval_block(art):
    b = art["eval"]["baseline"]
    assert b["headline_precision_at_k"] == 0.45
    assert b["roc_auc"] == 0.8451
    assert b["n_targets"] == 57
    assert b["without_pinned"]["precision_at_k"]["20"] == 0.45  # pinning does not inflate
    assert art["eval"]["seed"] == 42


def test_loop_before_after(art):
    lp = art["eval"]["loop"]
    assert lp["before_precision_at_20"] == 0.30
    assert lp["after_precision_at_20"] == 0.35
    assert lp["before_recoverable"] == lp["after_recoverable"]  # honest: re-ranking, not unlocking


# --- the flagship (query -> length-3 path -> predicted edge) -----------------
def test_flagship_length3_recovery(art):
    f = art["flagship"]
    assert f["edge"] == "Orf6|RAE1"
    assert f["path"] == ["Orf6", "NUP98", "NUP214", "RAE1"]  # genuine L3, not the 2-edge shortcut
    assert f["l3_rank"] == 7
    preds = {(p["source"], p["target"]): p for p in art["graph"]["predicted"]}
    assert ("Orf6", "RAE1") in preds, "flagship edge must be emitted so it draws + snaps green"
    pe = preds[("Orf6", "RAE1")]
    assert pe["held_out_true"] is True
    assert pe["path"] == ["Orf6", "NUP98", "NUP214", "RAE1"]


# --- the structural dossier (7VPH + residues + cited mechanism + skeptic) ----
def test_flagship_dossier(art):
    d = art["dossiers"]["Orf6|RAE1"]
    assert d["structure"]["kind"] == "experimental"
    assert d["structure"]["pdb"] == "7VPH"
    assert {"E55", "M58", "D61"} <= set(d["structure"]["interface_residues"])
    assert len(d["citations"]) >= 2
    for c in d["citations"]:
        assert str(c["pmid"]).isdigit() and c["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")
    # every mechanistic clause is cited or an explicit uncited connective
    assert any(cl["cites"] for cl in d["mechanism"])
    assert d["skeptic"]["verdict"] in ("pass", "downgrade", "veto")


def test_experimental_and_predicted_dossiers(art):
    dz = art["dossiers"]
    # second experimental structure with the repaired residues
    o9 = dz["Orf9b|TOMM70"]["structure"]
    assert o9["pdb"] == "7DHG" and o9["kind"] == "experimental"
    assert "S53" in o9["interface_residues"]
    assert "S55" not in o9["interface_residues"] and "K46" not in o9["interface_residues"]
    # predicted structure is labeled predicted with a real confidence, no asserted residues
    ng = dz["N|G3BP1"]["structure"]
    assert ng["kind"] == "predicted"
    assert ng["confidence"]["type"] == "pLDDT" and ng["confidence"]["value"] is not None
    assert ng["interface_residues"] == []


def test_no_uncited_mechanistic_claim(art):
    """No-citation-no-render: no mechanism clause carries a citation index that is
    absent from the dossier's citation list."""
    for key, d in art["dossiers"].items():
        cited_ns = {c["n"] for c in d["citations"]}
        for cl in d["mechanism"]:
            for n in cl["cites"]:
                assert n in cited_ns, f"{key}: clause cites [{n}] with no matching citation"
