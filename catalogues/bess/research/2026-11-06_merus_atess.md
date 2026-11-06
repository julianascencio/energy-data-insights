# Merus project references and exact ATESS equipment — 6 November 2026

Started **05:27:33 Atlantic/Canary (UTC)**. This continuation accepts **eight new
projects, one substantive project enrichment and24 exact equipment configurations**.
It adds supplier **ATESS**, with no new country. Finland, Poland and Denmark deepen.
Accepted rows are proposed changes in open PR188, not merged content.

## Current state and coordination

The isolated checkout began at PR188 head
`8703c75b59207cb935fad8164b1a443b2666f2c9`, with main
`036429f93354749517d91ac62b18390ec7bccddc`. PR44 is historical; its AEMO/CNE
identity ledger and withheld Chilean phases are preserved. Current BESS/OEM
workflows, schemas, dictionaries, source registers, coverage and recent research
were reviewed alongside compatible PV conventions. No AGENTS file was found.
At discovery PR188 was the only open PR; its title and40 changed paths were
inspected. Later PR189(PV),190(data centres),191(wind) and192(hydro) were inspected
by title and changed paths: no overlap with this scoped change. Shared schemas,
viewers and other catalogues are unchanged. No parallel agents, merge or force push.

Baseline totals were2,218 projects/50 countries/430 sources and1,289 equipment/
57 suppliers/565 sources. Prior launch reports and the previous Denmark/Hubble
iteration remain historical; their additions are not counted again here.

## Projects: inventory attempt, identities and enrichment

EirGrid's connected/contracted index and5August2026 TSO Non-Wind report were
attempted first. Ten representative rows across the first two pages were screened
for technology, TG identity, node/voltage and MEC. MEC is maximum export capacity,
not battery nameplate; contracted does not mean operational. Two mixed-technology
rows cannot supply battery-only ratings. EirGrid's disclaimer restricts reuse,
while the SmartGrid open-data licence applies only to expressly designated data.
No evidence that this report is designated was found, so **zero rows were imported**.
ESB's owner portfolio was the first alternative: four distinct named sites were
screened, but its explicit copyright restrictions also block ingestion. Fourteen
screened source observations are not fourteen unique new projects.

Merus's reference portfolio provides five explicit BESS cases. All five selected
references were examined: four new installations and one existing enrichment.
Other power-quality/STATCOM references are not classified as batteries. Three
named project releases and the previously held GreenLab site complete the batch:

- **Paistinkulma, Lempäälä:**30MW,110kV Fingrid connection, dedicated substation,
  CATL ENERONE family, Merus EPC/PCS, named sub-suppliers and15-year O&M. Explicit
  November2024 market-entry evidence establishes dated operation. The unnamed
  investor fund is not replaced by its manager as owner. Conflicting36/36.7MWh
  claims leave canonical energy null;60MW/72MWh expansion is not current capacity.
- **Järvenpää distribution centre:**2.6MW/1.55MWh Li-ion,20kV microgrid, solar
  buffering, FCR, peak shaving, backup and maintenance. Customer name is undisclosed;
  building area and generator kVA are not battery footprint or power.
- **Lempäälä Energy Society:**1.6MW/1.3MWh Li-ion,20kV, solar/gas microgrid,
  FCR and gas-generator black start. This is distinct from the30MW standalone site.
- **Merus-owned Lempäälä test facility:**1MW/1MWh, explicit25March2025 operational
  date, ownership, R&D/training applications, wholesale/reserve markets and
  MERUSCOPE. The issuer distinguishes this site from nearby customer installations.
- **Oravainen:**7MW/7.4MWh LFP battery, two20-foot containers, two PCS units,
  transformer MVA, cold-weather design and electric-boiler co-optimisation. Boiler
  heat capacity is excluded. Delivery is described, but explicit operating status
  is absent; status stays unknown. Source one-hour rating is not a derived duration.
- **Neve Rovaniemi:**30MW/80MWh signed supply agreement, end2026 delivery target,
  –50°C design and contracted grid-forming/O&M scope. Status remains announced;
  no construction or operation inferred from the contract.
- **TYMBARK-MWS, Poland:**2MW/10MWh supply contract, EPQS/Merus consortium, solar
  co-location and summer2027 target. Municipality is unknown and not inferred from
  the customer's name; capability claims remain prospective.
- **GreenLab LotA10, Skive:**one host-reported operating BESS site,22MW independently
  sourced from BOS's company page, Eurowind customer/occupant, integration scope,
  hybrid generation and site context.44MWh versus45MWh remains unresolved with
  canonical energy null. No separate1MW test phase, exact COD or container count
  is inferred. Host operating-lot status does not establish independent commissioning.

**Viinamäki Halmekangas** gains6.6MWh,20kV, linked20MW wind capacity, Merus
EPC/integration/PCS roles, maintenance and wind-turbine black-start context.
Existing5.6MW, Simo battery locality and source conflict remain intact; supplier6MW
and wind-farm locality Ii are not silently substituted. This is one enrichment,
not a new phase. Mäntyharju's October trading agreement was already present and
remains byte-unchanged. Two unnamed Riga20MW/40MWh facilities are held until
individual site identities are supported.

Twelve project identity candidates yielded8 new,1 enriched,1 unchanged and2 held.
Three accepted project records carry scoped conflicts, including Viinamäki's
previously flagged power discrepancy. No whole-record quarantine or permanent
rejection was created. Natural identities, aliases, country/site and phase scopes
were manually reconciled; no fuzzy merge or unsupported equipment assignment.

## Equipment:24 exact configurations, one new supplier

Six current, publicly linked English ATESS PDFs were downloaded with checksums.
Every accepted table's page2 was rendered and visually checked against column
order, shared cells, footnotes and component boundaries:

- Five HPS hybrid converters and five PCS bidirectional converters. Separate AC
  rated power, apparent/input ratings, DC charge/discharge limits, currents,
  dimensions, mass, operating limits and model-specific compliance claims.
  PCS1000 retains750kW maximum rectification versus1000kW rated output and
  1154A/1600A charge/discharge limits. Maximum converter efficiency is not RTE.
- Three integrated MatrixOne cabinets:IC261-400S,IC418-690 andIC418-800. Battery
  energy/voltage/configuration, PCS output, cooling, compartment/system IP,
  thermal/altitude derating, mechanical data, protocols and qualified92% maximum
  RTE. Measurement endpoints and auxiliaries remain unknown. IC418-800's printed
  AC range excludes its nominal800V; that range is quarantined, not repaired.
- Two separately identifiable EnerStack100/314 battery modules. Exact model,
  rated energy/capacity, voltage, dimensions/mass, chemistry and C-rate. Complete-
  cluster temperature, IP, cycle, current-A and certification claims are not inherited.
- Nine EnerStack314 clusters,BS96 throughBS225 including exactBS208R spelling.
  Published module counts link to the exact314Ah module record. Energy and
  voltages evaluate the document's explicit per-module formulas, with calculation
  and locator preserved; the rounded energy code is not the numerical energy.
  Charge/discharge temperatures, current/C-rate, DoD, mass, IP and cooling retain
  boundaries. Multi-tower dimensions remain unnormalised where geometry needs
  further review. No power inferred from volts, amps or stored energy.

Cycle claims without conditions remain qualified observations, not warranty or
normalised tested cycle life. Manufacturer compliance labels are not independent
certification; MSDS remains documentation, and ambiguous `UL.UN38.3` punctuation
is preserved. Optional C5, HMI and parallel arrangements do not multiply models.
Conflicting web/PDF parallel limits remain in the review ledger, not accepted
parallel-system configurations.

33 equipment candidates yielded24 new and9 held: seven EnerStack100 cluster
weights contradict the printed55kg component subtotal, and two Merus PCS web
configurations cannot safely map to a1–5MW configurable PDF range. No existing
model was changed. The module-only fact remains explicitly scoped; cluster weights
are not silently fixed. Exact natural model identities were checked against both
canonical data and the incoming batch.

## Rights, evidence and market prioritisation

Twelve project primary sources and six OEM datasheets underpin accepted facts.
Original bytes/checksums remain outside Git; the GreenLab public-reader observation
has no fabricated HTML checksum. DirectHTTP455 was not bypassed. Public access
is not treated as an open bulk licence; copyright remains with publishers.

The initially staged LinkedIn-hosted BOS post was **excluded before publication**
after inspecting clauses8.2.4/8.2.6. Its canonical source and all post-only
commissioning/container-count claims were removed. Independent host/BOS company
facts remain. No social-post excerpt, private contact, full document, artwork or
source table layout is redistributed. No contacts, forms, paid access or registration.

Freshly retrieved IEA29May2026 commentary provides a comparable selected-country
ranking by **2025 utility-scale stationary battery power additions in GW**:
China around55, United States over16, Australia around4.2. Europe4.6 is an excluded
regional comparator. Comparable country operational stationary battery energy
stock in GWh is unavailable in that source; no conversion or GWh ranking is
invented. All six geographic regions remain represented in the catalogue; this
iteration adds European project depth and a Chinese OEM, not projects in every region.

## Implementation, validation and effort

The offline ATESS adapter stages the two five-column converter tables and exact
nine-code EnerStack314 table. Twenty synthetic tests cover shifted/repeated
headers/rows, unit confusion, asymmetric currents, component identity, missing
formulas and rounded-code errors. CLI outputs are exclusive-create and no network
or catalogue mutation occurs. Original-source staging replay succeeded for all
three supported partitions. Manual MatrixOne/module reconciliation complements it.
Existing upsert API was used; Viinamäki's additive namespace collision was reviewed
explicitly without deleting prior fields or nested evidence.

Current totals: **2,226 projects /50 countries and territories /442 sources**;
**1,313 equipment /58 suppliers /571 sources**, comprising1,300 configurations
and13 explicit families. Coverage/completeness and immutable typed Zstandard
snapshot manifests were rebuilt. Both snapshots reproduced byte-identically in
separate external directories. All prior creation timestamps, facts, source entries,
source conflicts and nested namespaces remain unchanged except the documented
additive Viinamäki enrichment. No-op replay leaves updated_at stable; references
and explicit module links validate.

Local checks:627 focused BESS tests,20 new adapter tests,35 viewer DOM tests,
repository-wide Ruff/format/ty, repository hygiene, citation consistency, both
catalogue validators, both offline examples and duplicate/evidence/preservation
checks. Initial lint issues and example-path mistakes were fixed; the actual
examples ran from `examples/database/`. Final rights changes triggered fresh
catalogue validation and immutable snapshot rebuilds. Full local pytest and strict
Sphinx are not claimed because this host previously exhibited a transient-PID
collection blocker; final published-head hosted CI is recorded in the PR.

Research/extraction/reconciliation reached its final accepted-source checkpoint
at approximately **05:52 Atlantic/Canary**, about **25 minutes elapsed**, with
local checks overlapping. Publication and final hosted validation follow; their
actual completion time is recorded in the PR, not guessed here. The project yield
is below50 because the official inventory and owner alternative restrict reuse,
while the selected five-reference battery portfolio is small and unnamed Riga
sites remain held. The24-model accepted batch meets the equipment planning range.
The six selected OEM documents and five BESS reference partitions are exhausted
apart from explicitly held configurations/fields; no duration or count padding.

Next actionable work: resolve EnerStack100 module/cluster weight, identify the two
Latvenergo Riga sites from owner/EPC notices, and establish an explicit licence for
the Irish registry or a permissible alternative. Rotate subsequent registry work
toward underrepresented Asian/African markets. Recheck source freshness and live
heads before continuing. Historical AEMO/Chile and other saved holds remain intact.

Companions: [review](2026-11-06_merus_atess_review.json),
[backlog](2026-11-06_merus_atess_backlog.json),
[captures](2026-11-06_merus_atess_captures.json),
[markets](2026-11-06_merus_atess_markets.json),
[coverage](2026-11-06_merus_atess_coverage.json),
[manifests](2026-11-06_merus_atess_manifests.json),
[validation](2026-11-06_merus_atess_validation.json),
[concurrency](2026-11-06_merus_atess_concurrency.json), and
[cumulative counts](2026-11-06_merus_atess_cumulative.json).

Publication checkpoint **05:55 Atlantic/Canary**: approximately **28 minutes elapsed**
from discovery through extraction, reconciliation, rights cleanup and completed
local validation. Main and PR188 head remained unchanged; all five open PR path
lists were rechecked. Final hosted CI completion and total elapsed time will be
reported in the PR.
