"""Synthetic ENTSO-E contracts: curve semantics, direction, dates and credentials."""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.entsoe import (
    ENTSOE_HOSTS,
    ENTSOEClient,
    generation_requests,
    normalize_generation,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

AREA = "10YES-REE------0"
START = datetime(2025, 1, 1, tzinfo=UTC)
END = START + timedelta(hours=1)
UNIT = "21W000000000999G"


def period(
    points: str,
    *,
    start: str = "2025-01-01T00:00Z",
    end: str = "2025-01-01T01:00Z",
    resolution: str = "PT15M",
) -> str:
    return (
        f"<Period><timeInterval><start>{start}</start><end>{end}</end></timeInterval>"
        f"<resolution>{resolution}</resolution>{points}</Period>"
    )


def point(position: int, quantity: str | None = "10", reason: str = "") -> str:
    value = f"<quantity>{quantity}</quantity>" if quantity is not None else ""
    why = f"<Reason><code>{reason}</code></Reason>" if reason else ""
    return f"<Point><position>{position}</position>{value}{why}</Point>"


def series(
    periods: str | None = None,
    *,
    curve: str = "A03",
    flow: str = "in",
    unit: str = "MAW",
    area: str = AREA,
    resource: str = "",
    identifier: str = "1",
    technology: str = "B16",
) -> str:
    resource_xml = (
        f"<PowerSystemResources><mRID>{resource}</mRID>"
        "<name>Test unit</name></PowerSystemResources>"
        if resource
        else ""
    )
    return (
        f"<TimeSeries><mRID>{identifier}</mRID><businessType>A01</businessType>"
        f"<{flow}BiddingZone_Domain.mRID>{area}</{flow}BiddingZone_Domain.mRID>"
        f"<quantity_Measure_Unit.name>{unit}</quantity_Measure_Unit.name>"
        f"<curveType>{curve}</curveType><MktPSRType><psrType>{technology}</psrType>"
        f"{resource_xml}</MktPSRType>{periods or period(point(1))}</TimeSeries>"
    )


def document(*items: str, document_type: str = "A75") -> str:
    return (
        '<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">'
        f"<mRID>synthetic-test</mRID><revisionNumber>1</revisionNumber><type>{document_type}</type>"
        f"<process.processType>A16</process.processType>{''.join(items)}</GL_MarketDocument>"
    )


def acknowledgement(text: str, code: str = "999") -> str:
    return (
        '<Acknowledgement_MarketDocument xmlns="urn:test:ack">'
        f"<Reason><code>{code}</code><text>{text}</text></Reason></Acknowledgement_MarketDocument>"
    )


def test_a03_expands_changes_and_missing_blocks_without_inventing_zero() -> None:
    points = point(1, "0") + point(2, None, "A03") + point(4, "-2.5")
    result = normalize_generation(document(series(period(points))))
    assert len(result) == 4
    assert result["value"].iloc[0] == 0
    assert result["value"].iloc[1:3].isna().all()
    assert result["missing_reason"].tolist() == ["", "A03", "A03", ""]
    assert result["value"].iloc[3] == -2.5
    assert result["timestamp"].tolist() == list(pd.date_range(START, periods=4, freq="15min"))
    assert result["interval_end"].iloc[-1] == END
    assert result["duration_hours"].eq(0.25).all()
    assert result["unit"].eq("MW").all() and result["native_unit"].eq("MAW").all()
    assert result["technology_name"].eq("Solar").all()
    assert result.attrs["reference_ids"] == [
        "entsoe_transparency_api",
        "entsoe_generation_data_descriptions",
        "entsoe_curve_types",
    ]


def test_a01_absent_positions_remain_missing_without_forward_fill() -> None:
    result = normalize_generation(document(series(period(point(1) + point(3, "0")), curve="A01")))
    assert result["value"].iloc[::2].tolist() == [10, 0]
    assert result["value"].iloc[1::2].isna().all()


def test_a03_does_not_carry_values_between_periods_or_before_first_point() -> None:
    first = period(point(1))
    second = period(point(3, "5"), start="2025-01-01T01:00Z", end="2025-01-01T02:00Z")
    result = normalize_generation(document(series(first + second)))
    assert result["value"].iloc[:4].eq(10).all()
    assert result["value"].iloc[4:6].isna().all()
    assert result["value"].iloc[6:].eq(5).all()


def test_generation_and_consumption_are_distinct_even_for_same_technology() -> None:
    result = normalize_generation(
        document(series(technology="B10"), series(flow="out", identifier="2", technology="B10"))
    )
    assert len(result) == 8
    assert set(result["flow"]) == {"generation", "consumption"}
    assert result["value"].eq(10).all()  # No inferred netting or sign reversal.


def test_unit_resource_identity_preserved() -> None:
    result = normalize_generation(document(series(resource=UNIT), document_type="A73"))
    assert result["unit_id"].eq(UNIT).all()
    assert result["unit_name"].eq("Test unit").all()
    with pytest.raises(RetrievalError, match="resource EIC"):
        normalize_generation(document(series(), document_type="A73"))


def test_equal_duplicates_removed_and_conflicting_overlaps_fail() -> None:
    frame = normalize_generation(document(series(), series(identifier="2")))
    assert len(frame) == 4
    with pytest.raises(RetrievalError, match="conflicting"):
        normalize_generation(document(series(), series(period(point(1, "20")), identifier="2")))
    with pytest.raises(RetrievalError, match="overlapping"):
        normalize_generation(
            document(
                series(),
                series(
                    period(point(1), start="2025-01-01T00:05Z", end="2025-01-01T00:20Z"),
                    identifier="2",
                ),
            )
        )


@pytest.mark.parametrize(
    ("xml", "message"),
    [
        (document(series(curve="A02")), "A01 and A03"),
        (document(series(unit="MWH")), "MAW"),
        (document(series(period(point(1) + point(1)))), "duplicated"),
        (document(series(period(point(0)))), "outside"),
        (document(series(period(point(5)))), "outside"),
        (document(series(period(point(1, "nan")))), "non-finite"),
        (document(series(period(point(1, "inf")))), "non-finite"),
        (document(series(period(point(1, "unavailable")))), "nonnumeric"),
        (document(series(period(point(1), resolution="P1M"))), "resolution"),
        (document(series(period(point(1), end="2025-01-01T01:05Z"))), "boundaries"),
        (document(series(period(point(1), start="2025-01-01T00:00"))), "UTC"),
        (document(series(), document_type="A69"), "realised"),
        (document(series()).replace("A16", "A01"), "realised"),
        (
            document(series()).replace("<curveType>", "<cancelledTS>A01</cancelledTS><curveType>"),
            "cancelled",
        ),
        ("<html>maintenance</html>", "required"),
        ('<!DOCTYPE a [<!ENTITY b "x">]><a/>', "DTD"),
    ],
)
def test_malformed_or_wrong_product_fails(xml: str, message: str) -> None:
    with pytest.raises(RetrievalError, match=message):
        normalize_generation(xml)


def test_expansion_and_bytes_are_bounded() -> None:
    with pytest.raises(RetrievalError, match="maximum_rows"):
        normalize_generation(document(series()), maximum_rows=3)
    with pytest.raises(RetrievalError, match="byte limit"):
        normalize_generation(document(series()), maximum_bytes=10)


def test_no_data_acknowledgement_is_distinct_from_invalid_request() -> None:
    result = normalize_generation(acknowledgement("No matching data found for requested area"))
    assert result.empty and result.attrs["no_data"]
    assert str(result["timestamp"].dtype) == "datetime64[ns, UTC]"
    assert "entsoe_transparency_api" in result.attrs["reference_ids"]
    with pytest.raises(RetrievalError, match="rejected"):
        normalize_generation(acknowledgement("Invalid parameter securityToken=should-not-leak"))


def test_request_plan_uses_utc_exclusive_bounds_and_limits() -> None:
    first = datetime(2025, 3, 30, tzinfo=ZoneInfo("Europe/Madrid"))
    last = datetime(2025, 3, 31, tzinfo=ZoneInfo("Europe/Madrid"))
    planned = generation_requests(AREA, first, last, psr_type="B16")
    assert len(planned) == 1
    assert planned[0] == {
        "documentType": "A75",
        "processType": "A16",
        "in_Domain": AREA,
        "periodStart": "202503292300",
        "periodEnd": "202503302200",
        "psrType": "B16",
    }
    longer = generation_requests(AREA, START, START + timedelta(days=32))
    assert len(longer) == 2
    assert longer[0]["periodEnd"] == longer[1]["periodStart"]
    units = generation_requests(AREA, START, START + timedelta(days=2), per_unit=True, unit_id=UNIT)
    assert len(units) == 2 and units[0]["registeredResource"] == UNIT
    assert units[0]["documentType"] == "A73"
    with pytest.raises(ValueError, match="maximum_requests"):
        generation_requests(AREA, START, START + timedelta(days=32), maximum_requests=1)
    with pytest.raises(ValueError, match="timezone-aware"):
        generation_requests(AREA, datetime(2025, 1, 1), END)
    with pytest.raises(ValueError, match="whole minutes"):
        generation_requests(AREA, START + timedelta(seconds=1), END)
    with pytest.raises(ValueError, match="exclusive"):
        generation_requests(AREA, END, START)
    with pytest.raises(ValueError, match="16-character"):
        generation_requests("ES", START, END)
    with pytest.raises(ValueError, match="only valid"):
        generation_requests(AREA, START, END, unit_id=UNIT)


def test_client_request_contract_secret_isolation_and_provenance(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    token = "private-entsoe-test-token"
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        assert request.url.host == "web-api.tp.entsoe.eu"
        assert request.url.params["securityToken"] == token
        assert request.url.params["psrType"] == "B16"
        return httpx.Response(200, text=document(series()))

    with (
        caplog.at_level(logging.INFO, logger="httpx"),
        HTTPClient(
            ENTSOE_HOSTS,
            config=HTTPConfig(attempts=1, minimum_interval_seconds=0),
            transport=httpx.MockTransport(handle),
            cache_directory=tmp_path,
        ) as http,
    ):
        client = ENTSOEClient(http, token=token)
        result = client.generation_by_type(AREA, START, END, psr_type="B16")
        assert len(result.data) == 4
        assert len(result.requests) == 1
        assert token not in repr(client)
        assert token not in repr(asdict(result.requests[0]))
        client.generation_by_type(AREA, START, END, psr_type="B16")
    assert len(seen) == 2 and not list(tmp_path.iterdir())
    assert token not in caplog.text


def test_client_no_data_wrong_area_missing_token_and_row_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with HTTPClient(
        ENTSOE_HOSTS, transport=httpx.MockTransport(lambda _: httpx.Response(401))
    ) as http:
        monkeypatch.delenv("ENTSOE_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="ENTSOE_API_TOKEN"):
            ENTSOEClient.from_environment(http).generation_by_type(AREA, START, END)
    with HTTPClient(
        ENTSOE_HOSTS,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, text=acknowledgement("No matching data found"))
        ),
    ) as http:
        result = ENTSOEClient(http, token="test").generation_by_type(AREA, START, END)
        assert result.data.empty and len(result.requests) == 1
    with (
        HTTPClient(
            ENTSOE_HOSTS,
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, text=document(series(area="10YFR-RTE------C")))
            ),
        ) as http,
        pytest.raises(RetrievalError, match="outside the requested"),
    ):
        ENTSOEClient(http, token="test").generation_by_type(AREA, START, END)


def test_client_does_not_relabel_partial_native_intervals_as_complete() -> None:
    with HTTPClient(
        ENTSOE_HOSTS,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=document(series()))),
    ) as http:
        result = ENTSOEClient(http, token="test").generation_by_type(
            AREA, START + timedelta(minutes=5), END - timedelta(minutes=5)
        )
    assert len(result.data) == 2
    assert result.data["timestamp"].tolist() == [START + timedelta(minutes=m) for m in (15, 30)]


def test_unit_client_chunks_daily_and_applies_total_row_limit() -> None:
    seen: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        first = datetime.strptime(request.url.params["periodStart"], "%Y%m%d%H%M").replace(
            tzinfo=UTC
        )
        seen.append(request.url.params["documentType"])
        return httpx.Response(
            200,
            text=document(
                series(
                    period(
                        point(1),
                        start=first.isoformat(),
                        end=(first + timedelta(hours=1)).isoformat(),
                    ),
                    resource=UNIT,
                ),
                document_type="A73",
            ),
        )

    with (
        HTTPClient(
            ENTSOE_HOSTS,
            config=HTTPConfig(minimum_interval_seconds=0),
            transport=httpx.MockTransport(handle),
        ) as http,
        pytest.raises(RetrievalError, match="across its chunks"),
    ):
        ENTSOEClient(http, token="test", maximum_rows=7).generation_by_unit(
            AREA, START, START + timedelta(days=2), unit_id=UNIT
        )
    assert seen == ["A73", "A73"]


def test_chunk_seam_keeps_complete_native_intervals_inside_global_range() -> None:
    requests: list[tuple[str, str]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        start = request.url.params["periodStart"]
        end = request.url.params["periodEnd"]
        requests.append((start, end))
        first = pd.Timestamp(datetime.strptime(start, "%Y%m%d%H%M")).floor("15min")
        last = pd.Timestamp(datetime.strptime(end, "%Y%m%d%H%M")).ceil("15min")
        return httpx.Response(
            200,
            text=document(
                series(
                    period(
                        point(1),
                        start=first.tz_localize("UTC").isoformat(),
                        end=last.tz_localize("UTC").isoformat(),
                    ),
                    resource=UNIT,
                ),
                document_type="A73",
            ),
        )

    with HTTPClient(
        ENTSOE_HOSTS,
        config=HTTPConfig(minimum_interval_seconds=0),
        transport=httpx.MockTransport(handle),
    ) as http:
        first = START + timedelta(minutes=5)
        result = ENTSOEClient(http, token="test").generation_by_unit(
            AREA, first, first + timedelta(days=2), unit_id=UNIT
        )
    assert len(requests) == 2
    assert requests[0][1] == requests[1][0] == "202501020005"
    expected = pd.date_range(
        START + timedelta(minutes=15),
        START + timedelta(days=2),
        freq="15min",
        inclusive="left",
    )
    assert len(result.data) == len(expected) == 191
    assert result.data["timestamp"].tolist() == expected.tolist()
    assert result.data["timestamp"].eq(START + timedelta(days=1)).sum() == 1
    assert result.data["interval_end"].iloc[-1] == START + timedelta(days=2)
