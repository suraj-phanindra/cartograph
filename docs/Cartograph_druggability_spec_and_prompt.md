# Cartograph: live druggability + repurposing (Open Targets + ChEMBL)

Deferred Phase-2 item 5. This turns a predicted host target into a repurposing lead: if a host protein Cartograph flags already has an approved drug, that is a testable "block this host factor with an existing drug" hypothesis. It plugs straight into the Gordon 2020 thesis ("targets for drug repurposing") and the Impact axis.

## Sources (verified current, both free, no API key)
- Open Targets Platform GraphQL (PRIMARY). Endpoint: https://api.platform.opentargets.org/api/v4/graphql (data version 26.03). One query keyed by Ensembl gene ID returns BOTH tractability and known drugs (Open Targets already integrates ChEMBL). GraphiQL IDE is at the same URL for confirming the schema.
- ChEMBL REST (OPTIONAL cross-check / detail). Base: https://www.ebi.ac.uk/chembl/api/data/. Map UniProt to a ChEMBL target with `/target?target_components__accession=<UNIPROT>&target_type=SINGLE PROTEIN`; approved drugs are `max_phase=4`; mechanisms via `/mechanism?target_chembl_id=<ID>`.

Keys we already have: dossiers store Ensembl gene IDs (e.g., RAE1 = ENSG00000101146) and the evidence packs have UniProt ids. Use Ensembl for Open Targets, UniProt for ChEMBL.

## What to fetch and show
Per host target (in the dossier druggability section and as a worklist column):
- Tractability: the highest true small-molecule bucket from Open Targets `tractability` (for example "Approved Drug", "Advanced Clinical", "Phase 1 Clinical", "Discovery Precedence"), plus antibody tractability if present. Show the bucket label, not a made-up score.
- Known drugs: from Open Targets `knownDrugs` rows, the drugs that hit this target, each with name, max clinical phase, mechanism of action, and whether it is approved (phase 4). Link each drug to its Open Targets / ChEMBL page.
- Repurposing flag: if any known drug is approved (phase 4), mark the target as a "repurposing lead" in the dossier and as a filterable/sortable column in the "what to test next" worklist.

## Representative Open Targets query (CONFIRM field names against the live GraphiQL schema before coding)
```
query TargetDruggability($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    tractability { label modality value }
    knownDrugs {
      count
      rows {
        drug { id name isApproved maximumClinicalTrialPhase }
        mechanismOfAction
        phase
        status
        disease { name }
      }
    }
  }
}
```
Field names (e.g., maximumClinicalTrialPhase vs maxPhase, knownDrugs row fields) may differ by schema version. Verify in GraphiQL at the endpoint above, do not assume.

## Honesty rules (non-negotiable; this is where a repurposing feature can go wrong)
- A repurposing lead is a HYPOTHESIS, not a treatment claim. Label it exactly that: "Existing drugs against this host target — repurposing hypotheses, not validated for antiviral use." Never imply any drug treats COVID or the infection.
- Every drug, tractability bucket, and number must come from the live source and link out to it. No fabricated drugs, phases, or tractability. If a target has no known drugs, say so ("no approved drugs against this target").
- Label the source and freshness on screen: "Open Targets, data 26.03, fetched <date>". Same for ChEMBL if used.
- Keep the existing curated tier as a clearly-labeled fallback only; prefer live/cached real data.

## Offline vs online (match the existing pattern)
- Live in API mode (the 8792 server): fetch from Open Targets (and ChEMBL if used), cache responses on the server, with a timeout and graceful error handling. This is an online dependency, so it stays OFF the guaranteed offline demo path.
- Pre-cache for the demo: fetch once for the demo host targets (RAE1, NUP98, TOMM70, G3BP1, and the worklist's top targets) and commit the snapshots to `evidence/druggability/<gene>.json` with the fetch date and source. The offline demo (8791) reads these committed snapshots so it shows REAL druggability data, labeled with the fetch date, without a live call.
- Degrade honestly: if live and there is no cached snapshot and the fetch fails, show "druggability unavailable (source unreachable)", never a guess.

## Guardrails
- Do not touch the locked evaluator or the frozen split. This feature is display-only enrichment; it never affects prediction or scoring.
- The demo-critical core stays green; run the Stage 0 regression after the change.
- Cache and rate-limit politely (both APIs are free but be a good citizen: cache, timeout, back off on errors).

---

## Claude Code prompt (paste at the repo root)

Add live druggability and repurposing to Cartograph (deferred Phase-2 item 5). Same autonomous loop as before: plan, PRD, implement, test, fresh red-team review, iterate. Do not regress the core; run the Stage 0 regression after every change; do not touch the locked evaluator or the frozen split (this feature is display-only enrichment).

Read first: CLAUDE.md, docs/REPORT.md, docs/Cartograph_BUILD_SPEC.md, and the current dossier druggability section + the worklist code. Also read docs/Cartograph_druggability_spec.md (this spec).

Build:
1. A server-side druggability service (in the FastAPI app) that, given a target's Ensembl gene id, queries Open Targets GraphQL (https://api.platform.opentargets.org/api/v4/graphql) for tractability and knownDrugs. Confirm the exact field names against the live GraphiQL schema first (do not assume). Optionally cross-check approved drugs via ChEMBL REST by UniProt. Cache responses, set timeouts, handle errors.
2. Pre-cache snapshots for the demo host targets (RAE1, NUP98, TOMM70, G3BP1, and the worklist top targets) into evidence/druggability/<gene>.json with fetch date + source version, committed to the repo, so the offline demo shows real data with no live call.
3. Dossier druggability section: replace/augment the curated tier with the real tractability bucket and the known/approved drugs (name, phase, mechanism, approved flag), each linked out. If any drug is approved, show a labeled "Repurposing lead" badge.
4. Worklist: add a "druggability" and "approved drug" column so the "what to test next" table can sort/filter by repurposing potential.
5. Honesty: label repurposing as a hypothesis not validated for antiviral use; label the source and fetch date; never fabricate; show "no approved drugs" or "unavailable" honestly. Offline with no snapshot and no network degrades to a clear message.

Test: unit tests for the service (parse a real Open Targets response fixture; approved-drug detection; the no-drugs and error cases); the offline demo still works from committed snapshots with the API off; the core regression (Stage 0) still passes.

Adversarial review (fresh subagent): confirm no drug is presented as a validated treatment for the infection; every drug/number links to its real source; no fabricated data; the offline path makes no network call; the locked evaluator is untouched; and the new columns/section do not break the panel-lifecycle or overlap rules from the last pass.

Done: live druggability works in API mode, the offline demo shows real cached data labeled with source + date, repurposing leads are flagged in the dossier and worklist, tests pass, the core did not regress, and docs/REPORT.md is updated with the feature, the sources + data version, and the adversarial findings + resolutions.
