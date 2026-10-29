"""Synthetic historical exports test time, units, identities and restart contracts."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import httpx
import pandas as pd
import pytest
from openpyxl import Workbook

from energy_data_retrieval.cli import main
from energy_data_retrieval.sources.cen.history import (
    HistorySchema,
    import_history,
    normalize_history,
)
from energy_data_retrieval.tabular import read_export
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def schema(**changes: object) -> HistorySchema:
    base = HistorySchema(
        identity_column="name",
        value_column="energy",
        timestamp_column="time",
        timezone="UTC",
        timestamp_label="start",
        energy_unit="MWh",
    )
    return replace(base, **changes)  # type: ignore[arg-type]


def roster() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_id": ["A", "Alias A", "B"],
            "unit_id": ["u-a", "u-a", "u-b"],
            "site_id": ["plant", "plant", "plant"],
        }
    )


def observations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["A", "Alias A", "B", "A", "B"],
            "time": ["2026-01-01T00:00Z"] * 3 + ["2026-01-01T01:00Z"] * 2,
            "energy": ["1000", "1000", "0", "2000", ""],
        }
    )


def test_verified_aliases_units_zeros_and_missing_remain_distinct() -> None:
    result = normalize_history(observations(), roster(), schema(energy_unit="kWh"))
    assert result["actual_mwh"].iloc[0] == 1.0
    assert pd.isna(result["actual_mwh"].iloc[1])
    assert result["reported_mwh"].iloc[1] == 2.0
    assert result["valid_unit_count"].tolist() == [2, 1]
    assert result.attrs["duplicate_equal_rows_removed"] == 1


def test_conflicting_alias_is_not_summed_or_given_precedence() -> None:
    frame = observations()
    frame.loc[1, "energy"] = "2000"
    with pytest.raises(ValueError, match="Conflicting"):
        normalize_history(frame, roster(), schema())


def test_one_physical_unit_cannot_be_counted_at_multiple_sites() -> None:
    mapping = roster()
    mapping.loc[1, "site_id"] = "another-plant"
    with pytest.raises(ValueError, match="exactly one site"):
        normalize_history(observations(), mapping, schema())


def test_unknown_id_and_wrong_temporal_resolution_fail() -> None:
    with pytest.raises(ValueError, match="unmapped"):
        normalize_history(observations(), roster().iloc[:2], schema())
    with pytest.raises(ValueError, match="Daily"):
        schema(temporal_resolution="daily")


def test_dst_fold_requires_offsets_and_offsets_preserve_both_hours() -> None:
    mapping = roster().iloc[:1]
    frame = pd.DataFrame({"name": ["A"], "time": ["2026-04-04T23:00:00"], "energy": [1]})
    with pytest.raises(ValueError, match="Ambiguous"):
        normalize_history(frame, mapping, schema(timezone="America/Santiago"))
    frame = pd.DataFrame(
        {
            "name": ["A", "A"],
            "time": ["2026-04-04T23:00:00-03:00", "2026-04-04T23:00:00-04:00"],
            "energy": [1, 2],
        }
    )
    out = normalize_history(frame, mapping, schema(timezone="America/Santiago"))
    assert out["timestamp"].dt.hour.tolist() == [2, 3]
    assert out["actual_mwh"].sum() == 3


def test_nonexistent_civil_hour_is_not_shifted() -> None:
    frame = pd.DataFrame({"name": ["A"], "time": ["2026-09-06T00:00:00"], "energy": [1]})
    with pytest.raises(ValueError, match="nonexistent"):
        normalize_history(frame, roster().iloc[:1], schema(timezone="America/Santiago"))


def test_wide24_and_long_hour_labels_have_explicit_interval_end() -> None:
    cols = tuple(f"H{hour}" for hour in range(1, 25))
    frame = pd.DataFrame({"name": ["A"], "day": ["2026-01-01"], **{c: [1] for c in cols}})
    contract = schema(
        timestamp_column=None,
        date_column="day",
        hour_columns=cols,
        timestamp_label="end",
    )
    out = normalize_history(frame, roster().iloc[:1], contract)
    assert out["timestamp"].dt.hour.tolist() == list(range(24))
    assert out["actual_mwh"].sum() == 24
    long = pd.DataFrame({"name": ["A"], "day": ["2026-01-01"], "h": [24], "energy": [7]})
    out = normalize_history(
        long, roster().iloc[:1], replace(contract, hour_columns=(), hour_column="h")
    )
    assert out["timestamp"].iloc[0] == pd.Timestamp("2026-01-01T23:00Z")


def test_import_fingerprints_source_mapping_and_precision(tmp_path: Path) -> None:
    source = tmp_path / "qlik.csv"
    mapping = tmp_path / "mapping.csv"
    output = tmp_path / "generation.parquet"
    observations().to_csv(source, index=False)
    roster().to_csv(mapping, index=False)
    contract = schema(source="cen-qlik", decimal_places=2, measurement_basis="unspecified")
    first = import_history(source, mapping, output, contract)
    assert import_history(source, mapping, output, contract) == first
    manifest = json.loads(output.with_suffix(".parquet.json").read_text())
    assert manifest["request"]["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert manifest["request"]["schema"]["decimal_places"] == 2
    assert manifest["provenance"]["schema"]["measurement_basis"] == "unspecified"
    with pytest.raises(ValueError, match="snapshot"):
        import_history(source, mapping, output, replace(contract, measurement_basis="gross"))


def test_xlsx_explicit_sheet_and_zip_member_limits(tmp_path: Path) -> None:
    book = Workbook()
    sheet = book.active
    assert sheet is not None
    sheet.title = "Hourly"
    sheet.append(["name", "time", "energy"])
    sheet.append(["A", "2026-01-01T00:00:00Z", 0])
    path = tmp_path / "historical.xlsx"
    book.save(path)
    book.close()
    with pytest.raises(ValueError, match="sheet"):
        read_export(path)
    assert read_export(path, sheet="Hourly")["energy"].iloc[0] == 0
    zipped = tmp_path / "history.zip"
    with zipfile.ZipFile(zipped, "w") as archive:
        archive.write(path, "tables/hourly.xlsx")
        archive.writestr("../unsafe.csv", "unsafe")
    assert len(read_export(zipped, member="tables/hourly.xlsx", sheet="Hourly")) == 1
    with pytest.raises(ValueError, match="safe relative"):
        read_export(zipped, member="../unsafe.csv")
    csv = tmp_path / "too-many.csv"
    csv.write_text("a\n1\n2\n")
    with pytest.raises(RetrievalError, match="row limit"):
        read_export(csv, maximum_rows=1)


def test_streamed_download_retry_resume_and_tamper_detection(tmp_path: Path) -> None:
    payload = b"name,time,value\nsynthetic,2026-01-01,0\n"
    calls = 0
    sleeps: list[float] = []

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503) if calls == 1 else httpx.Response(200, content=payload)

    path = tmp_path / "archive.csv"
    with HTTPClient(
        frozenset({"fixture.example"}),
        config=HTTPConfig(minimum_interval_seconds=0),
        transport=httpx.MockTransport(handler),
        sleep=sleeps.append,
    ) as http:
        first = http.download_file("https://fixture.example/archive.csv", path)
        second = http.download_file("https://fixture.example/archive.csv", path)
        assert first.sha256 == second.sha256 == hashlib.sha256(payload).hexdigest()
        assert calls == 2 and sleeps == [1] and second.cache_hit
        path.write_bytes(b"tampered")
        with pytest.raises(ValueError, match="checksum"):
            http.download_file("https://fixture.example/archive.csv", path)


def test_oversized_or_wrong_hash_download_never_publishes(tmp_path: Path) -> None:
    with (
        HTTPClient(
            frozenset({"fixture.example"}),
            config=HTTPConfig(maximum_response_bytes=5, minimum_interval_seconds=0),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"123456")),
        ) as http,
        pytest.raises(RetrievalError, match="byte limit"),
    ):
        http.download_file("https://fixture.example/archive.csv", tmp_path / "large.csv")
    assert list(tmp_path.iterdir()) == []
    with (
        HTTPClient(
            frozenset({"fixture.example"}),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"x")),
        ) as http,
        pytest.raises(RetrievalError, match="unexpected SHA"),
    ):
        http.download_file(
            "https://fixture.example/x.csv", tmp_path / "x.csv", expected_sha256="0" * 64
        )
    assert list(tmp_path.iterdir()) == []


def test_history_cli_runs_offline(tmp_path: Path) -> None:
    source, mapping = tmp_path / "input.csv", tmp_path / "mapping.csv"
    observations().to_csv(source, index=False)
    roster().to_csv(mapping, index=False)
    config = tmp_path / "source.toml"
    config.write_text(
        'identity_column = "name"\nvalue_column = "energy"\ntimestamp_column = "time"\n'
        'timezone = "UTC"\ntimestamp_label = "start"\nenergy_unit = "MWh"\n'
    )
    output = tmp_path / "out.parquet"
    assert (
        main(
            [
                "cen-history",
                "--input",
                str(source),
                "--mapping",
                str(mapping),
                "--schema",
                str(config),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert len(pd.read_parquet(output)) == 2
