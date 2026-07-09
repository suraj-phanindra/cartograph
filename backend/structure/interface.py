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


def interface_residues(cif_path, chain_a_desc, chain_b_desc, cutoff=CONTACT_CUTOFF):
    """Interface residues on the polymer matching chain_a_desc that contact any
    polymer matching chain_b_desc, matched by mmCIF entity description via the
    label_asym (subchain) id. Returns (residue_dicts, subchain_desc_map)."""
    st = gemmi.read_structure(str(cif_path))
    st.setup_entities()
    model = st[0]
    sub_desc = _subchain_descriptions(cif_path)

    a_subs = {s for s, d in sub_desc.items() if _match(d, chain_a_desc)}
    b_subs = {s for s, d in sub_desc.items() if _match(d, chain_b_desc)}

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
    return (
        [{"resname": r, "seqid": s, "min_dist": round(hits[(r, s)], 2)} for r, s in out],
        sub_desc,
    )


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
