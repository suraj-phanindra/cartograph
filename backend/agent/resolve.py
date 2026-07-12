"""Stage 0 — RESOLVE (deterministic, no LLM).

Gene symbol -> reviewed human UniProt accession -> Ensembl gene id, via the
UniProt REST API. FAIL CLOSED: if a symbol maps to zero or more than one reviewed
entry whose PRIMARY gene name matches, or the Ensembl cross-reference is ambiguous,
mark it unresolved and stop for that edge. Never guess an identifier.

Verified live against UniProt release 2026_02.
"""
from __future__ import annotations

import functools

import httpx

from backend import config

_HEADERS = {"User-Agent": f"Cartograph/1.0 ({config.AGENT_CONTACT})"}


def _get_json(url, params=None, timeout=20):
    r = httpx.get(url, params=params, headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


@functools.lru_cache(maxsize=512)
def resolve_symbol(symbol, taxid="9606"):
    """gene symbol -> {'symbol','accession','ensembl'} or {'symbol','unresolved':reason}.

    Reviewed + exact gene name in the given organism (default 9606 = human). `gene_exact`
    also matches synonyms, so we keep ONLY entries whose primary gene name equals the
    symbol; exactly one -> resolve, else fail closed (0 = unknown, >=2 = ambiguous)."""
    sym = (symbol or "").strip()
    taxid = str(taxid or "9606").strip()
    if not sym:
        return {"symbol": symbol, "unresolved": "empty symbol"}
    try:
        q = f"gene_exact:{sym} AND organism_id:{taxid} AND reviewed:true"
        data = _get_json(f"{config.UNIPROT_API}/search",
                         params={"query": q, "fields": "accession,gene_names,xref_ensembl",
                                 "format": "json", "size": 25})
    except Exception as e:  # noqa: BLE001 - network failure is honest-unresolved, never a guess
        return {"symbol": sym, "unresolved": f"UniProt lookup failed ({type(e).__name__})"}

    results = data.get("results", [])
    primary = [r for r in results if _primary_name_matches(r, sym)]
    if not primary:
        who = "human" if taxid == "9606" else f"taxid {taxid}"
        return {"symbol": sym, "unresolved": f"no reviewed {who} entry with this primary gene name"}
    if len(primary) > 1:
        accs = ", ".join(r.get("primaryAccession", "?") for r in primary)
        return {"symbol": sym, "unresolved": f"ambiguous: {len(primary)} reviewed entries ({accs})"}

    entry = primary[0]
    acc = entry.get("primaryAccession")
    ensembl = _ensembl_of(entry)
    if ensembl is None:
        # fall back to a direct entry fetch (search field can be sparse), still fail-closed
        ensembl = _ensembl_from_entry(acc)
    return {"symbol": sym, "accession": acc, "ensembl": ensembl}  # ensembl may be None (druggability then skips)


def _primary_name_matches(result, sym):
    for g in result.get("genes", []) or []:
        if (g.get("geneName") or {}).get("value") == sym:
            return True
    return False


def _dedup_ensembl(xrefs):
    ids = set()
    for x in xrefs or []:
        if x.get("database") != "Ensembl":
            continue
        for p in x.get("properties", []) or []:
            if p.get("key") == "GeneId" and p.get("value"):
                ids.add(p["value"].split(".")[0])   # strip .NN version
    return ids


def _ensembl_of(entry):
    ids = _dedup_ensembl(entry.get("uniProtKBCrossReferences"))
    return next(iter(ids)) if len(ids) == 1 else None   # fail closed on 0 or >1


def _ensembl_from_entry(acc):
    if not acc:
        return None
    try:
        entry = _get_json(f"{config.UNIPROT_API}/{acc}.json")
    except Exception:  # noqa: BLE001
        return None
    return _ensembl_of(entry)


def resolve_edge(bait, prey, taxid="9606"):
    """Resolve both ends in the given organism. Returns {'bait','prey','ok','reason'}."""
    rb, rp = resolve_symbol(bait, taxid), resolve_symbol(prey, taxid)
    unresolved = [r for r in (rb, rp) if "unresolved" in r]
    if unresolved:
        why = "; ".join(f"{r['symbol']}: {r['unresolved']}" for r in unresolved)
        return {"bait": rb, "prey": rp, "ok": False, "reason": f"could not resolve identifiers — {why}"}
    return {"bait": rb, "prey": rp, "ok": True, "reason": None}


if __name__ == "__main__":
    for s in ("TP53", "RAE1", "G3BP1", "NOTAREALGENE123"):
        print(f"{s:16}", resolve_symbol(s))
    print("edge:", resolve_edge("TP53", "MDM2")["ok"])
