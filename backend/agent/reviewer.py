"""Stage 5 — FINAL ADVERSARIAL REVIEW (fresh Claude). Sees the assembled clauses,
the corpus, and the Stage-4 verify report. It may ONLY return clause ids to drop
plus free-text flags — it structurally cannot add a claim, because the pipeline reads
only `drop` (a list of ids) and `flags` from its output and ignores everything else.
Injectable for tests.
"""
from __future__ import annotations

from backend.agent import llm

_SYSTEM = (
    "You are the final reviewer of a protein-interaction dossier with a hard "
    "no-fabrication rule. You are shown clauses (each already citation-verified) with "
    "ids, the retrieved abstracts, and the verify report. Flag or remove any clause "
    "that overclaims beyond its cited abstract, uses causal language the source does "
    "not support, or presents a predicted structure as experimental. You CANNOT add or "
    "edit text. Respond with ONLY JSON: {\"drop\": [clause_id, ...], \"flags\": [str, ...]}."
)


def _default_reviewer(clauses, corpus, verify_report, review_fn=None):
    valid_ids = {c["id"] for c in clauses}
    if not llm.available() or not clauses:
        return {"drop": [], "flags": []}
    try:
        shown = "\n".join(f"[{c['id']}] {c['text']}  (cites PMID {c['pmid']})" for c in clauses)
        papers = "\n\n".join(f"PMID {p} — {r['title']}\n{(r['abstract'] or '')[:900]}"
                             for p, r in list(corpus["records"].items())[:12])
        out = llm.call_json(_SYSTEM, f"CLAUSES:\n{shown}\n\nABSTRACTS:\n{papers}")
    except Exception:  # noqa: BLE001
        out = None
    if not out:
        return {"drop": [], "flags": []}
    # STRUCTURAL enforcement: keep only real clause ids to drop; never any text the model wrote
    drop = [i for i in (out.get("drop") or []) if isinstance(i, int) and i in valid_ids]
    flags = [str(f) for f in (out.get("flags") or [])][:8]
    return {"drop": drop, "flags": flags}


def review(clauses, corpus, verify_report, review_fn=None):
    return (review_fn or _default_reviewer)(clauses, corpus, verify_report)
