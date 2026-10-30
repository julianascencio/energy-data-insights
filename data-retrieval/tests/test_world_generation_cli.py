"""Worldwide CLI dispatch, immutable snapshots, credentials and native imports."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from energy_data_retrieval import world_generation_cli
from energy_data_retrieval.cli import build_parser, main
from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.sources.adme import ADMEClient
from energy_data_retrieval.sources.aeso import AESOClient
from energy_data_retrieval.sources.caiso import CAISOClient
from energy_data_retrieval.sources.elexon import ElexonClient
from energy_data_retrieval.sources.emi import EMIClient
from energy_data_retrieval.sources.eskom import EskomClient
from energy_data_retrieval.sources.ieso import IESOClient
from energy_data_retrieval.sources.kpx import KPXClient
from energy_data_retrieval.sources.ons import ONSClient
from energy_data_retrieval.sources.pvdaq import PVDAQClient
from energy_data_retrieval.sources.rte import RTEClient
from energy_data_retrieval.sources.smard import SMARDClient
from energy_data_retrieval.sources.taipower import TaipowerClient
from energy_data_retrieval.sources.tepco import TEPCOClient
from energy_data_retrieval.sources.xm import XMClient
from energy_data_retrieval.storage import sha256_file
from energy_data_retrieval.transport import HTTPClient, RequestRecord

_DAY = date(2024, 6, 1)
_DATE_ARGS = ["--start", "2024-06-01", "--end", "2024-06-01"]
_SECRET = "synthetic-cli-test-key"


@pytest.mark.parametrize(
    ("name", "arguments", "client", "method", "positional", "keywords"),
    [
        (
            "adme-generation",
            [*_DATE_ARGS, "--central-id", "101", "--power-series", "X.GETOTMEDP.AV"],
            ADMEClient,
            "generation",
            (_DAY, _DAY),
            {
                "central_id": 101,
                "power_series": "X.GETOTMEDP.AV",
                "source_timezone": "America/Montevideo",
            },
        ),
        (
            "aeso-generation",
            ["--asset-id", "TEST"],
            AESOClient,
            "current_generation",
            (),
            {"api_key": _SECRET, "asset_ids": ["TEST"]},
        ),
        ("caiso-generation", _DATE_ARGS, CAISOClient, "generation", (_DAY, _DAY), {}),
        (
            "elexon-generation",
            [*_DATE_ARGS, "--bm-unit", "T_TEST"],
            ElexonClient,
            "generation",
            (_DAY, _DAY),
            {"bm_unit": "T_TEST"},
        ),
        (
            "emi-generation",
            [*_DATE_ARGS, "--plant", "te_apiti"],
            EMIClient,
            "generation",
            (_DAY, _DAY),
            {"plants": ["te_apiti"]},
        ),
        ("eskom-generation", [], EskomClient, "generation", (None, None), {"url": None}),
        (
            "ieso-generation",
            [*_DATE_ARGS, "--unit-id", "TEST"],
            IESOClient,
            "generation",
            (_DAY, _DAY),
            {"unit_ids": ["TEST"]},
        ),
        (
            "kpx-generation",
            [*_DATE_ARGS, "--region", "서울시"],
            KPXClient,
            "solar_generation",
            (_DAY, _DAY),
            {"region": "서울시"},
        ),
        (
            "ons-generation",
            [*_DATE_ARGS, "--plant-id", "ONS_TEST", "--include-estimates"],
            ONSClient,
            "generation",
            (_DAY, _DAY),
            {
                "plant_ids": ["ONS_TEST"],
                "source_timezone": "America/Sao_Paulo",
                "include_estimates": True,
            },
        ),
        (
            "ons-solar-curtailment",
            [*_DATE_ARGS, "--plant-id", "ONS_TEST"],
            ONSClient,
            "solar_curtailment",
            (_DAY, _DAY),
            {"plant_ids": ["ONS_TEST"], "source_timezone": "America/Sao_Paulo"},
        ),
        (
            "pvdaq-generation",
            [
                *_DATE_ARGS,
                "--system-id",
                "10",
                "--power-column",
                "ac_power__315",
                "--unit",
                "W",
                "--source-timezone=-07:00",
            ],
            PVDAQClient,
            "generation",
            (10, _DAY, _DAY),
            {"power_column": "ac_power__315", "unit": "W", "source_timezone": "-07:00"},
        ),
        ("pvdaq-metrics", ["--system-id", "10"], PVDAQClient, "metrics", (10,), {}),
        ("rte-generation", _DATE_ARGS, RTEClient, "generation", (_DAY, _DAY), {}),
        (
            "smard-generation",
            [*_DATE_ARGS, "--technology", "solar"],
            SMARDClient,
            "generation",
            (_DAY, _DAY),
            {"technologies": ["solar"]},
        ),
        (
            "taipower-generation",
            ["--include-aggregates", "--include-storage-load"],
            TaipowerClient,
            "latest",
            (),
            {"include_aggregates": True, "include_storage_load": True},
        ),
        (
            "tepco-generation",
            [*_DATE_ARGS, "--include-flows"],
            TEPCOClient,
            "generation",
            (_DAY, _DAY),
            {"include_flows": True},
        ),
        (
            "xm-generation",
            [*_DATE_ARGS, "--version", "TXR", "--resource-id", "TEST"],
            XMClient,
            "generation",
            (_DAY, _DAY),
            {"version": "TXR", "resource_ids": ["TEST"]},
        ),
    ],
)
def test_remote_dispatch_preserves_selection_and_snapshot_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    name: str,
    arguments: list[str],
    client: type,
    method: str,
    positional: tuple[object, ...],
    keywords: dict[str, object],
) -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-06-01T00:00Z", "2024-06-01T01:00Z"]),
            "value": [-2.0, float("nan")],
            "unit": ["MW", "MW"],
        }
    )
    frame.attrs.update(
        source="test measured source",
        missing_policy=None,
        metadata={"revised": True, "fields": ["value", None]},
    )
    record = RequestRecord(
        "https://source.example/data",
        {"public_selection": "TEST"},
        "2026-10-30T00:00Z",
        "a" * 64,
        100,
    )
    calls = []

    def fake(self, *args, **kwargs):
        calls.append((args, kwargs, self.maximum_rows))
        return GenerationResult(frame, (record,))

    monkeypatch.setattr(client, method, fake)
    monkeypatch.setenv("AESO_API_KEY", _SECRET)
    monkeypatch.setenv("KPX_API_KEY", _SECRET)
    output = tmp_path / "generation.parquet"
    argv = [name, *arguments, "--maximum-rows", "2000", "--output", str(output)]
    assert main(argv) == 0
    assert calls == [(positional, keywords, 2000)]
    manifest = json.loads(output.with_suffix(".parquet.json").read_text())
    assert manifest["provenance"]["requests"][0]["endpoint"] == record.endpoint
    assert manifest["provenance"]["metadata"]["metadata"]["fields"] == ["value", None]
    assert manifest["request"]["command"] == name
    saved = pd.read_parquet(output)
    assert saved.value.iloc[0] == -2 and pd.isna(saved.value.iloc[1])
    assert _SECRET not in output.with_suffix(".parquet.json").read_text()
    assert _SECRET not in capsys.readouterr().out

    def forbidden(*args, **kwargs):
        raise AssertionError("Snapshot reuse must precede HTTP client or credential access")

    monkeypatch.setattr(world_generation_cli, "HTTPClient", forbidden)
    monkeypatch.delenv("AESO_API_KEY")
    monkeypatch.delenv("KPX_API_KEY")
    assert main(argv) == 0 and len(calls) == 1
    changed = [name, *arguments, "--maximum-rows", "2001", "--output", str(output)]
    with pytest.raises(SystemExit, match="2"):
        main(changed)


@pytest.mark.parametrize(
    ("name", "arguments", "content", "expected_utc"),
    [
        (
            "nist-import",
            ["--array", "roof"],
            "TIMESTAMP,InvPAC_kW_Avg\n2016-07-01 12:00:00,25\n2016-07-01 12:01:00,NAN\n",
            "2016-07-01T17:00Z",
        ),
        (
            "dkasc-import",
            [
                "--system-id",
                "Alice-test",
                "--timestamp-column",
                "LocalTime",
                "--timestamp-format",
                "%d/%m/%Y %H:%M",
                "--power-column",
                "Test Array - 5-Min-Avg kW",
            ],
            "LocalTime,Test Array - 5-Min-Avg kW\n01/07/2024 12:00,25\n01/07/2024 12:05,\n",
            "2024-07-01T02:30Z",
        ),
        (
            "aeso-history",
            ["--interval-minutes", "60"],
            "Date (MST),Date (MPT),Asset Short Name,Asset Name,Volume,Fuel Type\n"
            "2024-07-01 12:00:00,2024-07-01 13:00:00,TEST,Test asset,25,SOLAR\n"
            "2024-07-01 13:00:00,2024-07-01 14:00:00,TEST,Test asset,,SOLAR\n",
            "2024-07-01T19:00Z",
        ),
    ],
)
def test_native_import_bytes_clock_and_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    arguments: list[str],
    content: str,
    expected_utc: str,
) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("Native imports must not perform HTTP requests")

    monkeypatch.setattr(HTTPClient, "get_json", forbidden)
    monkeypatch.setattr(HTTPClient, "get_text", forbidden)
    monkeypatch.setattr(HTTPClient, "download_file", forbidden)
    source = tmp_path / "native.csv"
    source.write_text(content)
    output = tmp_path / "import.parquet"
    argv = [name, *arguments, "--input", str(source), "--output", str(output)]
    assert main(argv) == 0
    frame = pd.read_parquet(output)
    assert frame.timestamp.iloc[0] == pd.Timestamp(expected_utc)
    assert frame.value.iloc[0] == 25 and pd.isna(frame.value.iloc[1])
    saved = json.loads(output.with_suffix(".parquet.json").read_text())
    checksum = hashlib.sha256(content.encode()).hexdigest()
    assert saved["request"]["input_sha256"] == checksum
    assert saved["provenance"]["requests"] == []
    assert main(argv) == 0
    old_hash = sha256_file(output)
    source.write_text(content.replace(",25", ",26"))
    with pytest.raises(SystemExit, match="2"):
        main(argv)
    assert sha256_file(output) == old_hash


@pytest.mark.parametrize("name", ["kpx-generation", "aeso-generation"])
def test_missing_credentials_fail_without_network_or_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.delenv("KPX_API_KEY", raising=False)
    monkeypatch.delenv("AESO_API_KEY", raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("Missing credentials must fail before a network request")

    monkeypatch.setattr(HTTPClient, "get_json", forbidden)
    output = tmp_path / "generation.parquet"
    dates = _DATE_ARGS if name == "kpx-generation" else []
    with pytest.raises(SystemExit, match="2"):
        main([name, *dates, "--output", str(output)])
    assert not output.exists() and not output.with_suffix(".parquet.json").exists()


@pytest.mark.parametrize(
    "argv",
    [
        ["taipower-generation", "--api-key", "never-accept-secrets", "--output", "x.parquet"],
        ["aeso-generation", "--api-key", "never-accept-secrets", "--output", "x.parquet"],
        [
            "kpx-generation",
            *_DATE_ARGS,
            "--service-key",
            "never-accept-secrets",
            "--output",
            "x.parquet",
        ],
        ["nist-import", "--input", "x.csv", "--output", "x.parquet"],
        [
            "pvdaq-generation",
            *_DATE_ARGS,
            "--system-id",
            "10",
            "--power-column",
            "ac_power__315",
            "--unit",
            "W",
            "--output",
            "x.parquet",
        ],
        ["caiso-generation", *_DATE_ARGS, "--maximum-requests", "0", "--output", "x.parquet"],
        ["aeso-history", "--input", "x.csv", "--output", "x.parquet"],
    ],
)
def test_parser_requires_source_semantics_and_rejects_cli_keys(argv: list[str]) -> None:
    with pytest.raises(SystemExit, match="2"):
        build_parser().parse_args(argv)


def test_native_import_enforces_input_byte_bound_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "native.csv"
    source.write_text("TIMESTAMP,InvPAC_kW_Avg\n2024-01-01 12:00:00,1\n")
    output = tmp_path / "x.parquet"

    def forbidden(*args, **kwargs):
        raise AssertionError("Byte bound must be checked before hashing a large file")

    monkeypatch.setattr(world_generation_cli, "sha256_file", forbidden)
    with pytest.raises(SystemExit, match="2"):
        main(
            [
                "nist-import",
                "--array",
                "roof",
                "--input",
                str(source),
                "--maximum-input-bytes",
                "1",
                "--output",
                str(output),
            ]
        )
    assert not output.exists()


def test_corrupt_snapshot_is_rejected_before_fetch(tmp_path: Path) -> None:
    output = tmp_path / "x.parquet"
    output.write_bytes(b"unpaired or corrupt output")
    with pytest.raises(SystemExit, match="2"):
        main(["taipower-generation", "--output", str(output)])
    assert output.read_bytes() == b"unpaired or corrupt output"


def test_all_world_providers_have_named_registered_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    for command in world_generation_cli.WORLD_GENERATION_COMMANDS:
        assert command in help_text
    assert (
        len({name.split("-", 1)[0] for name in world_generation_cli.WORLD_GENERATION_COMMANDS})
        == 17
    )
