"""Regression cases from independent review of worldwide generation importers."""

from __future__ import annotations

import io
from datetime import date

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources._generation_utils import bounded_csv, utc_labels
from energy_data_retrieval.sources.nist import parse_generation_csv as parse_nist
from energy_data_retrieval.sources.pvdaq import PVDAQ_HOSTS, PVDAQClient
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError


def test_explicit_offsets_remain_unambiguous_across_autumn_clock_change() -> None:
    labels = pd.Series(["2024-11-03T01:30:00-04:00", "2024-11-03T01:30:00-05:00"])
    actual = utc_labels(labels, source_timezone=None, timestamp_format="ISO8601")
    expected = pd.Series(pd.to_datetime(["2024-11-03T05:30:00Z", "2024-11-03T06:30:00Z"]))
    pd.testing.assert_series_equal(actual, expected)


def test_naive_ambiguous_clock_labels_still_fail() -> None:
    with pytest.raises(RetrievalError):
        utc_labels(
            pd.Series(["2024-11-03T01:30:00"]),
            source_timezone="America/New_York",
            timestamp_format="ISO8601",
        )


@pytest.mark.parametrize("reverse", [False, True])
def test_mixed_explicit_and_naive_timestamps_fail(reverse: bool) -> None:
    labels = ["2024-01-01T12:00:00-05:00", "2024-01-01T12:05:00"]
    if reverse:
        labels.reverse()
    with pytest.raises(RetrievalError, match="mix"):
        utc_labels(
            pd.Series(labels),
            source_timezone="America/New_York",
            timestamp_format="ISO8601",
        )


def test_csv_does_not_silently_turn_an_extra_field_into_an_index() -> None:
    # pandas.read_csv otherwise accepts this by inferring an undocumented index.
    with pytest.raises(RetrievalError):
        bounded_csv("TIMESTAMP,InvPAC_kW_Avg\nextra,2016-07-01 12:00:00,12.4\n")


def test_csv_truncated_rows_fail_but_explicit_missing_values_survive() -> None:
    with pytest.raises(RetrievalError, match="width"):
        bounded_csv("timestamp,power\n2016-07-01 12:00:00\n")
    result = bounded_csv("timestamp,power\n2016-07-01 12:00:00,\n")
    assert len(result) == 1
    assert pd.isna(result.power.iloc[0])


def test_csv_stops_at_row_cap_before_parsing_the_rest_of_the_file() -> None:
    with pytest.raises(RetrievalError, match="maximum_rows"):
        bounded_csv('power\n1\n2\n"unterminated', maximum_rows=1)


def test_nist_toa5_metadata_uses_logical_records_with_quoted_newlines() -> None:
    content = (
        '"TOA5","metadata with\na quoted newline"\n"TIMESTAMP","InvPAC_kW_Avg"\n'
        '"TS","kW"\n"","Avg"\n"2016-01-01 12:00:00",-0.2\n'
    )
    frame = parse_nist(content, array="ground")
    assert frame.value.tolist() == [-0.2]


@pytest.mark.parametrize("aggregation", ["Avg", "Max", ""])
def test_nist_one_second_toa5_requires_instantaneous_aggregation(aggregation: str) -> None:
    # Parser fixtures, deliberately not presented as observed NIST measurements.
    content = (
        '"TOA5","test fixture"\n"TIMESTAMP","InvPAC_kW"\n'
        f'"TS","kW"\n"","{aggregation}"\n"2016-01-01 12:00:00",-0.2\n'
    )
    with pytest.raises(RetrievalError):
        parse_nist(content, array="ground", power_column="InvPAC_kW", resolution="one-second")


def test_nist_one_second_toa5_sample_aggregation_is_accepted() -> None:
    content = (
        '"TOA5","test fixture"\n"TIMESTAMP","InvPAC_kW"\n'
        '"TS","kW"\n"","Smp"\n"2016-01-01 12:00:00",-0.2\n'
    )
    frame = parse_nist(content, array="ground", power_column="InvPAC_kW", resolution="one-second")
    assert frame.measurement_kind.tolist() == ["instantaneous_power"]
    assert frame.sampling_seconds.tolist() == [1]
    assert frame.value.tolist() == [-0.2]


def test_pvdaq_partition_check_preserves_mixed_explicit_offset_source_dates() -> None:
    content = (
        "measured_on,system_id,ac_power__315\n"
        "2024-11-03T01:30:00-04:00,4,10\n"
        "2024-11-03T01:30:00-05:00,4,20\n"
    )
    with HTTPClient(
        PVDAQ_HOSTS,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=content)),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = PVDAQClient(http).generation(
            4,
            date(2024, 11, 3),
            date(2024, 11, 3),
            power_column="ac_power__315",
            unit="W",
            source_timezone="America/New_York",
        )
    assert result.frame.timestamp.tolist() == [
        pd.Timestamp("2024-11-03T05:30:00Z"),
        pd.Timestamp("2024-11-03T06:30:00Z"),
    ]


def test_pvdaq_metadata_row_bound_precedes_parquet_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buffer = io.BytesIO()
    pd.DataFrame({"system_id": [4, 4]}).to_parquet(buffer, index=False)

    def unexpected_read(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Oversized metadata must be rejected before pd.read_parquet")

    monkeypatch.setattr(pd, "read_parquet", unexpected_read)
    with (
        HTTPClient(
            PVDAQ_HOSTS,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=buffer.getvalue())),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError, match="maximum_rows"),
    ):
        PVDAQClient(http, maximum_rows=1).metrics(4)


@pytest.mark.parametrize("maximum_rows", [0, -1, True, 10_000_001])
def test_pvdaq_rejects_invalid_row_bounds_before_http(maximum_rows: int) -> None:
    def unexpected_request(_request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid bounds must be rejected before any HTTP request")

    with (
        HTTPClient(PVDAQ_HOSTS, transport=httpx.MockTransport(unexpected_request)) as http,
        pytest.raises(ValueError, match="maximum_rows"),
    ):
        PVDAQClient(http, maximum_rows=maximum_rows).metrics(4)
