"""Offline CLI workflows preserve versioned native climate files and explicit limits."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from energy_data_retrieval import cli
from energy_data_retrieval.sources.cmip6 import load_plan
from energy_data_retrieval.transport import HTTPClient, HTTPConfig

BODY = b"synthetic opaque NetCDF payload; calendar=360_day; units=W m-2"
DATASET = "CMIP6.CMIP.CCCma.CanESM5.historical.r1i1p1f1.Amon.rsds.gn.v20190429"
FILENAME = "rsds_Amon_CanESM5_historical_r1i1p1f1_gn_200001-201412.nc"


def _feature(host: str = "esgf-node.ornl.gov") -> dict[str, object]:
    properties: dict[str, object] = {
        "version": "20190429",
        "latest": True,
        "retracted": False,
        "base_id": DATASET.rsplit(".", 1)[0],
        "start_datetime": "1980-01-16T12:00:00Z",
        "end_datetime": "2014-12-16T12:00:00Z",
        "datetime": None,
        "cmip6:mip_era": "CMIP6",
        "cmip6:activity_id": ["CMIP"],
        "cmip6:institution_id": "CCCma",
        "cmip6:source_id": "CanESM5",
        "cmip6:experiment_id": "historical",
        "cmip6:member_id": "r1i1p1f1",
        "cmip6:variant_label": "r1i1p1f1",
        "cmip6:sub_experiment_id": "none",
        "cmip6:table_id": "Amon",
        "cmip6:variable_id": "rsds",
        "cmip6:grid_label": "gn",
        "cmip6:frequency": "mon",
        "cmip6:variable_units": "W m-2",
        "cmip6:pid": "hdl:21.14100/synthetic-dataset",
        "license": "CC0-1.0",
    }
    assets = {}
    for filename in (FILENAME.replace("200001-201412", "198001-199912"), FILENAME):
        assets[filename] = {
            "href": f"https://{host}/thredds/fileServer/cmip6/{filename}",
            "type": "application/netcdf",
            "description": "HTTPServer Link",
            "roles": ["data"],
            "file:size": len(BODY),
            "file:checksum": "1220" + hashlib.sha256(BODY).hexdigest(),
            "file:local_path": f"CMIP6/CMIP/CCCma/CanESM5/{filename}",
        }
    return {
        "type": "Feature",
        "stac_version": "1.1.0",
        "id": DATASET,
        "collection": "CMIP6",
        "properties": properties,
        "assets": assets,
        "links": [
            {
                "rel": "cite-as",
                "href": "http://citation.example/synthetic-model-dataset.json",
            }
        ],
    }


def _search_arguments(path: Path, *extra: str) -> list[str]:
    return [
        "cmip6-search",
        "--model",
        "CanESM5",
        "--experiment",
        "historical",
        "--member",
        "r1i1p1f1",
        "--table",
        "Amon",
        "--variable",
        "rsds",
        "--grid",
        "gn",
        "--output",
        str(path),
        "--request-interval",
        "0",
        *extra,
    ]


def _mock_http(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> list[httpx.Request]:
    calls: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    def client(
        allowed_hosts: frozenset[str],
        *,
        config: HTTPConfig | None = None,
        cache_directory: Path | None = None,
    ) -> HTTPClient:
        return HTTPClient(
            allowed_hosts,
            config=config,
            cache_directory=cache_directory,
            transport=httpx.MockTransport(record),
            sleep=lambda _: None,
        )

    monkeypatch.setattr(cli, "HTTPClient", client)
    return calls


def _response(request: httpx.Request, *, host: str = "esgf-node.ornl.gov") -> httpx.Response:
    if request.url.path == "/collections":
        return httpx.Response(200, json={"collections": [{"id": "cmip6", "title": "CMIP6"}]})
    if request.url.path == "/search":
        return httpx.Response(
            200,
            json={
                "type": "FeatureCollection",
                "features": [_feature(host)],
                "links": [],
                "numberReturned": 1,
                "numberMatched": 1,
            },
        )
    assert request.url.host == host
    assert request.url.path.endswith(FILENAME)
    return httpx.Response(200, content=BODY)


def test_cli_search_download_and_verified_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls = _mock_http(monkeypatch, _response)
    path = tmp_path / "plan.json"
    assert (
        cli.main(
            _search_arguments(
                path,
                "--index",
                "west",
                "--start-year",
                "2005",
                "--end-year",
                "2006",
                "--version",
                "20190429",
                "--institution",
                "CCCma",
                "--activity",
                "CMIP",
                "--page-size",
                "2",
            )
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["files"] == 1
    assert summary["total_size_bytes"] == len(BODY)
    assert summary["downloaded"] is False
    assert summary["index"] == "west"
    plan = load_plan(path)
    assert plan.query.source_id == "CanESM5"
    assert plan.query.start_year == 2005 and plan.query.end_year == 2006
    assert plan.query.version == "20190429"
    assert all(request.url.host == "discovery.west.esgf.io" for request in calls)
    search = next(request for request in calls if request.url.path == "/search")
    assert search.url.params["collections"] == "cmip6"
    assert search.url.params["limit"] == "2"
    assert "cmip6:source_id" in search.url.params["filter"]
    assert "20190429" in search.url.params["filter"]
    assert not list(tmp_path.rglob("*.nc"))

    output = tmp_path / "download"
    arguments = [
        "cmip6-download",
        "--plan",
        str(path),
        "--output",
        str(output),
        "--maximum-file-bytes",
        str(len(BODY)),
        "--maximum-total-bytes",
        str(len(BODY)),
        "--request-interval",
        "0",
    ]
    assert cli.main(arguments) == 0
    json.loads(capsys.readouterr().out)
    files = list(output.rglob("*.nc"))
    assert len(files) == 1 and files[0].name == FILENAME
    assert files[0].read_bytes() == BODY
    assert all(part == part.lower() for part in files[0].relative_to(output).parts[:-1])
    assert not list(output.rglob("*.parquet"))
    initial_calls = len(calls)
    assert cli.main(arguments) == 0
    json.loads(capsys.readouterr().out)
    assert len(calls) == initial_calls
    assert files[0].read_bytes() == BODY


@pytest.mark.parametrize("option", ["--maximum-file-bytes", "--maximum-total-bytes"])
def test_cli_size_limit_prevents_any_file_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    option: str,
) -> None:
    calls = _mock_http(monkeypatch, _response)
    path = tmp_path / "plan.json"
    assert cli.main(_search_arguments(path, "--start-year", "2000", "--end-year", "2014")) == 0
    capsys.readouterr()
    before_download = len(calls)
    with pytest.raises(SystemExit) as caught:
        cli.main(
            [
                "cmip6-download",
                "--plan",
                str(path),
                "--output",
                str(tmp_path / "download"),
                option,
                str(len(BODY) - 1),
            ]
        )
    assert caught.value.code == 2
    assert "CMIP6 retrieval failed" in capsys.readouterr().err
    assert len(calls) == before_download
    assert not list(tmp_path.rglob("*.nc"))


def test_cli_unknown_data_host_requires_explicit_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls = _mock_http(
        monkeypatch, lambda request: _response(request, host="archive.fixture.example")
    )
    path = tmp_path / "plan.json"
    assert cli.main(_search_arguments(path, "--start-year", "2000", "--end-year", "2014")) == 0
    capsys.readouterr()
    arguments = ["cmip6-download", "--plan", str(path), "--output", str(tmp_path / "download")]
    before_download = len(calls)
    with pytest.raises(SystemExit) as caught:
        cli.main(arguments)
    assert caught.value.code == 2
    assert len(calls) == before_download
    capsys.readouterr()
    assert cli.main([*arguments, "--allow-host", "ARCHIVE.FIXTURE.EXAMPLE"]) == 0
    assert next(tmp_path.rglob("*.nc")).read_bytes() == BODY
    assert calls[-1].url.host == "archive.fixture.example"


def test_cli_invalid_arguments_and_existing_plan_fail_without_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def unexpected(_: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid CLI input must not request provider data")

    calls = _mock_http(monkeypatch, unexpected)
    path = tmp_path / "plan.json"
    for arguments in (
        ["cmip6-search", "--output", str(path)],
        _search_arguments(path, "--start-year", "2000"),
        [
            "cmip6-download",
            "--plan",
            str(path),
            "--output",
            str(tmp_path / "download"),
            "--allow-host",
            "https://archive.example/path",
        ],
    ):
        with pytest.raises(SystemExit) as caught:
            cli.main(arguments)
        assert caught.value.code == 2
        assert capsys.readouterr().err
    path.write_text("preserved plan")
    with pytest.raises(SystemExit) as caught:
        cli.main(_search_arguments(path))
    assert caught.value.code == 2
    assert "already exists" in capsys.readouterr().err
    assert path.read_text() == "preserved plan"
    assert not calls
