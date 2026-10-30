"""PVDAQ native channels, explicit clocks, daily bounds and real sample provenance."""

from __future__ import annotations

import hashlib
import io
import json
from datetime import date
from pathlib import Path
from typing import TypedDict

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.pvdaq import (
    PVDAQ_HOSTS,
    PVDAQClient,
    daily_url,
    parse_generation_csv,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

CSV = "measured_on,system_id,ac_power__315,ambient_temp__320\n2023-01-01 12:00:00,4,800,-2\n"


class ChannelOptions(TypedDict):
    power_column: str
    unit: str
    source_timezone: str


OPTIONS: ChannelOptions = {
    "power_column": "ac_power__315",
    "unit": "W",
    "source_timezone": "-07:00",
}


def test_explicit_power_units_and_clock_preserve_native_channels() -> None:
    frame = parse_generation_csv(CSV, system_id=4, **OPTIONS)
    assert frame.timestamp.iloc[0] == pd.Timestamp("2023-01-01T19:00:00Z")
    assert frame.value.tolist() == [800.0]
    assert frame.unit.tolist() == ["W"]
    assert frame.ambient_temp__320.tolist() == [-2]
    assert frame.attrs["source_timezone"] == "-07:00"


@pytest.mark.parametrize("replacement", ["-1", "0", ""])
def test_signed_zero_and_missing_power_are_preserved(replacement: str) -> None:
    frame = parse_generation_csv(CSV.replace(",800,", f",{replacement},"), system_id=4, **OPTIONS)
    if replacement:
        assert frame.value.iloc[0] == float(replacement)
    else:
        assert pd.isna(frame.value.iloc[0])


@pytest.mark.parametrize("replacement", ["inf", "false", "bad"])
def test_invalid_power_is_rejected(replacement: str) -> None:
    with pytest.raises(RetrievalError):
        parse_generation_csv(CSV.replace(",800,", f",{replacement},"), system_id=4, **OPTIONS)


def test_schema_id_duplicate_and_row_bounds() -> None:
    with pytest.raises(RetrievalError, match="system_id"):
        parse_generation_csv(CSV.replace(",4,", ",5,"), system_id=4, **OPTIONS)
    with pytest.raises(RetrievalError, match="duplicate column"):
        parse_generation_csv(
            CSV.replace("ambient_temp__320", "ac_power__315"), system_id=4, **OPTIONS
        )
    row = CSV.splitlines()[1] + "\n"
    with pytest.raises(RetrievalError, match="conflicting"):
        parse_generation_csv(CSV + row.replace(",800,", ",801,"), system_id=4, **OPTIONS)
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_generation_csv(CSV + row, maximum_rows=1, system_id=4, **OPTIONS)
    assert len(parse_generation_csv(CSV + row, system_id=4, **OPTIONS)) == 1


def test_ambiguous_source_clock_is_never_guessed() -> None:
    csv = CSV.replace("2023-01-01 12:00:00", "2023-11-05 01:30:00")
    options = OPTIONS.copy()
    options["source_timezone"] = "America/Denver"
    with pytest.raises(RetrievalError, match="ambiguous"):
        parse_generation_csv(csv, system_id=4, **options)


def test_daily_fetch_bounded_request_and_provenance() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert str(request.url) == daily_url(4, date(2023, 1, 1))
        return httpx.Response(200, text=CSV)

    with HTTPClient(
        PVDAQ_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        client = PVDAQClient(http, maximum_requests=1)
        with pytest.raises(ValueError, match="maximum_requests"):
            client.generation(
                4,
                date(2023, 1, 1),
                date(2023, 1, 2),
                **OPTIONS,
            )
        assert not calls
        result = client.generation(
            4,
            date(2023, 1, 1),
            date(2023, 1, 1),
            **OPTIONS,
        )
    assert len(result.requests) == 1
    assert result.requests[0].sha256 == hashlib.sha256(CSV.encode()).hexdigest()
    assert result.frame.attrs["requested_start"] == "2023-01-01"


def test_wrong_day_fails_instead_of_appearing_complete() -> None:
    with (
        HTTPClient(
            PVDAQ_HOSTS,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=CSV)),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError, match="outside"),
    ):
        PVDAQClient(http).generation(
            4,
            date(2023, 1, 2),
            date(2023, 1, 2),
            **OPTIONS,
        )


def test_channel_metadata_retains_units_and_scaling() -> None:
    buffer = io.BytesIO()
    pd.DataFrame(
        {
            "system_id": [4],
            "standard_name": ["ac_power__315"],
            "units": ["W"],
            "aggregation_type": ["avg"],
            "calc_scale": [1.0],
        }
    ).to_parquet(buffer, index=False)
    with HTTPClient(
        PVDAQ_HOSTS,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=buffer.getvalue())),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = PVDAQClient(http).metrics(4)
    assert result.frame.units.tolist() == ["W"]
    assert result.frame.attrs["product"] == "channel_metadata"
    assert len(result.requests) == 1


def test_real_capture_has_verified_hash_and_1440_measured_minutes() -> None:
    data = Path(__file__).resolve().parents[2] / "examples/connectors/data"
    content = (data / "generation_pvdaq.csv").read_bytes()
    manifest = json.loads((data / "generation_pvdaq_provenance.json").read_text())
    assert hashlib.sha256(content).hexdigest() == manifest["sha256"]
    frame = parse_generation_csv(content, system_id=4, **OPTIONS)
    assert len(frame) == 1440
    assert frame.value.max() > 500
    assert frame.value.max() < 1500
