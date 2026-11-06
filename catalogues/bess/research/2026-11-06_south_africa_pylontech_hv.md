# South Africa project lifecycle and Pylontech/Solar MD exact equipment

Started6November2026 at01:57:15 Atlantic/Canary (UTC). This continuation uses the
isolated current head of open PR187, `2b404de7efb1410d72ca060f4eeb2f2099332129`,
against main `4ef42de474f69b5cdca5824410c06db0d851b434`. PR44 is historical and was
not reused. Main and branch instructions, schemas, dictionaries, source registers,
coverage/manifests, original Australia/Chile review, latest research logs and PV
conventions were read. Open PR183–187 titles and changed paths were checked.
No overlapping BESS writes were visible; no subagents, merge or schema changes.

## Accepted facts and boundaries

- Projects: six named candidates in the licensed ministerial reply; **one new
  project, three substantive enrichments, two non-battery exclusions**. Komati is
  a150MW battery project in tender as of the signed19September2026 reply. The
  forecast tender conclusion is not an award or operation. Its72MW PV component
  and Lethabo75MW PV are excluded from battery capacity. Energy/chemistry remain unknown.
- Skaapvlei, Paleisheuwel and Graafwater retain prior scalar ratings/status and
  gain dated90%,40%,70% completion observations, missed prior target and explicit
  FY27 no-grid-addition expectations. Possible contract termination/replacement
  remains a contingency, not an executed event.
- Equipment: **18 exact candidates reviewed,15 new records accepted, zero existing
  equipment enrichments**. Eleven Pylontech records: six Force-H1-V2 single strings,
  FH48074, two exact PowerCube racks, H48050 and H48074. Four Solar MD records:
  SS214 module, SS4160, SS4083 and Logger V2. Solar MD is a newly represented
  South African manufacturer; CATL/CALB are separately identified cell suppliers.
- **One whole model quarantined**: US2000C's manualp10 and appended brochurep42
  disagree on mass, dimensions, current limits and altitude. Two controller models
  are deferred for substantive electrical ratings. These three are the held18-to15
  candidates; no duplicate optional parallel or rack-range configurations created.
- **One accepted record has a field quarantine**: SS4083 reports7.5kW at0.7C with
  8.3kWh. The power/C-rate condition is inconsistent if interpreted as energy-based
  C-rate. Native claims/evidence remain in conflicts; normalized power and duration
  stay null. Its independently stated chemistry, energy, voltage/current limits,
  dimensions, mass, cell supplier and operating conditions are retained.

Each accepted field maps to source IDs with exact URLs, publisher, printed revision
or explicitly labelled URL edition, retrieval timestamps, original-byte SHA256 and
page/table locators. Original files and rendered review images remain outside Git.
All eight Pylontech system-to-module links validate; no project-equipment assignments.
Force-H1-V2 is distinct from oldForce-H1. PowerCube's exact printed model overrides
a misleading distributor index label. Printed rounded kWh is not recomputed. System
IP/current/mass are not assigned to modules. PowerCube current units are unstated and
stay native; nominal/peak power is not inferred from current. Efficiencies96%/95%
with unspecified boundaries are not round-trip claims. Solar MD99% is charging-only.
Lifetime is not warranty; compliance lists are qualified manufacturer claims.
Logger V2's12-month standard product warranty is separate from battery energy warranty.
Its9–65V supply, USB-C5V2A, isolated ports and relay ratings are controller facts.

## Source batches, reuse and exclusions

The scalable source attempt was Eskom's2026 owner inventory/performance reports:
eight named sites screened. Eskom website terms2.1/2.2 restrict non-private reuse
and2.10 prohibits automated collection. **Zero records accepted from those reports**;
source bytes/text were discarded, metadata/checksums retained. Independently
published Ministry reply4150 via Parliamentary Monitoring Group supplies the
accepted project facts under PMG's CC BY3.0South Africa policy. The attribution
notice and precise source mapping are committed. Two PV entries were rejected.
The World Bank2023 Komati factsheet was read as historical corroboration, not used
to assign whole-transition financing to battery capex or old hybrid ratings.

For OEMs, two Pylontech manuals and four Solar MD technical sheets supplied the
accepted records. Individual numeric facts were reviewed with copyright/host terms;
this is not an assertion of an open bulk licence. No copyrighted manual, image or
installation instructions are redistributed. Getpylon-hosted oldForce-H1 material
was excluded after its automation terms were found; bytes were discarded. An
independent official Pylontech S3 download supplies the separate V2 model. Bornay's
indexed manual returned a distributor brochure and was excluded. Solar MD's public
resources index and linked sales/IP terms were checked before bounded extraction.
The US2000C combined document remains quarantined. Unnamed BMS/BMU and optional
CB35/36/39 rack ranges are deferred without multiplying capacity ranges into models.

IEA's29May2026 commentary was rechecked. The comparable selected-country metric is
**2025 utility-scale battery power additions**: China about55GW, US over16GW,
Australia about4.2GW. Europe4.6GW is regional, not a country rank. Comparable
operational stationary battery energy in GWh is unavailable in that source.
No power-to-energy conversion or completeness inference from catalogue counts.
Africa is deepened while all six world regions remain represented; no new country.

The four-project yield is below the50–200 working objective because the larger
owner inventory fails the reuse gate, the licensed alternative has only four
battery entries, and existing identities warrant enrichment. The15-model yield
meets the10–30 planning range. The selected six usable technical documents and
licensed project-reply partition are exhausted; no idle time or count padding.
The ranked backlog preserves exact URLs, versions, rights, fields, reviewed
partitions, results, retry gates and next actions. Highest next equipment partition:
Solar MD SS216/SS6160/SS70xx exact tables. Highest next project source: fresh licensed
South African parliamentary project updates and World Bank Komati restructuring,
with battery-only scope; retain previous DOE, Chile, AEMO and Fullriver holds.

## Implementation and validation

The new offline Force-H1-V2 adapter stages local table arrays and rejects changed
identity/revision, components, units, configuration order/count, dimensions and
voltage bounds. Eleven synthetic parser tests cover these failures without copying
the original tables into tests. The existing importer/upsert API is used. The three
additive project extension collisions are reviewed explicitly; prior facts, sources,
conflicts and created_at are preserved. New IDs and incoming natural identities are
checked against the canonical catalogue. Empty values do not overwrite facts.

Current totals: **2,208 projects /48countries /414sources** and **1,254 equipment
records /57supplier labels /550sources** (1,241configurations,13families).
Cumulative PR counts versus main: **59new projects,23pre-existing project enrichments,
62new equipment records,17pre-existing equipment enrichments**. Present increment:
1new project,3enrichments,15new equipment; none merged.

Local checks: **575 focused BESS tests**, including11new parser cases; **34viewer
tests**; repository Ruff/format/ty, hygiene/citations, both offline catalogue examples,
source/reference/preservation/no-op checks. Two independent typed Zstandard snapshots
per catalogue are byte-identical. Snapshots remain outside Git. The validation ledger
records final checks; full Python/package and strict full-gallery docs are verified
through published-head CI rather than claiming a new full local run. Local disk
headroom is limited; existing shared-workspace outputs are not deleted.

Research, extraction, reconciliation and overlapping validation used approximately
20minutes through02:17 Atlantic/Canary. Publication and wider CI follow. Actual final
elapsed effort and exact-head hosted results are recorded in the PR final verification.
The separate validation ledger distinguishes local passes from pending hosted checks.

Publication checkpoint: data/code commit `17e7abccb9289c466ba972d8374cfc6afd9fe8f4`
was published at02:21 Atlantic/Canary, approximately24minutes after this run began.
All26blob hashes and full tree `5e4e5b1241a67e9cbb106051664ca53cc197f4a5`
matched the reviewed local index. A follow-up updates stale documentation landing
counts/navigation; historical launch reports remain unchanged. Final hosted CI and
actual final elapsed effort are reported in PR187; this checkpoint does not claim
pending CI has passed.
