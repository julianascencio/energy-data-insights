"""Stage explicitly classified batteries from the EA September 2024 pipeline."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from typing import Any

HEADERS = [
    "Developer",
    "Project",
    "Fuel",
    "Technology",
    "Megawatts",
    "Capacity factor",
    "Approx annual gigawatt-hours",
    "Earliest commissioning year",
    "Status",
    "Grid connected?",
    "Island",
]


def parse_nz_pipeline(content: bytes) -> list[dict[str, Any]]:
    """Keep row locators and dated planning stages; never infer storage MWh or COD.

    No identities are merged. The 2024 file can contain superseded ratings,
    multi-phase aggregates and projects already operating in newer sources.
    """
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    if reader.fieldnames != HEADERS:
        raise ValueError("Unreviewed NZ pipeline header")
    result = []
    seen = set()
    for line, row in enumerate(reader, 2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f"Malformed CSV row {line}")
        if row["Technology"] != "Chemical battery energy storage system":
            continue
        if row["Fuel"] != "Electrical energy":
            raise ValueError(f"Conflicting battery classification at row {line}")
        identity = (row["Developer"], row["Project"])
        if not all(identity) or identity in seen:
            raise ValueError(f"Missing or duplicate candidate identity at row {line}")
        seen.add(identity)
        mw = float(row["Megawatts"])
        if not math.isfinite(mw) or mw <= 0:
            raise ValueError(f"Invalid battery MW at row {line}")
        if row["Status"] not in {"Committed", "Actively pursued", "Other"}:
            raise ValueError(f"Unreviewed planning status at row {line}")
        year = int(row["Earliest commissioning year"])
        if not 1900 <= year <= 2200 or row["Grid connected?"] not in {"Y", "N"}:
            raise ValueError(f"Invalid planning year or grid flag at row {line}")
        result.append(
            {
                "source_row": line,
                "developer": identity[0],
                "project": identity[1],
                "power_mw": mw,
                "earliest_commissioning_year": year,
                "planning_status": row["Status"],
                "grid_connected_flag": row["Grid connected?"],
                "island": row["Island"],
                "snapshot_date": "2024-09-12",
                "source_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return result


def parse_transpower_pipeline(content: bytes) -> list[dict[str, Any]]:
    """Stage October 2026 forward BESS rows, including unnamed rows for review.

    This adapter grants no source reuse rights. Connection stages are never
    physical construction/operating statuses; Max MW is not battery nameplate.
    Completed-sheet reconciliation is deliberately outside this forward adapter.
    """
    from datetime import datetime

    from openpyxl import load_workbook

    book = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    expected = [
        "Project ID",
        "Parent Project ID",
        "Customer",
        "Project name",
        "Region",
        "Connection location (substation or circuit)",
        "Max MW",
        "Connection voltage",
        "Technology",
        "Transpower stage",
        "Status Flag",
        "Stage % complete",
        "Status",
        "Consented",
        "Estimated connection livening date",
    ]
    try:
        sheet = book["Forward Pipeline"]
        iterator = sheet.iter_rows(values_only=True)
        if list(next(iterator)[:15]) != expected:
            raise ValueError("Unreviewed Transpower header")
        result = []
        seen = set()
        for line, values in enumerate(iterator, 2):
            row = dict(zip(expected, values[:15], strict=True))
            if row["Technology"] != "BESS":
                continue
            key = row["Project ID"]
            if key is None or str(key) in seen:
                raise ValueError(f"Missing or duplicate Transpower ID at row {line}")
            seen.add(str(key))
            for name, value in row.items():
                if isinstance(value, datetime):
                    row[name] = value.date().isoformat()
            row["Project ID"] = str(key)
            parent = row["Parent Project ID"]
            row["Parent Project ID"] = str(parent) if parent is not None else None
            result.append(
                {
                    "source_sheet": "Forward Pipeline",
                    "source_row": line,
                    "reported_fields": row,
                    "identity_review_required": not bool(row["Customer"] and row["Project name"]),
                    "source_sha256": hashlib.sha256(content).hexdigest(),
                }
            )
        return result
    finally:
        book.close()
