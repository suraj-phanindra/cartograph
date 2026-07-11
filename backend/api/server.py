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

import logging
import json
import random
import re
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import networkx as nx

import requests

from backend import config
from backend.graph.enrich import enriched_graph, _fetch_string_network
from backend.predict.l3 import l3_scores, rank_of
from backend.eval.evaluator import evaluate
from backend.reason.hypothesis import read_edge, EDGE_TO_PACK
from backend.druggability import service as drug_service
from backend.structure import cofold

log = logging.getLogger("cartograph.api")
app = FastAPI(title="Cartograph API", version="1.0")

# --- upload safety limits (trust boundary) ---------------------------------
GENE_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,40}$")
MAX_EDGES = 2000
MAX_NODES = 1200
MAX_BODY = 2_000_000          # bytes; reject oversized requests before reading them
MAX_STRING_PREY = 600         # cap identifiers sent to STRING
MAX_ENRICH_EDGES = 8000       # cap enrichment edges added to an uploaded graph
UPLOAD_SEED = 1234            # a SEPARATE seed; never the locked benchmark's seed
MAX_MATRIX_PROTEINS = 400     # cap proteins in a pooled-AF3 ipTM matrix
MAX_LENGTH_LOOKUPS = 150      # cap UniProt length lookups per screen (be polite)
_length_cache = {}
_upload_gate = threading.Semaphore(2)  # bound concurrent uploads (worker exhaustion)


class _NoDotfiles(StaticFiles):
    """StaticFiles that 404s dotfiles/dot-directories so stray files like
    frontend/.datum/ are never served."""
    def lookup_path(self, path):
        if any(seg.startswith(".") for seg in str(path).split("/")):
            return "", None
        return super().lookup_path(path)


@app.middleware("http")
async def _guards(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_BODY:
        return JSONResponse(status_code=413, content={"detail": "request body too large"})
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


# ---------------------------------------------------------------------------
# read-only wrappers over the engine (the static artifact mirrors these)
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"ok": True, "mode": "online", "string_version": config.STRING_VERSION}


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


@app.get("/api/druggability")
def druggability(gene: str, ensembl: str = None):
    """Live druggability from Open Targets (prefers the committed snapshot; only
    hits the network when a gene has no snapshot). Display-only enrichment."""
    from datetime import date
    if not GENE_RE.match(gene):
        raise HTTPException(400, "invalid gene symbol")
    if ensembl is not None and not re.match(r"^ENSG[0-9]{11}$", ensembl):
        raise HTTPException(400, "invalid Ensembl id")
    return drug_service.get(gene, ensembl, live=True, fetched=str(date.today()), timeout=15)


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
    edges: str = Field(max_length=1_000_000)  # pydantic rejects oversized before parsing
    heldout_fraction: float = 0.0


MAX_PAYLOAD = 500_000  # ~500 KB of edge-list text; bounds parse work


def _parse_edges(text: str):
    if len(text) > MAX_PAYLOAD:
        raise HTTPException(413, f"edge list too large (> {MAX_PAYLOAD} chars)")
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
            # do NOT echo the raw (rejected) token back — it failed the allowlist and
            # may contain arbitrary bytes. Report the line and the rule only.
            raise HTTPException(400, f"invalid gene name on line {i+1} "
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
    """STRING-enrich among the uploaded human prey (live call; pinned params).
    Caps prey sent and enrichment edges added. Never leaks exception detail."""
    prey = [n for n, d in g.nodes(data=True) if d["type"] == "human"][:MAX_STRING_PREY]
    if not prey:
        return 0
    try:
        raw = _fetch_string_network(prey)
    except Exception as e:  # network/STRING failure — honest, not fatal
        log.warning("STRING enrichment failed: %s", e)          # detail stays server-side
        g.graph["enrich_error"] = "enrichment unavailable (STRING request failed)"
        return 0
    present = {n.upper(): n for n in g.nodes}
    added = 0
    for e in raw:
        if added >= MAX_ENRICH_EDGES:
            break
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
    if not _upload_gate.acquire(blocking=False):
        raise HTTPException(429, "server busy; too many concurrent uploads, retry shortly")
    try:
        return _do_upload(req)
    finally:
        _upload_gate.release()


def _do_upload(req: UploadReq):
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


# ---------------------------------------------------------------------------
# pooled-AlphaFold3 score matrix upload (item 3): a virtual-screen ipTM matrix
# ---------------------------------------------------------------------------
class ScreenReq(BaseModel):
    matrix: str = Field(max_length=1_500_000)
    threshold: float = 0.55


def _parse_matrix(text):
    """Parse a symmetric protein x protein ipTM matrix (CSV/TSV): header row of
    protein names, each row = name + N ipTM values. Returns (proteins, pairs) where
    pairs are the upper-triangle (a, b, iptm) with a != b."""
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) < 2:
        raise HTTPException(400, "matrix needs a header row of protein names and >=1 data row")
    header = [c.strip() for c in re.split(r"[,\t]", lines[0])]
    first_data = [c.strip() for c in re.split(r"[,\t]", lines[1])]
    # a header with the same width as a data row has a corner cell (drop it);
    # a header one narrower is just the protein names.
    if len(header) == len(first_data):
        names = header[1:]
    elif len(header) == len(first_data) - 1:
        names = header
    else:
        names = header[1:] if len(header) > 1 else header
    for n in names:
        if not GENE_RE.match(n):
            raise HTTPException(400, f"invalid protein name in header: {n!r}")
    if len(names) > MAX_MATRIX_PROTEINS:
        raise HTTPException(400, f"too many proteins (> {MAX_MATRIX_PROTEINS})")
    row_names, grid = [], []
    for ln in lines[1:]:
        cells = [c.strip() for c in re.split(r"[,\t]", ln)]
        if len(cells) < len(names) + 1:
            continue
        rn = cells[0]
        if not GENE_RE.match(rn):
            raise HTTPException(400, f"invalid protein name in row: {rn!r}")
        row_names.append(rn)
        vals = []
        for c in cells[1:len(names) + 1]:
            try:
                vals.append(float(c))
            except ValueError:
                vals.append(None)
        grid.append(vals)
    idx = {n: i for i, n in enumerate(names)}
    pairs, seen = [], set()
    for ri, rn in enumerate(row_names):
        for ci, cn in enumerate(names):
            if rn == cn:
                continue
            v = grid[ri][ci]
            if v is None:
                continue
            key = tuple(sorted((rn, cn)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append((key[0], key[1], v))
    if not pairs:
        raise HTTPException(400, "no valid off-diagonal ipTM values found")
    return names, pairs


def _resolve_lengths(proteins):
    """Best-effort human-protein lengths from UniProt (for size-correction). Cached;
    capped; failures are tolerated (that pair simply is not size-corrected)."""
    out = {}
    todo = [p for p in proteins if p not in _length_cache][:MAX_LENGTH_LOOKUPS]
    for gene in todo:
        try:
            r = requests.get("https://rest.uniprot.org/uniprotkb/search",
                             params={"query": f"gene_exact:{gene} AND organism_id:9606 AND reviewed:true",
                                     "fields": "length", "format": "tsv", "size": 1}, timeout=8)
            rows = r.text.strip().splitlines()
            _length_cache[gene] = int(rows[1]) if len(rows) > 1 and rows[1].strip().isdigit() else None
        except Exception:
            _length_cache[gene] = None
    for p in proteins:
        if _length_cache.get(p):
            out[p] = _length_cache[p]
    return out


@app.post("/api/screen")
def screen(req: ScreenReq):
    """Triage a pooled-AlphaFold3 virtual screen: size-correct the ipTM matrix,
    threshold to candidate edges, band, and run the topology (L3) channel on the
    thresholded network. Display-only; never touches the locked benchmark."""
    if not _upload_gate.acquire(blocking=False):
        raise HTTPException(429, "server busy; retry shortly")
    try:
        thr = max(0.0, min(1.0, req.threshold if req.threshold is not None else 0.55))
        proteins, pairs = _parse_matrix(req.matrix)
        lengths = _resolve_lengths(proteins)
        rows = [{"a": a, "b": b, "iptm": round(v, 4),
                 "summed_len": (lengths.get(a, 0) + lengths.get(b, 0)) or None} for a, b, v in pairs]
        cofold.size_correct(rows)
        any_corrected = any(r["size_corrected"] for r in rows)
        for r in rows:
            eff = r["iptm_size_corrected"] if r["size_corrected"] else r["iptm"]
            r["effective"] = eff
            r["band"] = cofold.band_iptm(eff)["band"]
        kept = sorted([r for r in rows if (r["effective"] or 0) >= thr], key=lambda r: -(r["effective"] or 0))

        # topology channel: L3 on the thresholded network -> edges the folds may have
        # missed but topology proposes (the complementary signal).
        g = nx.Graph()
        for r in kept:
            for n in (r["a"], r["b"]):
                if n not in g:
                    g.add_node(n, type="human", uniprot="", annotations=[])
            g.add_edge(r["a"], r["b"], kind="known", score=r["effective"], evidence_ref="pooled_af3")
        l3_props = []
        for node in sorted(g.nodes)[:60]:
            for c in l3_scores(g, node)[:3]:
                l3_props.append({"a": node, "b": c["candidate"], "l3_score": c["l3_score"],
                                 "path": c["paths"][0] if c["paths"] else None})
        seen = set(); uniq = []
        for p in sorted(l3_props, key=lambda x: -x["l3_score"]):
            k = tuple(sorted((p["a"], p["b"])))
            if k in seen or g.has_edge(p["a"], p["b"]):
                continue
            seen.add(k); uniq.append(p)

        return {
            "source": "virtual screen (pooled-AlphaFold3)",
            "n_proteins": len(proteins), "n_pairs": len(pairs), "n_kept": len(kept),
            "threshold": thr, "size_corrected": any_corrected,
            "n_lengths_resolved": len(lengths),
            "top": kept[:30], "l3_proposals": uniq[:15],
            "note": ("ipTM is size-corrected (de-trended vs summed chain length) where lengths "
                     "resolved, banded, and labelled predicted. No cached evidence for these edges; "
                     "no mechanism/citation is invented. Not added to the locked benchmark."),
        }
    finally:
        _upload_gate.release()


# --- serve the static frontend from the same origin (so /api/* is same-site) --
# _NoDotfiles 404s any dotfile/dot-dir so stray internal files are never exposed.
app.mount("/", _NoDotfiles(directory=str(config.REPO_ROOT / "frontend"), html=True), name="frontend")


@app.exception_handler(HTTPException)
async def _http_exc(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
