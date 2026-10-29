"""CLI discovery chooses explicit local, metadata-only and live-probe workflows."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval import cli, discovery, discovery_cli
from energy_data_retrieval.station_discovery import StationCatalogue
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue


def arguments(*extra: str) -> list[str]:
    return ["discover", "--latitude", "28.5", "--longitude", "-16.5", *extra]


def deny_http_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("This discovery mode must not construct an HTTP client")

    monkeypatch.setattr(discovery_cli, "HTTPClient", unexpected)


def test_help_describes_station_grid_and_optional_verification_options(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        cli.main(["discover", "--help"])
    assert error.value.code == 0
    help_text = capsys.readouterr().out
    for option in ("--latitude", "--longitude", "--radius-km", "--catalogue", "--probe-date"):
        assert option in help_text
    assert "--grid-only" in help_text and "--cmip6-plan" in help_text


@pytest.mark.parametrize("selection", [("--grid-only",), ("--offline", "--station-source", "noaa")])
def test_metadata_only_and_offline_modes_do_not_construct_http_clients(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    selection: tuple[str, ...],
) -> None:
    deny_http_creation(monkeypatch)
    assert cli.main(arguments(*selection)) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["query"]["network_enabled"] is False
    assert body["stations"] == []
    assert len(body["grid_datasets"]) == 8
    assert all(row["availability_status"] == "not_checked" for row in body["grid_datasets"])
    if "--offline" in selection:
        assert body["source_status"][0]["status"] == "not_requested"
        assert body["status"] == "partial"
    else:
        assert body["source_status"] == []
        assert body["status"] == "complete"


def test_explicit_local_catalogue_selection_needs_no_http_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    deny_http_creation(monkeypatch)
    path = tmp_path / "stations.parquet"

    def load(
        source: str, http: HTTPClient | None, *, local_path: Path | None = None
    ) -> StationCatalogue:
        assert source == "noaa" and http is None and local_path == path
        return StationCatalogue(
            "noaa",
            "local_catalogue",
            pd.DataFrame(
                {"source": ["noaa"], "station_id": ["N1"], "latitude": [28.5], "longitude": [-16.5]}
            ),
            {"provider_catalogue_complete": True, "observations_verified": False},
            ("ascencio_vasquez_2021_thesis",),
            [],
            [],
        )

    monkeypatch.setattr(discovery, "load_station_catalogue", load)
    assert cli.main(arguments("--station-source", "noaa", "--catalogue", "noaa=" + str(path))) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["query"]["network_enabled"] is False
    assert body["stations"][0]["station_id"] == "N1"
    assert body["source_status"][0]["status"] == "local_catalogue"


def test_output_path_saves_full_snapshot_and_prints_summary_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    deny_http_creation(monkeypatch)
    path = tmp_path / "point.json"
    command = arguments("--grid-only", "--output", str(path))
    assert cli.main(command) == 0
    summary = json.loads(capsys.readouterr().out)
    body = json.loads(path.read_text())
    assert summary["output_path"] == str(path)
    assert summary["stations"] == 0 and summary["grid_datasets"] == 8
    assert body["query"]["latitude"] == 28.5
    assert len(body["discovery_sha256"]) == 64
    original = path.read_bytes()
    with pytest.raises(SystemExit) as error:
        cli.main(command)
    assert error.value.code == 2
    assert "already exists" in capsys.readouterr().err
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (("--offline", "--probe-date", "2025-01-01"), "cannot be used"),
        (("--grid-only", "--probe-date", "bad-date"), "YYYY-MM-DD"),
        (("--grid-only", "--station-source", "noaa"), "not allowed"),
        (("--offline", "--catalogue", "unknown=stations.parquet"), "SOURCE=PATH"),
        (
            ("--offline", "--catalogue", "noaa=a.parquet", "--catalogue", "noaa=b.parquet"),
            "SOURCE=PATH",
        ),
        (("--grid-only", "--limit", "0"), "limit"),
    ],
)
def test_invalid_cli_combinations_fail_without_http_creation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    extra: tuple[str, ...],
    message: str,
) -> None:
    deny_http_creation(monkeypatch)
    with pytest.raises(SystemExit) as error:
        cli.main(arguments(*extra))
    assert error.value.code == 2
    assert message in capsys.readouterr().err


def test_explicit_grid_probe_constructs_one_client_and_passes_selected_date(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    clients: list[HTTPClient] = []
    probes: list[tuple[HTTPClient, date]] = []

    def unexpected_request(request: httpx.Request) -> httpx.Response:
        pytest.fail("Routing test attempted an actual provider request")

    def client(
        allowed_hosts: frozenset[str],
        *,
        config: HTTPConfig,
        cache_directory: Path | None,
    ) -> HTTPClient:
        instance = HTTPClient(
            allowed_hosts,
            config=config,
            cache_directory=cache_directory,
            transport=httpx.MockTransport(unexpected_request),
        )
        clients.append(instance)
        return instance

    def probe(
        http: HTTPClient, candidates: list[dict[str, JSONValue]], *, day: date
    ) -> list[dict[str, JSONValue]]:
        probes.append((http, day))
        return candidates

    monkeypatch.setattr(discovery_cli, "HTTPClient", client)
    monkeypatch.setattr(discovery, "verify_open_meteo", probe)
    assert cli.main(arguments("--grid-only", "--probe-date", "2025-01-01")) == 0
    body = json.loads(capsys.readouterr().out)
    assert len(clients) == 1 and probes == [(clients[0], date(2025, 1, 1))]
    assert body["query"]["probe_date"] == "2025-01-01"
    assert body["query"]["network_enabled"] is True
    assert body["source_status"] == []
