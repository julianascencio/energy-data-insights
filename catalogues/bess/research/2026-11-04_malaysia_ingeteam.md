# Malaysia, Ingeteam and Omburu — 4 November 2026

This iteration started on PR133 head `592bdcd045b25eed2c780e7846b02b5f6e81dbcd`.
PR133 merged externally at13:42:53 UTC. The new work was moved without conflicts
to fresh main `6da869c9e6b990050f614ec0abbc62fd07a43604` on
`research/bess-database-20261104T1346Z`. PR133 and PR44 are historical; neither
closed branch is reused. Main includes the completed previous BESS iteration.
The proposed database adds **two Malaysian projects**, enriches **one Namibian
project**, and adds **16 exact Ingeteam converter configurations**. Nothing in
this iteration has been merged. Malaysia is a new project country; Ingeteam is
one new equipment supplier. No separate OEM entity table was introduced.

Current proposed totals are **2,066 projects/plants, 45 countries and 344 project
sources**, plus **906 equipment records, 51 suppliers and 443 equipment sources**.
The equipment total comprises 893 exact configurations and 13 retained family
records. This remains a researched sample, not a worldwide capacity census.
All six geographic regions remain represented; this pass concentrates on Asia,
African enrichment and European equipment manufacturing rather than US bulk data.

## Project batch and decisions

The official Energy Commission MyBeST statement of 19 December 2025 was reviewed
before isolated project releases. All four bidder rows were reconciled. The
programme total is excluded as an aggregate, and the shortlist does not prove
construction or operation. One row maps to the single BKHM BESS project company
through Blueleaf/Universal Peak's 1 September 2026 financial-close release.
This provides 100 MW/400 MWh, the BOO model, project company, developers, Universal
Peak's EPCC role, UOB financing and a mid-2027 target. Construction is still a
future statement in that source: canonical status stays announced. Its physical
site is undisclosed, so no locality or coordinates were invented.

Three bids remain held. Pekan has 400 MWh regulator/ERS evidence versus a 440 MWh
supplier announcement; no gross/usable or procurement/supply explanation is
assumed. ERS's second site is not identified. Leader's bidder row is not enough
to establish the Pajam site or construction, and its website terms restrict
information reuse. The ledger preserves exact URLs, observations and retry actions.
Original ERS and some Blueleaf pages returned403; public-reader access was clearly
separated from original downloaded bytes. No error-page checksum is a document hash.

Sarawak Energy's owner release provides a second accepted project: Sejingkat,
60 MW/82 MWh, energised December2024 and commissioned by14February2025. Its
150 MW coal host is excluded from battery capacity. The record adds location,
owner/operator, dated lifecycle and reserve/voltage/frequency/peak-demand services.
Chemistry, exact COD and equipment remain unknown. This historical operational
observation does not claim a fresh2026 operational verification.

NamPower's current project portfolio was also checked. Omburu gains explicit
energy-arbitrage, emergency-energy and grid-stability applications. Every old
rating conflict, timestamp basis, site fact and source remains intact; no overdue
forecast was promoted to operation. Adjacent solar and biomass entries are not BESS.

Six project candidates were reviewed: two new, one enriched and three held.
The lower project yield is explained by a four-row official cohort, unresolved
identities/ratings and reuse/access limits. The selected defensible project
sections are exhausted. Next scalable source remains Portugal's41 final award
IDs: map them to named sites using reusable permitting/owner evidence before
acceptance, and refresh the2026 programme. No previous award rows were reimported.

## Equipment batch and technical boundaries

Three public, product-linked Ingeteam PDFs were downloaded and checked visually:
M Series revision300002287_C, C Series HV300001994/F and350TL300002273_A.
The eight named M600/M630/M660/M690 M3/M4 configurations and seven C600–C840
configurations are separate. The350TL's eleven AC-voltage operating points stay
inside **one** model record, not eleven cosmetic variants. Thus26 table columns
produce16 canonical configurations. Existing and incoming natural identities were
reviewed; no automatic fuzzy merge, rebrand or project-equipment assignment occurred.

Specifications preserve grid-tied/off-grid DC minima, AC voltage/current,
charge versus discharge kVA at30/40/50°C, module/input counts, cooling,
standby/auxiliary boundaries, optional heating, humidity, altitude restrictions,
IP exceptions, dimensions, conversion efficiencies and explicit warranty terms.
C Series explicitly supports grid forming. All three advertise black-start
functions.350TL interfaces include Wi-Fi and Single Pair Ethernet. C Series'
five-year warranty statement is qualified; contractual exclusions are unknown.

Apparent kVA is never converted to active MW. Converter efficiency is not battery
AC-to-AC round-trip efficiency. Battery energy, chemistry and duration are null.
The M Series protection-page discrepancy and printedIEC61477-1 are withheld from
canonical protection/certification scalars.350TL's marketing350kW is not assigned
to the346kVA operating point. Standards are manufacturer claims, not independently
verified certificates. No publication date was inferred from the2026-05 URL path.

Four Delta EPCS IEC candidates were examined but held: the public reader exposes
model columns, while original public PDFs return503 and the principal filecenter
redirects to terms verification. Neither gate nor service failure was bypassed.
Ingeteam's older Portals PDF URL returned homepage HTML; it was not parsed as PDF.
The next independent equipment partition is the current430DC-DC product sheet.

Copyright and terms were inspected. Ingeteam prohibits copying the site; this
limited review retains independently structured factual specifications with
attribution, not copyrighted prose, tables, layout or full documents. No open
bulk-reuse licence is asserted. Malaysian owner/regulator facts are similarly
bounded and attributed. Leader and HyperStrong restricted material is used only
for discovery/access/conflict assessment, not document redistribution. Raw source
bytes, checksums and original documents remain outside Git.

## Implementation and validation

The new offline Ingeteam adapter and CLI accept local `pdftotext -layout` text,
check reviewed revisions/headings/units/columns, separate temperature/direction
ratings and consolidate350TL operating points. Synthetic tests exercise swapped
headers, units, missing columns, zero values and revised documents without
redistributing OEM fixtures. The existing upsert API creates records and fills
Omburu's previously empty applications field. No schema or shared importer changes.

Both catalogues validate and build typed Zstandard Parquet snapshots through the
existing package. Two independent builds are compared byte-for-byte. The adjacent
manifest and coverage files contain current hashes, completeness and country/supplier
counts; the preservation ledger checks all old facts, evidence, conflicts and
created_at. Offline project and equipment examples are exercised. Actual check
results and timing are recorded in the validation ledger; no remote-CI or online
full-gallery claim is implied.

The fresh IEA29May2026 commentary HTML and embedded2025 chart were rechecked.
The comparable metric is **annual utility-scale battery power additions in GW**:
China55.10, United States16.22, Australia4.32 among the chart's named countries.
Europe5.69 and MiddleEast2.87 are regional values, not country ranks. No comparable
worldwide operational-stationary-energy GWh table is available from this source.
Malaysia/Namibia are unranked, and earlier narrative/chart discrepancies remain.

Open PR titles and complete changed paths were inspected for PV142, HVAC141,
Kazakhstan140, DataCenters139, Wind137, BESS133 and dependency PRs49/48/47.
No other BESS path overlap was visible. Seven new bibliography records are queued
within BESS because concurrent Wind work touches shared references. Before
publication, main, the target head and relevant PR paths must be rechecked; create
a new scoped PR from current main and leave that research PR OPEN.

Started13:22:54 Atlantic/Canary (UTC on this date). Disk exhaustion interrupted one
scratch-script write. Investigation found171 stale temporary NCCL shared-library
copies from an earlier environment; those copies were removed while preserving
the installed library, source evidence and canonical data. The empty scratch
script was rewritten and all subsequent results validated. No idle padding,
parallel subagents, unrelated source edits or timestamp-only commits.

Final validation completed **13:53:29 Atlantic/Canary**, after **30.6minutes** of actual elapsed effort. The rebased full suite passes **2,381tests**, with five optional skips;349BESS tests and15viewer tests pass. Strict documentation and the final post-export link audit pass **572HTML pages**. Initial documentation attempts were killed after rendering; an incremental retry with other heavy checks finished succeeded. A premature link audit was superseded by the successful post-build audit. Publication follows; elapsed time here excludes the final GitHub mutation.
