# Freedom Won lifecycle and African mini-grids — 2 November 2026

Started at 12:48:34 Atlantic/Canary (UTC). PR #70 had merged externally at
12:40:47, so this isolated checkout starts from main `b5194488`. Open PR titles
and changed paths were checked: #47–49 only concern GitHub workflows. The BESS
workflow, OEM research specification, dictionaries, source registries, current
coverage manifests and recent Japanese/Solis and earlier regional research were
reviewed. Historical launch totals and Australia/Chile holds remain unchanged.

## Accepted records and reconciliation

This pass adds **five projects** in two new countries, **Kenya and Nigeria**,
plus **13 exact Freedom Won equipment configurations**. It substantively updates
**ten existing LiTE 2 Commercial records**: the current OEM index explicitly places
these exact models below its legacy/end-of-life heading. Their classification is
now `historical_document`; all technical values and original creation dates remain
unchanged. Freedom Won was already represented, so there is no new supplier.

Totals are **1,341 projects / 34 countries / 170 sources**, and **353 equipment
records / 38 suppliers / 127 sources** (340 configurations and 13 families).
All six geographical regions remain represented. Country counts are coverage,
not a claim of national completeness or operational capacity.

The new equipment comprises four LiTE Home Model A 52 V batteries, three LiTE
Business 52 V batteries, two LiTE Commercial 52 V batteries, and Encore 3K/5K/8K/10K
hybrid inverters. Each model is a named column or individual datasheet; no fabricated
option combinations or cosmetic regional variants. LiTE, LiTE 2 and HV identities
remain distinct. The records add energy and DoD alternatives, continuous/maximum
power and current, voltage, dimensions, mass, enclosure, controls and warranty/life
conditions. Commercial chemistry/cell capacity/cooling are explicitly sourced;
Home/Business chemistry remains unknown. Battery Ah is not mislabelled as cell Ah.

Encore active power remains null because the manufacturer specifies kVA. External
battery compatibility is not installed chemistry. Conversion efficiencies remain
qualified claims, not round-trip efficiency. Individual model sheets resolve the
overview's merged columns; the broader range-level grid certificate list is not
extrapolated onto 8K/10K. LAN and the Wi-Fi-only monitoring gateway are preserved
with their separate scopes, without asserting wired Ethernet. The Commercial
52 V extraction's unlabeled 96–97 efficiency figure is withheld.

The project batch is Oloibiri, Akipelai, Ndeda, Kalobeyei Town and Kalobeyei
Settlement. Owner evidence establishes batteries and operating mini-grids; UNITAR's
2023 field-research report adds Kalobeyei's technical and commercial context.
The two Kalobeyei systems are distinct. Settlement's original 120 kWh appears only
as history; the built 1.1 MWh system is one canonical record. The later financed
5 MWh expansion across Kakuma/Kalobeyei is not assumed complete or added again.
A combined 180 kWh Nigerian announcement is not divided arbitrarily between sites.
PV and wind capacities stay in co-location fields, never battery MW. No equipment
was assigned to these projects without evidence.

The importer/upsert API accepted the new records. Its ten lifecycle collisions
were reviewed explicitly using the current OEM index, then resolved through the
API's documented explicit-edit path. These are dated lifecycle reclassifications,
not unresolved numeric conflicts. There are **zero unresolved conflict quarantines
and zero whole-record rejections**. Seventeen portfolio sites and five legacy HV
model candidates remain held, separately from accepted records. A local validation
caught duplicate copies caused by mixing country-based and UUID-prefix project
shards; the staged copies were removed before publication. No canonical old project
record was changed.

## Scalable source attempts, access and ranking

The owner portfolio was the first scalable source: all **22 named site entries**
were reviewed. Five were accepted; the other 17 lack explicit site-level battery
evidence in that page. Ngurunit has a secondary 144 kWh lead requiring owner or
GIZ/EnDev confirmation. Ozuzu also has a Cross River heading versus Rivers State
text inconsistency. REA's 2022 impact-report inventory was examined through discovery
and representative named rows: 67 solar-hybrid sites are a high-yield next batch,
but PV kWp and hybrid wording do not establish battery ratings or technology.
No bulk extraction was performed without classification and reuse review.

Freedom Won's download index, June 2025 trade terms and PDF ownership notices,
Renewvia page footers, and UNITAR's copyright/publication notice were inspected.
No open bulk licence is asserted. This finite pass commits factual observations
and evidence metadata, not original text, artwork, layouts or PDF dumps. Normal
Freedom Won byte requests returned HTTP 403; primary-document text was available
through the search service. These sources explicitly have **null byte checksums**.
Error-page hashes are not represented as PDF hashes. Model-specific sheets avoid
relying on ambiguous merged-column extraction. The owner pages and UNITAR PDF
were downloaded successfully and SHA256-verified outside Git. No controls were
bypassed, no registration/contact/payment was attempted.

IEA's 29 May 2026 primary commentary was reopened. The dated comparable metric
remains **2025 annual stationary battery power additions**, not operational GWh:
China just over 63 GW, USA 19 GW, Australia nearly 8 GW, Chile approaching 1 GW.
This is a partial order among quantified country examples, not an exhaustive world
ranking; Europe and Middle East totals are incomparable country entries. A comparable
operational stationary energy GWh ranking remains unavailable. The established
`2026-11-02_dyness_baltic_markets.json` is retained without timestamp churn.

## Yield, implementation and next partition

Candidates: 22 portfolio sites → five accepted / 17 held; 18 new model candidates
→ 13 accepted / five HV models held. Ten existing equipment identities were reviewed
and enriched. The selected defensible model tables are exhausted. Project yield is
below the 50–200 planning range because the inventory mostly says solar mini-grid
without confirming batteries; no thin inferred battery rows were added to meet a
quota. The 13 exact models meet the equipment planning range. Work proceeds to
validation and publication rather than idling to fill the allotted time.

Next priority: REA's named NEP/PBG inventory with site-specific battery procurement
records and a source-reuse assessment; then Ngurunit's primary technical evidence,
Kakuma/Kalobeyei expansion scope and commissioning, and the individual legacy HV
sheets. The ranked backlog records URLs, versions, access, offered fields, processed
partitions and retry conditions. No schema or parser change was needed for this
finite manually reviewed batch, so no implementation-mirroring tests were added.

## Validation

The full Python suite passed: **1,607 passed**, one optional cdsapi skip. Focused
BESS suites: **30 passed**; viewer DOM: **8 passed**. Both catalogue validators,
repeatable typed Zstandard builds, old-record/timestamp/provenance and downloaded
byte checksum audits, Ruff check/format, ty, repository hygiene, citation exports,
both offline usage examples and six wheel/sdist package builds passed. No new
parser or schema was introduced. Remote CI for the forthcoming commit is not
asserted. Strict documentation and link validation are completed before publication.

Strict documentation build passed. The first link audit overlapped final dataset
copying; the audit was rerun after build completion. Publication checkpoint: 13:05:22
Atlantic/Canary (UTC), **16.8 minutes** actual elapsed effort. Selected defensible
source batches are exhausted; remaining candidates have explicit evidence blockers.

Completed documentation/link audit passed for **397 HTML pages**. Main remained
`b5194488`; open PRs #47–49 still touch only workflow files. No overlapping active
BESS or PV research branch was visible. The new PR remains open for review.
