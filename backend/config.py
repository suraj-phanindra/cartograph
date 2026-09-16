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


def _load_dotenv(path=REPO_ROOT / ".env"):
    """Minimal .env loader (no dependency): KEY=VALUE lines -> os.environ, without
    overriding a variable already set in the real environment. Secrets stay in .env
    (gitignored), never in code."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv()

EDGES_CSV = EVIDENCE_DIR / "gordon2020_edges.csv"
COV1_MERS_CSV = EVIDENCE_DIR / "gordon2020_science_cov1_mers_edges.csv"  # conservation (CoV-1 + MERS only)
CRISPR_HITS = EVIDENCE_DIR / "crispr_screen_hits.json"                   # 7 genome-wide CRISPR screens
CRISPR_SCREENS = EVIDENCE_DIR / "crispr_screens.json"                    # screen provenance (pmid/cell line)
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

# --- open-world background (backend/bench) ---------------------------------
# The closed-world universe is the 332 preys already in the map, which is not the
# population the tool addresses at deployment. The open-world prevalence uses the
# reviewed human proteome. Fetched from the UniProt REST API on 2026-09-03, not
# estimated. Re-pin deliberately; a drifting background silently invalidates every
# enrichment figure.
OPEN_WORLD_BACKGROUND = 20431
OPEN_WORLD_SOURCE = ("UniProt reviewed (Swiss-Prot) human proteome, "
                     "release 2026_03 (02-September-2026)")

# --- STRING enrichment (pinned for reproducibility) ------------------------
STRING_VERSION = "12.0"
STRING_SPECIES = 9606  # Homo sapiens
STRING_NETWORK_TYPE = "physical"  # physical subnetwork, NOT text-mining
STRING_REQUIRED_SCORE = 700  # high-confidence (0-1000 scale)
STRING_API = "https://version-12-0.string-db.org/api"

# --- literature / NCBI -----------------------------------------------------
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")  # optional; raises rate limit 3->10/s

# --- Evidence Agent (API-mode only; live per-edge dossiers) ----------------
# The reasoning stages (Reader/Skeptic/Reviewer) call the Anthropic API when a key
# is present, and degrade honestly to topology-only when it is not. The
# deterministic backbone (resolve/retrieve/verify/emit) needs no key.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("CARTOGRAPH_AGENT_MODEL", "claude-opus-4-8")
# Identity-linked API keys must name the workspace the request acts in. Console
# keys do not need this, so it stays optional and the header is only sent when set.
ANTHROPIC_WORKSPACE_ID = os.environ.get("ANTHROPIC_WORKSPACE_ID", "")
AGENT_CONTACT = os.environ.get("CARTOGRAPH_CONTACT", "cartograph-evidence-agent")  # tool/email etiquette
UNIPROT_API = "https://rest.uniprot.org/uniprotkb"
RCSB_SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_FILES = "https://files.rcsb.org/download"
ALPHAFOLD_API = "https://alphafold.ebi.ac.uk/api/prediction"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
AGENT_MAX_ABSTRACTS = 20        # cap papers fetched per edge
AGENT_EVIDENCE_VERSION = "1.0"  # cache key component

# --- demo edges to pre-cache (the 3-minute path) ---------------------------
# Edges whose dossiers must render offline during the demo.
DEMO_EDGES = ["Orf6|RAE1", "Orf9b|TOMM70", "N|G3BP1", "Orf6|NUP98"]

# The genuine length-3 flagship recovery path (verified: all edges exist once
# STRING enrichment is added). NEVER collapse to the 2-edge L2 shortcut.
FLAGSHIP_PATH = ["Orf6", "NUP98", "NUP214", "RAE1"]
FLAGSHIP_HELDOUT_EDGE = ("Orf6", "RAE1")
