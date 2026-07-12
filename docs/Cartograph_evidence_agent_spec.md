# Cartograph Evidence Agent: live dossiers for any uploaded edge

Goal: hand Cartograph a brand-new interactome and get everything the demo dataset gets — a mechanistic dossier with real citations, a real structure, druggability, novelty, and a Skeptic verdict — fetched live, reviewed, and adversarially audited. This closes the last gap between "works on our data" and "works on yours", which is the Build-track thesis and the sharpest question a judge will ask.

Two facts that make this safe to build:
- The offline demo runs off the baked artifact, so this cannot break the demo path. It is additive, API-mode only.
- The locked benchmark lives in the artifact/evaluator, not the server, so the agent cannot touch it.

## The core design principle
The agent may only ever say what a retrieved document says. Retrieval is deterministic tooling. Claude reads and explains. A programmatic gate — not a prompt — enforces that every citation is real, resolvable, and from the closed set of documents actually retrieved. That gate is what turns "no citation, no render" from an aspiration into a guarantee.

## Pipeline (per edge, on demand, streamed)

### Stage 0 — Resolve (deterministic, no LLM)
Gene symbol -> UniProt accession -> Ensembl gene id via the UniProt REST ID-mapping service (rest.uniprot.org). Fail closed: if a symbol is ambiguous or unresolvable, mark it unresolved and stop for that edge. Never guess an identifier.

### Stage 1 — Retrieve (deterministic tools; the ONLY source of truth)
- Literature: NCBI E-utilities. esearch for the co-mention (protein A AND protein B, plus organism context), and per protein; efetch the abstracts; PMC Open Access full text where available. Record every query string and timestamp. Respect the rate limit (3 requests/sec, 10/sec with a free NCBI API key — put the key in config).
- Novelty: the co-mention hit count from the same esearch is the novelty signal (this is already the method).
- Structure: RCSB Search API — query for entries containing BOTH UniProt accessions (an AND over the polymer-entity reference accession attribute). If a real complex exists, pull coordinates from the RCSB Data API and compute interface residues as heavy-atom contacts <= 3.0 A, which is the same method already used for 7VPH and 7DHG. If no complex exists, fall back to AlphaFold DB monomers (alphafold.ebi.ac.uk/api/prediction/{accession}), labelled predicted with pLDDT, and DO NOT invent contact residues — this is exactly the honest N-G3BP1 precedent already in the product.
- Druggability: Open Targets GraphQL by Ensembl id (already built; organism-agnostic for human targets).
- Everything is cached with provenance: {query, source, fetched_at}.

### Stage 2 — Read (Claude Reader subagent)
Input: ONLY the retrieved corpus plus the structural facts. The Reader is handed a closed set of PMIDs and told it may cite only those.
Output: structured claims as [{clause, pmid}], a confidence, and a proposed wet-lab experiment.
If the corpus does not support a mechanism, the Reader must return "no mechanism supported by retrieved literature". That is a valid, expected outcome, not a failure.

### Stage 3 — Skeptic (adversarial subagent, fresh context)
Runs targeted retrieval for disconfirming evidence, applies the AP-MS false-positive patterns from evidence/cartograph_domain.json (frequent-flyer / CRAPome contaminants), and checks whether a co-mention is spurious (e.g. both proteins merely listed in one large review, with no interaction claim).
Verdict: pass / downgrade / veto, with a reason. A veto blocks the dossier.

### Stage 4 — Verify (deterministic gate — the anti-hallucination mechanism; NOT an LLM)
For every citation the Reader produced:
1. Closed-set check: the PMID must be one that was actually retrieved in Stage 1. The Reader cannot cite a paper it never saw.
2. Resolve check: the PMID must resolve via E-utilities esummary.
3. Title check: the resolved title must match the retrieved record.
Any clause whose citation fails all-or-any of these is DROPPED. Structure ids must resolve in RCSB and actually contain both accessions. If no clauses survive, no dossier renders — the edge shows topology-only with the reason.
This stage is code, not a prompt. It is the single most important component.

### Stage 5 — Final adversarial review (fresh Claude subagent)
Sees the assembled dossier, the retrieved corpus, and the Stage 4 verify report. Audits:
- Is every claim traceable to a specific retrieved paper, and does the paper actually say it (no overclaim, no causal language the source does not support)?
- Is any predicted structure presented as experimental? Any invented residue?
- Is the Skeptic's verdict reflected honestly?
Output: pass, or revise with specific findings. Critical constraint: the reviewer may only REMOVE or FLAG content. It must not be able to add a claim. Enforce that structurally (it returns a list of clause ids to drop plus flags, never new text).

### Stage 6 — Emit, cache, and make offline-able
Render with full provenance: the queries run, the papers retrieved, the Skeptic verdict, and what the reviewer dropped. Cache keyed by (edge, evidence version). Allow exporting the cache so an uploaded map can be baked into its own offline artifact, exactly like the demo dataset. This makes the curation reproducible rather than bespoke.

## UX and performance
- Do NOT run the agent on every predicted edge. Run it (a) on demand when a dossier is opened for an uploaded edge, and (b) optionally in the background for the top N (default 10) by L3 score.
- Stream the agent's progress over the existing SSE endpoint: resolving -> retrieving (n papers found) -> reading -> skeptic -> verifying -> reviewed. Show that trace in the UI. This is both good UX and an excellent demo beat: the audience watches the agent build a cited hypothesis live.
- Caps: max papers per edge (e.g. 20 abstracts), max concurrent edges, per-call timeouts, and back-off. Honour NCBI rate limits.

## Honest scope for arbitrary organisms
- Literature, structure, druggability, novelty, and the Skeptic generalise to any protein pair; these APIs are organism-agnostic.
- Conservation and CRISPR are coronavirus-specific reference data. For a non-coronavirus upload they must display "not applicable — no reference data for this organism", never a blank that implies "absent". Optionally let a user supply their own reference sets later.

## Guardrails (non-negotiable)
- The offline demo path and the baked artifact are untouched. The agent is API-mode only.
- The locked benchmark and frozen split are untouched.
- No fabricated citation, structure, residue, drug, or mechanism, enforced by Stage 4 in code.
- Every network dependency degrades honestly: on failure, show topology-only with the reason, never a guess.

---

## Claude Code prompt (paste at the repo root)

Build the Cartograph Evidence Agent: live, verified dossiers for arbitrary uploaded edges. Same autonomous loop: plan, PRD, implement, test, fresh red-team review, iterate. Do not regress the demo-critical core; run the Stage 0 regression after every change. The offline demo runs off the baked artifact and must stay untouched; this feature is API-mode only. The locked benchmark and frozen split must remain untouched.

Read first: CLAUDE.md, docs/REPORT.md, docs/Cartograph_BUILD_SPEC.md, docs/Cartograph_evidence_agent_spec.md (this spec), backend/api/server.py (the existing /api/upload and /api/screen), the existing druggability service, and evidence/cartograph_domain.json (the AP-MS false-positive patterns).

Build a per-edge evidence pipeline, invoked on demand when a dossier is opened for an uploaded edge (and optionally in the background for the top 10 by L3), streamed over the existing SSE endpoint:

STAGE 0 RESOLVE (deterministic): gene symbol -> UniProt accession -> Ensembl id via the UniProt REST ID-mapping service. Fail closed on ambiguity; never guess an id.

STAGE 1 RETRIEVE (deterministic tools only; this is the sole source of truth):
- NCBI E-utilities: esearch for the pair co-mention and per protein; efetch abstracts; PMC OA full text where available. The co-mention count is the novelty signal. Respect 3 req/s (10 with an API key — add the key to config). Record every query and timestamp.
- RCSB Search API: find entries containing BOTH UniProt accessions (AND over the polymer-entity reference accession attribute). Confirm the exact attribute name and query shape against the live docs at search.rcsb.org before coding — do not assume. If a real complex exists, pull coordinates from the RCSB Data API and compute interface residues as heavy-atom contacts <= 3.0 A (reuse the method already used for 7VPH/7DHG). If no complex exists, fall back to AlphaFold DB monomers, labelled predicted with pLDDT, and DO NOT invent contact residues (follow the existing honest N-G3BP1 precedent).
- Open Targets GraphQL for druggability (reuse the existing service).
Cache everything with {query, source, fetched_at}.

STAGE 2 READ (Claude Reader subagent): given ONLY the retrieved corpus and structural facts, and a closed set of PMIDs it may cite, produce [{clause, pmid}], a confidence, and a proposed wet-lab experiment. If the corpus supports no mechanism, it must return "no mechanism supported by retrieved literature".

STAGE 3 SKEPTIC (adversarial subagent, fresh context): run targeted retrieval for disconfirming evidence; apply the AP-MS frequent-flyer / CRAPome patterns from evidence/cartograph_domain.json; detect spurious co-mentions (both proteins merely listed in a review). Verdict pass / downgrade / veto with a reason. A veto blocks the dossier.

STAGE 4 VERIFY (deterministic code, NOT a prompt — this is the anti-hallucination gate): for every citation, assert (a) the PMID is in the closed set actually retrieved in Stage 1, (b) it resolves via esummary, and (c) the resolved title matches the retrieved record. Drop any clause that fails. Assert any PDB id resolves and truly contains both accessions. If no clauses survive, render topology-only with the reason and no dossier.

STAGE 5 FINAL ADVERSARIAL REVIEW (fresh Claude subagent): sees the assembled dossier, the corpus, and the verify report. Audits for untraceable claims, overclaim beyond the source, predicted structures shown as experimental, invented residues, and whether the Skeptic verdict is reflected. It may ONLY return clause ids to drop plus flags — enforce structurally that it cannot add new text.

STAGE 6 EMIT + CACHE: render with full provenance (queries run, papers retrieved, Skeptic verdict, clauses dropped). Cache by (edge, evidence version). Support exporting the cache so an uploaded map can be baked into its own offline artifact, the same way the demo dataset was.

Also: for a non-coronavirus upload, the conservation and CRISPR channels must show "not applicable — no reference data for this organism", never a blank implying absence.

Caps and failure: max ~20 abstracts per edge, bounded concurrency, per-call timeouts, back-off. Every network dependency degrades honestly to topology-only with a stated reason. Never a guess.

Test: unit tests for Stage 4 with adversarial fixtures — a Reader output citing a PMID that was never retrieved MUST be dropped; a PMID that does not resolve MUST be dropped; a title mismatch MUST be dropped; a structure not containing both accessions MUST be rejected. Integration test: upload a small non-coronavirus edge list and assert real dossiers are produced with resolvable citations, and that conservation/CRISPR read "not applicable". Assert the offline demo and the locked benchmark are byte-identical/unchanged. Stage 0 core regression passes.

Adversarial review (fresh subagent, separate from the ones in the pipeline): try to make the agent fabricate — ambiguous gene symbols, a protein pair with zero literature, a pair whose only co-mention is a review, a network failure mid-run. Confirm each degrades honestly and nothing is invented. Confirm the final reviewer cannot inject new claims.

Done: uploading a brand-new interactome yields live, verified, cited dossiers with real structures and druggability; every citation is provably from the retrieved set; failures degrade honestly; the demo path and locked benchmark are untouched; tests pass; docs/REPORT.md documents the agent, its gates, and the adversarial results.
