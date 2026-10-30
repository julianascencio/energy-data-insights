"""EIA contract tests use synthetic API responses and a sourced public CSV excerpt."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import cast

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.eia import (
    EIA_HOSTS,
    EIAClient,
    balance_file_url,
    normalize_hourly_generation,
    normalize_monthly_generation,
    parse_balance_csv,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

START = datetime(2024, 1, 1, tzinfo=UTC)
DATA = Path(__file__).resolve().parents[2] / "examples" / "data"


def hourly(period: str = "2024-01-01T00", **updates: JSONValue) -> dict[str, JSONValue]:
    row: dict[str, JSONValue] = {
        "period": period,
        "respondent": "CISO",
        "respondent-name": "California Independent System Operator",
        "fueltype": "SUN",
        "type-name": "Solar",
        "value": "12.5",
        "value-units": "megawatthours",
    }
    return row | updates


def monthly(**updates: JSONValue) -> dict[str, JSONValue]:
    row: dict[str, JSONValue] = {
        "period": "2024-02",
        "plantCode": "00123",
        "plantName": "Synthetic test plant",
        "state": "CA",
        "fuel2002": "SUN",
        "fuelType": "SUN",
        "fuelTypeDescription": "Solar",
        "primeMover": "PV",
        "generation": "200.5",
        "generation-units": "megawatthours",
    }
    return row | updates


def response(rows: list[JSONValue], total: int | None = None, frequency: str = "hourly") -> dict:
    return {
        "response": {
            "total": str(len(rows) if total is None else total),
            "frequency": frequency,
            "data": rows,
        }
    }


def test_hour_ending_utc_units_missing_zero_and_negative() -> None:
    rows: list[JSONValue] = [
        hourly("2024-01-01T00", value="0"),
        hourly("2024-01-01T01", value=None),
        hourly("2024-01-01T02", value="-1.5"),
        hourly("2024-01-01T03", value="(s)"),
    ]
    result = normalize_hourly_generation(rows)
    assert result["timestamp"].iloc[0] == pd.Timestamp("2024-01-01T00:00Z")
    assert result["interval_start_utc"].iloc[0] == pd.Timestamp("2023-12-31T23:00Z")
    assert result["value"].iloc[0] == 0
    assert pd.isna(result["value"].iloc[1])
    assert result["value"].iloc[2] == -1.5
    assert pd.isna(result["value"].iloc[3])
    assert result["source_value"].iloc[3] == "(s)"
    assert result["unit"].eq("MWh").all()
    assert result["source_unit"].eq("megawatthours").all()
    assert result["respondent-name"].iloc[0] == "California Independent System Operator"


@pytest.mark.parametrize(
    "updates",
    [
        {"value": True},
        {"value": "NaN"},
        {"value": "Infinity"},
        {"value": "surprise"},
        {"value-units": "MW"},
        {"period": "2024-02-30T00"},
        {"period": "2024-01-01T00:30"},
        {"respondent": None},
    ],
)
def test_bad_hourly_values_fail(updates: dict[str, JSONValue]) -> None:
    with pytest.raises(RetrievalError):
        normalize_hourly_generation([hourly() | updates])


def test_duplicates_and_conflicts() -> None:
    assert len(normalize_hourly_generation([hourly(), hourly()])) == 1
    with pytest.raises(RetrievalError, match="Conflicting"):
        normalize_hourly_generation([hourly(), hourly(value="13")])


def test_monthly_preserves_plant_fuel_prime_mover_and_aggregates() -> None:
    frame = normalize_monthly_generation(
        [
            monthly(),
            monthly(primeMover="ALL"),
            monthly(fuel2002="NG", fuelType="NG", generation=None),
        ]
    )
    assert len(frame) == 3
    assert set(frame["primeMover"]) == {"PV", "ALL"}
    assert frame["unit_id"].eq("00123").all()
    assert frame["reporting_month"].eq("2024-02").all()
    assert frame["timestamp"].eq(pd.Timestamp("2024-02-01T00:00Z")).all()
    assert "duration_hours" not in frame
    assert "interval_end_utc" not in frame
    assert frame["value"].isna().sum() == 1


def test_paginates_beyond_5000_rows_and_sorts_all_keys() -> None:
    rows: list[JSONValue] = [
        hourly((START + timedelta(hours=index)).strftime("%Y-%m-%dT%H")) for index in range(5001)
    ]
    offsets: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        query = request.url.params
        offset = int(query["offset"])
        offsets.append(offset)
        assert query["frequency"] == "hourly"
        assert query["data[0]"] == "value"
        assert query["facets[respondent][0]"] == "CISO"
        assert [query[f"sort[{i}][column]"] for i in range(3)] == [
            "period",
            "respondent",
            "fueltype",
        ]
        return httpx.Response(200, json=response(rows[offset : offset + 5000], total=5001))

    with HTTPClient(
        EIA_HOSTS, transport=httpx.MockTransport(handler), sleep=lambda _: None
    ) as http:
        result = EIAClient(http, "fake-test-key").hourly_generation(
            START, START + timedelta(hours=5000), respondents=["CISO"]
        )
    assert offsets == [0, 5000]
    assert len(result.frame) == 5001
    assert len(result.requests) == 2
    assert "api_key" not in result.requests[0].parameters


@pytest.mark.parametrize(
    "failure", ["changed_total", "truncated", "duplicate", "filter", "period", "frequency"]
)
def test_rejects_incomplete_or_mismatched_api_results(failure: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        row = hourly("2024-01-01T00" if offset == 0 or failure == "duplicate" else "2024-01-01T01")
        if failure == "filter":
            row["respondent"] = "ERCO"
        if failure == "period":
            row["period"] = "2025-01-01T00"
        payload = response(
            [] if failure == "truncated" else [row],
            total=3 if offset and failure == "changed_total" else 2,
            frequency="local-hourly" if failure == "frequency" else "hourly",
        )
        return httpx.Response(200, json=payload)

    with (
        HTTPClient(EIA_HOSTS, transport=httpx.MockTransport(handler), sleep=lambda _: None) as http,
        pytest.raises(RetrievalError),
    ):
        EIAClient(http, "fake-test-key", page_size=1).hourly_generation(
            START, START + timedelta(hours=1), respondents=["CISO"]
        )


def test_row_limit_and_empty_response() -> None:
    with (
        HTTPClient(
            EIA_HOSTS,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json=response([], total=5001))
            ),
        ) as http,
        pytest.raises(RetrievalError, match="page limit"),
    ):
        EIAClient(http, "fake-test-key", maximum_pages=1).hourly_generation(
            START, START, respondents=["CISO"]
        )
    with HTTPClient(
        EIA_HOSTS, transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response([])))
    ) as http:
        result = EIAClient(http, "fake-test-key").hourly_generation(
            START, START, respondents=["CISO"]
        )
    assert result.frame.empty
    assert str(result.frame["timestamp"].dtype) == "datetime64[ns, UTC]"


def test_monthly_request_and_metadata() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.url.path.endswith("/data/"):
            query = request.url.params
            assert query["frequency"] == "monthly"
            assert query["data[0]"] == "generation"
            assert query["facets[plantCode][0]"] == "00123"
            assert query["facets[primeMover][0]"] == "PV"
            assert query["sort[4][column]"] == "primeMover"
            return httpx.Response(200, json=response([monthly()], frequency="monthly"))
        return httpx.Response(200, json={"response": {"facets": [{"id": "plantCode"}]}})

    with HTTPClient(
        EIA_HOSTS, transport=httpx.MockTransport(handler), sleep=lambda _: None
    ) as http:
        client = EIAClient(http, "fake-test-key")
        result = client.monthly_generation(
            "2024-02", "2024-02", plant_codes=["00123"], prime_movers=["PV"]
        )
        metadata, _ = client.metadata("monthly")
    assert result.frame["value"].iloc[0] == 200.5
    assert metadata["facets"] == [{"id": "plantCode"}]
    assert seen == ["/v2/electricity/facility-fuel/data/", "/v2/electricity/facility-fuel/"]


def test_key_is_private_and_errors_are_sanitized(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "synthetic-private-test-key"
    caplog.set_level(logging.DEBUG, logger="httpx")
    with HTTPClient(
        EIA_HOSTS,
        cache_directory=tmp_path,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"error": f"bad key {secret}"})
        ),
    ) as http:
        client = EIAClient(http, secret)
        assert secret not in repr(client)
        with pytest.raises(RetrievalError) as error:
            client.hourly_generation(START, START, respondents=["CISO"])
    assert secret not in str(error.value)
    assert secret not in caplog.text
    assert not list(tmp_path.iterdir())


def test_environment_key_and_input_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EIA_API_KEY", "synthetic-test-key")
    with HTTPClient(EIA_HOSTS) as http:
        assert EIAClient.from_environment(http).api_key == "synthetic-test-key"
        with pytest.raises(ValueError, match="EIA_API_KEY"):
            EIAClient(http).hourly_generation(START, START, respondents=["CISO"])
        with pytest.raises(ValueError, match="timezone-aware"):
            EIAClient(http, "x").hourly_generation(
                datetime(2024, 1, 1), START, respondents=["CISO"]
            )
        with pytest.raises(ValueError, match="hour boundaries"):
            EIAClient(http, "x").hourly_generation(
                START + timedelta(minutes=5), START, respondents=["CISO"]
            )
        with pytest.raises(ValueError, match="explicit source codes"):
            EIAClient(http, "x").hourly_generation(START, START, respondents="CISO")
        with pytest.raises(ValueError, match="calendar months"):
            EIAClient(http, "x").monthly_generation("2024-13", "2024-14", plant_codes=["1"])
        with pytest.raises(ValueError, match="page_size"):
            EIAClient(http, page_size=True)


def test_timezone_bounds_are_converted_to_utc() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["start"] == "2024-01-01T00"
        return httpx.Response(200, json=response([hourly()]))

    local = datetime(2024, 1, 1, 2, tzinfo=timezone(timedelta(hours=2)))
    with HTTPClient(EIA_HOSTS, transport=httpx.MockTransport(handler)) as http:
        assert (
            len(EIAClient(http, "x").hourly_generation(local, local, respondents=["CISO"]).frame)
            == 1
        )


def test_real_csv_excerpt_and_provenance() -> None:
    raw = (DATA / "generation_eia_ciso_2024.csv").read_bytes()
    manifest = json.loads((DATA / "generation_eia_ciso_2024.provenance.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest["sample_sha256"]
    frame = parse_balance_csv(raw.decode(), respondents=["CISO"], fuel_types=["SUN", "WND"])
    assert len(frame) == 168 * 2
    assert frame["timestamp"].nunique() == 168
    assert frame["area"].eq("CISO").all()
    assert frame["source_unit"].eq("MW").all()
    assert frame["unit"].eq("MWh").all()
    assert frame["duration_hours"].eq(1).all()
    assert frame["timestamp"].min() == pd.Timestamp("2024-06-20T08:00Z")
    assert frame["timestamp"].max() == pd.Timestamp("2024-06-27T07:00Z")
    assert not frame["source_column"].str.contains("Adjusted|Imputed").any()


def test_bulk_file_uses_no_key_and_keeps_provenance(tmp_path: Path) -> None:
    raw = (DATA / "generation_eia_ciso_2024.csv").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert "api_key" not in request.url.params
        assert request.url.path.endswith("EIA930_BALANCE_2024_Jan_Jun.csv")
        return httpx.Response(200, content=raw)

    with HTTPClient(
        EIA_HOSTS, transport=httpx.MockTransport(handler), config=HTTPConfig(attempts=1)
    ) as http:
        result = EIAClient(http).balance_file(
            2024, 1, tmp_path / "balance.csv", respondents=["CISO"], fuel_types=["SUN"]
        )
    assert len(result.frame) == 168
    assert result.requests[0].sha256 == hashlib.sha256(raw).hexdigest()
    assert (tmp_path / "balance.csv.download.json").exists()


def test_csv_uses_reported_values_and_new_storage_codes() -> None:
    text = (
        "Balancing Authority,UTC Time at End of Hour,"
        "Net Generation (MW) from Solar without Integrated Battery Storage,"
        "Net Generation (MW) from Solar with Integrated Battery Storage,"
        "Net Generation (MW) from Battery Storage,"
        "Net Generation (MW) from Solar without Integrated Battery Storage (Adjusted),"
        "Net Generation (MW) from Unknown Energy Storage\n"
        "CISO,01/01/2025 1:00:00 AM,0,5,-3,999,\n"
    )
    frame = parse_balance_csv(text).set_index("fueltype")
    assert set(frame.index) == {"SUN", "SNB", "BAT", "UES"}
    assert frame.loc["SUN", "value"] == 0
    assert frame.loc["BAT", "value"] == -3
    assert pd.isna(frame.loc["UES", "value"])


def test_csv_rejects_unknown_or_absent_selected_fuels() -> None:
    text = (
        "Balancing Authority,UTC Time at End of Hour,Net Generation (MW) from Solar\n"
        "CISO,01/01/2024 1:00:00 AM,1\n"
    )
    with pytest.raises(ValueError, match="unsupported source code"):
        parse_balance_csv(text, fuel_types=["SUN", "MISSING"])
    with pytest.raises(RetrievalError, match="selected fuel columns"):
        parse_balance_csv(text, fuel_types=["SUN", "BAT"])
    assert parse_balance_csv(text, fuel_types=["SUN"])["fueltype"].tolist() == ["SUN"]


@pytest.mark.parametrize("change", ["truncated", "row_limit", "bad_time", "unknown_fuel"])
def test_csv_rejects_bad_records(change: str) -> None:
    text = (
        "Balancing Authority,UTC Time at End of Hour,Net Generation (MW) from Solar\n"
        "CISO,01/01/2024 1:00:00 AM,1\n"
    )
    if change == "truncated":
        text = text.removesuffix("1\n")
    elif change == "bad_time":
        text = text.replace("1:00:00", "1:10:00")
    elif change == "unknown_fuel":
        text = text.replace("Solar", "Future Unknown Technology")
    elif change == "row_limit":
        text += "CISO,01/01/2024 2:00:00 AM,2\n"
    with pytest.raises(RetrievalError):
        parse_balance_csv(text, maximum_rows=1)


def test_balance_urls_and_empty_normalizers() -> None:
    assert balance_file_url(2024, 2).endswith("EIA930_BALANCE_2024_Jul_Dec.csv")
    with pytest.raises(ValueError):
        balance_file_url(2015, 1)
    with pytest.raises(ValueError):
        balance_file_url(True, 1)
    assert normalize_hourly_generation(cast(list[JSONValue], [])).empty
    assert normalize_monthly_generation([]).empty
