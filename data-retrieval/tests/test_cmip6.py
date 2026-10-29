"""Synthetic STAC and native-file fixtures; no live discovery or credentials."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import httpx
import pytest

from energy_data_retrieval.sources.cmip6 import (
    CMIP6_DATA_HOSTS,
    CMIP6_INDEX_HOSTS,
    CMIP6Client,
    CMIP6Plan,
    CMIP6Query,
    download_plan,
    load_plan,
    save_plan,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

NATIVE_BYTES = b"CDF\x01synthetic native file bytes\x00\x01"
SHA256 = hashlib.sha256(NATIVE_BYTES).hexdigest()
QUERY = CMIP6Query("CanESM5", "historical", "r1i1p1f1", "Amon", "rsds", "gn")


def item(
    *,
    ranges: tuple[str, ...] = ("198001-199912", "200001-201412"),
    institution: str = "CCCma",
    version: str = "20190429",
) -> dict[str, JSONValue]:
    identifier = f"CMIP6.CMIP.{institution}.CanESM5.historical.r1i1p1f1.Amon.rsds.gn.v{version}"
    assets: dict[str, JSONValue] = {}
    for period in ranges:
        name = f"rsds_Amon_CanESM5_historical_r1i1p1f1_gn_{period}.nc"
        assets[name] = {
            "href": f"https://esgf-node.ornl.gov/thredds/fileServer/fixture/{name}",
            "description": "HTTPServer Link",
            "type": "application/netcdf",
            "roles": ["data"],
            "file:size": len(NATIVE_BYTES),
            "file:checksum": "1220" + SHA256,
        }
    return {
        "type": "Feature",
        "id": identifier,
        "collection": "CMIP6",
        "properties": {
            "cmip6:activity_id": ["CMIP"],
            "cmip6:institution_id": institution,
            "cmip6:source_id": "CanESM5",
            "cmip6:experiment_id": "historical",
            "cmip6:member_id": "r1i1p1f1",
            "cmip6:variant_label": "r1i1p1f1",
            "cmip6:sub_experiment_id": "none",
            "cmip6:table_id": "Amon",
            "cmip6:variable_id": "rsds",
            "cmip6:grid_label": "gn",
            "cmip6:mip_era": "CMIP6",
            "cmip6:variable_units": "W m-2",
            "cmip6:pid": "hdl:synthetic/example",
            "license": "CC-BY-4.0",
            "version": version,
            "latest": True,
            "retracted": False,
        },
        "links": [{"rel": "cite-as", "href": "https://fixture.example/citation"}],
        "assets": assets,
    }


def props(feature: dict[str, JSONValue]) -> dict[str, JSONValue]:
    return cast(dict[str, JSONValue], feature["properties"])


def first_asset(feature: dict[str, JSONValue]) -> dict[str, JSONValue]:
    return next(iter(cast(dict[str, dict[str, JSONValue]], feature["assets"]).values()))


def response_page(
    features: list[dict[str, JSONValue]],
    *,
    links: list[dict[str, object]] | None = None,
    total: int | None = None,
) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": features,
        "numberReturned": len(features),
        "numberMatched": len(features) if total is None else total,
        "links": links or [],
    }


def discover(
    features: list[dict[str, JSONValue]] | None = None,
    query: CMIP6Query = QUERY,
    *,
    maximum_datasets: int = 100,
    maximum_files: int = 1000,
) -> CMIP6Plan:
    items = [item()] if features is None else features

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/collections":
            return httpx.Response(200, json={"collections": [{"id": "CMIP7"}, {"id": "CMIP6"}]})
        return httpx.Response(200, json=response_page(items))

    with HTTPClient(
        CMIP6_INDEX_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        return CMIP6Client(
            http, maximum_datasets=maximum_datasets, maximum_files=maximum_files
        ).search(query)


def test_exact_query_and_current_collection_case_with_whole_file_years() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.url.host == "discovery.west.esgf.io"
        if request.url.path == "/collections":
            return httpx.Response(200, json={"collections": [{"id": "CMIP7"}, {"id": "cmip6"}]})
        assert request.url.params["collections"] == "cmip6"
        assert request.url.params["filter-lang"] == "cql2-json"
        filters = json.loads(request.url.params["filter"])["args"]
        values = {clause["args"][0]["property"]: clause["args"][1] for clause in filters}
        assert values["cmip6:source_id"] == "CanESM5"
        assert values["cmip6:member_id"] == "r1i1p1f1"
        assert values["latest"] is True and values["retracted"] is False
        assert "datetime" not in request.url.params
        return httpx.Response(200, json=response_page([item()]))

    with HTTPClient(
        CMIP6_INDEX_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        plan = CMIP6Client(http, index="west").search(
            replace(QUERY, start_year=2005, end_year=2006)
        )
    assert len(seen) == 2 and len(plan.files) == 1
    assert plan.files[0].start_label == "200001" and plan.files[0].end_label == "201412"
    assert plan.collection == "cmip6"
    assert props(plan.datasets[0])["license"] == "CC-BY-4.0"
    assert plan.datasets[0]["links"] == item()["links"]
    assert plan.as_dict()["global_coverage_claimed"] is False


def test_pagination_keeps_filters_and_accepts_empty_terminal_page() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        if request.url.path == "/collections":
            return httpx.Response(200, json={"collections": [{"id": "CMIP6"}]})
        calls += 1
        if calls == 1:
            link = str(request.url.copy_set_param("token", "second"))
            return httpx.Response(
                200, json=response_page([item()], total=1, links=[{"rel": "next", "href": link}])
            )
        assert request.url.params["token"] == "second"
        assert "filter" in request.url.params
        return httpx.Response(200, json=response_page([], total=1))

    with HTTPClient(
        CMIP6_INDEX_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        plan = CMIP6Client(http).search(QUERY)
    assert calls == 2 and len(plan.requests) == 3


@pytest.mark.parametrize(
    "change", ["external", "filter", "post", "cycle", "truncated", "count-drift", "duplicate"]
)
def test_bad_pagination_never_produces_complete_plan(change: str) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        if request.url.path == "/collections":
            return httpx.Response(200, json={"collections": [{"id": "CMIP6"}]})
        calls += 1
        link: dict[str, object] = {
            "rel": "next",
            "href": str(request.url.copy_set_param("token", "next")),
        }
        if change == "external":
            link["href"] = "https://unapproved.example/search?token=next"
        if change == "filter":
            link["href"] = str(
                request.url.copy_set_param("collections", "CMIP7").copy_set_param("token", "next")
            )
        if change == "post":
            link["method"] = "POST"
        if change == "truncated":
            return httpx.Response(200, json=response_page([item()], total=2))
        if calls == 1:
            return httpx.Response(200, json=response_page([item()], total=2, links=[link]))
        if change == "count-drift":
            return httpx.Response(200, json=response_page([item(institution="Other")], total=3))
        if change == "duplicate":
            return httpx.Response(200, json=response_page([item()], total=2))
        return httpx.Response(
            200, json=response_page([item(institution="Other")], total=2, links=[link])
        )

    with (
        HTTPClient(
            CMIP6_INDEX_HOSTS,
            transport=httpx.MockTransport(handler),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError, match=r"pagination|catalogue|endpoint|filters|cyclic"),
    ):
        CMIP6Client(http, page_size=1).search(QUERY)
    assert calls <= 2


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cmip6:source_id", "Wrong-Model"),
        ("cmip6:member_id", "s2000-r1i1p1f1"),
        ("cmip6:sub_experiment_id", "s2000"),
        ("version", "20200101"),
        ("latest", False),
        ("retracted", True),
    ],
)
def test_inconsistent_dataset_facets_are_rejected(field: str, value: JSONValue) -> None:
    feature = item()
    props(feature)[field] = value
    with pytest.raises(RetrievalError):
        discover([feature])


def test_explicit_version_can_retrieve_old_version_but_cannot_drift() -> None:
    feature = item()
    props(feature)["latest"] = False
    plan = discover([feature], replace(QUERY, version="v20190429"))
    assert plan.query.version == "20190429"
    assert plan.files[0].dataset_id.endswith("v20190429")
    with pytest.raises(RetrievalError, match="different version"):
        discover([feature], replace(QUERY, version="20200101"))
    with pytest.raises(RetrievalError, match="ambiguous versions"):
        discover([item(), item(version="20200101")])


@pytest.mark.parametrize(
    "settings",
    [
        {"source_id": "*"},
        {"member_id": "r1i1p1f1,r2i1p1f1"},
        {"start_year": 2000},
        {"start_year": 2005, "end_year": 2000},
        {"start_year": True, "end_year": 2000},
        {"version": "latest"},
    ],
)
def test_queries_are_explicit_and_validated(settings: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        replace(QUERY, **settings)


def test_calendar_labels_are_not_forced_into_gregorian_dates() -> None:
    plan = discover(
        [item(ranges=("20000230-20000330",))], replace(QUERY, start_year=2000, end_year=2000)
    )
    assert plan.files[0].start_label == "20000230"
    with pytest.raises(RetrievalError, match="invalid calendar"):
        discover([item(ranges=("20001301-20011301",))])
    with pytest.raises(RetrievalError, match="overlap"):
        discover(query=replace(QUERY, start_year=2050, end_year=2060))


def test_fixed_fields_have_no_time_selection() -> None:
    feature = item(ranges=("200001-201412",))
    feature["id"] = str(feature["id"]).replace(".Amon.rsds.", ".fx.areacella.")
    props(feature)["cmip6:table_id"] = "fx"
    props(feature)["cmip6:variable_id"] = "areacella"
    asset = first_asset(feature)
    filename = "areacella_fx_CanESM5_historical_r1i1p1f1_gn.nc"
    asset["href"] = "https://esgf-node.ornl.gov/files/" + filename
    feature["assets"] = {filename: asset}
    query = replace(QUERY, table_id="fx", variable_id="areacella")
    plan = discover([feature], query)
    assert plan.files[0].start_label is None and plan.files[0].end_label is None
    with pytest.raises(RetrievalError, match="year selection"):
        discover([feature], replace(query, start_year=2000, end_year=2001))


@pytest.mark.parametrize(
    "change",
    ["raw-sha256", "other-multihash", "http", "query", "traversal", "wrong-name", "zero-size"],
)
def test_unsafe_or_unverifiable_assets_are_rejected(change: str) -> None:
    feature = item()
    asset = first_asset(feature)
    url = str(asset["href"])
    if change == "raw-sha256":
        asset["file:checksum"] = SHA256
    elif change == "other-multihash":
        asset["file:checksum"] = "1114" + "0" * 40
    elif change == "http":
        asset["href"] = url.replace("https://", "http://")
    elif change == "query":
        asset["href"] = url + "?token=private"
    elif change == "traversal":
        asset["href"] = url.replace("/fixture/", "/%2e%2e/")
    elif change == "wrong-name":
        asset["href"] = url + "other.nc"
    else:
        asset["file:size"] = 0
    with pytest.raises((RetrievalError, ValueError)):
        discover([feature])


def test_resource_caps_reject_incomplete_searches() -> None:
    with pytest.raises(RetrievalError, match="maximum_datasets"):
        discover([item(), item(institution="Other")], maximum_datasets=1)
    with pytest.raises(RetrievalError, match="file limit"):
        discover(maximum_files=1)
    with pytest.raises(RetrievalError, match="No matching"):
        discover([])


def test_plan_roundtrip_rejects_tampered_content_and_derived_paths(tmp_path: Path) -> None:
    plan = discover()
    path = tmp_path / "plan.json"
    save_plan(plan, path)
    assert load_plan(path).as_dict() == plan.as_dict()
    with pytest.raises(ValueError, match="already exists"):
        save_plan(plan, path)
    saved = json.loads(path.read_bytes())
    saved["files"][0]["relative_path"] = "../../outside.nc"
    path.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="fingerprint"):
        load_plan(path)
    payload = {key: value for key, value in saved.items() if key != "plan_sha256"}
    saved["plan_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()
    path.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="inconsistent"):
        load_plan(path)


def test_download_checksum_native_bytes_and_restart(tmp_path: Path) -> None:
    plan = discover()
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=NATIVE_BYTES)

    with HTTPClient(
        CMIP6_DATA_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        first = download_plan(plan, tmp_path / "run", http)
        manifest_before = (tmp_path / "run/manifest.json").read_bytes()
        second = download_plan(plan, tmp_path / "run", http)
        assert first["reused_files"] == 0 and second["reused_files"] == 2 and calls == 2
        assert (tmp_path / "run/manifest.json").read_bytes() == manifest_before
        for file in plan.files:
            path = tmp_path / "run" / file.relative_path
            assert path.read_bytes() == NATIVE_BYTES
            assert all(part == part.lower() for part in Path(file.relative_path).parts[:-1])
        path.write_bytes(b"tampered")
        with pytest.raises(ValueError, match="checkpoint"):
            download_plan(plan, tmp_path / "run", http)
        assert calls == 2


def test_download_preflight_bounds_and_hosts_make_no_requests(tmp_path: Path) -> None:
    plan = discover()

    def forbidden(_: httpx.Request) -> httpx.Response:
        pytest.fail("Preflight failures must not access the network")

    with (
        HTTPClient(CMIP6_DATA_HOSTS, transport=httpx.MockTransport(forbidden)) as http,
        pytest.raises(ValueError, match="maximum_total_bytes"),
    ):
        download_plan(plan, tmp_path / "total", http, maximum_total_bytes=1)
    with (
        HTTPClient(
            frozenset({"different.example"}), transport=httpx.MockTransport(forbidden)
        ) as http,
        pytest.raises(ValueError, match="not approved"),
    ):
        download_plan(plan, tmp_path / "host", http)
    with (
        HTTPClient(
            CMIP6_DATA_HOSTS,
            transport=httpx.MockTransport(forbidden),
            config=HTTPConfig(maximum_response_bytes=1),
        ) as http,
        pytest.raises(ValueError, match="per-file"),
    ):
        download_plan(plan, tmp_path / "size", http)
    assert list(tmp_path.iterdir()) == []


def test_partial_download_resumes_only_missing_files(tmp_path: Path) -> None:
    plan = discover()
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503) if calls == 2 else httpx.Response(200, content=NATIVE_BYTES)

    with HTTPClient(
        CMIP6_DATA_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0, attempts=1),
    ) as http:
        with pytest.raises(RetrievalError, match="HTTP 503"):
            download_plan(plan, tmp_path / "run", http)
        assert (tmp_path / "run/plan.json").exists()
        assert not (tmp_path / "run/manifest.json").exists()
        result = download_plan(plan, tmp_path / "run", http)
    assert calls == 3 and result["file_count"] == 2 and result["reused_files"] == 1


def test_wrong_download_bytes_are_never_published(tmp_path: Path) -> None:
    plan = discover([item(ranges=("200001-201412",))])
    with (
        HTTPClient(
            CMIP6_DATA_HOSTS,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, content=b"X" * len(NATIVE_BYTES))
            ),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError, match="SHA-256"),
    ):
        download_plan(plan, tmp_path / "run", http)
    assert not (tmp_path / "run" / plan.files[0].relative_path).exists()
    assert not (tmp_path / "run/manifest.json").exists()


def test_changed_plan_or_symlink_output_is_not_reused(tmp_path: Path) -> None:
    plan = discover()
    with HTTPClient(
        CMIP6_DATA_HOSTS,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=NATIVE_BYTES)),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        download_plan(plan, tmp_path / "run", http)
        with pytest.raises(ValueError, match="different or changed"):
            download_plan(
                discover(query=replace(QUERY, start_year=2000, end_year=2014)),
                tmp_path / "run",
                http,
            )
        (tmp_path / "linked").symlink_to(tmp_path / "run", target_is_directory=True)
        with pytest.raises(ValueError, match="symlink"):
            download_plan(plan, tmp_path / "linked", http)
