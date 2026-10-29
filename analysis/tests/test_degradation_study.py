"""Synthetic provider data exercise retrieval -> saved partitions -> methods -> report."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from energy_analysis.degradation.cli import main
from energy_analysis.degradation.config import StudyConfig, load_config
from energy_analysis.degradation.pipeline import retrieve, run
from energy_data_retrieval.sources.open_meteo.client import OPEN_METEO_HOSTS
from energy_data_retrieval.storage import sha256_file
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def config() -> StudyConfig:
    original = load_config(ROOT / "analysis/examples/degradation/global_2016_2018.toml")
    return replace(
        original,
        name="Synthetic test only",
        latitude_min=0,
        latitude_max=15,
        longitude_min=0,
        longitude_max=15,
        end_year=2017,
    )


@pytest.fixture
def inputs(tmp_path: Path, config: StudyConfig, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Mock only the external CRU acquisition. Open-Meteo parsing, alignment, partition
    # writing, SHA checks and all scientific calculations use their real implementations.
    months = xr.DataArray(
        [[[20.0, np.nan], [np.nan, 20.0]]],
        dims=("time", "lat", "lon"),
        coords={"time": [pd.Timestamp("2016-01-01")], "lat": [0, 15], "lon": [0, 15]},
    )
    module = "energy_analysis.degradation.pipeline"
    monkeypatch.setattr(f"{module}.CRUTSClient.download", lambda *args: [])
    monkeypatch.setattr(f"{module}.iter_monthly", lambda *args, **kwargs: iter([months]))
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        start = pd.Timestamp(params["start_date"], tz="UTC")
        stop = pd.Timestamp(params["end_date"], tz="UTC") + pd.Timedelta(days=1)
        times = pd.date_range(start, stop, freq="h", inclusive="left")
        length = len(times)
        daylight = (times.hour >= 7) & (times.hour <= 18)
        rh: list[float | None] = [50.0] * length
        if float(params["latitude"]) == 15 and start.year == 2016:
            rh[10] = None  # two adjacent normalized hours, hence whole cell-year unavailable
        toa = np.where(daylight, 1000.0, 0.0)
        if float(params["latitude"]) == 15 and start.year == 2017:
            toa[2] = -15.0  # invalid provider night value must remain unavailable
        calls.append(str(request.url))
        return httpx.Response(
            200,
            json={
                "latitude": float(params["latitude"]),
                "longitude": float(params["longitude"]),
                "utc_offset_seconds": 0,
                "hourly_units": {
                    "temperature_2m": "°C",
                    "wind_speed_10m": "m/s",
                    "wind_gusts_10m": "m/s",
                    "shortwave_radiation": "W/m²",
                    "relative_humidity_2m": "%",
                    "terrestrial_radiation": "W/m²",
                },
                "hourly": {
                    "time": (times.as_unit("s").astype("int64")).tolist(),
                    "temperature_2m": [20.0] * length,
                    "wind_speed_10m": [2.0] * length,
                    "wind_gusts_10m": [3.0] * length,
                    "relative_humidity_2m": rh,
                    "shortwave_radiation": np.where(daylight, 500.0, 0.0).tolist(),
                    "terrestrial_radiation": toa.tolist(),
                },
            },
        )

    directory = tmp_path / "inputs"
    with HTTPClient(
        OPEN_METEO_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        retrieve(config, directory, http)
        assert len(calls) == 4
        retrieve(config, directory, http)  # valid partitions restart without weather requests
        assert len(calls) == 4
    return directory


@pytest.mark.integration
def test_saved_inputs_to_real_methods_and_report(
    config: StudyConfig,
    inputs: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Computation must be offline; no provider object may be instantiated.
    monkeypatch.setattr(
        "energy_analysis.degradation.pipeline.OpenMeteoClient",
        lambda *args, **kwargs: pytest.fail("run attempted retrieval"),
    )
    output = tmp_path / "output"
    result_path = run(config, inputs, output)
    with xr.open_dataset(output / "annual_stresses.nc") as annual:
        row = annual.sel(year=2016, lat=0, lon=0)
        assert row.uv_dose_kwh_m2.item() == pytest.approx(30.871 * 12 * 366 / 1000)
        assert row.cycles_per_year.item() == 366
        assert row.valid_hour_count.item() == 8784
        assert annual.negative_toa_hours.sel(year=2017, lat=15, lon=15).item() == 1
        assert annual.valid_hour_count.sel(year=2017, lat=15, lon=15).item() == 8759
        assert annual.valid_hour_count.sel(year=2016, lat=15, lon=15).item() == 8782
    with xr.open_dataset(result_path) as result:
        assert np.isnan(result.total_rate.sel(lat=15, lon=15))
        assert result.rate_class.sel(lat=15, lon=15) == 0
        # Independent closed-form calculation from constant synthetic weather.
        parameters = config.parameters()
        rise = 500 / (26.9 + 6.2 * 2 * 0.2**0.2)
        temperature = 20 + rise / 2 + 273.15
        kb = 8.62e-5  # Rounded publication constant retained by the methods model.
        kh = parameters.a_h * 50**parameters.n * np.exp(-parameters.e_h / (kb * temperature))
        uv = 30.871 * 12 * 365.5 / 1000
        kp = (
            parameters.a_p
            * uv**parameters.x
            * (1 + 50**parameters.n)
            * np.exp(-parameters.e_p / (kb * temperature))
        )
        kt = (
            parameters.a_tm
            * rise**parameters.theta
            * 365.5
            * np.exp(-parameters.e_tm / (kb * (20 + rise + 273.15)))
        )
        expected = parameters.a_n * (1 + kh) * (1 + kp) * (1 + kt) - 1
        assert result.total_rate.sel(lat=0, lon=0).item() == pytest.approx(expected)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is True
    assert (
        manifest["land_cells"],
        manifest["valid_cells"],
        manifest["masked_incomplete_cells"],
    ) == (2, 1, 1)
    assert manifest["hours_retrieved"] == 2 * (8784 + 8760)
    for path, checksum in manifest["outputs_sha256"].items():
        assert sha256_file(output / path) == checksum
    report = (output / "reports/index.html").read_text()
    assert "data:image/png;base64," in report and "site-specific" in report
    with pytest.raises(FileExistsError):
        run(config, inputs, output)


@pytest.mark.parametrize("target", ["mask", "partition", "manifest"])
def test_corrupt_input_fails_without_output(
    config: StudyConfig,
    inputs: Path,
    tmp_path: Path,
    target: str,
) -> None:
    if target == "mask":
        with (inputs / "land_mask.nc").open("ab") as stream:
            stream.write(b"corrupt")
    elif target == "partition":
        path = next(inputs.glob("open-meteo/*/*.parquet"))
        with path.open("ab") as stream:
            stream.write(b"corrupt")
    else:
        path = inputs / "retrieval_manifest.json"
        value = json.loads(path.read_text())
        value["partitions"].pop()
        path.write_text(json.dumps(value))
    output = tmp_path / "failed"
    with pytest.raises(ValueError):
        run(config, inputs, output, reports=False)
    assert not output.exists()


def test_configuration_and_cli_boundaries(config: StudyConfig, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exact multiple"):
        replace(config, step_degrees=7)
    with pytest.raises(ValueError, match="years"):
        replace(config, end_year=2015)
    with pytest.raises(ValueError, match="separate"):
        run(config, tmp_path / "data", tmp_path / "data/output")
    with pytest.raises(SystemExit) as error:
        main(
            [
                "run",
                "--config",
                str(ROOT / "analysis/examples/degradation/global_2016_2018.toml"),
                "--data-dir",
                str(tmp_path),
            ]
        )
    assert error.value.code == 2
