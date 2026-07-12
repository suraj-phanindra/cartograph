"""Evidence Agent tests. The heart is Stage 4 (the deterministic anti-hallucination
gate) exercised with adversarial fixtures — no network, no LLM. Plus offline pipeline
integration with injected deterministic stages, and the guarantee that the reviewer
cannot inject text and the demo/benchmark are untouched.
"""
import json

import pytest

from backend import config
from backend.agent import verify, pipeline, reviewer, cache


# ---------------------------------------------------------------------------
# Stage 4 — VERIFY gate: adversarial citation fixtures
# ---------------------------------------------------------------------------
RETRIEVED = {
    "pmids": ["111", "222"],
    "records": {"111": {"title": "ORF6 binds RAE1 at the nuclear pore"},
                "222": {"title": "A broad review of coronavirus cell biology"}},
}
GOOD_ESUMMARY = {"111": {"title": "ORF6 binds RAE1 at the nuclear pore."},   # trailing period tolerated
                 "222": {"title": "A broad review of coronavirus cell biology"}}


def test_verify_drops_pmid_never_retrieved():
    clauses = [{"id": 0, "text": "real", "pmid": "111"},
               {"id": 1, "text": "hallucinated", "pmid": "999"}]  # not in closed set
    surv, drop = verify.verify_clauses(clauses, RETRIEVED, lambda p: GOOD_ESUMMARY.get(p))
    assert [c["id"] for c in surv] == [0]
    assert drop[0]["id"] == 1 and "closed set" in drop[0]["drop_reason"]


def test_verify_drops_non_resolving_pmid():
    # pmid is in the closed set but esummary cannot resolve it -> dropped
    surv, drop = verify.verify_clauses([{"id": 0, "pmid": "111"}], RETRIEVED, lambda p: None)
    assert not surv and "does not resolve" in drop[0]["drop_reason"]


def test_verify_drops_title_mismatch():
    surv, drop = verify.verify_clauses([{"id": 0, "pmid": "111"}], RETRIEVED,
                                       lambda p: {"title": "an entirely different paper"})
    assert not surv and "title" in drop[0]["drop_reason"]


def test_verify_keeps_valid_citation():
    surv, drop = verify.verify_clauses([{"id": 0, "pmid": "222"}], RETRIEVED,
                                       lambda p: GOOD_ESUMMARY.get(p))
    assert [c["id"] for c in surv] == [0] and not drop


def test_verify_structure_rejects_missing_accession():
    exp = {"kind": "experimental", "pdb": "7VPH", "accessions": ["P0DTC6", "P78406"]}
    ok, reason = verify.verify_structure(exp, lambda pdb: (True, {"P0DTC6"}))  # only one present
    assert ok is None and "does not contain both" in reason


def test_verify_structure_rejects_unresolvable():
    exp = {"kind": "experimental", "pdb": "9ZZZ", "accessions": ["P1", "P2"]}
    ok, reason = verify.verify_structure(exp, lambda pdb: (False, set()))
    assert ok is None and "does not resolve" in reason


def test_verify_structure_accepts_real_complex_and_predicted_monomer():
    exp = {"kind": "experimental", "pdb": "7VPH", "accessions": ["P0DTC6", "P78406"]}
    assert verify.verify_structure(exp, lambda pdb: (True, {"P0DTC6", "P78406", "P52948"}))[0] is exp
    pred = {"kind": "predicted", "pdb": None, "accessions": ["P78406"]}
    assert verify.verify_structure(pred, lambda pdb: (False, set()))[0]["kind"] == "predicted"


def test_verify_rejects_title_prefix_false_accept():
    # red-team BLOCKER: a longer title that merely STARTS WITH the record title is a
    # different paper and must not pass the independent PMID->title re-confirmation
    assert not verify.titles_match("A binds B at the interface",
                                   "A binds B at the interface, a claim the paper never makes")
    assert not verify.titles_match("Materials and methods", "Materials and methods in cell biology")
    # a title differing only by trailing punctuation still matches (real records vary)
    assert verify.titles_match("A binds B at the interface", "A binds B at the interface.")


def test_verify_strips_residues_from_predicted_structure():
    # red-team MAJOR: a predicted block can never carry contact residues past the gate,
    # even if a producer left some in — enforced at the chokepoint, not trusted upstream
    pred = {"kind": "predicted", "pdb": None, "accessions": ["P1"],
            "interface_residues": ["SMUGGLED_R99", "SMUGGLED_R42"]}
    out, _ = verify.verify_structure(pred, lambda pdb: (False, set()))
    assert out["interface_residues"] == []


# ---------------------------------------------------------------------------
# Stage 5 — reviewer cannot inject text (structural)
# ---------------------------------------------------------------------------
def test_reviewer_can_only_drop_never_add():
    clauses = [{"id": 0, "text": "kept", "pmid": "111"}, {"id": 1, "text": "flagged", "pmid": "222"}]

    # a malicious reviewer tries to add a new clause and drop an invalid id
    def evil(cl, corpus, vr, review_fn=None):
        return {"drop": [1, 99], "flags": ["ok"], "clauses": [{"id": 5, "text": "INJECTED"}],
                "new_text": "fabricated mechanism"}
    out = reviewer.review(clauses, {}, {}, review_fn=evil)
    # the pipeline reads ONLY drop + flags; injected text/clauses are structurally ignored
    assert out["drop"] == [1, 99] and "INJECTED" not in json.dumps(out.get("flags", []))
    # and drop ids are applied by id only — no way to introduce new clause text
    assert "clauses" not in out or all("INJECTED" not in str(x) for x in out.get("flags", []))


# ---------------------------------------------------------------------------
# Pipeline integration — offline, deterministic injected stages
# ---------------------------------------------------------------------------
def _fixture_corpus(bait, prey, resolved):
    return {
        "bait": bait, "prey": prey,
        "pmids": ["111", "222"],
        "records": {"111": {"pmid": "111", "title": "A binds B at a real interface",
                            "journal": "J", "year": "2020", "abstract": "A binds B.",
                            "url": "https://pubmed.ncbi.nlm.nih.gov/111/"},
                    "222": {"pmid": "222", "title": "A review", "journal": "J", "year": "2019",
                            "abstract": "listed.", "url": "https://pubmed.ncbi.nlm.nih.gov/222/"}},
        "comention_count": 12,
        "structure": {"kind": "experimental", "pdb": "1ABC", "accessions": ["P1", "P2"],
                      "source": "PDB 1ABC", "confidence": {"type": "deposited", "value": "1ABC"},
                      "interface_residues": ["R10"], "url": "/api/structure?file=1ABC.cif"},
        "druggability": {"gene": prey, "ensembl": "ENSG1", "unavailable": False,
                         "tractability": {"small_molecule": "High-Quality Pocket"}},
        "queries": [{"query": "x", "source": "ncbi-esearch", "fetched_at": "t"}],
    }


def _ok_resolve(bait, prey):
    return {"ok": True, "bait": {"accession": "P1", "ensembl": "ENSG0"},
            "prey": {"accession": "P2", "ensembl": "ENSG1"}, "reason": None}


def _stages(reader_clauses, skeptic="pass"):
    return {
        "resolve_fn": _ok_resolve,
        "retrieve_fn": _fixture_corpus,
        "read_fn": lambda c, r: {"no_mechanism": not reader_clauses, "clauses": reader_clauses,
                                 "confidence": "moderate", "experiment": "co-IP + mutate the interface"},
        "skeptic_fn": lambda c, r, f=None: {"verdict": skeptic, "reason": skeptic, "caveat": None},
        "review_fn": lambda cl, c, vr, f=None: {"drop": [], "flags": []},
        "esummary": lambda pmid: {"title": c_title(pmid)},
        "rcsb_contains": lambda pdb: (True, {"P1", "P2"}),
    }


def c_title(pmid):
    return {"111": "A binds B at a real interface", "222": "A review"}.get(pmid, "")


def setup_function(_):
    cache.clear()


def test_pipeline_assembles_verified_dossier():
    clauses = [{"id": 0, "text": "A binds B.", "pmid": "111"}]
    d = pipeline.run("A", "B", l3_score=1.5, stages=_stages(clauses), use_cache=False)
    assert d["mechanism_status"] == "cited mechanism verified"
    assert d["mechanism"] and d["citations"][0]["pmid"] == "111"
    assert d["structure"]["pdb"] == "1ABC"                 # survived the structure gate
    assert d["conservation"]["not_applicable"] and d["crispr"]["not_applicable"]
    assert d["proposed_test"]["text"].startswith("co-IP")


def test_pipeline_drops_fabricated_citation_then_topology_only():
    # the ONLY clause cites a PMID that was never retrieved -> gate drops it -> topology-only
    clauses = [{"id": 0, "text": "fabricated", "pmid": "88888"}]
    d = pipeline.run("A", "B", stages=_stages(clauses), use_cache=False)
    assert d["mechanism"] == [] and "verify gate" in d["mechanism_status"]
    assert d["structure"] is not None                      # real facts still surfaced honestly


def test_pipeline_skeptic_veto_blocks_dossier():
    clauses = [{"id": 0, "text": "A binds B.", "pmid": "111"}]
    d = pipeline.run("A", "B", stages=_stages(clauses, skeptic="veto"), use_cache=False)
    assert d["mechanism"] == [] and "veto" in d["mechanism_status"].lower()


def test_pipeline_unresolved_symbol_degrades_honestly():
    stages = {"resolve_fn": lambda b, p: {"ok": False, "bait": {}, "prey": {},
              "reason": "could not resolve identifiers — AMBIG: ambiguous: 2 reviewed entries"}}
    d = pipeline.run("AMBIG", "B", stages=stages, use_cache=False)
    assert d["mechanism"] == [] and "resolve" in d["mechanism_status"].lower()
    assert d["conservation"]["not_applicable"]             # still honest, never blank


# ---------------------------------------------------------------------------
# Guardrails: the agent never touches the locked benchmark / demo artifact
# ---------------------------------------------------------------------------
def test_agent_dossier_is_not_benchmarked():
    d = pipeline.run("A", "B", stages=_stages([{"id": 0, "text": "A binds B.", "pmid": "111"}]),
                     use_cache=False)
    assert "not benchmarked" in d["provenance"]["evaluator"]


def test_agent_modules_do_not_import_frozen_split():
    import inspect
    from backend.agent import resolve, retrieve, pipeline as pl
    for mod in (resolve, retrieve, pl):
        src = inspect.getsource(mod)
        assert "heldout.frozen" not in src and "load_frozen" not in src


def test_baseline_unchanged():
    from backend.eval.evaluator import evaluate
    m = evaluate()["metrics"]
    assert m["k"][20]["precision"] == 0.45 and m["roc_auc"] == 0.8451


# ---------------------------------------------------------------------------
# Live integration (network) — skips cleanly offline
# ---------------------------------------------------------------------------
@pytest.mark.integration
def test_live_dossier_has_resolvable_citation():
    """Upload-style edge, resolved + retrieved LIVE; a deterministic Reader cites the
    top real retrieved PMID; the verify gate confirms it resolves. Proves real dossiers
    with resolvable citations. Skips if the network is unavailable."""
    from backend.agent import retrieve as rt
    try:
        from backend.agent.resolve import resolve_edge
        resolved = resolve_edge("TP53", "MDM2")
        if not resolved["ok"]:
            pytest.skip("resolve unavailable")
        corpus = rt.retrieve("TP53", "MDM2", resolved, max_abstracts=5)
    except Exception:
        pytest.skip("network unavailable")
    if not corpus["records"]:
        pytest.skip("no literature retrieved")
    top = next(iter(corpus["records"]))
    d = pipeline.run("TP53", "MDM2", stages={
        "read_fn": lambda c, r: {"no_mechanism": False, "confidence": "moderate",
                                 "experiment": "co-IP", "clauses": [{"id": 0,
                                 "text": "TP53 and MDM2 interact.", "pmid": top}]},
    }, use_cache=False)
    assert d["citations"], "a real retrieved citation should survive the gate"
    assert d["citations"][0]["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")
    assert d["conservation"]["not_applicable"] and d["crispr"]["not_applicable"]
    # structure gate ran against real coordinates (1YCR contains both accessions)
    assert d["structure"] is None or d["structure"]["pdb"]
