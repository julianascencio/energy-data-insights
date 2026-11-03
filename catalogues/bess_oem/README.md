# Global BESS OEM product database

The 3 November 2026 expanded research snapshot contains **624 records from 43 product
suppliers, backed by 292 registered sources**: 611 documented configurations and 13
explicitly configurable families. It covers utility-scale systems, C&I cabinets,
a small residential sample, standalone battery inverter/chargers, and non-lithium
storage technologies. This is a
researched starting inventory, not a complete list of suppliers or market-share ranking.

It follows the PV module catalogue pattern: one reviewable JSONL row per exact
OEM model/configuration, expandable typed columns, source lists, field-level
provenance and UTC creation/update/verification dates. BESS products have their
own schema because active power, apparent power, stored energy, PCS integration
and performance boundaries cannot be represented safely by PV module fields.
Project installations remain in the separate [BESS projects](../bess/README.md) catalogue.

## Use

```bash
uv sync --locked --all-packages
uv run python -m energy_data_retrieval.bess_oem_catalogue validate
uv run python -m energy_data_retrieval.bess_oem_catalogue build --output artifacts/bess-oem-v1
uv run python examples/database/plot_bess_oem_catalogue.py
```

```python
import pandas as pd

systems = pd.read_parquet("artifacts/bess-oem-v1/systems.parquet")
print(systems.groupby(["manufacturer", "record_scope"]).size())
print(
    systems.loc[
        systems.manufacturer.eq("Sungrow"),
        ["model", "variant", "energy_capacity_mwh", "energy_basis", "source_urls"],
    ]
)
```

The [interactive OEM viewer](https://julianascencio.github.io/energy-data-insights/bess-oem-database-viewer.html)
provides search, supplier/chemistry/architecture filters, all 73 columns, source
inspection, grouped statistics and filtered CSV export. The documentation build
publishes `datasets/bess_oem/systems.parquet`, schema, source registry, manifest
and checksum-linked browser projections after merge and successful deployment.
Parquet is built offline from Git; binary snapshots are not committed.

## Files and update contract

- `records/systems/{UUID-prefix}.jsonl`: canonical, sorted, hash-sharded records.
- `sources.json`: exact primary-source URL, publisher, title, access time, method,
  document revision/date when available, and source terms.
- `DATA_DICTIONARY.md`: 73 typed columns and units; packaged `schema.json` is authoritative.
- `research/2026-11-01_report.md`: scope, decisions, limitations and further research queue.
- `research/2026-11-01_summary.json`: dated initial counts and field completeness.
- `RESEARCH_PROMPT.md`: next-iteration collection/reconciliation procedure.

Stable IDs use manufacturer + exact model + explicit variant, preserving model
case and punctuation. Never include changing ratings in identity unless the OEM
itself uses that rating to define the marketed configuration. Reuse an existing
ID when correcting a record; supplier renames require alias/reconciliation review.
`created_at` is database creation, not product launch. Change `updated_at` only for
substantive content or evidence changes. `last_verified_at` means source text was
checked, including indexed text where explicitly marked, not hardware tested.

Every populated factual field has its own source-ID list in `field_sources_json`.
There is no wildcard attribution. With multiple documents, changed fields must
cite the correct document. Source URLs are generated on export. Add new source IDs
for changed document revisions; preserve old evidence in Git and the research log.
Exact URLs and printed revisions are retained, but PDFs are not redistributed and
not all sources are byte-hash pinned. Rebuild reproducibility refers to canonical
records, not to future availability of an external URL.

## Interpretation rules

- A product supplier is not automatically its cell manufacturer. OEM and integrator
  product brands are included; `cell_manufacturer` requires direct product evidence.
- `record_scope=family` keeps rating ranges in namespaced extensions. It has no
  scalar capacity/power/duration, preventing fictional combinations and false totals.
- `power_capacity_mw` is active power. `apparent_power_mva` stays separate. AC/DC,
  nominal/usable/peak energy, and power maximum/rated qualifiers remain explicit.
- RTE requires boundary, qualifier and conditions; unknown boundaries are labelled.
  Minimum/maximum RTE claims are not point measurements. Cycle life and warranty
  require conditions. Never equate a design-life claim to a warranty.
- `compliance_claims_json` preserves status and scope. A manufacturer's standards
  list is not an independently checked certificate. UL 9540A is a test method.
- `product_status` classifies the source document: documented, preliminary or
  historical. It is not a promise of current delivery, regulatory approval or support.
- No prices, project-to-product links, cell assignments or geographic availability
  are inferred. Unknown is null, never zero or false. Conflicts require `needs_review`
  plus evidence in `conflicts_json`; do not overwrite differing regions or revisions.

Schema additions are nullable and versioned. Update the dictionary and validation
when promoting frequent extension fields. Validate all retained records, rebuild
into a new immutable output directory, run catalogue/viewer tests and submit an
isolated PR. Never overwrite another writer's branch or remove retained records.

Source terms apply separately from the repository's software license. Only factual
metadata and attribution are stored; no OEM datasheets, images or logos are bundled.

Earlier iteration: [Dyness, Nordic and Baltic research](../bess/research/2026-11-02_dyness_baltic_report.md), with model-level reconciliation, source backlog and current coverage.

## Offline STACK100 table staging

The source-specific adapter supports only the reviewed Dyness manual with printed
revision V2 (2025-03-07). It stages the thirteen explicitly named strings, preserves
rounded printed energy and voltage limits, and rejects missing/duplicate columns,
changed units or an unreviewed revision. It does not generate configurations from
a family range or import records automatically.

```bash
pdftotext -layout /outside-git/stack100-manual.pdf /outside-git/stack100-manual.txt
uv run python scripts/stage_bess_dyness.py \
  --document /outside-git/stack100-manual.pdf \
  --text /outside-git/stack100-manual.txt \
  --output artifacts/stack100-candidates.json
```

The output includes PDF/text SHA-256 fingerprints and printed page/model locators.
Review source terms, identities and all additional specifications before using the
existing `upsert_records` API. The newer 2026 family sheet differs from the manual;
it must not silently replace the older exact-configuration columns. Components
S51100 and SBDU100 are separate product levels, not additional complete systems.

Previous pass: [Victron/SMA equipment and Scatec projects](../bess/research/2026-11-02_victron_scatec_report.md), including field conflicts and the next source queue.

## Offline Victron staging

For the reviewed four-column MultiPlus-II **new-model 230 V** datasheet, stage
selected continuous/peak power and charge-current facts without modifying records:

```bash
pdftotext -layout /path/to/Datasheet-MultiPlus-II-inverter-charger-4k-4k5-6k5-10k-EN.pdf /tmp/victron.txt
uv run python scripts/stage_bess_victron.py \
  --text /tmp/victron.txt \
  --document /path/to/Datasheet-MultiPlus-II-inverter-charger-4k-4k5-6k5-10k-EN.pdf \
  --output artifacts/victron-candidates.json
```

The adapter requires the four reviewed model columns in order, validates units
and overload durations, and records the PDF/text hashes. The apparent-feed-in row
uses kW despite its label, so it never fills apparent MVA. It does not decode nominal
DC voltage from model names. Other specifications, shared cells, source terms,
revisions, identities and conflicts still require review before the normal upsert.
The separate standard-model and SMA tables were manually reviewed, not parsed by
this adapter. No source PDF is bundled.

Previous pass: [GIGA portfolio and Quattro/MultiPlus-II models](../bess/research/2026-11-02_giga_quattro_report.md), including capacity conflicts and exact electrical variants.

For the nine exact Quattro 230 V codes printed in five grouped columns:

```bash
pdftotext -layout /outside-git/quattro.pdf /outside-git/quattro.txt
uv run python scripts/stage_bess_victron.py --layout quattro-230v \
  --document /outside-git/quattro.pdf --text /outside-git/quattro.txt \
  --output artifacts/quattro-candidates.json
```

This adapter checks model grouping and column order, separates W from VA, and
retains individual charger currents. It rejects changed units, incomplete groups
and unsupported regional voltage tables. It stages candidates for review only.

Previous pass: [Regional Victron specifications and Singapore reconciliation](../bess/research/2026-11-02_regional_victron_singapore_report.md).

Previous pass: [Asian projects, Deye and Hubble equipment](../bess/research/2026-11-02_asia_deye_hubble_report.md).

## Offline Deye Pro staging

The four exact BOS-G-Pro EU columns in the 20260414 V1.0 brochure can be staged
for review without importing them:

```bash
pdftotext -layout /outside-git/deye-pro.pdf /outside-git/deye-pro.txt
uv run python scripts/stage_bess_deye.py \
  --document /outside-git/deye-pro.pdf --text /outside-git/deye-pro.txt \
  --output artifacts/deye-pro-candidates.json
```

The adapter rejects missing/reordered model columns, duplicate rows, unit changes,
and missing energy test conditions. It preserves printed power independently from
energy: the G60 power observation requires review against the conflicting webpage.
It does not stage the separately restricted BOS-G manual, infer variants, or accept
records automatically. Source rights, document version and identity remain review
steps; PDF and extracted text hashes are emitted with the candidate ledger.

Previous pass: [Hubble high-voltage configurations and Zenobē enrichment](../bess/research/2026-11-02_hubble_hv_zenobe_report.md).

Previous pass: [Irish project reconciliation and GoodWe exact models](../bess/research/2026-11-02_ireland_goodwe_report.md).

## Reviewed MultiPlus HTML tables

`python scripts/stage_bess_victron_html.py downloaded.html --source-url URL
--output artifacts/victron-candidates.jsonl` stages the supported 120 V
500–1200 VA and 230 V 2 kVA manual tables without network access. Exact model
headers and explicit HTML column spans are required; W and VA remain separate.
This complements the existing PDF-layout adapter in `stage_bess_victron.py`.
Neither adapter imports records or reconciles conflicting document editions.
See the [2 November review](../bess/research/2026-11-02_victron_nemsa_review.json).

## Rolls flooded model staging

The [ODRÉ/Rolls/Lithops review](../bess/research/2026-11-02_odre_rolls.md)
adds 16 independently named stationary monobloc models. Rated Ah varies by
specified discharge rate and is not battery energy or individual-cell capacity.

```bash
uv run python scripts/stage_bess_rolls.py artifacts/research-inputs/rolls_s6-l16-ex.html --source-url https://rollsbattery.com/battery/s6-l16-ex/ --model 'S6 L16-EX' --output artifacts/rolls-review.json
```

This offline parser requires the exact model identity and preserves revision,
units and test conditions. Reconcile candidates against canonical records before
using the existing upsert API; inspect charging-unit anomalies explicitly.

Latest iteration: [second French partition and Rolls components](../bess/research/2026-11-02_odre_partition2.md), including Bellac enrichment and the next reviewed-source queue.

Latest pass: [French partition 400–599 and Rolls LFP review](../bess/research/2026-11-02_odre_partition3.md).

Latest pass: [Final French partition, LFP and Ventavon](../bess/research/2026-11-02_odre_partition4.md).

Latest pass: [India IATI and HW15 inverter components](../bess/research/2026-11-02_india_vedirect.md).

Latest pass: [Pacific inventories and exact HW15 120 V models](../bess/research/2026-11-03_pacific_hw15.md).

Latest: [Tonga and LiTE 2 research](../bess/research/2026-11-03_tonga_lite2.md).

Latest: [Outer Tonga and Encore research](../bess/research/2026-11-03_outer_tonga_encore.md).

Latest: [Tonga review and EMS/PCS specifications](../bess/research/2026-11-03_tonga_ems_pcs.md).

Latest: [Pacific portfolio and Discover equipment](../bess/research/2026-11-03_pacific_discover.md).

Latest: [Nordic portfolios, Samoa tender and Crown configurations](../bess/research/2026-11-03_nordic_crown.md).

Latest: [Named Ingrid/Locus sites and exact Rolls two-volt cells](../bess/research/2026-11-03_ingrid_r2.md).

Previous: [South African portfolios, Finnish owner evidence and Rolls AGM configurations](../bess/research/2026-11-03_south_africa_rolls.md).

Latest research: [Harmony portfolio and exact Sinexcel conversion equipment](../bess/research/2026-11-03_harmony_conversion.md).
