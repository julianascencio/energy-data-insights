"""Run deterministic synthetic CCYA paths, not real SSP or Bolzano projections.

From the workspace: uv run --no-sync python methods/examples/ccya_synthetic.py
Prints portable calibration provenance and 25/50-year cumulative comparisons.
No API calls, files, random values or original research datasets are required.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from energy_methods.ccya import fit_ccya


def synthetic_climate(start_year: int, years: int) -> pd.DataFrame:
    """Synthetic monthly seasonal weather on its native Gregorian calendar."""
    index = pd.period_range(f"{start_year}-01", periods=12 * years, freq="M")
    seasonal = np.sin(2 * np.pi * (index.month.to_numpy() - 3) / 12)
    return pd.DataFrame(
        {
            "ghi_wm2": 150 + 90 * seasonal,
            "temperature_c": 12 + 9 * seasonal,
            "days": index.days_in_month,
        },
        index=index,
    )


def main() -> None:
    historical = synthetic_climate(2010, 10)
    measured = historical.copy()
    measured["ghi_wm2"] = 1.1 * historical["ghi_wm2"] + 5
    measured["temperature_c"] = historical["temperature_c"] + 2
    measured["dc_yield_kwh_kwp"] = measured["ghi_wm2"] * 24 / 1000 * 0.85 * measured["days"]
    model = fit_ccya(measured, historical)
    print("SYNTHETIC ONLY: no real climate-model or plant data")
    print(json.dumps(model.to_dict(), indent=2, allow_nan=False))
    rows = []
    for label, total_ghi_change, total_warming in (
        ("synthetic_brightening", 0.10, 2.0),
        ("synthetic_dimming", -0.05, 4.0),
    ):
        future = synthetic_climate(2020, 50)
        progress = np.repeat(np.arange(50) / 49, 12)
        future["ghi_wm2"] *= 1 + total_ghi_change * progress
        future["temperature_c"] += total_warming * progress
        for rate in (0.0, 0.0025, 0.005, 0.01):
            result = model.project(future, scenario=label, degradation_per_year=rate)
            for operating_year in (25, 50):
                row = result.annual.iloc[operating_year - 1]
                rows.append(
                    {
                        "synthetic_scenario": label,
                        "degradation_pct_year": rate * 100,
                        "operating_year": operating_year,
                        "irradiance_gain_pct": row["irradiance_cumulative_gain_p50_pct"],
                        "with_temperature_gain_pct": row[
                            "irradiance_temperature_cumulative_gain_p50_pct"
                        ],
                        "with_power_gain_pct": row["irradiance_power_cumulative_gain_p50_pct"],
                        "combined_gain_pct": row["combined_cumulative_gain_p50_pct"],
                    }
                )
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
