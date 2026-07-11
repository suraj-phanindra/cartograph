"""Structural-evidence channel: a second, orthogonal signal to topology.

The thesis (Silas/Todor pooled-AlphaFold3; network-topology + AF-Multimer papers):
degree-normalized L3 proposes an edge; a co-fold interface confidence corroborates
it; a candidate strong on BOTH is a real lead. This module turns interface
confidence into a calibrated, size-corrected, honestly-labelled signal.

Honesty (non-negotiable):
  - We do NOT run AlphaFold3/Boltz-2 (no GPU) and never fabricate an ipTM. Values
    come only from real sources: a deposited experimental complex (the strongest
    evidence — labelled experimental, not predicted), a committed pre-computed
    co-fold file, or the user's uploaded pooled-AF3 matrix.
  - ipTM is always BANDED (calibration from AF3 benchmarking: >0.80 highly
    confident, 0.60-0.80 confident, 0.55-0.60 weak, <0.55 no better than random)
    and SIZE-CORRECTED (ipTM correlates with summed chain length; correct before
    ranking), and labelled predicted.
"""

from __future__ import annotations


# --- ipTM calibration bands (AF3 benchmarking, Briefings in Bioinformatics 2025)
def band_iptm(iptm):
    if iptm is None:
        return {"band": "n/a", "tier": 0, "label": "no model"}
    if iptm >= 0.80:
        return {"band": "highly confident", "tier": 3, "label": "ipTM ≥ 0.80"}
    if iptm >= 0.60:
        return {"band": "confident", "tier": 2, "label": "ipTM 0.60–0.80"}
    if iptm >= 0.55:
        return {"band": "weak", "tier": 1, "label": "ipTM 0.55–0.60"}
    return {"band": "no better than random", "tier": 0, "label": "ipTM < 0.55"}


def size_correct(rows):
    """Size-correct a set of ipTM values against summed chain length.

    ipTM rises with the summed size of the pair (Silas session caveat), so a raw
    ranking favours big proteins. We de-trend: fit iptm ~ a + b*(L_a+L_b) by least
    squares across the provided rows and return the residual re-centred on the mean
    ipTM. This is meaningful only at scale (a matrix); with <3 points we cannot fit
    and return the raw value flagged uncorrected.

    rows: list of dicts each with 'iptm' (float) and 'summed_len' (int).
    Adds 'iptm_size_corrected' and 'size_corrected' (bool) to each row (in place).
    """
    pts = [(r["summed_len"], r["iptm"]) for r in rows
           if r.get("iptm") is not None and r.get("summed_len")]
    if len(pts) < 3:
        for r in rows:
            r["iptm_size_corrected"] = r.get("iptm")
            r["size_corrected"] = False
        return rows
    n = len(pts)
    sx = sum(x for x, _ in pts); sy = sum(y for _, y in pts)
    sxx = sum(x * x for x, _ in pts); sxy = sum(x * y for x, y in pts)
    denom = (n * sxx - sx * sx) or 1e-9
    b = (n * sxy - sx * sy) / denom          # slope
    a = (sy - b * sx) / n                     # intercept
    mean_y = sy / n
    for r in rows:
        if r.get("iptm") is not None and r.get("summed_len"):
            resid = r["iptm"] - (a + b * r["summed_len"])
            r["iptm_size_corrected"] = round(mean_y + resid, 4)
            r["size_corrected"] = True
        else:
            r["iptm_size_corrected"] = r.get("iptm")
            r["size_corrected"] = False
    return rows


# --- structural evidence per demo edge (from structure_facts, real) ---------
def structural_block(edge, structure_facts, interface_counts=None):
    """Build the dossier's in-silico-validation block for a demo edge from the
    already-computed structure_facts. Experimental complexes are the strongest
    evidence (labelled experimental, not predicted); a predicted monomer is
    labelled as such with no complex ipTM; anything else is honestly 'no co-fold'."""
    st = structure_facts.get(edge)
    if st and st.get("kind") == "experimental":
        ncontacts = (interface_counts or {}).get(edge)
        return {
            "provenance": "experimental",
            "band": "experimental",
            "tier": 4,
            "label": f"experimental complex ({st['source']})",
            "iptm": None,
            "method": st.get("method"),
            "resolution_A": st.get("resolution_A"),
            "interface_contacts": ncontacts,
            "predicted": False,
            "note": "Structurally resolved — the pair is observed in contact, stronger "
                    "than a predicted co-fold.",
        }
    if st and st.get("kind") == "predicted":
        c = st.get("confidence", {})
        return {
            "provenance": "predicted-monomer",
            "band": "monomer model",
            "tier": 1,
            "label": f"{st['source']} · {c.get('type','pLDDT')} {c.get('value')}",
            "iptm": None,
            "predicted": True,
            "note": "Predicted monomer model only — no complex co-fold, so no ipTM. "
                    "Roadmap: pre-compute an AlphaFold3/Boltz-2 co-fold.",
        }
    return {
        "provenance": "none", "band": "n/a", "tier": 0, "iptm": None, "predicted": False,
        "note": "No co-fold computed. Roadmap: pre-compute an AlphaFold3/Boltz-2 model "
                "or ingest a pooled-AF3 ipTM matrix.",
    }


def structural_scores(structure_facts):
    """Evaluator boost per pair from real structural evidence. Only deposited
    experimental complexes contribute here (the demo has no committed co-folds);
    the boost is a transparent additive term the evaluator logs, never a hidden
    re-weighting. Returns {(bait, prey): boost}."""
    scores = {}
    for edge, st in structure_facts.items():
        if st.get("kind") == "experimental":
            bait, prey = edge.split("|")
            scores[(bait, prey)] = 0.5   # strong, transparent corroboration
    return scores


if __name__ == "__main__":
    for v in [0.9, 0.72, 0.57, 0.4, None]:
        print(v, "->", band_iptm(v)["band"])
    rows = [{"iptm": 0.9, "summed_len": 1200}, {"iptm": 0.6, "summed_len": 200},
            {"iptm": 0.7, "summed_len": 700}, {"iptm": 0.5, "summed_len": 150}]
    size_correct(rows)
    for r in rows:
        print(f"iptm {r['iptm']} len {r['summed_len']} -> corrected {r['iptm_size_corrected']} ({r['size_corrected']})")
