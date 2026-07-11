"""STEP 0: fetch the SARS-CoV-1 + MERS interactomes from Gordon et al. 2020 Science
(PMID 33060197) via the EBI IntAct REST API, the same IMEx source as the Nature
ground truth. Writes a raw staging JSON for inspection; the committed CSV is built
from it in a second, auditable pass. No approximation: every edge is an IntAct
record, virus assigned by NCBI taxid, viral protein name taken from the record.
"""
import json
import re
import time
import urllib.request

REST = "https://www.ebi.ac.uk/intact/ws/interaction/findInteractions/33060197"
STRAIN_BY_TAXID = {
    "694009": "SARS-CoV-1", "227859": "SARS-CoV-1",   # Human SARS coronavirus
    "1335626": "MERS-CoV", "1335626 ": "MERS-CoV",
    "2697049": "SARS-CoV-2",                            # Science CoV-2 (isolation: not committed)
}
HUMAN = "9606"


def _alias_of(aliases, mi):
    """first alias tagged with the given MI (e.g. 'MI:0301' gene name)."""
    for a in aliases or []:
        if mi in a:
            return a.split(" (")[0].strip()
    return None


def fetch_all():
    recs, page, size = [], 0, 200
    while True:
        url = f"{REST}?page={page}&pageSize={size}"
        with urllib.request.urlopen(url, timeout=90) as r:
            d = json.load(r)
        recs.extend(d["content"])
        total = d["totalElements"]
        if len(recs) >= total:
            break
        page += 1
        time.sleep(0.34)
    return recs, total


def parse(rec):
    """Return (strain, viral_name_raw, viral_orf, viral_gene, human_gene, human_ok)
    or None if not a clean virus<->human pair."""
    def side(letter):
        return {
            "species": rec.get(f"species{letter}"),
            "molecule": rec.get(f"molecule{letter}"),
            "desc": rec.get(f"description{letter}"),
            "aliases": rec.get(f"aliases{letter}"),
            "id": rec.get(f"id{letter}"),
            "role": rec.get(f"experimentalRole{letter}"),
        }
    A, B = side("A"), side("B")
    # human is the Homo sapiens side; viral is the other
    if A["species"] == "Homo sapiens" and B["species"] != "Homo sapiens":
        human, viral = A, B
    elif B["species"] == "Homo sapiens" and A["species"] != "Homo sapiens":
        human, viral = B, A
    else:
        return None
    strain = {"Human SARS coronavirus": "SARS-CoV-1",
              "Severe acute respiratory syndrome coronavirus 2": "SARS-CoV-2",
              "Middle East respiratory syndrome-related coronavirus": "MERS-CoV",
              "Betacoronavirus England 1": "MERS-CoV"}.get(viral["species"], viral["species"])
    human_gene = _alias_of(human["aliases"], "MI:0301") or human["molecule"]
    viral_orf = _alias_of(viral["aliases"], "MI:0306")        # orf name
    viral_gene = _alias_of(viral["aliases"], "MI:0301")
    return {
        "strain": strain, "viral_species": viral["species"],
        "viral_desc": viral["desc"], "viral_orf": viral_orf, "viral_gene": viral_gene,
        "viral_id": viral["id"], "viral_molecule": viral["molecule"],
        "human_gene": human_gene, "human_id": human["id"],
    }


if __name__ == "__main__":
    recs, total = fetch_all()
    print(f"fetched {len(recs)} / {total} IntAct records for PMID 33060197")
    parsed = [p for p in (parse(r) for r in recs) if p]
    print(f"clean virus<->human pairs: {len(parsed)}")
    from collections import Counter
    print("by strain:", dict(Counter(p["strain"] for p in parsed)))
    out = "/Users/suraj/Desktop/Built with Claude Science/cartograph/scripts/_cov1_mers_raw.json"
    with open(out, "w") as f:
        json.dump(parsed, f, indent=1)
    print("wrote", out)
    # show the distinct viral protein descriptors per strain (for canonical mapping)
    for strain in ("SARS-CoV-1", "MERS-CoV", "SARS-CoV-2"):
        names = sorted({(p["viral_desc"] or p["viral_orf"] or p["viral_molecule"])
                        for p in parsed if p["strain"] == strain})
        print(f"\n{strain}: {len(names)} distinct viral proteins")
        for n in names:
            print("   ", n)
