# Pacific projects and exact Fullriver models

Started **5 November 2026, 22:53:48 Atlantic/Canary (UTC)**. This isolated checkout
starts from main `4ef42de4`; BESS PR #182 had been merged externally. Open PRs
#183–186 were inspected by title and complete changed paths. They cover PV, Wind,
Hydro and Data Centers, with no BESS overlap. Shared schemas, references and viewer
code were left with concurrent work. Repository instructions, BESS dictionaries,
source registers, current coverage, recent logs and historical Australia/Chile
identity holds were reviewed.

## Accepted database changes

| Entity | Candidates screened | New | Enriched | Unchanged | Held | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ADB project components | 26 | 1 | 4 | 15 | 4 | 2 |
| Exact Fullriver models | 30 | 10 | 17 | 0 | 3 | 0 |

The counts above distinguish candidates from accepted canonical records. Four
accepted project enrichments and four new equipment records retain field-level
conflicts; they are not additional rejected identities. No prior records are deleted.

**Haapai OIREP BESS** adds a historical 0.5 MW / 0.66 MWh battery, separate 0.55 MW
solar generation, grid-forming purpose and reported 2017 commissioning year. The
status date uses year-end precision; it is not exact COD or current availability.
Whole-subproject budget and funders remain separate from battery-only capex and
ownership. Chemistry, equipment assignments and exact interconnection voltage stay unknown.

**Atiu, Mangaia, Mauke and Mitiaro** gain sealed lead-acid chemistry, solar ratings,
approximate 50% minimum state of charge and site-specific historical observations.
New energy observations and 2019 completion versus earlier 2018 installation dates
remain conflicts. Existing battery capacity, status, creation dates and EPC facts
are preserved. No usable MWh is derived from the state-of-charge footnote.

**Ten new Fullriver models**—DC7-12, DC10-12, DC12-12, DC17-12, DC20-12, DC24-12,
DC26-12A, DC26-12B, DC38-12 and DC40-12—have rate-specific battery-unit Ah, nominal
voltage, resistance, mechanical observations and exact-sheet charging/temperature
tables. A/B suffixes have distinct printed geometry and rate tables, not cosmetic
variants. Seventeen existing models receive charging and temperature enrichment.

The tables retain recommended versus maximum temperatures for storage, operation,
charging with compensation and charging without compensation. Voltage columns refer
to battery banks, not extra models or operating-voltage limits. Native rounded
Fahrenheit/Celsius compensation values remain separate. No inferred stored MWh,
active power, duration, cell count, warranty, cycle life or certification claim.

## Evidence, conflicts and exclusions

ADB's Pacific inventory portal and Samoa project 58247-003 page returned 403. No
bypass or repeated blocked download was attempted. The alternative August 2022 ADB
report, **TCS220320-2**, was downloaded and checksummed. Its author-attributed tables
are CC BY 3.0 IGO; third-party photographs are excluded. All 26 components in
Tables 3.1–3.3 were screened. Eua's OIREP solar/controller phase and the unquantified
Niuafoou solar-home-system aggregation are excluded. Four Rarotonga/Aitutaki phase
candidates remain held. The prior SPREP Tonga source mirrors the same publication;
it is not independent corroboration.

Fullriver's index, live cards and 28 exact PDFs were freshly acquired. The 18 PDFs
from the previous pass retain identical hashes. DC105-12 charging tables remain
raster and require independent transcription; DC210-12/DC260-12 lack exact current
index links. No suffix substitution or discontinuation inference.

New equipment field holds are explicit:

- DC12-12 prints C1 = 15 Ah, exceeding its C20/C100 values. Visual review confirms
  the print; it is quarantined outside the accepted rate table, never repaired.
- DC26-12A mass and DC26-12B mass/dimensions differ between undated web/PDF sources.
  Affected scalar fields remain unset; both native observations are retained.
- DC38-12 metric/imperial height differs beyond simple two-decimal rounding.
  The height scalar remains unset.

Fullriver retains copyright. Footer/privacy and the prior ordering-policy assessment
were reviewed; this is bounded factual extraction, not an asserted bulk-reuse licence.
No original document, artwork or substantial prose is redistributed. Exact URLs,
titles, retrieval timestamps, locators and original-byte hashes are in source and
capture metadata. Raw evidence stays outside Git.

## Implementation and preservation

The offline Fullriver adapters require exact model headings, labels and units.
The new ADB adapter stages only the four-island Table 3.3 partition. Synthetic tests
reject changed identities, duplicate rows, units, category order and missing
conditions. Staging never merges identities automatically.

Accepted changes use the existing upsert API. Additive nested-JSON collisions were
reviewed; all old nested facts, sources, creation timestamps and unresolved conflicts
are preserved. Empty inputs do not erase facts. Two independent typed Zstandard
Parquet builds are byte-identical, with readback/reference checks and no-op replay.
The 27 model-condition, ten new electrical/mechanical and four island replays match
canonical observations, including the explicitly quarantined anomaly.

## Yield, coverage and next partition

Current totals are **2,150 projects / 48 countries / 411 sources** and **1,202 equipment
records / 56 supplier labels / 515 sources** (1,189 configurations and 13 families).
All six regions remain represented; no new country or supplier. These are catalogue
counts, not national installed-capacity or supplier-market-share estimates.

The market ledger freshly checks IEA's 29 May 2026 commentary using comparable
2025 utility-scale **power additions in GW** for selected countries. It explicitly
cannot provide a comparable operational stationary **energy ranking in GWh**.

The project planning target was not reached: the alternative inventory had only
26 components, most already represented or requiring phase/technology clarification.
Equipment work meets the 10–30 model planning range with ten new models plus
seventeen substantive enrichments. The selected 26-component and 30-model partitions
are exhausted; broader source queues remain. Research and implementation reached
validation after approximately 15 actual minutes, without waiting to fill a duration.

Next: reconcile Airport South/West and Aitutaki phases against utility as-built
records, then review the remaining exact DC model sheets. Preserve existing blocked
source cooldowns, Niuafoou malformed capacity, Atacama and Solar Ray holds. Publication
time, final elapsed effort and executed validation results are recorded below.

## Validation checkpoint

536 focused tests, repository-wide Ruff/format/ty, hygiene/citation checks,
33 viewer tests and the offline OEM example passed. All three packages built
(six distributions); the retrieval wheel contains both adapters and schema.
Full local pytest was attempted but collection stopped in unchanged worldwide
KGPV example code at Dask/psutil process-PID visibility. It is not a full-suite
pass. Strict documentation and final published-head CI results will be recorded
in the PR description; no unavailable check is represented as passed.

Pre-publication validation completed **5 November, 23:13 Atlantic/Canary**, about
19 actual elapsed minutes (roughly 15 research/implementation and four validation).
Strict Sphinx with gallery execution disabled and all 709 HTML-page links/assets
passed; generated BESS/OEM assets match the rebuilt 2,150/1,202-row snapshots.
Full offline-gallery and full-suite CI results are reported separately on the
published PR. The early completion follows exhaustion of the selected batches,
not a claim that the broader research backlog is complete.
