"""Compute interface residues directly from experimental structures.

This is the strongest honesty source for CARRY_FORWARD item 3: rather than trust
the prototype's residue guesses or a paper's prose, we derive the interface from
the deposited coordinates. A residue is an interface residue if any of its heavy
atoms sits within CONTACT_CUTOFF of a heavy atom on the partner chain.

Used at build time to stamp verified residues into the exported dossier. If a
residue cannot be shown to be a real contact, it is not rendered.
"""

from __future__ import annotations

import gemmi

CONTACT_CUTOFF = 4.0  # angstroms, heavy-atom to heavy-atom


def _subchain_descriptions(cif_path):
    """Map each polymer subchain (label_asym_id) -> its entity pdbx_description."""
    doc = gemmi.cif.read(str(cif_path))
    block = doc.sole_block()
    strip = gemmi.cif.as_string
    ent_id = [strip(x) for x in block.find_loop("_entity.id")]
    ent_desc = [strip(x) for x in block.find_loop("_entity.pdbx_description")]
    id2desc = dict(zip(ent_id, ent_desc))
    asym = [strip(x) for x in block.find_loop("_struct_asym.id")]
    asym_ent = [strip(x) for x in block.find_loop("_struct_asym.entity_id")]
    return {a: id2desc.get(e, "") for a, e in zip(asym, asym_ent)}


def _match(desc, needle):
    return needle.lower() in (desc or "").lower()


def _contacts(cif_path, a_subs, b_subs, cutoff):
    """Heavy-atom contacts: residues on subchains a_subs whose atoms sit within
    `cutoff` of any heavy atom on subchains b_subs. The one shared method used for
    both the description- and accession-keyed entry points below."""
    st = gemmi.read_structure(str(cif_path))
    st.setup_entities()
    model = st[0]
    ns = gemmi.NeighborSearch(model, st.cell, cutoff + 1).populate()
    hits = {}
    for chain in model:
        for res in chain:
            if res.subchain not in a_subs:
                continue
            for atom in res:
                if atom.is_hydrogen():
                    continue
                for m in ns.find_atoms(atom.pos, "\0", radius=cutoff):
                    cra = m.to_cra(model)
                    if cra.residue.subchain in b_subs and not cra.atom.is_hydrogen():
                        key = (res.name, res.seqid.num)
                        hits[key] = min(hits.get(key, 1e9), atom.pos.dist(cra.atom.pos))
    out = sorted(hits.keys(), key=lambda k: k[1])
    return [{"resname": r, "seqid": s, "min_dist": round(hits[(r, s)], 2)} for r, s in out]


def interface_residues(cif_path, chain_a_desc, chain_b_desc, cutoff=CONTACT_CUTOFF):
    """Interface residues on the polymer matching chain_a_desc that contact any
    polymer matching chain_b_desc, matched by mmCIF entity description via the
    label_asym (subchain) id. Returns (residue_dicts, subchain_desc_map)."""
    sub_desc = _subchain_descriptions(cif_path)
    a_subs = {s for s, d in sub_desc.items() if _match(d, chain_a_desc)}
    b_subs = {s for s, d in sub_desc.items() if _match(d, chain_b_desc)}
    return _contacts(cif_path, a_subs, b_subs, cutoff), sub_desc


def subchains_by_accession(cif_path):
    """Map UniProt accession -> set of polymer subchains (label_asym_id), via the
    mmCIF _struct_ref (db_name UNP -> pdbx_db_accession -> entity_id) + _struct_asym.
    Lets a live-fetched complex be keyed by accession, not by prose description."""
    doc = gemmi.cif.read(str(cif_path))
    block = doc.sole_block()
    strip = gemmi.cif.as_string
    ref_ent = [strip(x) for x in block.find_loop("_struct_ref.entity_id")]
    ref_db = [strip(x) for x in block.find_loop("_struct_ref.db_name")]
    ref_acc = [strip(x) for x in block.find_loop("_struct_ref.pdbx_db_accession")]
    ent2acc = {e: acc.upper() for e, db, acc in zip(ref_ent, ref_db, ref_acc)
               if db.upper() in ("UNP", "UNIPROT")}
    asym = [strip(x) for x in block.find_loop("_struct_asym.id")]
    asym_ent = [strip(x) for x in block.find_loop("_struct_asym.entity_id")]
    acc2subs = {}
    for a, e in zip(asym, asym_ent):
        acc = ent2acc.get(e)
        if acc:
            acc2subs.setdefault(acc, set()).add(a)
    return acc2subs


def interface_residues_by_accession(cif_path, acc_a, acc_b, cutoff=CONTACT_CUTOFF):
    """Interface residues between two UniProt accessions in a deposited complex.
    Returns (residue_dicts, acc2subs). Empty residues if either accession is not a
    mapped polymer in the entry (honest: we then assert no contacts)."""
    acc2subs = subchains_by_accession(cif_path)
    a_subs = acc2subs.get((acc_a or "").upper(), set())
    b_subs = acc2subs.get((acc_b or "").upper(), set())
    if not a_subs or not b_subs:
        return [], acc2subs
    return _contacts(cif_path, a_subs, b_subs, cutoff), acc2subs


# short (one-letter) codes for compact residue labels like "M58"
_THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V", "SEP": "S", "TPO": "T", "PTR": "Y",
}


def short_labels(residues):
    return [f"{_THREE_TO_ONE.get(r['resname'], r['resname'])}{r['seqid']}" for r in residues]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    cif_dir = Path(__file__).parent / "cif"

    print("=== 7VPH: ORF6 residues contacting RAE1 (mRNA export factor) ===")
    res, desc = interface_residues(cif_dir / "7VPH.cif", "ORF6", "mRNA export factor")
    print("  chain descriptions:", desc)
    print("  ORF6 interface residues (contact RAE1):", short_labels(res))
    for r in res:
        print(f"    {r['resname']}{r['seqid']}  min_dist={r['min_dist']}A")

    print("\n=== 7DHG: ORF9b residues contacting TOM70 ===")
    res2, desc2 = interface_residues(cif_dir / "7DHG.cif", "ORF9b", "TOM70")
    print("  chain descriptions:", desc2)
    print("  ORF9b interface residues (contact TOM70):", short_labels(res2))
    for r in res2:
        print(f"    {r['resname']}{r['seqid']}  min_dist={r['min_dist']}A")
