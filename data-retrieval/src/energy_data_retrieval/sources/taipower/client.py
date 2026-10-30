"""Taipower's public net-generation snapshot, preserving MW and asset scope."""

from __future__ import annotations

import math
import re
from datetime import datetime

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RetrievalError,
    array_value,
    object_value,
)

TAIPOWER_HOSTS = frozenset({"service.taipower.com.tw"})
GENERATION_ENDPOINT = "https://service.taipower.com.tw/data/opendata/apply/file/d006001/001.json"
REFERENCE_IDS = ("taipower_live_generation", "taipower_generation_history")
_COLUMNS = [
    "timestamp",
    "source",
    "area",
    "asset_id",
    "technology",
    "source_technology",
    "value",
    "unit",
    "capacity_mw",
    "aggregation",
    "is_total",
    "is_aggregate",
    "flow",
    "source_status",
    "source_datetime",
    "measurement_kind",
]


def _text(value: JSONValue, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RetrievalError(f"Taipower omitted {name}")
    return value.strip()


def _number(value: JSONValue, *, subtotal: bool = False) -> float:
    if value is None or (isinstance(value, str) and value.strip() in {"", "-", "--", "N/A"}):
        return float("nan")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise RetrievalError("Taipower power/capacity must be numeric or missing")
    if subtotal and isinstance(value, str):
        value = re.sub(r"\([0-9.]+%\)$", "", value.strip())
    try:
        result = float(value)
    except ValueError:
        raise RetrievalError("Taipower power/capacity is not numeric") from None
    if not math.isfinite(result):
        raise RetrievalError("Taipower power/capacity contains a non-finite value")
    return result


def _technology(label: str) -> str:
    for fragment, technology in (
        ("太陽", "solar"),
        ("風力", "wind"),
        ("核能", "nuclear"),
        ("燃氣", "gas"),
        ("燃煤", "coal"),
        ("燃油", "oil"),
        ("燃料油", "oil"),
        ("輕油", "oil"),
        ("儲能", "storage"),
        ("水力", "hydro"),
        ("再生", "other_renewable"),
    ):
        if fragment in label:
            return technology
    return re.sub(r"<[^>]*>", "", label)


def parse_generation(
    payload: JSONValue,
    *,
    include_aggregates: bool = False,
    include_storage_load: bool = False,
    maximum_rows: int = 20_000,
) -> pd.DataFrame:
    """Parse the actual feed, excluding subtotal/group rows and charging by default.

    The 10-minute publication cadence is not a documented averaging interval.
    Values remain power snapshots in MW; they are never converted to MWh.
    ``asset_id`` is the provider's reported label, which can denote a unit, plant
    or group. Known groups/subtotals are explicitly marked. No complete plant
    inventory or unit-to-plant registry is inferred from display names.
    """
    if type(maximum_rows) is not int or maximum_rows < 1:
        raise ValueError("maximum_rows must be a positive integer")
    root = object_value(payload)
    label = _text(root.get("DateTime"), "snapshot datetime")
    try:
        parsed = datetime.fromisoformat(label)
        stamp = pd.Timestamp(parsed)
        stamp = stamp.tz_localize("Asia/Taipei") if stamp.tzinfo is None else stamp
        stamp = stamp.tz_convert("UTC")
    except (ValueError, TypeError):
        raise RetrievalError("Taipower snapshot datetime is invalid") from None
    data = array_value(root.get("aaData"))
    if len(data) > maximum_rows:
        raise RetrievalError("Taipower response exceeds maximum_rows")
    rows: list[dict[str, object]] = []
    for value in data:
        item = object_value(value)
        asset = _text(item.get("機組名稱"), "asset name")
        category = _text(item.get("機組類型"), "technology")
        total = any(marker in asset for marker in ("小計", "合計", "總計"))
        grouped = total or any(
            marker in asset
            for marker in (
                "其它",
                "其他",
                "小水力",
                "自有地熱",
                "購電地熱",
                "生質能",
                "電池",
                "&",
                "、",
            )
        )
        flow = "consumption" if "負載" in category or "Load" in category else "generation"
        if (grouped and not include_aggregates) or (
            flow == "consumption" and not include_storage_load
        ):
            continue
        if "淨發電量(MW)" not in item or "裝置容量(MW)" not in item:
            raise RetrievalError("Taipower feed omitted its MW fields")
        rows.append(
            {
                "timestamp": stamp,
                "source": "taipower",
                "area": "TW",
                "asset_id": asset,
                "technology": _technology(category),
                "source_technology": category,
                "value": _number(item["淨發電量(MW)"], subtotal=total),
                "unit": "MW",
                "capacity_mw": _number(item["裝置容量(MW)"], subtotal=total),
                "aggregation": "technology_total"
                if total
                else "reported_group"
                if grouped
                else "reported_asset",
                "is_total": total,
                "is_aggregate": grouped,
                "flow": flow,
                "source_status": item.get("備註"),
                "source_datetime": label,
                "measurement_kind": "power_snapshot",
            }
        )
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    if frame.duplicated(["timestamp", "source_technology", "asset_id", "flow"]).any():
        raise RetrievalError("Taipower feed contains duplicate asset observations")
    return frame.sort_values(["technology", "asset_id", "flow"]).reset_index(drop=True)


class TaipowerClient:
    """Retrieve one uncached live snapshot with bounded response size and rows."""

    def __init__(self, http: HTTPClient, *, maximum_rows: int = 20_000) -> None:
        if type(maximum_rows) is not int or maximum_rows < 1:
            raise ValueError("maximum_rows must be a positive integer")
        self.http, self.maximum_rows = http, maximum_rows

    def latest(
        self, *, include_aggregates: bool = False, include_storage_load: bool = False
    ) -> GenerationResult:
        """Read the current publication; no API key is required."""
        response = self.http.get_json(GENERATION_ENDPOINT, use_cache=False)
        frame = parse_generation(
            response.value,
            include_aggregates=include_aggregates,
            include_storage_load=include_storage_load,
            maximum_rows=self.maximum_rows,
        )
        return GenerationResult(frame, (response.record,))
