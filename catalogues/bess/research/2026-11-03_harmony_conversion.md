# Harmony portfolio and exact Sinexcel conversion equipment

Started 3 November 2026, 09:47:52 Atlantic/Canary (UTC+00:00). Validation completed at 09:56:53: 9.02 minutes elapsed. Publication follows. The selected batches are exhausted; no idle time was added.
PR99 was already merged; this isolated branch starts from main5063c41. Prior
Australia/Chile reconciliation and all historical research reports remain intact.

## Accepted batch

- Seven new New Zealand battery proposals, zero existing-project enrichments.
- Twelve new exact Sinexcel models, zero existing-equipment enrichments.
- Three project fields quarantined across two records; one equipment efficiency
  field quarantined. Zero permanent whole-record rejections; no new countries/OEMs.
- Totals: 1,796 projects /37 countries /261 sources; 624 equipment records /43
  suppliers /292 sources (611 configurations and13 families). All six regions retained.
- All1,789 prior projects and612 equipment records are byte-for-byte unchanged
  as parsed objects, including IDs, facts, source lists and timestamps.

The owner portfolio has ten named projects. Seven explicitly describe batteries:
Bunnythorpe hybrid and standalone, Hinuera, Tangiwai, Huirangi, Waihou and Opunake.
Bunnythorpe's two separately named pages describe distinct150MWh hybrid/300MWh
standalone scopes and300ha/10ha sites; neither is the NZCE or Meridian proposal.
No automatic match by substation or place name is made. Marton, Carterton and
Tauhei currently describe solar-only capacity: retained as research holds, not
promoted to battery records or declared battery cancellations. Marton's older EPA
application includes battery-container details; the current owner's omission
requires a permit/history reconciliation before choosing a battery scope.

Battery energy, developer, locality, grid/substation, hybrid coupling, site area,
services and explicit consent evidence are retained. Grid-export limits stay in
extensions rather than battery MW. Solar MWp is separate. Animated zero counters
are ignored. The Bunnythorpe hybrid heading says210kV while its narrative says220;
Hinuera says110/33kV and its portfolio/narrative solar ratings differ88/89MW.
These fields remain null with both observations, rather than silently repaired.
A fast-track listing is not a granted consent. Opunake explicitly reports2024
resource consent; no project is promoted to operation.

Eight OEM sheets cover PWS1-160M-H-EX/NA,450M-H-L,225M-H-L,215M-H-X,
PDS1-100M-H, PWS1-2500/2750/3000K-H, PWS1-3150/3450K-H and PDS1-750K-H.
Specifications include DC/bus voltage-current limits and branch options, AC
apparent versus active ratings, dimensions/mass, liquid/air cooling, IP/corrosion,
ambient and voltage derating, protocols, overload conditions and explicit black
start. Transformer ratings and physical dry/oil configurations are distinguished
from converter ratings. PWS1-3000K-H has a3150kVA transformer: this does not become
3000kW battery power. Upper-bound masses remain bounds in extensions. The160M
model dimensions include handles/terminals; excluded dimensions are also retained.
Above3000m derating/customization is not an unconditional altitude ceiling.

PWS1-215M-H-X reports98% on page1 and98.2% on page2: neither is selected.
All conversion efficiencies remain separate from RTE. Manufacturer standard
listings are labelled claims, not independently checked certificates. No battery
energy, chemistry, warranty, project assignments or Cartesian option variants
are invented. Document dates remain unknown; upload paths are not publication dates.

## Source access and method

Transpower's operator listing was freshly reopened and still identifies the
8October2026 release. Its prior bulk-reuse hold remains; this run does not
reimport the41 forward rows. The named-owner alternative led to Harmony's full
ten-card portfolio. Seven explicit battery pages were individually downloaded,
hashed and reviewed. Copyright footer/privacy terms were checked: no open bulk
licence is inferred. Sinexcel's current official download list and copyright
footer were checked; eight sheets individually reviewed. Original bytes remain
outside Git; canonical files contain selected factual observations, not source
prose, images or full PDFs. Download metadata and page/section locators accompany
every accepted field through the source register and field mappings.

Existing upsert APIs accepted this manually reviewed data-only batch. No parser
layout was generalized from the preceding Sinexcel adapter: these sheets have
materially different boundaries and multi-page tables. No code/schema/dependency
change or new implementation-mirroring tests. Typed Zstandard snapshots were
built twice through the existing packages and compared; binary artifacts remain
outside Git. The committed manifest gives field completeness and input/output
hashes. The market file freshly rechecks IEA's29May2026 comparison of2025 annual
GW additions; operational GWh ranking remains unavailable and is not fabricated.

The equipment working objective was met. Project yield is below50 because the
complete owner portfolio contains only seven explicit batteries, three solar
scopes require reconciliation, and the larger operator inventory remains held.
The selected eight OEM sheets and owner pages are exhausted. There is no
purposeful waiting or sparse-record padding to meet a time or record quota.

## Concurrency and next actions

Open DC100 changes its catalogue/viewer, and Wind101 owns shared bibliography
paths. Those overlapping files are deliberately untouched. Sixteen fully formed
reference entries are staged in the companion pending-references JSON; merge
into the shared bibliography after Wind101 settles. Catalogue sources and field
citations are complete now; global bibliography integration is explicitly pending.
No unrelated branch is overwritten or merged by this run.

Next highest-value project work: EPA/MfE Marton/Carterton/Masterton permit and
current owner scope reconciliation, then the other named Transpower applicants.
Next equipment: unprocessed Sinexcel125P/135K tables, with independently reviewed
regional configurations. Resolve the voltage/solar discrepancies before adding
more competing ratings. See the dated ranked backlog for retry conditions.
