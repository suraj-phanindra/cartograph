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
    # never call STRING or UniProt in tests
    monkeypatch.setattr(server, "_fetch_string_network", lambda genes: [])
    monkeypatch.setattr(server, "_resolve_lengths",
                        lambda proteins: {p: 300 + 100 * i for i, p in enumerate(proteins)})


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


# --- pooled-AF3 matrix screen ----------------------------------------------
MATRIX = ("prot,NUP98,RAE1,NUP214,G3BP1\n"
          "NUP98,1,0.88,0.72,0.15\n"
          "RAE1,0.88,1,0.65,0.10\n"
          "NUP214,0.72,0.65,1,0.14\n"
          "G3BP1,0.15,0.10,0.14,1")


def test_screen_parses_size_corrects_thresholds():
    d = client.post("/api/screen", json={"matrix": MATRIX, "threshold": 0.55}).json()
    assert d["source"] == "virtual screen (pooled-AlphaFold3)"
    assert d["n_proteins"] == 4 and d["n_pairs"] == 6
    assert d["size_corrected"] is True                      # monkeypatched lengths -> de-trend runs
    for r in d["top"]:
        assert r["band"] in ("highly confident", "confident", "weak", "no better than random")
        assert "iptm_size_corrected" in r
    # every kept pair is above threshold on its effective (size-corrected) value
    assert all(r["effective"] >= 0.55 for r in d["top"])


def test_screen_rejects_bad_protein_name():
    bad = "prot,<script>\n<script>,1"
    assert client.post("/api/screen", json={"matrix": bad}).status_code == 400


def test_screen_rejects_empty_matrix():
    assert client.post("/api/screen", json={"matrix": "prot"}).status_code == 400


def test_screen_partial_length_does_not_fabricate(monkeypatch):
    # red-team MAJOR: when one protein of a pair does not resolve, that pair must
    # be left uncorrected (no invented 0-length skewing the fit), not silently
    # flagged size_corrected on a fabricated basis.
    monkeypatch.setattr(server, "_resolve_lengths",
                        lambda proteins: {p: 300 + 100 * i for i, p in enumerate(proteins) if p != "NUP214"})
    d = client.post("/api/screen", json={"matrix": MATRIX, "threshold": 0.0}).json()
    by_pair = {tuple(sorted((r["a"], r["b"]))): r for r in d["top"]}
    for pair, r in by_pair.items():
        if "NUP214" in pair:
            assert r["size_corrected"] is False           # not corrected on a missing length
            assert r["effective"] == r["iptm"]            # effective == raw, nothing invented
            assert r["band_basis"] == "raw ipTM"


def test_screen_never_touches_locked_benchmark():
    # /api/screen must not import or use the frozen split; the eval endpoint number
    # is unchanged after a screen call
    client.post("/api/screen", json={"matrix": MATRIX})
    m = client.post("/api/eval/run").json()["metrics"]
    assert m["k"]["20"]["precision"] == 0.45
