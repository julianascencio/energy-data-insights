"""Fail-closed staging of NRCan MPI workbooks; never automatic plant acceptance."""

from __future__ import annotations

import hashlib
import io
import math
import re
from typing import Any
from zipfile import BadZipFile

import openpyxl

HEADERS = (
    "Project ID",
    "Project Name",
    "Company/ Proponent",
    "Phases/ Components ",
    "P/T",
    "Location",
    "Latitude 1",
    "Longitude 1",
    "Lat. 2",
    "Lon. 2",
    "Lat. 3",
    "Lon. 3",
    "Lat. 4",
    "Lon. 4",
    "Lat. 5",
    "Lon. 5",
    "Lat. 6",
    "Lon. 6",
    "Geometry",
    "Status 2025",
    "Status 2024",
    "Status change 2024 to 2025",
    "Cost 2025 (CAD) {$M}",
    "Cost 2024 (CAD) {$M}",
    "Sector",
    "Mining - Group",
    "Mining - Critical Minerals",
    "Clean Technology",
    "ENERGY - Type",
    "Cleantech - Type",
)


def read_nrcan_mpi(content: bytes, *, sha256: str) -> dict[str, Any]:
    """Stage native Solar claims after schema and embedded-publication checks.

    An open portal licence cannot override a contradictory workbook notice. The
    2025 workbook retrieved in November 2026 is rejected by this gate. A future
    corrected release still needs independent reuse and canonical identity review.
    Solar is not proof of PV; cost is an approximate native CAD-million estimate.
    Hidden vendor sheets, geometry and coordinate fields never enter the output.
    """
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("NRCan source checksum mismatch")
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except (OSError, ValueError, KeyError, BadZipFile) as exc:
        raise ValueError("NRCan workbook unreadable") from exc
    try:
        if not {"About + Caveats", "Definitions", "MPI 2025 Data"} <= set(workbook.sheetnames):
            raise ValueError("NRCan required sheets changed")
        caveats = " ".join(
            str(value)
            for row in workbook["About + Caveats"].iter_rows(values_only=True)
            for value in row
            if value is not None
        )
        normalized = " ".join(caveats.lower().split())
        if re.search(
            r"\bnot (?:authori[sz]ed|approved)"
            r"(?: or (?:authori[sz]ed|approved))? for publication\b",
            normalized,
        ):
            raise ValueError("NRCan embedded publication restriction; no rows staged")
        if "potential cost estimates are approximate" not in normalized:
            raise ValueError("NRCan cost caveat changed; review before staging")
        rows = workbook["MPI 2025 Data"].iter_rows(values_only=True)
        if next(rows, ()) != HEADERS:
            raise ValueError("NRCan projected schema changed")
        identifiers: set[str] = set()
        candidates = []
        reviewed = 0
        for number, values in enumerate(rows, 2):
            if all(value is None for value in values):
                continue
            reviewed += 1
            data = dict(zip(HEADERS, values, strict=True))
            identifier = data["Project ID"]
            if not isinstance(identifier, str) or not re.fullmatch(r"\d{4}", identifier):
                raise ValueError("NRCan project ID must retain four-digit text")
            if identifier in identifiers:
                raise ValueError("NRCan duplicate project ID")
            identifiers.add(identifier)
            if data["Cleantech - Type"] != "Solar":
                continue
            if data["Sector"] != "Energy" or data["ENERGY - Type"] != "Electricity":
                raise ValueError("NRCan Solar classification changed")
            for field in ["Project Name", "Company/ Proponent", "P/T", "Status 2025"]:
                if not isinstance(data[field], str) or not data[field].strip():
                    raise ValueError("NRCan candidate identity/status missing")
            cost = data["Cost 2025 (CAD) {$M}"]
            if cost is not None and (
                type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0
            ):
                raise ValueError("NRCan native cost malformed")
            candidates.append(
                {
                    "source_project_id": identifier,
                    "workbook_row": number,
                    "name_as_reported": data["Project Name"],
                    "proponent_as_reported": data["Company/ Proponent"],
                    "phase_scope_as_reported": data["Phases/ Components "],
                    "province_as_reported": data["P/T"],
                    "locality_as_reported": data["Location"],
                    "status_2025_as_reported": data["Status 2025"],
                    "cost_2025_million_cad_as_reported": cost,
                    "technology_as_reported": "Solar",
                    "accepted": False,
                    "held_reasons": [
                        "generic_solar_does_not_prove_photovoltaic",
                        "proponent_is_not_verified_owner",
                        "phase_site_and_natural_identity_review_required",
                        "historical_status_not_present_operation",
                        "approximate_nominal_cost_not_verified_actual_capex",
                        "independent_source_reuse_review_required",
                    ],
                }
            )
        return {"sha256": sha256, "source_rows_reviewed": reviewed, "candidates": candidates}
    finally:
        workbook.close()
