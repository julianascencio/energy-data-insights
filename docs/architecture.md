# Architecture

## Three subprojects, one reproducible workspace

The repository has three independently buildable Python distributions. They use
the requested directory names and conventional import names:

| Directory | Distribution | Python import | Responsibility |
| --- | --- | --- | --- |
| `data-retrieval/` | `energy-data-retrieval` | `energy_data_retrieval` | Provider clients, retrieval, normalization and provenance |
| `methods/` | `energy-methods` | `energy_methods` | Country-neutral scientific algorithms |
| `analysis/` | `energy-analysis` | `energy_analysis` | Configured country studies, beginning with Chile's PV fleet |

Each member has its own `pyproject.toml`, `src` layout, documentation and tests.
The root `uv.lock` resolves them together. A change to a scientific method and
its country-level caller can therefore be reviewed and tested in one pull
request. These are package subprojects with a shared Git history.

Dependencies flow from `analysis` to `methods` and `data-retrieval`. The methods
package performs no provider retrieval. Source clients know their provider's
payloads and clocks; they do not decide which sites underperform.

## Data contracts

The interchange is a typed, explicit tabular schema, not a provider's raw JSON.
Hourly records identify a site and an offset-aware UTC timestamp. Energy is
MWh per declared interval; irradiance is W/m², temperature °C and wind m/s.
Coordinate units are decimal degrees. Capacity values are MW with DC and AC
kept distinct. See each package's schema documentation for its exact required
columns and validation rules.

Missing data are missing, not zero. A reported zero is retained. Negative energy
is excluded from performance comparisons and remains distinguishable from an
unreported value. Duplicate site/time keys require an explicit resolution.
Naive local timestamps must not be silently shifted through a daylight-saving
ambiguity. Chile reporting dates use `America/Santiago`; TDP uses its explicitly
declared analysis clock.

Large raw responses, normalized Parquet, fitted models and report outputs live
outside the source tree or in ignored directories. Provenance records bind
inputs and outputs using hashes and record the relevant configuration. API
credentials are supplied locally, not stored in Git or output manifests.

## Scientific boundaries

The reusable implementation comes from the preceding ASVA Chile analysis. It
does not claim to be a byte-identical replacement for every historical script
or fitted model. The saved dashboard release and its production data remain
separate records. New fits record their own configuration and evaluation.

Geometry, timing, acceptance-band bounds and model parameters must be fitted
on training observations. Held-out observations remain available for honest
evaluation, including low or zero production; they must not be filtered using
their own target values to improve the score.

The constrained physical response and LightGBM are distinct algorithms. A
monotonic LightGBM model does not automatically guarantee a concave response.
Neither algorithm guarantees a 75% prediction score for every plant.

An hourly operational screen describes evidence. It does not confirm the cause
of curtailment, outage, environmental restriction or equipment failure. Public
energy and modeled weather alone cannot establish continuous hourly availability.

## Adding another country

1. Add or reuse a provider folder in `data-retrieval`. Translate its units,
   timestamp convention and identity fields into the documented schema.
2. Add a country package under `energy_analysis`, with the regional clock,
   metadata mapping and study configuration.
3. Reuse `energy_methods`; put country-specific assumptions in the country
   workflow, not in the shared algorithms.
   Put report generation in that country's `reports/` subpackage and generated
   artifacts under the corresponding run's `reports/` directory.
4. Add fixtures for provider irregularities, calendar transitions, coverage and
   chronological evaluation. Keep live API calls out of ordinary CI.

## Reports and research attribution

Chile rendering lives in `energy_analysis.chile_fleet.reports`. It consumes the
completed run or frozen-reference comparison contract. The report manifest
records the inputs and output hashes separately from the original analysis;
rendering does not fit a model or change predictions. Individual site pages keep
the fleet landing page small, and publication drafts use the same qualified
totals shown in the dashboard.

The primary scientific citation is Julián Andrés Ascencio Vásquez's 2021 PhD
thesis. `CITATION.cff`, `references.bib` and `docs/references.md` expose citation
metadata for readers and tools. The `energy_methods.references` catalogue is
also available to analysis reports. Method-specific citations credit the
papers actually used and distinguish background context from implemented work.

## Tooling sources

- [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)
- [Ruff configuration](https://docs.astral.sh/ruff/configuration/)
- [ty configuration](https://docs.astral.sh/ty/reference/configuration/)
- [uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)
