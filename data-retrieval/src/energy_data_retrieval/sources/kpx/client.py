"""KPX hourly regional market-participating solar generation, in MWh."""

from __future__ import annotations

import math
import os
import re
from datetime import date, datetime, timedelta

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import HTTPClient, JSONValue, RetrievalError, object_value

KPX_HOSTS = frozenset({"apis.data.go.kr"})
GENERATION_ENDPOINT = "https://apis.data.go.kr/B552115/PvAmountByLocHr/getPvAmountByLocHr"
REFERENCE_IDS = ("kpx_regional_solar", "kpx_trading_periods", "kpx_data_guide")
_COLUMNS = [
    "timestamp",
    "interval_end",
    "source",
    "area",
    "technology",
    "value",
    "unit",
    "aggregation",
    "source_date",
    "trading_hour",
    "measurement_kind",
]


def _limit(value: int, name: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def solar_requests(
    start: date, end: date, *, page_size: int = 1000, maximum_requests: int = 100
) -> tuple[dict[str, str], ...]:
    """Plan first pages for inclusive Korean dates, without credentials.

    The client follows further pages up to maximum_requests. The plan is not a
    promise that every date fits one page or that an account has API permission.
    """
    _limit(maximum_requests, "maximum_requests")
    _limit(page_size, "page_size")
    if page_size > 1000:
        raise ValueError("page_size must be no greater than 1000")
    if type(start) is not date or type(end) is not date or end < start:
        raise ValueError("start and end must be ordered calendar dates")
    days = (end - start).days + 1
    if days > maximum_requests:
        raise ValueError("KPX interval exceeds maximum_requests before pagination")
    return tuple(
        {
            "tradeYmd": (start + timedelta(days=n)).strftime("%Y%m%d"),
            "pageNo": "1",
            "numOfRows": str(page_size),
            "dataType": "json",
        }
        for n in range(days)
    )


def _response(payload: JSONValue) -> tuple[list[JSONValue], int, int]:
    root = object_value(payload)
    root = object_value(root["response"]) if "response" in root else root
    header = object_value(root.get("header"))
    code = str(header.get("resultCode"))
    if code == "03":
        return [], 0, 1
    if code not in {"00", "0"}:
        raise RetrievalError("KPX returned an API error; verify access, key and query")
    body = object_value(root.get("body"))
    total = body.get("totalCount")
    page = body.get("pageNo")
    try:
        if isinstance(total, bool) or isinstance(page, bool):
            raise ValueError
        count, number = int(str(total)), int(str(page))
        if count < 0 or number < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise RetrievalError("KPX returned invalid pagination metadata") from None
    raw = body.get("items")
    if isinstance(raw, dict):
        raw = raw.get("item")
    if raw in (None, ""):
        items: list[JSONValue] = []
    elif isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = [raw]
    else:
        raise RetrievalError("KPX returned invalid generation items")
    if (items and count == 0) or len(items) > count:
        raise RetrievalError("KPX items disagree with its totalCount")
    return items, count, number


def parse_generation(payload: JSONValue, *, maximum_rows: int = 100_000) -> pd.DataFrame:
    """Parse one API page, retaining hourly energy and the market date.

    KPX trading hours 01..24 label the interval END: hour 01 is 00:00-01:00
    Asia/Seoul and hour 24 ends at midnight on the following civil date.
    API quantities are MWh. Missing values remain NaN; negatives and zero stay.
    Coverage is participating solar generators and may include coupled ESS.
    """
    _limit(maximum_rows, "maximum_rows")
    items, _, _ = _response(payload)
    if len(items) > maximum_rows:
        raise RetrievalError("KPX page exceeds maximum_rows")
    rows: list[dict[str, object]] = []
    for raw in items:
        item = object_value(raw)
        label, hour, region = item.get("tradeYmd"), item.get("tradeNo"), item.get("regionNm")
        if (
            not isinstance(label, str)
            or not re.fullmatch(r"\d{8}", label)
            or not isinstance(region, str)
            or not region.strip()
        ):
            raise RetrievalError("KPX row omitted its trading date or region")
        try:
            day = datetime.strptime(label, "%Y%m%d").date()
            if isinstance(hour, bool) or not isinstance(hour, (str, int)):
                raise ValueError
            number = int(hour)
            if not 1 <= number <= 24:
                raise ValueError
            begin = pd.Timestamp(day, tz="Asia/Seoul").tz_convert("UTC")
            stamp = begin + pd.Timedelta(hours=number - 1)
        except (ValueError, TypeError):
            raise RetrievalError("KPX returned an invalid trading date/hour") from None
        if "amgo" not in item:
            raise RetrievalError("KPX row omitted its generation field")
        energy = item["amgo"]
        if energy is None or energy == "":
            value = float("nan")
        else:
            if isinstance(energy, bool) or not isinstance(energy, (float, int, str)):
                raise RetrievalError("KPX generation is not numeric")
            try:
                value = float(energy)
            except ValueError:
                raise RetrievalError("KPX generation is not numeric") from None
            if not math.isfinite(value):
                raise RetrievalError("KPX generation contains a non-finite value")
        rows.append(
            {
                "timestamp": stamp,
                "interval_end": stamp + pd.Timedelta(hours=1),
                "source": "kpx",
                "area": region,
                "technology": "solar",
                "value": value,
                "unit": "MWh",
                "aggregation": "region_technology",
                "source_date": day.isoformat(),
                "trading_hour": number,
                "measurement_kind": "market_traded_net_energy",
            }
        )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    for name in ("timestamp", "interval_end"):
        frame[name] = pd.to_datetime(frame[name], utc=True)
    if frame.duplicated(["timestamp", "area"]).any():
        raise RetrievalError("KPX returned duplicate region/hour observations")
    return frame.sort_values(["timestamp", "area"]).reset_index(drop=True)


class KPXClient:
    """Bounded daily queries with complete pagination and secret-safe provenance."""

    def __init__(
        self,
        http: HTTPClient,
        *,
        api_key: str,
        maximum_requests: int = 100,
        maximum_rows: int = 100_000,
        page_size: int = 1000,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("KPX_API_KEY is required; request access through data.go.kr")
        _limit(maximum_requests, "maximum_requests")
        _limit(maximum_rows, "maximum_rows")
        _limit(page_size, "page_size")
        if page_size > 1000:
            raise ValueError("page_size must be no greater than 1000")
        self.http, self._api_key = http, api_key
        self.maximum_requests, self.maximum_rows, self.page_size = (
            maximum_requests,
            maximum_rows,
            page_size,
        )

    @classmethod
    def from_environment(
        cls,
        http: HTTPClient,
        *,
        maximum_requests: int = 100,
        maximum_rows: int = 100_000,
        page_size: int = 1000,
    ) -> KPXClient:
        """Read the decoded service key from KPX_API_KEY; never include it in plans."""
        return cls(
            http,
            api_key=os.environ.get("KPX_API_KEY", ""),
            maximum_requests=maximum_requests,
            maximum_rows=maximum_rows,
            page_size=page_size,
        )

    def solar_generation(
        self, start: date, end: date, *, region: str | None = None
    ) -> GenerationResult:
        """Retrieve all reported regions before applying an optional exact region name."""
        plans = solar_requests(
            start, end, page_size=self.page_size, maximum_requests=self.maximum_requests
        )
        if region is not None and (not isinstance(region, str) or not region.strip()):
            raise ValueError("region must be a nonempty source region name")
        records, frames = [], []
        total_rows = 0
        for plan in plans:
            page, fetched, expected = 1, 0, None
            while True:
                if len(records) >= self.maximum_requests:
                    raise RetrievalError("KPX pagination exceeds maximum_requests")
                response = self.http.get_json(
                    GENERATION_ENDPOINT,
                    plan | {"pageNo": str(page)},
                    secrets={"serviceKey": self._api_key},
                )
                items, count, actual_page = _response(response.value)
                if count + total_rows - fetched > self.maximum_rows:
                    raise RetrievalError("KPX response exceeds maximum_rows")
                if actual_page != page or (expected is not None and count != expected):
                    raise RetrievalError("KPX pagination changed or returned the wrong page")
                if count and not items:
                    raise RetrievalError("KPX pagination ended before totalCount was reached")
                frame = parse_generation(response.value, maximum_rows=self.maximum_rows)
                if (
                    not frame.empty
                    and not frame.source_date.eq(
                        datetime.strptime(plan["tradeYmd"], "%Y%m%d").date().isoformat()
                    ).all()
                ):
                    raise RetrievalError("KPX returned observations outside the requested date")
                frames.append(frame)
                records.append(response.record)
                total_rows += len(items)
                fetched += len(items)
                expected = count
                if fetched >= count:
                    if fetched != count:
                        raise RetrievalError("KPX pagination exceeded totalCount")
                    break
                page += 1
        frame = pd.concat(frames, ignore_index=True)
        if frame.duplicated(["timestamp", "area"]).any():
            raise RetrievalError("KPX returned duplicate observations across pages")
        if region is not None:
            if region not in set(frame.area):
                raise RetrievalError("Requested KPX region is absent from the interval")
            frame = frame.loc[frame.area.eq(region)]
        return GenerationResult(
            frame.sort_values(["timestamp", "area"]).reset_index(drop=True), tuple(records)
        )
