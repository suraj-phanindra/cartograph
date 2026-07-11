"""Structural channel + novelty grounding — the honesty-critical paths the
red-team flagged as untested. Pure functions, no network.
"""
import json

from backend import config
from backend.structure import cofold
from backend.reason import novelty


# --- ipTM banding (AF3 calibration) ----------------------------------------
def test_band_iptm_boundaries():
    assert cofold.band_iptm(0.85)["band"] == "highly confident"
    assert cofold.band_iptm(0.60)["band"] == "confident"
    assert cofold.band_iptm(0.55)["band"] == "weak"
    assert cofold.band_iptm(0.54)["band"] == "no better than random"
    assert cofold.band_iptm(None)["band"] == "n/a"


# --- size-correction --------------------------------------------------------
def test_size_correct_needs_three_points():
    rows = [{"iptm": 0.9, "summed_len": 800}, {"iptm": 0.5, "summed_len": 400}]
    cofold.size_correct(rows)
    assert all(r["size_corrected"] is False for r in rows)
    assert all(r["iptm_size_corrected"] == r["iptm"] for r in rows)


def test_size_correct_detrends_length():
    # ipTM rises purely with length -> de-trend should flatten toward the mean
    rows = [{"iptm": 0.60, "summed_len": 300}, {"iptm": 0.70, "summed_len": 600},
            {"iptm": 0.80, "summed_len": 900}, {"iptm": 0.90, "summed_len": 1200}]
    cofold.size_correct(rows)
    assert all(r["size_corrected"] for r in rows)
    corrected = [r["iptm_size_corrected"] for r in rows]
    # a perfect linear length trend collapses to the mean ipTM (0.75) for all
    assert max(corrected) - min(corrected) < 0.02


def test_size_correct_skips_pair_with_unresolved_length():
    # the red-team MAJOR: a pair missing a length must NOT be corrected, and must
    # never receive a fabricated summed_len upstream. Here summed_len is None.
    rows = [{"iptm": 0.60, "summed_len": 300}, {"iptm": 0.70, "summed_len": 600},
            {"iptm": 0.80, "summed_len": 900}, {"iptm": 0.65, "summed_len": None}]
    cofold.size_correct(rows)
    unresolved = rows[-1]
    assert unresolved["size_corrected"] is False
    assert unresolved["iptm_size_corrected"] == 0.65        # left as raw, not invented
    # the three resolved rows still corrected among themselves
    assert all(r["size_corrected"] for r in rows[:3])


# --- novelty grounding ------------------------------------------------------
def test_novelty_never_confident_without_a_real_signal():
    cache = {"A|B": 0, "C|D": 4}
    # missing count -> unassessed, NEVER guessed novel/known
    assert novelty.classify("X", "Y", False, False, cache)["tag"] == "unassessed"
    # 0 co-mentions -> novel; >=1 -> partially known
    assert novelty.classify("A", "B", False, False, cache)["tag"] == "novel"
    assert novelty.classify("C", "D", False, False, cache)["tag"] == "partially known"
    # ground-truth / dossier short-circuit to known before any cache lookup
    assert novelty.classify("X", "Y", True, False, cache)["tag"] == "known"
    assert novelty.classify("X", "Y", False, True, cache)["tag"] == "known"
    # basis always names the real source
    assert "co-mention" in novelty.classify("A", "B", False, False, cache)["basis"]


# --- artifact invariant: no inflated aggregate structural gain --------------
def test_artifact_structure_channel_is_honest():
    art = json.loads((config.REPO_ROOT / "frontend" / "data" / "cartograph_computed.json").read_text())
    sc = art["eval"]["structure_channel"]
    # the honest aggregate, excluding the self-referential pinned flagship, is flat
    assert sc["aggregate_gain_excl_pinned"] == 0.0
    assert sc["l3_only_excl_pinned_p20"] == sc["l3_plus_structure_excl_pinned_p20"]
    # the with-pinned number is disclosed in its key name, not headline-able
    assert "with_pinned_disclosed" in json.dumps(sc)
    # baseline never moved
    assert art["eval"]["baseline"]["precision_at_k"]["20"] == 0.45
