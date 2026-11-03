"""Stage the reviewed December 2021 Maldives ARISE screening table offline.

Input is local ``pdftotext -layout`` output. These are historical planning
observations, not as-built capacities or evidence of operation. Identity review
must keep the two Addu grids separate and the Kallaidhoo shared grid together.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

SITE_LABELS = (
    "Eydhafushi",
    "Thinadhoo",
    "Kulhudhuhfushi",
    "Addu (Mainland in Hithadhoo)",
    "Addu (Hulhudhoo Meedhoo)",
    "Hinnavaru",
    "Fuvahmulah",
    "Fonadhoo",
    "Gan",
    "Kallaidhoo",
    "Maabaidhoo",
    "Maamendhoo",
    "Kunahandhoo",
    "Hithadhoo",
    "Maavah",
    "Funadhoo",
    "Naifaru",
    "Villingili",
)


def parse_arise_screening(text: str) -> list[dict[str, Any]]:
    """Extract 18 reviewed rows; fail closed on changed units, date or identity.

    Values are staged without catalogue IDs, inferred power or coordinates. The
    table sum is deliberately not forced to equal the approximate cover total.
    """
    if "09th December 2021" not in text or "37 MWh" not in text:
        raise ValueError("Unreviewed ARISE report revision")
    pages = text.split("\f")
    matches = [p for p in pages if "Island" in p and "Container Number Estimate" in p]
    if len(matches) != 1:
        raise ValueError("Expected one reviewed ARISE capacity table")
    page = matches[0]
    if "(MWh)" not in page or "(sqft)" not in page or "pg. 15" not in page:
        raise ValueError("Changed table units or page")
    body = page.split("(sqft)", 1)[1].split("pg. 15", 1)[0]
    # Source wraps these two labels around their numeric cells.
    body = re.sub(r"\n\s*in Hithadhoo\)", "", body)
    body = re.sub(r"\n\s*\(Hulhudhoo\s*\n\s*Meedhoo\)", "", body)
    rows: list[dict[str, Any]] = []
    for line in body.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(
            r"\s*(.*?)\s+(\d+(?:\.\d+)?)\s+(20|40)\u2019\s*x\s*8\u2019\s+(\d+)\s+(\d+)\s*",
            line,
        )
        if match is None:
            raise ValueError("Unrecognized ARISE table row")
        label, energy, length, count, area = match.groups()
        label = {
            "Addu (Mainland": "Addu (Mainland in Hithadhoo)",
            "Addu": "Addu (Hulhudhoo Meedhoo)",
        }.get(label, label)
        if Decimal(energy) <= 0 or int(count) <= 0 or int(area) <= 0:
            raise ValueError("Nonpositive planning observation")
        rows.append(
            {
                "source_site_label": label,
                "planned_energy_mwh": float(energy),
                "planned_container_length_ft": int(length),
                "planned_container_width_ft": 8,
                "estimated_container_count": int(count),
                "estimated_area_sqft": int(area),
                "observation_date": "2021-12-09",
                "locator": f"PDF page 15, capacity table, row {len(rows) + 1}",
            }
        )
    if tuple(r["source_site_label"] for r in rows) != SITE_LABELS:
        raise ValueError("Changed, missing or duplicate ARISE site identity")
    return rows
