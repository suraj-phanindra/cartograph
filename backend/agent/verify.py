"""Stage 4 — VERIFY: the deterministic anti-hallucination gate.

This is code, not a prompt, and it is the single most important component of the
Evidence Agent. It takes whatever the (LLM) Reader produced and lets a clause
survive ONLY if its citation is real, resolvable, and from the closed set of
documents actually retrieved in Stage 1. A structure is accepted ONLY if its PDB
id resolves and truly contains both proteins' UniProt accessions.

The external lookups (esummary title resolve, RCSB "contains these accessions")
are injected as callables so the gate is exhaustively testable offline with
adversarial fixtures. Nothing here trusts the model.
"""
from __future__ import annotations

import re


def _norm_title(t):
    """Normalise a title for comparison: lowercase, drop non-alphanumerics, collapse
    whitespace. Tolerant of trailing periods / punctuation, strict on content."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (t or "").lower())).strip()


def titles_match(a, b):
    na, nb = _norm_title(a), _norm_title(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # tolerate one being a clean prefix of the other (truncated title fields)
    shorter, longer = sorted((na, nb), key=len)
    return len(shorter) >= 20 and longer.startswith(shorter)


def verify_clauses(clauses, retrieved, esummary):
    """Return (surviving, dropped). `retrieved` is the Stage-1 corpus:
    {"pmids": [...closed set...], "records": {pmid: {"title": ...}}}.
    `esummary(pmid)` returns {"title": ...} or None (injected; live in production).

    A clause survives only if ALL hold:
      (a) its pmid is in the retrieved closed set,
      (b) the pmid resolves via esummary,
      (c) the esummary title matches the retrieved record's title.
    """
    closed = {str(p) for p in retrieved.get("pmids", [])}
    records = retrieved.get("records", {})
    surviving, dropped = [], []
    for cl in clauses:
        pmid = str(cl.get("pmid", "")).strip()
        if not pmid or pmid not in closed:
            dropped.append({**cl, "drop_reason": "cited PMID was not in the retrieved closed set"})
            continue
        summ = None
        try:
            summ = esummary(pmid)
        except Exception:  # noqa: BLE001 - a lookup failure is a drop, never a pass
            summ = None
        if not summ or not summ.get("title"):
            dropped.append({**cl, "drop_reason": "PMID does not resolve via esummary"})
            continue
        if not titles_match(summ["title"], (records.get(pmid) or {}).get("title", "")):
            dropped.append({**cl, "drop_reason": "esummary title does not match the retrieved record"})
            continue
        surviving.append(cl)
    return surviving, dropped


def verify_structure(structure, contains_accessions):
    """Return (accepted_structure_or_None, reason_or_None).

    A PREDICTED (AlphaFold monomer) block is accepted as-is: it makes no complex
    claim and asserts no contact residues, so there is nothing to fabricate. An
    EXPERIMENTAL complex is accepted ONLY if its PDB id resolves AND actually
    contains BOTH accessions. `contains_accessions(pdb)` returns (resolves: bool,
    present_accessions: set[str]) — injected; live against RCSB in production.
    """
    if not structure:
        return None, None
    if structure.get("kind") == "predicted":
        return structure, None
    pdb = structure.get("pdb")
    need = {a for a in (structure.get("accessions") or []) if a}
    if not pdb or len(need) < 2:
        return None, "experimental structure is missing a PDB id or both accessions"
    try:
        resolves, present = contains_accessions(pdb)
    except Exception:  # noqa: BLE001
        resolves, present = False, set()
    if not resolves:
        return None, f"PDB {pdb} does not resolve"
    present = {str(a).upper() for a in (present or set())}
    if not {a.upper() for a in need} <= present:
        return None, f"PDB {pdb} does not contain both accessions {sorted(need)}"
    return structure, None


if __name__ == "__main__":
    # demo self-check: the gate drops every adversarial case and keeps the honest one
    retrieved = {"pmids": ["111", "222"],
                 "records": {"111": {"title": "ORF6 binds RAE1 at the nuclear pore"},
                             "222": {"title": "A large review of coronavirus biology"}}}
    good_esum = {"111": {"title": "ORF6 binds RAE1 at the nuclear pore."},   # trailing period ok
                 "222": {"title": "A large review of coronavirus biology"}}
    clauses = [
        {"id": 0, "text": "real", "pmid": "111"},               # keep
        {"id": 1, "text": "never retrieved", "pmid": "999"},    # drop: not in closed set
        {"id": 2, "text": "title tampered", "pmid": "222"},     # keep only if title matches
    ]
    surv, drop = verify_clauses(clauses, retrieved, lambda p: good_esum.get(p))
    assert [c["id"] for c in surv] == [0, 2], surv
    assert [c["id"] for c in drop] == [1], drop
    # non-resolving pmid drops even if in the closed set
    s2, d2 = verify_clauses([{"id": 9, "pmid": "111"}], retrieved, lambda p: None)
    assert not s2 and d2[0]["drop_reason"].startswith("PMID does not resolve")
    # title mismatch drops
    s3, d3 = verify_clauses([{"id": 9, "pmid": "111"}], retrieved,
                            lambda p: {"title": "totally different paper"})
    assert not s3 and "title" in d3[0]["drop_reason"]
    # structure gate
    exp = {"kind": "experimental", "pdb": "7VPH", "accessions": ["P0DTC6", "P78406"]}
    assert verify_structure(exp, lambda pdb: (True, {"P0DTC6", "P78406", "P52948"}))[0] is exp
    assert verify_structure(exp, lambda pdb: (True, {"P0DTC6"}))[0] is None       # missing one -> reject
    assert verify_structure(exp, lambda pdb: (False, set()))[0] is None           # unresolvable -> reject
    pred = {"kind": "predicted", "pdb": None, "accessions": ["P78406"]}
    assert verify_structure(pred, lambda pdb: (False, set()))[0] is pred          # monomer always ok
    print("verify gate ok: all adversarial cases dropped, honest cases kept")
