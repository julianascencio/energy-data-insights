# Pylontech exact configurations and Saft project evidence

2 November 2026, Atlantic/Canary (UTC). Run started 00:51:33. Continued open
PR #54 at `2bcc53fc7210d3c95bbb012b693c8508e5e440ff`, based on main `9bab286`.
The current main, catalogue workflows, dictionaries, schemas, source registers,
completeness manifests and recent Philippine, Huntly and Australia/Chile ledgers
were reviewed. PR #55 was inspected by title and all changed paths: PV data and
its ODRE adapter, not BESS. No shared importer/schema or PV record was changed.

## Accepted changes

**Two new projects, two substantive project enrichments, twelve new equipment
records.** No existing equipment changed, no records rejected or newly quarantined.
Three project candidates and seven equipment candidates remain held. Separate
field-level observations retain unresolved edition differences. Two importer
collisions on serialized JSON were explicitly reviewed: only a new Saft namespace
was added; all previous Genesis metadata remained byte-for-byte equivalent.

Current totals: **1,283 projects / 30 countries / 99 sources**, and **184 equipment
records / 32 suppliers / 80 sources** (171 configurations/components, 13 families).
Pylontech is the new supplier; there are no new countries. Existing coverage in
Africa, Asia, Europe, Latin America/Caribbean, North America and Oceania remains.
Counts represent catalogue observations, not an exhaustive census or installed MW.

The French Orbec and Bois Paillet contracts have separate 41MW/92MWh and
14MW/30MWh ratings, respectively. Their 18 and six Intensium Flex containers,
Saft integration, Axpo development, liquid cooling, I-Sight monitoring, services
and forecast delivery are retained. Contract award is recorded as announced with
an explicit commercial-stage extension, not physical construction or operation.
No aggregate portfolio row or exact 3.4/4.3/5.1MWh equipment variant is invented.

Huntly stages 1 and 2 gain explicit Intensium Shift+ model, Saft integration and
generic lithium-ion chemistry from stage-specific supply evidence. Only stage 1
gets the documented 70-container count. Owner status, rating, capex, dates and
existing phase distinction are preserved; stage 2 remains permitted. LFP subtype
is not inferred from secondary reporting or the supplier's usual technology.

Pylontech additions comprise six Force-H3 strings, four Force-H2 strings,
FH10050 battery module and FC1000 controller. Each table column is independently
identified by module count. The module and controller are separately specified
product levels, not additional assembled systems. Canonical string energy uses
the explicitly usable row; total-energy observations retain unspecified basis.
Current limits and their 15-second versus 15-minute duty windows, voltage,
dimensions, mass, DoD, IP rating and communication protocols are preserved.
The H3 manual adds voltage limits and temperature-dependent derating. The module
has explicitly sourced LFP chemistry and series-cell count; the controller has
separate working/system voltage ranges and a strict auxiliary-power bound.

No active power is derived from voltage/current. The manual's 96% efficiency at
0.5C has an unspecified measurement boundary and is not published as AC-to-AC
RTE. Cycle/design-life bounds are retained with their incomplete conditions;
neither becomes a warranty. UL9540A is labelled a listed test method, not a
certification. H2 chemistry remains unknown because the retrieved manual covers
an older configuration/revision. H3 storage limits disagree between the sheet and
manual; no single canonical range was selected. The dated review ledger retains
both source-specific observations and older H2 differences.

## Source selection and limitations

Scalable inventories were attempted before isolated releases. The Philippine DOE
September2024 Luzon indicative inventory was sampled for battery classification,
fields and date. Its reuse terms permit attributed reproduction but restrict
commercial distribution and technical linkages; compatibility with unrestricted
catalogue reuse is unresolved, so no bulk import was attempted. Pumped hydro was
excluded. ERC's newer August2026 inventory returned403. The existing NGCP holds
remain unchanged. No contact, form submission, registration or access bypass was
performed.

Axpo's public owner portfolio supplied three distinct candidates in Switzerland
and Sweden. Later releases show that the Swiss portfolio page is stale and its
8.6MW proposal differs from the8.4MW commissioning disclosure. Axpo and alternative
owner energieUri both require permission for public reuse, so all three candidates
remain held; no Swiss record or country count was added. This blocks the selected
multi-record project batches, not the entire ongoing research programme.

Pylontech's indexed product tables are richer than its currently empty live
product/download HTML. Accessible public distributor mirrors supplied the actual
OEM-authored PDFs, with visible OEM identity, document codes, exact table columns
and SHA-256 hashes. BayWa and PV und so are recorded as hosts, not manufacturers.
The historical H1/H2 sheet and unmatched H3X option combinations were withheld;
no unit typo was silently corrected and no cross-product of options fabricated.
The accepted January2025 tables and H3 manual are fully exhausted for the chosen
ten strings and two components. Newer listed revisions are actionable follow-ups.

Saft releases were readable through indexed primary-source retrieval, but direct
requests returned503. Their exact dates, URLs and locators are registered, with
explicit unavailable-original-byte checksums. These verify the cited historical
release contents, not freshly downloaded source bytes. No full copyrighted PDF,
HTML dump or binary snapshot is committed. Public access is not described as an
open bulk-reuse licence.

The dated market assessment rechecks the IEA's comparable **annual2025 stationary
battery power additions in GW**, with country examples China, US, Australia and
Chile; Europe and Middle East remain separate regional comparisons. An exhaustive
world ranking of operational battery energy in GWh remains unavailable. No MW/MWh
conversion or new-type-storage-to-battery equivalence is assumed.

## Validation and continuation

Candidate-to-accepted accounting: seven reconciled project candidates yield two
new and two enriched records, with three held; nineteen equipment candidates
yield twelve accepted and seven held. DOE/ ERC discovery screens are not counted
as accepted or fully reconciled project batches. Project yield falls below the
planning objective because of specific rights/access blockers; the equipment
objective is met with substantive exact configurations and components.

Both catalogue validators passed. Twenty-eight focused tests, Ruff lint/format,
ty using the project environment, citation consistency, repository hygiene and
four viewer DOM tests passed. Both typed Zstandard Parquet snapshots were built
twice with equal manifests. The identity/preservation audit verifies all previous
IDs and creation timestamps, unchanged existing equipment, unchanged Huntly
lifecycle/ratings/costs and unchanged Genesis metadata. No parser or schema changed,
so no artificial implementation-mirroring test was added.

Next highest-value work: an accessible, suitably reusable ERC/DOE project partition
or grid-operator alternative for the Swiss sites; current Pylontech Force-H3,
US5000 and H3X document bytes; matching H2 manual and explicit warranty conditions;
Saft original bytes and later delivery/lifecycle evidence. The ranked backlog
records version, access, attempt, cursor, retry condition and next action.

Strict Sphinx and executable gallery validation passed; 387 HTML pages passed
local-link checks, and both offline BESS examples ran successfully. The complete
Python suite and package-build checks were not repeated for this data-only change.
Final validation and publication preparation completed around 01:05 Atlantic/Canary,
approximately 14 minutes elapsed: eight minutes discovery/reconciliation and six
minutes implementation/validation/publication preparation. Early completion follows
exhaustion of the two exact configuration tables and component specifications,
with the selected scalable project sources blocked on specific terms/access
issues after alternatives were tried. No time was idled and no counts padded.
The PR remains open; committed additions are not merged main-branch content.
