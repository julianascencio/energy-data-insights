# Energy Data Insights

Python tools for retrieving energy, weather and climate-model data, applying reusable
scientific methods, and running reproducible fleet performance studies.
The first country workflow is Chile's solar fleet.

## Repository structure

| Subproject | Contents | Python import |
| --- | --- | --- |
| [data-retrieval](data-retrieval/) | Provider folders for CEN, BSRN, NOAA GHCNh, AEMET, DWD, SURFRAD, measured-station exports, Open-Meteo, native ERA5, Copernicus CDS and CMIP6 through ESGF; bounded requests and provenance | `energy_data_retrieval` |
| [methods](methods/) | CCYA climate-change yield assessment, TDP, acceptance bands, PR filtering, effective POA and timing, constrained physics, LightGBM, evaluation, hourly operational screening, KGPV and degradation mapping | `energy_methods` |
| [analysis](analysis/) | Real-data degradation maps and reports; Chile fleet configuration, input preparation, chronological fitting/evaluation, site/fleet outputs and analysis-specific reports | `energy_analysis` |

These are independently installable Python packages in one uv workspace. Each
has its own source, tests and packaging metadata; one lockfile keeps their
dependencies consistent. All folder names are lowercase.
See [architecture and extension points](docs/architecture.md).

## Install

Use Python 3.12 or 3.13 and uv 0.13.4 or later:

```bash
git clone https://github.com/julianascencio/energy-data-insights.git
cd energy-data-insights
uv sync --locked --all-packages
```

Direct [Copernicus CDS API access](data-retrieval/src/energy_data_retrieval/sources/cds/README.md)
is available with `uv sync --locked --all-packages --extra cds`. Use
`energy-retrieve cds-retrieve` for catalogue selection JSON or `energy-retrieve cds-era5`
for hourly/monthly ERA5 selections divided into monthly requests. Both offer offline
`--plan-only`; downloads retain native files and require a CDS personal access token
and accepted dataset terms.

The optional native ERA5 source has additional dependencies; its package README
documents installation. Ordinary tests and the synthetic demo require no API
credentials and make no live provider requests.

## Run the degradation map analysis

The [applied degradation workflow](analysis/src/energy_analysis/degradation/README.md)
connects the retrieval package to the methods model, with a bounded 2016–2018
global sampling configuration and offline map reports:

```bash
uv run --no-sync energy-degradation-study all \
  --config analysis/examples/degradation/global_2016_2018.toml \
  --data-dir data/degradation-2016-2018 \
  --output artifacts/degradation-2016-2018
```

This command retrieves real ERA5 weather and a CRU land mask. The 15° sample-grid
scenario uses published coefficients with explicit aggregation assumptions.

## Run an end-to-end example

```bash
uv run --no-sync energy-chile demo --output artifacts/demo --reports
```

The demo creates **explicitly synthetic** hourly inputs and runs the full
country workflow. It is a smoke test and usage example, not a report about real
Chilean farms. Open `artifacts/demo/results/reports/index.html` for the offline
fleet dashboard and linked site reports. To exercise the alternative model:

```bash
uv run --no-sync energy-chile demo --algorithm lightgbm --output artifacts/demo-lightgbm --reports
```

For actual data, follow the [Chile workflow and schemas](analysis/README.md).
The `prepare` command joins normalized generation/weather records, and `run`
uses a TOML study configuration with explicit paths and time boundaries:

```bash
uv run --no-sync energy-retrieve --help
uv run --no-sync energy-chile prepare --help
uv run --no-sync energy-chile compare --help
uv run --no-sync energy-chile run --config analysis/examples/chile_fleet.toml
```

The real-data example requires your own acquired input files. Source-specific
retrieval commands, credentials, API access limitations and provider attribution
are documented in [data-retrieval](data-retrieval/README.md). Environment-variable
names are listed in [.env.example](.env.example); credentials are never bundled.
Use `energy-chile compare` when you already have frozen expected-generation
columns: it performs fleet accounting without fitting or replacing those values.

## Find weather data from latitude and longitude

Use one geographic query to rank nearby BSRN, NOAA GHCNh, AEMET, DWD and
SURFRAD stations and list the integrated gridded weather and climate products:

```bash
uv run energy-retrieve discover \
  --latitude 28.4775 --longitude -16.3294 \
  --radius-km 100 --limit 20 \
  --output data/discovery/tenerife.json
```

The JSON contains station distances, source identities, catalogue scope,
available coverage evidence, retrieval parameters and references. Missing
credentials and provider failures are reported per source. Add
`--probe-date 2025-01-01` to verify a small sample from the two Open-Meteo
products and record the actual selected grid cells and missing-value counts.
CMIP6 candidates retain explicit model/member/grid selection requirements.

See [location discovery](docs/location-discovery.md) for the Python API,
offline catalogue reuse, dataset statuses and scientific limits.

## Assess climate-change yield (CCYA)

The [CCYA method](docs/ccya.md) implements the workflow in the cited PhD thesis,
Chapter 7, sections 7.5.1-7.5.3. Calibrate historical monthly DC yield and weather
against a climate model, then assess future irradiance, temperature and power
degradation separately and together. Outputs include annual yields, 10-year
rolling trends and cumulative gain/loss against historical P10/P50/P90 baselines.
The guide documents the exact percentile convention and implementation choices.

```bash
uv run --no-sync python methods/examples/ccya_synthetic.py
```

This deterministic example uses synthetic data. Real runs require qualified
monthly DC plant measurements and preprocessed climate-model data; the method
does not reproduce the thesis's Bolzano results or automatically parse NetCDF.

## Retrieve CMIP6 data

CMIP6 has its own provider under
`data-retrieval/src/energy_data_retrieval/sources/cmip6/`. Search the current ESGF
STAC catalogue for an explicit model, experiment, member, table, variable and grid,
save the resolved version in a retrieval plan, then download that plan's native
NetCDF files with byte limits and SHA-256 verification:

```bash
uv run energy-retrieve cmip6-search --help
uv run energy-retrieve cmip6-download --help
```

See the [CMIP6 examples and source contract](data-retrieval/README.md#cmip6-climate-model-data)
for historical and scenario selections, bounded downloads and restart behavior.
Supported public endpoints need no account or additional package dependencies.
Native units and calendars are preserved. Climate-model files require a separate,
explicit analysis step before they can be used with the hourly fleet workflow.

## Retrieve measured station data

Each station provider has its own lowercase source folder and explicit commands:

| Provider | Commands | Access and product |
| --- | --- | --- |
| [BSRN](data-retrieval/README.md#bsrn-radiation-stations) | `bsrn-search`, `bsrn-dataset` | Public PANGAEA DOIs; monthly minute radiation data |
| [NOAA GHCNh](data-retrieval/README.md#noaa-ghcnh-weather-stations) | `noaa-stations`, `noaa-observations` | Public native station/year weather files |
| [AEMET](data-retrieval/README.md#aemet-opendata-stations) | `aemet-stations`, `aemet-daily`, `aemet-recent` | API key; historical daily climate and a separate recent-observation snapshot |
| [DWD CDC](data-retrieval/README.md#dwd-hourly-solar-stations) | `dwd-stations`, `dwd-solar` | Public hourly solar station archives |
| [NOAA SURFRAD](data-retrieval/README.md#noaa-surfrad-radiation-stations) | `surfrad-stations`, `surfrad-observations` | Public daily radiation and weather files |

Use `uv run energy-retrieve <command> --help` for options. These providers need
no additional package dependencies. AEMET reads `AEMET_API_KEY` from your
environment; the other four use public HTTPS routes without credentials.
Retrieved observations retain their native clocks, units, missing values,
source metadata and quality annotations. Saved source snapshots and hashes
support reproducible reuse. Station selection, scientific quality checks and
conversion to the hourly fleet schema remain explicit analysis steps. SURFRAD
participates in BSRN; those feeds can contain overlapping observations.

## Generate reports for a saved analysis

```bash
uv run --no-sync energy-chile report --run artifacts/my-study
```

The report generator belongs to
`analysis/src/energy_analysis/chile_fleet/reports/`. Each completed analysis writes
its own `reports/` output folder with a fleet dashboard, individual site pages,
publication drafts, bibliography and a hash manifest. The report reads saved
results without retraining or changing predictions. It works with `run` and
frozen-reference `compare` results; unavailable model or hourly evidence is
shown as unavailable. Add `--reports` to `run`, `demo` or `compare` to generate
reports immediately after the analysis.

Fleet pages link to separate site pages, keeping hourly history out of a giant
single-page payload. Synthetic runs retain their synthetic label in the saved
manifest and all generated narrative. Website and LinkedIn drafts are local
outputs for review; generating them does not publish anything.

## Scientific workflow

1. Normalize site identity, UTC intervals, measurement units and site metadata.
   Keep missing generation distinct from a reported zero.
2. Split a pre-event baseline chronologically. Fit geometry/timing, acceptance
   curves and model parameters using the training partition only.
3. Apply the published acceptance-band method and the qualified-DC PR gate.
   Fit the constrained physical model or the separate monotone LightGBM model.
4. Evaluate on later held-out observations and retain model-quality/support
   diagnostics. Refit the final pre-event reference separately for the report.
5. Compare actual and expected energy on the same reported intervals. Show
   underperformance, overperformance and insufficient comparison separately.
6. Export hourly operational screens and TDP results with their assumptions,
   configuration and input/output provenance.

The default fleet comparison uses at least 80% coverage of available reference
energy and an adjustable ±20% site-period tolerance. This is a triage rule, not
a statistical confidence interval. Positive and negative site-period gaps are
reported separately, alongside the signed fleet balance.

The physical model and LightGBM are different algorithms. LightGBM's monotonic
constraints alone do not guarantee concavity. A prediction score is not status
classification accuracy; no 75% score is promised. Screening states do not
confirm IEC operating causes, plant damage or recoverable energy losses.
Detailed method conventions and primary references are in [methods](methods/README.md).

## Quality and performance

```bash
uv run --no-sync ruff format --check .
uv run --no-sync ruff check .
uv run --no-sync ty check
uv run --no-sync pytest --cov --cov-report=term-missing
uv run --no-sync python scripts/check_repository.py
uv run --no-sync python scripts/check_citations.py
uv build --all-packages
```

GitHub Actions runs the locked environment, formatting, lint, type checks,
tests, package builds and the synthetic workflow on Python 3.12 and 3.13.
Tests use controlled fixtures and mocked network responses.

Numerical work is vectorized, processing is bounded, model threads are explicit,
and large results use file-backed formats. A reproducible
[fleet-accounting benchmark](docs/performance.md) measures its stated workload
without pretending to measure network retrieval or model training.

## Data and previous work

This repository maintains reusable code from the ASVA Chile analysis. Its
tests and examples are separate from the saved national dataset, fitted model
release and standalone HTML dashboard. The migration does not claim that a new
fit reproduces every previous fitted parameter or prediction byte for byte.

Raw provider data, normalized Parquet, fitted artifacts and generated reports
stay in local/object storage with provenance; they are excluded from Git.
Provider access conditions and attribution still apply to retrieved data.
The methods are country-neutral so additional countries can reuse the pipeline.

See [contributing](CONTRIBUTING.md) for development and review conventions.

## Cite this repository and its scientific foundations

**Main scientific reference:** Julián Andrés Ascencio Vásquez (2021).
_Modelling and worldwide assessment of performance and aging of photovoltaic
modules and systems_. Doctoral dissertation, University of Ljubljana, Faculty
of Electrical Engineering.
[Permanent record: URN:NBN:SI:DOC-TMG3QFI9](https://www.dlib.si/details/URN:NBN:SI:DOC-TMG3QFI9).

The root [CITATION.cff](CITATION.cff) sets the thesis as the preferred citation
for GitHub's **Cite this repository** feature. Also cite the individual papers,
software and datasets used in your analysis, plus this repository's URL and exact
commit. The [reference catalogue](docs/references.md) maps every reference to
its implementation, distinguishes background from implemented methods, and is
also available as [BibTeX](references.bib). Generated reports use the same
packaged catalogue and present the thesis first.

Citation metadata is generated from one source and checked for drift:

```bash
uv run --no-sync python scripts/check_citations.py
```

## Climate grids and KGPV maps

GPCC Monthly v2025 and CRU TS v4.10 retrieval/processing are available through
`energy-retrieve gpcc` and `energy-retrieve cru-ts`. `energy-kgpv` builds the
published 12-zone classification with explicit GHI input. Reusable climatology
and mapping utilities are in `methods`. See the [workflow and scientific rules](docs/kgpv.md).

## Map climate-driven PV degradation

`energy-degradation` maps hydrolysis, photo-degradation, thermomechanical and
combined rates from annual climate stresses and an explicit module calibration,
following the thesis. It exports NetCDF/GeoJSON, 0.2%/year categories and optional
area-weighted KGPV summaries. See the [scientific contract and runnable synthetic
example](docs/degradation.md).
