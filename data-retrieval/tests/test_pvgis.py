"""Offline wire-contract tests; mock responses are synthetic, never observations."""

from __future__ import annotations

import hashlib
import json
from email import policy
from email.parser import BytesParser
from typing import Any

import httpx
import pytest

from energy_data_retrieval.sources.pvgis import (
    PVGIS_HOSTS,
    PVGIS6Client,
    PVGISClient,
    describe_endpoint,
    endpoints,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError, object_value

V6_PATHS = (
    "/coverage/map",
    "/coverage/layers",
    "/coverage/layers/{name}",
    "/coverage/location-within-selected-source",
    "/coverage/available-sources-in-selected-location",
    "/performance/broadband",
    "/performance/broadband-multiple-surfaces",
    "/power/broadband",
    "/power/broadband-multiple-surfaces",
    "/power/surface/optimisation",
    "/reference/citation",
    "/reference/publications",
    "/reference/conventions-in-pvgis",
    "/reference/license",
    "/solar-position/overview",
    "/features",
    "/topography/horizon-profile",
    "/topography/elevation",
    "/meteorological/typical-meteorological-year",
    "/meteorological/degree-days",
)
POST_PATHS = (
    "/performance/broadband",
    "/performance/broadband-multiple-surfaces",
    "/power/broadband",
    "/power/broadband-multiple-surfaces",
    "/power/surface/optimisation",
    "/solar-position/overview",
    "/topography/horizon-profile",
)


def transport(handler, **config):
    return HTTPClient(
        PVGIS_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0, **config),
        sleep=lambda _: None,
    )


@pytest.mark.parametrize("version", ["5.2", "5.3"])
@pytest.mark.parametrize(
    ("endpoint", "parameters"),
    [
        ("PVcalc", {"peakpower": 1, "loss": 14, "pvprice": 1, "systemcost": 1500, "interest": 4}),
        (
            "SHScalc",
            {
                "peakpower": 1000,
                "batterysize": 2000,
                "cutoff": 20,
                "consumptionday": 3000,
                "hourconsumption": [1 / 24] * 24,
            },
        ),
        ("MRcalc", {"horirrad": True, "avtemp": 1}),
        ("DRcalc", {"month": 0, "global": True, "localtime": False}),
        ("seriescalc", {"pvcalculation": 1, "peakpower": 1, "loss": 0, "trackingtype": 5}),
        ("tmy", {"startyear": 2010, "endyear": 2020}),
        ("printhorizon", {"userhorizon": [0, 10, 20, 0]}),
    ],
)
def test_every_legacy_endpoint_and_version(version, endpoint, parameters):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "inputs": {"location": {"latitude": 28}},
                "outputs": {"hourly": [{"P": 0}, {"P": None}]},
                "meta": {"P": {"units": "W"}},
            },
        )

    with transport(handler) as http:
        result = PVGISClient(http, version).request(endpoint, lat=28, lon=-16, **parameters)
    request = seen[0]
    assert request.url.path == f"/api/v{version.replace('.', '_')}/{endpoint}"
    assert request.method == "GET"
    assert request.url.params["outputformat"] == "json"
    assert request.url.params["lat"] == "28"
    assert object_value(object_value(object_value(result.json())["meta"])["P"])["units"] == "W"
    assert result.table("outputs", "hourly")["P"].iloc[0] == 0
    assert result.table("outputs", "hourly")["P"].isna().sum() == 1
    if endpoint == "SHScalc":
        assert request.url.params["peakpower"] == "1000"  # W, never divided by 1000.
        assert len(request.url.params["hourconsumption"].split(",")) == 24


@pytest.mark.parametrize("path", V6_PATHS)
def test_all_v6_get_paths(path):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"synthetic": True})

    params: dict[str, Any] = (
        {"latitude": 28, "longitude": -16}
        if "latitude" in describe_endpoint(path)["parameters"]
        else {}
    )
    if path == "/coverage/layers/{name}":
        params["name"] = "sarah3_coverage_layer"
    with transport(handler) as http:
        result = PVGIS6Client(http).request(path, parameters=params)
    assert seen[0].method == "GET"
    assert seen[0].url.path == "/api/v6" + path.replace("{name}", "sarah3_coverage_layer")
    assert not seen[0].content
    assert result.version == "6"
    assert result.request.parameters["method"] == "GET"
    assert "name" not in seen[0].url.params


@pytest.mark.parametrize("path", POST_PATHS)
def test_all_v6_multipart_operations_put_parameters_in_body(path, tmp_path):
    horizon = tmp_path / "profile.json"
    horizon.write_text('{"horizon_height": [0, 10, 20, 0], "units": "degrees"}')
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"synthetic": True})

    params = {"latitude": 28, "longitude": -16, "angle_output_units": "Degrees"}
    if path == "/solar-position/overview":
        params["solar_position_models"] = ["NOAA", "pvlib"]
    with transport(handler) as http:
        result = PVGIS6Client(http).request(path, horizon_file=horizon, parameters=params)
    r = seen[0]
    assert r.method == "POST" and not r.url.query
    message = BytesParser(policy=policy.default).parsebytes(
        ("Content-Type: " + r.headers["content-type"] + "\r\n\r\n").encode() + r.content
    )
    values = {}
    for part in message.iter_parts():
        values.setdefault(part.get_param("name", header="content-disposition"), []).append(
            part.get_payload(decode=True)
        )
    assert values["latitude"] == [b"28"] and values["longitude"] == [b"-16"]
    assert values["horizon_profile"] == [horizon.read_bytes()]
    if path == "/solar-position/overview":
        assert values["solar_position_models"] == [b"NOAA", b"pvlib"]
    assert (
        result.request.parameters["file:horizon_profile:sha256"]
        == hashlib.sha256(horizon.read_bytes()).hexdigest()
    )


def test_v6_repeated_query_alias_and_boolean():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={})

    with transport(handler) as http:
        c = PVGIS6Client(http)
        c.solar_position(
            28, -16, solar_position_models=["NOAA", "pvlib"], apply_atmospheric_refraction=False
        )
        c.power(28, -16, **{"peak-power": 2})
    assert seen[0].url.params.get_list("solar_position_models") == ["NOAA", "pvlib"]
    assert seen[0].url.params["apply_atmospheric_refraction"] == "false"
    assert seen[1].url.params["peak-power"] == "2"


@pytest.mark.parametrize(
    ("endpoint", "parameters"),
    [
        ("PVcalc", {"peakpower": 1}),
        ("SHScalc", {"peakpower": 1}),
        ("MRcalc", {}),
        ("DRcalc", {"month": 13, "global": 1}),
        ("seriescalc", {"pvcalculation": True}),
        ("tmy", {"startyear": 2020, "endyear": 2021}),
        ("printhorizon", {"userhorizon": [0, 100, 0, 0]}),
        ("printhorizon", {"userhorizon": "0,no,0,0"}),
        ("seriescalc", {"startyear": 2021, "endyear": 2020}),
        ("PVcalc", {"peakpower": 1, "loss": float("nan")}),
        (
            "SHScalc",
            {
                "peakpower": 1000,
                "batterysize": 2000,
                "cutoff": 20,
                "consumptionday": 3000,
                "hourconsumption": [1] * 24,
            },
        ),
    ],
)
def test_invalid_legacy_never_networks(endpoint, parameters):
    def forbidden(_):
        raise AssertionError("Invalid inputs reached the network")

    with transport(forbidden) as http, pytest.raises(ValueError):
        PVGISClient(http).request(endpoint, lat=28, lon=-16, **parameters)


@pytest.mark.parametrize(
    "parameters",
    [
        {"latitude": 91, "longitude": -16},
        {"latitude": True, "longitude": -16},
        {"latitude": float("inf"), "longitude": -16},
        {"latitude": 28},
        {"latitude": 28, "longitude": -16, "typo": 0},
        {"latitude": 28, "longitude": -16, "irradiance_source": "NOT-A-SOURCE"},
        {"latitude": 28, "longitude": -16, "start_time": "tomorrow"},
        {"latitude": 28, "longitude": -16, "start_time": "2020-02-02", "end_time": "2020-01-01"},
        {"latitude": 28, "longitude": -16, "periods": 0},
        {"latitude": 28, "longitude": -16, "surface_tilt": -5},
    ],
)
def test_invalid_v6_never_networks(parameters):
    def forbidden(_):
        raise AssertionError("Invalid inputs reached the network")

    with transport(forbidden) as http, pytest.raises(ValueError):
        PVGIS6Client(http).request("/power/broadband", **parameters)


@pytest.mark.parametrize(
    ("body", "media"),
    [
        (b"a,b\n0,1\n", "text/csv"),
        (b"LOCATION,example\n", "text/plain"),
        (b"\x89PNG\r\n\x00", "image/png"),
        (b"PK\x03\x04\x00", "application/zip"),
        (b"@misc{example}", "application/x-bibtex"),
        (b"<html>coverage</html>", "text/html"),
    ],
)
def test_native_formats_saved_exactly(body, media, tmp_path):
    with transport(
        lambda _: httpx.Response(
            200, content=body, headers={"Content-Type": media, "X-Request-ID": "abc"}
        )
    ) as http:
        result = PVGIS6Client(http).features()
    result.save(tmp_path / "native.dat")
    assert (tmp_path / "native.dat").read_bytes() == body
    manifest = json.loads((tmp_path / "native.dat.provenance.json").read_text())
    assert manifest["content_type"] == media
    assert manifest["request_id"] == "abc"
    assert manifest["request"]["sha256"] == hashlib.sha256(body).hexdigest()
    with pytest.raises(RetrievalError):
        result.json()


def test_v6_operation_inventory_and_contract_copy():
    assert set(endpoints()) == {f"GET {p}" for p in V6_PATHS} | {f"POST {p}" for p in POST_PATHS}
    assert len(endpoints("5.3")) == 7
    a = describe_endpoint("/topography/elevation")
    a["parameters"].clear()
    assert "latitude" in describe_endpoint("/topography/elevation")["parameters"]
    with pytest.raises(ValueError):
        describe_endpoint("/not-a-route")
    with pytest.raises(ValueError):
        endpoints("4")


@pytest.mark.parametrize("status", [429, 500, 529])
def test_transient_statuses_retry_with_retry_after(status):
    seen = []
    waits = []

    def handler(request):
        seen.append(request)
        return (
            httpx.Response(status, headers={"Retry-After": "2"})
            if len(seen) == 1
            else httpx.Response(200, json={})
        )

    with HTTPClient(
        PVGIS_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
        sleep=waits.append,
    ) as http:
        PVGIS6Client(http).features()
    assert len(seen) == 2 and waits == [2]


def test_response_limit_and_no_redirects():
    with (
        transport(
            lambda _: httpx.Response(200, content=b"x" * 100), maximum_response_bytes=10
        ) as http,
        pytest.raises(RetrievalError, match="byte limit"),
    ):
        PVGIS6Client(http).features()
    calls = []

    def redirect(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "https://example.com"})

    with transport(redirect) as http, pytest.raises(RetrievalError, match="302"):
        PVGIS6Client(http).features()
    assert len(calls) == 1


def test_non_retryable_errors_keep_request_identifier():
    with (
        transport(lambda _: httpx.Response(422, headers={"X-Request-ID": "request-123"})) as http,
        pytest.raises(RetrievalError, match="422; request_id=request-123"),
    ):
        PVGIS6Client(http).features()


@pytest.mark.parametrize("name", ["../other", "/power/broadband", "x?query=y", "x#y", ""])
def test_coverage_path_cannot_escape_endpoint(name):
    with transport(lambda _: pytest.fail("Unexpected request")) as http, pytest.raises(ValueError):
        PVGIS6Client(http).coverage_layer(name)


def test_malformed_json_and_nonrectangular_tables():
    with transport(lambda _: httpx.Response(200, content=b'{"x":NaN}')) as http:
        result = PVGIS6Client(http).features()
    with pytest.raises(RetrievalError):
        result.json()
    with transport(lambda _: httpx.Response(200, json={"a": [1, 2], "b": [3]})) as http:
        result = PVGIS6Client(http).features()
    with pytest.raises(RetrievalError):
        result.table()
    with pytest.raises(RetrievalError):
        result.table("missing")


@pytest.mark.parametrize(
    "content",
    [
        '{"horizon_height":[0,1]}',
        '{"horizon_height":[0,1,2,91]}',
        '{"horizon_height":[0,1,2,3],"units":"radians"}',
        '{"horizon_height":[0,1,2,3],"azimuth":[0,90]}',
        '{"horizon_height":[0,1,NaN,3]}',
    ],
)
def test_bad_horizon_file_rejected(content, tmp_path):
    file = tmp_path / "horizon.json"
    file.write_text(content)
    with transport(lambda _: pytest.fail("Unexpected request")) as http, pytest.raises(ValueError):
        PVGIS6Client(http).horizon(28, -16, horizon_file=file)


def test_saved_response_integrity_and_column_selection(tmp_path):
    from energy_data_retrieval.sources.pvgis import load_response

    with transport(
        lambda _: httpx.Response(
            200,
            json={
                "timestamps": ["2020-01-01 00:09", "2020-01-01 01:09"],
                "power": [0, None],
                "technology": "synthetic",
            },
        )
    ) as http:
        result = PVGIS6Client(http).features()
    path = tmp_path / "result.json"
    result.save(path)
    restored = load_response(path)
    frame = restored.table(columns=("timestamps", "power"))
    assert frame["timestamps"].iloc[0].endswith("00:09")
    assert frame["power"].iloc[0] == 0 and frame["power"].isna().sum() == 1
    assert restored.json() == result.json()
    path.write_bytes(b"{}")
    with pytest.raises(ValueError, match="checksum"):
        load_response(path)


@pytest.mark.parametrize(
    "parameters",
    [
        {"surface_tilt": [25, 25], "surface_orientation": [90, 270]},
        {"surface_tilt": [25, 25], "surface_orientation": [90, 270], "peak-power": [1]},
        {"surface_tilt": [181], "surface_orientation": [90], "peak-power": [1]},
        {"surface_tilt": [25], "surface_orientation": [90], "peak-power": [-1]},
    ],
)
def test_correlated_multi_surface_inputs_fail_before_network(parameters):
    with transport(lambda _: pytest.fail("Unexpected request")) as http, pytest.raises(ValueError):
        PVGIS6Client(http).request(
            "/power/broadband-multiple-surfaces", latitude=28, longitude=-16, parameters=parameters
        )


def test_native_csv_and_epw_legacy_output_selection():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(
            200, text="Native provider text\n", headers={"Content-Type": "text/plain"}
        )

    with transport(handler) as http:
        assert (
            PVGISClient(http).typical_year(28, -16, outputformat="epw").text().startswith("Native")
        )
        PVGISClient(http).horizon(28, -16, outputformat="basic")
    assert [r.url.params["outputformat"] for r in seen] == ["epw", "basic"]


def test_public_binary_transport_rejects_secrets_and_unsafe_urls():
    with transport(lambda _: pytest.fail("Unexpected request")) as http:
        for endpoint in [
            "http://re.jrc.ec.europa.eu/api",
            "https://example.com/api",
            "https://re.jrc.ec.europa.eu/api?x=1",
        ]:
            with pytest.raises(ValueError):
                http.request_bytes(endpoint)
        with pytest.raises(ValueError):
            http.request_bytes("https://re.jrc.ec.europa.eu/api", {"api_key": "example"})


def test_packaged_gallery_captures_are_complete_and_verified():
    from pathlib import Path

    from energy_data_retrieval.sources.pvgis import load_response

    root = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    captures = sorted(root.glob("pvgis_v*.json"))
    captures = [p for p in captures if not p.name.endswith(".provenance.json")]
    assert len(captures) == 12
    for path in captures:
        response = load_response(path)
        assert isinstance(response.json(), dict)
    assert len(load_response(root / "pvgis_v5_hourly.json").table("outputs", "hourly")) == 8784
    assert len(load_response(root / "pvgis_v5_tmy.json").table("outputs", "tmy_hourly")) == 8760
