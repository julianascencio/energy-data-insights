# Global BESS OEM product database

The 2 November 2026 expanded research snapshot contains **184 records from 32 product
suppliers, backed by 80 primary sources**: 171 documented configurations and 13
explicitly configurable families. It covers utility-scale systems, C&I cabinets,
a small residential sample, and non-lithium storage technologies. This is a
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

Latest iteration: [India, Fox ESS and Freedom Won research](../bess/research/2026-11-01_india_fox_freedom_report.md), including the candidate ledger, source access decisions and dated market-priority metric.
