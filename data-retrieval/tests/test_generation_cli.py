"""Source-specific CLI dispatch and auditable snapshot reuse without network."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from energy_data_retrieval.cli import build_parser, main
from energy_data_retrieval.sources.aemo import AEMOClient
from energy_data_retrieval.sources.eia import EIAClient
from energy_data_retrieval.sources.entsoe import ENTSOEClient
from energy_data_retrieval.sources.ree import REEClient
from energy_data_retrieval.transport import RequestRecord


@pytest.mark.parametrize(
    ("command", "arguments", "client", "method"),
    [
        (
            "aemo-generation",
            ["--date", "2024-06-01", "--duid", "TEST1"],
            AEMOClient,
            "generation_day",
        ),
        (
            "eia-generation",
            ["--start", "2024-06-01T01:00Z", "--end", "2024-06-02T00:00Z", "--respondent", "CISO"],
            EIAClient,
            "hourly_generation",
        ),
        (
            "eia-plant-generation",
            ["--start", "2024-01", "--end", "2024-12", "--plant-code", "123"],
            EIAClient,
            "monthly_generation",
        ),
        (
            "ree-generation",
            ["--start", "2024-06-01", "--end", "2024-06-30"],
            REEClient,
            "generation",
        ),
        (
            "entsoe-generation",
            [
                "--start",
                "2024-06-01T00:00Z",
                "--end",
                "2024-06-02T00:00Z",
                "--area",
                "10YES-REE------0",
            ],
            ENTSOEClient,
            "generation_by_type",
        ),
        (
            "entsoe-generation",
            [
                "--start",
                "2024-06-01T00:00Z",
                "--end",
                "2024-06-02T00:00Z",
                "--area",
                "10YES-REE------0",
                "--per-unit",
            ],
            ENTSOEClient,
            "generation_by_unit",
        ),
    ],
)
def test_dispatch_and_snapshot_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    arguments: list[str],
    client: type,
    method: str,
) -> None:
    calls = []
    frame = pd.DataFrame({"timestamp": pd.to_datetime(["2024-06-01"], utc=True), "value": [0.0]})
    frame.attrs["unit"] = "MWh"
    record = RequestRecord(
        "https://source.example/data", {"selection": "public"}, "2026-10-30T00:00Z", "a" * 64, 12
    )

    def fake(self, *args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(frame=frame, data=frame, request=record, requests=(record,))

    monkeypatch.setattr(client, method, fake)
    output = tmp_path / "generation.parquet"
    argv = [command, *arguments, "--output", str(output)]
    assert main(argv) == 0
    saved = json.loads(output.with_suffix(".parquet.json").read_text())
    assert saved["provenance"]["requests"][0]["endpoint"] == record.endpoint
    assert saved["provenance"]["metadata"]["unit"] == "MWh"
    assert pd.read_parquet(output)["value"].tolist() == [0.0]
    assert main(argv) == 0 and len(calls) == 1
    if command == "aemo-generation":
        assert calls[0] == ((date(2024, 6, 1),), {"duids": ["TEST1"]})


def test_generation_parser_requires_explicit_timezone() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as error:
        parser.parse_args(
            [
                "eia-generation",
                "--start",
                "2024-06-01T00:00",
                "--end",
                "2024-06-02T00:00Z",
                "--respondent",
                "CISO",
                "--output",
                "data.parquet",
            ]
        )
    assert error.value.code == 2


def test_entsoe_unit_filter_requires_unit_product(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as error:
        main(
            [
                "entsoe-generation",
                "--start",
                "2024-06-01T00:00Z",
                "--end",
                "2024-06-02T00:00Z",
                "--area",
                "10YES-REE------0",
                "--unit-id",
                "TEST",
                "--output",
                str(tmp_path / "x.parquet"),
            ]
        )
    assert error.value.code == 2
