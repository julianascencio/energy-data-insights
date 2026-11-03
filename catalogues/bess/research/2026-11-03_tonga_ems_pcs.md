# Tonga inventory and exact EMS/PCS specifications — 3 November 2026

Research began 03:49 UTC (Atlantic/Canary also UTC). This bounded pass completed
DFAT's February 2024 Table One: fifteen separately identified battery installations.
The five previously held TREP-03 Lot 2 islands are now identifiable records;
five older OIREP island grids, the separate Niuafoou health clinic and four TREP
design-stage village grids complete the selected table. Kapa Falevai and Kapa
Otea are distinct villages, not duplicate names. Clinic capacity excludes the
unquantified solar-home-system aggregate and later island-wide TREP battery.
Table Two describes estimated needs, not accepted projects.

## Accepted changes

- 15 new projects; no existing-project enrichment. Five energy fields withheld
  against different earlier design observations (including a malformed Niuafoou
  number that was not repaired). No chemistry, equipment assignments or COD inferred.
- Historical status is explicitly February 2024, not today's operating status.
  The schema requires a full date: the report month is represented by month-end
  with `reporting_period_end` and explicit month precision in each record.
- Seven exact equipment configurations: EMS Standard and Pro hardware from the
  21 October 2024 EOL sheet, plus five expressly tabulated CAB1000 (3L.2) nominal
  AC voltage configurations. Different voltage/power/DC limits are preserved;
  no Cartesian combination of options or inferred kVA-to-kW conversion.
- Four existing equipment records enriched: ENVA 5/16 storage-temperature periods
  and prospective short-circuit currents, SOLVA AC261 current THD and connection/
  isolation details, and DC208 breaker/interface/cable-entry specifications.
- Five CAB1000 current fields quarantined because the table labels 1255 with
  VRMS in a current row. Optional black-start and -40 C capability remain optional.
  Conversion efficiencies at 690 V are not transferred to other voltage columns.
- EMS internal backup Wh stays separate from BESS system energy. Hardware is
  distinguished from 2025 commercial Essential/Pro/Ultra packages; those packages
  are deferred rather than duplicated. Warranty claims are not verified contracts.

Proposed totals: **1,730 projects / 35 countries / 213 sources; 525 equipment
records / 40 suppliers / 237 sources**. EPC Power is a new manufacturer; Freedom
Won is the publisher/distributor for CAB1000, not its manufacturer. No new country;
existing six-region coverage retained. Main at 76d0c1a remains 1,710 projects and
465 equipment records; proposed additions are unmerged.

## Sources, limits and reproducibility

The downloadable donor portfolio was attempted before individual announcements.
DFAT direct PDF returned 503 twice; its complete table was available in the web
PDF reader. Original checksum is unavailable, explicitly null. DFAT's website
CC BY 4.0 notice was checked, subject to third-party exceptions; only selected
facts are recorded with Department of Foreign Affairs and Trade attribution.
SPREP's technical-publication mirror returned 403; its indexed case table supplies
conflicting observations only. No original documents or artwork are committed.

Fourteen Freedom Won sheets were downloaded and checksummed outside Git: eleven
existing storage sheets plus two EMS editions and CAB1000. Seven configurations
added, four existing records substantively enriched; the remaining storage sheets
produced no accepted changes. The ENVA 16 filename suggests August, but its printed
revision remains 5 June 2026; the printed revision was retained. Manufacturer
copyright and lack of an open bulk licence remain explicit.

The existing upsert API was used. Four nested-JSON collisions required reviewed
additive edits, with every prior extension key and scalar value preserved. The
preservation audit confirms all old projects unchanged, four equipment updates,
no deletions, and unchanged creation timestamps. No schema/code changes or new
parser were necessary for this manually reconciled bounded table batch.

The dated IEA comparison was reopened: 2025 annual stationary power additions
(GW), ordered quantified examples China >63, US 19, Australia nearly 8, Chile
approaching 1. This is not an exhaustive country ranking or operational energy
GWh; comparable operational-GWh rankings remain unavailable.

The project objective of 50–200 was not met: the selected national table contains
only fifteen defensible installations. The equipment objective was met with
11 exact additions/enrichments. The source batches are exhausted for this pass;
remaining work requires corrected current units, as-built island ratings and
EMS hardware/package reconciliation. The ranked backlog retains Songino and
Cook Islands per-site lender evidence as additional next steps.

## Validation

- Full Python suite: 1,666 passed, one optional cdsapi skip.
- Both catalogue validators passed; independent typed Zstandard Parquet builds and
  coverage/completeness manifests match exactly.
- Ruff lint/format, ty, repository hygiene, citations and git whitespace checks passed.
- Eight viewer tests and both offline BESS examples passed.
- Strict Sphinx build passed. Link checks run before the build finished reported
  incomplete output; the final completed-site link check is reported below.
- No code/schema/packaging change; package builds were not repeated.

Research/reconciliation completed approximately 03:55 UTC; validation completed
approximately 04:00 UTC. Actual elapsed effort about 11 minutes before publication
(roughly 6 minutes research and 5 minutes validation). Selected defensible tables
were exhausted; no idle time added to meet the planning window. Remote CI is
separate from local checks. PR #86 remains open and unmerged.

Final completed-site check: all 409 HTML pages pass local link and asset validation.
