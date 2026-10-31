# Energy Data Insights

<p align="center">
  <a href="https://asvaconsulting.com">
    <img
      src="https://asvaconsulting.com/wp-content/uploads/2022/05/ASVA-1-1-scaled.jpg"
      alt="ASVA Consulting"
      width="280"
    />
  </a>
</p>

<p align="center">
  <strong>Created by ASVA Consulting</strong><br>
  <a href="https://asvaconsulting.com">asvaconsulting.com</a><br>
  <a href="mailto:contacto@asvaconsulting.com">contacto@asvaconsulting.com</a>
</p>

Created by **ASVA Consulting**, Energy Data Insights provides Python tools for
retrieving energy, weather and climate-model data, applying reusable
scientific methods, and running reproducible fleet performance studies.
The first country workflow is Chile's solar fleet.

**[Documentation](https://julianascencio.github.io/energy-data-insights/)** —
installation, user guides, searchable API reference and executable example gallery.
Built with Sphinx and the PyData theme; GitHub Actions validates every PR and
deploys the site from `main`. See [building and deploying the documentation](docs/development.rst).

[PVGIS connector](docs/pvgis.md): all PVGIS 5 and 6 endpoints, including weather,
PV output, TMY, terrain, coverage and metadata, with offline gallery examples.

## AI-generated implementation and scientific sources

Most of the code, documentation and examples in this repository are **AI-generated
under developer direction**. The scientific methods are based on **real, specifically
identified literature selected by the repository's developers**, who define the
research scope, choose the sources and guide the implementation.

The [reference catalogue](docs/references.md) identifies the original literature
and connects it to the relevant methods. Method-specific documentation records
implementation choices, adaptations and validation limits; responsibility for
review, testing and scientific validation remains with the developers and contributors.

As the project evolves, errors or omissions may remain in the code or documentation.
Please check assumptions and results for your intended use; corrections and issue
reports are welcome.

## Repository structure

| Subproject | Contents | Python import |
| --- | --- | --- |
| [data-retrieval](data-retrieval/) | Worldwide power-system and measured PV generation connectors; station, weather and climate sources; bounded requests and provenance | `energy_data_retrieval` |
| [methods](methods/) | CCYA climate-change yield assessment, TDP, acceptance bands, PR filtering, effective POA and timing, constrained physics, LightGBM, evaluation, hourly operational screening, KGPV and degradation mapping | `energy_methods` |
| [analysis](analysis/) | Real-data degradation maps and reports; Chile fleet configuration, input preparation, chronological fitting/evaluation, site/fleet outputs and analysis-specific reports | `energy_analysis` |

These are independently installable Python packages in one uv workspace. Each
has its own source, tests and packaging metadata; one lockfile keeps their
dependencies consistent. All folder names are lowercase.
See [architecture and extension points](docs/architecture.md).

## Example gallery

The [executable gallery](https://julianascencio.github.io/energy-data-insights/auto_examples/index.html)
and the repository use the same three sections:

| Section | Examples |
| --- | --- |
| [Methods](examples/methods/) | Climate-change yield assessment, typical daily profiles and KGPV classification |
| [Connectors](examples/connectors/) | Worldwide coverage map, generation providers, measured PV datasets, station catalogues and weather request planning |
| [Analysis](examples/analysis/) | PV climate comparisons, site metadata lookup, degradation-rate maps, KGPV and soiling/snow risk maps |

Every gallery example runs offline during the documentation build. Download links
on the example pages include the supporting data and provenance where needed.

Start with the **[worldwide connector coverage map](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/plot_generation_coverage.html)**
and its [Python source](examples/connectors/plot_generation_coverage.py).
Two reproducible figures introduce all 48 source modules: 22 generation providers,
five station networks, 19 weather/climate/terrain/imagery grid adapters, the local station-file
importer and the Natural Earth basemap. Country shading identifies host countries
for country/system products; regional and research-site markers retain their
specific scope. The station map uses actual catalogue coordinates, which do not
establish weather observations or current availability. See the
[coverage guide](docs/worldwide-generation.md#worldwide-connector-coverage-map)
for the interpretation, source catalogue and offline data files.

## Retrieve real electricity generation

The [worldwide generation catalogue](docs/worldwide-generation.md) adds ONS,
IESO, AESO, XM/SIMEM, ADME, Elexon, RTE, SMARD, CAISO, EMI, Taipower, TEPCO, KPX,
Eskom, PVDAQ, NIST and DKASC alongside CEN and the
[AEMO, EIA, REE and ENTSO-E connectors](docs/generation-connectors.md).
Each new source has a worked gallery example and Python/CLI workflow.

Most examples include genuine attributed observations that run offline.
Credentialed ENTSO-E/KPX examples default to request plans; NIST and DKASC import
native exports downloaded through their provider portals. Scope, native units,
time conventions and access limitations remain explicit. Source revisions and
local input files are tracked through checksums and provenance manifests.

```bash
uv run energy-retrieve ree-generation \
  --start 2024-06-01 --end 2024-06-30 --system national \
  --output data/ree_june_2024.parquet
```

## Install

Once the first releases are published, each subproject can be installed from
public PyPI with `pip install energy-data-retrieval`, `pip install energy-methods`
or `pip install energy-analysis`. Analysis also installs the other two packages.
See [tag-based releases and publisher setup](docs/releases.md) for independent
release tags, optional extras and the one-time PyPI setup.

For development from source:

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

## PV climate classification comparison

JRC performance climates, ML21 and PVCZ thermal/humidity zones now complement
KGPV. [Compare the methods](docs/climate-comparison.md) and run offline maps of
the world, Chile and the Canary Islands. Published reference labels and new
cluster fits are identified separately; coverage gaps remain visible.

The [one-site tutorial](docs/site-climate.md) queries all four schemes for Rengo,
Chile, retaining full native fields, nearest-source distances, periods, resolution
and provenance. It explains how to use the results for benchmarking, yield
modelling and reliability screening, and how to load full catalogues for another site.

## Climate grids and KGPV maps

GPCC Monthly v2025 and CRU TS v4.10 retrieval/processing are available through
`energy-retrieve gpcc` and `energy-retrieve cru-ts`. `energy-kgpv` builds the
published 12-zone classification with explicit GHI input. Reusable climatology
and mapping utilities are in `methods`. See the [workflow and scientific rules](docs/kgpv.md).

## Soiling and snow risk maps

Select one or several countries by name/code, acquire their Natural Earth
shapefiles and use a configurable regional grid with contour clipping.
See [country mapping and the real 0.5° example](docs/country-mapping.md).

Map the thesis's soiling-rate and snow-shading indicators with five risk levels,
complete-year validation and explicit units. The [scientific guide](docs/soiling-snow.md)
and offline worldwide gallery use real NASA POWER/ERA5-Land inputs, document
source substitutions and provide NetCDF/GeoJSON exports.

## Map climate-driven PV degradation

`energy-degradation` maps hydrolysis, photo-degradation, thermomechanical and
combined rates from annual climate stresses and an explicit module calibration,
following the thesis. It exports NetCDF/GeoJSON, 0.2%/year categories and optional
area-weighted KGPV summaries. See the [scientific contract and runnable synthetic
example](docs/degradation.md).

The [degradation-rate gallery](docs/degradation-gallery.md) recalculates the saved
2016-2018 ERA5 scenario from annual stresses and shows four mechanism/combined-rate
maps plus rate categories. It includes the full offline input bundle and keeps
the 15-degree sampling, calibration assumptions and missing-data mask explicit.

## Creator and contact

Energy Data Insights is created and maintained by **ASVA Consulting**.

- Website: https://asvaconsulting.com
- Contact: [contacto@asvaconsulting.com](mailto:contacto@asvaconsulting.com)

Terrain: [SRTM, Copernicus DEM, IGN and USGS connectors](docs/terrain.md),
with native-resolution maps and a one-site elevation/metadata example.

Satellite imagery: [Orbital PV connector and native-resolution usage](docs/satellite-imagery.md), including 10 m Sentinel-2 and an attributed 0.33 m WorldView example.
The [solar-farm example near Candelaria, Tenerife](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/plot_candelaria_solar_farm.html) maps Planta Icor in Arico, with official site metadata, a plant boundary, Sentinel-2 and a separate detailed PNOA aerial view.
