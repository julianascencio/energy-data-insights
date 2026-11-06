"""Contract tests for the AEMET temperature forecasting runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "aemet_temperature_benchmark.py"
SPEC = importlib.util.spec_from_file_location("aemet_temperature_benchmark", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
benchmark_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark_module)


def test_load_station_decimal_comma_and_missing_dates(tmp_path: Path) -> None:
    path = tmp_path / "aemet.csv"
    path.write_text(
        "fecha,indicativo,tmed\n2023-01-01,C001,12,5\n".replace("12,5", '"12,5"')
        + "2023-01-03,C001,13\n"
        + "2023-01-02,C002,25\n"
    )
    series = benchmark_module.load_aemet(path, "C001")
    assert len(series) == 3
    assert series.iloc[0] == 12.5
    assert np.isnan(series.iloc[1])
    with pytest.raises(ValueError, match="No observations"):
        benchmark_module.load_aemet(path, "UNKNOWN")


def test_baselines_are_causal_and_keep_negative_temperatures() -> None:
    dates = pd.date_range("2022-01-01", periods=400)
    series = pd.Series(np.linspace(-12.0, -2.0, 400), index=dates)
    future = pd.date_range(dates[-1] + pd.Timedelta(days=1), periods=10)
    np.testing.assert_allclose(benchmark_module.forecast("last_value", series, future), -2.0)
    weekly = benchmark_module.forecast("seasonal_7", series, future)
    assert len(weekly) == 10
    assert (weekly < 0).all()


def test_rolling_origins_do_not_see_future_labels() -> None:
    dates = pd.date_range("2022-01-01", periods=440)
    series = pd.Series(np.arange(440, dtype=float), index=dates)
    scores = benchmark_module.benchmark(series, ["last_value"], [1, 7], 2)
    assert set(scores["horizon_days"]) == {1, 7}
    assert len(scores) == 4
    assert (scores["mae_c"] >= 0).all()


def test_missing_training_data_is_not_imputed() -> None:
    dates = pd.date_range("2022-01-01", periods=440)
    series = pd.Series(np.arange(440, dtype=float), index=dates)
    series.iloc[100] = np.nan
    with pytest.raises(ValueError, match="No complete eligible origins"):
        benchmark_module.benchmark(series, ["last_value"], [1], 2)
