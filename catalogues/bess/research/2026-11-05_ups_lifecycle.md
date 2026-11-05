# TAB UPS and South African end-of-life planning — 5 November 2026

Started 16:49:52 Atlantic/Canary (UTC), isolated checkout of open PR172 at
`3fd831364c3f5ccf75088c38be77830eb10ba132`; main `76179409` unchanged.
Current instructions, schema/dictionaries, source register, coverage and previous
research read; all11 open PR titles and changed paths inspected. No BESS overlap,
shared-schema/PV edits, agents, force push or merge. Historical PR44 is not reused.

## Accepted and reviewed

- Equipment: 15 candidates, 15 new exact TAB UPS models, zero enriched existing
  models, zero whole-row rejections/quarantines. One shared printed compensation-unit
  anomaly is quarantined on all15 accepted rows; no normalized coefficient selected.
- Projects: seven existing sites reviewed, seven substantive enrichments, no new
  projects or new quarantines/rejections. No current lifecycle or capacity changes.
- Totals: 2,147 projects /48 countries /404 sources; 1,162 equipment records
  (1,149 configurations,13 families) /55 supplier labels /480 sources.
  No new country/OEM this pass; all six regions retained.
- Cumulative PR:13 new projects,9 enriched pre-existing projects,98 new exact models,
  17 enriched pre-existing Microcare models. Seven project enrichments overlap
  prior PR updates and are not double counted. These are unmerged branch counts.

## Evidence and useful metadata

Official AfDB multi-site project index attempted before isolated press releases;
reader returned402. Original 2021 appraisal returned200, checksum unchanged.
Section3.2.5 on PDF p23 /printed p12 assigns end-of-life decommissioning and battery
recycling to the EPC contractor and describes land restoration after a planned
20-year installation life. Seven previously reconciled named appraisal sites gain
this historical programme-plan context. It is not an executed site contract,
battery warranty, named contractor, retirement date or proof recycling occurred.
Existing facts, conflicts, status, MW/MWh and creation timestamps preserved.

Fresh original TAB brochure returned200, unchanged checksum. Reviewed PDF p8 table
and p9 UPS-specific conditions, including rendered table. Fifteen exact identities
are distinct from prior OGi/OPzS/OPzV models: six12V and six6V monoblocs, three2V cells.
C10 Ah belongs to the catalogued unit; timed W/cell observations at60/30/15/10/5minutes
remain per cell, with separate end voltages and20°C reference temperature. No model
code, kVA, cell count or duration is used to derive energy or whole-unit power.

Added nominal voltage, C10 capacity, timed per-cell power, fault current in kA,
resistance in milliohms, dimensions, dry/wet mass/tolerance, plate/container/terminal
construction, electrolyte density, temperature limits, float/boost conditions,
conditional upper-bound life claims, qualified800-cycle claim, normal-use DoD,
self-discharge, water-refilling and maintenance conditions. Cycle-test DoD/retention
remain unknown; normal-use80% is not substituted. Life claims are not warranties,
and manufacturer standard/protection claims are not independently verified certificates.
The printed -0.004mV/°K compensation statement is held without unit repair.

Existing source IDs reused with unchanged original bytes; fresh retrieval times,
SHA256 and exact page/row locators in captures and record extensions. Copyright
retained; bounded factual review only, not an open bulk-reuse licence. Originals
and typed binary snapshots remain outside Git. No new project-equipment assignment.

## Implementation and next work

New `scripts/stage_bess_tab_ups.py` stages local `pdftotext -layout` output. It checks
all15 identities, mixed Ah/W-per-cell units, discharge times/end voltages, numeric
width and dry/wet ordering. Nine synthetic tests avoid source-document fixtures.
Existing importer/upsert used; seven nested collisions reviewed as strictly additive
patches. Previous facts and creation times preserved, repeat upserts idempotent.

Same-day IEA comparison retained with its original check time: selected-country
2025 utility-scale battery power additions in GW, China/US/Australia. Not an
exhaustive world ranking or operational stationary GWh comparison; no conversion.

The15-model batch meets the equipment planning range. Project yield is below50–200
because the permitted selected multi-site document supplies seven useful existing
project plans rather than new assets. Both selected partitions are exhausted, not
the global backlog. Prior Philippine/CEA/Microcare backoffs and Eskom/Irish rights
restrictions remain respected, without repeat requests. Next equipment: TOPzS
exact-model table after fresh review. Next projects: newer lender IPR or site
technical schedules and an accessible original Philippine inventory. Existing
Chile and other identity/rating holds remain unchanged.

## Validation

Both catalogues, references and natural identities validate. Two independent builds
of each snapshot are byte-identical; typed Parquet readback and ZSTD checked.
Preservation and replay checks pass. Local test/check results and actual elapsed
checkpoint are appended below; full final-head CI is reported in the PR.

Evidence: [review](2026-11-05_ups_lifecycle_review.json),
[captures](2026-11-05_ups_lifecycle_captures.json),
[backlog](2026-11-05_ups_lifecycle_backlog.json),
[markets](2026-11-05_ups_lifecycle_markets.json),
[coverage](2026-11-05_ups_lifecycle_coverage.json),
[manifests](2026-11-05_ups_lifecycle_manifests.json),
[audit](2026-11-05_ups_lifecycle_audit.json).

491 focused BESS tests (nine new cases),25 viewer tests, Ruff/format/ty, hygiene/citations, offline OEM example, three wheel/sdist builds, strict Twine and installed-wheel CLI checks passed. Packaged parser equals validated source. Strict local Sphinx (gallery disabled) and664-page link/asset checks passed; existing wind/hydro publishers regenerated local assets without shared edits. Full local suite not rerun owing prior host Dask/psutil limitation; final-head remote CI reported in PR.

Local validation checkpoint **16:57:41 Atlantic/Canary (UTC)**, **7.8minutes actual effort**. Selected15-model and seven-site evidence partitions exhausted; publication and CI follow. No idle time added.
