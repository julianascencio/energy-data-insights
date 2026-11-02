# India owner portfolio and exact SolaX configurations

2 November 2026, Atlantic/Canary (UTC). Started 03:51:02. Continued open PR #60
at `0c55da732a2e8082bcbc11d6653a004566caa282` in an isolated checkout.
Current main was `35f21a304dd4289bfbe3f98e0ead4259cb20f3f6`; its advancement
contains the first PV GEM partition, with no BESS or shared-schema overlap.
Open PR titles and paths (#47–49, #57–60) were inspected, alongside the BESS
workflow, dictionaries, schemas, source registers and recent ledgers. Historical
research checkpoints, Baltic conflicts and all existing rows remain unchanged.

## Accepted work

Five new named FDRE battery portions in India and 23 exact SolaX configurations.
No existing project or equipment row was enriched in this pass. SolaX Power is a
new supplier; country coverage is unchanged. Current totals: **1,297 projects /
31 countries / 115 sources**, **239 equipment records / 33 suppliers / 86 sources**
(226 configurations and 13 families). All six geographic regions remain covered.
These are catalogue observations, not a global installed-capacity census.

## Project coverage, scope and exclusions

CEA's September 30, 2026 BESS inventory was attempted first. Its current listing
was indexed, but the dashboard retrieval timed out, the division page returned
503, and the legacy listing returned 404. No project was extracted from snippets.
The backlog retains the exact endpoints and retry condition; a bounded owner
portfolio was used as the alternative, not a national-coverage claim.

Juniper's live FDRE portfolio contains eight detailed cards representing six unique
contract-project scopes. Beta Six repeats under two dated cards; Stellar II appears
in both operational and construction tabs. Both pairs are consolidated. Five scopes
are accepted: Beta Six, Light Ten, Stellar I, Stellar II and Nirjara. Each has an
explicit battery MWh value, legal project entity, PPA duration and offtaker.

Stellar I and II each explicitly report their full 201.28 MWh battery commissioned
as of October 16, 2026. Their partly built renewable components do not downgrade
battery status. The other three battery portions remain conservatively announced:
construction of the wider hybrid project does not establish physical battery work.
No battery MW is inferred from the renewable MWp, no exact COD from an as-of date,
and no chemistry, grid voltage, coordinates or equipment assignment is invented.
State-level geography describes the contract project; battery distribution across
Rajasthan/Gujarat is unresolved. The scope explicitly says contract-project battery
portion, not a precisely geolocated physical plant. Entity labels are retained as
legal-project metadata, not an inferred ownership percentage.

Cosmic's NHPC contract battery scope is held pending reconciliation with separately
reported merchant Bikaner expansion. The older 100 MWh Bikaner release and 400 MWh
Fatehgarh aggregate are discovery evidence only; neither is added on top of possibly
related contract-project portions. Secondary expansion reports are not used as
technical specifications or current primary lifecycle evidence. Portfolio totals
and unnamed awarded capacity do not become rows. No whole project was rejected.

The portfolio's separate offer-document disclaimer was inspected. It explicitly
concerns the RHP/abridged prospectus; neither was opened and no residence declaration
was made. The ordinary public project cards were reviewed for bounded factual
metadata only. No bulk-reuse licence or right to republish documents is asserted.

## Equipment depth and field conflicts

The OEM-hosted Spanish T-BAT-SYS-HV-S25/S36 manual is Version 0.0, document code
320101113100; publication date is unverified. Its printed configuration tables name
24 strings, not independent options from which combinations were generated. The
rendered PDF pages 10–11 (printed 14–17) were checked against extracted text.

Twenty-three exact configurations are accepted: eleven HS25 and twelve HS36. The
HS22.5 configuration is held because its performance heading reads HS22.2. The
remaining accepted records preserve rounded usable energy at 90% DoD, nominal
voltage, rated and maximum DC power, module/BMS counts, 50 A current limits,
short-circuit current, battery round-trip efficiency and its 0.2C/25°C conditions,
6000-cycle claim with 90% DoD/25°C, temperature-dependent derating, heated versus
unheated thermal envelopes, storage-duration limits and IP65. Expected ten-year
life is not a warranty; battery efficiency is not AC-to-AC system efficiency.
Chemistry and complete-string dimensions remain null rather than being inferred
from a product family page or sums of component dimensions.

Four conflicting numerical fields are quarantined, without rejecting their whole
records: HS10.0 minimum voltage (180/182 V), HS15.0 minimum voltage (270/280 V),
HS32.4 minimum voltage (405/450 V), and HS36.0 nominal energy (36.86/40.55 kWh).
The latter's independently printed usable 33.2 kWh is retained. Values are not
silently corrected by multiplication. Source locators and both observations are
in each record's conflict metadata. No marketing-year or region variants inflate
counts. Model identities were compared with canonical records and within the batch.

## Evidence, market priorities and continuation

The existing upsert API and validators handled the additions without schema changes.
All prior IDs, content and timestamps are unchanged. Exact URLs, publishers, revision,
retrieval timestamp, table/card locator and downloaded-byte checksum are registered.
Original HTML/PDF files and renders remain outside Git. Committed content is factual
structured metadata and review evidence, not copyrighted documents or prose.

The IEA May 29, 2026 source for the existing dated market comparison was reopened.
Its comparable metric remains 2025 annual stationary battery power additions in GW,
not an exhaustive ranking of operational GWh. Among quantified country examples:
China > United States > Australia > Chile; regional Europe/Middle East figures remain
separate. The existing assessment is preserved rather than timestamp-churned.

The bounded owner cards and two exact-configuration tables are exhausted. Project
yield is below 50–200 because national inventory access failed, duplicate cards were
consolidated and overlapping Cosmic/Bikaner/Fatehgarh scopes were withheld. The
23-model batch meets the equipment objective. Next highest-value source is the
recovering CEA September inventory, then primary Cosmic/Bikaner phase schedules and
a corrected SolaX manual. The ranked backlog records partitions and retry conditions.

## Validation and publication

Research, reconciliation and validation completed at 03:59:41 Atlantic/Canary
(UTC), 8.7 minutes after starting, before publication. The selected bounded
batches are exhausted; no idle time was added to reach the planning window.

Both catalogue validators and duplicate/reference audits passed. Typed Zstandard
Parquet was rebuilt twice identically for each final dataset. Full Python suite:
1,545 passed, one optional `cdsapi` skip; 28 focused catalogue tests rerun after the
final data edit passed. Ruff format/lint and ty passed. Strict Sphinx, 389-page local
link check, four viewer DOM tests and both offline examples passed. All three package
sdist/wheel builds completed and all six archives were checked. Repository and
citation checks passed. No schema/importer code was changed. Leave PR #60 open; these
accepted additions are branch content and are not merged into main.
