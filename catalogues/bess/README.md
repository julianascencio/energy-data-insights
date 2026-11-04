# Worldwide BESS projects

The BESS section contains **2,005 project and plant records across
42 countries**, supported by **321 registered sources**. It combines curated
commercial projects with reviewed U.S., UK, Australian, Chilean and French inventory subsets, not an
exhaustive global inventory. It includes electrochemical
batteries (including vanadium flow), not pumped hydro, compressed air or thermal
storage. Exact equipment is maintained separately in the [BESS OEM catalogue](../bess_oem/README.md).

## Storage and usage

- Reviewable UTF-8 JSONL under `records/projects/<country>[_<region>].jsonl` is canonical.
- `sources.json` registers the publisher, URL, retrieval date, publication date
  where known, access method, evidence notes and source-license qualification.
- The packaged [schema](../../data-retrieval/src/energy_data_retrieval/bess_catalogue/schema.json)
  defines 60 typed, nullable columns. Extra metadata goes in `extensions_json`.
- Parquet with Zstandard is rebuilt offline; list fields remain lists, numeric
  fields retain their units, timestamps are UTC and all-null fields stay typed.
- `manifest.json` fingerprints the canonical rows, schema and sources and records
  the output file hash, countries, row count and completeness of each field.
- Browser JSON is a derived projection of the exact Parquet file; the viewer
  verifies its checksum. Neither browser JSON nor CSV is a second source of truth.

```bash
uv sync --locked --all-packages --group docs
uv run python -m energy_data_retrieval.bess_catalogue validate
uv run python -m energy_data_retrieval.bess_catalogue build --output artifacts/bess-v1
uv run python examples/database/plot_bess_projects.py
```

```python
import pandas as pd

bess = pd.read_parquet("artifacts/bess-v1/projects.parquet")
print(
    bess.loc[
        bess.country_code.eq("CHL"),
        [
            "name",
            "power_capacity_mw",
            "energy_capacity_mwh",
            "status",
            "status_as_of",
            "quality_status",
            "conflicts_json",
            "source_urls",
        ],
    ]
)
```

The [BESS viewer](https://julianascencio.github.io/energy-data-insights/bess-database-viewer.html)
and [database gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/database/index.html)
are rebuilt after a successful main documentation deployment. Browse filters,
all metadata, source links and dates; export filtered CSV, record JSON or Parquet.

## Meaning of a row

One row represents a named project or a registry-defined plant with an explicit
`capacity_scope`. EIA plant IDs are not always whole commercial projects. Separate
named facilities have separate IDs. A multistage project can retain phases in
`phases_json`; its total must not appear alongside overlapping phase rows.
Collie includes Stages 1 and 2 once. The original and Two Yllikkälä facilities
are separate named installations. Four Lithuanian parks are four rows, without
an additional fleet-total row. Hazelwood reports the operating first stage's
capacity and records the unfinished extension in phase metadata.

`power_capacity_mw` is battery power; `energy_capacity_mwh` is stored energy.
`grid_connection_capacity_mw` is a different field. Neither PV MW nor grid
connection MW may fill missing battery power. `power_basis` and `energy_basis`
are explicit, often `unspecified`. Reported discharge hours are not synthesized
from an E/P ratio. The catalogue is not a simulation parameter library: usable
energy, efficiency, degradation and dispatch limits need additional evidence.

## Dates, evidence and conflicts

`created_at` records first insertion; `updated_at` records substantive edits;
`last_verified_at` means access to source evidence, not live operation. The
source's `access_method` distinguishes an opened page from an indexed excerpt.
`status_as_of` and `status_date_basis` distinguish publication dates, reporting
period ends (`reporting_period_end`) and access to undated pages. EIA status is
as reported at year-end 2025, not at its 2026 retrieval date. An inauguration or publication date is not automatically
COD. Planned dates do not promote a project to operational.

Every populated factual field has explicit source IDs in `field_sources_json`.
Country codes and status labels are normalized from source descriptions; capacity
scope and unspecified rating bases are editorial interpretations of that evidence.
Curated records are AI-assisted factual transcriptions; inventory records use
tested adapters and a reviewed exclusion ledger. Both need ongoing review. Numeric precision does not imply independent verification.

Conflicts are retained in `conflicts_json` with both source observations and a
`needs_review` flag. The catalogue preserves conflicting Coya/Tamaya/Salisbury power ratings,
Jurong Island energy ratings and Edwards & Sanborn registry-scope differences. It does not select a universal engineering
rating from a marketing announcement. See [latest research notes](research/2026-11-03_flower_guidebook.md) and the
[original launch audit](research/launch_report.md).

## Contribution contract

1. Prefer regulator/system-operator registries, owner pages and OEM/EPC releases.
   Reuse an existing source registration when appropriate; record access method.
2. Reconcile name, locality, aliases, external IDs and phase scope before adding a
   row. Stable IDs use original country/locality/name, never mutable capacities.
3. Fill only supported fields. Unknown is null, never zero, an assumed chemistry,
   a guessed manufacturer, a city-centroid coordinate or an inferred COD.
4. Retain creation time. Change update time only for substantive edits; refresh
   verification time after checking evidence. Retain previous observations in Git
   and unresolved discrepancies in `conflicts_json`.
5. Edit records on an isolated branch. Validate, rebuild and run relevant tests
   before submitting the next batch as a reviewable PR. Conflicting populated
   fields require an explicit evidence-backed edit; no automatic overwrite.
6. Add every new source to the repository reference registry and regenerate
   citation exports. Do not bundle copyrighted articles, datasheets or imagery.

No blanket open-data license is asserted for third-party material. These files
contain small factual transcriptions and attribution; source terms still apply.
The hourly research process follows the [research workflow](RESEARCH_WORKFLOW.md); scheduling is managed separately from repository CI.

## National inventory staging

Schema 1.1.0 adds the `reporting_period_end` status-date basis without changing
its 60 columns. Source files stay outside Git; their checksums, dates and
interpretation are registered in `sources.json`.

```bash
uv run python scripts/stage_bess_inventory.py eia860 /path/to/eia8602025.zip \
  --source-id eia860_2025_bess --output artifacts/eia-bess-candidates.jsonl
uv run python scripts/stage_bess_inventory.py repd /path/to/REPD_Publication_Q2_2026.csv \
  --source-id repd_2026_q2_bess --output artifacts/repd-bess-candidates.jsonl
```

These commands validate the pinned input and write a new candidate file; they
never overwrite the catalogue. Candidates can overlap one another or a curated
project. Reconcile them using the [review ledger](research/2026-11-01_inventory_review.json)
before accepting rows. Preserve existing creation times and UUIDs.

- EIA: select OP / BA / Batteries, exclude electrochemical capacitors, and
  aggregate by plant ID. Other battery units stay nested outside the totals.
  MW is nameplate AC and MWh is nominal. Missing components make a total unknown.
  Generator operating dates do not become whole-project CODs. No PV MW is added.
- REPD: stage Battery / Operational entries after whitespace normalization.
  Only reviewed records are published. The applicant/operator field stays in
  native metadata; it is not proof of ownership. Unreported MWh stays null.
  Native projected coordinates are not treated as latitude/longitude.
- AEMO: sum existing/commissioning battery unit aggregate AC nameplates at each
  survey site. Other phases stay nested outside totals; site connection limits
  are not battery MW. Consolidate survey sites belonging to one commercial
  project, as for MREH. NEM coverage excludes Western Australia and NT.
- CNE: stage administrative BESS construction declarations. Keep associated
  generation and additional grid injection separate from battery ratings;
  hybrid net MW stays native. Forecast interconnection months never imply COD.
  See the [Australia/Chile ledger](research/2026-11-01_australia_chile_review.json)
  for accepted rows, five existing-project matches, and three withheld entries.
- This batch withholds nearby UK records and unresolved phase entries. Proximity
  is a review trigger, not proof of duplication. The ledger explains every
  omission and the two matches to existing operating UK projects.

The EIA source is U.S. government public-domain data. REPD attribution:
**Contains public sector information licensed under the Open Government Licence
v3.0.** Other primary-source material retains its own terms.

Earlier iteration: [India, Fox ESS and Freedom Won research](research/2026-11-01_india_fox_freedom_report.md), including the candidate ledger, source access decisions and dated market-priority metric.

Previous pass: [Victron/SMA equipment and Scatec projects](research/2026-11-02_victron_scatec_report.md), including field conflicts and the next source queue.

Previous pass: [GIGA portfolio and Quattro/MultiPlus-II models](research/2026-11-02_giga_quattro_report.md), including capacity conflicts and exact electrical variants.

Previous pass: [Regional Victron specifications and Singapore reconciliation](research/2026-11-02_regional_victron_singapore_report.md).

Previous pass: [Asian projects, Deye and Hubble equipment](../bess/research/2026-11-02_asia_deye_hubble_report.md).

Previous pass: [Hubble high-voltage configurations and Zenobē enrichment](../bess/research/2026-11-02_hubble_hv_zenobe_report.md).

Previous pass: [Irish project reconciliation and GoodWe exact models](../bess/research/2026-11-02_ireland_goodwe_report.md).

## NEMSA application staging

The offline NEMSA adapter stages one publicly indexed Nigerian mini-grid inspection
application for manual review. These applicant declarations are not certificates
or evidence of commercial operation. It allowlists site/battery fields, excludes
personal contact and owner-name fields, and preserves conflicting units verbatim.
It never repairs capacities, assigns canonical identities or imports records.

```bash
uv run python scripts/stage_bess_nemsa.py /path/to/application.html \
  --source-url https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/1511981/ \
  --output artifacts/nemsa-candidate.jsonl
```

Review the exact entry ID, community, battery table and any earlier applications
before using the established upsert API. A second inspection application is not
a second asset. Public accessibility is not a bulk-reuse licence; inspect source
terms before retrieval. See the [NEMSA/Freedom Won review](research/2026-11-02_nemsa_freedom_report.md)
for accepted records, conflicts and the next source partition.

## French registry staging

The [ODRÉ/Rolls/Lithops review](research/2026-11-02_odre_rolls.md) records
113 accepted French installations, one Namibian enrichment and 16 exact models.
Consult its EIC ledger and ranked backlog before continuing a partition. Only
individual, explicitly battery-only rows are eligible; multiple same-commune
EICs, confidential names and hybrid scope require additional review.

```bash
uv run python scripts/stage_bess_odre.py artifacts/research-inputs/odre_battery_ge1mw_0.json --snapshot-date 2026-08-31 --output artifacts/odre-review.json
```

This offline command stages observations; it does not accept candidates or merge
identities. Download bytes separately after checking current terms and revision.

Latest iteration: [second French partition and Rolls components](research/2026-11-02_odre_partition2.md), including Bellac enrichment and the next reviewed-source queue.

Latest pass: [French partition 400–599 and Rolls LFP review](../bess/research/2026-11-02_odre_partition3.md).

Latest pass: [Final French partition, LFP and Ventavon](../bess/research/2026-11-02_odre_partition4.md).

Latest pass: [India IATI and HW15 inverter components](../bess/research/2026-11-02_india_vedirect.md).

Latest pass: [Pacific inventory review and HW15 equipment](research/2026-11-03_pacific_hw15.md).

Latest: [Tonga and LiTE 2 research](research/2026-11-03_tonga_lite2.md).

Latest: [Outer Tonga and Encore research](research/2026-11-03_outer_tonga_encore.md).

Latest: [Tonga review and EMS/PCS specifications](research/2026-11-03_tonga_ems_pcs.md).

Latest: [Pacific portfolio and Discover equipment](research/2026-11-03_pacific_discover.md).

Latest: [Nordic portfolios, Samoa tender and Crown configurations](research/2026-11-03_nordic_crown.md).

Latest: [Named Ingrid/Locus sites and exact Rolls two-volt cells](research/2026-11-03_ingrid_r2.md).

Previous: [South African portfolios, Finnish owner evidence and Rolls AGM configurations](research/2026-11-03_south_africa_rolls.md).

Previous research: [Harmony portfolio and exact Sinexcel conversion equipment](research/2026-11-03_harmony_conversion.md).

Previous research: [Flower portfolio, Sinexcel guidebook and BlueNova equipment](research/2026-11-03_flower_guidebook.md), with exact revisions, source conflicts and the next ranked source queue.

Latest research: [Mauritius and Philippine projects, Eskom milestones and BlueNova configurations](research/2026-11-03_islands_bluenova.md), with the CEB offline adapter and source-access backlog.

Latest reviewed batch: [Philippine historical inventory and BlueNova racks](research/2026-11-03_doe_racks.md).

## Poland funding records (3 November 2026)

The NFOŚiGW subset in `POL_20261103_funding_owner.jsonl` and the funding facts
in `POL_20261103_energa.jsonl` are adapted from official Gov.pl textual material,
attributed to NFOŚiGW and shared under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Changes include selecting battery-verified proposals, translating display names,
normalizing fields and linking signed contracts. Original investment names,
application IDs, contract IDs, source URLs and page/rank locators remain recorded.
This notice applies to that source-derived subset, not unrelated catalogue sources.
The ranking is technology-neutral and does not establish operation or funding.
See the [review ledger](research/2026-11-03_poland_containers_review.json).

To stage the reviewed 479-row/24-page edition offline (optional `pdfplumber`):

```bash
uv run --with pdfplumber python scripts/stage_bess_nfosigw.py /path/to/ranking.pdf --output /tmp/candidates.jsonl
```

The adapter stages funding applications; it never merges loan/grant rows,
assigns chemistry, allocates portfolio capacity or promotes physical lifecycle.

The funding facts in `POL_20261103_tauron.jsonl` also adapt NFOŚiGW material under CC BY-SA 4.0. Sixteen applications were manually linked by named site, beneficiary and power to the battery-classified TAURON portfolio. This attribution covers those funding facts only.

The signed-contract and application facts in `POL_20261103_energa_tender.jsonl`, and the additional TAURON contract observations, adapt NFOŚiGW material under CC BY-SA 4.0. Original titles/identifiers and source links are retained; normalized monetary values and English field labels are modifications. Owner technical evidence has separate attribution. See the [Energa/BYD iteration](research/2026-11-03_energa_byd.md).

Latest research: [Dominican technical annexes and HV PACK configurations](research/2026-11-04_fv6_hv_pack.md).

Latest research: [Kenya source screening and Pylontech component/service evidence](research/2026-11-04_kenya_pylon.md).

Latest research: [Philippines service and project reconciliation; EFFEKTA and Pylontech components](research/2026-11-04_philippines_effekta.md).
