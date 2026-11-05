"""Scientific contracts for the AEMET/ERA5 scenario workflow."""

import numpy as np
import pandas as pd
import pytest

from energy_analysis.aemet_era5_canary import annual_drivers, daily_pairs, validate


def test_temperature_pair_uses_daily_extrema_midpoint():
    index = pd.date_range("2022-01-01", periods=24, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "temperature_c": [0.0] * 23 + [20.0],
            "relative_humidity_percent": 50.0,
            "wind_speed_ms": 2.0,
            "ghi_wm2": 0.0,
        },
        index=index,
    )
    observed = pd.DataFrame(
        {"fecha": ["2022-01-01"], "tmed": ["10,0"], "hrMedia": ["50"], "velmedia": ["2,0"]}
    )
    pairs = daily_pairs(observed, frame)
    t = pairs.loc[pairs.variable == "temperature_c"].iloc[0]
    assert t.observed == t.modelled == 10


def test_full_year_and_uv_energy_contract():
    index = pd.date_range("2023-01-01", "2024-01-01", inclusive="left", freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "temperature_c": 20.0,
            "relative_humidity_percent": 50.0,
            "wind_speed_ms": 2.0,
            "ghi_wm2": 100.0,
        },
        index=index,
    )
    drivers = annual_drivers(frame)
    assert drivers["uv_dose_kwh_m2"] == pytest.approx(43.8)
    assert drivers["cycles_per_year"] == 365
    with pytest.raises(ValueError, match="Complete"):
        annual_drivers(frame.iloc[:-1])
    frame.iloc[0, 0] = np.nan
    with pytest.raises(ValueError, match="Finite"):
        annual_drivers(frame)


def test_holdout_metrics_include_worsening_not_just_success():
    dates = pd.date_range("2023-01-01", "2023-12-31")
    pairs = pd.DataFrame(
        {"date": dates, "variable": "temperature_c", "observed": 10.0, "modelled": 11.0}
    )
    result = validate(pairs, {"temperature_c": np.ones(12)})[0]
    assert result["raw_monthly_rmse"] == 1
    assert result["corrected_monthly_rmse"] == 2


def test_offline_pipeline_exports_verified_rasters(tmp_path):
    """A controlled two-station fixture exercises fit, holdout and raster export."""
    import hashlib
    import json

    import rasterio

    from energy_analysis.aemet_era5_canary import run_study

    folder = tmp_path / "study"
    (folder / "weather").mkdir(parents=True)
    stamps = pd.date_range("2022-01-01", "2024-01-01", inclusive="left", freq="h", tz="UTC")
    hourly = pd.DataFrame(
        {
            "timestamp": stamps,
            "temperature_c": 20.0,
            "relative_humidity_percent": 50.0,
            "wind_speed_ms": 2.0,
            "ghi_wm2": 100.0,
        }
    )
    path = folder / "weather/28.25_-16.50.csv"
    hourly.to_csv(path, index=False)
    (folder / "weather/28.25_-16.50.json").write_text(
        json.dumps(
            {
                "files": [
                    {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                ]
            }
        )
    )
    stations = pd.DataFrame(
        {"station_id": ["C001", "C002"], "latitude": [28.25, 28.25], "longitude": [-16.5, -16.5]}
    )
    stations.to_csv(folder / "stations.csv", index=False)
    dates = pd.date_range("2022-01-01", "2023-12-31").strftime("%Y-%m-%d")
    observations = pd.concat(
        [
            pd.DataFrame(
                {
                    "indicativo": sid,
                    "fecha": dates,
                    "tmed": "23,0",
                    "hrMedia": "55",
                    "velmedia": "3,0",
                }
            )
            for sid in stations.station_id
        ]
    )
    observations.to_csv(folder / "daily.csv", index=False)
    (folder / "aemet_provenance.json").write_text(
        json.dumps(
            {
                "daily_files": [
                    {
                        "file": "daily.csv",
                        "sha256": hashlib.sha256((folder / "daily.csv").read_bytes()).hexdigest(),
                    }
                ],
                "station_sha256": hashlib.sha256(
                    (folder / "stations.csv").read_bytes()
                ).hexdigest(),
            }
        )
    )
    from rasterio.warp import transform

    x, y = transform("EPSG:4326", "EPSG:32628", [-16.5], [28.25])
    pd.DataFrame(
        {
            "row": [25],
            "col": [40],
            "latitude": [28.25],
            "longitude": [-16.5],
            "easting": x,
            "northing": y,
        }
    ).to_csv(folder / "grid.csv", index=False)
    parameters = tmp_path / "parameters.json"
    parameters.write_text(
        json.dumps(
            {
                "a_h": 1.0,
                "a_p": 1.0,
                "a_tm": 1.0,
                "e_h": 0.7,
                "e_p": 0.5,
                "e_tm": 0.4,
                "n": 1.0,
                "x": 1.0,
                "theta": 1.0,
                "a_n": 1.0,
                "calibration_id": "synthetic-test-only",
                "calibration_source": "unit test fixture",
            }
        )
    )
    summary = run_study(folder, parameters)
    assert summary["supported_grid_cells"] == 1
    assert summary["stations_with_coefficients"] == 2
    validation = pd.read_csv(folder / "validation.csv")
    np.testing.assert_allclose(validation.corrected_monthly_rmse, 0, atol=1e-10)
    with rasterio.open(folder / "corrected_rates.tif") as raster:
        assert raster.count == 4
        assert np.isfinite(raster.read()[:, 25, 40]).all()
