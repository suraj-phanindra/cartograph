"""Freeze the held-out edge split. THIS IS THE LOCKED EVALUATOR'S GROUND TRUTH.

Run once; the output `heldout.frozen.json` is committed BEFORE any prediction
code and is never touched again by the graph, predictor, or reasoning layers.
The reasoning agents cannot import this module or read the frozen file. That is
the Darwin-Godel anti-objective-hacking property, made concrete: an evaluator the
optimizer can edit gets gamed.

Protocol (fully disclosed, so a skeptic can reproduce it):
  1. Take all 332 high-confidence Gordon viral->host edges.
  2. Sort them (stable, hash-independent) and draw a seeded random 17% sample.
     That sample is the held-out set: hidden from the predictor, revealed only
     when scoring.
  3. Pin the flagship walkthrough edge Orf6-RAE1 into the held-out set so the
     narrated demo edge is genuinely hidden. This is DISCLOSED; the evaluator
     reports precision both including and excluding pinned edges so pinning
     cannot quietly inflate the headline number.

Determinism: identical seed -> identical file (byte-for-byte, verified by sha256).
"""

from __future__ import annotations

import hashlib
import json
import random

from backend import config
from backend.graph.load import load_graph, known_edges


def compute_split(seed=config.HELDOUT_SEED, fraction=config.HELDOUT_FRACTION):
    g = load_graph()
    edges = sorted(known_edges(g))  # sort -> hash-independent, reproducible
    n_hold = round(len(edges) * fraction)

    rng = random.Random(seed)
    sampled = set(tuple(e) for e in rng.sample(edges, n_hold))

    pinned = set(tuple(e) for e in config.PINNED_HELDOUT)
    # verify pinned edges are real known edges before pinning
    for p in pinned:
        assert p in set(edges), f"pinned held-out edge {p} is not a known Gordon edge"

    held_out = sampled | pinned
    return {
        "seed": seed,
        "fraction": fraction,
        "n_known_edges": len(edges),
        "n_random_sampled": len(sampled),
        "n_held_out": len(held_out),
        "held_out": sorted([list(e) for e in held_out]),
        "pinned_walkthrough": sorted([list(e) for e in pinned]),
        "random_sampled": sorted([list(e) for e in sampled]),
        "protocol": (
            "seeded random {:.0%} sample of the 332 HC Gordon viral->host edges, "
            "plus disclosed pinned walkthrough edge(s). Precision reported with and "
            "without pinned edges."
        ).format(fraction),
        "source": "evidence/gordon2020_edges.csv (IntAct IM-27814, Gordon 2020 PMID 32353859)",
    }


def _canonical_json(split: dict) -> str:
    return json.dumps(split, indent=2, sort_keys=True)


def sha256_of(split: dict) -> str:
    return hashlib.sha256(_canonical_json(split).encode("utf-8")).hexdigest()


def freeze(force=False):
    """Write the frozen split file. Idempotent: refuses to change a committed
    split unless force=True, so predictions can never silently move the target."""
    split = compute_split()
    split["sha256"] = sha256_of(split)
    payload = _canonical_json(split)

    path = config.HELDOUT_FROZEN
    if path.exists() and not force:
        existing = json.loads(path.read_text())
        # recompute checksum over the same fields (drop stored sha256)
        recomputed = {k: v for k, v in existing.items() if k != "sha256"}
        if sha256_of(recomputed) == split["sha256"]:
            return split, "unchanged"
        return existing, "MISMATCH (existing frozen split differs; not overwriting without force)"

    path.write_text(payload)
    return split, "written"


def load_frozen():
    """Load the committed held-out set. Verifies integrity via sha256."""
    split = json.loads(config.HELDOUT_FROZEN.read_text())
    stored = split.get("sha256", "")
    recomputed = sha256_of({k: v for k, v in split.items() if k != "sha256"})
    assert stored == recomputed, "frozen split checksum mismatch — file was tampered with"
    return split


if __name__ == "__main__":
    split, status = freeze()
    print(f"frozen split: {status}")
    print(f"  seed={split['seed']} fraction={split['fraction']}")
    print(f"  {split['n_random_sampled']} random + {len(split['pinned_walkthrough'])} pinned "
          f"= {split['n_held_out']} held out of {split['n_known_edges']}")
    print(f"  sha256={split['sha256'][:16]}...")
    print(f"  flagship Orf6-RAE1 held out: {['Orf6','RAE1'] in split['held_out']}")
    # determinism check
    again = compute_split()
    again["sha256"] = sha256_of(again)
    assert again["sha256"] == split["sha256"], "NON-DETERMINISTIC split!"
    print("  determinism check: PASS (identical sha256 on recompute)")
