# PRD: Cartograph Evidence Agent

Live, verified, cited dossiers for arbitrary uploaded edges. API-mode only; the
offline demo (baked artifact) and the locked benchmark/frozen split are untouched.

## Core principle
The agent may only say what a retrieved document says. Retrieval is deterministic
tooling; Claude reads and explains; a **deterministic code gate (Stage 4)** — not a
prompt — enforces that every citation is real, resolvable, and from the closed set
actually retrieved. That gate is the anti-hallucination guarantee.

## Runtime-Claude decision
There is no existing Anthropic integration. The three LLM stages (Reader, Skeptic,
Reviewer) are added as an **injectable** interface (`backend/agent/llm.py`), backed
by the Anthropic API when `ANTHROPIC_API_KEY` is set, and **degrading honestly** to
"reasoning layer not configured → topology only" when it is not. The deterministic
backbone (resolve, retrieve, **verify**, emit) and all honesty guarantees work and
are fully tested WITHOUT a key. Tests inject deterministic stand-in stages.

## Modules (`backend/agent/`)
- `resolve.py` — Stage 0: gene symbol → UniProt accession (reviewed, human) →
  Ensembl gene id via UniProt REST. Fail closed on ambiguity/none.
- `retrieve.py` — Stage 1: NCBI E-utilities (esearch co-mention + per-protein,
  efetch abstracts, PMC OA where available), RCSB Search (entries with BOTH
  accessions) → coords → interface residues (reuse the ≤3.0 Å heavy-atom method),
  AlphaFold DB monomer fallback (pLDDT, no invented residues), Open Targets
  (reuse service). Everything cached with `{query, source, fetched_at}`.
- `llm.py` — thin Anthropic client; `available()`; honest-degrade.
- `reader.py` — Stage 2 (injectable): corpus + closed PMID set → `[{clause, pmid}]`,
  confidence, proposed experiment, or "no mechanism supported by retrieved literature".
- `skeptic.py` — Stage 3 (injectable): disconfirming retrieval + the 5 AP-MS
  FP patterns from `evidence/cartograph_domain.json` → pass/downgrade/veto + reason.
- `verify.py` — **Stage 4 (deterministic gate)**: per clause — (a) PMID in the
  retrieved closed set, (b) resolves via esummary, (c) esummary title matches the
  retrieved record; drop on any failure. Structure: PDB id resolves AND contains
  both accessions, else reject. Resolvers are injectable for adversarial tests.
- `reviewer.py` — Stage 5 (injectable): sees dossier + corpus + verify report;
  returns ONLY `{drop: [clause_id], flags: [...]}` — structurally cannot add text.
- `pipeline.py` — orchestrates 0→6, streams stage events, caches, assembles the
  dossier in the exact shape the frontend `openDossier` consumes.
- `cache.py` — cache by `(edge, evidence_version)`; export to an offline artifact.

## Endpoints (API server)
- Extend `GET /api/stream?edge=BAIT|PREY`: demo edge → existing cached replay;
  uploaded edge → run the agent live, stream stage events
  (`resolving → retrieving(n) → reading → skeptic → verifying → reviewed → dossier`).
- `POST /api/evidence` (optional background): run + cache for the top-N by L3.
- `GET /api/evidence/export`: dump the cache as an offline-able artifact.

## Honest scope for arbitrary organisms
Literature/structure/druggability/novelty/Skeptic are organism-agnostic. Conservation
and CRISPR are coronavirus-specific reference data → for a non-coronavirus upload they
render **"not applicable — no reference data for this organism"**, never a blank.

## Guardrails (non-negotiable)
- Offline demo path + baked artifact untouched; agent is API-mode only.
- Locked benchmark + frozen split untouched.
- No fabricated citation/structure/residue/drug/mechanism — enforced by Stage 4 in code.
- Every network dependency degrades honestly to topology-only with a stated reason.

## Tests
- Stage 4 adversarial unit tests (deterministic, no key): non-retrieved PMID dropped;
  non-resolving PMID dropped; title mismatch dropped; structure lacking both
  accessions rejected; no-clauses → topology-only.
- Reviewer cannot inject text (structural: it returns only drop ids).
- Integration: upload a small non-coronavirus edge list → resolve + retrieve live,
  inject a deterministic Reader citing a REAL retrieved PMID → a real dossier renders
  with a resolvable citation; conservation/CRISPR read "not applicable".
- Offline demo artifact + locked benchmark byte-identical/unchanged. Stage 0 green.

## Fresh red-team
Separate from the pipeline's own Skeptic/Reviewer: try to force fabrication
(ambiguous symbol, zero-literature pair, review-only co-mention, mid-run network
failure); confirm honest degradation and that the reviewer cannot add claims.
