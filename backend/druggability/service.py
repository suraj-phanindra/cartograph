"""Live druggability + repurposing from Open Targets Platform GraphQL.

Display-only enrichment. This module NEVER imports the locked evaluator or the
frozen split and never affects prediction or scoring — it only annotates a target
with real tractability and real drugs so a predicted host factor can be read as a
repurposing hypothesis.

Schema was introspected against the live endpoint (data 26.06), not assumed:
  target(ensemblId).tractability -> [{label, modality, value:Bool}]
  target(ensemblId).drugAndClinicalCandidates -> {count, rows:[{maxClinicalStage,
      drug{id,name,drugType,maximumClinicalStage,mechanismsOfAction{rows{mechanismOfAction}}}}]}
  approved := maxClinicalStage == "APPROVAL"

Honesty: a repurposing lead is a HYPOTHESIS, not an antiviral treatment claim.
Every drug/bucket/number here comes from the source and links back to it. If a
target has no drugs we say so; on failure we return unavailable, never a guess.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

from backend import config

OT_ENDPOINT = "https://api.platform.opentargets.org/api/v4/graphql"
SNAPSHOT_DIR = config.EVIDENCE_DIR / "druggability"

# small-molecule tractability buckets, best first
SM_PRIORITY = [
    "Approved Drug", "Advanced Clinical", "Phase 1 Clinical", "Structure with Ligand",
    "High-Quality Ligand", "High-Quality Pocket", "Med-Quality Pocket", "Druggable Family",
]
STAGE_LABEL = {
    "APPROVAL": "Approved", "PHASE_4": "Approved", "PHASE_3": "Phase III",
    "PHASE_2": "Phase II", "PHASE_1": "Phase I", "EARLY_PHASE_1": "Early Phase I",
    "PRECLINICAL": "Preclinical",
}

_TARGET_QUERY = """
query T($id: String!) {
  target(ensemblId: $id) {
    id approvedSymbol
    tractability { label modality value }
    drugAndClinicalCandidates {
      count
      rows {
        maxClinicalStage
        drug { id name drugType maximumClinicalStage
               mechanismsOfAction { rows { mechanismOfAction } } }
      }
    }
  }
}
"""
_SEARCH_QUERY = """
query S($q: String!) {
  search(queryString: $q, entityNames: ["target"]) {
    hits { id object { ... on Target { approvedSymbol } } }
  }
}
"""

_mem_cache = {}


def _gql(query, variables, timeout):
    r = requests.post(OT_ENDPOINT, json={"query": query, "variables": variables},
                      timeout=timeout, headers={"User-Agent": "cartograph/1.0"})
    r.raise_for_status()
    body = r.json()
    if body.get("errors"):
        raise RuntimeError("; ".join(e.get("message", "") for e in body["errors"])[:200])
    return body["data"]


def _data_version(timeout):
    try:
        d = _gql("{ meta { dataVersion { year month } } }", {}, timeout)["meta"]["dataVersion"]
        return f"{d['year']}.{d['month']}"
    except Exception:
        return "26.06"


def resolve_ensembl(gene, timeout=15):
    """Gene symbol -> Ensembl id via OT search (exact approvedSymbol match)."""
    data = _gql(_SEARCH_QUERY, {"q": gene}, timeout)
    for h in data.get("search", {}).get("hits", []):
        obj = h.get("object") or {}
        if (obj.get("approvedSymbol") or "").upper() == gene.upper():
            return h["id"]
    return None


def _normalize(gene, ensembl, tgt, fetched, data_version):
    # tractability: highest true SM/AB bucket
    true_buckets = [{"modality": t["modality"], "label": t["label"]}
                    for t in (tgt.get("tractability") or []) if t.get("value")]
    sm = next((b for name in SM_PRIORITY for b in true_buckets
               if b["modality"] == "SM" and b["label"] == name), None)
    ab = next((b for b in true_buckets if b["modality"] == "AB"), None)

    # drugs: dedup by drug id, keep best stage
    by_id = {}
    dc = tgt.get("drugAndClinicalCandidates") or {}
    for row in (dc.get("rows") or []):
        dr = row.get("drug") or {}
        did = dr.get("id")
        if not did:
            continue
        stage = row.get("maxClinicalStage") or dr.get("maximumClinicalStage") or ""
        moa_rows = ((dr.get("mechanismsOfAction") or {}).get("rows")) or []
        mech = moa_rows[0].get("mechanismOfAction") if moa_rows else None
        approved = stage == "APPROVAL"
        entry = {
            "id": did, "name": dr.get("name"), "drug_type": dr.get("drugType"),
            "max_stage": stage, "stage_label": STAGE_LABEL.get(stage, stage.title() if stage else "Unknown"),
            "approved": approved, "mechanism": mech,
            "ot_url": f"https://platform.opentargets.org/drug/{did}",
            "chembl_url": f"https://www.ebi.ac.uk/chembl/explore/compound/{did}",
        }
        prev = by_id.get(did)
        if prev is None or (approved and not prev["approved"]):
            by_id[did] = entry
    drugs = sorted(by_id.values(), key=lambda d: (not d["approved"], d["name"] or ""))
    n_approved = sum(1 for d in drugs if d["approved"])

    return {
        "gene": tgt.get("approvedSymbol") or gene, "ensembl": ensembl,
        "source": "Open Targets Platform GraphQL", "data_version": data_version,
        "endpoint": OT_ENDPOINT, "fetched": fetched,
        "tractability": {"small_molecule": sm["label"] if sm else None,
                         "antibody": ab["label"] if ab else None, "buckets": true_buckets},
        "drugs": drugs, "n_drugs": len(drugs), "n_approved": n_approved,
        "repurposing_lead": n_approved > 0,
        "opentargets_url": f"https://platform.opentargets.org/target/{ensembl}",
    }


def fetch_druggability(gene, ensembl=None, fetched=None, timeout=20):
    """Live fetch + normalize for one target. Raises on network/GraphQL error."""
    if fetched is None:
        raise ValueError("pass an explicit fetched date (Date.now is unavailable here)")
    if not ensembl:
        ensembl = resolve_ensembl(gene, timeout)
        if not ensembl:
            return {"gene": gene, "unavailable": True, "reason": f"no Ensembl id for {gene}"}
    dv = _data_version(timeout)
    tgt = _gql(_TARGET_QUERY, {"id": ensembl}, timeout).get("target")
    if not tgt:
        return {"gene": gene, "ensembl": ensembl, "unavailable": True,
                "reason": "target not found in Open Targets"}
    return _normalize(gene, ensembl, tgt, fetched, dv)


# --- snapshots (committed; the offline demo reads these) -------------------
def snapshot_path(gene):
    return SNAPSHOT_DIR / f"{gene}.json"


def load_snapshot(gene):
    p = snapshot_path(gene)
    if p.exists():
        return json.loads(p.read_text())
    return None


def save_snapshot(gene, data):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path(gene).write_text(json.dumps(data, indent=2))


def get(gene, ensembl=None, live=False, fetched=None, timeout=15):
    """Prefer the committed snapshot (offline, real, dated). Only if live=True and
    no snapshot exists do we hit the network. On failure: unavailable, never a guess."""
    if gene in _mem_cache:
        return _mem_cache[gene]
    snap = load_snapshot(gene)
    if snap is not None:
        _mem_cache[gene] = snap
        return snap
    if not live:
        return {"gene": gene, "ensembl": ensembl, "unavailable": True,
                "reason": "no cached druggability snapshot (offline). Run the API (./run.sh api)."}
    try:
        d = fetch_druggability(gene, ensembl, fetched=fetched, timeout=timeout)
    except Exception as e:
        return {"gene": gene, "ensembl": ensembl, "unavailable": True,
                "reason": "druggability unavailable (Open Targets unreachable)"}
    _mem_cache[gene] = d
    return d


if __name__ == "__main__":
    import sys
    from datetime import date
    gene = sys.argv[1] if len(sys.argv) > 1 else "TOMM70"
    ens = sys.argv[2] if len(sys.argv) > 2 else None
    d = fetch_druggability(gene, ens, fetched=str(date.today()))
    if d.get("unavailable"):
        print("unavailable:", d["reason"])
    else:
        print(f"{d['gene']} ({d['ensembl']}) — SM tractability: {d['tractability']['small_molecule']} · "
              f"{d['n_drugs']} drugs, {d['n_approved']} approved · repurposing_lead={d['repurposing_lead']}")
        for dr in d["drugs"][:6]:
            print(f"  {'[APPROVED]' if dr['approved'] else '['+dr['stage_label']+']':12} {dr['name']} — {dr['mechanism']}")
