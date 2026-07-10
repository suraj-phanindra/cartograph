"""API + upload tests. Offline: the STRING call is monkeypatched so tests never
hit the network. Guards the trust boundary (gene-name validation) and the
non-negotiable that uploaded data uses its OWN seed, never the locked benchmark's.
"""

import pytest
from fastapi.testclient import TestClient

import backend.api.server as server
from backend.api.server import app, UPLOAD_SEED
from backend import config

client = TestClient(app)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    # never call STRING in tests; return no enrichment edges
    monkeypatch.setattr(server, "_fetch_string_network", lambda genes: [])


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_eval_run_mirrors_engine():
    m = client.post("/api/eval/run").json()["metrics"]
    assert m["k"]["20"]["precision"] == 0.45
    assert m["roc_auc"] == 0.8451


def test_dossier_endpoint():
    d = client.get("/api/dossier", params={"edge": "Orf9b|TOMM70"}).json()
    assert d["citations"] and all(str(c["pmid"]).isdigit() for c in d["citations"])


def test_upload_valid():
    body = {"edges": "ORF6,NUP98\nORF6,RAE1\nNsp9,NUP214\nNsp9,NUP98\nN,G3BP1\nN,G3BP2",
            "heldout_fraction": 0.0}
    r = client.post("/api/upload", json=body)
    assert r.status_code == 200
    d = r.json()
    assert d["n_baits"] == 3 and d["n_edges"] == 6
    assert "predictions" in d
    # honest degradation: never invents evidence
    assert "no cached evidence" in d["note"].lower() or "not added" in d["note"].lower()


def test_upload_rejects_injection():
    r = client.post("/api/upload", json={"edges": "ORF6,<script>alert(1)</script>"})
    assert r.status_code == 400
    assert "invalid gene name" in r.json()["detail"].lower()


def test_upload_rejects_empty():
    assert client.post("/api/upload", json={"edges": "   "}).status_code == 400


def test_upload_own_eval_uses_separate_seed():
    # the uploaded eval must never reuse the locked benchmark's seed
    assert UPLOAD_SEED != config.HELDOUT_SEED


def test_upload_own_eval_runs():
    body = {"edges": "\n".join(f"B{i%3},P{i}" for i in range(30)), "heldout_fraction": 0.2}
    d = client.post("/api/upload", json=body).json()
    assert d["eval"] is not None and d["eval"]["seed"] == UPLOAD_SEED


def test_druggability_cached_snapshot():
    # RPL36 has a committed snapshot -> served offline, no network, a genuine lead
    # (approved drug AND Open Targets' Approved-Drug tractability bucket agree)
    d = client.get("/api/druggability", params={"gene": "RPL36"}).json()
    assert d["repurposing_lead"] is True
    assert d["source"] == "Open Targets Platform GraphQL"
    assert all(x["ot_url"].startswith("https://platform.opentargets.org/drug/") for x in d["drugs"])


def test_druggability_rejects_bad_gene():
    assert client.get("/api/druggability", params={"gene": "<script>"}).status_code == 400
    assert client.get("/api/druggability", params={"gene": "RAE1", "ensembl": "bad"}).status_code == 400
