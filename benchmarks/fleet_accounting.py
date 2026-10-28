"""Measure fleet accounting on explicit synthetic hourly inputs, without network I/O."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from energy_analysis.chile_fleet.fleet import compare_site, summarize_fleet


def run(sites: int, hours: int, repeats: int) -> dict[str, object]:
    """Keep one site's hourly arrays in memory and retain only per-site summaries."""
    if sites < 1 or hours < 24 or repeats < 1:
        raise ValueError("Use positive sites/repeats and at least 24 hours")
    random = np.random.default_rng(42)
    hour = np.arange(hours) % 24
    expected = np.maximum(0.0, np.sin((hour - 6) * np.pi / 12)) * 20
    actual = expected * random.uniform(0.65, 1.15, hours)
    actual[::97] = np.nan
    actual[::211] = 0.0
    actual[::509] = -1.0
    data = pd.DataFrame(
        {
            "actual_mwh": actual,
            "expected_mwh": expected,
            "ghi_wm2": expected * 50,
            "temperature_c": 18 + 8 * np.sin(hour * np.pi / 12),
            "wind_speed_ms": random.uniform(0, 12, hours),
            "gust_ms": random.uniform(12, 24, hours),
        }
    )
    # A scalar check is independent of the vectorized accounting implementation.
    pairs = [
        (float(a), float(e))
        for a, e in zip(actual, expected, strict=True)
        if np.isfinite(a) and a >= 0 and np.isfinite(e) and e >= 0
    ]
    reference_actual = sum(a for a, _ in pairs)
    reference_expected = sum(e for _, e in pairs)
    first = compare_site(data)
    first_actual, first_expected = first["matched_actual_mwh"], first["matched_expected_mwh"]
    if not isinstance(first_actual, (int, float)) or not isinstance(first_expected, (int, float)):
        raise TypeError("Fleet accounting must return numeric matched energy")
    if not np.isclose(first_actual, reference_actual):
        raise AssertionError("Scalar/vector matched actual energy differs")
    if not np.isclose(first_expected, reference_expected):
        raise AssertionError("Scalar/vector matched expected energy differs")
    durations: list[float] = []
    result: dict[str, object] = {}
    for _ in range(repeats):
        started = time.perf_counter()
        rows = [{"site_id": str(index), **compare_site(data)} for index in range(sites)]
        result = summarize_fleet(pd.DataFrame(rows))
        durations.append(time.perf_counter() - started)
    median = statistics.median(durations)
    return {
        "benchmark": "fleet-accounting-v1",
        "input_kind": "deterministic synthetic; identical hourly pattern reused per site",
        "scope": (
            "Matched energy, weather summaries, coverage and fleet totals only; "
            "excludes I/O, POA and model training"
        ),
        "sites": sites,
        "hours_per_site": hours,
        "site_hours": sites * hours,
        "repeats": repeats,
        "seconds": durations,
        "median_seconds": median,
        "site_hours_per_second": sites * hours / median,
        "working_data_strategy": "one hourly site frame plus one summary row per site",
        "scalar_energy_check_passed": True,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "pandas", "energy-analysis")
        },
        "fleet_summary": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", type=int, default=787)
    parser.add_argument("--hours", type=int, default=2207)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.sites, args.hours, args.repeats)
    payload = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
