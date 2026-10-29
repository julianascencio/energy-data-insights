"""Generate a transparent synthetic analogue of the thesis case-study design."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 202110


def create_demo(output: Path, *, seed: int = SEED) -> Path:
    """Write ten calibration years and seven 50-year artificial climate paths.

    These are not EURAC measurements, CMIP6 downloads or published SSP results.
    All CSV rows and the generated configuration carry the synthetic designation.
    """
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    inputs = output / "inputs"
    inputs.mkdir()
    rng = np.random.default_rng(seed)
    months = pd.period_range("2010-01", "2019-12", freq="M", name="month")
    seasonal = np.sin(2 * np.pi * (months.month.to_numpy() - 3) / 12)
    ghi = (145 + 90 * seasonal) * (1 + rng.normal(0, 0.035, len(months)))
    temperature = 12 + 11 * seasonal + rng.normal(0, 0.6, len(months))
    daily_yield = ghi * 0.024 * (0.90 - 0.05 * seasonal) * (1 + rng.normal(0, 0.02, len(months)))
    measured = pd.DataFrame(
        {
            "ghi_wm2": ghi,
            "temperature_c": temperature,
            "days": months.days_in_month,
            "dc_yield_kwh_kwp": daily_yield * months.days_in_month,
            "data_kind": "synthetic",
        },
        index=months,
    )
    measured.to_csv(inputs / "measured.csv", index_label="month")
    lines = [
        "[ccya]",
        'title = "CCYA: Bolzano thesis workflow demonstration"',
        'data_kind = "synthetic"',
        'measured_path = "inputs/measured.csv"',
        'measured_source = "Artificial DC yield and weather; '
        f'generator seed {seed}; no EURAC data"',
        'output_path = "results"',
        "degradation_rates = [0.0, 0.0025, 0.005, 0.01]",
        "report_years = [25, 50]",
        "plot_degradation_rate = 0.005",
        "",
    ]
    recipes = [
        (0.12, 1.3),
        (0.09, 1.8),
        (0.03, 2.5),
        (-0.02, 3.7),
        (0.06, 2.8),
        (0.02, 3.5),
        (-0.05, 4.8),
    ]
    future_index = pd.period_range("2020-01", "2069-12", freq="M", name="month")
    age = np.repeat(np.arange(50), 12)
    for number, (ghi_change, warming) in enumerate(recipes):
        key = f"synthetic-path-{number + 1}"
        history = measured.drop(columns="dc_yield_kwh_kwp").copy()
        history["ghi_wm2"] = (ghi - 6) / (1.06 + number * 0.005) + rng.normal(0, 3, len(ghi))
        history["temperature_c"] = temperature - 5 - number * 0.1 + rng.normal(0, 0.4, len(ghi))
        history.to_csv(inputs / f"{key}-historical.csv", index_label="month")
        centers = history[["ghi_wm2", "temperature_c"]].groupby(months.month).mean()
        future = pd.DataFrame(
            {
                "ghi_wm2": centers["ghi_wm2"].to_numpy()[future_index.month.to_numpy() - 1],
                "temperature_c": centers["temperature_c"].to_numpy()[
                    future_index.month.to_numpy() - 1
                ],
                "days": future_index.days_in_month,
                "data_kind": "synthetic",
            },
            index=future_index,
        )
        variability = 0.025 * np.sin(age * 0.71 + number) + 0.012 * np.cos(age * 1.13)
        future["ghi_wm2"] *= 1 + ghi_change * age / 49 + variability
        future["temperature_c"] += warming * age / 49 + 0.35 * np.sin(age * 0.47 + number)
        future.to_csv(inputs / f"{key}-projection.csv", index_label="month")
        lines.extend(
            [
                "[[scenarios]]",
                f'id = "{key}"',
                f'label = "Path {chr(65 + number)}"',
                f'historical_path = "inputs/{key}-historical.csv"',
                f'projection_path = "inputs/{key}-projection.csv"',
                f'source = "Synthetic path: imposed GHI change {100 * ghi_change:g}%, '
                f'warming {warming:g} C over 50 years; seed {seed}; not an SSP projection"',
                "",
            ]
        )
    config = output / "case.toml"
    config.write_text("\n".join(lines), encoding="utf-8")
    return config
