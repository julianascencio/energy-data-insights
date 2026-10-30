"""EMI trading days, kWh and real fixture contracts; HTTP tests use synthetic rows."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.emi import (
    EMI_HOSTS,
    EMIClient,
    generation_urls,
    parse_generation_csv,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

DATA = Path(__file__).resolve().parents[2] / "examples/connectors/data"


def csv_day(day: str, periods: int, first: str = "0") -> str:
    header = "POC_Code,Nwk_Code,Gen_Code,Fuel_Code,Tech_Code,Trading_Date,"
    header += ",".join(f"TP{n}" for n in range(1, 51))
    values = [first, "", *["-1.5"] * (periods - 2), *[""] * (50 - periods)]
    return header + "\nPOINT,NET,plant,Wind,Wind," + day + "," + ",".join(values) + "\n"


@pytest.mark.parametrize(
    "day,periods", [("2024-09-29", 46), ("2024-04-07", 50), ("2024-01-01", 48)]
)
def test_dst_days_are_contiguous_utc_intervals(day: str, periods: int) -> None:
    frame = parse_generation_csv(csv_day(day, periods))
    assert len(frame) == periods
    assert frame.value.iloc[0] == 0 and pd.isna(frame.value.iloc[1])
    assert frame.value.iloc[-1] == -1.5
    assert frame.unit.eq("kWh").all()
    assert frame.timestamp.diff().iloc[1:].eq(pd.Timedelta(minutes=30)).all()
    assert frame.interval_end.iloc[-1] == pd.Timestamp(
        date.fromisoformat(day), tz="Pacific/Auckland"
    ) + pd.DateOffset(days=1)


def test_rejects_invalid_period_padding_duplicates_and_numbers() -> None:
    with pytest.raises(RetrievalError, match="outside"):
        parse_generation_csv(csv_day("2024-09-29", 48))
    for bad in ("nan", "inf", "abc"):
        with pytest.raises(RetrievalError, match=r"numeric|finite"):
            parse_generation_csv(csv_day("2024-01-01", 48, first=bad))
    data = csv_day("2024-01-01", 48)
    with pytest.raises(RetrievalError, match="duplicate"):
        parse_generation_csv(data + data.splitlines()[1])
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_generation_csv(data, maximum_rows=47)


def test_month_plans_bounded_and_inclusive() -> None:
    urls = generation_urls(date(2024, 12, 31), date(2025, 1, 1))
    assert len(urls) == 2 and urls[1].endswith("202501_Generation_MD.csv")
    with pytest.raises(ValueError, match="maximum_requests"):
        generation_urls(date(2024, 12, 31), date(2025, 1, 1), maximum_requests=1)
    with pytest.raises(ValueError, match="August 1997"):
        generation_urls(date(1997, 1, 1), date(1997, 1, 1))


def test_client_filtering_and_provenance() -> None:
    raw = (DATA / "generation_emi.csv").read_bytes()
    with HTTPClient(
        EMI_HOSTS,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=raw)),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = EMIClient(http).generation(date(2024, 9, 29), date(2024, 9, 29), plants=["Kohira"])
        assert len(result.frame) == 46
        assert result.requests[0].sha256 == hashlib.sha256(raw).hexdigest()
        with pytest.raises(RetrievalError, match="absent"):
            EMIClient(http).generation(date(2024, 9, 29), date(2024, 9, 29), plants=["unknown"])


def test_real_fixture_integrity_and_dst_coverage() -> None:
    raw = (DATA / "generation_emi.csv").read_bytes()
    manifest = json.loads((DATA / "generation_emi_provenance.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"]
    frame = parse_generation_csv(raw)
    assert frame.groupby(["plant_id", "source_date"]).size().tolist() == [48, 46, 48] * 3
