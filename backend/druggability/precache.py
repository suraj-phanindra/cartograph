"""Pre-fetch Open Targets druggability for the demo + worklist targets and commit
the snapshots to evidence/druggability/<gene>.json, so the OFFLINE demo shows real,
dated druggability data with no live call. Run once (needs network):

    python -m backend.druggability.precache

Polite: caches, one request at a time with a small delay. Re-running refreshes.
"""

from __future__ import annotations

import json
import time
from datetime import date

from backend import config
from backend.druggability import service

# demo dossier targets with their known Ensembl ids (skip a search round-trip)
DEMO_TARGETS = {
    "RAE1": "ENSG00000101146", "NUP98": "ENSG00000110713",
    "TOMM70": "ENSG00000154174", "G3BP1": "ENSG00000145907",
}


def _worklist_genes():
    art = config.FRONTEND_DATA_DIR / "cartograph_computed.json"
    if not art.exists():
        return []
    wl = json.loads(art.read_text()).get("worklist", [])
    seen, out = set(), []
    for r in wl:
        g = r.get("prey")
        if g and g not in seen:
            seen.add(g)
            out.append(g)
    return out


def run(fetched=None, delay=0.34):
    fetched = fetched or str(date.today())
    genes = list(DEMO_TARGETS) + [g for g in _worklist_genes() if g not in DEMO_TARGETS]
    print(f"pre-caching druggability for {len(genes)} targets (fetched {fetched})…")
    leads, failed = [], []
    for i, gene in enumerate(genes, 1):
        ens = DEMO_TARGETS.get(gene)
        try:
            d = service.fetch_druggability(gene, ens, fetched=fetched, timeout=25)
        except Exception as e:
            failed.append((gene, str(e)[:60]))
            print(f"  [{i:>2}/{len(genes)}] {gene:12} FAILED: {str(e)[:50]}")
            time.sleep(delay)
            continue
        if d.get("unavailable"):
            failed.append((gene, d["reason"]))
            print(f"  [{i:>2}/{len(genes)}] {gene:12} unavailable: {d['reason'][:40]}")
            time.sleep(delay)
            continue
        service.save_snapshot(gene, d)
        tag = "  ⇒ REPURPOSING LEAD" if d["repurposing_lead"] else ""
        if d["repurposing_lead"]:
            leads.append(gene)
        print(f"  [{i:>2}/{len(genes)}] {gene:12} SM={str(d['tractability']['small_molecule']):20} "
              f"drugs={d['n_drugs']:>3} approved={d['n_approved']:>2}{tag}")
        time.sleep(delay)
    print(f"\ndone. snapshots in {service.SNAPSHOT_DIR}")
    print(f"repurposing leads (>=1 approved drug): {leads}")
    if failed:
        print(f"failed/unavailable ({len(failed)}): {[g for g,_ in failed]}")
    return leads


if __name__ == "__main__":
    import sys
    run(fetched=sys.argv[1] if len(sys.argv) > 1 else None)
