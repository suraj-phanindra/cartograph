"""Tests for the honesty invariants of the reasoning and structure layers:
no-citation-no-render, verified residues only, and predicted-labeled-predicted.
"""

import json

import pytest

from backend import config
from backend.reason.hypothesis import (
    read_edge, skeptic_review, assert_no_uncited_claims, DOSSIER, EDGE_TO_PACK,
)


DEMO_EDGES = ["Orf6|RAE1", "Orf9b|TOMM70", "N|G3BP1", "Orf6|NUP98"]


@pytest.mark.parametrize("edge", DEMO_EDGES)
def test_every_mechanistic_clause_is_cited(edge):
    r = read_edge(edge)
    assert_no_uncited_claims(r)  # zero uncitable mechanistic claims survived
    for clause in r["mechanism"]:
        # a clause is legal iff it has a citation OR it is an explicit connective/
        # provenance note (the only uncited clauses we allow, marked cites=[])
        assert isinstance(clause["cites"], list)


@pytest.mark.parametrize("edge", DEMO_EDGES)
def test_all_citations_are_openable_and_resolve(edge):
    r = read_edge(edge)
    assert r["citations"], "a dossier with a mechanism must have >=1 citation"
    for c in r["citations"]:
        assert c["pmid"] and str(c["pmid"]).isdigit()
        assert c["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")
        assert c["title"]


def test_no_placeholder_citation_survives():
    """The prototype's broken N-G3BP1 placeholder (Yang 2023 / pmc.ncbi.nlm.nih.gov/)
    must be gone: every N-G3BP1 citation resolves to a real PMID."""
    r = read_edge("N|G3BP1")
    urls = [c["url"] for c in r["citations"]]
    assert "https://pmc.ncbi.nlm.nih.gov/" not in urls
    assert all("/33495715/" in u or u.rstrip("/").split("/")[-1].isdigit() for u in urls)


def test_skeptic_vetoes_sticky_proteins():
    assert skeptic_review("RPL36")["verdict"] == "veto"
    assert skeptic_review("TUBB")["verdict"] == "veto"
    # a supported real edge passes
    assert skeptic_review("RAE1", has_structure=True, literature_count=2)["verdict"] == "pass"


def test_structure_predicted_is_labeled_predicted():
    facts = json.loads((config.FRONTEND_DATA_DIR / "structure_facts.json").read_text())
    ng = facts["N|G3BP1"]
    assert ng["kind"] == "predicted"
    assert ng["confidence"]["type"] == "pLDDT"
    assert ng["interface_residues"] == []  # no unverified residues asserted


def test_experimental_residues_are_structure_verified():
    facts = json.loads((config.FRONTEND_DATA_DIR / "structure_facts.json").read_text())
    # 7VPH-derived ORF6 residues include the anchored, structure-confirmed set
    orf6 = set(facts["Orf6|RAE1"]["interface_residues"])
    assert {"E55", "M58", "D61"} <= orf6
    # 7DHG: S53 confirmed; the prototype's wrong S55/K46 must NOT appear
    orf9b = set(facts["Orf9b|TOMM70"]["interface_residues"])
    assert "S53" in orf9b
    assert "S55" not in orf9b and "K46" not in orf9b
