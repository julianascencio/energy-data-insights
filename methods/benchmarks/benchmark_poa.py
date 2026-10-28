"""Compare repeated transposition with prepared geometry-bank fitting.

Run from the repository root:
    uv run python methods/benchmarks/benchmark_poa.py --hours 2160

Inputs are explicitly synthetic; timings are local measurements, not a guaranteed
fleet throughput. Both paths calculate the same physical transposition outputs.
"""

from __future__ import annotations

import argparse
import json
from time import perf_counter

import numpy as np
import pandas as pd
import pvlib

from energy_methods.poa import Geometry, fit_effective_poa, solar_elevation_midpoint, transpose_ghi


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=int, default=2160)
    args = parser.parse_args()
    if not 168 <= args.hours <= 17520:
        parser.error("hours must be between one week and two years")
    times = pd.date_range("2026-07-01", periods=args.hours, freq="h", tz="UTC")
    elevation = solar_elevation_midpoint(times, -33.5, -70.6)
    ghi = np.maximum(np.sin(np.radians(elevation)), 0) * 950
    candidates = [
        Geometry(tilt_deg=tilt, azimuth_deg=azimuth)
        for tilt in (0, 10, 20, 30, 40)
        for azimuth in (0, 30, 90, 180)
    ]
    candidates += [
        Geometry(kind="single_axis", axis_azimuth_deg=azimuth, gcr=gcr)
        for azimuth in (0, 30, 90, 150)
        for gcr in (0.25, 0.35, 0.45)
    ]
    started = perf_counter()
    separate = [
        transpose_ghi(times, ghi, -33.5, -70.6, geometry).poa_wm2 for geometry in candidates
    ]
    repeated_seconds = perf_counter() - started
    actual = separate[8] * 0.008
    started = perf_counter()
    fitted = fit_effective_poa(
        times, ghi, actual, -33.5, -70.6, training_end=times[-1], candidates=candidates
    )
    prepared_seconds = perf_counter() - started
    baseline = separate[candidates.index(fitted.geometry)]
    np.testing.assert_allclose(fitted.poa_wm2, baseline, rtol=0, atol=0)
    print(
        json.dumps(
            {
                "input": "synthetic",
                "hours": args.hours,
                "geometries": len(candidates),
                "lags_per_geometry": 5,
                "repeated_transposition_seconds": repeated_seconds,
                "prepared_bank_fitting_seconds": prepared_seconds,
                "ratio_repeated_to_prepared": repeated_seconds / prepared_seconds,
                "selected_projection_identical": True,
                "pvlib_version": pvlib.__version__,
                "numpy_version": np.__version__,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
