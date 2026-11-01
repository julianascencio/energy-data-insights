"""Privacy-minimized, offline review staging for Japan FIT prefectural workbooks.

Certification IDs are not a plant-boundary crosswalk. This module deliberately
does not produce canonical records or infer operation from certification. The
staged output requires named-project/parcel reconciliation before acceptance.
"""

from __future__ import annotations

import io
import math
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from typing import Any
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

from .sam import verify_sha256

MAIN_HEADERS = {
    1: "設備ID",
    6: "発電設備区分",
    7: "発電出力（kW）",  # noqa: RUF001 -- exact publisher header
    8: "発電設備の所在地",
    10: "太陽電池の合計出力（kW）",  # noqa: RUF001 -- exact publisher header
    11: "新規認定日",
    12: "運転開始予定日",
    13: "運転開始報告年月",
}
PARCEL_HEADERS = {1: "設備ID", 3: "連番", 5: "発電設備区分", 7: "発電設備の所在地"}
MISSING = (None, "", "-", "－")  # noqa: RUF001 -- publisher missing-value marker


def _number(value: Any) -> float | None:
    if value in MISSING:
        return None
    if isinstance(value, bool):
        raise ValueError("Invalid FIT capacity")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("Invalid FIT capacity")
    return number


def _day(value: Any, epoch: datetime) -> str | None:
    if value in MISSING:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = from_excel(value, epoch)
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raise ValueError("Unrecognized FIT date; review workbook revision")


def _month(value: Any, snapshot: date) -> str | None:
    if value in MISSING:
        return None
    match = re.fullmatch(r"(\d{4})年(\d{1,2})月", str(value))
    if match is None:
        raise ValueError("Unrecognized FIT reported operation month")
    year, month = map(int, match.groups())
    if date(year, month, 1) > snapshot:
        raise ValueError("Reported operation month exceeds FIT snapshot")
    return f"{year:04d}-{month:02d}"


def _id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z0-9]{10}", value):
        raise ValueError("Invalid FIT facility ID")
    return value


def stage_fit_review(
    content: bytes,
    *,
    sha256: str,
    source_id: str,
    snapshot_date: str,
    prefecture: str,
    minimum_kw: float = 1000,
) -> dict[str, Any]:
    """Extract factual candidate metadata; all candidates remain unaccepted.

    Names/representatives, business addresses, phone numbers and plant parcel
    strings never leave this function. Parcel overlaps are ID-only review flags.
    Two sheets are reconciled by ID, never counted as separate projects. Positive
    solar-cell output is required in addition to the source's solar label.
    """
    verify_sha256(content, sha256)
    snapshot = date.fromisoformat(snapshot_date)
    if not source_id or not prefecture or not math.isfinite(minimum_kw) or minimum_kw < 1000:
        raise ValueError("FIT review requires source, prefecture and >=1 MW scope")
    if len(content) > 30_000_000:
        raise ValueError("FIT workbook exceeds size limit")
    with ZipFile(io.BytesIO(content)) as archive:
        if sum(item.file_size for item in archive.infolist()) > 150_000_000:
            raise ValueError("Expanded FIT workbook exceeds size limit")
    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        if set(workbook.sheetnames) != {"認定設備", "すべての設備所在地"}:
            raise ValueError("FIT sheets changed; review adapter")
        main = list(workbook["認定設備"].values)
        parcels = list(workbook["すべての設備所在地"].values)
        for rows, index, headers in ((main, 2, MAIN_HEADERS), (parcels, 1, PARCEL_HEADERS)):
            if len(rows) <= index or any(
                len(rows[index]) <= col or rows[index][col] != label
                for col, label in headers.items()
            ):
                raise ValueError("FIT columns changed; review adapter")
        identities: dict[str, tuple[int, tuple[Any, ...]]] = {}
        for line, row in enumerate(main[4:], 5):
            if not any(value is not None for value in row):
                continue
            if len(row) < 14:
                raise ValueError("Truncated FIT row")
            fid = _id(row[1])
            if fid in identities:
                raise ValueError("Duplicate FIT facility ID")
            identities[fid] = (line, row)
        parcel_owners: dict[str, set[str]] = defaultdict(set)
        parcel_rows: dict[str, list[int]] = defaultdict(list)
        for line, row in enumerate(parcels[2:], 3):
            if not any(value is not None for value in row):
                continue
            fid = _id(row[1])
            if fid not in identities or row[5] != identities[fid][1][6]:
                raise ValueError("FIT parcel identity/technology mismatch")
            if not isinstance(row[7], str) or not row[7].strip():
                raise ValueError("FIT parcel location missing")
            key = re.sub(r"\s+", "", unicodedata.normalize("NFKC", row[7]))
            parcel_owners[key].add(fid)
            parcel_rows[fid].append(line)
        overlaps: dict[str, set[str]] = defaultdict(set)
        for ids in parcel_owners.values():
            for fid in ids:
                overlaps[fid].update(ids - {fid})
        candidates = []
        solar_count = 0
        for fid, (line, row) in identities.items():
            if row[6] != "太陽光":
                continue
            solar_count += 1
            capacity = _number(row[7])
            if capacity is None or capacity < minimum_kw:
                continue
            cells = _number(row[10])
            certified = _day(row[11], workbook.epoch)
            if certified and date.fromisoformat(certified) > snapshot:
                raise ValueError("FIT certification exceeds snapshot")
            flags = ["named_project_and_plant_boundary_crosswalk_required"]
            if cells is None or cells == 0:
                flags.append("positive_solar_cell_output_not_verified")
            if not parcel_rows[fid]:
                flags.append("missing_parcel_sheet_rows")
            if overlaps[fid]:
                flags.append("shared_normalized_parcel_with_other_registration")
            candidates.append(
                {
                    "fit_facility_id": fid,
                    "country_code": "JPN",
                    "prefecture": prefecture,
                    "source_id": source_id,
                    "source_sha256": sha256,
                    "snapshot_date": snapshot_date,
                    "source_locator": f"認定設備!B{line}:N{line}",
                    "parcel_sheet_rows": parcel_rows[fid],
                    "source_technology": row[6],
                    "photovoltaic_evidence": cells is not None and cells > 0,
                    "registered_generation_output_kw_basis_unspecified": capacity,
                    "solar_cell_total_output_kw": cells,
                    "new_certification_date": certified,
                    "planned_operation_date": _day(row[12], workbook.epoch),
                    "reported_operation_month": _month(row[13], snapshot),
                    "related_registration_ids": sorted(overlaps[fid]),
                    "disposition": "held_not_canonical",
                    "review_flags": flags,
                }
            )
        return {
            "source_id": source_id,
            "source_sha256": sha256,
            "snapshot_date": snapshot_date,
            "prefecture": prefecture,
            "minimum_kw": minimum_kw,
            "facility_rows": len(identities),
            "solar_rows": solar_count,
            "candidate_count": len(candidates),
            "accepted_count": 0,
            "candidates": candidates,
            "limitations": (
                "Certification is not current operation. Reported operation has month precision; "
                "planned dates are forecasts. Paper filings may lag the portal snapshot. "
                "Exact parcel equality is only a risk screen, not proof of shared plant scope; "
                "nearby/differently written parcels and multiple registrations need review. "
                "No personal details, business names or parcel addresses exported."
            ),
        }
    finally:
        workbook.close()
