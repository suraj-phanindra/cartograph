# Cartograph — build report

What was built, the honest numbers it produces, how it was tested, what the
adversarial review found and how each finding was resolved, and the 3-minute
demo checklist. Every number below is computed by the pipeline in this repo
(`./run.sh build`), not asserted.

> **Phase-2 addendum (hardening + features) is in section 5 below.** The
> demo-critical core did not regress: the Stage-0 gate passes and the evaluator
> number is unchanged (precision@20 = 0.45, ROC-AUC = 0.8451 on 57 held-out).

---

## 1. Computed precision — baseline vs. loop

**Ground truth.** 332 real Gordon 2020 SARS-CoV-2→human AP-MS edges (IntAct
IM-27814). The locked evaluator freezes a seeded 17% held-out sample (seed 42) —
56 random edges + 1 disclosed pinned walkthrough edge (Orf6–RAE1) = **57 held-out
edges**. The split was committed as the first commit, before any prediction code,
in a module the predictor and reasoning layers cannot import.

**Baseline (deterministic L3, topology only, no LLM) — the honest floor:**

| metric | value |
|---|---|
| precision@10 | 0.30 |
| **precision@20 (headline)** | **0.45** |
| precision@50 | 0.26 |
| recall@20 | 0.64 |
| recall@50 | 0.93 |
| ROC-AUC | **0.845** |
| average precision | 0.373 |

Only **14 of 57** held-out edges are reachable by any length-3 path on this
sparse bipartite graph — the honest topology ceiling. When L3 can reach a
held-out edge, its median rank among its bait's candidates is **2**. ROC-AUC 0.845
means the predictor ranks true held-out edges well above chance.

**Pinning does not inflate the headline.** Recomputed with the pinned Orf6–RAE1
edge excluded: precision@20 = **0.45** (identical), ROC-AUC 0.859 on 56 edges. The
pinned edge sits at global rank > 20 (its L3 rank is honestly 7/8), so it never
entered the precision@20 window. Both numbers ship in the artifact and on screen.

**Loop round (self-improvement) — measured, fair, positive.** Confirm the four
recovered-true edges that L3 ranked #1 for their bait (N–G3BP1, Nsp13–PCNT,
Nsp4–TIMM10, Orf9c–ECSIT — every one a real Gordon edge), fold them back as known,
and re-score the **same** remaining held-out set:

| | precision@20 on remaining | reachable set |
|---|---|---|
| before fold-back | 0.30 | 10 |
| after fold-back | **0.35** | 10 |

The gain is **honest re-ranking**: folding the confirmed edges back adds paths
that lift one already-reachable held-out edge into the top 20. No edge becomes
newly reachable at this scale (10 → 10), and the report says so — the earlier
"unlocks previously-unreachable edges" wording was corrected after the review
flagged it as outrunning the data.

**What the reasoning layer contributes.** The Reader/Skeptic/Curator layer does
not inflate the precision number — and that is deliberate and honest. Its value
is the per-edge dossier: a cited mechanism, a real structure, and a testable
prediction. The Skeptic's false-positive filter (it vetoes AP-MS sticky proteins
like RPL36) is a correctness guard; on this split it is precision-neutral because
only one sticky protein reaches the top 20.

**Flagship.** Orf6–RAE1 held out and recovered via the genuine length-3 path
`Orf6 → NUP98 → NUP214 → RAE1` (all edges real STRING physical links), L3 rank
**7/8** in Orf6's dense nuclear-pore candidate set. The experimental structure
PDB **7VPH** confirms ORF6 directly contacts RAE1.

---

## 2. Test summary — 24 tests, all green

Run with `./run.sh test`. The suite guards the honesty invariants, not just
happy paths:

- **Graph/counts:** 332 edges / 26 baits / 332 preys asserted at load; flagship anchors present; STRING flagship bridges (NUP98–NUP214, NUP214–RAE1, NUP98–RAE1) exist.
- **Determinism:** frozen split reproduces byte-for-byte (sha256); L3 ranking identical across runs; evaluator precision identical across runs; the exported artifact is byte-identical even under randomized `PYTHONHASHSEED`.
- **Locked-evaluator boundary:** an AST walk asserts nothing under `backend/predict` or `backend/reason` imports the evaluator or the frozen split.
- **Flagship honesty:** RAE1 recovered via genuine length-3 paths (every hop asserted to be a real edge); canonical display path is length-3, never the 2-edge shortcut.
- **Reasoning honesty:** every mechanistic clause is cited or dropped; all citations openable; the broken N–G3BP1 placeholder is gone; Skeptic vetoes sticky proteins.
- **Structure honesty:** predicted structure labeled predicted with a real pLDDT and no asserted residues; experimental residues are structure-derived (E55/M58/D61 kept; wrong S55/K46 absent).
- **Evaluator realness:** headline precision is a computed value in (0,1) with ROC-AUC > 0.5, not the prototype's hard-coded 0.80.

---

## 3. Adversarial review — findings and resolutions

Three fresh red-team agents (code, science-honesty, evaluator-integrity) reviewed
the repo; the author did not grade its own work. The evaluator-integrity and
science auditors **verified the core clean** (split frozen before prediction,
boundary real, determinism holds, held-out edges real, flagship genuinely
length-3, residues structure-derived, citations real, headline computed). The
actionable findings and what was done:

| # | sev | finding | resolution |
|---|---|---|---|
| 1 | **critical** | Flagship Orf6–RAE1 (L3 rank 7) dropped by the top-6-per-bait cap → hero edge never drew or snapped green | Always emit held-out-true + dossier'd candidates regardless of the cap; verified the edge now draws and snaps green |
| 2 | high | Length-3 path animation had a dark middle: NUP98–NUP214 stored as `NUP214\|NUP98`, looked up in the other orientation | Orientation-independent `edgeBetween()` lookup; path now lights fully |
| 3 | high | Frontend built DOM via unescaped `innerHTML`; `href` from data unchecked (XSS the moment upload lands) | `esc()` on every interpolated string; `href` validated (`^https?:` / `^ENSG[0-9]+$`); `rel="noopener noreferrer"` added |
| 4 | medium | Config promised a with/without-pins report that never shipped on screen | Compute and surface `without_pinned` precision on the eval chip |
| 5 | medium | Headline k=20 is the precision argmax; @10/@50 hidden on screen | Render the full precision@10/20/50 curve + average precision on the chip |
| 6 | medium | Loop story claimed "unlocks previously-unreachable edges" while reachable held at 10→10 | Reworded to the honest mechanism (re-ranking, reachability unchanged) — flagged by two independent auditors |
| 7 | low | `boot()` had no error handling → blank page on fetch/`file://` failure | try/catch with a visible "serve over http" fallback |
| 8 | low | Loop narrated 4 confirmations but 3 baits are off-screen | Narrate the in-view count honestly (`confirmed_in_view`) |
| 9 | low | Flagship path hard-coded in prose could drift from the computed path | Build-time assert that the narrated path equals `config.FLAGSHIP_PATH` |
| 10 | low | Orf6–RAE1 structural clause rode the uncited exemption | Reworded to point at the openable structure panel; added an RCSB link |
| 11 | low | Druggability tier is a subjective curated value next to computed/cited fields | Labeled explicitly "curated prior, not computed/cited" |
| 12 | low | `resolve.py` build-time fragility (no pLDDT/missing-file guards) | Guarded `_mean_plddt` and the CIF copy with clear errors |

All fixes re-verified end-to-end in a headless browser (0 console errors) and
against the test suite (24 pass); the computed artifact remains byte-identical.

---

## 4. The 3-minute demo checklist

Run `./run.sh`, open `http://127.0.0.1:8791/index.html`.

1. **Frame (15s).** "A protein interaction map with the missing edges drawn in, each proven and scored." Point to the real map: Gordon 2020, 332 edges, 26 baits.
2. **Ask (20s).** Click *"What interaction is Orf6 missing?"* Watch the length-3 path `Orf6 → NUP98 → NUP214 → RAE1` light up and the missing `Orf6 → RAE1` edge appear. Say: genuine length-3, not the 2-edge shortcut.
3. **Dossier (60s).** The panel opens: the real experimental structure (PDB 7VPH) in Mol\*, structure-derived interface residues E55/M58/D61, a mechanism where every clause opens to a real paper, a proposed wet-lab test, the Skeptic's verdict, the confidence split into three unblended signals.
4. **Evaluator (45s).** Click *Run evaluator*. Held-out true edges snap green, misses flash red. Read the chip: **precision@20 = 45%** on 57 real held-out Gordon edges, ROC-AUC 0.845, "frozen seed 42, committed before prediction," and the without-pinned check.
5. **Loop (20s).** Click *Run one loop round*. Confirm the recovered edges, fold them back, precision on the remaining hidden edges rises **30% → 35%** (honest re-ranking).
6. **Close (20s).** The integrity rules on the left, all enforced by tests: deterministic graph, no citation no render, predicted always labeled, locked evaluator. Point to the predicted N–G3BP1 dossier for the "labeled predicted with a real pLDDT" case.

**Backup if Mol\* is slow:** the two experimental structures load from local CIFs
offline; if a panel stalls, the residues and mechanism still render and the
evaluator/loop beats are independent of the 3D.

---

## 5. Phase-2 addendum — hardening + features (no core regression)

Built on the green core with the same loop (plan → implement → test → fresh
red-team → iterate). **Stage 0** froze a regression gate
(`backend/tests/test_regression_core.py`) that pins the flagship recovery, the
three dossiers, and the exact evaluator/loop numbers; it was run after every
change. The core stayed green throughout and the headline number never moved.

### 5.1 Stage A — UI foundation + QA fixes (all shipped)
- **P0 expanded-viewer trap (the demo-breaker):** replaced Mol\*'s native fullscreen with an app-owned `#struct-fullscreen` overlay — an always-on-top **Close** button (plus Spin/Reset), Escape to exit, the viewer disposed on close, and `refreshInert()` making the rest of the app inert while open. Verified in the worst case (dossier + evaluator + loop panels all present): both exit paths work, no scroll-lock leak, focus restored.
- **Panel lifecycle:** one system for every transient panel (dossier, node, evaluator, loop, modal, fullscreen) — visible close, Escape, click-away, no stale panel, no overlap.
- **Hero-cluster legibility:** stronger repulsion + a deterministic de-overlap pass (min node distance 40 → 78 px); the nuclear-pore neighborhood is legible at default zoom.
- **Loop fold-back visible:** the Confirmed (loop) count goes 0 → 4 and the edges recolor.
- **Trimmed Mol\* controls** (custom spin/reset/expand; native dev panels hidden); **accessibility** (keyboard-operable `role=switch` layer toggles, aria-live status regions, labeled graph canvas + documented keyboard path, focus-visible rings, node hover cursor/tooltip); **responsive** reflow < 820 px; **prefers-reduced-motion**.

### 5.2 Stage B — features (kept 1–3, plus 6 and 4)
1. **FastAPI + SSE** (`backend/api/server.py`): wraps `evaluate()` / `l3_scores()` / `read_edge()`, streams the cited reasoning over SSE, and serves the static frontend from the same origin. The static offline artifact remains the guaranteed fallback (`./run.sh`); `./run.sh api` adds the live path.
2. **Bring-your-own-interactome upload:** validate an edge-list (gene-name allowlist, size caps) → live STRING enrichment → L3 → optional **own** held-out eval on the user's network with a **separate seed (1234)**. The locked Gordon benchmark is never touched. Dossiers degrade honestly: no cached evidence → topology only, shown as "no cached evidence", never a fabricated mechanism/citation.
3. **Ranked "what to test next" worklist:** sortable/filterable table of the top-40 predicted edges (L3, rank, recovered-held-out, structure availability, cited-mechanism, druggability), CSV export, row → dossier. Conservation is **omitted** (no cross-coronavirus data — a conservation column would be fabricated).
4. **Export:** worklist → CSV, and any dossier → a self-contained HTML report (with CSV formula-injection guard).
6. **Eval transparency:** every one of the 57 held-out edges as recovered/missed with its L3 rank and length-3 path, plus the reachability ceiling (14 of 57).

Item 5 (deepened druggability) is partial by design: dossiers carry curated
tractability tiers (labeled "curated prior, not computed/cited") and real Open
Targets deep-links; a live ChEMBL/Open-Targets fetch is a documented extension
(cut per the stated priority, and it would need approved-drug data not in `evidence/`).

### 5.3 Adversarial reviews — findings and resolutions
Two fresh red-team passes (Stage A: UI + a11y; Stage B: API-security + UI-matrix)
verified the non-negotiables held (the security auditor confirmed the **upload path
is fully isolated from the locked benchmark** — separate seed, no disk writes, no
import of the frozen split) and surfaced the following, all fixed:

| sev | finding | resolution |
|---|---|---|
| high | upload had no pre-parse body-size limit (memory DoS) | pydantic `max_length` + a Content-Length middleware (413) bound the body before parsing |
| high | `runLoop` never un-hid the precision chip → loop result invisible if the eval chip had been dismissed | `chip.classList.remove('hidden')` in `runLoop` |
| medium | 90 s synchronous STRING call → worker exhaustion; enrichment uncapped | timeout lowered, prey/edge caps, a concurrency gate (429) |
| medium | `enrich_error` returned raw exception text (infra disclosure) | generic client message; detail logged server-side only |
| medium | worklist sort inspected only one operand / no null handling (Drug column) | comparator normalizes both operands; nulls sort last |
| medium | toast and precision chip overlapped 821–1132 px | toast max-width capped so it can't reach the chip lane |
| medium | flagship animation had no cancel token (overlapping animations on rapid clicks) | `queryToken` guard cancels superseded animations |
| low | error echoed rejected gene bytes; no `nosniff`; JS-context XSS in the report button's inline `onclick`; StaticFiles served `frontend/.datum`; CSV formula injection; mobile legend overlap; no dialog focus trap | error reports line+rule only; `X-Content-Type-Options: nosniff`; report button wired in JS; `_NoDotfiles` StaticFiles + dir removed; CSV `=+-@` guard; legend hidden < 820 px; `inert` focus trap on all dialogs |

### 5.4 Stage C — full matrix + no-regression confirmation
Drove the full screen × control × state matrix in a headless browser, including
the expanded viewer with a dossier + evaluator + loop panel all present, keyboard
operation of the core flow, and the < 820 px reflow. Result:
- Core path (ask → length-3 path → 7VPH dossier → evaluator 45%/0.8451 → loop 30 → 35%, Confirmed 4) runs with **zero console errors** on the offline static origin.
- Every panel opens/closes/dismisses (✕ + Escape + click-away); `inert` never sticks across nested/overlapping dialogs; upload without the API degrades to a clear message.
- **39 tests pass** (24 core + 7 Stage-0 regression + 8 API). Evaluator unchanged; computed artifact byte-identical across runs.

**Run it:** `./run.sh` (offline static demo) or `./run.sh api` (adds the live API +
upload). `./run.sh test` runs the suite.

---

## 6. Live druggability + repurposing (Phase-2 item 5)

Display-only enrichment — never touches prediction, scoring, the locked evaluator,
or the frozen split (enforced by `test_druggability_does_not_import_locked_evaluator`).

**Source (schema introspected, not assumed).** Open Targets Platform GraphQL,
**data version 26.06** (the spec's 26.03 was stale; caught by querying `meta`). The
schema had changed: there is no `knownDrugs`/`isApproved`/numeric phase — drugs come
from `drugAndClinicalCandidates.rows[].{maxClinicalStage, drug{...maximumClinicalStage,
mechanismsOfAction}}`, and **approved = `maxClinicalStage == "APPROVAL"`**. Committed
snapshots for 32 targets (demo + worklist) in `evidence/druggability/<gene>.json` with
source + fetch date let the **offline** demo show real, dated data with **no live call**
(the frontend never fetches `/api/druggability`); `./run.sh api` fetches uncached
targets live.

**What shipped.** Dossier druggability section = real small-molecule tractability
bucket + the drug list (name, clinical stage, mechanism, approved flag, link) + a
"Repurposing lead" badge + source/date; the curated tier remains only as a clearly
labelled fallback. Worklist gains sortable/filterable **Tractability** and
**Repurposing** columns. Everywhere the repurposing framing is explicit: *a
hypothesis, not a validated antiviral; no drug here treats the infection.*

**Adversarial review — findings and resolutions.** Two fresh agents (repurposing-
honesty + code) verified 5/6 non-negotiables clean and confirmed offline-makes-no-
network and display-only. The substantive finding, **verified against live Open
Targets**: `BRD4`'s pelabresib row reports `APPROVAL` while BRD4's own tractability
lacks the Approved-Drug bucket — Open Targets contradicting itself (pelabresib is
Phase III, not approved). Resolution: a repurposing lead now requires **both** OT
signals to agree (an approved drug **and** the target-level Approved-Drug tractability
bucket), so BRD4 is correctly **not** a lead (pelabresib down-labelled to "Clinical")
while `RPL36` (ataluren + bucket) stays a genuine lead. Low-severity fixes: compound
stage labels, dedup-keeps-highest-stage, `AB_PRIORITY`, dropped the fake-magnitude
tractability bar, null-guarded tractability, `safeUrl` on the worklist link, CSV guard
covers tab/CR, and `snapshot_path` validates the gene at the sink. **48 tests pass**;
artifact byte-identical; evaluator unchanged (precision@20 = 0.45, ROC-AUC = 0.8451).

**The genuine repurposing lead:** RPL36 (approved ribosome-modulator ataluren) is the
one lead in the current top-40 worklist; the flagship structural targets
(RAE1/NUP98/TOMM70/G3BP1) are honestly poorly druggable (0 drugs).

---

## 7. UI refinement — professional interactome workbench

A UI + copy pass (no data, prediction, evaluator, or citation logic changed;
Stage-0 green after every change, evaluator unchanged at precision@20 = 0.45,
ROC-AUC = 0.8451). The app now reads as an instrument, not a guided demo.

**Shipped.**
- **Central "Ask the map" search** replaces the three hardcoded query buttons: a free-text input + example chips, backed by a **deterministic intent parser** (`parseIntent`/`runSearch`) that works offline — probe a named viral protein (any of the 26 baits, with aliases), "most druggable predicted", "run evaluation"/"loop". Unrecognised queries return a plain "not understood" message; nothing is ever fabricated (every rendered number comes from the artifact).
- **All tutorial / self-describing / integrity-marketing copy removed** (right-panel onboarding, the left INTEGRITY block, bottom captions). Right-panel default is the terse empty state. Section headers are bare labels.
- **Integrity kept as functional labels only:** PREDICTED/KNOWN + EXPERIMENTAL/PREDICTED-structure badges (predicted structures still carry a confidence value), the 🔒 locked-evaluator lock, the dossier provenance footer, inline openable citations, and the "repurposing hypothesis, not a validated antiviral" disclaimer.
- **Bug D (scroll overlap):** the sticky dossier header is now opaque with a z-index above scrolling content, and the structure badge is clipped inside the viewport (`isolation:isolate` + `overflow:hidden`) — no header/badge overlap on scroll.
- **Bug E (selected label):** selected/path-lit node labels are high-contrast (light text + dark outline); the ORF6 hero label is readable again. Hover tooltip preserved.
- **One unified frontend, both modes.** Mode is detected via `/api/health` — the offline static server (`backend/serve_static.py`) answers it too, so there is no console 404. Live-only controls (Bring your own map; Compare strains = phase-two) are disabled with a quiet tooltip offline and enabled in API mode. Workbench chrome: name + "interactome workbench", strain selector, top-right Compare / Bring your own map / Export.

**Adversarial review — findings and resolutions.** Two fresh agents (UI-copy-honesty
+ code/interaction) confirmed the honesty bar holds (the parser never fabricates;
all functional integrity labels survive; predicted structures still labelled; no
tutorial/marketing copy remains) and both serving modes render the identical
frontend. Fixes applied: dropped the remaining explanatory section-header captions
and the upload-dialog framing (tone); deleted 11 orphaned CSS rulesets from the
purge; made the flagship gate data-driven (`DATA.flagship.path[0]`) and the probe
toast report the real revealed-edge count; **removed a CSS regression** where a late
`position:relative` rule turned the eval precision card into a full-width in-flow
bar (now a compact bottom-right card, no search-bar overlap); cleared the stale
export key on node-panel open; de-raced the search "loop" intent; shipped
`act-upload` disabled to avoid an enabled-yet-inert window; and escaped bait ids
before building the intent RegExp. Verified in both modes: 0 console errors, search
intents work, dossier scroll clean, selected labels readable. **48 tests pass**;
artifact byte-identical; core did not regress.

## 8. Virtual PPI-screening layer (pooled-AlphaFold3 direction)

Positioning: pooled-AlphaFold3 (Anlin/Todor, *Mol Syst Biol* 2026) makes
genome-wide PPI maps cheap to generate; Cartograph is the triage layer that
decides **what to test first** with auditable evidence. Six items shipped in
order, then roadmap articulation. The demo-critical core did not regress — the
Stage 0 regression (`test_regression_core.py`) ran after every change and the
baseline held at **precision@20 = 0.45, ROC-AUC = 0.8451** throughout.

**8.1 Rounds-run counter.** `runLoop()` steps through an honest multi-round
trajectory (`eval.loop.rounds`): round 1 confirms 4 recovered-true edges and
moves the remaining-set precision@20 0.30 → 0.35; later rounds plateau honestly
(0.20 → 0.20) as the easy edges are used up. The UI shows "rounds run: N".

**8.2 Structural evidence channel + virtual validation.** `backend/structure/cofold.py`
turns interface confidence into a banded (AF3 calibration: ≥0.80 / 0.60–0.80 /
0.55–0.60 / <0.55), size-corrected, honestly-labelled signal, fused into the
evaluator as a transparent additive boost. **Honest result:** on this sparse
332-edge AP-MS map only 3 pairs have a deposited complex, so the aggregate
precision@20 **excluding the disclosed pinned flagship is unchanged (0.45 → 0.45)**;
the +0.05 with the pinned edge is the flagship being re-found via its own 7VPH
structure, not a general gain. `aggregate_gain_excl_pinned = 0.0` is asserted by a
test. The channel's value is per-hypothesis corroboration and, at scale, on a
virtual screen.

**8.3 Pooled-AlphaFold3 matrix upload.** `POST /api/screen` parses a symmetric
protein×protein ipTM matrix, resolves chain lengths (UniProt, best-effort, cached,
capped), **size-corrects** ipTM (de-trends vs summed chain length), thresholds to
candidate edges, bands each, and runs the L3 topology channel on the thresholded
network. Source labelled "virtual screen (pooled-AlphaFold3)"; every ipTM labelled
predicted; no cached evidence → topology only, never a fabricated mechanism; never
touches the locked benchmark (asserted by test). Trust boundary: gene allowlist on
every name, protein/lookup/payload caps, concurrency gate.

**8.4 Worklist as ranked testable hypotheses.** Each row is one testable
interaction with a **novelty tag grounded in a real NCBI PubMed co-mention count**
(novel = 0 co-mentions under SARS-CoV-2 context, known = recovered Gordon edge or
cited pack, partially known = ≥1 co-mention; 40 pairs pre-cached to
`evidence/novelty_comention.cached.json`), the Skeptic verdict (Nsp8–RPL36 vetoed
as an AP-MS frequent-flyer), a structural band only where a real structure exists
("no model" otherwise — no fabricated ipTM), real druggability, and the single
next experiment. Grounding is honest: 27 of 40 rows are genuinely novel (0
co-mentions), which is the point of the tool.

**8.5 Human-in-the-loop feedback.** Confirmed / to-test / refuted + a lab note per
dossier, persisted to `localStorage`, restored on reopen, **folded back onto the
map** (confirmed → green edge), surfaced in a worklist "You" column + live count,
and exported/imported as JSON. Trust boundary on import (edge-key regex, verdict
allowlist, note cap). Never part of the locked benchmark.

**8.6 Interoperable export.** The whole map as **CX2** (valid NDEx/Cytoscape
aspect array — nodes, edges with `interaction='predicted'` + `l3_score`, reviewer
verdicts folded in), and the ranked hypotheses as a structured **Claude Science
handoff** JSON (mechanism, citations, novelty, Skeptic, experiment, provenance,
data-source versions, honesty note).

**Adversarial review — findings and resolutions.** A fresh red-team agent audited
all four core items against the non-negotiables and traced each end-to-end (52
tests re-run, artifact inspected, size-correction reproduced under partial length
resolution). It confirmed the verified-clean set (baseline 0.45/0.8451 and frozen
seed 42 intact; `/api/screen` reads no frozen split and uses its own graph;
`aggregate_gain_excl_pinned = 0.0` with the honest 0.45 headlined; no fabricated
ipTM anywhere; novelty grounded and non-contradictory on all 40 rows; trust
boundary enforced) and raised **1 MAJOR + 3 MINOR**, all fixed:
- **MAJOR** `/api/screen` injected a 0-length when only one protein of a pair
  resolved in UniProt, skewing the size-correction fit for every pair and flagging
  the partial pair `size_corrected` on a fabricated basis. Fixed: a pair is
  size-corrected only when **both** lengths resolve; otherwise it stays at raw
  ipTM, never invented. Covered by a new partial-length test.
- **MINOR** the AF3 bands (calibrated on raw ipTM) were applied to the
  size-corrected value without disclosure. Fixed: each row carries `band_basis`
  and the screen note states it.
- **MINOR** the with-pinned structural precision (0.50) sat one field from a
  headline. Fixed: renamed to `l3_plus_structure_with_pinned_disclosed`.
- **MINOR** the honesty-critical paths lacked tests. Fixed: added banding /
  size-correction / novelty-classify / artifact-invariant / partial-length tests.

**59 tests pass**; artifact rebuilt with the baseline intact; every feature
verified in-browser (0 console errors). Roadmap (not built, deliberately scoped
out) articulated in the README: live pooled-AF3 folding, active-learning loop,
multi-user realtime, cross-species conservation, learned embeddings, chemical/
functional-genomics channels — each behind the same locked-benchmark contract.

## 9. Cross-species conservation channel (SARS-CoV-1 / MERS)

The first corroboration channel that **measurably improves accuracy** — and the
gain is honest.

**9.1 Data (STEP 0, verified).** The SARS-CoV-1 and MERS interactomes were fetched
from Gordon et al. 2020 *Science* ("Comparative host-coronavirus protein
interaction networks", PMID 33060197, DOI 10.1126/science.abe9403, IMEx IM-28441)
via the EBI IntAct REST API — the same IMEx source as the Nature ground truth.
Committed `evidence/gordon2020_science_cov1_mers_edges.csv`: **366 SARS-CoV-1 + 296
MERS** interactions, both **exactly the paper's canonical numbers**. Viral proteins
were mapped to Gordon canonical names (Nsp1-16, N/M/E/Spike, accessory ORFs; SARS-
CoV-1 Orf8a+Orf8b→Orf8 and protein-14→Orf9c; MERS lineage-specific ORF3/4a/4b/5 kept
distinct). Reproducible via `scripts/fetch_cov1_mers.py` + `build_cov1_mers_csv.py`.

**Benchmark isolation.** The Science paper also contains a SARS-CoV-2 map (396 PPIs,
distinct from the Nature 332 the frozen split uses). It was fetched but **deliberately
not committed** — it never enters the repo, so it cannot modify, extend, or
contaminate the frozen split or ground truth. Asserted by a test (`grep -c
SARS-CoV-2` on the committed file is 0; baseline stays 0.45 / 0.8451).

**9.2 Three states, never collapsed.** An edge is **conserved** if the orthologous
viral protein binds the same human prey in a reference strain; **not_conserved** if
that ortholog is represented in the strain's screen but no such edge is reported;
**no_ortholog** if the strain has no orthologous viral protein. Viral orthology is
partial: Nsp1-16/N/M/E/Spike are universal; MERS encodes lineage-specific ORF3/4a/4b/5
and has **no ortholog** of any SARS accessory ORF; Orf10 has no ortholog in either
(CoV-2 putative-specific). Rendering "no_ortholog" as "not_conserved" would be a
fabrication — the flagship case Orf6→RAE1 is **conserved in SARS-CoV-1** but
**no_ortholog in MERS**, and both are shown as distinct states everywhere (module,
worklist, dossier, Compare-strains, exports). A test asserts the states never collapse.

**9.3 Honest accuracy result.** Used as an additive candidate prior in the locked
evaluator (kept SEPARATE from topology/structure/literature, never blended into one
score), conservation **genuinely helps, and the gain survives excluding the pinned
flagship**: precision@10 **0.30 → 0.60**, precision@20 **0.45 → 0.50**, ROC-AUC
0.859 → 0.892 (excl. pinned). This is unlike the structural channel, which honestly
reported 0.0 aggregate gain. Across all 332 Gordon edges, **118 (36%) are
pan-coronavirus** (111 conserved in SARS-CoV-1, 30 in MERS); 107 MERS "no ortholog"
cases are correctly distinguished from "not conserved". The baseline evaluator number
is unchanged — conservation is reported alongside it, never replacing it.

**9.4 Product surfaces.** A Conserved map layer (highlights pan-coronavirus edges);
**Compare strains** (previously greyed out) is now a live offline view of shared vs
SARS-CoV-2-specific edges with per-strain state; a worklist Conservation column +
"conserved only" filter; a separate dossier corroboration block; and the evaluator
panel reports the conservation gain plus the **free win** — "recall on the reachable
set: **14/14**" (L3 recovers every held-out edge a length-3 path can reach), formerly
buried one click deep. Fixes landed: the worklist experiment text wraps (was
truncated); every disabled control carries a why-tooltip; the "every hypothesis is
backed by an openable paper" line is kept.

**Data-integrity review + CRISPR status.** A fresh adversarial review audited the
conservation channel (states never collapsed, benchmark isolation, no fabricated
matches, gain honest excl-pinned). The second planned channel — CRISPR functional
genomics — is pending real per-screen hit-list data: `crispr_screens.json` is
metadata-only and `crispr_gold_standard.csv` is only the ≥2-of-7 consensus (which
overlaps our prey solely at SCAP), and a per-screen union cannot be reconstructed
from full text without presenting mentions as hits. The verified hit lists are being
sourced (via Claude Science) so the channel can be built as a real weighted union
rather than approximated. **67 tests pass**; baseline intact; Stage 0 green.
