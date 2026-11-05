"""Read bounded EIA annual wind partitions without promoting unit status to farms."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import math
import re
import unicodedata
from typing import Any

import openpyxl

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

REFERENCE_IDS = ("eia860_2025", "wri_usa_identity")
STATUS = {
    "RE": "retired",
    "CN": "canceled",
    "IP": "indefinitely postponed or no longer in resource plan",
}
WIND_COLUMNS = (
    "Utility ID",
    "Utility Name",
    "Plant Code",
    "Plant Name",
    "State",
    "County",
    "Generator ID",
    "Status",
    "Technology",
    "Prime Mover",
    "Sector Name",
    "Sector",
    "Nameplate Capacity (MW)",
    "Summer Capacity (MW)",
    "Winter Capacity (MW)",
    "Operating Month",
    "Operating Year",
    "Number of Turbines",
    "Predominant Turbine Manufacturer",
    "Predominant Turbine Model Number",
    "Design Wind Speed (mph)",
    "Wind Quality Class",
    "Turbine Hub Height (Feet)",
)
PLANT_COLUMNS = (
    "Plant Code",
    "Plant Name",
    "State",
    "County",
    "Latitude",
    "Longitude",
    "Balancing Authority Code",
    "Balancing Authority Name",
    "Transmission or Distribution System Owner",
    "Grid Voltage (kV)",
    "Grid Voltage 2 (kV)",
    "Grid Voltage 3 (kV)",
)


def _number(value: Any, *, integer: bool = False) -> float | int | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean is not an EIA quantity")
    number = float(value)
    if not math.isfinite(number) or number < 0 or (integer and not number.is_integer()):
        raise ValueError("Invalid nonnegative EIA quantity")
    return int(number) if integer else number


def _rows(data: bytes, sheet: str, columns: tuple[str, ...], year: int) -> list[dict[str, Any]]:
    book = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        values = book[sheet].iter_rows(values_only=True)
        title = str(next(values)[0])
        if not title.startswith(f"{year} Form EIA-860 Data"):
            raise ValueError("Unexpected EIA reporting year")
        headers = list(next(values))
        if any(headers.count(x) != 1 for x in columns):
            raise ValueError("Missing or duplicated EIA column")
        result = []
        for index, values_row in enumerate(values, 3):
            if not any(v is not None and str(v).strip() for v in values_row):
                continue
            item = dict(zip(headers, values_row, strict=True))
            item = {
                k: (None if isinstance(v, str) and not v.strip() else v)
                for k, v in item.items()
                if k
            }
            item["_row"] = index
            result.append(item)
        return result
    finally:
        book.close()


def parse_retired_partition(
    wind: bytes,
    plant: bytes,
    *,
    year: int,
    wind_sha256: str,
    plant_sha256: str,
    operable_range: tuple[int, int] | None = None,
) -> list[dict[str, Any]]:
    """Return every nonoperable wind plant group, retaining original unit rows.

    This is a complete workbook tab, not a complete historical retirement census.
    By default operable rows supply context only. ``operable_range`` selects a
    complete inclusive plant-code range instead; hybrid scope stays open.
    """
    if (
        hashlib.sha256(wind).hexdigest() != wind_sha256
        or hashlib.sha256(plant).hexdigest() != plant_sha256
    ):
        raise ValueError("EIA original workbook checksum mismatch")
    retired = _rows(
        wind, "Retired and Canceled", (*WIND_COLUMNS, "Retirement Month", "Retirement Year"), year
    )
    operable = _rows(wind, "Operable", WIND_COLUMNS, year)
    plants = _rows(plant, "Plant", PLANT_COLUMNS, year)
    plant_map = {}
    for row in plants:
        code = _number(row["Plant Code"], integer=True)
        if not code or code in plant_map:
            raise ValueError("Duplicate or missing EIA plant code")
        plant_map[code] = row
    if any(x["Status"] not in {"OP", "OS", "OA"} for x in operable):
        raise ValueError("Unknown operable EIA status")
    groups: dict[int, list[dict[str, Any]]] = {}
    seen = set()
    for row in [*retired, *operable]:
        code = _number(row["Plant Code"], integer=True)
        generator = str(row["Generator ID"] or "").strip()
        if not code or not generator or (code, generator) in seen:
            raise ValueError("Duplicate or missing EIA generator identity")
        seen.add((code, generator))
        if (row["Technology"], row["Prime Mover"]) not in {
            ("Onshore Wind Turbine", "WT"),
            ("Offshore Wind Turbine", "WS"),
        }:
            raise ValueError("Non-wind row in EIA wind partition")
    states = (
        STATUS
        if operable_range is None
        else {"OP": "operating", "OS": "out of service", "OA": "standby"}
    )
    selected = retired
    sheet = "Retired and Canceled"
    if operable_range is not None:
        low, high = operable_range
        if type(low) is not int or type(high) is not int or not 1 <= low <= high:
            raise ValueError("Invalid complete plant-code range")
        selected = [x for x in operable if low <= x["Plant Code"] <= high]
        sheet = "Operable"
    for row in selected:
        if row["Status"] not in states:
            raise ValueError("Unknown nonoperable EIA status")
        code = int(row["Plant Code"])
        if code not in plant_map:
            raise ValueError("Wind plant missing from EIA plant workbook")
        groups.setdefault(code, []).append(row)
    result = []
    for code, units in sorted(groups.items()):
        plant_row = plant_map[code]
        observations = []
        for row in units:

            def number(k: str, row: dict[str, Any] = row) -> float | int | None:
                return _number(row[k])

            count = _number(row["Number of Turbines"], integer=True)
            for prefix in ("Operating", "Retirement"):
                month = _number(row.get(f"{prefix} Month"), integer=True)
                yr = _number(row.get(f"{prefix} Year"), integer=True)
                if month is not None and (not 1 <= month <= 12 or yr is None):
                    raise ValueError("Invalid EIA month/year observation")
            height = number("Turbine Hub Height (Feet)")
            speed = number("Design Wind Speed (mph)")
            observations.append(
                {
                    "generator_id": str(row["Generator ID"]).strip(),
                    "status": states[row["Status"]],
                    "status_code": row["Status"],
                    "status_as_of": f"{year}-12-31",
                    "original": {k: v for k, v in row.items() if k != "_row"},
                    "locator": f"3_2_Wind_Y{year}.xlsx / {sheet} / row {row['_row']}",
                    "reported_unit_nameplate_mw": number("Nameplate Capacity (MW)"),
                    "reported_unit_net_summer_mw": number("Summer Capacity (MW)"),
                    "reported_unit_net_winter_mw": number("Winter Capacity (MW)"),
                    "reported_turbine_count": count,
                    "representative_hub_height_m": None if height is None else height * 0.3048,
                    "source_wind_speed_m_s": None if speed is None else speed * 0.44704,
                    "normalization": {
                        "height": "feet * 0.3048; representative across generator turbines",
                        "speed": (
                            "mph * 0.44704; workbook says Design Wind Speed, instructions p15 "
                            "say representative annual average; method, dates and height "
                            "unspecified"
                        ),
                    },
                    "fleet_completeness": (
                        "predominant manufacturer/model only; mixed fleet possible; not "
                        "exact OEM configuration"
                    ),
                    "capacity_scope": (
                        "one reported generator or generator aggregation, not whole plant "
                        "or current installed capacity"
                    ),
                }
            )
        result.append(
            {
                "plant_code": code,
                "name": plant_row["Plant Name"],
                "year": year,
                "plant_context": {k: plant_row[k] for k in PLANT_COLUMNS},
                "plant_locator": f"2___Plant_Y{year}.xlsx / Plant / row {plant_row['_row']}",
                "units": observations,
                "operable_context": [
                    {
                        "generator_id": str(x["Generator ID"]).strip(),
                        "status_code": x["Status"],
                        "locator": f"3_2_Wind_Y{year}.xlsx / Operable / row {x['_row']}",
                    }
                    for x in operable
                    if x["Plant Code"] == code
                ],
                "scope": (
                    "All rows for this plant in the annual Retired and Canceled wind "
                    "tab; not comprehensive historical retirements, installed turbine "
                    "inventory, or hybrid/repowering reconciliation"
                ),
                "plant_coordinate_scope": (
                    "EIA whole-plant point; accuracy unspecified; not individual "
                    "turbine coordinates"
                ),
            }
        )
    if operable_range is not None:
        for item in result:
            item["scope"] = (
                "Complete Operable wind plant-code partition; OP/OS/OA stay distinct. "
                "Generator observations are not a current whole-farm operating census "
                "or hybrid/repowering reconciliation."
            )
            item["plant_code_range"] = list(operable_range)
    return result


def _name(value: str) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower(),
    )


def enrich_retired_partition(
    candidates: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    approved: dict[int, str],
    *,
    source_id: str,
    identity_source_id: str,
    now: str,
) -> list[dict[str, Any]]:
    """Apply reviewed exact IDs with independent name and coordinate agreement.

    Preserve farm status, capacity, historical observations and creation timestamps.
    A source revision is immutable and replay is idempotent.
    """
    if len({x["plant_code"] for x in candidates}) != len(candidates):
        raise ValueError("Duplicate candidate plant code")
    if set(approved) - {x["plant_code"] for x in candidates} or len(set(approved.values())) != len(
        approved
    ):
        raise ValueError("Invalid approved identity mapping")
    by_id = {x["record_id"]: x for x in existing}
    if len(by_id) != len(existing):
        raise ValueError("Duplicate existing catalogue identity")
    result = []
    for item in candidates:
        code = item["plant_code"]
        if code not in approved:
            continue
        row = copy.deepcopy(by_id[approved[code]])
        ids = json.loads(row["external_ids_json"])
        if (
            row["country_code"] != "USA"
            or ids.get("wri_gppd") != f"USA{code:07d}"
            or _name(row["name"]) != _name(item["name"])
        ):
            raise ValueError("EIA identity does not match reviewed WRI code/name")
        for key, source_key in (("latitude", "Latitude"), ("longitude", "Longitude")):
            old = row.get(key)
            new = item["plant_context"][source_key]
            if (
                old is None
                or new is None
                or not math.isfinite(float(new))
                or abs(old - float(new)) > 0.0001
            ):
                raise ValueError("EIA identity coordinate disagreement")
        if ids.get("eia_plant_code", str(code)) != str(code):
            raise ValueError("Conflicting existing EIA identifier")
        ext = json.loads(row["extensions_json"])
        observation = {**copy.deepcopy(item), "source_id": source_id}
        history = ext.setdefault("eia_annual_wind_partitions", [])
        prior = [x for x in history if x["source_id"] == source_id]
        if prior:
            if prior != [observation]:
                raise ValueError("Immutable EIA observation changed")
            result.append(row)
            continue
        # Source aliases or overlapping bounds must not duplicate an observation.
        # Different dated/revised observations remain independently reviewable.
        if any(
            old.get("year") == item["year"]
            and old.get("plant_code") == code
            and old.get("units") == item["units"]
            for old in history
        ):
            raise ValueError("Overlapping EIA unit observation from another source")
        history.append(observation)
        ids["eia_plant_code"] = str(code)
        fs = json.loads(row["field_sources_json"])
        ev = json.loads(row["evidence_json"])
        for field, value in (("external_ids_json", ids), ("extensions_json", ext)):
            row[field] = canonical_json(value)
            fs[field] = sorted(set([*fs.get(field, []), source_id, identity_source_id]))
            ev[field] = {
                "prior_observation": ev.get(field),
                "source_id": source_id,
                "locator": item["plant_locator"]
                + "; unit row locators embedded in extensions_json",
                "confidence": "high",
                "normalization": (
                    "Reviewed EIA code encoded by upstream WRI importer; matching name "
                    "and coordinates; nested unit scope only"
                ),
            }
        row.update(
            field_sources_json=canonical_json(fs),
            evidence_json=canonical_json(ev),
            sources=sorted(set(row["sources"] + [source_id, identity_source_id])),
            updated_at=now,
            last_verified_at=now,
        )
        result.append(row)
    return sorted(result, key=lambda x: x["record_id"])


def stage_reviewed_site(item: dict[str, Any], *, source_id: str, now: str) -> dict[str, Any]:
    """Stage one independently reviewed new EIA site, without inferring farm totals.

    Caller must review existing registry IDs, names, coordinates and related phases.
    Unit observations retain status and capacity; unresolved farm scope excludes sums.
    """
    from .catalogue import stable_id
    from .gppd import evidence_record

    code = item["plant_code"]
    if type(code) is not int or code <= 0 or not item["name"] or not item["units"]:
        raise ValueError("Require a named EIA site with generating-unit evidence")
    native = item["plant_context"]
    lat, lon = native["Latitude"], native["Longitude"]
    if (
        lat is None
        or lon is None
        or not math.isfinite(lat)
        or not math.isfinite(lon)
        or not -90 <= lat <= 90
        or not -180 <= lon <= 180
    ):
        raise ValueError("Require valid whole-plant coordinates")
    technologies = {u["original"]["Technology"] for u in item["units"]}
    if technologies != {"Onshore Wind Turbine"}:
        raise ValueError("Review offshore/mixed site scope separately")
    return evidence_record(
        {
            "record_id": stable_id("projects", "EIA plant", str(code)),
            "entity_type": "projects",
            "record_scope": "farm",
            "name": item["name"],
            "country_code": "USA",
            "region": native["State"],
            "latitude": lat,
            "longitude": lon,
            "location_accuracy": "EIA whole-plant point; positional accuracy unquantified",
            "technology": "onshore",
            "status": "unknown",
            "status_as_of": f"{item['year']}-12-31",
            "status_date_basis": "Annual generator statuses retained; farm lifecycle unresolved",
            "aggregation_role": "unresolved",
            "capacity_scope": "EIA registry site; phase/hybrid/repowering boundary unresolved",
            "external_ids_json": canonical_json({"eia_plant_code": str(code)}),
            "extensions_json": canonical_json(
                {
                    "eia_annual_wind_partitions": [{**copy.deepcopy(item), "source_id": source_id}],
                    "coordinate_precision": "Source whole-plant point; accuracy unknown",
                    "inventory_completeness": "All selected wind generator rows; no turbine IDs",
                }
            ),
        },
        source_id=source_id,
        now=now,
        locator=item["plant_locator"] + "; embedded generator row locators",
    )
