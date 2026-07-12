"""Stage 2 — READ (Claude Reader). Given ONLY the retrieved corpus + structural
facts and a CLOSED set of PMIDs it may cite, produce cited mechanism clauses, a
confidence, and a proposed wet-lab experiment. If the corpus supports no mechanism
it returns no_mechanism=True. The Reader is never trusted: Stage 4 re-verifies every
citation it emits. Injectable (`read_fn`) so tests use a deterministic stand-in.
"""
from __future__ import annotations

from backend.agent import llm

_SYSTEM = (
    "You are the Reader in a protein-interaction evidence pipeline with a hard "
    "no-fabrication rule. You are given the ABSTRACTS actually retrieved for a "
    "protein pair and a CLOSED LIST of PMIDs. Write a mechanistic hypothesis for how "
    "the two proteins interact, as short clauses, and cite ONLY PMIDs from the closed "
    "list — a citation to any other PMID will be discarded. Do not state anything the "
    "retrieved abstracts do not support. If the abstracts do not support a mechanism, "
    "say so. Respond with ONLY a JSON object: "
    '{"no_mechanism": bool, "clauses": [{"text": str, "pmid": str}], '
    '"confidence": "low|moderate|high", "experiment": str}. Every clause.pmid MUST be '
    "one of the closed PMIDs. Keep clauses factual and free of causal overclaim. "
    "Provide at most 6 clauses; keep each under 40 words."
)


def _default_reader(corpus, resolved):
    if not llm.available():
        return {"no_mechanism": True, "clauses": [], "confidence": "n/a",
                "experiment": None, "reason": "reasoning layer not configured (no ANTHROPIC_API_KEY)"}
    closed = list(corpus["records"].keys())
    papers = "\n\n".join(
        f"PMID {p} — {r['title']} ({r['journal']} {r['year']})\n{(r['abstract'] or '')[:1500]}"
        for p, r in corpus["records"].items()
    ) or "(no abstracts retrieved)"
    struct = corpus.get("structure")
    struct_line = (f"Structure: {struct['source']} ({struct['kind']}); "
                   f"interface residues {struct.get('interface_residues') or 'not shown'}."
                   if struct else "Structure: none found.")
    user = (f"Protein pair: {corpus['bait']} (bait) and {corpus['prey']} (prey).\n"
            f"Closed PMID list you may cite: {closed}\n{struct_line}\n\nRETRIEVED ABSTRACTS:\n{papers}")
    out = llm.call_json(_SYSTEM, user)
    if not out:
        return {"no_mechanism": True, "clauses": [], "confidence": "n/a",
                "experiment": None, "reason": "Reader produced no parseable output"}
    # normalise + id the clauses; drop any clause missing text/pmid up front
    clauses = []
    for i, c in enumerate((out.get("clauses") or [])):
        if c.get("text") and c.get("pmid"):
            clauses.append({"id": i, "text": str(c["text"]), "pmid": str(c["pmid"])})
    return {"no_mechanism": bool(out.get("no_mechanism")) or not clauses,
            "clauses": clauses, "confidence": out.get("confidence", "n/a"),
            "experiment": out.get("experiment")}


def read(corpus, resolved, read_fn=None):
    return (read_fn or _default_reader)(corpus, resolved)
