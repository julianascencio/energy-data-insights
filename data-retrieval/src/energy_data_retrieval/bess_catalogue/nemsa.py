"""Offline, allowlisted staging of public NEMSA mini-grid inspection applications.

These are applicant declarations, not certificates or commercial-operation
records. Keep reported units/text untouched for manual identity and scope review.
No network access, personal-contact extraction, numeric repair or canonical import.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from energy_data_retrieval.bess_catalogue.pib import _Tables

_SITE = {
    "Name of the Village/Community",
    "State",
    "Local Government Area",
    "GPS Coordinates",
    "Total Solar PV Installed (kWp)",
    "Total Storage Capacity (kwh)",
    "Storage Technology/Manufacturer",
    "Type of Coupling (AC/DC)",
    "Year of Construction",
    "Date of Installation of Mini-Grid",
    "Date of Application",
}
_BATTERY = {"Manufacturer", "Model", "Technology", "Cell Voltage (V)", "Battery Voltage"}


def parse_nemsa_minigrid_html(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage one application, keyed by the supplied exact public entry URL.

    Identical page copies collapse; conflicting copies or changed mandatory
    headers fail closed. Company-address State rows are excluded by anchoring
    at the community label. Battery subsection observations never overwrite the
    top-level storage claim. Owner fields may contain personal applicant names,
    so ownership is deliberately left for manual source review.
    """
    match = re.fullmatch(
        r"https://nemsa\.gov\.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/(\d+)/?",
        source_url,
    )
    if not match:
        raise ValueError("Expected an exact NEMSA public inspection entry URL")
    parser = _Tables()
    parser.feed(content.decode("utf-8-sig"))
    candidates = []
    for table in parser.tables:
        rows = [cells for cells in table if len(cells) == 2]
        starts = [i for i, row in enumerate(rows) if row[0] == "Name of the Village/Community"]
        if not starts:
            continue
        if len(starts) != 1:
            raise ValueError("Multiple community identities in one table")
        start = starts[0]
        stop = next(
            (i for i in range(start + 1, len(rows)) if rows[i][0] == "Manufacturer"), len(rows)
        )
        summary: dict[str, str] = {}
        for label, value in rows[start:stop]:
            if label in _SITE:
                if label in summary and summary[label] != value:
                    raise ValueError("Conflicting site field in application")
                summary[label] = value
        mandatory = {
            "Name of the Village/Community",
            "State",
            "Total Storage Capacity (kwh)",
            "Storage Technology/Manufacturer",
        }
        if not mandatory <= summary.keys() or any(not summary[key] for key in mandatory):
            raise ValueError("Missing NEMSA site/storage headers; review source revision")
        batteries = []
        for i in range(stop, len(rows)):
            if rows[i][0] != "Cell Voltage (V)":
                continue
            # Exact battery table shape: Manufacturer, Model, Technology,
            # Cell Voltage, Battery Voltage. Do not borrow preceding PV/PCS data.
            block = rows[max(stop, i - 3) : i + 2]
            if [r[0] for r in block] != [
                "Manufacturer",
                "Model",
                "Technology",
                "Cell Voltage (V)",
                "Battery Voltage",
            ]:
                raise ValueError("Battery subsection shape changed")
            batteries.append({k: v for k, v in block if k in _BATTERY})
        capacity_observations = [
            {"label": label, "reported_value": value}
            for label, value in rows[stop:]
            if label in {"C10 Capacity", "Total C10 capacity [kWh]"}
        ]
        candidate = {
            "site_reported": summary,
            "battery_reported": batteries,
            "battery_capacity_observations": capacity_observations,
        }
        if candidates and candidate != candidates[0]:
            raise ValueError("Conflicting NEMSA page copies")
        candidates.append(candidate)
    if not candidates:
        raise ValueError("NEMSA community table not found")
    return {
        "source_url": source_url,
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "external_id": {"nemsa_inspection_entry": match[1]},
        **candidates[0],
        "review_required": True,
        "evidence_class": "applicant_inspection_request_not_operating_certificate",
    }
