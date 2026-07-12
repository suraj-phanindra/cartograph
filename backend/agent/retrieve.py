"""Stage 1 — RETRIEVE (deterministic tools; the ONLY source of truth).

Everything the agent may later say must trace to something fetched here. NCBI
E-utilities for literature + the novelty co-mention count; RCSB for a real
deposited complex (interface residues computed from coordinates, the same <=3.0 A
heavy-atom method as the demo); AlphaFold DB for an honestly-labelled predicted
monomer when no complex exists; Open Targets for druggability. Every call is
recorded with {query, source, fetched_at}; every failure degrades to "unavailable"
with a reason, never a guess. API shapes verified live (see docs/REPORT.md).
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from backend import config
from backend.druggability import service as drug_service
from backend.structure import interface as iface

CACHE_DIR = Path(__file__).parent / "_cache"
CACHE_DIR.mkdir(exist_ok=True)
_HEADERS = {"User-Agent": f"Cartograph/1.0 ({config.AGENT_CONTACT})"}
CORE_CUTOFF = 3.0
MAX_RESIDUES = 6

# --- NCBI rate limiting (3/s without a key, 10/s with) ---------------------
_ncbi_lock = threading.Lock()
_ncbi_last = [0.0]


def _now():
    return datetime.now(timezone.utc).isoformat()


def _ncbi_throttle():
    gap = 0.11 if config.NCBI_API_KEY else 0.34
    with _ncbi_lock:
        wait = gap - (time.monotonic() - _ncbi_last[0])
        if wait > 0:
            time.sleep(wait)
        _ncbi_last[0] = time.monotonic()


def _eutils(endpoint, params, timeout=20):
    _ncbi_throttle()
    p = dict(params)
    p.update(tool="cartograph", email=config.AGENT_CONTACT)
    if config.NCBI_API_KEY:
        p["api_key"] = config.NCBI_API_KEY
    r = httpx.get(f"{config.EUTILS}/{endpoint}", params=p, headers=_HEADERS, timeout=timeout)
    r.raise_for_status()
    return r


def esearch(term, retmax=20):
    """Return (count, [pmids]) for a PubMed query."""
    r = _eutils("esearch.fcgi", {"db": "pubmed", "retmode": "json", "term": term, "retmax": retmax})
    res = r.json().get("esearchresult", {})
    return int(res.get("count", 0)), list(res.get("idlist", []))


def esummary(pmid):
    """Return {'title','journal','year'} or None. Also the live resolver for the
    Stage 4 verify gate (independent PMID->title confirmation)."""
    try:
        r = _eutils("esummary.fcgi", {"db": "pubmed", "id": str(pmid), "retmode": "json"})
        rec = (r.json().get("result", {}) or {}).get(str(pmid))
    except Exception:  # noqa: BLE001
        return None
    if not rec or not rec.get("title"):
        return None
    year = (rec.get("sortpubdate", "") or rec.get("pubdate", ""))[:4]
    return {"title": rec["title"].rstrip(". "), "journal": rec.get("source", ""), "year": year}


def efetch_abstract(pmid, timeout=20):
    try:
        r = _eutils("efetch.fcgi", {"db": "pubmed", "id": str(pmid),
                                    "rettype": "abstract", "retmode": "text"}, timeout=timeout)
        return r.text.strip()
    except Exception:  # noqa: BLE001
        return ""


# --- RCSB ------------------------------------------------------------------
def _rcsb_query(accessions):
    attr = "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession"
    return {
        "query": {"type": "group", "logical_operator": "and",
                  "nodes": [{"type": "terminal", "service": "text",
                             "parameters": {"attribute": attr, "operator": "exact_match", "value": a}}
                            for a in accessions]},
        "return_type": "entry",
        "request_options": {"return_all_hits": True},
    }


def find_complex(acc_a, acc_b, timeout=20):
    """PDB ids whose structure contains BOTH accessions (a real deposited complex)."""
    try:
        r = httpx.get(config.RCSB_SEARCH_API,
                      params={"json": json.dumps(_rcsb_query([acc_a, acc_b]))},
                      headers=_HEADERS, timeout=timeout)
        if r.status_code == 204:
            return []
        r.raise_for_status()
        return [x["identifier"] for x in r.json().get("result_set", [])]
    except Exception:  # noqa: BLE001
        return []


def fetch_cif(pdb, timeout=40):
    """Download a deposited mmCIF to the cache; return the local path (or None)."""
    pdb = pdb.upper()
    dest = CACHE_DIR / f"{pdb}.cif"
    if dest.exists():
        return dest
    try:
        r = httpx.get(f"{config.RCSB_FILES}/{pdb}.cif", headers=_HEADERS, timeout=timeout)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest
    except Exception:  # noqa: BLE001
        return None


def rcsb_contains(pdb, timeout=20):
    """(resolves, {accessions}) for the Stage-4 structure gate — read from the CIF we
    actually downloaded, so the check is against real coordinates."""
    path = fetch_cif(pdb, timeout=timeout)
    if not path:
        return False, set()
    try:
        return True, set(iface.subchains_by_accession(path).keys())
    except Exception:  # noqa: BLE001
        return False, set()


def alphafold_monomer(acc, gene, timeout=30):
    """Predicted-monomer fallback (honest N-G3BP1 precedent): pLDDT, model url, NO
    invented contact residues. Returns a structure-facts block or None."""
    try:
        r = httpx.get(f"{config.ALPHAFOLD_API}/{acc}", headers=_HEADERS, timeout=timeout)
        r.raise_for_status()
        rec = r.json()[0]
    except Exception:  # noqa: BLE001
        return None
    plddt = rec.get("globalMetricValue")
    cif_url = rec.get("cifUrl")
    local = None
    if cif_url:
        try:
            cif = httpx.get(cif_url, headers=_HEADERS, timeout=timeout)
            cif.raise_for_status()
            local = CACHE_DIR / f"AF-{acc}.cif"
            local.write_bytes(cif.content)
        except Exception:  # noqa: BLE001
            local = None
    return {
        "kind": "predicted",
        "source": f"AlphaFold DB (AF-{acc}, {gene})",
        "pdb": None, "accessions": [acc],
        "model_id": f"AF-{acc}-F1",
        "url": f"/api/structure?file=AF-{acc}.cif" if local else None,
        "method": "AlphaFold2 monomer (predicted)",
        "confidence": {"type": "pLDDT", "value": round(plddt, 1) if plddt else None, "unit": "mean pLDDT"},
        "chains": f"{gene} (predicted monomer; no deposited complex for this pair)",
        "interface_residues": [],
        "interface_source": ("no deposited complex; specific contact residues are not shown "
                             "(they would be unverified)."),
        "note": "PREDICTED monomer, shown labelled predicted with its real confidence. "
                "Not the complex; not experimental fact.",
    }


def _experimental_complex(pdb, acc_bait, acc_prey, bait, prey):
    """Build an experimental structure-facts block from a real deposited complex,
    with interface residues COMPUTED from coordinates (<=3.0 A heavy-atom)."""
    path = fetch_cif(pdb)
    if not path:
        return None
    residues, acc2subs = iface.interface_residues_by_accession(path, acc_bait, acc_prey)
    if acc_bait.upper() not in acc2subs or acc_prey.upper() not in acc2subs:
        return None
    core = [r for r in residues if r["min_dist"] <= CORE_CUTOFF]
    core = sorted(core, key=lambda r: r["min_dist"])[:MAX_RESIDUES]
    core = iface.short_labels(sorted(core, key=lambda r: r["seqid"]))
    return {
        "kind": "experimental",
        "source": f"PDB {pdb}", "pdb": pdb, "accessions": [acc_bait, acc_prey],
        "rcsb_url": f"https://www.rcsb.org/structure/{pdb}",
        "url": f"/api/structure?file={pdb}.cif",
        "method": "deposited structure (RCSB)",
        "confidence": {"type": "deposited", "value": pdb, "unit": "experimental complex"},
        "chains": f"{bait} + {prey} (deposited complex)",
        "interface_residues": core,
        "interface_source": f"computed: {bait} heavy-atom contacts with {prey} <= 3.0 Å in PDB {pdb}",
        "note": f"Experimental structure containing both {bait} and {prey}; interface residues "
                f"derived from the coordinates, not from prose.",
    }


def structure_for_pair(acc_bait, acc_prey, bait, prey):
    """Experimental complex if one exists, else an AlphaFold monomer of the prey,
    else None. Never invents contacts."""
    for pdb in find_complex(acc_bait, acc_prey):
        block = _experimental_complex(pdb, acc_bait, acc_prey, bait, prey)
        if block:
            return block
    return alphafold_monomer(acc_prey, prey)


# --- top-level retrieval ---------------------------------------------------
def retrieve(bait, prey, resolved, max_abstracts=None, taxid="9606"):
    """Fetch the full evidence corpus for one edge. Returns a dict with the closed
    PMID set, per-paper records, the co-mention (novelty) count, the structure
    block, druggability, and a provenance log of every query."""
    max_abstracts = max_abstracts or config.AGENT_MAX_ABSTRACTS
    acc_b = resolved["bait"]["accession"]
    acc_p = resolved["prey"]["accession"]
    queries = []

    term = f'"{bait}"[tiab] AND "{prey}"[tiab]'
    comention_count, pmids = 0, []
    try:
        comention_count, pmids = esearch(term, retmax=max_abstracts)
        queries.append({"query": term, "source": "ncbi-esearch", "fetched_at": _now(),
                        "count": comention_count})
    except Exception as e:  # noqa: BLE001
        queries.append({"query": term, "source": "ncbi-esearch", "fetched_at": _now(),
                        "error": type(e).__name__})

    records = {}
    for pmid in pmids[:max_abstracts]:
        summ = esummary(pmid)
        if not summ:
            continue
        abstract = efetch_abstract(pmid)
        records[pmid] = {"pmid": pmid, "title": summ["title"], "journal": summ["journal"],
                         "year": summ["year"], "abstract": abstract,
                         "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"}
    queries.append({"query": f"efetch {len(records)} abstracts", "source": "ncbi-efetch",
                    "fetched_at": _now()})

    structure = structure_for_pair(acc_b, acc_p, bait, prey)
    queries.append({"query": f"RCSB complex {acc_b}+{acc_p}", "source": "rcsb-search",
                    "fetched_at": _now(),
                    "result": (structure or {}).get("source", "none")})

    # druggability (Open Targets) is human-target-specific — skip honestly for other organisms
    if str(taxid) == "9606":
        drug = drug_service.get(prey, ensembl=resolved["prey"].get("ensembl"), live=True,
                                fetched=datetime.now().date().isoformat())
    else:
        drug = {"gene": prey, "unavailable": True,
                "reason": "druggability is human-target-specific (Open Targets); not shown for this organism"}
    queries.append({"query": f"OpenTargets {prey}", "source": "opentargets",
                    "fetched_at": _now(), "result": "unavailable" if drug.get("unavailable") else "ok"})

    return {
        "bait": bait, "prey": prey,
        "pmids": list(records.keys()),          # the closed set the verifier enforces
        "records": records,
        "comention_count": comention_count,
        "structure": structure,
        "druggability": drug,
        "queries": queries,
    }


if __name__ == "__main__":
    from backend.agent.resolve import resolve_edge
    r = resolve_edge("TP53", "MDM2")
    corpus = retrieve("TP53", "MDM2", r)
    print(f"co-mentions: {corpus['comention_count']} | papers: {len(corpus['records'])} | "
          f"structure: {(corpus['structure'] or {}).get('source')} | "
          f"druggable: {not corpus['druggability'].get('unavailable')}")
    for p, rec in list(corpus["records"].items())[:3]:
        print(f"  {p}: {rec['title'][:70]}")
