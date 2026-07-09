"""Deterministic-core tests. These guard the honesty invariants:
graph counts, frozen-split determinism, reproducible L3 ranking, evaluator
precision identical across runs, and the eval/reasoning import boundary.
"""

import ast
import importlib
from pathlib import Path

import pytest

from backend import config
from backend.graph.load import load_graph, known_edges
from backend.graph.enrich import enriched_graph
from backend.predict.l3 import l3_scores, rank_of, pick_display_path
from backend.eval.freeze_split import compute_split, sha256_of, load_frozen
from backend.eval.evaluator import evaluate


# --- graph ------------------------------------------------------------------
def test_graph_counts():
    g = load_graph()
    assert sum(1 for *_, d in g.edges(data=True) if d["kind"] == "known") == config.N_EDGES
    assert len(g.graph["baits"]) == config.N_BAITS
    assert len(g.graph["preys"]) == config.N_PREYS


def test_flagship_anchor_edges_present():
    ke = known_edges(load_graph())
    for e in [("Orf6", "RAE1"), ("Orf6", "NUP98"), ("Orf9b", "TOMM70"), ("N", "G3BP1")]:
        assert e in ke


# --- frozen split -----------------------------------------------------------
def test_frozen_split_deterministic():
    a = compute_split()
    b = compute_split()
    assert sha256_of(a) == sha256_of(b)


def test_frozen_file_integrity():
    split = load_frozen()  # asserts sha256 internally
    assert ["Orf6", "RAE1"] in split["held_out"]
    assert split["seed"] == config.HELDOUT_SEED


# --- enrichment -------------------------------------------------------------
def test_enrichment_flagship_bridges():
    g = enriched_graph()
    for a, b in [("NUP98", "NUP214"), ("NUP214", "RAE1"), ("NUP98", "RAE1")]:
        assert g.has_edge(a, b), f"missing enrichment bridge {a}-{b}"


# --- L3 ---------------------------------------------------------------------
def test_l3_reproducible():
    g = enriched_graph()
    r1 = l3_scores(g, "Orf6")
    r2 = l3_scores(g, "Orf6")
    assert [(c["candidate"], c["l3_score"]) for c in r1] == [(c["candidate"], c["l3_score"]) for c in r2]


def test_flagship_recovered_via_genuine_length3_path():
    g = enriched_graph()
    frozen = load_frozen()
    train = g.copy()
    for bait, prey in frozen["held_out"]:
        if train.has_edge(bait, prey):
            train.remove_edge(bait, prey)
    ranked = l3_scores(train, "Orf6")
    rae1 = next((c for c in ranked if c["candidate"] == "RAE1"), None)
    assert rae1 is not None, "RAE1 not recovered"
    # every recorded path is a genuine 3-edge path (all edges real)
    for p in rae1["paths"]:
        assert len(p) == 4
        assert all(train.has_edge(p[i], p[i + 1]) for i in range(3)), f"fabricated edge in {p}"
    # canonical display path is real and length-3, never the 2-edge shortcut
    disp = pick_display_path(rae1, preferred=config.FLAGSHIP_PATH)
    assert disp == config.FLAGSHIP_PATH
    assert len(disp) == 4


# --- evaluator --------------------------------------------------------------
def test_evaluator_precision_identical_across_runs():
    m1 = evaluate()["metrics"]
    m2 = evaluate()["metrics"]
    assert m1["headline_precision_at_k"] == m2["headline_precision_at_k"]
    assert m1["k"] == m2["k"]
    assert m1["roc_auc"] == m2["roc_auc"]


def test_evaluator_number_is_real_not_illustrative():
    m = evaluate()["metrics"]
    # a real computed number in (0,1), not the prototype's hard-coded 0.80
    assert 0.0 < m["headline_precision_at_k"] < 1.0
    assert m["roc_auc"] is not None and m["roc_auc"] > 0.5  # better than random


# --- the locked boundary: reasoning/predict must not import the evaluator ----
@pytest.mark.parametrize("pkg", ["backend/predict", "backend/reason"])
def test_no_import_of_locked_evaluator(pkg):
    root = config.REPO_ROOT / pkg
    for py in root.rglob("*.py"):
        tree = ast.parse(py.read_text())
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            for m in mods:
                assert "eval" not in m.split("."), (
                    f"{py} imports '{m}': the predictor/reasoning layer must not "
                    f"import the locked evaluator or read the frozen split"
                )
