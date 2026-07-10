"""Druggability service tests. Offline: parse a crafted-from-real Open Targets
response and the committed snapshots. No network. Guards approved-drug detection,
dedup, tractability selection, honest no-drugs/unavailable, and that this
display-only layer never imports the locked evaluator.
"""

import ast
import json

from backend import config
from backend.druggability import service


# a minimal response in the REAL OT 26.06 shape (introspected, not invented)
FIXTURE_TARGET = {
    "id": "ENSGTEST", "approvedSymbol": "TESTG",
    "tractability": [
        {"label": "Approved Drug", "modality": "SM", "value": False},   # false -> skipped
        {"label": "Advanced Clinical", "modality": "SM", "value": True},  # highest true SM
        {"label": "High-Quality Pocket", "modality": "SM", "value": True},
        {"label": "Approved Drug", "modality": "AB", "value": True},
    ],
    "drugAndClinicalCandidates": {"count": 3, "rows": [
        {"maxClinicalStage": "APPROVAL", "drug": {
            "id": "CHEMBL1", "name": "DrugA", "drugType": "Small molecule",
            "maximumClinicalStage": "APPROVAL",
            "mechanismsOfAction": {"rows": [{"mechanismOfAction": "X inhibitor"}]}}},
        {"maxClinicalStage": "PHASE_2", "drug": {
            "id": "CHEMBL2", "name": "DrugB", "drugType": "Small molecule",
            "maximumClinicalStage": "PHASE_2", "mechanismsOfAction": {"rows": []}}},
        {"maxClinicalStage": "PHASE_1", "drug": {  # duplicate of CHEMBL1, lower stage
            "id": "CHEMBL1", "name": "DrugA", "drugType": "Small molecule",
            "maximumClinicalStage": "APPROVAL",
            "mechanismsOfAction": {"rows": [{"mechanismOfAction": "X inhibitor"}]}}},
    ]},
}


def test_normalize_approved_detection_and_dedup():
    d = service._normalize("TESTG", "ENSGTEST", FIXTURE_TARGET, "2026-07-10", "26.06")
    # highest TRUE small-molecule bucket (Approved Drug was value=False)
    assert d["tractability"]["small_molecule"] == "Advanced Clinical"
    assert d["tractability"]["antibody"] == "Approved Drug"
    # deduped by drug id: 2 unique drugs, CHEMBL1 kept as approved
    assert d["n_drugs"] == 2
    assert d["n_approved"] == 1
    assert d["repurposing_lead"] is True
    a = next(x for x in d["drugs"] if x["id"] == "CHEMBL1")
    b = next(x for x in d["drugs"] if x["id"] == "CHEMBL2")
    assert a["approved"] is True and a["mechanism"] == "X inhibitor"
    assert b["approved"] is False and b["stage_label"] == "Phase II"
    # every drug links to its real source
    assert a["ot_url"] == "https://platform.opentargets.org/drug/CHEMBL1"


def test_normalize_no_drugs_is_honest():
    tgt = {"id": "E", "approvedSymbol": "NODRUG",
           "tractability": [{"label": "High-Quality Pocket", "modality": "SM", "value": True}],
           "drugAndClinicalCandidates": {"count": 0, "rows": []}}
    d = service._normalize("NODRUG", "E", tgt, "2026-07-10", "26.06")
    assert d["n_drugs"] == 0 and d["repurposing_lead"] is False
    assert d["tractability"]["small_molecule"] == "High-Quality Pocket"


def test_get_unavailable_when_offline_and_no_snapshot():
    d = service.get("NOSUCHGENE12345", live=False)
    assert d["unavailable"] is True and "no cached" in d["reason"].lower()


def test_committed_snapshots_real_and_labeled():
    # the demo/worklist snapshots exist, carry a source + date, and are self-consistent
    for gene in ["RAE1", "TOMM70", "G3BP1", "BRD4"]:
        snap = service.load_snapshot(gene)
        assert snap is not None, f"missing committed snapshot for {gene}"
        assert snap["source"] == "Open Targets Platform GraphQL"
        assert snap["data_version"] and snap["fetched"]
        assert snap["repurposing_lead"] == (snap["n_approved"] > 0)
        for dr in snap["drugs"]:
            assert dr["ot_url"].startswith("https://platform.opentargets.org/drug/")


def test_repurposing_lead_requires_target_approved_bucket():
    """A lead needs BOTH Open Targets signals to agree: an approved drug AND the
    target-level Approved-Drug tractability bucket. RPL36 (ataluren + bucket) is a
    real lead; BRD4 is NOT — its pelabresib row says APPROVAL but BRD4's own
    tractability has no Approved-Drug bucket (OT contradicting itself), so we
    refuse the over-claim."""
    rpl36 = service.load_snapshot("RPL36")
    assert rpl36["repurposing_lead"] is True and rpl36["n_approved"] >= 1

    brd4 = service.load_snapshot("BRD4")
    assert brd4["repurposing_lead"] is False
    assert brd4["n_approved"] == 0
    # pelabresib is down-labelled from Approved to Clinical (bucket disagrees)
    pela = next(d for d in brd4["drugs"] if d["name"] == "PELABRESIB")
    assert pela["approved"] is False and pela["stage_label"] == "Clinical"

    # the poorly-druggable flagship targets are honestly NOT leads
    for gene in ["RAE1", "TOMM70", "G3BP1"]:
        assert service.load_snapshot(gene)["repurposing_lead"] is False


def test_normalize_refuses_contradictory_approval():
    """Unit: a drug with APPROVAL stage but no target Approved-Drug bucket is not
    counted approved and is shown as Clinical, never as a repurposing lead."""
    tgt = {"id": "E", "approvedSymbol": "CONTRA",
           "tractability": [{"label": "Advanced Clinical", "modality": "SM", "value": True}],
           "drugAndClinicalCandidates": {"count": 1, "rows": [
               {"maxClinicalStage": "APPROVAL", "drug": {
                   "id": "CHEMBLX", "name": "DrugX", "drugType": "Small molecule",
                   "maximumClinicalStage": "APPROVAL", "mechanismsOfAction": {"rows": []}}}]}}
    d = service._normalize("CONTRA", "E", tgt, "2026-07-10", "26.06")
    assert d["repurposing_lead"] is False and d["n_approved"] == 0
    assert d["drugs"][0]["approved"] is False and d["drugs"][0]["stage_label"] == "Clinical"


def test_druggability_does_not_import_locked_evaluator():
    root = config.REPO_ROOT / "backend" / "druggability"
    for py in root.rglob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                    else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            for m in mods:
                assert "eval" not in m.split("."), f"{py} imports the locked evaluator ({m})"
