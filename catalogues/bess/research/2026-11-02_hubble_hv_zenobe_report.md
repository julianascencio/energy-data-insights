# Hubble high-voltage configurations and Zenobē enrichment — 2 November 2026

Main `ebe18eadc8a04658e9ab5ba17c92e01861f8945c` includes merged PR #63. This isolated pass uses branch `research/bess-database-20261102-0900`. Open PRs 47–49 were inspected by title and changed paths: workflow-only, no BESS/PV overlap. No active workflow runs at discovery. CONTRIBUTING, BESS workflow, dictionaries, schemas, current source registers, previous manifests and backlog were inspected. No AGENTS.md found. Historical Australia/Chile reconciliation is preserved.

## Accepted data

13 new exact equipment configurations: five Hubble HV racks (REV3 V1.3), six HV100Ah stack assemblies distinguished by 3–8 series modules (V1.3), HV 768-215 (V5), HV 768-241 (V1.1). These are physically distinct assemblies, not cosmetic names or generated combinations. All four accepted PDF tables are exhausted. Six PDFs were reviewed in total. Two Energy Block offerings remain held because energy is a configurable range; no arbitrary minimum battery count was paired with maximum PCS power.

Electrical capacity, current, voltage, cell/module counts, operating temperatures, dimensional and mass data, cooling, controls and qualified life claims are recorded. Approximate cycle life and mass remain qualified extensions. Recommended DOD is not a test DOD or usable energy basis. Printed cutoff values are preserved without silently fixing surprising values. No active power is calculated from current/voltage. Claimed certifications, transport codes and cell-level tests are distinguished; warranties and RTE remain unknown. Old rack webpage values are not extrapolated across the explicitly pinned hardware revision.

The scalable-project attempt started with Zenobē's owner portfolio/map, then the five-site Wärtsilä reference table. The public pages have retained copyright and no open bulk-reuse licence; no automated portfolio crawl was performed. Two existing REPD identities match site name, battery MW, location and applicant: Kilmarnock South (REPD 9696) and Capenhurst (12725). They gain 600/100 MWh respectively, services and control-product evidence. Kilmarnock gains integrator and Quantum High Energy product-family evidence; Capenhurst receives GEMS retrofit evidence, not an invented battery-supplier assignment. Native dates, IDs, power and registry observations are preserved. No new project rows were added. Blackhillock phases and Shetland remain held for aggregate/phase and alias reconciliation. This avoids adding duplicate UK registry rows.

Five project candidates yielded two enrichments and three holds. Fifteen equipment candidates yielded thirteen new records and two holds. Zero whole-record rejections and zero newly quarantined fields. No new countries or suppliers. Existing unresolved conflicts remain unchanged. This equipment-led pass deepens a regional African supplier; it does not imply increased geographic project coverage.

## Evidence and market context

Source originals and text remain outside Git. Exact URLs, revisions, retrieval timestamps, page/table locators and original-byte SHA256s are registered. Hubble's marketing page explicitly offers brochures for presentation; this is not described as an open-data licence. Zenobē's policies/footer and Wärtsilä copyright were inspected. No documents, imagery or copied prose are committed. The stack table was visually inspected as well as extracted. The existing importer/upsert API checks IDs and preserves creation timestamps; registry extensions are retained when adding reviewed supplier evidence.

The IEA commentary (29 May 2026) was reopened on 2 November: its comparable metric is 2025 stationary battery power additions, including utility and behind-the-meter, not operational GWh. Among quantified country examples China >63 GW, US 19 GW, Australia nearly 8 GW, Chile nearly 1 GW; Europe 6.2 GW is a region. The existing dated market file remains authoritative for that limited comparison. No comparable worldwide operational-energy ranking was obtained; GW is not converted to GWh.

Current snapshot: 1,322 projects / 32 countries / 153 sources; 305 equipment records / 37 suppliers / 111 sources (292 configurations/components, 13 families). These are catalogue counts, not national capacity totals.

## Yield and next action

The selected source batches are exhausted. Project yield is low because the portfolio mostly identifies already registered sites and unresolved phases; enrichment is preferable to sparse duplicate rows. Equipment yield meets the 10–30 planning objective. Next work is Blackhillock phase/aggregate reconciliation and exact Energy Block order configurations; the backlog includes URL, rights assessment, partition and retry condition. No minimum elapsed time was used as a target.

## Validation and effort

Started 08:58:55 Atlantic/Canary (UTC), completed validation 09:07:15: **8.3 elapsed minutes**, excluding publication. This shorter pass exhausted all four accepted OEM tables and both held family tables, rather than idling to a duration. The inventory attempt did not provide 50 independent admissible projects.

Full Python suite: 1,607 passed, one optional cdsapi skip; 28 focused catalogue tests passed, including after final capacity-scope clarification. Both catalogue validators, Ruff check/format, ty, repository hygiene, citation regeneration/consistency, four viewer tests, both offline examples and all six package builds passed. Strict Sphinx and local-link checks passed for 397 HTML pages. Two independent typed Zstandard builds per catalogue match the committed manifests; originals and binary snapshots remain outside Git. No code/schema change or new parser was necessary.

Pre-publication main remained `ebe18ea`; PR heads 47–49 were unchanged. A concurrent PV process was observed late in validation; its working changes were inspected read-only and scoped to `catalogues/pv/`, with no overlap. No files or branches from that run were modified. These changes will be submitted in a new scoped OPEN PR; no merge is performed.
