# Performance and resource bounds

Performance claims need a stated workload. The repository includes a synthetic
benchmark for fleet accounting, separately from retrieval and model fitting:

```bash
uv run --no-sync python benchmarks/fleet_accounting.py \
  --sites 787 --hours 2207 --repeats 3 \
  --output artifacts/fleet-accounting-benchmark.json
```

The default performs accounting for 1,736,909 synthetic site-hours. It validates
matched energy against an independent scalar calculation, then reports timings,
throughput, Python/package versions and machine context. It reuses one site's
hourly frame and retains a summary row per site. It does not measure national
downloads, disk I/O, geometric optimization, TDP or model training. This is not
a benchmark of the historical production dataset.

The architecture uses NumPy/pandas operations within a site and bounded
per-site processing for studies. Network retrieval has finite response sizes,
timeouts, retries and request spacing. Shared public weather cells can be
retrieved once and mapped to many sites; this does not make them independent
on-site measurements. Native ERA5 access is optional and selects the relevant
coordinates/time span rather than downloading the global archive.

LightGBM's worker count is explicit and bounded. CI sets BLAS/OpenMP thread
counts to one so multiple numerical libraries do not compete for the same
cores. Set the same limits when launching multiple per-site workers; prefer
one layer of parallelism. Large data and generated artifacts are not loaded
as part of importing a package.

Timing thresholds are not a correctness gate on shared CI runners. Before
changing a hot path, rerun the same benchmark on the same machine and inspect
both timing and numerical equivalence. Record production workloads separately.
