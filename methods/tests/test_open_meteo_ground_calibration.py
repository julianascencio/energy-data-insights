"""Offline tests for Open-Meteo ground calibration evaluation."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.open_meteo_ground_calibration import evaluate_station_holdout
from energy_methods.weather_calibration import fit_monthly_bias


def _pairs():
    dates = pd.date_range("2022-01-01", "2024-01-01", freq="D", inclusive="left")
    return pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "variable": "temperature_c",
            "observed": np.full(len(dates), 20.0),
            "modelled": np.full(len(dates), 22.0),
        }
    )


def test_independent_year_improves():
    pairs = _pairs()
    params = fit_monthly_bias(pairs, year=2022)
    report = evaluate_station_holdout(pairs, params, validation_year=2023)
    assert len(report) == 12
    assert report.improved.all()
    assert np.allclose(report.corrected_rmse, 0)
    assert np.allclose(report.raw_rmse, 2)


def test_reject_training_leakage():
    pairs = _pairs()
    params = fit_monthly_bias(pairs, year=2022)
    with pytest.raises(ValueError, match="independent"):
        evaluate_station_holdout(pairs, params, validation_year=2022)


def test_missing_month_is_not_imputed():
    pairs = _pairs()
    pairs = pairs.loc[
        ~((pd.to_datetime(pairs.date).dt.year == 2023) & (pd.to_datetime(pairs.date).dt.month == 3))
    ]
    params = fit_monthly_bias(pairs, year=2022)
    report = evaluate_station_holdout(pairs, params, validation_year=2023)
    assert len(report) == 11
