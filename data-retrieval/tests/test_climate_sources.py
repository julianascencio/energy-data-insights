"""Synthetic offline NetCDF and HTTP fixtures; no credentials or provider downloads."""

import gzip
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from energy_data_retrieval.cli import main
from energy_data_retrieval.climate_grid import open_netcdf
from energy_data_retrieval.sources.cru_ts import CRU_TS_HOSTS, CRUTSClient, CRUTSRequest
from energy_data_retrieval.sources.cru_ts import iter_monthly as cru_monthly
from energy_data_retrieval.sources.gpcc import GPCCRequest
from energy_data_retrieval.sources.gpcc import iter_monthly as gpcc_monthly
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def fixture(tmp_path: Path, variable: str, units: str) -> Path:
    ds = xr.Dataset(
        {variable: (("time", "lat", "lon"), [[[20.0, np.nan], [0.0, 10.0]]])},
        coords={"time": pd.to_datetime(["2025-01-16"]), "lat": [2.0, 1.0], "lon": [350.0, 351.0]},
    )
    ds[variable].attrs["units"] = units
    native = tmp_path / f"{variable}.nc"
    ds.to_netcdf(
        native,
        engine="scipy",
        encoding={variable: {"dtype": "int16", "_FillValue": -9999, "scale_factor": 0.1}},
    )
    path = native.with_suffix(".nc.gz")
    path.write_bytes(gzip.compress(native.read_bytes()))
    return path


def test_gpcc_archive_transition_and_resolution() -> None:
    urls = GPCCRequest(2020, 2025, 0.5, end_month=2).urls()
    assert len(urls) == 4
    assert urls[0].endswith("2016_2020_v2025_050.nc.gz")
    assert urls[1].endswith("2021_2024_v2025_050.nc.gz")
    assert urls[2].endswith("2025_01_v2025_050.nc.gz")
    assert GPCCRequest(1991, 2020).doi == "10.5676/DWD_GPCC/MONTHLY_V2025_050"
    assert len(GPCCRequest(1991, 2020).urls()) == 6
    with pytest.raises(ValueError):
        GPCCRequest(2000, 2001, 0.2)


def test_cru_decades_and_validation() -> None:
    urls = CRUTSRequest("tmp", 1991, 2025).urls()
    assert len(urls) == 4
    assert urls[-1].endswith("cru_ts4.10.2021.2025.tmp.dat.nc.gz")
    for variable, start, end in [("bad", 2000, 2001), ("tmp", 2000, 2026), ("pre", 2001, 2000)]:
        with pytest.raises(ValueError):
            CRUTSRequest(variable, start, end)


@pytest.mark.parametrize("provider", ["gpcc", "cru"])
def test_cf_scaling_missing_coordinates_and_month_labels(tmp_path: Path, provider: str) -> None:
    variable, units = ("precip", "mm/month") if provider == "gpcc" else ("tmp", "degrees Celsius")
    path = fixture(tmp_path, variable, units)
    arrays = (
        gpcc_monthly([path], start_year=2025, end_year=2025)
        if provider == "gpcc"
        else cru_monthly([path], variable="tmp", start_year=2025, end_year=2025)
    )
    result = next(arrays)
    assert result.lat.values.tolist() == [1.0, 2.0]
    assert result.lon.values.tolist() == [-10.0, -9.0]
    assert str(result.time.values[0]).startswith("2025-01-01")
    np.testing.assert_allclose(result.values, [[[0.0, 10.0], [20.0, np.nan]]], equal_nan=True)
    assert result.attrs["units"] == ("mm" if provider == "gpcc" else "degC")


def test_limits_and_bbox(tmp_path: Path) -> None:
    path = fixture(tmp_path, "precip", "mm/month")
    with (
        pytest.raises(RetrievalError, match="byte limit"),
        open_netcdf(path, maximum_uncompressed_bytes=10),
    ):
        pass
    with pytest.raises(ValueError, match="maximum_values"):
        next(gpcc_monthly([path], start_year=2025, end_year=2025, maximum_values=1))
    result = next(gpcc_monthly([path], start_year=2025, end_year=2025, bbox=(-10, 1, -10, 1)))
    assert result.item() == 0
    with pytest.raises(ValueError, match="monthly millimetres"):
        next(
            gpcc_monthly(
                [fixture(tmp_path, "precip", "kg m-2 s-1")], start_year=2025, end_year=2025
            )
        )


def test_download_stream_and_verified_reuse(tmp_path: Path) -> None:
    request = CRUTSRequest("tmp", 2021, 2025)
    calls = []
    body = b"synthetic archive bytes"

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(str(req.url))
        return httpx.Response(200, content=body)

    config = HTTPConfig(attempts=1, minimum_interval_seconds=0)
    with HTTPClient(CRU_TS_HOSTS, config=config, transport=httpx.MockTransport(handler)) as http:
        client = CRUTSClient(http)
        records = client.download(request, tmp_path)
        assert records[0].size_bytes == len(body)
        assert client.download(request, tmp_path)[0].cache_hit
    assert calls == list(request.urls())


def test_plan_cli_has_no_network_or_files(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(
            [
                "gpcc",
                "--start-year",
                "2025",
                "--end-year",
                "2025",
                "--end-month",
                "1",
                "--plan-only",
            ]
        )
        == 0
    )
    assert "2025_01_v2025_050.nc.gz" in capsys.readouterr().out
    assert main(["cru-ts", "--start-year", "2021", "--end-year", "2025", "--plan-only"]) == 0
    assert "cru_ts4.10.2021.2025.tmp.dat.nc.gz" in capsys.readouterr().out
