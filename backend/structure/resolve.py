"""Resolve the structural dossier block for each demo edge.

Two honest kinds, never conflated:
  - experimental: a deposited PDB structure (7DHG, 7VPH). Interface residues are
    COMPUTED from the coordinates (backend/structure/interface.py), not copied
    from prose, so every residue shown is a real heavy-atom contact.
  - predicted: an open folding-model output (AlphaFold DB) wired into the same
    Mol* panel, always labeled predicted with its real confidence (pLDDT). Never
    presented as experimental fact.

Build time only: this stamps verified facts into the exported artifact and copies
the CIFs into frontend/data/structures/ so the demo loads them offline.
"""

from __future__ import annotations

import json
import shutil
import statistics
from pathlib import Path

import gemmi

from backend import config
from backend.structure.interface import interface_residues, short_labels

CIF_DIR = Path(__file__).parent / "cif"
FRONTEND_STRUCT_DIR = config.FRONTEND_DATA_DIR / "structures"
CORE_CUTOFF = 3.0  # tight-contact core interface, <= this many angstroms
MAX_RESIDUES = 6


def _core_residues(residues):
    core = [r for r in residues if r["min_dist"] <= CORE_CUTOFF]
    core = sorted(core, key=lambda r: r["min_dist"])[:MAX_RESIDUES]
    # present in sequence order for readability
    core = sorted(core, key=lambda r: r["seqid"])
    return short_labels(core)


def _mean_plddt(cif_path):
    st = gemmi.read_structure(str(cif_path))
    vals = [res.find_atom("CA", "*").b_iso for ch in st[0] for res in ch if res.find_atom("CA", "*")]
    return round(statistics.mean(vals), 1)


def build_structure_facts():
    """Compute every demo edge's structure block. Returns a dict keyed by
    'BAIT|PREY'. Copies CIFs to the frontend for offline loading."""
    FRONTEND_STRUCT_DIR.mkdir(parents=True, exist_ok=True)
    for cif in ["7VPH.cif", "7DHG.cif", "AF-Q13283-G3BP1.cif"]:
        shutil.copy(CIF_DIR / cif, FRONTEND_STRUCT_DIR / cif)

    facts = {}

    # --- Orf6 -> RAE1 : experimental 7VPH (ORF6 bound to Rae1-Nup98) ---------
    orf6_rae1, _ = interface_residues(CIF_DIR / "7VPH.cif", "ORF6", "mRNA export factor")
    facts["Orf6|RAE1"] = {
        "kind": "experimental",
        "source": "PDB 7VPH",
        "pdb": "7VPH",
        "url": "data/structures/7VPH.cif",
        "method": "X-ray diffraction",
        "resolution_A": 2.8,
        "confidence": {"type": "resolution", "value": 2.8, "unit": "Å (X-ray)"},
        "chains": "SARS-CoV-2 ORF6 C-terminal tail + human RAE1 + human NUP98",
        "interface_residues": _core_residues(orf6_rae1),
        "interface_source": "computed: ORF6 heavy-atom contacts with RAE1 <= 3.0 Å in PDB 7VPH",
        "note": "Experimental structure. ORF6 directly contacts RAE1 at the mRNA-export "
                "groove; the graph independently re-proposed this held-out edge and the "
                "structure confirms it.",
    }

    # --- Orf6 -> NUP98 : same experimental 7VPH (calibration, known edge) ----
    orf6_nup98, _ = interface_residues(CIF_DIR / "7VPH.cif", "ORF6", "Nup98")
    facts["Orf6|NUP98"] = {
        "kind": "experimental",
        "source": "PDB 7VPH",
        "pdb": "7VPH",
        "url": "data/structures/7VPH.cif",
        "method": "X-ray diffraction",
        "resolution_A": 2.8,
        "confidence": {"type": "resolution", "value": 2.8, "unit": "Å (X-ray)"},
        "chains": "SARS-CoV-2 ORF6 C-terminal tail + human NUP98",
        "interface_residues": _core_residues(orf6_nup98),
        "interface_source": "computed: ORF6 heavy-atom contacts with NUP98 <= 3.0 Å in PDB 7VPH",
        "note": "Experimental; known AP-MS edge shown for calibration.",
    }

    # --- Orf9b -> TOMM70 : experimental 7DHG --------------------------------
    orf9b, _ = interface_residues(CIF_DIR / "7DHG.cif", "ORF9b", "TOM70")
    facts["Orf9b|TOMM70"] = {
        "kind": "experimental",
        "source": "PDB 7DHG",
        "pdb": "7DHG",
        "url": "data/structures/7DHG.cif",
        "method": "X-ray diffraction",
        "resolution_A": 2.2,
        "confidence": {"type": "resolution", "value": 2.2, "unit": "Å (X-ray)"},
        "chains": "SARS-CoV-2 ORF9b + human TOM70 (TOMM70)",
        "interface_residues": _core_residues(orf9b),
        "interface_source": "computed: ORF9b heavy-atom contacts with TOM70 <= 3.0 Å in PDB 7DHG",
        "note": "Experimental. S53 (the phospho-regulated serine) confirmed as a real "
                "contact; the prototype's S55/K46 are NOT contacts and were repaired.",
    }

    # --- N -> G3BP1 : PREDICTED (open model), labeled predicted -------------
    plddt = _mean_plddt(CIF_DIR / "AF-Q13283-G3BP1.cif")
    facts["N|G3BP1"] = {
        "kind": "predicted",
        "source": "AlphaFold DB (AF-Q13283, G3BP1)",
        "pdb": None,
        "model_id": "AF-Q13283-F1",
        "url": "data/structures/AF-Q13283-G3BP1.cif",
        "method": "AlphaFold2 monomer (predicted)",
        "confidence": {"type": "pLDDT", "value": plddt, "unit": "mean pLDDT"},
        "chains": "human G3BP1 (predicted monomer; the N–G3BP1 complex is not deposited)",
        "interface_residues": [],  # no experimental complex -> we do NOT assert contact residues
        "interface_source": "no deposited complex; specific N-protein contact residues are not "
                            "shown (would be unverified). Binding is via the literature-verified "
                            "ITFG/ΦxFG G3BP1-binding motif.",
        "note": "PREDICTED structure of the human G3BP1 target, shown to demonstrate the "
                "predicted-vs-experimental integrity path. Not the complex; not experimental fact.",
    }

    return facts


if __name__ == "__main__":
    facts = build_structure_facts()
    for edge, f in facts.items():
        c = f["confidence"]
        print(f"{edge:14} {f['kind']:12} {f['source']:28} "
              f"{c['type']}={c['value']}{c.get('unit','')}  residues={f['interface_residues']}")
    out = config.FRONTEND_DATA_DIR / "structure_facts.json"
    out.write_text(json.dumps(facts, indent=2))
    print(f"\nwrote {out}")
