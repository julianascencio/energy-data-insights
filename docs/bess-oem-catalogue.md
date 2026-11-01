# Global BESS OEM product database

The expanded research database contains **90 records from 28 suppliers and 53 primary
sources**, with 73 typed metadata fields. This extends the PV equipment database
pattern to complete BESS products, cabinets and explicitly labelled product families.

Open the [interactive OEM viewer](https://julianascencio.github.io/energy-data-insights/bess-oem-database-viewer.html),
[Database gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/database/index.html),
[catalogue guide](../catalogues/bess_oem/README.md),
[data dictionary](../catalogues/bess_oem/DATA_DICTIONARY.md) and
[research report](../catalogues/bess_oem/research/2026-11-01_report.md).

## Download and reproduce

After the corresponding main documentation deployment:

- [Systems Parquet](https://julianascencio.github.io/energy-data-insights/datasets/bess_oem/systems.parquet)
- [Snapshot manifest](https://julianascencio.github.io/energy-data-insights/datasets/bess_oem/manifest.json)
- [Source registry](https://julianascencio.github.io/energy-data-insights/datasets/bess_oem/sources.json)
- [Versioned schema](https://julianascencio.github.io/energy-data-insights/datasets/bess_oem/schema.json)

```bash
uv run python -m energy_data_retrieval.bess_oem_catalogue validate
uv run python -m energy_data_retrieval.bess_oem_catalogue build --output artifacts/bess-oem-v1
uv run python examples/database/plot_bess_oem_catalogue.py
```

## What the fields mean

| Metadata group | Contents |
| --- | --- |
| Identity | Supplier, exact model, variant, family/configuration scope, document status |
| Electrical | Active MW, apparent MVA, nominal/usable/peak MWh, AC/DC boundaries, voltages, duration |
| Battery and enclosure | Chemistry, cell capacity, sourced cell OEM, cooling, temperature, dimensions, mass, IP |
| Controls | PCS integration/model, EMS, grid-forming, black start, communication protocols |
| Performance | RTE with qualifier/boundary/conditions, documented lifecycle and warranty conditions |
| Evidence | Source-ID/URL lists, field-source crosswalks, UTC dates, compliance claims, conflicts and extensions |

77 rows describe configurations; 13 explicitly describe configurable families. Family
ranges are nested and are not turned into fictional model combinations. The collection
includes supplier/integrator brands; cell manufacturer is populated only with direct
product evidence. The separate BESS project table is not joined to products by guessing.

Use `record_scope`, `capacity_scope`, `energy_basis`, `energy_boundary` and
`power_basis` before comparing systems. MVA is not MW. RTE percentages from different
boundaries or tests are not interchangeable. A standard named by a manufacturer is
not an independently checked certification; UL 9540A is a test method.

`product_status` classifies documentation, not live availability. Preliminary sheets
and historical products remain labelled, including NGK's NAS discontinuation evidence.
Creation/update/verification dates describe database research. Null means unknown.
The catalogue is broad but incomplete, with sparse warranty and efficiency-condition
coverage. Read the research report for the next supplier and metadata priorities.
