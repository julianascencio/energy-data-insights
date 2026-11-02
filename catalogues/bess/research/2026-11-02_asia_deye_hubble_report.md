# Asian projects, Deye and Hubble equipment — 2 November 2026

## Starting point and concurrency

PR #62 was merged at 07:20 UTC. This pass starts from main
`5b6b505a8ef08e507484ae156e513ebf0b1f4746` in an isolated checkout on
`research/bess-database-20261102-0810`. Main includes the earlier BESS and PV
work. The three open PRs (#47–49) change workflows only; no active workflow run
was reported at discovery. Repository instructions, project/OEM schemas and
60/73-column dictionaries, sources, latest manifests, recent research logs and
PV conventions were inspected. No AGENTS.md was found. The Australia/Chile
checkpoint is historical; its candidates and withheld phases were not reimported.

## Accepted work

Ten projects are new: Nusantara and Morowali in Indonesia; Qidong Baidishi,
Shujiatang and Nanjing water-facility storage in China; two independently awarded
Sembcorp Indian hybrid battery portions; Wagerup and two Reeves Plains stages in
Australia. One existing project, Sembcorp Jurong Island, gains the owner's dated
100% equity-stake evidence. Its capacity, creation date and prior expansion
history are preserved. Indonesia is new to the catalogue.

The candidate ledger accounts for 23 project scopes: 10 new, one enriched,
five held, and seven company-level aggregates excluded from project admission.
The official owner asset register was attempted before individual releases:
all 15 storage-bearing rows were reviewed, then eight additional named project
scopes were followed through owner evidence. No bulk-reuse licence was found,
and the register mixes sites, corporate portfolios and secured/construction
capacity. It cannot support 50 independent project additions. The five held
site candidates have specific next actions rather than being inflated into rows.

Wagerup's 27 October 2026 owner release explicitly confirms commercial operation
since September: it supersedes a stale undated group construction statement.
Reeves Stage 1 is in construction, while Stage 2 remains in feasibility; no
500 MW aggregate is added. The 194 battery units and 89 inverters are recorded
as unit counts, not assumed cell counts or exact equipment models. The site's
four-hour claim is qualified; no energy is calculated from power alone.

India's two awards remain announced, with buyer, contract conditions, 25-year
term and relative completion target. The 150 MW solar contracts are not battery
MW, and four hours of daily peak service is not treated as measured duration.
Morowali has hybrid construction and financing evidence; battery delivery is not
asserted. Approximate USD210 million cost is explicitly whole-hybrid capex.
Nusantara's 10 versus 14.2 MWh observations and lifecycle discrepancy remain
quarantined; status and energy are unknown. Nanjing is a documented deployed
0.4 MW / 0.4 MWh immersion-cooled demonstration, but operation is not explicitly
confirmed, so status is unknown. No chemistry is inferred from cooling.

Eleven equipment records are new: four Deye BOS-G-Pro strings, its separately
specified battery module and control box, and five Hubble battery models
(AM-4 Revision 3, AM5+, AM10+, AM16+, BLADE). Deye ESS and Hubble Energy are new
product suppliers; no claim is made that either manufactures the referenced cells.
Six selected technical documents were exhausted. Voltage, current, usable/nominal
energy, temperatures, dimensions, monitoring, auxiliary consumption and qualified
cycle/warranty claims are retained. Hubble's unlimited-cycle warranty marketing
is not an infinite numerical cycle-life result. No AC power, RTE or project
assignment is inferred. Components are not counted as complete systems.

Seven equipment fields remain quarantined: Deye G60-Pro DC power; Hubble parallel
limits for AM5+/AM10+/AM16+; and AM16+ discharge current, height and depth. The
versioned brochures and undated pages are retained as separate observations.
AM16 current observations explicitly differ in duty basis (maximum versus
maximum continuous); they are not asserted to be directly comparable.
Approximate masses/design life remain qualified extensions, not exact scalars.
There are no whole-record rejections; exclusions and field holds are separate.

## Rights, evidence and implementation

Deye's separate BOS-G manual has an express restriction on publication of its
information. Its ten inspected configurations are held, and no equivalent-copy
workaround is used. The Pro brochure is a separate document/product batch; only
bounded factual metadata is retained. Hubble's marketing hub offers brochures
for presenting products; this is not represented as a general open-data licence.
Sembcorp/China Power/Alinta rights notices were inspected. No source document,
logo, photograph, account registration or contact submission is committed.
Downloaded bytes and extracted text remain outside Git; accepted-source hashes,
exact URLs, dates, locators and access limitations are registered. An unavailable
original checksum is explicitly null, not invented.

A new offline Deye Pro adapter stages four exact model columns and fingerprints
original PDF/text bytes. It rejects missing/duplicate/reordered columns, wrong
units, malformed values and missing energy conditions. It preserves the printed
G60 power observation for human review and never imports records itself. The
accepted rows use the existing upsert API, with exact identity review against
canonical data and incoming duplicates. No fuzzy merges or schema changes.
The Singapore enrichment preserves original creation time and all earlier facts.

The dated IEA comparison was re-opened: 2025 stationary battery power additions
(utility plus behind-the-meter) rank the quantified country examples China
above 63 GW, US 19 GW, Australia nearly 8 GW, Chile nearly 1 GW. Europe 6.2 GW is
a region, not a country. The established comparison file remains the reference;
no comparable worldwide operational stationary GWh ranking was obtained and no
GW-to-GWh conversion is made. This pass deepens Asia and a regional African OEM,
with non-NEM Australia coverage; existing coverage across all six regions remains.

## Current snapshot and next partition

Totals are 1,322 projects across 32 countries, with 152 project sources; 292
model/component/family records across 37 suppliers and 107 equipment sources
(279 configurations/components, 13 families). These are catalogue coverage counts,
not national installation totals or merged publication claims.

The selected owner register and six accepted OEM tables are exhausted. Project
yield is limited by mixed corporate scope, five unresolved site identities and
source reuse conditions. Equipment yield meets the 10–30 planning range without
using the ten restricted candidates. Next priorities are the held China owner
sites, Nusantara as-built capacity evidence, and Hubble high-voltage models.
The ranked backlog records partitions, retry conditions and expected useful yield.

## Validation and actual effort

Started 08:09:41 Atlantic/Canary (UTC); validation completed at
08:25:18 on 2 November 2026: **15.6 elapsed minutes**, excluding the
subsequent GitHub publication round trip. The selected source batches are
exhausted; this is not a claim of 30–35 minutes of research. Earlier completion
avoids repeating restricted or unresolved candidates merely to reach a quota.

The full Python suite passed **1,607 tests**, with one optional `cdsapi` skip.
The ten new parser tests also passed independently. Ruff check/format (553
files), ty, repository hygiene, citation consistency, four viewer tests, six
package builds and both offline BESS usage examples passed. Strict Sphinx and
local link/asset verification passed for 397 HTML pages. Both catalogue
validators passed. Independent typed Zstandard Parquet builds reproduce the
committed coverage/completeness manifests; binaries remain outside Git. A final
AM16 duty-basis clarification was followed by repeated OEM builds, both
catalogue validations and focused parser tests. No unrun check is represented
as passed. Two initially attempted validator script paths did not exist; the
documented package CLI commands above were used successfully instead.

Pre-publication main and open-PR heads were rechecked: main is unchanged,
PRs 47–49 retain workflow-only changes, and there are no active workflow runs.
A new scoped PR will contain these accepted changes and remain OPEN for review.
No historical launch report or held Australia/Chile entry was changed.
