"""ENTSO-E actual generation, with UTC intervals and explicit consumption flows.

The Transparency Platform reports interval-average power in MW. A03 points are
step changes, not a sparse list of independent samples. Missing quantities remain
missing, including when the missing block extends across several positions.
"""

from __future__ import annotations

import math
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pandas as pd

from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError

ENTSOE_ENDPOINT = "https://web-api.tp.entsoe.eu/api"
ENTSOE_HOSTS = frozenset({"web-api.tp.entsoe.eu"})
REFERENCE_IDS = (
    "entsoe_transparency_api",
    "entsoe_generation_data_descriptions",
    "entsoe_curve_types",
)
PSR_TYPES = {
    "B01": "Biomass",
    "B02": "Fossil Brown coal/Lignite",
    "B03": "Fossil Coal-derived gas",
    "B04": "Fossil Gas",
    "B05": "Fossil Hard coal",
    "B06": "Fossil Oil",
    "B07": "Fossil Oil shale",
    "B08": "Fossil Peat",
    "B09": "Geothermal",
    "B10": "Hydro Pumped Storage",
    "B11": "Hydro Run-of-river and poundage",
    "B12": "Hydro Water Reservoir",
    "B13": "Marine",
    "B14": "Nuclear",
    "B15": "Other renewable",
    "B16": "Solar",
    "B17": "Waste",
    "B18": "Wind Offshore",
    "B19": "Wind Onshore",
    "B20": "Other",
    "B25": "Energy storage",
}
_COLUMNS = (
    "timestamp",
    "interval_end",
    "duration_hours",
    "source",
    "area",
    "unit_id",
    "unit_name",
    "technology",
    "technology_name",
    "flow",
    "value",
    "unit",
    "native_unit",
    "document_type",
    "document_id",
    "revision",
    "series_id",
    "curve_type",
    "business_type",
    "missing_reason",
)
_KEYS = ["timestamp", "area", "unit_id", "technology", "flow"]
_DURATION = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?\Z")


def _integer(value: int, label: str, maximum: int) -> None:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer in 1..{maximum}")


def _eic(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Z0-9-]{16}", value) is None:
        raise ValueError("Use a 16-character EIC from ENTSO-E's official area or unit list")
    return value


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("ENTSO-E boundaries must be timezone-aware datetimes")
    if value.second or value.microsecond:
        raise ValueError("ENTSO-E request boundaries must align to whole minutes")
    return value.astimezone(UTC)


def generation_requests(
    area: str,
    start: datetime,
    end: datetime,
    *,
    per_unit: bool = False,
    psr_type: str | None = None,
    unit_id: str | None = None,
    maximum_requests: int = 366,
) -> tuple[dict[str, str], ...]:
    """Plan non-secret requests for ``[start, end)`` in UTC.

    Aggregate queries use conservative 31-day chunks; per-unit queries use one-day
    chunks. EICs are explicit because countries and bidding zones are not always
    interchangeable. This function makes no network requests.
    """
    _eic(area)
    _integer(maximum_requests, "maximum_requests", 10000)
    first, last = _utc(start), _utc(end)
    if first >= last:
        raise ValueError("ENTSO-E end must be strictly after start (exclusive end)")
    if psr_type is not None and psr_type not in PSR_TYPES:
        raise ValueError("psr_type must be a supported ENTSO-E PSR code, for example B16")
    if unit_id is not None:
        _eic(unit_id)
        if not per_unit:
            raise ValueError("unit_id is only valid for generation per unit")
    step = timedelta(days=1 if per_unit else 31)
    if math.ceil((last - first) / step) > maximum_requests:
        raise ValueError("ENTSO-E date range exceeds maximum_requests; request a smaller range")
    requests: list[dict[str, str]] = []
    cursor = first
    while cursor < last:
        chunk_end = cursor + min(step, last - cursor)
        parameters = {
            "documentType": "A73" if per_unit else "A75",
            "processType": "A16",
            "in_Domain": area,
            "periodStart": cursor.strftime("%Y%m%d%H%M"),
            "periodEnd": chunk_end.strftime("%Y%m%d%H%M"),
        }
        if psr_type is not None:
            parameters["psrType"] = psr_type
        if unit_id is not None:
            parameters["registeredResource"] = unit_id
        requests.append(parameters)
        cursor = chunk_end
    return tuple(requests)


def _text(element: ET.Element, path: str, *, required: bool = False) -> str:
    found = element.find("/".join("{*}" + name for name in path.split("/")))
    result = found.text.strip() if found is not None and found.text else ""
    if required and not result:
        raise RetrievalError(f"ENTSO-E document lacks required {path}")
    return result


def _stamp(value: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() != timedelta(0):
            raise ValueError
        return stamp.astimezone(UTC)
    except (ValueError, OverflowError):
        raise RetrievalError("ENTSO-E XML time boundaries must be valid UTC timestamps") from None


def _resolution(value: str) -> timedelta:
    match = _DURATION.fullmatch(value)
    if match is None or not any(match.groups()):
        raise RetrievalError("ENTSO-E has an unsupported fixed-duration resolution")
    days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds
    if not 1 <= total <= 86400:
        raise RetrievalError("ENTSO-E generation resolution must be between one second and one day")
    return timedelta(seconds=total)


def _empty(*, no_data: bool = False) -> pd.DataFrame:
    frame = pd.DataFrame(columns=list(_COLUMNS))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["interval_end"] = pd.to_datetime(frame["interval_end"], utc=True)
    frame["value"] = frame["value"].astype(float)
    frame["duration_hours"] = frame["duration_hours"].astype(float)
    frame.attrs.update(
        source="entsoe",
        no_data=no_data,
        timestamp_convention="interval_start",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


def _deduplicate(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop equal repeats; never silently sum revised or overlapping observations."""
    compare = [*_KEYS, "interval_end", "value", "missing_reason"]
    result = frame.drop_duplicates(compare)
    if result.duplicated(_KEYS).any():
        raise RetrievalError("ENTSO-E returned conflicting duplicate or overlapping intervals")
    result = result.sort_values(_KEYS).reset_index(drop=True)
    for _, group in result.groupby(_KEYS[1:], sort=False, dropna=False):
        if (
            group["timestamp"].iloc[1:].to_numpy() < group["interval_end"].iloc[:-1].to_numpy()
        ).any():
            raise RetrievalError(
                "ENTSO-E returned overlapping intervals with different resolutions"
            )
    return result


def normalize_generation(
    xml: str | bytes,
    *,
    maximum_rows: int = 1_000_000,
    maximum_bytes: int = 32 * 1024 * 1024,
) -> pd.DataFrame:
    """Parse an A75/A73 realised-generation XML document without network access.

    A01 absent positions are represented by NaN. A03 changes are expanded only
    within their own Period; an explicit missing quantity stops the prior value.
    Generation and consumption remain separate positive/negative-as-published
    flows. Values are never clipped, imputed, or summed across these flows.

    An acknowledgement with reason 999 and the provider's explicit no-matching-
    data message returns an empty frame. Other acknowledgements fail, without
    echoing provider text that might contain credential-bearing request URLs.
    """
    _integer(maximum_rows, "maximum_rows", 10_000_000)
    _integer(maximum_bytes, "maximum_bytes", 256 * 1024 * 1024)
    raw = xml.encode("utf-8") if isinstance(xml, str) else xml
    if len(raw) > maximum_bytes:
        raise RetrievalError("ENTSO-E XML exceeded the configured byte limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise RetrievalError("ENTSO-E XML must use UTF-8 encoding") from None
    # Generation exports need neither DTDs nor entities. Refuse both before parsing.
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper() or "\x00" in text:
        raise RetrievalError("ENTSO-E XML must not contain a DTD or entity declaration")
    try:
        root = ET.fromstring(text)
    except (ET.ParseError, ValueError):
        raise RetrievalError(
            "ENTSO-E returned invalid XML; compressed exports are unsupported"
        ) from None
    name = root.tag.rsplit("}", 1)[-1]
    if name == "Acknowledgement_MarketDocument":
        reasons = root.findall("{*}Reason")
        if reasons and all(
            _text(reason, "code") == "999" and "no matching data" in _text(reason, "text").lower()
            for reason in reasons
        ):
            return _empty(no_data=True)
        raise RetrievalError("ENTSO-E rejected the query; check token, area, dates and parameters")
    document_type = _text(root, "type", required=True)
    if (
        name != "GL_MarketDocument"
        or document_type not in {"A73", "A75"}
        or _text(root, "process.processType", required=True) != "A16"
    ):
        raise RetrievalError("Expected ENTSO-E realised generation document A73 or A75 / A16")
    document_id = _text(root, "mRID", required=True)
    revision = _text(root, "revisionNumber", required=True)
    rows: list[dict[str, object]] = []
    series_list = root.findall("{*}TimeSeries")
    if not series_list:
        raise RetrievalError("ENTSO-E generation document contains no TimeSeries")
    for series in series_list:
        if _text(series, "cancelledTS"):
            raise RetrievalError("ENTSO-E returned a cancelled TimeSeries; inspect its revision")
        curve = _text(series, "curveType", required=True)
        if curve not in {"A01", "A03"}:
            raise RetrievalError("ENTSO-E generation supports A01 and A03 curves only")
        native_unit = _text(series, "quantity_Measure_Unit.name", required=True)
        if native_unit != "MAW":
            raise RetrievalError("ENTSO-E generation must use the native MAW (MW) unit")
        in_area = _text(series, "inBiddingZone_Domain.mRID")
        out_area = _text(series, "outBiddingZone_Domain.mRID")
        if bool(in_area) == bool(out_area):
            raise RetrievalError("ENTSO-E generation requires one unambiguous in/out domain")
        area = in_area or out_area
        technology = _text(series, "MktPSRType/psrType", required=True)
        resource = "MktPSRType/PowerSystemResources/"
        unit_id = _text(series, resource + "mRID")
        if document_type == "A73" and not unit_id:
            raise RetrievalError("ENTSO-E per-unit generation lacks its resource EIC")
        base: dict[str, object] = {
            "source": "entsoe",
            "area": area,
            "unit_id": unit_id,
            "unit_name": _text(series, resource + "name"),
            "technology": technology,
            "technology_name": PSR_TYPES.get(technology, technology),
            "flow": "generation" if in_area else "consumption",
            "unit": "MW",
            "native_unit": native_unit,
            "document_type": document_type,
            "document_id": document_id,
            "revision": revision,
            "series_id": _text(series, "mRID", required=True),
            "curve_type": curve,
            "business_type": _text(series, "businessType"),
        }
        periods = series.findall("{*}Period")
        if not periods:
            raise RetrievalError("ENTSO-E TimeSeries contains no Period")
        for period in periods:
            first = _stamp(_text(period, "timeInterval/start", required=True))
            last = _stamp(_text(period, "timeInterval/end", required=True))
            step = _resolution(_text(period, "resolution", required=True))
            count, remainder = divmod(last - first, step)
            if count < 1 or remainder != timedelta(0):
                raise RetrievalError("ENTSO-E Period boundaries do not match its resolution")
            if len(rows) + count > maximum_rows:
                raise RetrievalError("ENTSO-E expanded data exceeded maximum_rows")
            points: dict[int, tuple[float, str]] = {}
            for point in period.findall("{*}Point"):
                try:
                    position = int(_text(point, "position", required=True))
                except ValueError:
                    raise RetrievalError("ENTSO-E Point has an invalid position") from None
                if not 1 <= position <= count or position in points:
                    raise RetrievalError(
                        "ENTSO-E Point position is duplicated or outside its Period"
                    )
                quantity = _text(point, "quantity")
                reason = _text(point, "Reason/code")
                if quantity:
                    try:
                        value = float(quantity)
                    except ValueError:
                        raise RetrievalError(
                            "ENTSO-E Point contains a nonnumeric quantity"
                        ) from None
                    if not math.isfinite(value):
                        raise RetrievalError("ENTSO-E Point contains a non-finite quantity")
                    points[position] = value, reason
                else:
                    points[position] = math.nan, reason or "not_provided"
            current = (math.nan, "not_provided")
            for position in range(1, count + 1):
                if curve == "A01":
                    current = points.get(position, (math.nan, "not_provided"))
                elif position in points:
                    current = points[position]
                timestamp = first + (position - 1) * step
                rows.append(
                    base
                    | {
                        "timestamp": timestamp,
                        "interval_end": timestamp + step,
                        "duration_hours": step.total_seconds() / 3600,
                        "value": current[0],
                        "missing_reason": current[1],
                    }
                )
    frame = _deduplicate(pd.DataFrame(rows, columns=list(_COLUMNS)))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["interval_end"] = pd.to_datetime(frame["interval_end"], utc=True)
    frame.attrs.update(
        source="entsoe",
        no_data=False,
        timestamp_convention="interval_start",
        quantity="interval_average_net_power",
        missing_values_filled=False,
        a03_expansion="constant blocks within each Period; explicit missing blocks preserved",
        reference_ids=list(REFERENCE_IDS),
    )
    return frame


@dataclass(frozen=True, slots=True)
class ENTSOEGeneration:
    """Long-form interval-average power and sanitized HTTP request provenance."""

    data: pd.DataFrame
    requests: tuple[RequestRecord, ...]


@dataclass(slots=True)
class ENTSOEClient:
    """Authenticated actual-generation retrieval; never requests forecasts."""

    http: HTTPClient
    token: str = field(default="", repr=False)
    maximum_requests: int = 366
    maximum_rows: int = 1_000_000

    def __post_init__(self) -> None:
        _integer(self.maximum_requests, "maximum_requests", 10000)
        _integer(self.maximum_rows, "maximum_rows", 10_000_000)

    @classmethod
    def from_environment(cls, http: HTTPClient) -> ENTSOEClient:
        return cls(http=http, token=os.environ.get("ENTSOE_API_TOKEN", ""))

    def generation_by_type(
        self,
        area: str,
        start: datetime,
        end: datetime,
        *,
        psr_type: str | None = None,
    ) -> ENTSOEGeneration:
        """Actual generation per production type (A75/A16), with consumption separate."""
        return self._generation(area, start, end, psr_type=psr_type)

    def generation_by_unit(
        self,
        area: str,
        start: datetime,
        end: datetime,
        *,
        psr_type: str | None = None,
        unit_id: str | None = None,
    ) -> ENTSOEGeneration:
        """Actual generation per unit (A73/A16), queried in one-day chunks."""
        return self._generation(area, start, end, per_unit=True, psr_type=psr_type, unit_id=unit_id)

    def _generation(
        self,
        area: str,
        start: datetime,
        end: datetime,
        *,
        per_unit: bool = False,
        psr_type: str | None = None,
        unit_id: str | None = None,
    ) -> ENTSOEGeneration:
        planned = generation_requests(
            area,
            start,
            end,
            per_unit=per_unit,
            psr_type=psr_type,
            unit_id=unit_id,
            maximum_requests=self.maximum_requests,
        )
        if not self.token:
            raise ValueError("ENTSOE_API_TOKEN must contain a personal token with API access")
        first, last = _utc(start), _utc(end)
        frames: list[pd.DataFrame] = []
        records: list[RequestRecord] = []
        row_count = 0
        for parameters in planned:
            response = self.http.get_text(
                ENTSOE_ENDPOINT,
                parameters,
                secrets={"securityToken": self.token},
                use_cache=False,
            )
            frame = normalize_generation(response.value, maximum_rows=self.maximum_rows)
            if not frame.empty:
                if (
                    not frame["area"].eq(area).all()
                    or not frame["document_type"].eq(parameters["documentType"]).all()
                    or (psr_type is not None and not frame["technology"].eq(psr_type).all())
                    or (unit_id is not None and not frame["unit_id"].eq(unit_id).all())
                ):
                    raise RetrievalError(
                        "ENTSO-E returned data outside the requested area or resource"
                    )
                # Clip only to the caller's outer boundaries. ENTSO-E may
                # return whole MTUs overlapping an artificial chunk seam;
                # clipping to each chunk would discard such an MTU twice.
                # Equal overlap is removed once when all chunks are combined.
                frame = frame.loc[
                    (frame["timestamp"] >= first) & (frame["interval_end"] <= last)
                ].copy()
                row_count += len(frame)
                if row_count > self.maximum_rows:
                    raise RetrievalError("ENTSO-E query exceeded maximum_rows across its chunks")
                if not frame.empty:
                    frames.append(frame)
            records.append(response.record)
        result = (
            _deduplicate(pd.concat(frames, ignore_index=True)) if frames else _empty(no_data=True)
        )
        result.attrs.update(
            source="entsoe",
            timestamp_convention="interval_start",
            quantity="interval_average_net_power",
            requested_start_utc=first.isoformat(),
            requested_end_utc=last.isoformat(),
            interval_selection="only whole native intervals contained in the requested range",
            reference_ids=list(REFERENCE_IDS),
        )
        return ENTSOEGeneration(result, tuple(records))
