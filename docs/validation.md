# Initial workspace validation

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
