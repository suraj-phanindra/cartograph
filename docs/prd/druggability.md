# PRD — live druggability + repurposing (Phase-2 item 5)

**Goal.** Turn a predicted host target into a *repurposing hypothesis*: if a host
protein Cartograph flags already has an approved drug, surface that as a testable
"block this host factor with an existing drug" lead. Display-only enrichment —
never touches prediction, scoring, the locked evaluator, or the frozen split.

**Source (confirmed live, no key).** Open Targets Platform GraphQL,
`https://api.platform.opentargets.org/api/v4/graphql`, **data version 26.06**
(verified via `meta.dataVersion`; the spec's 26.03 was stale). One query by
Ensembl gene id returns both tractability and drug candidates (OT integrates ChEMBL).

**Confirmed schema (introspected, not assumed):**
- `target(ensemblId).tractability` → `[{label, modality, value:Boolean}]`. Highest true `SM` bucket is the small-molecule tractability (priority: Approved Drug > Advanced Clinical > Phase 1 Clinical > Structure with Ligand > High-Quality Ligand > High-Quality Pocket > Med-Quality Pocket > Druggable Family).
- `target.drugAndClinicalCandidates` → `{count, rows:[{maxClinicalStage, drug{id,name,drugType,maximumClinicalStage,mechanismsOfAction{rows{mechanismOfAction,actionType}}}}]}`. There is **no** `knownDrugs`/`isApproved`/numeric phase in this version. **Approved = `maxClinicalStage == "APPROVAL"`.**
- `search(queryString, entityNames:["target"])` resolves a gene symbol → Ensembl id (exact `approvedSymbol` match).
- Drug link: `platform.opentargets.org/drug/<CHEMBL_ID>`; `drug.id` is a ChEMBL id.

**Data contract (normalized snapshot / API response):**
```
{ gene, ensembl, source:"Open Targets Platform GraphQL", data_version:"26.06",
  endpoint, fetched:"YYYY-MM-DD",
  tractability:{ small_molecule:<bucket|null>, antibody:<bucket|null>, buckets:[{modality,label}] },
  drugs:[ {id,name,drug_type,max_stage,stage_label,approved,mechanism,ot_url,chembl_url} ],  # deduped by id
  n_drugs, n_approved, repurposing_lead:<bool> }
```
Unavailable → `{ unavailable:true, reason }` (never a guess).

**Acceptance.**
- Service parses a real OT response; approved detection correct; no-drugs and error cases handled; timeouts + caching.
- Snapshots for the demo targets (RAE1, NUP98, TOMM70, G3BP1) + worklist top targets committed to `evidence/druggability/<gene>.json` with fetch date + version. Offline demo reads these — real data, no live call.
- Dossier shows the real tractability bucket + drugs (name, stage, mechanism, approved flag, link), a "Repurposing lead" badge if any approved, and the source+date label + the "not validated for antiviral use" disclaimer. Curated tier kept as a labeled fallback only.
- Worklist gains sortable/filterable Tractability + Approved-drug columns.
- Live `/api/druggability` works in API mode; offline with no snapshot + no network → "unavailable (source unreachable)".

**Honesty (non-negotiable).** A repurposing lead is a hypothesis, not a treatment
claim — never imply any drug treats COVID/the infection. Every drug/bucket/number
comes from the live source and links out. Label source + freshness. No fabrication.

**Tests.** Fixture-parse (real OT JSON), approved detection, no-drugs, error/unavailable,
offline-from-snapshot, and the Stage-0 core regression unchanged.

**Guardrails.** No import of the locked evaluator/frozen split; core stays green
(Stage 0 after every change); cache + timeout + polite rate-limit.
