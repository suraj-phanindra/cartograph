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


def test_brd4_is_a_repurposing_lead_flagship_targets_are_not():
    brd4 = service.load_snapshot("BRD4")
    assert brd4["repurposing_lead"] is True and brd4["n_approved"] >= 1
    # the poorly-druggable flagship targets are honestly NOT leads
    for gene in ["RAE1", "TOMM70", "G3BP1"]:
        assert service.load_snapshot(gene)["repurposing_lead"] is False


def test_druggability_does_not_import_locked_evaluator():
    root = config.REPO_ROOT / "backend" / "druggability"
    for py in root.rglob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                    else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            for m in mods:
                assert "eval" not in m.split("."), f"{py} imports the locked evaluator ({m})"
