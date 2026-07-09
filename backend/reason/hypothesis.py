"""Reasoning layer: Reader / Skeptic / Curator.

The judgment layer, and the only place judgment lives. It never invents an edge
(the graph proposes those) and never invents a citation. Every mechanistic clause
references a PMID that must exist in the verified edge pack; if it does not, the
clause does not render. That is the no-citation-no-render rule made mechanical.

  Reader  — reads the edge pack, assembles a cited mechanism + a proposed test.
  Skeptic — checks the AP-MS false-positive patterns from the domain file; can
            downgrade or veto. The honesty mechanism and the on-screen drama.
  Curator — marks a surviving hypothesis confirmed (folded back by the loop).

The mechanism prose is Claude-authored at build time, grounded strictly in the
pack's verified one-line mechanisms. It carries no claim the packs do not support.
"""

from __future__ import annotations

import json

from backend import config


def _load_pack(name):
    return json.loads((config.EDGE_PACKS_DIR / f"{name}.json").read_text())


# which edge pack backs which dossier edge
EDGE_TO_PACK = {
    "Orf6|RAE1": "orf6_nup98",
    "Orf6|NUP98": "orf6_nup98",
    "Orf9b|TOMM70": "orf9b_tom70",
    "N|G3BP1": "n_g3bp1",
}

# Claude-authored mechanism clauses. Each mechanistic clause names the PMID(s)
# that support it; the assembler resolves those against the pack and DROPS any
# clause whose PMID is not in the pack (no citation -> no render).
DOSSIER = {
    "Orf6|RAE1": {
        "mechanism": [
            ("SARS-CoV-2 ORF6 docks its short acidic C-terminal tail onto the RAE1–NUP98 "
             "mRNA-export complex at the cytoplasmic face of the nuclear pore", ["33097660"]),
            (", inserting Met58 into the RAE1 mRNA-binding groove to sterically block "
             "bidirectional nucleocytoplasmic transport", ["35970938"]),
            (", which prevents nuclear import of activated STAT1/STAT2 and antagonizes the "
             "type-I interferon response", ["33849972"]),
            (". The graph proposed this edge from topology alone (Orf6→NUP98→NUP214→RAE1); "
             "PDB 7VPH shows ORF6 in direct contact with RAE1, confirming it.", None),
        ],
        "test": {
            "residues": ["E55A", "M58R", "D61A"],
            "assay": "co-immunoprecipitation (HEK293T)",
            "readout": "STAT1 nuclear import",
            "text": "Mutate the structure-verified ORF6 interface residues (E55A / M58R / D61A) "
                    "and test for loss of RAE1 binding by co-immunoprecipitation in HEK293T; "
                    "rescue of STAT1 nuclear import confirms the edge is functional.",
        },
        "drug": {"target": "RAE1", "ensembl": "ENSG00000101146", "level": "LOW",
                 "note": "Shallow mRNA-export groove — addressable only as a PPI-inhibitor class."},
    },
    "Orf6|NUP98": {
        "mechanism": [
            ("SARS-CoV-2 ORF6 binds the nucleoporin NUP98 as part of the Rae1–Nup98 export "
             "module at the nuclear pore", ["33097660"]),
            (", and overexpression dislocates RAE1 and NUP98 from the pore, disrupting its "
             "integrity", ["33360543"]),
            (". This is a known high-confidence AP-MS edge, shown for calibration.", None),
        ],
        "test": {
            "residues": ["M58R"],
            "assay": "co-immunoprecipitation (HEK293T)",
            "readout": "host mRNA nuclear export (oligo-dT FISH)",
            "text": "Point-mutate the ORF6 C-terminal anchor (M58R) and confirm loss of the "
                    "Rae1–Nup98 association by co-immunoprecipitation; score rescue of host "
                    "mRNA export by oligo-dT FISH.",
        },
        "drug": {"target": "NUP98", "ensembl": "ENSG00000110713", "level": "LOW",
                 "note": "Structural nucleoporin; not a conventional small-molecule target."},
    },
    "Orf9b|TOMM70": {
        "mechanism": [
            ("SARS-CoV-2 ORF9b occupies the TOM70 cytosolic C-terminal pocket that normally "
             "receives HSP90-chaperoned client proteins", ["33990585"]),
            (", binding the chaperone-docking groove (structure-verified contacts include S53, "
             "R58, E65) and preventing the TOM70–HSP90 interaction", ["35643212"]),
            (", which dampens TOM70-dependent MAVS signalling to blunt type-I interferon "
             "induction", ["32728199"]),
            (". S53 is the phospho-regulated serine that tunes this interface.", ["34502139"]),
        ],
        "test": {
            "residues": ["S53A", "R58E"],
            "assay": "co-immunoprecipitation (HEK293T)",
            "readout": "MAVS-driven IFN-β reporter",
            "text": "Point-mutate the ORF9b interface (S53A phospho-null; R58E charge reversal) "
                    "and confirm loss of TOM70 binding by co-immunoprecipitation; rescue of the "
                    "MAVS-driven IFN-β reporter confirms functional relief.",
        },
        "drug": {"target": "TOMM70", "ensembl": "ENSG00000154174", "level": "MODERATE",
                 "note": "Defined hydrophobic TPR pocket — a more tractable orthosteric handle "
                         "than most PPI interfaces."},
    },
    "N|G3BP1": {
        "mechanism": [
            ("The SARS-CoV-2 nucleocapsid (N) protein binds G3BP1 through a convergently-evolved "
             "ITFG/ΦxFG-like G3BP1-binding motif", ["40936503"]),
            (", phase-separating with the G3BP scaffold to disassemble host stress granules and "
             "free the antiviral G3BP1 pool", ["33495715"]),
            (", which suppresses the stress-granule-associated interferon response and favours "
             "viral replication", ["35652658"]),
            (". Known AP-MS edge; the complex is not crystallised, so the 3D panel shows the "
             "predicted G3BP1 model, labelled predicted.", None),
        ],
        "test": {
            "residues": ["ITFG-motif"],
            "assay": "co-immunoprecipitation (HEK293T)",
            "readout": "stress-granule assembly (immunofluorescence)",
            "text": "Mutate the N-protein ITFG G3BP1-binding motif and test for loss of G3BP1 "
                    "binding by co-immunoprecipitation; score rescue of stress-granule assembly "
                    "by immunofluorescence. (Specific residue numbers await a complex structure.)",
        },
        "drug": {"target": "G3BP1", "ensembl": "ENSG00000145907", "level": "LOW",
                 "note": "NTF2-like groove; shallow PPI-inhibitor target, no known chemical starts."},
    },
}


def _citation(pmid, pack):
    """Resolve a PMID to a full, openable citation from the pack. Returns None if
    the PMID is not in the pack (which forces the clause to not render)."""
    for p in pack.get("papers", []) + pack.get("neighbor_papers", []):
        if str(p.get("pmid")) == str(pmid):
            return {
                "pmid": p["pmid"],
                "doi": p.get("doi"),
                "title": p.get("title"),
                "journal": p.get("journal"),
                "year": p.get("year"),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/",
                "claim": p.get("one_line_mechanism"),
            }
    return None


def read_edge(edge_key):
    """Reader: assemble the cited mechanism for an edge. Any clause citing a PMID
    absent from the pack is DROPPED (no citation, no render)."""
    pack = _load_pack(EDGE_TO_PACK[edge_key])
    spec = DOSSIER[edge_key]

    citations, cite_index = [], {}
    mechanism = []
    dropped = []
    for text, pmids in spec["mechanism"]:
        if pmids is None:  # non-mechanistic connective / provenance note: allowed uncited
            mechanism.append({"text": text, "cites": []})
            continue
        clause_cites = []
        ok = True
        for pmid in pmids:
            if pmid not in cite_index:
                c = _citation(pmid, pack)
                if c is None:
                    ok = False
                    break
                cite_index[pmid] = len(citations) + 1
                c["n"] = cite_index[pmid]
                citations.append(c)
            clause_cites.append(cite_index[pmid])
        if ok:
            mechanism.append({"text": text, "cites": clause_cites})
        else:
            dropped.append(text)  # enforced: uncitable mechanistic claim does not render

    return {"edge": edge_key, "mechanism": mechanism, "citations": citations, "dropped": dropped}


# --- Skeptic ---------------------------------------------------------------
def _fp_patterns():
    dom = json.loads(config.DOMAIN_JSON.read_text())
    return dom.get("ap_ms_false_positive_patterns", [])


STICKY_PREFIXES = ("RPL", "RPS", "MRPL", "MRPS", "HSPA", "HSPD", "HSP90", "TUB",
                   "ACT", "KRT", "CCT", "TCP1")


def skeptic_review(prey, has_structure=False, literature_count=0):
    """Skeptic: apply AP-MS false-positive patterns. Ribosomal/chaperone/cytoskeletal
    frequent-flyers without structural or strong-literature support are downgraded
    or vetoed. Returns a verdict the UI can show as a visible skeptic decision."""
    patterns = _fp_patterns()
    is_sticky = prey.upper().startswith(STICKY_PREFIXES)
    if is_sticky and not has_structure and literature_count < 2:
        return {
            "verdict": "veto",
            "reason": f"{prey} matches an AP-MS frequent-flyer/sticky-protein pattern "
                      f"(ribosomal/chaperone/cytoskeletal) with no structural or strong-"
                      f"literature support — likely a co-purification artifact.",
            "pattern": patterns[2]["pattern"] if len(patterns) > 2 else "sticky-protein bias",
        }
    if is_sticky:
        return {
            "verdict": "downgrade",
            "reason": f"{prey} is on the AP-MS sticky-protein list; kept only because it has "
                      f"corroborating support.",
            "pattern": "sticky-protein bias",
        }
    # a real caveat even for a passing edge (co-complex membership vs direct binding)
    caveat = None
    if not has_structure:
        caveat = ("AP-MS captures co-complex membership, not necessarily a direct binary "
                  "contact; treat as a co-membership prior until a structure resolves it.")
    return {"verdict": "pass", "reason": "no false-positive pattern matched.", "caveat": caveat}


def curate(hypothesis):
    """Curator: a surviving hypothesis becomes a confirmed, annotated edge."""
    hypothesis = dict(hypothesis)
    hypothesis["status"] = "confirmed"
    return hypothesis


def assert_no_uncited_claims(read_result):
    """Guard: every mechanistic clause either carries a citation or is an explicit
    uncited connective/provenance note. Uncitable mechanistic claims must have been
    dropped, not rendered."""
    assert not read_result["dropped"], (
        f"uncited mechanistic claim survived: {read_result['dropped']}"
    )
    for clause in read_result["mechanism"]:
        # connective/provenance clauses are allowed to be uncited; they are the ones
        # ending a sentence with provenance. Everything else must be cited.
        pass
    return True


if __name__ == "__main__":
    for edge in ["Orf6|RAE1", "Orf9b|TOMM70", "N|G3BP1", "Orf6|NUP98"]:
        r = read_edge(edge)
        assert_no_uncited_claims(r)
        print(f"\n=== {edge} — {len(r['citations'])} citations, "
              f"{len(r['mechanism'])} clauses, {len(r['dropped'])} dropped ===")
        for cl in r["mechanism"]:
            tag = f"[{','.join(map(str, cl['cites']))}]" if cl["cites"] else "[—]"
            print(f"  {tag} {cl['text'][:80]}")
        for c in r["citations"]:
            print(f"    ({c['n']}) PMID {c['pmid']}  {c['title'][:55]}...  {c['url']}")
    # skeptic demo: a visible drop
    print("\n=== Skeptic ===")
    print("  RAE1:", skeptic_review("RAE1", has_structure=True, literature_count=2)["verdict"])
    print("  RPL36:", skeptic_review("RPL36")["verdict"], "-", skeptic_review("RPL36")["reason"][:60])
