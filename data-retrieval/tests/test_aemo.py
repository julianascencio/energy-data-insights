"""AEMO dispatch labels, instantaneous readings, nested archives and provenance."""

from __future__ import annotations

import hashlib
import io
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.aemo import (
    AEMO_HOSTS,
    ARCHIVE_ENDPOINT,
    CURRENT_ENDPOINT,
    AEMOClient,
    parse_dispatch_scada,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

HEADER = "I,DISPATCH,UNIT_SCADA,1,SETTLEMENTDATE,DUID,SCADAVALUE,LASTCHANGED\r\n"
ROW = 'D,DISPATCH,UNIT_SCADA,1,"2026/01/01 00:05:00",NYNGAN1,10.25,"2026/01/01 00:00:02"\r\n'
FILE = "PUBLIC_DISPATCHSCADA_202601010005_00001.zip"


def zipped(members: dict[str, str | bytes]) -> bytes:
    output = io.BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, body in members.items():
            archive.writestr(name, body)
    return output.getvalue()


def client(handler: Callable[[httpx.Request], httpx.Response]) -> HTTPClient:
    return HTTPClient(
        AEMO_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0, retry_base_seconds=0),
        sleep=lambda _: None,
    )


def test_nem_clock_retains_dispatch_label_without_daylight_saving_shift() -> None:
    summer = ROW
    winter = ROW.replace("2026/01/01", "2026/07/01")
    frame = parse_dispatch_scada(HEADER + summer + winter)
    assert frame.timestamp.tolist() == [
        pd.Timestamp("2025-12-31T14:05:00Z"),
        pd.Timestamp("2026-06-30T14:05:00Z"),
    ]
    assert frame["value"].tolist() == [10.25, 10.25]
    assert set(frame["unit"]) == {"MW"}
    assert set(frame["quantity_kind"]) == {"instantaneous_power"}
    assert frame["technology"].isna().all()
    assert frame["source:SETTLEMENTDATE"].iloc[0] == "2026/01/01 00:05:00"
    assert frame["source:LASTCHANGED"].iloc[0] == "2026/01/01 00:00:02"
    assert frame.attrs["interval_average"] is False
    assert frame.attrs["settlement_energy"] is False


def test_missing_negative_and_punctuation_duids_are_preserved() -> None:
    negative = ROW.replace("NYNGAN1,10.25", "TARONG#1,-0.25")
    missing = ROW.replace("NYNGAN1,10.25", "W/HOE#1,")
    frame = parse_dispatch_scada(HEADER + negative + missing)
    assert frame.unit_id.tolist() == ["TARONG#1", "W/HOE#1"]
    assert frame.value.iloc[0] == -0.25
    assert pd.isna(frame.value.iloc[1])
    assert frame["source:SCADAVALUE"].tolist() == ["-0.25", ""]


def test_nested_daily_zip_and_filter_match_plain_csv() -> None:
    second = ROW.replace("00:05:00", "00:10:00").replace("10.25", "20.5")
    extra = ROW.replace("NYNGAN1", "COLEASF1")
    body = zipped(
        {
            "first.zip": zipped({"first.CSV": HEADER + ROW + extra}),
            "second.zip": zipped({"second.CSV": HEADER + second}),
        }
    )
    frame = parse_dispatch_scada(body, duids=["NYNGAN1"])
    assert frame["value"].tolist() == [10.25, 20.5]
    assert frame.attrs["source_rows_before_filter"] == 3
    assert frame.attrs["selected_duids"] == ["NYNGAN1"]
    assert frame["source_member"].str.contains(".zip!", regex=False).all()


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (HEADER + ROW + ROW, "duplicate"),
        (ROW, "matching header"),
        (HEADER.replace("SCADAVALUE", "OTHER") + ROW, "required"),
        (HEADER + ROW.replace("10.25", "oops"), "nonnumeric"),
        (HEADER + ROW.replace("10.25", "nan"), "nonfinite"),
        (HEADER + ROW.replace("10.25", "inf"), "nonfinite"),
        (HEADER + ROW.replace("00:05:00", "00:04:00"), "five-minute"),
        (HEADER + ROW.replace("2026/01/01 00:05:00", "bad"), "five-minute"),
        ("<html>maintenance</html>", "no matching"),
    ],
)
def test_malformed_or_ambiguous_data_fails(text: str, message: str) -> None:
    with pytest.raises(RetrievalError, match=message):
        parse_dispatch_scada(text)


def test_duplicate_keys_across_zip_members_are_not_double_counted() -> None:
    body = zipped({"first.CSV": HEADER + ROW, "second.CSV": HEADER + ROW})
    with pytest.raises(RetrievalError, match="duplicate"):
        parse_dispatch_scada(body)


def test_row_limit_applies_before_requested_duid_filter() -> None:
    body = HEADER + ROW + ROW.replace("NYNGAN1", "COLEASF1")
    with pytest.raises(RetrievalError, match="row bound"):
        parse_dispatch_scada(body, duids=["NYNGAN1"], maximum_rows=1)
    with pytest.raises(RetrievalError, match="absent"):
        parse_dispatch_scada(HEADER + ROW, duids=["NYNGAN1", "MISSING1"])


def test_archive_resource_bounds() -> None:
    large = HEADER + ROW + " " * 10000
    body = zipped({"file.CSV": large})
    with pytest.raises(RetrievalError, match="byte bound"):
        parse_dispatch_scada(body, maximum_uncompressed_bytes=1000)
    with pytest.raises(RetrievalError, match="member bound"):
        parse_dispatch_scada(zipped({"a.CSV": HEADER + ROW, "b.CSV": HEADER}), maximum_members=1)
    with pytest.raises(RetrievalError, match="nesting"):
        parse_dispatch_scada(zipped({"a.zip": zipped({"b.zip": zipped({"c.CSV": HEADER + ROW})})}))
    with pytest.raises(RetrievalError, match="ZIP"):
        parse_dispatch_scada(b"PKbroken")


def test_listing_discovers_only_supported_public_files() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == CURRENT_ENDPOINT
        return httpx.Response(
            200,
            text=(
                f'<a href="{FILE}">ok</a><a href="{FILE}">duplicate</a>'
                f'<a href="https://example.org/{FILE}">external</a>'
                '<a href="DUPLICATE/">subdirectory</a>'
                f'<a href="{ARCHIVE_ENDPOINT}PUBLIC_DISPATCHSCADA_20260101.zip">archive</a>'
            ),
        )

    with client(handler) as http:
        result = AEMOClient(http).list_files()
    assert result.urls == (CURRENT_ENDPOINT + FILE,)
    assert result.request.endpoint == CURRENT_ENDPOINT


def test_generation_day_fetches_real_archive_shape_with_hash() -> None:
    end = ROW.replace("2026/01/01 00:05:00", "2026/01/02 00:00:00")
    body = zipped(
        {"first.zip": zipped({"a.CSV": HEADER + ROW}), "last.zip": zipped({"b.CSV": HEADER + end})}
    )
    url = ARCHIVE_ENDPOINT + "PUBLIC_DISPATCHSCADA_20260101.zip"

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == url
        return httpx.Response(200, content=body)

    with client(handler) as http:
        result = AEMOClient(http).generation_day(date(2026, 1, 1), duids=["NYNGAN1"])
    assert len(result.frame) == 2
    assert result.frame.attrs["nem_day"] == "2026-01-01"
    assert result.request.sha256 == hashlib.sha256(body).hexdigest()
    assert result.request.size_bytes == len(body)


def test_wrong_day_and_untrusted_urls_fail() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=zipped({"a.CSV": HEADER + ROW}))

    with client(handler) as http:
        source = AEMOClient(http)
        with pytest.raises(RetrievalError, match="outside"):
            source.generation_day(date(2026, 1, 2))
        for url in ("https://example.org/file.zip", CURRENT_ENDPOINT + "../file.zip"):
            with pytest.raises(ValueError):
                source.fetch_file(url)


def test_checked_in_real_sample_matches_manifest_and_all_three_units() -> None:
    directory = Path(__file__).resolve().parents[2] / "examples" / "connectors" / "data"
    manifest = json.loads((directory / "generation_aemo_manifest.json").read_text())
    data = (directory / "generation_aemo_scada.csv").read_bytes()
    assert hashlib.sha256(data).hexdigest() == manifest["subset_sha256"]
    frame = parse_dispatch_scada(data)
    assert len(frame) == manifest["subset_rows"] == 864
    assert frame.groupby("unit_id").size().to_dict() == dict.fromkeys(manifest["duids"], 288)
    assert frame.timestamp.nunique() == 288
    assert frame.timestamp.min() == pd.Timestamp("2026-10-26T14:05Z")
    assert frame.timestamp.max() == pd.Timestamp("2026-10-27T14:00Z")
    assert frame.groupby("unit_id")["value"].max().to_dict() == {
        "BROKENH1": 53.39919,
        "COLEASF1": 141.90089,
        "NYNGAN1": 100.25,
    }
