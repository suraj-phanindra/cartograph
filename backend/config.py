"""Single source of truth for every reproducibility-critical constant.

Kept in one file so the evaluator, the graph build, and the exported artifact all
agree. Nothing here is invented at runtime; changing a value here changes the
frozen split or the enrichment and therefore the headline number, so treat it as
part of the committed record.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- paths -----------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "evidence"
FRONTEND_DATA_DIR = REPO_ROOT / "frontend" / "data"

EDGES_CSV = EVIDENCE_DIR / "gordon2020_edges.csv"
DOMAIN_JSON = EVIDENCE_DIR / "cartograph_domain.json"
EDGE_PACKS_DIR = EVIDENCE_DIR / "edge_packs"
STRING_CACHE = EVIDENCE_DIR / "string_enrichment.cached.json"
HELDOUT_FROZEN = REPO_ROOT / "backend" / "eval" / "heldout.frozen.json"

# --- ground-truth canonical numbers (asserted at load) ---------------------
N_EDGES = 332
N_BAITS = 26
N_PREYS = 332

# --- evaluator: the locked, frozen held-out split --------------------------
# Seed is fixed and committed. See backend/eval/freeze_split.py for the exact,
# disclosed protocol (including the pinned walkthrough edge and why).
HELDOUT_SEED = 42
HELDOUT_FRACTION = 0.17  # ~17% of high-confidence viral->host edges
# The flagship walkthrough edge is pinned into the held-out set so the narrated
# demo edge is genuinely hidden from the predictor. This is DISCLOSED on screen
# and precision is reported both including and excluding pinned edges.
PINNED_HELDOUT = [("Orf6", "RAE1")]

# precision@k / recall@k reporting cutoffs
EVAL_K_VALUES = [10, 20, 50]
HEADLINE_K = 20

# --- STRING enrichment (pinned for reproducibility) ------------------------
STRING_VERSION = "12.0"
STRING_SPECIES = 9606  # Homo sapiens
STRING_NETWORK_TYPE = "physical"  # physical subnetwork, NOT text-mining
STRING_REQUIRED_SCORE = 700  # high-confidence (0-1000 scale)
STRING_API = "https://version-12-0.string-db.org/api"

# --- literature / NCBI -----------------------------------------------------
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")  # optional; raises rate limit

# --- demo edges to pre-cache (the 3-minute path) ---------------------------
# Edges whose dossiers must render offline during the demo.
DEMO_EDGES = ["Orf6|RAE1", "Orf9b|TOMM70", "N|G3BP1", "Orf6|NUP98"]

# The genuine length-3 flagship recovery path (verified: all edges exist once
# STRING enrichment is added). NEVER collapse to the 2-edge L2 shortcut.
FLAGSHIP_PATH = ["Orf6", "NUP98", "NUP214", "RAE1"]
FLAGSHIP_HELDOUT_EDGE = ("Orf6", "RAE1")
