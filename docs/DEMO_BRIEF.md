# Cartograph — State-of-the-Build Brief (verified)

Everything below was verified on 2026-07-13 by reading the source and **running it**
(fresh evaluator run, live agent calls, in-browser timing with network instrumentation).
Numbers are measured, not remembered. Two serving modes: **offline** (`./run.sh`,
port 8791, static artifact, zero network) and **API** (`./run.sh api`, port 8792,
adds the live upload + Evidence Agent).

---

## A. FEATURE INVENTORY

| Feature | Trigger | Mode | Network | Offline-safe? |
|---|---|---|---|---|
| Load map + "Ask the map" search | page load / search bar | both | none (offline) | ✅ |
| Flagship walkthrough (Orf6→RAE1 path animation → dossier) | search "what is Orf6 hitting…" or the ORF6 chip | both | none | ✅ |
| Structural dossier + **Mol\* 3D** (7VPH/7DHG/AF-G3BP1) | click a demo edge / open dossier | both | none — CIFs served locally from `frontend/data/structures/` | ✅ |
| Cited mechanism + openable PMIDs | inside dossier | both | none (baked); PMID links open PubMed in a new tab only if clicked | ✅ |
| Locked evaluator (green/red edges + precision chip) | "Run evaluator" / search "run evaluation" | both | none | ✅ |
| Self-improving loop (rounds 1–3, counter) | "Run loop round" | both | none | ✅ |
| Held-out transparency (57 rows) | "Held-out transparency" | both | none | ✅ |
| Worklist / "What to test next" (40 ranked hypotheses) | "What to test next" | both | none | ✅ |
| Conservation: Conserved map layer + **Compare strains** | layer toggle / "Compare strains" | both | none (in artifact) | ✅ |
| CRISPR "Option B" functional-genomics panel | evaluator-chip "Option B" link | both | none | ✅ |
| Druggability (Open Targets snapshots in dossiers) | inside dossier | both | none offline (committed snapshots); live fetch only via `/api/druggability` | ✅ offline |
| Human-in-the-loop verdicts (confirm/to-test/refuted + note) | dossier "Your verdict" | both | none (localStorage) | ✅ |
| Exports: dossier report / worklist CSV / CX2 / hypotheses JSON | "Export" / worklist buttons | both | none | ✅ |
| **Bring your own map** (edge list → STRING → L3) | top bar (API only) | **API only** | **STRING v12 live call** | ❌ disabled offline |
| **Pooled-AF3 ipTM matrix** screen | upload modal, matrix tab | **API only** | **UniProt** (chain lengths) | ❌ |
| **Evidence Agent** (live per-edge dossier) | "run Evidence Agent" on an uploaded prediction | **API only** | **UniProt + NCBI + RCSB + AlphaFold + Open Targets + Anthropic** | ❌ |
| Uploaded map becomes the workbench (mode-aware chrome, dropdown, "Run all") | after upload | **API only** | as above | ❌ |

**Offline flag:** on port 8791 the mode pill reads "offline", **Bring your own map is
disabled** with a tooltip, and I instrumented `fetch` across the full demo path —
**zero network calls**. Everything demo-critical is baked into the artifact. The only
network-dependent features are the three API-only ones above, which are correctly gated
off on 8791.

---

## B. THE NUMBERS (verified fresh; honest caveats)

**Locked evaluator (baseline, L3 topology only):**
- Held-out edges: **57**
- precision@10 **0.30** · @20 **0.45** · @50 **0.26**
- ROC-AUC **0.8451** · AP (average precision) **0.3733**
- recall@10 **0.2143** (3/14) · recall@20 **0.6429** (9/14) · recall@50 **0.9286** (13/14)
- *Caveat:* precision@20 = 0.45 means 9 of the top-20 ranked proposals are true held-out edges. AP 0.37 is modest — this is a hard, sparse bipartite recovery task, not a 0.9-AUC toy.

**The reachable set — confirmed 14 of 14:**
- Of the 57 held-out edges, only **14 are reachable** by a length-3 path (the honest topology ceiling; the other 43 have no length-3 route back to a co-prey). L3 surfaces **all 14** as candidates → **14/14**.
- *Caveat (important):* "reachable" and "recovered as a candidate" are nearly the same condition, so 14/14 is close to definitional — it says L3's candidate generation misses nothing a length-3 path can reach. The real skill is the **ranking**: recall@50 is **13/14** (one reachable edge sits below rank 50), recall@20 is 9/14. Frame it as "L3 recovers every reachable held-out edge, and ranks 13 of them in the top 50" — do **not** say "100% recall" unqualified.

**Loop trajectory (measured, all rounds):**
- Round 1: confirm 4 (N–G3BP1, Nsp13–PCNT, Nsp4–TIMM10, Orf9c–ECSIT) → P@20 **0.30 → 0.35**; recoverable 10→10
- Round 2: confirm 4 (N–PABPC1, Nsp13–PDE4DIP, Nsp4–TIMM29, Orf9c–NDUFAF1) → P@20 **0.20 → 0.20**; recoverable 6→7
- Round 3: confirm 1 (Nsp13–PRKAR2A) → P@20 **0.15 → 0.15**; recoverable 6→6
- **Plateaus at round 2** (the easy edges are used up; the gain is real only in round 1). 3 rounds total. *Caveat:* the headline loop beat is round 1 (0.30→0.35 on the remaining set). Don't imply monotonic improvement — it flattens honestly.

**Structural channel — confirmed 0.0 aggregate gain:**
- 3 pairs have a deposited complex (Orf6–NUP98, Orf6–RAE1, Orf9b–TOMM70). Excluding the pinned flagship: P@20 **0.45 → 0.45**, **aggregate_gain_excl_pinned = 0.0**. The +0.05 you see with the pinned edge is the flagship re-found via its own 7VPH — self-referential, disclosed. *This channel corroborates per-hypothesis; it does not move the aggregate. Say so.*

**Conservation channel — it genuinely helped (this is the strong one):**
- As an additive prior, excluding the pinned flagship: precision@10 **0.30 → 0.60** (+0.30), precision@20 **0.45 → 0.50** (+0.05), ROC-AUC **0.859 → 0.8922**.
- 118 of 332 CoV-2 edges (36%) are pan-coronavirus (111 in SARS-CoV-1, 30 in MERS); 107 MERS "no ortholog" cases kept distinct from "not conserved".
- *This is the one channel that moved the number, and it holds without the pinned edge.* Honest and real.

**CRISPR functional-genomics coverage — read this carefully:**
- Map-wide (Option B): **11 of 332** host factors are CRISPR dependency hits (**9** excluding the two soft-provenance screens). Top: RAB7A (2 screens), SCAP (2), WASHC4 (2).
- **In the 40-hypothesis worklist: 0** have CRISPR support. None of the top-40 L3 predictions target a known dependency factor — binding partners and dependency hits are different biology.
- *Caveat (do not overclaim):* the CRISPR column on the worklist is **empty** in the demo. The channel's honest value is the whole-map Option-B aggregate (11/332), not per-hypothesis. Present it as corroboration, not a headline.

**Novelty distribution (40 worklist hypotheses):** **27 novel** (0 PubMed co-mentions), **12 known**, **1 partially known**. Grounded in real cached co-mention counts.

**Druggability:** exactly **1 repurposing lead** (RPL36) — and it is **Skeptic-vetoed** (ribosomal frequent-flyer). So the single repurposing lead carries a veto. Honest tension: druggable but suspect. Don't present RPL36 as a clean lead.

**Skeptic (worklist):** 39 pass, **1 veto** (RPL36).

---

## C. THE FLAGSHIP PATH (verbatim, verified from the artifact)

- **Query:** "what is Orf6 hitting that we haven't mapped?" (or the "ORF6's unmapped targets" chip)
- **Length-3 path:** `Orf6 → NUP98 → NUP214 → RAE1` (a genuine 3-edge path, not the 2-edge L2 shortcut — the CLAUDE.md honesty check)
- **L3 rank:** **7 of 8** for Orf6 (score 0.508631). *Caveat: RAE1 is near the bottom of Orf6's own candidate list; it earns its place via the global ranking, not by being Orf6's #1. Do not say "L3 ranks RAE1 first for Orf6."*
- **Structure:** PDB **7VPH**, X-ray diffraction, **2.8 Å**, chains = SARS-CoV-2 ORF6 C-terminal tail + human RAE1 + human NUP98
- **Interface residues (computed ≤3.0 Å heavy-atom):** **E55, Q56, M58, E59, D61**
- **Citations (PMIDs):** 33097660, 35970938, 33849972 (all resolve on PubMed)
- **Skeptic:** **pass** ("no false-positive pattern matched")
- **Proposed experiment:** mutate the structure-verified interface residues **E55A / M58R / D61A**, test loss of RAE1 binding by **co-IP in HEK293T**, readout **STAT1 nuclear import** rescue
- **Conservation:** **conserved in SARS-CoV-1**, **no ortholog in MERS** (MERS has no Orf6 — shown as a distinct state, never "not conserved")

---

## D. WHAT CHANGED SINCE THE LAST QA

**Conservation channel (new):** SARS-CoV-1 + MERS from Gordon 2020 *Science* (366 + 296 edges, exact paper counts), fetched via IntAct; the Science SARS-CoV-2 map is deliberately **not** committed (benchmark isolation). Adds the Conserved layer, live Compare-strains view, worklist column, dossier block, and the measured **+0.30 P@10 / +0.05 P@20** prior gain (excl-pinned). Four honest states (conserved / not_conserved / no_ortholog / not_screened).

**CRISPR channel (new):** 433 sourced hits from 7 genome-wide screens; Option-B panel (11/332 host factors), worklist "Functional" column (empty on the top-40), dossier line with linked PMIDs. Never claims a hit validates a physical interaction.

**The Evidence Agent — YES, it landed and it is live.** On a **brand-new uploaded edge** (API mode) it runs a 6-stage pipeline, streamed over SSE: resolve identifiers (UniProt) → retrieve literature + a real deposited structure + druggability (NCBI / RCSB / AlphaFold / Open Targets) → Claude Reader drafts cited clauses → Claude Skeptic → **deterministic Stage-4 verify gate re-checks every citation** (closed-set + esummary-resolve + title-match; a PDB must contain both accessions) → Claude final reviewer (drop-only) → renders. No citation, structure, residue, or drug is ever fabricated; failures degrade to topology-only.

- **End-to-end time for one cold dossier: ~33 seconds** (measured, Opus 4.8 model). **Cached: ~13 ms.**
- **Non-coronavirus upload: works.** Measured live on **FOS → JUN** (human): returned the real **PDB 1A02** complex (interface Q166/K176/E182), a verified cited mechanism (PMID 42420224), Skeptic pass.
- **On a non-coronavirus edge, conservation and CRISPR display "not applicable — no reference data for this organism"** (never a blank implying absence). Verified in the returned dossier.
- Model is **Opus 4.8** (`claude-opus-4-8`), configured via `.env` (gitignored). Opus is a rigorous Reader — it returns "no cited mechanism" and shows only the real structure when the retrieved abstracts describe regulation rather than direct binding (e.g. CDK2→TP53 shows PDB 1H26 but no mechanism, because CDK2 and p53 don't directly contact there).

---

## E. DEMO DRY-RUN (measured wall-clock, offline port 8791)

I executed the intended click-path with `fetch` instrumented. **Every step ran with ZERO network calls.**

| Step | Wall-clock | >2 s? | Network? | Risk |
|---|---|---|---|---|
| Page load → map rendered | instant | no | none | none |
| Search "what is Orf6 hitting…" → path animation → dossier opens | **3.64 s** | ⚠ yes | none | It's the *scripted* 3-edge walk (650 ms/step) + Mol\* mount, not lag. Looks intentional. |
| Mol\* 3D structure (7VPH) renders in the dossier | within the 3.6 s above | — | none (local CIF) | first Mol\* init is the heaviest client op; fine once warmed |
| "Run evaluator" → green/red edges snap + precision chip | **2.20 s** | ⚠ yes | none | scripted snap animation, intentional |
| "Run loop round" (×1) | **0.055 s** | no | none | instant |
| Open worklist (40 rows) | instant | no | none | none |
| Open Compare strains | instant | no | none | none |
| Open Held-out transparency (57 rows) | instant | no | none | none |

The two >2 s steps are **deliberate animations**, not slowness, and neither touches the network.

**Safest 3-minute path — run OFFLINE (port 8791):**
1. Open the map; read the one-line thesis. (0:00–0:20)
2. Ask "what is Orf6 hitting that we haven't mapped?" → watch the length-3 path light up → the **7VPH dossier** opens with 3D structure, computed interface residues, cited mechanism. (0:20–1:20) — the hero beat.
3. "Run evaluator" → real held-out edges snap **green**, misses **red**, precision chip shows **45% @20 / ROC 0.845 on 57 real edges**. (1:20–2:00)
4. "Run loop round" once → P@20 0.30→0.35 on the remainder; mention it plateaus honestly. (2:00–2:20)
5. Open **Compare strains** → 118/332 pan-coronavirus, and say conservation is the one prior that measurably helped (+0.30 P@10). (2:20–2:50)
6. One-line close: "and it works on your data too" — cut to a *pre-recorded / pre-warmed* Evidence Agent clip if you want it (see Fragilities). (2:50–3:00)

**Run the whole video offline.** The Evidence Agent is the strongest "wow" but it is 33 s cold and needs 5 live APIs — treat it as a separate, pre-warmed segment, not a live click.

---

## F. FRAGILITIES

- **The live Evidence Agent is the #1 on-camera risk.** 33 s cold, depends on UniProt + NCBI + RCSB + AlphaFold + Open Targets + Anthropic all responding. Any one being slow/down = a stall or a topology-only fallback on camera. **Pre-warm it:** before recording, POST the exact edge(s) you'll show to `/api/evidence` so they're cached (then it renders in ~13 ms), OR screen-record the agent segment separately and play it back.
- **First Mol\* initialization** is the heaviest client operation. Open one dossier before recording so the viewer is warm.
- **Do NOT run "Bring your own map" or the agent cold on camera.** Pre-warm or pre-record.
- **STRING enrichment (upload)** is a live call — if you show an upload, pre-run it once so it's fast, or expect a few seconds.
- Browser cache: hard-reload with a `?v=` query bump between takes to avoid a stale `app.js`.
- The precision chip and toasts auto-dismiss (6 s) — don't wait too long to narrate them.

**Pre-warm checklist before recording:**
```bash
# ensure both servers are up
curl -s http://127.0.0.1:8791/api/health   # offline (the demo)
curl -s http://127.0.0.1:8792/api/health   # api (only if showing the agent)
# warm any agent edge you'll show (API mode), so it's instant on camera:
curl -s -X POST http://127.0.0.1:8792/api/evidence -H 'Content-Type: application/json' \
  -d '{"bait":"E2F1","prey":"CCNA2","l3_score":0.63}' > /dev/null
```

---

## G. RESET BETWEEN TAKES

State lives in three places:
- **In-memory** (evaluator done, loop round counter, revealed edges): cleared by a **page reload**.
- **localStorage** (`cartograph.feedback.v1`) — your confirm/to-test/refuted verdicts **persist across reloads**. Clear them or last take's verdicts show.
- **Agent dossier cache** (API server, in-memory): harmless (serves cached). Restart the server only if you want cold timings back.

**Clean reset (paste in the browser DevTools console, then hard-reload):**
```js
localStorage.removeItem('cartograph.feedback.v1'); location.reload();
```
Or one-liner in the address bar path — just reload with a fresh cache-buster: `…/index.html?v=take2`.
To fully reset the API agent cache between takes, restart it:
```bash
lsof -ti :8792 | xargs kill -9; ./run.sh api
```

---

## H. SUBMISSION ARTIFACTS

- **Repo is LOCAL ONLY — there is NO git remote configured.** ⚠ **This is a submission blocker.** You must create a public GitHub repo and `git push` before submitting. (Branch `main`, working tree clean, HEAD `18e7940`.)
- **License:** MIT (`LICENSE` present). ✅
- **Run instructions:** `./run.sh` (offline) / `./run.sh api` (with the live API). Documented in README. ✅
- **Tests:** **92 tests**, all passing (`./run.sh test`). ✅
- **docs/REPORT.md:** present and current (11 sections, through the Evidence Agent). ✅
- **README.md:** present, with the honest headline numbers + integrity rules. ✅
- **100–200 word written summary:** ⚠ **does not exist yet.** You need to write it for the submission form. (I can draft it from this brief if you want.)

**Before submit:** (1) push to a public repo, (2) write the 100–200 word summary, (3) confirm the license header, (4) record the video.

---

## I. YOUR PICKS

**3 most impressive to a scientist-judge:**
1. **The deterministic anti-hallucination gate (Stage 4) on a live agent.** "Claude reads, but a *code* gate — not a prompt — re-checks that every citation is in the retrieved set, resolves, and title-matches; a structure must actually contain both accessions." On a real run it dropped a fabricated PMID while keeping the real 1YCR interface. This is the credibility differentiator — it directly answers "how do I know it's not making this up."
2. **The flagship, structure-grounded.** Topology re-proposes a held-out edge; the deposited 7VPH structure confirms it; the interface residues (E55/M58/D61) are *computed from coordinates*, not copied from prose; and the proposed experiment mutates exactly those residues. A judge sees software that reasons from structure, not vibes.
3. **The locked evaluator + honest headline.** 45% precision@20 / ROC 0.845 on 57 real held-out edges, frozen before prediction — plus the willingness to say the structural channel added *0.0*. The honesty is the sell.

**3 I would NOT show on camera:**
1. **The CRISPR worklist column** — it's empty (0 of 40); the value is buried in the Option-B panel. Showing the empty column invites "so it does nothing?"
2. **The RPL36 repurposing lead** — the only lead, and it's Skeptic-vetoed. Confusing on camera.
3. **A cold live Evidence Agent run** — 33 s and 5 external APIs. Pre-warm it or pre-record it; never click it cold on camera.

---

## J. HONEST CAVEAT LIST (do not overclaim)

- **The recall numbers use a denominator of 14, not 57.** Verified in code: recall = hits / (positives in the ranked list) = hits / **14** (only the 14 reachable edges can appear as proposals). So recall@50 = **13/14 = 93%** is recall *against the reachable set*. **Against all 57 held-out edges, recall@50 = 13/57 = 23%.** Cite it as "13 of the 14 reachable edges" — **never "93% recall" unqualified**, or a judge who assumes the denominator is 57 will feel misled.
- **14/14 reachable recall is near-definitional.** "Reachable" ≈ "L3 produces it as a candidate," so 14/14 mostly says candidate generation misses nothing. The honest ranking number is precision@20 = **0.45**. Never say "100% recall" bare.
- **Only 14 of 57 held-out edges are reachable at all.** The other 43 have no length-3 path — a topology ceiling, not a bug, but say it: L3 can only ever recover 14.
- **The structural channel added 0.0** to aggregate precision (excl-pinned). It corroborates individual hypotheses; it is not an accuracy win.
- **The loop plateaus at round 1.** Rounds 2–3 are flat (0.20→0.20, 0.15→0.15). The self-improvement is one real step, then it flattens.
- **CRISPR lights up 0 of the 40 hypotheses.** Map-wide overlap is 11/332. It is corroboration, not a per-hypothesis signal.
- **The flagship is L3 rank 7/8 for Orf6**, not #1. It's recovered via the global ranking.
- **The one repurposing lead (RPL36) is Skeptic-vetoed.** Not a clean drug story.
- **Opus is a conservative Reader** — some uploaded edges show a real structure but "no cited mechanism" (honest, but less flashy). Choose demo edges where the literature is direct (E2F1→CCNA2 gives cited clauses; CDK2→TP53 shows structure only).
- **Mechanism prose is Claude-authored** (grounded in verified packs offline, or live-retrieved + gate-verified in the agent). It is not a database lookup; it is generated then verified.
- **AP is 0.37** — a modest average-precision on a hard task. The ROC (0.845) is the friendlier number; cite both.

---

## K. SCREEN SETUP

- **Record at 1920×1080, browser at 100% zoom, window maximized.** The 3-column layout (left controls · center graph · right dossier) is designed for this and renders cleanly; verified at ~1470–1500 px with no overflow, and it has headroom to 1920.
- **The graph node labels and hexagons are large and legible; the dossier body text is ~12–13 px.** At true 1080p full-screen that reads fine, but if the judge watches on a small window, bump browser zoom to **110%** for the dossier-heavy beats — the layout tolerates it (the graph re-fits). Don't exceed ~125% or the right dossier column starts to crowd.
- **The graph auto-fits;** after opening/closing a dossier, hit "Reset view" if it drifts.
- **Dark UI** — record in a dark room / dark player background so the teal predicted edges and green eval edges pop.
- Keep the precision chip (bottom-right) and toasts in frame when you trigger them; they're small and auto-dismiss in 6 s.
- **Do not resize the window mid-take** — Cytoscape re-lays-out on resize and the graph will jump.

---

*Generated from a live verification pass: fresh `evaluate()`, live `/api/evidence` calls
(FOS–JUN cold 32.7 s, cached 13 ms), in-browser timing with `fetch` instrumented (0
network calls on the offline path), Mol\* render confirmed, 92 tests, MIT, no git remote yet.*
