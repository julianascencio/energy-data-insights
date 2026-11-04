"""Stage public RVO SDE subsidy decisions; never turn an award into a plant.

Recipient names, addresses and postcodes are deliberately excluded. Anonymised
decisions are withheld entirely, even if another field might reveal their site.
"""

from __future__ import annotations

import hashlib
import io
import math
import re
from typing import Any

from openpyxl import load_workbook

REQUIRED = {
    "SDE ronde",
    "Referentie",
    "Categorie",
    "Thema",
    "Aanvrager Naam",
    "Adres",
    "Postcode",
    "Plaats lokatie",
    "Gemeente",
    "RES-regio",
    "Provincie",
    "Looptijd [jr.]",
    "Maximale subsidie [€]",
    "Opstelling zon-pv",
    "Gerealiseerd",
    "Ingebruikname jaar",
}
PRIVATE = {"Aanvrager Naam", "Adres", "Postcode", "Plaats lokatie"}
MOUNTINGS = {"Veldsysteem", "Watersysteem"}


def read_rvo_workbook(
    content: bytes, *, sha256: str, after_reference: str | None = None, limit: int = 100
) -> dict[str, Any]:
    """Read a bounded ground/water PV decision partition from a pinned workbook.

    Exact award references define the cursor, not canonical plant identities.
    Subsidy maxima are not capex; category MWp thresholds are not plant ratings.
    Realisation flags/years are source observations, not current operating states.
    """
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("RVO source checksum mismatch")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("RVO partition limit must be 1-1000")
    if after_reference is not None and (
        not isinstance(after_reference, str) or not after_reference.strip()
    ):
        raise ValueError("RVO cursor must be a nonempty exact reference")
    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        sheets = [s for s in workbook if s.title.startswith("Projecten in beheer")]
        if len(sheets) != 1:
            raise ValueError("RVO decision worksheet missing or ambiguous")
        sheet = sheets[0]
        header, header_row = None, None
        for number, values in enumerate(sheet.iter_rows(max_row=40, values_only=True), 1):
            names = [value.strip() if isinstance(value, str) else value for value in values]
            if "Referentie" in names and "Categorie" in names:
                present = [n for n in names if n is not None]
                if len(present) != len(set(present)) or not set(present) >= REQUIRED:
                    raise ValueError("RVO decision schema changed")
                header, header_row = names, number
                break
        if header is None or header_row is None:
            raise ValueError("RVO decision header missing")
        counts = dict.fromkeys(
            [
                "decision_rows",
                "explicit_pv",
                "non_pv_or_unproven",
                "anonymised_pv",
                "other_pv_mountings",
                "eligible_ground_water",
            ],
            0,
        )
        references: set[str] = set()
        candidates: list[dict[str, Any]] = []
        for number, values in enumerate(
            sheet.iter_rows(min_row=header_row + 1, values_only=True), header_row + 1
        ):
            row = dict(zip(header, values, strict=True))
            reference = row["Referentie"]
            if reference is None and all(row.get(k) is None for k in REQUIRED):
                continue
            if not isinstance(reference, str) or not reference.strip():
                raise ValueError("RVO decision reference missing")
            if reference in references:
                raise ValueError("RVO repeated decision reference requires review")
            references.add(reference)
            counts["decision_rows"] += 1
            theme = row["Thema"]
            if (
                row["Categorie"] != "Zon"
                or not isinstance(theme, str)
                or not re.search(r"\bZon-PV\b", theme, flags=re.IGNORECASE)
            ):
                counts["non_pv_or_unproven"] += 1
                continue
            counts["explicit_pv"] += 1
            if any("***" in str(row.get(k) or "") for k in PRIVATE):
                counts["anonymised_pv"] += 1
                continue
            if row["Opstelling zon-pv"] not in MOUNTINGS:
                counts["other_pv_mountings"] += 1
                continue
            for key in ["Looptijd [jr.]", "Maximale subsidie [€]"]:
                value = row[key]
                if value is not None and (
                    type(value) not in (int, float) or not math.isfinite(value) or value < 0
                ):
                    raise ValueError("RVO grant amount/duration is not a native nonnegative number")
            for key in ["SDE ronde", "Gemeente", "Provincie", "RES-regio", "Gerealiseerd"]:
                if row[key] is not None and not isinstance(row[key], str):
                    raise ValueError("RVO text field type changed")
            year = row["Ingebruikname jaar"]
            if year is not None and (
                type(year) not in (str, int, float)
                or (type(year) is float and not math.isfinite(year))
            ):
                raise ValueError("RVO native year field type changed")
            counts["eligible_ground_water"] += 1
            candidates.append(
                {
                    "decision_reference": reference,
                    "worksheet_row": number,
                    "round_native": row["SDE ronde"],
                    "pv_category_native": theme,
                    "mounting_native": row["Opstelling zon-pv"],
                    "municipality_native": row["Gemeente"],
                    "province_native": row["Provincie"],
                    "res_region_native": row["RES-regio"],
                    "maximum_subsidy_eur": row["Maximale subsidie [€]"],
                    "subsidy_duration_years": row["Looptijd [jr.]"],
                    "realised_native": row["Gerealiseerd"],
                    "in_use_year_native": row["Ingebruikname jaar"],
                    "accepted": False,
                    "held_reasons": [
                        "subsidy_decision_not_reviewed_plant_or_phase_identity",
                        "no_nameplate_capacity_in_workbook",
                        "realisation_flag_not_current_operation_verification",
                        "subsidy_maximum_not_capex_or_actual_payment",
                    ],
                }
            )
        candidates.sort(key=lambda row: row["decision_reference"])
        pending = [
            r
            for r in candidates
            if after_reference is None or r["decision_reference"] > after_reference
        ]
        selected = pending[:limit]
        return {
            "sha256": sha256,
            "worksheet": sheet.title,
            "header_row": header_row,
            "counts": counts,
            "candidates": selected,
            "next_after_reference": selected[-1]["decision_reference"]
            if selected
            else after_reference,
            "remaining_after_partition": len(pending) - len(selected),
            "accepted_records": 0,
            "private_fields_and_geometry_excluded": True,
        }
    finally:
        workbook.close()
