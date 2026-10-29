# Applied analyses

## Degradation mapping

The [degradation mapping study](src/energy_analysis/degradation/README.md) retrieves
ERA5/CRU inputs through `data-retrieval`, applies the models in `methods`, and
generates geographic maps and reports. Use `energy-degradation-study --help`.

## Climate Change Yield Assessment

The [applied CCYA example](examples/ccya/README.md) follows the Bolzano case-study
design in the PhD thesis: seven climate paths, 50 operating years, four degradation
rates, and 25/50-year yield comparisons. Its runnable demonstration uses explicitly
synthetic data and includes a configuration for qualified plant/model CSVs.

```bash
uv sync --locked --all-packages
uv run energy-ccya demo --output artifacts/ccya-demo
```

Open `artifacts/ccya-demo/results/reports/index.html` for the complete analysis,
seven PNG/SVG figures, component comparisons, source references and provenance.
Report generation belongs to `src/energy_analysis/ccya_case/reports/`.

## Chile PV fleet

`energy-analysis` assembles reusable retrieval and scientific methods into an auditable
Chile PV fleet workflow. The package operates on the **entire registry supplied to a
run**. It does not silently equate all historical registry records with independent
physical farms, merge farms by name, or discard sites with missing observations.

## Commands

From the repository root after `uv sync --all-packages --group dev`:

```bash
# A complete deterministic smoke run. Every observation is explicitly synthetic.
uv run energy-chile demo --output .local/chile-demo --reports

# Fit the same synthetic study with the separate LightGBM algorithm.
uv run energy-chile demo --output .local/chile-demo-lgbm --algorithm lightgbm

# Join normalized site-level generation and weather with an outer UTC-key join.
uv run energy-chile prepare \
  --generation .local/generation \
  --weather .local/weather \
  --sites .local/sites.csv \
  --output .local/prepared

# Run every registry record with the configured periods and model choice.
uv run energy-chile run --config analysis/examples/chile_fleet.toml

# Reuse supplied frozen expected values without retraining or modifying them.
uv run energy-chile compare \
  --hourly .local/frozen-hourly.parquet --sites .local/sites.csv \
  --start 2026-10-27T03:00:00Z --end 2026-10-28T03:00:00Z \
  --reference expected_final_mwh --output .local/frozen-comparison

# Render an existing result directory without fitting a model or changing inputs.
uv run energy-chile report --run .local/frozen-comparison
```

The example dates are explicit **study boundaries**, not independently verified storm
timestamps. Set them for your study. None of these commands claims to have freshly
retrieved the entire Chile fleet: retrieval is a separate package with source-specific
access and coverage limits.

`prepare`, `run`, `compare` and `report` refuse to overwrite an existing output directory.
Successful runs atomically rename a temporary directory; interrupted runs cannot leave
a misleading `complete=true` release at the requested destination.

## Input contract

Hourly inputs may be a Parquet file, a Parquet directory/dataset, or a small CSV.
Parquet is the production format. **Partition by `site_id` or use site-sorted row
groups** so Arrow can skip unrelated rows. One site's data is materialized at a time;
using a single unpartitioned unsorted file forces repeated scans and will be slower.
CSV is deliberately limited to one million rows and loaded once as a convenience.
The pipeline keeps site processing sequential and model thread counts bounded, avoiding
nested fleet-level and model-level thread pools.

| Column | Meaning | Requirement |
|---|---|---|
| `site_id` | Stable registry identifier, normalized to a string | Required, nonempty |
| `timestamp` | UTC/offset-aware **interval-start** timestamp | Required; unique site/hour; whole hour |
| `actual_mwh` | Reported energy during the following one elapsed hour | Required; NaN remains missing |
| `ghi_wm2` | Interval-mean original GHI, W/m² | Missing allowed; no model/resource guess |
| `temperature_c` | Aligned ambient temperature, °C | Missing allowed |
| `wind_speed_ms`, `gust_ms` | Aligned m/s values with source semantics retained | Optional |
| `duration_hours` | Interval duration | Optional; when present must equal 1 |
| `generation_complete` | Complete trusted-roster aggregate | Optional; false withholds `actual_mwh` |
| `expected_mwh` | Supplied frozen reference energy | Required only for the default `compare` mode |
| `expected_final_mwh`, `expected_heldout_mwh` | Explicitly selected frozen streams | Supported by `compare --reference` |

Do not pass unit-level CEN records directly: a `unit_id` column is rejected. Use the
retrieval package's explicit unit-roster aggregation first. Missing constituent units
must remain missing. Raw source timestamps and weather units must be normalized by
retrieval; this package does not guess whether an input labelled MW is hourly MWh,
or whether a radiation value is interval-ending.

Naive civil-clock timestamps are rejected. Explicit UTC offsets retain both occurrences
of an autumn DST hour. The analysis grid uses elapsed UTC hours; Chile calendar labels
use `America/Santiago`, so a civil day can contain 23 or 25 hours. No interpolation,
zero filling or forward filling is performed.

The metadata registry requires `site_id`; useful columns are `name`, `region`,
`latitude`, `longitude`, `ac_capacity_mw`, `dc_capacity_mw`, `dc_capacity_qualified`,
`racking_type`, `tilt_deg` and `azimuth_deg`. Coordinates may be missing: the site stays
in fleet output with model fitting withheld. DC qualification defaults to false.
**AC/registry capacity is never silently substituted for qualified DC capacity.**
A true DC qualification flag requires finite positive DC capacity. Unsupported module
or mounting claims are not invented from a name or location.

## Scientific workflow

1. The baseline is the configured number of elapsed 24-hour days before `event_start`.
   Its final `holdout_days` form a chronological test block. All intervals are half-open.
2. For the held-out model, geometry, time shift, acceptance band and model parameters
   are fitted only before the holdout start. For the final model, they are fitted only
   before the event boundary. Post-cutoff generation cannot influence either fit.
   Shifted weather source times outside the training window are excluded from fitting.
3. Metadata narrows a bounded fixed-tilt/single-axis geometry candidate set. Otherwise
   candidates are **effective fitted geometries**, not confirmed physical metadata.
   The selected lag is applied to POA and ambient temperature; original GHI and solar
   elevation remain available for the operational screen. `fit_geometry=false` fixes
   the first metadata/default geometry and a zero lag; it does not verify that geometry.
4. The Ascencio-Vásquez acceptance band is fitted only on eligible training data.
   Qualified-DC estimated PR is then gated to the inclusive interval `[0.5, 1.0]`.
   Missing qualified DC skips that PR gate with explicit provenance. Unsupported band
   fitting withholds the model; it never silently removes the filter to force a fit.
5. The default constrained physical model has a nondecreasing concave irradiance
   response and a nonincreasing temperature response within its declared domain.
   `algorithm="lightgbm"` selects a separate monotonic LightGBM implementation; it is
   not represented as the historical frozen physical model, and does not inherit a
   concavity guarantee. Chronological test metrics are recorded with no 75% promise.
6. The earlier ten-state IEC-informed screen uses original resource evidence,
   selected-stage reference/support/Q95, acceptance-band disagreement and persistence.
   Zero output with adequate resource remains observable even if a model cannot be fit.
   Every operating cause remains **unconfirmed**. No IEC availability percentage,
   recoverable loss, forced outage, curtailment or causal storm-damage claim is inferred.
7. TDP uses **all supplied history for each site**, independently of the short model
   baseline. It retains reported zeros and explicitly qualifies coverage. Chile TDP
   uses fixed UTC−04; it deliberately differs from the civil-clock fleet calendar.

For an immutable historical reference, use `compare` with exported expected values.
The modular `run` command fits new models; bit-for-bit equivalence with an earlier
monolithic model release is not claimed. `compare` preserves expected values but does
not recreate absent historical training support or status evidence.

## Energy accounting

Only finite, nonnegative actual and expected observations form a matched pair. Reported
zero is valid. Missing and negative actual observations are excluded from the ratio,
with counts retained. Neither the acceptance band, PR gate nor status classification
filters the evaluation/energy-accounting population.

`reference_energy_coverage = matched expected energy / all available reference energy`.
This is coverage of the **available** reference, not proof of a complete measured day.
Zero expected denominator is unscorable. The default gate is 80%; the default site-period
triage band is ±20%, with exact boundaries included in `within_tolerance`.

Fleet totals sum only comparable registry records. Other records remain in the output
and denominator counts. Positive and negative **site-period** gaps are summed separately;
they differ from sums of positive/negative hourly residuals. Weather statistics use valid
hourly values, retaining negative ambient temperatures but excluding negative GHI/wind.
The score `100 * (1 − WAPE)` is an energy-prediction score, not classification accuracy.

## Run outputs

| Path | Contents |
|---|---|
| `fleet.csv`, `fleet.parquet` | Every registry record, coverage, matched energy, under/over group, weather statistics, test score |
| `summary.json` | Explicitly scoped fleet counts and energy totals |
| `hourly/site-NNNNNN.parquet` | UTC/civil-clock fields, actual, final/heldout expected, selected POA, filter masks, hourly states/evidence |
| `models/site-NNNNNN.json` | Stage boundaries, geometry, lag, accepted counts, DC qualification, band parameters and portable fitted state |
| `tdp/site-NNNNNN-{avg,y2y,coverage}.parquet` | All-history profiles and qualification evidence |
| `manifest.json` | Config, software versions, input/output hashes, site-to-file mapping, scope and limitations |
| `reports/` | Optional fleet/site HTML, publication drafts, references and separate report manifest |

The numbered file key is a safe filename, not a renamed plant identifier. The manifest
maps every key back to its exact registry ID. No credentials or private request URLs
are written to run provenance. Input hashes are on by default; `hash_inputs=false`
records sizes only and explicitly weakens input reproducibility.

## Analysis-specific report generation

All Chile report generation code is in
[`src/energy_analysis/chile_fleet/reports/`](src/energy_analysis/chile_fleet/reports/).
The API and output contract are documented in that folder. Other analyses should
own their own `reports/` package rather than adding country-specific rendering
to `methods` or `data-retrieval`.

Use either `--reports` when running an analysis or the separate `report` command
on a completed result directory. For example:

```bash
uv run energy-chile run --config analysis/examples/chile_fleet.toml --reports
uv run energy-chile report --run .local/frozen-comparison \
  --title "Chile PV fleet: frozen-reference comparison"
```

By default the report destination is `<run>/reports`. `--output` selects a new
destination when a separate report version is needed. An existing report folder
is never silently replaced. Generating reports after a run leaves the original
analysis manifest, fitted parameters and expected generation unchanged.

The fleet page provides searchable, sortable comparisons and links to individual
site pages. Coverage, comparison eligibility, matched observed/expected energy,
chronological validation and hourly screening evidence are displayed separately.
TDP evidence appears when the analysis produced it. Frozen-reference comparisons
without saved hourly/model/TDP details show those limits explicitly. References
include the thesis first and the works underlying the methods and data sources.

The TOML setting `data_kind` accepts `"synthetic"`, `"observational"` or
`"unspecified"` (default); it describes the supplied data, not model accuracy.
The demo always sets `"synthetic"`, including when its config is loaded later.
For synthetic frozen inputs use `compare --synthetic`; `report --synthetic` can
also mark older results. The generated dashboard and publication drafts carry
the synthetic label. A missing label does not establish field validation.

Reports are self-contained offline HTML with no external chart library, CDN or
analytics requests. Fleet hourly series are split into per-site pages and chart
data are bounded. Website and LinkedIn outputs are **drafts**, with figures drawn
from the saved fleet accounting; this command never publishes them.

## Sources and verification

The reusable scientific method references live in [`methods`](../methods/README.md).
Relevant primary sources include the acceptance-band publication
[Ascencio-Vásquez et al. (2020)](https://doi.org/10.3390/en13092166),
[pvlib solar/POA documentation](https://pvlib-python.readthedocs.io/en/stable/), and the
[IEC TS 63019:2019 scope](https://webstore.iec.ch/en/publication/27253).

Package tests cover zero/missing/negative accounting, separate site/hourly gaps,
coverage/tolerance boundaries, DST-aware keys, incomplete unit aggregates, preparation
joins, withheld-model resource detection, configuration round trips, leakage protection,
and complete synthetic workflow outputs. Synthetic smoke results verify implementation
behavior; they are not field-validation scores for Chile's fleet.
