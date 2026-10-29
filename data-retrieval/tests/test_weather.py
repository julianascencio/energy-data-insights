"""Synthetic hourly endpoints prove units and off-by-one interval alignment."""

from __future__ import annotations

from datetime import date

import httpx
import numpy as np
import pandas as pd
import pytest

from energy_data_retrieval.sources.earthmover_era5 import NativeERA5Client, normalize_native_arrays
from energy_data_retrieval.sources.open_meteo import (
    OpenMeteoClient,
    Site,
    WeatherProduct,
    normalize_hourly,
)
from energy_data_retrieval.sources.open_meteo.client import OPEN_METEO_HOSTS
from energy_data_retrieval.transport import (
    HTTPClient,
    HTTPConfig,
    JSONValue,
    RetrievalError,
    object_value,
)

DAY = date(2026, 10, 27)


def payload() -> dict[str, JSONValue]:
    seconds = int(pd.Timestamp("2026-10-27T00:00:00Z").timestamp())
    return {
        "latitude": -34.0,
        "longitude": -71.0,
        "utc_offset_seconds": 0,
        "hourly_units": {
            "shortwave_radiation": "W/m²",
            "temperature_2m": "°C",
            "wind_speed_10m": "m/s",
            "wind_gusts_10m": "m/s",
        },
        "hourly": {
            "time": [seconds + i * 3600 for i in range(25)],
            "shortwave_radiation": list(range(25)),
            "temperature_2m": list(range(25)),
            "wind_speed_10m": [2] * 25,
            "wind_gusts_10m": [3] * 25,
        },
    }


def test_alignment_preserves_null_and_declares_gust_product() -> None:
    source = payload()
    hourly = object_value(source["hourly"])
    hourly["temperature_2m"] = [None, *list(range(1, 25))]
    result = normalize_hourly(source, "site", DAY, DAY, product=WeatherProduct.IFS)
    assert len(result) == 24
    assert result["timestamp"].iloc[0] == pd.Timestamp("2026-10-27T00:00:00Z")
    assert result["ghi_wm2"].iloc[0] == 1
    assert pd.isna(result["temperature_c"].iloc[0])
    assert result["temperature_c"].iloc[1] == 1.5
    assert result["wind_speed_ms"].iloc[0] == 2
    assert result.attrs["gust_alignment"] == "preceding-hour maximum at end"
    era5 = normalize_hourly(source, "site", DAY, DAY, product=WeatherProduct.ERA5)
    assert era5.attrs["gust_alignment"] == "instantaneous end sample"


def test_unit_and_axis_failures() -> None:
    source = payload()
    object_value(source["hourly_units"])["wind_speed_10m"] = "km/h"
    with pytest.raises(RetrievalError, match="source unit"):
        normalize_hourly(source, "site", DAY, DAY, product=WeatherProduct.ERA5)
    source = payload()
    object_value(source["hourly"])["time"] = [0, 7200]
    with pytest.raises(RetrievalError, match="nonhourly"):
        normalize_hourly(source, "site", DAY, DAY, product=WeatherProduct.ERA5)


def test_request_is_explicit_and_bounded() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "historical-forecast-api.open-meteo.com"
        assert request.url.params["models"] == "ecmwf_ifs"
        assert request.url.params["end_date"] == "2026-10-28"
        assert request.url.params["timezone"] == "UTC"
        assert request.url.params["wind_speed_unit"] == "ms"
        assert request.url.params["cell_selection"] == "nearest"
        return httpx.Response(200, json=payload())

    with HTTPClient(
        OPEN_METEO_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        client = OpenMeteoClient(http, WeatherProduct.IFS, chunk_days=1)
        chunk = client.weather(Site("fixture", -34, -71), DAY, DAY)
        assert len(chunk.frame) == 24 and chunk.cell_latitude == -34
        with pytest.raises(ValueError, match="chunk_days"):
            client.weather(Site("fixture", -34, -71), DAY, date(2026, 10, 28))


def test_native_era5_conversion() -> None:
    result = normalize_native_arrays(
        "site",
        np.array([0, 3600, 7200]),
        t2m=np.array([273.15, 275.15, np.nan]),
        u10=np.array([3, 0, 3]),
        v10=np.array([4, 0, 4]),
        ssrd=np.array([0, 360000, 720000]),
        fg10=np.array([0, 8, 9]),
    )
    np.testing.assert_allclose(result["ghi_wm2"], [100, 200])
    np.testing.assert_allclose(result["wind_speed_ms"], [2.5, 2.5])
    assert result["temperature_c"].iloc[0] == pytest.approx(1)
    assert pd.isna(result["temperature_c"].iloc[1])
    assert result["gust_ms"].iloc[0] == 8


def test_native_optional_dependencies_fail_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(_: str) -> object:
        raise ModuleNotFoundError

    monkeypatch.setattr(
        "energy_data_retrieval.sources.earthmover_era5.client.importlib.import_module", missing
    )
    with pytest.raises(ImportError, match="era5-native"):
        list(NativeERA5Client().iter_weather([Site("site", -34, -71)], DAY, DAY))


def test_optional_degradation_fields_align_endpoints_and_radiation() -> None:
    source = payload()
    units = object_value(source["hourly_units"])
    units.update(relative_humidity_2m="%", terrestrial_radiation="W/m²")
    hourly = object_value(source["hourly"])
    hourly["relative_humidity_2m"] = [None, *list(range(1, 25))]
    hourly["terrestrial_radiation"] = list(range(25))

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["models"] == "era5"
        assert "relative_humidity_2m" in request.url.params["hourly"]
        assert "terrestrial_radiation" in request.url.params["hourly"]
        return httpx.Response(200, json=source)

    with HTTPClient(OPEN_METEO_HOSTS, transport=httpx.MockTransport(handler)) as http:
        result = (
            OpenMeteoClient(http, include_degradation=True)
            .weather(Site("fixture", -34, -71), DAY, DAY)
            .frame
        )
    assert pd.isna(result.relative_humidity_percent.iloc[0])
    assert result.relative_humidity_percent.iloc[1] == 1.5
    assert result.toa_wm2.iloc[0] == 1
    assert result.toa_wm2.iloc[-1] == 24
    units["relative_humidity_2m"] = "fraction"
    with pytest.raises(RetrievalError, match="relative_humidity_2m"):
        normalize_hourly(
            source, "fixture", DAY, DAY, product=WeatherProduct.ERA5, include_degradation=True
        )
