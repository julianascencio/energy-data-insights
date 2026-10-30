"""AESO net generation, with capacity and contingency reserve kept separate."""

from __future__ import annotations

import hashlib
import io
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RetrievalError,
    array_value,
    object_value,
)

AESO_HOSTS = frozenset({"apimgw.aeso.ca"})
CURRENT_ENDPOINT = (
    "https://apimgw.aeso.ca/public/currentsupplydemand-api/v1/csd/generation/assets/current"
)
REFERENCE_IDS = ("aeso_historical_generation", "aeso_current_generation_api")
_MST = timezone(timedelta(hours=-7))
_ASSET = re.compile(r"[A-Za-z0-9_-]{1,32}")


def _limit(value: int, name: str, upper: int) -> None:
    if type(value) is not int or not 1 <= value <= upper:
        raise ValueError(f"{name} must be an integer in 1..{upper}")


def _number(value: JSONValue) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise RetrievalError("AESO measurements must be finite numbers or null")
    return float(value)


def _text(value: JSONValue, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RetrievalError(f"AESO omitted {label}")
    return value.strip()


def _finish(frame: pd.DataFrame, *, aggregation: str) -> pd.DataFrame:
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["value"] = frame["value"].astype(float)
    frame["source"] = "aeso"
    frame["area"] = "Alberta"
    frame["unit"] = "MW"
    frame["aggregation"] = aggregation
    frame["quality"] = frame["value"].map(
        lambda value: "missing" if pd.isna(value) else "operational_net_generation"
    )
    frame = frame.drop_duplicates()
    if frame.duplicated(["timestamp", "unit_id"]).any():
        raise RetrievalError("AESO conflicting asset/timestamp observations")
    frame = frame.sort_values(["timestamp", "unit_id"]).reset_index(drop=True)
    frame.attrs.update(
        reference_ids=list(REFERENCE_IDS),
        missing_policy="Null/blank generation remains missing; negative net output is preserved",
        scope="AESO current supply-demand reporting assets, not all distributed generation",
        timestamp_semantics="Published time label converted to UTC without shifting",
    )
    return frame


def parse_current_generation(payload: JSONValue, *, maximum_rows: int = 100_000) -> pd.DataFrame:
    """Parse the official Current Supply Demand v1 asset response in MW.

    ``last_updated_datetime_utc`` is authoritative; the MPT display time is
    retained separately. Current readings are snapshots, not interval energy.
    Maximum capability and dispatched contingency reserve are separate fields.
    """
    _limit(maximum_rows, "maximum_rows", 10_000_000)
    root = object_value(payload)
    label = _text(root.get("last_updated_datetime_utc"), "last_updated_datetime_utc")
    try:
        stamp = datetime.strptime(label, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
    except ValueError:
        raise RetrievalError("AESO current report has an invalid UTC timestamp") from None
    assets = array_value(root.get("asset_list"))
    if len(assets) > maximum_rows:
        raise RetrievalError("AESO response exceeds maximum_rows")
    rows: list[dict[str, object]] = []
    for item in assets:
        asset = object_value(item)
        if "net_generation" not in asset:
            raise RetrievalError("AESO asset omitted net_generation")
        rows.append(
            {
                "timestamp": stamp,
                "source_datetime_mpt": root.get("last_updated_datetime_mpt"),
                "unit_id": _text(asset.get("asset"), "asset"),
                "technology": _text(asset.get("fuel_type"), "fuel_type"),
                "sub_fuel_type": asset.get("sub_fuel_type"),
                "value": _number(asset["net_generation"]),
                "maximum_capability_mw": _number(asset.get("maximum_capability")),
                "dispatched_contingency_reserve_mw": _number(
                    asset.get("dispatched_contingency_reserve")
                ),
            }
        )
    frame = pd.DataFrame(
        rows,
        columns=[
            "timestamp",
            "source_datetime_mpt",
            "unit_id",
            "technology",
            "sub_fuel_type",
            "value",
            "maximum_capability_mw",
            "dispatched_contingency_reserve_mw",
        ],
    )
    frame = _finish(frame, aggregation="snapshot")
    frame.attrs["source_timezone"] = "UTC (explicit source field)"
    return frame


def parse_generation_csv(
    payload: str, *, interval_minutes: int = 60, maximum_rows: int = 1_000_000
) -> pd.DataFrame:
    """Parse a native AESO CSD Generation historical CSV; Volume is mean MW.

    The caller must identify the source export as hourly (60) or five-minute (5).
    The explicit ``Date (MST)`` column uses fixed UTC-07 throughout the year;
    ``Date (MPT)`` is retained and never guessed across daylight-saving folds.
    Native capability fields remain separate from actual ``Volume``.
    """
    _limit(maximum_rows, "maximum_rows", 10_000_000)
    if type(interval_minutes) is not int or interval_minutes not in {5, 60}:
        raise ValueError("interval_minutes must identify the native five-minute or hourly export")
    try:
        native = pd.read_csv(
            io.StringIO(payload), dtype=str, keep_default_na=False, nrows=maximum_rows + 1
        )
    except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError):
        raise RetrievalError("AESO returned malformed native CSV") from None
    required = {"Date (MST)", "Date (MPT)", "Asset Short Name", "Asset Name", "Volume", "Fuel Type"}
    if not required <= set(native.columns):
        raise RetrievalError("AESO CSV lacks native CSD Generation columns")
    if len(native) > maximum_rows:
        raise RetrievalError("AESO CSV exceeds maximum_rows")
    if (
        native["Asset Short Name"].str.strip().eq("").any()
        or native["Fuel Type"].str.strip().eq("").any()
    ):
        raise RetrievalError("AESO CSV omitted asset or fuel identifiers")
    try:
        stamp = pd.to_datetime(native["Date (MST)"], format="%Y-%m-%d %H:%M:%S", errors="raise")
        if not stamp.dt.second.eq(0).all() or not stamp.dt.minute.mod(interval_minutes).eq(0).all():
            raise ValueError("Unexpected interval")
        native["timestamp"] = stamp.dt.tz_localize(_MST).dt.tz_convert("UTC")
        for column in ["Volume", "Maximum Capability", "System Capability"]:
            if column not in native:
                continue
            native[column] = pd.to_numeric(native[column].replace("", float("nan")), errors="raise")
            if native[column].dropna().isin([float("inf"), float("-inf")]).any():
                raise ValueError("Infinite measurement")
    except (ValueError, TypeError):
        raise RetrievalError(
            "AESO CSV contains invalid fixed-MST labels or numeric values"
        ) from None
    native["unit_id"] = native["Asset Short Name"]
    native["technology"] = native["Fuel Type"]
    native["value"] = native["Volume"]
    native["interval_minutes"] = interval_minutes
    frame = _finish(native, aggregation=f"{interval_minutes}_minute_mean")
    frame.attrs.update(source_timezone="UTC-07:00 (fixed MST)", native_value_column="Volume")
    return frame


@dataclass(slots=True)
class AESOClient:
    """Current API retrieval plus bounded import of AESO's public historical CSV."""

    http: HTTPClient
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        _limit(self.maximum_rows, "maximum_rows", 10_000_000)

    def current_generation(
        self, *, api_key: str, asset_ids: list[str] | None = None
    ) -> GenerationResult:
        """Fetch one current report. AESO account and free API subscription required.

        Secrets travel only in ``API-KEY`` and are excluded from provenance.
        No repeated polling or historical availability is implied by this method.
        """
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("An AESO API subscription key is required")
        if asset_ids is not None and (
            not 1 <= len(asset_ids) <= 20
            or any(not isinstance(x, str) or not _ASSET.fullmatch(x) for x in asset_ids)
        ):
            raise ValueError("AESO accepts 1..20 alphanumeric asset_ids")
        parameters = {} if asset_ids is None else {"assetIds": ",".join(asset_ids)}
        response = self.http.get_json(
            CURRENT_ENDPOINT,
            parameters,
            secret_headers={"API-KEY": api_key},
            use_cache=False,
        )
        frame = parse_current_generation(response.value, maximum_rows=self.maximum_rows)
        if asset_ids is not None and set(asset_ids) - set(frame["unit_id"]):
            raise RetrievalError(
                "AESO returned no current data for one or more requested asset_ids"
            )
        if asset_ids is not None:
            frame = frame.loc[frame["unit_id"].isin(asset_ids)].reset_index(drop=True)
        return GenerationResult(frame, (response.record,))

    def from_native_file(
        self, path: Path, *, interval_minutes: int = 60, maximum_bytes: int = 64 * 1024 * 1024
    ) -> GenerationResult:
        """Import a user-downloaded historical CSV with a bounded read and SHA-256.

        The public AESO Box archive serves ZIP downloads through changing
        redirect hosts. This method accepts an extracted native CSV and does
        not pretend that it performed an HTTP acquisition (requests is empty).
        """
        _limit(maximum_bytes, "maximum_bytes", 1024 * 1024 * 1024)
        with Path(path).open("rb") as stream:
            raw = stream.read(maximum_bytes + 1)
        if len(raw) > maximum_bytes:
            raise RetrievalError("AESO native file exceeds maximum_bytes")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise RetrievalError("AESO native file must be UTF-8 CSV") from None
        frame = parse_generation_csv(
            text, interval_minutes=interval_minutes, maximum_rows=self.maximum_rows
        )
        frame.attrs.update(
            local_file_sha256=hashlib.sha256(raw).hexdigest(),
            local_file_size_bytes=len(raw),
            acquisition="caller_supplied_native_csv",
        )
        return GenerationResult(frame, ())
