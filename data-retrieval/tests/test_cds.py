"""Synthetic SDK responses exercise CDS boundaries; no live jobs or credentials."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from energy_data_retrieval.cli import main
from energy_data_retrieval.sources.cds import CDS_URL, CDSClient, CDSRequest, era5_requests
from energy_data_retrieval.sources.cds import client as module
from energy_data_retrieval.transport import JSONValue, RetrievalError


class Result:
    def __init__(self, payload: bytes = b"GRIB-synthetic-fixture", *, size: int | None = None):
        self.payload = payload
        self.content_length = len(payload) if size is None else size
        self.downloads = 0

    def download(self, target: str) -> None:
        self.downloads += 1
        Path(target).write_bytes(self.payload)


class SDK:
    def __init__(self, result: Result | None = None):
        self.result = result or Result()
        self.calls: list[tuple[str, dict[str, JSONValue]]] = []

    def retrieve(self, name: str, request: dict[str, JSONValue]) -> Result:
        self.calls.append((name, request))
        return self.result


def request() -> CDSRequest:
    return CDSRequest("reanalysis-era5-single-levels", {"variable": ["2m_temperature"]})


def test_immutable_canonical_request_and_validation():
    selection: dict[str, JSONValue] = {"year": ["2024"], "variable": ["2m_temperature"]}
    query = CDSRequest("reanalysis-era5-single-levels", selection)
    same = CDSRequest(query.dataset, dict(reversed(list(selection.items()))))
    assert query.sha256 == same.sha256
    selection["year"] = ["2025"]
    query.selection["year"] = ["2026"]
    assert query.selection["year"] == ["2024"]
    assert "era5_single_levels" in query.reference_ids


@pytest.mark.parametrize(
    "selection",
    [
        {},
        {"api_key": "synthetic"},
        {"nested": {"Authorization": "synthetic"}},
        {"temperature": float("nan")},
        {"bad key": "x"},
        {"url": "https://example.org"},
    ],
)
def test_invalid_request_fails_before_submission(selection):
    with pytest.raises(ValueError):
        CDSRequest("reanalysis-era5-single-levels", selection)


@pytest.mark.parametrize("dataset", ["../escape", "https://example.org", "", "UpperCase"])
def test_dataset_slug_cannot_be_url_or_path(dataset):
    with pytest.raises(ValueError, match="slug"):
        CDSRequest(dataset, {"variable": "x"})


def test_native_download_provenance_and_verified_offline_reuse(tmp_path, monkeypatch):
    sdk = SDK()
    first = CDSClient(sdk=sdk).download(request(), tmp_path)
    assert first.path.name == "download.grib" and not first.reused
    assert first.sha256 == hashlib.sha256(sdk.result.payload).hexdigest()
    assert first.path.read_bytes() == sdk.result.payload
    manifest = json.loads(first.manifest_path.read_text())
    assert manifest["request"] == request().as_dict()
    assert manifest["request_sha256"] == request().sha256
    assert manifest["complete"] is True
    assert manifest["artifact"]["bytes"] == len(sdk.result.payload)
    assert "Native bytes" in manifest["processing"]

    def no_import(*args, **kwargs):
        raise AssertionError("Reusing verified output must not initialize the SDK")

    monkeypatch.setattr(module.importlib, "import_module", no_import)
    second = CDSClient().download(request(), tmp_path)
    assert second.reused and second.path == first.path
    assert len(sdk.calls) == 1
    first.path.write_bytes(b"tampered")
    with pytest.raises(RetrievalError, match="checksum"):
        CDSClient().download(request(), tmp_path)


@pytest.mark.parametrize(
    "payload,suffix",
    [
        (b"PK\x03\x04synthetic-zip", "zip"),
        (b"CDF\x01fixture", "nc"),
        (b"\x89HDF\r\n\x1a\nfixture", "h5"),
        (b"\x1f\x8bfixture", "gz"),
        (b"x,y\n1,2", "bin"),
    ],
)
def test_actual_signature_is_used_instead_of_requested_format(tmp_path, payload, suffix):
    query = CDSRequest("example-dataset", {"data_format": "netcdf"})
    result = CDSClient(sdk=SDK(Result(payload))).download(query, tmp_path)
    assert result.path.suffix == f".{suffix}"
    assert result.path.read_bytes() == payload  # Archives are never automatically extracted.


def test_size_limit_prevents_transfer_and_partial_files_are_removed(tmp_path):
    oversized = Result(size=100)
    with pytest.raises(RetrievalError, match="size"):
        CDSClient(sdk=SDK(oversized), maximum_download_bytes=10).download(request(), tmp_path)
    assert oversized.downloads == 0
    assert not list(tmp_path.rglob("manifest.json"))
    assert not list(tmp_path.rglob(".cds-*"))
    mismatch = Result(size=1)
    with pytest.raises(RetrievalError, match="size does not match"):
        CDSClient(sdk=SDK(mismatch)).download(request(), tmp_path)
    assert not list(tmp_path.rglob("manifest.json"))


def test_provider_error_never_exposes_secret_and_partial_output_is_removed(tmp_path):
    class BrokenResult(Result):
        def download(self, target: str) -> None:
            super().download(target)
            raise RuntimeError("private-token https://example.org/result?secret=private-token")

    with pytest.raises(RetrievalError) as caught:
        CDSClient(sdk=SDK(BrokenResult())).download(request(), tmp_path)
    assert "private-token" not in str(caught.value)
    assert caught.value.__suppress_context__
    assert not list(tmp_path.rglob("download.*"))


def test_incomplete_cache_is_not_silently_reused(tmp_path):
    directory = tmp_path / request().dataset / request().sha256
    directory.mkdir(parents=True)
    (directory / "download.grib").write_bytes(b"synthetic")
    sdk = SDK()
    with pytest.raises(RetrievalError, match="incomplete"):
        CDSClient(sdk=sdk).download(request(), tmp_path)
    assert not sdk.calls


def test_sdk_setup_options_and_errors_are_safe(tmp_path, monkeypatch):
    sdk = SDK()

    def create(**options):
        assert options["url"] == CDS_URL and options["verify"] is True
        assert options["retry_max"] == 3 and options["timeout"] == 60
        assert options["quiet"] is True and options["progress"] is False
        for key in ("debug_callback", "warning_callback", "error_callback", "info_callback"):
            options[key]("private-token")
        return sdk

    monkeypatch.setattr(
        module.importlib, "import_module", lambda name: SimpleNamespace(Client=create)
    )
    CDSClient().download(request(), tmp_path)

    def missing(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(module.importlib, "import_module", missing)
    with pytest.raises(ImportError, match=r"\[cds\]"):
        CDSClient().download(request(), tmp_path / "missing")

    def broken(**options):
        raise RuntimeError("private-token")

    monkeypatch.setattr(
        module.importlib, "import_module", lambda name: SimpleNamespace(Client=broken)
    )
    with pytest.raises(RetrievalError, match="personal access token") as caught:
        CDSClient().download(request(), tmp_path / "failed")
    assert "private-token" not in str(caught.value)


def test_real_sdk_constructor_accepts_adapter_options_with_mocked_http(monkeypatch):
    pytest.importorskip("cdsapi")
    requests = pytest.importorskip("requests")
    monkeypatch.setenv("CDSAPI_KEY", "synthetic-test-token")
    monkeypatch.setenv("CDSAPI_URL", "https://example.org/must-not-use")

    seen = []

    def mock_send(self, prepared, **kwargs):
        assert prepared.method == "GET" and prepared.url == CDS_URL + "/catalogue/v1/messages"
        seen.append(prepared.url)
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"messages":[]}'
        response.request = prepared
        return response

    monkeypatch.setattr(requests.Session, "send", mock_send)
    sdk = CDSClient()._client()
    assert vars(sdk)["url"] == CDS_URL
    assert vars(sdk)["verify"] is True
    assert len(seen) == 1


def test_era5_hourly_plan_handles_leap_year_and_partial_months():
    plans = era5_requests(
        date(2024, 2, 28), date(2024, 3, 2), variables=["2m_temperature"], area=(29, -17, 28, -16)
    )
    assert len(plans) == 2
    assert plans[0].selection["day"] == ["28", "29"]
    assert plans[1].selection["day"] == ["01", "02"]
    assert plans[0].selection["time"] == [f"{hour:02d}:00" for hour in range(24)]
    assert plans[0].selection["area"] == [29, -17, 28, -16]
    assert plans[0].selection["download_format"] == "unarchived"
    assert plans[0].dataset == "reanalysis-era5-single-levels"


def test_era5_monthly_plan_crosses_year_and_keeps_monthly_semantics():
    plans = era5_requests(
        date(2023, 12, 1),
        date(2024, 2, 29),
        variables=["surface_solar_radiation_downwards"],
        area=(29, -17, 28, -16),
        monthly_means=True,
        data_format="netcdf",
    )
    assert len(plans) == 3
    assert [p.selection["month"] for p in plans] == [["12"], ["01"], ["02"]]
    assert [p.selection["year"] for p in plans] == [["2023"], ["2024"], ["2024"]]
    for plan in plans:
        assert "day" not in plan.selection
        assert plan.selection["product_type"] == ["monthly_averaged_reanalysis"]
        assert plan.selection["time"] == ["00:00"]
        assert "era5_single_levels_monthly" in plan.reference_ids


@pytest.mark.parametrize(
    "changes",
    [
        {"start": date(1939, 1, 1)},
        {"start": datetime(2024, 1, 1)},
        {"end": date(2023, 1, 1)},
        {"area": (29, 170, 28, -170)},
        {"area": (91, -17, 28, -16)},
        {"area": (29, float("nan"), 28, -16)},
        {"variables": ["2m_temperature", "2m_temperature"]},
        {"variables": "2m_temperature"},
        {"monthly_means": True, "start": date(2024, 1, 2)},
        {"data_format": "csv"},
    ],
)
def test_era5_invalid_selections_rejected(changes):
    settings = {
        "start": date(2024, 1, 1),
        "end": date(2024, 1, 31),
        "variables": ["2m_temperature"],
        "area": (29, -17, 28, -16),
    } | changes
    with pytest.raises(ValueError):
        era5_requests(**settings)


def test_cli_plan_needs_no_credentials_or_sdk(capsys, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("No SDK during planning")

    monkeypatch.setattr(CDSClient, "_client", fail)
    assert (
        main(
            [
                "cds-era5",
                "--start",
                "2024-02-01",
                "--end",
                "2024-02-29",
                "--variables",
                "2m_temperature",
                "--area",
                "29",
                "-17",
                "28",
                "-16",
                "--plan-only",
            ]
        )
        == 0
    )
    body = json.loads(capsys.readouterr().out)
    assert body["submitted"] is False
    assert len(body["requests"]) == 1


def test_cli_generic_download_and_duplicate_json_rejection(tmp_path, monkeypatch, capsys):
    path = tmp_path / "request.json"
    path.write_text('{"variable":["2m_temperature"]}')
    monkeypatch.setattr(CDSClient, "_client", lambda self: SDK())
    arguments = [
        "cds-retrieve",
        "--dataset",
        request().dataset,
        "--request",
        str(path),
        "--output",
        str(tmp_path / "downloads"),
    ]
    assert main(arguments) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["complete"] is True and len(result["artifacts"]) == 1
    path.write_text('{"variable":"a","variable":"b"}')
    with pytest.raises(SystemExit) as caught:
        main(arguments)
    assert caught.value.code == 2
    assert "Duplicate JSON request key" in capsys.readouterr().err
