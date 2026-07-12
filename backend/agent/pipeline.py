"""The Evidence Agent pipeline: orchestrates Stages 0-6 for one uploaded edge, emits
a progress trace, and assembles a dossier in the exact shape the frontend renders —
but ONLY out of clauses that survived the deterministic Stage-4 verify gate. Every
failure degrades honestly to topology-only with a stated reason; nothing is invented.

Conservation and CRISPR are coronavirus-specific reference data, so for an arbitrary
uploaded edge they are marked "not applicable", never blank.
"""
from __future__ import annotations

from backend.agent import cache, reader, retrieve, reviewer, skeptic, verify
from backend.agent.resolve import resolve_edge

NOT_APPLICABLE = {"not_applicable": True,
                  "reason": "no reference data for this organism (coronavirus-specific)"}


def _emit(cb, event, data=None):
    if cb:
        cb(event, data or {})


def _topology_only(edge, bait, prey, reason, l3_score=None, l3_path=None,
                   corpus=None, skeptic_out=None):
    """No cited mechanism survived — surface the real deterministic facts (structure,
    druggability, novelty) with an honest reason, but no fabricated dossier."""
    struct = (corpus or {}).get("structure")
    drug = (corpus or {}).get("druggability")
    return {
        "edge": edge, "source": bait, "target": prey, "status": "predicted",
        "live": True, "mechanism_status": reason, "mechanism": [], "citations": [],
        "structure": struct,
        "confidence": _confidence([], struct, (corpus or {}).get("comention_count", 0), l3_score),
        "conservation": NOT_APPLICABLE, "crispr": NOT_APPLICABLE,
        "structural_validation": None,
        "novelty": _novelty(corpus),
        "druggability": _druggability_block(prey, drug),
        "skeptic": skeptic_out or {"verdict": "n/a", "reason": reason, "caveat": None},
        "proposed_test": {"residues": [], "assay": "", "readout": "", "text": ""},
        "l3_path": l3_path, "held_out": False,
        "provenance": _provenance(corpus),
        "queries": (corpus or {}).get("queries", []),
    }


def _novelty(corpus):
    if not corpus:
        return None
    n = corpus.get("comention_count", 0)
    tag = "novel" if n == 0 else ("partially known" if n < 5 else "known")
    return {"tag": tag, "basis": f"{n} PubMed co-mentions of the pair (live esearch)"}


def _confidence(citations, struct, comention, l3_score):
    lit_n = len(citations)
    return {
        "topology": None, "topology_rank": None,
        "topology_note": f"L3 score {l3_score:.3f}" if l3_score is not None else None,
        "structure": (struct or {}).get("confidence"),
        "literature": ("multiple reports" if lit_n >= 2 else "single report" if lit_n == 1 else "none"),
        "literature_count": lit_n,
    }


def _druggability_block(prey, drug):
    return {"target": prey, "ensembl": (drug or {}).get("ensembl"),
            "curated_level": None, "curated_note": None, "live": drug}


def _provenance(corpus):
    return {
        "proposed_by": "deterministic degree-normalized L3 (your uploaded map)",
        "evidence_by": "Cartograph Evidence Agent — live retrieval (NCBI/RCSB/AlphaFold/Open Targets), "
                       "Claude Reader + Skeptic, deterministic citation-verify gate, final adversarial review",
        "structure_by": (corpus or {}).get("structure", {}).get("source") if corpus and corpus.get("structure") else "no structure found",
        "evaluator": "not benchmarked — uploaded edge, outside the locked held-out set",
    }


def _assemble(edge, bait, prey, corpus, clauses, skeptic_out, struct, reader_out,
              dropped, reviewer_out, l3_score, l3_path):
    """Build the rendered dossier from verified clauses only."""
    # citations: one entry per unique cited PMID, numbered in first-seen order
    order, cites = [], {}
    for c in clauses:
        if c["pmid"] not in cites:
            cites[c["pmid"]] = len(order) + 1
            order.append(c["pmid"])
    citations = []
    for pmid in order:
        rec = corpus["records"][pmid]
        citations.append({"n": cites[pmid], "pmid": pmid, "title": rec["title"],
                          "journal": rec["journal"], "year": rec["year"], "url": rec["url"]})
    mechanism = [{"text": c["text"], "cites": [cites[c["pmid"]]]} for c in clauses]
    residues = (struct or {}).get("interface_residues", []) if struct and struct.get("kind") == "experimental" else []
    return {
        "edge": edge, "source": bait, "target": prey, "status": "predicted", "live": True,
        "mechanism_status": "cited mechanism verified",
        "mechanism": mechanism, "citations": citations,
        "structure": struct,
        "confidence": _confidence(citations, struct, corpus.get("comention_count", 0), l3_score),
        "conservation": NOT_APPLICABLE, "crispr": NOT_APPLICABLE,
        "structural_validation": None,
        "novelty": _novelty(corpus),
        "druggability": _druggability_block(prey, corpus.get("druggability")),
        "skeptic": skeptic_out,
        "proposed_test": {"residues": residues, "assay": "", "readout": "",
                          "text": reader_out.get("experiment") or ""},
        "l3_path": l3_path, "held_out": False,
        "provenance": _provenance(corpus),
        "agent_report": {
            "queries": corpus.get("queries", []),
            "papers_retrieved": len(corpus["records"]),
            "comention_count": corpus.get("comention_count", 0),
            "skeptic_verdict": skeptic_out["verdict"],
            "clauses_dropped_by_verify": [{"text": d.get("text"), "pmid": d.get("pmid"),
                                           "reason": d.get("drop_reason")} for d in dropped],
            "clauses_dropped_by_reviewer": reviewer_out.get("drop", []),
            "reviewer_flags": reviewer_out.get("flags", []),
            "confidence": reader_out.get("confidence"),
        },
    }


def run(bait, prey, l3_score=None, l3_path=None, taxid="9606", stages=None, emit=None, use_cache=True):
    """Run the full pipeline for one edge in the given organism (default 9606 = human).
    `stages` may inject deterministic read_fn / skeptic_fn / review_fn / esummary /
    rcsb_contains / resolve_fn / retrieve_fn for tests."""
    stages = stages or {}
    edge = f"{bait}|{prey}"
    if use_cache:
        cached = cache.get(edge)
        if cached:
            _emit(emit, "cached", {"edge": edge})
            return cached

    _emit(emit, "resolving", {"bait": bait, "prey": prey})
    rf = stages.get("resolve_fn")
    resolved = rf(bait, prey) if rf else resolve_edge(bait, prey, taxid)
    if not resolved["ok"]:
        result = _topology_only(edge, bait, prey, resolved["reason"], l3_score, l3_path)
        _emit(emit, "topology_only", {"reason": resolved["reason"]})
        return result

    _emit(emit, "retrieving", {})
    rtf = stages.get("retrieve_fn")
    corpus = rtf(bait, prey, resolved) if rtf else retrieve.retrieve(bait, prey, resolved, taxid=taxid)
    _emit(emit, "retrieved", {"papers": len(corpus["records"]),
                              "comention_count": corpus["comention_count"],
                              "structure": (corpus["structure"] or {}).get("source", "none")})

    _emit(emit, "reading", {})
    reader_out = reader.read(corpus, resolved, stages.get("read_fn"))

    _emit(emit, "skeptic", {})
    skeptic_out = skeptic.review(corpus, resolved, stages.get("skeptic_fn"))
    if skeptic_out["verdict"] == "veto":
        result = _topology_only(edge, bait, prey, f"Skeptic veto: {skeptic_out['reason']}",
                                l3_score, l3_path, corpus, skeptic_out)
        _emit(emit, "vetoed", {"reason": skeptic_out["reason"]})
        if use_cache:
            cache.put(edge, result)
        return result

    if reader_out.get("no_mechanism"):
        reason = reader_out.get("reason", "no mechanism supported by retrieved literature")
        result = _topology_only(edge, bait, prey, reason, l3_score, l3_path, corpus, skeptic_out)
        _emit(emit, "topology_only", {"reason": reason})
        if use_cache:
            cache.put(edge, result)
        return result

    # STAGE 4 — the deterministic anti-hallucination gate
    _emit(emit, "verifying", {})
    esummary_fn = stages.get("esummary") or retrieve.esummary
    surviving, dropped = verify.verify_clauses(reader_out["clauses"], corpus, esummary_fn)
    struct_ok, struct_reason = verify.verify_structure(
        corpus["structure"], stages.get("rcsb_contains") or retrieve.rcsb_contains)
    corpus["structure"] = struct_ok  # a structure that fails the gate is dropped entirely
    _emit(emit, "verified", {"kept": len(surviving), "dropped": len(dropped),
                             "structure_ok": bool(struct_ok), "structure_reason": struct_reason})

    if not surviving:
        reason = "no citation survived the verify gate"
        result = _topology_only(edge, bait, prey, reason, l3_score, l3_path, corpus, skeptic_out)
        _emit(emit, "topology_only", {"reason": reason})
        if use_cache:
            cache.put(edge, result)
        return result

    # STAGE 5 — final adversarial review (drop-only)
    _emit(emit, "reviewing", {})
    reviewer_out = reviewer.review(surviving, corpus, {"dropped": dropped, "structure_reason": struct_reason},
                                   stages.get("review_fn"))
    final = [c for c in surviving if c["id"] not in set(reviewer_out.get("drop", []))]
    if not final:
        reason = "final reviewer dropped all clauses"
        result = _topology_only(edge, bait, prey, reason, l3_score, l3_path, corpus, skeptic_out)
        _emit(emit, "topology_only", {"reason": reason})
        if use_cache:
            cache.put(edge, result)
        return result

    result = _assemble(edge, bait, prey, corpus, final, skeptic_out, struct_ok,
                       reader_out, dropped, reviewer_out, l3_score, l3_path)
    _emit(emit, "dossier", {"edge": edge})
    if use_cache:
        cache.put(edge, result)
    return result
