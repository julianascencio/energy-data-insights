# BYD and Dyness model-table pass — 1 November 2026

15 new exact configurations: BYD HVS 5.1/7.7/10.2/12.8 and HVM 8.3/11.0/13.8/16.6/19.3/22.1 (BCU2.0 English downloads), plus Dyness Tower Pro TP7/TP11/TP15/TP19/TP23 (20250626 EN). Total: 90 records, 28 supplier brands, 53 sources; 77 configurations and 13 families. Dyness is new; BYD was already present. No existing rows enriched. Publish to existing OEM foundation PR #45 without merging or copying its implementation to the projects PR.

## Evidence and extraction

Three complete manufacturer model tables, 15/15 configurations accepted. The two BYD page-2 table images were visually checked against extracted text; exact model columns, footnotes and source hashes retained. Dyness revision-specific table was read; downloaded original retained outside Git with checksum. All new rows cite each factual field and preserve physical-unit scope. Sources are factual transcriptions, not redistribution of OEM PDFs or assertions of bulk reuse rights.

BYD HVM has two possible module weights and mixed towers: retain weight ranges, not exact scalar mass or duplicated combinatorial variants. Energy is usable DC; no active MW inferred from current/voltage. Filename/download revision and HVM PDF metadata-title discrepancy are noted; no printed revision invented. RTE and warranty left null pending boundary/contract verification.

Dyness 20250626 supersedes the reviewed 20241218 table for this observation: do not blend older voltage/weight figures. Standard charge and discharge temperature envelopes are stored separately, optional heating is not assumed installed. Rated and usable energy stay distinct. The >=8000-cycle claim remains a lower bound with test conditions and unknown EOL threshold, not an unqualified scalar lifespan. System Ah is not cell Ah. Certification lists and a warranty headline are not independently verified certification or warranty contracts.

The older Dyness Tower T7/T10/T14/T17/T21 table is a separate five-candidate review hold because English/Spanish cycle-test DOD and manual voltage definitions differ. These are not Tower Pro and were not inserted. No definitive rejections. Backlog records sources and exact retry conditions. No extra language/revision copies inserted to inflate model count.

## Scope and next step

Selected model tables exhausted; no need to manufacture further configurations. Continue with another absent supplier's model-level industrial/utility catalogue, and resolve the five older Tower candidates before acceptance. Project work added 11 rows and enriched two in PR #44. Country market shares and equipment installed base cannot be inferred from catalogue counts.

Fresh canonical validation, typed Parquet snapshot and coverage manifest generated. Binary artifacts and downloaded PDFs remain outside Git. Initial report and launch summary remain historical. Validation and elapsed effort follow below.

### Final checks (2026-11-01)

Full Python suite: 1,445 passed, five skipped (optional CDS/orbital imagery dependencies absent). Focused tests: 14 OEM/analysis passed. Ruff lint and format, ty with the locked Python 3.13 environment, repository hygiene, citation consistency and diff whitespace passed. Both offline gallery examples executed and matched exported manifest fingerprints. Preservation audit: no deleted rows; old creation dates unchanged; exactly two existing project rows changed, zero existing OEM rows changed. No schema, parser or viewer-code changes; strict Sphinx/browser/package builds were not rerun in this data-only pass.

Elapsed to final validation: approximately 8 minutes (09:45–09:54 UTC). Selected model tables and project batch exhausted; OEM objective met. Bulk project yield was constrained by transient MaStR HTTP 503, not evidence acceptance quotas. Continue with the documented source queue next pass.
