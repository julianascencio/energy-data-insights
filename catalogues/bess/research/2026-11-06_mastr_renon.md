# 6 November 2026 — MaStR partitions1–2 and Renon exact configurations

Started **09:47:32 Atlantic/Canary (UTC)**. This checkpoint was written at
**10:12:06**, actual elapsed **24.6 minutes**, covering discovery,
extraction, identity reconciliation, implementation and local validation to this
point. Publication/final hosted-CI elapsed is recorded in PR193. No idle duration
padding, subagents, forms, contacts, payments, merge or force-push.

## Starting state and concurrency

Current main was `64dcf52278bb942591d16571252e4090963f67a1`; compatible OPEN PR193
head `1639905b14e7bef7c2ae1b346655c5abd87d770a` was continued in an isolated checkout.
PR44 is historical; it was not reused. Current instructions, BESS/OEM schemas,
dictionaries, source registers, workflow, recent logs/manifests and PV conventions
were checked. PR192–198 titles and complete changed paths were inspected; only193
contains BESS writes. Prior main/schema conventions remain unchanged. A final
remote-head/main/open-path check precedes non-force expected-head publication.

## Accepted work versus candidates

| Entity | Reviewed candidates | New accepted | Substantively enriched | Held/rejected |
|---|---:|---:|---:|---|
| Projects |206 threshold candidates from200000 storage units|79|0|30 battery holds;97 non-battery exclusions|
| Equipment |16new exact models +13existing configurations|16|13|8new rows retain field-level holds;0whole-row rejections in this selected model batch|

Both planning ranges are met. The two selected registry partitions and five
selected OEM tables are exhausted; the full30-part unit archive is **not** claimed
complete. No repeated Australia/Chile candidates or historical additions counted.

Projects add **76 registry-operational and3 temporarily suspended** batteries.
Germany rises from27 to106records; no new project country this iteration. Current
catalogue totals are **2315projects /51countries /465sources** and
**1363equipment /60suppliers /591sources**, with1350configurations and13families.
**Renon Power** is one newly represented system supplier. All six world regions
remain represented; record counts are not a global installed-capacity census.

Net kW, gross kW, assigned-inverter kW and usable kWh are retained independently.
Every accepted project has reciprocal SEE/SSE identity and a unique reviewed SEL
within the supplied partitions. Status, first commissioning, network-check dates,
source chemistry categories, region/locality and coordinates are preserved without
inferring commercial COD, ownership, grid voltage, chemistry subtype or equipment.
Exact existing identities were checked; nearest-site pairs and shared SELs were
reviewed manually and held, never fuzzy-merged. Mockrehna, Bexbach and Elverlingsen
pairs remain held despite distinct SEL IDs. Leipzig partitions, Cremzow/Reckertshausen
shared sites, Hilden units, missing-site entries and the1923battery date require
further reconciliation. The complete206-row disposition ledger is committed.

## Equipment and enrichment

Five current Renon originals supply3MPack cabinets,2ECube EPS configurations,
6Smart Matrix configurations,4EBrick-IND stacks and1R-CC01C00800 EMS communication
cabinet. Models are exact printed codes, including the irregular
`R-EB0300161-IND1`; no corrected cosmetic duplicate is invented. The EMS cabinet
appears in two brochures and is represented once. Cells/modules are named only as
components, not invented independently specified products or project assignments.

Data includes explicit energy/power boundary, voltage/current limits, module/string
counts, current/peak time, DoD, EPS conversion efficiency, liquid/air cooling,
temperature/altitude derating, physical dimensions with qualifiers, IP, interfaces,
warranty claims and conditioned EBrick cycle life. Three Smart Matrix A models
retain cover kW versus table kVA holds; four EBrick configurations retain parallel
scope holds, three also have unresolved Ah/energy boundaries. MPack233dimensions
conflict across packaging/specification tables and remain unselected. AC apparent
power is never converted into active power, and conversion efficiency is not RTE.
Cover dates2026-04-22(MPack261) and2026-05-05(Smart Matrix) are explicit; upload-path
dates are not publication revisions. EBrick chemistry remains unknown.

Thirteen previously accepted ATESS configurations gain exact-column AC internal
resistance upper bounds and stated three-level BMS; six BC55NPB configurations also
gain LCD/protection capabilities. Test frequency/temperature are unstated. Existing
facts, IDs, timestamps and the nine-module VoltStack conflict are preserved.

## Access, acquisition and alternatives

MaStR current production index/rights pages explicitly grant XML DL-DE/BY2.0.
Only six selected members were acquired using bounded sequential HTTP Range206
requests. ZIP size and CRC32 were checked against the central directory, and each
original decompressed XML has a SHA256. No whole-ZIP checksum is asserted. Raw
XML, PDF, downloaded-byte captures and Zstandard snapshots stay outside Git.
Official documentation revision26.2 explicitly identifies kW and usable kWh.

WSTECH media downloads require registration; no access bypass was attempted.
The historical REFU PDF returned HTML. Master Battery's brochure exposed Renon
branding and was used for discovery only; no unsupported OEM/rebrand identities
were added. A historical Renon URL returned404, so current linked OEM sheets were
retrieved instead. OEM rights are qualified bounded factual transcription, not an
invented bulk-reuse licence or redistribution of proprietary documents.

The dated IEA comparison was freshly retrieved: selected-country2025 utility-scale
battery power additions rank China(around55GW), US(over16GW), Australia(around4.2GW).
Europe4.6GW is an incomparable regional aggregate. Comparable operational stationary
energy stock in GWh is unavailable in this examined source; no power-to-energy
conversion or unqualified world ranking is claimed.

## Implementation and checks

New offline `mastr.py` / `stage_bess_mastr.py` parses XML incrementally, checks
classification codes, duplicate incoming IDs, numeric validity, source roots,
exclusive reciprocal energy joins and shared-site siblings, including those below
the power threshold. It stages only and never automatically merges/imports.
Eleven synthetic boundary tests cover units, non-batteries, duplicate identities,
missing/multi-unit energy, implausible dates and small siblings. Initial file-handle
warnings/type diagnostics were fixed before publication; final local checks pass.

**654focused BESS tests,37viewer DOM tests, Ruff/format, ty, repository hygiene,
citations and both offline examples passed.** Validators, exact natural/reference
identity checks and replay audit pass. All2236prior projects are unchanged;
1334of1347prior equipment rows are unchanged and the remaining13are additive
technical enrichments. All old source entries and created_at values survive.
Two independent typed Zstandard builds are byte-identical for each catalogue;
coverage/completeness and input/output hashes are committed in dated manifests.
Full hosted Python/package and strict-documentation checks will run on publication;
the previous head's CI is not represented as this update's validation.

## Next actionable partition

Recheck the current production release, reconcile the30battery holds against owner
and later-unit/site evidence, then process MaStR unit partition3 with explicit SSE
joins. Prioritize a non-European official inventory next when its downloadable
battery partition and reuse terms are clear (NZ EA remains a documented alternative).
For equipment, review ECube's exact-model technical agreement and warranty before
promoting retention/throughput terms. The ranked backlog includes source URLs,
versions, rights, fields, processed cursors, retries, outcomes and next actions.
