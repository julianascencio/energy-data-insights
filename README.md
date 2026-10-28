# Energy Data Insights

Python tools for retrieving energy and weather data, applying reusable
scientific methods, and running reproducible fleet performance studies.
The first country workflow is Chile's solar fleet.

## Repository structure

| Subproject | Contents | Python import |
| --- | --- | --- |
| [Data-retrieval](Data-retrieval/) | One folder per provider: CEN, Open-Meteo, and native ERA5 through Earthmover; bounded requests, normalization and provenance | `energy_data_retrieval` |
| [methods](methods/) | TDP, acceptance bands, PR filtering, effective POA and timing, constrained physics, LightGBM, evaluation and hourly operational screening | `energy_methods` |
| [Analysis](Analysis/) | Chile fleet configuration, input preparation, chronological fitting/evaluation and site/fleet outputs | `energy_analysis` |

These are independently installable Python packages in one uv workspace. Each
has its own source, tests and packaging metadata; one lockfile keeps their
dependencies consistent. The directory names follow the requested organization.
See [architecture and extension points](docs/architecture.md).

## Install

Use Python 3.12 or 3.13 and uv 0.13.4 or later:

```bash
git clone https://github.com/julianascencio/energy-data-insights.git
cd energy-data-insights
uv sync --locked --all-packages
```

The optional native ERA5 source has additional dependencies; its package README
documents installation. Ordinary tests and the synthetic demo require no API
credentials and make no live provider requests.

## Run an end-to-end example

```bash
uv run --no-sync energy-chile demo --output artifacts/demo
```

The demo creates **explicitly synthetic** hourly inputs and runs the full
country workflow. It is a smoke test and usage example, not a report about real
Chilean farms. To exercise the alternative model:

```bash
uv run --no-sync energy-chile demo --algorithm lightgbm --output artifacts/demo-lightgbm
```

For actual data, follow the [Chile workflow and schemas](Analysis/README.md).
The `prepare` command joins normalized generation/weather records, and `run`
uses a TOML study configuration with explicit paths and time boundaries:

```bash
uv run --no-sync energy-retrieve --help
uv run --no-sync energy-chile prepare --help
uv run --no-sync energy-chile compare --help
uv run --no-sync energy-chile run --config Analysis/examples/chile_fleet.toml
```

The real-data example requires your own acquired input files. Source-specific
retrieval commands, credentials, API access limitations and provider attribution
are documented in [Data-retrieval](Data-retrieval/README.md). Environment-variable
names are listed in [.env.example](.env.example); credentials are never bundled.
Use `energy-chile compare` when you already have frozen expected-generation
columns: it performs fleet accounting without fitting or replacing those values.

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
