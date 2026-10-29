# Validation record

## Historical imports, analysis reports and citations — 29 October 2026

Validated locally with Python 3.12.14, Ruff 0.17.3 and ty 0.0.94 using the
updated lockfile. CI exercises the same required checks on Python 3.12/3.13.

| Check | Result |
| --- | --- |
| Ruff formatting and lint | Passed |
| ty, warnings treated as errors | Passed |
| Complete pytest suite | 116 passed |
| Retrieval / methods / analysis tests | 50 / 37 / 29 passed |
| Citation catalogue and generated-export consistency | Passed; 26 entries |
| CFF metadata | Validated against official CFF 1.2.0 schema |
| BibTeX metadata | All 26 entries parsed successfully |
| Three wheels and three source distributions | Built successfully |
| Built-wheel import/report smoke check | Passed, including packaged reference JSON |
| Physics and LightGBM examples with `--reports` | Both completed |
| Offline desktop/mobile browser checks | Passed at 1440 × 1000 and 390 × 844 |
| Browser search, group filter and numeric sorting | Passed |
| Browser JavaScript errors / external HTTP requests / page overflow | None |
| Repository hygiene and patch whitespace checks | Passed |

Historical tests exercise alias resolution, a single site per physical unit,
equal-duplicate removal, conflict rejection, incomplete unit rosters, explicit
units, source precision/basis, DST gaps/folds, end-labelled wide-hour exports,
bounded XLSX/ZIP handling and checkpoint/hash-verified downloads. A reviewer found
and corrected a case where aliases could assign one physical unit to two sites;
the regression test prevents duplicated site generation.

Report tests check preservation of source inputs and frozen references,
matched-energy accounting, unavailable evidence, escaping, safe filenames,
source hash/summary verification, atomic failure cleanup, persistent synthetic
labels and energy-conserving chart aggregation. The dashboard holds summary
rows and links to separate site pages instead of embedding fleet-wide hourly
history in a single HTML payload. Validation used a temporary headless Chromium
browser; no browser package is added to the Python runtime dependencies.

These results validate code and controlled fixtures. They do not establish live
CEN/Qlik authorization, a fresh national history download, measured-station
accuracy, or replay of the earlier archived production release. The two model
examples and browser previews use explicitly synthetic data. The previous
release's raw data, fitted coefficients and dashboard are not changed.

## Initial workspace — 28 October 2026

Validation performed on 28 October 2026, with Python 3.12.14 on Linux x86-64.
The committed `uv.lock` records the complete dependency resolution.

| Check | Local result |
| --- | --- |
| Ruff 0.17.3 formatting | Passed |
| Ruff 0.17.3 lint | Passed |
| ty 0.0.94 | Passed |
| pytest, warnings treated as errors | 77 passed in 8.43 seconds |
| Combined statement/branch coverage report | 80% |
| Retrieval package | 32 tests passed |
| Scientific methods package | 25 tests passed |
| Chile analysis package | 20 tests passed |
| All three wheels and source distributions | Built successfully |
| Physics CLI example | Completed |
| LightGBM CLI example | Completed |
| Repository source/credential check | Passed |

The CLI examples use deterministic synthetic observations. Both process two
supported sites plus an empty registry record and produce model, hourly-status,
fleet and TDP outputs. They are not validation against real Chile field data.
API tests use mocked HTTP and native-array fixtures; live provider availability,
authorization and optional native-store dependencies are not asserted by these
tests. CI also runs on Python 3.13; its outcome is recorded in the pull request's
checks rather than inferred from this local Python 3.12 run.

## Scientific regressions

Tests cover reported zero versus missing energy, exact coverage/tolerance
boundaries, negative energy, DST offsets, complete-unit aggregation, source-unit
conversion, PR boundaries, support/extrapolation, physical response derivatives,
LightGBM monotonicity, chronological geometry/model fitting, TDP year-month
qualification and the operational-screen precedence/persistence rules.

The frozen-reference workflow is tested for unchanged input hashes and no model
fitting. Output manifests are checked against actual output bytes after the run
directory is committed. Spreadsheet exports escape metadata formula prefixes
without changing numeric negative values or the underlying Parquet metadata.

Two compatibility issues found during implementation were corrected:

- NumPy is constrained to the verified 2.3.x-compatible range; the initial
  NumPy 2.5.4/pandas/pvlib combination emitted an import-time deprecation under
  strict warnings. The final environment uses NumPy 2.3.5.
- LightGBM monotone constraints reject the `regression_l1` objective. The
  tested implementation uses squared-error `regression`, with that distinction
  documented rather than hidden behind an incompatible parameter combination.

## Measured synthetic workloads

These are local, machine-dependent measurements; they are not service-level
guarantees and do not measure production national retrieval.

**Fleet accounting:** 787 sites × 2,207 hours = 1,736,909 site-hours. Three runs
took 0.1366, 0.1409 and 0.1361 seconds (median 0.1366 seconds), using one shared
hourly pattern and one summary row per site. Matched energy agreed with an
independent scalar calculation. I/O, model training and POA are excluded.

**POA geometry bank:** 2,160 hours, 32 geometries and five candidate lags.
Repeated independent transpositions took 5.9399 seconds; fitting with prepared
solar/GHI/decomposition arrays took 0.4734 seconds. The measured ratio was
12.55×, with a bit-identical selected projection. The repeated path measures
transposition only, while the prepared path also performs candidate selection.
This comparison demonstrates reuse of invariant calculations, not a universal
speed factor for the entire analysis pipeline.

Reproduce these workloads with `benchmarks/fleet_accounting.py` and
`methods/benchmarks/benchmark_poa.py`. BLAS/OpenMP thread counts were set to one.
