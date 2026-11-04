"""Stage Taipower public PV sites without equating stations, sites and plants."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from typing import Any

HEADERS = (
    "發電站編號/Number of The Power Station",
    "能源別/Type of Energy",
    "發電站名稱/Name of The Power Station",
    "場址編號/Number of the Site",
    "場址說明/Description fo The Site",
    "型號/Model",
    "裝置容量(瓩)/Installed Capacity(kW)",
    "風機數量/Number of The Windturbine",
    "地址/Address",
    "申設狀態/Application Status",
    "備註/Remarks",
)


def read_taipower_sites(
    content: bytes, *, sha256: str, after_station_id: int | None = None, limit: int = 100
) -> dict[str, Any]:
    """Read bounded station groups; keep all sites and their native observations.

    A station can cover separate sites/roofs/phases. IDs are technology-scoped.
    Installed kW has no established AC/DC basis here. Application status is not
    current operation. Source addresses are deliberately excluded from staging.
    """
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("Taipower source checksum mismatch")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Taipower partition limit must be 1-1000")
    if after_station_id is not None and (type(after_station_id) is not int or after_station_id < 1):
        raise ValueError("Taipower cursor must be a positive station ID")
    reader = csv.reader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    if tuple(next(reader, ())) != HEADERS:
        raise ValueError("Taipower site schema changed")
    groups: dict[str, dict[str, Any]] = {}
    site_ids: set[str] = set()
    station_ids: dict[int, str] = {}
    counts = dict.fromkeys(["source_rows", "blank_rows", "non_pv_rows", "pv_sites"], 0)
    for number, cells in enumerate(reader, 2):
        if not cells or not any(value.strip() for value in cells):
            counts["blank_rows"] += 1
            continue
        if len(cells) != len(HEADERS):
            raise ValueError("Taipower row width changed")
        counts["source_rows"] += 1
        station, energy, name, site, description, model, power, wind_count, _, status, remark = (
            value.strip() for value in cells
        )
        if energy != "太陽能/Solar":
            counts["non_pv_rows"] += 1
            continue
        if "光電" not in name and "photovoltaic" not in name.lower():
            raise ValueError("Taipower generic Solar is insufficient to prove PV")
        if not re.fullmatch(r"[1-9][0-9]*", site) or site in site_ids:
            raise ValueError("Taipower missing or repeated PV site ID")
        site_ids.add(site)
        if wind_count:
            raise ValueError("Taipower PV wind-count cell requires review")
        if not re.fullmatch(r"\d+(?:\.\d+)?", power):
            raise ValueError("Taipower capacity must be a native nonnegative kW number")
        capacity = float(power)
        if not math.isfinite(capacity):
            raise ValueError("Taipower capacity is not finite")
        if name not in groups:
            groups[name] = {"station_name_native": name, "station_id": None, "sites": []}
        group = groups[name]
        if station != "-":
            if not re.fullmatch(r"[1-9][0-9]*", station):
                raise ValueError("Taipower station ID is invalid")
            station_id = int(station)
            if station_id in station_ids and station_ids[station_id] != name:
                raise ValueError("Taipower station ID has conflicting names")
            if group["station_id"] not in (None, station_id):
                raise ValueError("Taipower station name has conflicting IDs")
            station_ids[station_id] = name
            group["station_id"] = station_id
        group["sites"].append(
            {
                "site_id": site,
                "csv_record_number": number,
                "description_native": description or None,
                "model_label_native": model or None,
                "installed_capacity_kw_native": capacity,
                "capacity_basis": "AC/DC unspecified; no scalar conversion or aggregation",
                "application_status_native": status or None,
                "remarks_native": remark or None,
            }
        )
        counts["pv_sites"] += 1
    if any(g["station_id"] is None for g in groups.values()):
        raise ValueError("Taipower station group has no explicit ID; no forward fill")
    ordered = sorted(groups.values(), key=lambda g: g["station_id"])
    if after_station_id is not None and after_station_id not in station_ids:
        raise ValueError("Taipower cursor is absent from this source revision")
    pending = [g for g in ordered if after_station_id is None or g["station_id"] > after_station_id]
    selected = pending[:limit]
    for group in selected:
        group.update(
            accepted=False,
            held_reasons=[
                "station_site_plant_phase_identity_requires_review",
                "capacity_ac_dc_basis_unestablished",
                "source_effective_date_unestablished",
                "application_status_not_current_operation",
                "model_labels_not_OEM_verified_equipment_records",
            ],
        )
    return {
        "sha256": sha256,
        "counts": {**counts, "pv_station_groups": len(ordered)},
        "candidates": selected,
        "next_after_station_id": selected[-1]["station_id"] if selected else after_station_id,
        "remaining_after_partition": len(pending) - len(selected),
        "accepted_records": 0,
        "addresses_and_personal_contacts_excluded": True,
        "no_capacity_sum_or_status_date_inference": True,
    }
