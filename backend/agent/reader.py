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
    "no-fabrication rule. You are given the ABSTRACTS actually retrieved for a protein "
    "pair, a CLOSED LIST of PMIDs, and any structural fact. Summarise what the retrieved "
    "evidence ESTABLISHES about the relationship between the two proteins, as short cited "
    "clauses. The relationship may be a direct physical interaction, a regulatory or "
    "signalling relationship, or co-complex membership — state precisely which the source "
    "supports, and DO NOT claim direct binding if the source only shows regulation or "
    "co-occurrence. If a deposited complex structure is provided, you may note that the "
    "two proteins are found in one experimentally-determined complex (cite it as the PDB "
    "id in the pdb field, not as a PMID). Cite ONLY PMIDs from the closed list — any other "
    "PMID is discarded. If the abstracts establish no relationship at all, set "
    "no_mechanism true. Respond with ONLY a JSON object: "
    '{"no_mechanism": bool, "clauses": [{"text": str, "pmid": str}], '
    '"confidence": "low|moderate|high", "experiment": str}. Every clause.pmid MUST be one '
    "of the closed PMIDs. Factual, no causal overclaim; at most 6 clauses, each under 40 words."
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
