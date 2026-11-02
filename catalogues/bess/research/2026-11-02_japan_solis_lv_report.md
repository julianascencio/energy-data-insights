# Japanese project identities and Solis low-voltage models — 2 November 2026

Started 11:49:39 Atlantic/Canary (UTC), continuing open PR #68 at 6faabe0.
The isolated checkout retains current main 7675a0a and prior BESS work. Read the
workflow, research prompt/data dictionary, canonical schemas, source registers,
coverage manifests and recent research ledgers. Open PR titles and actual paths
were checked: PV #69 is confined to catalogues/pv; #47–49 are workflow updates.
Historical launch reports and Australia/Chile phase holds remain unchanged.

## Accepted batch

Eight Japanese projects were accepted from a six-site IBeeT consortium disclosure
and two detailed project releases. Nine exact Solis models were accepted from the
complete Spanish EU table (five) and Australian-hosted PRO table (four). This is
not nine regional copies: model codes, battery voltage/current, dimensions,
operating temperature and backup limits distinguish EU and PRO hardware.
No existing canonical records were changed. No new country or supplier. Proposed
totals: 1,336 projects / 32 countries / 166 sources; 340 equipment records / 38
suppliers / 119 sources, including 327 configurations and 13 families.
All six geographical regions remain represented; Japan grows from two to ten sites.

The inventory-first attempt refreshed Gore Street's downloadable manager portfolio
and searched Japanese names in Japanese. Susono, Naie and Yufu remain held for
precise identity/location and richer evidence. The manager labels Susono Tokyo;
that is not safely promoted to a site location. A secondary Japanese database
was used for discovery only, never imported as technical evidence. An alternative
primary six-site consortium table supplied six named locations and planned power.
All six columns were reviewed, including their explicit grid-battery scope.

The two Shiroishi projects are distinct: Libra's 45 MW Fukuoka Nagafukuro site
versus the 20 MW / 75.2 MWh Obara site with a different owner. Similarly, Libra's
40 MW Akasaka project is not the separate 67 MW / 230.1 MWh Chikuzen joint venture.
All incoming names, addresses and ownership scopes were reconciled against the
existing two Japanese records and one another; no automatic fuzzy merge.

Consortium costs remain a labelled portfolio total, never project capex. Procurement
by ITOCHU is not battery manufacture. Planned O&M is not an operational assignment.
Japanese fiscal-half periods remain literal forecasts. January 2028 falls within
FY2027 and is not a conflicting COD. Chikuzen has explicit construction evidence;
the seven other projects remain announced. No assumed operation, exact commissioning
dates, MW-to-MWh calculations or unsupported equipment links were introduced.

The equipment rows retain rated active and maximum apparent power separately,
battery operating voltage and current, PV/MPPT limits, backup apparent overload
and switching conditions, cooling, enclosure, environment, controls and safety
claims. Efficiency lower bounds stay lower bounds and are not RTE. External
battery compatibility is not installed chemistry. The EU table's ambiguous Spanish
dimension axis labels remain a literal tuple in extensions instead of normalized
width/depth; no selected field conflict or whole-record rejection was introduced.
There are zero whole-record rejections and zero new conflict quarantines; three
project candidates remain held. Prior unresolved values are unchanged.

## Evidence, access and market context

Five admitted original PDFs downloaded successfully with SHA256 fingerprints.
Model/shared cells and the project table were visually inspected, including the
PRO passthrough-current grouping. Copyright footers and the linked Solis and
Bluestorage privacy policies were inspected. No open bulk-reuse licence is asserted:
only bounded factual observations from the selected public technical/news releases
are committed, not document text, artwork, original layout or binary dumps.
No forms, registration, contact, payments or access-control bypass occurred.
Raw bytes and typed Zstandard snapshots remain outside Git in ignored artifacts.

IEA's 29 May 2026 commentary was reopened on 2 November. The available comparable
country metric remains 2025 annual stationary power additions: China >63 GW,
USA 19 GW, Australia nearly 8 GW, Chile approaching 1 GW. This partial order is
not an exhaustive market ranking; Europe/Middle East aggregates are incomparable
country entries. Operational stationary GWh ranking remains unavailable. The
existing dated market file is preserved without timestamp churn.

The existing upsert API admitted all records; an independent audit confirms every
old record is unchanged and each populated new factual field has a registered
source mapping. No code/schema changes or new parser were needed for this manually
reviewed finite batch. Review IDs, source byte checksums, licensing assessment,
processed partitions and retry actions are in adjacent JSON ledgers.

## Yield and next actions

Candidates: nine equipment → nine accepted; eleven selected Japanese projects →
eight accepted and three held. The selected two OEM tables and three project
releases are exhausted. The yield is below the 10-model/50-project planning targets
because the reviewed tables contain exactly nine models and the defensible project
batch contains eight sites; no variants, phases or thin manager cards were invented
to reach a quota. Final checks and publication follow without idling.

Next: obtain Japanese owner/municipality evidence for Susono/Naie/Yufu, inspect
new IBeeT project releases beyond these processed partitions, and rotate to a
regional battery OEM rather than repeat Solis. Retain the DECC/EirGrid rights and
MEC/phase reconciliation backlog for a later registry attempt.

## Validation and publication reconciliation

PR #68 and PV #69 merged externally during validation. This checkout fast-forwarded
to main `213b573e74fa2bf7072ff5d3b9b367f55fadea24` with no conflict. The new changes
will go to a fresh scoped PR, not the closed PR. The merged PV records are retained.

The full Python suite passed again after reconciliation: **1,607 passed**, one
optional cdsapi skip. Focused BESS suites: **30 passed**; viewer DOM: **8 passed**.
Both catalogue validators, Ruff check/format, ty, repository hygiene, citation
generation, both offline examples and six wheel/sdist builds passed. Independent
typed Zstandard builds match. Source-byte checksum and prior-record/field-provenance
audits passed. The initially reused environment symlink was replaced by a local
locked environment before final repository/full-suite checks.

Pre-publication reconciliation checkpoint: 11:59:47 Atlantic/Canary (UTC),
10.1 minutes actual elapsed effort. Both strict documentation builds passed;
the final regenerated-reference/link audit passed for 397 HTML pages.
No remote CI result for the new commit is asserted.

Publication-ready at 12:00:53 Atlantic/Canary (UTC): 11.2 minutes elapsed. New scoped branch/PR will remain open for review.
