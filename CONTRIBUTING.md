# Contributing

Use Python 3.12 or 3.13 and uv. From the repository root:

```bash
uv sync --locked --all-packages
uv run --no-sync ruff format .
uv run --no-sync ruff check .
uv run --no-sync ty check
uv run --no-sync pytest
uv run --no-sync python scripts/check_repository.py
uv run --no-sync python scripts/check_citations.py
uv build --all-packages
```

Run `uv lock` after intentional dependency changes and commit `uv.lock` with
the affected `pyproject.toml`. CI uses the lockfile and fails if it is stale.
NumPy is currently bounded below 2.4: the validated 2.3.5 line avoids a
NumPy 2.5/pandas 2.3/pvlib import deprecation found by the strict test suite.
Revisit that compatibility bound with the full scientific tests when upgrading.

Keep provider logic in `data-retrieval`, reusable numerical algorithms in
`methods`, and study-specific orchestration in `analysis`. Public APIs need
type annotations, units, timestamp semantics and explicit handling of missing
values. Input validation should fail at the boundary with a useful message.
Keep report generation in the respective analysis's `reports/` package; write
generated reports below that analysis run's output folder.

Credit every paper and source introduced or discussed by a contribution. Add
verified metadata to `methods/src/energy_methods/references.json`, connect
method `REFERENCE_IDS`, then run `uv run python scripts/check_citations.py --write`.
The PhD thesis remains the primary scientific citation. Identify background
references and implementation adaptations explicitly. Citing the thesis does
not replace attribution to individual method authors or data providers.

Test scientific decisions with small independent calculations and edge cases:
reported zeros, all-missing series, duplicate keys, DST, empty training sets,
training/holdout separation and unsupported model domains. Synthetic fixtures
must be labeled as synthetic. Network tests use mocked transports; CI does not
need a user's API credentials or perform national data downloads.

Prefer vectorized calculations and bounded batches. Parallelize at one level
at a time and bound model threads to avoid CPU oversubscription. Benchmark a
specific workload before claiming a speed improvement; include the workload,
versions and machine context with a result. Do not add a timing assertion that
will fail unpredictably on shared CI runners.

Commit source, tests, small documented fixtures and scientific references.
Keep raw data, fitted artifacts, generated dashboards, secrets and local
configuration outside Git. The repository hygiene check is a basic safeguard,
not a comprehensive secret detector.
