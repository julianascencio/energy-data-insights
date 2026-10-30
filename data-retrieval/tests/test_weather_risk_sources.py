"""Offline source contracts: exact dates, physical units and explicit products."""

from datetime import date

import httpx
import numpy as np
import pandas as pd
import pytest

from energy_data_retrieval.sources.nasa_power import NASAPowerClient
from energy_data_retrieval.sources.open_meteo import Site
from energy_data_retrieval.sources.open_meteo.snow import OpenMeteoSnowClient
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

SITE = Site("test", 47.5, 12.5)
START, END = date(2023, 1, 1), date(2023, 1, 2)


def client(payload, assertions):
    def handler(request):
        assertions(request)
        return httpx.Response(200, json=payload)

    return HTTPClient(
        allowed_hosts=frozenset({"power.larc.nasa.gov", "archive-api.open-meteo.com"}),
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(attempts=1, minimum_interval_seconds=0),
    )


def nasa_payload():
    return {
        "header": {"fill_value": -999, "time_standard": "UTC", "sources": ["SYN1DEG"]},
        "parameters": {"AOD_55": {"units": "dimensionless"}},
        "properties": {"parameter": {"AOD_55": {"20230101": 0.2, "20230102": -999}}},
    }


def test_nasa_explicit_utc_wavelength_and_missing_data():
    def check(request):
        assert request.url.params["time-standard"] == "UTC"
        assert request.url.params["parameters"] == "AOD_55"
        assert request.url.params["start"] == "20230101"
        assert request.url.params["end"] == "20230102"

    with client(nasa_payload(), check) as http:
        result = NASAPowerClient(http).daily_aod(SITE, START, END)
    np.testing.assert_allclose(result.frame.aod550, [0.2, np.nan])
    assert str(result.frame.timestamp.dt.tz) == "UTC"
    assert result.request.sha256


@pytest.mark.parametrize("bad", ["missing_date", "units", "clock", "negative"])
def test_nasa_rejects_bad_response(bad):
    payload = nasa_payload()
    if bad == "missing_date":
        del payload["properties"]["parameter"]["AOD_55"]["20230102"]
    if bad == "units":
        payload["parameters"]["AOD_55"]["units"] = "%"
    if bad == "clock":
        payload["header"]["time_standard"] = "LST"
    if bad == "negative":
        payload["properties"]["parameter"]["AOD_55"]["20230101"] = -1
    with client(payload, lambda request: None) as http, pytest.raises(RetrievalError):
        NASAPowerClient(http).daily_aod(SITE, START, END)


def snow_payload():
    times = pd.date_range("2023-01-01", periods=48, freq="h", tz="UTC").as_unit("s")
    return {
        "latitude": 47.5,
        "longitude": 12.5,
        "utc_offset_seconds": 0,
        "hourly_units": {"time": "unixtime", "snow_depth": "m"},
        "hourly": {
            "time": times.to_numpy(dtype="int64").tolist(),
            "snow_depth": [0.2] * 47 + [None],
        },
    }


def test_snow_metres_to_cm_instantaneous_hours_and_explicit_model():
    def check(request):
        assert request.url.params["models"] == "era5_land"
        assert request.url.params["end_date"] == "2023-01-02"  # No extra day/end shift.
        assert request.url.params["elevation"] == "nan"

    with client(snow_payload(), check) as http:
        result = OpenMeteoSnowClient(http).hourly_depth(SITE, START, END)
    assert len(result.frame) == 48 and result.frame.snow_depth_cm.iloc[0] == 20
    assert np.isnan(result.frame.snow_depth_cm.iloc[-1])
    assert result.frame.timestamp.iloc[0] == pd.Timestamp("2023-01-01", tz="UTC")


@pytest.mark.parametrize("bad", ["duplicate", "units", "negative", "length"])
def test_snow_rejects_bad_response(bad):
    payload = snow_payload()
    if bad == "duplicate":
        payload["hourly"]["time"][1] = payload["hourly"]["time"][0]
    if bad == "units":
        payload["hourly_units"]["snow_depth"] = "m of water equivalent"
    if bad == "negative":
        payload["hourly"]["snow_depth"][0] = -0.1
    if bad == "length":
        payload["hourly"]["snow_depth"].pop()
    with client(payload, lambda request: None) as http, pytest.raises(RetrievalError):
        OpenMeteoSnowClient(http).hourly_depth(SITE, START, END)


def test_bounded_date_ranges_before_network():
    with client({}, lambda request: pytest.fail("No network expected")) as http:
        for source, method in (
            (NASAPowerClient(http), "daily_aod"),
            (OpenMeteoSnowClient(http), "hourly_depth"),
        ):
            with pytest.raises(ValueError):
                getattr(source, method)(SITE, date(2020, 1, 1), date(2021, 1, 1))
            with pytest.raises(ValueError):
                getattr(source, method)(SITE, END, START)
