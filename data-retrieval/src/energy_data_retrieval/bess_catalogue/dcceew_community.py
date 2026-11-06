"""Stage DCCEEW community-battery location tables from a local reader export.

This parser accepts the attributed text representation, not original HTML bytes.
It never converts grant recipients into owners or in-progress grants into built
assets. One row can aggregate several batteries in the named programme location.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from typing import Any

COUNTS = {
    "Australian Capital Territory": 3,
    "New South Wales": 16,
    "Queensland": 13,
    "South Australia": 2,
    "Tasmania": 2,
    "Victoria": 16,
    "Western Australia": 5,
}
HEADER = "Applicant details | Location | Grant amount | (kWh) capacity | Operational status"


def parse_community_tables(text: str) -> list[dict[str, Any]]:
    """Require the reviewed 12 October 2026 partition, all 57 displayed rows.

    The narrative says 58 locations; the displayed table contains 57. That gap
    must remain explicit. Source line prefixes from the reader are optional.
    """
    text = re.sub(r"^L\d+: ?", "", text, flags=re.M)
    if "Last updated: 12 October 2026" not in text:
        raise ValueError("Unreviewed publication date")
    if text.count("### Business Grants Hub streams 1 & 2") != 1:
        raise ValueError("Missing or duplicate programme partition")
    text = text.split("### Business Grants Hub streams 1 & 2")[1]
    if "### ARENA Community Batteries round 1" not in text:
        raise ValueError("Truncated programme partition")
    text = text.split("### ARENA Community Batteries round 1")[0]
    region = None
    header_seen = False
    counts: Counter[str] = Counter()
    identities: set[tuple[str, str, str]] = set()
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = " ".join(line.split())
        if not line:
            continue
        if line.startswith("#### [Button: ") and line.endswith("]"):
            region = line.removeprefix("#### [Button: ").removesuffix("]")
            if region not in COUNTS or region in counts:
                raise ValueError("Unknown or repeated region")
            header_seen = False
        elif line == HEADER:
            if header_seen or region is None:
                raise ValueError("Unexpected table header")
            header_seen = True
        elif line == "--- | --- | --- | --- | ---":
            continue
        elif "|" in line:
            if not header_seen or region is None:
                raise ValueError("Changed table header")
            cells = [x.strip() for x in line.split("|")]
            if len(cells) != 5 or not all(cells):
                raise ValueError("Incomplete table row")
            applicant, locality, grant, energy, status = cells
            identity = region, applicant, locality
            if identity in identities:
                raise ValueError("Duplicate applicant/location identity")
            identities.add(identity)
            if not re.fullmatch(r"\$\d{1,3}(?:,\d{3})*", grant):
                raise ValueError("Changed grant currency/format")
            if not re.fullmatch(r"\d+", energy) or int(energy) <= 0:
                raise ValueError("Invalid kWh capacity")
            operational_from = None
            if status.startswith("From "):
                if not re.fullmatch(r"From \d{1,2}/\d{1,2}/\d{2}", status):
                    raise ValueError("Changed operation date format")
                day, month, year = map(int, status[5:].split("/"))
                operational_from = date(2000 + year, month, day)
                if operational_from > date(2026, 10, 12):
                    raise ValueError("Operation date after publication")
            elif status != "In progress":
                raise ValueError("Unreviewed status")
            counts[region] += 1
            rows.append(
                {
                    "region": region,
                    "applicant": applicant,
                    "locality": locality,
                    "grant_amount": int(grant[1:].replace(",", "")),
                    "grant_symbol": "$",
                    "capacity_kwh": int(energy),
                    "operational_status_native": status,
                    "operational_from": operational_from.isoformat() if operational_from else None,
                    "locator": (
                        f"Business Grants Hub streams 1 & 2; {region}; "
                        f"row {counts[region]} ({locality})"
                    ),
                }
            )
        else:
            raise ValueError("Unreviewed content inside table partition")
    if dict(counts) != COUNTS:
        raise ValueError("Incomplete or changed regional row counts (57 expected)")
    return rows
