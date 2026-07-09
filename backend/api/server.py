"""FastAPI + SSE wrapper over the deterministic engine.

Turns evaluate() / l3_scores() / read_edge() into real endpoints and adds the
bring-your-own-interactome upload. The static offline artifact remains the
guaranteed demo fallback: this server ADDS a live path, it does not replace it.

Non-negotiables enforced here:
  - The locked Gordon benchmark is never touched. Uploaded networks get their OWN
    optional held-out eval, computed inline with a separate seed; the frozen split
    in backend/eval/ is never imported by the upload path.
  - No fabrication: uploaded edges have no cached evidence, so the API returns
    topology only and the UI says 'no cached evidence' rather than inventing one.
"""

from __future__ import annotations

import json
import random
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import networkx as nx

from backend import config
from backend.graph.enrich import enriched_graph, _fetch_string_network
from backend.predict.l3 import l3_scores, rank_of
from backend.eval.evaluator import evaluate
from backend.reason.hypothesis import read_edge, EDGE_TO_PACK

app = FastAPI(title="Cartograph API", version="1.0")

# --- upload safety limits (trust boundary) ---------------------------------
GENE_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,40}$")
MAX_EDGES = 2000
MAX_NODES = 1200
UPLOAD_SEED = 1234  # a SEPARATE seed; never the locked benchmark's seed


# ---------------------------------------------------------------------------
# read-only wrappers over the engine (the static artifact mirrors these)
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"ok": True, "string_version": config.STRING_VERSION}


class PredictReq(BaseModel):
    node: str


@app.post("/api/predict")
def predict(req: PredictReq):
    g = enriched_graph()
    if req.node not in g:
        raise HTTPException(404, f"node '{req.node}' not in the interactome")
    ranked = l3_scores(g, req.node)[:25]
    return {"node": req.node, "candidates": ranked}


@app.get("/api/dossier")
def dossier(edge: str):
    if edge not in EDGE_TO_PACK:
        raise HTTPException(404, f"no cached dossier for '{edge}'")
    return read_edge(edge)


@app.post("/api/eval/run")
def eval_run():
    r = evaluate()
    return {"metrics": r["metrics"]}


@app.get("/api/stream")
def stream(edge: str):
    """SSE: stream the cached, cited reasoning for an edge, clause by clause, so a
    client can render 'Claude reasoning' progressively. Cited, never fabricated."""
    if edge not in EDGE_TO_PACK:
        raise HTTPException(404, f"no cached dossier for '{edge}'")
    r = read_edge(edge)

    def gen():
        yield f"event: start\ndata: {json.dumps({'edge': edge})}\n\n"
        for cl in r["mechanism"]:
            yield f"event: clause\ndata: {json.dumps(cl)}\n\n"
        yield f"event: citations\ndata: {json.dumps(r['citations'])}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# bring-your-own-interactome upload
# ---------------------------------------------------------------------------
class UploadReq(BaseModel):
    edges: str
    heldout_fraction: float = 0.0


def _parse_edges(text: str):
    edges = []
    nodes = set()
    for i, raw in enumerate(text.strip().splitlines()):
        line = raw.strip()
        if not line:
            continue
        parts = [p.strip() for p in re.split(r"[,\t]", line)]
        if len(parts) < 2:
            continue
        a, b = parts[0], parts[1]
        if i == 0 and a.lower() in ("bait", "source", "protein1") and b.lower() in ("prey", "target", "protein2"):
            continue  # header row
        if not GENE_RE.match(a) or not GENE_RE.match(b):
            raise HTTPException(400, f"invalid gene name on line {i+1}: {a!r} or {b!r} "
                                     f"(allowed: letters, digits, _ . - ; max 40 chars)")
        if a == b:
            continue
        edges.append((a, b))
        nodes.update((a, b))
        if len(edges) > MAX_EDGES:
            raise HTTPException(400, f"too many edges (> {MAX_EDGES})")
        if len(nodes) > MAX_NODES:
            raise HTTPException(400, f"too many nodes (> {MAX_NODES})")
    if not edges:
        raise HTTPException(400, "no valid 'bait,prey' edges found")
    return edges


def _build_uploaded_graph(edges):
    """Bait = any node in column 1 (viral); the rest are prey (human). Mirrors the
    Gordon bipartite structure so L3 predicts bait->prey edges."""
    baits = {a for a, _ in edges}
    g = nx.Graph()
    for a, b in edges:
        for n in (a, b):
            if n not in g:
                g.add_node(n, type="viral" if n in baits else "human", uniprot="", annotations=[])
        g.add_edge(a, b, kind="known", score=1.0, evidence_ref="upload")
    return g, baits


def _enrich_uploaded(g):
    """STRING-enrich among the uploaded human prey (live call; pinned params)."""
    prey = [n for n, d in g.nodes(data=True) if d["type"] == "human"]
    if not prey:
        return 0
    try:
        raw = _fetch_string_network(prey)
    except Exception as e:  # network/STRING failure — honest, not fatal
        g.graph["enrich_error"] = str(e)
        return 0
    present = {n.upper(): n for n in g.nodes}
    added = 0
    for e in raw:
        na, nb = present.get(e["a"].upper()), present.get(e["b"].upper())
        if na and nb and na != nb and not g.has_edge(na, nb):
            g.add_edge(na, nb, kind="enrichment", score=e["score"] / 1000.0, evidence_ref="string_v12")
            added += 1
    return added


def _own_eval(g, baits, fraction):
    """The user's OWN held-out eval on THEIR network. Separate seed; the locked
    Gordon benchmark is never involved."""
    known = sorted((u, v) if u in baits else (v, u)
                   for u, v, d in g.edges(data=True) if d["kind"] == "known")
    k = round(len(known) * fraction)
    if k < 1:
        return None
    held = set(random.Random(UPLOAD_SEED).sample(known, k))
    train = g.copy()
    for a, b in held:
        if train.has_edge(a, b):
            train.remove_edge(a, b)
    # global ranked predictions, precision@k
    proposals = []
    for bait in sorted(baits):
        for c in l3_scores(train, bait):
            proposals.append((bait, c["candidate"], c["l3_score"]))
    proposals.sort(key=lambda p: -p[2])
    kk = min(20, len(held))
    hits = sum(1 for (b, p, _) in proposals[:kk] if (b, p) in held)
    return {"k": kk, "precision": round(hits / kk, 4) if kk else 0.0,
            "n_heldout": len(held), "seed": UPLOAD_SEED}


@app.post("/api/upload")
def upload(req: UploadReq):
    frac = max(0.0, min(0.5, req.heldout_fraction or 0.0))
    edges = _parse_edges(req.edges)
    g, baits = _build_uploaded_graph(edges)
    n_enrich = _enrich_uploaded(g)

    ev = _own_eval(g, baits, frac) if frac > 0 else None

    # top L3 predictions across the uploaded baits (topology only, no evidence)
    preds = []
    for bait in sorted(baits):
        for c in l3_scores(g, bait)[:10]:
            preds.append({"bait": bait, "prey": c["candidate"], "l3_score": c["l3_score"],
                          "path": c["paths"][0] if c["paths"] else None})
    preds.sort(key=lambda p: -p["l3_score"])

    return {
        "n_baits": len(baits),
        "n_prey": sum(1 for _, d in g.nodes(data=True) if d["type"] == "human"),
        "n_edges": g.number_of_edges() - n_enrich,
        "n_enrichment": n_enrich,
        "enrich_error": g.graph.get("enrich_error"),
        "predictions": preds[:25],
        "eval": ev,
        "note": "Topology only. No cached evidence for uploaded edges; Cartograph will not "
                "fabricate a mechanism, structure, or citation. Not added to the locked benchmark.",
    }


# --- serve the static frontend from the same origin (so /api/* is same-site) --
app.mount("/", StaticFiles(directory=str(config.REPO_ROOT / "frontend"), html=True), name="frontend")


@app.exception_handler(HTTPException)
async def _http_exc(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
