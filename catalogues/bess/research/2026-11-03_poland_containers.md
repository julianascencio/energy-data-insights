# Poland funding and owner portfolios; BlueNova containers and warranty

Started 3 November 2026 at 13:49:44 Atlantic/Canary (UTC). Continued open PR #102
from `f3f6ba5`, with main `5063c416` as the discovery baseline. Reviewed the
catalogue workflows, dictionaries, source registers, current records and recent
research ledgers. PR #44 is historical; no Australia/Chile candidates were reimported.
PV #103, Wind #101 and Data Center #100 changed paths were checked. Wind overlaps
the shared bibliography, so this iteration queues references in BESS research.
Shared schemas, viewer code, bibliography, lockfile and dependency files are unchanged.

## Accepted records and candidate decisions

**29 new projects: 26 in Poland, two in Senegal and one German distributed
commercial aggregation.** No pre-existing project row changed. Poland is a new
catalogue country.

The NFOŚiGW 24-page ranking contains **479 funding applications**, not 479 battery
projects. The governing [EC decision SA.112460](https://ec.europa.eu/competition/state_aid/cases1/202443/SA_112460_44.pdf),
recital 38, permits any electrical storage technology. Only 28 project titles
explicitly identify batteries; an applicant name containing BESS is insufficient.
Of these, 17 named proposals were accepted, nine identity-ambiguous proposals were
held, and two grant/loan rows were linked to the same investment without adding
assets. Holds cover four Jasin SPVs, a two-battery Strumień proposal, three unnamed
sites and JSW KOKS without a specific plant. Three named Mithra projects retain
500 MW / 1,000 MWh upper limits in extensions, without fabricated phases.

An Energa owner portfolio corroborated nine additional battery projects among
the unclassified applications: eight PV/battery sites and Sompolno. Solar and wind
MW remain separate from battery power; portfolio figures of 467 MWh and over
100 MW are not divided among sites. Four further PV-site names remain deferred
because the owner release describes five projects without identifying every phase.
**442 applications remain technology-unverified.** A 179-row signed-contract table
supplies exact contract IDs, forms and PLN amounts for 13 of the new records.
These are richer new records, not counted again as existing-record enrichments.
Ranking recommendations, contracts, disbursement and construction remain distinct.
Proposed total costs retain 2025, PLN, investment scope and an unknown tax basis.

SENELEC supports Diass at 56 MW / 56 MWh under construction, including financing
and a solar link, and operational Walo at 10 MW / 20 MWh beside 16 MWp of PV.
Ceremonies are distinguished from contractual COD; Diass's expected March 2027
commissioning is not actual operation. Polarium's initial German tolling portfolio
is one commercial aggregation, not 1,600 project rows. Qualified future flexibility
is in extensions; physical nameplate and exact equipment assignments remain unknown.

**Five exact BlueNova configurations** were accepted: two DC battery containers
and three integrated PowerBlocks. Every original sheet was visually reviewed.
Energy at C2 / 25°C, voltage, module arrangement, cooling, enclosure, communications,
fire sensors and dimensions retain their component and measurement scope. PCS
active kW, apparent kVA, transformer ratings, efficiency and derating are separate.
The 5 MW PowerBlock's final energy column says 10,032 Wh, inconsistent with its
10 MWh label and two 5,016 kWh components. Canonical energy is null and the conflicting
observations are retained. No arithmetic repair or mixed-boundary duration is used.

**34 existing exact BlueNova cabinets/racks** gain conditional warranty evidence
from v202604HV, effective 1 April 2026. All seven pages were visually reviewed;
fresh bytes match the earlier downloaded edition. The cell limit is ten years or
6,000 cycles, whichever comes first; electronics have three years. SLA, purchase,
registration, installer, cycle, DoD, temperature and full-charge conditions remain
attached. Applicability is not extended to AIO or BMAC products merely by brand.
For 32 air-cooled models, the 70% year-ten retention table and 80% rebate trigger
remain separate provisions, without selecting one performance guarantee. Sixteen
inherited protection inequalities remain quarantined. The effective date is not
misrepresented as a publication date.

There are zero permanent record rejections this iteration. The ledger separately
counts nine identity holds, two funding duplicates, 442 unverified technologies,
32 warranty ambiguities and one new equipment energy-unit conflict. These are not
all whole-record rejections and must not be added into a single rejection total.

## Evidence, rights and reproducibility

Gov.pl textual material carries CC BY-SA 4.0; an official-material permission
exception is also published. The adapted NFOŚiGW subset has explicit attribution,
licence and modification notices. Unrelated sources are not relicensed. Each
accepted field maps to registered sources with exact URLs, dates, timestamps,
locators and original-byte SHA256 checksums. PDFs and rendered pages stay outside Git.
Other owner/OEM sources are bounded, manually reviewed factual observations, not
assumed open datasets. RWE's section-six reproduction restriction blocked that
portfolio source; the independent Polarium participant release supplied the German
facts. No registration, payments, contacts or access-control bypasses were used.

The new offline NFOŚiGW adapter checks the 24-page / 479-row edition, ten columns,
application IDs, funding forms, numeric PLN and missing recommendation markers.
It stages applications and never merges identities or imports records. Nine
synthetic tests cover layout drift, duplicate IDs, loan/grant distinctions, missing
funding and BESS appearing only in applicant names. The CLI reproduced all 479 rows
from the original PDF using optional pdfplumber, without changing shared dependencies.
The established upsert API accepted new rows and surfaced 34 populated JSON
collisions. Reviewed evidence additions preserve creation dates and existing facts.

Current totals: **1,862 projects / 39 countries / 281 sources; 679 equipment records /
44 suppliers / 342 sources**, comprising 666 exact configurations and 13 families.
All six world regions remain represented. All 1,833 earlier project rows and 640
of 674 earlier equipment rows are unchanged. Both typed Zstandard Parquet snapshots
were rebuilt twice identically outside Git; coverage manifests are committed.

The refreshed IEA comparison uses **2025 annual stationary battery power additions
in GW**, ordered only among quantified country examples. Comparable worldwide
operational GWh and unavailable national ranks remain explicitly unreported;
regional totals are never ranked as countries or converted to energy.

## Validation, yield and next work

The full Python suite passed **1,857 tests**, with one optional cdsapi skip; 37
focused catalogue/parser tests passed. Both catalogue validators, preservation
checks, Ruff, format checking, ty, repository hygiene, existing citation consistency
and whitespace checks passed. Thirteen viewer tests, both offline BESS examples,
strict Sphinx and the 449-page local link/asset audit passed. All three workspace
packages built source distributions and wheels. Remote CI is reported separately.
Shared bibliography integration remains pending: 13 references from this pass bring
the scoped queue to 86. The per-field source register already contains the evidence.

The project yield is below the 50-project planning range because the inventory is
technology-neutral and unresolved identities are excluded. Equipment depth covers
39 exact configurations, including substantive warranty enrichment rather than
cosmetic variants. The selected ranking, contract table, bounded owner portfolio,
five datasheets and seven-page warranty were exhausted for defensible acceptance.
The pass ends before 45 minutes for that reason, not to pad counts or idle. Next:
the latest TAURON battery investment table with current quarterly confirmation,
Energa tender phase mapping, then the remaining Polish technology/identity holds.

Local acceptance and validation completed at 14:15:01 Atlantic/Canary on
3 November 2026: **25.3 minutes of actual elapsed effort**, followed by the
GitHub publication and final remote-state check. All times in data are UTC.
