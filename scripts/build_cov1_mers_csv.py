"""Build the committed conservation ground-truth from the raw IntAct fetch.

Maps each IntAct viral-protein description to the Gordon canonical bait name
(matching evidence/gordon2020_edges.csv exactly, e.g. 'Nsp9', 'Orf6', 'Spike'),
buckets by strain, and writes ONLY SARS-CoV-1 + MERS edges. The Science paper's
SARS-CoV-2 map (396 PPIs) is deliberately NOT committed: keeping it out of the
repo is the strongest guarantee it can never contaminate the frozen benchmark
(which is built on the Nature 332). Nothing is approximated.
"""
import csv
import json
import re
from collections import Counter

RAW = "/Users/suraj/Desktop/Built with Claude Science/cartograph/scripts/_cov1_mers_raw.json"
OUT_CSV = "/Users/suraj/Desktop/Built with Claude Science/cartograph/evidence/gordon2020_science_cov1_mers_edges.csv"
OUT_JSON = "/Users/suraj/Desktop/Built with Claude Science/cartograph/evidence/gordon2020_science_cov1_mers_counts.json"


def strain_of(raw_strain):
    if "Middle East" in raw_strain or "MERS" in raw_strain or "Betacoronavirus England" in raw_strain:
        return "MERS-CoV"
    if raw_strain in ("SARS-CoV-1", "Human SARS coronavirus"):
        return "SARS-CoV-1"
    if raw_strain in ("SARS-CoV-2", "Severe acute respiratory syndrome coronavirus 2"):
        return "SARS-CoV-2"
    return raw_strain


def canonical_viral(desc, orf, molecule):
    """IntAct description -> Gordon canonical bait name. Returns None if unmappable
    (which must never happen silently -> the build asserts full coverage)."""
    text = " ".join(x for x in (desc, orf, molecule) if x)
    low = text.lower()
    # nsp: 'RNA-directed RNA polymerase nsp12', 'Non-structural protein 8', etc.
    m = re.search(r"nsp\s*(\d+)", low)
    if m:
        return f"Nsp{int(m.group(1))}"
    m = re.search(r"non-structural protein\s+(\d+)\b", low)
    if m:
        return f"Nsp{int(m.group(1))}"
    if "nucleoprotein" in low:
        return "N"
    if "envelope" in low:
        return "E"
    if "membrane protein" in low and "envelope" not in low:
        return "M"
    if "spike" in low:
        return "Spike"
    # accessory ORFs (SARS-CoV-2 canonical names). CoV-1 8a/8b -> Orf8; orf14 -> Orf9c.
    if re.search(r"\borf\s*8[ab]?\b", low) or "protein 8" in low:
        return "Orf8"
    if re.search(r"\borf\s*3a\b", low):
        return "Orf3a"
    if re.search(r"\bprotein 3b\b", low) or re.search(r"\borf\s*3b\b", low):
        return "Orf3b"
    if re.search(r"\borf\s*6\b", low):
        return "Orf6"
    if re.search(r"\borf\s*7a\b", low):
        return "Orf7a"
    if re.search(r"\borf\s*9b\b", low):
        return "Orf9b"
    if re.search(r"\borf\s*9c\b", low) or re.search(r"\b(uncharacterized )?protein 14\b", low) or "orf14" in low:
        return "Orf9c"
    if re.search(r"\borf\s*10\b", low):
        return "Orf10"
    # MERS lineage-specific accessory ORFs: keep their own names (NOT orthologous to SARS)
    m = re.search(r"\borf\s*(3|4a|4b|5)\b", low)
    if m:
        return f"MERS-ORF{m.group(1)}"
    return None


def uniprot(idstr):
    if not idstr:
        return ""
    return re.sub(r"\s*\(uniprotkb\)\s*", "", idstr).replace("uniprotkb_", "").strip()


def main():
    raw = json.load(open(RAW))
    rows, unmapped = [], []
    for r in raw:
        strain = strain_of(r["strain"])
        vp = canonical_viral(r.get("viral_desc"), r.get("viral_orf"), r.get("viral_molecule"))
        if vp is None:
            unmapped.append(r)
            continue
        rows.append({
            "strain": strain,
            "viral_protein": vp,
            "human_gene": r["human_gene"],
            "viral_uniprot": uniprot(r.get("viral_id")),
            "human_uniprot": uniprot(r.get("human_id")),
            "viral_desc": r.get("viral_desc") or "",
        })
    assert not unmapped, f"{len(unmapped)} unmapped viral proteins: " + \
        str(sorted({(x['strain'], x['viral_desc']) for x in unmapped}))

    # commit ONLY CoV-1 + MERS (benchmark isolation: Science CoV-2 is never committed)
    keep = [x for x in rows if x["strain"] in ("SARS-CoV-1", "MERS-CoV")]
    # dedup on (strain, viral_protein, human_gene) — spoke expansion can repeat pairs
    seen, deduped = set(), []
    for x in sorted(keep, key=lambda r: (r["strain"], r["viral_protein"], r["human_gene"])):
        k = (x["strain"], x["viral_protein"], x["human_gene"])
        if k in seen:
            continue
        seen.add(k)
        deduped.append(x)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["strain", "viral_protein", "human_gene",
                                          "viral_uniprot", "human_uniprot", "viral_desc"])
        w.writeheader()
        w.writerows(deduped)

    by_strain = Counter(x["strain"] for x in deduped)
    excluded_cov2 = sum(1 for x in rows if x["strain"] == "SARS-CoV-2")
    prov = {
        "source": "Gordon et al. 2020, Science, 'Comparative host-coronavirus protein interaction "
                  "networks reveal pan-viral disease mechanisms' (PMID 33060197, "
                  "DOI 10.1126/science.abe9403, PMC7808408, IMEx IM-28441), retrieved via EBI "
                  "IntAct REST (findInteractions) by publication id.",
        "retrieved": "2026-07-10",
        "committed_edges": {"SARS-CoV-1": by_strain["SARS-CoV-1"], "MERS-CoV": by_strain["MERS-CoV"]},
        "raw_intact_records": {"total_pmid_33060197": len(raw)},
        "benchmark_isolation": (
            f"The Science SARS-CoV-2 map ({excluded_cov2} PPIs, distinct from the Nature 332 the frozen "
            "benchmark uses) was fetched but is DELIBERATELY NOT committed, so it cannot modify, extend, "
            "or contaminate the frozen held-out split or ground truth. Only CoV-1 + MERS are committed, "
            "used exclusively for cross-species conservation."),
        "orthology_note": (
            "Viral orthology is partial. Nsp1-16, N, M, E, Spike have clear orthologs across all three "
            "viruses. Accessory ORFs do not: MERS encodes lineage-specific ORF3/4a/4b/5 (named MERS-ORF* "
            "here) and has NO ortholog of SARS Orf3a/3b/6/7a/8/9b/9c/10. SARS-CoV-1 Orf8a+Orf8b are mapped "
            "to the single SARS-CoV-2 Orf8, and SARS-CoV-1 'protein 14' to Orf9c. 'No ortholog' is a "
            "distinct state from 'not conserved' and is never collapsed."),
    }
    json.dump(prov, open(OUT_JSON, "w"), indent=1)
    print(f"wrote {OUT_CSV}: {len(deduped)} edges  {dict(by_strain)}")
    print(f"  (excluded {excluded_cov2} Science SARS-CoV-2 edges for benchmark isolation)")
    # per-strain viral protein coverage (for the ortholog model)
    for s in ("SARS-CoV-1", "MERS-CoV"):
        vps = sorted({x["viral_protein"] for x in deduped if x["strain"] == s})
        print(f"  {s} viral proteins ({len(vps)}): {vps}")


if __name__ == "__main__":
    main()
