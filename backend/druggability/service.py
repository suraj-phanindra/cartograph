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

# tractability buckets, best first (per modality)
SM_PRIORITY = [
    "Approved Drug", "Advanced Clinical", "Phase 1 Clinical", "Structure with Ligand",
    "High-Quality Ligand", "High-Quality Pocket", "Med-Quality Pocket", "Druggable Family",
]
AB_PRIORITY = [
    "Approved Drug", "Advanced Clinical", "Phase 1 Clinical", "UniProt loc high conf",
    "GO CC high conf", "UniProt loc med conf", "UniProt SigP or TMHMM", "Human Protein Atlas loc",
]
APPROVED_BUCKET = "Approved Drug"

STAGE_LABEL = {
    "APPROVAL": "Approved", "PHASE_4": "Approved", "PHASE_3": "Phase III",
    "PHASE_2_3": "Phase II/III", "PHASE_2": "Phase II", "PHASE_1_2": "Phase I/II",
    "PHASE_1_3": "Phase I/III", "PHASE_1": "Phase I", "EARLY_PHASE_1": "Early Phase I",
    "PRECLINICAL": "Preclinical",
}
# clinical-trial order, for dedup "keep the highest stage" and for the honest
# down-labelling of a drug whose per-drug APPROVAL contradicts the target's
# curated tractability (Open Targets can disagree with itself; see BRD4).
STAGE_ORDER = {
    "PRECLINICAL": 0, "EARLY_PHASE_1": 1, "PHASE_1": 2, "PHASE_1_2": 3, "PHASE_2": 4,
    "PHASE_1_3": 4, "PHASE_2_3": 5, "PHASE_3": 6, "PHASE_4": 7, "APPROVAL": 8,
}


def _stage_label(stage):
    return STAGE_LABEL.get(stage, (stage or "Unknown").replace("_", " ").title())

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
    # tractability: highest true bucket per modality, by explicit priority
    true_buckets = [{"modality": t["modality"], "label": t["label"]}
                    for t in (tgt.get("tractability") or []) if t.get("value")]
    sm = next((b for name in SM_PRIORITY for b in true_buckets
               if b["modality"] == "SM" and b["label"] == name), None)
    ab = next((b for name in AB_PRIORITY for b in true_buckets
               if b["modality"] == "AB" and b["label"] == name), None)
    # Open Targets' authoritative, curated "this target has an approved drug" signal
    target_has_approved = any(b["label"] == APPROVED_BUCKET for b in true_buckets)

    # drugs: dedup by id keeping the HIGHEST clinical stage
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
        # A drug counts as APPROVED only if BOTH Open Targets signals agree: the
        # per-drug stage is APPROVAL AND the target carries the Approved-Drug
        # tractability bucket. This refuses to over-claim when OT contradicts
        # itself (e.g. BRD4/pelabresib: APPROVAL stage but no Approved-Drug bucket).
        approved = (stage == "APPROVAL") and target_has_approved
        if stage == "APPROVAL" and not target_has_approved:
            label = "Clinical"  # conservative: OT's target view says no approved drug
        else:
            label = "Approved" if approved else _stage_label(stage)
        entry = {
            "id": did, "name": dr.get("name"), "drug_type": dr.get("drugType"),
            "max_stage": stage, "stage_label": label, "approved": approved, "mechanism": mech,
            "ot_url": f"https://platform.opentargets.org/drug/{did}",
            "chembl_url": f"https://www.ebi.ac.uk/chembl/explore/compound/{did}",
        }
        prev = by_id.get(did)
        if prev is None or STAGE_ORDER.get(stage, -1) > STAGE_ORDER.get(prev["max_stage"], -1):
            by_id[did] = entry
    drugs = sorted(by_id.values(),
                   key=lambda d: (not d["approved"], -STAGE_ORDER.get(d["max_stage"], -1), d["name"] or ""))
    n_approved = sum(1 for d in drugs if d["approved"])
    lead = target_has_approved and n_approved > 0

    return {
        "gene": tgt.get("approvedSymbol") or gene, "ensembl": ensembl,
        "source": "Open Targets Platform GraphQL", "data_version": data_version,
        "endpoint": OT_ENDPOINT, "fetched": fetched,
        "tractability": {"small_molecule": sm["label"] if sm else None,
                         "antibody": ab["label"] if ab else None, "buckets": true_buckets},
        "drugs": drugs, "n_drugs": len(drugs), "n_approved": n_approved,
        "repurposing_lead": lead,
        "lead_basis": ("an approved drug and Open Targets' target-level Approved-Drug "
                       "tractability bucket agree") if lead else None,
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
import re as _re
_GENE_OK = _re.compile(r"^[A-Za-z0-9_.\-]{1,40}$")


def snapshot_path(gene):
    # enforce the gene allowlist at the sink so no caller can path-traverse
    if not _GENE_OK.match(gene or ""):
        raise ValueError(f"invalid gene symbol: {gene!r}")
    return SNAPSHOT_DIR / f"{gene}.json"


def load_snapshot(gene):
    try:
        p = snapshot_path(gene)
    except ValueError:
        return None                # invalid gene -> treat as no snapshot
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
