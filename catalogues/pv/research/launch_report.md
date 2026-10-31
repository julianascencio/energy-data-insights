# Launch research — 31 October 2026

## Accepted evidence

The launch combines machine-readable official equipment libraries, a government
plant inventory and individually checked OEM/owner publications. Counts are in
[launch_summary.json](launch_summary.json); every accepted row resolves to an
entry in [sources.json](../sources.json).

| Table | Accepted records | Basis and limits |
| --- | ---: | --- |
| Modules | 21,605 | 282 manufacturer labels in pinned SAM/CEC library; not current worldwide market availability |
| Inverters | 2,344 | 2,343 SAM/CEC entries plus a configuration-specific Sungrow SG350HX extract; 152 manufacturer labels |
| Trackers | 5 | Nextracker NX Horizon, Soltec SF7/SFOne, Arctech SkyLine II, TrinaTracker Vanguard 1P |
| Combiner boxes | 3 | Phoenix Contact 1694150; Weidmüller 8000081269 and 8000078118 |
| Projects | 7,320 | 7,309 EIA plant IDs, one reconciled Topaz owner record, 11 other projects in 10 other countries |

Project country codes: ARE, AUS, CHL, EGY, ESP, FRA, IND, MEX, MLI, USA and ZAF.
Regions represented include Africa, Asia, Europe, North America, South America and
Oceania. This is geographic breadth, not complete coverage. Small projects, many
countries, trackers and combiners need substantial expansion.

## What the launch actually downloaded and parsed

1. [SAM libraries](https://github.com/NatLabRockies/SAM/tree/784177b634fa1475fda6672b70595e087a238aea/deploy/libraries),
   pinned at `784177b634fa1475fda6672b70595e087a238aea`. The source register preserves
   SHA-256 hashes for `CEC Modules.csv` and `CEC Inverters.csv`. The module rows
   report library version 2026.7.3 and source dates; date fields are not relabeled
   as the retrieval date. The
   [CEC program](https://www.energy.ca.gov/programs-and-topics/programs/solar-equipment-lists)
   remains the upstream listing authority.
2. [EIA-860 report year 2025](https://www.eia.gov/electricity/data/eia860/),
   archive hash `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba`.
   Plant and solar workbooks are joined by Plant Code. Only `OP`, `PV`,
   `Solar Photovoltaic` rows enter totals. Every retained generator's nonempty
   metadata is nested in its plant row. The archive's instructions define nameplate
   power as AC, and DC net power as the sum of module ratings at STC. Missing
   component capacity prevents an apparently complete total. Generator dates,
   tilt/azimuth and technology flags are not assigned to an entire plant by taking
   the first row. [EIA reuse policy](https://www.eia.gov/about/copyrights_reuse.php)
   permits reuse with source acknowledgment.
3. OEM and project facts were extracted from the exact URLs in the source register.
   Complete copyrighted PDFs, marketing text and images are not redistributed.
   Published options, upper bounds and approximations remain qualified. Tracker
   product families without public configuration sheets remain intentionally sparse.

The pinned SAM license is retained in `licenses/SAM-BSD-3-Clause.txt`. Generated
snapshots carry this notice and the source registry; repository software licensing
does not replace source-specific terms.

## Research findings that changed the design

- **36 conflicting module names / 72 rows:** SAM has duplicate exact names with
  different PTC, temperature and fitted model parameters. All affected rows are
  preserved in `launch_quarantine.jsonl` and excluded from accepted module records.
  No arbitrary first-row selection. Case-distinct OEM suffixes are preserved because
  changing case can change a product; these require future identity review.
- **Topaz rating and date differences:** BHE's current project page reports 550 MW
  without an AC/DC basis; EIA's five operating PV generators total 585.9 MWac and
  752.1 MWdc. These are preserved as different, unresolved rating bases, with a
  review status. BHE's 2014 text and 2015 operational-year panel remain documented
  in extensions. Topaz is one row, with EIA Plant Code 57695 and both sources.
- **Configuration is essential:** Sungrow's SG350HX document lists a standard
  12-MPPT version and optional 14/16-MPPT versions. The accepted row is explicitly
  the 12-MPPT version. Its 352 kVA at 30°C is not entered as 352 kW. Optional weights,
  temperature limits and tracker rotation choices are not combined into a false SKU.
- **Project phases differ from complete projects:** New England Solar has an
  operating 521 MWdc / 400 MWac first stage and a separate pipeline second stage.
  Only the operating first stage enters top-level capacity; stage and BESS details
  remain nested. Benban is a park-level row, not a duplicate Scatec subportfolio.
- **Current ownership cannot be inferred from an old article:** the Kita source
  records Taranis's 2025 acquisition; old Akuo references are not treated as current
  owner evidence. Historical Sishen technical facts do not assert today's owner.
- **Source checking is not field inspection:** `last_verified_at` records when a
  source was accessed. The EIA report-year status remains 2025; old commissioning
  releases do not prove a plant's current operating condition.

## Expansion sources reviewed, not yet imported

| Source | Value | Required handling before import |
| --- | --- | --- |
| [GEM Global Solar Power Tracker](https://globalenergymonitor.org/projects/global-solar-power-tracker) | February 2026 worldwide facility/phase inventory; >100,000 phases | Filter PV vs assumed-PV/CSP; aggregate phases only with validated project IDs; preserve source rating basis; exclude national distributed aggregates from project rows; TZ-tagged CC BY-NC records need separate license treatment |
| [WRI GPPD](https://github.com/wri/global-power-plant-database) | CC BY 4.0 global historical discovery catalogue | WRI says not maintained since early 2022; generic Solar includes unresolved technology; not a current verified PV inventory |
| [Chile CEN Infotécnica](https://api-infotecnica.coordinador.cl/) | Plant IDs, geographic points and engineering metadata; existing CEN connector in repository | Extend official plant metadata mapping, reuse stable source IDs, verify reuse terms and pagination |
| [UK REPD](https://www.gov.uk/government/publications/renewable-energy-planning-database-quarterly-extract) | July 2026 project planning/operation snapshot, >150 kW scope | PV filter; revised/re-applied planning IDs can describe the same project; reconcile links before counting; CRS of native X/Y is not lat/lon |
| [ANEEL SIGA](https://dadosabertos.aneel.gov.br/dataset/siga-sistema-de-informacoes-de-geracao-da-aneel) | Brazil's plant engineering and lifecycle registry, recent updates | ODbL attribution/share-alike obligations require a deliberate derivative-database plan; distinguish granted and inspected capacity |
| [EIA-860M](https://www.eia.gov/electricity/data/eia860m/index.php) | September 2026 preliminary monthly statuses, released 23 October | Preliminary values and silent revisions need separate source versions; do not blindly overwrite the annual detailed solar inventory |
| [Nextracker downloads](https://nextracker.eu/downloads/) | Tracker regional/version sheets | Keep revisions/options distinct; don't copy unsupported marketing energy gains into physical performance ratings |
| [Arctech SkyLine II](https://en.arctechsolar.com/skyline-ii/) | 1P/synchronous-drive public facts | Detailed S155 sheets require contact form; no form submitted, no guessed numerical ratings |
| [ARRAY DuraTrack](https://arraytechinc.com/resource/array-duratrack-data-sheet/) | Additional major OEM tracker family | Download and verify exact current datasheet before numerical population |
| [Trina module datasheet](https://static.trinasolar.com/sites/default/files/Vertex%20N_NEG21C.20_EN_2024_APAC_A_web.pdf) | OEM mechanical/warranty details for CEC enrichment | Match exact power bin and regional revision; do not insert a product range as a single exact model |
| [Jinko module datasheet](https://www.jinkosolar.com/uploads/JKM570-590N-72HL4-BDV-F7-EN.pdf) | STC/NOCT electrical tables and coefficients | Verify PDF table alignment; extracted NOCT Voc values appear lower than Vmp in search text, so no blind ingestion |

## Storage decision

[Apache Parquet](https://parquet.apache.org/docs/overview/) is the analytical delivery
format: typed nullable columns, native lists/timestamps, column projection and
Zstandard compression. Canonical JSONL makes every contribution reviewable in Git;
the source register avoids duplicating document metadata in every row. Explicit
schema versioning prevents arbitrary column drift. This avoids putting a mutable
SQLite binary or large Parquet diffs into pull requests. It is not a transactional
multiwriter store; a later PostgreSQL/table-format migration needs an explicit plan.

## Next research priorities

1. Grow trackers/combiners with exact OEM technical tables and regional options.
2. Add current PV projects outside the USA using official IDs, starting with Chile,
   then countries with no verified records across the six rotating macroregions.
3. Enrich existing equipment with dimensions, connector details, certification
   references, warranty conditions, efficiency curves and communication metadata.
4. Resolve the 36 ambiguous SAM model names against OEM sheets and document decisions.
5. Add reviewed EIA monthly updates and government-source adapters with snapshot
   provenance; improve commissioning/status timelines without retroactively
   pretending old datasets were current.

The scheduled specification is [RESEARCH_PROMPT.md](../RESEARCH_PROMPT.md).
Routine findings stay in a single open research PR; only the launch PR has advance
merge authorization. No row-count quota overrides evidence quality.
