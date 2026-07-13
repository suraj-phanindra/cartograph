# Cartograph — submission summary

Cartograph is a navigation layer for protein-interaction maps. It loads an
experimentally-derived interactome — the Gordon 2020 SARS-CoV-2→human AP-MS map (332
edges, 26 baits) — deterministically proposes the missing edges via degree-normalized
L3 link prediction, and has Claude read the literature and structure behind each
candidate to produce a mechanistic, cited hypothesis. A locked evaluator, frozen
before any prediction, hides real edges and measures recovery: precision@20 = 45%,
ROC-AUC = 0.845 on 57 held-out edges. In the flagship, topology re-proposes the
held-out ORF6–RAE1 edge via a genuine length-3 path, and the deposited 7VPH structure
confirms it — with the interface residues computed from the coordinates, not copied
from prose.

The core principle: the graph proposes deterministically, Claude only explains, and a
deterministic code gate — not a prompt — enforces that every citation is real,
resolvable, and from the retrieved set. That gate powers a live Evidence Agent: upload
any interactome (any organism) and get verified, cited dossiers with real structures,
fetched on demand. Nothing is fabricated; where the evidence is thin, it says so. Open
source, MIT.
