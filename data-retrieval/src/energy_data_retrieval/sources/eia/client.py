"""Bounded EIA API v2 and public EIA-930 generation retrieval.

EIA-930 hourly labels denote the **end** of an hour. API ``frequency=hourly``
uses UTC; ``local-hourly`` is deliberately not requested. Energy is retained in
MWh, with a separate interval start. Monthly plant data keep their reporting
month and every fuel/prime-mover dimension; month labels are not SCADA samples.
"""

from __future__ import annotations

import csv
import io
import math
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from energy_data_retrieval.transport import (
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    array_value,
    object_value,
)

EIA_HOSTS = frozenset({"api.eia.gov", "www.eia.gov"})
REFERENCE_IDS = ("eia_api_v2", "eia_930", "eia_930_source_codes", "eia_930_instructions")
HOURLY_GENERATION_ENDPOINT = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
MONTHLY_GENERATION_ENDPOINT = "https://api.eia.gov/v2/electricity/facility-fuel/data/"
_BALANCE_ROOT = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles"
BALANCE_CATALOGUE_ENDPOINT = _BALANCE_ROOT + "/EIA930_File_List_Meta.csv"
_HOUR = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}\Z")
_MONTH = re.compile(r"\d{4}-\d{2}\Z")
_CODE = re.compile(r"[A-Za-z0-9_+.-]{1,32}\Z")
_MISSING = frozenset({"", "--", "NA", "(NA)", "W", "(W)", "NM", "(NM)", "(s)", "(S)"})
_HOURLY_KEYS = ("period", "respondent", "fueltype")
_MONTHLY_KEYS = ("period", "plantCode", "fuel2002", "fuelType", "primeMover")
_BALANCE_FUELS = {
    "Coal": ("COL", "Coal"),
    "Natural Gas": ("NG", "Natural gas"),
    "Nuclear": ("NUC", "Nuclear"),
    "All Petroleum Products": ("OIL", "Petroleum"),
    "Hydropower and Pumped Storage": ("WAT", "Hydro"),
    "Hydropower Excluding Pumped Storage": ("WAT", "Hydro excluding pumped storage"),
    "Pumped Storage": ("PS", "Pumped storage"),
    "Solar": ("SUN", "Solar"),
    "Solar without Integrated Battery Storage": ("SUN", "Solar without integrated battery storage"),
    "Solar with Integrated Battery Storage": ("SNB", "Solar with integrated battery storage"),
    "Wind": ("WND", "Wind"),
    "Wind without Integrated Battery Storage": ("WND", "Wind without integrated battery storage"),
    "Wind with Integrated Battery Storage": ("WNB", "Wind with integrated battery storage"),
    "Other Fuel Sources": ("OTH", "Other"),
    "Unknown Fuel Sources": ("UNK", "Unknown"),
    "Battery Storage": ("BAT", "Battery storage"),
    "Other Energy Storage": ("OES", "Other energy storage"),
    "Unknown Energy Storage": ("UES", "Unknown energy storage"),
    "Geothermal": ("GEO", "Geothermal"),
}


@dataclass(frozen=True, slots=True)
class EIAResult:
    """Normalized observations and sanitized request provenance for all pages."""

    frame: pd.DataFrame
    requests: tuple[RequestRecord, ...]


def _integer(value: JSONValue, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise RetrievalError(f"EIA {label} is not a nonnegative integer")
    if isinstance(value, str) and not re.fullmatch(r"\d+", value):
        raise RetrievalError(f"EIA {label} is not a nonnegative integer")
    result = int(value)
    if result < 0:
        raise RetrievalError(f"EIA {label} is not a nonnegative integer")
    return result


def _codes(values: Sequence[str], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not 1 <= len(values) <= 200:
        raise ValueError(f"{name} must contain between 1 and 200 explicit source codes")
    if any(not isinstance(value, str) or not _CODE.fullmatch(value) for value in values):
        raise ValueError(f"{name} contains an invalid source code")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} contains duplicate source codes")
    return tuple(values)


def _utc_hour(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("EIA hourly bounds require timezone-aware datetimes")
    utc = value.astimezone(UTC)
    if utc.minute or utc.second or utc.microsecond:
        raise ValueError("EIA hourly bounds must fall exactly on UTC hour boundaries")
    return utc.strftime("%Y-%m-%dT%H")


def _month(value: str) -> str:
    if not isinstance(value, str) or not _MONTH.fullmatch(value):
        raise ValueError("EIA monthly bounds must use YYYY-MM")
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ValueError("EIA monthly bounds must be valid calendar months") from None
    return value


def _source_string(row: dict[str, JSONValue], name: str) -> str:
    value = row.get(name)
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value):
        raise RetrievalError(f"EIA generation row is missing {name}")
    return str(value)


def _number(value: JSONValue) -> tuple[float, str]:
    if value is None or (isinstance(value, str) and value.strip() in _MISSING):
        return np.nan, "missing_or_suppressed"
    if isinstance(value, bool) or not isinstance(value, (str, float, int)):
        raise RetrievalError("EIA generation contains an invalid numeric value")
    try:
        number = float(value)
    except ValueError:
        raise RetrievalError(
            "EIA generation contains an unknown numeric or missing-value code"
        ) from None
    if not math.isfinite(number):
        raise RetrievalError("EIA generation contains a non-finite numeric value")
    return number, "reported"


def _energy_unit(value: JSONValue) -> str:
    if not isinstance(value, str) or value.lower().replace(" ", "") not in {
        "megawatthours",
        "megawatthour",
        "mwh",
    }:
        raise RetrievalError("EIA returned an unexpected generation unit; MWh is required")
    return value


def _finish(rows: list[dict[str, object]], *, monthly: bool) -> pd.DataFrame:
    source_keys = list(_MONTHLY_KEYS if monthly else _HOURLY_KEYS)
    columns = list(
        dict.fromkeys(
            [
                *source_keys,
                "timestamp",
                "source",
                "area",
                "unit_id",
                "technology",
                "value",
                "unit",
                "source_value",
                "source_unit",
                "status",
                *(["reporting_month"] if monthly else ["interval_start_utc", "interval_end_utc"]),
            ]
        )
    )
    frame = pd.DataFrame(rows) if rows else pd.DataFrame(columns=columns)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["value"] = frame["value"].astype("float64")
    if not monthly:
        frame["interval_end_utc"] = frame["timestamp"]
        frame["interval_start_utc"] = frame["timestamp"] - pd.Timedelta(hours=1)
    if not frame.empty:
        conflicting = frame.groupby(source_keys, dropna=False)["source_value"].nunique(dropna=False)
        if bool((conflicting > 1).any()):
            raise RetrievalError("Conflicting EIA generation observations require reconciliation")
        frame = frame.drop_duplicates(source_keys).sort_values(source_keys).reset_index(drop=True)
    frame.attrs.update(
        source="U.S. Energy Information Administration",
        reference_ids=list(REFERENCE_IDS),
        unit="MWh",
        aggregation_level="plant_fuel_prime_mover" if monthly else "balancing_authority_or_region",
        timestamp_convention=(
            "UTC month label only; no submonthly timing inferred"
            if monthly
            else "UTC interval end; interval_start_utc is one hour earlier"
        ),
        missing_data="Missing/suppressed values remain NaN; zero and negative values remain",
        aggregate_warning=(
            "ALL fuel/prime-mover rows overlap detailed rows; select one aggregation level"
            if monthly
            else "Regional and US48 respondents overlap individual balancing authorities"
        ),
    )
    return frame


def normalize_hourly_generation(rows: Sequence[JSONValue]) -> pd.DataFrame:
    """Normalize API fuel-type rows with UTC hour-ending labels and MWh units.

    Original API fields are retained, except ``value`` becomes numeric and its
    untouched representation is retained as ``source_value``. Exact duplicate
    keys collapse; conflicting values fail. No missing hours are filled.
    """
    result: list[dict[str, object]] = []
    for raw in rows:
        row = object_value(raw)
        labels = {key: _source_string(row, key) for key in _HOURLY_KEYS}
        period = labels["period"]
        if not _HOUR.fullmatch(period):
            raise RetrievalError("EIA hourly period must be a UTC YYYY-MM-DDTHH label")
        try:
            timestamp = datetime.strptime(period, "%Y-%m-%dT%H").replace(tzinfo=UTC)
        except ValueError:
            raise RetrievalError("EIA returned an invalid hourly calendar label") from None
        if "value" not in row:
            raise RetrievalError("EIA generation row is missing value")
        number, status = _number(row["value"])
        unit = _energy_unit(row.get("value-units"))
        result.append(
            {
                **row,
                **labels,
                "timestamp": timestamp,
                "source": "EIA",
                "area": labels["respondent"],
                "unit_id": "",
                "technology": row.get("type-name") or labels["fueltype"],
                "value": number,
                "unit": "MWh",
                "source_value": row["value"],
                "source_unit": unit,
                "status": status,
            }
        )
    return _finish(result, monthly=False)


def normalize_monthly_generation(rows: Sequence[JSONValue]) -> pd.DataFrame:
    """Normalize plant/fuel/prime-mover monthly net generation without aggregation.

    ``timestamp`` is a UTC month label for indexing, not an assertion about the
    plant's reporting timezone. ``reporting_month`` retains the source label.
    Aggregated ``ALL`` categories remain explicitly visible and must not be
    summed with their detail rows. These records are not individual generators.
    """
    result: list[dict[str, object]] = []
    for raw in rows:
        row = object_value(raw)
        labels = {key: _source_string(row, key) for key in _MONTHLY_KEYS}
        try:
            period = _month(labels["period"])
        except ValueError:
            raise RetrievalError("EIA returned an invalid monthly calendar label") from None
        if "generation" not in row:
            raise RetrievalError("EIA plant row is missing generation")
        number, status = _number(row["generation"])
        unit = _energy_unit(row.get("generation-units"))
        result.append(
            {
                **row,
                **labels,
                "timestamp": datetime.strptime(period, "%Y-%m").replace(tzinfo=UTC),
                "reporting_month": period,
                "source": "EIA",
                "area": row.get("state") or "US",
                "unit_id": labels["plantCode"],
                "technology": row.get("fuelTypeDescription") or labels["fuelType"],
                "value": number,
                "unit": "MWh",
                "source_value": row["generation"],
                "source_unit": unit,
                "status": status,
            }
        )
    return _finish(result, monthly=True)


def balance_file_url(year: int, half: int) -> str:
    """Official public six-month EIA-930 balance file URL (no API key)."""
    if (
        type(year) is not int
        or not 2015 <= year <= 9998
        or type(half) is not int
        or half not in (1, 2)
    ):
        raise ValueError("Use an EIA-930 year from 2015 and half 1 or 2")
    if year == 2015 and half == 1:
        raise ValueError("EIA-930 starts in July 2015")
    return f"{_BALANCE_ROOT}/EIA930_BALANCE_{year}_{'Jan_Jun' if half == 1 else 'Jul_Dec'}.csv"


def parse_balance_csv(
    text: str,
    *,
    respondents: Sequence[str] | None = None,
    fuel_types: Sequence[str] | None = None,
    maximum_rows: int = 500_000,
) -> pd.DataFrame:
    """Parse reported fuel generation from a public EIA-930 six-month balance CSV.

    Uses native ``UTC Time at End of Hour`` and only unadjusted fuel columns.
    Source headers label hourly average power as MW. Multiplication by the
    explicit one-hour interval gives MWh; ``source_unit`` retains ``MW``.
    Imputed, adjusted, demand, interchange and total-generation columns are not
    mixed into the fuel series. Missing fuels are not inferred as zero.
    """
    selected = _codes(respondents, "respondents") if respondents is not None else None
    fuels = _codes(fuel_types, "fuel_types") if fuel_types is not None else None
    supported_fuels = {code for code, _ in _BALANCE_FUELS.values()}
    if fuels is not None and not set(fuels).issubset(supported_fuels):
        raise ValueError("EIA balance fuel_types contains an unsupported source code")
    if type(maximum_rows) is not int or not 1 <= maximum_rows <= 2_000_000:
        raise ValueError("maximum_rows must be an integer between 1 and 2000000")
    if not text or not text.endswith(("\n", "\r")):
        raise RetrievalError("EIA balance CSV is empty or lacks a complete final record")
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader)
        if len(set(header)) != len(header) or not 2 <= len(header) <= 256:
            raise RetrievalError("EIA balance CSV has duplicate or excessive columns")
        required = {"Balancing Authority", "UTC Time at End of Hour"}
        if not required.issubset(header):
            raise RetrievalError("EIA balance CSV is missing its authority or UTC timestamp column")
        reported_columns = [
            column
            for column in header
            if column.startswith("Net Generation (MW) from ")
            and not column.endswith(("(Imputed)", "(Adjusted)"))
        ]
        if any(
            column.removeprefix("Net Generation (MW) from ") not in _BALANCE_FUELS
            for column in reported_columns
        ):
            raise RetrievalError("EIA balance CSV contains an unrecognized reported fuel column")
        columns = {
            f"Net Generation (MW) from {name}": (code, label)
            for name, (code, label) in _BALANCE_FUELS.items()
            if f"Net Generation (MW) from {name}" in header and (fuels is None or code in fuels)
        }
        if not columns:
            raise RetrievalError("EIA balance CSV contains no selected reported fuel columns")
        if fuels is not None and not set(fuels).issubset({code for code, _ in columns.values()}):
            raise RetrievalError("EIA balance CSV is missing one or more selected fuel columns")
        if len({code for code, _ in columns.values()}) != len(columns):
            raise RetrievalError("EIA balance CSV has overlapping old and new fuel categories")
        indexes = {name: header.index(name) for name in header}
        rows: list[JSONValue] = []
        for row_number, record in enumerate(reader, start=1):
            if row_number > maximum_rows:
                raise RetrievalError("EIA balance CSV exceeds its configured row limit")
            if len(record) != len(header):
                raise RetrievalError("EIA balance CSV contains a truncated record")
            respondent = record[indexes["Balancing Authority"]]
            if selected is not None and respondent not in selected:
                continue
            stamp = record[indexes["UTC Time at End of Hour"]]
            try:
                timestamp = datetime.strptime(stamp, "%m/%d/%Y %I:%M:%S %p")
            except ValueError:
                raise RetrievalError("EIA balance CSV has an invalid UTC timestamp") from None
            if timestamp.minute or timestamp.second:
                raise RetrievalError("EIA balance CSV timestamp is not an hour boundary")
            for column, (code, label) in columns.items():
                rows.append(
                    {
                        "period": timestamp.strftime("%Y-%m-%dT%H"),
                        "respondent": respondent,
                        "fueltype": code,
                        "type-name": label,
                        "value": record[indexes[column]],
                        "value-units": "megawatthours",
                        "source_column": column,
                        "source_timestamp": stamp,
                        "source_local_time": record[indexes["Local Time at End of Hour"]]
                        if "Local Time at End of Hour" in indexes
                        else None,
                        "source_operating_date": record[indexes["Data Date"]]
                        if "Data Date" in indexes
                        else None,
                        "source_region": record[indexes["Region"]] if "Region" in indexes else None,
                    }
                )
    except (csv.Error, StopIteration):
        raise RetrievalError("EIA balance CSV is not a valid complete table") from None
    frame = normalize_hourly_generation(rows)
    frame["source_unit"] = "MW"
    frame["duration_hours"] = 1.0
    frame.attrs.update(
        dataset="EIA-930 six-month balance CSV",
        value_selection="Reported fuel columns only; no imputed or adjusted values substituted",
        conversion="Hourly average MW multiplied by one hour to obtain MWh",
    )
    return frame


@dataclass(slots=True)
class EIAClient:
    """EIA source client; API credentials are never included in repr or provenance."""

    http: HTTPClient
    api_key: str = field(default="", repr=False)
    page_size: int = 5000
    maximum_pages: int = 200

    def __post_init__(self) -> None:
        if (
            type(self.page_size) is not int
            or not 1 <= self.page_size <= 5000
            or type(self.maximum_pages) is not int
            or not 1 <= self.maximum_pages <= 1000
        ):
            raise ValueError("EIA requires page_size 1..5000 and maximum_pages 1..1000")

    @classmethod
    def from_environment(cls, http: HTTPClient) -> EIAClient:
        """Use a free user-registered EIA_API_KEY for API requests."""
        return cls(http, api_key=os.environ.get("EIA_API_KEY", ""))

    def metadata(
        self, dataset: Literal["hourly", "monthly"]
    ) -> tuple[dict[str, JSONValue], RequestRecord]:
        """Retrieve official route metadata (frequencies, facets, and data fields)."""
        self._require_key()
        if dataset not in {"hourly", "monthly"}:
            raise ValueError("dataset must be hourly or monthly")
        endpoint = (
            HOURLY_GENERATION_ENDPOINT if dataset == "hourly" else MONTHLY_GENERATION_ENDPOINT
        )
        response = self.http.get_json(
            endpoint.removesuffix("data/"), secrets={"api_key": self.api_key}
        )
        payload = object_value(response.value)
        if "error" in payload:
            raise RetrievalError("EIA reported an API error; verify key and request parameters")
        return object_value(payload.get("response")), response.record

    def _require_key(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ValueError(
                "Set EIA_API_KEY to an authorized EIA API key; public balance files need none"
            )

    def _query(
        self,
        *,
        monthly: bool,
        start: str,
        end: str,
        facets: Mapping[str, Sequence[str]],
    ) -> EIAResult:
        self._require_key()
        if start > end:
            raise ValueError("EIA start must be on or before end")
        endpoint = MONTHLY_GENERATION_ENDPOINT if monthly else HOURLY_GENERATION_ENDPOINT
        frequency = "monthly" if monthly else "hourly"
        sort_columns = _MONTHLY_KEYS if monthly else _HOURLY_KEYS
        parameters = {
            "frequency": frequency,
            "data[0]": "generation" if monthly else "value",
            "start": start,
            "end": end,
            "length": str(self.page_size),
        }
        for index, column in enumerate(sort_columns):
            parameters[f"sort[{index}][column]"] = column
            parameters[f"sort[{index}][direction]"] = "asc"
        for facet, values in facets.items():
            for index, code in enumerate(_codes(values, facet)):
                parameters[f"facets[{facet}][{index}]"] = code
        rows: list[JSONValue] = []
        records: list[RequestRecord] = []
        total: int | None = None
        offset = 0
        for _ in range(self.maximum_pages):
            response = self.http.get_json(
                endpoint,
                parameters | {"offset": str(offset)},
                secrets={"api_key": self.api_key},
            )
            payload = object_value(response.value)
            if "error" in payload:
                raise RetrievalError("EIA reported an API error; verify key and request parameters")
            body = object_value(payload.get("response"))
            advertised = _integer(body.get("total"), label="total")
            if body.get("frequency") != frequency:
                raise RetrievalError("EIA returned an unexpected frequency")
            if advertised > self.page_size * self.maximum_pages:
                raise RetrievalError(
                    "EIA query exceeds the configured page limit; narrow the selection"
                )
            if total is not None and advertised != total:
                raise RetrievalError(
                    "EIA pagination changed during retrieval; retry the bounded query"
                )
            total = advertised
            page = array_value(body.get("data"))
            if len(page) != min(self.page_size, total - offset):
                raise RetrievalError("EIA returned an incomplete or oversized page")
            for raw in page:
                row = object_value(raw)
                period = _source_string(row, "period")
                if not start <= period <= end:
                    raise RetrievalError("EIA returned a period outside the requested bounds")
                if any(
                    _source_string(row, facet) not in values for facet, values in facets.items()
                ):
                    raise RetrievalError("EIA did not honor the requested source filters")
            records.append(response.record)
            rows.extend(page)
            offset += len(page)
            if offset == total:
                frame = (
                    normalize_monthly_generation(rows)
                    if monthly
                    else normalize_hourly_generation(rows)
                )
                if len(frame) != total:
                    raise RetrievalError(
                        "EIA repeated observations across pages; snapshot is incomplete"
                    )
                return EIAResult(frame, tuple(records))
        raise RetrievalError("EIA pagination exceeded its configured page limit")

    def hourly_generation(
        self,
        start: datetime,
        end: datetime,
        *,
        respondents: Sequence[str],
        fuel_types: Sequence[str] | None = None,
    ) -> EIAResult:
        """Hourly net generation by fuel, inclusive UTC hour-ending label bounds.

        Select BAs (e.g. ``CISO``), regions or ``US48`` explicitly. These levels
        overlap and must not be summed together. Full advertised pagination is
        fetched or an error is raised; an empty successful result is valid.
        """
        facets: dict[str, Sequence[str]] = {"respondent": respondents}
        if fuel_types is not None:
            facets["fueltype"] = fuel_types
        return self._query(monthly=False, start=_utc_hour(start), end=_utc_hour(end), facets=facets)

    def monthly_generation(
        self,
        start: str,
        end: str,
        *,
        plant_codes: Sequence[str],
        fuel_types: Sequence[str] | None = None,
        prime_movers: Sequence[str] | None = None,
    ) -> EIAResult:
        """EIA-923 plant monthly net generation, inclusive YYYY-MM bounds.

        Preserve plantCode, fuel2002, fuelType and primeMover, including any
        provider aggregate rows. Filter one consistent aggregation level before
        summing; a plant with multiple fuels/prime movers has several records.
        """
        facets: dict[str, Sequence[str]] = {"plantCode": plant_codes}
        if fuel_types is not None:
            facets["fuelType"] = fuel_types
        if prime_movers is not None:
            facets["primeMover"] = prime_movers
        return self._query(monthly=True, start=_month(start), end=_month(end), facets=facets)

    def balance_file(
        self,
        year: int,
        half: int,
        path: Path,
        *,
        respondents: Sequence[str] | None = None,
        fuel_types: Sequence[str] | None = None,
    ) -> EIAResult:
        """Download and parse a key-free six-month reported-generation CSV.

        The native file and its verified request manifest remain at ``path``.
        Files may be tens of MB; the shared HTTP byte cap still applies. Use
        narrow respondent/fuel filters to reduce the parsed in-memory result.
        """
        if respondents is not None:
            _codes(respondents, "respondents")
        if fuel_types is not None:
            _codes(fuel_types, "fuel_types")
        record = self.http.download_file(balance_file_url(year, half), path)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            raise RetrievalError("EIA balance file is not UTF-8 CSV") from None
        frame = parse_balance_csv(text, respondents=respondents, fuel_types=fuel_types)
        return EIAResult(frame, (record,))
